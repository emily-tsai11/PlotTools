# -*- coding: utf-8 -*-
import array
# import ConfigParser
import configparser
import itertools
import pickle
import re
from math import *

import multiplot
import numpy
import numpy as np
import ROOT
import style

# binCfg = ConfigParser.SafeConfigParser()
binCfg = configparser.SafeConfigParser()

saveStuff = []


#!/usr/bin/env python
import os
import subprocess


def KILL(log):
    raise SystemExit('\n '+'\033[1m'+'@@@ '+'\033[91m'+'FATAL'  +'\033[0m'+' -- '+log+'\n')
# --

def WARNING(log):
    print ('\n '+'\033[1m'+'@@@ '+'\033[93m'+'WARNING'+'\033[0m'+' -- '+log+'\n')
# --

def EXE(cmd, suspend=True, verbose=False, dry_run=False):
    if verbose: print ('\033[1m'+'>'+'\033[0m'+' '+cmd)
    if dry_run: return

    _exitcode = os.system(cmd)

    if _exitcode and suspend: raise SystemExit(_exitcode)

    return _exitcode
# --

def get_output(cmd, permissive=False):
    prc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    out, err = prc.communicate()

    if (not permissive) and prc.returncode:
       KILL('get_output -- shell command failed (execute command to reproduce the error):\n'+' '*14+'> '+cmd)

    return (out, err)
# --

def command_output_lines(cmd, stdout=True, stderr=False, permissive=False):

    _tmp_out_ls = []

    if not (stdout or stderr):
       WARNING('command_output_lines -- options "stdout" and "stderr" both set to FALSE, returning empty list')
       return _tmp_out_ls

    _tmp_out = get_output(cmd, permissive=permissive).decode('utf-8')

    if stdout: _tmp_out_ls += _tmp_out[0].split('\n')
    if stderr: _tmp_out_ls += _tmp_out[1].split('\n')

    return _tmp_out_ls
# --

def rreplace(str__, old__, new__, occurrence__):
    li_ = str__.rsplit(old__, occurrence__)
    return new__.join(li_)
# --

def which(program, permissive=False, verbose=False):

    fpath, fname = os.path.split(program)

    _exe_ls = []

    if fpath:
        if os.path.isfile(program) and os.access(program, os.X_OK):
           _exe_ls += [program]

    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)

            if os.path.isfile(exe_file) and os.access(exe_file, os.X_OK):
               _exe_ls += [exe_file]

    _exe_ls = list(set(_exe_ls))

    if len(_exe_ls) == 0:
       log_msg = 'which -- executable not found: '+program

       if permissive:
          if verbose: WARNING(log_msg)
          return None

       else:
          KILL(log_msg)

    if len(_exe_ls) >  1:
       if verbose:
          WARNING('which -- executable "'+program+'" has multiple matches: \n'+str(_exe_ls))

    return _exe_ls[0]
# --

def is_int(value):

    try: int(value)
    except ValueError: return False

    return True
# --

def is_float(value):

    try: float(value)
    except ValueError: return False

    return True
# --

def colored_text(txt, keys=[]):

    _tmp_out = ''

    for _i_tmp in keys:
        _tmp_out += '\033['+_i_tmp+'m'

    _tmp_out += txt

    if len(keys) > 0: _tmp_out += '\033[0m'

    return _tmp_out
# --

def HTCondor_jobIDs(username=None):

    if not username:
       if 'USER' in os.environ: username = os.environ['USER']

    if not username:
       KILL('HTCondor_jobIDs -- unspecified argument "username"')

    _condorq_jobIDs = []

    _condorq_lines = get_output('condor_q')[0].decode('utf-8').split('\n')

    for _i_condorq in _condorq_lines:
        _i_condorq_pieces = _i_condorq.split()

        if (len(_i_condorq_pieces) > 0) and (_i_condorq_pieces[0] == str(username)):
           _condorq_jobIDs += [_i_condorq_pieces[-1]]

    return _condorq_jobIDs

def HTCondor_jobExecutables(username=None):

    if not username:
       if 'USER' in os.environ: username = os.environ['USER']

    if not username:
       KILL('HTCondor_jobExecutables -- unspecified argument "username"')

    _condorq_jobExes = []

    _condorq_lines = get_output('condor_q -long '+username)[0].decode('utf-8').split('\n')

    for _i_condorq in _condorq_lines:

        if not _i_condorq.startswith('Cmd = '): continue

        _i_condorq_cmd_pieces = _i_condorq.split(' = ')

        if len(_i_condorq_cmd_pieces) != 2: continue

        _exe_path = _i_condorq_cmd_pieces[1]
        _exe_path = _exe_path.replace(' ', '')

        if len(_exe_path) == 0: continue

        if _exe_path.startswith('"'): _exe_path = _exe_path[+1:]
        if _exe_path.endswith  ('"'): _exe_path = _exe_path[:-1]

        _exe_path = os.path.abspath(os.path.realpath(_exe_path))

        _condorq_jobExes += [_exe_path]

    _condorq_jobExes = sorted(list(set(_condorq_jobExes)))

    return _condorq_jobExes

def HTCondor_jobExecutables_2(username=None):

    if not username:
       if 'USER' in os.environ: username = os.environ['USER']

    if not username:
       KILL('HTCondor_jobExecutables -- unspecified argument "username"')

    _condorq_jobExes_dict = {}

    _condorq_cmd = 'condor_q {:} -format "%d." ClusterId -format "%d " ProcId -format "%s\\n" Cmd'.format(username)

    _condorq_lines = get_output(_condorq_cmd, permissive=True)[0].decode('utf-8').split('\n')

    for _i_condorq_line in _condorq_lines:

        _i_condorq_cmd_pieces = _i_condorq_line.split()

        if len(_i_condorq_cmd_pieces) != 2: continue

        _exe_path = os.path.abspath(_i_condorq_cmd_pieces[1])

        _condorq_jobExes_dict[_exe_path] = _i_condorq_cmd_pieces[0]

    return _condorq_jobExes_dict

def HTCondor_executable_from_jobID(jobID):

    _condorq_cmd = get_output('condor_q '+jobID+' -long')[0].decode('utf-8').split('\n')
    _condorq_cmd = [_tmp for _tmp in _condorq_cmd if _tmp.startswith('Cmd = ')]

    if len(_condorq_cmd) != 1: return None

    _condorq_cmd_pieces = _condorq_cmd[0].split(' = ')
    if len(_condorq_cmd_pieces) != 2: return None

    _exe_path = _condorq_cmd_pieces[1]
    _exe_path = _exe_path.replace(' ', '')

    if _exe_path.startswith('"'): _exe_path = _exe_path[+1:]
    if _exe_path.endswith  ('"'): _exe_path = _exe_path[:-1]

    _exe_path = os.path.abspath(os.path.realpath(_exe_path))

    return _exe_path
# --

def hadd_rootfiles(output, inputs):

    if os.path.exists(output):
       KILL('hadd_rootfiles -- path to target output file already exists: '+output)

    if len(inputs) == 0:
       KILL('hadd_rootfiles -- empty list of inputs')

    valid_inputs = []
    for i_inp in inputs:

        valid_inputs += [i_inp]

    _merger = ROOT.TFileMerger(False, False)
    _merger.OutputFile(output_file)

    for i_inp in inputs:

        if not os.path.isfile(i_inp):
           KILL('hadd_rootfiles -- invalid path to input file: '+i_inp)

        _tmp_tfile = ROOT.TFile.Open(i_inp)

        if not _tmp_tfile:
           KILL('hadd_rootfiles -- failed conversion from input file path to TFile: '+i_inp)

        elif _tmp_tfile.IsZombie():
           KILL('hadd_rootfiles -- input TFile in Zombie state: '+i_inp)

        _tmp_tfile.Close()

        _merger.AddFile(i_inp)

    _ret = _merger.Merge(False)

    if not _ret: KILL('hadd_rootfiles -- call to TFileMerger::Merge() failed: output='+output)

    print (colored_text('[output='+output_file+']', ['93']), 'merging completed {0}, {1:.2f} MB'.format(output_file, os.path.getsize(output_file)/1024.0/1024.0))
# --




def frange(start, end, step):
    a = []
    tmp = start
    # while(tmp < end):
    while(tmp <= end):
        a.append(tmp)
        tmp += step
    return a

def frangeN(start, end, N):
    a = []
    tmp = start
    step = abs(end - start) / N
    while(tmp <= end):
        a.append(tmp)
        tmp += step
    return a



def sumSq(*items):
    return sqrt(sum([i**2 for i in items]))

def dataLikeName(name):
    return "Data" in name or "Pseudodata" in name or "Direct" in name


def getProjections(h2, axis="x", scale=True):
    if axis == "x":
        a1 = h2.GetXaxis()
        a2 = h2.GetYaxis()
    elif axis == "y":
        a1 = h2.GetYaxis()
        a2 = h2.GetXaxis()
    else:
        print ("please use 'x' or 'y' as argument")
    hs = []
    label = a2.GetTitle()

    for ybin in range(a2.GetNbins() + 2):

        ylow = a2.GetBinLowEdge(ybin)
        yhigh = a2.GetBinUpEdge(ybin)
        name = "{} #leq {} < {}".format(ylow, label, yhigh)
        if ybin == 0:
            name = "{} < {}".format(label, yhigh)
        if ybin == a2.GetNbins() + 1:
            name = "{} #leq {}".format(ylow, label)

        h = h2.ProjectionX(name, ybin, ybin) if axis == "x" else h2.ProjectionY(
            name, ybin, ybin)
        h.SetDirectory(0)
        h.GetXaxis().SetTitleOffset(h2.GetXaxis().GetTitleOffset())
        h.SetLineColor(getPaletteColor(1. * ybin / (a2.GetNbins() + 2)))
        h.SetTitle(";{};{}".format(
            h.GetXaxis().GetTitle(), h2.GetZaxis().GetTitle()))
        if not h.GetEntries():
            continue
        if scale:
            print ("Scale projections!")
            h.Scale(1. / h.GetEntries())
        hs.append(h)

    return hs


def drawContributions(stack, mini=0, maxi=1.1, title="Fractions"):
    total = stack.GetStack().Last()
    b = total.GetNbinsX() - 1
    newStack = ROOT.THStack()
    hists = [h.Clone(h.GetName() + randomName()) for h in stack.GetStack()]
    for ih in range(len(hists) - 1, 0, -1):
        hists[ih].Add(hists[ih - 1], -1)
    for h in hists:
        h.Divide(total)
        h.SetFillColor(h.GetFillColor())
        newStack.Add(h)
    newStack.SetTitle(";{};{}".format(h.GetXaxis().GetTitle(), title))
    newStack.SetMinimum(mini)
    newStack.SetMaximum(maxi)
    newStack.Draw("hist")
    saveStuff.append(newStack)


