#!/usr/bin/env python
import gc
import json
import os

import ROOT
from auxiliary import *
# from datasets import *
# from ROOT import *

gc.enable()

listOfModelingUnc = [
    "CMS_LHE_weights_scale_muF_ttbb",
    "CMS_LHE_weights_scale_muF_ttbbdps",
    "CMS_LHE_weights_scale_muF_tt2b",
    "CMS_LHE_weights_scale_muF_ttbj",
    "CMS_LHE_weights_scale_muF_ttbjdps",
    "CMS_LHE_weights_scale_muF_tt2c",
    "CMS_LHE_weights_scale_muF_ttcj",
    "CMS_LHE_weights_scale_muF_ttlf",

    "CMS_LHE_weights_scale_muR_ttbb",
    "CMS_LHE_weights_scale_muR_ttbbdps",
    "CMS_LHE_weights_scale_muR_tt2b",
    "CMS_LHE_weights_scale_muR_ttbj",
    "CMS_LHE_weights_scale_muR_ttbjdps",
    "CMS_LHE_weights_scale_muR_tt2c",
    "CMS_LHE_weights_scale_muR_ttcj",
    "CMS_LHE_weights_scale_muR_ttlf",

    "CMS_PS_fsr_ttbb",
    "CMS_PS_fsr_ttbbdps",
    "CMS_PS_fsr_tt2b",
    "CMS_PS_fsr_ttbj",
    "CMS_PS_fsr_ttbjdps",
    "CMS_PS_fsr_ttcc",
    "CMS_PS_fsr_tt2c",
    "CMS_PS_fsr_ttcj",
    "CMS_PS_fsr_ttlf",

    "CMS_PS_psr_ttbb",
    "CMS_PS_psr_ttbbdps",
    "CMS_PS_psr_tt2b",
    "CMS_PS_psr_ttbj",
    "CMS_PS_psr_ttbjdps",
    "CMS_PS_psr_ttcc",
    "CMS_PS_psr_tt2c",
    "CMS_PS_psr_ttcj",
    "CMS_PS_psr_ttlf",

    "CMS_ttHcc_HDAMPML_ttcc",
    "CMS_ttHcc_HDAMPML_tt2c",
    "CMS_ttHcc_HDAMPML_ttcj",
    "CMS_ttHcc_HDAMPML_ttlf",

    "PDF_TTBB_MERGED",
    
    "FIVEFS",
    "FIVEFS_TTBB",
    "FIVEFS_TTBJ",
    "FIVEFS_TT2B",

    "FOURFS",
    "FOURFS_TTBB",
    "FOURFS_TTBJ",
    "FOURFS_TT2B",
    
    "FIVEFS2MU",
    "FIVEFS2MU_TTBB",
    "FIVEFS2MU_TTBJ",
    "FIVEFS2MU_TT2B",

    "AMCATNLOFXFX",
    "AMCATNLOFXFX_TTBB",
    "AMCATNLOFXFX_TTBJ",
    "AMCATNLOFXFX_TT2B",
    "AMCATNLOFXFX_TTCC",
    "AMCATNLOFXFX_TTCJ",
    "AMCATNLOFXFX_TT2C",
    "AMCATNLOFXFX_TTLF",

    "HERWIG",
    "HERWIG_TTBB",
    "HERWIG_TTBJ",
    "HERWIG_TT2B",
    "HERWIG_TTCC",
    "HERWIG_TTCJ",
    "HERWIG_TT2C",
    "HERWIG_TTLF",
]

def CreateFakeHistoFromData(h_, newName):
    for binX in range(1, h_.GetNbinsX()+1):
        h_.SetBinContent(binX, 0.000001)
        h_.SetBinError(binX, 0.000001)
    h_.SetBinContent(0, 0.)
    h_.SetBinError(0, 0.)
    h_.SetBinContent(h_.GetNbinsX()+1, 0.)
    h_.SetBinError(h_.GetNbinsX()+1, 0.)
    h_.SetName(newName)
    return h_

def convertLepChannel(proc):
    proc = proc.replace("emu","DLem")
    proc = proc.replace("ee","DLee")
    proc = proc.replace("mumu","DLmm")
    proc = proc.replace("dilepton","DL")
    proc = proc.replace("se","SLe")
    proc = proc.replace("smu","SLm")
    proc = proc.replace("slep","SL")
    proc = proc.replace("fhad","FH")
    return proc

def getCombineChannelName(hPath, year= None, channel = None):
    isFullPath = len(hPath.split("/")) > 1
    if isFullPath:
        year_ = hPath.split("/")[0]
        lepChannel_ = convertLepChannel(hPath.split("/")[1])
        hName_ =  hPath.split("/")[3]
        outName = "ttHcc_"+year_+"_"+lepChannel_+"_"
    else:
        outName = "ttHcc_"+year+"_"+channel+"_"
        hName_ = hPath

    

    # SL
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_GreaterThreeJet_TTBBCategoryMidScore", "catBB_MidScoreVR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_GreaterThreeJet_TTBJCategoryMidScore", "catBJ_MidScoreVR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_GreaterThreeJet_TTCCCategoryMidScore", "catCC_MidScoreVR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_GreaterThreeJet_TTCJCategoryMidScore", "catCJ_MidScoreVR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_GreaterThreeJet_TTLFCategoryMidScore", "catLF_MidScoreVR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_GreaterThreeJet_TTHbbCategoryMidScore", "catHbb_MidScoreVR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_GreaterThreeJet_TTHccCategoryMidScore", "catHcc_MidScoreVR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_GreaterThreeJet_TTZbbCategoryMidScore", "catZbb_MidScoreVR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_GreaterThreeJet_TTZccCategoryMidScore", "catZcc_MidScoreVR")

    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_ThreeJet_TTBBCategoryLowNJet", "catBB_LowNJetVR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_ThreeJet_TTBJCategoryLowNJet", "catBJ_LowNJetVR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_ThreeJet_TTCCCategoryLowNJet", "catCC_LowNJetVR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_ThreeJet_TTCJCategoryLowNJet", "catCJ_LowNJetVR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_ThreeJet_TTLFCategoryLowNJet", "catLF_LowNJetVR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_ThreeJet_TTHbbCategoryLowNJet", "catHbb_LowNJetVR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_ThreeJet_TTHccCategoryLowNJet", "catHcc_LowNJetVR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_ThreeJet_TTZbbCategoryLowNJet", "catZbb_LowNJetVR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_ThreeJet_TTZccCategoryLowNJet", "catZcc_LowNJetVR")

    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_GreaterThreeJet_TTBBCategory", "catBB_SR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_GreaterThreeJet_TTBJCategory", "catBJ_SR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_GreaterThreeJet_TTCCCategory", "catCC_SR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_GreaterThreeJet_TTCJCategory", "catCJ_SR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_GreaterThreeJet_TTLFCategory", "catLF_SR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_GreaterThreeJet_TTHbbCategory", "catHbb_SR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_GreaterThreeJet_TTHccCategory", "catHcc_SR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_GreaterThreeJet_TTZbbCategory", "catZbb_SR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_GreaterThreeJet_TTZccCategory", "catZcc_SR")

    # DL
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_GreaterFourJet_TTBBCategoryMidScore", "catBB_MidScoreVR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_GreaterFourJet_TTBJCategoryMidScore", "catBJ_MidScoreVR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_GreaterFourJet_TTCCCategoryMidScore", "catCC_MidScoreVR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_GreaterFourJet_TTCJCategoryMidScore", "catCJ_MidScoreVR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_GreaterFourJet_TTLFCategoryMidScore", "catLF_MidScoreVR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_GreaterFourJet_TTHbbCategoryMidScore", "catHbb_MidScoreVR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_GreaterFourJet_TTHccCategoryMidScore", "catHcc_MidScoreVR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_GreaterFourJet_TTZbbCategoryMidScore", "catZbb_MidScoreVR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_GreaterFourJet_TTZccCategoryMidScore", "catZcc_MidScoreVR")

    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_FourJet_TTBBCategoryLowNJet", "catBB_LowNJetVR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_FourJet_TTBJCategoryLowNJet", "catBJ_LowNJetVR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_FourJet_TTCCCategoryLowNJet", "catCC_LowNJetVR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_FourJet_TTCJCategoryLowNJet", "catCJ_LowNJetVR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_FourJet_TTLFCategoryLowNJet", "catLF_LowNJetVR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_FourJet_TTHbbCategoryLowNJet", "catHbb_LowNJetVR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_FourJet_TTHccCategoryLowNJet", "catHcc_LowNJetVR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_FourJet_TTZbbCategoryLowNJet", "catZbb_LowNJetVR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_FourJet_TTZccCategoryLowNJet", "catZcc_LowNJetVR")

    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_GreaterFourJet_TTBBCategory", "catBB_SR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_GreaterFourJet_TTBJCategory", "catBJ_SR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_GreaterFourJet_TTCCCategory", "catCC_SR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_GreaterFourJet_TTCJCategory", "catCJ_SR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_GreaterFourJet_TTLFCategory", "catLF_SR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_GreaterFourJet_TTHbbCategory", "catHbb_SR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_GreaterFourJet_TTHccCategory", "catHcc_SR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_GreaterFourJet_TTZbbCategory", "catZbb_SR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_GreaterFourJet_TTZccCategory", "catZcc_SR")

    # FH
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_GreaterSixJet_TTBBCategoryMidScore", "catBB_MidScoreVR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_GreaterSixJet_TTBJCategoryMidScore", "catBJ_MidScoreVR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_GreaterSixJet_TTCCCategoryMidScore", "catCC_MidScoreVR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_GreaterSixJet_TTCJCategoryMidScore", "catCJ_MidScoreVR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_GreaterSixJet_TTLFCategoryMidScore", "catLF_MidScoreVR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_GreaterSixJet_TTHbbCategoryMidScore", "catHbb_MidScoreVR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_GreaterSixJet_TTHccCategoryMidScore", "catHcc_MidScoreVR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_GreaterSixJet_TTZbbCategoryMidScore", "catZbb_MidScoreVR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_GreaterSixJet_TTZccCategoryMidScore", "catZcc_MidScoreVR")

    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_SixJet_TTBBCategoryLowNJet", "catBB_LowNJetVR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_SixJet_TTBJCategoryLowNJet", "catBJ_LowNJetVR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_SixJet_TTCCCategoryLowNJet", "catCC_LowNJetVR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_SixJet_TTCJCategoryLowNJet", "catCJ_LowNJetVR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_SixJet_TTLFCategoryLowNJet", "catLF_LowNJetVR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_SixJet_TTHbbCategoryLowNJet", "catHbb_LowNJetVR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_SixJet_TTHccCategoryLowNJet", "catHcc_LowNJetVR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_SixJet_TTZbbCategoryLowNJet", "catZbb_LowNJetVR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_SixJet_TTZccCategoryLowNJet", "catZcc_LowNJetVR")

    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_GreaterSixJet_TTBBCategory", "catBB_SR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_GreaterSixJet_TTBJCategory", "catBJ_SR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_GreaterSixJet_TTCCCategory", "catCC_SR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_GreaterSixJet_TTCJCategory", "catCJ_SR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_GreaterSixJet_TTLFCategory", "catLF_SR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_GreaterSixJet_TTHbbCategory", "catHbb_SR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_GreaterSixJet_TTHccCategory", "catHcc_SR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_GreaterSixJet_TTZbbCategory", "catZbb_SR")
    hName_ = hName_.replace("GreaterTwoMediumBCTagGreaterZeroMediumBTag_GreaterSixJet_TTZccCategory", "catZcc_SR")

    hName_ = hName_.split("_")[0]+"_"+hName_.split("_")[1]

    outName = outName + hName_

    return outName

def addHistosTogether(histoList):
    nBins = []
    for h in histoList:
        nBins.append(h.GetNbinsX())
    nTotalBins = sum(nBins)
    iTot = 1
    rn = aux.randomName()
    hOut = TH1D(rn, rn, nTotalBins, 0, nTotalBins)
    for h in histoList:
        for binX in range(1, h.GetNbinsX()+1):
            hOut.SetBinContent(iTot, h.GetBinContent(binX))
            hOut.SetBinError(iTot, h.GetBinError(binX))
            iTot = iTot +1
    return hOut

def modifyDatacardDict(datacard_dict, years, channels, newBinning = False):
    datacard_dict_ = datacard_dict.copy()
    for year in years:
        # filename = pathPlotting.replace("YEAR",year).replace("SYSTEMATIC", "Nominal")
        # fIn = ROOT.TFile(filename,"READ")
        for channel in channels:
            for key in datacard_dict_:
                # print (year+"_"+channel+"_"+key+"_",datacard_dict_[key]["distribution"])
                category = key
                observable_ = datacard_dict_[key]["distribution"]
                if not (observable_ == "NEvents"):
                    binAr = aux.loadBinningFromFile(year+"_"+channel+"_"+category+"_"+observable_, filepath = binningFilePath)
                    # print (binAr)
                    if len(binAr)==2:
                        observable_ = "NEvents"
                    else:
                        # print (year+"_"+channel+"_"+category+"_"+observable_,datacard_dict_[key]["distribution"])
                        observable_ = datacard_dict_[key]["distribution"]
                    datacard_dict_[key]["distribution"] = observable_

    return datacard_dict_.copy()

def createCombinedShapeFile(years, channels, datacard_dict_, inShapeFile, outFilePath, categoryList, applyShapeSystematics=False, addShapeNuisances = None, addPDF=True, addModels = False):
    # if not os.path.exists(outFolder):
    #     os.makedirs(outFolder, exist_ok=True)
    print ("-"*50)
    print ("Creating Combined Shape file")
    print (years, channels)
    print ("from infile:",inShapeFile)
    print ("to outpath:",inShapeFile.replace(".root","Unrolled.root"))
    print ("with Systematics:",applyShapeSystematics)
    print ("with addPDF:",addPDF)
    print( "with addShapeNuisances:",addShapeNuisances)
    print ("with categoryList:",categoryList)
    inRootFile_ = TFile(inShapeFile, "READ")
    outRootFile_ = TFile(inShapeFile.replace(".root","Unrolled.root"),"RECREATE")
    outRootFile_.cd()
    for year in years:
        print ("--year",year,"\t",years.index(year)+1,"out of",len(years))
        histosToAppendPerProc = {}
        for proc in procs:
            histosToAppendPerProc[proc]=[]
            for channel in channels:
                for category in categoryList:
                    # print (category,datacard_dict_[category]["distribution"])
                    observable = datacard_dict_[category]["distribution"]
                    hIn = inRootFile_.Get(year+"_"+channel+"_"+category+"_"+observable+"_"+proc)
                    # hIn = hIn.Clone()
                    # hIn.SetDirectory(0)
                    histosToAppendPerProc[proc].append(hIn)
        for proc in procs:
            h = addHistosTogether(histosToAppendPerProc[proc])
            # h.SetDirectory(0)
            h.Write(year+"_"+proc)
        # del histosToAppendPerProc
        #gc.collect()
        #data
        histosToAppendData=[]
        for channel in channels:
            for category in categoryList:
                observable = datacard_dict_[category]["distribution"]
                hData = inRootFile_.Get(year+"_"+channel+"_"+category+"_"+observable+"_"+"data_obs")
                # hData = hData.Clone()
                # hData.SetDirectory(0)
                histosToAppendData.append(hData)
        h = addHistosTogether(histosToAppendData)
        # h.SetDirectory(0)
        h.Write(year+"_data_obs")
        # del histosToAppendData
        #gc.collect()
        if(applyShapeSystematics):
            systs = updateSystematics(year, addShapeNuisances = addShapeNuisances, addPDF=addPDF, addModels = addModels)
            # systs.update({"MASS": [s for s in signals]+["ttbarbg","ttbarsignal_BKGNoAddJet"]})
            # systs.update({"MASS": [s for s in signals]+["ttbarbg","ttbarsignal_BKGNoAddJet","singlet"]})
            systs.update({"MASS": [s for s in signals]+["ttbarbgFromLjets","ttbarbgFromHadronic","ttbarbgFromDilepton","ttbarsignal_BKGNoAddJet","singlet"]})
            for sys in systs:
                # print "sys",sys,"\t",systs.keys().index(sys)+1,"out of",len(systs)
                print ("sys",sys,"\t",systs.keys().index(sys)+1,"out of",len(systs),"- year",year,"\t",years.index(year)+1,"out of",len(years))
                for typ in ["Up","Down"]:
                    histosToAppendPerProcSys = {}
                    for proc in procs:
                        histosToAppendPerProcSys[proc]=[]
                        for channel in channels:
                            for category in categoryList:
                                observable = datacard_dict_[category]["distribution"]
                                hIn = inRootFile_.Get(year+"_"+channel+"_"+category+"_"+observable+"_"+proc+"__"+sys+typ)
                                # hIn = hIn.Clone()
                                # hIn.SetDirectory(0)
                                histosToAppendPerProcSys[proc].append(hIn)
                    for proc in procs:
                        # print sys,histosToAppendPerProcSys[proc]
                        hs = addHistosTogether(histosToAppendPerProcSys[proc])
                        # hs.SetDirectory(0)
                        hs.Write(year+"_"+proc+"__"+sys+typ)
                    # del histosToAppendPerProcSys
                    #gc.collect()
    # outRootFile.Close()
    # inRootFile_.Close()
    # outRootFile_.Close()

