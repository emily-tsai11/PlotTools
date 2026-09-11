import ROOT
import auxiliary as aux
from math import sqrt
import auxiliary as aux
import style
import numpy as np

def clearXaxisCurrentPad():
    # Delete label and title of all histograms in the current pad
    for ding in ROOT.gPad.GetListOfPrimitives():
        if isinstance(ding, ROOT.TH1) or isinstance(ding, ROOT.THStack):
            xaxis = ding.GetXaxis()
            xaxis.SetLabelSize(0)
            xaxis.SetLabelColor(0)
            xaxis.SetLabelOffset(1000)
            xaxis.SetTitle("")
            xaxis.SetTitleColor(0)
            xaxis.SetTitleSize(0)


def createBottomPad(r=.2):
    # r: the ratio in which the pad is splitted
    ROOT.gPad.SetBottomMargin(
        r + (1 - r) * ROOT.gPad.GetBottomMargin() - r * ROOT.gPad.GetTopMargin())
    rPad = ROOT.TPad("rPad", "ratio", 0, 0, 1, 1)
    rPad.SetTopMargin((1 - r) - (1 - r) *
                      rPad.GetBottomMargin() + r * rPad.GetTopMargin())
    rPad.SetFillStyle(3955)
    rPad.Draw()
    rPad.cd()
    rPad.SetLogy(0)
    ROOT.SetOwnership(rPad, False)
    return rPad


def convertToTH1(profile):
    h = profile.ProjectionX(aux.randomName())
    h.SetLineColor(profile.GetLineColor())
    return h