def write2File(obj2Write, name, fname):
    obj = obj2Write.Clone()
    if isinstance(obj, ROOT.TH1):
        for a in obj.GetXaxis(), obj.GetYaxis():
            pass
            # a.UnZoom() #TODO: find out why this affects original histogram as well

    f = ROOT.TFile(fname, "update")
    obj.Write(name, ROOT.TObject.kWriteDelete)
    f.Close()



def getFromFile(filename, histoname):
    f = ROOT.TFile(filename, "READ")
    h = f.Get(histoname)
    if not h:
        if ROOT.gErrorIgnoreLevel < ROOT.kBreak:
            print ("Object {} not found in file {}".format(histoname, filename))
        return
    
    h = ROOT.gROOT.CloneObject(h)
    # h.SetDirectory(0)
    # h = h.Clone()
    ROOT.SetOwnership(h, True)
    if isinstance(h, ROOT.TH1) and not h.GetSumw2N():
        h.Sumw2()
    h.drawOption_ = ""
    h.SetTitle("")
    f.Close()
    return h


def getXAxisFromFile(filename, histoname):
    f = ROOT.TFile(filename)
    h = f.Get(histoname)
    if not h:
        if ROOT.gErrorIgnoreLevel < ROOT.kBreak:
            print ("Object {} not found in file {}".format(histoname, filename))
        return
    h = ROOT.gROOT.CloneObject(h)
    # if isinstance(h, ROOT.TH1) and not h.GetSumw2N():
    #     h.Sumw2()
    # h.drawOption_ = ""
    # h.SetTitle("")
    # print h.GetXaxis().GetTitle()
    return h.GetXaxis().GetTitle()

def fixHistogram(histo, isData):
    if isData:
        return histo
    if isinstance(histo, ROOT.TH1):
        #Add underflow to first bin
        if histo.GetBinContent(0) > 0.:
            errorFirst= histo.GetBinError(1)
            errorUnderflow = histo.GetBinError(0)
            histo.SetBinContent(1, histo.GetBinContent(0)+histo.GetBinContent(1))
            histo.SetBinError(1, np.sqrt(errorFirst*errorFirst + errorUnderflow*errorUnderflow))
        #Add overflow bin to last bin
        if histo.GetBinContent(histo.GetNbinsX()+1) > 0.:
            errorLast = histo.GetBinError(histo.GetNbinsX())
            errorOverflow = histo.GetBinError(histo.GetNbinsX()+1)
            histo.SetBinContent(histo.GetNbinsX(), histo.GetBinContent(histo.GetNbinsX())+histo.GetBinContent(histo.GetNbinsX()+1))
            histo.SetBinError(histo.GetNbinsX(), np.sqrt(errorLast*errorLast + errorOverflow*errorOverflow))
        # for (int x=1; x<histo.GetNbinsX()+1; ++x):
        for x in range(1,histo.GetNbinsX()+1):
            if(histo.GetBinContent(x) < 0.0000001):
                histo.SetBinContent(x, 0.0000001)
            if(histo.GetBinError(x) > histo.GetBinContent(x)):
                histo.SetBinError(x, histo.GetBinContent(x))
            if (histo.Integral(1, histo.GetNbinsX()) == 0):
                histo.SetBinContent(1, 0.0000001)
                histo.SetBinError(1, 0.0000001)
        
        histo.SetBinContent(0, 0.)
        histo.SetBinError(0, 0.)
        histo.SetBinContent(histo.GetNbinsX()+1, 0.)
        histo.SetBinError(histo.GetNbinsX()+1, 0.)
        return histo
    else:
        ValueError("FixHistogram -- No TH1D, should not be here!")
        # print("FixHistogram -- No TH1D, should not be here!", histo, histo.GetName())

def getYAxisFromFile(filename, histoname):
    f = ROOT.TFile(filename)
    h = f.Get(histoname)
    if not h:
        if ROOT.gErrorIgnoreLevel < ROOT.kBreak:
            print ("Object {} not found in file {}".format(histoname, filename))
        return
    h = ROOT.gROOT.CloneObject(h)
    # if isinstance(h, ROOT.TH1) and not h.GetSumw2N():
    #     h.Sumw2()
    # h.drawOption_ = ""
    # h.SetTitle("")
    # print h.GetYaxis().GetTitle()
    return h.GetYaxis().GetTitle()

def getObjectNames(filename, path="", objects=[ROOT.TH1]):
    f = ROOT.TFile(filename)
    tmpDir = f.GetDirectory(path)

    outList = []
    for element in tmpDir.GetListOfKeys():
        if element.GetName() == "rawEff_vs_run":
            continue
        obj = element.ReadObj()

        if any([isinstance(obj, o) for o in objects]):
            outList.append(element.GetName())

    return outList


def getDirNames(filename):
    f = ROOT.TFile(filename)
    allDirs = [e.GetName() for e in f.GetListOfKeys()
               if isinstance(e.ReadObj(), ROOT.TDirectory)]
    return allDirs


def getBinning(axis):
    binning = []
    for i in range(axis.GetNbins() + 1):
        binning.append(axis.GetBinUpEdge(i))
    return binning


def checkRebinningConsistence(axis, newBinning):
    oldBinning = getBinning(axis)
    # get rid of unprecise floats:
    oldBinning = [round(i, 5) for i in oldBinning]
    newBinning = [round(i, 5) for i in newBinning]
    # ignore new bin edges out of range of old binning
    newBinning = [i for i in newBinning if i >= oldBinning[0]]
    for i in newBinning:
        if i not in oldBinning:
            print ("New bin edge is not compatible with old binning", i, "old binning:", oldBinning)


def rebin2d(h, binEdgesX=None, binEdgesY=None):
    if not binEdgesX and not binEdgesY:
        return h
    # Check consistency with old binning
    if binEdgesX:
        checkRebinningConsistence(h.GetXaxis(), binEdgesX)
    else:
        binEdgesX = [h.GetXaxis().GetBinLowEdge(bin + 1)
                     for bin in range(h.GetNbinsX())]

    if binEdgesY:
        checkRebinningConsistence(h.GetYaxis(), binEdgesY)
    else:
        binEdgesY = [h.GetYaxis().GetBinLowEdge(bin + 1)
                     for bin in range(h.GetNbinsY())]

    # Create
    binEdgesXArr = array.array('d', binEdgesX)
    binEdgesYArr = array.array('d', binEdgesY)
    hnew = ROOT.TH2F(h.GetName() + randomName(), h.GetTitle(),
                     len(binEdgesX) - 1, binEdgesXArr, len(binEdgesY) - 1, binEdgesYArr)
    hnew.SetDirectory(0)
    hnew.GetYaxis().SetTitleOffset(h.GetYaxis().GetTitleOffset())

    # GetProperties
    hnew.drawOption_ = h.drawOption_ if hasattr(h, "drawOption_") else ""
    hnew.SetTitle("{};{};{}".format(
        h.GetTitle(), h.GetXaxis().GetTitle(), h.GetYaxis().GetTitle()))

    # Fill
    for xbin in range(h.GetNbinsX() + 2):
        x = h.GetXaxis().GetBinCenter(xbin)
        for ybin in range(h.GetNbinsY() + 2):
            y = h.GetYaxis().GetBinCenter(ybin)
            newBin = hnew.FindFixBin(x, y)
            hnew.SetBinContent(newBin, hnew.GetBinContent(
                newBin) + h.GetBinContent(xbin, ybin))
            hnew.SetBinError(newBin, sqrt(hnew.GetBinError(
                newBin)**2 + h.GetBinError(xbin, ybin)**2))
    return hnew


def rebin3d(h, binEdgesX=None, binEdgesY=None, binEdgesZ=None):
    if not binEdgesX and not binEdgesY and not binEdgesZ:
        return h
    # Check consistency with old binning
    if binEdgesX:
        checkRebinningConsistence(h.GetXaxis(), binEdgesX)
    else:
        binEdgesX = [h.GetXaxis().GetBinLowEdge(bin + 1)
                     for bin in range(h.GetNbinsX())]
    if binEdgesY:
        checkRebinningConsistence(h.GetYaxis(), binEdgesY)
    else:
        binEdgesY = [h.GetYaxis().GetBinLowEdge(bin + 1)
                     for bin in range(h.GetNbinsY())]
    if binEdgesZ:
        checkRebinningConsistence(h.GetZaxis(), binEdgesZ)
    else:
        binEdgesZ = [h.GetZaxis().GetBinLowEdge(bin + 1)
                     for bin in range(h.GetNbinsZ())]

    # Create
    binEdgesXArr = array.array('d', binEdgesX)
    binEdgesYArr = array.array('d', binEdgesY)
    binEdgesZArr = array.array('d', binEdgesZ)
    hnew = ROOT.TH3F(h.GetName(), h.GetTitle(), len(binEdgesX) - 1, binEdgesXArr,
                     len(binEdgesY) - 1, binEdgesYArr, len(binEdgesZ) - 1, binEdgesZArr)

    # GetProperties
    hnew.drawOption_ = h.drawOption_ if hasattr(h, "drawOption_") else ""
    hnew.SetTitle("{};{};{};{}".format(h.GetTitle(), h.GetXaxis(
    ).GetTitle(), h.GetYaxis().GetTitle(), h.GetZaxis().GetTitle()))

    # Fill
    for xbin in range(h.GetNbinsX() + 2):
        x = h.GetXaxis().GetBinCenter(xbin)
        for ybin in range(h.GetNbinsY() + 2):
            y = h.GetYaxis().GetBinCenter(ybin)
            for zbin in range(h.GetNbinsZ() + 2):
                z = h.GetZaxis().GetBinCenter(zbin)
                newBin = hnew.FindFixBin(x, y, z)
                hnew.SetBinContent(newBin, hnew.GetBinContent(
                    newBin) + h.GetBinContent(xbin, ybin, zbin))
                hnew.SetBinError(newBin, sqrt(hnew.GetBinError(
                    newBin)**2 + h.GetBinError(xbin, ybin, zbin)**2))
    return hnew


import json


