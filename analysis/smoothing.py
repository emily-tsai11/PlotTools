import re
from argparse import ArgumentParser
from pathlib import Path
import uproot # I had 3.13.0 before
from hist import Hist,storage
from os.path import join
import os
import numpy as np
from itertools import product
import scipy.interpolate as itp
from glob import glob
import pdb

listToSmooth = [
    "CMS_met",
    "CMS_res_j",
    "CMS_scale_j",
]

bypassSmoothing = True

listSymm = [
    # "AMCATNLOFXFX_TTBB",
    # "AMCATNLOFXFX_TTBJ",
    # "AMCATNLOFXFX_TT2B",
    # "AMCATNLOFXFX_TTCC",
    # "AMCATNLOFXFX_TTCJ",
    # "AMCATNLOFXFX_TT2C",
    # "AMCATNLOFXFX_TTLF",
    # "CMS_flavTag_JES_",
    # "CMS_flavTag_JER_",
    # "CMS_flavTag_xsec_",
    # "CMS_flavTag_PS_",
    # "CMS_flavTag_",
]

listNotSymm = [
    "CR1",
    "CR2",
    "bFragPetersonWeight_",
]

def matchSyst(systname, bypass = bypassSmoothing):
    if bypass:
        return True
    for entry in listToSmooth:
        if entry in systname:
            return True
        # else:
        #     return False
    return False

def matchSystSymm(systname):
    for entry in listSymm:
        if entry in systname:
            print ("matchSystSymm: matched", entry, "in", systname)
            return True
        # else:
        #     return False
    return False

def matchSystNotSymm(systname):
    for entry in listNotSymm:
        if entry in systname:
            print ("matchSystNotSymm: matched", entry, "in", systname)
            return True
    return False


#structure
# category
#   process__syst

def get_process(key):
    # print ("get_process: key",key)
    if "CMS" in key or "PDF" in key or "AMCATNLOFXFX_TT" in key or "HERWIG_TT" in key or "FIVEFS_TT" in key or "FIVEFS" in key or "FIVEFS2MU_TT" in key or "FIVEFS2MU" in key or "FOURFS_TT" in key or "FOURFS" in key:
        if "CMS" in key:
            return key.split('_CMS_')[0]
        if "PDF" in key:
            return key.split('_PDF_')[0]
    else:
        # print ("key",key)
        return key.split(";")[0]


def get_systematics_names(uproot_templates: uproot.reading.ReadOnlyDirectory):
    list_ = []
    for k in uproot_templates.keys():
        # if "CMS" in k or "PDF" in k:
        # if "CMS" in k or "PDF" in k or "AMCATNLOFXFX_TT" in k or "HERWIG_TT" in k or "FIVEFS_TT" in k or "FIVEFS" in k or "FIVEFS2MU" in k or "FOURFS" in k:
        # print ("get_systematics_names: k",k)
        if len(k.split("/")) > 1 and not "data_obs" in k:
            k = k.split("/")[-1]
            if "_" in k:
                # keep all but the first part of the "_" split as k
                k = "_".join(k.split("_")[1:])
                # print ("-get_systematics_names: k",k)
                # n_ = k.split("_")[1].replace("Up","").replace("Down","")
                # n_ = join(k.split("_")[1:]).replace("Up","").replace("Down","")
                n_ = k.replace("Up","").replace("Down","")
                n_ = n_.split(";")[0]
                if n_ not in list_:
                    list_.append(n_)
    return list_

def get_categories(uproot_templates: uproot.reading.ReadOnlyDirectory):
    list_ = []
    for k in uproot_templates.keys():
        if "/" in k:
            n_ = k.split("/")[0]
            if n_ not in list_:
                list_.append(n_)
    return list_

def get_nominal_templates(uproot_templates: uproot.reading.ReadOnlyDirectory):
    dic_ = {get_process(k): Hist(uproot_templates[k]) for k in uproot_templates.keys() if ( not ('_' in k.split("/")[-1] and not "data_obs" in k) and 'CMS' not in k and "PDF" not in k and len(k.split("/")) > 1)}
    return dic_

def get_processes(uproot_templates: uproot.reading.ReadOnlyDirectory):
    list_ = []
    for k in uproot_templates.keys():
        # print ("get_processes: k",k)
        if '_' not in k.split("/")[-1] and 'CMS' not in k and "PDF" not in k and "AMCATNLOFXFX_TT" not in k and "HERWIG_TT" not in k and "FIVEFS_TT" not in k and "FIVEFS" not in k and "FIVEFS2MU" not in k and "FOURFS" not in k and len(k.split("/")) > 1:
            n_ = k.split(";")[0].split("/")[1]
            if not n_ in list_:
                list_.append(n_)
    return list_

