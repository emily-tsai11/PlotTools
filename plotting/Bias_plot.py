#!/usr/bin/env python
import argparse
import ctypes
import glob

from utilities import style
from utilities.auxiliary import *


def get_combine_values(file_path, tree_name, expr, doBias = False, injectedSignal = 1.0):

    vals = []

    if not os.path.getsize(file_path) > 10: return []

    ifile = ROOT.TFile.Open(file_path)
    if (not ifile) or ifile.IsZombie() or ifile.TestBit(ROOT.TFile.kRecovered): return []

    itree = ifile.Get(tree_name)
    if not itree:
       print('get_combine_values -- target TTree object not found in input file: '+file_path+':'+tree_name)
       return None

    POIList = {
        # "rate_ttHcc": 0,
        # "rate_ttHbb" : 2,
        # "rate_ttZcc": 4,
        # "rate_ttZbb": 6
        "r": 0
    }
    
    entries = []
    toys = []
    vals = []
    quantiles = []
    nToys = 0
    for entry in itree:
        # quant = getattr(entry, "quantileExpected")
        # val = getattr(entry, expr)
        # if quant == -1:
        #     if doBias:
        #         newVal = injectedSignal - val
        #     else:
        #         newVal = val
        #     vals.append(val)

        # print (entry, getattr(entry, "iToy"), getattr(entry, "quantileExpected"), getattr(entry, "rate_ttHcc"), getattr(entry, "rate_ttHbb"), getattr(entry, "rate_ttZcc"), getattr(entry, "rate_ttZbb"))

        numToy = getattr(entry, "iToy")
        val = getattr(entry, expr)
        quant = getattr(entry, "quantileExpected")
        entries.append(entry)
        toys.append(numToy)
        vals.append(val)
        quantiles.append(quant)
        if quant == -1:
            nToys = nToys + 1

    print(entries)
    print(toys)
    print(vals)
    print(quantiles)
    print(nToys)

    # -> order is ttHccDown, ttHccUp, ttHbbDown, ttHbbUp, ttZccDown, ttZccUp, ttZbbDown, ttZbbUp

    # Name: limit Title: limit 1 -1.0 -3.987074851989746 0.7276461124420166 2.397599697113037 0.9522366523742676
    # Name: limit Title: limit 1 -0.3199999928474426    -15.082571029663086 0.7276461124420166 2.397599697113037 0.9522366523742676
    # Name: limit Title: limit 1 0.3199999928474426       6.795461654663086 0.7276461124420166 2.397599697113037 0.9522366523742676
    # Name: limit Title: limit 1 -0.3199999928474426     -3.987074851989746 0.2440432906150818 2.397599697113037 0.9522366523742676
    # Name: limit Title: limit 1 0.3199999928474426      -3.987074851989746 1.2887614965438843 2.397599697113037 0.9522366523742676
    # Name: limit Title: limit 1 -0.3199999928474426     -3.987074851989746 0.7276461124420166 0.9560200572013855 0.9522366523742676
    # Name: limit Title: limit 1 0.3199999928474426      -3.987074851989746 0.7276461124420166 3.970207929611206 0.9522366523742676
    # Name: limit Title: limit 1 -0.3199999928474426     -3.987074851989746 0.7276461124420166 2.397599697113037 0.2523677945137024
    # Name: limit Title: limit 1 0.3199999928474426      -3.987074851989746 0.7276461124420166 2.397599697113037 1.6948245763778687


    # print ("-------------")
    # print (expr)
    biases = []
    centrals = []
    # original was 9 for 4 POis, now 3 for 1 POI
    for idxToy in range(nToys):
        # print (idxToy)
        checkQuantile = quantiles[idxToy*3]
        if checkQuantile == -1:
            centralVal = vals[idxToy*3]
            errUp =  abs(vals[idxToy*3 + POIList[expr]+1] - centralVal)
            errDown =  abs(vals[idxToy*3 + POIList[expr]+2] - centralVal)
            err = abs(errUp + errDown)/2.
            # print(idxToy, idxToy*3 + POIList[expr]+1, centralVal, err)
            bias = (centralVal-injectedSignal)/(err)
            centrals.append(centralVal)
            biases.append(bias)


    ifile.Close()

    # return vals
    if doBias:
        return biases
    else:
        return centrals