def createToyShapeFileFromShapeFile(inpath, datacard_dict_, years, channels, categories, outputFolder, withSystematics=True, seedNumber = None):
    print ("Creating Toy Shape file")
    # print "Creating Toy Shape file for:"
    # print years, channels
    # print "from infile:",inpath
    # print "to outpath:",outputFolder
    # print "with Systematics:",withSystematics
    # print "using seed:",seedNumber
    #set random seed
    if seedNumber:
        ROOT.gRandom.SetSeed(int(seedNumber))
    else:
        from time import time
        ROOT.gRandom.SetSeed(int(time()*100.))
    # create outfile and load input shapes
    inRootFile = TFile(inpath, "READ")
    outFile = TFile(outputFolder+"/AllShapes.root","RECREATE")
    outFile.cd()
    #start looping
    for year in years:
        # print year
        # nominal
        for channel in channels:
            # print channel
            for key in datacard_dict_:
                # print key
                hOldNominals = {}
                hOldNominalAddedForData = None
                hNewNominals = {}
                category = key
                observable = datacard_dict_[key]["distribution"]
                for proc in procs:
                    # print proc
                    #get raw and scaled original histograms
                    hIn = inRootFile.Get(year+"_"+channel+"_"+category+"_"+observable+"_"+proc)
                    hInUnscaled = inRootFile.Get(year+"_"+channel+"_"+category+"_"+observable+"_"+proc+"_unscale")
                    # hIn.SetDirectory(0)
                    # hInUnscaled.SetDirectory(0)
                    hOut = hIn.Clone()
                    # hOut.SetDirectory(0)
                    #calculate new values
                    # for binX in range(1,hIn.GetNbinsX()):
                    for binX in range(1,hIn.GetNbinsX()+1):
                        old = hIn.GetBinContent(binX)
                        oldErr = hIn.GetBinError(binX)
                        trueEntries = hInUnscaled.GetBinContent(binX)
                        factor = old/trueEntries
                        newTrue = ROOT.gRandom.Poisson(trueEntries)
                        # newTrue = trueEntries
                        newBinContent = newTrue*factor
                        newBinError = oldErr * np.sqrt(newBinContent/old)
                        hOut.SetBinContent(binX, newBinContent)
                        hOut.SetBinError(binX, newBinError)
                    hOut.SetBinContent(0, 0.)
                    hOut.SetBinError(0, 0.)
                    hOut.SetBinContent(hIn.GetNbinsX()+2, 0.)
                    hOut.SetBinError(hIn.GetNbinsX()+2, 0.)
                    #save the new and old histograms for correlated systematics
                    hOldNominals[proc] = hIn.Clone()
                    hNewNominals[proc] = hOut.Clone()
                    # hOldNominals[proc].SetDirectory(0)
                    # hNewNominals[proc].SetDirectory(0)
                    # add old nominals to "Data" (Asimov)
                    if hOldNominalAddedForData == None:
                        hOldNominalAddedForData = hIn.Clone()
                        # hOldNominalAddedForData.SetDirectory(0)
                    else:
                        hOldNominalAddedForData = aux.addHists(hOldNominalAddedForData, hIn)
                    #write to file
                    hOut.Write(year+"_"+channel+"_"+category+"_"+observable+"_"+proc)
                hOldNominalAddedForData.Write(year+"_"+channel+"_"+category+"_"+observable+"_"+"data_obs")
                #run systematics
                if withSystematics:
                    systs = updateSystematics(year)
                    # systs.update({"MASS": [s for s in signals]+["ttbarbg","ttbarsignal_BKGNoAddJet"]})
                    # systs.update({"MASS": [s for s in signals]+["ttbarbg","ttbarsignal_BKGNoAddJet","singlet"]})
                    systs.update({"MASS": [s for s in signals]+["ttbarbgFromLjets","ttbarbgFromHadronic","ttbarbgFromDilepton","ttbarsignal_BKGNoAddJet","singlet"]})
                    for sys in systs:
                        # systematics from dedicated samples
                        # if sys in uncorrelatedFromNominalSystematics:
                        if sys in uncorrelatedFromNominalSystematicsTotal:
                            for typ in ["Up","Down"]:
                                for proc in procs:
                                    hIn = inRootFile.Get(year+"_"+channel+"_"+category+"_"+observable+"_"+proc+"__"+sys+typ)
                                    hInUnscaled = inRootFile.Get(year+"_"+channel+"_"+category+"_"+observable+"_"+proc+"__"+sys+typ+"_unscale")
                                    # hIn.SetDirectory(0)
                                    # hInUnscaled.SetDirectory(0)
                                    hOut = hIn.Clone()
                                    # hOut.SetDirectory(0)
                                    # for binX in range(1,hIn.GetNbinsX()):
                                    for binX in range(1,hIn.GetNbinsX()+1):
                                        old = hIn.GetBinContent(binX)
                                        oldErr = hIn.GetBinError(binX)
                                        trueEntries = hInUnscaled.GetBinContent(binX)
                                        factor = old/trueEntries
                                        newTrue = ROOT.gRandom.Poisson(trueEntries)
                                        newBinContent = newTrue*factor
                                        newBinError = oldErr * np.sqrt(newBinContent/old)
                                        hOut.SetBinContent(binX, newBinContent)
                                        hOut.SetBinError(binX, newBinError)
                                    hOut.SetBinContent(0, 0.)
                                    hOut.SetBinError(0, 0.)
                                    hOut.SetBinContent(hIn.GetNbinsX()+2, 0.)
                                    hOut.SetBinError(hIn.GetNbinsX()+2, 0.)
                                    hOut.Write(year+"_"+channel+"_"+category+"_"+observable+"_"+proc+"__"+sys+typ)
                        elif sys in uncorrelatedFromNominalSystematicsUpType:
                            for typ in ["Up"]:
                                for proc in procs:
                                    hIn = inRootFile.Get(year+"_"+channel+"_"+category+"_"+observable+"_"+proc+"__"+sys+typ)
                                    hInUnscaled = inRootFile.Get(year+"_"+channel+"_"+category+"_"+observable+"_"+proc+"__"+sys+typ+"_unscale")
                                    # hIn.SetDirectory(0)
                                    # hInUnscaled.SetDirectory(0)
                                    hOut = hIn.Clone()
                                    # hOut.SetDirectory(0)
                                    # for binX in range(1,hIn.GetNbinsX()):
                                    for binX in range(1,hIn.GetNbinsX()+1):
                                        old = hIn.GetBinContent(binX)
                                        oldErr = hIn.GetBinError(binX)
                                        trueEntries = hInUnscaled.GetBinContent(binX)
                                        factor = old/trueEntries
                                        newTrue = ROOT.gRandom.Poisson(trueEntries)
                                        newBinContent = newTrue*factor
                                        newBinError = oldErr * np.sqrt(newBinContent/old)
                                        hOut.SetBinContent(binX, newBinContent)
                                        hOut.SetBinError(binX, newBinError)
                                    hOut.SetBinContent(0, 0.)
                                    hOut.SetBinError(0, 0.)
                                    hOut.SetBinContent(hIn.GetNbinsX()+2, 0.)
                                    hOut.SetBinError(hIn.GetNbinsX()+2, 0.)
                                    hOut.Write(year+"_"+channel+"_"+category+"_"+observable+"_"+proc+"__"+sys+typ)
                            for typ in ["Down"]:
                                for proc in procs:
                                    hIn = inRootFile.Get(year+"_"+channel+"_"+category+"_"+observable+"_"+proc+"__"+sys+typ)
                                    hIn.SetDirectory(0)
                                    hOut = hIn.Clone()
                                    hOut.SetDirectory(0)
                                    # for binX in range(1,hIn.GetNbinsX()):
                                    for binX in range(1,hIn.GetNbinsX()+1):
                                        old = hIn.GetBinContent(binX)
                                        oldErr = hIn.GetBinError(binX)
                                        nom = hOldNominals[proc].GetBinContent(binX)
                                        nomNew = hNewNominals[proc].GetBinContent(binX)
                                        factor = old/nom
                                        newBinContent = nomNew*factor
                                        newBinError = oldErr * np.sqrt(newBinContent/old)
                                        hOut.SetBinContent(binX, newBinContent)
                                        hOut.SetBinError(binX, newBinError)
                                    hOut.SetBinContent(0, 0.)
                                    hOut.SetBinError(0, 0.)
                                    hOut.SetBinContent(hIn.GetNbinsX()+2, 0.)
                                    hOut.SetBinError(hIn.GetNbinsX()+2, 0.)
                                        # print sys, typ, proc, old, oldErr, nom, nomNew, newBinContent, newBinError
                                    hOut.Write(year+"_"+channel+"_"+category+"_"+observable+"_"+proc+"__"+sys+typ)
                        else:
                            # systematics correlated to nominal statistics
                            for typ in ["Up","Down"]:
                                for proc in procs:
                                    hIn = inRootFile.Get(year+"_"+channel+"_"+category+"_"+observable+"_"+proc+"__"+sys+typ)
                                    hIn.SetDirectory(0)
                                    hOut = hIn.Clone()
                                    hOut.SetDirectory(0)
                                    # for binX in range(1,hIn.GetNbinsX()):
                                    for binX in range(1,hIn.GetNbinsX()+1):
                                        old = hIn.GetBinContent(binX)
                                        oldErr = hIn.GetBinError(binX)
                                        nom = hOldNominals[proc].GetBinContent(binX)
                                        nomNew = hNewNominals[proc].GetBinContent(binX)
                                        factor = old/nom
                                        newBinContent = nomNew*factor
                                        newBinError = oldErr * np.sqrt(newBinContent/old)
                                        hOut.SetBinContent(binX, newBinContent)
                                        hOut.SetBinError(binX, newBinError)
                                    hOut.SetBinContent(0, 0.)
                                    hOut.SetBinError(0, 0.)
                                    hOut.SetBinContent(hIn.GetNbinsX()+2, 0.)
                                    hOut.SetBinError(hIn.GetNbinsX()+2, 0.)
                                        # print sys, typ, proc, old, oldErr, nom, nomNew, newBinContent, newBinError
                                    hOut.Write(year+"_"+channel+"_"+category+"_"+observable+"_"+proc+"__"+sys+typ)
    # print "loop done, close outputfile"
    outFile.Close()
    # gROOT.GetListOfFiles().Remove(outFile)
    # print "close now input file"
    inRootFile.Close()
    # gROOT.GetListOfFiles().Remove(inRootFile)
    # print "toy file created, exiting method"

def createFakeShapeSystematicFromRate(inputHisto, sysName, rateFactor = 0., typ = None):
    # h_in = inputHisto.Clone()
    h_out =inputHisto.Clone()
    h_out.SetDirectory(0)
    name = inputHisto.GetName()
    isNominal = True if name.split("__")[-1] == "" else False
    outName = name+"__"+sysName+"Up" if typ=="Up" else name+"__"+sysName+"Down"
    uncRate = 0.
    if typ == "Up":
        uncRate = abs(rateFactor)
    elif typ == "Down":
        uncRate = -1. * abs(rateFactor)
    else:
        print ("ERROR: createFakeShapeSystematicFromRate, typ not known!")
    uncRate = 1. + uncRate
    # print uncRate
    for binX in range(1,h_out.GetNbinsX()+1):
        h_out.SetBinContent(binX, h_out.GetBinContent(binX) * uncRate)
    h_out.SetName(outName)
    # del h_in
    #gc.collect()
    return h_out

def createShapeSystsForProcessAndCategory(inputHisto, processName, catname, affectedProcesses, affectedCategories, sysName, rateFactor = 0., typ = None):
    h_in = inputHisto.Clone()
    h_in.SetDirectory(0)
    h_out = createFakeShapeSystematicFromRate(h_in, sysName, 0., typ)
    h_out.SetDirectory(0)
    # print (processName, affectedProcesses)
    # print( catname, affectedCategories)
    if processName in affectedProcesses:
        if catname in affectedCategories:
            h_out = createFakeShapeSystematicFromRate(h_in, sysName, rateFactor, typ)
            h_out.SetDirectory(0)
    # del h_in
    #gc.collect()
    return h_out

def getRescalingFactor(sys, typ, year, channel, proc, rescaleSyst = None):
    # print (rescaleSyst, sys)
    if rescaleSyst == None:
        return 1.
    elif rescaleSyst == "HERWIG" and not "HERWIG" in sys:
        return 1.
    elif rescaleSyst == "AMCATNLOFXFX" and not "AMCATNLOFXFX" in sys:
        return 1.
    elif rescaleSyst == "FIVEFS" and not "FIVEFS" in sys:
        return 1.
    elif rescaleSyst == "FOURFS" and not "FOURFS" in sys:
        return 1.
    elif rescaleSyst == "FIVEFS2MU" and not "FIVEFS2MU" in sys:
        return 1.
    elif (rescaleSyst == "AMCATNLOFXFX" and "AMCATNLOFXFX" in sys) \
    or (rescaleSyst == "HERWIG" and "HERWIG" in sys) \
    or (rescaleSyst == "FIVEFS" and "FIVEFS" in sys) \
    or (rescaleSyst == "FOURFS" and "FOURFS" in sys) \
    or (rescaleSyst == "FIVEFS2MU" and "FIVEFS2MU" in sys) \
    or (rescaleSyst == "MODEL" and sys.replace("Up","").replace("Down","") in listOfModelingUnc) :
        if proc not in ["tt_bb", "tt_bb4FS", "tt_bb4FS2mu", "tt_bj", "tt_bj4FS", "tt_bj4FS2mu", "tt_2b", "tt_2b4FS", "tt_2b4FS2mu", "tt_cc", "tt_cj", "tt_2c", "tt_lf"]:
            return 1.
        if "FIVEFS2MU" in sys and proc not in ["tt_bb4FS2mu", "tt_bj4FS2mu", "tt_2b4FS2mu"]+["tt_bb4FS", "tt_bj4FS", "tt_2b4FS"]:
            return 1.
        if "FIVEFS" in sys and proc not in ["tt_bb4FS", "tt_bj4FS", "tt_2b4FS"]+["tt_bb4FS2mu", "tt_bj4FS2mu", "tt_2b4FS2mu"]:
            return 1.
        if "FOURFS" in sys and proc not in ["tt_bb", "tt_bj", "tt_2b"]+["tt_bb4FS2mu", "tt_bj4FS2mu", "tt_2b4FS2mu"]:
            return 1.
        category = "GreaterTwoMediumBCTagGreaterZeroMediumBTag_InclusiveNJet_InclusiveNNCategory"
        observable = "NEvents"
        # print ("HERE",year+"/"+channel+"/"+proc+"/"+category+"_"+observable+"__"+sys+typ)
        filenameN = pathPlotting.replace("YEAR",year).replace("SYSTEMATIC","Nominal").replace("ADDNAME","")
        filenameS = pathPlotting.replace("YEAR",year).replace("SYSTEMATIC",sys+typ).replace("ADDNAME","")
        fInN = ROOT.TFile(filenameN, "READ")
        fInS = ROOT.TFile(filenameS, "READ")
        ROOT.SetOwnership(fInN, True)
        ROOT.SetOwnership(fInS, True)
        hS = fInS.Get(year+"/"+channel+"/"+proc+"/"+category+"_"+observable+"__"+sys+typ)
        hN = fInN.Get(year+"/"+channel+"/"+proc+"/"+category+"_"+observable)
        if hN is None:
            ValueError("getRescalingFactor -- Histogram hN with name", year+"/"+channel+"/"+proc+"/"+category+"_"+observable, "in file", filenameN, "is NONE!")
        if hS is None:
            ValueError("getRescalingFactor -- Histogram hS with name", year+"/"+channel+"/"+proc+"/"+category+"_"+observable+"__"+sys+typ, "in file", filenameS, "is NONE!")
        ROOT.SetOwnership(hS, True)
        ROOT.SetOwnership(hN, True)
        hS.SetDirectory(0)
        hN.SetDirectory(0)
        fixHistogram(hS, False)
        fixHistogram(hN, False)
        iS = hS.Integral()
        iN = hN.Integral()
        absDiff = np.abs(iS - iN)
        fInN.Close()
        fInS.Close()
        # import pdb
        # pdb.set_trace()
        # print (hN, hS)
        # print (iN, iS)
        # print (iN / iS)
        if absDiff > 0.01:
            # print (iN, iS)
            return iN / iS
        else:
            return 1.
    else:
        return 1.

def processSystematic(sys, systs, year, years, channels, datacard_dict_, binningJson, verbosity, outRootFilePath, checkBinning, use4FS = True,
                    use2muF = False, scaleYields = None, scaleTTBB = None, rescaleSyst = None):
    newOutpath = outRootFilePath.replace("/AllShapes.root","/SystShapes"+year+"/"+sys+".root")
    newOutFolder = outRootFilePath.replace("/AllShapes.root","/SystShapes"+year+"/")
    if not os.path.exists(newOutFolder):
        os.makedirs(newOutFolder, exist_ok = True)
    if not os.path.exists(newOutpath):
        if verbosity > 1:
            print ("-- sys:",sys,"|",systs.index(sys)+1,"out of",len(systs),"[ year:",year,"|",years.index(year)+1,"out of",len(years),"]")
        outRootFile = TFile(newOutpath,"RECREATE")
        ROOT.SetOwnership(outRootFile, True)
        procsToUse = procs
        if use4FS and not use2muF:
            procsToUse = procs
        elif use4FS and use2muF:
            procsToUse = procs4FS2mu
        else:
            procsToUse = procs5FS
        procs_ = procsToUse.keys()
        for typ in ["Up", "Down"]:
            filename = pathPlotting.replace("YEAR",year).replace("SYSTEMATIC",sys+typ).replace("ADDNAME","")
            fIn = ROOT.TFile(filename, "READ")
            ROOT.SetOwnership(fIn, True)
            outRootFile.cd()
            for channel in channels:
                if verbosity > 2: print ("--- channel:",channel,"|",channels.index(channel)+1,"out of",len(channels))
                if verbosity > 3: keys = datacard_dict_[channel].keys()
                for category in datacard_dict_[channel]:
                    if verbosity > 3:  print ("--- key:",category,"|",keys.index(category)+1,"out of",len(keys))
                    observable_orig = datacard_dict_[channel][category]["distribution"]
                    observable = datacard_dict_[channel][category]["distribution"]
                    if checkBinning:
                        if not (observable == "NEvents"):
                            binAr = aux.loadBinningFromJson(year+"_"+channel+"_"+category+"_"+observable, binningJson)
                            if binAr == None:
                                print ("ERROR with binning in:", year+"_"+channel+"_"+category+"_"+observable)
                            if len(binAr)==2:
                                observable = "NEvents"
                            else:
                                observable = observable_orig
                    isNEvents = True if observable == "NEvents" else False
                    for proc in procsToUse:
                        # store already here one fake histogram, so we don't have to load it multiple times
                        filename_nominalForData_FAKE = pathPlotting.replace("YEAR",year).replace("SYSTEMATIC","Nominal").replace("ADDNAME","")
                        fIn_nominalForData_FAKE = ROOT.TFile(filename_nominalForData_FAKE, "READ")
                        hVar_FAKE = fIn_nominalForData_FAKE.Get(year+"/"+channel+"/"+"data_obs"+"/"+category+"_"+observable)
                        ROOT.SetOwnership(hVar_FAKE, True)
                        hVar_FAKE = CreateFakeHistoFromData(hVar_FAKE, year+"/"+channel+"/"+proc+"/"+category+"_"+observable+"__"+sys+typ)
                        ROOT.SetOwnership(hVar_FAKE, True)
                        if verbosity > 4: print ("---- proc:",proc,"|",procs_.index(proc)+1,"out of",len(procs_),"| With observable:",observable, "; and original observable:",observable_orig)
                        if not isNEvents:
                            hVar = fIn.Get(year+"/"+channel+"/"+proc+"/"+category+"_"+observable+"__"+sys+typ)
                            ROOT.SetOwnership(hVar, True)
                            if not hVar:
                                hVar = hVar_FAKE.Clone()
                                hVar.SetName(year+"/"+channel+"/"+proc+"/"+category+"_"+observable+"__"+sys+typ)
                            if checkBinning:
                                hVar = aux.rebin(hVar, binAr, scale=False)
                        else:
                            hVar = fIn.Get(year+"/"+channel+"/"+proc+"/"+category+"_"+"NEvents"+"__"+sys+typ)
                            ROOT.SetOwnership(hVar, True)
                            if not hVar:
                                hVar = hVar_FAKE.Clone()
                                hVar.SetName(year+"/"+channel+"/"+proc+"/"+category+"_"+observable+"__"+sys+typ)
                        outChannelName = getCombineChannelName(year+"/"+channel+"/"+proc+"/"+category+"_"+observable_orig)
                        outRootFile.cd()
                        if not outRootFile.GetDirectory(outChannelName):
                            outRootFile.mkdir(outChannelName)
                        if scaleYields:
                            hVar.Scale(scaleYields)
                        if scaleTTBB:
                            if "tt_bb" in proc:
                                hVar.Scale(scaleTTBB)
                        fixHistogram(hVar, False)
                        if rescaleSyst is not None:
                            rs = getRescalingFactor(sys, typ, year, channel, proc, rescaleSyst)
                            if abs(rs - 1.0) > 0.:
                                hVar.Scale(rs)
                                print (sys, typ, year, channel, proc, rs)
                        outRootFile.cd()
                        outRootFile.cd(outChannelName)
                        hVar.Write(proc+"__"+sys+typ)
                        del hVar, hVar_FAKE
                        fIn_nominalForData_FAKE.Close()
                        del fIn_nominalForData_FAKE
            fIn.Close()
            del fIn
        outRootFile.Close()
    else:
        if verbosity > 1:
            print ("-- sys:",sys,"exists. Skip!|",systs.index(sys)+1,"out of",len(systs),"[ year:",year,"|",years.index(year)+1,"out of",len(years),"]")

def multi_run_wrapper(args):
   return processSystematic(*args)

