"""hdumper_faster.py

Full-featured hdumper.py (flavTagWeightPlugin on-the-fly SF recomputation,
the current expanded systematics list, all CLI options), with process_tree's
inner loop rebuilt around RDataFrame's Vary()/VariationsFor() API
(ROOT::RDF::Experimental) for systematics batching.

Why this exists: hdumper.py computes each systematic's weight via its own
separate Define() call -- with the current systematics list that's ~140
distinct strings per selection, individually JIT-compiled by cling, even
though they all boil down to "multiply the nominal weight by one more ratio
branch". Vary() lets you express "one nominal value + N alternate values" as
a SINGLE expression (one JIT-compiled function returning a vector of all N+1
values), and VariationsFor() unpacks the nominal result plus every variation
from ONE booked action. Concretely, per selection this collapses roughly
N_systematics separate Histo1D-per-branch bookings down to 1 booking per
branch (or, in --eventClassification mode, 1 per branch instead of
N_systematics per branch, since each branch still needs its own Filter
before the weight can be read).

Gotchas this file works around:
  - Calling .GetValue()/.Count()/.Sum() eagerly *inside* the selection loop
    forces a full event-loop pass per call instead of one shared pass; every
    Histo1D/Sum/Count action below is only *booked* inside the loop, and
    materialized (.GetPtr()/.GetValue()/VariationsFor()) exactly once per
    booking, all together, in the final "Materializing" block.
  - VariationsFor() itself has the same eager-trigger behavior as .GetValue(),
    so it must also be deferred to that same final block, not called once per
    selection inside the loop (confirmed 2x slower when done eagerly).
  - The per-selection Filter() is hoisted out of the systematics loop (it
    doesn't depend on which systematic is being computed), avoiding redundant
    JIT compiles of the same filter string once per systematic.
  - The per-selection Vary() is computed once and shared between the Sum()
    booking and every histogram booking outside --eventClassification mode
    (two separate but identical Vary() calls would each pay their own JIT
    compile of the ~140-entry expression for no benefit).

Everything else -- the flavTagWeightPlugin on-the-fly flavour-tagging SF
recomputation, the exact systematics dictionary, weight formulas, CLI,
selections, and output file naming/merging -- is carried over unchanged from
hdumper.py; this file should produce byte-for-byte equivalent histograms to
hdumper.py, just computed with far fewer JIT-compiled functions.

Caveat: ROOT::RDF::Experimental is, as the namespace says, still tagged
experimental upstream -- its interface could change in a future ROOT release.
"""

import ROOT
import argparse
import glob
import csv
import os
from colorama import Fore, Style
import numpy as np
import multiprocessing as mp
from functools import partial
import correctionlib
import flavTagWeightPlugin

ROOT.ROOT.EnableImplicitMT()
ROOT.gROOT.SetBatch(True)
ROOT.TTreeCache.SetLearnEntries(200)
ROOT.gEnv.SetValue("TFile.AsyncPrefetching", 2)
ROOT.TH1.SetDefaultSumw2(True)

suffix_dict = {'base' : '', 'ttLF' : '_0', 'ttcj' : '_41', 'tt2c' : '_42', 'ttcc' : '_43', 'ttbj' : '_51', 'tt2b' : '_52', 'ttbb' : '_53'}
perProcessSysts = [
    "topHdampWeight_", "bFragWeight_", "bFragPetersonWeight_",
    "LHE_muF_", "LHE_muR_", "LHE_PDF_", "LHE_aS_", "PS_fsr_", "PS_isr_",
    "minorBkg_PS_ISR_", "minorBkg_PS_FSR_",
]

VARIATION_NAME = "syst"  # internal RDF variation-group name; remapped back to CMS systematic names before anything is written out


def add_overflow_underflow(hist):
    """
    Add underflow (bin 0) to first bin and overflow (bin N+1) to last bin.

    Parameters:
    - hist: ROOT.TH1 histogram
    """
    nbins = hist.GetNbinsX()

    # Add underflow to first bin
    underflow = hist.GetBinContent(0)
    underflow_err = hist.GetBinError(0)
    first_bin = hist.GetBinContent(1)
    first_bin_err = hist.GetBinError(1)

    hist.SetBinContent(1, first_bin + underflow)
    hist.SetBinError(1, np.sqrt(first_bin_err**2 + underflow_err**2))
    hist.SetBinContent(0, 0)
    hist.SetBinError(0, 0)

    # Add overflow to last bin
    overflow = hist.GetBinContent(nbins + 1)
    overflow_err = hist.GetBinError(nbins + 1)
    last_bin = hist.GetBinContent(nbins)
    last_bin_err = hist.GetBinError(nbins)

    hist.SetBinContent(nbins, last_bin + overflow)
    hist.SetBinError(nbins, np.sqrt(last_bin_err**2 + overflow_err**2))
    hist.SetBinContent(nbins + 1, 0)
    hist.SetBinError(nbins + 1, 0)

    return hist


def _active_systematics(systematics, do_systematics, infile):
    """Replicates hdumper.py's per-process systematic skip logic, returning
    just the list of systematic names that actually apply here (excluding
    "None", the nominal case, which is always handled separately). Operates
    purely on systematic *names*, so it's unaffected by whether the
    systematics dict's expressions were remapped by flavTagWeightPlugin."""
    if not do_systematics:
        return []

    # perProcessSystsWithoutLHEmuRmuF = [p for p in perProcessSysts
    #                                     if not (p.startswith("LHE_muR") or p.startswith("LHE_muF") or p.startswith("minorBkg_PS_"))]
    perProcessSystsWithoutMinorBkg = [p for p in perProcessSysts if not p.startswith("minorBkg_PS_")]
    active = []
    for syst in systematics.keys():
        if syst == "None":
            continue
        # if any(syst.startswith(p) for p in perProcessSystsWithoutLHEmuRmuF) and "tt" not in infile:
        if any(syst.startswith(p) for p in perProcessSystsWithoutMinorBkg) and "tt" not in infile:
            continue  # Skip certain systematics if the process is not a ttbar one (including signal, ttH, and ttV)
        if syst.startswith("minorBkg") and "tt" in infile:
            continue  # Minor background systematics do not pertain to ttbar processes
        active.append(syst)
    return active


