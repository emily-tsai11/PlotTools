#!/usr/bin/env python3
"""Overview of the prepareTensor decisions: dropped / norm / smoothed / symmetrised.

    analysis/plotDecisionSummary.py Validation_200826/ourRetune
    analysis/plotDecisionSummary.py Validation_200826/ourRetune --compare Validation_200826/ourFull

Reads <base>_decisions.csv (+ <base>_symmetrisation.csv) and writes
<base>_decision_summary.png. With --compare it also draws an old-vs-new panel.
matplotlib only; no ROOT/rabbit needed.
"""

import argparse
import csv
import os
import sys
from collections import Counter, defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

C_SHAPE, C_NORM = "#2ca02c", "#e08214"
C_DROPI, C_DROPN = "#999999", "#cccccc"
STACK = [("shape", C_SHAPE), ("norm", C_NORM),
         ("dropped_irrelevant", C_DROPI), ("dropped_noop", C_DROPN)]


def load(path):
    return list(csv.DictReader(open(path)))


def bar(ax, labels, values, colors, title):
    y = list(range(len(labels)))[::-1]
    ax.barh(y, values, color=colors)
    for yi, v in zip(y, values):
        ax.text(v, yi, f" {v}", va="center", fontsize=8)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=8)
    ax.set_title(title, fontsize=10)
    ax.set_xlim(0, max(values) * 1.18 if values and max(values) else 1)
    ax.tick_params(labelsize=8)


def stacked(ax, keys, per, title, labelmap=lambda k: k, legend=False):
    left = [0] * len(keys)
    y = list(range(len(keys)))[::-1]
    for d, col in STACK:
        vals = [per[k].get(d, 0) for k in keys]
        ax.barh(y, vals, left=left, color=col, label=d)
        left = [l + v for l, v in zip(left, vals)]
    ax.set_yticks(y)
    ax.set_yticklabels([labelmap(k) for k in keys], fontsize=7)
    ax.set_title(title, fontsize=10)
    if legend:
        ax.legend(fontsize=7, loc="lower right")
    ax.tick_params(labelsize=8)