def loadBinningFromFile(entryname, filepath = "/nfs/dust/cms/user/sewuchte/TTH/MyFramework/CMSSW_11_3_4/src/TopAnalysis/Configuration/diLeptonic/MiniTreeAnalysis/binnings/testBinning.json"):
    # year = entryname.split("_")[0]
    # channel = entryname.split("_")[1]
    with open(filepath, 'r') as fp:
        data = json.load(fp)
    if entryname in data:
        return data[entryname]
    else:
        raise ValueError("Entry",entryname,"not found in binningJson from file", filepath, "!")
    
def loadBinningFromJson(entryname, data):
    # year = entryname.split("_")[0]
    # channel = entryname.split("_")[1]
    # with open(filepath, 'r') as fp:
    #     data = json.load(fp)
    if entryname in data:
        # return data[entryname]
        # ret = [e for e in data[entryname]]
        # print ("-",ret)
        if data[entryname] is not None:
            ret = [np.round(e,4) for e in data[entryname]]
            # print (ret)
        else:
            ret = None
        # print ("-",ret)
        # print ("--",np.around(data[entryname], 4))
        # return np.around(data[entryname], 4)
        return ret
    else:
        raise ValueError("Entry", entryname, "not found in binningJson!")

    
def rebin(h, binEdges, scale=True):
    if not binEdges:
        return h
    # if not binEdges.any(): return h
    checkRebinningConsistence(h.GetXaxis(), binEdges)
    binEdgesArr = array.array('d', binEdges)
    #print binEdgesArr
    hnew = h.Rebin(len(binEdges) - 1, "new", binEdgesArr)
    hnew.drawOption_ = h.drawOption_ if hasattr(h, "drawOption_") else ""
    #if scale: hnew.Scale( 1., "width" )
    if style.divideByBinWidth:
        hnew.Scale(1., "width")
    # del h,binEdges
    return hnew


def rebinX(h, binEdgesX=None, binEdgesY=None, binEdgesZ=None):
    nDim = h.GetDimension()
    if nDim == 1:
        return rebin(h, binEdgesX, False)
    elif nDim == 2:
        return rebin2d(h, binEdgesX, binEdgesY)
    elif nDim == 3:
        return rebin3d(h, binEdgesX, binEdgesY, binEdgesZ)
    else:
        print ("Do not know what to do with dimension", nDim)


def absHistWeighted(origHist):
    origNbins = origHist.GetNbinsX()
    origXmin = origHist.GetBinLowEdge(1)
    origXmax = origHist.GetBinLowEdge(origHist.GetNbinsX() + 1)
    if origXmin + origXmax > 0.1:
        if origXmin:
            print ("cant handle assymetric histograms")
        return origHist

    h = origHist.Clone()
    newN = int(ceil(origNbins / 2.))
    # TODO: doesn not work, only first bin in filled
    h = rebin(h, [origXmax * i / newN for i in range(newN + 1)])

    for origBin in range(origNbins + 2):
        newBin = int(abs(origBin - (origNbins + 1.) / 2)) + 1

        c1 = origHist.GetBinContent(origBin)
        e1 = origHist.GetBinError(origBin)
        c2 = h.GetBinContent(newBin)
        e2 = h.GetBinError(newBin)

        if e1 and e2:
            h.SetBinContent(newBin, (c1 * e1**-2 + c2 *
                                     e2**-2) / (e1**-2 + e2**-2))
            h.SetBinError(newBin, 1. / sqrt(e1**-2 + e2**-2))

        else:
            h.SetBinContent(newBin, origHist.GetBinContent(origBin))
            h.SetBinError(newBin, origHist.GetBinError(origBin))

    return h

def addPoissonUncertainty(hist):
    mediumWeight = hist.Integral(0, -1) / hist.GetEntries()
    for b in loopH(hist):
        c = hist.GetBinContent(b)
        if not c:
            hist.SetBinError(b, mediumWeight * 1.84102164458)
        elif abs((c - mediumWeight) / c) < 1e-2:  # one effective entry
            hist.SetBinError(b, mediumWeight * 2.6378596228)


def randomName():
    """
    Generate a random string. This function is useful to give ROOT objects
    different names to avoid overwriting.
    """
    from random import randint
    # from sys import maxint
    from sys import maxsize

    # return "%x" % (randint(0, maxint))
    return "%x" % (randint(0, maxsize))


def TH1F_binning(name, title, binEdges):
    # Wrapper for the TH1F constructor for variable binning
    binEdgesArray = array.array("d", binEdges)
    return ROOT.TH1F(name, ";%s;Events" % xVar.title, len(binEdgesArray) - 1, binEdgesArray)



def mergeBins(h, dest, source):
    h.SetBinContent(dest, h.GetBinContent(dest) + h.GetBinContent(source))
    h.SetBinError(dest, sumSq(h.GetBinError(dest), h.GetBinError(source)))
    h.SetBinContent(source, 0)
    h.SetBinError(source, 0)


def appendFlowBin(h, under=True, over=True):
    if under:
        mergeBins(h, 1, 0)
    if over:
        mergeBins(h, h.GetNbinsX(), h.GetNbinsX() + 1)


def appendFlowBin3d(h, mergeX=True, mergeY=True, mergeZ=True):
    if mergeZ:
        for xb in range(h.GetNbinsX() + 2):
            for yb in range(h.GetNbinsY() + 2):
                mergeBins(h, h.GetBin(xb, yb, 1), h.GetBin(xb, yb, 0))
                mergeBins(h, h.GetBin(xb, yb, h.GetNbinsZ()),
                          h.GetBin(xb, yb, h.GetNbinsZ() + 1))
    if mergeY:
        for xb in range(h.GetNbinsX() + 2):
            for zb in range(h.GetNbinsZ() + 2):
                mergeBins(h, h.GetBin(xb, 1, zb), h.GetBin(xb, 0, zb))
                mergeBins(h, h.GetBin(xb, h.GetNbinsY(), zb),
                          h.GetBin(xb, h.GetNbinsY() + 1, zb))
    if mergeX:
        for yb in range(h.GetNbinsY() + 2):
            for zb in range(h.GetNbinsZ() + 2):
                mergeBins(h, h.GetBin(1, yb, zb), h.GetBin(0, yb, zb))
                mergeBins(h, h.GetBin(h.GetNbinsX(), yb, zb),
                          h.GetBin(h.GetNbinsX() + 1, yb, zb))


def appendFlowBin2d(h, mergeX=True, mergeY=True):
    if mergeY:
        for b in range(h.GetNbinsX() + 2):
            mergeBins(h, h.GetBin(b, 1), h.GetBin(b, 0))
            mergeBins(h, h.GetBin(b, h.GetNbinsY()),
                      h.GetBin(b, h.GetNbinsY() + 1))
    if mergeX:
        for b in range(h.GetNbinsY() + 2):
            mergeBins(h, h.GetBin(1, b), h.GetBin(0, b))
            mergeBins(h, h.GetBin(h.GetNbinsX(), b),
                      h.GetBin(h.GetNbinsX() + 1, b))


def integralAndError(h, binx1=0, binx2=-1, bins=True):
    if not bins:
        binx1 = h.FindFixBin(binx1)
        binx2 = h.FindFixBin(binx2)
    e = ROOT.Double()
    c = h.IntegralAndError(binx1, binx2, e)
    return c, e


def getValAndError(val, err, sig=2):
    digit = sig - int(floor(log10(err))) - 1
    return (round(val, digit), round(err, digit))


def getValAndErrorStr(val, err, sig=2, digits=False, tex=False):
    # if digits, treat 'sig' as number of siginifcant digits
    out = ""
    if digits:
        if sig == 0:
            out = "{:d} #pm {:d}".format(int(round(val)), int(round(err)))
        elif sig > 0:
            out = "{{:.{0:d}f}} #pm {{:.{0:d}f}}".format(sig).format(val, err)
        else:
            print ("What are negative digits even meaning???")
    else:
        out = "{} #pm {}".format(getValAndError(val, err, sig))
    if tex:
        out = "${}$".format(out.replace("#", "\\").replace(" ", ""))
    return out

def getDataLabelFromChannel(channel, preUL = False):
    if channel == "ee":
        return "Data"
    if channel == "emu":
        return "Data"
    if channel == "mumu":
        return "Data"
    if channel == "ll":
        return "Data"
    if channel == "sameflavor":
        return "Data"
    if channel == "dilepton":
        return "Data"
    if channel == "se":
        return "Data"
    if channel == "smu":
        return "Data"
    if channel == "slep":
        return "Data"
    if channel == "fhad":
        return "Data"

def getBJetCategoryLabel(input):
    # "OneBTag","InclusiveBTag","TwoBTag","ZeroPlusGreaterTwoBTag"
    if input == "ZeroBTag":
        return "N_{b jet} = 0"
    elif input == "OneBTag":
        return "N_{b jet} = 1"
    elif input == "GreaterZeroBTag":
        return "N_{b jet} > 0"
    elif input == "GreaterOneBTag":
        return "N_{b jet} > 1"
    elif input == "InclusiveBTag":
        return "N_{b jet} #geq 1"
    elif input == "TwoBTag":
        return "N_{b jet} = 2"
    elif input == "ZeroPlusGreaterTwoBTag":
        return "N_{b jet} = 0 or #geq 2"
    elif input == "OnePlusTwoBTag":
        return "N_{b jet} = 1 or 2"
    elif input == "GreaterOneMediumBTag":
        return "N_{b jet} > 1"
    elif input == "GreaterTwoMediumBCTag":
        return "N_{b/c jet} > 2"
    elif input == "GreaterTwoMediumBCTagGreaterOneMediumBTag":
        return "N_{b/c jet} > 2, N_{b jet} > 1"
    elif input == "GreaterTwoMediumBCTagGreaterZeroMediumBTag":
        return "N_{b/c jet} > 2, N_{b jet} > 0"
    else:
        print ("ERROR getBJetCategoryLabel", input, "not known")
        return None

