#!/usr/bin/env python3
"""Overlay the profile-likelihood scans (2*dNLL) across setups, per POI.

    analysis/plotValidationScans.py Validation_200826

One PNG per configuration (SR/CR/CRo) under <outdir>/plots: a panel per scanned
POI overlaying the combine grid scan and every rabbit leg (C, E, D trials).
rabbit curves come from nll_scan_<poi> in the fit hdf5 (POI axis un-sqrt-ed like
analysis.rabbitResults); the combine curve from the higgsCombinescan TTree.
Needs ROOT (cmsenv) + rabbit venv.
"""

import argparse
import csv
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

POIS = ["tt-vcb", "xsec_ttbb", "xsec_ttbj", "xsec_tt2b", "xsec_ttcc",
        "xsec_ttcj", "xsec_tt2c", "xsec_ttLF"]
CONFIGS = [("SR", "CR + SR, Asimov"), ("CR", "CR only, Asimov"),
           ("CRo", "CR only, OBSERVED")]
# rabbit legs: label -> (short, colour, hdf5 template)
RABBIT = [
    ("C_rabbit_ours",      ("rabbit ours (C)",  "#1f77b4"), "B_{cfg}.hdf5"),
    ("Cnew_rabbit_retuned", ("rabbit retuned (C*)", "#e377c2"), "Cnew_{cfg}.hdf5"),
    ("E_rabbit_converter", ("rabbit conv. (E)", "#17becf"), "A_{cfg}.hdf5"),
    ("D_raw",      ("D raw",      "#2ca02c"), "Draw_{cfg}.hdf5"),
    ("D_smOnly",   ("D smOnly",   "#9467bd"), "DsmOnly_{cfg}.hdf5"),
    ("D_isoNorm",  ("D isoNorm",  "#8c564b"), "DisoNorm_{cfg}.hdf5"),
    ("D_isoPrune", ("D isoPrune", "#7f7f7f"), "DisoPrune_{cfg}.hdf5"),
]


def rabbit_scan(path, poi):
    from rabbit import io_tools
    fr, meta = io_tools.get_fitresult(path, meta=True)
    key = f"nll_scan_{poi}"
    if key not in fr.keys():
        return None
    h = fr[key].get()
    x = np.array([float(v) for v in np.array(h.axes[0])])
    y = 2.0 * h.values()
    pois = {str(p) for p in np.asarray(meta["pois"]).astype(str)}
    if poi in pois:
        x = x ** 2
    elif poi.startswith("xsec_"):
        x = np.exp(np.log(1.01) * x)      # converter rateParam: lnN theta -> multiplier
    o = np.argsort(x)
    return x[o], y[o]


def combine_scan(path, branch):
    import ROOT
    f = ROOT.TFile.Open(path)
    t = f.Get("limit")
    if not t:
        f.Close()
        return None
    xs, ys = [], []
    for e in t:
        xs.append(float(getattr(e, branch)))
        ys.append(2.0 * float(e.deltaNLL))
    f.Close()
    xs, ys = np.array(xs), np.array(ys)
    o = np.argsort(xs)
    return xs[o], ys[o]

def combine_gaussians(path):
    """Per-POI (value, error) for combine default/robust, from matrix_<cfg>.csv."""
    if not os.path.exists(path):
        return {}
    rows = list(csv.reader(open(path)))
    idx = {name: i for i, name in enumerate(rows[0])}
    out = {}
    for r in rows[1:]:
        d = {}
        for mode, pre in (("default", "A_combine_default"), ("robust", "B_combine_robust")):
            vi, ei = idx.get(pre + "_val"), idx.get(pre + "_err")
            if vi is not None and r[vi] != "" and float(r[ei]) > 0:
                d[mode] = (float(r[vi]), float(r[ei]))
        if d:
            out[r[0]] = d
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("outdir")
    args = ap.parse_args()
    C = os.path.join(args.outdir, "combine")
    R = os.path.join(args.outdir, "rabbit")
    pdir = os.path.join(args.outdir, "plots")
    os.makedirs(pdir, exist_ok=True)

    for cfg, label in CONFIGS:
        curves = {}                       # poi -> list of (short, colour, x, y)
        for poi in POIS:
            got = []
            branch = "r" if poi == "tt-vcb" else poi
            cpath = os.path.join(C, f"higgsCombinescan_{cfg}_{branch}.MultiDimFit.mH120.root")
            if os.path.exists(cpath):
                try:
                    s = combine_scan(cpath, branch)
                    if s is not None:
                        got.append(("combine", "#000000", s[0], s[1]))
                except Exception:
                    pass
            for _lab, (short, col), tpl in RABBIT:
                try:
                    s = rabbit_scan(os.path.join(R, tpl.format(cfg=cfg)), poi)
                except Exception:
                    s = None
                if s is not None:
                    got.append((short, col, s[0], s[1]))
            if got:
                curves[poi] = got

        gauss = combine_gaussians(os.path.join(args.outdir, f"matrix_{cfg}.csv"))

        pois = [p for p in POIS if p in curves]
        if not pois:
            print(f"  skip {cfg}: no scans")
            continue
        ncol = 4
        nrow = -(-len(pois) // ncol)
        fig, axes = plt.subplots(nrow, ncol, figsize=(4.2 * ncol, 3.2 * nrow),
                                 squeeze=False)
        for ax in axes.flat:
            ax.set_visible(False)
        for k, poi in enumerate(pois):
            ax = axes[k // ncol][k % ncol]
            ax.set_visible(True)
            for short, col, x, y in curves[poi]:
                lw = 2.0 if short == "combine" else 1.2
                ls = "-" if short == "combine" else "--"
                ax.plot(x, y, ls, color=col, lw=lw, label=short)
            for mode, gcol in (("default", "#d62728"), ("robust", "#ff7f0e")):
                g = gauss.get(poi, {}).get(mode)
                if not g:
                    continue
                v, e = g
                xx = np.linspace(v - 3.2 * e, v + 3.2 * e, 200)
                ax.plot(xx, ((xx - v) / e) ** 2, ":", color=gcol, lw=1.1,
                        label=f"combine {mode} (Hesse)")
            for lvl in (1.0, 4.0):        # 68% / 95% CL
                ax.axhline(lvl, color="0.6", lw=0.6, ls=":")
            ax.set_ylim(0, 9)
            ax.set_title(poi, fontsize=10)
            ax.set_xlabel("parameter value")
            ax.set_ylabel(r"$2\,\Delta\mathrm{NLL}$")
            ax.grid(ls=":", alpha=0.4)
        # one shared legend
        h, l = axes[0][0].get_legend_handles_labels()
        fig.legend(h, l, fontsize=8, ncol=len(l), loc="lower center")
        fig.suptitle(f"profile-likelihood scans  --  {cfg}: {label}", fontsize=13)
        fig.tight_layout(rect=(0, 0.04, 1, 0.97))
        out = os.path.join(pdir, f"scans_{cfg}.png")
        fig.savefig(out, dpi=130)
        plt.close(fig)
        print(f"  wrote {out}  ({len(pois)} POIs)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
