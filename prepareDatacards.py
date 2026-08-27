import CombineHarvester.CombineTools.ch as ch
import ROOT
import os
import subprocess
import argparse
from fixNegativeBins import fixNegativeBins

parser = argparse.ArgumentParser(description='Prepare datacards for Vcb analysis')
parser.add_argument('--year', type=str, default='2024', help='Data taking year')
parser.add_argument('--inputdir', type=str, required=True, help='Input directory for the analysis')
parser.add_argument('--outdir', type=str, required=True, help='Output directory for the datacards')
parser.add_argument('--doAutoMCStats', nargs="?", const=1, type=bool, default=False, required=False, help='Use AutoMCStats')
parser.add_argument('--optimizeWSforFits', nargs="?", const=1, type=bool, default=False, required=False, help='Add workspace optimization options for fits. Not suitable for pre/postfit plots')
args = parser.parse_args()

year = args.year
inputdir = args.inputdir
outdir = args.outdir

if not os.path.exists(outdir):
    os.makedirs(outdir)

channel = "SL"
# Keep only processes that are currently produced in shapes files.
bkgs = ['singletop', 'ttbb', 'ttbj', 'tt2b', 'ttbb-dps', 'ttbj-dps', 'tt2b-dps', 'ttcc', 'ttcj', 'tt2c', 'ttLF', 'wjets', 'ttZ', 'ttW', 'diboson', 'ttHbb', 'ttHcc']
signal = ['tt-vcb']
tt_components = ['tt-vcb','ttbb', 'ttbj', 'tt2b', 'ttbb-dps', 'ttbj-dps', 'tt2b-dps', 'ttcc', 'ttcj', 'tt2c', 'ttLF']
minorBkg_components = ['singletop', 'wjets', 'diboson']
tt_components_mainBkg = ['ttbb', 'ttbj', 'tt2b', 'ttbb-dps', 'ttbj-dps', 'tt2b-dps', 'ttcc', 'ttcj', 'tt2c', 'ttLF'] 
tt_components_extended = ['tt-vcb', 'ttbb', 'ttbj', 'tt2b', 'ttbb-dps', 'ttbj-dps', 'tt2b-dps', 'ttcc', 'ttcj', 'tt2c', 'ttLF', 'ttZ', 'ttW', 'ttHbb', 'ttHcc'] 
tt_components_reduced = ['tt-vcb', 'ttZ', 'ttW', 'ttHbb', 'ttHcc'] 
tt_components_nobb = ['tt-vcb', 'ttcc', 'ttcj', 'tt2c', 'ttLF'] 
tt_components_bbdps = ['ttbb-dps', 'ttbj-dps', 'tt2b-dps'] 
tt_components_mainBkg_nodps = ['ttbb', 'ttbj', 'tt2b', 'ttcc', 'ttcj', 'tt2c', 'ttLF']
ttH_components = ['ttHbb', 'ttHcc']
signal_and_ttbb = ['tt-vcb', 'ttbb', 'tt2b', 'ttbj']
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
                "Vcb_cat2B_CR" : {
                "distribution" : "fscore_tt2b",
                },
                "Vcb_catCC_CR" : {
                "distribution" : "fscore_ttcc",
                },
                "Vcb_catCJ_CR" : {
                "distribution" : "fscore_ttcj",
                },
                "Vcb_cat2C_CR" : {
                "distribution" : "fscore_tt2c",
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
if year == '2024':
    cb.cp().AddSyst(cb, 'CMS_lumi_13p6TeV_2024', 'lnN', ch.SystMap()(1.016)),
    #cb.cp().process(signal).AddSyst(cb, 'effi', 'lnN', ch.SystMap()((1.002)))
    cb.cp().process(['singletop']).AddSyst(cb, 'norm_singletop', 'lnN', ch.SystMap()((1.25))) # A sentimento
    cb.cp().process(['ttW']).AddSyst(cb, 'norm_ttW', 'lnN', ch.SystMap()((1.068))) # PRL 131 (2023) 231901
    cb.cp().process(['ttZ']).AddSyst(cb, 'norm_ttZ', 'lnN', ch.SystMap()((1.096,1.085))) # EPJC 80 (2020) 428
    cb.cp().process(tt_components_bbdps).AddSyst(cb, 'norm_ttbb-dps', 'lnN', ch.SystMap()((1.50))) # 50% uncertainty on the DPS contribution
    #Find appropriate uncertainties for the following lnN nuisances
    cb.cp().process(ttH_components).AddSyst(cb, 'norm_ttH', 'lnN', ch.SystMap()((1.20))) # Slightly conservative wrt numbers at 13 TeV in https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageAt13TeV
    cb.cp().process(['diboson']).AddSyst(cb, 'norm_diboson', 'lnN', ch.SystMap()((1.30))) # A sentimento
    cb.cp().process(['wjets']).AddSyst(cb, 'norm_wjets', 'lnN', ch.SystMap()(1.30)) # A sentimento

for proc in tt_components_mainBkg_nodps:
    cb.cp().process([proc]).AddSyst(cb, f"xsec_{proc}", 'rateParam', ch.SystMap()(1.0))
    #cb.cp().process([proc]).AddSyst(cb, f"xsec_{proc}", 'lnN', ch.SystMap()(1.5))



#############################
#    Shape uncertainties    #
#############################

# Input files to extract shapes from
inputfiles = {bin: "" for bin in bins}
print(f"INPUTDIR: {inputdir}")
for dp, dn, filenames in os.walk(inputdir): # Careful: this will look into all subdirectories, make sure there are no other undesired root file is around

    for f in filenames:
        if f.endswith(".root"):
            bin = f.replace(".root", "")
            if bin in bins:
                fullpath = os.path.join(dp, f)
                inputfiles[bin] = fullpath

print(f"Input files {inputfiles}")

# Output shapes file (will collect all the histograms with shape variations)
outputShapesName = outputCardName.replace(".txt", "_shapes.root")
print("Output file name: " + outputShapesName)

shapeSysts = {
    'CMS_pileup_%s' % year: all_procs,
    'CMS_trigEff' : all_procs,
    'CMS_muEff' : all_procs,
    'CMS_elEff' : all_procs,
    'CMS_elSmear' : all_procs,
    'CMS_elScale' : all_procs,
    'CMS_muSmear' : all_procs,
    'CMS_muScale' : all_procs,
    # Flavor tagging
    'CMS_flavTag_TTWeight_ttbar': all_procs,
    'CMS_flavTag_HDamp_ttbar': all_procs,
    'CMS_flavTag_BDecay_ttbar': all_procs,
    'CMS_flavTag_CDecay_ttbar': all_procs,
    'CMS_flavTag_xsec_ttbar': all_procs,
    'CMS_flavTag_xsec_wjets_c': all_procs,
    'CMS_flavTag_xsec_wjets_b': all_procs,
    'CMS_flavTag_xsec_zjets_c': all_procs,
    'CMS_flavTag_xsec_zjets_b': all_procs,
    'CMS_flavTag_xsec_singlet_tCh': all_procs,
    'CMS_flavTag_xsec_singlet_tW': all_procs,
    'CMS_flavTag_xsec_VV': all_procs,
    'CMS_flavTag_EleReco': all_procs,
    'CMS_flavTag_EleScale': all_procs,
    'CMS_flavTag_EleSmear': all_procs,
    'CMS_flavTag_EleID': all_procs,
    'CMS_flavTag_EleTrigger': all_procs,
    'CMS_flavTag_MuID': all_procs,
    'CMS_flavTag_MuIso': all_procs,
    'CMS_flavTag_MuTrigger': all_procs,
    'CMS_flavTag_MuScale': all_procs,
    'CMS_flavTag_MuResol': all_procs,
    'CMS_flavTag_MET_UnclEnergy': all_procs,
    'CMS_flavTag_PU_%s' % year: all_procs,
    'CMS_flavTag_Lumi_%s' % year: all_procs,
    'CMS_flavTag_Stat_flavB_C0_%s' % year: all_procs,
    'CMS_flavTag_Stat_flavB_C1_%s' % year: all_procs,
    'CMS_flavTag_Stat_flavB_C2_%s' % year: all_procs,
    'CMS_flavTag_Stat_flavB_C3_%s' % year: all_procs,
    'CMS_flavTag_Stat_flavB_C4_%s' % year: all_procs,
    'CMS_flavTag_Stat_flavB_B0_%s' % year: all_procs,
    'CMS_flavTag_Stat_flavB_B1_%s' % year: all_procs,
    'CMS_flavTag_Stat_flavB_B2_%s' % year: all_procs,
    'CMS_flavTag_Stat_flavB_B3_%s' % year: all_procs,
    'CMS_flavTag_Stat_flavB_B4_%s' % year: all_procs,
    'CMS_flavTag_Stat_flavC_C0_%s' % year: all_procs,
    'CMS_flavTag_Stat_flavC_C1_%s' % year: all_procs,
    'CMS_flavTag_Stat_flavC_C2_%s' % year: all_procs,
    'CMS_flavTag_Stat_flavC_C3_%s' % year: all_procs,
    'CMS_flavTag_Stat_flavC_C4_%s' % year: all_procs,
    'CMS_flavTag_Stat_flavC_B0_%s' % year: all_procs,
    'CMS_flavTag_Stat_flavC_B1_%s' % year: all_procs,
    'CMS_flavTag_Stat_flavC_B2_%s' % year: all_procs,
    'CMS_flavTag_Stat_flavC_B3_%s' % year: all_procs,
    'CMS_flavTag_Stat_flavC_B4_%s' % year: all_procs,
    'CMS_flavTag_Stat_flavL_C0_%s' % year: all_procs,
    'CMS_flavTag_Stat_flavL_C1_%s' % year: all_procs,
    'CMS_flavTag_Stat_flavL_C2_%s' % year: all_procs,
    'CMS_flavTag_Stat_flavL_C3_%s' % year: all_procs,
    'CMS_flavTag_Stat_flavL_C4_%s' % year: all_procs,
    'CMS_flavTag_Stat_flavL_B0_%s' % year: all_procs,
    'CMS_flavTag_Stat_flavL_B1_%s' % year: all_procs,
    'CMS_flavTag_Stat_flavL_B2_%s' % year: all_procs,
    'CMS_flavTag_Stat_flavL_B3_%s' % year: all_procs,
    'CMS_flavTag_Stat_flavL_B4_%s' % year: all_procs,
    'CMS_flavTag_LHE_muF_ttbar': all_procs,
    'CMS_flavTag_LHE_muR_ttbar': all_procs,
    'CMS_flavTag_LHE_muF_singlet': all_procs,
    'CMS_flavTag_LHE_muR_singlet': all_procs,
    'CMS_flavTag_LHE_muF_wjets': all_procs,
    'CMS_flavTag_LHE_muR_wjets': all_procs,
    'CMS_flavTag_LHE_muF_zjets': all_procs,
    'CMS_flavTag_LHE_muR_zjets': all_procs,
    'CMS_flavTag_LHE_muF_diboson': all_procs,
    'CMS_flavTag_LHE_muR_diboson': all_procs,
    'CMS_flavTag_LHE_PDF_ttbar': all_procs,
    'CMS_flavTag_LHE_PDF_singlet': all_procs,
    'CMS_flavTag_LHE_PDF_wjets': all_procs,
    'CMS_flavTag_LHE_PDF_zjets': all_procs,
    'CMS_flavTag_LHE_PDF_diboson': all_procs,
    'CMS_flavTag_LHE_aS_ttbar': all_procs,
    'CMS_flavTag_LHE_aS_singlet': all_procs,
    'CMS_flavTag_LHE_aS_wjets': all_procs,
    'CMS_flavTag_LHE_aS_zjets': all_procs,
    'CMS_flavTag_LHE_aS_diboson': all_procs,
    'CMS_flavTag_PS_ISR_ttbar': all_procs,
    'CMS_flavTag_PS_FSR_ttbar': all_procs,
    'CMS_flavTag_PS_ISR_singlet': all_procs,
    'CMS_flavTag_PS_FSR_singlet': all_procs,
    'CMS_flavTag_PS_ISR_wjets': all_procs,
    'CMS_flavTag_PS_FSR_wjets': all_procs,
    'CMS_flavTag_PS_ISR_zjets': all_procs,
    'CMS_flavTag_PS_FSR_zjets': all_procs,
    'CMS_flavTag_PS_ISR_diboson': all_procs,
    'CMS_flavTag_PS_FSR_diboson': all_procs,
    'CMS_flavTag_JES_Absolute': all_procs,
    'CMS_flavTag_JES_BBEC1': all_procs,
    'CMS_flavTag_JES_FlavorQCD': all_procs,
    'CMS_flavTag_JES_RelativeBal': all_procs,
    'CMS_flavTag_JES_Absolute_%s' % year: all_procs,
    'CMS_flavTag_JES_BBEC1_%s' % year: all_procs,
    'CMS_flavTag_JES_RelativeSample_%s' % year: all_procs,
    'CMS_flavTag_JEReta0to1p93_%s' % year: all_procs,
    'CMS_flavTag_JEReta1p93to2p5_%s' % year: all_procs,
    'jes_Absolute': all_procs,
    'jes_Absolute_%s' % year: all_procs,
    'jes_BBEC1': all_procs,
    'jes_BBEC1_%s' % year: all_procs,
    'jes_FlavorQCD': all_procs,
    'jes_RelativeBal': all_procs,
    'jes_RelativeSample_%s' % year: all_procs,
    'jer' : all_procs,
    'met' : all_procs,
    'tune_CP5' : signal,
    #'CR1' : signal_and_ttbb,
    #'CR2' : signal_and_ttbb,
    'CR1' : signal,
    'CR2' : signal,
    'bFragWeight_%s' % year: tt_components_extended,
    #'bFragPetersonWeight' : tt_components_extended,
}

#Above here, perhaps it should be something like  'LHE_muF_%s%s' % year %tt_component: tt_components, for tt_component in tt_components

for syst in shapeSysts:
    print(f"Adding systematic: {syst} for processes: {shapeSysts[syst]}")
    cb.cp().process(shapeSysts[syst]).AddSyst(cb, syst, 'shape', ch.SystMap()(1.0))
            
#Now add process-dependent shape systematics (only for certain processes)
for proc in tt_components_nobb:
    syst_name = f"topHdampWeight_{proc}_{year}"
    print(f"Adding process-dependent systematic: {syst_name} for process: {proc}")
    cb.cp().process([proc]).AddSyst(cb, syst_name, 'shape', ch.SystMap()(1.0))

per_process_systematics = ['LHE_muF', 'LHE_muR', 'PS_fsr_G2GG_muR', 'PS_isr_G2GG_muR', 
                           'PS_fsr_G2QQ_muR', 'PS_isr_G2QQ_muR', 'PS_fsr_Q2QG_muR', 'PS_isr_Q2QG_muR', 
                           'PS_fsr_X2XG_muR', 'PS_isr_X2XG_muR', 'PS_fsr_G2GG_cNS', 'PS_isr_G2GG_cNS',
                           'PS_fsr_G2QQ_cNS', 'PS_isr_G2QQ_cNS', 'PS_fsr_G2QG_cNS', 'PS_isr_G2QG_cNS',
                           'PS_fsr_X2XG_cNS', 'PS_isr_X2XG_cNS']#, 'bFragWeight']#, 'bFragPetersonWeight']

for proc in tt_components_extended:
    for var in per_process_systematics:
        syst_name = f"{var}_{proc}_{year}"
        print(f"Adding process-dependent systematic: {syst_name} for process: {proc}")
        cb.cp().process([proc]).AddSyst(cb, syst_name, 'shape', ch.SystMap()(1.0))

per_process_systematics_minorBkg = ["LHE_muF", "LHE_muR", "minorBkg_PS_ISR", "minorBkg_PS_FSR"]
for proc in minorBkg_components:
    for var in per_process_systematics_minorBkg:
        syst_name = f"{var}_{proc}_{year}"
        print(f"Adding process-dependent systematic: {syst_name} for minor backgrounds")
        cb.cp().process([proc]).AddSyst(cb, syst_name, 'shape', ch.SystMap()(1.0))

for bin in bins:
    print(f"Extracting shapes for bin {bin} from file {inputfiles[bin]}")
    cb.cp().bin([bin]).ExtractShapes(inputfiles[bin], "$PROCESS", "$PROCESS_$SYSTEMATIC")



cb.WriteDatacard(outputCardName, outputShapesName)

#Fix negative bins in the shape file. Negative bin contents are set to zero. Uncertainties larger than the bin content are set to the bin content.
fixNegativeBins(outputShapesName, False)

# Now produce a new datacard with the negative bins fixed
cb_fixed = ch.CombineHarvester()
cb_fixed.ParseDatacard(outputCardName)


systematics_nuisances = sorted(
    s for s in cb_fixed.syst_name_set()
)
if len(systematics_nuisances) > 0:
    cb_fixed.AddDatacardLineAtEnd('systematics group = ' + ' '.join(systematics_nuisances))

allbutflavor = sorted(
    s for s in cb_fixed.syst_name_set() if not s.startswith('CMS_flavTag')
)
if len(allbutflavor) > 0:
    cb_fixed.AddDatacardLineAtEnd('allbutflavor group = ' + ' '.join(allbutflavor))

cb_fixed.WriteDatacard(outputCardName, outputShapesName)

# Create workspace with specific model and POI definitions
print ("Test datacards and create workspace for " + year + "!")
# Note that 0.00085 is the ratio of Br(W->cb)/Br(W->qq' - cb) using the PDG values. BR(W->cb) = 0.00085 and BR(W->qq') = 0.6741
workspace_name = outputCardName.replace(".txt", ".root")
print("Workspace name: " + workspace_name)
workspace_name = workspace_name.replace("/Vcb","/workspace_Vcb")
print("Workspace name: " + workspace_name)


if args.optimizeWSforFits:
    command = "text2workspace.py " + outputCardName + " -o " + workspace_name + \
    " -m 125.38 -v 0" + \
    " --for-fits --no-wrappers --use-histsum --X-pack-asympows" + \
    " --optimize-simpdf-constraints=cms --channel-masks"
else:
    command = "text2workspace.py " + outputCardName + " -o " + workspace_name + \
    " -m 125.38 -v 0 --channel-masks"

#command = "text2workspace.py " + outputCardName + " -o " + workspace_name + \
#    " -m 125.38 -v 0 -P HiggsAnalysis.CombinedLimit.PhysicsModel:multiSignalModel" + \
#    " --PO verbose --for-fits --no-wrappers --use-histsum --X-pack-asympows" + \
#    " --optimize-simpdf-constraints=cms --channel-masks" + \
#    " --PO 'map=.*/tt-vcb:rate_ttWcb=expr;;rate_ttWcb(\"@0*@0\",Vcb[1,-1.,3.])'"+ \
#    " --PO 'map=.*/tt2b:xsec_tt2b[1,-1.,2.]'" + \
#    " --PO 'map=.*/ttbb:xsec_ttbb[1,-1.,2.]'" + \
#    " --PO 'map=.*/ttbj:xsec_ttbj[1,-1.,2.]'" + \
#    " --PO 'map=.*/ttcc:xsec_ttcc[1,-1.,2.]'" + \
#    " --PO 'map=.*/tt2c:xsec_tt2c[1,-1.,2.]'" + \
#    " --PO 'map=.*/ttcj:xsec_ttcj[1,-1.,2.]'" + \
#    " --PO 'map=.*/ttLF:xsec_ttLF[1,-1.,2.]'"
    
#if args.doValidation:
#    command = "text2workspace.py " + outputCardName + " -o " + workspace_name + \
#        " -m 125.38 -v 0 -P HiggsAnalysis.CombinedLimit.PhysicsModel:multiSignalModel" + \
#        " --PO verbose --for-fits --no-wrappers --use-histsum --X-pack-asympows" + \
#        " --optimize-simpdf-constraints=cms --channel-masks" + \
#        " --PO 'map=.*/tt2b:xsec_tt2b[1,-1.,2.]'" + \
#        " --PO 'map=.*/ttbb:xsec_ttbb[1,-1.,2.]'" + \
#        " --PO 'map=.*/ttbj:xsec_ttbj[1,-1.,2.]'" + \
#        " --PO 'map=.*/ttcc:xsec_ttcc[1,-1.,2.]'" + \
#        " --PO 'map=.*/tt2c:xsec_tt2c[1,-1.,2.]'" + \
#        " --PO 'map=.*/ttcj:xsec_ttcj[1,-1.,2.]'" + \
#        " --PO 'map=.*/ttLF:xsec_ttLF[1,-1.,2.]'"+ \
#        " --PO 'map=.*/tt-vcb:xsec_ttWcb[1,-1.,2.]'"   


#command = "text2workspace.py " + outputCardName + " -o " + workspace_name + " -m 125.38 -v 0 -P HiggsAnalysis.CombinedLimit.PhysicsModel:multiSignalModel --PO verbose --channel-masks --PO 'map=.*/ttbb:rate_tt[1.,-1.,2.]' --PO 'map=.*/ttbj:rate_tt[1.,-1.,2.]' --PO 'map=.*/ttcc:rate_tt[1.,-1.,2.]' --PO 'map=.*/ttcj:rate_tt[1.,-1.,2.]' --PO 'map=.*/ttLF:rate_tt[1.,-1.,2.]' --PO 'map=.*/ttWcb:rate_ttWcb=expr;;rate_ttWcb(\"@0*@1*@1*1./(0.00085*(1.-@1*@1)+1.)\",rate_tt,rate_ratio[1,-1.,2.])'"


print(command)
subprocess.call(command, shell=True)