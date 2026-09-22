#!/usr/bin/env python3
"""Likelihood scan plot for every scanned parameter.

    analysis/rabbitPlotScan.py fit.hdf5 -o plots/scans

One figure per `nll_scan_<param>` present in the fit result. The header carries
the profile-likelihood interval read off the 2*deltaNLL = 1 crossings and, for
comparison, the parabolic uncertainty from the inverse Hessian.

Two conventions have to be undone:
  * rabbit stores the scan as deltaNLL, so it is doubled here to make the 1 sigma
    crossing sit at 1;
  * a POI is scanned in the internal variable x = sqrt(mu), so the axis is
    squared back to mu (which is what makes the interval asymmetric).
"""

import argparse
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from rabbit import io_tools

from analysis.rabbitPlotStyle import cms_label


def crossing(x, y, best, level):
    """(low, high) where 2*deltaNLL first crosses `level`, walking outward
    from the minimum along `x` (must be sorted ascending) -- for a POI that
    means the internal sqrt(mu) variable, not mu itself, since mu=sqrt(mu)**2
    is double-valued once a wide scan range pushes sqrt(mu) through zero.

    Always anchored at the minimum itself (2*deltaNLL=0 there), so a crossing
    between the minimum and the first sampled point on either side is found
    by interpolation even when that first step already overshoots `level`
    (a plain lookup within the already-sampled points misses it and used to
    return nan here). Also nan if the level is never reached, or if y stops
    rising before it is (e.g. past the sqrt(mu) wrap)."""
    i0 = int(np.argmin(y))

    def walk(idx_range):
        px, py = x[i0], y[i0]
        for i in idx_range:
            if y[i] >= level:
                return float(np.interp(level, [py, y[i]], [px, x[i]]))
            if y[i] < py - 1e-9:
                return np.nan
            px, py = x[i], y[i]
        return np.nan

    lo = walk(range(i0 - 1, -1, -1))
    hi = walk(range(i0 + 1, len(x)))
    return lo, hi


def poi_crossing_mu(x_sqrt, y, best_sqrt, level):
    """1 sigma/2 sigma bound on mu=sqrt(mu)**2 at `level`, for a POI scan.

    crossing() is run in the (monotonic) internal sqrt(mu) variable. If the
    low-side crossing is still at sqrt(mu) >= 0, the mu bound is the square
    as usual. If the scan range is wide enough that the low-side crossing
    sits at sqrt(mu) < 0, the physical (mu >= 0) confidence region reaches
    all the way down to mu=0, and its upper edge is whichever of the two
    sqrt-space crossings maps to the larger mu."""
    lo, hi = crossing(x_sqrt, y, best_sqrt, level)
    if not np.isfinite(hi):
        return np.nan, np.nan
    if not np.isfinite(lo):
        return np.nan, hi ** 2
    if lo < 0:
        return 0.0, max(lo ** 2, hi ** 2)
    return lo ** 2, hi ** 2


def read_scan(fr, name, pois):
    """(x, x_sqrt, 2*deltaNLL) for `name` from a rabbit fit result. `x` is
    squared back to mu for a POI (same conventions as the main curve);
    `x_sqrt` is the untouched, always-monotonic internal scan variable
    (identical to `x` for a non-POI)."""
    h = fr[f"nll_scan_{name}"].get()
    x_sqrt = np.array([float(v) for v in np.array(h.axes[0])])
    y = 2.0 * h.values()                            # rabbit stores deltaNLL
    x = x_sqrt ** 2 if name in pois else x_sqrt      # internal x = sqrt(mu)
    return x, x_sqrt, y


def read_combine(path, param):
    """(x, 2*deltaNLL) from a combine MultiDimFit --algo grid output."""
    import uproot
    t = uproot.open(path)["limit"]
    if param not in t.keys():
        return None
    x = np.asarray(t[param].array(library="np"), dtype=float)
    d = np.asarray(t["deltaNLL"].array(library="np"), dtype=float)
    ok = np.isfinite(x) & np.isfinite(d)
    x, d = x[ok], d[ok]
    o = np.argsort(x)
    return x[o], 2.0 * d[o]


POI_DISPLAY = {"tt-vcb": r"$|V_{cb}|^{2}$"}


