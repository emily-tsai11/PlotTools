#!/usr/bin/env python3
"""One line per systematic: how it enters the fit and how big it is.

    analysis/systematicsReport.py RabbitFits_.../tensor_SR_decisions.csv

Reads the decision table written by analysis/prepareTensor.py and collapses it
to one row per nuisance parameter:

  written     shape  - full up/down templates, so this nuisance carries the
                       normalisation AND the shape change of the systematic
                       (rabbit has no norm/shape decorrelation; a split would
                       need two separate nuisances)
              norm   - only the integral ratio survived the flat-line test, so
                       flat kappa_up/kappa_down templates are written
              mixed  - shape in some (category, process), norm in others
              lnN    - a card lnN, written with add_norm_systematic
              DROPPED- nothing left after the no-op and relevance cuts
  max |dN|/N   largest per-bin variation relative to the process itself
  max |dN|/tot largest per-bin variation relative to the total prediction
  norm effect  largest |kappa - 1| for the entries written as normalisation
"""

import argparse
import csv
import os
import sys
from collections import defaultdict


def load(path):
    with open(path) as fh:
        return list(csv.DictReader(fh))


def num(x, default=0.0):
    try:
        return float(x)
    except (TypeError, ValueError):
        return default


def _kappa_effect(kappa):
    """Relative size of an lnN kappa; kappa may be scalar or an (up, down) pair."""
    if isinstance(kappa, tuple):
        return max(abs(kappa[0] - 1), abs(kappa[1] - 1))
    return kappa - 1


def build(rows, lnN_names):
    per = defaultdict(lambda: {"shape": 0, "norm": 0, "dropped": 0, "entries": 0,
                               "rel_proc": 0.0, "rel_tot": 0.0, "kappa": 0.0,
                               "sym": set(), "cats": set(), "procs": set()})
    for r in rows:
        d = per[r["systematic"]]
        d["entries"] += 1
        dec = r["decision"]
        if dec.startswith("dropped"):
            d["dropped"] += 1
            continue
        d[dec] += 1
        d["cats"].add(r["category"])
        d["procs"].add(r["process"])
        d["rel_proc"] = max(d["rel_proc"], num(r["rel_process"]))
        d["rel_tot"] = max(d["rel_tot"], num(r["rel_total"]))
        if r["symmetrize"]:
            d["sym"].add(r["symmetrize"].split(" ")[0])
        for k in ("kappa_up", "kappa_down"):
            if r[k]:
                d["kappa"] = max(d["kappa"], abs(num(r[k], 1.0) - 1.0))

    out = []
    for name, d in per.items():
        if d["shape"] and d["norm"]:
            kind = "mixed"
        elif d["shape"]:
            kind = "shape"
        elif d["norm"]:
            kind = "norm"
        else:
            kind = "DROPPED"
        out.append({"systematic": name, "written": kind,
                    "n_shape": d["shape"], "n_norm": d["norm"],
                    "n_dropped": d["dropped"], "n_entries": d["entries"],
                    "categories": len(d["cats"]), "processes": len(d["procs"]),
                    "max_rel_process": round(d["rel_proc"], 5),
                    "max_rel_total": round(d["rel_tot"], 6),
                    "max_norm_effect": round(d["kappa"], 5),
                    "symmetrize": "/".join(sorted(d["sym"])) or "-"})
    for name, kappa in sorted(lnN_names.items()):
        out.append({"systematic": name, "written": "lnN", "n_shape": 0, "n_norm": 0,
                    "n_dropped": 0, "n_entries": 0, "categories": 0,
                    "processes": len(kappa[1]), "max_rel_process": round(_kappa_effect(kappa[0]), 5),
                    "max_rel_total": "", "max_norm_effect": round(_kappa_effect(kappa[0]), 5),
                    "symmetrize": "symmetric"})
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("decisions", help="<tensor>_decisions.csv")
    p.add_argument("-o", "--out", default=None, help="CSV to write (default: next to the input)")
    p.add_argument("--year", default="2024")
    p.add_argument("--top", type=int, default=25, help="rows printed; 0 prints all")
    args = p.parse_args()

    from configs import model as M

    rows = build(load(args.decisions), M.lnN_systematics(args.year))
    rows.sort(key=lambda r: -(r["max_rel_total"] or 0))

    kinds = defaultdict(int)
    for r in rows:
        kinds[r["written"]] += 1
    print(f"{len(rows)} nuisance parameters: "
          + "  ".join(f"{k}={v}" for k, v in sorted(kinds.items())))
    print()
    hdr = f"{'systematic':<38}{'written':<9}{'shape':>6}{'norm':>6}{'drop':>6}" \
          f"{'|dN|/N':>9}{'|dN|/tot':>10}{'norm eff':>10}  symmetrize"
    print(hdr)
    print("-" * len(hdr))
    shown = rows if args.top == 0 else rows[: args.top]
    for r in shown:
        rt = r["max_rel_total"]
        print(f"{r['systematic']:<38}{r['written']:<9}{r['n_shape']:>6}{r['n_norm']:>6}"
              f"{r['n_dropped']:>6}{r['max_rel_process']:>9.3f}"
              f"{(f'{rt:.4f}' if rt != '' else '-'):>10}"
              f"{r['max_norm_effect']:>10.3f}  {r['symmetrize']}")
    if args.top and len(rows) > args.top:
        print(f"... {len(rows) - args.top} more, full table in the CSV")

    out = args.out or os.path.splitext(args.decisions)[0].replace("_decisions", "") \
        + "_systematics_report.csv"
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"\nwrote {out}")


if __name__ == "__main__":
    sys.exit(main())