def is_sys_dir(dr):
    return dr.startswith('CMS') or dr == 'nominal'



def get_smoothed_scale_factor(smoothed_ratio_diff, nom_hist, var_hist):
    '''determine an overall systematic template smoothing which minimizes the chi-squared between
        the smoothed systematic and the unsmoothed template it is derived from.
        Taken from:
             https://cms.cern.ch/iCMS/jsp/openfile.jsp?tp=draft&files=AN2018_077_v4.pdf'''


    total_var = nom_hist.variances() + var_hist.variances()
    unsmoothed_diff = var_hist.values() - nom_hist.values()
    ratio_factor = smoothed_ratio_diff * nom_hist.values()
    numerator = np.sum(ratio_factor * unsmoothed_diff / total_var)
    denominator = np.sum((ratio_factor / np.sqrt(total_var)) ** 2)

    # try again with cleaning and catches
    smoothed_ratio_diff_ = np.nan_to_num(smoothed_ratio_diff, nan=0.0, posinf=0.0, neginf=0.0)
    nom_hist_values_ = np.nan_to_num(nom_hist.values(), nan=0.000001, posinf=0.000001, neginf=0.000001)
    var_hist_values_ = np.nan_to_num(var_hist.values(), nan=0.000001, posinf=0.000001, neginf=0.000001)
    nom_hist_variances_ = np.nan_to_num(nom_hist.variances(), nan=10000.0, posinf=10000.0, neginf=10000.0)
    var_hist_variances_ = np.nan_to_num(var_hist.variances(), nan=10000.0, posinf=10000.0, neginf=10000.0)

    total_var = nom_hist_variances_ + var_hist_variances_

    rf = np.nan_to_num(smoothed_ratio_diff_ * nom_hist_values_, nan=0.0, posinf=0.0, neginf=0.0)
    unsmoothed_diff = np.nan_to_num(var_hist_values_ - nom_hist_values_, nan=0.0, posinf=0.0, neginf=0.0)

    ratio_factor = np.sign(rf) * np.abs(rf)

    numerator = np.sum(np.where(np.abs(total_var) > 0., ratio_factor * unsmoothed_diff / total_var, ratio_factor * unsmoothed_diff))

    denominator = np.sum(( np.where(np.abs(total_var) > 0., ratio_factor / np.sqrt(total_var), ratio_factor) )**2.)

    return np.sign(np.where(abs(denominator) > 0., numerator / denominator, 1.)) * np.clip(np.abs(np.where(abs(denominator) > 0., numerator / denominator, 1.)), 0.1, 10.)






def get_smoothed_scale_factor_unc(smoothed_ratio_diff, nom_hist, var_hist):
    return (np.sum((smoothed_ratio_diff * nom_hist.values() / np.sqrt(nom_hist.variances()) )**2.))**0.5

