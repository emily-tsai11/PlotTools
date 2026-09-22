"""
Plugin to recompute the flavour-tagging event weight ("flavTagWeight") and all
of its systematic variations on the fly, directly inside an RDataFrame graph,
from a correctionlib SF file that is independent of whatever flavTagWeight
branches are already stored in the flat ntuple (e.g. to test an updated
flavTaggingSF*.json.gz without re-running the NanoAOD-tools postprocessing
step, see PhysicsTools/NanoTTH/python/producers/flavTagSFProducer.py for how
the stored branches were originally produced).

The flat ntuples keep the per-jet arrays needed to reproduce that computation
(ak4_hflav, ak4_tag, ak4_eta, ak4_pt), so the weight can be rebuilt event by
event as the product of the per-jet scale factors, exactly like
FlavTagSFProducer.compute_weights does, but evaluated lazily by RDataFrame
instead of at ntuple-production time.

Typical use, mirroring the systematics dictionaries in hdumper.py /
prepareHistosForCards.py, whose entries look like
"flavTagWeight_XSec_ttbar_UP/flavTagWeight":

    systematics = produce_systematics(year, suffix)
    df, prefix = define_flavtag_weights(
        df, year, json_path=alt_json,
        systematics=extract_systematics(systematics.values()))
    systematics = {k: remap_expression(v, prefix) for k, v in systematics.items()}

after which every flavTagWeight term in those expressions -- central value and
up/down variations alike -- refers to the recomputed columns rather than to the
branches stored in the ntuple.
"""
import gzip
import json
import os
import re

import ROOT

# era / correction-name lookup, mirrored from FlavTagSFProducer so that a
# sensible default json.gz / correction name can be derived from just the
# data-taking year when the caller doesn't pass one explicitly.
_ERA_FOR_YEAR = {
    2015: '2016preVFP_UL',
    2016: '2016postVFP_UL',
    2017: '2017_UL',
    2018: '2018_UL',
    20220: '2018_UL',
    20221: '2018_UL',
    20230: '2018_UL',
    20231: '2018_UL',
    2024: '2024',
    2025: '2024',
    20242025: '2024',
}

# Name of the weight as stored in the ntuple; also the stem of the stored
# systematic branches ("<STORED_WEIGHT_NAME>_<syst>_UP"/"_DOWN").
STORED_WEIGHT_NAME = 'flavTagWeight'

# Same clipping as applied by FlavTagSFProducer when filling its branches.
_WEIGHT_CLIP = (0.3, 3.0)

_loaded_corrections = {}  # (json_path, correction_name) -> generated C++ function name
_pyroot_binding_registered = False


def _correction_name_for_year(year):
    return 'UParTAK4_pseudocontinuous' if year in (2024, 2025, 20242025) else 'particleNetAK4_shape'


def default_json_for_year(year):
    era = _ERA_FOR_YEAR[year]
    return os.path.expandvars(
        f'$CMSSW_BASE/src/PhysicsTools/NanoTTH/data/flavTagSF/flavTaggingSF_{era}.json.gz')


def extract_systematics(expressions, stored_name=STORED_WEIGHT_NAME):
    """
    Scan a collection of weight expressions (e.g. the values of the dictionary
    returned by produce_systematics) and return the sorted set of flavour-tagging
    systematic names they reference.

    An expression such as "flavTagWeight_XSec_ttbar_UP/flavTagWeight" yields
    "XSec_ttbar"; this is the name that maps onto the correctionlib keys
    "up_XSec_ttbar" / "down_XSec_ttbar".
    """
    pattern = re.compile(rf'\b{re.escape(stored_name)}_(.+?)_(?:UP|DOWN)\b')
    found = set()
    for expr in expressions:
        if not isinstance(expr, str):
            continue
        found.update(pattern.findall(expr))
    return sorted(found)