class Ratio:
    # def __init__(self, title, numerator, denominator, sysHisto=None, plotStat=True, ytitleOffset=1.6):
    # def __init__(self, title, numerator, denominator, sysHisto=None, plotStat=False, ytitleOffset=1.3):
    def __init__(self, title, numerator, denominator, sysHisto=None, plotStat=False, ytitleOffset=1.6):

        # convcert TProfiles to histograms
        if isinstance(numerator, ROOT.TProfile):
            numerator = convertToTH1(numerator)
        if isinstance(denominator, ROOT.TProfile):
            denominator = convertToTH1(denominator)

        self.title = title
        self.numerator = numerator
        self.denominator = denominator.Clone(aux.randomName())
        self.sysHisto = sysHisto
        self.ratio = numerator.Clone(aux.randomName())
        self.ratioStat = denominator.Clone(aux.randomName())
        self.ratioSys = sysHisto.Clone(
            aux.randomName()) if sysHisto else denominator.Clone(aux.randomName())
        self.totalUncert = denominator.Clone(aux.randomName())
        self.allowUnsymmetricYaxis = False

        # self.leg = ROOT.TLegend(0.2, 0.22, 0.28, 0.28)
        # self.leg = ROOT.TLegend(0.35, 0.21, 0.55, 0.28)
        # self.leg = ROOT.TLegend(0.65, 0.23, 0.97, 0.27)
        self.leg = ROOT.TLegend(0.25, 0.23, 0.57, 0.27)
        self.leg.SetFillStyle(0)

        self.plotStat = plotStat

        # self.ratio.drawOption_ = "e0"
        self.ratio.drawOption_ = "e0e1"

        # Set ratio properties
        for hist in [self.ratio, self.ratioSys, self.ratioStat, self.totalUncert]:
        # for hist in [self.ratio, self.ratioStat, self.totalUncert]:
            # hist.GetYaxis().SetNdivisions(2, 5, 2)
            if isinstance(hist, ROOT.TH1):
                # hist.SetTitleOffset(1.2, "Y")
                # # hist.SetLabelOffset(1.2, "X")
                # hist.SetYTitle(self.title)
                # hist.GetYaxis().SetNdivisions(510)
                hist.GetYaxis().SetNdivisions(504)
                hist.GetYaxis().SetTickLength(0.05)
                hist.GetYaxis().CenterTitle()
                # hist.SetTitleOffset(1.6, "Y")
                hist.SetTitleOffset(ytitleOffset, "Y")
                # hist.SetTitleOffset(1.2, "Y")
                hist.SetYTitle(self.title)

        aux.drawOpt(self.totalUncert, "totUnc")
        aux.drawOpt(self.ratioSys, "sysUnc")
        # aux.drawOpt(self.ratioStat, "statUnc")
        aux.drawOpt(self.ratioStat, "statUncLikeTTH")
        #aux.drawOpt(self.ratioStat, "totUnc")

    def calculateRatio(self):
        for bin in range(self.denominator.GetNbinsX() + 2):
            self.denominator.SetBinError(bin, 0)
        self.ratio.Divide(self.denominator)
        self.ratioGraph = ROOT.TGraphAsymmErrors(self.ratio)
        for bin in range(self.ratio.GetNbinsX() + 1):
            den = self.denominator.GetBinContent(bin)
            if den:
                self.ratioGraph.SetPointEYhigh(
                    bin - 1, self.numerator.GetBinErrorUp(bin) / den)
                self.ratioGraph.SetPointEYlow(
                    bin - 1, self.numerator.GetBinErrorLow(bin) / den)
                if aux.integerContent(self.numerator, True) and style.divideByBinWidth:
                    bw = self.numerator.GetBinWidth(bin)
                    entries = int(
                        round(self.numerator.GetBinContent(bin) * bw))
                    edn, eup = aux.getPoissonUnc(entries)
                    self.ratioGraph.SetPointEYhigh(bin - 1, eup / den / bw)
                    self.ratioGraph.SetPointEYlow(bin - 1, edn / den / bw)
            self.ratioGraph.SetPointEXhigh(bin - 1,0.)
            self.ratioGraph.SetPointEXlow(bin - 1,0.)

        self.ratioStat.Divide(self.denominator)
        if self.sysHisto and isinstance(self.sysHisto,ROOT.TH1):
            self.ratioSys.Divide(self.denominator)
            # for bin in range(self.denominator.GetNbinsX() + 2):
            #     self.totalUncert.SetBinContent(bin, 1)
            #     self.totalUncert.SetBinError(bin, sqrt(self.ratioSys.GetBinError(
            #         bin)**2 + self.ratioStat.GetBinError(bin)**2))

            # also here
            self.ratioSys.SetFillStyle(3154)
            self.ratioSys.SetMarkerSize(0)
            self.ratioSys.SetFillColor(ROOT.kGray +1)

        else:
            if isinstance(self.sysHisto,ROOT.TGraphAsymmErrors):
                self.ratioSys = self.sysHisto.Clone()
                for bin in aux.loopH(self.ratio):
                    d = self.denominator.GetBinContent(bin)
                    from ctypes import c_double
                    # d1, d2 = ROOT.Double(0), ROOT.Double(0)
                    d1, d2 = c_double(0), c_double(0)
                    # m = self.sysHisto.GetPoint(bin,d1,d2)
                    self.sysHisto.GetPoint(bin,d1,d2)
                    d1 = d1.value
                    d2 = d2.value
                    m = d2
                    xMin = self.ratio.GetBinLowEdge(bin)
                    xMax = self.ratio.GetBinLowEdge(bin)+self.ratio.GetBinWidth(bin)
                    # y = hNominal.GetBinContent(bin)
                    x = xMin + (xMax - xMin) / 2;
                    uncUp = self.sysHisto.GetErrorYhigh(bin)
                    uncDn = self.sysHisto.GetErrorYlow(bin)
                    uncXL = self.sysHisto.GetErrorXlow(bin)
                    uncXU = self.sysHisto.GetErrorXhigh(bin)
                    # print (d,m,x)
                    if m <0.001:
                        uncNewUp = 0.
                        uncNewDn = 0.
                    else:
                        uncNewUp = np.sqrt(d**2./m**4. * uncUp**2.)
                        uncNewDn = np.sqrt(d**2./m**4. * uncDn**2.)
                    self.ratioSys.SetPoint(bin, x , 1.)
                    self.ratioSys.SetPointError(bin, x - xMin, xMax - x, uncNewDn, uncNewUp)
                    # self.ratioSys.SetFillStyle(1001)
                    # self.ratioSys.SetFillStyle(3244)
                    self.ratioSys.SetFillStyle(3154)
                    self.ratioSys.SetMarkerSize(0)
                    self.ratioSys.SetFillColor(ROOT.kGray +1)
                    # self.ratioSys.Draw("same e2")

    def getYrange(self):
        # If no minimum or maximum is specified, choose a minimum from 0 to .5
        # and a maximum from 1.5 to 50
        yMin = 0
        minimum = self.ratio.GetBinContent(self.ratio.GetMaximumBin())
        for bin in range(self.ratio.GetNbinsX() + 2):
            minInBin = self.ratio.GetBinContent(bin)
            if minInBin < minimum and minInBin > 0:
                minimum = minInBin
        yMin = minimum * .95

        from math import ceil
        yMax = min(
            max(1.5, ceil(self.ratio.GetBinContent(self.ratio.GetMaximumBin()))), 50)
        yMax = self.ratio.GetBinContent(self.ratio.GetMaximumBin()) * 1.05

        yValues = [self.ratio.GetBinContent(
            bin) for bin in range(self.ratio.GetNbinsX() + 2)]
        yValues = filter(lambda a: a != 0, yValues)
        if self.allowUnsymmetricYaxis:
            return yMin, yMax
        else:
            yValuesAbsDiff = [abs(x - 1) for x in yValues]
            yValuesAbsDiff.sort()
            maxYDiff = yValuesAbsDiff[-1]
            y = 0.5
            if maxYDiff < 0.05:
                y = 0.05
            if maxYDiff < 0.01:
                y = 0.01

            return 1 - y, 1 + y

    def draw(self, yMin=.9, yMax=1.1, stack=None, onlyTotal=False):
        self.calculateRatio()

        #yMin, yMax = self.getYrange()
        for hist in [self.ratio, self.ratioSys, self.ratioStat, self.totalUncert]:
            hist.SetMinimum(yMin)
            hist.SetMaximum(yMax)
            # hist.SetLabelOffset(1.5, "X")

        clearXaxisCurrentPad()
        p = createBottomPad()
        # self.ratio.GetXaxis().SetLabelOffset(1.5)
        # self.ratioSys.GetXaxis().SetLabelOffset(1.5)
        # self.ratioStat.GetXaxis().SetLabelOffset(1.5)
        # self.totalUncert.GetXaxis().SetLabelOffset(1.5)
        # self.ratioGraph.GetXaxis().SetLabelOffset(1.5)

        if stack:
            aux.drawContributions(stack, yMin, yMax, self.title)

        # leg2 = ROOT.TLegend(0.05, 0.05, 0.9, 0.9)

        # leg.AddEntry(self.ratio, "ratio", "l")
        # leg.AddEntry(self.ratioSys, "ratioSys", "l")
        # leg.AddEntry(self.totalUncert, "total", "l")

        # if not self.isTrig:
            # self.ratioStat.Draw("e x0" + "same" if stack else "")
            # self.ratioStat.Draw("e2" + "same" if stack else "")
        if self.plotStat:
            self.ratioStat.Draw("e2same")
            # leg = ROOT.TLegend()
            # self.leg.AddEntry(self.ratioStat, "#sigma_{stat}^{sim.}", "lf")
            self.leg.AddEntry(self.ratioStat, "Stat. uncertainty (Pred.)", "lf")
        else:
            self.ratioStat.SetLineColor(ROOT.kWhite)
            self.ratioStat.SetFillColor(ROOT.kWhite)
            self.ratioStat.SetMarkerColor(ROOT.kWhite)
        #     # self.ratioStat.Draw("e x0" + "same" if stack else "")
        #     # self.ratioStat.Draw("e2" + "same" if stack else "")
            # self.ratioStat.Draw("e2same")
            self.ratioStat.Draw("e same")
        # self.ratioStat.Draw("same e2")
        if self.sysHisto:
            # if not onlyTotal:
            self.ratioSys.Draw("same e2")
            if self.plotStat:
                self.ratioStat.Draw("e2same")
            # if not self.isTrig:
            #     self.totalUncert.Draw("same e2")
        #self.ratio.Draw("same "+self.ratio.drawOption_)
        #self.ratioGraph.Draw("same pz0")
        self.ratioGraph.SetMarkerColor(ROOT.kBlack)
        self.ratioGraph.SetLineColor(ROOT.kBlack)
        # if not self.isTrig:

        self.ratioGraph.Draw("same p0")
        # self.ratioGraph.Draw("epX0ep")
        # else:
        #     self.ratioGraph.Draw("p0")


        if yMin < 1 and yMax > 1:
            oneLine = ROOT.TLine()
            oneLine.SetLineStyle(2)
            axis = self.ratio.GetXaxis()
            oneLine.DrawLine(axis.GetBinLowEdge(axis.GetFirst()),
                             1.0, axis.GetBinLowEdge(1 + axis.GetLast()), 1.0)
        # if not self.isTrig:
        if self.plotStat:
            self.leg.Draw()


