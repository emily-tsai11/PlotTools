"""Diagnostic plots for the prepareTensor decisions.

Exactly one PNG per (category, process, systematic) entry:

    <outdir>/<category>/<process>/<systematic>.png

The plot carries the full decision -- kept or dropped and why, shape or
normalisation, smoothed or not, symmetrisation -- so nothing has to be
duplicated into per-decision directories. It shows the raw variation as read
from the shapes file, what is written into the tensor (smoothed shape, or the
flat lnN level for an entry turned into a normalisation), and the ratio to the
nominal.
"""

import os
import re
from multiprocessing import Pool

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

UP, DOWN = "Up", "Down"


def _fmt(v):
    return f"{v:.2e}" if isinstance(v, float) else str(v)


COL = {UP: "#cc0000", DOWN: "#0044cc"}
DECISION_COL = {"shape": "#006600", "norm": "#b36b00",
                "dropped_irrelevant": "#999999", "dropped_insignificant": "#999999",
                "dropped_noop": "#bbbbbb"}


def _written_legs(nom, raw, final, decision):
    """What ends up in the tensor for this entry, or None if nothing does."""
    if decision.startswith("dropped"):
        return None
    if decision == "norm":
        tot = nom.sum()
        if tot <= 0:
            return None
        return {leg: nom * (raw[leg].sum() / tot) for leg in raw}
    return final


def plot_entry(path, edges, nom, nom_err, raw, final, info):
    """raw/final: {'Up': array, 'Down': array}. info: the decision-table row."""
    decision = info["decision"]
    written = _written_legs(nom, raw, final, decision)

    x = 0.5 * (edges[1:] + edges[:-1])
    fig, (a, r) = plt.subplots(
        2, 1, figsize=(5.6, 4.8), sharex=True, dpi=160,
        gridspec_kw={"height_ratios": [2.2, 1], "hspace": 0.05})

    a.stairs(nom, edges, color="k", lw=1.4, label="nominal")
    a.stairs(nom + nom_err, edges, baseline=nom - nom_err, fill=True,
             color="k", alpha=0.15, lw=0)
    for leg in (UP, DOWN):
        if leg in raw:
            a.stairs(raw[leg], edges, color=COL[leg], lw=1.0, ls=":",
                     label=f"{leg} raw")
        if written and leg in written:
            a.stairs(written[leg], edges, color=COL[leg], lw=1.4,
                     label=f"{leg} written")

    safe = np.where(nom > 0, nom, np.nan)
    r.axhline(1.0, color="k", lw=1.0)
    r.fill_between(x, 1 - nom_err / safe, 1 + nom_err / safe,
                   color="k", alpha=0.15, step="mid", lw=0)
    for leg in (UP, DOWN):
        if leg in raw:
            r.stairs(raw[leg] / safe, edges, color=COL[leg], lw=1.0, ls=":")
        if written and leg in written:
            r.stairs(written[leg] / safe, edges, color=COL[leg], lw=1.4)

    a.set_ylabel("events")
    a.legend(fontsize=6, ncol=2, frameon=False)
    a.set_title(f"{info['category']} / {info['process']} / {info['systematic']}",
                fontsize=8)
    ratios = [v / safe for v in list(raw.values()) + list((written or {}).values())]
    if ratios:
        fin = np.concatenate([v[np.isfinite(v)] for v in ratios]) if ratios else np.array([1.0])
        if fin.size:
            lo, hi = float(fin.min()), float(fin.max())
            pad = max(0.02, 0.25 * (hi - lo))
            r.set_ylim(lo - pad, hi + pad)
    r.set_ylabel("var / nom", fontsize=8)
    r.set_xlabel(info.get("distribution", ""), fontsize=8)
    for ax in (a, r):
        ax.tick_params(labelsize=7)

    fig.text(0.5, 0.995, decision.upper().replace("_", " "), ha="center", fontsize=8,
             weight="bold", color=DECISION_COL.get(decision, "#000000"))
    fig.text(0.5, 0.963,
             f"p_shift={info['p_shift']:.3g}  p_shape={info['p_shape']:.3g}   "
             f"rel_tot={_fmt(info['rel_total'])}  rel_proc={_fmt(info['rel_process'])}   "
             f"sym={info['symmetrize']}  smoothed={info['smoothed'] or 'n/a'}",
             ha="center", fontsize=6, color="#444444")
    fig.text(0.5, 0.935, str(info.get("reason", ""))[:110], ha="center",
             fontsize=5.5, color="#666666")

    os.makedirs(os.path.dirname(path), exist_ok=True)
    fig.savefig(path, dpi=300, bbox_inches="tight")
    fig.savefig(os.path.splitext(path)[0] + ".pdf", bbox_inches="tight")
    plt.close(fig)


def _one(task):
    plot_entry(*task)


def plot_all(outdir, edges, nominal, raw_all, variations, rows, categories,
             only_kept=False, limit=0, jobs=1, channels=None):
    """rows: {key: decision-table row}. raw_all: pre-smoothing snapshot."""
    rx = re.compile(channels) if channels else None
    tasks = []
    for key, info in sorted(rows.items()):
        cat, proc, syst = key
        if rx and not rx.search(cat):
            continue
        if only_kept and info["decision"].startswith("dropped"):
            continue
        if limit and len(tasks) >= limit:
            break
        nom, var = nominal[(cat, proc)]
        info = dict(info, distribution=categories.get(cat, ""))
        os.makedirs(os.path.join(outdir, cat, proc), exist_ok=True)
        tasks.append((os.path.join(outdir, cat, proc, f"{syst}.png"),
                      edges[cat], nom, np.sqrt(np.maximum(var, 0.0)),
                      raw_all.get(key, {}),
                      {leg: v[0] for leg, v in variations.get(key, {}).items()},
                      info))

    if jobs > 1:
        with Pool(jobs) as pool:
            for i, _ in enumerate(pool.imap_unordered(_one, tasks, chunksize=16), 1):
                if i % 500 == 0:
                    print(f"    {i}/{len(tasks)} plots written", flush=True)
    else:
        for i, t in enumerate(tasks, 1):
            _one(t)
            if i % 200 == 0:
                print(f"    {i}/{len(tasks)} plots written", flush=True)
    print(f"  wrote {len(tasks)} plots -> {outdir}")
    return len(tasks)