def createShapeFile(datacard_dict_, years, channels, outputFolder="", applyShapeSystematics=True, checkBinning= True, addMet=False, addShapeNuisances = None, addPDF=True, binningFilePath = "",
                    use4FS = True, use2muF = False, usePSBreakdown = False, verbosity = 0, scaleYields = None, scaleTTBB = None, scaleTTH = None, scaleTTHcc = None, pseudoData = None, addModels = False, rescaleSyst = None):
    import multiprocessing
    from array import array
    outRootFilePath = outputFolder+"/AllShapes.root"
    # print (datacard_dict_)
    # outRootFile = TFile(outRootFilePath,"RECREATE")
    # outRootFile.Close()
    # Opening JSON file for binning:
    fJSON = open(binningFilePath)
    # print (binningFilePath)
    binningJson = json.load(fJSON)
    # procs_ = procs.keys()
    procsToUse = procs
    if use4FS and not use2muF:
        procsToUse = procs
    elif use4FS and use2muF:
        procsToUse = procs4FS2mu
    else:
        procsToUse = procs5FS
    # procs_ = procsToUse.keys()
    # start loop
    # print (binningJson)

    for year in years:
        if verbosity > 0: print ("- year:",year,"|",years.index(year)+1,"out of",len(years))
        if (applyShapeSystematics):
            systs = updateSystematics(year, addMet=addMet, addShapeNuisances=None, addPDF=addPDF, use4FS = use4FS, use2muF = use2muF, usePSBreakdown = usePSBreakdown, addModels = addModels)
            # systs = {"HERWIG_TTBB":{}}
            p = multiprocessing.Pool(26)
            systs_ = [key for key in systs]
            items = [(sys, systs_, year, years, channels, datacard_dict_, binningJson, verbosity, outRootFilePath, checkBinning, use4FS, use2muF, scaleYields, None, rescaleSyst) for sys in systs_]
            # print (items[0])
            for sys in p.map(multi_run_wrapper, items):
                if verbosity > 5:
                    print ("-- DONE sys:",sys,"|",systs_.index(sys)+1,"out of",len(systs_),"[ year:",year,"|",years.index(year)+1,"out of",len(years),"]")
        # nominal
        newOutpath = outRootFilePath.replace("/AllShapes.root","/SystShapes"+year+"/"+"Nominal"+".root")
        newOutFolder = outRootFilePath.replace("/AllShapes.root","/SystShapes"+year+"/")
        if not os.path.exists(newOutFolder):
            os.makedirs(newOutFolder, exist_ok=True)
        if not os.path.exists(newOutpath):
            outRootFile = TFile(newOutpath,"RECREATE")
            filename = pathPlotting.replace("YEAR",year).replace("SYSTEMATIC","Nominal").replace("ADDNAME","")
            fIn = ROOT.TFile(filename,"READ")
            outRootFile.cd()
            for channel in channels:
                for key in datacard_dict_[channel]:
                    category = key
                    # print (channel,keyCH)
                    # print (datacard_dict_[channel])
                    # print (datacard_dict_[channel][keyCH])
                    observable = datacard_dict_[channel][key]["distribution"]
                    observable_orig = datacard_dict_[channel][key]["distribution"]
                    if checkBinning:
                        if not (observable == "NEvents"):
                            binAr = aux.loadBinningFromJson(year+"_"+channel+"_"+category+"_"+observable, binningJson)
                            if len(binAr)==2:
                                observable = "NEvents"
                            else:
                                observable = observable_orig
                    for proc in procsToUse:
                        if not (observable == "NEvents"):
                            hVar = fIn.Get(year+"/"+channel+"/"+proc+"/"+category+"_"+observable)
                            ROOT.SetOwnership(hVar, True)
                            if not hVar:
                                hVar = fIn.Get(year+"/"+channel+"/"+"data_obs"+"/"+category+"_"+observable)
                                ROOT.SetOwnership(hVar, True)
                                hVar = CreateFakeHistoFromData(hVar,year+"/"+channel+"/"+proc+"/"+category+"_"+observable)
                            if checkBinning:
                                hVar = aux.rebin(hVar, binAr, scale=False)
                        else:
                            hVar = fIn.Get(year+"/"+channel+"/"+proc+"/"+category+"_"+"NEvents")
                            ROOT.SetOwnership(hVar, True)
                            if not hVar:
                                hVar = fIn.Get(year+"/"+channel+"/"+"data_obs"+"/"+category+"_"+observable)
                                hVar = CreateFakeHistoFromData(hVar,year+"/"+channel+"/"+proc+"/"+category+"_"+observable)
                        outChannelName = getCombineChannelName(year+"/"+channel+"/"+proc+"/"+category+"_"+observable_orig)
                        if not outRootFile.GetDirectory(outChannelName):
                            outRootFile.mkdir(outChannelName)
                        outRootFile.cd(outChannelName)
                        if scaleYields:
                            hVar.Scale(scaleYields)
                        fixHistogram(hVar, False)
                        hVar.Write(proc)
                        outRootFile.cd()
                        # # add. shape like nuisances
                        # if addShapeNuisances is not None:
                        #     for addShapeNuisance in addShapeNuisances:
                        #         for local_typ in ["Up","Down"]:
                        #             inputHisto =  hVar.Clone()
                        #             # inputHistoUnscale =  hVar_unscale.Clone()
                        #             inputHisto = createShapeSystsForProcessAndCategory(inputHisto, proc, category,
                        #                 addShapeNuisances[addShapeNuisance]["processes"], addShapeNuisances[addShapeNuisance]["categories"],
                        #                 addShapeNuisance, rateFactor = addShapeNuisances[addShapeNuisance]["magnitude"],
                        #                 typ = local_typ)
                        #             # inputHistoUnscale = createShapeSystsForProcessAndCategory(inputHistoUnscale, proc, category,
                        #             #     addShapeNuisances[addShapeNuisance]["processes"], addShapeNuisances[addShapeNuisance]["categories"],
                        #             #     addShapeNuisance, rateFactor = 0.,
                        #             #     typ = local_typ)
                        #             if inputHisto is not None:
                        #                 inputHisto.Write(year+"_"+channel+"_"+category+"_"+observable_orig+"_"+proc+"__"+addShapeNuisance+local_typ)
                        #             # if inputHistoUnscale is not None:
                        #             #     inputHistoUnscale.Write(year+"_"+channel+"_"+category+"_"+observable_orig+"_"+proc+"__"+addShapeNuisance+local_typ+"_unscale")
                    #data
                    allowedPseudoData = [None, "AMCATNLOFXFX", "HERWIG", "4FS", "5FS", "Nominal"]
                    if pseudoData not in allowedPseudoData:
                        raise  ValueError("Pseudodata value",pseudoData,"note allowed! Choose from",allowedPSeudoData)
                    if not pseudoData:
                        if not (observable == "NEvents"):
                            hData = fIn.Get(year+"/"+channel+"/"+"data_obs"+"/"+category+"_"+observable)
                            if checkBinning:
                                hData = aux.rebin(hData, binAr, scale=False)
                        else:
                            hData = fIn.Get(year+"/"+channel+"/"+"data_obs"+"/"+category+"_"+"NEvents")
                        outChannelName = getCombineChannelName(year+"/"+channel+"/"+"data_obs"+"/"+category+"_"+observable_orig)
                        if not outRootFile.GetDirectory(outChannelName):
                            outRootFile.mkdir(outChannelName)
                        outRootFile.cd(outChannelName)
                        # if scaleYields:
                        #         hVar.Scale(scaleYields)
                        fixHistogram(hData, False)
                        hData.Write("data_obs")
                    elif pseudoData == "AMCATNLOFXFX":
                        procsToUseFXFX = procsFXFX
                        filenameFXFX = pathPlotting.replace("YEAR",year).replace("SYSTEMATIC","AMCATNLOFXFXUp").replace("ADDNAME","")
                        fInFXFX = ROOT.TFile(filenameFXFX, "READ")
                        ROOT.SetOwnership(fIn, True)
                        outRootFile.cd()
                        # for channel in channels:
                        #     for category in datacard_dict_[channel]:
                        #         observable_orig = datacard_dict_[channel][category]["distribution"]
                        #         observable = datacard_dict_[channel][category]["distribution"]
                        #         if checkBinning:
                        #             if not (observable == "NEvents"):
                        #                 binAr = aux.loadBinningFromJson(year+"_"+channel+"_"+category+"_"+observable, binningJson)
                        #                 if binAr == None:
                        #                     print ("ERROR with binning in:", year+"_"+channel+"_"+category+"_"+observable)
                        #                 if len(binAr)==2:
                        #                     observable = "NEvents"
                        #                 else:
                        #                     observable = observable_orig
                        isNEvents = True if observable == "NEvents" else False
                        h_pseudoData = None
                        for procFXFX in procsToUseFXFX:
                            # store already here one fake histogram, so we don't have to load it multiple times
                            filename_nominalForData_FAKEFXFX = pathPlotting.replace("YEAR",year).replace("SYSTEMATIC","Nominal").replace("ADDNAME","")
                            fIn_nominalForData_FAKEFXFX = ROOT.TFile(filename_nominalForData_FAKEFXFX, "READ")
                            hVar_FAKEFXFX = fIn_nominalForData_FAKEFXFX.Get(year+"/"+channel+"/"+"data_obs"+"/"+category+"_"+observable)
                            ROOT.SetOwnership(hVar_FAKEFXFX, True)
                            hVar_FAKEFXFX = CreateFakeHistoFromData(hVar_FAKEFXFX, year+"/"+channel+"/"+"data_obs"+"/"+category+"_"+observable)
                            ROOT.SetOwnership(hVar_FAKEFXFX, True)
                            if not isNEvents:
                                hVar = fInFXFX.Get(year+"/"+channel+"/"+procFXFX+"/"+category+"_"+observable+"__"+"AMCATNLOFXFXUp")
                                ROOT.SetOwnership(hVar, True)
                                if not hVar:
                                    hVar = hVar_FAKEFXFX.Clone()
                                    hVar.SetName(year+"/"+channel+"/"+"data_obs"+"/"+category+"_"+observable)
                                if checkBinning:
                                    hVar = aux.rebin(hVar, binAr, scale=False)
                            else:
                                hVar = fInFXFX.Get(year+"/"+channel+"/"+procFXFX+"/"+category+"_"+"NEvents"+"__"+"AMCATNLOFXFXUp")
                                ROOT.SetOwnership(hVar, True)
                                if not hVar:
                                    hVar = hVar_FAKEFXFX.Clone()
                                    hVar.SetName(year+"/"+channel+"/"+"data_obs"+"/"+category+"_"+observable)
                            if scaleYields:
                                hVar.Scale(scaleYields)
                            if scaleTTBB:
                                if "tt_bb" in procFXFX:
                                    hVar.Scale(scaleTTBB)
                            if scaleTTH:
                                if "ttH_" in procFXFX:
                                    hVar.Scale(scaleTTH)
                            
                            if "ttH_hcc" in procFXFX and scaleTTHcc:
                                hVar.Scale(scaleTTHcc)
                            fixHistogram(hVar, False)
                            # hVar.Write(proc+"__"+sys+typ)
                            if h_pseudoData:
                                h_pseudoData = aux.addHists(h_pseudoData, hVar)
                            else:
                                h_pseudoData = hVar
                            ROOT.SetOwnership(h_pseudoData, True)
                            h_pseudoData.SetDirectory(0)
                            # del hVar, hVar_FAKE
                            fIn_nominalForData_FAKEFXFX.Close()
                            # del fIn_nominalForData_FAKE
                        outChannelName = getCombineChannelName(year+"/"+channel+"/"+"data_obs"+"/"+category+"_"+observable_orig)
                        outRootFile.cd()
                        if not outRootFile.GetDirectory(outChannelName):
                            outRootFile.mkdir(outChannelName)
                        outRootFile.cd()
                        outRootFile.cd(outChannelName)
                        h_pseudoData.Write("data_obs")
                    elif pseudoData == "HERWIG":
                        procsToUseHERWIG = procsHERWIG
                        filenameHERWIG = pathPlotting.replace("YEAR",year).replace("SYSTEMATIC","HERWIGUp").replace("ADDNAME","")
                        fInHERWIG = ROOT.TFile(filenameHERWIG, "READ")
                        ROOT.SetOwnership(fInHERWIG, True)
                        outRootFile.cd()
                        # for channel in channels:
                        #     for category in datacard_dict_[channel]:
                        #         observable_orig = datacard_dict_[channel][category]["distribution"]
                        #         observable = datacard_dict_[channel][category]["distribution"]
                        #         if checkBinning:
                        #             if not (observable == "NEvents"):
                        #                 binAr = aux.loadBinningFromJson(year+"_"+channel+"_"+category+"_"+observable, binningJson)
                        #                 if binAr == None:
                        #                     print ("ERROR with binning in:", year+"_"+channel+"_"+category+"_"+observable)
                        #                 if len(binAr)==2:
                        #                     observable = "NEvents"
                        #                 else:
                        #                     observable = observable_orig
                        isNEvents = True if observable == "NEvents" else False
                        h_pseudoData = None
                        for procHERWIG in procsToUseHERWIG:
                            # store already here one fake histogram, so we don't have to load it multiple times
                            filename_nominalForData_FAKEHERWIG = pathPlotting.replace("YEAR",year).replace("SYSTEMATIC","Nominal").replace("ADDNAME","")
                            fIn_nominalForData_FAKEHERWIG = ROOT.TFile(filename_nominalForData_FAKEHERWIG, "READ")
                            hVar_FAKEHERWIG = fIn_nominalForData_FAKEHERWIG.Get(year+"/"+channel+"/"+"data_obs"+"/"+category+"_"+observable)
                            ROOT.SetOwnership(hVar_FAKEHERWIG, True)
                            hVar_FAKEHERWIG = CreateFakeHistoFromData(hVar_FAKEHERWIG, year+"/"+channel+"/"+"data_obs"+"/"+category+"_"+observable)
                            ROOT.SetOwnership(hVar_FAKEHERWIG, True)
                            if not isNEvents:
                                hVarHERWIG = fInHERWIG.Get(year+"/"+channel+"/"+procHERWIG+"/"+category+"_"+observable+"__"+"HERWIGUp")
                                ROOT.SetOwnership(hVar, True)
                                if not hVarHERWIG:
                                    hVarHERWIG = hVar_FAKEHERWIG.Clone()
                                    hVarHERWIG.SetName(year+"/"+channel+"/"+"data_obs"+"/"+category+"_"+observable)
                                if checkBinning:
                                    hVarHERWIG = aux.rebin(hVarHERWIG, binAr, scale=False)
                            else:
                                hVarHERWIG = fInHERWIG.Get(year+"/"+channel+"/"+procHERWIG+"/"+category+"_"+"NEvents"+"__"+"HERWIGUp")
                                ROOT.SetOwnership(hVarHERWIG, True)
                                if not hVarHERWIG:
                                    hVarHERWIG = hVar_FAKEHERWIG.Clone()
                                    hVarHERWIG.SetName(year+"/"+channel+"/"+"data_obs"+"/"+category+"_"+observable)
                            if scaleYields:
                                hVarHERWIG.Scale(scaleYields)
                            if scaleTTBB:
                                if "tt_bb" in procHERWIG:
                                    hVarHERWIG.Scale(scaleTTBB)
                            if scaleTTH:
                                if "ttH_" in procHERWIG:
                                    hVar.Scale(scaleTTH)
                            if "ttH_hcc" in procHERWIG and scaleTTHcc:
                                hVar.Scale(scaleTTHcc)
                            fixHistogram(hVarHERWIG, False)
                            if h_pseudoData:
                                h_pseudoData = aux.addHists(h_pseudoData, hVarHERWIG)
                            else:
                                h_pseudoData = hVarHERWIG
                            ROOT.SetOwnership(h_pseudoData, True)
                            h_pseudoData.SetDirectory(0)
                            fIn_nominalForData_FAKEHERWIG.Close()
                        outChannelName = getCombineChannelName(year+"/"+channel+"/"+"data_obs"+"/"+category+"_"+observable_orig)
                        outRootFile.cd()
                        if not outRootFile.GetDirectory(outChannelName):
                            outRootFile.mkdir(outChannelName)
                        outRootFile.cd()
                        outRootFile.cd(outChannelName)
                        h_pseudoData.Write("data_obs")
                    elif pseudoData == "5FS":
                        procsToUse5FS = procs5FS
                        filename5FS = pathPlotting.replace("YEAR",year).replace("SYSTEMATIC","Nominal").replace("ADDNAME","")
                        fIn5FS = ROOT.TFile(filename5FS, "READ")
                        ROOT.SetOwnership(fIn5FS, True)
                        outRootFile.cd()
                        # for channel in channels:
                        #     for category in datacard_dict_[channel]:
                        #         observable_orig = datacard_dict_[channel][category]["distribution"]
                        #         observable = datacard_dict_[channel][category]["distribution"]
                        #         if checkBinning:
                        #             if not (observable == "NEvents"):
                        #                 binAr = aux.loadBinningFromJson(year+"_"+channel+"_"+category+"_"+observable, binningJson)
                        #                 if binAr == None:
                        #                     print ("ERROR with binning in:", year+"_"+channel+"_"+category+"_"+observable)
                        #                 if len(binAr)==2:
                        #                     observable = "NEvents"
                        #                 else:
                        #                     observable = observable_orig
                        isNEvents = True if observable == "NEvents" else False
                        h_pseudoData = None
                        for proc5FS in procsToUse5FS:
                            # print (proc5FS)
                            # store already here one fake histogram, so we don't have to load it multiple times
                            filename_nominalForData_FAKE5FS = pathPlotting.replace("YEAR",year).replace("SYSTEMATIC","Nominal").replace("ADDNAME","")
                            fIn_nominalForData_FAKE5FS = ROOT.TFile(filename_nominalForData_FAKE5FS, "READ")
                            hVar_FAKE5FS = fIn_nominalForData_FAKE5FS.Get(year+"/"+channel+"/"+"data_obs"+"/"+category+"_"+observable)
                            ROOT.SetOwnership(hVar_FAKE5FS, True)
                            hVar_FAKE5FS = CreateFakeHistoFromData(hVar_FAKE5FS, year+"/"+channel+"/"+"data_obs"+"/"+category+"_"+observable)
                            ROOT.SetOwnership(hVar_FAKE5FS, True)
                            # hVar_FAKE5FS.SetDirectory(0)
                            # hVar5FS.SetDirectory(0)
                            if not isNEvents:
                                hVar5FS = fIn5FS.Get(year+"/"+channel+"/"+proc5FS+"/"+category+"_"+observable)
                                # hVar5FS.SetDirectory(0)
                                ROOT.SetOwnership(hVar5FS, True)
                                if not hVar5FS:
                                    hVar5FS = hVar_FAKE5FS.Clone()
                                    hVar5FS.SetName(year+"/"+channel+"/"+"data_obs"+"/"+category+"_"+observable)
                                    # hVar5FS.SetDirectory(0)
                                if checkBinning:
                                    hVar5FS = aux.rebin(hVar5FS, binAr, scale=False)
                            else:
                                hVar5FS = fIn5FS.Get(year+"/"+channel+"/"+proc5FS+"/"+category+"_"+"NEvents")
                                ROOT.SetOwnership(hVar5FS, True)
                                if not hVar5FS:
                                    hVar5FS = hVar_FAKE5FS.Clone()
                                    hVar5FS.SetName(year+"/"+channel+"/"+"data_obs"+"/"+category+"_"+observable)
                                    # ROOT.SetOwnership(hVar5FS, True)
                                    # hVar5FS.SetDirectory(0)
                            if scaleYields:
                                hVar5FS.Scale(scaleYields)
                            if scaleTTBB:
                                if "tt_bb" in proc5FS or "tt_bj" in proc5FS or "tt_2b" in proc5FS:
                                    hVar5FS.Scale(scaleTTBB)
                            if scaleTTH:
                                if "ttH_" in proc5FS:
                                    hVar5FS.Scale(scaleTTH)
                            if "ttH_hcc" in proc5FS and scaleTTHcc:
                                hVar5FS.Scale(scaleTTHcc)
                            fixHistogram(hVar5FS, False)
                            ROOT.SetOwnership(hVar5FS, True)
                            if h_pseudoData is not None:
                                h_pseudoData = aux.addHists(h_pseudoData, hVar5FS)
                            else:
                                h_pseudoData = hVar5FS
                            h_pseudoData.SetName(year+"/"+channel+"/"+"data_obs"+"/"+category+"_"+observable)
                            h_pseudoData.SetDirectory(0)
                            ROOT.SetOwnership(h_pseudoData, True)
                            fIn_nominalForData_FAKE5FS.Close()
                        outChannelName = getCombineChannelName(year+"/"+channel+"/"+"data_obs"+"/"+category+"_"+observable_orig)
                        outRootFile.cd()
                        if not outRootFile.GetDirectory(outChannelName):
                            outRootFile.mkdir(outChannelName)
                        outRootFile.cd()
                        outRootFile.cd(outChannelName)
                        h_pseudoData.Write("data_obs")
                    elif pseudoData == "4FS":
                        procsToUse4FS = procs
                        filename4FS = pathPlotting.replace("YEAR",year).replace("SYSTEMATIC","Nominal").replace("ADDNAME","")
                        fIn4FS = ROOT.TFile(filename4FS, "READ")
                        ROOT.SetOwnership(fIn4FS, True)
                        outRootFile.cd()
                        # for channel in channels:
                        #     for category in datacard_dict_[channel]:
                        #         observable_orig = datacard_dict_[channel][category]["distribution"]
                        #         observable = datacard_dict_[channel][category]["distribution"]
                        #         if checkBinning:
                        #             if not (observable == "NEvents"):
                        #                 binAr = aux.loadBinningFromJson(year+"_"+channel+"_"+category+"_"+observable, binningJson)
                        #                 if binAr == None:
                        #                     print ("ERROR with binning in:", year+"_"+channel+"_"+category+"_"+observable)
                        #                 if len(binAr)==2:
                        #                     observable = "NEvents"
                        #                 else:
                        #                     observable = observable_orig
                        isNEvents = True if observable == "NEvents" else False
                        h_pseudoData = None
                        for proc4FS in procsToUse4FS:
                            # store already here one fake histogram, so we don't have to load it multiple times
                            filename_nominalForData_FAKE4FS = pathPlotting.replace("YEAR",year).replace("SYSTEMATIC","Nominal").replace("ADDNAME","")
                            fIn_nominalForData_FAKE4FS = ROOT.TFile(filename_nominalForData_FAKE4FS, "READ")
                            hVar_FAKE4FS = fIn_nominalForData_FAKE4FS.Get(year+"/"+channel+"/"+"data_obs"+"/"+category+"_"+observable)
                            ROOT.SetOwnership(hVar_FAKE4FS, True)
                            hVar_FAKE4FS = CreateFakeHistoFromData(hVar_FAKE4FS, year+"/"+channel+"/"+"data_obs"+"/"+category+"_"+observable)
                            ROOT.SetOwnership(hVar_FAKE4FS, True)
                            if not isNEvents:
                                hVar4FS = fIn.Get(year+"/"+channel+"/"+proc4FS+"/"+category+"_"+observable)
                                ROOT.SetOwnership(hVar, True)
                                if not hVar4FS:
                                    hVar4FS = hVar_FAKE4FS.Clone()
                                    hVar4FS.SetName(year+"/"+channel+"/"+"data_obs"+"/"+category+"_"+observable)
                                if checkBinning:
                                    hVar4FS = aux.rebin(hVar4FS, binAr, scale=False)
                            else:
                                hVar4FS = fIn.Get(year+"/"+channel+"/"+proc4FS+"/"+category+"_"+"NEvents")
                                ROOT.SetOwnership(hVar4FS, True)
                                if not hVar4FS:
                                    hVar4FS = hVar_FAKE4FS.Clone()
                                    hVar4FS.SetName(year+"/"+channel+"/"+"data_obs"+"/"+category+"_"+observable)
                            if scaleYields:
                                hVar4FS.Scale(scaleYields)
                            if scaleTTBB:
                                if "tt_bb" in proc4FS or "tt_bj" in proc4FS or "tt_2b" in proc4FS:
                                    hVar4FS.Scale(scaleTTBB)
                            if scaleTTH:
                                if "ttH_" in proc4FS:
                                    hVar4FS.Scale(scaleTTH)
                            if "ttH_hcc" in proc4FS and scaleTTHcc:
                                hVar4FS.Scale(scaleTTHcc)
                            fixHistogram(hVar4FS, False)
                            ROOT.SetOwnership(hVar4FS, True)
                            if h_pseudoData is not None:
                                h_pseudoData = aux.addHists(h_pseudoData, hVar4FS)
                            else:
                                h_pseudoData = hVar4FS
                            h_pseudoData.SetName(year+"/"+channel+"/"+"data_obs"+"/"+category+"_"+observable)
                            h_pseudoData.SetDirectory(0)
                            ROOT.SetOwnership(h_pseudoData, True)
                            fIn_nominalForData_FAKE4FS.Close()
                        outChannelName = getCombineChannelName(year+"/"+channel+"/"+"data_obs"+"/"+category+"_"+observable_orig)
                        outRootFile.cd()
                        if not outRootFile.GetDirectory(outChannelName):
                            outRootFile.mkdir(outChannelName)
                        outRootFile.cd()
                        outRootFile.cd(outChannelName)
                        h_pseudoData.Write("data_obs")
                    elif pseudoData == "Nominal":
                        procsToUseNomToy = procs
                        filenameNomToy = pathPlotting.replace("YEAR",year).replace("SYSTEMATIC","Nominal").replace("ADDNAME","")
                        fInNomToy = ROOT.TFile(filenameNomToy, "READ")
                        ROOT.SetOwnership(fInNomToy, True)
                        outRootFile.cd()
                        # for channel in channels:
                        #     for category in datacard_dict_[channel]:
                        #         observable_orig = datacard_dict_[channel][category]["distribution"]
                        #         observable = datacard_dict_[channel][category]["distribution"]
                        #         if checkBinning:
                        #             if not (observable == "NEvents"):
                        #                 binAr = aux.loadBinningFromJson(year+"_"+channel+"_"+category+"_"+observable, binningJson)
                        #                 if binAr == None:
                        #                     print ("ERROR with binning in:", year+"_"+channel+"_"+category+"_"+observable)
                        #                 if len(binAr)==2:
                        #                     observable = "NEvents"
                        #                 else:
                        #                     observable = observable_orig
                        isNEvents = True if observable == "NEvents" else False
                        h_pseudoData = None
                        for procNomToy in procsToUseNomToy:
                            # store already here one fake histogram, so we don't have to load it multiple times
                            filename_nominalForData_FAKENomToy = pathPlotting.replace("YEAR",year).replace("SYSTEMATIC","Nominal").replace("ADDNAME","")
                            fIn_nominalForData_FAKENomToy = ROOT.TFile(filename_nominalForData_FAKENomToy, "READ")
                            hVar_FAKENomToy = fIn_nominalForData_FAKENomToy.Get(year+"/"+channel+"/"+"data_obs"+"/"+category+"_"+observable)
                            ROOT.SetOwnership(hVar_FAKENomToy, True)
                            hVar_FAKENomToy = CreateFakeHistoFromData(hVar_FAKENomToy, year+"/"+channel+"/"+"data_obs"+"/"+category+"_"+observable)
                            ROOT.SetOwnership(hVar_FAKENomToy, True)
                            if not isNEvents:
                                hVarNomToy = fIn.Get(year+"/"+channel+"/"+procNomToy+"/"+category+"_"+observable)
                                ROOT.SetOwnership(hVar, True)
                                if not hVarNomToy:
                                    hVarNomToy = hVar_FAKENomToy.Clone()
                                    hVarNomToy.SetName(year+"/"+channel+"/"+"data_obs"+"/"+category+"_"+observable)
                                if checkBinning:
                                    hVarNomToy = aux.rebin(hVarNomToy, binAr, scale=False)
                            else:
                                hVarNomToy = fIn.Get(year+"/"+channel+"/"+procNomToy+"/"+category+"_"+"NEvents")
                                ROOT.SetOwnership(hVarNomToy, True)
                                if not hVarNomToy:
                                    hVarNomToy = hVar_FAKENomToy.Clone()
                                    hVarNomToy.SetName(year+"/"+channel+"/"+"data_obs"+"/"+category+"_"+observable)
                            if scaleYields:
                                hVarNomToy.Scale(scaleYields)
                            if scaleTTBB:
                                if "tt_bb" in procNomToy or "tt_bj" in procNomToy or "tt_2b" in procNomToy:
                                    hVarNomToy.Scale(scaleTTBB)
                            if scaleTTH:
                                if "ttH_" in procNomToy:
                                    hVarNomToy.Scale(scaleTTH)
                            if "ttH_hcc" in procNomToy and scaleTTHcc:
                                hVarNomToy.Scale(scaleTTHcc)
                            fixHistogram(hVarNomToy, False)
                            ROOT.SetOwnership(hVarNomToy, True)
                            if h_pseudoData is not None:
                                h_pseudoData = aux.addHists(h_pseudoData, hVarNomToy)
                            else:
                                h_pseudoData = hVarNomToy
                            h_pseudoData.SetName(year+"/"+channel+"/"+"data_obs"+"/"+category+"_"+observable)
                            h_pseudoData.SetDirectory(0)
                            ROOT.SetOwnership(h_pseudoData, True)
                            fIn_nominalForData_FAKENomToy.Close()
                        outChannelName = getCombineChannelName(year+"/"+channel+"/"+"data_obs"+"/"+category+"_"+observable_orig)
                        outRootFile.cd()
                        if not outRootFile.GetDirectory(outChannelName):
                            outRootFile.mkdir(outChannelName)
                        outRootFile.cd()
                        outRootFile.cd(outChannelName)
                        h_pseudoData.Write("data_obs")
            outRootFile.Close()
            fIn.Close()
        else:
            if verbosity > 2: print ("-- Nominal exists. Skip!")

    # hadd to real file:
    if not os.path.exists(outRootFilePath):
        command = "hadd -j 10 "+outRootFilePath+" "+outputFolder+"/SystShapes*/*.root"
        print ("Calling ", command)
        subprocess.call(command, shell = True)
    else:
        print ("Final file exists. Skip!")


