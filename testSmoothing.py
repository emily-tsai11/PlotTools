import re
from argparse import ArgumentParser
from pathlib import Path
import uproot # I had 3.13.0 before
from hist import Hist
from os.path import join
import os
import numpy as np
from itertools import product
import scipy.interpolate as itp
from glob import glob
import pdb
import pandas
import matplotlib.pyplot as plt

from analysis.smoothing import *

# ttHcc_2016_FH_catBB_SR CMS_PS_isr_tt2c
# Datacards_2024-09-20_extrapolationUnc/

# filename = "Datacards_2025-02-14_MergedYears_5FSFullCorrShapeUnc_rescaleFIVEFS_decor_PSSplit/AllShapes_bkp.root"
filename = "Datacards_280426/Vcb_SL_2024_shapes.root"
# filename = "Datacards_280426_smoothed/Vcb_SL_2024_shapes.root"


# proc = "tt-vcb"
proc = "tt2b"
# syst = "CMS_PS_fsr_g2gg_ren_ttcj"
syst = "CMS_flavTag_JES_Absolute"

# nomHist = "Vcb_catWcb_SR/"+proc
# upHist = "Vcb_catWcb_SR/"+proc+"_"+syst+"Up"
# downHist = "Vcb_catWcb_SR/"+proc+"_"+syst+"Down"

nomHist = "Vcb_cat2B_CR/"+proc
upHist = "Vcb_cat2B_CR/"+proc+"_"+syst+"Up"
downHist = "Vcb_cat2B_CR/"+proc+"_"+syst+"Down"

forceSymm = False
doNotSymm_ = False

f = uproot.open(filename)

# pdb.set_trace()

nom_hist = Hist(f[nomHist])
up_hist = Hist(f[upHist])
down_hist = Hist(f[downHist])

print (nomHist)
print (nom_hist)
print (upHist)
print (up_hist)
print (downHist)
print (down_hist)

print ("---1")

bin_centers = nom_hist.axes.centers[0]
# bin_centers = [i for i in range(len(nom_hist.axes.centers[0]))]
# half_ratio = [up_hist.values()[i] / nom_hist.values()[i] - 1. if nom_hist.values()[i] > 0.001 and up_hist.values()[i] > 0.001 else 0. for i in range(len(nom_hist.values()))]
# half_ratio = np.clip(half_ratio, 0.1, 10.)
# alt_half_ratio = np.clip(down_hist.values() / nom_hist.values() - 1., 0.00001, 10.)
# alt_half_ratio = [down_hist.values()[i] / nom_hist.values()[i] - 1. if nom_hist.values()[i] > 0.001 and down_hist.values()[i] > 0.001 else 0. for i in range(len(nom_hist.values()))]
# alt_half_ratio = np.clip(alt_half_ratio, 0.1, 10.)

# print (half_ratio)
# print (alt_half_ratio)

if doNotSymm_:
    down_hist = nom_hist

half_ratio =     np.where(nom_hist.values() > 0.001, np.where(up_hist.values()   > 0.001,   up_hist.values() / nom_hist.values() -1., 0.), 0.)
alt_half_ratio = np.where(nom_hist.values() > 0.001, np.where(down_hist.values() > 0.001, down_hist.values() / nom_hist.values() -1., 0.), 0.)

print ("half_ratio", half_ratio)
print ("alt_half_ratio", alt_half_ratio)

if forceSymm:
    # if abs(sum(half_ratio)) > 0.01:
    if abs(sum(half_ratio)) > 0.:
        ratio_diff = half_ratio
    # elif abs(sum(alt_half_ratio)) > 0.01:
    elif abs(sum(alt_half_ratio)) > 0.:
        ratio_diff = alt_half_ratio
    else:
        ratio_diff = half_ratio
else:
    ratio_diff = (half_ratio - alt_half_ratio) / 2.

if doNotSymm_:
    ratio_diff = half_ratio

print ("bin_centers", bin_centers)
print ("half_ratio", half_ratio)
print ("alt_half_ratio", alt_half_ratio)
print ("ratio_diff", ratio_diff)