class Ratio_pre:
    # def __init__(self, title, numerator, denominator, sysHisto=None, plotStat=True, ytitleOffset=1.6):
    def __init__(self, title, numerator, denominator, sysHisto=None, plotStat=False, ytitleOffset=1.3, addLine = None):

        # convcert TProfiles to histograms
        if isinstance(numerator, ROOT.TProfile):
            numerator = convertToTH1(numerator)
        if isinstance(denominator, ROOT.TProfile):
            denominator = convertToTH1(denominator)

        self.title = title
        self.numerator = numerator
        self.addLine = addLine
        self.denominator = denominator.Clone(aux.randomName())
        self.sysHisto = sysHisto
        self.ratio = numerator.Clone(aux.randomName())
        self.ratioaddLine = addLine.Clone(aux.randomName())
        self.ratioStat = denominator.Clone(aux.randomName())
        self.ratioSys = sysHisto.Clone(
            aux.randomName()) if sysHisto else denominator.Clone(aux.randomName())
        self.totalUncert = denominator.Clone(aux.randomName())
        self.allowUnsymmetricYaxis = False

        self.leg = ROOT.TLegend(0.32, 0.35, 0.64, 0.39)
        self.leg.SetFillStyle(0)

        self.plotStat = plotStat

        self.ratio.drawOption_ = "e0e1"

        # Set ratio properties
        for hist in [self.ratio, self.ratioSys, self.ratioStat, self.totalUncert, self.ratioaddLine]:
            if isinstance(hist, ROOT.TH1):
                hist.GetYaxis().SetNdivisions(504)
                hist.GetYaxis().SetTickLength(0.05)
                hist.GetYaxis().CenterTitle()
                hist.SetTitleOffset(ytitleOffset, "Y")
                hist.SetYTitle(self.title)

        aux.drawOpt(self.totalUncert, "totUnc")
        aux.drawOpt(self.ratioSys, "sysUnc")
        aux.drawOpt(self.ratioStat, "statUncLikeTTH")

    def calculateRatio(self):
        for bin in range(self.denominator.GetNbinsX() + 2):
            self.denominator.SetBinError(bin, 0)
        self.ratio.Divide(self.denominator)
        self.ratioaddLine.Divide(self.denominator)
        self.ratioGraph = ROOT.TGraphAsymmErrors(self.ratio)
        self.ratioGraphaddLine = ROOT.TGraphAsymmErrors(self.ratioaddLine)
        for bin in range(self.ratio.GetNbinsX() + 1):
            den = self.denominator.GetBinContent(bin)
            if den:
                self.ratioGraph.SetPointEYhigh(bin - 1, self.numerator.GetBinErrorUp(bin) / den)
                self.ratioGraph.SetPointEYlow(bin - 1, self.numerator.GetBinErrorLow(bin) / den)
                if aux.integerContent(self.numerator, True) and style.divideByBinWidth:
                    bw = self.numerator.GetBinWidth(bin)
                    entries = int(round(self.numerator.GetBinContent(bin) * bw))
                    edn, eup = aux.getPoissonUnc(entries)
                    self.ratioGraph.SetPointEYhigh(bin - 1, eup / den / bw)
                    self.ratioGraph.SetPointEYlow(bin - 1, edn / den / bw)
            self.ratioGraph.SetPointEXhigh(bin - 1,0.)
            self.ratioGraph.SetPointEXlow(bin - 1,0.)
            if den:
                # self.ratioGraphaddLine.SetPointEYhigh(bin - 1, self.addLine.GetBinErrorUp(bin) / den)
                self.ratioGraphaddLine.SetPointEYhigh(bin - 1,0)
                # self.ratioGraphaddLine.SetPointEYlow(bin - 1, self.addLine.GetBinErrorLow(bin) / den)
                self.ratioGraphaddLine.SetPointEYlow(bin - 1,0)
                if aux.integerContent(self.addLine, True) and style.divideByBinWidth:
                    bw = self.addLine.GetBinWidth(bin)
                    entries = int(round(self.addLine.GetBinContent(bin) * bw))
                    edn, eup = aux.getPoissonUnc(entries)
                    # self.ratioGraphaddLine.SetPointEYhigh(bin - 1, eup / den / bw)
                    self.ratioGraphaddLine.SetPointEYhigh(0)
                    # self.ratioGraphaddLine.SetPointEYlow(bin - 1, edn / den / bw)
                    self.ratioGraphaddLine.SetPointEYlow(0)
            self.ratioGraphaddLine.SetPointEXhigh(bin - 1,0.)
            self.ratioGraphaddLine.SetPointEXlow(bin - 1,0.)

        self.ratioStat.Divide(self.denominator)
        if self.sysHisto and isinstance(self.sysHisto,ROOT.TH1):
            self.ratioSys.Divide(self.denominator)

            # also here
            self.ratioSys.SetFillStyle(3154)
            self.ratioSys.SetMarkerSize(0)
            self.ratioSys.SetFillColor(ROOT.kGray +1)

        else:
            if isinstance(self.sysHisto,ROOT.TGraphAsymmErrors):
                self.ratioSys = self.sysHisto.Clone()
                for bin in aux.loopH(self.ratio):
                    d = self.denominator.GetBinContent(bin)
                    from ctypes import c_double
                    d1, d2 = c_double(0), c_double(0)
                    self.sysHisto.GetPoint(bin,d1,d2)
                    d1 = d1.value
                    d2 = d2.value
                    m = d2
                    xMin = self.ratio.GetBinLowEdge(bin)
                    xMax = self.ratio.GetBinLowEdge(bin)+self.ratio.GetBinWidth(bin)
                    x = xMin + (xMax - xMin) / 2
                    uncUp = self.sysHisto.GetErrorYhigh(bin)
                    uncDn = self.sysHisto.GetErrorYlow(bin)
                    uncXL = self.sysHisto.GetErrorXlow(bin)
                    uncXU = self.sysHisto.GetErrorXhigh(bin)
                    if m <0.001:
                        uncNewUp = 0.
                        uncNewDn = 0.
                    else:
                        uncNewUp = np.sqrt(d**2./m**4. * uncUp**2.)
                        uncNewDn = np.sqrt(d**2./m**4. * uncDn**2.)
                    self.ratioSys.SetPoint(bin, x , 1.)
                    self.ratioSys.SetPointError(bin, x - xMin, xMax - x, uncNewDn, uncNewUp)
                    self.ratioSys.SetFillStyle(3154)
                    self.ratioSys.SetMarkerSize(0)
                    self.ratioSys.SetFillColor(ROOT.kGray +1)

    def getYrange(self):
        # If no minimum or maximum is specified, choose a minimum from 0 to .5
        # and a maximum from 1.5 to 50
        yMin = 0
        minimum = self.ratio.GetBinContent(self.ratio.GetMaximumBin())
        for bin in range(self.ratio.GetNbinsX() + 2):
            minInBin = self.ratio.GetBinContent(bin)
            if minInBin < minimum and minInBin > 0:
                minimum = minInBin
        yMin = minimum * .95

        from math import ceil
        yMax = min(
            max(1.5, ceil(self.ratio.GetBinContent(self.ratio.GetMaximumBin()))), 50)
        yMax = self.ratio.GetBinContent(self.ratio.GetMaximumBin()) * 1.05

        yValues = [self.ratio.GetBinContent(
            bin) for bin in range(self.ratio.GetNbinsX() + 2)]
        yValues = filter(lambda a: a != 0, yValues)
        if self.allowUnsymmetricYaxis:
            return yMin, yMax
        else:
            yValuesAbsDiff = [abs(x - 1) for x in yValues]
            yValuesAbsDiff.sort()
            maxYDiff = yValuesAbsDiff[-1]
            y = 0.5
            if maxYDiff < 0.05:
                y = 0.05
            if maxYDiff < 0.01:
                y = 0.01

            return 1 - y, 1 + y

    def draw(self, yMin=.9, yMax=1.1, stack=None, onlyTotal=False):
        self.calculateRatio()

        for hist in [self.ratio, self.ratioSys, self.ratioStat, self.totalUncert]:
            hist.SetMinimum(yMin)
            hist.SetMaximum(yMax)

        clearXaxisCurrentPad()
        p = createBottomPad()

        if stack:
            aux.drawContributions(stack, yMin, yMax, self.title)
        if self.plotStat:
            self.ratioStat.Draw("e2same")
            self.leg.AddEntry(self.ratioStat, "Stat. uncertainty (Pred.)", "lf")
        
        else:
            self.ratioStat.SetLineColor(ROOT.kWhite)
            self.ratioStat.SetFillColor(ROOT.kWhite)
            self.ratioStat.SetMarkerColor(ROOT.kWhite)
            self.ratioStat.Draw("e same")
        if self.sysHisto:
            self.ratioSys.Draw("same e2")
            if self.plotStat:
                self.ratioStat.Draw("e2same")

        # self.ratioGraphaddLine.Draw("same l")
        self.ratioGraphaddLine.SetMarkerColor(ROOT.kRed+1)
        self.ratioGraphaddLine.SetLineColor(ROOT.kRed+1)
        self.ratioGraphaddLine.Draw("same l")

        self.ratioGraph.SetMarkerColor(ROOT.kBlack)
        self.ratioGraph.SetLineColor(ROOT.kBlack)

        self.ratioGraph.Draw("same p0")



        self.leg.AddEntry(self.ratioaddLine, "Pre-fit", "lf")

        if yMin < 1 and yMax > 1:
            oneLine = ROOT.TLine()
            oneLine.SetLineStyle(2)
            axis = self.ratio.GetXaxis()
            oneLine.DrawLine(axis.GetBinLowEdge(axis.GetFirst()),
                             1.0, axis.GetBinLowEdge(1 + axis.GetLast()), 1.0)
        if self.plotStat:
            self.leg.Draw()
        self.leg.Draw()