allsystematics= {
    "CMS_scale_j_absolute" : [s for s in signals]+[b for b in bkgs],
    "CMS_scale_j_bbec1" : [s for s in signals]+[b for b in bkgs],
    "CMS_scale_j_ec2" : [s for s in signals]+[b for b in bkgs],
    "CMS_scale_j_hf" : [s for s in signals]+[b for b in bkgs],
    "CMS_scale_j_relativebal" : [s for s in signals]+[b for b in bkgs],
    "CMS_scale_j_flavorqcd" : [s for s in signals]+[b for b in bkgs],
    "CMS_eff_e" : [s for s in signals]+[b for b in bkgs],
    "CMS_eff_m" : [s for s in signals]+[b for b in bkgs],

    "CMS_ttHcc_flavTag_JER" : [s for s in signals]+[b for b in bkgs],
    "CMS_ttHcc_flavTag_JES" : [s for s in signals]+[b for b in bkgs],
    "CMS_ttHcc_flavTag_LHEScaleWeight_muF_ttbar" : [s for s in signals]+[b for b in bkgs],
    "CMS_ttHcc_flavTag_LHEScaleWeight_muF_wjets" : [s for s in signals]+[b for b in bkgs],
    "CMS_ttHcc_flavTag_LHEScaleWeight_muF_zjets" : [s for s in signals]+[b for b in bkgs],
    "CMS_ttHcc_flavTag_LHEScaleWeight_muR_ttbar" : [s for s in signals]+[b for b in bkgs],
    "CMS_ttHcc_flavTag_LHEScaleWeight_muR_wjets" : [s for s in signals]+[b for b in bkgs],
    "CMS_ttHcc_flavTag_LHEScaleWeight_muR_zjets" : [s for s in signals]+[b for b in bkgs],
    # "CMS_ttHcc_flavTag_PSWeightFSR" : [s for s in signals]+[b for b in bkgs],
    "CMS_ttHcc_flavTag_PSWeightFSR_ttbar" : [s for s in signals]+[b for b in bkgs],
    "CMS_ttHcc_flavTag_PSWeightFSR_wjets" : [s for s in signals]+[b for b in bkgs],
    "CMS_ttHcc_flavTag_PSWeightFSR_zjets" : [s for s in signals]+[b for b in bkgs],
    # "CMS_ttHcc_flavTag_PSWeightISR" : [s for s in signals]+[b for b in bkgs],
    "CMS_ttHcc_flavTag_PSWeightISR_ttbar" : [s for s in signals]+[b for b in bkgs],
    "CMS_ttHcc_flavTag_PSWeightISR_wjets" : [s for s in signals]+[b for b in bkgs],
    "CMS_ttHcc_flavTag_PSWeightISR_zjets" : [s for s in signals]+[b for b in bkgs],
    "CMS_ttHcc_flavTag_PUWeight" : [s for s in signals]+[b for b in bkgs],
    "CMS_ttHcc_flavTag_XSec_WJets_b" : [s for s in signals]+[b for b in bkgs],
    "CMS_ttHcc_flavTag_XSec_WJets_c" : [s for s in signals]+[b for b in bkgs],
    "CMS_ttHcc_flavTag_XSec_ZJets_b" : [s for s in signals]+[b for b in bkgs],
    "CMS_ttHcc_flavTag_XSec_ZJets_c" : [s for s in signals]+[b for b in bkgs],

    "CMS_LHE_weights_scale_muF_st" : ["singlet"],
    "CMS_LHE_weights_scale_muF_ttW" : ["ttW"],
    "CMS_LHE_weights_scale_muF_ttbb" : ["tt_bb"],
    "CMS_LHE_weights_scale_muF_ttbbdps" : ["tt_bbDPS"],
    "CMS_LHE_weights_scale_muF_tt2b" : ["tt_2b"],
    # "CMS_LHE_weights_scale_muF_ttbb" : ["tt_bb_j3","tt_bb_j4","tt_bb_j5"],
    "CMS_LHE_weights_scale_muF_ttbj" : ["tt_bj"],
    "CMS_LHE_weights_scale_muF_ttbjdps" : ["tt_bjDPS"],
    # "CMS_LHE_weights_scale_muF_ttbj" : ["tt_bj_j2","tt_bj_j3","tt_bj_j4"],
    "CMS_LHE_weights_scale_muF_ttcc" : ["tt_cc"],
    "CMS_LHE_weights_scale_muF_tt2c" : ["tt_2c"],
    "CMS_LHE_weights_scale_muF_ttcj" : ["tt_cj"],
    "CMS_LHE_weights_scale_muF_ttlf" : ["tt_lf"],
    "CMS_LHE_weights_scale_muF_ttH" : ["ttH_hbb","ttH_hcc", "ttH_hww", "ttH_hzz", "ttH_hgg", "ttH_htt", "ttH_hother"],
    "CMS_LHE_weights_scale_muF_ttZ" : ["ttZ_zbb", "ttZ_zcc", "ttZ_zother"],
    "CMS_LHE_weights_scale_muF_twz" : ["twz"],
    # "CMS_LHE_weights_scale_muF_W" : ["wjets"],
    # "CMS_LHE_weights_scale_muF_Z" : ["zjets"],

    "CMS_LHE_weights_scale_muR_st" : ["singlet"],
    "CMS_LHE_weights_scale_muR_ttW" : ["ttW"],
    "CMS_LHE_weights_scale_muR_ttbb" : ["tt_bb"],
    "CMS_LHE_weights_scale_muR_ttbbdps" : ["tt_bbDPS"],
    "CMS_LHE_weights_scale_muR_tt2b" : ["tt_2b"],
    # "CMS_LHE_weights_scale_muR_ttbb" : ["tt_bb_j3","tt_bb_j4","tt_bb_j5"],
    "CMS_LHE_weights_scale_muR_ttbj" : ["tt_bj"],
    "CMS_LHE_weights_scale_muR_ttbjdps" : ["tt_bjDPS"],
    # "CMS_LHE_weights_scale_muR_ttbj" : ["tt_bj_j2","tt_bj_j3","tt_bj_j4"],
    "CMS_LHE_weights_scale_muR_ttcc" : ["tt_cc"],
    "CMS_LHE_weights_scale_muR_tt2c" : ["tt_2c"],
    "CMS_LHE_weights_scale_muR_ttcj" : ["tt_cj"],
    "CMS_LHE_weights_scale_muR_ttlf" : ["tt_lf"],
    "CMS_LHE_weights_scale_muR_ttH" : ["ttH_hbb","ttH_hcc", "ttH_hww", "ttH_hzz", "ttH_hgg", "ttH_htt", "ttH_hother"],
    "CMS_LHE_weights_scale_muR_ttZ" : ["ttZ_zbb", "ttZ_zcc", "ttZ_zother"],
    "CMS_LHE_weights_scale_muR_twz" : ["twz"],
    # "CMS_LHE_weights_scale_muR_W" : ["wjets"],
    # "CMS_LHE_weights_scale_muR_Z" : ["zjets"],

    "CMS_ttHcc_HDAMPML_ttcc" : ["tt_cc"],
    "CMS_ttHcc_HDAMPML_tt2c" : ["tt_2c"],
    "CMS_ttHcc_HDAMPML_ttcj" : ["tt_cj"],
    "CMS_ttHcc_HDAMPML_ttlf" : ["tt_lf"],

    # "PDF_1" : ["ttH_hbb","ttH_hcc", "ttH_hww", "ttH_hzz", "ttH_hgg", "ttH_htt", "ttH_hother", "ttZ_zbb", "ttZ_zcc", "ttZ_zother", "tt_lf", "tt_cc", "tt_cj", "ttW", "twz"],
    "PDF_ALPHAS" : ["ttH_hbb","ttH_hcc", "ttH_hww", "ttH_hzz", "ttH_hgg", "ttH_htt", "ttH_hother", "ttZ_zbb", "ttZ_zcc", "ttZ_zother", "tt_lf", "tt_cc", "tt_2c", "tt_cj", "ttW", "twz"],

    # "PDF_ALPHAS" : [s for s in signals]+["ttbarbgFromLjets","ttbarbgFromHadronic","ttbarbgFromDilepton","ttbarsignal_BKGNoAddJet"],
    # "MATCH" : [s for s in signals]+["ttbarbgFromLjets","ttbarbgFromHadronic","ttbarbgFromDilepton","ttbarsignal_BKGNoAddJet"],
    # "CMS_topptWeight" : ["tt_bb", "tt_bj", "tt_cc", "tt_cj", "tt_lf"]

    # "CMS_topptWeight" : ["tt_bb_j3","tt_bb_j4","tt_bb_j5",
    #                     "tt_bj_j2","tt_bj_j3","tt_bj_j4",
    #                     "tt_cc", "tt_cj", "tt_lf"]
}

# for indexPDF in range(1,51):
#     # print ("adding ","PDF_"+str(indexPDF))
#     allsystematics.update({"PDF_"+str(indexPDF): ["ttH_hbb","ttH_hcc", "ttH_hww", "ttH_hzz", "ttH_hgg", "ttH_htt", "ttH_hother", "ttZ_zbb", "ttZ_zcc", "ttZ_zother", "tt_lf", "tt_cc", "tt_cj", "ttW", "twz"]})
#     allsystematics.update({"PDF_TTBB_"+str(indexPDF): ["tt_bb", "tt_bj", "tt_2b"]})
# #     allsystematics.update({"PDF_"+str(indexPDF)+"Down": [s for s in signals]+["ttbarbg","ttbarsignal_BKGNoAddJet"]})

# uncorrelatedFromNominalSystematics = [
#     "ERDON", "ERDONRETUNE", "GLUONMOVETUNE", "MATCH", "UETUNE", "MASS"
# ]

# uncorrelatedFromNominalSystematicsTotal = [
#     "MATCH", "UETUNE", "MASS"
# ]
# uncorrelatedFromNominalSystematicsUpType = [
#     "ERDON", "ERDONRETUNE", "GLUONMOVETUNE"
# ]

