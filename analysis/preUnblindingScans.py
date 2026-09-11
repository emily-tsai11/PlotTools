#!/usr/bin/env python3
"""Profile-likelihood intervals from the pre-unblinding scans, Combine vs rabbit.

    analysis/preUnblindingScans.py Comparison_250826_preUnblinding

Reads what runPreUnblindingComparison.sh wrote and, for every model and every
scanned parameter, reports the 68% interval taken off the 2*deltaNLL = 1
crossings on both sides. Also writes one overlay figure per scan.

Three conventions have to be undone before the two curves are comparable:

  * rabbit stores a scan as deltaNLL, so it is doubled (rabbitPlotScan.read_*
    and the doubling here both follow COMBINE_FIXES.md).
  * a rabbit POI is scanned in the internal variable x = sqrt(mu), so the axis
    is squared back to mu. That is what makes the interval asymmetric.
  * leg A comes from analysis/cardToTensor.py, which writes Combine rateParams
    as unconstrained lnN with a 1% step. There the xsec_* are NOT POIs: the
    scan axis is theta and maps to the Combine multiplier as
    v = exp(ln(1.01)*theta). Leg B makes them real POIs, so they take the
    sqrt rule instead. Same rule analysis/compareCombine.py applies.

The signal strength is called r by Combine and tt-vcb by rabbit.
"""

import argparse
import os
import sys

import numpy as np

RATEPARAM_LNN = 1.01
CARDS = ["smoothed", "noFlavTagSymm", "nonSmoothed", "orig"]
# configuration -> (combine POI, rabbit POI) of the headline parameter
HEADLINE = {"SR": ("r", "tt-vcb"), "CRo": ("xsec_ttLF", "xsec_ttLF")}
# rabbit name -> combine name
TO_COMBINE = {"tt-vcb": "r"}


def rabbit_scan(fr, meta, name):
    """(x, 2*deltaNLL) for one rabbit scan, on the Combine parameter scale."""
    pois = {str(v) for v in np.asarray(meta["pois"]).astype(str)}
    h = fr[f"nll_scan_{name}"].get()
    x = np.array([float(v) for v in np.array(h.axes[0])], dtype=float)
    y = 2.0 * np.asarray(h.values(), dtype=float)
    if name in pois:
        x = x ** 2                                    # internal x = sqrt(mu)
    elif name.startswith("xsec_"):
        x = np.exp(np.log(RATEPARAM_LNN) * x)         # converter's lnN theta
    return x, y


def interval(x, y, level=1.0):
    """(best, lo, hi) from the 2*deltaNLL = level crossings; nan if not bracketed."""
    o = np.argsort(x)
    x, y = x[o], y[o]
    y = y - y.min()
    best = float(x[np.argmin(y)])
    lo_m, hi_m = x < best, x > best
    lo = hi = np.nan
    if lo_m.any() and y[lo_m].max() >= level:
        lo = float(np.interp(level, y[lo_m][::-1], x[lo_m][::-1]))
    if hi_m.any() and y[hi_m].max() >= level:
        hi = float(np.interp(level, y[hi_m], x[hi_m]))
    return best, lo, hi


def fmt(t):
    if t is None:
        return "        n/a         "
    best, lo, hi = t
    d = "" if np.isnan(lo) or np.isnan(hi) else f" -{best - lo:.4f}/+{hi - best:.4f}"
    if not d:
        return f"{best:8.4f}  (not bracketed)"
    return f"{best:8.4f}{d}"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("outdir", nargs="?", default="Comparison_250826_preUnblinding")
    ap.add_argument("--plots", action="store_true", help="also write overlay figures")
    ap.add_argument("--all-params", action="store_true",
                    help="table every scanned parameter, not just the headline POI")
    args = ap.parse_args()

    from rabbit import io_tools

    from analysis.rabbitPlotScan import draw, read_combine

    OUT = args.outdir
    plotdir = os.path.join(OUT, "plots", "scans")
    if args.plots:
        os.makedirs(plotdir, exist_ok=True)

    # (label, rabbit fit basename, combine tag) per configuration
    jobs = []
    for cfg in ("SR", "CRo"):
        for tag in CARDS:
            jobs.append((cfg, tag, "A", f"{tag}_A_{cfg}", tag))
        jobs.append((cfg, "orig", "B", f"B_{cfg}", "orig"))

    rows = []
    for cfg, tag, leg, fitname, ctag in jobs:
        path = os.path.join(OUT, "rabbit", f"{fitname}.hdf5")
        if not os.path.exists(path):
            print(f"  missing {path}", file=sys.stderr)
            continue
        fr, meta = io_tools.get_fitresult(path, meta=True)
        scanned = sorted(k[len("nll_scan_"):] for k in fr.keys()
                         if k.startswith("nll_scan_"))
        want = scanned if args.all_params else [HEADLINE[cfg][1]]
        for name in want:
            if name not in scanned:
                continue
            rx, ry = rabbit_scan(fr, meta, name)
            cname = TO_COMBINE.get(name, name)
            cpath = os.path.join(
                OUT, "combine",
                f"higgsCombine{ctag}_{cfg}_{cname}.MultiDimFit.mH120.root")
            comb = None
            if os.path.exists(cpath):
                try:
                    comb = read_combine(cpath, cname)
                except Exception as exc:
                    print(f"  (combine scan unreadable {cpath}: {exc})", file=sys.stderr)
            # leg B has no combine twin of its own model; orig is the closest,
            # same unsmoothed shapes, so it is shown for reference only
            rows.append((cfg, tag, leg, name,
                         interval(*comb) if comb is not None else None,
                         interval(rx, ry)))
            if args.plots:
                sfx = f"{ctag}_{cfg}_{leg}"
                draw(os.path.join(plotdir, f"scan_{name}_{sfx}.png"), name,
                     rx, ry, np.nan, sfx, combine=comb, asimov=(cfg == "SR"))

    w = 78
    print("=" * w)
    print(f"{'cfg':<4} {'model':<15}{'leg':<4}{'param':<12}"
          f"{'combine 68% PL':<26}{'rabbit 68% PL':<26}")
    print("-" * w)
    last = None
    for cfg, tag, leg, name, c, r in rows:
        if last is not None and last != cfg:
            print("-" * w)
        last = cfg
        note = "   (no combine twin)" if leg == "B" else ""
        print(f"{cfg:<4} {tag:<15}{leg:<4}{name:<12}{fmt(c):<26}{fmt(r):<26}{note}")
    print("=" * w)
    print("leg A = cardToTensor, identical model to combine -> difference is the minimiser")
    print("leg B = prepareTensor on unsmoothed orig shapes, our pruning/smoothing")
    print("SR is Asimov (-t -1). CRo is observed with the signal region masked.")
    print("Intervals are the 2*deltaNLL = 1 crossings of the 31-point grid.")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.exit(main())