class Ratio2:
    def __init__(self, title, numerator, numerator2, denominator, sysHisto=None, isTrig=False):

        # convcert TProfiles to histograms
        if isinstance(numerator, ROOT.TProfile):
            numerator = convertToTH1(numerator)
        if isinstance(numerator2, ROOT.TProfile):
            numerator2 = convertToTH1(numerator)
        if isinstance(denominator, ROOT.TProfile):
            denominator = convertToTH1(denominator)

        self.title = title
        self.numerator = numerator
        self.numerator2 = numerator2
        self.denominator = denominator.Clone(aux.randomName())
        self.sysHisto = sysHisto
        self.ratio = numerator.Clone(aux.randomName())
        self.ratio2 = numerator2.Clone(aux.randomName())
        self.ratioStat = denominator.Clone(aux.randomName())
        self.ratioSys = sysHisto.Clone(
            aux.randomName()) if sysHisto else denominator.Clone(aux.randomName())
        self.totalUncert = denominator.Clone(aux.randomName())
        self.allowUnsymmetricYaxis = False

        # self.leg = ROOT.TLegend(0.2, 0.22, 0.28, 0.28)
        self.leg = ROOT.TLegend(0.25, 0.23, 0.57, 0.27)
        self.leg.SetFillStyle(0)

        self.isTrig = isTrig

        # self.ratio.drawOption_ = "e0"
        self.ratio.drawOption_ = "e0e1"

        # Set ratio properties
        for hist in [self.ratio,self.ratio2, self.ratioSys, self.ratioStat, self.totalUncert]:
            # hist.GetYaxis().SetNdivisions(2, 5, 2)
            # hist.SetTitleOffset(1.2, "Y")
            # # hist.SetLabelOffset(1.2, "X")
            # hist.SetYTitle(self.title)
            # hist.GetYaxis().SetNdivisions(510)
            hist.GetYaxis().SetNdivisions(504)
            hist.GetYaxis().CenterTitle()
            # hist.SetTitleOffset(1.6, "Y")
            # hist.SetTitleOffset(1.3, "Y")
            hist.SetTitleOffset(1.6, "Y")
            # hist.SetTitleOffset(1.2, "Y")
            hist.SetYTitle(self.title)

        aux.drawOpt(self.totalUncert, "totUnc")
        aux.drawOpt(self.ratioSys, "sysUnc")
        # aux.drawOpt(self.ratioStat, "statUnc")
        aux.drawOpt(self.ratioStat, "statUncLikeTTH")
        #aux.drawOpt(self.ratioStat, "totUnc")

    def calculateRatio(self):
        for bin in range(self.denominator.GetNbinsX() + 2):
            self.denominator.SetBinError(bin, 0)
        self.ratio.Divide(self.denominator)
        self.ratio2.Divide(self.denominator)
        self.ratioGraph = ROOT.TGraphAsymmErrors(self.ratio)
        self.ratioGraph2 = ROOT.TGraphAsymmErrors(self.ratio2)
        for bin in range(self.ratio.GetNbinsX() + 1):
            den = self.denominator.GetBinContent(bin)
            if den:
                self.ratioGraph.SetPointEYhigh(
                    bin - 1, self.numerator.GetBinErrorUp(bin) / den)
                self.ratioGraph.SetPointEYlow(
                    bin - 1, self.numerator.GetBinErrorLow(bin) / den)
                #print (self.numerator.GetBinErrorUp(bin)/den, self.numerator.GetBinErrorLow(bin)/den)
                if aux.integerContent(self.numerator, True) and style.divideByBinWidth:
                    #print "-----"
                    bw = self.numerator.GetBinWidth(bin)
                    entries = int(
                        round(self.numerator.GetBinContent(bin) * bw))
                    edn, eup = aux.getPoissonUnc(entries)
                    self.ratioGraph.SetPointEYhigh(bin - 1, eup / den / bw)
                    self.ratioGraph.SetPointEYlow(bin - 1, edn / den / bw)

                self.ratioGraph2.SetPointEYhigh(
                    bin - 1, self.numerator2.GetBinErrorUp(bin) / den)
                self.ratioGraph2.SetPointEYlow(
                    bin - 1, self.numerator2.GetBinErrorLow(bin) / den)
                #print (self.numerator.GetBinErrorUp(bin)/den, self.numerator.GetBinErrorLow(bin)/den)
                if aux.integerContent(self.numerator2, True) and style.divideByBinWidth:
                    #print ("-----")
                    bw2 = self.numerator2.GetBinWidth(bin)
                    entries2 = int(
                        round(self.numerator2.GetBinContent(bin) * bw))
                    edn2, eup2 = aux.getPoissonUnc(entries)
                    self.ratioGraph2.SetPointEYhigh(bin - 1, eup2 / den2 / bw2)
                    self.ratioGraph2.SetPointEYlow(bin - 1, edn2 / den2 / bw2)

        self.ratioStat.Divide(self.denominator)
        if self.sysHisto:
            self.ratioSys.Divide(self.denominator)
            for bin in range(self.denominator.GetNbinsX() + 2):
                self.totalUncert.SetBinContent(bin, 1)
                self.totalUncert.SetBinError(bin, sqrt(self.ratioSys.GetBinError(
                    bin)**2 + self.ratioStat.GetBinError(bin)**2))

    def getYrange(self):
        # If no minimum or maximum is specified, choose a minimum from 0 to .5
        # and a maximum from 1.5 to 50
        yMin = 0
        minimum = self.ratio.GetBinContent(self.ratio.GetMaximumBin())
        for bin in range(self.ratio.GetNbinsX() + 2):
            minInBin = self.ratio.GetBinContent(bin)
            if minInBin < minimum and minInBin > 0:
                minimum = minInBin
        yMin = minimum * .95

        from math import ceil
        yMax = min(
            max(1.5, ceil(self.ratio.GetBinContent(self.ratio.GetMaximumBin()))), 50)
        yMax = self.ratio.GetBinContent(self.ratio.GetMaximumBin()) * 1.05

        yValues = [self.ratio.GetBinContent(
            bin) for bin in range(self.ratio.GetNbinsX() + 2)]
        yValues = filter(lambda a: a != 0, yValues)
        if self.allowUnsymmetricYaxis:
            return yMin, yMax
        else:
            yValuesAbsDiff = [abs(x - 1) for x in yValues]
            yValuesAbsDiff.sort()
            maxYDiff = yValuesAbsDiff[-1]
            y = 0.5
            if maxYDiff < 0.05:
                y = 0.05
            if maxYDiff < 0.01:
                y = 0.01

            return 1 - y, 1 + y

    def draw(self, yMin=.9, yMax=1.1, stack=None, onlyTotal=False):
        self.calculateRatio()

        #yMin, yMax = self.getYrange()
        for hist in [self.ratio, self.ratio2, self.ratioSys, self.ratioStat, self.totalUncert]:
            hist.SetMinimum(yMin)
            hist.SetMaximum(yMax)
            # hist.SetLabelOffset(1.5, "X")

        clearXaxisCurrentPad()
        p = createBottomPad()
        # self.ratio.GetXaxis().SetLabelOffset(1.5)
        # self.ratioSys.GetXaxis().SetLabelOffset(1.5)
        # self.ratioStat.GetXaxis().SetLabelOffset(1.5)
        # self.totalUncert.GetXaxis().SetLabelOffset(1.5)
        # self.ratioGraph.GetXaxis().SetLabelOffset(1.5)

        if stack:
            aux.drawContributions(stack, yMin, yMax, self.title)

        # leg2 = ROOT.TLegend(0.05, 0.05, 0.9, 0.9)

        # leg.AddEntry(self.ratio, "ratio", "l")
        # leg.AddEntry(self.ratioSys, "ratioSys", "l")
        # leg.AddEntry(self.totalUncert, "total", "l")

        if not self.isTrig:
            # self.ratioStat.Draw("e x0" + "same" if stack else "")
            # self.ratioStat.Draw("e2" + "same" if stack else "")
            self.ratioStat.Draw("e2same")
        # leg = ROOT.TLegend()
            # self.leg.AddEntry(self.ratioStat, "#sigma_{stat}^{sim.}", "lf")
            self.leg.AddEntry(self.ratioStat, "Stat. uncertainty (Pred.)", "lf")
        else:
            self.ratioStat.SetLineColor(ROOT.kWhite)
            # self.ratioStat.Draw("e x0" + "same" if stack else "")
            self.ratioStat.Draw("e2same")
        # self.ratioStat.Draw("same e2")
        if self.sysHisto:
            if not onlyTotal:
                self.ratioSys.Draw("same e2")
            if not self.isTrig:
                self.totalUncert.Draw("same e2")
        #self.ratio.Draw("same "+self.ratio.drawOption_)
        #self.ratioGraph.Draw("same pz0")
        self.ratioGraph.SetMarkerColor(ROOT.kBlack)
        self.ratioGraph.SetLineColor(ROOT.kBlack)
        # self.ratioGraph.SetMarkerColor(ROOT.kRed)
        # self.ratioGraph.SetLineColor(ROOT.kRed)
        self.ratioGraph2.SetMarkerColor(ROOT.kGreen+2)
        self.ratioGraph2.SetLineColor(ROOT.kGreen+2)
        if not self.isTrig:
            self.ratioGraph.Draw("same p0")
            self.ratioGraph2.Draw("same p0")
        else:
            self.ratioGraph.Draw("p0")
            self.ratioGraph2.Draw("p0")

        if yMin < 1 and yMax > 1:
            oneLine = ROOT.TLine()
            oneLine.SetLineStyle(2)
            axis = self.ratio.GetXaxis()
            oneLine.DrawLine(axis.GetBinLowEdge(axis.GetFirst()),
                             1.0, axis.GetBinLowEdge(1 + axis.GetLast()), 1.0)
        if not self.isTrig:
            self.leg.Draw()











