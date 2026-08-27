"""Smoothing of systematic shape variations.

Replacement for analysis/smoothing.py, which is kept for the Combine path. The
method is the same one (CMS AN-2018/077): build the antisymmetric relative
variation, smooth it, then rescale it back onto each leg by least squares. The
differences are in the details that were wrong before -- see COMBINE_FIXES.md.

Norm and shape are factorised here: only the shape is smoothed and the integral
of each leg is restored afterwards, so smoothing can never move a yield.
"""

import collections

import numpy as np
import scipy.interpolate as itp


SmoothingResult = collections.namedtuple("SmoothingResult", "up down note")


def _least_squares_scale(basis, target, inv_var):
    """Scale a that minimises sum((a*basis - target)^2 / var)."""
    denom = np.sum(basis * basis * inv_var)
    if denom <= 0:
        return 0.0
    return float(np.sum(basis * target * inv_var) / denom)


def smooth_variation(
    nom,
    up,
    down,
    sigma2_up,
    sigma2_down,
    centers,
    smoothing_factor=1.0,
    antisymmetrise=True,
    min_bins=4,
    method="spline",
    lowess_frac=0.9,
):
    """Smooth one (category, process, systematic) variation pair.

    nom/up/down       : bin contents
    sigma2_up/down    : per-bin variance of (varied - nominal), class-aware,
                        from configs.model.variance_of_shift
    centers           : bin centres
    smoothing_factor  : multiplies the spline's target chi2 (=n_bins). 1.0 means
                        "smooth until chi2/ndf ~ 1"; larger smooths harder.
    method            : "spline" (local cubic UnivariateSpline, chi2/ndf~1) or
                        "lowess" (locally-weighted regression, as in the old
                        analysis/smoothing.py). lowess ignores the per-bin
                        errors and smoothing_factor.
    lowess_frac       : fraction of points per local lowess fit (0.9 = the
                        strong, near-global setting the Combine chain used).

    Returns SmoothingResult, or None if the variation cannot be smoothed (too
    few usable bins), in which case the caller keeps the original templates.
    """
    nom = np.asarray(nom, dtype=float)
    up = np.asarray(up, dtype=float)
    down = np.asarray(down, dtype=float)

    usable = nom > 0
    if usable.sum() < min_bins:
        return None

    ntot = nom.sum()
    if ntot <= 0:
        return None

    # factorise: keep the integral ratios exactly, smooth only the shape
    knorm_up = up.sum() / ntot
    knorm_down = down.sum() / ntot
    if knorm_up <= 0 or knorm_down <= 0:
        return None

    x = np.asarray(centers, dtype=float)[usable]
    n = nom[usable]

    # shape-only relative variation of each leg
    r_up = (up[usable] / knorm_up) / n - 1.0
    r_down = (down[usable] / knorm_down) / n - 1.0

    # per-bin uncertainty on those ratios
    var_r_up = np.asarray(sigma2_up, dtype=float)[usable] / (n * n * knorm_up * knorm_up)
    var_r_down = np.asarray(sigma2_down, dtype=float)[usable] / (n * n * knorm_down * knorm_down)

    # A bin with no estimated uncertainty carries no information, so it must get
    # NO weight. Flooring the variance did the opposite: it gave such a bin the
    # smallest error and therefore the largest spline weight, up to 1e6 times
    # the rest, and one such bin then pinned the whole spline.
    big = np.max([var_r_up.max(), var_r_down.max(), 1e-12]) * 1e6
    var_r_up = np.where(var_r_up > 0, var_r_up, big)
    var_r_down = np.where(var_r_down > 0, var_r_down, big)

    # antisymmetric part is the shape template the two legs share
    basis_raw = 0.5 * (r_up - r_down)
    if not np.any(basis_raw != 0):
        return None

    var_basis = 0.25 * (var_r_up + var_r_down)
    sigma_basis = np.sqrt(var_basis)

    k = 3 if len(x) >= 4 else 1
    # UnivariateSpline weights are 1/sigma, so sum(w^2 (y-f)^2) is a chi2 and
    # s = n_bins is the "chi2/ndf ~ 1" stopping criterion.
    weights = 1.0 / sigma_basis
    s = smoothing_factor * len(x)

    if method == "lowess":
        # Locally-weighted regression, matching the old analysis/smoothing.py.
        # frac is the fraction of points in each local fit; 0.9 is a strong,
        # near-global smoother. lowess is unweighted, so the per-bin errors and
        # smoothing_factor do not enter here.
        try:
            import statsmodels.api as sm
        except Exception as exc:
            return SmoothingResult(up, down, f"lowess unavailable ({exc}), kept unsmoothed")
        try:
            basis = sm.nonparametric.lowess(basis_raw, x, frac=lowess_frac,
                                            return_sorted=False)
        except Exception as exc:
            return SmoothingResult(up, down, f"lowess failed ({exc}), kept unsmoothed")
    else:
        try:
            spline = itp.UnivariateSpline(x, basis_raw, w=weights, k=k, s=s)
            basis = spline(x)
        except Exception as exc:  # scipy raises on degenerate inputs
            return SmoothingResult(up, down, f"spline failed ({exc}), kept unsmoothed")

    basis = np.asarray(basis, dtype=float)
    if not np.all(np.isfinite(basis)) or not np.any(basis != 0):
        return SmoothingResult(up, down, "degenerate smoothing, kept unsmoothed")

    a_up = _least_squares_scale(basis, r_up, 1.0 / var_r_up)
    a_down = _least_squares_scale(basis, r_down, 1.0 / var_r_down)

    # If the two leg scales sum to zero within their combined error the
    # variation is antisymmetric; force it so. This removes the noise on the
    # (a_up + a_down) mode, matching the old smoothing.py behaviour. For a
    # one-sided leg (down == nominal, a_down == 0) the sum equals the real
    # a_up, so a genuine shape is not forced -- hence never call this on a
    # two-point systematic, whose down is nominal by construction.
    if antisymmetrise:
        d_up = float(np.sum(basis * basis / var_r_up))
        d_down = float(np.sum(basis * basis / var_r_down))
        if d_up > 0 and d_down > 0 and (a_up + a_down) ** 2 < 1.0 / d_up + 1.0 / d_down:
            half = 0.5 * (a_up - a_down)
            a_up, a_down = half, -half

    # Bound the least-squares rescale. An unbounded scale lets a poorly-fitting
    # antisymmetric basis blow the leg up (seen: a ~ -115 on CMS_elScale). The
    # old smoothing.py clipped the magnitude to [0.1, 10]; here bound a to [-10, 10].
    note = ""
    for label, a in (("up", a_up), ("down", a_down)):
        if abs(a) > 10.0:
            note = f"{label} rescale {a:.1f} clipped to +-10; smoothed shape fits the leg poorly"
        elif abs(a) > 5.0 and not note:
            note = f"large {label} rescale ({a:.2f}); smoothed shape fits the leg poorly"
    a_up = float(np.clip(a_up, -10.0, 10.0))
    a_down = float(np.clip(a_down, -10.0, 10.0))

    out_up = nom.copy()
    out_down = nom.copy()
    out_up[usable] = n * (1.0 + a_up * basis)
    out_down[usable] = n * (1.0 + a_down * basis)

    # a smoothed leg must not go negative
    out_up = np.clip(out_up, 0.0, None)
    out_down = np.clip(out_down, 0.0, None)

    # Restore the integral over the bins that were rewritten. Using the total
    # over ALL bins, while the array holds the nominal in the non-usable ones,
    # pushed the yield of those bins into the usable ones and changed the shape.
    for arr, leg in ((out_up, up), (out_down, down)):
        target = float(np.asarray(leg)[usable].sum())
        tot = float(arr[usable].sum())
        if tot > 0 and target > 0:
            arr[usable] *= target / tot

    return SmoothingResult(out_up, out_down, note)


