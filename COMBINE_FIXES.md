# Things to fix on the Combine side

Found while building the rabbit path (`analysis/prepareTensor.py`). All of these
affect the **current Combine results**, independently of the migration. Ordered
by how much they matter.

## 1. `analysis/smoothing.py`: the systematic allowlist is dead

`bypassSmoothing = True` (line 20) and the hardcoded `matchSyst(syst_, bypass=True)`
at the call site (line 350) mean `listToSmooth` is never consulted. **Every** one
of the ~385 systematics is spline-smoothed, including two-point and
alternative-sample variations (`CR1`, `CR2`, `tune_CP5`, `topHdampWeight_*`, the
whole `PS_isr/fsr_*` family). Smoothing a genuine two-point variation is not
noise reduction, it reshapes the systematic.

## 2. `analysis/smoothing.py`: `unweightedSpline` is not unweighted

```python
if 'un' in args.method:      # line 210 -- args.method is a LIST, e.g. ['unweightedSpline']
    weights = None
```
`'un' in ['unweightedSpline']` is `False` (list membership, not substring), so
weights are always applied and both methods run the *weighted* spline. Also
`args` is a module-level global, so importing the module and calling
`get_smoothed_up_and_down` directly (as `testSmoothing.py` does) raises
`NameError`.

## 3. `analysis/smoothing.py`: wrong spline weight convention and no smoothing factor

`w = 1./variance` (line 213), but `scipy.interpolate.UnivariateSpline` expects
`w = 1/sigma`. High-statistics bins are over-weighted quadratically, and empty
bins give `inf`. No `s` is set, so scipy's default `s = len(w)` is applied to a
weight array that is not `1/sigma` — the amount of smoothing is effectively
uncontrolled and changes with binning and normalisation.

`analysis/templateSmoothing.py` shows the corrected version: `w = 1/sigma`, and
`s = n_bins` so the stopping criterion is chi2/ndf ~ 1.

## 4. Sentinel bins create variation/nominal ratios up to 10^7

In `Datacards_100626_ge2bge1c_fix_clean_forJME/orig/Vcb_SL_2024_shapes.root`:

- 1,919 bins sit at exactly the 1e-6 placeholder, in 1,903 templates,
  concentrated in `ttbb-dps` (901), `tt2b-dps` (462), `wjets` (192), `ttW` (188),
  `ttZ` (160)
- 1,565 bins have content > 0 but **zero stored variance**
- `|log(varied/nominal)|` reaches **16.2**, i.e. a factor of ~10^7

Example: `Vcb_catCC_CR/wjets` bin 7 has nominal 1e-6 and
`jes_FlavorQCDUp` = 2.37. Combine's vertical morphing then holds a real ~2.4
event handle built on a placeholder. Neither the relevance cut nor a low-`n_eff`
guard catches this (`n_eff` there is infinite, since the variance is 0).

The rabbit path undoes the placeholder (`--sentinel-policy restore-zero`). On the
Combine side the floor is needed, so the fix has to be either a shape-systematic
suppression in those bins or a rebinning that avoids empty bins altogether.

## 5. `analysis/simplifyDatacards.py`: the pathological-systematic branch is contradictory

```python
if (any(abs(1.-x) < (1./2.0) for x in vals) or any(abs(1.-x) > (1.*2.0) for x in vals)) \
   and (yields[1] < 1. or yields[2] < 1.) and (yields[0] > 10.):
```
A genuine collapse (nominal 12 events, varied 0.4) gives `|1-x| ~ 0.97`, which is
neither `< 0.5` nor `> 2.0`, so it falls through to the `elif` and is converted to
a **lnN of ~0.03** instead of being dropped. A census of the current templates
found **zero** cases that trigger this branch as written.

## 6. `analysis/simplifyDatacards.py`: verbosity is hardcoded

`interface.verbosity = 99` (line 361) and `writer.SetVerbosity(99)` (line 387),
with no `-v` option. Hence the 1.4 MB `simplify_*.log` files; a significant
fraction of the runtime is printing.

Smaller: `load_rate_values` does `vals = vals[0]` before any emptiness check, so
a missing systematic raises `IndexError` rather than reaching the intended
"Could not find uncertainty" message (that `else` branch in `ratify` is
unreachable). The `make_symmetric` block is never called with `True`.

## 7. Store sumw2 of the *difference* at fill time

The blocker for a proper significance test. For a weight-based systematic the
varied and nominal histograms come from the same events, so
`var(varied - nominal)` is **not** recoverable from the two stored sumw2 arrays:

| estimator | overestimates var(shift) by | at eps = 0.002 |
|---|---|---|
| `var_nom + var_syst` | 2/eps^2 | 500,000x |
| `abs(var_syst - var_nom)` (Barlow) | 2/eps | 1,000x |

