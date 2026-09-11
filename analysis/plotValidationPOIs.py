#!/usr/bin/env python3
"""Plot the POIs / rateParams across all setups, from the matrix_<cfg>.csv files.

    analysis/plotValidationPOIs.py Validation_200826

One PNG per configuration (SR/CR/CRo) under <outdir>/plots: a panel per POI with
one point +- error for every setup (A-E). Reads the wide CSVs written by
analysis/validationMatrix.py, so it just needs matplotlib (no ROOT/rabbit).
"""

import argparse
import csv
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

POIS = ["tt-vcb", "xsec_ttbb", "xsec_ttbj", "xsec_tt2b", "xsec_ttcc",
        "xsec_ttcj", "xsec_tt2c", "xsec_ttLF"]
CONFIGS = [("SR", "CR + SR, Asimov"), ("CR", "CR only, Asimov"),
           ("CRo", "CR only, OBSERVED")]
# label -> (short name, colour, marker)
STYLE = {
    "A_combine_default":  ("combine default",  "#d62728", "s"),
    "B_combine_robust":   ("combine robust",   "#ff7f0e", "s"),
    "C_rabbit_ours":      ("rabbit ours (C)",  "#1f77b4", "o"),
    "Cnew_rabbit_retuned": ("rabbit retuned (C*)", "#e377c2", "D"),
    "E_rabbit_converter": ("rabbit conv. (E)", "#17becf", "o"),
    "D_raw":              ("D raw",            "#2ca02c", "^"),
    "D_smOnly":           ("D smOnly",         "#9467bd", "^"),
    "D_isoNorm":          ("D isoNorm",        "#8c564b", "^"),
    "D_isoPrune":         ("D isoPrune",       "#7f7f7f", "^"),
}


def read_matrix(path):
    rows = list(csv.reader(open(path)))
    head = rows[0]
    setups = [head[i][:-4] for i in range(1, len(head), 2)]   # strip "_val"
    data = {}
    for r in rows[1:]:
        vals = {}
        for k, i in zip(setups, range(1, len(head), 2)):
            if r[i] != "":
                vals[k] = (float(r[i]), float(r[i + 1]))
        data[r[0]] = vals
    return setups, data


def plot_nuisances(cfg, label, data, order, pdir, topn):
    """Pull/constraint comparison: post-fit value +- error per nuisance, all setups."""
    nuis = [p for p in data if p not in POIS and any(data[p].values())]

    def interest(p):                       # pulled OR differently constrained
        vs = [data[p][s] for s in order if s in data[p]]
        vals, errs = [v for v, _ in vs], [e for _, e in vs]
        return max(abs(x) for x in vals) + (max(errs) - min(errs))

    nuis.sort(key=interest, reverse=True)
    sel = nuis[:topn]
    n = len(sel)
    fig, ax = plt.subplots(figsize=(9, max(4.0, 0.42 * n)))
    offs = [(-0.36 + 0.72 * i / (len(order) - 1)) if len(order) > 1 else 0.0
            for i in range(len(order))]
    for i, s in enumerate(order):
        xs, ys, xe = [], [], []
        for j, p in enumerate(sel):
            if s in data[p]:
                v, e = data[p][s]
                xs.append(v); ys.append(n - 1 - j + offs[i]); xe.append(e)
        short, col, mk = STYLE[s]
        ax.errorbar(xs, ys, xerr=xe, fmt=mk, color=col, ms=4, lw=0,
                    elinewidth=1, capsize=1.5, label=short)
    ax.axvspan(-1, 1, color="0.9", zorder=0)      # prefit +-1 band
    ax.axvline(0, ls="--", lw=0.8, color="0.5")
    ax.set_yticks([n - 1 - j for j in range(n)])
    ax.set_yticklabels(sel, fontsize=6)
    ax.set_ylim(-1, n)
    ax.set_xlabel(r"post-fit  $\hat{\theta}\pm\sigma_\theta$   (prefit 0$\pm$1)")
    ax.set_title(f"nuisances (top {n} by pull / constraint spread)  --  {cfg}: {label}",
                 fontsize=11)
    ax.legend(fontsize=6, ncol=len(order), loc="upper center",
              bbox_to_anchor=(0.5, -0.05))
    fig.tight_layout()
    out = os.path.join(pdir, f"nuis_{cfg}.png")
    fig.savefig(out, dpi=130)
    plt.close(fig)
    print(f"  wrote {out}  (top {n} of {len(nuis)} nuisances)")

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("outdir")
    ap.add_argument("--top", type=int, default=40, help="nuisances shown in the pull plot")
    args = ap.parse_args()
    pdir = os.path.join(args.outdir, "plots")
    os.makedirs(pdir, exist_ok=True)

    for cfg, label in CONFIGS:
        mpath = os.path.join(args.outdir, f"matrix_{cfg}.csv")
        if not os.path.exists(mpath):
            print(f"  skip {cfg}: no {mpath}")
            continue
        setups, data = read_matrix(mpath)
        order = [s for s in STYLE if s in setups]                 # fixed legend order
        pois = [p for p in POIS if data.get(p) and any(data[p].values())]

        ncol = 4
        nrow = -(-len(pois) // ncol)
        fig, axes = plt.subplots(nrow, ncol, figsize=(4.2 * ncol, 3.0 * nrow),
                                 squeeze=False)
        for ax in axes.flat:
            ax.set_visible(False)

        for k, poi in enumerate(pois):
            ax = axes[k // ncol][k % ncol]
            ax.set_visible(True)
            ys = list(range(len(order)))[::-1]                    # first setup on top
            for y, s in zip(ys, order):
                if s not in data[poi]:
                    continue
                v, e = data[poi][s]
                short, col, mk = STYLE[s]
                ax.errorbar(v, y, xerr=e, fmt=mk, color=col, capsize=3, ms=6)
            # reference line: combine robust if present, else 1.0 (Asimov)
            ref = data[poi].get("B_combine_robust")
            ax.axvline(ref[0] if ref else 1.0, ls="--", lw=0.8, color="0.5")
            ax.set_yticks(ys)
            ax.set_yticklabels([STYLE[s][0] for s in order], fontsize=7)
            ax.set_ylim(-0.6, len(order) - 0.4)
            ax.set_title(poi, fontsize=10)
            ax.grid(axis="x", ls=":", alpha=0.5)

        fig.suptitle(f"POIs / rateParams  --  {cfg}: {label}", fontsize=13)
        fig.tight_layout(rect=(0, 0, 1, 0.97))
        out = os.path.join(pdir, f"pois_{cfg}.png")
        fig.savefig(out, dpi=130)
        plt.close(fig)
        print(f"  wrote {out}  ({len(pois)} POIs, {len(order)} setups)")
        plot_nuisances(cfg, label, data, order, pdir, args.top)
    return 0


if __name__ == "__main__":
    sys.exit(main())
