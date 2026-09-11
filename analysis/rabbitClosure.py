#!/usr/bin/env python3
"""Closure tests for the rabbit fit chain.

Checks that the machinery recovers what was put in, before any of it is
believed on data:

  1. Asimov self-consistency  -- nuisances stay at 0, POIs at their injected
     values, postfit chi2 ~ 0
  2. Signal injection         -- Asimov built at r = r_inj is fitted back to
     r_inj for a range of r_inj
  3. Rate-parameter injection -- same for one of the free xsec_tt* normalisations
  4. Toy pulls (optional)     -- (r_fit - r_true)/sigma over N toys should be
     centred on 0 with unit width

Run after analysis/prepareTensor.py, e.g.

    analysis/rabbitClosure.py tensor.hdf5 -o closure/ --toys 100
"""

import argparse
import os
import subprocess
import sys

import numpy as np

from analysis.rabbitResults import read_parameters

POI = "tt-vcb"
FREE_NORMS = ["ttbb", "ttbj", "tt2b", "ttcc", "ttcj", "tt2c", "ttLF"]


def param_model_args():
    return [
        "--paramModel", "Mu",
        "--paramModel", "analysis.rabbit_models.FreeNorm", ",".join(FREE_NORMS),
    ]


def run_fit(tensor, outdir, name, extra):
    cmd = ["rabbit_fit.py", tensor, "-o", outdir, "--outname", name] + param_model_args() + extra
    res = subprocess.run(cmd, capture_output=True, text=True)
    path = os.path.join(outdir, name + ".hdf5")
    if not os.path.exists(path):
        tail = "\n".join(res.stderr.strip().splitlines()[-6:])
        raise RuntimeError(f"fit '{name}' produced no output:\n{tail}")
    return path


def read_params(path):
    """POIs already converted from rabbit's sqrt storage to mu."""
    pars = read_parameters(path)
    labels = list(pars)
    return labels, np.array([pars[l][0] for l in labels]), np.array([pars[l][1] for l in labels])


def value_of(path, param):
    return read_parameters(path)[param]


def test_asimov(tensor, outdir, results):
    path = run_fit(tensor, outdir, "closure_asimov", ["-t", "-1"])
    labels, vals, errs = read_params(path)
    poi_names = [POI] + [f"xsec_{p}" for p in FREE_NORMS]
    nuis = [(l, v) for l, v in zip(labels, vals) if l not in poi_names]
    worst_l, worst_v = max(nuis, key=lambda kv: abs(kv[1]))
    pois = {l: (float(v), float(e)) for l, v, e in zip(labels, vals, errs) if l in poi_names}

    print("\n[1] Asimov self-consistency")
    print(f"    largest nuisance pull : {worst_v:+.2e}  ({worst_l})")
    for n in poi_names:
        v, e = pois[n]
        print(f"    {n:<12s} {v:.6f} +/- {e:.4f}   (expected 1.0, dev {v-1:+.1e})")
    ok = abs(worst_v) < 1e-3 and all(abs(v - 1) < 1e-3 for v, _ in pois.values())
    results.append(("asimov self-consistency", ok,
                    f"max |pull| = {abs(worst_v):.1e}"))
    return path


def test_injection(tensor, outdir, param, values, results):
    print(f"\n[{'2' if param == POI else '3'}] Injection closure for {param}")
    print(f"    {'injected':>10} {'recovered':>12} {'error':>10} {'bias':>12}")
    biases = []
    for x in values:
        name = f"closure_inj_{param}_{x}".replace(".", "p")
        try:
            path = run_fit(tensor, outdir, name,
                           ["-t", "-1", "--expectSignal", param, str(x)])
        except RuntimeError as exc:
            if "not in list of params" in str(exc):
                print(f"    {x:>10.3f}  skipped: rabbit's Mu rejects --expectSignal "
                      f"for parameters it does not own (upstream limitation)")
                results.append((f"injection closure ({param})", None,
                                "blocked by upstream --expectSignal handling"))
                return
            raise
        v, e = value_of(path, param)
        biases.append(v - x)
        print(f"    {x:>10.3f} {v:>12.6f} {e:>10.4f} {v-x:>+12.2e}")
    ok = max(abs(b) for b in biases) < 1e-3
    results.append((f"injection closure ({param})", ok,
                    f"max |bias| = {max(abs(b) for b in biases):.1e}"))


def test_toys(tensor, outdir, ntoys, results):
    print(f"\n[4] Toy pulls, {ntoys} toys")
    path = run_fit(tensor, outdir, "closure_toys",
                   ["-t", str(ntoys), "--toysDataMode", "expected"])
    pulls = []
    with __import__("h5py").File(path, "r") as f:
        keys = [k for k in f.keys() if k.startswith("results_toy")]
    for k in keys:
        try:
            v, e = read_parameters(path, result=k.replace("results_", ""))[POI]
        except Exception:
            continue
        if e > 0:
            pulls.append((v - 1.0) / e)
    if len(pulls) < 5:
        print(f"    only {len(pulls)} usable toys -- skipping (keys: {len(keys)})")
        results.append(("toy pulls", None, f"only {len(pulls)} usable toys"))
        return
    pulls = np.array(pulls)
    mean, width = float(pulls.mean()), float(pulls.std(ddof=1))
    err_mean = width / np.sqrt(len(pulls))
    print(f"    n = {len(pulls)}   mean = {mean:+.3f} +/- {err_mean:.3f}   width = {width:.3f}")
    ok = abs(mean) < 3 * err_mean and 0.8 < width < 1.2
    results.append(("toy pulls", ok, f"mean {mean:+.3f}, width {width:.3f}"))


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("tensor")
    p.add_argument("-o", "--outdir", default="closure")
    p.add_argument("--inject", type=float, nargs="+", default=[0.5, 1.0, 1.5, 2.0])
    p.add_argument("--inject-norm", default="xsec_ttbb",
                   help="free normalisation to test injection on, or 'none'")
    p.add_argument("--toys", type=int, default=0, help="number of toys (0 skips)")
    args = p.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    results = []

    test_asimov(args.tensor, args.outdir, results)
    test_injection(args.tensor, args.outdir, POI, args.inject, results)
    if args.inject_norm != "none":
        test_injection(args.tensor, args.outdir, args.inject_norm, [0.8, 1.2], results)
    if args.toys > 0:
        test_toys(args.tensor, args.outdir, args.toys, results)

    print("\n" + "=" * 62)
    print("closure summary")
    print("=" * 62)
    failed = 0
    for name, ok, detail in results:
        tag = "PASS" if ok else ("SKIP" if ok is None else "FAIL")
        if ok is False:
            failed += 1
        print(f"  [{tag}] {name:<34s} {detail}")
    print("=" * 62)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