def getNJetCategoryLabel(input):
    # ["TwoJet", "InclusiveNJet", "GreaterTwoJet", "ZeroAndOneJet"]
    if input == "ZeroJet":
        return "N_{jet} = 0"
    elif input == "OneJet":
        return "N_{jet} = 1"
    elif input == "TwoJet":
        return "N_{jet} = 2"
    elif input == "InclusiveNJet":
        return "N_{jet} #geq 3"
    elif input == "GreaterTwoJet":
        return "N_{jet} > 2"
    elif input == "GreaterOneJet":
        return "N_{jet} > 1"
    elif input == "ZeroAndOneJet":
        return "N_{jet} < 2"
    elif input == "LessThanThreeJet":
        return "N_{jet} < 3"
    elif input == "ThreeJet":
        return "N_{jet} = 3"
    elif input == "FourJet":
        return "N_{jet} = 4"
    elif input == "FiveJet":
        return "N_{jet} = 5"
    elif input == "SixJet":
        return "N_{jet} = 6"
    elif input == "SevenJet":
        return "N_{jet} = 7"
    elif input == "EightJet":
        return "N_{jet} = 8"
    elif input == "GreaterThreeJet":
        return "N_{jet} > 3"
    elif input == "GreaterFourJet":
        return "N_{jet} > 4"
    elif input == "GreaterFiveJet":
        return "N_{jet} > 5"
    elif input == "GreaterSixJet":
        return "N_{jet} > 6"
    elif input == "GreaterSevenJet":
        return "N_{jet} > 7"
    elif input == "GreaterEightJet":
        return "N_{jet} > 8"
    else:
        print ("ERROR getNJetCategoryLabel", input, "not known")
        return None

def getNNCategoryLabel(input):
    label = ""
    if "InclusiveNNCategory" in input:
        label = ""
    elif "TTHbbCategory" in input:
        label = "t#bar{t}H(b#bar{b}) cat."
    elif "TTHccCategory" in input:
        label = "t#bar{t}H(c#bar{c}) cat."
    elif "TTCCCategory" in input:
        label = "t#bar{t} + c#bar{c} cat."
    elif "TTCJCategory" in input:
        label = "t#bar{t} + c jets cat."
    elif "TTBBCategory" in input:
        label = "t#bar{t} + b#bar{b} cat."
    elif "TTBJCategory" in input:
        label = "t#bar{t} + b jets cat."
    elif "TTLFCategory" in input:
        label = "t#bar{t} + LF cat."
    elif "TTZccCategory" in input:
        label = "t#bar{t}Z(c#bar{c}) cat."
    elif "TTZbbCategory" in input:
        label = "t#bar{t}Z(b#bar{b}) cat."
    elif "TTZqqCategory" in input:
        label = "t#bar{t}Z(q#bar{q}) cat."

    if "SR" in input:
        label = label + " AR"
    elif "LowNJet" in input:
        label = label + " low-N_{jet} VR"
    elif "MidScore" in input:
        # label = label + " mid-score VR"
        label = label + " VR"
    return label
    # else:
    #     print ("ERROR getNNCategoryLabel", input, "not known")
    #     return None

def getCombineChannelFromRealChannel(channel):
    e = channel
    e = e.replace("2016APV","Y2016APV")
    e = e.replace("2015","2015")
    e = e.replace("2016","2016")
    e = e.replace("2017","2017")
    e = e.replace("2018","2018")
    e = e.replace("InclusiveBTag","InclB")
    e = e.replace("ZeroPlusGreaterTwoBTag","ZeroGTwoB")
    e = e.replace("OneBTag","OneB")
    e = e.replace("TwoBTag","TwoB")
    e = e.replace("InclusiveNJet","InclJ")
    e = e.replace("GreaterTwoJet","GTwoJ")
    e = e.replace("TwoJet","TwoJ")
    e = e.replace("ZeroJet","ZeroJ")
    return e


def getYAxisTitle(histo):
    # returns e.g.: "Events / 10 GeV"
    if not style.divideByBinWidth:
        # return "Events / Bin"
        # return "Number of Events"
        return "Number of events"
    yTitle = "Events"
    xaxis = histo.GetXaxis()
    binW = xaxis.GetBinWidth(1)
    binWmean = (xaxis.GetXmax() - xaxis.GetXmin()) / xaxis.GetNbins()
    unit = "GeV" if "GeV" in xaxis.GetTitle() else None

    if abs(binW - binWmean) < 1e-6:  # assume constant bin size
        # if abs(binW-binWmean) > -1000000000.: #assume constant bin size
        if abs(binW - 1) < 1e-6:
            return yTitle

        # get two significant digits
        binW = getValAndError(0, binW)[1]
        if binW.is_integer():
            binW = int(binW)
        if unit:
            return yTitle + " / " + str(binW) + " " + unit
        else:
            return yTitle + " / " + str(binW)
    else:  # assume variable bin size
        if unit:
            return yTitle + " / " + unit
        else:
            return yTitle


def setYAxisTitle(h):
    h.SetYTitle(getYAxisTitle(h))


def getROC(hSig, hBkg, highX=True):
    # highX: signal is at high values of the variable

    nRocBins = hSig.GetNbinsX()

    sigEff = []
    bkgEff = []

    sigDen = hSig.Integral()
    bkgDen = hBkg.Integral()
    if not sigDen or not bkgDen:
        print ("Warning, signal or background histogram has no integral")
        return

    for i in range(1, nRocBins + 1):
        if highX:
            sigNum = hSig.Integral(i, nRocBins + 1)
            bkgNum = hBkg.Integral(i, nRocBins + 1)
        else:
            sigNum = hSig.Integral(1, i)
            bkgNum = hBkg.Integral(1, i)

        sigEff.append(sigNum / sigDen)
        bkgEff.append(bkgNum / bkgDen)

    rocGraph = ROOT.TGraph(nRocBins, numpy.array(bkgEff), numpy.array(sigEff))
    rocGraph.SetTitle(";#varepsilon_{bkg};#varepsilon_{sig}")
    return rocGraph


def automaticRebinner(hlist, minEvents=3):
    # Ereates an array of bin edges on a list of histograms, such that each histogram
    # has at least 'maxEvents' events in each bin.
    if minEvents == 0:
        minEvents = 1e-10
    out = []
    tmp = [0] * len(hlist)
    nBins = hlist[0].GetNbinsX()

    # check overflow bin
    overflowList = [h.GetBinContent(nBins + 1) for h in hlist]
    if min(overflowList) > minEvents:
        out.append(hlist[0].GetBinLowEdge(nBins + 1))

    for bin in range(nBins, -1, -1):

        contents = [h.GetBinContent(bin) for h in hlist]
        tmp = [sum(x) for x in zip(tmp, contents)]

        # check upper bondary of last entry
        if not out:
            if contents != [0] * len(hlist):
                out.append(hlist[0].GetBinLowEdge(bin + 1))

        else:
            if min(contents) > minEvents:
                out.append(hlist[0].GetBinLowEdge(bin))
                tmp = [0] * len(hlist)

    print (out[::-1])


def getMinimum(hists):
    # Reset fMinimum, else 'GetMinimum' will return setted minimum
    return min([h.GetMinimum(0) for h in hists if not h.SetMinimum()])


def setMinMaxForLog():
    primitivesOnCanvas = [
        i for i in ROOT.gPad.GetCanvas().GetListOfPrimitives()]
    histograms = []
    stackedHistograms = []
    for h in primitivesOnCanvas:
        if isinstance(h, ROOT.THStack):
            stackedHistograms.append(h)
            for sh in h.GetStack():
                histograms.append(sh)
        elif isinstance(h, ROOT.TH1):
            histograms.append(h)
    maxC = max([h.GetMaximum() for h in histograms])
    minC = getMinimum(histograms)
    unity = 1. / maxBinWidth(histograms[0]) if style.divideByBinWidth else 1.
    minimum = max([unity, minC]) if style.minimumOne else minC
    #minimum /= 9.
    #minimum /= 90.
    for i in histograms:
        # i.SetMaximum(2.5 * maxC)
        # i.SetMaximum(100. * maxC)
        # i.SetMaximum(10000. * maxC)
        # i.SetMaximum(100000.*maxC)
        i.SetMaximum(1000000.*maxC)
        i.SetMinimum(minimum)
    for s in stackedHistograms:
        s.SetMinimum(minimum)
        # s.SetMaximum(2.5*maxC)
        # s.SetMaximum(10. * maxC)
        # s.SetMaximum(10000. * maxC)
        # s.SetMaximum(100000. * maxC)
        s.SetMaximum(1000000. * maxC)
        # s.SetMaximum(5000.*maxC)
    ROOT.gPad.Update()



# def save(name, folder="plots/", endings=[".pdf",".png"], normal=True, log=True, changeMinMax=True):
def save(name, folder="plots/", endings=[".pdf",".png"], normal=False, log=True, changeMinMax=True):
    name = modifySaveName(name)
    if normal:
        for ending in endings:
            ROOT.gPad.GetCanvas().SaveAs(folder + name + ending)
    if log:
        allH2s = [i for i in ROOT.gPad.GetCanvas().GetListOfPrimitives()
                  if isinstance(i, ROOT.TH2)]
        if allH2s:
            ROOT.gPad.GetCanvas().SetLogz()
        else:
            if changeMinMax:
                setMinMaxForLog()
            ROOT.gPad.GetCanvas().SetLogy(True)
        for ending in endings:
            ROOT.gPad.GetCanvas().SaveAs(folder + name + "_log" + ending)
    ROOT.gPad.GetCanvas().SetLogy(False)


def getBinningsFromName(name):
    out = {"": None}
    # get histogram name
    if binCfg.has_section(name):
        for binningName, binning in binCfg.items(name):
            binning = [float(x) for x in binning.split(" ")]
            out[binningName] = binning
    return out


def interpolate2D(h):
    for xbin in range(1, h.GetNbinsX() + 1):
        x = h.GetXaxis().GetBinCenter(xbin)
        for ybin in range(1, h.GetNbinsY() + 1):
            y = h.GetYaxis().GetBinCenter(ybin)
            c = h.GetBinContent(xbin, ybin)
            if c:
                continue
            ctop = h.GetBinContent(xbin, ybin + 1)
            cbot = h.GetBinContent(xbin, ybin - 1)
            crig = h.GetBinContent(xbin + 1, ybin)
            clef = h.GetBinContent(xbin - 1, ybin)
            intPoints = []
            if cbot and ctop:
                intPoints.extend([cbot, ctop])
            if crig and clef:
                intPoints.extend([crig, clef])
            newC = sum(intPoints) / len(intPoints) if len(intPoints) else 0
            h.SetBinContent(xbin, ybin, newC)
    return h


def diagonalFlip(original):
    # original, flipped are both TH2
    flipped = original.Clone(original.GetName() + "flipped")
    flipped.SetTitle("{};{};{}".format(
        original.GetTitle(),
        original.GetYaxis().GetTitle(),
        original.GetXaxis().GetTitle()
    ))

    for xbin in range(original.GetNbinsX() + 2):
        for ybin in range(original.GetNbinsY() + 2):
            flipped.SetBinContent(
                ybin, xbin, original.GetBinContent(xbin, ybin))
            flipped.SetBinError(ybin, xbin, original.GetBinError(xbin, ybin))
    return flipped


