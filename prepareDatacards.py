import CombineHarvester.CombineTools.ch as ch
import ROOT
import os

inputdir = "test_withSyst/2018/"
outFolder = "datacards"
doAutoMCStats = False
use4FS = True
year = "2018"
channelOrig = "Vcb_catWcb_SR"
channel = "SL"
bkgs = {
    "singletop": {
        "label": "Single top",
        "color": ROOT.kBlue-1
    },
    "ttbb-dps": {
        "label": "t#bar{t} + b#bar{b} DPS",
        "color": ROOT.kGreen
    },
    "ttbb": {
        "label": "t#bar{t} + b#bar{b} 4FS",
        "color": ROOT.kBlue-5
    },
    "ttbj": {
        "label": "t#bar{t} + bj",
        "color": ROOT.kBlue-5
    },
    "ttcc": {
        "label": "t#bar{t} + cc",
        "color": ROOT.kBlue-5
    },
    "ttcj": {
        "label": "t#bar{t} + cj",
        "color": ROOT.kBlue-5
    },
    "ttLF": {
        "label": "t#bar{t} + jj",
        "color": ROOT.kBlue-5
    },
    "wjets": {
        "label": "W + jets",
        "color": ROOT.kBlue-5
    },
    "ttZ": {
        "label": "t#bar{t} + Z",
        "color": ROOT.kBlue-5
    },
    "ttW": {
        "label": "t#bar{t} + W",
        "color": ROOT.kBlue-5
    },
    "diboson": {
        "label": "diboson",
        "color": ROOT.kBlue-5
    },
    "ttHbb": {
        "label": "t#bar{t} + H(bb)",
        "color": ROOT.kBlue-5
    },
    "ttHcc": {
        "label": "t#bar{t} + H(cc)",
        "color": ROOT.kBlue-5
    }
}
signal = {
    "ttWcb": {
        "label": "t#bar{t}(W#rightarrow cb)",
        "color": ROOT.kRed
    }
}

all_procs = bkgs.keys() + signal.keys()

cb = ch.CombineHarvester()
#cb.SetFlag("filters-use-regex", True)
cb.SetVerbosity(1)

datacard_dict = {"Vcb_catWcb_SR" : {
                "distribution" : "score_tt_Wcb",
                },
                "Vcb_catBB_CR" : {
                "distribution" : "score_ttbb",
                },
                "Vcb_catBJ_CR" : {
                "distribution" : "score_ttbj",
                },
                "Vcb_catCC_CR" : {
                "distribution" : "score_ttcc",
                },
                "Vcb_catCJ_CR" : {
                "distribution" : "score_ttcj",
                },
                "Vcb_catLF_CR" : {
                "distribution" : "score_ttLF",
                },
}


catNames = [(idx, cat) for idx, cat in enumerate(datacard_dict.keys())]
outputname = outFolder+ '/Vcb_%s_%s.txt' % (channel, year)
#print (catNames)
cb.AddObservations(['*'], ['Vcb'], [year], [channel], catNames)
cb.AddProcesses(['*'], ['Vcb'], [year], [channel], bkgs.keys(), catNames, False)
cb.AddProcesses(['*'], ['Vcb'], [year], [channel], signal.keys(), catNames, True)
bins = cb.bin_set()
#print(bins)

# Extract shapes 
inputfiles = {bin: "" for bin in bins}
for dp, dn, filenames in os.walk(inputdir):

    for f in filenames:
        if f.endswith(".root"):
            bin = f.replace(".root", "")
            if bin in bins:
                fullpath = os.path.join(dp, f)
                inputfiles[bin] = fullpath
            
print(inputfiles)

for bin in bins:
    print(inputfiles[bin])
    print(f"Extract shapes for bin {bin}")
    cb.cp().bin([bin]).ExtractShapes(inputfiles[bin], "$PROCESS", "$PROCESS_$SYSTEMATIC")

outFileName = outputname.replace(".txt", "_shapes.root")


# MC stats yes or no 
if doAutoMCStats:
    cb.SetAutoMCStats(cb, 0)
else:
    cb.SetAutoMCStats(cb, -1)

tt_components = ['ttcc', 'ttcj', 'ttLF']
if use4FS:
    tt_components += ['ttbb', 'ttbj']
ttH_modes = ['ttHbb', 'ttHcc']