def remap_expression(expression, prefix, stored_name=STORED_WEIGHT_NAME):
    """
    Rewrite a weight expression so that every reference to the flavour-tagging
    weight -- the central "flavTagWeight" as well as the "flavTagWeight_<syst>_UP"
    / "_DOWN" variations -- points at the recomputed columns defined by
    define_flavtag_weights instead of at the branches stored in the ntuple.
    """
    if not isinstance(expression, str) or prefix == stored_name:
        return expression
    return re.sub(rf'\b{re.escape(stored_name)}', prefix, expression)


def available_systematics(json_path, correction_name):
    """
    Return the set of systematic keys ("central", "up_JER", "down_JER", ...)
    understood by the given correction, by inspecting the correctionlib JSON
    directly. Returns None if the structure could not be interpreted, in which
    case callers should assume every requested systematic is available.
    """
    opener = gzip.open if json_path.endswith('.gz') else open
    try:
        with opener(json_path, 'rt') as handle:
            payload = json.load(handle)
    except (OSError, ValueError):
        return None

    for correction in payload.get('corrections', []):
        if correction.get('name') == correction_name:
            return _find_systematic_keys(correction.get('data'))
    return None


def _find_systematic_keys(node):
    """
    Walk a correctionlib data tree and return the keys of the first category
    node that switches on the "systematic" input.
    """
    if isinstance(node, dict):
        if node.get('nodetype') == 'category' and node.get('input') == 'systematic':
            keys = {item['key'] for item in node.get('content', [])
                    if isinstance(item, dict) and isinstance(item.get('key'), str)}
            if keys:
                return keys
        for value in node.values():
            keys = _find_systematic_keys(value)
            if keys:
                return keys
    elif isinstance(node, list):
        for value in node:
            keys = _find_systematic_keys(value)
            if keys:
                return keys
    return None


def _register_pyroot_binding():
    global _pyroot_binding_registered
    if _pyroot_binding_registered:
        return
    import correctionlib
    correctionlib.register_pyroot_binding()
    _pyroot_binding_registered = True


def _cpp_string_literal(value):
    return '"' + value.replace('\\', '\\\\').replace('"', '\\"') + '"'


def _get_eval_function(json_path, correction_name):
    """
    JIT-compile (and cache) a C++ function that lazily loads the given
    correctionlib json.gz file/correction on its first call (as a function-local
    static, so the load happens once) and evaluates the product of per-jet scale
    factors for the systematic passed at call time. Returns the function's name.

    The correctionlib Correction::Ref is a std::shared_ptr-based type that cannot
    be handed over from Python to a global C++ variable via plain attribute
    assignment (cppyy can only memcpy trivially-copyable types that way), so the
    file path and correction name are instead embedded as C++ string literals
    and the object is constructed entirely on the C++ side.
    """
    key = (json_path, correction_name)
    if key in _loaded_corrections:
        return _loaded_corrections[key]

    _register_pyroot_binding()
    func_name = f"flavTagWeightPlugin_eval{len(_loaded_corrections)}"
    lo, hi = _WEIGHT_CLIP
    ROOT.gInterpreter.Declare(f"""
    #include "correction.h"
    #include <algorithm>
    #include <cmath>

    double {func_name}(const std::string& syst,
                        const ROOT::RVec<Int_t>& hflav,
                        const ROOT::RVec<Float_t>& tag,
                        const ROOT::RVec<Float_t>& eta,
                        const ROOT::RVec<Float_t>& pt) {{
        static const correction::Correction::Ref corr =
            correction::CorrectionSet::from_file({_cpp_string_literal(json_path)})
                ->at({_cpp_string_literal(correction_name)});
        double w = 1.0;
        for (std::size_t i = 0; i < pt.size(); ++i) {{
            w *= corr->evaluate({{syst, hflav[i], static_cast<int>(tag[i]),
                                   static_cast<double>(std::fabs(eta[i])),
                                   static_cast<double>(pt[i])}});
        }}
        return std::clamp(w, {lo}, {hi});
    }}
    """)

    _loaded_corrections[key] = func_name
    return func_name


