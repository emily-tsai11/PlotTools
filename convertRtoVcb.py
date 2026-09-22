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
r_minus = 0.292
r_plus = 0.280
r_minus_stat_only = 0.163
r_plus_stat_only = 0.167

# Propagate the interval endpoints through Vcb(r) = Vcb_gen*sqrt(r) directly,
# rather than linearizing (delta method) -- exact for a monotonic transform,
# and captures the asymmetry that sqrt(r) introduces.

r_minus_syst_only = np.sqrt(r_minus**2 - r_minus_stat_only**2)
r_plus_syst_only = np.sqrt(r_plus**2 - r_plus_stat_only**2)

Vcb_fit = Vcb_gen * np.sqrt(r)
Vcb_up = Vcb_gen * np.sqrt(r + r_plus) - Vcb_fit
Vcb_down = Vcb_fit - Vcb_gen * np.sqrt(r - r_minus)

Vcb_up_stat_only = Vcb_gen * np.sqrt(r + r_plus_stat_only) - Vcb_fit
Vcb_down_stat_only = Vcb_fit - Vcb_gen * np.sqrt(r - r_minus_stat_only)

Vcb_up_syst_only = Vcb_gen * np.sqrt(r + r_plus_syst_only) - Vcb_fit
Vcb_down_syst_only = Vcb_fit - Vcb_gen * np.sqrt(r - r_minus_syst_only)

print()
print(f"r = {r:.3f} +{r_plus_stat_only:.3f} -{r_minus_stat_only:.3f} (stat) +{r_plus_syst_only:.3f} -{r_minus_syst_only:.3f} (syst). Total uncertainty: +{r_plus:.3f} -{r_minus:.3f}\n")
print(f"Vcb = {(Vcb_fit*100):.3f} +{Vcb_up_stat_only*100:.3f} -{Vcb_down_stat_only*100:.3f} (stat) +{Vcb_up_syst_only*100:.3f} -{Vcb_down_syst_only*100:.3f} (syst). Total uncertainty: +{Vcb_up*100:.3f} -{Vcb_down*100:.3f}\n")
print(f"Relative uncertainty: +{Vcb_up/Vcb_fit:.2%}  -{Vcb_down/Vcb_fit:.2%}")

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