def process_tree(infile, outfile, tree_name, hist_configs, year, selections, eventClassification, use5FS, count_events, do_systematics=False, flavtag_sf_json=None, flavtag_sf_name=None):
    """
    Processes a TTree, converts it to multiple TH1Ds for specified branches, and saves them to a ROOT file.
    Same signature, same output files/histograms as hdumper.py's process_tree -- see module docstring for
    what's different internally.

    Parameters:
    - input_files: List of input ROOT files.
    - output_files: List of output ROOT files.
    - tree_names: List of TTree names corresponding to input files.
    - hist_configs: List of dictionaries with keys 'branch', 'nbins', 'xmin', 'xmax'.
    - year: Year of data taking.
    - selections: String containing common event preselection.
    - eventClassification: Boolean indicating whether to apply event classification.
    - use5FS: Boolean indicating whether to use 5-flavor scheme MC for ttbb and ttbj processes.
    - count_events: Decide whether to count events for each selection (probably slows things down a bit).
    - flavtag_sf_json: Optional path to an alternate flavTaggingSF*.json.gz file; if given,
      flavTagWeight is recomputed on the fly from this file instead of the ntuple's branch.
    - flavtag_sf_name: Optional correctionlib correction name inside flavtag_sf_json.
    """
    print("")

    print(f"{Fore.RED}Processing file: {infile}{Style.RESET_ALL}")

    # Open input file
    input_file = ROOT.TFile.Open(infile)
    if not input_file or input_file.IsZombie():
        raise FileNotFoundError(f"Could not open file: {infile}")

    # Access the TTree
    tree = input_file.Get(tree_name)
    if not tree or not isinstance(tree, ROOT.TTree):
        raise ValueError(f"TTree '{tree_name}' not found in file '{infile}'.")

    # Optimize TTree reading
    tree.SetCacheSize(100000000)  # 100MB cache
    tree.AddBranchToCache("*", True)

    # Create RDataFrame from TTree
    df = ROOT.RDataFrame(tree)

    # Apply base selection everywhere (and early, to speed things up)
    base_filter = selections["base"]
    if "singlee" in infile:
        base_filter += " && passTrigMu==0"  # Remove from the electron channel the events that fired the muon trigger. Could choose to do vice versa as well.
    df = df.Filter(base_filter)

    # Recompute the flavour-tagging weight (central value, plus every systematic variation
    # referenced by produce_systematics when running with --systematics) on the fly from an
    # alternate correctionlib SF file, instead of relying on the flavTagWeight* branches
    # already stored in the ntuple. The flavour-tagging entries do not depend on the
    # per-category suffix, so the needed variations are collected from the suffix-less dict.
    flavtag_weight_branch = flavTagWeightPlugin.STORED_WEIGHT_NAME
    if flavtag_sf_json and "data" not in infile.lower():
        needed_systs = flavTagWeightPlugin.extract_systematics(
            produce_systematics(year, '').values()) if do_systematics else None
        df, flavtag_weight_branch = flavTagWeightPlugin.define_flavtag_weights(
            df, year, json_path=flavtag_sf_json, correction_name=flavtag_sf_name,
            systematics=needed_systs)

    adhoc_selection, adhoc_binning = None, None
    if eventClassification:
        print(f"{Fore.YELLOW}Running in event classification mode. Will define a series of fractional scores.{Style.RESET_ALL}")
        # Define the fractional scores
        df = df.Define("denominator", "score_ttbb + score_tt2b + score_ttbj + score_ttcc + score_tt2c + score_ttcj + score_ttLF") \
            .Define("fscore_ttbb", "score_ttbb / denominator") \
            .Define("fscore_tt2b", "score_tt2b / denominator") \
            .Define("fscore_ttbj", "score_ttbj / denominator") \
            .Define("fscore_ttcc", "score_ttcc / denominator") \
            .Define("fscore_tt2c", "score_tt2c / denominator") \
            .Define("fscore_ttcj", "score_ttcj / denominator") \
            .Define("fscore_ttLF", "score_ttLF / denominator")
        from configs.weights_and_constants import adhoc_selection, adhoc_binning
    else:
        df = df.Define("ak4_1_pt", "ak4_pt.size() > 0 ? ak4_pt[0] : 0") \
            .Define("ak4_1_phi",   "ak4_phi.size() > 0 ? ak4_phi[0] : 0") \
            .Define("ak4_1_eta",   "ak4_eta.size() > 0 ? ak4_eta[0] : 0") \
            .Define("ak4_2_pt",    "ak4_pt.size() > 1 ? ak4_pt[1] : 0") \
            .Define("ak4_2_phi",   "ak4_phi.size() > 1 ? ak4_phi[1] : 0") \
            .Define("ak4_2_eta",   "ak4_eta.size() > 1 ? ak4_eta[1] : 0") \
            .Define("ak4_3_pt",    "ak4_pt.size() > 2 ? ak4_pt[2] : 0") \
            .Define("ak4_3_phi",   "ak4_phi.size() > 2 ? ak4_phi[2] : 0") \
            .Define("ak4_3_eta",   "ak4_eta.size() > 2 ? ak4_eta[2] : 0") \
            .Define("ak4_4_pt",    "ak4_pt.size() > 3 ? ak4_pt[3] : 0") \
            .Define("ak4_4_phi",   "ak4_phi.size() > 3 ? ak4_phi[3] : 0") \
            .Define("ak4_4_eta",   "ak4_eta.size() > 3 ? ak4_eta[3] : 0")

    tt_file_names = ["ttbb-4f", "ttbar-powheg"]
    tt4f_strings = ["ttbb", "ttbj", "tt2b"]
    tt_strings   = ["ttcc", "ttcj", "tt2c", "ttLF"]

    # Initialize counters for events
    local_total_MC_events = 0
    local_events_in_category = {key: 0 for key in selections.keys() if not key == "base"}

    is_data = "data" in infile or "Data" in infile

    # Everything below is *booked* only -- .GetPtr()/.GetValue()/VariationsFor()
    # calls are deferred to the single "Materializing" block after this loop,
    # for the same reason as in hdumper.py: any of them triggers immediate
    # execution of the whole graph booked so far.
    hist_bookings = {}   # (selection_name, branch_name) -> (lazy RResultPtr, active_systs, hist_name_base)
    sum_bookings = {}    # selection_name -> (lazy RResultPtr, active_systs)
    count_results = {}   # selection_name -> lazy RResultPtr (Count doesn't depend on syst, no Vary needed)

    # Process each selection-output combinations
    for selection_name in selections:

        # Apply base selection to every sample; apply the ttbar-specific selection to the right 4F, dps, and 5F powheg samples
        if not "base" in selection_name and not any(x in infile for x in tt_file_names):
            continue
        if any(x in infile for x in tt_file_names) and "base" in selection_name:
            continue
        if any(x in selection_name for x in tt_strings) and not "powheg" in infile:
            continue
        if use5FS:  # only powheg
            if any(x in selection_name for x in tt4f_strings) and not "powheg" in infile:
                continue
        else:  # dedicated 4fs samples for ttbb, ttbj, tt2b
            if any(x in selection_name for x in tt4f_strings) and not "bb" in infile:
                continue

        suffix = suffix_dict.get(selection_name, '')

        # Filter once per selection (shared across every systematic and every
        # branch) -- avoids re-Filter()'ing (and re-JIT-compiling) the same
        # selection string once per systematic.
        if not "base" in selection_name:
            print(f"Applying additional selection for {infile}: {Fore.RED}{selection_name}{Style.RESET_ALL}")
            df_selected_base = df.Filter(selections[selection_name])
            if count_events:
                # Lazy: don't call .GetValue() here, materialized in bulk below.
                count_results[selection_name] = df_selected_base.Count()
        else:
            df_selected_base = df

        # Assign event weight based on data taking year and process type
        systematics = produce_systematics(year, suffix)

        # Point the flavour-tagging terms at the recomputed columns, if we are using an
        # alternate SF file (no-op when flavtag_weight_branch is the stored branch name).
        systematics = {name: flavTagWeightPlugin.remap_expression(expr, flavtag_weight_branch)
                       for name, expr in systematics.items()}

        active_systs = _active_systematics(systematics, do_systematics, infile)

        weight_column = f"weight_{selection_name}"
        if not is_data:
            nominal_weight = assign_event_weight(year, infile, suffix, flavtag_weight_branch=flavtag_weight_branch)
            #if "dps" in infile:
            #    nominal_weight = nominal_weight + "*4.52"
            print(f"Event weight: {nominal_weight}")
            # Vary() requires the varied values to share the base column's
            # type; the weight formulas mix float branches so the inferred
            # type can come out as float, while the Vary expression below is
            # built as ROOT::RVecD (double) -- force double here to match.
            df_weighted = df_selected_base.Define(weight_column, f"double({nominal_weight})")
        else:
            df_weighted = df_selected_base.Define(weight_column, "1.")  # Set collision data weight to 1

        vary_expr = None
        if active_systs:
            if is_data:
                # Data weight is always 1 regardless of "systematic" -- this
                # keeps every systematic-named histogram numerically
                # identical to nominal, matching hdumper.py's existing
                # behavior, just computed as one batched Vary() instead of
                # N separate Define+Histo1D passes.
                vary_expr = "ROOT::RVecD{" + ",".join(["1."] * len(active_systs)) + "}"
            else:
                def _syst_weight(syst):
                    w = assign_event_weight(year, infile, suffix, systematics[syst], flavtag_weight_branch=flavtag_weight_branch)
                    #if "dps" in infile:
                    #    w = w + "*4.52"
                    return w
                vary_expr = "ROOT::RVecD{" + ",".join(_syst_weight(syst) for syst in active_systs) + "}"

        print(f"Applying selection: {Fore.GREEN}{selection_name}{Style.RESET_ALL}")

        # Vary() once per selection and reuse the same varied node for the
        # Sum() booking and (outside --eventClassification) every histogram
        # booking too: calling .Vary() again with identical arguments builds
        # a second, functionally-redundant clone-generating node that still
        # needs its own JIT compile of the same ~140-entry expression.
        dfv = df_weighted.Vary(weight_column, vary_expr, active_systs, VARIATION_NAME) if active_systs else df_weighted

        if not is_data and not "base" in selection_name:
            sum_bookings[selection_name] = (dfv.Sum(weight_column), active_systs)

        # Create histograms for each branch. In --eventClassification mode
        # each branch needs its own Filter before the weight column can be
        # read, so each branch still needs its own Vary() call (B calls
        # instead of B*N_systematics); otherwise every branch shares the
        # exact same Vary()'d weighted node as the Sum() above (1 call total
        # for the whole selection, covering Sum() and every branch).
        if eventClassification:
            for hist_config in hist_configs:
                branch_name = hist_config['branch']
                print(f"Creating histogram for branch: {branch_name}")
                branch_df = df_weighted.Filter(adhoc_selection[branch_name])
                if active_systs:
                    branch_df = branch_df.Vary(weight_column, vary_expr, active_systs, VARIATION_NAME)
                hist_name = f"h_{branch_name}"
                hist_bookings[(selection_name, branch_name)] = (
                    branch_df.Histo1D((hist_name, f"Histogram of {branch_name}",
                                        len(adhoc_binning[branch_name]) - 1, adhoc_binning[branch_name]),
                                       branch_name, weight_column),
                    active_systs, hist_name)
        else:
            for hist_config in hist_configs:
                branch_name = hist_config['branch']
                nbins = int(hist_config['nbins'])
                xmin = float(hist_config['xmin'])
                xmax = float(hist_config['xmax'])
                print(f"Creating histogram for branch: {branch_name}")
                hist_name = f"h_{branch_name}"
                hist_bookings[(selection_name, branch_name)] = (
                    dfv.Histo1D((hist_name, f"Histogram of {branch_name}", nbins, xmin, xmax),
                                branch_name, weight_column),
                    active_systs, hist_name)

    # Materializing histograms + the deferred Sum/Count/VariationsFor actions
    # together: none of them were triggered above, so RDataFrame runs this as
    # a single event loop over the tree instead of one loop per booking.
    n_total_hists = sum(1 + len(active_systs) for _, active_systs, _ in hist_bookings.values())
    print(f"Materializing {len(hist_bookings)} histogram bookings ({n_total_hists} histograms total), "
          f"{len(sum_bookings)} event-count sum bookings, {len(count_results)} event counts...")

    materialized_hists = {}
    for (selection_name, branch_name), (hist_lazy, active_systs, hist_name) in hist_bookings.items():
        if active_systs:
            varied = ROOT.RDF.Experimental.VariationsFor(hist_lazy)
            materialized_hists[(branch_name, selection_name, "None")] = add_overflow_underflow(varied["nominal"])
            for syst in active_systs:
                h = varied[f"{VARIATION_NAME}:{syst}"]
                h.SetName(f"{hist_name}_{syst}")  # VariationsFor() names these "<name>_<variationName>_<tag>" by default
                materialized_hists[(branch_name, selection_name, syst)] = add_overflow_underflow(h)
        else:
            materialized_hists[(branch_name, selection_name, "None")] = add_overflow_underflow(hist_lazy.GetPtr())

    for selection_name, count_lazy in count_results.items():
        print(f"Events passing additional ttbar selection ({selection_name}): {count_lazy.GetValue()}")

    for selection_name, (sum_lazy, active_systs) in sum_bookings.items():
        if active_systs:
            varied = ROOT.RDF.Experimental.VariationsFor(sum_lazy)
            local_total_MC_events += varied["nominal"]
            local_events_in_category[selection_name] += varied["nominal"]
            for syst in active_systs:
                n_events = varied[f"{VARIATION_NAME}:{syst}"]
                local_total_MC_events += n_events
                local_events_in_category[selection_name] += n_events
        else:
            n_events = sum_lazy.GetValue()
            local_total_MC_events += n_events
            local_events_in_category[selection_name] += n_events

    output_file_handles = {}
    for key, hist in materialized_hists.items():
        branch_name, selection_name, syst = key
        tt_outfile_name = outfile.replace('.root', '_' + selection_name + '.root')
        output_file = tt_outfile_name if not "base" in selection_name else outfile

        if output_file not in output_file_handles:
            output_file_handles[output_file] = ROOT.TFile(output_file, "RECREATE")

        output_file_handles[output_file].cd()
        hist.Write()

    # Close all files
    for fOut in output_file_handles.values():
        fOut.Close()

    input_file.Close()
    print(f"{Fore.GREEN}Completed processing {infile}{Style.RESET_ALL}")

    return (local_total_MC_events, local_events_in_category)