The exact quantity is `sum(w^2 (r-1)^2)`, which `prepareHistosForCards.py` could
fill into a companion histogram at essentially no cost. With it, the
"is this systematic statistically significant" test becomes exact instead of
being disabled (see `--p-shift` in `analysis/prepareTensor.py`).

## 8. Wire `prepareDatacards.py` to `configs/model.py`

The lnN values, rateParams, category->distribution map and process lists are now
defined in `configs/model.py`. `prepareDatacards.py` still carries its own copy;
until it imports the shared module the two backends can drift apart silently.

## 9. `fixNegativeBins.py`: integral check inside the bin loop

```python
for i in range(1, h.GetNbinsX() + 1):
    ...
    if h.Integral(1, h.GetNbinsX()) == 0:
        h.SetBinContent(1, EPSILON)
```
The integral test runs once per bin rather than once per histogram, and always
writes to bin 1. Harmless in effect but it is not what the code intends.

---

# Upstream rabbit bugs found while building this

Both are worked around in `analysis/prepareTensor.py`; neither is fixed in the
`rabbit/` checkout. Worth reporting upstream.

## `add_norm_systematic` silently drops processes

```python
for p, u in zip(process, uncertainty):
```
A scalar `uncertainty` with a list of N processes passes the length check
(`len(uncertainty) != 1 and len(process) != len(uncertainty)`) but `zip` then
truncates to the **first process only**. An lnN declared for 18 processes is
applied to 1. Workaround: always pass one uncertainty per process.

## `add_norm_systematic` crashes for asymmetric uncertainties unless symmetrize="average"

The asymmetric branch calls `_compute_asym_syst(..., process, ...)` with the
whole `process` list instead of the loop variable `p`, so
`book_logk_halfdiff` -> `book_logk` does `self.dict_norm[channel][process]` with
a list and raises `TypeError: unhashable type: 'list'`. Only reachable when
`symmetrize` is not `"average"`, because the other paths do not call
`book_logk_halfdiff`. Workaround: write asymmetric normalisation effects as flat
shape variations through `add_systematic`, which handles the process correctly.

## POI values and errors are stored as sqrt(mu), not mu

Not a bug, but the easiest way to get a wrong answer. `rabbit_fit.py` writes
`values=fitter.x` into the `parms` histogram — the *internal* parameter vector.
With the default `allowNegativeParam=False` a POI is stored there as `sqrt(mu)`
(the transform enforcing `mu >= 0`), so

    x = sqrt(mu)        sigma_x = sigma(mu) / (2 sqrt(mu))

`rabbit_print_pulls_and_constraints.py` prints `x` and `sigma_x`. Reading those
as `mu` understates the uncertainty by `2*sqrt(mu)` -- a factor 2 at `mu = 1`.
Verified against `--allowNegativeParam` (which disables the transform): all 8
POIs agree to a ratio of 1.000.

Use `analysis/rabbitResults.read_parameters()`, which applies
`mu = x^2`, `sigma_mu = 2|x| sigma_x` to the parameters listed in `meta["pois"]`
and leaves nuisances alone.

## `Mu` rejects `--expectSignal` for parameters it does not own

In a `CompositeParamModel` every submodel receives the full `--expectSignal`
list, and `set_param_default` raises `ValueError: <name> not in list of params`
for any entry it does not own. So `--expectSignal xsec_ttbb 0.8` fails as soon as
`Mu` is also in the composite. `analysis/rabbit_models.FreeNorm` filters the list
to its own parameters to avoid the mirror-image problem; `Mu` upstream does not,
which blocks injection tests on the free normalisations.

## CRITICAL: the minimiser silently did not run (SciPy 1.10)

`fitter.py:75` -- the `scipy.optimize.minimize` callback does
`intermediate_result.fun`. That is the SciPy >= 1.11 callback signature. SciPy
1.10, which CMSSW_15_0_10 ships, calls `callback(xk)` with a plain ndarray, so
the callback raises `AttributeError` on its first call. `fitter.py:2324` catches
it, restores `callback.xval` (the starting point), sets
`minimizer_result = None`, and logs the exception at DEBUG level only.

Result: every fit returned its starting values. Verified -- an observed CR fit
came back with all 7 POIs at exactly 1.0 and all 218 nuisances at exactly 0.0.