def get_smoothed_up_and_down(nom_hist, up_hist, down_hist, method, ratio_only=False, forceSymm_ = False, doNotSymm_ = False):
    '''use up and down variations of a systematic to smooth them, by using the difference in each of their ratios to the nominal.
       the shapes of the systematic templates are constrained to be opposite to each other, up to some overall scaling.
      Taken from:
            https://cms.cern.ch/iCMS/jsp/openfile.jsp?tp=draft&files=AN2018_077_v4.pdf'''
    bin_centers = nom_hist.axes.centers[0]

    # for systematics where we only have one variation (usualy up) and which satisfy doNotSymm, we don't symmetrize and only smoothen the up template, and we take the down template to be the same as the nominal, so that we can still apply the smoothing procedure to these systematics
    if doNotSymm_:
        down_hist = nom_hist




    half_ratio =     np.where(nom_hist.values() > 0.001, np.where(up_hist.values() > 0.001,   up_hist.values() / nom_hist.values() -1.,   0.), 0.)
    alt_half_ratio = np.where(nom_hist.values() > 0.001, np.where(down_hist.values() > 0.001, down_hist.values() / nom_hist.values() -1., 0.), 0.)

    if forceSymm_:
        if abs(sum(half_ratio)) > 0.:
            ratio_diff = half_ratio
        elif abs(sum(alt_half_ratio)) > 0.:
            ratio_diff = alt_half_ratio
        else:
            ratio_diff = [0.]
    else:
        ratio_diff = (half_ratio - alt_half_ratio) / 2.

    if doNotSymm_:
        ratio_diff = half_ratio

    # ratio_diff = (half_ratio - alt_half_ratio) / 2.
    # if abs(sum(ratio_diff)) > 0.01:
    # if abs(sum(ratio_diff)) > 0.00001:
    if abs(sum(ratio_diff)) > 0.:
        if 'Spline' in method:
            if 'un' in  args.method:
                weights = None
            else:
                weights = 1. / sum([x.variances() for x in [nom_hist, up_hist, down_hist]])
            k_ = 2 if len(bin_centers)  < 4 else 3
            diff_smooth = itp.UnivariateSpline(bin_centers, ratio_diff, w = weights, k = k_)(bin_centers)
        elif method == 'lowess':
            import statsmodels.api as sm
            # diff_smooth = sm.nonparametric.lowess(ratio_diff, bin_centers, xvals=bin_centers)
            # diff_smooth = sm.nonparametric.lowess(ratio_diff, bin_centers)[:,1]
            diff_smooth = sm.nonparametric.lowess(ratio_diff, bin_centers, frac = 0.9)[:,1]

        up_scale = get_smoothed_scale_factor(diff_smooth, nom_hist, up_hist)
        up_scale_unc = get_smoothed_scale_factor_unc(diff_smooth, nom_hist, up_hist)
        down_scale = get_smoothed_scale_factor(diff_smooth, nom_hist, down_hist)
        down_scale_unc = get_smoothed_scale_factor_unc(diff_smooth, nom_hist, down_hist)

        if forceSymm_:
            if up_scale > 0.:
                up_scale_ = up_scale
                down_scale_ = -1. * up_scale
            elif down_scale > 0.:
                up_scale_ = -1. * down_scale
                down_scale_ = down_scale
            else:
                up_scale_ = up_scale
                down_scale_ = -1. * up_scale
        elif doNotSymm_:
            up_scale_ = up_scale
            down_scale_ = 0.
        elif ((up_scale + down_scale)**2.) < (2. * up_scale_unc **2.):
            # print ("comp")
            up_scale_ = (up_scale - down_scale)/2.
            down_scale_ = -1. * (up_scale - down_scale)/2.
        else:
            up_scale_ = up_scale
            down_scale_ = down_scale

        up_ratio = (1 + up_scale_ * diff_smooth)
        down_ratio = (1 + down_scale_ * diff_smooth)
        if ratio_only:
            return up_ratio, down_ratio

        new_var_up = nom_hist * np.nan_to_num(up_ratio, nan=1.0)
        new_var_down = nom_hist * np.nan_to_num(down_ratio, nan=1.0)
        for binX in range(len(new_var_up.values())):
            if new_var_up[binX].value < 0.:
                new_var_up[binX] = nom_hist[binX]
            if new_var_down[binX].value < 0.:
                new_var_down[binX] = nom_hist[binX]



        if doNotSymm_:
            new_var_down = nom_hist


        return new_var_up, new_var_down
    else:
        return up_hist, down_hist


def match_any(expressions, string):
    return any([re.match(e, string, re.DOTALL) for e in expressions])