def classic_forcesymm_smooth(nom, up, down, var_nom, var_up, var_down, centers,
                             lowess_frac=0.9, min_bins=4):
    """Faithful reproduction of the flavTag treatment in analysis/smoothing.py
    (get_smoothed_up_and_down(forceSymm_=True) + get_smoothed_scale_factor),
    for A/B testing against it. NOT the default.

    Three deliberate divergences from smooth_variation()/preprocess_legs()
    above, kept faithful to the old code on purpose:
      * the smoothed basis is the UP leg's own raw ratio (up/nom - 1), never
        an average with (mirrored or stored) down -- down's shape never enters
        the basis, only a possible fallback below;
      * the rescale fit runs in ABSOLUTE event-count space (target = leg -
        nominal, not the shape-only ratio smooth_variation uses), so unlike
        our pipeline it does not guarantee the leg's yield is preserved;
      * the rescale is weighted by raw Sumw2(nominal)+Sumw2(leg), the
        variance estimate documented as biased for a same-event weight
        systematic (COMBINE_FIXES.md item 7: overestimates var(leg-nominal)
        by a factor of order 2/eps^2). configs/model.shift_variance is the
        fix; this function does not use it, on purpose, to reproduce the old
        behaviour exactly.

    Master-leg rule: fit a scale from EACH leg against its own (possibly
    broken) stored data; prefer up if its fit is positive, else fall back to
    down (whichever direction is used, the OTHER leg is forced to its exact
    negative -- this is where the antisymmetry comes from, not from mirroring
    the histogram first).
    """
    nom = np.asarray(nom, dtype=float)
    up = np.asarray(up, dtype=float)
    down = np.asarray(down, dtype=float)
    var_nom = np.asarray(var_nom, dtype=float)
    var_up = np.asarray(var_up, dtype=float)
    var_down = np.asarray(var_down, dtype=float)

    usable = nom > 0.001
    if usable.sum() < min_bins:
        return None

    half_ratio = np.where(nom > 0.001, np.where(up > 0.001, up / nom - 1.0, 0.0), 0.0)
    alt_half_ratio = np.where(nom > 0.001, np.where(down > 0.001, down / nom - 1.0, 0.0), 0.0)
    ratio_diff = half_ratio if abs(np.sum(half_ratio)) > 0.0 else alt_half_ratio
    if abs(np.sum(ratio_diff)) == 0.0:
        return SmoothingResult(up, down, "flat ratio, kept unsmoothed (classic)")

    try:
        import statsmodels.api as sm
        diff_smooth = sm.nonparametric.lowess(ratio_diff, np.asarray(centers, dtype=float),
                                              frac=lowess_frac, return_sorted=False)
    except Exception as exc:
        return SmoothingResult(up, down, f"classic lowess failed ({exc}), kept unsmoothed")

    def scale(legv, var_legv):
        total_var = var_nom + var_legv
        unsmoothed_diff = legv - nom
        ratio_factor = diff_smooth * nom
        ok = total_var > 0
        num = np.where(ok, ratio_factor * unsmoothed_diff / np.where(ok, total_var, 1.0),
                       ratio_factor * unsmoothed_diff)
        den = np.where(ok, ratio_factor / np.sqrt(np.where(ok, total_var, 1.0)), ratio_factor) ** 2
        num, den = float(np.sum(num)), float(np.sum(den))
        a = num / den if den > 0 else 1.0
        return float(np.sign(a) * np.clip(abs(a), 0.1, 10.0))

    up_scale, down_scale = scale(up, var_up), scale(down, var_down)
    if up_scale > 0:
        a_up, a_down = up_scale, -up_scale
    elif down_scale > 0:
        a_up, a_down = -down_scale, down_scale
    else:
        a_up, a_down = up_scale, -up_scale

    up_ratio = np.nan_to_num(1.0 + a_up * diff_smooth, nan=1.0)
    down_ratio = np.nan_to_num(1.0 + a_down * diff_smooth, nan=1.0)
    out_up = nom * up_ratio
    out_down = nom * down_ratio
    out_up = np.where((out_up < 0) | ~np.isfinite(out_up), nom, out_up)
    out_down = np.where((out_down < 0) | ~np.isfinite(out_down), nom, out_down)
    return SmoothingResult(out_up, out_down, "")
