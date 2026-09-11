#!/usr/bin/env python3
"""Toy-calibrated saturated GoF plot: toy q-histogram, observed line, p-value
shading, chi2-shape fit overlay.

    analysis/plotToyGoF.py Comparison_250826_preUnblinding/rabbit \
        --pattern 'toyGoF_CRo_noFTS_postfitcond_batch*.hdf5' \
        --observed Comparison_250826_preUnblinding/rabbit/B_CRo_noFTS.hdf5 \
        -o Comparison_250826_preUnblinding/plots/toyGoF_CRo_noFTS.png \
        --label "Lepton + jets"

Reads every toy{1..N} result out of every file matching --pattern, computes
q = 2*nllvalreduced per toy, and the observed q from --observed's own
nllvalreduced (never from a toy). The chi2(ndf) curve is a real fit (ndf free,
normalisation fixed to N_toys*bin_width), matched to the toy histogram by
least squares with sqrt(N) bin errors -- not the naive/asymptotic ndf from
ndfsat, which analysis/preUnblindingSummary.py-style asymptotic GoF already
reports separately and which the toys were built specifically to cross-check
(see runToyGoF_CRo_noFTS_postfitcond.sh).
"""

import argparse
import glob
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy import optimize, stats

from rabbit import io_tools

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from analysis.rabbitPlotStyle import COM, LUMI


def collect_toys_npz(path):
    """Read the combined summary run_gof_toys_lean.sh writes (q, ndf arrays),
    the lean toy workflow's output -- the per-toy .hdf5 files it reads from
    are deleted right after compaction (see analysis/compact_toys.py)."""
    d = np.load(path)
    print(f"  {os.path.basename(path)}: {len(d['q'])} toys")
    return np.asarray(d["q"])


    q = []
    for path in sorted(glob.glob(os.path.join(directory, pattern))):
        with_toys = 0
        n = 1
        while True:
            try:
                fr, _ = io_tools.get_fitresult(path, result=f"toy{n}", meta=True)
            except (KeyError, ValueError):
                break
            q.append(2.0 * float(np.asarray(fr["nllvalreduced"])))
            with_toys += 1
            n += 1
        print(f"  {os.path.basename(path)}: {with_toys} toys")
    return np.asarray(q)


def observed_q(path):
    fr, _ = io_tools.get_fitresult(path, meta=True)
    return 2.0 * float(np.asarray(fr["nllvalreduced"]))


def fit_chi2_shape(q, bins):
    counts, edges = np.histogram(q, bins=bins)
    centers = 0.5 * (edges[1:] + edges[:-1])
    width = edges[1] - edges[0]
    norm = len(q) * width

    def model(x, ndf):
        return norm * stats.chi2.pdf(x, ndf)

    sigma = np.sqrt(np.maximum(counts, 1))
    ndf0 = q.mean()
    popt, pcov = optimize.curve_fit(model, centers, counts, p0=[ndf0], sigma=sigma,
                                    absolute_sigma=True)
    return popt[0], np.sqrt(pcov[0, 0]), edges, counts


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("directory", nargs="?", default=None,
                    help="required with --pattern (old raw-hdf5-batch mode)")
    ap.add_argument("--pattern", default=None,
                    help="glob for raw toy batch .hdf5 files (old mode, before "
                         "compact_toys.py -- most workflows now use --npz instead)")
    ap.add_argument("--npz", default=None,
                    help="combined toy summary .npz from run_gof_toys_lean.sh "
                         "(current default output, e.g. "
                         "rabbit/toyGoF_<name>_summary.npz)")
    ap.add_argument("--observed", required=True, help="fit result the toys are compared to")
    ap.add_argument("-o", "--output", required=True)
    ap.add_argument("--label", default="Lepton + jets", help="top-left channel label")
    ap.add_argument("--nbins", type=int, default=30)
    args = ap.parse_args()

    if not args.npz and not (args.directory and args.pattern):
        raise SystemExit("need --npz <summary.npz>, or <directory> --pattern <glob>")
    q = collect_toys_npz(args.npz) if args.npz else collect_toys(args.directory, args.pattern)
    if len(q) == 0:
        raise SystemExit("no toys found")
    q_obs = observed_q(args.observed)
    p_toy = float(np.mean(q >= q_obs))

    lo = min(q.min(), q_obs) - 2
    hi = q.max() + 2
    ndf_fit, ndf_err, edges, counts = fit_chi2_shape(q, np.linspace(lo, hi, args.nbins + 1))
    centers = 0.5 * (edges[1:] + edges[:-1])
    width = edges[1] - edges[0]

    fig, ax = plt.subplots(figsize=(7, 6.5), dpi=160)

    # p-value shading: the histogram area at q >= q_obs
    shade = centers >= q_obs
    h_shade = ax.bar(centers[shade], counts[shade], width=width, color="#5ab4e5",
                     edgecolor="none", zorder=1, label=f"p-value = {p_toy:.2f}")

    # toy data as points with sqrt(N) error bars, ROOT-style
    err = np.sqrt(np.maximum(counts, 1))
    h_data = ax.errorbar(centers, counts, yerr=err, fmt="ko-", ms=4, lw=0.8, capsize=0,
                         zorder=3, label="Toy data")

    # observed line
    h_obs = ax.axvline(q_obs, color="#1a3fa0", lw=1.6, zorder=2,
                       label=f"Observed = {q_obs:.2f}")

    # fitted chi2 curve
    xx = np.linspace(lo, hi, 400)
    h_fit, = ax.plot(xx, len(q) * width * stats.chi2.pdf(xx, ndf_fit), color="#d1332e",
                     lw=1.6, zorder=4,
                     label=rf"$\chi^2$ fit, ndf = {ndf_fit:.1f}  $\pm$ {ndf_err:.1f}")

    ax.set_xlabel("GoF (saturated)", fontsize=15)
    ax.set_ylabel("Number of MC Toys", fontsize=15)
    ax.set_xlim(lo, hi)
    ax.set_ylim(0, None)
    handles = [h_data, h_obs, h_shade, h_fit]
    labels = ["Toy data", f"Observed = {q_obs:.2f}", f"p-value = {p_toy:.2f}",
             rf"$\chi^2$ fit, ndf = {ndf_fit:.1f}  $\pm$ {ndf_err:.1f}",
             rf"N$_{{\mathrm{{Toys}}}}$ = {len(q)}"]
    handles.append(plt.Line2D([], [], linestyle=""))
    ax.legend(handles, labels, loc="upper right", frameon=False, fontsize=11)

    fig.text(0.11, 0.955, args.label, fontsize=17, fontweight="bold", va="top", ha="left",
             transform=fig.transFigure)
    fig.text(0.97, 0.955, f"{LUMI} fb$^{{-1}}$ ({COM} TeV)", fontsize=13, va="top",
             ha="right", transform=fig.transFigure)

    fig.tight_layout(rect=[0, 0, 1, 0.94])
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    fig.savefig(args.output)
    fig.savefig(os.path.splitext(args.output)[0] + ".pdf")
    plt.close(fig)
    print(f"\nwrote {args.output}")
    print(f"n_toys={len(q)}  q_obs={q_obs:.2f}  p_toy={p_toy:.4f}  "
         f"chi2-fit ndf={ndf_fit:.2f}+-{ndf_err:.2f}")


if __name__ == "__main__":
    main()