predefinedNuisanceGroups_ = {
    "JESCORR" : [
            "CMS_scale_j_absolute", "CMS_scale_j_bbec1", "CMS_scale_j_ec2", "CMS_scale_j_hf", "CMS_scale_j_flavorqcd", "CMS_scale_j_relativebal"
            ],
    "JESUNCORR" : [
            "CMS_scale_j_absolute_2015","CMS_scale_j_absolute_2016", "CMS_scale_j_absolute_2017", "CMS_scale_j_absolute_2018",
            "CMS_scale_j_bbec1_2015","CMS_scale_j_bbec1_2016", "CMS_scale_j_bbec1_2017", "CMS_scale_j_bbec1_2018",
            "CMS_scale_j_ec2_2015","CMS_scale_j_ec2_2016", "CMS_scale_j_ec2_2017", "CMS_scale_j_ec2_2018",
            "CMS_scale_j_hf_2015","CMS_scale_j_hf_2016", "CMS_scale_j_hf_2017", "CMS_scale_j_hf_2018",
            "CMS_scale_j_relativesample_2015", "CMS_scale_j_relativesample_2016", "CMS_scale_j_relativesample_2017", "CMS_scale_j_relativesample_2018",
            ],
    "JER" : [
            "CMS_res_j_2015","CMS_res_j_2016", "CMS_res_j_017", "CMS_res_j_2018",
            ],
    "MET" : [
            "CMS_met_2015","CMS_met_2016", "CMS_met_2017", "CMS_met_2018"
            ],
    "FTAGCORR" : [
            "CMS_ttHcc_flavTag_JER", "CMS_ttHcc_flavTag_JES", "CMS_ttHcc_flavTag_LHEScaleWeight_muF_ttbar", "CMS_ttHcc_flavTag_LHEScaleWeight_muF_wjets", "CMS_ttHcc_flavTag_LHEScaleWeight_muF_zjets",
            "CMS_ttHcc_flavTag_LHEScaleWeight_muR_ttbar", "CMS_ttHcc_flavTag_LHEScaleWeight_muR_wjets", "CMS_ttHcc_flavTag_LHEScaleWeight_muR_zjets",
            # "CMS_ttHcc_flavTag_PSWeightFSR",
            "CMS_ttHcc_flavTag_PSWeightFSR_ttbar","CMS_ttHcc_flavTag_PSWeightFSR_wjets","CMS_ttHcc_flavTag_PSWeightFSR_zjets",
            # "CMS_ttHcc_flavTag_PSWeightISR",
            "CMS_ttHcc_flavTag_PSWeightISR_ttbar","CMS_ttHcc_flavTag_PSWeightISR_wjets","CMS_ttHcc_flavTag_PSWeightISR_zjets",
            "CMS_ttHcc_flavTag_PUWeight", "CMS_ttHcc_flavTag_XSec_WJets_b", "CMS_ttHcc_flavTag_XSec_WJets_c", "CMS_ttHcc_flavTag_XSec_ZJets_b",
            "CMS_ttHcc_flavTag_XSec_ZJets_c"
            ],
    "FTAGUNCORR" : [
            "CMS_ttHcc_flavTag_stat_flavB_C0_2015","CMS_ttHcc_flavTag_stat_flavB_C0_2016","CMS_ttHcc_flavTag_stat_flavB_C0_2017","CMS_ttHcc_flavTag_stat_flavB_C0_2018",
            "CMS_ttHcc_flavTag_stat_flavB_C1_2015","CMS_ttHcc_flavTag_stat_flavB_C1_2016","CMS_ttHcc_flavTag_stat_flavB_C1_2017","CMS_ttHcc_flavTag_stat_flavB_C1_2018",
            "CMS_ttHcc_flavTag_stat_flavB_C2_2015","CMS_ttHcc_flavTag_stat_flavB_C2_2016","CMS_ttHcc_flavTag_stat_flavB_C2_2017","CMS_ttHcc_flavTag_stat_flavB_C2_2018",
            "CMS_ttHcc_flavTag_stat_flavB_C3_2015","CMS_ttHcc_flavTag_stat_flavB_C3_2016","CMS_ttHcc_flavTag_stat_flavB_C3_2017","CMS_ttHcc_flavTag_stat_flavB_C3_2018",
            "CMS_ttHcc_flavTag_stat_flavB_C4_2015","CMS_ttHcc_flavTag_stat_flavB_C4_2016","CMS_ttHcc_flavTag_stat_flavB_C4_2017","CMS_ttHcc_flavTag_stat_flavB_C4_2018",
            "CMS_ttHcc_flavTag_stat_flavB_B0_2015","CMS_ttHcc_flavTag_stat_flavB_B0_2016","CMS_ttHcc_flavTag_stat_flavB_B0_2017","CMS_ttHcc_flavTag_stat_flavB_B0_2018",
            "CMS_ttHcc_flavTag_stat_flavB_B1_2015","CMS_ttHcc_flavTag_stat_flavB_B1_2016","CMS_ttHcc_flavTag_stat_flavB_B1_2017","CMS_ttHcc_flavTag_stat_flavB_B1_2018",
            "CMS_ttHcc_flavTag_stat_flavB_B2_2015","CMS_ttHcc_flavTag_stat_flavB_B2_2016","CMS_ttHcc_flavTag_stat_flavB_B2_2017","CMS_ttHcc_flavTag_stat_flavB_B2_2018",
            "CMS_ttHcc_flavTag_stat_flavB_B3_2015","CMS_ttHcc_flavTag_stat_flavB_B3_2016","CMS_ttHcc_flavTag_stat_flavB_B3_2017","CMS_ttHcc_flavTag_stat_flavB_B3_2018",
            "CMS_ttHcc_flavTag_stat_flavB_B4_2015","CMS_ttHcc_flavTag_stat_flavB_B4_2016","CMS_ttHcc_flavTag_stat_flavB_B4_2017","CMS_ttHcc_flavTag_stat_flavB_B4_2018",
            "CMS_ttHcc_flavTag_stat_flavC_C0_2015","CMS_ttHcc_flavTag_stat_flavC_C0_2016","CMS_ttHcc_flavTag_stat_flavC_C0_2017","CMS_ttHcc_flavTag_stat_flavC_C0_2018",
            "CMS_ttHcc_flavTag_stat_flavC_C1_2015","CMS_ttHcc_flavTag_stat_flavC_C1_2016","CMS_ttHcc_flavTag_stat_flavC_C1_2017","CMS_ttHcc_flavTag_stat_flavC_C1_2018",
            "CMS_ttHcc_flavTag_stat_flavC_C2_2015","CMS_ttHcc_flavTag_stat_flavC_C2_2016","CMS_ttHcc_flavTag_stat_flavC_C2_2017","CMS_ttHcc_flavTag_stat_flavC_C2_2018",
            "CMS_ttHcc_flavTag_stat_flavC_C3_2015","CMS_ttHcc_flavTag_stat_flavC_C3_2016","CMS_ttHcc_flavTag_stat_flavC_C3_2017","CMS_ttHcc_flavTag_stat_flavC_C3_2018",
            "CMS_ttHcc_flavTag_stat_flavC_C4_2015","CMS_ttHcc_flavTag_stat_flavC_C4_2016","CMS_ttHcc_flavTag_stat_flavC_C4_2017","CMS_ttHcc_flavTag_stat_flavC_C4_2018",
            "CMS_ttHcc_flavTag_stat_flavC_B0_2015","CMS_ttHcc_flavTag_stat_flavC_B0_2016","CMS_ttHcc_flavTag_stat_flavC_B0_2017","CMS_ttHcc_flavTag_stat_flavC_B0_2018",
            "CMS_ttHcc_flavTag_stat_flavC_B1_2015","CMS_ttHcc_flavTag_stat_flavC_B1_2016","CMS_ttHcc_flavTag_stat_flavC_B1_2017","CMS_ttHcc_flavTag_stat_flavC_B1_2018",
            "CMS_ttHcc_flavTag_stat_flavC_B2_2015","CMS_ttHcc_flavTag_stat_flavC_B2_2016","CMS_ttHcc_flavTag_stat_flavC_B2_2017","CMS_ttHcc_flavTag_stat_flavC_B2_2018",
            "CMS_ttHcc_flavTag_stat_flavC_B3_2015","CMS_ttHcc_flavTag_stat_flavC_B3_2016","CMS_ttHcc_flavTag_stat_flavC_B3_2017","CMS_ttHcc_flavTag_stat_flavC_B3_2018",
            "CMS_ttHcc_flavTag_stat_flavC_B4_2015","CMS_ttHcc_flavTag_stat_flavC_B4_2016","CMS_ttHcc_flavTag_stat_flavC_B4_2017","CMS_ttHcc_flavTag_stat_flavC_B4_2018",
            "CMS_ttHcc_flavTag_stat_flavL_C0_2015","CMS_ttHcc_flavTag_stat_flavL_C0_2016","CMS_ttHcc_flavTag_stat_flavL_C0_2017","CMS_ttHcc_flavTag_stat_flavL_C0_2018",
            "CMS_ttHcc_flavTag_stat_flavL_C1_2015","CMS_ttHcc_flavTag_stat_flavL_C1_2016","CMS_ttHcc_flavTag_stat_flavL_C1_2017","CMS_ttHcc_flavTag_stat_flavL_C1_2018",
            "CMS_ttHcc_flavTag_stat_flavL_C2_2015","CMS_ttHcc_flavTag_stat_flavL_C2_2016","CMS_ttHcc_flavTag_stat_flavL_C2_2017","CMS_ttHcc_flavTag_stat_flavL_C2_2018",
            "CMS_ttHcc_flavTag_stat_flavL_C3_2015","CMS_ttHcc_flavTag_stat_flavL_C3_2016","CMS_ttHcc_flavTag_stat_flavL_C3_2017","CMS_ttHcc_flavTag_stat_flavL_C3_2018",
            "CMS_ttHcc_flavTag_stat_flavL_C4_2015","CMS_ttHcc_flavTag_stat_flavL_C4_2016","CMS_ttHcc_flavTag_stat_flavL_C4_2017","CMS_ttHcc_flavTag_stat_flavL_C4_2018",
            "CMS_ttHcc_flavTag_stat_flavL_B0_2015","CMS_ttHcc_flavTag_stat_flavL_B0_2016","CMS_ttHcc_flavTag_stat_flavL_B0_2017","CMS_ttHcc_flavTag_stat_flavL_B0_2018",
            "CMS_ttHcc_flavTag_stat_flavL_B1_2015","CMS_ttHcc_flavTag_stat_flavL_B1_2016","CMS_ttHcc_flavTag_stat_flavL_B1_2017","CMS_ttHcc_flavTag_stat_flavL_B1_2018",
            "CMS_ttHcc_flavTag_stat_flavL_B2_2015","CMS_ttHcc_flavTag_stat_flavL_B2_2016","CMS_ttHcc_flavTag_stat_flavL_B2_2017","CMS_ttHcc_flavTag_stat_flavL_B2_2018",
            "CMS_ttHcc_flavTag_stat_flavL_B3_2015","CMS_ttHcc_flavTag_stat_flavL_B3_2016","CMS_ttHcc_flavTag_stat_flavL_B3_2017","CMS_ttHcc_flavTag_stat_flavL_B3_2018",
            "CMS_ttHcc_flavTag_stat_flavL_B4_2015","CMS_ttHcc_flavTag_stat_flavL_B4_2016","CMS_ttHcc_flavTag_stat_flavL_B4_2017","CMS_ttHcc_flavTag_stat_flavL_B4_2018",
            ],
    "MUON" : [
            "CMS_eff_m"
            ],
    "ELE": [
            "CMS_eff_e",
            ],
    "PU": [
            "CMS_pileup_2015", "CMS_pileup_2016", "CMS_pileup_2017", "CMS_pileup_2018"
            ],
    "TRIG": [
            "CMS_ttHcc_trigeff_ee_2015","CMS_ttHcc_trigeff_ee_2016", "CMS_ttHcc_trigeff_ee_2017", "CMS_ttHcc_trigeff_ee_2018",
            "CMS_ttHcc_trigeff_em_2015", "CMS_ttHcc_trigeff_em_2016", "CMS_ttHcc_trigeff_em_2017", "CMS_ttHcc_trigeff_em_2018",
            "CMS_ttHcc_trigeff_mm_2015","CMS_ttHcc_trigeff_mm_2016", "CMS_ttHcc_trigeff_mm_2017", "CMS_ttHcc_trigeff_mm_2018",
            ],
    # "PDF": [
    #         # "PDF_"+str(i) for i in range(50)
    #         # "PDF_"+str(i) for i in range(1,50)
    #         "PDF_"+str(i) for i in range(1,100)
    #         ],

}
predefinedNuisanceGroups_["JES"] = predefinedNuisanceGroups_["JESCORR"] + predefinedNuisanceGroups_["JESUNCORR"]
predefinedNuisanceGroups_["FTAG"] = predefinedNuisanceGroups_["FTAGCORR"] + predefinedNuisanceGroups_["FTAGUNCORR"]
predefinedNuisanceGroups_["LEPTON"] = predefinedNuisanceGroups_["MUON"] + predefinedNuisanceGroups_["ELE"]
predefinedNuisanceGroups_["JETS"] = predefinedNuisanceGroups_["JES"] + predefinedNuisanceGroups_["JER"]
predefinedNuisanceGroups_["EXP"] = predefinedNuisanceGroups_["JES"] + predefinedNuisanceGroups_["JER"] + \
    predefinedNuisanceGroups_["ELE"] + predefinedNuisanceGroups_["MUON"] + predefinedNuisanceGroups_["FTAG"] + \
    predefinedNuisanceGroups_["TRIG"] + predefinedNuisanceGroups_["PU"] + predefinedNuisanceGroups_["LEPTON"] + predefinedNuisanceGroups_["MET"] \
    + ["L1PREFIRING"]
predefinedNuisanceGroups_["THEORY_TT"] = \
    ["PDF_ALPHAS",  "MERENSCALE", "MEFACSCALE"] + ["PSSCALE_WEIGHT_4", "PSSCALE_WEIGHT_5"]+["TOP_PT"]
predefinedNuisanceGroups_["THEORY_TT_SCALE"] = ["MERENSCALE", "MEFACSCALE"]
predefinedNuisanceGroups_["THEORY_TT_ISR"] = ["PSSCALE_WEIGHT_4"]
predefinedNuisanceGroups_["THEORY_TT_FSR"] = ["PSSCALE_WEIGHT_5"]
predefinedNuisanceGroups_["THEORY_TT_TOP_PT"] = ["TOP_PT"]
predefinedNuisanceGroups_["THEORY_ST"] = ["MERENSCALE_ST", "MEFACSCALE_ST"] + ["PSSCALE_WEIGHT_ST_4", "PSSCALE_WEIGHT_ST_5"]
predefinedNuisanceGroups_["THEORY_ST_SCALE"] = ["MERENSCALE_ST", "MEFACSCALE_ST"]
predefinedNuisanceGroups_["THEORY_ST_ISR"] = ["PSSCALE_WEIGHT_ST_4"]
predefinedNuisanceGroups_["THEORY_ST_FSR"] = ["PSSCALE_WEIGHT_ST_5"]
predefinedNuisanceGroups_["THEORY_DY"] = ["MERENSCALE_Z", "MEFACSCALE_Z"]
predefinedNuisanceGroups_["THEORY"] = predefinedNuisanceGroups_["THEORY_DY"] + predefinedNuisanceGroups_["THEORY_ST"] + predefinedNuisanceGroups_["THEORY_TT"]
predefinedNuisanceGroups_["MODEL"] = predefinedNuisanceGroups_["THEORY_DY"]+predefinedNuisanceGroups_["THEORY_ST"]+ predefinedNuisanceGroups_["THEORY_TT"] + ["MATCH", "UETUNE"]
predefinedNuisanceGroups_["HDAMP"] = ["MATCH"]


predefinedNuisanceGroups = predefinedNuisanceGroups_

def updateNuisanceGroups(years, addPDF=True):
    predefinedNuisanceGroups__ = predefinedNuisanceGroups.copy()
    for group in predefinedNuisanceGroups__:
        toRemove = []
        for nuisance in predefinedNuisanceGroups__[group]:
            keep = False
            missingYears = ["2015", "2016", "2017", "2018"]
            missingYears = [x for x in missingYears if x not in years]
            for year_ in missingYears:
                if year_ in nuisance:
                    toRemove.append(nuisance)
        predefinedNuisanceGroups__[group] = [x for x in predefinedNuisanceGroups__[group] if x not in toRemove]
    if addPDF:
        predefinedNuisanceGroups__.update({"PDF": [
                # "PDF_"+str(i) for i in range(50)
                # "PDF_"+str(i) for i in range(1,50)
                "PDF_"+str(i) for i in range(1,100)
                ]+["PDF_ALPHAS"]})
        predefinedNuisanceGroups__["THEORY_TT"] = predefinedNuisanceGroups__["THEORY_TT"]+predefinedNuisanceGroups__["PDF"]
        predefinedNuisanceGroups__["THEORY"] = predefinedNuisanceGroups__["THEORY_DY"] + predefinedNuisanceGroups__["THEORY_ST"] + predefinedNuisanceGroups__["THEORY_TT"]
    # predefinedNuisanceGroups__["DYRate"] = ["DYRate0Jet", "DYRate1Jet", "DYRate2Jet","DYRate3Jet","DYRate0BJet","DYRate1BJet","DYRate2BJet"]
    predefinedNuisanceGroups__["DYRate"] = ["DYRate1Jet", "DYRate2Jet","DYRate3Jet","DYRate1BJet","DYRate2BJet"]
    predefinedNuisanceGroups__["ST_NORM"] = ["norm_singlet"]
    # predefinedNuisanceGroups__["OTHER_NORM"] = ["norm_other"]
    predefinedNuisanceGroups__["OTHER_NORM"] = ["norm_wjets", "norm_ttbarX","norm_diboson"]
    predefinedNuisanceGroups__["TTBKG_NORM"] = ["norm_tt"]
    predefinedNuisanceGroups__["TT_NORM"] = ["rateTT0Jet","norm_tt"]
    # predefinedNuisanceGroups__["BKG_NORM"] = predefinedNuisanceGroups__["DYRate"]+["norm_tt","norm_other","norm_singlet"]
    predefinedNuisanceGroups__["BKG_NORM"] = predefinedNuisanceGroups__["DYRate"]+["norm_tt","norm_wjets", "norm_ttbarX","norm_diboson","norm_singlet"]
    predefinedNuisanceGroups__["ALLBKG_NORM"] = ["rateTT0Jet"]+predefinedNuisanceGroups__["BKG_NORM"]
    # predefinedNuisanceGroups__["LUMINOSITYGROUP"] = ["lumi2016","lumi2017","lumi2018","lumi1718","lumiCorr"]
    predefinedNuisanceGroups__["LUMINOSITYGROUP"] = ["lumi2016"]
    predefinedNuisanceGroups__["TT0JETNORM"] = ["rateTT0Jet"]
    predefinedNuisanceGroups__["TOPMASS"] = ["MASS"]
    return predefinedNuisanceGroups__.copy()