def process_trees_parallel(input_files, output_files, tree_name, hist_configs, year, selections, eventClassification, use5FS, count_events, do_systematics, flavtag_sf_json=None, flavtag_sf_name=None):
    """
    Basically a wrapper of process_tree to process multiple TTrees in parallel.
    """

    process_func = partial(
        process_tree,
        tree_name=tree_name,
        hist_configs=hist_configs,
        year=year,
        selections=selections,
        eventClassification=eventClassification,
        use5FS=use5FS,
        count_events=count_events,
        do_systematics=do_systematics,
        flavtag_sf_json=flavtag_sf_json,
        flavtag_sf_name=flavtag_sf_name
    )

    with mp.Pool(processes=min(len(input_files), mp.cpu_count())) as pool:
        results = pool.starmap(process_func, zip(input_files, output_files))

    # Aggregate results from all processes
    total_MC_events = 0
    events_in_category = {key: 0 for key in selections.keys() if not key == "base"}

    for local_total, local_category in results:
        total_MC_events += local_total
        for category, count in local_category.items():
            events_in_category[category] += count

    return (total_MC_events, events_in_category)

def read_csv(csv_file):
    """
    Open and read a csv file containing the name and the range of the variables to be plotted.
    Fill in a list of dictionaries containing branch (i.e., variable name), nbins, xmin, and xmax information.

    Parameters:
    - csv_file: The csv file containing variable names and binning for the respective histograms.
    """
    with open(csv_file, mode = 'r') as f:
        csv_reader = csv.reader(f)
        dict_list = [
            {'branch': line[0], 'nbins': line[1], 'xmin': line[2], 'xmax': line[3]}
            for line in csv_reader if not line[0] == 'Variable'
        ]
    # Note: the csv file must NOT contain empty lines.

    return dict_list

def assign_event_weight(year, infile, suffix, syst="", flavtag_weight_branch="flavTagWeight"):
    """
    Define the MC event weight according to the year. Collision data should be handled separately.

    Parameters:
    - year: Data taking year.
    - infile: Input file.
    - flavtag_weight_branch: Name of the branch/column to use for the flavour-tagging
      weight term (defaults to the "flavTagWeight" branch stored in the ntuple; pass
      the column added by flavTagWeightPlugin.define_flavtag_weight to use a weight
      recomputed on the fly from an alternate correctionlib SF file instead).
    """
    weight = "1"
    if year == 2024 or year == 2025:
        weight = f"lumiwgt*genWeight*xsecWeight*puWeight*muEffWeight*elEffWeight*{flavtag_weight_branch}*(((abs(lep1_pdgId)==11 && passTrigEl) || (abs(lep1_pdgId)==13 && passTrigMu)) && passmetfilters)"
    if "ttbar" in infile or "4f" in infile or "tt-vcb" in infile:
        weight = f"{weight}*TopPtWeight[1]*TopPtWeightNorm{suffix}[1]*TOPMLWeight[5]*TOPMLWeightNorm{suffix}[5]" # New variables in custom samples

    if not syst == "":
        weight = f"{weight}*{syst}"

    return weight

def prepare_output(output_dir, input_files):
    """
    Prepare the output file names based on the input file names.

    Parameters:
    - output_dir: Output directory for the new ROOT files.
    - input_files: List of input ROOT files.
    """
    os.makedirs(output_dir, exist_ok=True)
    return [
        f"{output_dir}h_{input_file.split('/')[-1].replace('_tree.root','.root')}"
        for input_file in input_files
    ]

def merge_files(directory, input_files, output_file):
    """
    Merges multiple ROOT files into a single ROOT file.

    Parameters:
    - directory: Directory where the ROOT files are located.
    - input_files: List of input ROOT files.
    - output_file: Output ROOT file.
    """
    if not all([os.path.exists(directory+'/'+infile) for infile in input_files]):
        print(f"Input files {input_files} not found in directory: {directory}")
        return

    hadd_command = f"hadd -f {directory}/{output_file} {' '.join([directory+'/'+infile for infile in input_files])}"
    os.system(hadd_command)
    rm_command = f"rm {' '.join([directory+'/'+infile for infile in input_files])}"
    os.system(rm_command)