Consequences:
 * Asimov results were still CORRECT: the start point is the Asimov minimum, so
   zero iterations lands on the right answer and the Hessian there is the right
   one. The Combine comparison (0.4-0.9 % agreement) is unaffected.
 * No data fit ever ran. Every "Hessian is not positive-definite" error was the
   Hessian evaluated at the PREFIT point, not at a minimum -- 77 of 225
   eigenvalues negative, the largest -1.4e6.
 * The earlier conclusion that `catLF_CR` caused the non-PD Hessian was WRONG.
   Masking changed which prefit Hessian happened to be positive definite. The
   high prefit chi2/bin in `catLF_CR` is a real data/MC observation, but it was
   not the cause.

Fix: `pip install "scipy<1.14"` into the venv (1.13.1 installed). Check any new
environment with a fit whose answer differs from its starting point.

## `--noHessian` is broken against CMSSW's SciPy

`fitter.edmval_cov_rows_hessfree` calls
`scipy.sparse.linalg.cg(..., rtol=..., atol=0.0)`. SciPy renamed that keyword
from `tol` to `rtol` in 1.12; CMSSW_15_0_10 ships SciPy 1.10.0, so the call
raises `TypeError: cg() got an unexpected keyword argument 'rtol'`. This removes
the only route to a fit result when the Hessian is not positive definite.
`--noEDM` is not an alternative: it writes the prefit values without fitting.

## Combine's default Hessian is wrong for this model -- use `--robustHesse 1`

`FitDiagnostics` and `MultiDimFit --saveFitResult` report parameter errors from
Minuit's Hessian. In this model those errors are not usable:

 * every nuisance that the data does not constrain gets an error of 0.9735
   instead of 1.0 -- a 2.7 % deficit across all 371 parameters at once;
 * `xsec_ttLF` gets an error of 0.0135 on the CR+SR Asimov fit but 0.3668 on
   the CR-only Asimov fit. Removing a channel cannot reduce an uncertainty by a
   factor 27, so at least one of the two is wrong;
 * on the same fit, `r` gets a Hessian error of 0.2324 and a MINOS error of
   -0.285/+0.322.

With `--robustHesse 1` all of it disappears. Against rabbit's analytic
(autodiff) Hessian on the identical model:

| Configuration | shared parameters | median error ratio | outside 5 % |
| --- | --- | --- | --- |
| CR+SR Asimov  | 371 | 1.0000 | 4  |
| CR Asimov     | 370 | 1.0000 | 3  |
| CR observed   | 370 | 0.9998 | 35 |

Fix: add `--robustHesse 1` to every Combine fit whose *parameter errors* are
used -- impacts, pulls-and-constraints plots, correlation matrices. The POI
uncertainty from a likelihood scan or from MINOS is not affected.

## `rabbit_text2hdf5` cannot mask channels

The converter has no equivalent of Combine's `--channel-masks`, so a CR-only
fit cannot be built from a datacard. `analysis/cardToTensor.py` adds `--mask
<regex>`; it patches `TensorWriter.add_channel`/`add_data`, so it will need
review after a rabbit upgrade.

## `rabbit_text2hdf5` maps rateParams to a 1 % lnN

`datacard_converter.py` writes each `rateParam` as an unconstrained lnN with a
1 % step, so a Combine rateParam value `v` is `exp(ln(1.01) * theta)` in rabbit.
`analysis/compareCombine.py` undoes it. Two consequences: the parameter range in
the card is ignored, and `add_norm_systematic` zips process against uncertainty,
so a `rateParam ... *` line covering several processes would silently apply to
the first one only. Our card names one process per line, so it is not hit here.

## `nllvalreduced` is delta-NLL, not the Combine test statistic

The saturated goodness-of-fit statistic that Combine prints is `2 * deltaNLL`.
Checked on the identical model, CR observed: rabbit `2 * nllvalreduced` = 52.02,
Combine `GoodnessOfFit --algo=saturated` = 51.40.

# Defects found by review and fixed (2026-08-19)

Four independent reviews were run on the rabbit pipeline: one primed with a
hypothesis and allowed to fit, one blind and allowed to fit, one pure code
reading with no execution, and one narrow audit of formulae and conditions.
The items below were confirmed in the source and then fixed.

## The free normalisations ARE real POIs (earlier "FreeNorm is broken" was a blinding artifact)

Earlier this section claimed `analysis/rabbit_models.FreeNorm` reported values the
fit did not use, and the free normalisations were written into the tensor as an
unconstrained lnN instead. That conclusion was WRONG. The mechanism, previously
"not yet identified", is rabbit's POI blinding on observed fits.

`rabbit_fit.py` sets `blinded_fits = [f == 0 ...]`, so every `-t 0` (observed)
fit turns POI blinding ON. Blinding multiplies each POI by `exp(random)`
(`fitter.py:673-681`) and touches only POIs and NOIs. `FreeNorm` makes `xsec_*`
real POIs, so they get blinded and the stored value is scrambled. A plain
unconstrained lnN (`constrained=False`, not `noi=True`) is neither a POI nor a
NOI, so it escapes blinding and reads back directly. The old "12649 vs 56.29
frozen" test froze `FreeNorm` at those scrambled values, so it evaluated the
loss at garbage norms. The fit itself is identical either way.