def updateSystematics(year, addMet=True, addShapeNuisances = None, addPDF=False, use4FS = True, use2muF = False, addModels = False, usePSBreakdown = False):
    systs_=allsystematics.copy()
    if addPDF:
        # for indexPDF in range(1,101):
        #     systs_.update({"PDF_"+str(indexPDF): [s for s in signals]+["ttbarbgFromLjets","ttbarbgFromHadronic","ttbarbgFromDilepton","ttbarsignal_BKGNoAddJet"]})
        for indexPDF in range(1,51):
            systs_.update({"PDF_"+str(indexPDF): ["ttH_hbb","ttH_hcc", "ttH_hww", "ttH_hzz", "ttH_hgg", "ttH_htt", "ttH_hother", "ttZ_zbb", "ttZ_zcc", "ttZ_zother", "tt_lf", "tt_cc", "tt_2c", "tt_cj", "ttW", "twz"]})
            if use4FS and not use2muF:
                systs_.update({"PDF_TTBB_MERGED": ["tt_bb4FS", "tt_bj4FS", "tt_2b4FS"]})
            elif use4FS and use2muF:
                systs_.update({"PDF_TTBB_MERGED": ["tt_bb4FS2mu", "tt_bj4FS2mu", "tt_2b4FS2mu"]})
            else:
                systs_.update({"PDF_"+str(indexPDF): ["tt_bb", "tt_bj", "tt_2b"]})
    if addMet:
        if year != "FR2":
            systs_.update({"CMS_met_"+year : [s for s in signals]+[b for b in bkgs]})
        else:
            systs_.update({"CMS_met_"+"2015" : [s for s in signals]+[b for b in bkgs]})
            systs_.update({"CMS_met_"+"2016" : [s for s in signals]+[b for b in bkgs]})
            systs_.update({"CMS_met_"+"2017" : [s for s in signals]+[b for b in bkgs]})
            systs_.update({"CMS_met_"+"2018" : [s for s in signals]+[b for b in bkgs]})

    if usePSBreakdown:

        systs_.update({"CMS_PS_fsr_ttbbdps" : ["tt_bbDPS"]})
        systs_.update({"CMS_PS_fsr_ttbjdps" : ["tt_bjDPS"]})
        systs_.update({"CMS_PS_isr_ttbbdps" : ["tt_bbDPS"]})
        systs_.update({"CMS_PS_isr_ttbjdps" : ["tt_bjDPS"]})

        systs_.update({"CMS_PS_fsr_g2gg_ren_st" : ["singlet"]})
        systs_.update({"CMS_PS_fsr_g2qq_ren_st" : ["singlet"]})
        systs_.update({"CMS_PS_fsr_q2qg_ren_st" : ["singlet"]})
        systs_.update({"CMS_PS_fsr_x2xg_ren_st" : ["singlet"]})
        systs_.update({"CMS_PS_fsr_g2gg_cns_st" : ["singlet"]})
        systs_.update({"CMS_PS_fsr_g2qq_cns_st" : ["singlet"]})
        systs_.update({"CMS_PS_fsr_q2qg_cns_st" : ["singlet"]})
        systs_.update({"CMS_PS_fsr_x2xg_cns_st" : ["singlet"]})

        systs_.update({"CMS_PS_fsr_g2gg_ren_ttW" : ["ttW"]})
        systs_.update({"CMS_PS_fsr_g2qq_ren_ttW" : ["ttW"]})
        systs_.update({"CMS_PS_fsr_q2qg_ren_ttW" : ["ttW"]})
        systs_.update({"CMS_PS_fsr_x2xg_ren_ttW" : ["ttW"]})
        systs_.update({"CMS_PS_fsr_g2gg_cns_ttW" : ["ttW"]})
        systs_.update({"CMS_PS_fsr_g2qq_cns_ttW" : ["ttW"]})
        systs_.update({"CMS_PS_fsr_q2qg_cns_ttW" : ["ttW"]})
        systs_.update({"CMS_PS_fsr_x2xg_cns_ttW" : ["ttW"]})

        systs_.update({"CMS_PS_fsr_g2gg_ren_ttbb" : ["tt_bb"]})
        systs_.update({"CMS_PS_fsr_g2qq_ren_ttbb" : ["tt_bb"]})
        systs_.update({"CMS_PS_fsr_q2qg_ren_ttbb" : ["tt_bb"]})
        systs_.update({"CMS_PS_fsr_x2xg_ren_ttbb" : ["tt_bb"]})
        systs_.update({"CMS_PS_fsr_g2gg_cns_ttbb" : ["tt_bb"]})
        systs_.update({"CMS_PS_fsr_g2qq_cns_ttbb" : ["tt_bb"]})
        systs_.update({"CMS_PS_fsr_q2qg_cns_ttbb" : ["tt_bb"]})
        systs_.update({"CMS_PS_fsr_x2xg_cns_ttbb" : ["tt_bb"]})

        systs_.update({"CMS_PS_fsr_g2gg_ren_tt2b" : ["tt_2b"]})
        systs_.update({"CMS_PS_fsr_g2qq_ren_tt2b" : ["tt_2b"]})
        systs_.update({"CMS_PS_fsr_q2qg_ren_tt2b" : ["tt_2b"]})
        systs_.update({"CMS_PS_fsr_x2xg_ren_tt2b" : ["tt_2b"]})
        systs_.update({"CMS_PS_fsr_g2gg_cns_tt2b" : ["tt_2b"]})
        systs_.update({"CMS_PS_fsr_g2qq_cns_tt2b" : ["tt_2b"]})
        systs_.update({"CMS_PS_fsr_q2qg_cns_tt2b" : ["tt_2b"]})
        systs_.update({"CMS_PS_fsr_x2xg_cns_tt2b" : ["tt_2b"]})

        systs_.update({"CMS_PS_fsr_g2gg_ren_ttbj" : ["tt_bj"]})
        systs_.update({"CMS_PS_fsr_g2qq_ren_ttbj" : ["tt_bj"]})
        systs_.update({"CMS_PS_fsr_q2qg_ren_ttbj" : ["tt_bj"]})
        systs_.update({"CMS_PS_fsr_x2xg_ren_ttbj" : ["tt_bj"]})
        systs_.update({"CMS_PS_fsr_g2gg_cns_ttbj" : ["tt_bj"]})
        systs_.update({"CMS_PS_fsr_g2qq_cns_ttbj" : ["tt_bj"]})
        systs_.update({"CMS_PS_fsr_q2qg_cns_ttbj" : ["tt_bj"]})
        systs_.update({"CMS_PS_fsr_x2xg_cns_ttbj" : ["tt_bj"]})

        systs_.update({"CMS_PS_fsr_g2gg_ren_ttcc" : ["tt_cc"]})
        systs_.update({"CMS_PS_fsr_g2qq_ren_ttcc" : ["tt_cc"]})
        systs_.update({"CMS_PS_fsr_q2qg_ren_ttcc" : ["tt_cc"]})
        systs_.update({"CMS_PS_fsr_x2xg_ren_ttcc" : ["tt_cc"]})
        systs_.update({"CMS_PS_fsr_g2gg_cns_ttcc" : ["tt_cc"]})
        systs_.update({"CMS_PS_fsr_g2qq_cns_ttcc" : ["tt_cc"]})
        systs_.update({"CMS_PS_fsr_q2qg_cns_ttcc" : ["tt_cc"]})
        systs_.update({"CMS_PS_fsr_x2xg_cns_ttcc" : ["tt_cc"]})

        systs_.update({"CMS_PS_fsr_g2gg_ren_tt2c" : ["tt_2c"]})
        systs_.update({"CMS_PS_fsr_g2qq_ren_tt2c" : ["tt_2c"]})
        systs_.update({"CMS_PS_fsr_q2qg_ren_tt2c" : ["tt_2c"]})
        systs_.update({"CMS_PS_fsr_x2xg_ren_tt2c" : ["tt_2c"]})
        systs_.update({"CMS_PS_fsr_g2gg_cns_tt2c" : ["tt_2c"]})
        systs_.update({"CMS_PS_fsr_g2qq_cns_tt2c" : ["tt_2c"]})
        systs_.update({"CMS_PS_fsr_q2qg_cns_tt2c" : ["tt_2c"]})
        systs_.update({"CMS_PS_fsr_x2xg_cns_tt2c" : ["tt_2c"]})

        systs_.update({"CMS_PS_fsr_g2gg_ren_ttcj" : ["tt_cj"]})
        systs_.update({"CMS_PS_fsr_g2qq_ren_ttcj" : ["tt_cj"]})
        systs_.update({"CMS_PS_fsr_q2qg_ren_ttcj" : ["tt_cj"]})
        systs_.update({"CMS_PS_fsr_x2xg_ren_ttcj" : ["tt_cj"]})
        systs_.update({"CMS_PS_fsr_g2gg_cns_ttcj" : ["tt_cj"]})
        systs_.update({"CMS_PS_fsr_g2qq_cns_ttcj" : ["tt_cj"]})
        systs_.update({"CMS_PS_fsr_q2qg_cns_ttcj" : ["tt_cj"]})
        systs_.update({"CMS_PS_fsr_x2xg_cns_ttcj" : ["tt_cj"]})

        systs_.update({"CMS_PS_fsr_g2gg_ren_ttlf" : ["tt_lf"]})
        systs_.update({"CMS_PS_fsr_g2qq_ren_ttlf" : ["tt_lf"]})
        systs_.update({"CMS_PS_fsr_q2qg_ren_ttlf" : ["tt_lf"]})
        systs_.update({"CMS_PS_fsr_x2xg_ren_ttlf" : ["tt_lf"]})
        systs_.update({"CMS_PS_fsr_g2gg_cns_ttlf" : ["tt_lf"]})
        systs_.update({"CMS_PS_fsr_g2qq_cns_ttlf" : ["tt_lf"]})
        systs_.update({"CMS_PS_fsr_q2qg_cns_ttlf" : ["tt_lf"]})
        systs_.update({"CMS_PS_fsr_x2xg_cns_ttlf" : ["tt_lf"]})

        systs_.update({"CMS_PS_fsr_g2gg_ren_ttH" : ["ttH_hbb","ttH_hcc", "ttH_hww", "ttH_hzz", "ttH_hgg", "ttH_htt", "ttH_hother"]})
        systs_.update({"CMS_PS_fsr_g2qq_ren_ttH" : ["ttH_hbb","ttH_hcc", "ttH_hww", "ttH_hzz", "ttH_hgg", "ttH_htt", "ttH_hother"]})
        systs_.update({"CMS_PS_fsr_q2qg_ren_ttH" : ["ttH_hbb","ttH_hcc", "ttH_hww", "ttH_hzz", "ttH_hgg", "ttH_htt", "ttH_hother"]})
        systs_.update({"CMS_PS_fsr_x2xg_ren_ttH" : ["ttH_hbb","ttH_hcc", "ttH_hww", "ttH_hzz", "ttH_hgg", "ttH_htt", "ttH_hother"]})
        systs_.update({"CMS_PS_fsr_g2gg_cns_ttH" : ["ttH_hbb","ttH_hcc", "ttH_hww", "ttH_hzz", "ttH_hgg", "ttH_htt", "ttH_hother"]})
        systs_.update({"CMS_PS_fsr_g2qq_cns_ttH" : ["ttH_hbb","ttH_hcc", "ttH_hww", "ttH_hzz", "ttH_hgg", "ttH_htt", "ttH_hother"]})
        systs_.update({"CMS_PS_fsr_q2qg_cns_ttH" : ["ttH_hbb","ttH_hcc", "ttH_hww", "ttH_hzz", "ttH_hgg", "ttH_htt", "ttH_hother"]})
        systs_.update({"CMS_PS_fsr_x2xg_cns_ttH" : ["ttH_hbb","ttH_hcc", "ttH_hww", "ttH_hzz", "ttH_hgg", "ttH_htt", "ttH_hother"]})

        systs_.update({"CMS_PS_fsr_g2gg_ren_ttZ" : ["ttZ_zbb", "ttZ_zcc", "ttZ_zother"]})
        systs_.update({"CMS_PS_fsr_g2qq_ren_ttZ" : ["ttZ_zbb", "ttZ_zcc", "ttZ_zother"]})
        systs_.update({"CMS_PS_fsr_q2qg_ren_ttZ" : ["ttZ_zbb", "ttZ_zcc", "ttZ_zother"]})
        systs_.update({"CMS_PS_fsr_x2xg_ren_ttZ" : ["ttZ_zbb", "ttZ_zcc", "ttZ_zother"]})
        systs_.update({"CMS_PS_fsr_g2gg_cns_ttZ" : ["ttZ_zbb", "ttZ_zcc", "ttZ_zother"]})
        systs_.update({"CMS_PS_fsr_g2qq_cns_ttZ" : ["ttZ_zbb", "ttZ_zcc", "ttZ_zother"]})
        systs_.update({"CMS_PS_fsr_q2qg_cns_ttZ" : ["ttZ_zbb", "ttZ_zcc", "ttZ_zother"]})
        systs_.update({"CMS_PS_fsr_x2xg_cns_ttZ" : ["ttZ_zbb", "ttZ_zcc", "ttZ_zother"]})

        systs_.update({"CMS_PS_fsr_g2gg_ren_twz" : ["twz"]})
        systs_.update({"CMS_PS_fsr_g2qq_ren_twz" : ["twz"]})
        systs_.update({"CMS_PS_fsr_q2qg_ren_twz" : ["twz"]})
        systs_.update({"CMS_PS_fsr_x2xg_ren_twz" : ["twz"]})
        systs_.update({"CMS_PS_fsr_g2gg_cns_twz" : ["twz"]})
        systs_.update({"CMS_PS_fsr_g2qq_cns_twz" : ["twz"]})
        systs_.update({"CMS_PS_fsr_q2qg_cns_twz" : ["twz"]})
        systs_.update({"CMS_PS_fsr_x2xg_cns_twz" : ["twz"]})

        systs_.update({"CMS_PS_isr_g2gg_ren_st" : ["singlet"]})
        systs_.update({"CMS_PS_isr_g2qq_ren_st" : ["singlet"]})
        systs_.update({"CMS_PS_isr_q2qg_ren_st" : ["singlet"]})
        systs_.update({"CMS_PS_isr_x2xg_ren_st" : ["singlet"]})
        systs_.update({"CMS_PS_isr_g2gg_cns_st" : ["singlet"]})
        systs_.update({"CMS_PS_isr_g2qq_cns_st" : ["singlet"]})
        systs_.update({"CMS_PS_isr_q2qg_cns_st" : ["singlet"]})
        systs_.update({"CMS_PS_isr_x2xg_cns_st" : ["singlet"]})

        systs_.update({"CMS_PS_isr_g2gg_ren_ttW" : ["ttW"]})
        systs_.update({"CMS_PS_isr_g2qq_ren_ttW" : ["ttW"]})
        systs_.update({"CMS_PS_isr_q2qg_ren_ttW" : ["ttW"]})
        systs_.update({"CMS_PS_isr_x2xg_ren_ttW" : ["ttW"]})
        systs_.update({"CMS_PS_isr_g2gg_cns_ttW" : ["ttW"]})
        systs_.update({"CMS_PS_isr_g2qq_cns_ttW" : ["ttW"]})
        systs_.update({"CMS_PS_isr_q2qg_cns_ttW" : ["ttW"]})
        systs_.update({"CMS_PS_isr_x2xg_cns_ttW" : ["ttW"]})

        systs_.update({"CMS_PS_isr_g2gg_ren_ttbb" : ["tt_bb"]})
        systs_.update({"CMS_PS_isr_g2qq_ren_ttbb" : ["tt_bb"]})
        systs_.update({"CMS_PS_isr_q2qg_ren_ttbb" : ["tt_bb"]})
        systs_.update({"CMS_PS_isr_x2xg_ren_ttbb" : ["tt_bb"]})
        systs_.update({"CMS_PS_isr_g2gg_cns_ttbb" : ["tt_bb"]})
        systs_.update({"CMS_PS_isr_g2qq_cns_ttbb" : ["tt_bb"]})
        systs_.update({"CMS_PS_isr_q2qg_cns_ttbb" : ["tt_bb"]})
        systs_.update({"CMS_PS_isr_x2xg_cns_ttbb" : ["tt_bb"]})

        systs_.update({"CMS_PS_isr_g2gg_ren_tt2b" : ["tt_2b"]})
        systs_.update({"CMS_PS_isr_g2qq_ren_tt2b" : ["tt_2b"]})
        systs_.update({"CMS_PS_isr_q2qg_ren_tt2b" : ["tt_2b"]})
        systs_.update({"CMS_PS_isr_x2xg_ren_tt2b" : ["tt_2b"]})
        systs_.update({"CMS_PS_isr_g2gg_cns_tt2b" : ["tt_2b"]})
        systs_.update({"CMS_PS_isr_g2qq_cns_tt2b" : ["tt_2b"]})
        systs_.update({"CMS_PS_isr_q2qg_cns_tt2b" : ["tt_2b"]})
        systs_.update({"CMS_PS_isr_x2xg_cns_tt2b" : ["tt_2b"]})

        systs_.update({"CMS_PS_isr_g2gg_ren_ttbj" : ["tt_bj"]})
        systs_.update({"CMS_PS_isr_g2qq_ren_ttbj" : ["tt_bj"]})
        systs_.update({"CMS_PS_isr_q2qg_ren_ttbj" : ["tt_bj"]})
        systs_.update({"CMS_PS_isr_x2xg_ren_ttbj" : ["tt_bj"]})
        systs_.update({"CMS_PS_isr_g2gg_cns_ttbj" : ["tt_bj"]})
        systs_.update({"CMS_PS_isr_g2qq_cns_ttbj" : ["tt_bj"]})
        systs_.update({"CMS_PS_isr_q2qg_cns_ttbj" : ["tt_bj"]})
        systs_.update({"CMS_PS_isr_x2xg_cns_ttbj" : ["tt_bj"]})

        systs_.update({"CMS_PS_isr_g2gg_ren_ttcc" : ["tt_cc"]})
        systs_.update({"CMS_PS_isr_g2qq_ren_ttcc" : ["tt_cc"]})
        systs_.update({"CMS_PS_isr_q2qg_ren_ttcc" : ["tt_cc"]})
        systs_.update({"CMS_PS_isr_x2xg_ren_ttcc" : ["tt_cc"]})
        systs_.update({"CMS_PS_isr_g2gg_cns_ttcc" : ["tt_cc"]})
        systs_.update({"CMS_PS_isr_g2qq_cns_ttcc" : ["tt_cc"]})
        systs_.update({"CMS_PS_isr_q2qg_cns_ttcc" : ["tt_cc"]})
        systs_.update({"CMS_PS_isr_x2xg_cns_ttcc" : ["tt_cc"]})

        systs_.update({"CMS_PS_isr_g2gg_ren_tt2c" : ["tt_2c"]})
        systs_.update({"CMS_PS_isr_g2qq_ren_tt2c" : ["tt_2c"]})
        systs_.update({"CMS_PS_isr_q2qg_ren_tt2c" : ["tt_2c"]})
        systs_.update({"CMS_PS_isr_x2xg_ren_tt2c" : ["tt_2c"]})
        systs_.update({"CMS_PS_isr_g2gg_cns_tt2c" : ["tt_2c"]})
        systs_.update({"CMS_PS_isr_g2qq_cns_tt2c" : ["tt_2c"]})
        systs_.update({"CMS_PS_isr_q2qg_cns_tt2c" : ["tt_2c"]})
        systs_.update({"CMS_PS_isr_x2xg_cns_tt2c" : ["tt_2c"]})

        systs_.update({"CMS_PS_isr_g2gg_ren_ttcj" : ["tt_cj"]})
        systs_.update({"CMS_PS_isr_g2qq_ren_ttcj" : ["tt_cj"]})
        systs_.update({"CMS_PS_isr_q2qg_ren_ttcj" : ["tt_cj"]})
        systs_.update({"CMS_PS_isr_x2xg_ren_ttcj" : ["tt_cj"]})
        systs_.update({"CMS_PS_isr_g2gg_cns_ttcj" : ["tt_cj"]})
        systs_.update({"CMS_PS_isr_g2qq_cns_ttcj" : ["tt_cj"]})
        systs_.update({"CMS_PS_isr_q2qg_cns_ttcj" : ["tt_cj"]})
        systs_.update({"CMS_PS_isr_x2xg_cns_ttcj" : ["tt_cj"]})

        systs_.update({"CMS_PS_isr_g2gg_ren_ttlf" : ["tt_lf"]})
        systs_.update({"CMS_PS_isr_g2qq_ren_ttlf" : ["tt_lf"]})
        systs_.update({"CMS_PS_isr_q2qg_ren_ttlf" : ["tt_lf"]})
        systs_.update({"CMS_PS_isr_x2xg_ren_ttlf" : ["tt_lf"]})
        systs_.update({"CMS_PS_isr_g2gg_cns_ttlf" : ["tt_lf"]})
        systs_.update({"CMS_PS_isr_g2qq_cns_ttlf" : ["tt_lf"]})
        systs_.update({"CMS_PS_isr_q2qg_cns_ttlf" : ["tt_lf"]})
        systs_.update({"CMS_PS_isr_x2xg_cns_ttlf" : ["tt_lf"]})

        systs_.update({"CMS_PS_isr_g2gg_ren_ttH" : ["ttH_hbb","ttH_hcc", "ttH_hww", "ttH_hzz", "ttH_hgg", "ttH_htt", "ttH_hother"]})
        systs_.update({"CMS_PS_isr_g2qq_ren_ttH" : ["ttH_hbb","ttH_hcc", "ttH_hww", "ttH_hzz", "ttH_hgg", "ttH_htt", "ttH_hother"]})
        systs_.update({"CMS_PS_isr_q2qg_ren_ttH" : ["ttH_hbb","ttH_hcc", "ttH_hww", "ttH_hzz", "ttH_hgg", "ttH_htt", "ttH_hother"]})
        systs_.update({"CMS_PS_isr_x2xg_ren_ttH" : ["ttH_hbb","ttH_hcc", "ttH_hww", "ttH_hzz", "ttH_hgg", "ttH_htt", "ttH_hother"]})
        systs_.update({"CMS_PS_isr_g2gg_cns_ttH" : ["ttH_hbb","ttH_hcc", "ttH_hww", "ttH_hzz", "ttH_hgg", "ttH_htt", "ttH_hother"]})
        systs_.update({"CMS_PS_isr_g2qq_cns_ttH" : ["ttH_hbb","ttH_hcc", "ttH_hww", "ttH_hzz", "ttH_hgg", "ttH_htt", "ttH_hother"]})
        systs_.update({"CMS_PS_isr_q2qg_cns_ttH" : ["ttH_hbb","ttH_hcc", "ttH_hww", "ttH_hzz", "ttH_hgg", "ttH_htt", "ttH_hother"]})
        systs_.update({"CMS_PS_isr_x2xg_cns_ttH" : ["ttH_hbb","ttH_hcc", "ttH_hww", "ttH_hzz", "ttH_hgg", "ttH_htt", "ttH_hother"]})

        systs_.update({"CMS_PS_isr_g2gg_ren_ttZ" : ["ttZ_zbb", "ttZ_zcc", "ttZ_zother"]})
        systs_.update({"CMS_PS_isr_g2qq_ren_ttZ" : ["ttZ_zbb", "ttZ_zcc", "ttZ_zother"]})
        systs_.update({"CMS_PS_isr_q2qg_ren_ttZ" : ["ttZ_zbb", "ttZ_zcc", "ttZ_zother"]})
        systs_.update({"CMS_PS_isr_x2xg_ren_ttZ" : ["ttZ_zbb", "ttZ_zcc", "ttZ_zother"]})
        systs_.update({"CMS_PS_isr_g2gg_cns_ttZ" : ["ttZ_zbb", "ttZ_zcc", "ttZ_zother"]})
        systs_.update({"CMS_PS_isr_g2qq_cns_ttZ" : ["ttZ_zbb", "ttZ_zcc", "ttZ_zother"]})
        systs_.update({"CMS_PS_isr_q2qg_cns_ttZ" : ["ttZ_zbb", "ttZ_zcc", "ttZ_zother"]})
        systs_.update({"CMS_PS_isr_x2xg_cns_ttZ" : ["ttZ_zbb", "ttZ_zcc", "ttZ_zother"]})

        systs_.update({"CMS_PS_isr_g2gg_ren_twz" : ["twz"]})
        systs_.update({"CMS_PS_isr_g2qq_ren_twz" : ["twz"]})
        systs_.update({"CMS_PS_isr_q2qg_ren_twz" : ["twz"]})
        systs_.update({"CMS_PS_isr_x2xg_ren_twz" : ["twz"]})
        systs_.update({"CMS_PS_isr_g2gg_cns_twz" : ["twz"]})
        systs_.update({"CMS_PS_isr_g2qq_cns_twz" : ["twz"]})
        systs_.update({"CMS_PS_isr_q2qg_cns_twz" : ["twz"]})
        systs_.update({"CMS_PS_isr_x2xg_cns_twz" : ["twz"]})

    else:
        systs_.update({"CMS_PS_fsr_st" : ["singlet"]})
        systs_.update({"CMS_PS_fsr_ttW" : ["ttW"]})
        systs_.update({"CMS_PS_fsr_ttbb" : ["tt_bb"]})
        systs_.update({"CMS_PS_fsr_ttbbdps" : ["tt_bbDPS"]})
        systs_.update({"CMS_PS_fsr_tt2b" : ["tt_2b"]})
        systs_.update({"CMS_PS_fsr_ttbj" : ["tt_bj"]})
        systs_.update({"CMS_PS_fsr_ttbjdps" : ["tt_bjDPS"]})
        systs_.update({"CMS_PS_fsr_ttcc" : ["tt_cc"]})
        systs_.update({"CMS_PS_fsr_tt2c" : ["tt_2c"]})
        systs_.update({"CMS_PS_fsr_ttcj" : ["tt_cj"]})
        systs_.update({"CMS_PS_fsr_ttlf" : ["tt_lf"]})
        systs_.update({"CMS_PS_fsr_ttH" : ["ttH_hbb","ttH_hcc", "ttH_hww", "ttH_hzz", "ttH_hgg", "ttH_htt", "ttH_hother"]})
        systs_.update({"CMS_PS_fsr_ttZ" : ["ttZ_zbb", "ttZ_zcc", "ttZ_zother"]})
        systs_.update({"CMS_PS_fsr_twz" : ["twz"]})

        systs_.update({"CMS_PS_isr_st" : ["singlet"]})
        systs_.update({"CMS_PS_isr_ttW" : ["ttW"]})
        systs_.update({"CMS_PS_isr_ttbb" : ["tt_bb"]})
        systs_.update({"CMS_PS_isr_ttbbdps" : ["tt_bbDPS"]})
        systs_.update({"CMS_PS_isr_tt2b" : ["tt_2b"]})
        systs_.update({"CMS_PS_isr_ttbj" : ["tt_bj"]})
        systs_.update({"CMS_PS_isr_ttbjdps" : ["tt_bjDPS"]})
        systs_.update({"CMS_PS_isr_ttcc" : ["tt_cc"]})
        systs_.update({"CMS_PS_isr_tt2c" : ["tt_2c"]})
        systs_.update({"CMS_PS_isr_ttcj" : ["tt_cj"]})
        systs_.update({"CMS_PS_isr_ttlf" : ["tt_lf"]})
        systs_.update({"CMS_PS_isr_ttH" : ["ttH_hbb","ttH_hcc", "ttH_hww", "ttH_hzz", "ttH_hgg", "ttH_htt", "ttH_hother"]})
        systs_.update({"CMS_PS_isr_ttZ" : ["ttZ_zbb", "ttZ_zcc", "ttZ_zother"]})
        systs_.update({"CMS_PS_isr_twz" : ["twz"]})


    if addModels and not use2muF:
        # systs_.update({"AMCATNLOFXFX" : [s for s in signals]+[b for b in bkgs]})
        # systs_.update({"AMCATNLOFXFX_TTBB" : ["tt_bb4FS"]})
        # systs_.update({"AMCATNLOFXFX_TTBJ" : ["tt_bj4FS"]})
        # systs_.update({"AMCATNLOFXFX_TT2B" : ["tt_2b4FS"]})
        # systs_.update({"AMCATNLOFXFX_TTCC" : ["tt_cc"]})
        # systs_.update({"AMCATNLOFXFX_TTCJ" : ["tt_cj"]})
        # systs_.update({"AMCATNLOFXFX_TT2C" : ["tt_2c"]})
        # systs_.update({"AMCATNLOFXFX_TTLF" : ["tt_lf"]})
        # systs_.update({"HERWIG_TTBB" : ["tt_bb4FS"]})
        # systs_.update({"HERWIG_TTBJ" : ["tt_bj4FS"]})
        # systs_.update({"HERWIG_TT2B" : ["tt_2b4FS"]})
        # systs_.update({"HERWIG_TTCC" : ["tt_cc"]})
        # systs_.update({"HERWIG_TTCJ" : ["tt_cj"]})
        # systs_.update({"HERWIG_TT2C" : ["tt_2c"]})
        # systs_.update({"HERWIG_TTLF" : ["tt_lf"]})
        # systs_.update({"FIVEFS_TTBB" : ["tt_bb4FS"]})
        # systs_.update({"FIVEFS_TTBJ" : ["tt_bj4FS"]})
        # systs_.update({"FIVEFS_TT2B" : ["tt_2b4FS"]})
        systs_.update({"FIVEFS" : ["tt_bb4FS", "tt_bj4FS", "tt_2b4FS"]})
        # systs_.update({"HERWIG" : [s for s in signals]+[b for b in bkgs]})

    if addModels and use2muF:
        # systs_.update({"AMCATNLOFXFX_TTBB" : ["tt_bb4FS2mu"]})
        # systs_.update({"AMCATNLOFXFX_TTBJ" : ["tt_bj4FS2mu"]})
        # systs_.update({"AMCATNLOFXFX_TT2B" : ["tt_2b4FS2mu"]})
        # systs_.update({"AMCATNLOFXFX_TTCC" : ["tt_cc"]})
        # systs_.update({"AMCATNLOFXFX_TTCJ" : ["tt_cj"]})
        # systs_.update({"AMCATNLOFXFX_TT2C" : ["tt_2c"]})
        # systs_.update({"AMCATNLOFXFX_TTLF" : ["tt_lf"]})
        # systs_.update({"HERWIG_TTBB" : ["tt_bb4FS2mu"]})
        # systs_.update({"HERWIG_TTBJ" : ["tt_bj4FS2mu"]})
        # systs_.update({"HERWIG_TT2B" : ["tt_2b4FS2mu"]})
        # systs_.update({"HERWIG_TTCC" : ["tt_cc"]})
        # systs_.update({"HERWIG_TTCJ" : ["tt_cj"]})
        # systs_.update({"HERWIG_TT2C" : ["tt_2c"]})
        # systs_.update({"HERWIG_TTLF" : ["tt_lf"]})
        # systs_.update({"FIVEFS" : ["tt_bb4FS2mu", "tt_bj4FS2mu", "tt_2b4FS2mu"]})
        systs_.update({"FIVEFS2MU" : ["tt_bb4FS2mu", "tt_bj4FS2mu", "tt_2b4FS2mu"]})

    if addModels and not use4FS:
        systs_.update({"FOURFS" : ["tt_bb", "tt_bj", "tt_2b"]})

    if use4FS and not use2muF:
        for sys in systs_:
            currentKeys = systs_[sys]
            newKeys = currentKeys
            for idx in range(len(newKeys)):
                currentProc = newKeys[idx]
                newProc = currentProc
                if "tt_bb" in currentProc and not "4FS" in currentProc and not "DPS" in currentProc:
                    newProc = currentProc.replace("tt_bb", "tt_bb4FS")
                # print (currentProc, newProc)
                if "tt_bj" in currentProc and not "4FS" in currentProc and not "DPS" in currentProc:
                    newProc = currentProc.replace("tt_bj", "tt_bj4FS")
                if "tt_2b" in currentProc and not "4FS" in currentProc and not "DPS" in currentProc:
                    newProc = currentProc.replace("tt_2b", "tt_2b4FS")
                # if currentProc == "tt_bb":
                #     newProc = "tt_bb4FS"
                # if currentProc == "tt_bj":
                #     newProc = "tt_bj4FS"
                newKeys[idx] = newProc
            systs_[sys] = newKeys

    if use4FS and use2muF:
        for sys in systs_:
            currentKeys = systs_[sys]
            newKeys = currentKeys
            for idx in range(len(newKeys)):
                currentProc = newKeys[idx]
                newProc = currentProc
                if "tt_bb" in currentProc and not "4FS2mu" in currentProc and not "DPS" in currentProc:
                    newProc = currentProc.replace("tt_bb", "tt_bb4FS2mu")
                if "tt_bj" in currentProc and not "4FS2mu" in currentProc and not "DPS" in currentProc:
                    newProc = currentProc.replace("tt_bj", "tt_bj4FS2mu")
                if "tt_2b" in currentProc and not "4FS2mu" in currentProc and not "DPS" in currentProc:
                    newProc = currentProc.replace("tt_2b", "tt_2b4FS2mu")
                newKeys[idx] = newProc
                # print (sys,newKeys)
            systs_[sys] = newKeys

    if year=="2015":
        systs_.update({"CMS_pileup_"+year : [s for s in signals]+[b for b in bkgs]})
        systs_.update({"CMS_res_j_"+year : [s for s in signals]+[b for b in bkgs]})
        systs_.update({"CMS_scale_j_absolute_"+year : [s for s in signals]+[b for b in bkgs]})
        systs_.update({"CMS_scale_j_bbec1_"+year : [s for s in signals]+[b for b in bkgs]})
        systs_.update({"CMS_scale_j_ec2_"+year : [s for s in signals]+[b for b in bkgs]})
        systs_.update({"CMS_scale_j_hf_"+year : [s for s in signals]+[b for b in bkgs]})
        systs_.update({"CMS_scale_j_relativesample_"+year : [s for s in signals]+[b for b in bkgs]})
        systs_.update({"CMS_ttHcc_trigeff_ee_"+year : [s for s in signals]+[b for b in bkgs]})
        systs_.update({"CMS_ttHcc_trigeff_em_"+year : [s for s in signals]+[b for b in bkgs]})
        systs_.update({"CMS_ttHcc_trigeff_mm_"+year : [s for s in signals]+[b for b in bkgs]})
        systs_.update({"CMS_ttHcc_trigeff_e_"+year : [s for s in signals]+[b for b in bkgs]})
        systs_.update({"CMS_ttHcc_trigeff_m_"+year : [s for s in signals]+[b for b in bkgs]})
        systs_.update({"CMS_ttHcc_trigeff_fhad_"+year : [s for s in signals]+[b for b in bkgs]})
        systs_.update({"CMS_met_"+year : [s for s in signals]+[b for b in bkgs]})
        systs_.update({"CMS_l1PrefiringWeight_"+year : [s for s in signals]+[b for b in bkgs]})
        systs_.update({"CMS_ttHcc_flavTag_stat_flavB_C0_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavB_C1_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavB_C2_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavB_C3_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavB_C4_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavB_B0_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavB_B1_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavB_B2_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavB_B3_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavB_B4_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavC_C0_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavC_C1_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavC_C2_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavC_C3_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavC_C4_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavC_B0_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavC_B1_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavC_B2_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavC_B3_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavC_B4_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavL_C0_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavL_C1_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavL_C2_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavL_C3_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavL_C4_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavL_B0_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavL_B1_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavL_B2_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavL_B3_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavL_B4_"+year : [s for s in signals]+[b for b in bkgs]}),
    if year=="2016":
        systs_.update({"CMS_pileup_"+year : [s for s in signals]+[b for b in bkgs]})
        systs_.update({"CMS_res_j_"+year : [s for s in signals]+[b for b in bkgs]})
        systs_.update({"CMS_scale_j_absolute_"+year : [s for s in signals]+[b for b in bkgs]})
        systs_.update({"CMS_scale_j_bbec1_"+year : [s for s in signals]+[b for b in bkgs]})
        systs_.update({"CMS_scale_j_ec2_"+year : [s for s in signals]+[b for b in bkgs]})
        systs_.update({"CMS_scale_j_hf_"+year : [s for s in signals]+[b for b in bkgs]})
        systs_.update({"CMS_scale_j_relativesample_"+year : [s for s in signals]+[b for b in bkgs]})
        systs_.update({"CMS_ttHcc_trigeff_ee_"+year : [s for s in signals]+[b for b in bkgs]})
        systs_.update({"CMS_ttHcc_trigeff_em_"+year : [s for s in signals]+[b for b in bkgs]})
        systs_.update({"CMS_ttHcc_trigeff_mm_"+year : [s for s in signals]+[b for b in bkgs]})
        systs_.update({"CMS_ttHcc_trigeff_e_"+year : [s for s in signals]+[b for b in bkgs]})
        systs_.update({"CMS_ttHcc_trigeff_m_"+year : [s for s in signals]+[b for b in bkgs]})
        systs_.update({"CMS_ttHcc_trigeff_fhad_"+year : [s for s in signals]+[b for b in bkgs]})
        systs_.update({"CMS_met_"+year : [s for s in signals]+[b for b in bkgs]})
        systs_.update({"CMS_l1PrefiringWeight_"+year : [s for s in signals]+[b for b in bkgs]})
        systs_.update({"CMS_ttHcc_flavTag_stat_flavB_C0_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavB_C1_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavB_C2_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavB_C3_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavB_C4_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavB_B0_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavB_B1_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavB_B2_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavB_B3_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavB_B4_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavC_C0_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavC_C1_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavC_C2_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavC_C3_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavC_C4_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavC_B0_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavC_B1_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavC_B2_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavC_B3_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavC_B4_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavL_C0_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavL_C1_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavL_C2_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavL_C3_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavL_C4_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavL_B0_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavL_B1_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavL_B2_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavL_B3_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavL_B4_"+year : [s for s in signals]+[b for b in bkgs]}),
    if year=="2017":
        systs_.update({"CMS_pileup_"+year : [s for s in signals]+[b for b in bkgs]})
        systs_.update({"CMS_res_j_"+year : [s for s in signals]+[b for b in bkgs]})
        systs_.update({"CMS_scale_j_absolute_"+year : [s for s in signals]+[b for b in bkgs]})
        systs_.update({"CMS_scale_j_bbec1_"+year : [s for s in signals]+[b for b in bkgs]})
        systs_.update({"CMS_scale_j_ec2_"+year : [s for s in signals]+[b for b in bkgs]})
        systs_.update({"CMS_scale_j_hf_"+year : [s for s in signals]+[b for b in bkgs]})
        systs_.update({"CMS_scale_j_relativesample_"+year : [s for s in signals]+[b for b in bkgs]})
        systs_.update({"CMS_ttHcc_trigeff_ee_"+year : [s for s in signals]+[b for b in bkgs]})
        systs_.update({"CMS_ttHcc_trigeff_em_"+year : [s for s in signals]+[b for b in bkgs]})
        systs_.update({"CMS_ttHcc_trigeff_mm_"+year : [s for s in signals]+[b for b in bkgs]})
        systs_.update({"CMS_ttHcc_trigeff_e_"+year : [s for s in signals]+[b for b in bkgs]})
        systs_.update({"CMS_ttHcc_trigeff_m_"+year : [s for s in signals]+[b for b in bkgs]})
        systs_.update({"CMS_ttHcc_trigeff_fhad_"+year : [s for s in signals]+[b for b in bkgs]})
        systs_.update({"CMS_met_"+year : [s for s in signals]+[b for b in bkgs]})
        systs_.update({"CMS_l1PrefiringWeight_"+year : [s for s in signals]+[b for b in bkgs]})
        systs_.update({"CMS_ttHcc_flavTag_stat_flavB_C0_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavB_C1_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavB_C2_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavB_C3_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavB_C4_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavB_B0_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavB_B1_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavB_B2_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavB_B3_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavB_B4_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavC_C0_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavC_C1_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavC_C2_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavC_C3_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavC_C4_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavC_B0_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavC_B1_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavC_B2_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavC_B3_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavC_B4_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavL_C0_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavL_C1_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavL_C2_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavL_C3_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavL_C4_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavL_B0_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavL_B1_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavL_B2_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavL_B3_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavL_B4_"+year : [s for s in signals]+[b for b in bkgs]}),
    if year=="2018":
        systs_.update({"CMS_scale_j_HEMIssue_2018_13TeV" : [s for s in signals]+[b for b in bkgs]})

        systs_.update({"CMS_pileup_"+year : [s for s in signals]+[b for b in bkgs]})
        systs_.update({"CMS_res_j_"+year : [s for s in signals]+[b for b in bkgs]})
        systs_.update({"CMS_scale_j_absolute_"+year : [s for s in signals]+[b for b in bkgs]})
        systs_.update({"CMS_scale_j_bbec1_"+year : [s for s in signals]+[b for b in bkgs]})
        systs_.update({"CMS_scale_j_ec2_"+year : [s for s in signals]+[b for b in bkgs]})
        systs_.update({"CMS_scale_j_hf_"+year : [s for s in signals]+[b for b in bkgs]})
        systs_.update({"CMS_scale_j_relativesample_"+year : [s for s in signals]+[b for b in bkgs]})
        systs_.update({"CMS_ttHcc_trigeff_ee_"+year : [s for s in signals]+[b for b in bkgs]})
        systs_.update({"CMS_ttHcc_trigeff_em_"+year : [s for s in signals]+[b for b in bkgs]})
        systs_.update({"CMS_ttHcc_trigeff_mm_"+year : [s for s in signals]+[b for b in bkgs]})
        systs_.update({"CMS_ttHcc_trigeff_e_"+year : [s for s in signals]+[b for b in bkgs]})
        systs_.update({"CMS_ttHcc_trigeff_m_"+year : [s for s in signals]+[b for b in bkgs]})
        systs_.update({"CMS_ttHcc_trigeff_fhad_"+year : [s for s in signals]+[b for b in bkgs]})
        systs_.update({"CMS_met_"+year : [s for s in signals]+[b for b in bkgs]})
        systs_.update({"CMS_l1PrefiringWeight_"+year : [s for s in signals]+[b for b in bkgs]})
        systs_.update({"CMS_ttHcc_flavTag_stat_flavB_C0_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavB_C1_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavB_C2_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavB_C3_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavB_C4_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavB_B0_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavB_B1_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavB_B2_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavB_B3_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavB_B4_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavC_C0_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavC_C1_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavC_C2_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavC_C3_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavC_C4_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavC_B0_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavC_B1_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavC_B2_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavC_B3_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavC_B4_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavL_C0_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavL_C1_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavL_C2_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavL_C3_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavL_C4_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavL_B0_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavL_B1_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavL_B2_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavL_B3_"+year : [s for s in signals]+[b for b in bkgs]}),
        systs_.update({"CMS_ttHcc_flavTag_stat_flavL_B4_"+year : [s for s in signals]+[b for b in bkgs]}),
    if year=="FR2":
        for y__ in ["2015", "2016", "2017", "2018"]:
            systs_.update({"CMS_pileup_"+y__ : [s for s in signals]+[b for b in bkgs]})
            systs_.update({"CMS_res_j_"+y__ : [s for s in signals]+[b for b in bkgs]})
            systs_.update({"CMS_scale_j_absolute_"+y__ : [s for s in signals]+[b for b in bkgs]})
            systs_.update({"CMS_scale_j_bbec1_"+y__ : [s for s in signals]+[b for b in bkgs]})
            systs_.update({"CMS_scale_j_ec2_"+y__ : [s for s in signals]+[b for b in bkgs]})
            systs_.update({"CMS_scale_j_hf_"+y__ : [s for s in signals]+[b for b in bkgs]})
            systs_.update({"CMS_scale_j_relativesample_"+y__ : [s for s in signals]+[b for b in bkgs]})
            systs_.update({"CMS_ttHcc_trigeff_ee_"+y__ : [s for s in signals]+[b for b in bkgs]})
            systs_.update({"CMS_ttHcc_trigeff_em_"+y__ : [s for s in signals]+[b for b in bkgs]})
            systs_.update({"CMS_ttHcc_trigeff_mm_"+y__ : [s for s in signals]+[b for b in bkgs]})
            systs_.update({"CMS_ttHcc_trigeff_e_"+y__ : [s for s in signals]+[b for b in bkgs]})
            systs_.update({"CMS_ttHcc_trigeff_m_"+y__ : [s for s in signals]+[b for b in bkgs]})
            systs_.update({"CMS_ttHcc_trigeff_fhad_"+y__ : [s for s in signals]+[b for b in bkgs]})
            systs_.update({"CMS_met_"+y__ : [s for s in signals]+[b for b in bkgs]})
            systs_.update({"CMS_l1PrefiringWeight_"+y__ : [s for s in signals]+[b for b in bkgs]})
            systs_.update({"CMS_ttHcc_flavTag_stat_flavB_C0_"+y__ : [s for s in signals]+[b for b in bkgs]}),
            systs_.update({"CMS_ttHcc_flavTag_stat_flavB_C1_"+y__ : [s for s in signals]+[b for b in bkgs]}),
            systs_.update({"CMS_ttHcc_flavTag_stat_flavB_C2_"+y__ : [s for s in signals]+[b for b in bkgs]}),
            systs_.update({"CMS_ttHcc_flavTag_stat_flavB_C3_"+y__ : [s for s in signals]+[b for b in bkgs]}),
            systs_.update({"CMS_ttHcc_flavTag_stat_flavB_C4_"+y__ : [s for s in signals]+[b for b in bkgs]}),
            systs_.update({"CMS_ttHcc_flavTag_stat_flavB_B0_"+y__ : [s for s in signals]+[b for b in bkgs]}),
            systs_.update({"CMS_ttHcc_flavTag_stat_flavB_B1_"+y__ : [s for s in signals]+[b for b in bkgs]}),
            systs_.update({"CMS_ttHcc_flavTag_stat_flavB_B2_"+y__ : [s for s in signals]+[b for b in bkgs]}),
            systs_.update({"CMS_ttHcc_flavTag_stat_flavB_B3_"+y__ : [s for s in signals]+[b for b in bkgs]}),
            systs_.update({"CMS_ttHcc_flavTag_stat_flavB_B4_"+y__ : [s for s in signals]+[b for b in bkgs]}),
            systs_.update({"CMS_ttHcc_flavTag_stat_flavC_C0_"+y__ : [s for s in signals]+[b for b in bkgs]}),
            systs_.update({"CMS_ttHcc_flavTag_stat_flavC_C1_"+y__ : [s for s in signals]+[b for b in bkgs]}),
            systs_.update({"CMS_ttHcc_flavTag_stat_flavC_C2_"+y__ : [s for s in signals]+[b for b in bkgs]}),
            systs_.update({"CMS_ttHcc_flavTag_stat_flavC_C3_"+y__ : [s for s in signals]+[b for b in bkgs]}),
            systs_.update({"CMS_ttHcc_flavTag_stat_flavC_C4_"+y__ : [s for s in signals]+[b for b in bkgs]}),
            systs_.update({"CMS_ttHcc_flavTag_stat_flavC_B0_"+y__ : [s for s in signals]+[b for b in bkgs]}),
            systs_.update({"CMS_ttHcc_flavTag_stat_flavC_B1_"+y__ : [s for s in signals]+[b for b in bkgs]}),
            systs_.update({"CMS_ttHcc_flavTag_stat_flavC_B2_"+y__ : [s for s in signals]+[b for b in bkgs]}),
            systs_.update({"CMS_ttHcc_flavTag_stat_flavC_B3_"+y__ : [s for s in signals]+[b for b in bkgs]}),
            systs_.update({"CMS_ttHcc_flavTag_stat_flavC_B4_"+y__ : [s for s in signals]+[b for b in bkgs]}),
            systs_.update({"CMS_ttHcc_flavTag_stat_flavL_C0_"+y__ : [s for s in signals]+[b for b in bkgs]}),
            systs_.update({"CMS_ttHcc_flavTag_stat_flavL_C1_"+y__ : [s for s in signals]+[b for b in bkgs]}),
            systs_.update({"CMS_ttHcc_flavTag_stat_flavL_C2_"+y__ : [s for s in signals]+[b for b in bkgs]}),
            systs_.update({"CMS_ttHcc_flavTag_stat_flavL_C3_"+y__ : [s for s in signals]+[b for b in bkgs]}),
            systs_.update({"CMS_ttHcc_flavTag_stat_flavL_C4_"+y__ : [s for s in signals]+[b for b in bkgs]}),
            systs_.update({"CMS_ttHcc_flavTag_stat_flavL_B0_"+y__ : [s for s in signals]+[b for b in bkgs]}),
            systs_.update({"CMS_ttHcc_flavTag_stat_flavL_B1_"+y__ : [s for s in signals]+[b for b in bkgs]}),
            systs_.update({"CMS_ttHcc_flavTag_stat_flavL_B2_"+y__ : [s for s in signals]+[b for b in bkgs]}),
            systs_.update({"CMS_ttHcc_flavTag_stat_flavL_B3_"+y__ : [s for s in signals]+[b for b in bkgs]}),
            systs_.update({"CMS_ttHcc_flavTag_stat_flavL_B4_"+y__ : [s for s in signals]+[b for b in bkgs]}),
            systs_.update({"CMS_scale_j_HEMIssue_2018_13TeV" : [s for s in signals]+[b for b in bkgs]})
    if year=="F16":
        for y__ in ["2015", "2016"]:
            systs_.update({"CMS_res_j_"+y__ : [s for s in signals]+[b for b in bkgs]})
            systs_.update({"CMS_scale_j_absolute_"+y__ : [s for s in signals]+[b for b in bkgs]})
            systs_.update({"CMS_scale_j_bbec1_"+y__ : [s for s in signals]+[b for b in bkgs]})
            systs_.update({"CMS_scale_j_ec2_"+y__ : [s for s in signals]+[b for b in bkgs]})
            systs_.update({"CMS_scale_j_hf_"+y__ : [s for s in signals]+[b for b in bkgs]})
            systs_.update({"JESRelativeSample"+y__ : [s for s in signals]+[b for b in bkgs]})
            systs_.update({"CMS_ttHcc_trigeff_ee_"+y__ : [s for s in signals]+[b for b in bkgs]})
            systs_.update({"CMS_ttHcc_trigeff_em_"+y__ : [s for s in signals]+[b for b in bkgs]})
            systs_.update({"CMS_ttHcc_trigeff_mm_"+y__ : [s for s in signals]+[b for b in bkgs]})
            systs_.update({"CMS_ttHcc_trigeff_e_"+y__ : [s for s in signals]+[b for b in bkgs]})
            systs_.update({"CMS_ttHcc_trigeff_m_"+y__ : [s for s in signals]+[b for b in bkgs]})
            systs_.update({"CMS_ttHcc_trigeff_fhad_"+y__ : [s for s in signals]+[b for b in bkgs]})
            systs_.update({"CMS_met_"+y__ : [s for s in signals]+[b for b in bkgs]})
            systs_.update({"CMS_l1PrefiringWeight_"+y__ : [s for s in signals]+[b for b in bkgs]})
            systs_.update({"CMS_ttHcc_flavTag_stat_flavB_C0_"+y__ : [s for s in signals]+[b for b in bkgs]}),
            systs_.update({"CMS_ttHcc_flavTag_stat_flavB_C1_"+y__ : [s for s in signals]+[b for b in bkgs]}),
            systs_.update({"CMS_ttHcc_flavTag_stat_flavB_C2_"+y__ : [s for s in signals]+[b for b in bkgs]}),
            systs_.update({"CMS_ttHcc_flavTag_stat_flavB_C3_"+y__ : [s for s in signals]+[b for b in bkgs]}),
            systs_.update({"CMS_ttHcc_flavTag_stat_flavB_C4_"+y__ : [s for s in signals]+[b for b in bkgs]}),
            systs_.update({"CMS_ttHcc_flavTag_stat_flavB_B0_"+y__ : [s for s in signals]+[b for b in bkgs]}),
            systs_.update({"CMS_ttHcc_flavTag_stat_flavB_B1_"+y__ : [s for s in signals]+[b for b in bkgs]}),
            systs_.update({"CMS_ttHcc_flavTag_stat_flavB_B2_"+y__ : [s for s in signals]+[b for b in bkgs]}),
            systs_.update({"CMS_ttHcc_flavTag_stat_flavB_B3_"+y__ : [s for s in signals]+[b for b in bkgs]}),
            systs_.update({"CMS_ttHcc_flavTag_stat_flavB_B4_"+y__ : [s for s in signals]+[b for b in bkgs]}),
            systs_.update({"CMS_ttHcc_flavTag_stat_flavC_C0_"+y__ : [s for s in signals]+[b for b in bkgs]}),
            systs_.update({"CMS_ttHcc_flavTag_stat_flavC_C1_"+y__ : [s for s in signals]+[b for b in bkgs]}),
            systs_.update({"CMS_ttHcc_flavTag_stat_flavC_C2_"+y__ : [s for s in signals]+[b for b in bkgs]}),
            systs_.update({"CMS_ttHcc_flavTag_stat_flavC_C3_"+y__ : [s for s in signals]+[b for b in bkgs]}),
            systs_.update({"CMS_ttHcc_flavTag_stat_flavC_C4_"+y__ : [s for s in signals]+[b for b in bkgs]}),
            systs_.update({"CMS_ttHcc_flavTag_stat_flavC_B0_"+y__ : [s for s in signals]+[b for b in bkgs]}),
            systs_.update({"CMS_ttHcc_flavTag_stat_flavC_B1_"+y__ : [s for s in signals]+[b for b in bkgs]}),
            systs_.update({"CMS_ttHcc_flavTag_stat_flavC_B2_"+y__ : [s for s in signals]+[b for b in bkgs]}),
            systs_.update({"CMS_ttHcc_flavTag_stat_flavC_B3_"+y__ : [s for s in signals]+[b for b in bkgs]}),
            systs_.update({"CMS_ttHcc_flavTag_stat_flavC_B4_"+y__ : [s for s in signals]+[b for b in bkgs]}),
            systs_.update({"CMS_ttHcc_flavTag_stat_flavL_C0_"+y__ : [s for s in signals]+[b for b in bkgs]}),
            systs_.update({"CMS_ttHcc_flavTag_stat_flavL_C1_"+y__ : [s for s in signals]+[b for b in bkgs]}),
            systs_.update({"CMS_ttHcc_flavTag_stat_flavL_C2_"+y__ : [s for s in signals]+[b for b in bkgs]}),
            systs_.update({"CMS_ttHcc_flavTag_stat_flavL_C3_"+y__ : [s for s in signals]+[b for b in bkgs]}),
            systs_.update({"CMS_ttHcc_flavTag_stat_flavL_C4_"+y__ : [s for s in signals]+[b for b in bkgs]}),
            systs_.update({"CMS_ttHcc_flavTag_stat_flavL_B0_"+y__ : [s for s in signals]+[b for b in bkgs]}),
            systs_.update({"CMS_ttHcc_flavTag_stat_flavL_B1_"+y__ : [s for s in signals]+[b for b in bkgs]}),
            systs_.update({"CMS_ttHcc_flavTag_stat_flavL_B2_"+y__ : [s for s in signals]+[b for b in bkgs]}),
            systs_.update({"CMS_ttHcc_flavTag_stat_flavL_B3_"+y__ : [s for s in signals]+[b for b in bkgs]}),
            systs_.update({"CMS_ttHcc_flavTag_stat_flavL_B4_"+y__ : [s for s in signals]+[b for b in bkgs]}),


    if addShapeNuisances is not None:
        for key in addShapeNuisances:
            systs_.update({key : addShapeNuisances[key]["processes"]})

    # sret = {"HERWIG_TTBB" : ["tt_bb4FS"]}
    # sret = {"FIVEFS_TTBB" : ["tt_bb4FS"]}
    # sret = {"FIVEFS" : ["tt_bb4FS", "tt_bj4FS", "tt_2b4FS"]}
    sret = systs_.copy()

    return sret