def produce_systematics(year, suffix):

    systematics = {"None" : "",
                   #Pileup and lepton efficiencies
                   "CMS_pileup_%sUp"   % year  : "puWeightUp/puWeight",
                   "CMS_pileup_%sDown" % year  : "puWeightDown/puWeight",
                   "CMS_trigEffUp"   : "trigEffWeightUp/trigEffWeight",
                   "CMS_trigEffDown" : "trigEffWeightDown/trigEffWeight",
                   "CMS_muEffUp"     : "muEffWeight_UP/muEffWeight",
                   "CMS_muEffDown"   : "muEffWeight_DOWN/muEffWeight",
                   "CMS_elEffUp"     : "elEffWeight_UP/elEffWeight",
                   "CMS_elEffDown"   : "elEffWeight_DOWN/elEffWeight",
                   "CMS_elSmearUp"   : "elSmear_UP",
                   "CMS_elSmearDown" : "elSmear_DOWN",
                   "CMS_elScaleUp"   : "elScale_UP",
                   "CMS_elScaleDown" : "elScale_DOWN",
                   "CMS_muSmearUp"   : "muSmear_UP",
                   "CMS_muSmearDown" : "muSmear_DOWN",
                   "CMS_muScaleUp"   : "muScale_UP",
                   "CMS_muScaleDown" : "muScale_DOWN",
                   # Flavor tagging
                   "CMS_flavTag_TTWeight_ttbarUp"     : "flavTagWeight_TTWeight_ttbar_UP/flavTagWeight",
                   "CMS_flavTag_TTWeight_ttbarDown"   : "flavTagWeight_TTWeight_ttbar_DOWN/flavTagWeight",
                   "CMS_flavTag_HDamp_ttbarUp"        : "flavTagWeight_HDamp_ttbar_UP/flavTagWeight",
                   "CMS_flavTag_HDamp_ttbarDown"      : "flavTagWeight_HDamp_ttbar_DOWN/flavTagWeight",
                   "CMS_flavTag_BDecay_ttbarUp"       : "flavTagWeight_BDecay_ttbar_UP/flavTagWeight",
                   "CMS_flavTag_BDecay_ttbarDown"     : "flavTagWeight_BDecay_ttbar_DOWN/flavTagWeight",
                   "CMS_flavTag_CDecay_ttbarUp"       : "flavTagWeight_CDecay_ttbar_UP/flavTagWeight",
                   "CMS_flavTag_CDecay_ttbarDown"     : "flavTagWeight_CDecay_ttbar_DOWN/flavTagWeight",
                   "CMS_flavTag_xsec_ttbarUp"         : "flavTagWeight_XSec_ttbar_UP/flavTagWeight",
                   "CMS_flavTag_xsec_ttbarDown"       : "flavTagWeight_XSec_ttbar_DOWN/flavTagWeight",
                   "CMS_flavTag_xsec_wjets_cUp"       : "flavTagWeight_XSec_WJets_c_UP/flavTagWeight",
                   "CMS_flavTag_xsec_wjets_cDown"     : "flavTagWeight_XSec_WJets_c_DOWN/flavTagWeight",
                   "CMS_flavTag_xsec_wjets_bUp"       : "flavTagWeight_XSec_WJets_b_UP/flavTagWeight",
                   "CMS_flavTag_xsec_wjets_bDown"     : "flavTagWeight_XSec_WJets_b_DOWN/flavTagWeight",
                   "CMS_flavTag_xsec_zjets_cUp"       : "flavTagWeight_XSec_ZJets_c_UP/flavTagWeight",
                   "CMS_flavTag_xsec_zjets_cDown"     : "flavTagWeight_XSec_ZJets_c_DOWN/flavTagWeight",
                   "CMS_flavTag_xsec_zjets_bUp"       : "flavTagWeight_XSec_ZJets_b_UP/flavTagWeight",
                   "CMS_flavTag_xsec_zjets_bDown"     : "flavTagWeight_XSec_ZJets_b_DOWN/flavTagWeight",
                   "CMS_flavTag_xsec_singlet_tChUp"   : "flavTagWeight_XSec_singlet_tCh_UP/flavTagWeight",
                   "CMS_flavTag_xsec_singlet_tChDown" : "flavTagWeight_XSec_singlet_tCh_DOWN/flavTagWeight",
                   "CMS_flavTag_xsec_singlet_tWUp"    : "flavTagWeight_XSec_singlet_tW_UP/flavTagWeight",
                   "CMS_flavTag_xsec_singlet_tWDown"  : "flavTagWeight_XSec_singlet_tW_DOWN/flavTagWeight",
                   "CMS_flavTag_xsec_VVUp"            : "flavTagWeight_XSec_VV_UP/flavTagWeight",
                   "CMS_flavTag_xsec_VVDown"          : "flavTagWeight_XSec_VV_DOWN/flavTagWeight",
                   "CMS_flavTag_PU_%sUp"     % year   : "flavTagWeight_PUWeight_UP/flavTagWeight",
                   "CMS_flavTag_PU_%sDown"   % year   : "flavTagWeight_PUWeight_DOWN/flavTagWeight",
                   "CMS_flavTag_Lumi_%sUp"   % year   : "flavTagWeight_Lumi_13p6TeV_%s_UP/flavTagWeight" % year,
                   "CMS_flavTag_Lumi_%sDown" % year   : "flavTagWeight_Lumi_13p6TeV_%s_DOWN/flavTagWeight" % year,
                   "CMS_flavTag_EleRecoUp"            : "flavTagWeight_Ele_Reco_UP/flavTagWeight",
                   "CMS_flavTag_EleRecoDown"          : "flavTagWeight_Ele_Reco_DOWN/flavTagWeight",
                   "CMS_flavTag_EleScaleUp"           : "flavTagWeight_Ele_Scale_UP/flavTagWeight",
                   "CMS_flavTag_EleScaleDown"         : "flavTagWeight_Ele_Scale_DOWN/flavTagWeight",
                   "CMS_flavTag_EleSmearUp"           : "flavTagWeight_Ele_Smear_UP/flavTagWeight",
                   "CMS_flavTag_EleSmearDown"         : "flavTagWeight_Ele_Smear_DOWN/flavTagWeight",
                   "CMS_flavTag_EleIDUp"              : "flavTagWeight_Ele_ID_UP/flavTagWeight",
                   "CMS_flavTag_EleIDDown"            : "flavTagWeight_Ele_ID_DOWN/flavTagWeight",
                   "CMS_flavTag_EleTriggerUp"         : "flavTagWeight_Ele_Trigger_UP/flavTagWeight",
                   "CMS_flavTag_EleTriggerDown"       : "flavTagWeight_Ele_Trigger_DOWN/flavTagWeight",
                   "CMS_flavTag_MuIDUp"               : "flavTagWeight_Mu_ID_UP/flavTagWeight",
                   "CMS_flavTag_MuIDDown"             : "flavTagWeight_Mu_ID_DOWN/flavTagWeight",
                   "CMS_flavTag_MuIsoUp"              : "flavTagWeight_Mu_Iso_UP/flavTagWeight",
                   "CMS_flavTag_MuIsoDown"            : "flavTagWeight_Mu_Iso_DOWN/flavTagWeight",
                   "CMS_flavTag_MuScaleUp"            : "flavTagWeight_Mu_Scale_UP/flavTagWeight",
                   "CMS_flavTag_MuScaleDown"          : "flavTagWeight_Mu_Scale_DOWN/flavTagWeight",
                   "CMS_flavTag_MuResolUp"            : "flavTagWeight_Mu_Resol_UP/flavTagWeight",
                   "CMS_flavTag_MuResolDown"          : "flavTagWeight_Mu_Resol_DOWN/flavTagWeight",
                   "CMS_flavTag_MuTriggerUp"          : "flavTagWeight_Mu_Trigger_UP/flavTagWeight",
                   "CMS_flavTag_MuTriggerDown"        : "flavTagWeight_Mu_Trigger_DOWN/flavTagWeight",
                   "CMS_flavTag_MET_UnclEnergyUp"     : "flavTagWeight_MET_UnclEnergy_UP/flavTagWeight",
                   "CMS_flavTag_MET_UnclEnergyDown"   : "flavTagWeight_MET_UnclEnergy_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavB_C0_%sUp"   % year : "flavTagWeight_Stat_flavB_C0_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavB_C0_%sDown" % year : "flavTagWeight_Stat_flavB_C0_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavB_C1_%sUp"   % year : "flavTagWeight_Stat_flavB_C1_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavB_C1_%sDown" % year : "flavTagWeight_Stat_flavB_C1_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavB_C2_%sUp"   % year : "flavTagWeight_Stat_flavB_C2_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavB_C2_%sDown" % year : "flavTagWeight_Stat_flavB_C2_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavB_C3_%sUp"   % year : "flavTagWeight_Stat_flavB_C3_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavB_C3_%sDown" % year : "flavTagWeight_Stat_flavB_C3_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavB_C4_%sUp"   % year : "flavTagWeight_Stat_flavB_C4_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavB_C4_%sDown" % year : "flavTagWeight_Stat_flavB_C4_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavB_B0_%sUp"   % year : "flavTagWeight_Stat_flavB_B0_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavB_B0_%sDown" % year : "flavTagWeight_Stat_flavB_B0_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavB_B1_%sUp"   % year : "flavTagWeight_Stat_flavB_B1_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavB_B1_%sDown" % year : "flavTagWeight_Stat_flavB_B1_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavB_B2_%sUp"   % year : "flavTagWeight_Stat_flavB_B2_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavB_B2_%sDown" % year : "flavTagWeight_Stat_flavB_B2_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavB_B3_%sUp"   % year : "flavTagWeight_Stat_flavB_B3_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavB_B3_%sDown" % year : "flavTagWeight_Stat_flavB_B3_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavB_B4_%sUp"   % year : "flavTagWeight_Stat_flavB_B4_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavB_B4_%sDown" % year : "flavTagWeight_Stat_flavB_B4_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavC_C0_%sUp"   % year : "flavTagWeight_Stat_flavC_C0_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavC_C0_%sDown" % year : "flavTagWeight_Stat_flavC_C0_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavC_C1_%sUp"   % year : "flavTagWeight_Stat_flavC_C1_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavC_C1_%sDown" % year : "flavTagWeight_Stat_flavC_C1_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavC_C2_%sUp"   % year : "flavTagWeight_Stat_flavC_C2_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavC_C2_%sDown" % year : "flavTagWeight_Stat_flavC_C2_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavC_C3_%sUp"   % year : "flavTagWeight_Stat_flavC_C3_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavC_C3_%sDown" % year : "flavTagWeight_Stat_flavC_C3_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavC_C4_%sUp"   % year : "flavTagWeight_Stat_flavC_C4_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavC_C4_%sDown" % year : "flavTagWeight_Stat_flavC_C4_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavC_B0_%sUp"   % year : "flavTagWeight_Stat_flavC_B0_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavC_B0_%sDown" % year : "flavTagWeight_Stat_flavC_B0_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavC_B1_%sUp"   % year : "flavTagWeight_Stat_flavC_B1_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavC_B1_%sDown" % year : "flavTagWeight_Stat_flavC_B1_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavC_B2_%sUp"   % year : "flavTagWeight_Stat_flavC_B2_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavC_B2_%sDown" % year : "flavTagWeight_Stat_flavC_B2_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavC_B3_%sUp"   % year : "flavTagWeight_Stat_flavC_B3_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavC_B3_%sDown" % year : "flavTagWeight_Stat_flavC_B3_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavC_B4_%sUp"   % year : "flavTagWeight_Stat_flavC_B4_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavC_B4_%sDown" % year : "flavTagWeight_Stat_flavC_B4_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavL_C0_%sUp"   % year : "flavTagWeight_Stat_flavL_C0_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavL_C0_%sDown" % year : "flavTagWeight_Stat_flavL_C0_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavL_C1_%sUp"   % year : "flavTagWeight_Stat_flavL_C1_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavL_C1_%sDown" % year : "flavTagWeight_Stat_flavL_C1_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavL_C2_%sUp"   % year : "flavTagWeight_Stat_flavL_C2_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavL_C2_%sDown" % year : "flavTagWeight_Stat_flavL_C2_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavL_C3_%sUp"   % year : "flavTagWeight_Stat_flavL_C3_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavL_C3_%sDown" % year : "flavTagWeight_Stat_flavL_C3_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavL_C4_%sUp"   % year : "flavTagWeight_Stat_flavL_C4_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavL_C4_%sDown" % year : "flavTagWeight_Stat_flavL_C4_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavL_B0_%sUp"   % year : "flavTagWeight_Stat_flavL_B0_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavL_B0_%sDown" % year : "flavTagWeight_Stat_flavL_B0_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavL_B1_%sUp"   % year : "flavTagWeight_Stat_flavL_B1_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavL_B1_%sDown" % year : "flavTagWeight_Stat_flavL_B1_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavL_B2_%sUp"   % year : "flavTagWeight_Stat_flavL_B2_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavL_B2_%sDown" % year : "flavTagWeight_Stat_flavL_B2_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavL_B3_%sUp"   % year : "flavTagWeight_Stat_flavL_B3_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavL_B3_%sDown" % year : "flavTagWeight_Stat_flavL_B3_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavL_B4_%sUp"   % year : "flavTagWeight_Stat_flavL_B4_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavL_B4_%sDown" % year : "flavTagWeight_Stat_flavL_B4_DOWN/flavTagWeight",
                   "CMS_flavTag_LHE_muF_ttbarUp"     : "flavTagWeight_LHEScaleWeight_muF_ttbar_UP/flavTagWeight",
                   "CMS_flavTag_LHE_muF_ttbarDown"   : "flavTagWeight_LHEScaleWeight_muF_ttbar_DOWN/flavTagWeight",
                   "CMS_flavTag_LHE_muR_ttbarUp"     : "flavTagWeight_LHEScaleWeight_muR_ttbar_UP/flavTagWeight",
                   "CMS_flavTag_LHE_muR_ttbarDown"   : "flavTagWeight_LHEScaleWeight_muR_ttbar_DOWN/flavTagWeight",
                   "CMS_flavTag_LHE_muF_singletUp"   : "flavTagWeight_LHEScaleWeight_muF_singlet_UP/flavTagWeight",
                   "CMS_flavTag_LHE_muF_singletDown" : "flavTagWeight_LHEScaleWeight_muF_singlet_DOWN/flavTagWeight",
                   "CMS_flavTag_LHE_muR_singletUp"   : "flavTagWeight_LHEScaleWeight_muR_singlet_UP/flavTagWeight",
                   "CMS_flavTag_LHE_muR_singletDown" : "flavTagWeight_LHEScaleWeight_muR_singlet_DOWN/flavTagWeight",
                   "CMS_flavTag_LHE_muF_wjetsUp"     : "flavTagWeight_LHEScaleWeight_muF_wjets_UP/flavTagWeight",
                   "CMS_flavTag_LHE_muF_wjetsDown"   : "flavTagWeight_LHEScaleWeight_muF_wjets_DOWN/flavTagWeight",
                   "CMS_flavTag_LHE_muR_wjetsUp"     : "flavTagWeight_LHEScaleWeight_muR_wjets_UP/flavTagWeight",
                   "CMS_flavTag_LHE_muR_wjetsDown"   : "flavTagWeight_LHEScaleWeight_muR_wjets_DOWN/flavTagWeight",
                   "CMS_flavTag_LHE_muF_zjetsUp"     : "flavTagWeight_LHEScaleWeight_muF_zjets_UP/flavTagWeight",
                   "CMS_flavTag_LHE_muF_zjetsDown"   : "flavTagWeight_LHEScaleWeight_muF_zjets_DOWN/flavTagWeight",
                   "CMS_flavTag_LHE_muR_zjetsUp"     : "flavTagWeight_LHEScaleWeight_muR_zjets_UP/flavTagWeight",
                   "CMS_flavTag_LHE_muR_zjetsDown"   : "flavTagWeight_LHEScaleWeight_muR_zjets_DOWN/flavTagWeight",
                   "CMS_flavTag_LHE_muF_dibosonUp"   : "flavTagWeight_LHEScaleWeight_muF_diboson_UP/flavTagWeight",
                   "CMS_flavTag_LHE_muF_dibosonDown" : "flavTagWeight_LHEScaleWeight_muF_diboson_DOWN/flavTagWeight",
                   "CMS_flavTag_LHE_muR_dibosonUp"   : "flavTagWeight_LHEScaleWeight_muR_diboson_UP/flavTagWeight",
                   "CMS_flavTag_LHE_muR_dibosonDown" : "flavTagWeight_LHEScaleWeight_muR_diboson_DOWN/flavTagWeight",
                   "CMS_flavTag_LHE_PDF_ttbarUp"     : "flavTagWeight_LHEScaleWeight_PDF_ttbar_UP/flavTagWeight",
                   "CMS_flavTag_LHE_PDF_ttbarDown"   : "flavTagWeight_LHEScaleWeight_PDF_ttbar_DOWN/flavTagWeight",
                   "CMS_flavTag_LHE_PDF_singletUp"   : "flavTagWeight_LHEScaleWeight_PDF_singlet_UP/flavTagWeight",
                   "CMS_flavTag_LHE_PDF_singletDown" : "flavTagWeight_LHEScaleWeight_PDF_singlet_DOWN/flavTagWeight",
                   "CMS_flavTag_LHE_PDF_wjetsUp"     : "flavTagWeight_LHEScaleWeight_PDF_wjets_UP/flavTagWeight",
                   "CMS_flavTag_LHE_PDF_wjetsDown"   : "flavTagWeight_LHEScaleWeight_PDF_wjets_DOWN/flavTagWeight",
                   "CMS_flavTag_LHE_PDF_zjetsUp"     : "flavTagWeight_LHEScaleWeight_PDF_zjets_UP/flavTagWeight",
                   "CMS_flavTag_LHE_PDF_zjetsDown"   : "flavTagWeight_LHEScaleWeight_PDF_zjets_DOWN/flavTagWeight",
                   "CMS_flavTag_LHE_PDF_dibosonUp"   : "flavTagWeight_LHEScaleWeight_PDF_diboson_UP/flavTagWeight",
                   "CMS_flavTag_LHE_PDF_dibosonDown" : "flavTagWeight_LHEScaleWeight_PDF_diboson_DOWN/flavTagWeight",
                   "CMS_flavTag_LHE_aS_ttbarUp"      : "flavTagWeight_LHEScaleWeight_aS_ttbar_UP/flavTagWeight",
                   "CMS_flavTag_LHE_aS_ttbarDown"    : "flavTagWeight_LHEScaleWeight_aS_ttbar_DOWN/flavTagWeight",
                   "CMS_flavTag_LHE_aS_singletUp"    : "flavTagWeight_LHEScaleWeight_aS_singlet_UP/flavTagWeight",
                   "CMS_flavTag_LHE_aS_singletDown"  : "flavTagWeight_LHEScaleWeight_aS_singlet_DOWN/flavTagWeight",
                   "CMS_flavTag_LHE_aS_wjetsUp"      : "flavTagWeight_LHEScaleWeight_aS_wjets_UP/flavTagWeight",
                   "CMS_flavTag_LHE_aS_wjetsDown"    : "flavTagWeight_LHEScaleWeight_aS_wjets_DOWN/flavTagWeight",
                   "CMS_flavTag_LHE_aS_zjetsUp"      : "flavTagWeight_LHEScaleWeight_aS_zjets_UP/flavTagWeight",
                   "CMS_flavTag_LHE_aS_zjetsDown"    : "flavTagWeight_LHEScaleWeight_aS_zjets_DOWN/flavTagWeight",
                   "CMS_flavTag_LHE_aS_dibosonUp"    : "flavTagWeight_LHEScaleWeight_aS_diboson_UP/flavTagWeight",
                   "CMS_flavTag_LHE_aS_dibosonDown"  : "flavTagWeight_LHEScaleWeight_aS_diboson_DOWN/flavTagWeight",
                   "CMS_flavTag_PS_ISR_ttbarUp"      : "flavTagWeight_PSWeightISR_ttbar_UP/flavTagWeight",
                   "CMS_flavTag_PS_ISR_ttbarDown"    : "flavTagWeight_PSWeightISR_ttbar_DOWN/flavTagWeight",
                   "CMS_flavTag_PS_FSR_ttbarUp"      : "flavTagWeight_PSWeightFSR_ttbar_UP/flavTagWeight",
                   "CMS_flavTag_PS_FSR_ttbarDown"    : "flavTagWeight_PSWeightFSR_ttbar_DOWN/flavTagWeight",
                   "CMS_flavTag_PS_ISR_singletUp"    : "flavTagWeight_PSWeightISR_singlet_UP/flavTagWeight",
                   "CMS_flavTag_PS_ISR_singletDown"  : "flavTagWeight_PSWeightISR_singlet_DOWN/flavTagWeight",
                   "CMS_flavTag_PS_FSR_singletUp"    : "flavTagWeight_PSWeightFSR_singlet_UP/flavTagWeight",
                   "CMS_flavTag_PS_FSR_singletDown"  : "flavTagWeight_PSWeightFSR_singlet_DOWN/flavTagWeight",
                   "CMS_flavTag_PS_ISR_wjetsUp"      : "flavTagWeight_PSWeightISR_wjets_UP/flavTagWeight",
                   "CMS_flavTag_PS_ISR_wjetsDown"    : "flavTagWeight_PSWeightISR_wjets_DOWN/flavTagWeight",
                   "CMS_flavTag_PS_FSR_wjetsUp"      : "flavTagWeight_PSWeightFSR_wjets_UP/flavTagWeight",
                   "CMS_flavTag_PS_FSR_wjetsDown"    : "flavTagWeight_PSWeightFSR_wjets_DOWN/flavTagWeight",
                   "CMS_flavTag_PS_ISR_zjetsUp"      : "flavTagWeight_PSWeightISR_zjets_UP/flavTagWeight",
                   "CMS_flavTag_PS_ISR_zjetsDown"    : "flavTagWeight_PSWeightISR_zjets_DOWN/flavTagWeight",
                   "CMS_flavTag_PS_FSR_zjetsUp"      : "flavTagWeight_PSWeightFSR_zjets_UP/flavTagWeight",
                   "CMS_flavTag_PS_FSR_zjetsDown"    : "flavTagWeight_PSWeightFSR_zjets_DOWN/flavTagWeight",
                   "CMS_flavTag_PS_ISR_dibosonUp"    : "flavTagWeight_PSWeightISR_diboson_UP/flavTagWeight",
                   "CMS_flavTag_PS_ISR_dibosonDown"  : "flavTagWeight_PSWeightISR_diboson_DOWN/flavTagWeight",
                   "CMS_flavTag_PS_FSR_dibosonUp"    : "flavTagWeight_PSWeightFSR_diboson_UP/flavTagWeight",
                   "CMS_flavTag_PS_FSR_dibosonDown"  : "flavTagWeight_PSWeightFSR_diboson_DOWN/flavTagWeight",
                   "CMS_flavTag_JES_AbsoluteUp"      : "flavTagWeight_JESRegrouped_Absolute_UP/flavTagWeight",
                   "CMS_flavTag_JES_AbsoluteDown"    : "flavTagWeight_JESRegrouped_Absolute_DOWN/flavTagWeight",
                   "CMS_flavTag_JES_BBEC1Up"         : "flavTagWeight_JESRegrouped_BBEC1_UP/flavTagWeight",
                   "CMS_flavTag_JES_BBEC1Down"       : "flavTagWeight_JESRegrouped_BBEC1_DOWN/flavTagWeight",
                   "CMS_flavTag_JES_FlavorQCDUp"     : "flavTagWeight_JESRegrouped_FlavorQCD_UP/flavTagWeight",
                   "CMS_flavTag_JES_FlavorQCDDown"   : "flavTagWeight_JESRegrouped_FlavorQCD_DOWN/flavTagWeight",
                   "CMS_flavTag_JES_RelativeBalUp"   : "flavTagWeight_JESRegrouped_RelativeBal_UP/flavTagWeight",
                   "CMS_flavTag_JES_RelativeBalDown" : "flavTagWeight_JESRegrouped_RelativeBal_DOWN/flavTagWeight",
                   "CMS_flavTag_JES_Absolute_%sUp"   % year : "flavTagWeight_JESRegrouped_Absolute_%s_UP/flavTagWeight" % year,
                   "CMS_flavTag_JES_Absolute_%sDown" % year : "flavTagWeight_JESRegrouped_Absolute_%s_DOWN/flavTagWeight" % year,
                   "CMS_flavTag_JES_BBEC1_%sUp"      % year : "flavTagWeight_JESRegrouped_BBEC1_%s_UP/flavTagWeight" % year,
                   "CMS_flavTag_JES_BBEC1_%sDown"    % year : "flavTagWeight_JESRegrouped_BBEC1_%s_DOWN/flavTagWeight" % year,
                   "CMS_flavTag_JES_RelativeSample_%sUp"   % year : "flavTagWeight_JESRegrouped_RelativeSample_%s_UP/flavTagWeight" % year,
                   "CMS_flavTag_JES_RelativeSample_%sDown" % year : "flavTagWeight_JESRegrouped_RelativeSample_%s_DOWN/flavTagWeight" % year,
                   "CMS_flavTag_JEReta0to1p93_%sUp"   % year : "flavTagWeight_JEReta0to1p93_UP/flavTagWeight",
                   "CMS_flavTag_JEReta0to1p93_%sDown" % year : "flavTagWeight_JEReta0to1p93_DOWN/flavTagWeight",
                   "CMS_flavTag_JEReta1p93to2p5_%sUp"   % year : "flavTagWeight_JEReta1p93to2p5_UP/flavTagWeight",
                   "CMS_flavTag_JEReta1p93to2p5_%sDown" % year : "flavTagWeight_JEReta1p93to2p5_DOWN/flavTagWeight",
                   # Hdamp, b fragmentation, LHE scale, PS weights
                   "topHdampWeight_%sUp"   % year : f"TOPMLWeight[1]*TOPMLWeightNorm{suffix}[1]",
                   "topHdampWeight_%sDown" % year : f"TOPMLWeight[3]*TOPMLWeightNorm{suffix}[3]",
                   "bFragWeight_%sUp"   % year : f"(TOPMLWeight[4]*TOPMLWeightNorm{suffix}[4])/(TOPMLWeight[5]*TOPMLWeightNorm{suffix}[5])", # Divide by bFrag nominal and multiply by bFrag up
                   "bFragWeight_%sDown" % year : f"1/(TOPMLWeight[5]*TOPMLWeightNorm{suffix}[5])", # The standard samples are effectively bFrag down, so here just dividing by bFrag nominal and its renorm weight
                   "bFragPetersonWeight_%sUp"   % year : f"(bFragAndDecayWeight[3]*BFragAndDecayWeightNorm{suffix}[3])/(TOPMLWeight[5]*TOPMLWeightNorm{suffix}[5])", # A one-sided systematic
                   "bFragPetersonWeight_%sDown" % year : f"1.", # Effectively a one-sided systematic
                   # LHE scale for minor bkgs
                   # "LHE_minorBkg_muF_%sUp" % year : "LHEScaleWeight[5]*LHEScaleWeightNorm[5]",
                   # "LHE_minorBkg_muF_%sDown" % year : "LHEScaleWeight[3]*LHEScaleWeightNorm[3]",
                   # "LHE_minorBkg_muR_%sUp" % year : "LHEScaleWeight[7]*LHEScaleWeightNorm[7]",
                   # "LHE_minorBkg_muR_%sDown" % year : "LHEScaleWeight[1]*LHEScaleWeightNorm[1]",
                   # LHE scale for large bkgs
                   "LHE_muF_%sUp"   % year : f"LHEScaleWeight[5]*LHEScaleWeightNorm{suffix}[5]",
                   "LHE_muF_%sDown" % year : f"LHEScaleWeight[3]*LHEScaleWeightNorm{suffix}[3]",
                   "LHE_muR_%sUp"   % year : f"LHEScaleWeight[7]*LHEScaleWeightNorm{suffix}[7]",
                   "LHE_muR_%sDown" % year : f"LHEScaleWeight[1]*LHEScaleWeightNorm{suffix}[1]",
                   # LHE PDF
                   "LHE_PDF_1_%sUp" % year : f"LHEPdfWeight[1]*LHEPdfWeightNorm{suffix}[1]",
                   "LHE_PDF_1_%sDown" % year : f"LHEPdfWeight[2]*LHEPdfWeightNorm{suffix}[2]",
                   "LHE_PDF_2_%sUp" % year : f"LHEPdfWeight[3]*LHEPdfWeightNorm{suffix}[3]",
                   "LHE_PDF_2_%sDown" % year : f"LHEPdfWeight[4]*LHEPdfWeightNorm{suffix}[4]",
                   "LHE_PDF_3_%sUp" % year : f"LHEPdfWeight[5]*LHEPdfWeightNorm{suffix}[5]",
                   "LHE_PDF_3_%sDown" % year : f"LHEPdfWeight[6]*LHEPdfWeightNorm{suffix}[6]",
                   "LHE_PDF_4_%sUp" % year : f"LHEPdfWeight[7]*LHEPdfWeightNorm{suffix}[7]",
                   "LHE_PDF_4_%sDown" % year : f"LHEPdfWeight[8]*LHEPdfWeightNorm{suffix}[8]",
                   "LHE_PDF_5_%sUp" % year : f"LHEPdfWeight[9]*LHEPdfWeightNorm{suffix}[9]",
                   "LHE_PDF_5_%sDown" % year : f"LHEPdfWeight[10]*LHEPdfWeightNorm{suffix}[10]",
                   "LHE_PDF_6_%sUp" % year : f"LHEPdfWeight[11]*LHEPdfWeightNorm{suffix}[11]",
                   "LHE_PDF_6_%sDown" % year : f"LHEPdfWeight[12]*LHEPdfWeightNorm{suffix}[12]",
                   "LHE_PDF_7_%sUp" % year : f"LHEPdfWeight[13]*LHEPdfWeightNorm{suffix}[13]",
                   "LHE_PDF_7_%sDown" % year : f"LHEPdfWeight[14]*LHEPdfWeightNorm{suffix}[14]",
                   "LHE_PDF_8_%sUp" % year : f"LHEPdfWeight[15]*LHEPdfWeightNorm{suffix}[15]",
                   "LHE_PDF_8_%sDown" % year : f"LHEPdfWeight[16]*LHEPdfWeightNorm{suffix}[16]",
                   "LHE_PDF_9_%sUp" % year : f"LHEPdfWeight[17]*LHEPdfWeightNorm{suffix}[17]",
                   "LHE_PDF_9_%sDown" % year : f"LHEPdfWeight[18]*LHEPdfWeightNorm{suffix}[18]",
                   "LHE_PDF_10_%sUp" % year : f"LHEPdfWeight[19]*LHEPdfWeightNorm{suffix}[19]",
                   "LHE_PDF_10_%sDown" % year : f"LHEPdfWeight[20]*LHEPdfWeightNorm{suffix}[20]",
                   "LHE_PDF_11_%sUp" % year : f"LHEPdfWeight[21]*LHEPdfWeightNorm{suffix}[21]",
                   "LHE_PDF_11_%sDown" % year : f"LHEPdfWeight[22]*LHEPdfWeightNorm{suffix}[22]",
                   "LHE_PDF_12_%sUp" % year : f"LHEPdfWeight[23]*LHEPdfWeightNorm{suffix}[23]",
                   "LHE_PDF_12_%sDown" % year : f"LHEPdfWeight[24]*LHEPdfWeightNorm{suffix}[24]",
                   "LHE_PDF_13_%sUp" % year : f"LHEPdfWeight[25]*LHEPdfWeightNorm{suffix}[25]",
                   "LHE_PDF_13_%sDown" % year : f"LHEPdfWeight[26]*LHEPdfWeightNorm{suffix}[26]",
                   "LHE_PDF_14_%sUp" % year : f"LHEPdfWeight[27]*LHEPdfWeightNorm{suffix}[27]",
                   "LHE_PDF_14_%sDown" % year : f"LHEPdfWeight[28]*LHEPdfWeightNorm{suffix}[28]",
                   "LHE_PDF_15_%sUp" % year : f"LHEPdfWeight[29]*LHEPdfWeightNorm{suffix}[29]",
                   "LHE_PDF_15_%sDown" % year : f"LHEPdfWeight[30]*LHEPdfWeightNorm{suffix}[30]",
                   "LHE_PDF_16_%sUp" % year : f"LHEPdfWeight[31]*LHEPdfWeightNorm{suffix}[31]",
                   "LHE_PDF_16_%sDown" % year : f"LHEPdfWeight[32]*LHEPdfWeightNorm{suffix}[32]",
                   "LHE_PDF_17_%sUp" % year : f"LHEPdfWeight[33]*LHEPdfWeightNorm{suffix}[33]",
                   "LHE_PDF_17_%sDown" % year : f"LHEPdfWeight[34]*LHEPdfWeightNorm{suffix}[34]",
                   "LHE_PDF_18_%sUp" % year : f"LHEPdfWeight[35]*LHEPdfWeightNorm{suffix}[35]",
                   "LHE_PDF_18_%sDown" % year : f"LHEPdfWeight[36]*LHEPdfWeightNorm{suffix}[36]",
                   "LHE_PDF_19_%sUp" % year : f"LHEPdfWeight[37]*LHEPdfWeightNorm{suffix}[37]",
                   "LHE_PDF_19_%sDown" % year : f"LHEPdfWeight[38]*LHEPdfWeightNorm{suffix}[38]",
                   "LHE_PDF_20_%sUp" % year : f"LHEPdfWeight[39]*LHEPdfWeightNorm{suffix}[39]",
                   "LHE_PDF_20_%sDown" % year : f"LHEPdfWeight[40]*LHEPdfWeightNorm{suffix}[40]",
                   "LHE_PDF_21_%sUp" % year : f"LHEPdfWeight[41]*LHEPdfWeightNorm{suffix}[41]",
                   "LHE_PDF_21_%sDown" % year : f"LHEPdfWeight[42]*LHEPdfWeightNorm{suffix}[42]",
                   "LHE_PDF_22_%sUp" % year : f"LHEPdfWeight[43]*LHEPdfWeightNorm{suffix}[43]",
                   "LHE_PDF_22_%sDown" % year : f"LHEPdfWeight[44]*LHEPdfWeightNorm{suffix}[44]",
                   "LHE_PDF_23_%sUp" % year : f"LHEPdfWeight[45]*LHEPdfWeightNorm{suffix}[45]",
                   "LHE_PDF_23_%sDown" % year : f"LHEPdfWeight[46]*LHEPdfWeightNorm{suffix}[46]",
                   "LHE_PDF_24_%sUp" % year : f"LHEPdfWeight[47]*LHEPdfWeightNorm{suffix}[47]",
                   "LHE_PDF_24_%sDown" % year : f"LHEPdfWeight[48]*LHEPdfWeightNorm{suffix}[48]",
                   "LHE_PDF_25_%sUp" % year : f"LHEPdfWeight[49]*LHEPdfWeightNorm{suffix}[49]",
                   "LHE_PDF_25_%sDown" % year : f"LHEPdfWeight[50]*LHEPdfWeightNorm{suffix}[50]",
                   "LHE_PDF_26_%sUp" % year : f"LHEPdfWeight[51]*LHEPdfWeightNorm{suffix}[51]",
                   "LHE_PDF_26_%sDown" % year : f"LHEPdfWeight[52]*LHEPdfWeightNorm{suffix}[52]",
                   "LHE_PDF_27_%sUp" % year : f"LHEPdfWeight[53]*LHEPdfWeightNorm{suffix}[53]",
                   "LHE_PDF_27_%sDown" % year : f"LHEPdfWeight[54]*LHEPdfWeightNorm{suffix}[54]",
                   "LHE_PDF_28_%sUp" % year : f"LHEPdfWeight[55]*LHEPdfWeightNorm{suffix}[55]",
                   "LHE_PDF_28_%sDown" % year : f"LHEPdfWeight[56]*LHEPdfWeightNorm{suffix}[56]",
                   "LHE_PDF_29_%sUp" % year : f"LHEPdfWeight[57]*LHEPdfWeightNorm{suffix}[57]",
                   "LHE_PDF_29_%sDown" % year : f"LHEPdfWeight[58]*LHEPdfWeightNorm{suffix}[58]",
                   "LHE_PDF_30_%sUp" % year : f"LHEPdfWeight[59]*LHEPdfWeightNorm{suffix}[59]",
                   "LHE_PDF_30_%sDown" % year : f"LHEPdfWeight[60]*LHEPdfWeightNorm{suffix}[60]",
                   "LHE_PDF_31_%sUp" % year : f"LHEPdfWeight[61]*LHEPdfWeightNorm{suffix}[61]",
                   "LHE_PDF_31_%sDown" % year : f"LHEPdfWeight[62]*LHEPdfWeightNorm{suffix}[62]",
                   "LHE_PDF_32_%sUp" % year : f"LHEPdfWeight[63]*LHEPdfWeightNorm{suffix}[63]",
                   "LHE_PDF_32_%sDown" % year : f"LHEPdfWeight[64]*LHEPdfWeightNorm{suffix}[64]",
                   "LHE_PDF_33_%sUp" % year : f"LHEPdfWeight[65]*LHEPdfWeightNorm{suffix}[65]",
                   "LHE_PDF_33_%sDown" % year : f"LHEPdfWeight[66]*LHEPdfWeightNorm{suffix}[66]",
                   "LHE_PDF_34_%sUp" % year : f"LHEPdfWeight[67]*LHEPdfWeightNorm{suffix}[67]",
                   "LHE_PDF_34_%sDown" % year : f"LHEPdfWeight[68]*LHEPdfWeightNorm{suffix}[68]",
                   "LHE_PDF_35_%sUp" % year : f"LHEPdfWeight[69]*LHEPdfWeightNorm{suffix}[69]",
                   "LHE_PDF_35_%sDown" % year : f"LHEPdfWeight[70]*LHEPdfWeightNorm{suffix}[70]",
                   "LHE_PDF_36_%sUp" % year : f"LHEPdfWeight[71]*LHEPdfWeightNorm{suffix}[71]",
                   "LHE_PDF_36_%sDown" % year : f"LHEPdfWeight[72]*LHEPdfWeightNorm{suffix}[72]",
                   "LHE_PDF_37_%sUp" % year : f"LHEPdfWeight[73]*LHEPdfWeightNorm{suffix}[73]",
                   "LHE_PDF_37_%sDown" % year : f"LHEPdfWeight[74]*LHEPdfWeightNorm{suffix}[74]",
                   "LHE_PDF_38_%sUp" % year : f"LHEPdfWeight[75]*LHEPdfWeightNorm{suffix}[75]",
                   "LHE_PDF_38_%sDown" % year : f"LHEPdfWeight[76]*LHEPdfWeightNorm{suffix}[76]",
                   "LHE_PDF_39_%sUp" % year : f"LHEPdfWeight[77]*LHEPdfWeightNorm{suffix}[77]",
                   "LHE_PDF_39_%sDown" % year : f"LHEPdfWeight[78]*LHEPdfWeightNorm{suffix}[78]",
                   "LHE_PDF_40_%sUp" % year : f"LHEPdfWeight[79]*LHEPdfWeightNorm{suffix}[79]",
                   "LHE_PDF_40_%sDown" % year : f"LHEPdfWeight[80]*LHEPdfWeightNorm{suffix}[80]",
                   "LHE_PDF_41_%sUp" % year : f"LHEPdfWeight[81]*LHEPdfWeightNorm{suffix}[81]",
                   "LHE_PDF_41_%sDown" % year : f"LHEPdfWeight[82]*LHEPdfWeightNorm{suffix}[82]",
                   "LHE_PDF_42_%sUp" % year : f"LHEPdfWeight[83]*LHEPdfWeightNorm{suffix}[83]",
                   "LHE_PDF_42_%sDown" % year : f"LHEPdfWeight[84]*LHEPdfWeightNorm{suffix}[84]",
                   "LHE_PDF_43_%sUp" % year : f"LHEPdfWeight[85]*LHEPdfWeightNorm{suffix}[85]",
                   "LHE_PDF_43_%sDown" % year : f"LHEPdfWeight[86]*LHEPdfWeightNorm{suffix}[86]",
                   "LHE_PDF_44_%sUp" % year : f"LHEPdfWeight[87]*LHEPdfWeightNorm{suffix}[87]",
                   "LHE_PDF_44_%sDown" % year : f"LHEPdfWeight[88]*LHEPdfWeightNorm{suffix}[88]",
                   "LHE_PDF_45_%sUp" % year : f"LHEPdfWeight[89]*LHEPdfWeightNorm{suffix}[89]",
                   "LHE_PDF_45_%sDown" % year : f"LHEPdfWeight[90]*LHEPdfWeightNorm{suffix}[90]",
                   "LHE_PDF_46_%sUp" % year : f"LHEPdfWeight[91]*LHEPdfWeightNorm{suffix}[91]",
                   "LHE_PDF_46_%sDown" % year : f"LHEPdfWeight[92]*LHEPdfWeightNorm{suffix}[92]",
                   "LHE_PDF_47_%sUp" % year : f"LHEPdfWeight[93]*LHEPdfWeightNorm{suffix}[93]",
                   "LHE_PDF_47_%sDown" % year : f"LHEPdfWeight[94]*LHEPdfWeightNorm{suffix}[94]",
                   "LHE_PDF_48_%sUp" % year : f"LHEPdfWeight[95]*LHEPdfWeightNorm{suffix}[95]",
                   "LHE_PDF_48_%sDown" % year : f"LHEPdfWeight[96]*LHEPdfWeightNorm{suffix}[96]",
                   "LHE_PDF_49_%sUp" % year : f"LHEPdfWeight[97]*LHEPdfWeightNorm{suffix}[97]",
                   "LHE_PDF_49_%sDown" % year : f"LHEPdfWeight[98]*LHEPdfWeightNorm{suffix}[98]",
                   "LHE_PDF_50_%sUp" % year : f"LHEPdfWeight[99]*LHEPdfWeightNorm{suffix}[99]",
                   "LHE_PDF_50_%sDown" % year : f"LHEPdfWeight[100]*LHEPdfWeightNorm{suffix}[100]",
                   # LHE aS
                   "LHE_PDF_aS_%sUp" % year : f"LHEPdfWeight[102]*LHEPdfWeightNorm{suffix}[102]",
                   "LHE_PDF_aS_%sDown" % year : f"LHEPdfWeight[101]*LHEPdfWeightNorm{suffix}[101]",
                   # PS for minor bkgs
                   "minorBkg_PS_ISR_%sUp"   % year : f"PSWeight[0]*PSWeightNorm{suffix}[0]",
                   "minorBkg_PS_ISR_%sDown" % year : f"PSWeight[2]*PSWeightNorm{suffix}[2]",
                   "minorBkg_PS_FSR_%sUp"   % year : f"PSWeight[1]*PSWeightNorm{suffix}[1]",
                   "minorBkg_PS_FSR_%sDown" % year : f"PSWeight[3]*PSWeightNorm{suffix}[3]",
                   # PS-fsr for large bkgs
                   "PS_fsr_G2GG_muR_%sDown" %year : f"PSWeight[6]*PSWeightNorm{suffix}[6]",
                   "PS_fsr_G2GG_muR_%sUp"   %year : f"PSWeight[7]*PSWeightNorm{suffix}[7]",
                   "PS_fsr_G2QQ_muR_%sDown" %year : f"PSWeight[8]*PSWeightNorm{suffix}[8]",
                   "PS_fsr_G2QQ_muR_%sUp"   %year : f"PSWeight[9]*PSWeightNorm{suffix}[9]",
                   "PS_fsr_Q2QG_muR_%sDown" %year : f"PSWeight[10]*PSWeightNorm{suffix}[10]",
                   "PS_fsr_Q2QG_muR_%sUp"   %year : f"PSWeight[11]*PSWeightNorm{suffix}[11]",
                   "PS_fsr_X2XG_muR_%sDown" %year : f"PSWeight[12]*PSWeightNorm{suffix}[12]",
                   "PS_fsr_X2XG_muR_%sUp"   %year : f"PSWeight[13]*PSWeightNorm{suffix}[13]",
                   "PS_fsr_G2GG_cNS_%sDown" %year : f"PSWeight[14]*PSWeightNorm{suffix}[14]",
                   "PS_fsr_G2GG_cNS_%sUp"   %year : f"PSWeight[15]*PSWeightNorm{suffix}[15]",
                   "PS_fsr_G2QQ_cNS_%sDown" %year : f"PSWeight[16]*PSWeightNorm{suffix}[16]",
                   "PS_fsr_G2QQ_cNS_%sUp"   %year : f"PSWeight[17]*PSWeightNorm{suffix}[17]",
                   "PS_fsr_G2QG_cNS_%sDown" %year : f"PSWeight[18]*PSWeightNorm{suffix}[18]",
                   "PS_fsr_G2QG_cNS_%sUp"   %year : f"PSWeight[19]*PSWeightNorm{suffix}[19]",
                   "PS_fsr_X2XG_cNS_%sDown" %year : f"PSWeight[20]*PSWeightNorm{suffix}[20]",
                   "PS_fsr_X2XG_cNS_%sUp"   %year : f"PSWeight[21]*PSWeightNorm{suffix}[21]",
                   # PS-isr for large bkgs
                   "PS_isr_G2GG_muR_%sDown" %year : f"PSWeight[28]*PSWeightNorm{suffix}[28]",
                   "PS_isr_G2GG_muR_%sUp"   %year : f"PSWeight[29]*PSWeightNorm{suffix}[29]",
                   "PS_isr_G2QQ_muR_%sDown" %year : f"PSWeight[30]*PSWeightNorm{suffix}[30]",
                   "PS_isr_G2QQ_muR_%sUp"   %year : f"PSWeight[31]*PSWeightNorm{suffix}[31]",
                   "PS_isr_Q2QG_muR_%sDown" %year : f"PSWeight[32]*PSWeightNorm{suffix}[32]",
                   "PS_isr_Q2QG_muR_%sUp"   %year : f"PSWeight[33]*PSWeightNorm{suffix}[33]",
                   "PS_isr_X2XG_muR_%sDown" %year : f"PSWeight[34]*PSWeightNorm{suffix}[34]",
                   "PS_isr_X2XG_muR_%sUp"   %year : f"PSWeight[35]*PSWeightNorm{suffix}[35]",
                   "PS_isr_G2GG_cNS_%sDown" %year : f"PSWeight[36]*PSWeightNorm{suffix}[36]",
                   "PS_isr_G2GG_cNS_%sUp"   %year : f"PSWeight[37]*PSWeightNorm{suffix}[37]",
                   "PS_isr_G2QQ_cNS_%sDown" %year : f"PSWeight[38]*PSWeightNorm{suffix}[38]",
                   "PS_isr_G2QQ_cNS_%sUp"   %year : f"PSWeight[39]*PSWeightNorm{suffix}[39]",
                   "PS_isr_G2QG_cNS_%sDown" %year : f"PSWeight[40]*PSWeightNorm{suffix}[40]",
                   "PS_isr_G2QG_cNS_%sUp"   %year : f"PSWeight[41]*PSWeightNorm{suffix}[41]",
                   "PS_isr_X2XG_cNS_%sDown" %year : f"PSWeight[42]*PSWeightNorm{suffix}[42]",
                   "PS_isr_X2XG_cNS_%sUp"   %year : f"PSWeight[43]*PSWeightNorm{suffix}[43]",
               }

    return systematics

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process ROOT TTrees into TH1D histograms.")
    parser.add_argument("--input_dirs", nargs='+', required=True, help="List of directories where the ROOT files are fetched.")
    parser.add_argument("--output_dir", type=str, required=True, help="Output directory of the new ROOT files.")
    parser.add_argument("--tree_name", type=str, required=True, help="List of TTree names in the input files.")
    parser.add_argument("--nbins", type=int, required=False, help="Number of bins for the histograms.")
    parser.add_argument("--xmin", type=float, required=False, help="Minimum value for the histograms.")
    parser.add_argument("--xmax", type=float, required=False, help="Maximum value for the histograms.")
    parser.add_argument("--input_csv", type=str, required=True, help="The csv file to read variables and ranges from.")
    parser.add_argument("--year", type=int, required=True, help="Data taking year.")
    parser.add_argument("--electron", nargs="?", const=1, type=bool, default=False, required=False, help="Process electron channel only.")
    parser.add_argument("--muon", nargs="?", const=1, type=bool, default=False, required=False, help="Process muon channel only.")
    parser.add_argument("--add_selection", type=str, required=False, help="Additional selection to apply to all processes.")
    parser.add_argument("--count_events", nargs="?", const=1, type=bool, default=False, required=False, help="Count events for each selection.")
    parser.add_argument("--eventClassification", nargs="?", const=1, type=bool, default=False, required=False, help="Apply event classification selection.")
    parser.add_argument("--use5FS", nargs="?", const=1, type=bool, default=False, required=False, help="Use 5-flavor scheme.")
    parser.add_argument("--systematics", nargs="?", const=1, type=bool, default=False, required=False, help="Make systematic variations.")
    parser.add_argument("--flavtag_sf_json", type=str, required=False, default=None,
                         help="Path to an alternate flavTaggingSF*.json.gz correctionlib file. "
                              "If given, flavTagWeight is recomputed on the fly from this file "
                              "instead of using the flavTagWeight branch stored in the ntuple.")
    parser.add_argument("--flavtag_sf_name", type=str, required=False, default=None,
                         help="Name of the correction inside --flavtag_sf_json "
                              "(defaults to the standard per-year name, e.g. particleNetAK4_shape "
                              "or UParTAK4_pseudocontinuous).")


    args = parser.parse_args()

    # Get input files from the input_dirs list
    input_files = []
    for input_dir in args.input_dirs:
        input_files.extend(glob.glob(f"{input_dir}*.root"))
    input_files = sorted(set(input_files))

    # Prepare list of output files based on the name of the input files
    output_files = prepare_output(args.output_dir, input_files)

    # Prepare histogram configurations for each branch
    hist_configs = read_csv(args.input_csv)

    selections = {"base": "n_ak4>=4 && n_btagM>=2 && n_ctagM>=1",
                 "ttbb" : "genEventClassifier==9",
                 "ttbj" : "genEventClassifier==7",
                 "tt2b" : "genEventClassifier==8",
                 "ttcc" : "genEventClassifier==6",
                 "ttcj" : "genEventClassifier==4",
                 "tt2c" : "genEventClassifier==5",
                 "ttLF" : "tt_category==0"
    }

    # Apply trigger selection to separate channels if requested
    if args.electron:
        selections["base"] += " && passTrigEl"
    if args.muon:
        selections["base"] += " && passTrigMu"

    use5FS = False
    if args.use5FS:
        use5FS = True
        print(f"{Fore.GREEN}Using 5-flavor scheme for ttbb, tt2b, and ttbj processes.{Style.RESET_ALL}")

    # Apply additional selections if specified
    if args.add_selection:
        for key in selections.keys():
            selections[key] += f" && ({args.add_selection})"

    print(f"{Fore.YELLOW}Final selections to be applied:{Style.RESET_ALL}")
    for key, value in selections.items():
        print(f"{Fore.YELLOW} - {key}: {value}{Style.RESET_ALL}")

    # Process the trees and get event counts
    total_MC_events, events_in_category = process_trees_parallel(input_files, output_files, args.tree_name, hist_configs, args.year, selections, args.eventClassification, use5FS, args.count_events, args.systematics, args.flavtag_sf_json, args.flavtag_sf_name)

    # Make sure the previous step is completed before merging files
    ROOT.gSystem.Exec("sync")

    # Merge some of the output files
    ttH_list = ["h_ttHbb.root", "h_ttHcc.root", "h_ttZ.root", "h_ttW.root", "h_diboson.root", "h_singletop.root", "h_wjets.root"]
    merge_files(args.output_dir, ttH_list, "h_others.root")

    merge_files(args.output_dir, ["h_ttbb-4f_ttbb.root", "h_ttbb-4f-dps_ttbb.root"], "h_ttbb.root")
    merge_files(args.output_dir, ["h_ttbb-4f_tt2b.root", "h_ttbb-4f-dps_tt2b.root"], "h_tt2b.root")
    merge_files(args.output_dir, ["h_ttbb-4f_ttbj.root", "h_ttbb-4f-dps_ttbj.root"], "h_ttbj.root")

    data_list = ["h_singlee.root", "h_singlemu.root"]
    merge_files(args.output_dir, data_list, "h_Data.root")

    if args.count_events:
        print(f"{Fore.YELLOW}Total MC events after preselection: {total_MC_events}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Event counts in each category:{Style.RESET_ALL}")
        for category, count in events_in_category.items():
            print(f"{Fore.YELLOW} - {category}: {count}{Style.RESET_ALL}")
            print(f"  --> Fraction: {count/total_MC_events:.4f}\n")