def process_file(unsmoothed_template_dir, smoothed_template_dir, method, args):
    # tags for up and down
    up_dn = ['Up', 'Down']
    UP, DN = up_dn

    # print ("----entering process_file")
    # print ("unsmoothed_template_dir", unsmoothed_template_dir)
    # print ("smoothed_template_dir", smoothed_template_dir)
    # root_files = [r for r in os.listdir(join(unsmoothed_template_dir)) if re.match('AllShapes*\.root', r, re.DOTALL)]
    # root_files = [r for r in os.listdir(join(unsmoothed_template_dir)) if re.match('Vcb*\_shapes.root', r, re.DOTALL)]
    root_files = [r for r in os.listdir(join(unsmoothed_template_dir)) if "_shapes.root" in r]


    # print ("smoothing with method", method)
    # print ("root_files", root_files)

    for file_ in root_files:
        # print ("----entering file loop, file_", file_)
        outfile = smoothed_template_dir+"/"+file_
        outfile_root = uproot.recreate(outfile)
        nominal = get_nominal_templates(uproot.open(join(unsmoothed_template_dir, file_)))
        # print ("-------------------------------------------------------------------")
        # print ("nominal")
        # print (nominal)
        processes_ = get_processes(uproot.open(join(unsmoothed_template_dir, file_)))
        processes_ = [p for p in processes_ if not "data" in p]
        # print ("-------------------------------------------------------------------")
        # print ("processes_")
        # print (processes_)
        systematics_ = get_systematics_names(uproot.open(join(unsmoothed_template_dir, file_)))
        # print ("-------------------------------------------------------------------")
        # print ("systematics_")
        # print (systematics_)
        categories_ = get_categories(uproot.open(join(unsmoothed_template_dir, file_)))
        # print ("-------------------------------------------------------------------")
        # print ("categories_")
        # print (categories_)
        # break

        listSaved = []
        infile = uproot.open(unsmoothed_template_dir+"/"+file_)
        for cat_ in categories_:
            for syst_ in systematics_:
                for proc_ in processes_:
                    nomHist = nominal[cat_+"/"+proc_]
                    # print (cat_, syst_)
                    # if "201" in syst_:
                    #     systYear = syst_.split("_")[-1].replace("Up","").replace("Down","")
                    #     if "13TeV" in systYear:
                    #         systYear = "2018" #special for HEM
                    #     # print ("systYear", systYear)
                    #     # if systYear not in cat_:
                    #     if systYear not in cat_ and "FR2" not in cat_:
                    #         print ("skip this one", syst_)
                    #         continue
                    if matchSystSymm(syst_):
                        forceSymm = True
                    else:
                        forceSymm = False
                    # unsmoothed_sys = [infile[cat_+"/"+proc_+"__"+syst_ + "Up"], infile[cat_+"/"+proc_+"__"+syst_ + "Down"]]


                    # for process based systematics we won;t find matches for other processes, so we have to implement a safeguard that we just skip it, but we print this out for debugging
                    # so basically if "cat_+"/"+proc_+"_"+syst_ + "Up" is not in infile, we skip it and print out a message, but we still save the nominal and data templates for this category and process
                    if cat_+"/"+proc_+"_"+syst_ + "Up" not in infile:
                        print ("no systematic template found for", cat_+"/"+proc_+"_"+syst_ + "Up, skipping smoothing for this one")
                        if cat_+"/"+proc_ not in listSaved:
                            outfile_root[cat_+"/"+proc_] = nomHist
                            listSaved.append(cat_+"/"+proc_)
                        continue

                    unsmoothed_sys = [infile[cat_+"/"+proc_+"_"+syst_ + "Up"], infile[cat_+"/"+proc_+"_"+syst_ + "Down"]]
                    if matchSyst(syst_, bypass = True):
                        print ("Smoothing", syst_, cat_, proc_)
                        smoothed_sys = get_smoothed_up_and_down(nomHist, *unsmoothed_sys, method, forceSymm_ = forceSymm, doNotSymm_ = matchSystNotSymm(syst_))
                        if cat_+"/"+proc_ not in listSaved:
                            outfile_root[cat_+"/"+proc_] = nomHist
                            listSaved.append(cat_+"/"+proc_)
                        outfile_root[cat_+"/"+proc_+"_"+syst_ + "Up"] = smoothed_sys[0]
                        outfile_root[cat_+"/"+proc_+"_"+syst_ + "Down"] = smoothed_sys[1]
                    else:
                        if cat_+"/"+proc_ not in listSaved:
                            outfile_root[cat_+"/"+proc_] = nomHist
                            listSaved.append(cat_+"/"+proc_)
                        outfile_root[cat_+"/"+proc_+"_"+syst_ + "Up"] = unsmoothed_sys[0]
                        outfile_root[cat_+"/"+proc_+"_"+syst_ + "Down"] = unsmoothed_sys[1]
                # and data
                if cat_+"/"+"data_obs" not in listSaved:
                    nomHistData = nominal[cat_+"/"+"data_obs"]
                    outfile_root[cat_+"/"+"data_obs"] = nomHistData
                    listSaved.append(cat_+"/"+"data_obs")


if __name__ == '__main__':
    parser = ArgumentParser('Smooth systematics. Templates can be selected using regular expressions '
                            '(with the dot operator representing any character)')
    parser.add_argument('template_directory', nargs='+',
                        help='directory inside results folder containing the templates in a Cards directory')
    parser.add_argument('-ch', '--channel', default=['*'], choices=['FH', 'SL', 'DL'], nargs='+',
                        help='Channel. Use star to take all available. Default: %(default)s')
    parser.add_argument('-y', '--years', default=['*'], nargs='+',
                        help='year(s). Use star to take all available. Default: %(default)s')
    parser.add_argument('-m', '--method', default=['unweightedSpline'], nargs='+',
                        choices=['lowess', 'weightedSpline', 'unweightedSpline'],
                        help='Smoothing algorithm. Default: %(default)s')
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()

    print(args)

    for td, c, y, m in product(args.template_directory, args.channel, args.years, args.method):
        print (f'processing {td} {c} {y} with method {m}')
        cards_dirs = glob(join(td))
        print (f'found cards directories: {cards_dirs}')
        smooth_dir = td + 'smoothed' + m.capitalize()
        sd = td.replace(td, smooth_dir)
        print(f'outputting to {sd}')
        if not os.path.exists(sd):
            os.makedirs(sd)
        process_file(td, sd, m, args)
