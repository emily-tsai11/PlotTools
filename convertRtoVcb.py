import numpy as np

Vcb_gen = 0.0411  # PDG 2025 eq. 76.3, per xsec_run3.conf:149

# From e.g. `combine -M MultiDimFit --algo singles -P r`: r_hat, and the
# +1 sigma / -1 sigma offsets (both positive numbers: r_hat+r_plus, r_hat-r_minus).
# Preapproval values
#r = 0.6896
#r_plus = 0.2857
#r_minus = 0.2876

# Rescaled DPS
#r = 0.7218
#r_minus = 0.3073
#r_plus = 0.2962

# Rescaled DPS and muR in ttbb, tt2b, ttbj
r = 0.837
r_minus = 0.281
r_plus = 0.281

# Propagate the interval endpoints through Vcb(r) = Vcb_gen*sqrt(r) directly,
# rather than linearizing (delta method) -- exact for a monotonic transform,
# and captures the asymmetry that sqrt(r) introduces.
Vcb_fit = Vcb_gen * np.sqrt(r)
Vcb_up = Vcb_gen * np.sqrt(r + r_plus) - Vcb_fit
Vcb_down = Vcb_fit - Vcb_gen * np.sqrt(r - r_minus)

print(f"Vcb = {(Vcb_fit*1000):.5f}  +{Vcb_up*1000:.5f}  -{Vcb_down*1000:.5f}")
print(f"Relative uncertainty: +{Vcb_up/Vcb_fit:.3%}  -{Vcb_down/Vcb_fit:.3%}")

# --- Alternative: full profile-likelihood scan (use if you have the grid scan
# ROOT file and want the interval read off directly from 2*deltaNLL=1, which
# is the most rigorous option and doesn't assume --algo singles' local
# quadratic approximation) ---
#
# import uproot
# f = uproot.open("higgsCombineTest.MultiDimFit.mH125.38.root")["limit"]
# r_scan = f["r"].array(library="np")
# dnll = f["deltaNLL"].array(library="np")
#
# order = np.argsort(r_scan)
# r_scan, dnll = r_scan[order], dnll[order]
# Vcb_scan = Vcb_gen * np.sqrt(r_scan)
# twoDnll = 2 * dnll
#
# i_min = np.argmin(twoDnll)
# Vcb_hat = Vcb_scan[i_min]
#
# lo_mask = Vcb_scan < Vcb_hat
# hi_mask = Vcb_scan > Vcb_hat
# Vcb_lo = np.interp(1.0, twoDnll[lo_mask][::-1], Vcb_scan[lo_mask][::-1])
# Vcb_hi = np.interp(1.0, twoDnll[hi_mask], Vcb_scan[hi_mask])
#
# print(f"Vcb = {Vcb_hat:.5f}  +{Vcb_hi-Vcb_hat:.5f}  -{Vcb_hat-Vcb_lo:.5f}")
