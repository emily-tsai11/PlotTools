import glob
import json
from array import array

import numpy as np
import ROOT
from plotting.Bias_plot import plotBias
from plotting.GOF_plotPValue import plotGOF
# from plotting.plotPrePostFit import (plotMergedPostFitPlots,
#                                      producePrePostFitFromCombineHarvester, plotPostFitPlots)
# from ROOT import *
from utilities.auxiliary import *
from utilities.include import *

def producePrePostFitFromCombineHarvester(datacard, workspace, outputDir ,outputfile, fitresult, fitName="fit_mdf", nSamples="1500", testOnly = False):
    command = "PostFitShapesFromWorkspace"
    command += " -d "+datacard
    command += " -w "+workspace
    command += " --output "+outputDir+"/"+outputfile
    command += " -m 125.38"
    command += " --samples "+nSamples
    command += " --covariance"
    command += " --skip-proc-errs"
    # command += " --total-shapes"
    command += " -f "+fitresult+":"+fitName
    command += " --postfit --sampling"
    if not os.path.exists(outputDir):
        os.makedirs(outputDir)
    print (command)
    if not testOnly:
        subprocess.call(command, shell=True)
    return command


unblind_global = False

def convertChannel(channelIn):
    # print (channelIn)
    # if channelIn == "SL":
    if channelIn == "Vcb":
        return "Lepton + jets"
    elif channelIn == "DL":
        return "Dilepton"
    elif channelIn == "FH":
        return "Fully hadronic"
    elif channelIn == "ALL":
        return "Combined"

def getRighttext(year):
    intLumi15 = 19502.
    intLumi16APV = 19502.
    intLumi16 = 16812.
    intLumi17 = 41480.
    intLumi18 = 59830.
    intLumiFR2 = 137620
    intLumiF16 = 36314
    intLumi2024 = 110000.

    if year=="2018":
        intLumi=intLumi18
    elif year=="2017":
        intLumi=intLumi17
    elif year=="2016APV":
        intLumi=intLumi16APV
    elif year=="2015":
        intLumi=intLumi15
    elif year=="2016":
        intLumi=intLumi16
    elif year=="FR2":
        intLumi=intLumiFR2
    elif year=="FR2old":
        intLumi=intLumiFR2
    elif year=="F16":
        intLumi=intLumiF16
    elif year=="2024":
        intLumi=intLumi2024
    else:
        intLumi=0.

    # return "#scale[0.72]{%.1f fb^{-1} (%s TeV)}" % (intLumi / 1000., 13.)
    return "#scale[0.72]{%.0f fb^{-1} (%s TeV)}" % (intLumi / 1000., 13.6)


def getPOIsAndNuisancesFromFile(filename):
    with open(filename) as json_file:
        data = json.load(json_file)
    POIs = data["POIs"]
    dictPOIs = {}
    dictConstraints = {}
    dictConstraintsAndPOIs = {}
    for entry in POIs:
        dictPOIs[entry["name"]] = entry["fit"]
        dictConstraintsAndPOIs[entry["name"]] = entry["fit"]
    params = data["params"]
    for entry in params:
        dictConstraints[entry["name"]] = entry["fit"]
        dictConstraintsAndPOIs[entry["name"]] = entry["fit"]
    # return dictPOIs,dictConstraints
    # return dictConstraints
    return dictConstraintsAndPOIs

def getPOIsAndNuisancesFromFitFile(filename):
    fin = ROOT.TFile(filename)
    rfr = fin.Get("fit_mdf")
    # rfr.Print()
    all_pars = rfr.floatParsFinal()
    dictConstraints = {}
    # for i in xrange(all_pars.getSize()):
    for i in range(all_pars.getSize()):
        par = all_pars.at(i)
        # print '%s: %+.3f + %.3f - %.3f' % (par.GetName(), par.getVal(), par.getErrorHi(), par.getErrorLo())
        # dictConstraints[par.GetName()] = [par.getErrorLo(),par.getVal(),par.getErrorHi()]
        dictConstraints[par.GetName()] = [par.getErrorLo(),par.getValV(),par.getErrorHi()]
    return dictConstraints


def createGraphsFromConstraints(listN, names, dictConstraints):
    graphs = []
    nNuisance = len(listN)
    nGroups = len(names)
    max = 1000.
    # stepsize = max/((nGroups+(nGroups-1))*nNuisance)
    # empty = 1
    empty = 0.5
    # bigstep = max/(((empty+1)*nNuisance))
    bigstep = max/(((empty+1)*nNuisance)) if nNuisance > 0 else max/(((empty+1)))
    stepsize = bigstep/(nGroups-1) if nGroups > 1 else bigstep
    # print bigstep,stepsize,nGroups,nNuisance
    def getYCoord(iGroupLoop, iN):
        # return min + (   stepsize*(iN*nGroups) + iGroupLoop*stepsize )
        # return min + (   iGroupLoop+nNuisance )*stepsize + iN*stepsize
        # return min + (   iN*nGroups )*stepsize + iGroupLoop*stepsize
        # return min + (   iN*nGroups )*stepsize + (iGroupLoop+1)*stepsize
        # return min + (    iN*(nNuisance-1)*max/(2.*nNuisance-1)         +  (stepsize*iGroupLoop)            )
        return (iN*(empty+1))*bigstep - (stepsize*iGroupLoop)

    iGroup = 0
    # for name in names:
    coordinates=[]

    for iGroup in range(nGroups):
        name = names[iGroup]
        gr = ROOT.TGraphAsymmErrors()

        for iNuisance,nuisance in enumerate(listN):
            iNuisance = iNuisance+1
            if nuisance in dictConstraints[name]:
                x = dictConstraints[name][nuisance][1]
                exLow,exhigh = abs(dictConstraints[name][nuisance][0]),abs(dictConstraints[name][nuisance][2])
                gr.SetPoint(iNuisance-1, x, getYCoord(iGroup,iNuisance))
                gr.SetPointError(iNuisance-1, exLow, exhigh, 0., 0.)
        gr.GetXaxis().SetRangeUser(-1.,1.)
        gr.GetXaxis().SetTitle("#hat{#theta}-#theta/#Delta#theta")
        graphs.append(gr)

    for iNuisance,nuisance in enumerate(listN):
        iNuisance = iNuisance+1
        c = (iNuisance*(empty+1))*bigstep - (stepsize*nGroups/2.)
        coordinates.append((c,nuisance))
    
    return graphs, coordinates

