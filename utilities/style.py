import ROOT

# own style options:
divideByBinWidth = False
# divideByBinWidth = True
minimumOne = True
additionalPoissonUncertainty = False

# https://colorbrewer2.org/?type=diverging&scheme=RdYlBu&n=11
# colorID0 = ROOT.TColor.GetFreeColorIndex()
color_0 = ROOT.TColor.GetColor(165,0,38)
color_1 = ROOT.TColor.GetColor(215,48,39)
color_2 = ROOT.TColor.GetColor(244,109,67)
color_3 = ROOT.TColor.GetColor(253,174,97)
color_4 = ROOT.TColor.GetColor(254,224,144)
color_5 = ROOT.TColor.GetColor(255,255,191)
color_6 = ROOT.TColor.GetColor(224,243,248)
color_7 = ROOT.TColor.GetColor(171,217,233)
color_8 = ROOT.TColor.GetColor(116,173,209)
color_9 = ROOT.TColor.GetColor(69,117,180)
color_9_1 = ROOT.TColor.GetColor(209, 221, 237)
color_9_2 = ROOT.TColor.GetColor(117, 154, 202)
color_9_3 = ROOT.TColor.GetColor(53,90,138)
color_9_4 = ROOT.TColor.GetColor(18,30,46)
color_10 = ROOT.TColor.GetColor(49,54,149)
color_10_1 = ROOT.TColor.GetColor(207, 209, 239)
color_10_2 = ROOT.TColor.GetColor(111, 116, 208)
color_10_3 = ROOT.TColor.GetColor(47, 52, 144)
color_10_4 = ROOT.TColor.GetColor(16, 17, 48)


def defaultStyle0():
    st = ROOT.TStyle("defaultStyle", "Sebastian's owns style")
    st.SetCanvasColor(ROOT.kWhite)
    st.SetCanvasBorderMode(0)
    st.SetFrameBorderMode(0)
    st.SetCanvasDefH(800)
    st.SetCanvasDefW(800)

    st.SetPadTickX(1)
    st.SetPadTickY(1)

    st.SetPadColor(ROOT.kWhite)

    # Margins:
    st.SetPadTopMargin(0.06)
    st.SetPadBottomMargin(0.12)
    st.SetPadLeftMargin(0.16)
    st.SetPadRightMargin(0.04)

    st.SetTitleFillColor(ROOT.kWhite)
    st.SetTitleBorderSize(0)

    # st.SetTitleOffset(1.1, "x")
    # st.SetTitleOffset(1.0, "x")
    st.SetTitleOffset(0.9, "x")
    # st.SetTitleOffset(1.6, "y")
    st.SetTitleOffset(1.3, "y")

    st.SetStatBorderSize(1)
    st.SetStatColor(0)

    st.SetLegendBorderSize(0)
    st.SetLegendFillColor(ROOT.kWhite)
    st.SetLegendFont(st.GetLabelFont())
    # st.SetLegendTextSize( st.GetLabelSize() ) not in current ROOT version

    st.SetOptStat(0)

    # textSize = 0.05
    # st.SetLabelSize(textSize, "xyz")
    # st.SetTitleSize(textSize, "xyz")
    # st.SetLabelSize(textSize, "xyz")
    st.SetLabelSize(0.04, "xyz")
    # st.SetTitleSize(0.04, "xyz")
    st.SetTitleSize(0.055, "xyz")

    st.SetTextFont(st.GetLabelFont())
    # st.SetTextSize(st.GetLabelSize())
    st.SetTextSize(0.05)

    # st.SetNdivisions(505, "xyz")
    st.SetNdivisions(510, "xyz")
    ROOT.TGaxis.SetMaxDigits(4)

    st.SetTickLength(0.03, "XYZ")
    st.SetStripDecimals(ROOT.kTRUE)
    st.SetLabelOffset(0.007, "XYZ")
    # st.SetLegendTextSize(0.02)

    st.SetPalette(56)
    st.SetNumberContours(999)

    # st.SetErrorX(1)
    # st.SetErrorX(0)

    st.cd()
    return st