# Shape uncertainties
shapeSysts = {
    'CMS_pileup_%s' % year: all_procs,
    # 'CMS_ttHcc_puJetId_%s' % year: all_procs,
    # 'CMS_ttHcc_topptWeight': ['ttbar'],
    # 'CMS_ttHcc_zptEWKWeight': ['zjets'],
    # 'CMS_VV_NNLOWeights_13TeV': ['vzcc', 'vzbb', 'vwqq', 'vvother'],
    # 'CMS_ttHcc_boost_EWK_13TeV': ['zhbb', 'zhcc'],
    # 'CMS_res_j_13TeV_%s' % year: all_procs,
    # 'CMS_ttHcc_eff_e_Zll_13TeV_%s' % year: all_procs,  # lnN
    # 'CMS_ttHcc_eff_m_Zll_13TeV_%s' % year: all_procs,  # lnN
    # 'CMS_scale_e_13TeV_%s' % year: all_procs,
    # 'CMS_LHE_weights_scale_muF_$PROCESS': all_procs,
    # 'CMS_LHE_weights_scale_muR_$PROCESS': all_procs,
    # 'CMS_ttHcc_ccTag_eff_cc_%s' % year: ['zhcc', 'ggzhcc', 'vzcc'],
    # 'CMS_ttHcc_ccTag_mistag_bb_%s' % year: ['zhbb', 'ggzhbb', 'vvother'],
    # 'CMS_HDAMP_$PROCESS': tt_components,
    'CMS_PS_isr_%s$PROCESS' % year: tt_components + ['ttH_hbb', 'ttH_hcc'] + signal.keys(),
    'CMS_PS_fsr_%s$PROCESS' % year: tt_components + ['ttH_hbb', 'ttH_hcc'] + signal.keys(),
    'CMS_LHE_weights_scale_muF_%s$PROCESS' % year: tt_components + ['ttH_hbb', 'ttH_hcc'] + signal.keys(),
    'CMS_LHE_weights_scale_muR_%s$PROCESS' % year: tt_components + ['ttH_hbb', 'ttH_hcc'] + signal.keys(),
    "CMS_JER%s$PROCESS" % year : all_procs,
    "CMS_JES%s$PROCESS" % year : all_procs,
}

for syst in shapeSysts:
    cb.cp().process(shapeSysts[syst]).AddSyst(cb, syst, 'shape', ch.SystMap()(1.0))

# PDF/Scale uncertainties on xsec
if year == '2018':
    cb.cp().AddSyst(cb, 'CMS_lumi_13TeV_2018', 'lnN', ch.SystMap()(1.015))
cb.cp().process(['wjets']).AddSyst(cb, 'QCDscale_V', 'lnN', ch.SystMap()(1.038))
cb.cp().process(['singletop']).AddSyst(cb, 'QCDscale_singletop', 'lnN', ch.SystMap()((1.031, 1 - 0.021)))
cb.cp().process(tt_components).AddSyst(cb, 'QCDscale_ttbar', 'lnN', ch.SystMap()((1.024, 1 - 0.035)))
cb.cp().process(['ttW']).AddSyst(cb, 'QCDscale_ttbar', 'lnN', ch.SystMap()((1.255, 1 - 0.164)))
cb.cp().process(['ttZ']).AddSyst(cb, 'QCDscale_ttbar', 'lnN', ch.SystMap()((1.081, 1 - 0.093)))
cb.cp().process(signal.keys()).AddSyst(cb, 'QCDscale_ttbar', 'lnN', ch.SystMap()((1.081, 1 - 0.093))) # Fix this number

cb.cp().process(ttH_modes).AddSyst(cb, 'QCDscale_ttH', 'lnN', ch.SystMap()((1.058, 1 - 0.092)))

cb.cp().process(['wjets']).AddSyst(cb, 'pdf_qqbar', 'lnN', ch.SystMap()((1.008, 1 - 0.004)))
cb.cp().process(['singletop']).AddSyst(cb, 'pdf_qg', 'lnN', ch.SystMap()(1.028))
cb.cp().process(tt_components).AddSyst(cb, 'pdf_gg', 'lnN', ch.SystMap()(1.042))
cb.cp().process(['ttW']).AddSyst(cb, 'pdf_qqbar', 'lnN', ch.SystMap()(1.036))
cb.cp().process(['ttZ']).AddSyst(cb, 'pdf_gg', 'lnN', ch.SystMap()(1.035))
cb.cp().process(signal.keys()).AddSyst(cb, 'pdf_qg', 'lnN', ch.SystMap()(1.028)) # Fix this number

cb.cp().process(ttH_modes).AddSyst(cb, 'pdf_Higgs_ttH', 'lnN', ch.SystMap()(1.036))

cb.WriteDatacard(outputname, outFileName)
