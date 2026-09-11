#!/usr/bin/env python3
"""Sankey flow of the prepareTensor pipeline.

    analysis/plotDecisionSankey.py Validation_200826/ourRetune

read -> (no-op | kept) -> (shape | norm | dropped-irrelevant)
     -> (smoothed | raw | norm) -> (forced->envelope | kept-asymmetric)

Ribbon widths are entry counts (real joint counts, not proportional guesses).
Writes <base>_decision_sankey.png. matplotlib only.
"""

import argparse
import csv
import sys
from collections import Counter, defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.patches import PathPatch, Rectangle

COLX = {0: 0.0, 1: 3.0, 2: 6.0, 3: 9.0, 4: 12.0}
W = 0.45


def load(path):
    return list(csv.DictReader(open(path)))


def ribbon(ax, x0, y0t, y0b, x1, y1t, y1b, color):
    mid = 0.5 * (x0 + x1)
    verts = [(x0, y0t), (mid, y0t), (mid, y1t), (x1, y1t),
             (x1, y1b), (mid, y1b), (mid, y0b), (x0, y0b), (x0, y0t)]
    codes = [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4,
             Path.LINETO, Path.CURVE4, Path.CURVE4, Path.CURVE4, Path.CLOSEPOLY]
    ax.add_patch(PathPatch(Path(verts, codes), facecolor=color, alpha=0.42,
                           edgecolor="none", zorder=2))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("base")
    args = ap.parse_args()
    rows = load(args.base + "_decisions.csv")

    dec = Counter(r["decision"] for r in rows)
    n_all = len(rows)
    noop = dec.get("dropped_noop", 0)
    irrel = dec.get("dropped_irrelevant", 0)
    shape, norm = dec.get("shape", 0), dec.get("norm", 0)
    kept = n_all - noop

    def issym(r):
        s = r["symmetrize"]
        return "forced" if (s.startswith("conservative") or s.startswith("average")) else "asym"

    def node3(r):
        if r["decision"] == "norm":
            return "normp"
        return "smoothed" if r["smoothed"] == "yes" else "raw"

    j = Counter()                       # (node3, sym) joint counts over written
    smoothed = raw = 0
    for r in rows:
        if r["decision"] not in ("shape", "norm"):
            continue
        j[(node3(r), issym(r))] += 1
        if r["decision"] == "shape":
            if r["smoothed"] == "yes":
                smoothed += 1
            else:
                raw += 1
    forced = sum(v for (n, s), v in j.items() if s == "forced")
    asym = sum(v for (n, s), v in j.items() if s == "asym")

    # nodes: name -> (col, value, color, label, order)
    G = "#2ca02c"; O = "#e08214"; GR = "#aaaaaa"
    nodes = {
        "read":  (0, n_all, "#4477aa", f"read\n{n_all}", 0),
        "kept":  (1, kept,  "#4477aa", f"kept\n{kept}", 0),
        "noop":  (1, noop,  GR,        f"no-op drop\n{noop}", 1),
        "shape": (2, shape, G,         f"shape\n{shape}", 0),
        "norm":  (2, norm,  O,         f"norm\n{norm}", 1),
        "irrel": (2, irrel, GR,        f"irrelevant drop\n{irrel}", 2),
        "smoothed": (3, smoothed, G,   f"smoothed\n{smoothed}", 0),
        "raw":      (3, raw,      "#a1d99b", f"raw shape\n{raw}", 1),
        "normp":    (3, norm,     O,    f"norm (lnN)\n{norm}", 2),
        "forced": (4, forced, "#8856a7", f"forced->envelope\n{forced}", 0),
        "asym":   (4, asym,   "#9ecae1", f"kept asym\n{asym}", 1),
    }
    flows = [
        ("read", "kept", kept, "#4477aa"), ("read", "noop", noop, GR),
        ("kept", "shape", shape, G), ("kept", "norm", norm, O), ("kept", "irrel", irrel, GR),
        ("shape", "smoothed", smoothed, G), ("shape", "raw", raw, G),
        ("norm", "normp", norm, O),
    ]
    for n3, col in (("smoothed", G), ("raw", "#a1d99b"), ("normp", O)):
        for s in ("forced", "asym"):
            v = j.get((n3, s), 0)
            if v:
                flows.append((n3, s, v, col))

    # layout: stack nodes top-down per column, centred
    colnodes = defaultdict(list)
    for name, nd in nodes.items():
        colnodes[nd[0]].append(name)
    H = n_all
    gap = 0.03 * H
    ybt = {}
    for c, ns in colnodes.items():
        ns.sort(key=lambda n: nodes[n][4])
        tot = sum(nodes[n][1] for n in ns) + gap * (len(ns) - 1)
        top = (H + tot) / 2
        for n in ns:
            v = nodes[n][1]
            ybt[n] = (top - v, top)          # (bottom, top)
            top -= v + gap

    fig, ax = plt.subplots(figsize=(15, 8))
    for name, nd in nodes.items():
        b, t = ybt[name]
        x = COLX[nd[0]]
        ax.add_patch(Rectangle((x, b), W, t - b, color=nd[2], zorder=3))
        ax.text(x + W / 2, t + 0.015 * H, nd[3], ha="center", va="bottom", fontsize=7.5)

    out_off = {n: ybt[n][1] for n in nodes}
    in_off = {n: ybt[n][1] for n in nodes}
    flows.sort(key=lambda f: (nodes[f[0]][0], nodes[f[0]][4], nodes[f[1]][4]))
    for src, dst, val, col in flows:
        xs = COLX[nodes[src][0]] + W
        xd = COLX[nodes[dst][0]]
        s_top, s_bot = out_off[src], out_off[src] - val
        d_top, d_bot = in_off[dst], in_off[dst] - val
        out_off[src] = s_bot
        in_off[dst] = d_bot
        ribbon(ax, xs, s_top, s_bot, xd, d_top, d_bot, col)

    ax.set_xlim(-0.3, COLX[4] + W + 1.5)
    ax.set_ylim(-0.05 * H, 1.12 * H)
    ax.axis("off")
    stages = ["no-op cut", "classify + prune", "smoothing", "symmetrisation"]
    for c in (1, 2, 3, 4):
        ax.text(COLX[c] + W / 2, -0.03 * H, stages[c - 1], ha="center", fontsize=8,
                style="italic", color="#555555")
    ax.set_title(f"prepareTensor flow  --  {args.base.split('/')[-1]}  ({n_all} entries)",
                 fontsize=13)
    fig.tight_layout()
    out = args.base + "_decision_sankey.png"
    fig.savefig(out, dpi=140)
    plt.close(fig)
    print(f"wrote {out}")
    print(f"  read {n_all} -> noop {noop} | kept {kept} -> shape {shape} / norm {norm} / irrel {irrel}")
    print(f"  shape -> smoothed {smoothed} / raw {raw};  written -> forced {forced} / asym {asym}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