def main(doPrePostFitPlots = False, doEvolutionPlots = False, doImpactPlots = False, doGoodnessOfFitPlots = False, doCorrelations = False, doBiasTestPlots = False, doCondor = False):
    # basePath = "/eos/cms/store/cmst3/user/sewuchte/ttHccNewFixedAll/"
    # basePath = "/eos/cms/store/cmst3/user/sewuchte/ttHcc_workshop/"
    # basePath = "/eos/cms/store/cmst3/user/sewuchte/bkp_ttHcc_ANv4/"
    # basePath = "/eos/cms/store/cmst3/user/sewuchte/ttHcc_ANv4/"
    # basePath = "/eos/cms/store/cmst3/group/vhcc/ttHcc_trees/HTC_results/ttHcc_ANv4/"
    # basePath = "/eos/cms/store/cmst3/group/vhcc/ttHcc_trees/HTC_results/ttHcc_ARCv1/"
    # basePath = "/eos/cms/store/cmst3/group/top/Vcb_trees/HTC_results/ForANv1/"
    basePath = "/eos/cms/store/cmst3/group/top/Vcb_trees/HTC_results/preUnblinding/"

    style.defaultStyle()
    s = style.defaultStyle()

    can = ROOT.TCanvas("","",900,1200)
    style.divideByBinWidth = False
    style.minimumOne = False
    can.SetLeftMargin(0.35)


    # basename_ = "070526_ge2bge1c"
    # basename_ = "070526_ge2bge1c_fix"
    # basename_ = "070526_CRttWcbM0p2m0p8"
    # basename_ = "070526_ge2bge1c_fix_smoothed"
    # basename_ = "070526_CRttWcbM0p2m0p8_smoothed"
    # basename_ = "080526_ge2bge1c_fix_clean"
    # basename_ = "080526_ge2bge1c_fix_clean_pseudoData5FS"
    # basename_ = "100626_ge2bge1c_fix_clean_pseudoData5FS"
    # basename_ = "100626_ge2bge1c_fix_clean_forJME"
    # basename_ = "100626_ge2bge1c_fix_clean_onlySurvivingVeto"

    basename_ = "250826_preUnblinding_noFlavTagSymm"
    # basename_ = "250826_preUnblinding_nonSmoothed"
    # basename_ = "250826_preUnblinding"

    # basename = "FitStudies_Datacards_280426_simplified_"
    # basename = "FitStudies_Datacards_280426_smoothed_simplified_"
    # basename = "FitStudies_Datacards_280426_trial1_simplified_"
    # basename = "FitStudies_Datacards_280426_trial2_simplified_"
    # basename = "FitStudies_Datacards_280426_trial3_simplified_"
    # basename = "FitStudies_Datacards_290426_correctedBnormalization_simplified_"
    # basename = "FitStudies_Datacards_290426_correctedBnormalization_noPeterson_simplified_"
    # basename = "FitStudies_Datacards_290426_correctedBnormalization_noPeterson_inflateFlav_simplified_"
    # basename = "FitStudies_Datacards_040526_fixes_simplified_"
    basename = "FitStudies_Datacards_"+basename_+"_simplified_"


    if "pseudoData" in basename_:
        unblind = True
    else:
        unblind = unblind_global

    ev_names = [
        # basename+"VR/",
        # basename+"VR/",
        basename+"SR/",
        basename+"SR/",
        basename+"CR/",
        basename+"CR/",
        # basename+"CRbb/",
        # basename+"CRbj/",
        # basename+"CRcc/",
        # basename+"CRcj/",
        # basename+"CR2b/",
        # basename+"CR2c/",
        # basename+"CRlf/",
        # basename+"CRnolf/",
        # basename+"SRnolf/",
        # basename+"All/",
        # basename+"All/",
        # basename+"CRPlusTTZ/",
        # basename+"CRPlusTTZ/",
        # basename+"CRPlusTTH/",
        # basename+"CRPlusTTH/",
    ]

    ev_namesOut = [
        # "VR_obs/",
        # "VR_exp/",
        "SR_exp/",
        "SR_obs/",
        "CR_exp/",
        "CR_obs/",
        # "CRbb_obs/",
        # "CRbj_obs/",
        # "CRcc_obs/",
        # "CRcj_obs/",
        # "CR2b_obs/",
        # "CR2c_obs/",
        # "CRlf_obs/",
        # "CRnolf_obs/",
        # "SRnolf_obs/",
        # "All_exp/",
        # "All_obs/",
        # "CRPlusTTZ_exp/",
        # "CRPlusTTZ_obs/",
        # "CRPlusTTH_exp/",
        # "CRPlusTTH_obs/",
    ]

    # outwebfolder = ""
    # outwebfolder = "/eos/home-s/sewuchte/www/Vcb/Apr26/"
    outwebfolder = "/eos/home-s/sewuchte/www/Vcb/Aug26/"
    outfolderlocal = "/afs/cern.ch/work/s/sewuchte/private/VCB/CMSSW_15_0_10/src/PlotTools/"

    # baseOutputFolder = outwebfolder+"BehaviorStudies_2026-04-28/"
    # baseOutputFolder = outwebfolder+"BehaviorStudies_280426/"
    # baseOutputFolder = outwebfolder+"BehaviorStudies_280426_smoothed/"
    # baseOutputFolder = outwebfolder+"BehaviorStudies_280426_trial1/"
    # baseOutputFolder = outwebfolder+"BehaviorStudies_280426_trial2/"
    # baseOutputFolder = outwebfolder+"BehaviorStudies_280426_trial3/"
    # baseOutputFolder = outwebfolder+"BehaviorStudies_290426_correctedBnormalization/"
    # baseOutputFolder = outwebfolder+"BehaviorStudies_290426_correctedBnormalization_noPeterson/"
    # baseOutputFolder = outwebfolder+"BehaviorStudies_290426_correctedBnormalization_noPeterson_inflateFlav/"
    # baseOutputFolder = outwebfolder+"BehaviorStudies_040526_fixes/"
    # baseOutputFolder = outwebfolder+"BehaviorStudies_070526_ge2bge1c_fixes/"
    baseOutputFolder = outwebfolder+"BehaviorStudies_"+basename_+"/"


    baseOutputFolderLocal = baseOutputFolder.replace(outwebfolder,outfolderlocal)

    for ev_name, ev_nameOut in zip(ev_names, ev_namesOut):

        # print ("DOING", ev_name, ev_nameOut)

        extNames = [
            ev_name+"/workspace_Vcb_SL_2024/",
            # ev_name+"/workspace_ALL_2015/",
            # ev_name+"/workspace_ALL_2016/",
            # ev_name+"/workspace_ALL_2017/",
            # ev_name+"/workspace_ALL_2018/",
            # ev_name+"/workspace_ALL_FR2/",
            # # ev_name+"/workspace_DL_2015/",
            # # ev_name+"/workspace_DL_2016/",
            # # ev_name+"/workspace_DL_2017/",
            # # ev_name+"/workspace_DL_2018/",
            # ev_name+"/workspace_DL_FR2/",
            # # ev_name+"/workspace_SL_2015/",
            # # ev_name+"/workspace_SL_2016/",
            # # ev_name+"/workspace_SL_2017/",
            # # ev_name+"/workspace_SL_2018/",
            # ev_name+"/workspace_SL_FR2/",
            # # ev_name+"/workspace_FH_2015/",
            # # ev_name+"/workspace_FH_2016/",
            # # ev_name+"/workspace_FH_2017/",
            # # ev_name+"/workspace_FH_2018/",
            # ev_name+"/workspace_FH_FR2/",
        ]

        for i in range(len(extNames)):
            extNames[i] = extNames[i].replace("//","/")

        #####################################################################
        ######################## plotNuisanceEvolution
        #####################################################################
        if doEvolutionPlots:
            # names = [x.split("/")[1]+"_"+x.split("/")[2] for x in extNames]
            names = [x.split("/")[1].replace("workspace_","") for x in extNames]

            filenames =[]
            if "obs" in ev_nameOut:
                filenames_ = [
                    basePath+e+"/ImpactsObserved/higgsCombine_nominal_obs_impacts.Impacts.mH125p38.json" for e in extNames
                ]
            else:
                filenames_ = [
                    basePath+e+"/ImpactsExpected/higgsCombine_nominal_exp_impacts.Impacts.mH125p38.json" for e in extNames
                ]

            filenames = []
            for f_ in filenames_:
                filenames.append(f_)

            dictCon = {}
            dictP = {}
            listN = []
            listPOIs = []

            usedNames=[]

            for fname,n in zip(filenames, names):
                if os.path.exists(fname):
                    dictConstraints = getPOIsAndNuisancesFromFile(fname)
                    dictCon[n]=dictConstraints
                    usedNames.append(n)
                    for entry in dictConstraints:
                        if entry not in listN:
                            if not "prop" in entry:
                                listN.append(entry)

            graphs, coordinates = createGraphsFromConstraints(listN[0:10], usedNames, dictCon)

            for isub, sub in enumerate([listN[i:i+5] for i in range(0, len(listN), 5)]):
                graphs, coordinates = createGraphsFromConstraints(sub, usedNames, dictCon)
                colors= [ROOT.kBlack, ROOT.kRed+1, ROOT.kBlue+1, ROOT.kGreen+1, ROOT.kOrange-3, ROOT.kGreen-2, ROOT.kRed-3,ROOT.kCyan, ROOT.kViolet,ROOT.kGreen-7,ROOT.kPink-9, ROOT.kCyan+3]
                colors=colors*3

                # outFolder=(baseOutputFolder+"/EvolutionPlots/").replace("Plots/","Plots"+ev_name.replace("FitStudies","")+"/")
                outFolder=(baseOutputFolder+"/EvolutionPlots/").replace("Plots/","_"+ev_nameOut.replace("FitStudies","")+"/")

                can.Clear()
                # leg = ROOT.TLegend(0.37,0.76,0.98,0.935)
                leg = ROOT.TLegend(0.37,0.76,0.96,0.935)
                leg.SetNColumns(2)
                leg.SetTextSize(0.02)

                line1 = ROOT.TLine(1,0.,1,1010.)
                line1.SetLineColor(ROOT.kBlack)
                line1.SetLineStyle(ROOT.kDotted)
                line2 = ROOT.TLine(-1,0.,-1,1010.)
                line2.SetLineColor(ROOT.kBlack)
                line2.SetLineStyle(ROOT.kDotted)
                line3 = ROOT.TLine(0.,0.,0.,1010.)
                line3.SetLineColor(ROOT.kBlack)
                line3.SetLineStyle(ROOT.kDotted)
                line4 = ROOT.TLine(-2.,0.,-2.,1010.)
                line4.SetLineColor(ROOT.kBlack)
                line4.SetLineStyle(ROOT.kDotted)


                i = 0
                for graph in graphs:
                    graph.SetMarkerColor(colors[i])
                    graph.SetLineColor(colors[i])
                    # if i%2==0:
                    #     graph.SetMarkerColor(colors[i/2])
                    #     graph.SetLineColor(colors[i/2])
                    # else:
                    #     graph.SetMarkerColor(colors[int((i-1)/2.)])
                    #     graph.SetLineColor(colors[int((i-1)/2.)])
                    #     # graph.SetLineStyle(ROOT.kDashed)

                    graph.GetXaxis().SetRangeUser(-3.,3.)
                    graph.GetXaxis().SetLimits(-3.,3.)
                    graph.GetYaxis().SetRangeUser(0,1300)
                    graph.GetYaxis().SetLimits(0,1300)
                    graph.GetYaxis().SetTickLength(0.)
                    graph.GetYaxis().SetLabelSize(0.)
                    graph.GetXaxis().SetTickLength(0.)
                    graph.GetXaxis().SetTitle("#hat{#theta}-#theta/#Delta#theta")
                    graph.SetLineWidth(2)
                    graph.SetMarkerStyle(8)
                    leg.AddEntry(graph, names[i],"lep")

                    if i==0:
                        graph.GetXaxis().SetRangeUser(-3.,3.)
                        graph.GetXaxis().SetLimits(-3.,3.)
                        graph.Draw("AP")
                        graph.GetXaxis().SetRangeUser(-3.,3.)
                        graph.GetXaxis().SetLimits(-3.,3.)
                        graph.GetXaxis().SetTitle("#hat{#theta}-#theta/#Delta#theta")
                        graph.Draw("AP")
                        can.Update()
                        line1.Draw("same")
                        line2.Draw("same")
                        line3.Draw("same")
                    elif graph.GetN()>0:
                        graph.GetXaxis().SetRangeUser(-3.,3.)
                        graph.GetXaxis().SetLimits(-3.,3.)
                        graph.GetXaxis().SetTitle("#hat{#theta}-#theta/#Delta#theta")
                        graph.Draw("Psame")
                        can.Update()
                    i = i+1

                ROOT.gPad.RedrawAxis()

                labels=[]
                can.Update()

                for yC ,n in coordinates:
                    t = ROOT.TText(-6.2,yC,n)
                    t.SetTextSize(0.021)
                    t.Draw("same")
                    labels.append(t)

                if not os.path.exists(outFolder):
                    os.makedirs(outFolder)

                info = ""
                l = aux.LabelEvolution(info="#scale[0.7]{%s}" % info, sim=(not "obs" in ev_nameOut), year="", status="Preliminary")

                leg.Draw("same")
                saveName = "EvolutionPlot_"+str(isub)
                aux.save(saveName, folder=outFolder, normal=True, log=False)

        #####################################################################
        ######################## plotRateParamEvolution
        #####################################################################
        if doEvolutionPlots:
            # names = [x.split("/")[1]+"_"+x.split("/")[2] for x in extNames]
            names = [x.split("/")[1].replace("workspace_","") for x in extNames]

            filenames =[]
            if "obs" in ev_nameOut:
                filenames_ = [
                    # basePath+e+"/ImpactsObserved/multidimfit_initialFit__nominal_obs_impacts.root" for e in extNames
                    basePath+e+"/FitObserved/multidimfit_nominal_obs_fit.root" for e in extNames
                ]
            else:
                filenames_ = [
                    # basePath+e+"/ImpactsExpected/multidimfit_initialFit__nominal_exp_impacts.root" for e in extNames
                    basePath+e+"/FitExpected/multidimfit_nominal_exp_fit.root" for e in extNames
                ]

            filenames = []
            for f_ in filenames_:
                filenames.append(f_)

            dictCon = {}
            dictP = {}
            listN = []
            listPOIs = []

            usedNames=[]

            for fname,n in zip(filenames, names):
                if os.path.exists(fname):
                    # dictConstraints = getPOIsAndNuisancesFromFile(fname)
                    dictConstraints = getPOIsAndNuisancesFromFitFile(fname)
                    dictCon[n]=dictConstraints
                    usedNames.append(n)
                    for entry in dictConstraints:
                        if entry not in listN:
                            # if not "prop" in entry:
                            if "SF_norm" in entry:
                                listN.append(entry)

            graphs, coordinates = createGraphsFromConstraints(listN[0:10], usedNames, dictCon)

            for isub, sub in enumerate([listN[i:i+5] for i in range(0, len(listN), 5)]):
                graphs, coordinates = createGraphsFromConstraints(sub, usedNames, dictCon)
                colors= [ROOT.kBlack, ROOT.kRed+1, ROOT.kBlue+1, ROOT.kGreen+1, ROOT.kOrange-3, ROOT.kGreen-2, ROOT.kRed-3,ROOT.kCyan, ROOT.kViolet,ROOT.kGreen-7,ROOT.kPink-9, ROOT.kCyan+3]
                colors=colors*3

                # outFolder=(baseOutputFolder+"/EvolutionPlots/").replace("Plots/","Plots"+ev_name.replace("FitStudies","")+"/")
                outFolder=(baseOutputFolder+"/RateParamEvolutionPlots/").replace("Plots/","_"+ev_nameOut.replace("FitStudies","")+"/")

                can.Clear()
                # leg = ROOT.TLegend(0.37,0.76,0.98,0.935)
                leg = ROOT.TLegend(0.37,0.76,0.96,0.935)
                leg.SetNColumns(2)
                leg.SetTextSize(0.02)

                line1 = ROOT.TLine(1,0.,1,1010.)
                line1.SetLineColor(ROOT.kBlack)
                line1.SetLineStyle(ROOT.kDotted)
                line2 = ROOT.TLine(-1,0.,-1,1010.)
                line2.SetLineColor(ROOT.kBlack)
                line2.SetLineStyle(ROOT.kDotted)
                line3 = ROOT.TLine(0.,0.,0.,1010.)
                line3.SetLineColor(ROOT.kBlack)
                line3.SetLineStyle(ROOT.kDotted)
                line4 = ROOT.TLine(-2.,0.,-2.,1010.)
                line4.SetLineColor(ROOT.kBlack)
                line4.SetLineStyle(ROOT.kDotted)


                i = 0
                for graph in graphs:
                    graph.SetMarkerColor(colors[i])
                    graph.SetLineColor(colors[i])
                    # if i%2==0:
                    #     graph.SetMarkerColor(colors[i/2])
                    #     graph.SetLineColor(colors[i/2])
                    # else:
                    #     graph.SetMarkerColor(colors[int((i-1)/2.)])
                    #     graph.SetLineColor(colors[int((i-1)/2.)])
                    #     # graph.SetLineStyle(ROOT.kDashed)

                    graph.GetXaxis().SetRangeUser(-1.,3.)
                    graph.GetXaxis().SetLimits(-1.,3.)
                    graph.GetYaxis().SetRangeUser(0,1300)
                    graph.GetYaxis().SetLimits(0,1300)
                    graph.GetYaxis().SetTickLength(0.)
                    graph.GetYaxis().SetLabelSize(0.)
                    graph.GetXaxis().SetTickLength(0.)
                    graph.GetXaxis().SetTitle("rateParam")
                    graph.SetLineWidth(2)
                    graph.SetMarkerStyle(8)
                    leg.AddEntry(graph, names[i],"lep")

                    if i==0:
                        graph.GetXaxis().SetRangeUser(-1.,3.)
                        graph.GetXaxis().SetLimits(-1.,3.)
                        graph.Draw("AP")
                        graph.GetXaxis().SetRangeUser(-1.,3.)
                        graph.GetXaxis().SetLimits(-1.,3.)
                        graph.GetXaxis().SetTitle("rateParam")
                        graph.Draw("AP")
                        can.Update()
                        line1.Draw("same")
                        line2.Draw("same")
                        line3.Draw("same")
                    elif graph.GetN()>0:
                        graph.GetXaxis().SetRangeUser(-1.,3.)
                        graph.GetXaxis().SetLimits(-1.,3.)
                        graph.GetXaxis().SetTitle("rateParam")
                        graph.Draw("Psame")
                        can.Update()
                    i = i+1

                ROOT.gPad.RedrawAxis()

                labels=[]
                can.Update()

                for yC ,n in coordinates:
                    t = ROOT.TText(-3.2,yC,n)
                    t.SetTextSize(0.021)
                    t.Draw("same")
                    labels.append(t)

                if not os.path.exists(outFolder):
                    os.makedirs(outFolder)

                info = ""
                l = aux.LabelEvolution(info="#scale[0.7]{%s}" % info, sim=False, year="",status="Preliminary")

                leg.Draw("same")
                saveName = "RateParamEvolutionPlot_"+str(isub)
                aux.save(saveName, folder=outFolder, normal=True, log=False)

        #####################################################################
        ######################## plotGOF
        #####################################################################
        # if doGoodnessOfFitPlots:
        if doGoodnessOfFitPlots and "obs" in ev_nameOut:
            # for type in ["","_KS","_AD"]:
            # for type in ["_AD"]:
            for type in [""]:
                filenames =[]
                filenames_ = [
                    # basePath+e+"/GoodnessOfFit/TOREPLACE1/higgsCombine_"+e.replace(ev_name,"").replace("/","")+".GoodnessOfFit_TOREPLACE2_nominal_obs_data.GoodnessOfFit.mH125.root" for e in extNames
                    basePath+e+"/GoodnessOfFit/TOREPLACE1/higgsCombine_"+e.replace(ev_name,"").replace("/","")+"_TOREPLACE2.GoodnessOfFit.mH125.38.root" for e in extNames
                ]
                filenames = []
                for f_ in filenames_:
                    filenames.append(f_)
                # names = [x.split("/")[1]+"_"+x.split("/")[2] for x in extNames]
                names = [x.split("/")[1] for x in extNames]
                for fname,n in zip(filenames, names):
                    # data = fname.replace("TOREPLACE","Data")
                    # toys = fname.replace("TOREPLACE","Toys").replace(".mH125.root",".mH125.100.root")
                    data = fname.replace("TOREPLACE1","Data"+type)
                    # toys = fname.replace("TOREPLACE1","Toys"+type).replace(".mH125.38.root",".mH125.38.101.root")
                    toys = fname.replace("TOREPLACE1","Toys"+type).replace(".mH125.38.root",".mH125.38*.root")
                    data = data.replace("_TOREPLACE2","")
                    # toys = toys.replace("_TOREPLACE2","").replace(".mH125.38.root",".mH125.38.101   .root")
                    toys = toys.replace("_TOREPLACE2","").replace(".mH125.38.root",".mH125.38*.root")
                    # print (toys,data)
                    # toys = toys.replace("/GoodnessOfFit_Toys/","/GoodnessOfFit_Toys/CloneWithLess/")
                    # print toys,data

                    alltoys = glob.glob(toys)
                    anyexists = [os.path.exists(t) for t in alltoys]
                    anyexists = sum(anyexists)
                    # print (anyexists)

                    # if os.path.exists(data) and os.path.exists(toys):
                    if os.path.exists(data) and anyexists > 0:
                        # outputFolder = outFolder=(baseOutputFolder+"/GoF_Plots"+type+"/").replace("Plots/",""+ev_name.replace("EvolutionStudies","")+"/")+n+"/"
                        outputFolder = outFolder=(baseOutputFolder+"/GoF_Plots"+type+"/").replace("Plots/",""+ev_nameOut.replace("EvolutionStudies","")+"/")+n+"/"
                        # print (fname,n)
                        channel = n.split("_")[1]
                        year = n.split("_")[3]
                        leftText = convertChannel(channel)
                        rightText = getRighttext(year)
                        plotGOF(data, toys, outputFolder, txtTL=leftText, txtTR=rightText)
                    elif os.path.exists(data):
                        print (toys, "does not exist")
                    elif os.path.exists(toys):
                        print (data, "does not exist")

            for type in [""]:
                filenames =[]
                filenames_ = [
                    basePath+e+"/GoodnessOfFitFixedSignal/TOREPLACE1/higgsCombine_"+e.replace(ev_name,"").replace("/","")+"_TOREPLACE2.GoodnessOfFit.mH125.38.root" for e in extNames
                ]
                filenames = []
                for f_ in filenames_:
                    filenames.append(f_)
                names = [x.split("/")[1] for x in extNames]
                for fname,n in zip(filenames, names):
                    data = fname.replace("TOREPLACE1","Data"+type)
                    toys = fname.replace("TOREPLACE1","Toys"+type).replace(".mH125.38.root",".mH125.38*.root")
                    data = data.replace("_TOREPLACE2","")
                    toys = toys.replace("_TOREPLACE2","").replace(".mH125.38.root",".mH125.38*.root")

                    alltoys = glob.glob(toys)
                    anyexists = [os.path.exists(t) for t in alltoys]
                    anyexists = sum(anyexists)

                    if os.path.exists(data) and anyexists > 0:
                        outputFolder = outFolder=(baseOutputFolder+"/GoF_fixedSignal_Plots"+type+"/").replace("Plots/",""+ev_nameOut.replace("EvolutionStudies","")+"/")+n+"/"
                        channel = n.split("_")[1]
                        year = n.split("_")[3]
                        leftText = convertChannel(channel)
                        rightText = getRighttext(year)
                        plotGOF(data, toys, outputFolder, txtTL=leftText, txtTR=rightText)
                    elif os.path.exists(data):
                        print (toys, "does not exist")
                    elif os.path.exists(toys):
                        print (data, "does not exist")

        #####################################################################
        ######################## prePostFit Plots
        #####################################################################
        if doPrePostFitPlots:
            filenames =[]
            if "obs" in ev_nameOut:
                filenames_ = [
                    basePath+e+"/FitObserved/" for e in extNames
                ]
            else:
                filenames_ = [
                    basePath+e+"/FitExpected/" for e in extNames
                ]
            filenames = []
            for f_ in filenames_:
                filenames.append(f_)
            names = [x.split("/")[1]+"_"+x.split("/")[2] for x in extNames]

            allCommands = []
            allOutfiles = []
            allOutfilesCopy = []

            for fname,n in zip(filenames, names):
                baseCommandFolder = os.getcwd()
                inpath = fname
                # print (fname,n)
                if "obs" in ev_nameOut:
                    fitresult = inpath+"/multidimfit_nominal_obs_fit.root"
                    blinded = False
                else:
                    fitresult = inpath+"/multidimfit_nominal_exp_fit.root"
                    blinded = True
                # datacardPath = inpath+"/datacard_FR2_ll.txt".replace("FR2_ll",n)
                datacardPath = inpath.split("/")[10].replace("FitStudies_","").replace("_VR","").replace("_SR","").replace("_CR","")+"/datacards/Vcb_SL_2024.txt".replace("FR2_ll",n.replace("workspace","")).replace("_.",".")
                # workspacePath = inpath+"/workspace_FR2_ll.root".replace("FR2_ll",n)
                workspacePath = datacardPath.replace("Vcb","workspace_Vcb").replace(".txt","_classic.root")
                # shapeRootOutputFolder = inpath+"/Shapes/"
                shapeRootOutputFolder = baseOutputFolderLocal + "/htc_prepost_"+ev_nameOut+"/Shapes/"
                shapeRootOutputFolderCopy = inpath+"/Shapes/"
                # PlotOutputFolder = (baseOutputFolder+"/PrePostFit_Plots/").replace("Plots/","Plots"+ev_name.replace("EvolutionStudies","")+"/")+n+"/"
                print (n, ev_nameOut)
                # PlotOutputFolder = (baseOutputFolder+"/PrePostFit_Plots/").replace("Plots/","Plots"+ev_nameOut.replace("EvolutionStudies","")+"/")+n.replace("workspace_","")+"/"
                PlotOutputFolder = (baseOutputFolder+"/PrePostFitPlots/").replace("Plots/","Plots"+ev_nameOut+"/")+n.replace("workspace_","")+"/"
                PlotOutputFolder = PlotOutputFolder.replace("_/","/")
                print (PlotOutputFolder)
                # shapeRootOutputFile = "PrePostShapes.root"
                shapeRootOutputFile = ("PrePostShapes"+n.replace("workspace","")+".root").replace("_.root",".root")

                print (fitresult, datacardPath, workspacePath)

                if os.path.exists(fitresult) and os.path.exists(datacardPath) and os.path.exists(workspacePath):

                    if not os.path.exists(shapeRootOutputFolder+shapeRootOutputFile) or doCondor:
                        # outCommand = producePrePostFitFromCombineHarvester(datacardPath, workspacePath, shapeRootOutputFolder, shapeRootOutputFile, fitresult, fitName="fit_mdf",nSamples="5000", testOnly = doCondor)
                        outCommand = producePrePostFitFromCombineHarvester(baseCommandFolder+"/"+datacardPath, baseCommandFolder+"/"+workspacePath, shapeRootOutputFolder, shapeRootOutputFile, fitresult, fitName="fit_mdf",nSamples="3000", testOnly = doCondor)
                        allCommands.append(outCommand)
                        allOutfiles.append(shapeRootOutputFolder)
                        allOutfilesCopy.append(shapeRootOutputFolderCopy)

                    if not doCondor:
                        years= []
                        channels= []
                        if "FR2" in n:
                            years = ["2015","2016","2017","2018","2024"]
                            if "MergedYears" in PlotOutputFolder:
                                years = ["FR2"]
                        elif "2015" in n:
                            years.append("2015")
                        elif "2016" in n:
                            years.append("2016")
                        elif "2017" in n:
                            years.append("2017")
                        elif "2018" in n:
                            years.append("2018")
                        elif "2024" in n:
                            years.append("2024")
                        if "ALL" in n:
                            channels = ["FH","SL","DL"]
                        elif "SL" in n:
                            channels.append("SL")
                        elif "FH" in n:
                            channels.append("FH")
                        elif "DL" in n:
                            channels.append("DL")

                        from analysis.makeDatacards_CH import (
                            datacard_dict_DL, datacard_dict_FH,
                            datacard_dict_merged, datacard_dict_SL)

                        sortedCatListSR = [
                            "catLF_SR", "catBJ_SR", "catBB_SR", "catCJ_SR", "catCC_SR",
                            "catZbb_SR", "catZcc_SR", "catHbb_SR", "catHcc_SR"
                        ]
                        sortedCatListVR = [
                            "catLF_MidScoreVR", "catBJ_MidScoreVR", "catBB_MidScoreVR", "catCJ_MidScoreVR", "catCC_MidScoreVR",
                            "catZbb_MidScoreVR", "catZcc_MidScoreVR", "catHbb_MidScoreVR", "catHcc_MidScoreVR"
                        ]
                        sortedCatListCR = [
                            "catLF_SR", "catBJ_SR", "catBB_SR", "catCJ_SR", "catCC_SR",
                        ]
                        sortedCatListCRPlusTTZ = [
                            "catLF_SR", "catBJ_SR", "catBB_SR", "catCJ_SR", "catCC_SR",
                            "catZbb_SR", "catZcc_SR",
                        ]
                        sortedCatListCRPlusTTH = [
                            "catLF_SR", "catBJ_SR", "catBB_SR", "catCJ_SR", "catCC_SR",
                            "catHbb_SR", "catHcc_SR",
                        ]
                        if "VR" in ev_nameOut:
                            sortedCatList = sortedCatListVR
                        elif "SR" in ev_nameOut:
                            sortedCatList = sortedCatListSR
                        elif "CRPlusTTZ" in ev_nameOut:
                            sortedCatList = sortedCatListCRPlusTTZ
                        elif "CRPlusTTH" in ev_nameOut:
                            sortedCatList = sortedCatListCRPlusTTH
                        elif "CR" in ev_nameOut:
                            sortedCatList = sortedCatListCR
                        for year in years:
                        # # #     # plotInputValPostFitPlots(shapeRootOutputFolder+shapeRootOutputFile, year, PlotOutputFolder, xLabel="", prepostfit="prefit", blinded=False, plotLines=False)
                        # # #     # plotInputValPostFitPlots(shapeRootOutputFolder+shapeRootOutputFile, year, PlotOutputFolder, xLabel="", prepostfit="postfit", blinded=False, plotLines=False)
                            for channel in channels:
                                for cat in sortedCatList[-1::-1]:
                                    plotPostFitPlots(shapeRootOutputFolder+shapeRootOutputFile, year, channel, cat, PlotOutputFolder+"/Individual_"+channel+"_"+cat+"/", xLabel="", prepostfit="prefit", blinded=blinded)
                                    plotPostFitPlots(shapeRootOutputFolder+shapeRootOutputFile, year, channel, cat, PlotOutputFolder+"/Individual_"+channel+"_"+cat+"/", xLabel="", prepostfit="postfit", blinded=blinded)

                            plotMergedPostFitPlots(shapeRootOutputFolder+shapeRootOutputFile, year, channels, sortedCatList, PlotOutputFolder, xLabel="", prepostfit="prefit", blinded=blinded, singleYearFit = len(years)==1, plotLines=True)
                            plotMergedPostFitPlots(shapeRootOutputFolder+shapeRootOutputFile, year, channels, sortedCatList, PlotOutputFolder, xLabel="", prepostfit="postfit", blinded=blinded, singleYearFit = len(years)==1, plotLines=True)

            if doCondor:
                # print (len(allCommands))
                # outCondorFolder = baseOutputFolder + "/htc_prepost_"+ev_nameOut+"/"
                outCondorFolder = baseOutputFolderLocal + "/htc_prepost_"+ev_nameOut+"/"
                if not os.path.exists(outCondorFolder):
                    os.makedirs(outCondorFolder)

                subLines = [
                    "executable = condor_combine_task.sh",
                    "arguments = $(ProcId)",
                    "output = prepost_task.$(ClusterId).$(ProcId).out",
                    "error  = prepost_task.$(ClusterId).$(ProcId).err",
                    "log    = prepost_task.$(ClusterId).log",
                    "on_exit_hold = (ExitBySignal == True) || (ExitCode != 0)",
                    "periodic_release =  (NumJobStarts < 3) && ((CurrentTime - EnteredCurrentStatus) > 600)",
                    'getenv = true',
                    '+JobFlavour="testmatch"',
                    'RequestCpus = 3',
                    '+AccountingGroup = "group_u_CMST3.all"',
                    'queue '+str(len(allCommands))
                ]

                out_file_sub = open(outCondorFolder+'/condor_combine_task.sub', 'w')
                for _tmp in subLines:
                    out_file_sub.write(_tmp+'\n')
                out_file_sub.close()

                sh_lines = [
                    '#!/bin/sh',
                    'ulimit -s unlimited',
                    'set -e',
                    'cd '+os.environ['CMSSW_BASE']+'/src/',
                    'export '+os.environ['SCRAM_ARCH'],
                    'source /cvmfs/cms.cern.ch/cmsset_default.sh',
                    'eval `scramv1 runtime -sh`',
                    # 'cd '+baseCommandFolder+'/'+outCondorFolder,
                    'cd '+outCondorFolder,
                    '',
                ]

                for i_command, command_ in enumerate(allCommands):
                    sh_lines.append('if [ $1 -eq '+str(i_command)+' ]; then')
                    sh_lines.append('    '+command_)
                    # sh_lines.append('    '+'mkdir -p '+allOutfilesCopy[i_command])
                    # sh_lines.append('    '+'mv '+allOutfiles[i_command]+'/'+shapeRootOutputFile+' '+allOutfilesCopy[i_command]+"/")
                    # sh_lines.append('    '+'ln -s '+allOutfilesCopy[i_command]+'/'+shapeRootOutputFile+' '+allOutfiles[i_command]+'/'+shapeRootOutputFile)
                    sh_lines.append('fi')

                out_file_sub = open(outCondorFolder+'/condor_combine_task.sh', 'w')
                for _tmp in sh_lines:
                    out_file_sub.write(_tmp+'\n')
                out_file_sub.close()

                

        #####################################################################
        ######################## copy Impact Plots
        #####################################################################
        if doImpactPlots:
            print ("Making impact plots for",ev_name)
            filenames =[]
            if "obs" in ev_nameOut:
                if (unblind and "SR" in ev_nameOut) or not "SR" in ev_nameOut:
                    filenames_ = [
                        basePath+e+"/ImpactsObserved/" for e in extNames
                    ]
            else:
                filenames_ = [
                    basePath+e+"/ImpactsExpected/" for e in extNames
                ]
            # print filenames_
            filenames = []
            for f_ in filenames_:
                filenames.append(f_)
            names = [x.split("/")[1]+"_"+x.split("/")[2] for x in extNames]
            # print names
            for fname,n in zip(filenames, names):
                print (fname)
                # outPathName = (baseOutputFolder+"/ImpactPlots/").replace("Plots/","Plots"+ev_name.replace("FitStudies","")+"/")+n+"/"
                outPathName = (baseOutputFolder+"/ImpactPlots/").replace("Plots/","Plots_"+ev_nameOut.replace("FitStudies","")+"/")+n+"/"
                outPathName = outPathName.replace("_/","/").replace("workspace_","")
                # import glob
                print (outPathName)
                command = "cp "+fname+"/*.pdf "+outPathName+"/"
                if len(glob.glob(fname+"/*.pdf"))>0:
                    if not os.path.exists(outPathName):
                        os.makedirs(outPathName)
                    EXE(command)

        #####################################################################
        ######################## nuisance correlations
        #####################################################################
        if doCorrelations:
            for extName in extNames:
                n_ = extName.replace(ev_name,"")
                # print (n_)
                print ("Making correlation plots for",ev_name)
                if "obs" in ev_nameOut:
                    fitDiaPathAll = basePath+ev_name+"/"+n_+"/FitDiagnosticsObserved/fitDiagnostics_nominal_obs_FitDiagnostics.root"
                else:
                    fitDiaPathAll = basePath+ev_name+"/"+n_+"/FitDiagnosticsExpected/fitDiagnostics_nominal_exp_FitDiagnostics.root"
                # outPlotFolderName = baseOutputFolder+"CorrelationStudies_"+ev_nameOut.replace("FitStudies_","")+"/"
                outPlotFolderName = baseOutputFolder+"Correlation_"+ev_nameOut.replace("FitStudies_","")+"/"+n_+"/"

                print (fitDiaPathAll, outPlotFolderName)


                if os.path.exists(fitDiaPathAll) and os.path.getsize(fitDiaPathAll) > 10:
                    command = "python3 plotting/plotFitDiagnostics_evolutions.py"
                    command += " -i "+fitDiaPathAll
                    command += " -o "+outPlotFolderName
                    # command += " -p SF_norm_tt_lf"
                    command += " -p rate_ttZbb"
                    # import glob
                    if len(glob.glob(fitDiaPathAll))>0:
                        EXE(command)

        #####################################################################
        ######################## bias tests
        #####################################################################
        if doBiasTestPlots and "obs" in ev_nameOut and "SR" in ev_nameOut:
            for type in [""]:
                filenames =[]
                filenames_ = [
                    basePath+e+"/FrequentistToys/higgsCombine_nominal_FrequentistToys.MultiDimFit.mH125.38.*.root" for e in extNames
                ]
                filenames = []
                for f_ in filenames_:
                    filenames.append(f_)
                names = [x.split("/")[1] for x in extNames]
                for fname,n in zip(filenames, names):
                    toys = fname

                    alltoys = glob.glob(toys)
                    anyexists = [os.path.exists(t) for t in alltoys]
                    anyexists = sum(anyexists)
                    if anyexists > 0:
                        outputFolder = outFolder=(baseOutputFolder+"/Bias_Plots"+type+"/").replace("Plots/",""+ev_nameOut.replace("EvolutionStudies","")+"/")+n+"/"
                        channel = n.split("_")[1]
                        year = n.split("_")[3]
                        leftText = convertChannel(channel)
                        POIs = ["r"]
                        rightText = getRighttext(year)
                        for POI in POIs:
                            plotBias(toys, outputFolder, POI, txtTL=leftText, txtTR=rightText)
                            plotBias(toys, outputFolder, POI, txtTL=leftText, txtTR=rightText, injectedSignal = 1.0, doBias = True)
                    else:
                        print ("doBiasTestPlots: Toy file", toys, "does not exist!")

