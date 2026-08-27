import ROOT
# from ROOT import *
from array import array
from utilities.include import *
from utilities.auxiliary   import *
import numpy as np
import json

def getPOIsAndNuisancesFromFile(filename):
    with open(filename) as json_file:
        data = json.load(json_file)
    POIs = data["POIs"]
    dictPOIs = {}
    dictConstraints = {}
    for entry in POIs:
        dictPOIs[entry["name"]] = entry["fit"]
    params = data["params"]
    for entry in params:
        dictConstraints[entry["name"]] = entry["fit"]
    # return dictPOIs,dictConstraints
    return dictConstraints

def getPOIsAndNuisancesFromFitFile(filename):
    fin = ROOT.TFile(filename)
    rfr = fin.Get("fit_mdf")
    # rfr.Print()
    all_pars = rfr.floatParsFinal()
    dictConstraints = {}
    for i in xrange(all_pars.getSize()):
        par = all_pars.at(i)
        # print '%s: %+.3f + %.3f - %.3f' % (par.GetName(), par.getVal(), par.getErrorHi(), par.getErrorLo())
        dictConstraints[par.GetName()] = [par.getErrorLo(),par.getVal(),par.getErrorHi()]
    return dictConstraints


def createGraphsFromConstraints(listN, names, dictConstraints):
    graphs = []
    nNuisance = len(listN)
    nGroups = len(names)
    max = 1000.

    # print (nNuisance, nGroups)

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
            # print iGroup,iNuisance,getYCoord(iGroup,iNuisance)
            if nuisance in dictConstraints[name]:
                x = dictConstraints[name][nuisance][1]
                exLow,exhigh = abs(dictConstraints[name][nuisance][0]),abs(dictConstraints[name][nuisance][2])
                gr.SetPoint(iNuisance-1, x, getYCoord(iGroup,iNuisance))
                gr.SetPointError(iNuisance-1, exLow, exhigh, 0., 0.)
        gr.GetXaxis().SetRangeUser(-1.,1.)
        graphs.append(gr)

    for iNuisance,nuisance in enumerate(listN):
        iNuisance = iNuisance+1
        c = (iNuisance*(empty+1))*bigstep - (stepsize*nGroups/2.)
        coordinates.append((c,nuisance))

    return graphs,coordinates

