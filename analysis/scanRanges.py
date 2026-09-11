#!/usr/bin/env python3
"""Scan ranges for a Combine grid scan, taken from a robustHesse fit result.

    analysis/scanRanges.py multidimfitorig_SR.root --nsigma 4

Prints one "<param> <lo> <hi>" line per floating POI-like parameter.

Why not --autoRange: it sizes its window from Combine's default Minuit Hessian,
which is measured unreliable on this model (COMBINE_FIXES.md). On the 250826
pre-unblinding cards it produced windows up to 26x too narrow -- e.g.
orig/SR/xsec_ttLF got a width of 0.0197 where 3 sigma is 0.522 -- so the scan
never reached 2*deltaNLL = 1 and no interval could be read off it. The
robustHesse errors written by the --algo none fit are trustworthy, so the range
is built from those and is deterministic.
"""

import argparse
import sys


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("fitresult", help="multidimfit*.root from --algo none --saveFitResult")
    ap.add_argument("--nsigma", type=float, default=4.0)
    ap.add_argument("--result", default="fit_mdf")
    ap.add_argument("--params", nargs="*", default=None,
                    help="default: r and every xsec_*")
    args = ap.parse_args()

    import ROOT
    ROOT.gROOT.SetBatch(True)

    f = ROOT.TFile.Open(args.fitresult)
    if not f or f.IsZombie():
        raise SystemExit(f"{args.fitresult}: cannot open")
    fr = f.Get(args.result)
    if not fr:
        raise SystemExit(f"{args.fitresult}: no RooFitResult '{args.result}'")

    for p in fr.floatParsFinal():
        n = p.GetName()
        if args.params is not None:
            if n not in args.params:
                continue
        elif not (n == "r" or n.startswith("xsec_")):
            continue
        v, e = p.getVal(), p.getError()
        if not (e > 0):
            print(f"# {n}: error {e}, skipped", file=sys.stderr)
            continue
        lo, hi = v - args.nsigma * e, v + args.nsigma * e
        # stay inside what the workspace declares, or combine clamps and the
        # grid silently comes out lopsided
        lo = max(lo, p.getMin())
        hi = min(hi, p.getMax())
        print(f"{n} {lo:.6f} {hi:.6f}")
    f.Close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
