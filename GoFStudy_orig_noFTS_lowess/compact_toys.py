#!/usr/bin/env python3
"""Compact a set of toy-batch hdf5 files into one small .npz summary, then
delete the bulky originals.

Each toy batch keeps a full fit-result payload (covariance, parms histogram,
etc.) per toy for a GoF study that only ever reads two scalars:
nllvalreduced and ndfsat. Measured cost: ~1.1 MB/toy. This script extracts
those two arrays (plus a manifest of source files, for provenance) into one
.npz of a few KB, verifies it round-trips before deleting anything, and only
then removes the original batch files.

    python3 compact_toys.py rabbit/toyGoF_SR_observed_batch{}.hdf5 1 16 313 \
        -o rabbit/toyGoF_SR_observed_summary.npz --delete-originals
"""

import argparse
import os
import sys

import numpy as np

from rabbit import io_tools


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pattern", help="path with {} for the batch index, e.g. "
                                    "'rabbit/toyGoF_SR_observed_batch{}.hdf5'")
    ap.add_argument("first_batch", type=int)
    ap.add_argument("last_batch", type=int)
    ap.add_argument("toys_per_batch", type=int)
    ap.add_argument("-o", "--output", required=True)
    ap.add_argument("--delete-originals", action="store_true",
                    help="remove the source batch files after a verified write")
    args = ap.parse_args()

    q, ndf, source = [], [], []
    missing = []
    for k in range(args.first_batch, args.last_batch + 1):
        path = args.pattern.format(k)
        if not os.path.exists(path):
            missing.append(path)
            continue
        n_ok = 0
        for t in range(1, args.toys_per_batch + 1):
            try:
                fr, _ = io_tools.get_fitresult(path, result=f"toy{t}", meta=True)
                q.append(2.0 * float(np.asarray(fr["nllvalreduced"])))
                ndf.append(int(np.asarray(fr["ndfsat"])))
                source.append(f"{os.path.basename(path)}:toy{t}")
                n_ok += 1
            except (KeyError, ValueError):
                break
        print(f"  {os.path.basename(path)}: {n_ok}/{args.toys_per_batch} toys")

    if missing:
        print(f"WARNING: {len(missing)} batch file(s) missing: {missing}", file=sys.stderr)

    q = np.asarray(q)
    ndf = np.asarray(ndf)
    if len(q) == 0:
        raise SystemExit("no toys extracted, refusing to write an empty summary")

    np.savez(args.output, q=q, ndf=ndf, source=np.asarray(source))
    print(f"wrote {args.output}: {len(q)} toys, ndf consistent="
         f"{len(set(ndf.tolist())) == 1}")

    # verify round-trip before touching anything
    check = np.load(args.output)
    assert len(check["q"]) == len(q) and np.allclose(check["q"], q), \
        "round-trip verification failed, NOT deleting originals"
    print("round-trip verified OK")

    if args.delete_originals:
        freed = 0
        for k in range(args.first_batch, args.last_batch + 1):
            path = args.pattern.format(k)
            if os.path.exists(path):
                freed += os.path.getsize(path)
                os.remove(path)
        print(f"deleted {args.last_batch - args.first_batch + 1} originals, "
             f"freed {freed / 1e9:.2f} GB")


if __name__ == "__main__":
    main()
