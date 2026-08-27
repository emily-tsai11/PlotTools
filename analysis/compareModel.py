#!/usr/bin/env python3
"""Compare a rabbit tensor against a Combine datacard without fitting anything.

    analysis/compareModel.py tensor.hdf5 card.txt

Answers three questions from the inputs alone:

  a) do the shapes close?   per (channel, process) yields and data, tensor vs card
  b) is the model the same? processes, signal flags, free parameters, systematics
  c) who scales what?       which process each free parameter multiplies, and
                            which (channel, process) each nuisance touches

Systematics that the card declares but the tensor does not carry are expected
when the tensor came from analysis/prepareTensor.py: that is the pruning. They
are listed so the pruning is visible rather than silent.
"""

import argparse
import os
import sys
from collections import defaultdict

import numpy as np


def load_tensor(path):
    from rabbit.inputdata import FitInputData
    from rabbit.debugdata import FitDebugData
    indata = FitInputData(path)
    return indata, FitDebugData(indata)


def load_card(path):
    from rabbit.datacard_parser import DatacardParser
    p = DatacardParser()
    p.parse_file(path)
    return p


def dec(x):
    return x.decode() if isinstance(x, bytes) else str(x)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("card")
    ap.add_argument("tensors", nargs="+", metavar="NAME=PATH",
                    help="one or more tensors to compare against the card")
    ap.add_argument("--tol", type=float, default=1e-3,
                    help="relative yield tolerance")
    ap.add_argument("--show", type=int, default=12, help="rows per listing")
    args = ap.parse_args()

    card = load_card(args.card)
    tens = {}
    for spec in args.tensors:
        name, _, path = spec.partition("=")
        tens[name or os.path.basename(path)] = load_tensor(path)

    print("=" * 92)
    print("a) shapes: every tensor against the card")
    print("=" * 92)
    print(f"{'tensor':<12}{'channels':>10}{'masked':>8}{'procs':>7}{'systs':>7}"
          f"{'free':>6}{'yield pairs off':>17}{'data off':>10}")
    info = {}
    for name, (indata, dbg) in tens.items():
        tproc = [dec(p) for p in indata.procs]
        chans = list(indata.channel_info)
        masked = [c for c, i in indata.channel_info.items() if i.get("masked", False)]
        bad = 0
        for ch in chans:
            h = dbg.nominal_hists[ch]
            for p in tproc:
                if (ch, p) not in card.rates:
                    continue
                tv = float(h[{"processes": p}].values().sum())
                cv = float(card.rates[(ch, p)])
                if abs(cv) > 0 and abs(tv - cv) / abs(cv) > args.tol:
                    bad += 1
        dbad = 0
        for ch in chans:
            if ch in masked:
                continue
            tv = float(dbg.data_obs_hists[ch].values().sum())
            cv = float(card.observations.get(ch, np.nan))
            if np.isfinite(cv) and abs(tv - cv) > 0.5:
                dbad += 1
        tsyst = [dec(x) for x in indata.systs]
        tfree = [dec(x) for x in indata.systsnoconstraint]
        info[name] = dict(procs=tproc, chans=chans, masked=masked, systs=tsyst,
                          free=tfree, dbg=dbg, indata=indata)
        print(f"{name:<12}{len(chans):>10}{len(masked):>8}{len(tproc):>7}"
              f"{len(tsyst):>7}{len(tfree):>6}{bad:>17}{dbad:>10}")
    print(f"\ncard: {len(card.bins)} channels, {len(card.processes)} processes, "
          f"{len(card.systematics)} systematics, {len(card.rate_params)} rateParams")

    print()
    print("=" * 92)
    print("b) processes and free parameters")
    print("=" * 92)
    csig = [p for p in card.processes if card.process_indices.get(p, 1) <= 0]
    print(f"card signal (process index <= 0): {csig}")
    for name, d in info.items():
        sig = [dec(x) for x in d["indata"].signals]
        print(f"  {name:<12} signal {sig}   "
              f"processes match card: {set(d['procs']) == set(card.processes)}   "
              f"unconstrained in tensor: {sorted(d['free']) if d['free'] else 'none (supplied by --paramModel)'}")
    print("\ncard rateParams -- which process each one scales:")
    for parts in card.rate_params:
        print(f"  {parts[0]:<14} scales '{parts[2]}' in channel '{parts[1]}'")

    print()
    print("=" * 92)
    print("c) nuisances: which one touches what")
    print("=" * 92)
    csyst = {x["name"]: x for x in card.systematics}
    cactive = defaultdict(set)
    for nm, x in csyst.items():
        # For a shape row "1" is the normal marker that the shape applies. For a
        # lnN row "1" is a kappa of one, so it has no effect.
        dead = ("-", "0", "1", "1.0") if x["type"] in ("lnN", "lnU") else ("-", "0")
        for (ch, p), eff in x["effects"].items():
            if eff not in dead:
                cactive[nm].add((ch, p))

    tactive = {}
    for name, d in info.items():
        act = defaultdict(set)
        for ch in d["chans"]:
            v = d["dbg"].syst_active_hists[ch].values()
            for ip, p in enumerate(d["procs"]):
                for isy, sname in enumerate(d["systs"]):
                    if v[ip, isy] > 0:
                        act[sname].add((ch, p))
        tactive[name] = act

    print(f"{'tensor':<12}{'systs':>7}{'missing vs card':>17}{'extra':>7}"
          f"{'(chan,proc) entries':>21}{'card entries':>14}")
    ncard_entries = sum(len(v) for v in cactive.values())
    for name, d in info.items():
        miss = len(set(csyst) - set(d["systs"]))
        extra = len(set(d["systs"]) - set(csyst) - set(d["free"]))
        nent = sum(len(v) for v in tactive[name].values())
        print(f"{name:<12}{len(d['systs']):>7}{miss:>17}{extra:>7}{nent:>21}{ncard_entries:>14}")

    # per-systematic coverage, worst offenders for each tensor
    for name, d in info.items():
        rows = []
        for sname in sorted(set(d["systs"]) & set(csyst)):
            t, c = tactive[name][sname], cactive[sname]
            if t != c:
                rows.append((sname, len(c), len(t)))
        print(f"\n  {name}: {len(rows)} shared systematics with different coverage")
        for sname, nc, nt in sorted(rows, key=lambda r: -(r[1] - r[2]))[: args.show]:
            print(f"    {sname:<40} card {nc:>4}   tensor {nt:>4}")

    lnn = sorted(n for n, x in csyst.items() if x["type"] in ("lnN", "lnU"))
    print(f"\n  lnN in card ({len(lnn)}): {lnn}")
    for name, d in info.items():
        print(f"    present in {name:<12}: {sorted(n for n in lnn if n in d['systs'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
