#!/usr/bin/env python3
"""Full Combine <-> rabbit matrix: every parameter, value and error, no cut.

    analysis/validationMatrix.py Validation_200826

Writes one wide CSV per configuration (SR / CR / CRo) under <outdir>:
matrix_<cfg>.csv, with one row per parameter (union over all setups) and a
value+error column pair for each setup A-E:

    A = combine default Hesse      B = combine robustHesse
    C = rabbit our workflow        E = rabbit combine-converter
    D_raw / D_smOnly / D_isoNorm / D_isoPrune = rabbit pieces isolated

Reuses the readers in analysis/validationReport.py (same rateParam->lnN
back-transform and r<->tt-vcb rename). Needs ROOT (cmsenv) + rabbit venv.
"""

import argparse
import csv
import os
import sys

from analysis.validationReport import combine_params, rabbit_params, RENAME, CONFIGS

# label -> (kind, filename template under combine/ or rabbit/)
SETUPS = [
    ("A_combine_default", "combine", "multidimfit{cfg}_default.root"),
    ("B_combine_robust",  "combine", "multidimfit{cfg}_robust.root"),
    ("C_rabbit_ours",     "rabbit",  "B_{cfg}.hdf5"),
    ("Cnew_rabbit_retuned", "rabbit", "Cnew_{cfg}.hdf5"),
    ("E_rabbit_converter", "rabbit", "A_{cfg}.hdf5"),
    ("D_raw",      "rabbit", "Draw_{cfg}.hdf5"),
    ("D_smOnly",   "rabbit", "DsmOnly_{cfg}.hdf5"),
    ("D_isoNorm",  "rabbit", "DisoNorm_{cfg}.hdf5"),
    ("D_isoPrune", "rabbit", "DisoPrune_{cfg}.hdf5"),
]


def _sort_key(name):
    # POIs first (tt-vcb, then xsec_*), then nuisances alphabetically
    if name == "tt-vcb":
        return (0, "")
    if name.startswith("xsec_"):
        return (1, name)
    return (2, name)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("outdir")
    args = ap.parse_args()
    C = os.path.join(args.outdir, "combine")
    R = os.path.join(args.outdir, "rabbit")

    for cfg, label in CONFIGS:
        cols = {}          # setup label -> {param: (val, err)}
        for name, kind, tpl in SETUPS:
            base = C if kind == "combine" else R
            path = os.path.join(base, tpl.format(cfg=cfg))
            try:
                d = combine_params(path) if kind == "combine" else rabbit_params(path)
            except Exception:
                d = {}
            if kind == "combine":                       # unify r -> tt-vcb
                d = {RENAME.get(k, k): v for k, v in d.items()}
            cols[name] = d

        params = sorted({p for d in cols.values() for p in d}, key=_sort_key)
        out = os.path.join(args.outdir, f"matrix_{cfg}.csv")
        header = ["parameter"]
        for name, _, _ in SETUPS:
            header += [f"{name}_val", f"{name}_err"]
        with open(out, "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(header)
            for p in params:
                row = [p]
                for name, _, _ in SETUPS:
                    v = cols[name].get(p)
                    row += ["", ""] if v is None else [f"{v[0]:.6g}", f"{v[1]:.6g}"]
                w.writerow(row)
        present = [n for n, _, _ in SETUPS if cols[n]]
        print(f"{cfg:4s} {label:20s} {len(params):4d} parameters -> {out}")
        print(f"       setups present: {', '.join(present)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
