# Writing a rabbit tensor: a practical guide

Standalone notes from building a rabbit input tensor for an analysis with several
free-floating background normalisations (real POIs, not lnN nuisances) and ~300+
shape systematics. Written to be reusable for a different analysis; nothing here
is specific to one repo.

## 1. Minimum viable tensor

```python
from rabbit import tensorwriter
import hist

w = tensorwriter.TensorWriter(
    sparse=False,
    clip_syst_variations=10.0,      # see section 3
    zero_syst_low_neff=1.0,         # see section 3 -- read the warning first
)

for channel, axis in channels.items():
    w.add_channel([axis], channel, masked=channel in masked_channels)
    if channel not in masked_channels:
        w.add_data(data_hist[channel], channel)
    for proc in processes:
        w.add_process(nominal_hist[channel, proc], proc, channel, signal=proc in signals)

# shape systematic: pass [up_hist, down_hist], or one hist + mirror=True
w.add_systematic([up_h, down_h], "syst_name", proc, channel, symmetrize=None)

# flat/lnN systematic: one kappa (or (up, down) tuple) per process, never a bare scalar with a process list
w.add_norm_systematic("norm_name", [proc], channel, [kappa], groups=["group_name"])

w.write(outfolder=out_dir, outfilename=out_name)
```

That part is straightforward and well documented in rabbit itself. Everything
below is what actually took time to get right.

## 2. Many free-floating normalisations

If several backgrounds float freely (not just the signal), decide **how** they
float before writing anything:

- **`FreeNorm`-style param model** (one unconstrained POI per process, value =
  the multiplier itself, `mu = x^2` internally under `allowNegativeParam=False`)
  reproduces a classic `rateParam` cleanly and gives you real POIs with proper
  profile-likelihood scans, impacts, everything.
- **An unconstrained lnN written into the tensor** (`add_norm_systematic(...,
  constrained=False)`) is *not* the same thing: rabbit stores it as
  `exp(ln(kappa) * theta)`, not as the multiplier directly, and it is **not** a
  POI (so no scan/blinding treatment).

Pick one per parameter and be consistent; don't let a converter silently give
you the second when you wanted the first (see 2.3).

### 2.1 Blinding bites every POI, not just the signal

`rabbit_fit.py` blinds **every** POI on an observed fit (`-t 0`) by default —
each gets multiplied by `exp(random)`. If your background normalisations are
real POIs (via a `FreeNorm`-style model), they get scrambled too, unless you
explicitly unblind them:

```
--unblind 'xsec_.*'        # fullmatch regex -- '^xsec_' would NOT match, be exact
```

The failure mode is nasty: the fit converges, the numbers look like real
results, and they are silently wrong. If a background-normalisation POI's
"result" looks scrambled/nonsensical on an observed fit and fine on Asimov,
check blinding before anything else.

### 2.2 Composite param models and `--expectSignal`

If you combine multiple param models (e.g. one for the signal, one `FreeNorm`
per background), a composite model can pass its **entire** `--expectSignal`
list to every submodel. A submodel that doesn't own a given parameter name can
raise instead of ignoring it. Filter to your own parameters inside the
submodel's constructor before calling `set_param_default`.

### 2.3 `add_norm_systematic`: pass one uncertainty per process, always

```python
# WRONG -- looks fine, silently wrong:
w.add_norm_systematic("lumi", all_processes, channel, 1.02)
# zip(process, uncertainty) truncates a scalar wrapped in a 1-list against N
# processes to the FIRST process only. lumi ends up applied to one process.

# RIGHT:
w.add_norm_systematic("lumi", all_processes, channel, [1.02] * len(all_processes))
```

Also: the asymmetric branch (`kappa` given as `(up, down)`) can require
`symmetrize="average"` to avoid an internal type error passing a list where a
single process name is expected. If you need a genuinely asymmetric,
non-averaged effect, write it as a flat shape variation via `add_systematic`
instead of `add_norm_systematic` — same physics, avoids the bug.

### 2.4 Reading the fit result back

A POI stored under `allowNegativeParam=False` is internally `x = sqrt(mu)`.
Reading `x` and its error as if it were `mu` understates the uncertainty by a
factor `2*sqrt(mu)` (a factor 2 at `mu=1`). Always transform:

```
mu = x**2
sigma_mu = 2 * abs(x) * sigma_x
```