def display_mask(x_sqrt, x, best_idx):
    """For a POI's mu axis, drop the part of the scan that re-traces mu
    values already shown. Walking outward from the minimum toward negative
    sqrt(mu), mu decreases until the wrap through zero, then increases again
    -- plotting that tail as well as the near-best branch that already
    covers the same mu range is what draws the confusing criss-cross seen
    once a wide scan range pushes sqrt(mu) through zero. Keeps everything
    once mu stops decreasing (i.e. everything, for the non-wrapping side)."""
    keep = np.ones(len(x), dtype=bool)
    prev = x[best_idx]
    for i in range(best_idx - 1, -1, -1):
        if x[i] > prev + 1e-12:
            keep[:i + 1] = False
            break
        prev = x[i]
    return keep


def draw(path, name, x, x_sqrt, y, hesse, title, is_poi, combine=None, statonly=None,
         asimov=False):
    disp = POI_DISPLAY.get(name, name)
    best_idx = int(np.argmin(y))
    best = x[best_idx]
    best_sqrt = x_sqrt[best_idx]
    if is_poi:
        lo1, hi1 = poi_crossing_mu(x_sqrt, y, best_sqrt, 1.0)
        lo2, hi2 = poi_crossing_mu(x_sqrt, y, best_sqrt, 4.0)
        pm = display_mask(x_sqrt, x, best_idx)
    else:
        lo1, hi1 = crossing(x, y, best, 1.0)
        lo2, hi2 = crossing(x, y, best, 4.0)
        pm = np.ones(len(x), dtype=bool)
    xhi_candidates = [hi2 if np.isfinite(hi2) else float(x.max())]
    xlo_candidates = [0.0 if is_poi else float(x.min())]

    fig, a = plt.subplots(figsize=(10, 9), dpi=160)
    a.grid(True, lw=0.5, alpha=0.35, zorder=0)
    a.plot(x[pm], y[pm], color="#1f4fd8", lw=2.2, label="Stat+Syst", zorder=3)
    if statonly is not None:
        sx, sx_sqrt, sy = statonly
        sbest_idx = int(np.argmin(sy))
        spm = display_mask(sx_sqrt, sx, sbest_idx) if is_poi else np.ones(len(sx), dtype=bool)
        a.plot(sx[spm], sy[spm], color="#e08a00", lw=2.0, ls="--", label="Stat",
               zorder=3)
        sbest = sx[np.argmin(sy)]
        sbest_sqrt = sx_sqrt[np.argmin(sy)]
        if is_poi:
            slo1, shi1 = poi_crossing_mu(sx_sqrt, sy, sbest_sqrt, 1.0)
            _, shi2 = poi_crossing_mu(sx_sqrt, sy, sbest_sqrt, 4.0)
        else:
            slo1, shi1 = crossing(sx, sy, sbest, 1.0)
            _, shi2 = crossing(sx, sy, sbest, 4.0)
        xhi_candidates.append(shi2 if np.isfinite(shi2) else float(sx.max()))
    if combine is not None:
        cx, cy = combine
        a.plot(cx, cy, color="#cc2222", lw=1.8, ls="--", label="Combine", zorder=3)
        cbest = cx[np.argmin(cy)]
        clo, chi = crossing(cx, cy, cbest, 1.0)

    a.set_xlabel(disp, fontsize=18 * 1.2)
    a.set_ylabel(r"$2\,\Delta\mathrm{NLL}$", fontsize=18 * 1.2)
    ytop = min(9.0, float(np.nanmax(y)) * 1.05)
    a.set_ylim(0, ytop)
    xhi = max(xhi_candidates) * 1.2
    xlo = min(xlo_candidates)
    a.set_xlim(xlo, xhi)

    for lvl, lab, c in ((1.0, r"1$\,\sigma$", "#888888"), (4.0, r"2$\,\sigma$", "#bbbbbb")):
        a.axhline(lvl, color=c, lw=1.0, zorder=1)
        a.text(xhi, lvl, f" {lab}", va="center", ha="left", fontsize=13 * 2, color=c)
    for v in (lo1, hi1):
        if np.isfinite(v):
            a.plot([v, v], [0, 1.0], color="#888888", lw=1.0, zorder=1)

    # central legend: label at txt_x, uncertainty numbers at the shared num_x
    # so the stat+syst and stat-only lines line up in a column. num_x is
    # measured off the actually-rendered label widths (font size and label
    # text both vary), not guessed, so the numbers never overlap the labels.
    txt_x = 0.28
    head_fs, stat_fs = 14 * 1.2, 11 * 1.3 * 1.2
    up = hi1 - best if np.isfinite(hi1) else np.nan
    dn = best - lo1 if np.isfinite(lo1) else np.nan
    head_lbl = a.text(txt_x, 0.66, f"{disp} = {best:.3f}", transform=a.transAxes,
                       ha="left", va="top", fontsize=head_fs, color="#1f4fd8")
    labels = [head_lbl]
    if statonly is not None:
        labels.append(a.text(txt_x, 0.60, "stat. only", transform=a.transAxes,
                              ha="left", va="top", fontsize=stat_fs, color="#e08a00"))
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    num_x = max(t.get_window_extent(renderer=renderer)
                .transformed(a.transAxes.inverted()).x1 for t in labels) + 0.02

    head_num = f"$-{dn:.3f}/+{up:.3f}$" if np.isfinite(up + dn) \
        else "(1 sigma outside the scan range)"
    a.text(num_x, 0.66, head_num, transform=a.transAxes, ha="left", va="top",
           fontsize=head_fs, color="#1f4fd8")
    if statonly is not None:
        su = shi1 - sbest if np.isfinite(shi1) else np.nan
        sd = sbest - slo1 if np.isfinite(slo1) else np.nan
        stat_num = f"$-{sd:.3f}/+{su:.3f}$" if np.isfinite(su + sd) \
            else "(1 sigma outside the scan range)"
        a.text(num_x, 0.60, stat_num, transform=a.transAxes, ha="left", va="top",
               fontsize=stat_fs, color="#e08a00")
    if combine is not None:
        cu = chi - cbest if np.isfinite(chi) else np.nan
        cd = cbest - clo if np.isfinite(clo) else np.nan
        a.text(0.5, -0.14, f"Combine: {cbest:.4f}  $-{cd:.4f}/+{cu:.4f}$",
               transform=a.transAxes, ha="center", fontsize=11, color="#cc2222")
    a.legend(fontsize=12 * 1.4, frameon=False, loc="center right",
             bbox_to_anchor=(0.98, 1.7 / ytop), bbox_transform=a.transAxes)
    cms_label(a, data=not asimov, loc=0)

    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(os.path.splitext(path)[0] + "." + ext, bbox_inches="tight")
    plt.close(fig)
    print(f"  {os.path.basename(path)}")


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("fitresult")
    p.add_argument("-o", "--outdir", default="./")
    p.add_argument("--postfix", default=None)
    p.add_argument("--result", default=None)
    p.add_argument("--params", nargs="*", default=None,
                   help="default: everything that was scanned")
    p.add_argument("--combine", default=None,
                   help="combine MultiDimFit --algo grid output to overlay. Use "
                        "{param} in the path for a per-parameter file, e.g. "
                        "'scans/higgsCombine{param}.MultiDimFit.mH120.root'")
    p.add_argument("--statonly", default=None,
                   help="second rabbit scan fit result (systematics frozen) to "
                        "overlay as a 'stat only' curve")
    p.add_argument("--asimov", action="store_true",
                   help="fit ran on Asimov/expected data: CMS label reads 'Simulation'")
    args = p.parse_args()

    fr, meta = io_tools.get_fitresult(args.fitresult, result=args.result, meta=True)
    pois = {str(v) for v in np.asarray(meta["pois"]).astype(str)}
    tag = args.postfix or os.path.splitext(os.path.basename(args.fitresult))[0]

    scanned = [k[len("nll_scan_"):] for k in fr.keys() if k.startswith("nll_scan_")]
    names = [n for n in scanned if args.params is None or n in args.params]
    if not names:
        print(f"  no scans in {args.fitresult}")
        return

    fr_stat = None
    if args.statonly:
        fr_stat = io_tools.get_fitresult(args.statonly, result=args.result)

    parms = fr["parms"].get()
    for name in sorted(names):
        x, x_sqrt, y = read_scan(fr, name, pois)
        is_poi = name in pois
        sx = float(np.sqrt(parms[{"parms": name}].variance))
        if is_poi:                                  # internal x = sqrt(mu)
            sx = 2.0 * abs(float(parms[{"parms": name}].value)) * sx
        stat = None
        if fr_stat is not None:
            if f"nll_scan_{name}" in fr_stat.keys():
                stat = read_scan(fr_stat, name, pois)
            else:
                print(f"  (no stat-only scan for {name} in {args.statonly})")
        comb = None
        if args.combine:
            cpath = args.combine.replace("{param}", name)
            try:
                comb = read_combine(cpath, name)
            except Exception as exc:
                print(f"  (no combine overlay for {name}: {exc})")
        draw(os.path.join(args.outdir, f"scan_{name}_{tag}.png"), name, x, x_sqrt, y, sx,
             tag, is_poi, combine=comb, statonly=stat, asimov=args.asimov)


if __name__ == "__main__":
    main()
