#!/usr/bin/env python3
"""
    simple wrapper to organize plot commands
"""
import argparse
import os
import glob
import ROOT
from utilities.auxiliary   import *
import pdb

def createHTMLFromResults(inFolder, outPath, outFileName, POIs, rates, tests, doObserved = False):
    # print (inFolder, outPath, outFileName, POIs, rates, tests, doObserved)

    outJson = {}

    types = ["Expected"]
    if doObserved:
        types.append("Observed")
        types.append("ExpectedFreq")

    for workspacePath in os.listdir(inFolder):
        workspacename = workspacePath.replace("workspace_","")
        # print (workspacename)
        outJson[workspacename] = {}
        for type_ in types:
            for test in tests:
                outJson[workspacename][test+type_] = {}

                if "Fit" in test:
                    fileToRead = inFolder+"/"+workspacePath+"/"+test+type_+"/*.out.txt"
                    # print (fileToRead)
                    fileToRead = glob.glob(fileToRead)
                    # print (fileToRead)
                    if len(fileToRead) > 0:
                        fileToRead = fileToRead[0]
                        for POI in POIs:
                            with open(fileToRead) as file:
                                lines = [line.rstrip() for line in file]
                                for line in lines:
                                    if POI+" :    " in line:
                                        result = line.replace(POI+" :    ","")
                                        result = result.replace(" (68%)","")
                                        outJson[workspacename][test+type_][POI] = result
                                    if POI+" :   " in line:
                                        result = line.replace(POI+" :   ","")
                                        result = result.replace(" (68%)","")
                                        outJson[workspacename][test+type_][POI] = result

                                        
                    # rootfileToRead = inFolder+"/"+workspacePath+"/"+test+type_+"/multidimfit_*.root"
                    # rootfileToRead = inFolder+"/"+workspacePath+"/"+"Impacts"+type_+"/multidimfit_*.root"
                    rootfileToRead = inFolder+"/"+workspacePath+"/"+"Fit"+type_+"/multidimfit_*.root"
                    # print (rootfileToRead)
                    files__ = glob.glob(rootfileToRead)
                    if len(files__) > 0:
                        rootfileToRead = files__[0]
                        for rate in rates:
                            # print (rate)
                            # with open(rootfileToRead) as file:
                            f = ROOT.TFile(rootfileToRead, "READ")
                            fitResult = f.Get("fit_mdf")
                            if rates:
                                rates_ = []
                                if "FH" in rootfileToRead:
                                    for p_ in rates:
                                        rates_.append(p_ + "_FH")
                                if "SL" in rootfileToRead:
                                    for p_ in rates:
                                        rates_.append(p_)
                                        rates_.append(p_ + "_FH")
                                for p in rates_:
                                    # print (p)
                                    # if "FH" in rootfileToRead:
                                    #     p = p + "_FH"
                                    var = fitResult.floatParsFinal().find(p)
                                    # print (p, var)
                                    if var != None:
                                        # pdb.set_trace()
                                        # vals.append(var.getValV())
                                        # errLo.append(var.getErrorLo())
                                        # errHi.append(var.getErrorHi())
                                        # err.append(var.getError())
                                        # outJson[workspacename][test+type_][p] = str(np.round(var.getValV(),3))+" +- "+str(np.round(var.getError(),3))
                                        e_ = (np.abs(var.getErrorLo())+np.abs(var.getErrorHi()))/2.
                                        # print (p, var.getValV(), var.getVal(), e_,var.getError())
                                        outJson[workspacename][test+type_][p] = str(np.round(var.getValV(),3))+" +- "+str(np.round(e_,3))

                                # lines = [line.rstrip() for line in file]
                                # for line in lines:
                                #     if rate+" :    " in line:
                                #         result = line.replace(rate+" :    ","")
                                #         result = result.replace(" (68%)","")
                                #         outJson[workspacename][test+type_][rate] = result

                if "Limits" in test:
                    for POI in POIs:
                        fileToRead = inFolder+"/"+workspacePath+"/"+test+type_+'/'+POI+"/*.out.txt"
                        fileToRead = glob.glob(fileToRead)
                        if len(fileToRead) > 0:
                            fileToRead = fileToRead[0]
                            with open(fileToRead) as file:
                                lines = [line.rstrip() for line in file]
                                # print (lines)
                                for line in lines:
                                    if type_ == "Observed":
                                        if "Observed Limit:" in line:
                                            result = line.replace("Observed Limit: ","")
                                            result = result.replace(POI+" < ","")
                                            # print (result)
                                            outJson[workspacename][test+type_][POI] = result
                                    else:
                                        if "Expected 50.0%:" in line:
                                            result = line.replace("Expected 50.0%: ","")
                                            result = result.replace(POI+" < ","")
                                            # print (result)
                                            outJson[workspacename][test+type_][POI] = result

                if "Significance" in test:
                    for POI in POIs:
                        fileToRead = inFolder+"/"+workspacePath+"/"+test+type_+'/'+POI+"/*.out.txt"
                        fileToRead = glob.glob(fileToRead)
                        if len(fileToRead) > 0:
                            fileToRead = fileToRead[0]
                            with open(fileToRead) as file:
                                lines = [line.rstrip() for line in file]
                                # print (lines)
                                for line in lines:
                                    if "Significance:" in line:
                                        result = line.replace("Significance: ","")
                                        # print (POI,result)
                                        outJson[workspacename][test+type_][POI] = result


    from json2table import convert

    build_direction = "LEFT_TO_RIGHT"
    table_attributes = {
        # "style" : "width:100%",
        "class" : "table table-striped",
        "border" : 1,
        }

    html=convert(outJson, build_direction=build_direction, table_attributes=table_attributes)
    # print(html)

    f = open(outPath+outFileName, "w")
    f.write(html)
    f.close()


#### main
if __name__ == '__main__':
    ### args
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('-i', '--input', dest='input', action='store', default=None, required=True,
                        help='path to input folder')

    parser.add_argument('-o', '--output', dest='output', action='store', default=None, required=True,
                        help='path to output folder')

    parser.add_argument('-f', '--fileName', dest='fileName', action='store', default=None, required=True,
                        help='output HTML filename')

    parser.add_argument('-p', '--POIs', dest='POIs', nargs='+', default=['r'], required=False,
                        help='list of POIs to consider (defaults = rate_ttHbb, rate_ttHcc, rate_ttZbb, rate_ttZcc)')

    parser.add_argument('-r', '--rates', dest='rates', nargs='+', default=['xsec_ttbb', 'xsec_ttbj', 'xsec_ttcc', 'xsec_ttcj', 'xsec_ttLF', 'xsec_tt2c', 'xsec_tt2b',], required=False,
                        help='list of ratess to consider')

    parser.add_argument('-t', '--tests', dest='tests', nargs='+', default=['Fit','Limits', 'Significance'], required=False,
                        help='list of tests to include (default = Fit, Limits, Significance)')

    parser.add_argument('--observed', dest='observed', action='store_true', default=False,
                        help='include observed values')

    opts, opts_unknown = parser.parse_known_args()
    ###
    # inFolder = '/eos/cms/store/cmst3/user/sewuchte/ttHccNew/FitStudies_Datacards_020424_binning_Huilin_140324_summedChannelsYears_simplified_VR/'
    # outPath = '/eos/home-s/sewuchte/www/ttH/FitStudies/'
    # outFileName = 'summedChannelsYears_VR.html'
    createHTMLFromResults(opts.input, opts.output, opts.fileName, opts.POIs, opts.rates, opts.tests, opts.observed)


