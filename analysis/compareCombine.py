#!/usr/bin/env python3
"""Compare every fitted parameter between Combine and rabbit.

    analysis/compareCombine.py multidimfit.root fit_rabbit.hdf5 -o cmp.csv

Combine side: the RooFitResult 'fit_mdf' written by
    combine -M MultiDimFit --algo singles --saveFitResult ...
Rabbit side: analysis.rabbitResults.read_parameters (POIs already un-sqrt-ed).

Name mapping: Combine's rateParams are xsec_<proc> and the POI is r; rabbit
calls them xsec_<proc> and <signal process>. Nuisances share their names.
Needs ROOT, so run it with cmsenv active and the rabbit venv only for the
hdf5 read -- both work at once because setup_rabbit.sh keeps CMSSW on the path.
"""

import argparse
import csv
import sys

import numpy as np


def read_combine(path, result="fit_mdf"):
    import ROOT
    f = ROOT.TFile.Open(path)
    fr = f.Get(result)
    if not fr:
        raise SystemExit(f"{path}: no RooFitResult '{result}'")
    out = {}
    for p in fr.floatParsFinal():
        out[p.GetName()] = (p.getVal(), p.getError())
    consts = {p.GetName(): (p.getVal(), 0.0) for p in fr.constPars()}
    f.Close()
    return out, consts


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("combine", help="multidimfit*.root")
    ap.add_argument("rabbit", help="rabbit fit .hdf5")
    ap.add_argument("-o", "--out", default=None, help="write a CSV here")
    ap.add_argument("--poi-map", default="r=tt-vcb",
                    help="comma separated combine=rabbit renames")
    ap.add_argument("--result", default="fit_mdf")
    ap.add_argument("--rateparam-prefix", default="xsec_",
                    help="rabbit parameters with this prefix came from a Combine "
                         "rateParam, which the converter writes as an unconstrained "
                         "lnN; '' disables the back-transform")
    ap.add_argument("--rateparam-lnn", type=float, default=1.01,
                    help="the lnN step the converter used (rabbit/datacard_converter.py)")
    ap.add_argument("--tol-value", type=float, default=0.05,
                    help="flag |dv| / sigma above this")
    ap.add_argument("--tol-error", type=float, default=0.05,
                    help="flag |sigma_rabbit/sigma_combine - 1| above this")
    args = ap.parse_args()

    from analysis.rabbitResults import read_parameters

    comb, _ = read_combine(args.combine, args.result)
    rab = read_parameters(args.rabbit)

    ren = dict(kv.split("=") for kv in args.poi_map.split(",") if kv)
    comb = {ren.get(k, k): v for k, v in comb.items()}

    # rateParams: the converter turns them into unconstrained lnN, so rabbit
    # holds theta while combine holds the multiplier. When the tensor was built
    # by prepareTensor.py they are real POIs instead, already converted out of
    # the sqrt storage by read_parameters -- those must be left alone.
    if args.rateparam_prefix:
        from analysis.rabbitResults import poi_names
        rabbit_pois = set(poi_names(args.rabbit))
        lk = np.log(args.rateparam_lnn)
        for n in list(rab):
            if n.startswith(args.rateparam_prefix) and n not in rabbit_pois:
                th, sth = rab[n]
                v = float(np.exp(lk * th))
                rab[n] = (v, float(v * lk * sth))

    common = sorted(set(comb) & set(rab))
    only_c = sorted(set(comb) - set(rab))
    only_r = sorted(set(rab) - set(comb))

    rows = []
    for n in common:
        vc, ec = comb[n]
        vr, er = rab[n]
        ref = ec if ec > 0 else 1.0
        rows.append({
            "parameter": n,
            "combine_value": vc, "combine_error": ec,
            "rabbit_value": vr, "rabbit_error": er,
            "dvalue_over_sigma": (vr - vc) / ref,
            "error_ratio": er / ec if ec > 0 else np.nan,
        })

    rows.sort(key=lambda r: -abs(r["dvalue_over_sigma"]))

    print(f"{len(common)} shared parameters, {len(only_c)} combine-only, "
          f"{len(only_r)} rabbit-only")
    if only_c:
        print(f"  combine-only: {only_c[:12]}{' ...' if len(only_c) > 12 else ''}")
    if only_r:
        print(f"  rabbit-only : {only_r[:12]}{' ...' if len(only_r) > 12 else ''}")

    dv = np.array([r["dvalue_over_sigma"] for r in rows])
    er = np.array([r["error_ratio"] for r in rows])
    print(f"\n  |dvalue|/sigma : max {np.nanmax(np.abs(dv)):.3f}  "
          f"median {np.nanmedian(np.abs(dv)):.4f}")
    print(f"  error ratio    : min {np.nanmin(er):.3f}  max {np.nanmax(er):.3f}  "
          f"median {np.nanmedian(er):.4f}")

    bad = [r for r in rows
           if abs(r["dvalue_over_sigma"]) > args.tol_value
           or abs(r["error_ratio"] - 1) > args.tol_error]
    print(f"\n  {len(bad)} parameters outside tolerance "
          f"(dv/sigma > {args.tol_value}, |ratio-1| > {args.tol_error})")
    print(f"\n{'parameter':<38} {'combine':>18} {'rabbit':>18} {'dv/sig':>8} {'err ratio':>10}")
    for r in bad[:40]:
        print(f"{r['parameter']:<38} {r['combine_value']:>9.4f}+-{r['combine_error']:<7.4f} "
              f"{r['rabbit_value']:>9.4f}+-{r['rabbit_error']:<7.4f} "
              f"{r['dvalue_over_sigma']:>8.3f} {r['error_ratio']:>10.3f}")

    if args.out:
        with open(args.out, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
        print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