def drawDiagonal(h2, xmin=None):
    if not xmin:
        xmin = h2.GetXaxis().GetXmin()
    xmax = h2.GetXaxis().GetXmax()
    ymin = h2.GetYaxis().GetXmin()
    ymax = h2.GetYaxis().GetXmax()
    l = ROOT.TLine()
    l.SetLineColor(ROOT.kGray + 2)
    l.SetLineStyle(2)
    l.DrawLine(max(xmin, ymin), max(xmin, ymin),
               min(xmax, ymax), min(xmax, ymax))


def addHists(*histograms):
    out = histograms[0].Clone()
    for h in histograms[1:]:
        out.Add(h)
    return out


def addHistUncert(*histograms):
    out = histograms[0].Clone()
    for h in histograms[1:]:
        for bin in range(out.GetNbinsX() + 2):
            out.SetBinError(bin, sqrt(out.GetBinError(bin)
                                      ** 2 + h.GetBinError(bin)**2))
    return out


def maxBinWidth(h):
    return max([h.GetBinWidth(bin) for bin in range(h.GetNbinsX() + 2)])



def loopH2(h2):
    return [(xbin, ybin) for xbin in range(h2.GetNbinsX() + 2) for ybin in range(h2.GetNbinsY() + 2)]


def loopH3(h3):
    return [(xbin, ybin, zbin) for xbin in range(h3.GetNbinsX() + 2) for ybin in range(h3.GetNbinsY() + 2) for zbin in range(h3.GetNbinsZ() + 2)]


def loopH(h):
    if isinstance(h, ROOT.TH3):
        return loopH3(h)
    elif isinstance(h, ROOT.TH2):
        return loopH2(h)
    else:
        return range(h.GetNbinsX() + 2)


def printH2(h2, flow=True):
    for xbin, ybin in loopH2(h2):
        if not flow and (not xbin or not xbin or xbin == h2.GetNbinsX() + 1 or ybin == h2.GetNbinsY() + 1):
            continue
        print (xbin, ybin, h2.GetBinContent( xbin, ybin), "±", h2.GetBinError(xbin, ybin))


def stdHist(dataset, name, binning=None, xCut=True, cut1=0, cut2=1e8):
    h = dataset.getHist(name)
    if not h:
        return
    if isinstance(h, ROOT.TH2):
        if xCut:
            h = h.ProjectionY(randomName(), h.GetXaxis().FindFixBin(
                cut1), h.GetYaxis().FindFixBin(cut2))
        else:
            h = h.ProjectionX(randomName(), h.GetYaxis().FindFixBin(
                cut1), h.GetXaxis().FindFixBin(cut2))
    if binning:
        h = rebin(h, binning)
    #if (binning.any()): h = rebin(h, binning)
    appendFlowBin(h)
    h.SetYTitle(getYAxisTitle(h))
    return h


def stdHist2d(dataset, name, binning=None, xCut=True, cut1=0, cut2=1e8):
    h = dataset.getHist2d(name)
    if not h:
        return
    # if isinstance(h, ROOT.TH2):
       #if xCut: h = h.ProjectionY(randomName(), h.GetXaxis().FindFixBin(cut1), h.GetYaxis().FindFixBin(cut2))
       # else:    h = h.ProjectionX(randomName(), h.GetYaxis().FindFixBin(cut1), h.GetXaxis().FindFixBin(cut2))
    #print binning
    if binning:
        h = rebin2d(h, *binning)
    #if (binning.any()): h = rebin(h, binning)
    appendFlowBin2d(h)
    # h.SetYTitle(getYAxisTitle(h))
    return h



def stdHistWithoutNGenWithWeights(dataset, name, arWeights, binning=None, xCut=True, cut1=0, cut2=1e8):
    h = dataset.getHistWithoutNGenWithWeights(name, arWeights)
    if not h:
        return
    if isinstance(h, ROOT.TH2):
        if xCut:
            h = h.ProjectionY(randomName(), h.GetXaxis().FindFixBin(
                cut1), h.GetYaxis().FindFixBin(cut2))
        else:
            h = h.ProjectionX(randomName(), h.GetYaxis().FindFixBin(
                cut1), h.GetXaxis().FindFixBin(cut2))
    if binning:
        h = rebin(h, binning)
    #if (binning.any()): h = rebin(h, binning)
    appendFlowBin(h)
    h.SetYTitle(getYAxisTitle(h))
    return h


def getEnvelopeHists(hlist):
    hUp = hlist[0].Clone(randomName())
    hDn = hlist[0].Clone(randomName())

    for h in hlist:
        for b in loopH(h):
            c = h.GetBinContent(b)
            if c > hUp.GetBinContent(b):
                hUp.SetBinContent(b, c)
            if c < hDn.GetBinContent(b):
                hDn.SetBinContent(b, c)
    return hUp, hDn


def integerContent(h, scaledByWidth=False):
    for bin in loopH(h):
        c = h.GetBinContent(bin)
        if scaledByWidth:
            c *= h.GetBinWidth(bin)
        c = np.nan_to_num(c)
        if abs(c - int(round(c))) > 1e-5:
            return False
    return True


def drawOpt(h, style):
    if style == "data":
        h.SetLineColor(ROOT.kBlack)
        h.SetMarkerColor(ROOT.kBlack)
        h.SetMarkerStyle(20)
        # h.SetMarkerSize(0.7)
        h.SetMarkerSize(1.)
        h.drawOption_ = "pz"
        if isinstance(h, ROOT.TH1):
            h.SetBinErrorOption(ROOT.TH1.kPoisson)
            # h.drawOption_="e0p0"
            # h.drawOption_ = "e0e1p0"
            h.drawOption_ = "x0e0e1p0x0"
            if integerContent(h):
                h.Sumw2(False)  # kPoisson uncertainties are drawn
    if style == "datalike":
        # h.SetLineColor(ROOT.kBlack)
        # h.SetMarkerColor(ROOT.kBlack)
        h.SetMarkerStyle(20)
        # h.SetMarkerSize(0.7)
        # h.SetMarkerSize(0.8)
        h.SetMarkerSize(1.0)
        # h.drawOption_ = "pze0"
        h.drawOption_ = "pz"
        if isinstance(h, ROOT.TH1):
            # h.drawOption_ = "e0e1p0"
            h.drawOption_ = "x0e0e1p0x0"
    elif style == "pre":
        h.SetLineColor(ROOT.kBlack)
        h.drawOption_ = "hist"
    elif style == "signal":
        # h.SetLineWidth(3)
        # h.SetLineWidth(2)
        h.SetLineWidth(2)
        # h.drawOption_ = "hist"
        h.drawOption_ = "hist"
    elif style == "line":
        h.SetLineWidth(2)
        h.drawOption_ = "histl"
    elif style == "smoothline":
        h.SetLineWidth(2)
        h.drawOption_ = "histc"
    elif style == "signalWithErr":
        # h.SetLineWidth(0)
        # h.drawOption_ = "hist"
        h.SetMarkerStyle(0)
        h.SetMarkerSize(0)
        # h.SetLineColor(ROOT.kGray)
        h.drawOption_ = "e2"
        # h.SetLineWidth(2)
        # h.drawOption_ = "e2 l"
        # h.drawOption_ = "e2 hist"
        # h.SetFillStyle(1001)
        h.SetFillStyle(3354)
        # h.SetFillColor(ROOT.kGray)
    elif style == "signale":
        # h.SetLineWidth(3)
        h.SetLineWidth(2)
        # h.SetLineWidth(1)
        # h.drawOption_ = "hist"
        h.drawOption_ = "hist e0"
    elif style == "statUnc":
        # h.SetLineWidth(5)
        h.SetLineWidth(10)
        h.SetMarkerStyle(0)
        h.SetMarkerSize(0)
        # h.SetLineColor(ROOT.kGray + 2)
        h.SetLineColor(ROOT.kGray + 1)
        # h.SetLineColor(ROOT.kGray)
        h.drawOption_ = "e2x0"
        # h.SetFillStyle(3254)
        h.SetFillStyle(0)
        h.SetFillColor(0)
        #h.drawOption_ = "e2"
    elif style == "statUncLikeTTH":
        # h.SetLineWidth(5)
        # h.SetLineWidth(2)
        # h.SetLineWidth(10)
        h.SetMarkerStyle(0)
        h.SetMarkerSize(0)
        h.SetLineColor(ROOT.kGray+1)
        # h.SetLineColor(ROOT.kGray)
        # h.drawOption_ = "e2x0"
        h.drawOption_ = "e2"
        # h.SetFillStyle(3254)
        h.SetFillStyle(1001)
        h.SetFillColor(ROOT.kGray+1)
        #h.drawOption_ = "e2"
    elif style == "totErr":
        h.SetMarkerStyle(0)
        h.SetMarkerSize(0)
        h.SetLineColor(ROOT.kGray)
        h.drawOption_ = "e2"
        h.SetFillStyle(1001)
        h.SetFillColor(ROOT.kGray)
    elif style == "totUnc":
        # h.SetFillStyle(3254)
        h.SetFillStyle(3354)
        # h.SetFillStyle(3454)
        h.SetMarkerSize(0)
        # h.SetFillColor(ROOT.kBlack)
        h.SetFillColor(ROOT.kGray + 3)
        h.drawOption_ = "e2"
    elif style == "sysUnc":
        # h.SetFillStyle(3245)
        h.SetFillStyle(3345)
        # h.SetFillStyle(3445)
        h.SetMarkerSize(0)
        # h.SetFillColor(ROOT.kRed)
        h.SetFillColor(ROOT.kRed + 1)
        # ROOT.gStyle.SetHatchesLineWidth(1.5)
        h.drawOption_ = "e2"
    elif style == "sysUncGraph":
        # h.SetFillStyle(3245)
        h.SetFillStyle(3445)
        # h.SetFillStyle(3001)
        # h.SetMarkerSize(0)
        h.SetFillColor(ROOT.kRed)
        #h.drawOption_ = "a2 p same"
        h.drawOption_ = "a2same"
        #h.drawOption_ = "p"
    elif style == "sys":
        c = h.GetLineColor()
        h.SetFillColor(c)
        h.SetMarkerColor(c)
        h.SetFillStyle(3333)
        h.drawOption_ = "e2"
    else:
        print ("Do not know what to do with draw option", style)


def getPaletteColor(f):
    # f should be a fraction from 0 to 1, such that the whole palette is used
    return ROOT.TColor.GetColorPalette(int(f * ROOT.TColor.GetNumberOfColors()))