def ws_keys_from_set(workspace, set_key):
    """Description:
    """

    _keys = []

    if not workspace.InheritsFrom('RooWorkspace'):
        KILL('ws_keys_from_set -- typ of first argument does not inherit from RooWorkspace class')

    _tmp_argset = workspace.set(set_key)

    if _tmp_argset:

        _tmp_ite = _tmp_argset.createIterator()
        _tmp_ite.Reset()

        _tmp_obj = _tmp_ite.Next()

        while _tmp_obj:
            _keys += [_tmp_obj.GetName()]
            _tmp_obj = _tmp_ite.Next()

    return _keys
#---

def ws_keys(workspace, ws_method):
    """Description:
    """

    _keys = []

    if not workspace.InheritsFrom('RooWorkspace'):
        KILL('ws_keys -- typ of first argument does not inherit from RooWorkspace class')

    _tmp_objs = getattr(workspace, ws_method)()

    _tmp_ite = _tmp_objs.createIterator()
    _tmp_ite.Reset()

    _tmp_obj = _tmp_ite.Next()

    while _tmp_obj:
        _keys += [_tmp_obj.GetName()]
        _tmp_obj = _tmp_ite.Next()

    return _keys
#---

def ws_import(workspace, *arg):
    """Description:
    """

    if not workspace.InheritsFrom('RooWorkspace'):
       KILL('ws_import -- typ of first argument does not inherit from RooWorkspace class')

    _tmp_argN = len(arg)

    if _tmp_argN > 0:

        if not arg[0].InheritsFrom('TObject'):
            KILL('ws_import -- typ of second argument does not inherit from TObject class')

        if arg[0].InheritsFrom('RooAbsData'):

            _tmp_cmd1 = ROOT.RooCmdArg()

            if   _tmp_argN == 1: getattr(workspace, 'import')(arg[0]                                                        , _tmp_cmd1)
            elif _tmp_argN == 2: getattr(workspace, 'import')(arg[0], arg[1]                                                , _tmp_cmd1)
            elif _tmp_argN == 3: getattr(workspace, 'import')(arg[0], arg[1], arg[2]                                        , _tmp_cmd1)
            elif _tmp_argN == 4: getattr(workspace, 'import')(arg[0], arg[1], arg[2], arg[3]                                , _tmp_cmd1)
            elif _tmp_argN == 5: getattr(workspace, 'import')(arg[0], arg[1], arg[2], arg[3], arg[4]                        , _tmp_cmd1)
            elif _tmp_argN == 6: getattr(workspace, 'import')(arg[0], arg[1], arg[2], arg[3], arg[4], arg[5]                , _tmp_cmd1)
            elif _tmp_argN == 7: getattr(workspace, 'import')(arg[0], arg[1], arg[2], arg[3], arg[4], arg[5], arg[6]        , _tmp_cmd1)
            elif _tmp_argN == 8: getattr(workspace, 'import')(arg[0], arg[1], arg[2], arg[3], arg[4], arg[5], arg[6], arg[7], _tmp_cmd1)

            else: KILL('ws_import -- invalid number of arguments ('+str(1+_tmp_argN)+')')

        else:
            _tmp_cmd0 = ROOT.RooFit.RecycleConflictNodes()
            _tmp_cmd1 = ROOT.RooFit.Silence()

            if   _tmp_argN == 1: getattr(workspace, 'import')(arg[0]                                                , _tmp_cmd0, _tmp_cmd1)
            elif _tmp_argN == 2: getattr(workspace, 'import')(arg[0], arg[1]                                        , _tmp_cmd0, _tmp_cmd1)
            elif _tmp_argN == 3: getattr(workspace, 'import')(arg[0], arg[1], arg[2]                                , _tmp_cmd0, _tmp_cmd1)
            elif _tmp_argN == 4: getattr(workspace, 'import')(arg[0], arg[1], arg[2], arg[3]                        , _tmp_cmd0, _tmp_cmd1)
            elif _tmp_argN == 5: getattr(workspace, 'import')(arg[0], arg[1], arg[2], arg[3], arg[4]                , _tmp_cmd0, _tmp_cmd1)
            elif _tmp_argN == 6: getattr(workspace, 'import')(arg[0], arg[1], arg[2], arg[3], arg[4], arg[5]        , _tmp_cmd0, _tmp_cmd1)
            elif _tmp_argN == 7: getattr(workspace, 'import')(arg[0], arg[1], arg[2], arg[3], arg[4], arg[5], arg[6], _tmp_cmd0, _tmp_cmd1)

            else: KILL('ws_import -- invalid number of arguments ('+str(1+_tmp_argN)+')')

    else: KILL('ws_import -- invalid number of arguments ('+str(1+_tmp_argN)+')')

    return
#---
def ws_keys_all_parameters(workspace, model_config='ModelConfig', skip=[]):
    """Description:
    """
    if not workspace.InheritsFrom('RooWorkspace'):
       KILL('ws_keys_all_parameters -- typ of first argument does not inherit from RooWorkspace class')

    res = []

    config = workspace.genobj(model_config)
    pdfvars = config.GetPdf().getParameters(config.GetObservables())
    it = pdfvars.createIterator()
    var = it.Next()

    while var:
      if (var.GetName() not in skip) and (not var.isConstant()) and var.InheritsFrom('RooRealVar'):
         res.append(var.GetName())
      var = it.Next()
    return res
#---
