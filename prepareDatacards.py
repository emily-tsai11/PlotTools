import CombineHarvester.CombineTools.ch as ch
import ROOT
import os
import subprocess
import argparse
from fixNegativeBins import fixNegativeBins

parser = argparse.ArgumentParser(description='Prepare datacards for Vcb analysis')
parser.add_argument('--year', type=str, default='2018', help='Data taking year')
parser.add_argument('--inputdir', type=str, required=True, help='Input directory for the analysis')
parser.add_argument('--outdir', type=str, required=True, help='Output directory for the datacards')
parser.add_argument('--doAutoMCStats', nargs="?", const=1, type=bool, default=False, required=False, help='Use AutoMCStats')
args = parser.parse_args()

year = args.year
inputdir = args.inputdir
outdir = args.outdir

if not os.path.exists(outdir):
    os.makedirs(outdir)

channel = "SL"
bkgs = ["singletop", "ttbb-dps", "ttbb", "ttbj", "ttcc", "ttcj", "ttLF", "w-fxfx", "ttZ", "ttW", "diboson", "ttHbb", "ttHcc"]
signal = ["ttWcb"]
tt_components = ['ttbb', 'ttbj', 'ttbb-dps' ,'ttcc', 'ttcj', 'ttLF']
ttH_modes = ['ttHbb', 'ttHcc']
all_procs = bkgs + signal


cb = ch.CombineHarvester()
#cb.SetFlag("filters-use-regex", True)
cb.SetVerbosity(1)

datacard_dict = {"Vcb_catWcb_SR" : {
                "distribution" : "score_tt_Wcb",
                },
                "Vcb_catBB_CR" : {
                "distribution" : "fscore_ttbb",
                },
                "Vcb_catBJ_CR" : {
                "distribution" : "fscore_ttbj",
                },
                "Vcb_catCC_CR" : {
                "distribution" : "fscore_ttcc",
                },
                "Vcb_catCJ_CR" : {
                "distribution" : "fscore_ttcj",
                },
                "Vcb_catLF_CR" : {
                "distribution" : "fscore_ttLF",
                },
}


catNames = [(idx, cat) for idx, cat in enumerate(datacard_dict.keys())]
outputCardName = outdir+ '/Vcb_%s_%s.txt' % (channel, year)
#print (catNames)
cb.AddObservations(['*'], ['Vcb'], [year], [channel], catNames)
cb.AddProcesses(['*'], ['Vcb'], [year], [channel], bkgs, catNames, False)
cb.AddProcesses(['*'], ['Vcb'], [year], [channel], signal, catNames, True)
bins = cb.bin_set()
#print(bins)

# MC stats yes or no 
if args.doAutoMCStats:
    cb.SetAutoMCStats(cb, 0)
else:
    cb.SetAutoMCStats(cb, -1)

###############################
# Normalization uncertainties #
###############################

# PDF/Scale uncertainties on xsec
if year == '2018':
    cb.cp().AddSyst(cb, 'CMS_lumi_13TeV_2018', 'lnN', ch.SystMap()(1.015))
#cb.cp().process(['wjets']).AddSyst(cb, 'QCDscale_V', 'lnN', ch.SystMap()(1.038))
#cb.cp().process(['singletop']).AddSyst(cb, 'QCDscale_singletop', 'lnN', ch.SystMap()((1.031, 1 - 0.021)))
#cb.cp().process(tt_components).AddSyst(cb, 'QCDscale_ttbar', 'lnN', ch.SystMap()((1.024, 1 - 0.035)))
#cb.cp().process(['ttW']).AddSyst(cb, 'QCDscale_ttbar', 'lnN', ch.SystMap()((1.255, 1 - 0.164)))
#cb.cp().process(['ttZ']).AddSyst(cb, 'QCDscale_ttbar', 'lnN', ch.SystMap()((1.081, 1 - 0.093)))
#cb.cp().process(signal.keys()).AddSyst(cb, 'QCDscale_ttbar', 'lnN', ch.SystMap()((1.081, 1 - 0.093))) # Fix this number
#
#cb.cp().process(ttH_modes).AddSyst(cb, 'QCDscale_ttH', 'lnN', ch.SystMap()((1.058, 1 - 0.092)))
#
#cb.cp().process(['wjets']).AddSyst(cb, 'pdf_qqbar', 'lnN', ch.SystMap()((1.008, 1 - 0.004)))
#cb.cp().process(['singletop']).AddSyst(cb, 'pdf_qg', 'lnN', ch.SystMap()(1.028))
#cb.cp().process(tt_components).AddSyst(cb, 'pdf_gg', 'lnN', ch.SystMap()(1.042))
#cb.cp().process(['ttW']).AddSyst(cb, 'pdf_qqbar', 'lnN', ch.SystMap()(1.036))
#cb.cp().process(['ttZ']).AddSyst(cb, 'pdf_gg', 'lnN', ch.SystMap()(1.035))
#cb.cp().process(signal.keys()).AddSyst(cb, 'pdf_qg', 'lnN', ch.SystMap()(1.028)) # Fix this number
#
#cb.cp().process(ttH_modes).AddSyst(cb, 'pdf_Higgs_ttH', 'lnN', ch.SystMap()(1.036))