def main():
    basePath = "/eos/cms/store/cmst3/group/top/Vcb_trees/HTC_results/ForANv1/"

    # basename_ = "290426_correctedBnormalization_noPeterson"
    # basename_ = "070526_ge2bge1c"
    # basename_ = "070526_ge2bge1c_fix"
    basename_ = "070526_CRttWcbM0p2m0p8"
    # basename_ = "070526_ge2bge1c_fix_smoothed"
    # basename_ = "070526_CRttWcbM0p2m0p8_smoothed"

    ev_names = [
        "FitStudies_Datacards__simplified_CRbb",
        "FitStudies_Datacards_"+basename_+"_simplified_CRbj",
        "FitStudies_Datacards_"+basename_+"_simplified_CR2b",
        "FitStudies_Datacards_"+basename_+"_simplified_CRcc",
        "FitStudies_Datacards_"+basename_+"_simplified_CRcj",
        "FitStudies_Datacards_"+basename_+"_simplified_CR2c",
        "FitStudies_Datacards_"+basename_+"_simplified_CRlf",
        "FitStudies_Datacards_"+basename_+"_simplified_CRnolf",
        "FitStudies_Datacards_"+basename_+"_simplified_CR",
        "FitStudies_Datacards_"+basename_+"_simplified_SR",
        "FitStudies_Datacards_"+basename_+"_simplified_SRnolf",

        # "FitStudies_Datacards_280426_smoothed_simplified_CR",
        # "FitStudies_Datacards_280426_smoothed_simplified_SR",
    ]

    outwebfolder = "/eos/home-s/sewuchte/www/Vcb/Apr26/"
    outfolderlocal = "/afs/cern.ch/work/s/sewuchte/private/VCB/CMSSW_15_0_10/src/PlotTools/"

    # baseOutputFolder = outwebfolder+"NuisanceEvolution_290426_correctedBnormalization_noPeterson/"
    # baseOutputFolder = outwebfolder+"NuisanceEvolution_280426_smoothed/"
    # baseOutputFolder = outwebfolder+"NuisanceEvolution_290426_correctedBnormalization_noPeterson/"
    # baseOutputFolder = outwebfolder+"NuisanceEvolution_290426_correctedBnormalization_noPeterson_inflateFlav/"
    # baseOutputFolder = outwebfolder+"NuisanceEvolution_040526_fixes/"
    baseOutputFolder = outwebfolder+"NuisanceEvolution_"+basename_+"/"

    # for ev_name in ev_names:

    # extNames = [
    #     ev_name+"/workspace_Vcb_SL_2024/",
    #     # ev_name+"/FR2_ee/",
    # ]

    extNames = [ev_name+"/workspace_Vcb_SL_2024/" for ev_name in ev_names]

    #####################################################################
    ######################## plotNuisanceEvolution
    #####################################################################
    # names = [x.split("/")[1] for x in extNames]
    # names = [x.split("/")[1].replace("workspace_Vcb_SL_2024", "SL_2024") for x in extNames]
    names = [x.split("/")[0].split("_")[-1] for x in extNames]

    filenames =[]
    filenames_ = [
        # basePath+e+"/ImpactsObserved/impacts_obs.json" for e in extNames
        basePath+e+"/ImpactsObserved/higgsCombine_nominal_obs_impacts.Impacts.mH125p38.json" for e in extNames
    ]
    filenames = []
    for f_ in filenames_:
        filenames.append(f_)

    dictCon = {}
    # dictP = {}
    listN = []
    # listPOIs = []

    usedNames=[]

    for fname,n in zip(filenames, names):
        if os.path.exists(fname):
            # dictConstraints = getPOIsAndNuisancesFromFitFile(fname)
            dictConstraints = getPOIsAndNuisancesFromFile(fname)
            dictCon[n]=dictConstraints
            usedNames.append(n)
            for entry in dictConstraints:
                if entry not in listN:
                    # if not "prop" in entry and not "rateDY" in entry and not "rateTT0Jet" in entry:
                    # if not "prop" in entry:
                    if not "prop" in entry and not ("PDF_" in entry and not "PDF_ALPHAS" in entry):
                        listN.append(entry)


    # graphs,coordinates = createGraphsFromConstraints(listN[0:10], usedNames, dictCon)
    graphs,coordinates = createGraphsFromConstraints(listN, usedNames, dictCon)


    can = ROOT.TCanvas("","",900,1200)
    style.defaultStyle()
    s = style.defaultStyle()
    style.divideByBinWidth = False
    style.minimumOne=True
    can.SetLeftMargin(0.35)

    for isub,sub in enumerate([listN[i:i+5] for i in range(0, len(listN), 5)]):
        can.Clear()
        # graphs,coordinates = createGraphsFromConstraints(sub, names, dictCon)
        graphs,coordinates = createGraphsFromConstraints(sub, usedNames, dictCon)

        colors= [ROOT.kBlack, ROOT.kRed+1, ROOT.kBlue+1, ROOT.kGreen+1, ROOT.kOrange-3, ROOT.kGreen-2, ROOT.kRed-3,ROOT.kCyan, ROOT.kViolet,ROOT.kGreen-7,ROOT.kPink-9, ROOT.kCyan+3]
        colors=colors*3

        # outFolder=(baseOutputFolder+"/NuisanceEvolutionPlots/").replace("Plots/","Plots"+ev_name.replace("NuisanceEvolution","")+"/")
        outFolder=(baseOutputFolder)

        leg = ROOT.TLegend(0.5,0.78,0.95,0.935)
        # leg = ROOT.TLegend(0.27,0.76,0.95,0.935)
        leg.SetNColumns(2)
        leg.SetTextSize(0.02)

        # line1 = ROOT.TLine(0.5,0.,0.5,1010.)
        line1 = ROOT.TLine(1,0.,1,1010.)
        line1.SetLineColor(ROOT.kBlack)
        line1.SetLineStyle(ROOT.kDotted)
        # line2 = ROOT.TLine(-0.5,0.,-0.5,1010.)
        line2 = ROOT.TLine(-1,0.,-1,1010.)
        line2.SetLineColor(ROOT.kBlack)
        line2.SetLineStyle(ROOT.kDotted)
        # line3 = ROOT.TLine(1.,0.,1.,1050.)
        line3 = ROOT.TLine(0.,0.,0.,1010.)
        line3.SetLineColor(ROOT.kBlack)
        line3.SetLineStyle(ROOT.kDotted)
        line4 = ROOT.TLine(-1.,0.,-1.,1010.)
        # line4 = ROOT.TLine(-3.,0.,-3.,1010.)
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

            # graph.GetXaxis().SetRangeUser(-1.,1.)
            graph.GetXaxis().SetRangeUser(-3.,3.)
            graph.GetXaxis().SetLimits(-3.,3.)
            graph.GetYaxis().SetRangeUser(0,1300)
            graph.GetYaxis().SetLimits(0,1300)
            graph.GetYaxis().SetTickLength(0.)
            graph.GetYaxis().SetLabelSize(0.)
            graph.GetXaxis().SetTickLength(0.)
            graph.GetXaxis().SetTitle("#hat{#theta}-#theta/#Delta#theta")
            leg.AddEntry(graph,names[i],"lep")
            graph.SetMarkerStyle(20)
            graph.SetMarkerSize(1.2)

            if i==0:
                # graph.GetXaxis().SetRangeUser(-2.,2.)
                # graph.GetXaxis().SetLimits(-2.,2.)
                graph.GetXaxis().SetRangeUser(-3.,3.)
                graph.GetXaxis().SetLimits(-3.,3.)
                graph.Draw("AP")
                graph.GetXaxis().SetRangeUser(-3.,3.)
                graph.GetXaxis().SetLimits(-3.,3.)
                graph.Draw("AP")
                can.Update()
                line1.Draw("same")
                line2.Draw("same")
                line3.Draw("same")
                # line4.Draw("same")
            else:
                # graph.GetXaxis().SetRangeUser(-2.,2.)
                # graph.GetXaxis().SetLimits(-2.,2.)
                graph.GetXaxis().SetRangeUser(-3.,3.)
                graph.GetXaxis().SetLimits(-3.,3.)
                graph.Draw("Psame")
            i = i+1

        labels=[]
        can.Update()

        for yC,n in coordinates:
            t = ROOT.TText(-4.2,yC,n)
            t.SetTextSize(0.021)
            t.Draw("same")
            labels.append(t)

        if not os.path.exists(outFolder):
            os.makedirs(outFolder)

        info = "Preliminary"
        l = aux.Label(info="#scale[0.7]{%s}" % info, sim=False, year="2024")

        leg.Draw("same")
        saveName = "EvolutionPlot_"+str(isub)
        aux.save(saveName, folder=outFolder, normal=True, log=False)

if __name__ == "__main__":
    main()