def metrics(rows):
    """The 6 counts compared old-vs-new: 4 decisions + forced/kept symmetrisation."""
    dec = Counter(r["decision"] for r in rows)
    forced = kept = 0
    for r in rows:
        if r["decision"] not in ("shape", "norm"):
            continue
        s = r["symmetrize"]
        if s.startswith("average") or s.startswith("conservative"):
            forced += 1
        elif s.startswith("None"):
            kept += 1
    return {"shape": dec.get("shape", 0), "norm": dec.get("norm", 0),
            "dropped_irrelevant": dec.get("dropped_irrelevant", 0),
            "dropped_noop": dec.get("dropped_noop", 0),
            "forced-sym": forced, "kept-asym": kept}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("base", help="tensor base path, e.g. Validation_200826/ourRetune")
    ap.add_argument("--compare", default=None, help="a second base to diff against (old)")
    args = ap.parse_args()
    rows = load(args.base + "_decisions.csv")

    symclass = {}
    spath = args.base + "_symmetrisation.csv"
    if os.path.exists(spath):
        for r in load(spath):
            symclass[r["systematic"]] = ("forced" if r["symmetrize"] == "conservative"
                                         else "rule-asym" if "alternative-sample" in r["reason"]
                                         else "default-asym")

    dec = Counter(r["decision"] for r in rows)
    n_all = len(rows)
    noop, dropi = dec.get("dropped_noop", 0), dec.get("dropped_irrelevant", 0)
    shape, norm = dec.get("shape", 0), dec.get("norm", 0)
    written = shape + norm

    fig, ax = plt.subplots(2, 3, figsize=(19, 9))

    # 1) pipeline funnel
    bar(ax[0][0],
        ["entries read", "after no-op cut", "after relevance cut", "written: shape",
         "written: norm"],
        [n_all, n_all - noop, written, shape, norm],
        ["#4477aa", "#4477aa", "#4477aa", C_SHAPE, C_NORM],
        f"pipeline (drop {noop} no-op + {dropi} irrelevant = {100*(noop+dropi)/n_all:.0f}%)")

    # 2) symmetrisation (written entries)
    sym = Counter()
    for r in rows:
        if r["decision"] not in ("shape", "norm"):
            continue
        s = r["symmetrize"]
        if s.startswith("conservative"):
            sym["forced -> envelope"] += 1
        elif "one-sided, conservative" in s:
            sym["forced (one-sided, kept asym)"] += 1
        elif symclass.get(r["systematic"]) == "rule-asym":
            sym["kept asym (rule)"] += 1
        else:
            sym["kept asym (default)"] += 1
    labs = ["forced -> envelope", "forced (one-sided, kept asym)",
            "kept asym (rule)", "kept asym (default)"]
    bar(ax[0][1], labs, [sym.get(k, 0) for k in labs],
        ["#8856a7", "#b3a2c7", "#3182bd", "#9ecae1"], "symmetrisation (written)")

    # 3) smoothing among shape entries
    sm = Counter()
    for r in rows:
        if r["decision"] != "shape":
            continue
        s = r["smoothed"]
        sm["smoothed" if s == "yes" else "one-sided" if "one-sided" in s
           else "spline n/a" if "spline" in s else "other"] += 1
    labs = ["smoothed", "one-sided", "spline n/a", "other"]
    bar(ax[0][2], labs, [sm.get(k, 0) for k in labs],
        [C_SHAPE, "#a1d99b", "#c7e9c0", "#eeeeee"], f"smoothing (of {shape} shape)")

    # 4) per-region stacked
    per_cat = defaultdict(Counter)
    for r in rows:
        per_cat[r["category"]][r["decision"]] += 1
    cats = sorted(per_cat)
    stacked(ax[1][0], cats, per_cat, "decisions per region",
            labelmap=lambda c: c.replace("Vcb_cat", "").replace("_", " "), legend=True)

    # 5) per-process stacked (signal first, then by size)
    per_proc = defaultdict(Counter)
    for r in rows:
        per_proc[r["process"]][r["decision"]] += 1
    procs = sorted(per_proc, key=lambda p: (p != "tt-vcb", -sum(per_proc[p].values())))
    stacked(ax[1][1], procs, per_proc, "decisions per process (signal first)", legend=True)

    # 6) old-vs-new comparison
    axc = ax[1][2]
    if args.compare and os.path.exists(args.compare + "_decisions.csv"):
        oldm = metrics(load(args.compare + "_decisions.csv"))
        newm = metrics(rows)
        cats6 = ["shape", "norm", "dropped_irrelevant", "dropped_noop",
                 "forced-sym", "kept-asym"]
        y = list(range(len(cats6)))[::-1]
        h = 0.38
        axc.barh([yi + h/2 for yi in y], [oldm[c] for c in cats6], height=h,
                 color="#bbbbbb", label=f"old ({os.path.basename(args.compare)})")
        axc.barh([yi - h/2 for yi in y], [newm[c] for c in cats6], height=h,
                 color="#4477aa", label=f"new ({os.path.basename(args.base)})")
        for yi, c in zip(y, cats6):
            axc.text(oldm[c], yi + h/2, f" {oldm[c]}", va="center", fontsize=7)
            axc.text(newm[c], yi - h/2, f" {newm[c]}", va="center", fontsize=7)
        axc.set_yticks(y)
        axc.set_yticklabels(cats6, fontsize=8)
        axc.set_title("old vs new", fontsize=10)
        axc.legend(fontsize=7, loc="lower right")
        axc.set_xlim(0, max(max(oldm.values()), max(newm.values())) * 1.2)
    else:
        # fraction per region if no comparison given
        stacked(axc, cats, {c: Counter({d: per_cat[c][d]/max(sum(per_cat[c].values()), 1)
                                        for d in per_cat[c]}) for c in cats},
                "decisions per region (fraction)",
                labelmap=lambda c: c.replace("Vcb_cat", "").replace("_", " "))

    fig.suptitle(f"prepareTensor decision summary  --  {os.path.basename(args.base)}  "
                 f"({n_all} entries)", fontsize=13)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    out = args.base + "_decision_summary.png"
    fig.savefig(out, dpi=140)
    plt.close(fig)
    print(f"wrote {out}")
    print(f"  written {written} (shape {shape}, norm {norm}); dropped {noop} no-op + {dropi} irrelevant")
    if args.compare:
        print(f"  old vs new: {metrics(load(args.compare + '_decisions.csv'))}  ->  {metrics(rows)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