# def style2d():
#     st = defaultStyle()
#     st.SetPadRightMargin(0.19)
#     # st.SetTitleOffset(1.35, "z")
#     st.SetTitleOffset(1.15, "z")
#     return st
# def style1d():
#     st = defaultStyle()
#     # st.SetPadRightMargin(0.19)
#     # st.SetTitleOffset(1.35, "z")
#     return st


# def setPaletteRWB():
#     # Sets the current palette to red -> white -> blue
#     from array import array
#     steps = array('d', [0.0, 0.5, 1.0])
#     red = array('d', [1.0, 1.0, 0.0])
#     green = array('d', [0.0, 1.0, 0.0])
#     blue = array('d', [0.0, 1.0, 1.0])
#     ROOT.TColor.CreateGradientColorTable(
#         len(steps), steps, red, green, blue, ROOT.gStyle.GetNumberContours())


# def setPaletteBWR():
#     # Sets the current palette to blue -> white -> red
#     from array import array
#     steps = array('d', [0.0, 0.5, 1.0])
#     red = array('d', [0.0, 1.0, 1.0])
#     green = array('d', [0.0, 1.0, 0.0])
#     blue = array('d', [1.0, 1.0, 0.0])
#     ROOT.TColor.CreateGradientColorTable(
#         len(steps), steps, red, green, blue, ROOT.gStyle.GetNumberContours())

# def setPalette(styletype):
#     from array import array
#     NRGBs = 9
#     NCont = 255
#     stops = [0.0000, 0.1250, 0.2500, 0.3750, 0.5000, 0.6250, 0.7500, 0.8750, 1.0000]

#     if styletype=="bird":
#         # #Bird
#         red   = [ 0.2082, 0.0592, 0.0780, 0.0232, 0.1802, 0.5301, 0.8186, 0.9956, 0.9764]
#         green = [ 0.1664, 0.3599, 0.5041, 0.6419, 0.7178, 0.7492, 0.7328, 0.7862, 0.9832]
#         blue  = [ 0.5293, 0.8684, 0.8385, 0.7914, 0.6425, 0.4662, 0.3499, 0.1968, 0.0539]
#     elif styletype=="light":
#         #Light Temperature
#         red   = [  31./255.,  71./255., 123./255., 160./255., 210./255., 222./255., 214./255., 199./255., 183./255.]
#         green = [  40./255., 117./255., 171./255., 211./255., 231./255., 220./255., 190./255., 132./255.,  65./255.]
#         blue  = [ 234./255., 214./255., 228./255., 222./255., 210./255., 160./255., 105./255.,  60./255.,  34./255.]
#     elif styletype=="rainbow":
#         # #Rainbow
#         red   = [  0./255.,   5./255.,  15./255.,  35./255., 102./255., 196./255., 208./255., 199./255., 110./255.]
#         green = [  0./255.,  48./255., 124./255., 192./255., 206./255., 226./255.,  97./255.,  16./255.,   0./255.]
#         blue  = [ 99./255., 142./255., 198./255., 201./255.,  90./255.,  22./255.,  13./255.,   8./255.,   2./255.]
#     elif styletype=="pastel":
#         # #Pastel
#         red   = [ 180./255., 190./255., 209./255., 223./255., 204./255., 228./255., 205./255., 152./255.,  91./255.]
#         green = [  93./255., 125./255., 147./255., 172./255., 181./255., 224./255., 233./255., 198./255., 158./255.]
#         blue  = [ 236./255., 218./255., 160./255., 133./255., 114./255., 132./255., 162./255., 220./255., 218./255.]
#     elif styletype=="cool":
#         # #Cool
#         red   = [  33./255.,  31./255.,  42./255.,  68./255.,  86./255., 111./255., 141./255., 172./255., 227./255.]
#         green = [ 255./255., 175./255., 145./255., 106./255.,  88./255.,  55./255.,  15./255.,   0./255.,   0./255.]
#         blue  = [ 255./255., 205./255., 202./255., 203./255., 208./255., 205./255., 203./255., 206./255., 231./255.]
#     else:
#         #Light Temperature
#         red   = [  31./255.,  71./255., 123./255., 160./255., 210./255., 222./255., 214./255., 199./255., 183./255.]
#         green = [  40./255., 117./255., 171./255., 211./255., 231./255., 220./255., 190./255., 132./255.,  65./255.]
#         blue  = [ 234./255., 214./255., 228./255., 222./255., 210./255., 160./255., 105./255.,  60./255.,  34./255.]