def convertToYaml1D(outFolder, filename, unit_x, unit_y, name_x, name_y, binsX,
                    nominals, err_stat_up = None, err_stat_down = None, err_syst_up = None, err_syst_down = None, err_tot_up = None, err_tot_down = None):
    if not os.path.exists(outFolder):
        os.makedirs(outFolder)
    nBins = len(binsX)-1
    # print "-------------------"
    # print nominals
    # print binsX
    # print err_stat_up
    # print "-------------------"

    from math import floor, log10

    # roundN = [3-int(floor(log10(min(abs(err_tot_down[i]),abs(err_tot_up[i]))))) for i in range(nBins)]
    roundN = [6 for i in range(nBins) ]
    # print("Round to {0} digits".format(roundN))

    with open(outFolder+filename+".yaml","w") as yaml:
        yaml.write("\n")
        # x axis and bins
        yaml.write("independent_variables:\n")
        yaml.write("- header: {name: '"+name_x+"', units: '"+unit_x+"'}\n")
        yaml.write("  values:\n")
        for i in range(nBins):
            yaml.write("  - {low: "+str(binsX[i])+", high: "+str(binsX[i+1])+"}\n")
        yaml.write("\n")

        # y axis and entries
        yaml.write("dependent_variables:\n")
        yaml.write("- header: {name: '"+name_y+"', units: '"+unit_y+"'}\n")
        yaml.write("  values:\n")
        for i in range(nBins):
            yaml.write("  - value: "+str(round(nominals[i],roundN[i]))+"\n")
            yaml.write("    errors:\n")
            if err_tot_up is not None and err_tot_down is not None:
                yaml.write("    - asymerror:\n")
                yaml.write("        minus: -"+str(abs(round(err_tot_down[i],roundN[i])))+"\n")
                yaml.write("        plus: "+str(round(err_tot_up[i],roundN[i]))+"\n")
                yaml.write("      label: total\n")
            if err_stat_up is not None and err_stat_down is not None:
                yaml.write("    - asymerror:\n")
                yaml.write("        minus: -"+str(abs(round(err_stat_down[i],roundN[i])))+"\n")
                yaml.write("        plus: "+str(round(err_stat_up[i],roundN[i]))+"\n")
                yaml.write("      label: stat\n")
            if err_syst_up is not None and err_syst_down is not None:
                yaml.write("    - asymerror:\n")
                yaml.write("        minus: -"+str(abs(round(err_syst_down[i],roundN[i])))+"\n")
                yaml.write("        plus: "+str(round(err_syst_up[i],roundN[i]))+"\n")
                yaml.write("      label: syst\n")
        yaml.write("\n")

def convertToYaml2D(outFolder, filename, unit, binsX, mat):
    if not os.path.exists(outFolder):
        os.makedirs(outFolder)
    nBins = len(binsX)-1

    from math import floor, log10
    roundN = 2-int(floor(log10(max(abs(mat.flatten())))))
    # print roundN
    roundN = 6
    # print("Round to {0} digits".format(roundN))
    covMatRound = np.array([[round(mat[i,j],roundN) for j in range(nBins)] for i in range(nBins)])
    covMatInv = np.linalg.inv(covMatRound)
    print("--- rounded covariance matrix was successfully inverted!")
    # print(covMatInv)
    binsx = range(nBins)
    binsy = range(nBins)
    binsy = np.flip(binsy)

    with open(outFolder+filename+".yaml","w") as yaml:
        yaml.write("\n")
        # x axis bins
        yaml.write("independent_variables:\n")
        yaml.write(r"- header: {name: 'parton level $\rho$ bin number x'}"+"\n")
        yaml.write("  values:\n")
        for i in binsy:
            # for j in range(nBins):
            for j in binsx:
                yaml.write("  - {low: "+str(j-0.5)+", high: "+str(j+0.5)+"}\n")
        yaml.write("\n")
        # y axis bins
        yaml.write(r"- header: {name: 'parton level $\rho$ bin number y'}"+"\n")
        yaml.write("  values:\n")
        # for i in range(nBins):
        for i in binsy:
            # for j in range(nBins):
            for j in binsx:
                yaml.write("  - {low: "+str(i-0.5)+", high: "+str(i+0.5)+"}"+"\n")
        yaml.write("\n")

        # y axis and entries
        yaml.write("dependent_variables:\n")
        yaml.write(r"- header: {name: 'covariance', units: '"+unit+"'}"+"\n")
        yaml.write("  values:\n")
        # for i in range(nBins):
        for i in binsy:
            # for j in range(nBins):
            for j in binsx:
                yaml.write("  - value: "+str(covMatRound[i, j])+"\n")
        yaml.write("\n")


def getPoissonUnc(n):
    """http://prd.aps.org/abstract/PRD/v86/i1/e010001 (p.399)
    For the case of Poisson distributed n, the upper and lower limits on
    the mean value ν can be found from the Neyman procedure where the upper
    and lower limits are at confidence levels of 1 − α low and 1 − α up ,
    respectively, and F χ −1 2 is the quantile of the χ distribution
    (inverse of the cumulative distribution). The quantiles F χ −1 2 can be
    obtained from standard tables or from the ROOT routine TMath::ChisquareQuantile.
    For central confidence intervals at confidence level 1 − α, set α lo = α up = α/2.
    """

    # calculate x = 1-alpha ( approx 68% )
    x = ROOT.TMath.Erf(1. / sqrt(2))
    alpha = 1 - x

    # for central confidence intervals, alpha_lo =alpha_up = alpha/2
    alpha_lo = alpha / 2
    alpha_up = alpha / 2

    # confidence interval is [ xlo, xup ]
    xlo = 0.5 * ROOT.TMath.ChisquareQuantile(alpha_lo, 2 * n)
    xup = 0.5 * ROOT.TMath.ChisquareQuantile(1 - alpha_up, 2 * (n + 1))
    return n - xlo, xup - n


def getSysHisto(h, relUncert):
    hsys = h.Clone(randomName())
    for bin in range(hsys.GetNbinsX() + 2):
        c = hsys.GetBinContent(bin)
        if c > 1e-10:
            e = relUncert * c
            hsys.SetBinError(bin, e)
        elif hsys.GetBinContent(bin - 1) or hsys.GetBinContent(bin + 1):
            #print "here"
            # check if option "width" should be used
            # TODO: check if the weight agrees with the lumi+pu weight
            meanWeight = hsys.Integral(0, -1) / hsys.GetEntries()
            poissonZeroError = 1.8410216450098775
            e = meanWeight * poissonZeroError
            e /= hsys.GetBinWidth(bin) if style.divideByBinWidth else 1.
            #print e,meanWeight,hsys.Integral(0,-1),hsys.GetEntries()
            hsys.SetBinError(bin, e)
    return hsys


def iterate(h, axis="x"):
    if axis == "x":
        return range(h.GetNbinsX() + 2)
    elif axis == "y":
        return range(h.GetNbinsY() + 2)
    elif axis == "z":
        return range(h.GetNbinsZ() + 2)
    else:
        print ("Please specify correct axis")


def getAxis(h, ax="x"):
    ax = ax.lower()
    if ax == "x":
        return h.GetXaxis()
    elif ax == "y":
        return h.GetYaxis()
    elif ax == "z":
        return h.GetZaxis()
    else:
        print ("do not know what do do with ", ax)


def getProjection(h, ax="x", cutBin1=0, cutBin2=-1):
    ax = ax.lower()
    if ax == "x":
        return h.ProjectionX(randomName(), cutBin1, cutBin2)
    elif ax == "y":
        return h.ProjectionY(randomName(), cutBin1, cutBin2)
    else:
        print ("do not know what do do with ", ax)


def getSystFromDifference(h1, h2, changeStyle=True):
    out = h1.Clone(randomName())
    if changeStyle:
        drawOpt(out, "sys")
    for bin in range(out.GetNbinsX() + 2):
        c1 = h1.GetBinContent(bin)
        c2 = h2.GetBinContent(bin)
        out.SetBinContent(bin, 0.5 * (c1 + c2))
        out.SetBinError(bin, 0.5 * abs(c1 - c2))
    return out


def getSystFromEnvelopes(h0, hUp, hDn, changeStyle=True):
    out = h0.Clone(randomName())
    if changeStyle:
        drawOpt(out, "sys")
    for bin in range(out.GetNbinsX() + 2):
        c = h0.GetBinContent(bin)
        up = hUp.GetBinContent(bin)
        dn = hDn.GetBinContent(bin)
        out.SetBinError(bin, max(abs(up - c), abs(dn - c)))
    return out

def getCrossSectionWeight(filename, lumi=30000.):
    topxsec = 830.91

    short_fname = filename.split("/")[-1]
    short_fname.replace(".root","")

    f = ROOT.TFile.Open(filename, "READ")
    # print ("Opening ",filename)
    h = f.Get("weightedEvents")
    h.SetDirectory(0)
    # h = getFromFile(filename, "weightedEvents")
    nEventsTotal = h.GetBinContent(1)

    isData = False

    xSec = 1.
    if ("run201" in short_fname):
        xSec = 1.
        isData = True
    elif ("fromDilepton" in short_fname):
        xSec = topxsec * 0.10706
    elif ("fromLjets" in short_fname):
        xSec = topxsec * 0.44113
    elif ("fromHadronic" in short_fname):
        xSec = topxsec * 0.45441
    elif ("ttbar" in short_fname and not "ttbarW" in short_fname and not "ttbarZ" in short_fname):
        xSec = topxsec
    elif ("single" in short_fname and "tw" in short_fname and "NoFullyHadronicDecays" in short_fname):
        xSec = (35.85*(1 - 0.45441))
    elif ("single" in short_fname and "tw" in short_fname):
        xSec = (35.85)
    elif ("singletop" in short_fname and "_t" in short_fname):
        xSec = (136.02)
    elif ("singleantitop" in short_fname and "_t" in short_fname):
        xSec = (80.95)
    elif ("single" in short_fname and "_s" in short_fname):
        xSec = (10.32)
    elif ("ww" in short_fname):
        xSec = 118.7
    elif ("wz" in short_fname):
        xSec = 47.13
    elif ("zz" in short_fname):
        xSec = 16.523
    elif ("1050" in short_fname):
        xSec = 22635.1
    elif ("0j_amcatnlofxfx" in short_fname):
        xSec = 4620.52
    elif ("1j_amcatnlofxfx" in short_fname):
        xSec = 859.59
    elif ("2j_amcatnlofxfx" in short_fname):
        xSec = 338.26
    elif ("50inf_ht0040to0070" in short_fname):
        xSec = 310.7*1.23
    elif ("50inf_ht0070to0100" in short_fname):
        xSec = 169.9*1.23
    elif ("50inf_ht0100to0200" in short_fname):
        xSec = 147.40*1.23
    elif ("50inf_ht0200to0400" in short_fname):
        xSec = 40.99*1.23
    elif ("50inf_ht0400to0600" in short_fname):
        xSec = 5.678*1.23
    elif ("50inf_ht0600to0800" in short_fname):
        xSec = 1.367*1.23
    elif ("50inf_ht0800to1200" in short_fname):
        xSec = 0.6304*1.23
    elif ("50inf_ht1200to2500" in short_fname):
        xSec = 0.1514*1.23
    elif ("50inf_ht2500toINFT" in short_fname):
        xSec = 0.003565*1.23
    elif ("50inf" in short_fname):
        xSec = 3.*2075.14
    elif ("wtolnu" in short_fname):
        xSec = 61526.7
    elif ("ttgjets" in short_fname):
        xSec = 3.697
    elif ("ttbarWjetstolnu" in short_fname):
        xSec = 0.2043
    elif ("ttbarWjetstoqq" in short_fname):
        xSec = 0.4062
    elif ("ttbarZtollnunu" in short_fname):
        xSec = 0.2529
    elif ("ttbarZtoqq" in short_fname):
        xSec = 0.5297
    else:
        print ("SHOULD NOT BE HERE")
        xSec=1.

    # print ("Getting xsec weight for",short_fname,":")
    # print ("lumi:",lumi," xSec:",xSec,"nEventsTotal",nEventsTotal)

    f.Close()
    weight = 1.
    if isData:
        weight = 1.
    else:
        weight = lumi * xSec / nEventsTotal
    # print("->",lumi * xSec / nEventsTotal)
    # print("->",weight)
    return weight