if __name__ == "__main__":
    ### args
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('--gof', dest='dogof', action='store_true', default=False,
                        help='do goodness of fit plots')
    parser.add_argument('--impacts', dest='doimpacts', action='store_true', default=False,
                        help='do impact plots')
    parser.add_argument('--evolution', dest='doevolution', action='store_true', default=False,
                        help='do nuisance evolution plots')
    parser.add_argument('--prepostfit', dest='doprepostfit', action='store_true', default=False,
                        help='do nuisance evolution plots')
    parser.add_argument('--condor', dest='docondor', action='store_true', default=False,
                        help='do nuisance evolution plots')
    parser.add_argument('--correlations', dest='docorrelations', action='store_true', default=False,
                        help='do nuisance evolution plots')
    parser.add_argument('--bias', dest='dobias', action='store_true', default=False,
                        help='do bias test plots')

    import sys
    if len(sys.argv)==1:
        print ("ERROR: Not enough arguments provided!")
        parser.print_help()
        parser.exit()

    opts, opts_unknown = parser.parse_known_args()

    dogof   = opts.dogof
    doimpacts   = opts.doimpacts
    doevolution   = opts.doevolution
    doprepostfit   = opts.doprepostfit
    docondor   = opts.docondor
    docorrelations   = opts.docorrelations
    dobias   = opts.dobias

    main(doPrePostFitPlots = doprepostfit, doEvolutionPlots = doevolution, doImpactPlots = doimpacts, doGoodnessOfFitPlots = dogof, doCorrelations = docorrelations, doBiasTestPlots = dobias, doCondor = docondor)
