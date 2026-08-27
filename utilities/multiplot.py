import ROOT
import auxiliary as aux
# from datasets import my_own_order, orderNumbers
# my_own_order = ['t#bar{t}H(c#bar{c})','t#bar{t}H(b#bar{b})','t#bar{t}Z(c#bar{c})','t#bar{t}Z(b#bar{b})',
#                 't#bar{t}H(other)', 't#bar{t}Z(other)', 
#                 't#bar{t}+b#bar{b} 4FS', 't#bar{t}+b jets 4FS', 't#bar{t}+c#bar{c}', 't#bar{t}+c jets', 't#bar{t}+LF','Other']
my_own_order = ['t#bar{t}H(H#rightarrowc#bar{c})','t#bar{t}H(H#rightarrowb#bar{b})','t#bar{t}Z(Z#rightarrowc#bar{c})','t#bar{t}Z(Z#rightarrowb#bar{b})',
                't#bar{t}H(H#rightarrowother)', 't#bar{t}Z(Z#rightarrowother)', 
                't#bar{t}+#geq2b', 't#bar{t}+b', 't#bar{t}+#geq2c', 't#bar{t}+c', 't#bar{t}+light','Other']
orderNumbers = {key: i for i, key in enumerate(my_own_order)}

class Multiplot:
    def __init__(self, legCoords=None):
        self.hists = []
        self.histsToStack = []

        # todo: impmlement setter and getter
        self.minimum = None
        self.maximum = None

        #self.leg = ROOT.TLegend(.56,.59,.94,.915)
        # self.leg = ROOT.TLegend(.56, .69, .94, .915)
        if legCoords:
            self.leg = ROOT.TLegend(legCoords[0],legCoords[1],legCoords[2],legCoords[3])
        else:
            # self.leg = ROOT.TLegend(.52, .69, .94, .915)
            self.leg = ROOT.TLegend(.72, .69, .94, .915)
        self.leg.SetFillColor(ROOT.kWhite)
        self.leg.SetFillStyle(0)

    def add(self, h, label=""):
        h.SetName(label)
        self.hists.append(h)

    def addStack(self, h, label=""):
        h.SetName(label)
        self.histsToStack.append(h)

    def getMinimum(self):
        return min([h.GetMinimum(0) for h in self.hists + self.histsToStack if not isinstance(h, ROOT.THStack) and not isinstance(h, ROOT.TGraph)])

    def getMaximum(self):
        return max([h.GetMaximum() for h in self.hists])

    def getStack(self):
        stacks = [h for h in self.hists if isinstance(h, ROOT.THStack)]
        return stacks[0] if stacks else None

    def stackHists(self):
        if not self.histsToStack:
            return
        stack = ROOT.THStack()
        stack.SetTitle(";%s;%s" % (self.histsToStack[0].GetXaxis(
        ).GetTitle(), self.histsToStack[0].GetYaxis().GetTitle()))
        stack.drawOption_ = "hist"
        #stack.drawOption_ = "hist e2"
        for h in self.histsToStack:
            h.SetFillColor(h.GetLineColor())
            h.SetLineColor(ROOT.kBlack)
            stack.Add(h)

        self.hists.append(stack)

    def sortStackByIntegral(self):
        self.histsToStack = sorted(
            self.histsToStack, key=lambda x: x.Integral(0, -1))

    def sortStackByCustomOrder(self, inverted=False):
        if inverted:
            self.histsToStack = sorted(
                self.histsToStack, key=lambda x: orderNumbers[x.GetName()], reverse=False)
        else:
            self.histsToStack = sorted(
                self.histsToStack, key=lambda x: orderNumbers[x.GetName()], reverse=True)

    def Draw(self, legColumns=1, newLegOrder = None):

        if not self.hists and not self.histsToStack:
            return False
        self.stackHists()

        #minimum = 1e-5
        #minimum = 1e-3
        minimum = self.getMinimum()
        # minimum = 0.1
        #minimum = 0.001
        # maximum = 1.5*self.getMaximum()
        # maximum = 1.75*self.getMaximum()
        maximum = 2.2*self.getMaximum()
        # maximum = 1.95*self.getMaximum()
        # maximum = 1.8*self.getMaximum()
        # maximum = 10.1 * self.getMaximum()
        #maximum = 1.1*self.getMaximum()*100.
        #maximum = 0.1

        if self.maximum != None:
            maximum = self.maximum
        if self.minimum != None:
            minimum = self.minimum

        # Fill legend:
        # Data first
        for h in self.hists:
            if isinstance(h, ROOT.THStack):
                continue
            if not hasattr(h, "drawOption_"):
                # h.drawOption_ = ""
                h.drawOption_ = "pe1"
            if aux.dataLikeName(h.GetName()):
                # self.leg.AddEntry(h, h.GetName(), "pel")
                self.leg.AddEntry(h, h.GetName(), "pe1")

        # Stacked histograms
        for h in self.histsToStack[-1::-1]:
            # h.SetLineColor(0)
            self.leg.AddEntry(h, h.GetName(), "f")
        if legColumns==2:
            if not newLegOrder: self.leg.GetListOfPrimitives().Add(ROOT.TLegendEntry())
        # Other histograms
        for h in self.hists:
            if not h.GetName():
                continue
            if isinstance(h, ROOT.THStack):
                continue
            if aux.dataLikeName(h.GetName()):
                continue

            if "p" in h.drawOption_:
                # self.leg.AddEntry(h, h.GetName(), "ep")
                self.leg.AddEntry(h, h.GetName(), "ep1")
            elif "e2" in h.drawOption_:
                h.SetLineColor(0)
                # self.leg.AddEntry(h, h.GetName(), "epf")
                self.leg.AddEntry(h, h.GetName(), "ef")
                # self.leg.AddEntry(h, h.GetName(), "pze0")
            else:
                self.leg.AddEntry(h, h.GetName(), "l")
                # self.leg.AddEntry(h, h.GetName(), "ef")

        # change the order for drawing
        self.hists.reverse()
        for ih, h in enumerate(self.hists):
            import style
            if aux.dataLikeName(h.GetName()) and aux.integerContent(h, True) and style.divideByBinWidth:
                gr = ROOT.TGraphAsymmErrors(h)
                aux.saveStuff.append(gr)
                aux.drawOpt(gr, "Data")
                for p in range(gr.GetN()):
                    bw = h.GetBinWidth(p + 1)
                    entries = int(round(gr.GetY()[p] * bw))
                    edn, eup = aux.getPoissonUnc(entries)
                    gr.SetPointEYlow(p, edn / bw)
                    gr.SetPointEYhigh(p, eup / bw)
                gr.Draw(gr.drawOption_ + "same")
                # gr.RedrawAxis()
            else:
                if not ih:
                    h.SetMinimum(minimum)
                    h.SetMaximum(maximum)
                else:
                    h.drawOption_ += "same"
                h.Draw(h.drawOption_)
                # h.GetXaxis().RedrawAxis()

        # gPad.RedrawAxis()
        ROOT.gPad.RedrawAxis()

        # self.leg.SetNColumns(2)
        # self.leg.SetNColumns(1)
        self.leg.SetNColumns(legColumns)
        # self.leg.SetNColumns(3)
        # self.leg.Draw()
        # self.leg.Draw("same")
        if newLegOrder:
            self.leg.Clear()
            for entry in newLegOrder:
                # if aux.dataLikeName(h.GetName()):
                #     drawOption = "pe1"
                # elif if "p" in entry["object"].drawOption_:
                #     drawOption = "ep1"
                # elif if "e2" in entry["object"].drawOption_:
                #     drawOption = "ef"
                # else:
                #     drawOption = "l"
                # print (entry, newLegOrder[entry])
                if legColumns==2:
                    if newLegOrder[entry]["name"] == "Syst. uncertainty":
                        self.leg.GetListOfPrimitives().Add(ROOT.TLegendEntry())
                    if newLegOrder[entry]["name"] == "Total uncertainty":
                        self.leg.GetListOfPrimitives().Add(ROOT.TLegendEntry())
                self.leg.AddEntry(newLegOrder[entry]["object"], newLegOrder[entry]["name"], newLegOrder[entry]["drawOpt"])
            self.leg.SetNColumns(legColumns)
            # self.leg.GetListOfPrimitives().Add(ROOT.TLegendEntry())
            self.leg.Draw("same")
        else:
            self.leg.Draw("same")

        return True

    def draw(self):  # simple alias
        self.Draw()
