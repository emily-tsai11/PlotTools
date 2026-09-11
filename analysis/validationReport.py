#!/usr/bin/env python3
"""Assemble the Combine <-> rabbit validation into one table.

    analysis/validationReport.py Validation_190826

For every configuration it prints the free-floating parameters side by side:
combine with the default Minuit Hessian, combine with --robustHesse, and the two
rabbit legs (A = same datacard through the converter, B = our own tensor).
Then the profile-likelihood intervals, and finally the worst nuisance
disagreement over all ~400 parameters.
"""

import argparse
import os
import sys

import numpy as np

FREE = ["r", "xsec_ttbb", "xsec_ttbj", "xsec_tt2b", "xsec_ttcc", "xsec_ttcj",
        "xsec_tt2c", "xsec_ttLF"]
RENAME = {"r": "tt-vcb"}
CONFIGS = [("SR", "CR + SR, Asimov"), ("CR", "CR only, Asimov"),
           ("CRo", "CR only, OBSERVED")]
# setup D: rabbit our-workflow with the reduction steps isolated one at a time
DTRIALS = ["raw", "smOnly", "isoNorm", "isoPrune"]


def combine_params(path, result="fit_mdf"):
    import ROOT
    f = ROOT.TFile.Open(path)
    fr = f.Get(result)
    if not fr:
        return {}
    out = {p.GetName(): (p.getVal(), p.getError()) for p in fr.floatParsFinal()}
    f.Close()
    return out


def rabbit_params(path):
    from analysis.rabbitResults import read_parameters, poi_names
    import numpy as np
    pars = read_parameters(path)
    pois = set(poi_names(path))
    lk = np.log(1.01)                      # converter's rateParam -> lnN step
    out = {}
    for n, (v, e) in pars.items():
        if n.startswith("xsec_") and n not in pois:
            v2 = float(np.exp(lk * v))
            out[n] = (v2, float(v2 * lk * e))
        else:
            out[n] = (v, e)
    return out


def scan_interval(path, param):
    """(best, -low, +high) from the rabbit scan, or None."""
    from rabbit import io_tools
    fr, meta = io_tools.get_fitresult(path, meta=True)
    key = f"nll_scan_{param}"
    if key not in fr.keys():
        return None
    h = fr[key].get()
    x = np.array([float(v) for v in np.array(h.axes[0])])
    y = 2.0 * h.values()
    if param in {str(p) for p in np.asarray(meta["pois"]).astype(str)}:
        x = x ** 2
    best = x[np.argmin(y)]
    lo_m, hi_m = x < best, x > best
    # np.interp clamps without left/right, so a scan that never reaches
    # 2*deltaNLL = 1 returned the edge of the range as if it were the crossing.
    lo = np.interp(1.0, y[lo_m][::-1], x[lo_m][::-1],
                   left=np.nan, right=np.nan) if lo_m.any() else np.nan
    hi = np.interp(1.0, y[hi_m], x[hi_m],
                   left=np.nan, right=np.nan) if hi_m.any() else np.nan
    if lo_m.any() and y[lo_m].max() < 1.0:
        lo = np.nan
    if hi_m.any() and y[hi_m].max() < 1.0:
        hi = np.nan
    return best, best - lo, hi - best


def fmt(p):
    return f"{p[0]:9.4f} +-{p[1]:7.4f}" if p else " " * 19


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("outdir")
    args = ap.parse_args()
    C = os.path.join(args.outdir, "combine")
    R = os.path.join(args.outdir, "rabbit")

    for cfg, label in CONFIGS:
        print("\n" + "=" * 104)
        print(f"{cfg}   {label}")
        print("=" * 104)
        cd = combine_params(os.path.join(C, f"multidimfit{cfg}_default.root"))
        cr = combine_params(os.path.join(C, f"multidimfit{cfg}_robust.root"))

        def maybe(fn, *a):
            try:
                return fn(*a)
            except Exception:
                return {}          # fit still running, or file not written yet
        ra = maybe(rabbit_params, os.path.join(R, f"A_{cfg}.hdf5"))
        rb = maybe(rabbit_params, os.path.join(R, f"B_{cfg}.hdf5"))

        print(f"{'parameter':<12}{'combine default':>21}{'combine robustHesse':>21}"
              f"{'rabbit A (same card)':>21}{'rabbit B (our tensor)':>21}")
        print("-" * 104)
        for name in FREE:
            rn = RENAME.get(name, name)
            row = [cd.get(name), cr.get(name), ra.get(rn), rb.get(rn)]
            if not any(row):
                continue
            print(f"{name:<12}" + "".join(f"{fmt(p):>21}" for p in row))

        # profile likelihood, rabbit leg B
        pl = []
        for name in FREE:
            rn = RENAME.get(name, name)
            f = os.path.join(R, f"B_{cfg}.hdf5")
            if not os.path.exists(f):
                continue
            try:
                iv = scan_interval(f, rn)
            except Exception:
                iv = None
            if iv:
                pl.append((name, iv))
        if pl:
            print(f"\n  profile likelihood (rabbit B, 2dNLL = 1):")
            for name, (b, d, u) in pl:
                print(f"    {name:<12} {b:9.4f}  -{d:.4f} / +{u:.4f}")

        # setup D: isolation trials (full = rabbit B above)
        dcols = [("full=C", rb)] + [
            (t, maybe(rabbit_params, os.path.join(R, f"D{t}_{cfg}.hdf5")))
            for t in DTRIALS]
        if any(d for _, d in dcols[1:]):
            print(f"\n  setup D (rabbit, pieces isolated):")
            print("    " + f"{'parameter':<10}" + "".join(f"{n:>19}" for n, _ in dcols))
            print("    " + "-" * (10 + 19 * len(dcols)))
            for name in FREE:
                rn = RENAME.get(name, name)
                row = [d.get(rn) for _, d in dcols]
                if not any(row):
                    continue
                print("    " + f"{name:<10}" + "".join(f"{fmt(p):>19}" for p in row))

    print("\nfull per-nuisance tables: analysis/compareCombine.py "
          f"{C}/multidimfit<cfg>_robust.root {R}/<leg>_<cfg>.hdf5 --result fit_mdf")
    return 0


if __name__ == "__main__":
    sys.exit(main())
