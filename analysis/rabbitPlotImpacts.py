#!/usr/bin/env python3
"""Impact and pull plot as a static PNG/PDF.

rabbit_plot_pulls_and_impacts.py writes plotly HTML and needs a working Chrome
for a static export; Chrome does not start on lxplus. This gives the same
content with matplotlib.

    analysis/rabbitPlotImpacts.py fit.hdf5 --poi tt-vcb -o plots/
    analysis/rabbitPlotImpacts.py fit.hdf5 --poi tt-vcb -o plots/ --grouped

Left panel: nuisance pull and its postfit constraint. Right panel: the impact
on the POI, ranked. POIs are reported in the fitted quantity, not rabbit's
internal sqrt storage.
"""

import argparse
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from rabbit import io_tools

from analysis.rabbitPlotStyle import COM, LUMI


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("fitresult")
    p.add_argument("--poi", required=True)
    p.add_argument("-o", "--outdir", default="./")
    p.add_argument("--postfix", default=None)
    p.add_argument("--result", default=None)
    p.add_argument("--grouped", action="store_true", help="impacts by nuisance group")
    p.add_argument("--impact-type", default="traditional",
                   choices=["traditional", "global"])
    p.add_argument("-n", "--nmax", type=int, default=40)
    p.add_argument("--asimov", action="store_true",
                   help="fit ran on Asimov/expected data: CMS label reads 'Simulation'")
    p.add_argument("--redact", default=None, metavar="PARAM",
                   help="hide PARAM's own fitted value everywhere it appears as a pull "
                        "row in this plot -- not just when PARAM is --poi itself. A "
                        "blinded free parameter can leak into ANOTHER poi's impact plot "
                        "via correlation (it shows up as a pull row there too), so this "
                        "must be passed for every --poi call, not only PARAM's own. "
                        "Impacts BY other parameters remain shown in full; only PARAM's "
                        "own printed value is hidden. If PARAM == --poi, the 'total' "
                        "subtitle figure is hidden too.")
    args = p.parse_args()

    fitresult, meta = io_tools.get_fitresult(args.fitresult, result=args.result,
                                             meta=True)
    out = io_tools.read_impacts_poi(fitresult, args.poi, grouped=args.grouped,
                                    impact_type=args.impact_type, pulls=not args.grouped)
    if args.grouped:
        impacts, labels = out
        pulls = constraints = None
    else:
        pulls, _pulls_prefit, constraints, _c_prefit, impacts, labels = out

    # rabbit stores a POI as sqrt(mu); an impact on it scales by |dmu/dx| = 2|x|
    pois = {str(x) for x in np.asarray(meta["pois"]).astype(str)}
    if args.poi in pois:
        x = float(fitresult["parms"].get()[{"parms": args.poi}].value)
        impacts = impacts * 2.0 * abs(x)

    labels = np.asarray([str(l) for l in labels])
    total = float("nan")
    if len(labels) and labels[-1] == "Total":       # appended by read_impacts_poi
        total, impacts, labels = float(impacts[-1]), impacts[:-1], labels[:-1]
    if pulls is not None:
        pulls, constraints = np.asarray(pulls), np.asarray(constraints)

    order = np.argsort(-np.abs(impacts))[: args.nmax][::-1]
    impacts, labels = impacts[order], labels[order]
    free = np.array([l in pois for l in labels])
    y = np.arange(len(labels))
    ncol = 1 if pulls is None else 2
    fig, axes = plt.subplots(1, ncol, figsize=(6 + 5 * ncol, 2.0 + 0.36 * len(y)),
                             dpi=160, sharey=True,
                             gridspec_kw={"width_ratios": [1, 1][:ncol], "wspace": 0.06})
    axes = np.atleast_1d(axes)
    a_imp = axes[-1]
    for i in range(len(y)):
        if i % 2:
            for ax in axes:
                ax.axhspan(i - 0.5, i + 0.5, color="#f2f2f2", zorder=0)

    if pulls is not None:
        pulls, constraints = pulls[order], constraints[order]
        a = axes[0]
        for v in (-2, -1, 1, 2):
            a.axvline(v, color="#bbbbbb", lw=0.8, ls=":" if abs(v) == 2 else "-", zorder=1)
        a.axvline(0, color="k", lw=1.1, zorder=1)
        # constrained nuisances: pull and postfit constraint. Free parameters have
        # no prefit width, so a pull is meaningless -- print the fitted value.
        c = ~free
        a.errorbar(pulls[c], y[c], xerr=constraints[c], fmt="ko", ms=4.5, lw=1.4,
                   capsize=2, zorder=3)
        for i in np.where(free)[0]:
            if args.redact is not None and labels[i] == args.redact:
                a.text(0, y[i], "hidden", ha="center", va="center", fontsize=9,
                      color="#888888", style="italic", zorder=4,
                      bbox=dict(fc="white", ec="none", pad=0.6))
                continue
            # every free parameter is stored as sqrt(mu) unless the fit ran
            # with --allowNegativeParam
            v, e = pulls[i], constraints[i]
            v, e = v * v, 2 * abs(v) * e
            a.text(0, y[i], f"{v:.3f} $\\pm$ {e:.3f}", ha="center", va="center",
                  fontsize=9, color="#0044aa", zorder=4,
                  bbox=dict(fc="white", ec="none", pad=0.6))
        a.set_xlim(-2.6, 2.6)
        # marker: (theta_hat - theta_I)/sigma_I, which is theta_hat itself because
        # rabbit parametrises constrained nuisances with theta_I = 0, sigma_I = 1.
        # bar: the POSTFIT constraint sigma_hat/sigma_I, not the pull uncertainty.
        # sqrt(sigma_I^2 - sigma_hat^2) is not usable here: sigma_hat > sigma_I for
        # part of the nuisances.
        a.set_xlabel(r"$(\hat\theta-\theta_I)/\sigma_I$,  bar $=\hat\sigma/\sigma_I$",
                     fontsize=12)
        a.set_yticks(y)
        a.set_yticklabels(labels, fontsize=10)
        a.tick_params(axis="x", labelsize=10)

    a_imp.axvline(0, color="k", lw=1.1, zorder=1)
    a_imp.barh(y, np.abs(impacts) * np.sign(impacts), height=0.72,
               color="#e42536", label=r"$+1\sigma$", zorder=2)
    a_imp.barh(y, -np.abs(impacts) * np.sign(impacts), height=0.72,
               color="#5790fc", label=r"$-1\sigma$", zorder=2)
    a_imp.set_xlabel(f"Impact on {args.poi}", fontsize=12)
    a_imp.tick_params(axis="x", labelsize=10)
    a_imp.legend(fontsize=11, ncol=2, loc="lower right", frameon=False)
    if pulls is None:
        a_imp.set_yticks(y)
        a_imp.set_yticklabels(labels, fontsize=10)
    a_imp.set_ylim(-0.7, len(y) - 0.3)
    tag = args.postfix or os.path.splitext(os.path.basename(args.fitresult))[0]
    kindlabel = "Grouped" if args.grouped else "Ungrouped"
    subtitle = f"{tag}  --  {kindlabel} {args.impact_type} impacts on {args.poi}"
    if np.isfinite(total) and args.poi != args.redact:
        subtitle += f"   (total = {total:.4f})"
    elif np.isfinite(total):
        subtitle += "   (total = hidden)"
    # Fixed-height figure-frame header: hep.cms.label's axes-relative
    # placement either overlaps the top rows (loc=2) or, combined with a
    # naive y > 1 suptitle, blows up the bbox_inches='tight' canvas (this
    # plot's row count -- and so its height -- varies a lot). Reserving a
    # fixed number of inches at the top and drawing in figure coordinates
    # keeps the header the same size regardless of plot height.
    fw, fh = fig.get_size_inches()
    top = max(0.5, 1.0 - 0.95 / fh)
    fig.subplots_adjust(top=top)
    label = "Simulation Work in Progress" if args.asimov else "Work in Progress"
    fig.text(0.01, 0.995, "CMS", transform=fig.transFigure, va="top", ha="left",
              fontsize=20, fontweight="bold")
    fig.text(0.01 + 1.05 / fw, 0.995, label, transform=fig.transFigure, va="top",
              ha="left", fontsize=15, fontstyle="italic")
    fig.text(0.99, 0.995, f"{LUMI} fb$^{{-1}}$ ({COM} TeV)", transform=fig.transFigure,
              va="top", ha="right", fontsize=15)
    fig.text(0.5, top + (1.0 - top) * 0.28, subtitle, transform=fig.transFigure,
              va="top", ha="center", fontsize=12, color="#333333")

    os.makedirs(args.outdir, exist_ok=True)
    kind = "grouped" if args.grouped else "ungrouped"
    name = f"impacts_{args.impact_type}_{kind}_{args.poi}_{tag}"
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(args.outdir, f"{name}.{ext}"), bbox_inches="tight")
    print(f"  {name}.png")
    plt.close(fig)


if __name__ == "__main__":
    main()
