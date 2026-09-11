#!/usr/bin/env python3
"""Overlay the POIs of several validation runs in one figure.

    analysis/plotValidationCombined.py \
        Validation_200826:orig Validation_simplified_200826:simplified \
        -o Validation_200826/plots/pois_combined.png

Rows = POIs, columns = configs (SR / CR / CRo). In every panel each setup gets
one point +- error per run, so an orig-vs-simplified card comparison lands side
by side: filled marker = first run, hollow = second (fill styles cycle).
Reads the matrix_<cfg>.csv written by analysis/validationMatrix.py, so it only
needs matplotlib. Setups keep the colours/markers of plotValidationPOIs.
"""

import argparse
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from analysis.plotValidationPOIs import POIS, CONFIGS, STYLE, read_matrix

FILLS = ["full", "none", "top", "bottom"]      # one per run, in order given


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("runs", nargs="+",
                    help="outdir[:label] for each validation run to overlay")
    ap.add_argument("-o", "--out", default="pois_combined.png")
    args = ap.parse_args()

    runs = []                                   # (label, {cfg: (setups, data)})
    for spec in args.runs:
        outdir, _, label = spec.partition(":")
        label = label or os.path.basename(outdir.rstrip("/"))
        per_cfg = {}
        for cfg, _ in CONFIGS:
            m = os.path.join(outdir, f"matrix_{cfg}.csv")
            if os.path.exists(m):
                per_cfg[cfg] = read_matrix(m)
        if not per_cfg:
            print(f"  skip {spec}: no matrix_<cfg>.csv under {outdir}")
            continue
        runs.append((label, per_cfg))
    if not runs:
        raise SystemExit("no runs with matrices")

    nrun = len(runs)
    offs = [(-0.28 + 0.56 * i / (nrun - 1)) if nrun > 1 else 0.0
            for i in range(nrun)]
    fills = [FILLS[i % len(FILLS)] for i in range(nrun)]

    ncol = len(CONFIGS)
    nrow = len(POIS)
    fig, axes = plt.subplots(nrow, ncol, figsize=(3.9 * ncol, 2.1 * nrow),
                             squeeze=False)

    for r, (cfg, clabel) in enumerate(CONFIGS):
        # setups populated in this config by any run, in fixed legend order
        present = set()
        for _, per_cfg in runs:
            if cfg in per_cfg:
                _, data = per_cfg[cfg]
                for d in data.values():
                    present |= set(d)
        order = [s for s in STYLE if s in present]
        ys = list(range(len(order)))[::-1]      # first setup on top

        for p, poi in enumerate(POIS):
            ax = axes[p][r]
            for y, s in zip(ys, order):
                short, col, mk = STYLE[s]
                for ri, (_, per_cfg) in enumerate(runs):
                    if cfg not in per_cfg:
                        continue
                    _, data = per_cfg[cfg]
                    v = data.get(poi, {}).get(s)
                    if v is None:
                        continue
                    ax.errorbar(v[0], y + offs[ri], xerr=v[1], fmt=mk, color=col,
                                fillstyle=fills[ri], ms=6, capsize=2.5,
                                markeredgewidth=1.0, lw=0, elinewidth=1)
            # reference: orig combine-robust if present, else 1.0 (Asimov)
            ref = None
            if cfg in runs[0][1]:
                ref = runs[0][1][cfg][1].get(poi, {}).get("B_combine_robust")
            ax.axvline(ref[0] if ref else 1.0, ls="--", lw=0.8, color="0.5")
            ax.set_yticks(ys)
            ax.set_yticklabels([STYLE[s][0] for s in order], fontsize=6)
            ax.set_ylim(-0.6, len(order) - 0.4)
            ax.grid(axis="x", ls=":", alpha=0.5)
            if p == 0:
                ax.set_title(f"{cfg}: {clabel}", fontsize=11)
            if r == 0:
                ax.set_ylabel(poi, fontsize=9)

    run_handles = [Line2D([0], [0], marker="o", color="0.3", fillstyle=fills[i],
                          lw=0, ms=7, markeredgewidth=1.0, label=lab)
                   for i, (lab, _) in enumerate(runs)]
    fig.legend(handles=run_handles, ncol=nrun, loc="upper center",
               fontsize=10, frameon=False, bbox_to_anchor=(0.5, 0.995))
    fig.suptitle("POIs / rateParams  --  " + " vs ".join(l for l, _ in runs),
                 fontsize=13, y=1.005)
    fig.tight_layout(rect=(0, 0, 1, 0.985))
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    fig.savefig(args.out, dpi=130, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {args.out}  ({nrow} POIs x {ncol} configs, {nrun} runs)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