#     s = array('d', stops)
#     r = array('d', red)
#     g = array('d', green)
#     b = array('d', blue)
#     ROOT.TColor.CreateGradientColorTable(NRGBs, s, r, g, b, NCont)
#     ROOT.gStyle.SetNumberContours(NCont)


# def CATCMSStyle():
def defaultStyle():
    # global cmsStyle
    # if cmsStyle != None:
    #     del cmsStyle
    cmsStyle = ROOT.TStyle("cmsStyle", "Style for P-CMS")
    ROOT.gROOT.SetStyle(cmsStyle.GetName())
    ROOT.gROOT.ForceStyle()
    # for the canvas:
    cmsStyle.SetCanvasBorderMode(0)
    cmsStyle.SetCanvasColor(ROOT.kWhite)
    cmsStyle.SetCanvasDefH(800)  # Height of canvas
    cmsStyle.SetCanvasDefW(800)  # Width of canvas
    cmsStyle.SetCanvasDefX(0)  # Position on screen
    cmsStyle.SetCanvasDefY(0)
    cmsStyle.SetPadBorderMode(0)
    cmsStyle.SetPadColor(ROOT.kWhite)
    cmsStyle.SetPadGridX(False)
    cmsStyle.SetPadGridY(False)
    cmsStyle.SetGridColor(0)
    cmsStyle.SetGridStyle(3)
    cmsStyle.SetGridWidth(1)
    # For the frame:
    cmsStyle.SetFrameBorderMode(0)
    cmsStyle.SetFrameBorderSize(1)
    cmsStyle.SetFrameFillColor(0)
    cmsStyle.SetFrameFillStyle(0)
    cmsStyle.SetFrameLineColor(1)
    cmsStyle.SetFrameLineStyle(1)
    cmsStyle.SetFrameLineWidth(1)
    # For the histo:
    # cmsStyle.SetHistLineColor(1)
    # cmsStyle.SetHistLineStyle(0)
    # cmsStyle.SetHistLineWidth(1)
    # cmsStyle.SetEndErrorSize(2)
    # cmsStyle.SetMarkerStyle(20)
    # For the fit/function:
    cmsStyle.SetOptFit(1)
    cmsStyle.SetFitFormat("5.4g")
    cmsStyle.SetFuncColor(2)
    cmsStyle.SetFuncStyle(1)
    cmsStyle.SetFuncWidth(1)
    # For the date:
    cmsStyle.SetOptDate(0)
    # For the statistics box:
    cmsStyle.SetOptFile(0)
    cmsStyle.SetOptStat(0)  # To display the mean and RMS:   SetOptStat('mr')
    cmsStyle.SetStatColor(ROOT.kWhite)
    cmsStyle.SetStatFont(42)
    cmsStyle.SetStatFontSize(0.025)
    cmsStyle.SetStatTextColor(1)
    cmsStyle.SetStatFormat("6.4g")
    cmsStyle.SetStatBorderSize(1)
    cmsStyle.SetStatH(0.1)
    cmsStyle.SetStatW(0.15)
    # Margins:
    # cmsStyle.SetPadTopMargin(0.05)
    cmsStyle.SetPadTopMargin(0.06)
    # cmsStyle.SetPadBottomMargin(0.13)
    cmsStyle.SetPadBottomMargin(0.14)
    # cmsStyle.SetPadLeftMargin(0.16)
    cmsStyle.SetPadLeftMargin(0.18)
    cmsStyle.SetPadRightMargin(0.02)
    # For the Global title:
    cmsStyle.SetOptTitle(0)
    cmsStyle.SetTitleFont(42)
    cmsStyle.SetTitleColor(1)
    cmsStyle.SetTitleTextColor(1)
    cmsStyle.SetTitleFillColor(10)
    cmsStyle.SetTitleFontSize(0.05)
    # For the axis titles:
    cmsStyle.SetTitleColor(1, "XYZ")
    cmsStyle.SetTitleFont(42, "XYZ")
    cmsStyle.SetTitleSize(0.06, "XYZ")
    # cmsStyle.SetTitleXOffset(0.9)
    cmsStyle.SetTitleXOffset(0.96)
    # cmsStyle.SetTitleYOffset(1.25)
    cmsStyle.SetTitleYOffset(1.6)
    # For the axis labels:
    cmsStyle.SetLabelColor(1, "XYZ")
    cmsStyle.SetLabelFont(42, "XYZ")
    cmsStyle.SetLabelOffset(0.012, "XYZ")
    cmsStyle.SetLabelSize(0.05, "XYZ")
    # For the axis:
    cmsStyle.SetAxisColor(1, "XYZ")
    cmsStyle.SetStripDecimals(True)
    cmsStyle.SetTickLength(0.03, "XYZ")
    cmsStyle.SetNdivisions(510, "XYZ")
    cmsStyle.SetPadTickX(1)  # To get tick marks on the opposite side of the frame
    cmsStyle.SetPadTickY(1)
    # Change for log plots:
    cmsStyle.SetOptLogx(0)
    cmsStyle.SetOptLogy(0)
    cmsStyle.SetOptLogz(0)
    # Postscript options:
    cmsStyle.SetPaperSize(20.0, 20.0)
    # cmsStyle.SetHatchesLineWidth(5)
    # cmsStyle.SetHatchesSpacing(0.05)


    # # Set canvas dimensions and margins
    # W_ref = 800
    # H_ref = 800
    # extraSpace = 0.01

    # W = W_ref
    # H = H_ref
    # T = 0.07 * H_ref
    # B = 0.11 * H_ref
    # # L = 0.13 * H_ref
    # L = 0.15
    # # R = 0.03 * H_ref
    # R = 0.05

    # cmsStyle.SetPadLeftMargin(L / W + extraSpace)
    # cmsStyle.SetPadRightMargin(R / W)
    # # if with_z_axis:
    #     # cmsStyle.SetPadRightMargin(B / W + 0.03)
    # # cmsStyle.SetPadTopMargin(T / H)
    # cmsStyle.SetPadTopMargin(0.08)
    # cmsStyle.SetPadBottomMargin(B / H + 0.02)

    # y_offset = 1.2
    # cmsStyle.SetTitleOffset(y_offset, "y")
    # cmsStyle.SetTitleOffset(0.9, "x")

    cmsStyle.SetLegendBorderSize(0)
    cmsStyle.SetLegendFillColor(ROOT.kWhite)
    cmsStyle.SetLegendFont(42)
    # cmsStyle.SetLegendTextSize(0.04)
    cmsStyle.SetLegendTextSize(0.03)

    cmsStyle.SetTextFont(cmsStyle.GetLabelFont())

    cmsStyle.SetPalette(56)
    cmsStyle.SetNumberContours(999)

    cmsStyle.cd()

    return cmsStyle

def style2d():
    st = defaultStyle()
    st.SetPadRightMargin(0.19)
    # st.SetPadLeftMargin(0.19)
    # st.SetTitleOffset(1.35, "z")
    # st.SetTitleOffset(2.65, "z")
    st.SetTitleOffset(1.15, "z")
    st.SetPalette(ROOT.kViridis)
    return st

defaultStyle()
# CATCMSStyle()

# # not style, but similar
ROOT.gROOT.SetBatch()
ROOT.TH1.SetDefaultSumw2()
ROOT.TH2.SetDefaultSumw2()
ROOT.gROOT.ForceStyle()
# import cmsstyle as CMS