def plotBias(toys, output_plot_basename, POI, txtTL="", txtTR="", injectedSignal = 1.0, doBias = False):
    ### conf
    log_prx = os.path.basename(__file__)+' -- '

    ext_ls = sorted(list(set(['pdf','png'])))

    if len(ext_ls) == 0:
       KILL(log_prx+'empty list of extensions for output file(s) [-e]')

    ROOT.gROOT.SetBatch()
    ### -------------------

    TOYS = []

    alltoys = glob.glob(toys)
    # print (toys)
    # print (alltoys)
    for at in alltoys:
        # print ("----------",at)
        if not os.path.isfile(at):
            WARNING(log_prx+'invalid path to input path for MC-Toys: '+at)

        if  get_combine_values(at, "limit", POI) is None:
            print(log_prx+'logic error: toys input is NONE: '+str(at))
            return

        if doBias:
            TOYS += get_combine_values(at, "limit", POI, doBias = True, injectedSignal = injectedSignal)
        else:
            TOYS += get_combine_values(at, "limit", POI, doBias = False)

        # print (TOYS)

    if len(TOYS) == 0:
        WARNING(log_prx+'logic error: no values found in TOYS input')
        return

    # print (TOYS)
    ### -------------------

    ### output plot
    if not doBias:
        output_plot_basename = (output_plot_basename+"/"+POI if output_plot_basename else 'Bias_'+POI)
    else:
        output_plot_basename = (output_plot_basename+"/"+"Bias_"+POI if output_plot_basename else 'Bias_'+POI)

    out_plot_files = []
    for ext in ext_ls:
        out_plot_f = os.path.abspath(output_plot_basename)+'.'+ext
        out_plot_files.append(out_plot_f)

    if len(out_plot_files) == 0:
       raise SystemExit(1)

    output_plot_dir = os.path.dirname(os.path.abspath(output_plot_basename))
    if not os.path.isdir(output_plot_dir):
        EXE('mkdir -p '+output_plot_dir)

    ### output plot
    canvas_name = os.path.basename(output_plot_basename+"_"+POI)
    cbias = ROOT.TCanvas(canvas_name, canvas_name, 800, 800)
    L, R, T, B = 0.150, 0.035, 0.100, 0.150
    cbias.SetLeftMargin  (L)
    cbias.SetRightMargin (R)
    cbias.SetTopMargin   (T)
    cbias.SetBottomMargin(B)
    ROOT.TGaxis.SetMaxDigits(4)
    ROOT.TGaxis.SetExponentOffset(-L+.50*L, 0.03, 'y')

    binN = int(float(len(TOYS)) / 10.)
    # binN = int(float(len(TOYS)) / 5.)

    # xmin0 = max(0, min(min(TOYS) * 0.90 , min(TOYS) - 5))
    # xmin0 = max(0, min((TOYS)) * 0.90)
    xmin0 = min((TOYS))
    if xmin0<0:
        xmin0 = xmin0 * 1.1
    else:
        xmin0 = xmin0 * 0.9
    xmax0 = max(TOYS) * 1.10

    # if xmax0>10.*np.mean(TOYS):
    #     xmax0 = np.mean(TOYS)*1.5

    binW0 = (xmax0-xmin0) / binN
    binW = (binW0)

    xmin = xmin0
    xmax = xmin + binN*binW

    toys_h1 = ROOT.TH1F(canvas_name+'_toys_h1', canvas_name+'_toys_h1', binN, xmin, xmax)
    toys_h1.SetStats(0)
    toys_h1.Sumw2(0)
    toys_h1.SetBinErrorOption(ROOT.TH1.kPoisson)
    for toy_v in TOYS:
        toys_h1.Fill(toy_v)

    toys_h1.SetMarkerStyle(20)
    toys_h1.SetMarkerSize(1.5)
    toys_h1.SetMarkerColor(1)
    toys_h1.SetLineColor(1)
    toys_h1.SetLineWidth(2)
    toys_h1.SetLineStyle(1)

    cbias.cd()
    toys_h1.Draw('hist')

    ymin = 1e-4
    ymax = toys_h1.GetMaximum() / 0.5

    chi2_func = None
    # if chi2_fit:
    # if True:

    #    chi2_func = ROOT.TF1('chi2_func', '[0]*ROOT::Math::chisquared_pdf(x,[1])', xmin, xmax)
    #    chi2_func.SetLineColor(ROOT.kRed)
    #    chi2_func.SetFillColor(ROOT.kRed)
    #    chi2_func.SetParameter(0, toys_h1.Integral())
    #    chi2_func.SetParameter(1, toys_h1.GetMean(1))

    #    chi2_fit = toys_h1.Fit(chi2_func, 'mlerso')


    #    chi2_func.SetLineWidth(2)
    #    chi2_func.Draw('same')

    # toys_h1.Draw('lep,same')
    # toys_h1.Draw('axis,same')

    cbias.Update()
    if not doBias:
        toys_h1.SetTitle(';'+POI.replace("_"," ")+';Number of toys;')
    else:
        toys_h1.SetTitle(';'+POI.replace("_"," ")+" bias"+';Number of toys;')
    toys_h1.GetXaxis().SetLabelSize  (0.045)
    toys_h1.GetYaxis().SetLabelSize  (0.045)
    toys_h1.GetXaxis().SetTitleSize  (0.055)
    toys_h1.GetYaxis().SetTitleSize  (0.055)
    toys_h1.GetXaxis().SetTitleOffset(1.05)
    toys_h1.GetYaxis().SetTitleOffset(1.20)
    toys_h1.GetYaxis().SetRangeUser(ymin, ymax)

    legH = (0.28 if chi2_func else 0.21)

    leg = ROOT.TLegend(L+(1-R-L)*.550, B+(1-T-B)*(.975-legH), L+(1-R-L)*.975, B+(1-T-B)*.975)
    leg.SetBorderSize(0)
    leg.SetFillColor(0)
    leg.SetTextFont(42)
    leg.AddEntry(toys_h1, 'Toy data', 'f')

    if chi2_func:
       chi2_func_str  = '#chi^{2} fit, ndf = '
       chi2_func_str += '{:.1f} #pm {:.1f}'.format(chi2_func.GetParameter(1), chi2_func.GetParError(1))
       leg.AddEntry(chi2_func, chi2_func_str, 'l')

    leg.Draw('same')

    mean = toys_h1.GetMean()
    x_ = np.array([0.])
    q_ = ctypes.c_double(0.5)
    median = toys_h1.GetQuantiles(1, x_, q_)
    rms = toys_h1.GetRMS()
    ntoys = len(TOYS)
    print ("ntoys", ntoys)
    # print ("median", q_)
    print ("median", x_)
    print ("mean", mean)
    print ("rms", rms)

    meanLatex = ROOT.TLatex()
    meanLatex.SetTextSize(0.85 * meanLatex.GetTextSize())
    meanLatex2 = ROOT.TLatex()
    meanLatex2.SetTextSize(0.85 * meanLatex2.GetTextSize())
    meanLatex3 = ROOT.TLatex()
    meanLatex3.SetTextSize(0.85 * meanLatex3.GetTextSize())
    meanLatex4 = ROOT.TLatex()
    meanLatex4.SetTextSize(0.85 * meanLatex3.GetTextSize())

    coordsX = 0.2
    coordsY = 0.75
    meanLatex.DrawLatexNDC(coordsX, coordsY, "nToys: "+str(np.round(ntoys)))
    meanLatex2.DrawLatexNDC(coordsX, coordsY-0.05,  "mean: "+str(np.round(mean,3)))
    meanLatex3.DrawLatexNDC(coordsX, coordsY-0.1,  "median: "+str(np.round(x_[0],3)))
    meanLatex4.DrawLatexNDC(coordsX, coordsY-0.15,  "rms: "+str(np.round(rms,3)))

    txtTL = ROOT.TLatex(L+(1-R-L)*0.00, (1-T)+T*.25, txtTL)
    txtTL.SetTextAlign(11)
    txtTL.SetTextSize(0.055)
    txtTL.SetTextFont(42)
    txtTL.SetNDC()
    txtTL.Draw('same')

    txtTR = ROOT.TLatex(L+(1-R-L)*1.00, (1-T)+T*.25, txtTR)
    txtTR.SetTextAlign(31)
    txtTR.SetTextSize(0.055)
    txtTR.SetTextFont(42)
    txtTR.SetNDC()
    txtTR.Draw('same')

    for _tmp in out_plot_files:
        cbias.SaveAs(_tmp)

    cbias.Close()
    ### --------------------------------------------