class Ratio_N:
    def __init__(self, title, numerators, denominator, sysHisto=None, bottomPadSize=0.2, plotStat=True):

        # convcert TProfiles to histograms
        # if isinstance(numerator, ROOT.TProfile):
        #     numerator = convertToTH1(numerator)
        # if isinstance(numerator2, ROOT.TProfile):
        #     numerator2 = convertToTH1(numerator)
        # if isinstance(denominator, ROOT.TProfile):
        #     denominator = convertToTH1(denominator)

        self.title = title
        self.numerators = numerators
        # self.numerator2 = numerator2
        self.denominator = denominator.Clone(aux.randomName())
        self.sysHisto = sysHisto
        self.ratios = [numerator.Clone(aux.randomName()) for numerator in numerators]
        self.ratioGraphs=[]
        # self.ratio2 = numerator2.Clone(aux.randomName())
        self.ratioStat = denominator.Clone(aux.randomName())
        self.ratioSys = sysHisto.Clone(
            aux.randomName()) if sysHisto else denominator.Clone(aux.randomName())
        self.totalUncert = denominator.Clone(aux.randomName())
        self.allowUnsymmetricYaxis = False

        # self.leg = ROOT.TLegend(0.2, 0.22, 0.28, 0.28)
        self.leg = ROOT.TLegend(0.25, 0.23, 0.57, 0.27)
        # self.leg = ROOT.TLegend(0.2, bottomPadSize*1.1, 0.28, bottomPadSize*1.4)
        self.leg.SetFillStyle(0)

        self.plotStat = plotStat

        self.bottomPadSize = bottomPadSize

        # self.ratio.drawOption_ = "e0e1"
        for h in self.ratios:
            h.drawOption_ = "e0e1"

        # Set ratio properties
        for hist in [h0 for h0 in self.ratios]+[ self.ratioSys, self.ratioStat, self.totalUncert]:
            # hist.GetYaxis().SetNdivisions(2, 5, 2)
            # hist.SetTitleOffset(1.2, "Y")
            # hist.SetYTitle(self.title)
            # hist.GetYaxis().SetNdivisions(510)
            hist.GetYaxis().SetNdivisions(504)
            hist.GetYaxis().CenterTitle()
            # hist.SetTitleOffset(1.6, "Y")
            if not isinstance(hist, ROOT.TGraphAsymmErrors): 
                hist.SetTitleOffset(1.3, "Y")
            # hist.SetTitleOffset(1.2, "Y")
                hist.SetYTitle(self.title)

        aux.drawOpt(self.totalUncert, "totUnc")
        aux.drawOpt(self.ratioSys, "sysUnc")
        aux.drawOpt(self.ratioStat, "statUncLikeTTH")

    def calculateRatio(self):
        for bin in range(self.denominator.GetNbinsX() + 2):
            self.denominator.SetBinError(bin, 0)
        for i in range(len(self.ratios)):
            self.ratios[i].Divide(self.denominator)
        # self.ratio2.Divide(self.denominator)
            # self.ratioGraphs[i] = ROOT.TGraphAsymmErrors(self.ratios[i])
            self.ratioGraphs.append(ROOT.TGraphAsymmErrors(self.ratios[i]))
        # self.ratioGraph2 = ROOT.TGraphAsymmErrors(self.ratio2)
            for bin in range(self.ratios[i].GetNbinsX() + 1):
                den = self.denominator.GetBinContent(bin)
                if den:
                    self.ratioGraphs[i].SetPointEYhigh(
                        bin - 1, self.numerators[i].GetBinErrorUp(bin) / den)
                    self.ratioGraphs[i].SetPointEYlow(
                        bin - 1, self.numerators[i].GetBinErrorLow(bin) / den)
                    if aux.integerContent(self.numerators[i], True) and style.divideByBinWidth:
                        bw = self.numerators[i].GetBinWidth(bin)
                        entries = int(
                            round(self.numerators[i].GetBinContent(bin) * bw))
                        edn, eup = aux.getPoissonUnc(entries)
                        self.ratioGraphs[i].SetPointEYhigh(bin - 1, eup / den / bw)
                        self.ratioGraphs[i].SetPointEYlow(bin - 1, edn / den / bw)

                # self.ratioGraph2.SetPointEYhigh(
                #     bin - 1, self.numerator2.GetBinErrorUp(bin) / den)
                # self.ratioGraph2.SetPointEYlow(
                #     bin - 1, self.numerator2.GetBinErrorLow(bin) / den)
                # if aux.integerContent(self.numerator2, True) and style.divideByBinWidth:
                #     bw2 = self.numerator2.GetBinWidth(bin)
                #     entries2 = int(
                #         round(self.numerator2.GetBinContent(bin) * bw))
                #     edn2, eup2 = aux.getPoissonUnc(entries)
                #     self.ratioGraph2.SetPointEYhigh(bin - 1, eup2 / den2 / bw2)
                #     self.ratioGraph2.SetPointEYlow(bin - 1, edn2 / den2 / bw2)

        self.ratioStat.Divide(self.denominator)
        # if self.sysHisto:
        #     self.ratioSys.Divide(self.denominator)
        #     for bin in range(self.denominator.GetNbinsX() + 2):
        #         self.totalUncert.SetBinContent(bin, 1)
        #         self.totalUncert.SetBinError(bin, sqrt(self.ratioSys.GetBinError(
        #             bin)**2 + self.ratioStat.GetBinError(bin)**2))

        if self.sysHisto and isinstance(self.sysHisto,ROOT.TH1):
            self.ratioSys.Divide(self.denominator)
            # for bin in range(self.denominator.GetNbinsX() + 2):
            #     self.totalUncert.SetBinContent(bin, 1)
            #     self.totalUncert.SetBinError(bin, sqrt(self.ratioSys.GetBinError(
            #         bin)**2 + self.ratioStat.GetBinError(bin)**2))

            # also here
            self.ratioSys.SetFillStyle(3154)
            self.ratioSys.SetMarkerSize(0)
            self.ratioSys.SetFillColor(ROOT.kGray +1)

        else:
            if isinstance(self.sysHisto,ROOT.TGraphAsymmErrors):
                self.ratioSys = self.sysHisto.Clone()
                for bin in aux.loopH(self.ratios[0]):
                    d = self.denominator.GetBinContent(bin)
                    from ctypes import c_double
                    # d1, d2 = ROOT.Double(0), ROOT.Double(0)
                    d1, d2 = c_double(0), c_double(0)
                    # m = self.sysHisto.GetPoint(bin,d1,d2)
                    self.sysHisto.GetPoint(bin,d1,d2)
                    d1 = d1.value
                    d2 = d2.value
                    m = d2
                    xMin = self.ratios[0].GetBinLowEdge(bin)
                    xMax = self.ratios[0].GetBinLowEdge(bin)+self.ratios[0].GetBinWidth(bin)
                    # y = hNominal.GetBinContent(bin)
                    x = xMin + (xMax - xMin) / 2
                    uncUp = self.sysHisto.GetErrorYhigh(bin)
                    uncDn = self.sysHisto.GetErrorYlow(bin)
                    uncXL = self.sysHisto.GetErrorXlow(bin)
                    uncXU = self.sysHisto.GetErrorXhigh(bin)
                    # print (d,m,x)
                    if m <0.001:
                        uncNewUp = 0.
                        uncNewDn = 0.
                    else:
                        uncNewUp = np.sqrt(d**2./m**4. * uncUp**2.)
                        uncNewDn = np.sqrt(d**2./m**4. * uncDn**2.)
                    self.ratioSys.SetPoint(bin, x , 1.)
                    self.ratioSys.SetPointError(bin, x - xMin, xMax - x, uncNewDn, uncNewUp)
                    # self.ratioSys.SetFillStyle(1001)
                    # self.ratioSys.SetFillStyle(3244)
                    self.ratioSys.SetFillStyle(3154)
                    self.ratioSys.SetMarkerSize(0)
                    self.ratioSys.SetFillColor(ROOT.kGray +1)
                    # self.ratioSys.Draw("same e2")

    def getYrange(self):
        # If no minimum or maximum is specified, choose a minimum from 0 to .5
        # and a maximum from 1.5 to 50
        yMin = 0
        for i in range(len(self.ratios)):
            minimum = self.ratios[i].GetBinContent(self.ratios[i].GetMaximumBin())
            for bin in range(self.ratios[i].GetNbinsX() + 2):
                minInBin = self.ratios[i].GetBinContent(bin)
                if minInBin < minimum and minInBin > 0:
                    minimum = minInBin
            yMin = minimum * .95

            from math import ceil
            yMax = min(
                max(1.5, ceil(self.ratios[i].GetBinContent(self.ratios[i].GetMaximumBin()))), 50)
            yMax = self.ratios[i].GetBinContent(self.ratios[i].GetMaximumBin()) * 1.05

            yValues = [self.ratios[i].GetBinContent(
                bin) for bin in range(self.ratios[i].GetNbinsX() + 2)]
            yValues = filter(lambda a: a != 0, yValues)

        # print (yMin, yMax)
        if self.allowUnsymmetricYaxis:
            return yMin, yMax
        else:
            yValuesAbsDiff = [abs(x - 1) for x in yValues]
            yValuesAbsDiff.sort()
            maxYDiff = yValuesAbsDiff[-1]
            y = 0.5
            if maxYDiff < 0.05:
                y = 0.05
            if maxYDiff < 0.01:
                y = 0.01

            return 1 - y, 1 + y

    def draw(self, yMin=.9, yMax=1.1, stack=None, onlyTotal=False):
        self.calculateRatio()

        for hist in [h0 for h0 in self.ratios]+[ self.ratioSys, self.ratioStat, self.totalUncert]:
            hist.SetMinimum(yMin)
            hist.SetMaximum(yMax)

        clearXaxisCurrentPad()
        p = createBottomPad(r = self.bottomPadSize)

        # if stack:
        #     aux.drawContributions(stack, yMin, yMax, self.title)
        #
        #     self.ratioStat.Draw("e2same")
        #     self.leg.AddEntry(self.ratioStat, "#sigma_{stat}^{sim.}", "lf")
        # else:
        # self.ratioStat.SetLineColor(ROOT.kWhite)
        # self.ratioStat.Draw("e2same")
        # if self.plotStat:
        #     self.ratioStat.SetLineColor(ROOT.kWhite)
        #     # self.ratioStat.SetFillColor(ROOT.kWhite)
        #     # self.ratioStat.SetMarkerColor(ROOT.kWhite)
        #     self.ratioStat.Draw("e2same")
        #     # self.leg.AddEntry(self.ratioStat, "#sigma_{stat}^{sim.}", "lf")
        #     # self.leg.AddEntry(self.ratioStat, "#sigma_{stat}^{sim.}", "f")
        #     self.leg.AddEntry(self.ratioStat, "Stat. uncertainty (Pred.)", "lf")
        if self.plotStat:
            self.ratioStat.Draw("e2same")
            # leg = ROOT.TLegend()
            # self.leg.AddEntry(self.ratioStat, "#sigma_{stat}^{sim.}", "lf")
            self.leg.AddEntry(self.ratioStat, "Stat. uncertainty (Pred.)", "lf")
        else:
            self.ratioStat.SetLineColor(ROOT.kWhite)
            self.ratioStat.SetFillColor(ROOT.kWhite)
            self.ratioStat.SetMarkerColor(ROOT.kWhite)
            self.ratioStat.Draw("e2same")
        if self.sysHisto:
            if not onlyTotal:
                if self.plotStat:
                    self.ratioStat.Draw("e2same")
                self.ratioSys.Draw("same e2")
                # self.totalUncert.Draw("same e2")

        # self.ratioGraph.SetMarkerColor(ROOT.kBlack)
        # self.ratioGraph.SetLineColor(ROOT.kBlack)
        # self.ratioGraph2.SetMarkerColor(ROOT.kGreen+2)
        # self.ratioGraph2.SetLineColor(ROOT.kGreen+2)
        for ig, graph in enumerate(self.ratioGraphs):
            graph.Draw("same p0")
            # self.ratioGraph2.Draw("same p0")
        # else:
        #     self.ratioGraph.Draw("p0")
        #     self.ratioGraph2.Draw("p0")

        if yMin < 1 and yMax > 1:
            oneLine = ROOT.TLine()
            oneLine.SetLineStyle(2)
            axis = self.ratios[0].GetXaxis()
            oneLine.DrawLine(axis.GetBinLowEdge(axis.GetFirst()),
                             1.0, axis.GetBinLowEdge(1 + axis.GetLast()), 1.0)
        self.leg.Draw()