Write one small helper that does this for every POI and use it everywhere;
never read `fitresult["parms"]` directly for a POI. Same story for a
free-normalisation POI's impacts: `impact_on_mu = impact_on_x * 2 * abs(x)`.

`nllvalreduced` is `delta-NLL`, not the saturated goodness-of-fit statistic —
that's `2 * nllvalreduced`.

## 3. Shape systematics

### 3.1 Undo any placeholder-bin convention before rabbit sees it

If the upstream shapes file was built for a tool that cannot take a literal
zero under a shape systematic (Combine can't), it likely has a small sentinel
value (e.g. `1e-6`) standing in for empty/negative bins. rabbit doesn't need
that. Restore those bins to zero at read time, or you'll get `log(varied /
1e-6)` ratios of up to `1e7` that vertical morphing (or your own smoother) will
treat as a real, huge, informative variation.

### 3.2 `clip_syst_variations` and `zero_syst_low_neff` — know what each does

- `clip_syst_variations=X`: clips every per-bin `logk` to `[1/X, X]`. Tames
  near-empty bins whose nominal is a statistical-cancellation residual.
- `zero_syst_low_neff=N`: at write time, for every `(bin, process)` with
  effective sample size `n_eff = sumw^2/sumw2 < N`, **every systematic's**
  `logk` in that bin is set to 0.

**The second one has a sharp edge**: it runs *after* your own shape-vs-norm
decisions. If you deliberately wrote a systematic as a flat normalisation
(constant `logk` across all bins), this can zero it in some bins only, so the
lever is no longer flat and its effective size no longer matches whatever you
recorded as its kappa. It's a broad hammer (zeros *every* systematic in the
low-`n_eff` bin, not just the one that misbehaves) and it hits your low-
statistics background templates hardest — which are usually the ones a
free-floating normalisation depends on most. Decide this deliberately, don't
leave it at a default you haven't checked against your lowest-stats process.

### 3.3 One-sided vs two-sided legs

Never silently drop a one-sided variation (no down leg, or vice versa) at
tensor-write time just because your writer expects a pair. Either write it
genuinely one-sided (rabbit supports this — asymmetric writer, `symmetrize=
None`), or mirror it about the nominal if the analysis convention requires a
symmetric pair. Silently dropping it deletes a real systematic effect while
your bookkeeping still claims it was kept.

### 3.4 Not every systematic is the same statistical object — classify first

Before smoothing or symmetrising anything, know which of these a systematic
is:

- **independent / alternative-sample** (a genuinely different MC sample vs
  nominal, e.g. colour-reconnection or tune variations): there is no "down"
  leg in any meaningful sense — one alternative vs nominal. Treat it
  one-sided. Never force it into an antisymmetric shape, and never smooth it
  as if it were noise around a smooth truth — the shape *is* the physics.
- **same-event weight variation** (up/down come from reweighting the *same*
  events as nominal): up, down, and nominal are highly correlated. `var_nom +
  var_leg` (the naive sum of the two histograms' `Sumw2`) **overestimates**
  `var(leg - nominal)` by orders of magnitude (roughly `2/eps^2` for a
  relative variation of size `eps`; at `eps ~ 1%` that's a factor ~10^4). Any
  significance test or smoothing-weight built on the naive sum will be
  systematically miscalibrated. If you can't store the exact quantity (`sum(w^2
  (r-1)^2)`, only available at histogram-fill time), an empirical estimator
  from the ratio's own bin-to-bin scatter (e.g. second differences, MAD-based)
  is far closer than the naive sum.
- **migration-class** (same events, but they move between bins/categories,
  e.g. a jet energy scale shift): genuinely couples a shape change to a yield
  change. If your smoother factors shape and normalisation apart (recommended,
  see below), decide explicitly whether that's appropriate here — for a
  systematic where the yield change *is* real physics, forcing exact yield
  preservation and a smoother that doesn't may legitimately disagree.

Get this classification into your model config once, keyed by systematic name
or pattern, and have every downstream step (significance test, smoothing,
symmetrisation) consult it. Don't apply one blanket treatment to every
systematic — that is the single most consequential design mistake to avoid.

### 3.5 If you smooth: factor norm from shape, and bound the rescale

If statistical smoothing is warranted for some class of systematic (typically
same-event weight variations with real per-bin noise):

- **Factor the integral (yield ratio) out before smoothing, restore it after.**
  Smoothing should never be able to move a yield. Fit only the shape-only
  residual; rescale the smoothed shape back onto each leg by least squares;
  restore the leg's original integral over the bins you actually rewrote (not
  over the whole histogram, or you'll push yield into/out of bins you didn't
  touch).
- **A bin with zero estimated uncertainty must get zero weight, not infinite
  weight.** Flooring a zero variance to something tiny inverts this and lets
  one meaningless bin pin the whole smoothing fit.
- **Bound the least-squares rescale factor.** An unbounded fit can blow up on
  a poorly-fitting basis (we saw factors of -100+ on real data). Clip it (e.g.
  `[-10, 10]`) and flag when the clip fires — that flag is telling you the
  smoothed shape doesn't actually describe that leg.
- **Never let the antisymmetric-basis trick manufacture a one-sided systematic
  into a fake two-sided one, or vice versa.** If you rebuild one leg from the
  other (e.g. because one leg is known-broken upstream), that's a deliberate,
  documented choice — write down which leg you trust and why, and don't smooth
  a leg you've already synthesised as if it carried independent information.

### 3.6 Order matters: classify shape-vs-flat before or after smoothing?

A statistical test for "is this shape actually flat" run on the **raw, noisy**
input will under-detect real small shape effects — the noise swamps them, the
flat-fit passes, and a real (if modest) systematic gets written as a flat
normalisation instead of a shape, discarding per-bin information. Running the
same test **after** smoothing is materially more powerful (in one real
analysis, ~37% of shape/norm decisions changed on a shape-vs-flat threshold of
p=0.05 depending purely on this ordering, concentrated in the systematics with
the largest coherent effect on the total prediction).

The catch: after smoothing, *any* residual curvature — including one a smoother
manufactures out of a handful of near-empty bins — will register as
"significant", because the test's implied uncertainty shrinks along with the
smoothing. On genuinely low-statistics bins (single-digit event counts), don't
trust a p-value computed post-smoothing at face value; check the underlying
statistics before accepting the classification.

## 4. Validation strategy that actually catches bugs

- **Build two independent paths to the same tensor and diff them.** One
  "verbatim converter" leg that goes straight from an existing, already-
  validated format (e.g. a Combine datacard) through rabbit's own converter,
  and one leg through your own hand-built tensor writer from the raw shapes.
  Any unexplained difference between the two on a clean input is a bug in your
  writer, not a physics effect. This is the single most effective check
  available.
- **Validate on your cleanest available input first**, before your messiest.
  If you have both a "raw" and a "cleaned/pre-processed" version of the same
  shapes, get agreement with Combine on the clean one before trying to explain
  disagreement on the raw one — otherwise you can't tell whether a divergence
  is your tensor-writing code or genuinely a difference in the two inputs.
- **Make every transformation step independently switchable** (smoothing on/
  off, classification threshold, pruning threshold, symmetrisation policy,
  each behind its own flag). When something disagrees with a reference, you
  can then isolate it to one step by literally turning steps off one at a
  time, rather than guessing. Trying to reason about a multi-step pipeline's
  aggregate effect without this is close to impossible once you have hundreds
  of systematics.
- **Sanity-check the minimiser actually ran.** If every parameter comes back
  at exactly its starting value on a real (non-Asimov) fit, the minimiser
  silently failed, not converged instantly — check the fit log for an
  exception being swallowed. This is nastier than it sounds: Asimov fits can
  look fine (the start point often *is* the Asimov solution) while every real
  fit is silently broken.
- **Cross-check the default Hessian.** A default Minuit-style Hessian can be
  measurably wrong on a model with many correlated nuisances and free norms
  (we saw systematic ~3% deficits on unconstrained-by-data nuisances, and
  factor-of-many discrepancies on a POI's error between configurations that
  shouldn't differ that much). Compare against a more robust Hessian
  computation before trusting parameter *errors* (the central values from a
  profile scan are usually fine regardless).

## 5. One-paragraph summary

Get the tensor structurally right first (channels, processes, data, masking),
then treat "which systematics are POIs vs nuisances, and how they're
blinded" as its own careful design step — that's where free-floating-parameter
analyses go wrong first. For shape systematics, classify by statistical class
before doing anything to them, keep smoothing's effect on yield to exactly
zero, and never trust one blanket treatment for all ~hundreds of them. Validate
by diffing two independent conversion paths on your cleanest input, with every
processing step behind its own on/off switch.