# if abs(sum(ratio_diff)) > 0.01:
if abs(sum(ratio_diff)) > 0.00:

    import statsmodels.api as sm
    # diff_smooth = sm.nonparametric.lowess(ratio_diff, bin_centers, xvals=bin_centers, is_sorted =True, missing = 'none')

    # frac_ = 0.5 if len(bin_centers) < 4 else 2./3.
    print ("smoothing...", ratio_diff)
    # diff_smooth = sm.nonparametric.lowess(ratio_diff, bin_centers)[:,1]
    diff_smooth = sm.nonparametric.lowess(ratio_diff, bin_centers, frac = 0.9)[:,1]
    # import lowess
    # diff_smooth = lowess.lowess(pandas.Series(ratio_diff), pandas.Series(bin_centers), bandwidth=0.2, polynomialDegree=1)
    # print ("diff_smooth ", diff_smooth)


    # k_ = 2 if len(bin_centers)  < 4 else 3
    # diff_smooth = itp.UnivariateSpline(bin_centers, ratio_diff, w = None, k = k_)(bin_centers)

    print ("diff_smooth", diff_smooth)


    plt.figure()
    plt.plot(half_ratio, label = "up ratio")
    plt.plot(alt_half_ratio, label = "down ratio")
    plt.plot(ratio_diff, label = "half ratio")
    plt.plot(diff_smooth, label = "smooth ratio")
    plt.legend()
    plt.savefig("testSmoothing.png")

    up_scale = get_smoothed_scale_factor(diff_smooth, nom_hist, up_hist)
    up_scale_unc = get_smoothed_scale_factor_unc(diff_smooth, nom_hist, up_hist)
    down_scale = get_smoothed_scale_factor(diff_smooth, nom_hist, down_hist)
    down_scale_unc = get_smoothed_scale_factor_unc(diff_smooth, nom_hist, down_hist)

    print ("--2")
    print ("up_scale", up_scale)
    print ("up_scale_unc", up_scale_unc)
    print ("down_scale", down_scale)
    print ("down_scale_unc", down_scale_unc)

    if forceSymm:
        if up_scale > 0:
            up_scale_ = up_scale
            down_scale_ = -1. * up_scale
        elif down_scale > 0:
            up_scale_ = -1. * down_scale
            down_scale_ = down_scale
    elif doNotSymm_:
        up_scale_ = up_scale
        down_scale_ = 0.
    elif ((up_scale + down_scale)**2.) < (2. * up_scale_unc **2.):
        print ("comp")
        up_scale_ = (up_scale - down_scale)/2.
        down_scale_ = -1. * (up_scale - down_scale)/2.
    else:
        up_scale_ = up_scale
        down_scale_ = down_scale
        
    print ("--3")
    print (up_scale_)
    # print (up_scale_unc)
    print (down_scale_)
    # print (down_scale_unc)


    up_ratio = (1. + up_scale_ * diff_smooth)
    down_ratio = (1. + down_scale_ * diff_smooth)

    print (up_ratio)
    print (down_ratio)

    new_var_up = nom_hist * np.nan_to_num(up_ratio, nan=1.0)
    new_var_down = nom_hist * np.nan_to_num(down_ratio, nan=1.0)
    for binX in range(len(new_var_up.values())):
        if new_var_up[binX].value < 0.:
            new_var_up[binX] = nom_hist[binX]
        if new_var_down[binX].value < 0.:
            new_var_down[binX] = nom_hist[binX]
else:
    print ("ratio diff only",abs(sum(ratio_diff)))
    new_var_up = up_hist
    new_var_down = down_hist

print ("new variation yields:")
print (new_var_up)
print (new_var_down)

plt.figure()
# plt.plot(nom_hist, label = "nom")
plt.plot(half_ratio, label = "up")
plt.plot(alt_half_ratio, label = "down")
plt.plot(up_ratio-1, label = "up smooth")
plt.plot(down_ratio-1, label = "down smooth")
plt.legend()
plt.savefig("testSmoothing2.png")

plt.figure()
plt.plot(nom_hist.values(), label = "nom")
plt.plot(up_hist.values(), label = "up")
plt.plot(down_hist.values(), label = "down")
plt.plot(new_var_up.values(), label = "up smooth")
plt.plot(new_var_down.values(), label = "down smooth")
plt.legend()
plt.savefig("testSmoothing3.png")