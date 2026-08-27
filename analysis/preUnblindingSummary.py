#!/usr/bin/env python3
"""One table of the pre-unblinding Combine vs rabbit comparison.

    analysis/preUnblindingSummary.py Comparison_250826_preUnblinding

Reads what runPreUnblindingComparison.sh wrote and prints, per model and per
configuration, the parameter of interest from both tools.

POI per configuration: SR -> r (combine) / tt-vcb (rabbit), CRo -> xsec_ttLF.

Leg A tensors come from analysis/cardToTensor.py, which writes Combine
rateParams as unconstrained lnN with a 1% step, so a rabbit theta maps back to
a Combine multiplier as v = exp(ln(1.01)*theta). Leg B tensors make the same
quantities real POIs, which read_parameters already un-sqrt-es, so they are
left alone -- exactly the rule analysis/compareCombine.py uses.
"""

import os
import sys

import numpy as np

RATEPARAM_LNN = 1.01
CARDS = ["smoothed", "noFlavTagSymm", "nonSmoothed", "orig"]
POI = {"SR": ("r", "tt-vcb"), "CRo": ("xsec_ttLF", "xsec_ttLF")}


def read_combine(path, name):
    import ROOT
    f = ROOT.TFile.Open(path)
    if not f or f.IsZombie():
        return None
    fr = f.Get("fit_mdf")
    if not fr:
        f.Close()
        return None
    out = None
    for p in fr.floatParsFinal():
        if p.GetName() == name:
            out = (p.getVal(), p.getError())
    f.Close()
    return out


def read_rabbit(path, name):
    from analysis.rabbitResults import poi_names, read_parameters
    try:
        pars = read_parameters(path)
        pois = set(poi_names(path))
    except Exception:
        return None
    if name not in pars:
        return None
    v, e = pars[name]
    if name.startswith("xsec_") and name not in pois:
        lk = np.log(RATEPARAM_LNN)
        v2 = float(np.exp(lk * v))
        return (v2, float(v2 * lk * e))
    return (v, e)


def fmt(x):
    return "     n/a      " if x is None else f"{x[0]:8.4f} +- {x[1]:6.4f}"


def main():
    argv = [a for a in sys.argv[1:] if not a.startswith("-")]
    allpois = "--all" in sys.argv
    out = argv[0] if argv else "Comparison_250826_preUnblinding"

    # (combine name, rabbit name) per configuration. With the SR masked the
    # signal is unconstrained, so r / tt-vcb is frozen in CRo and only the
    # tt+X normalisations float there.
    xsec = [f"xsec_{p}" for p in
            ("ttbb", "ttbj", "tt2b", "ttcc", "ttcj", "tt2c", "ttLF")]
    pois = {"SR": [("r", "tt-vcb")] + [(x, x) for x in xsec],
            "CRo": [(x, x) for x in xsec]}

    rows = []
    for cfg in ("SR", "CRo"):
        plist = pois[cfg] if allpois else [POI[cfg]]
        for cpoi, rpoi in plist:
            for tag in CARDS:
                c = read_combine(f"{out}/combine/multidimfit{tag}_{cfg}.root", cpoi)
                r = read_rabbit(f"{out}/rabbit/{tag}_A_{cfg}.hdf5", rpoi)
                rows.append((cfg, tag, "A", cpoi, c, r))
            b = read_rabbit(f"{out}/rabbit/B_{cfg}.hdf5", rpoi)
            rows.append((cfg, "orig", "B", cpoi, None, b))
            # same pipeline, flavTag mirror-up switched off
            bn = read_rabbit(f"{out}/rabbit/B_{cfg}_noFTS.hdf5", rpoi)
            if bn:
                rows.append((cfg, "orig noFTS", "B", cpoi, None, bn))

    w = 78
    print("=" * w)
    print(f"{'cfg':4} {'model':14} {'leg':3} {'poi':11} {'combine':21} {'rabbit':21} {'d/sig':>6}")
    print("-" * w)
    last = None
    for cfg, tag, leg, poi, c, r in rows:
        if last is not None and last != (cfg, poi):
            print("-" * w)
        last = (cfg, poi)
        d = ""
        if c and r:
            s = max(c[1], 1e-12)
            d = f"{(r[0] - c[0]) / s:+6.2f}"
        note = "" if leg == "A" else "  (no combine twin)"
        print(f"{cfg:4} {tag:14} {leg:3} {poi:11} {fmt(c):21} {fmt(r):21} {d:>6}{note}")
    print("=" * w)
    print("leg A = cardToTensor, identical model to combine -> difference is minimiser/Hessian")
    print("leg B = prepareTensor on unsmoothed orig shapes, our pruning/smoothing/symmetrisation")
    print("SR is Asimov (-t -1). CRo is observed with the signal region masked.")

    nmiss = sum(1 for _, _, _, _, c, r in rows if (c is None and r is None))
    if nmiss:
        print(f"WARNING: {nmiss} rows have neither result; check the logs under {out}")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.exit(main())