Verified on a controlled toy (one background floated, true scale 1.30):

| how the norm floats | fit | recovered scale |
| --- | --- | --- |
| unconstrained lnN | in-process | 1.30000 |
| `FreeNorm` POI | in-process | 1.30000 |
| `FreeNorm` POI | Asimov `-t -1` | 1.0 (Asimov truth) |
| `FreeNorm` POI | observed `-t 0`, no `--unblind` | scrambled (blinded) |
| `FreeNorm` POI | observed `-t 0`, `--unblind 'xsec_.*'` | 1.30000 |

Fix: use `FreeNorm`. `analysis/prepareTensor.py` no longer writes the free
normalisations into the tensor; they are supplied at fit time by
`--paramModel Mu --paramModel analysis.rabbit_models.FreeNorm <procs>`, so the
fitted value is the norm multiplier itself (POI, `mu = x^2`), not
`exp(ln(1.01) * theta)`. Observed fits add `--unblind 'xsec_.*'` (fullmatch, so
`^xsec_` would NOT match) to reveal the CR normalisations while `tt-vcb` stays
blinded. `read_parameters`, `compareCombine.py` and `validationReport.py` already
branch on `meta["pois"]`, so they read the POI path automatically.

## The lnN values did not match the datacard

`configs/model.py` had `norm_singletop` 1.02 against the card's 1.25,
`norm_wjets` 1.02 against 1.30, `norm_diboson` 1.05 against 1.30, and
`norm_ttZ` 1.07 against an asymmetric 1.096/1.085. `singletop` is 7.4 % of the
control-region prediction. The error also changed which processes the relevance
safety catch protects, because that keys on kappa >= 1.15.

Fix: values copied from the card; a kappa may now be a `(up, down)` pair.

## Template-changing defects

 * `prepareTensor.py` symmetrisation wrote `nom*exp(0)` in every bin where the
   nominal, up or down was not positive, which replaced a real variation with
   the nominal. It now rewrites only the bins the average is defined on.
 * A one-sided entry kept `symmetrize="average"`, so rabbit wrote it at half
   size. One-sided entries are now kept asymmetric.
 * A one-sided *shape* entry was dropped at write time while the decision table
   said it was kept. It is now mirrored about the nominal and written.
 * `templateSmoothing.py` floored a zero variance, which gave a bin with no
   information the *largest* spline weight. Such bins now get no weight.
 * `templateSmoothing.py` restored the leg integral over all bins while the
   array held the nominal in the non-usable ones, which pushed yield into the
   usable bins. The integral is now restored over the rewritten bins only.

## Statistical defects

 * `_empirical_ratio_noise` gave one flat relative error to every bin. The ratio
   noise scales as 1/sqrt(n_eff), so it now returns `c^2 * var_nom` per bin.
 * The same function took second differences on the compressed array, which
   leaps over empty bins; that step is structure, not noise. It now uses only
   triplets of adjacent bins.
 * `_leg_pvalues` returned `(0.0, 0.0)` when no bin was usable. A p-value of 0
   is the most significant value, so an entry with no information was always
   kept as a shape. It now returns `(1.0, 1.0)`.
 * The bin selection is now `(s2 > 0) & finite & (nom > 0)`. Selecting on `s2`
   alone made the classification depend on `--sentinel-policy`: under
   `keep-floor` a nominal of 1e-6 gave a huge chi2 and every entry became shape.
 * The flat-shape test took `ntot`/`ltot` over all bins while the chi2 ran over
   the usable ones, so `ndf = n-1` was wrong. Both now use the same bins.
 * The two legs were combined with `min()`, which is two tries at one threshold.
   They are now combined with Fisher's rule.

## Reporting defects

 * `validationReport.py` used `np.interp` with no `left`/`right`, so a scan that
   never reached 2*deltaNLL = 1 reported the edge of the scan range as the
   crossing. It now returns NaN, as `rabbitPlotScan.crossing` already did.
 * `compareModel.py` counted a lnN row written as `1` as active. The test is now
   type-aware, since for a shape row `1` does mean active.

## Still open

 * `--zero-syst-low-neff 1.0` is our own default in `prepareTensor.py` (rabbit's
   is 0.0). It zeroes a systematic in low-n_eff bins after we write it, so a
   flat normalisation lever is not flat and its effective kappa is smaller than
   the value recorded in the decision table.