class Ratio_N_finalPlot:
    def __init__(self, title, numerators, numerators_histo, denominator, sysHisto=None, bottomPadSize=0.2, plotStat=False):
        self.title = title
        self.numerators = numerators
        self.numerators_histo = numerators_histo
        self.denominator = denominator.Clone(aux.randomName())
        self.sysHisto = sysHisto
        self.ratios = [numerator.Clone(aux.randomName()) for numerator in numerators]
        self.ratios_h = [numerator.Clone(aux.randomName()) for numerator in numerators_histo]
        self.ratioGraphs=[]
        self.ratioHistos=[]
        self.ratioStat = denominator.Clone(aux.randomName())
        self.ratioSys = sysHisto.Clone(
            aux.randomName()) if sysHisto else denominator.Clone(aux.randomName())
        self.allowUnsymmetricYaxis = False

        self.leg = ROOT.TLegend(0.2, 0.22, 0.28, 0.28)
        self.leg.SetFillStyle(0)

        self.plotStat = plotStat

        self.bottomPadSize = bottomPadSize

        for h in self.ratios:
            h.drawOption_ = "e0e1"

        # Set ratio properties
        for hist in [h0 for h0 in self.ratios]+[ self.ratioSys, self.ratioStat]+[h0 for h0 in self.ratios_h]:
            # hist.GetYaxis().SetNdivisions(2, 5, 2)
            # hist.GetYaxis().SetNdivisions(510)
            hist.GetYaxis().SetNdivisions(504)
            hist.GetYaxis().CenterTitle()
            # hist.SetTitleOffset(1.6, "Y")
            hist.SetTitleOffset(1.3, "Y")
            # hist.SetTitleOffset(1.2, "Y")
            hist.SetYTitle(self.title)

        # aux.drawOpt(self.ratioSys, "sysUnc")
        aux.drawOpt(self.ratioSys, "totErr")
        aux.drawOpt(self.ratioStat, "statUncLikeTTH")

    def calculateRatio(self):
        for bin in range(self.denominator.GetNbinsX() + 2):
            self.denominator.SetBinError(bin, 0)
        for i in range(len(self.ratios)):
            self.ratios[i].Divide(self.denominator)
            self.ratioGraphs.append(ROOT.TGraphAsymmErrors(self.ratios[i]))
            for bin in range(self.ratios[i].GetNbinsX() + 1):
                den = self.denominator.GetBinContent(bin)
                if den:
                    self.ratioGraphs[i].SetPointEYhigh(
                        bin - 1, self.numerators[i].GetBinErrorUp(bin) / den)
                    self.ratioGraphs[i].SetPointEYlow(
                        bin - 1, self.numerators[i].GetBinErrorLow(bin) / den)
                    if aux.integerContent(self.numerators[i], True) and style.divideByBinWidth:
                        bw = self.numerators[i].GetBinWidth(bin)
                        entries = int(
                            round(self.numerators[i].GetBinContent(bin) * bw))
                        edn, eup = aux.getPoissonUnc(entries)
                        self.ratioGraphs[i].SetPointEYhigh(bin - 1, eup / den / bw)
                        self.ratioGraphs[i].SetPointEYlow(bin - 1, edn / den / bw)
        for i in range(len(self.ratios_h)):
            self.ratios_h[i].Divide(self.denominator)
            self.ratios_h[i].drawOption_ = self.numerators_histo[i].drawOption_
            self.ratioHistos.append(self.ratios_h[i])

        self.ratioStat.Divide(self.denominator)
        if self.sysHisto:
            self.ratioSys.Divide(self.denominator)

    def getYrange(self):
        yMin = 0
        for i in range(len(self.ratios)):
            minimum = self.ratios[i].GetBinContent(self.ratios[i].GetMaximumBin())
            for bin in range(self.ratios[i].GetNbinsX() + 2):
                minInBin = self.ratios[i].GetBinContent(bin)
                if minInBin < minimum and minInBin > 0:
                    minimum = minInBin
            yMin = minimum * .95

            from math import ceil
            yMax = min(
                max(1.5, ceil(self.ratios[i].GetBinContent(self.ratios[i].GetMaximumBin()))), 50)
            yMax = self.ratios[i].GetBinContent(self.ratios[i].GetMaximumBin()) * 1.05

            yValues = [self.ratios[i].GetBinContent(
                bin) for bin in range(self.ratios[i].GetNbinsX() + 2)]
            yValues = filter(lambda a: a != 0, yValues)

        # print (yMin, yMax)
        if self.allowUnsymmetricYaxis:
            return yMin, yMax
        else:
            yValuesAbsDiff = [abs(x - 1) for x in yValues]
            yValuesAbsDiff.sort()
            maxYDiff = yValuesAbsDiff[-1]
            y = 0.5
            if maxYDiff < 0.05:
                y = 0.05
            if maxYDiff < 0.01:
                y = 0.01

            return 1 - y, 1 + y

    def draw(self, yMin=.9, yMax=1.1, stack=None, onlyTotal=False):
        self.calculateRatio()

        for hist in [h0 for h0 in self.ratios]+[ self.ratioSys, self.ratioStat]:
            hist.SetMinimum(yMin)
            hist.SetMaximum(yMax)

        clearXaxisCurrentPad()
        p = createBottomPad(r = self.bottomPadSize)

        if self.plotStat:
            self.ratioStat.SetLineColor(ROOT.kWhite)
            self.ratioStat.Draw("e2same")
            # self.leg.AddEntry(self.ratioStat, "#sigma_{stat}^{sim.}", "lf")
            self.leg.AddEntry(self.ratioStat, "Stat. uncertainty (Pred.)", "lf")
        if self.sysHisto:
            if not onlyTotal:
                if self.plotStat:
                    self.ratioStat.Draw("e2same")
                self.ratioSys.Draw("same e2")

        for graph in self.ratioGraphs:
            graph.Draw("same p0")
        for histo in self.ratioHistos:
            # print histo, histo.drawOption_
            if "e2" in histo.drawOption_:
                histo.Draw("same e2")
            else:
                histo.Draw("same hist")
            # histo.Draw("same hist")

        if yMin < 1 and yMax > 1:
            oneLine = ROOT.TLine()
            oneLine.SetLineStyle(2)
            axis = self.ratios[0].GetXaxis()
            oneLine.DrawLine(axis.GetBinLowEdge(axis.GetFirst()),
                             1.0, axis.GetBinLowEdge(1 + axis.GetLast()), 1.0)
        self.leg.Draw()