def getSystFromVariance(h0, hList):
    import numpy
    out = h0.Clone(randomName())
    for bin in loopH(h0):
        cs = []
        for h in hList:
            cs.append(h.GetBinContent(bin))
        mean = numpy.mean(cs)
        out.SetBinError(
            bin, max(numpy.std(cs), abs(mean - out.GetBinContent(bin))))
    return out


def getSystBandGraph(hNominal, histoList, addMCStat = False):
    outGraph =  ROOT.TGraphAsymmErrors()
    # outGraph.SetDirectory(0)
    for bin in loopH(hNominal):
        xMin = hNominal.GetBinLowEdge(bin)
        xMax = hNominal.GetBinLowEdge(bin)+hNominal.GetBinWidth(bin)
        y = hNominal.GetBinContent(bin)
        x = xMin + (xMax - xMin) / 2;
        # nomVal = hNominal.GetBinContent(bin)
        totErrUp = 0.
        totErrDn = 0.
        for uncHist in histoList:
            val = uncHist.GetBinContent(bin)
            diff = val-y
            if (diff > 0.):
                totErrUp = totErrUp + diff**2.
            else:
                totErrDn = totErrDn + diff**2.

        if addMCStat:
            mcErr = hNominal.GetBinError(bin)
            totErrUp = totErrUp + mcErr**2.
            totErrDn = totErrDn + mcErr**2.

        totErrUp = numpy.sqrt(totErrUp)
        totErrDn = numpy.sqrt(totErrDn)

        outGraph.SetPoint(bin, x, y)
        outGraph.SetPointError(bin, x - xMin, xMax - x, totErrDn, totErrUp)
    return outGraph

def modifySaveName(name):
    replacements = {"(": "", ")": "", "&": "AND", ".": "p",
                    "/": "DIV", "<": "", ">": "", "*": "TIMES", "$": "DOLLAR"}
    # for a, b in replacements.iteritems():
    for a, b in iter(replacements.items()):
        name = name.replace(a, b)
    return name



############################### tree stuff ####################################


lumis = {
    "2015": (19502.,0.012),
    "2016APV": (19502.,0.012),
    "2016": (16812.,0.012),
    "2017": (41480.,0.023),
    "2018": (59830.,0.025),
    "2024": (109000.,0.025),
    "FR2": (137620,0.016),
    "FR2old": (137620,0.016),
    "F16": (36314,0.012),
}

intLumi15 = 19502.
intLumi16APV = 19502.
intLumi16 = 16812.
intLumi17 = 41480.
intLumi18 = 59830.
intLumiFR2 = 137620
intLumiF16 = 36314
intLumi24 = 109000.

class Label:
    # Create labels
    # Usage:
    # * With Labels(), all default labels will be printed
    # * With Labels(False), the method is only initiated and labels can be modified before calling the 'draw' method

    cmsEnergy = 13  # TeV

    def draw(self):
        varDict = vars(self)
        # for varName, obj in varDict.iteritems():
        for varName, obj in iter(varDict.items()):
            if isinstance(obj, ROOT.TLatex):
                obj.SetNDC()
                obj.Draw()

    # def __init__( self, drawAll=True, sim=False, status="Private Work", info="" ):
    # def __init__(self, drawAll=True, sim=False, status="Work in Progress", info="", year=None):
    def __init__(self, drawAll=True, sim=False, status="", info="", year=None):
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
            intLumi=intLumi24
        else:
            intLumi=0.
        saveStuff.append(self)
        # if status == "Private Work":
        if status == "Work in Progress":
            if sim:
                # self.cms = ROOT.TLatex( 0.2, .887, "#scale[0.76]{#font[52]{Private Work Simulation}}" )
                # self.cms = ROOT.TLatex( 0.2, .95, "#scale[0.76]{#font[52]{Private Work Simulation}}" )
                # self.cms = ROOT.TLatex( 0.2, .95, "#font[61]{CMS} #scale[0.76]{#font[52]{Work in Progress Simulation}}" )
                # self.cms = ROOT.TLatex( 0.15, .95, "#font[61]{CMS} #scale[0.76]{#font[52]{Work in Progress Simulation}}" )
                self.cms = ROOT.TLatex(
                    # 0.16, .92, "#splitline{#font[61]{CMS} #scale[0.76]{#font[52]{Work in Progress}}}{#scale[0.76]{#font[52]{  Simulation}}}")
                    # 0.16, .95, "#splitline{#font[61]{CMS} #scale[0.76]{#font[52]{Work in Progress}}}{#scale[0.76]{#font[52]{  Simulation}}}")
                    # 0.16, .92, "#splitline{#font[61]{CMS} #scale[0.76]{#font[52]{Work in Progress}}}{#scale[0.76]{#font[52]{  Simulation}}}")
                    0.18, .85, "#splitline{#font[61]{CMS} #scale[0.76]{#font[52]{Private Work}}}{#scale[0.76]{#font[52]{Simulation}}}")
            else:
                # self.pub = ROOT.TLatex( 0.2, .887, "#font[61]{CMS} #scale[0.76]{#font[52]{%s}}"%status )
                # self.pub = ROOT.TLatex(
                #     0.15, .95, "#font[61]{CMS} #scale[0.76]{#font[52]{%s}}" % status)
                self.pub = ROOT.TLatex(
                    # 0.28, .95, "#font[61]{CMS} #scale[0.68]{#font[52]{%s}}" % status)
                    # 0.16, .95, "#font[61]{CMS} #scale[0.68]{#font[52]{%s}}" % status)
                    # 0.18, .85, "#font[61]{CMS} #scale[0.68]{#font[52]{%s}}" % status)
                    # 0.18, .87, "#font[61]{CMS} #scale[0.68]{#font[52]{%s}}" % status)
                    0.18, .87, "#font[61]{CMS}")
                self.pub2 = ROOT.TLatex(0.25, .95, "#scale[0.68]{#font[52]{%s}}" % status)
        else:
            if sim:
                self.cms = ROOT.TLatex(
                    # 0.16, .948, "#font[61]{CMS} #scale[0.76]{#font[52]{%s}}" % status)
                    # 0.16, .948, "#scale[0.76]{#font[52]{%s}}" % status)
                    # 0.16, .95, "#scale[0.76]{#font[52]{%s}}" % status)
                    # 0.16, .95, "#font[61]{CMS} #scale[0.76]{#font[52]{%s}}" % status)
                    # 0.18, .87, "#font[61]{CMS} #scale[0.76]{#font[52]{%s}}" % status)
                    # 0.18, .85, "#splitline{#font[61]{CMS}}{#scale[0.76]{#font[52]{  Simulation}}}")
                    # 0.19, .85, "#splitline{#font[61]{CMS}}{#scale[0.76]{#font[52]{  Simulation}}}")
                    0.19, .85, "#splitline{#font[61]{CMS} #scale[0.76]{#font[52]{%s}}}{#scale[0.76]{#font[52]{Simulation}}}" % status)
                # self.sim = ROOT.TLatex(
                #     0.16, 0.902, "#scale[0.76]{#font[52]{  Simulation}}")
                # 0.2, .887, "#font[61]{CMS} #scale[0.76]{#font[52]{Simulation}}")
            else:
                # self.cms = ROOT.TLatex(0.2, .887, "#font[61]{CMS}")
                self.cms = ROOT.TLatex(
                    # 0.16, .948, "#font[61]{CMS} #scale[0.76]{#font[52]{%s}}" % status)
                    # 0.16, .948, "#scale[0.76]{#font[52]{%s}}" % status)
                    # 0.16, .95, "#scale[0.76]{#font[52]{%s}}" % status)
                    # 0.16, .95, "#font[61]{CMS} #scale[0.76]{#font[52]{%s}}" % status)
                    # 0.18, .87, "#font[61]{CMS} #scale[0.76]{#font[52]{%s}}" % status)
                    0.19, .87, "#font[61]{CMS} #scale[0.76]{#font[52]{%s}}" % status)
            # self.pub = ROOT.TLatex(
            #     0.2, .857, "#scale[0.76]{#font[52]{%s}}" % status)
        if year:
            if year=="FR2" or year=="FR2old" or year=="2024":
                # self.lum = ROOT.TLatex(.62, .95,
                #                        "%.1f fb^{-1} (%s TeV)" % (np.round(intLumi / 1000., 0), self.cmsEnergy))
                # self.lum = ROOT.TLatex(.71, .95,"#scale[0.72]{%.1f fb^{-1} (%s TeV)}" % (np.round(intLumi / 1000., 0), self.cmsEnergy))
                lText = '{:.0f}'.format(intLumi / 1000.)
                # self.lum = ROOT.TLatex(.69, .95,"#scale[0.72]{%.0f fb^{-1} (%s TeV)}" % (intLumi / 1000., self.cmsEnergy))
                self.lum = ROOT.TLatex(.74, .95,"#scale[0.72]{%.0f fb^{-1} (%s TeV)}" % (intLumi / 1000., self.cmsEnergy))
            else:
                # self.lum = ROOT.TLatex(.62, .95,
                #                        "%.1f fb^{-1} (%s TeV)" % (intLumi / 1000., self.cmsEnergy))
                # self.lum = ROOT.TLatex(.67, .95, "#scale[0.72]{%.1f fb^{-1} (%s TeV)}" % (intLumi / 1000., self.cmsEnergy))
                # self.lum = ROOT.TLatex(.71, .95, "#scale[0.72]{%.1f fb^{-1} (%s TeV)}" % (intLumi / 1000., self.cmsEnergy))
                self.lum = ROOT.TLatex(.73, .95, "#scale[0.72]{%.1f fb^{-1} (%s TeV)}" % (intLumi / 1000., self.cmsEnergy))
        if info:
            # self.info = ROOT.TLatex(.15, .95, info)
            self.info = ROOT.TLatex(.16, .95, info)
        #if info: self.info = ROOT.TLatex( .85, .85, info )

        if drawAll:
            self.draw()