#############################
#    Shape uncertainties    #
#############################

# Input files to extract shapes from
inputfiles = {bin: "" for bin in bins}
for dp, dn, filenames in os.walk(inputdir):

    for f in filenames:
        if f.endswith(".root"):
            bin = f.replace(".root", "")
            if bin in bins:
                fullpath = os.path.join(dp, f)
                inputfiles[bin] = fullpath

# Output shapes file (will collect all the histograms with shape variations)
outputShapesName = outputCardName.replace(".txt", "_shapes.root")
print("Output file name: " + outputShapesName)

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


    #'$PROCESS_CMS_PS_isr_%s' % year: tt_components + ttH_modes + list(signal.keys()),
    #'$PROCESS_CMS_PS_fsr_%s' % year: tt_components + ttH_modes + list(signal.keys()),
    #'$PROCESS_CMS_LHE_weights_scale_muF_%s' % year: tt_components + ttH_modes + list(signal.keys()),
    #'$PROCESS_CMS_LHE_weights_scale_muR_%s' % year: tt_components + ttH_modes + list(signal.keys()),

    'CMS_JER%s' % year : all_procs,
    'CMS_JES%s' % year : all_procs,
}

for syst in shapeSysts:
    print(f"Adding systematic: {syst} for processes: {shapeSysts[syst]}")
    cb.cp().process(shapeSysts[syst]).AddSyst(cb, syst, 'shape', ch.SystMap()(1.0))
            
#print(inputfiles)

for bin in bins:
    print(f"Extracting shapes for bin {bin} from file {inputfiles[bin]}")
    cb.cp().bin([bin]).ExtractShapes(inputfiles[bin], "$PROCESS", "$PROCESS_$SYSTEMATIC")
    #print(f"Shapes extracted for bin {bin}:")
    #cb.PrintAll()

cb.WriteDatacard(outputCardName, outputShapesName)

#Fix negative bins in the shape file. Negative bin contents are set to zero. Uncertainties larger than the bin content are set to the bin content.
fixNegativeBins(outputShapesName, False)

# Now produce a new datacard with the negative bins fixed
cb_fixed = ch.CombineHarvester()
cb_fixed.ParseDatacard(outputCardName)
cb_fixed.WriteDatacard(outputCardName, outputShapesName)

# Create workspace with specific model and POI definitions
print ("Test datacards and create workspace for " + year + "!")
# Note that 0.00085 is the ratio of Br(W->cb)/Br(W->qq' - cb) using the PDG values. BR(W->cb) = 0.00085 and BR(W->qq') = 0.6741
workspace_name = outputCardName.replace(".txt", ".root")
print("Workspace name: " + workspace_name)
workspace_name = workspace_name.replace("/Vcb","/workspace_Vcb")
print("Workspace name: " + workspace_name)
command = "text2workspace.py " + outputCardName + " -o " + workspace_name + " -m 125.38 -v 0 -P HiggsAnalysis.CombinedLimit.PhysicsModel:multiSignalModel --PO verbose --channel-masks --PO 'map=.*/ttbb:rate_tt[1.,-1.,2.]' --PO 'map=.*/ttbj:rate_tt[1.,-1.,2.]' --PO 'map=.*/ttcc:rate_tt[1.,-1.,2.]' --PO 'map=.*/ttcj:rate_tt[1.,-1.,2.]' --PO 'map=.*/ttLF:rate_tt[1.,-1.,2.]' --PO 'map=.*/ttWcb:rate_ttWcb=expr;;rate_ttWcb(\"@0*@1*@1*1./(0.00085*(1.-@1*@1)+1.)\",rate_tt,rate_ratio[1,-1.,2.])'"
print(command)
subprocess.call(command, shell=True)