def define_flavtag_weights(df, year, json_path=None, correction_name=None,
                            systematics=None, prefix='flavTagWeightRecomputed',
                            hflav_branch='ak4_hflav', tag_branch='ak4_tag',
                            eta_branch='ak4_eta', pt_branch='ak4_pt',
                            verbose=True):
    """
    Add the recomputed flavour-tagging weight columns to an RDataFrame:
    `prefix` for the central value, plus `prefix_<syst>_UP` and
    `prefix_<syst>_DOWN` for every requested systematic.

    Parameters:
    - df: input RDataFrame (must already contain the per-jet ak4_* branches).
    - year: data-taking year, used to pick a default json.gz / correction name
            if json_path / correction_name are not given explicitly.
    - json_path: path to the flavTaggingSF*.json.gz file to use as the alternate
                 source (defaults to the same file/era mapping as FlavTagSFProducer).
    - correction_name: name of the correction inside the json.gz file (defaults
                       to the standard per-year name).
    - systematics: iterable of systematic names, in the same spelling as the
                   stored branches ("XSec_ttbar", "JER", "Stat_flavB_C0", ...).
                   Pass the result of extract_systematics() to define exactly
                   those needed by a given systematics dictionary. If None, only
                   the central weight is defined.
    - prefix: base name of the columns added to the dataframe.

    Systematics that the SF file does not provide are defined as copies of the
    central weight, so that the corresponding up/down ratios evaluate to 1 and
    the nuisance is flat rather than the job failing; a warning lists them.

    Returns the (df, prefix) tuple.
    """
    if json_path is None:
        json_path = default_json_for_year(year)
    else:
        json_path = os.path.expandvars(json_path)
    if correction_name is None:
        correction_name = _correction_name_for_year(year)

    func_name = _get_eval_function(json_path, correction_name)
    jets = f'{hflav_branch}, {tag_branch}, {eta_branch}, {pt_branch}'

    df = df.Define(prefix, f'{func_name}("central", {jets})')

    if not systematics:
        return df, prefix

    known = available_systematics(json_path, correction_name)
    missing = []
    for syst in systematics:
        keys = {'UP': f'up_{syst}', 'DOWN': f'down_{syst}'}
        # Treat a systematic as unavailable unless both directions are present, so that a
        # partially-defined variation degrades to a flat nuisance rather than a one-sided one.
        absent = known is not None and any(key not in known for key in keys.values())
        if absent:
            missing.append(syst)
        for direction, key in keys.items():
            # Falling back to the central value makes the up/down ratio evaluate to 1.
            df = df.Define(f'{prefix}_{syst}_{direction}',
                           prefix if absent else f'{func_name}("{key}", {jets})')

    if verbose:
        n_defined = len(systematics) - len(missing)
        print(f'[flavTagWeightPlugin] Recomputing flavTagWeight from {json_path} '
              f'(correction "{correction_name}"): central + {n_defined} systematic(s).')
        if missing:
            print(f'[flavTagWeightPlugin] WARNING: {len(missing)} systematic(s) are absent '
                  f'from this SF file and were set equal to the central weight '
                  f'(flat nuisance): {", ".join(missing)}')

    return df, prefix


def define_flavtag_weight(df, year, json_path=None, correction_name=None, syst='central',
                           new_branch='flavTagWeightRecomputed',
                           hflav_branch='ak4_hflav', tag_branch='ak4_tag',
                           eta_branch='ak4_eta', pt_branch='ak4_pt'):
    """
    Define a single recomputed flavour-tagging weight column for one systematic
    (central by default). Kept for callers that only need the nominal weight;
    define_flavtag_weights() is the entry point that also covers the variations.

    Returns the (df, new_branch) tuple.
    """
    if json_path is None:
        json_path = default_json_for_year(year)
    else:
        json_path = os.path.expandvars(json_path)
    if correction_name is None:
        correction_name = _correction_name_for_year(year)

    func_name = _get_eval_function(json_path, correction_name)

    df = df.Define(
        new_branch,
        f'{func_name}("{syst}", {hflav_branch}, {tag_branch}, {eta_branch}, {pt_branch})'
    )
    return df, new_branch