class Label2D:
    # Create labels
    # Usage:
    # * With Labels(), all default labels will be printed
    # * With Labels(False), the method is only initiated and labels can be modified before calling the 'draw' method

    cmsEnergy = 13  # TeV

    def draw(self):
        varDict = vars(self)
        for varName, obj in iter(varDict.items()):
            if isinstance(obj, ROOT.TLatex):
                obj.SetNDC()
                obj.Draw()

    def __init__(self, drawAll=True, sim=False, status="", info="", year=None):
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
            intLumi=intLumi24
        else:
            intLumi=0.
        saveStuff.append(self)
        if status == "Work in Progress":
            if sim:
                self.cms = ROOT.TLatex(
                    0.18, .85, "#splitline{#font[61]{CMS} #scale[0.76]{#font[52]{Private Work}}}{#scale[0.76]{#font[52]{Simulation}}}")
            else:
                self.pub = ROOT.TLatex(
                    0.18, .87, "#font[61]{CMS}")
                self.pub2 = ROOT.TLatex(0.25, .95, "#scale[0.68]{#font[52]{%s}}" % status)
        else:
            if sim:
                self.cms = ROOT.TLatex(
                    0.16, .85, "#splitline{#font[61]{CMS} #scale[0.76]{#font[52]{%s}}}{#scale[0.76]{#font[52]{Simulation}}}" % status)
            else:
                self.cms = ROOT.TLatex(
                    0.19, .87, "#font[61]{CMS} #scale[0.76]{#font[52]{%s}}" % status)
        if year:
            if year=="FR2" or year=="FR2old" or year=="2024":
                lText = '{:.0f}'.format(intLumi / 1000.)
                self.lum = ROOT.TLatex(.74, .95,"#scale[0.72]{%.0f fb^{-1} (%s TeV)}" % (intLumi / 1000., self.cmsEnergy))
            else:
                self.lum = ROOT.TLatex(.73, .95, "#scale[0.72]{%.1f fb^{-1} (%s TeV)}" % (intLumi / 1000., self.cmsEnergy))
        if info:
            self.info = ROOT.TLatex(.16, .95, info)

        if drawAll:
            self.draw()

class LabelFinalPlot:
    cmsEnergy = 13  # TeV

    def draw(self):
        varDict = vars(self)
        # for varName, obj in varDict.iteritems():
        for varName, obj in iter(varDict.items()):
            if isinstance(obj, ROOT.TLatex):
                obj.SetNDC()
                obj.Draw()

    def __init__(self, drawAll=True, sim=False, status="", info="", year=None):
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
            intLumi=intLumi24
        else:
            intLumi=0.
        saveStuff.append(self)
        if status == "Work in Progress":
            if sim:
                self.cms = ROOT.TLatex(
                    # 0.12, .84, "#splitline{#font[61]{CMS} #scale[0.76]{#font[52]{Work in Progress}}}{#scale[0.76]{#font[52]{  Simulation}}}")
                    0.07, .84, "#splitline{#font[61]{CMS} #scale[0.76]{#font[52]{Work in Progress}}}{#scale[0.76]{#font[52]{  Simulation}}}")
            else:
                self.pub = ROOT.TLatex(
                    # 0.12, .87, "#font[61]{CMS} #scale[0.68]{#font[52]{%s}}" % status)
                    0.07, .95, "#font[61]{CMS} #scale[0.68]{#font[52]{%s}}" % status)
        else:
            if sim:
                self.cms = ROOT.TLatex(
                    0.12, .87, "#scale[0.76]{#font[52]{%s}}" % status)
            else:
                # self.cms = ROOT.TLatex(
                #     0.12, .87, "#scale[0.76]{#font[52]{%s}}" % status)
                # self.pub = ROOT.TLatex(
                #     0.12, .87, "#font[61]{CMS} #scale[0.68]{#font[52]{%s}}" % status)
                # self.pub = ROOT.TLatex(0.07, .95, "#font[61]{CMS} #scale[0.68]{#font[52]{%s}}" % status)
                self.pub = ROOT.TLatex(0.07, .95, "#font[61]{CMS} #scale[0.68]{#font[52]{%s}}" % status)
        if year:
            if year=="FR2" or year=="FR2old" or year=="2024":
                self.lum = ROOT.TLatex(.85, .95,"#scale[0.72]{%.0f fb^{-1} (%s TeV)}" % (np.round(intLumi / 1000., 0), self.cmsEnergy))
            else:
                # self.lum = ROOT.TLatex(.83, .95, "#scale[0.72]{%.1f fb^{-1} (%s TeV)}" % (intLumi / 1000., self.cmsEnergy))
                # self.lum = ROOT.TLatex(.755, .95, "#scale[0.72]{%.1f fb^{-1} (%s TeV)}" % (intLumi / 1000., self.cmsEnergy))
                self.lum = ROOT.TLatex(.85, .95, "#scale[0.72]{%.1f fb^{-1} (%s TeV)}" % (intLumi / 1000., self.cmsEnergy))
        if info:
            self.info = ROOT.TLatex(.16, .95, info)

        if drawAll:
            self.draw()

class LabelEvolution:
    cmsEnergy = 13  # TeV

    def draw(self):
        varDict = vars(self)
        # for varName, obj in varDict.iteritems():
        for varName, obj in iter(varDict.items()):
            if isinstance(obj, ROOT.TLatex):
                obj.SetNDC()
                obj.Draw()

    def __init__(self, drawAll=True, sim=False, status="", info="", year=None):
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
            intLumi=intLumi24
        else:
            intLumi=0.
        saveStuff.append(self)
        if status == "Work in Progress":
            if sim:
                self.cms = ROOT.TLatex(
                    0.07, .84, "#splitline{#font[61]{CMS} #scale[0.76]{#font[52]{Work in Progress}}}{#scale[0.76]{#font[52]{  Simulation}}}")
            else:
                self.pub = ROOT.TLatex(
                    0.07, .95, "#font[61]{CMS} #scale[0.68]{#font[52]{%s}}" % status)
        else:
            if sim:
                self.cms = ROOT.TLatex(0.35, .95, "#scale[0.76]{#font[52]{%s}}" % status)
            else:
                self.pub = ROOT.TLatex(0.35, .95, "#font[61]{CMS} #scale[0.68]{#font[52]{%s}}" % status)
        if year:
            if year=="FR2" or year=="FR2old" or year=="2024":
                self.lum = ROOT.TLatex(.81, .95,"#scale[0.72]{%.1f fb^{-1} (%s TeV)}" % (np.round(intLumi / 1000., 0), self.cmsEnergy))
            else:
                self.lum = ROOT.TLatex(.85, .95, "#scale[0.72]{%.1f fb^{-1} (%s TeV)}" % (intLumi / 1000., self.cmsEnergy))
        if info:
            self.info = ROOT.TLatex(.16, .95, info)

        if drawAll:
            self.draw()


class Label2D(Label):
    def __init__(self, drawAll=True, sim=False, status="Work in Progress", info="", year="2016"):
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
            intLumi=intLumi24
        else:
            intLumi=0.
        saveStuff.append(self)
        cmsText = ""
        # if status != "Private Work":
        #     cmsText += "#font[61]{CMS}"
        if status == "Private Work":
            if sim:
                self.cms  = ROOT.TLatex(0.19, .87, "#font[61]{CMS}")
                self.rest = ROOT.TLatex(0.17, .95, "#scale[0.7]{#font[52]{%s}} #scale[0.7]{#font[52]{Simulation}}" % status)
            else:
                self.cms = ROOT.TLatex(
                    0.19, .87, "#font[61]{CMS} #scale[0.76]{#font[52]{%s}}" % status)
        #     # cmsText += ""
        # if sim:
        #     cmsText += " #scale[0.76]{#font[52]{Simulation}}"
        # if status:
        #     cmsText += " #scale[0.76]{#font[52]{%s}}" % status
        else:
            if sim:
                self.cms = ROOT.TLatex(
                    # 0.19, .85, "#splitline{#font[61]{CMS}}{#scale[0.76]{#font[52]{  Simulation}}}")
                    0.19, .85, "#splitline{#font[61]{CMS} #scale[0.76]{#font[52]{%s}}}{#scale[0.76]{#font[52]{  Simulation}}}" % status)
            else:
                self.cms = ROOT.TLatex(
                    0.19, .87, "#font[61]{CMS} #scale[0.76]{#font[52]{%s}}" % status)
            # self.cms = ROOT.TLatex(.15, .95, cmsText)
            # self.cms = ROOT.TLatex(.19, .87, cmsText)
            # cmsText = ""
        if info:
            self.info = ROOT.TLatex(0.2, .895, info)
        if year:
            if year=="FR2" or year=="FR2old" or year=="2024":
                self.lum = ROOT.TLatex(.45, .95, "%.1f fb^{-1} (%s TeV)" % (intLumi / 1000., self.cmsEnergy))
            else:
                # self.lum = ROOT.TLatex(.47, .95, "%.1f fb^{-1} (%s TeV)" % (intLumi / 1000., self.cmsEnergy))
                self.lum = ROOT.TLatex(.55, .95, "#scale[0.72]{%.1f fb^{-1} (%s TeV)}" % (intLumi / 1000., self.cmsEnergy))
        if drawAll:
            self.draw()
