"""
Faster, parallel-safe rewrite of prepareHistosForCards.py.

The original script requires --nproc 1 because every worker opens the *same*
shared output ROOT file (one per discriminant category) with TFile(..., "UPDATE"),
and concurrent UPDATE opens from separate processes can corrupt the file's key
table. On top of that, one process handles an entire input file, including every
ttbar sub-category it is tagged for (ttbb/ttbj/tt2b/ttcc/ttcj/tt2c/ttLF), each with
~150 systematics x 8 discriminant categories -- so a file like ttbar-powheg, which
needs several of those sub-categories, becomes one long single-core job while every
other (smaller) file finishes and leaves the rest of the cores idle.

This version:
  1. Has every worker write its histograms to a private, uniquely-named temp ROOT
     file instead of the shared output file, then merges all temp files into the
     real outputs in one fast, sequential pass at the end. This removes the
     concurrent-write hazard entirely, so --nproc can use every core.
  2. Splits work at (input file, ttbar sub-category) granularity instead of one
     job per input file, so a file tagged for several sub-categories has its work
     spread across multiple workers instead of monopolizing one core.
  3. Only calls RResultPtr.GetValue()/GetPtr() once, after every Filter/Define/
     Histo1D for a job has been booked, so RDataFrame runs the whole job in a
     single pass over the tree instead of one pass per progress printout.
  4. For data (singlee/singlemu), whose per-event weight never depends on `syst`,
     only produces the central histogram instead of ~150 numerically-identical
     copies -- prepareDatacards.py / CombineHarvester only ever read the plain
     "data_obs", not a per-systematic shape for data.
  5. Leaves ROOT's own implicit multithreading off by default (--threads_per_job,
     default 1) since parallelism now comes from --nproc worker processes; raising
     both without care will oversubscribe the machine's cores.

The physics content (selections, weights, systematics, binning) is unchanged from
prepareHistosForCards.py; only the parallelization and I/O strategy differ.
"""
import argparse
import glob
import hashlib
import multiprocessing as mp
import os
import shutil
import tempfile
from functools import partial

import ROOT
from colorama import Fore, Style

import flavTagWeightPlugin

ROOT.gROOT.SetBatch(True)
ROOT.TTreeCache.SetLearnEntries(100)
ROOT.gEnv.SetValue("TFile.AsyncPrefetching", 1)

suffix_dict = {'base': '', 'ttLF': '_0', 'ttcj': '_41', 'tt2c': '_42', 'ttcc': '_43', 'ttbj': '_51', 'tt2b': '_52', 'ttbb': '_53'}
mc_processes_for_data_obs = ['tt-vcb', 'ttbb', 'ttbj', 'tt2b', 'ttcc', 'ttcj', 'tt2c', 'ttLF', 'singletop', 'wjets', 'ttZ', 'ttW', 'diboson', 'ttHbb', 'ttHcc']
tt_5fs_replacement_processes = ['ttbb', 'ttbj', 'tt2b']

JME_scaling_factors = {"ttWcb": 6.26, "ttLF": 4.88, "ttbb": 4.61, "tt2b": 5.02, "ttbj": 5.51, "ttcc": 4.43, "tt2c": 5.13, "ttcj": 5.50}

tt_file_names = ["ttbb-4f", "ttbar-powheg"]
tt4f_strings = ["ttbb", "ttbj", "tt2b"]
tt_strings = ["ttcc", "ttcj", "tt2c", "ttLF"]

perProcessSysts = ["topHdampWeight_", "bFragWeight_", "bFragPetersonWeight_", "LHE_muF_", "LHE_muR_", "PS_fsr_", "PS_isr_", "minorBkg_PS_ISR_", "minorBkg_PS_FSR_"]


def is_data_infile(infile):
    return "data" in infile or "Data" in infile


def assign_event_weight(year, infile, suffix, syst="", flavtag_weight_branch="flavTagWeight", available_columns=None):
    """
    Define the MC event weight according to the year. Collision data should be handled separately.

    Parameters:
    - year: Data taking year.
    - infile: Input file.
    - syst: Systematic uncertainty string.
    - flavtag_weight_branch: Name of the branch/column to use for the flavour-tagging
      weight term (defaults to the "flavTagWeight" branch stored in the ntuple; pass
      the column defined by flavTagWeightPlugin.define_flavtag_weights to use a weight
      recomputed on the fly from an alternate correctionlib SF file instead).
    - available_columns: optional set of branch/column names available on the input
      tree. When given, the TopPtWeight/TOPMLWeight top reweighting term is only
      appended if those branches actually exist -- some external systematic-shape
      productions (e.g. JES) don't carry them, and referencing a missing branch
      would otherwise fail RDataFrame's JIT compilation of the Define() call.
    """
    weight = "1"
    if year == 2024 or year == 2025:
        weight = f"lumiwgt*genWeight*xsecWeight*puWeight*muEffWeight*elEffWeight*{flavtag_weight_branch}*(((abs(lep1_pdgId)==11 && passTrigEl) || (abs(lep1_pdgId)==13 && passTrigMu)) && passmetfilters)"
    needs_top_reweighting = "ttbar" in infile or "4f" in infile or "tt-vcb" in infile
    required_top_columns = {"TopPtWeight", f"TopPtWeightNorm{suffix}", "TOPMLWeight", f"TOPMLWeightNorm{suffix}"}
    if needs_top_reweighting and (available_columns is None or required_top_columns <= available_columns):
        weight = f"{weight}*TopPtWeight[1]*TopPtWeightNorm{suffix}[1]*TOPMLWeight[5]*TOPMLWeightNorm{suffix}[5]"  # TOPMLWeight[5] is b-fragmentation nominal

    if not syst == "":
        weight = f"{weight}*{syst}"

    return weight


def produce_systematics(year, suffix):
    # Kept at module level (rather than nested inside `if __name__ == "__main__"` as in
    # the original) so worker processes started with a 'spawn' multiprocessing start
    # method can resolve it too, not just ones started by 'fork'.
    systematics = {"None": "",
                   # Pileup and lepton efficiencies
                   "CMS_pileup_%sUp" % year: "puWeightUp/puWeight",
                   "CMS_pileup_%sDown" % year: "puWeightDown/puWeight",
                   "CMS_trigEffUp": "trigEffWeightUp/trigEffWeight",
                   "CMS_trigEffDown": "trigEffWeightDown/trigEffWeight",
                   "CMS_muEffUp": "muEffWeight_UP/muEffWeight",
                   "CMS_muEffDown": "muEffWeight_DOWN/muEffWeight",
                   "CMS_elEffUp": "elEffWeight_UP/elEffWeight",
                   "CMS_elEffDown": "elEffWeight_DOWN/elEffWeight",
                   "CMS_elSmearUp": "elSmear_UP",
                   "CMS_elSmearDown": "elSmear_DOWN",
                   "CMS_elScaleUp": "elScale_UP",
                   "CMS_elScaleDown": "elScale_DOWN",
                   "CMS_muSmearUp": "muSmear_UP",
                   "CMS_muSmearDown": "muSmear_DOWN",
                   "CMS_muScaleUp": "muScale_UP",
                   "CMS_muScaleDown": "muScale_DOWN",
                   # Flavor tagging
                   "CMS_flavTag_TTWeight_ttbarUp": "flavTagWeight_TTWeight_ttbar_UP/flavTagWeight",
                   "CMS_flavTag_TTWeight_ttbarDown": "flavTagWeight_TTWeight_ttbar_DOWN/flavTagWeight",
                   "CMS_flavTag_HDamp_ttbarUp": "flavTagWeight_HDamp_ttbar_UP/flavTagWeight",
                   "CMS_flavTag_HDamp_ttbarDown": "flavTagWeight_HDamp_ttbar_DOWN/flavTagWeight",
                   "CMS_flavTag_BDecay_ttbarUp": "flavTagWeight_BDecay_ttbar_UP/flavTagWeight",
                   "CMS_flavTag_BDecay_ttbarDown": "flavTagWeight_BDecay_ttbar_DOWN/flavTagWeight",
                   "CMS_flavTag_CDecay_ttbarUp": "flavTagWeight_CDecay_ttbar_UP/flavTagWeight",
                   "CMS_flavTag_CDecay_ttbarDown": "flavTagWeight_CDecay_ttbar_DOWN/flavTagWeight",
                   "CMS_flavTag_xsec_ttbarUp": "flavTagWeight_XSec_ttbar_UP/flavTagWeight",
                   "CMS_flavTag_xsec_ttbarDown": "flavTagWeight_XSec_ttbar_DOWN/flavTagWeight",
                   "CMS_flavTag_xsec_wjets_cUp": "flavTagWeight_XSec_WJets_c_UP/flavTagWeight",
                   "CMS_flavTag_xsec_wjets_cDown": "flavTagWeight_XSec_WJets_c_DOWN/flavTagWeight",
                   "CMS_flavTag_xsec_wjets_bUp": "flavTagWeight_XSec_WJets_b_UP/flavTagWeight",
                   "CMS_flavTag_xsec_wjets_bDown": "flavTagWeight_XSec_WJets_b_DOWN/flavTagWeight",
                   "CMS_flavTag_xsec_zjets_cUp": "flavTagWeight_XSec_ZJets_c_UP/flavTagWeight",
                   "CMS_flavTag_xsec_zjets_cDown": "flavTagWeight_XSec_ZJets_c_DOWN/flavTagWeight",
                   "CMS_flavTag_xsec_zjets_bUp": "flavTagWeight_XSec_ZJets_b_UP/flavTagWeight",
                   "CMS_flavTag_xsec_zjets_bDown": "flavTagWeight_XSec_ZJets_b_DOWN/flavTagWeight",
                   "CMS_flavTag_xsec_singlet_tChUp": "flavTagWeight_XSec_singlet_tCh_UP/flavTagWeight",
                   "CMS_flavTag_xsec_singlet_tChDown": "flavTagWeight_XSec_singlet_tCh_DOWN/flavTagWeight",
                   "CMS_flavTag_xsec_singlet_tWUp": "flavTagWeight_XSec_singlet_tW_UP/flavTagWeight",
                   "CMS_flavTag_xsec_singlet_tWDown": "flavTagWeight_XSec_singlet_tW_DOWN/flavTagWeight",
                   "CMS_flavTag_xsec_VVUp": "flavTagWeight_XSec_VV_UP/flavTagWeight",
                   "CMS_flavTag_xsec_VVDown": "flavTagWeight_XSec_VV_DOWN/flavTagWeight",
                   "CMS_flavTag_PU_%sUp" % year: "flavTagWeight_PUWeight_UP/flavTagWeight",
                   "CMS_flavTag_PU_%sDown" % year: "flavTagWeight_PUWeight_DOWN/flavTagWeight",
                   "CMS_flavTag_Lumi_%sUp" % year: "flavTagWeight_Lumi_13p6TeV_%s_UP/flavTagWeight" % year,
                   "CMS_flavTag_Lumi_%sDown" % year: "flavTagWeight_Lumi_13p6TeV_%s_DOWN/flavTagWeight" % year,
                   "CMS_flavTag_EleRecoUp": "flavTagWeight_Ele_Reco_UP/flavTagWeight",
                   "CMS_flavTag_EleRecoDown": "flavTagWeight_Ele_Reco_DOWN/flavTagWeight",
                   "CMS_flavTag_EleScaleUp": "flavTagWeight_Ele_Scale_UP/flavTagWeight",
                   "CMS_flavTag_EleScaleDown": "flavTagWeight_Ele_Scale_DOWN/flavTagWeight",
                   "CMS_flavTag_EleSmearUp": "flavTagWeight_Ele_Smear_UP/flavTagWeight",
                   "CMS_flavTag_EleSmearDown": "flavTagWeight_Ele_Smear_DOWN/flavTagWeight",
                   "CMS_flavTag_EleIDUp": "flavTagWeight_Ele_ID_UP/flavTagWeight",
                   "CMS_flavTag_EleIDDown": "flavTagWeight_Ele_ID_DOWN/flavTagWeight",
                   "CMS_flavTag_EleTriggerUp": "flavTagWeight_Ele_Trigger_UP/flavTagWeight",
                   "CMS_flavTag_EleTriggerDown": "flavTagWeight_Ele_Trigger_DOWN/flavTagWeight",
                   "CMS_flavTag_MuIDUp": "flavTagWeight_Mu_ID_UP/flavTagWeight",
                   "CMS_flavTag_MuIDDown": "flavTagWeight_Mu_ID_DOWN/flavTagWeight",
                   "CMS_flavTag_MuIsoUp": "flavTagWeight_Mu_Iso_UP/flavTagWeight",
                   "CMS_flavTag_MuIsoDown": "flavTagWeight_Mu_Iso_DOWN/flavTagWeight",
                   "CMS_flavTag_MuScaleUp": "flavTagWeight_Mu_Scale_UP/flavTagWeight",
                   "CMS_flavTag_MuScaleDown": "flavTagWeight_Mu_Scale_DOWN/flavTagWeight",
                   "CMS_flavTag_MuResolUp": "flavTagWeight_Mu_Resol_UP/flavTagWeight",
                   "CMS_flavTag_MuResolDown": "flavTagWeight_Mu_Resol_DOWN/flavTagWeight",
                   "CMS_flavTag_MuTriggerUp": "flavTagWeight_Mu_Trigger_UP/flavTagWeight",
                   "CMS_flavTag_MuTriggerDown": "flavTagWeight_Mu_Trigger_DOWN/flavTagWeight",
                   "CMS_flavTag_MET_UnclEnergyUp": "flavTagWeight_MET_UnclEnergy_UP/flavTagWeight",
                   "CMS_flavTag_MET_UnclEnergyDown": "flavTagWeight_MET_UnclEnergy_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavB_C0_%sUp" % year: "flavTagWeight_Stat_flavB_C0_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavB_C0_%sDown" % year: "flavTagWeight_Stat_flavB_C0_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavB_C1_%sUp" % year: "flavTagWeight_Stat_flavB_C1_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavB_C1_%sDown" % year: "flavTagWeight_Stat_flavB_C1_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavB_C2_%sUp" % year: "flavTagWeight_Stat_flavB_C2_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavB_C2_%sDown" % year: "flavTagWeight_Stat_flavB_C2_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavB_C3_%sUp" % year: "flavTagWeight_Stat_flavB_C3_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavB_C3_%sDown" % year: "flavTagWeight_Stat_flavB_C3_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavB_C4_%sUp" % year: "flavTagWeight_Stat_flavB_C4_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavB_C4_%sDown" % year: "flavTagWeight_Stat_flavB_C4_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavB_B0_%sUp" % year: "flavTagWeight_Stat_flavB_B0_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavB_B0_%sDown" % year: "flavTagWeight_Stat_flavB_B0_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavB_B1_%sUp" % year: "flavTagWeight_Stat_flavB_B1_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavB_B1_%sDown" % year: "flavTagWeight_Stat_flavB_B1_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavB_B2_%sUp" % year: "flavTagWeight_Stat_flavB_B2_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavB_B2_%sDown" % year: "flavTagWeight_Stat_flavB_B2_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavB_B3_%sUp" % year: "flavTagWeight_Stat_flavB_B3_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavB_B3_%sDown" % year: "flavTagWeight_Stat_flavB_B3_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavB_B4_%sUp" % year: "flavTagWeight_Stat_flavB_B4_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavB_B4_%sDown" % year: "flavTagWeight_Stat_flavB_B4_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavC_C0_%sUp" % year: "flavTagWeight_Stat_flavC_C0_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavC_C0_%sDown" % year: "flavTagWeight_Stat_flavC_C0_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavC_C1_%sUp" % year: "flavTagWeight_Stat_flavC_C1_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavC_C1_%sDown" % year: "flavTagWeight_Stat_flavC_C1_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavC_C2_%sUp" % year: "flavTagWeight_Stat_flavC_C2_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavC_C2_%sDown" % year: "flavTagWeight_Stat_flavC_C2_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavC_C3_%sUp" % year: "flavTagWeight_Stat_flavC_C3_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavC_C3_%sDown" % year: "flavTagWeight_Stat_flavC_C3_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavC_C4_%sUp" % year: "flavTagWeight_Stat_flavC_C4_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavC_C4_%sDown" % year: "flavTagWeight_Stat_flavC_C4_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavC_B0_%sUp" % year: "flavTagWeight_Stat_flavC_B0_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavC_B0_%sDown" % year: "flavTagWeight_Stat_flavC_B0_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavC_B1_%sUp" % year: "flavTagWeight_Stat_flavC_B1_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavC_B1_%sDown" % year: "flavTagWeight_Stat_flavC_B1_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavC_B2_%sUp" % year: "flavTagWeight_Stat_flavC_B2_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavC_B2_%sDown" % year: "flavTagWeight_Stat_flavC_B2_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavC_B3_%sUp" % year: "flavTagWeight_Stat_flavC_B3_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavC_B3_%sDown" % year: "flavTagWeight_Stat_flavC_B3_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavC_B4_%sUp" % year: "flavTagWeight_Stat_flavC_B4_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavC_B4_%sDown" % year: "flavTagWeight_Stat_flavC_B4_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavL_C0_%sUp" % year: "flavTagWeight_Stat_flavL_C0_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavL_C0_%sDown" % year: "flavTagWeight_Stat_flavL_C0_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavL_C1_%sUp" % year: "flavTagWeight_Stat_flavL_C1_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavL_C1_%sDown" % year: "flavTagWeight_Stat_flavL_C1_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavL_C2_%sUp" % year: "flavTagWeight_Stat_flavL_C2_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavL_C2_%sDown" % year: "flavTagWeight_Stat_flavL_C2_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavL_C3_%sUp" % year: "flavTagWeight_Stat_flavL_C3_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavL_C3_%sDown" % year: "flavTagWeight_Stat_flavL_C3_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavL_C4_%sUp" % year: "flavTagWeight_Stat_flavL_C4_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavL_C4_%sDown" % year: "flavTagWeight_Stat_flavL_C4_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavL_B0_%sUp" % year: "flavTagWeight_Stat_flavL_B0_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavL_B0_%sDown" % year: "flavTagWeight_Stat_flavL_B0_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavL_B1_%sUp" % year: "flavTagWeight_Stat_flavL_B1_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavL_B1_%sDown" % year: "flavTagWeight_Stat_flavL_B1_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavL_B2_%sUp" % year: "flavTagWeight_Stat_flavL_B2_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavL_B2_%sDown" % year: "flavTagWeight_Stat_flavL_B2_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavL_B3_%sUp" % year: "flavTagWeight_Stat_flavL_B3_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavL_B3_%sDown" % year: "flavTagWeight_Stat_flavL_B3_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavL_B4_%sUp" % year: "flavTagWeight_Stat_flavL_B4_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavL_B4_%sDown" % year: "flavTagWeight_Stat_flavL_B4_DOWN/flavTagWeight",
                   "CMS_flavTag_LHE_muF_ttbarUp": "flavTagWeight_LHEScaleWeight_muF_ttbar_UP/flavTagWeight",
                   "CMS_flavTag_LHE_muF_ttbarDown": "flavTagWeight_LHEScaleWeight_muF_ttbar_DOWN/flavTagWeight",
                   "CMS_flavTag_LHE_muR_ttbarUp": "flavTagWeight_LHEScaleWeight_muR_ttbar_UP/flavTagWeight",
                   "CMS_flavTag_LHE_muR_ttbarDown": "flavTagWeight_LHEScaleWeight_muR_ttbar_DOWN/flavTagWeight",
                   "CMS_flavTag_LHE_muF_singletUp": "flavTagWeight_LHEScaleWeight_muF_singlet_UP/flavTagWeight",
                   "CMS_flavTag_LHE_muF_singletDown": "flavTagWeight_LHEScaleWeight_muF_singlet_DOWN/flavTagWeight",
                   "CMS_flavTag_LHE_muR_singletUp": "flavTagWeight_LHEScaleWeight_muR_singlet_UP/flavTagWeight",
                   "CMS_flavTag_LHE_muR_singletDown": "flavTagWeight_LHEScaleWeight_muR_singlet_DOWN/flavTagWeight",
                   "CMS_flavTag_LHE_muF_wjetsUp": "flavTagWeight_LHEScaleWeight_muF_wjets_UP/flavTagWeight",
                   "CMS_flavTag_LHE_muF_wjetsDown": "flavTagWeight_LHEScaleWeight_muF_wjets_DOWN/flavTagWeight",
                   "CMS_flavTag_LHE_muR_wjetsUp": "flavTagWeight_LHEScaleWeight_muR_wjets_UP/flavTagWeight",
                   "CMS_flavTag_LHE_muR_wjetsDown": "flavTagWeight_LHEScaleWeight_muR_wjets_DOWN/flavTagWeight",
                   "CMS_flavTag_LHE_muF_zjetsUp": "flavTagWeight_LHEScaleWeight_muF_zjets_UP/flavTagWeight",
                   "CMS_flavTag_LHE_muF_zjetsDown": "flavTagWeight_LHEScaleWeight_muF_zjets_DOWN/flavTagWeight",
                   "CMS_flavTag_LHE_muR_zjetsUp": "flavTagWeight_LHEScaleWeight_muR_zjets_UP/flavTagWeight",
                   "CMS_flavTag_LHE_muR_zjetsDown": "flavTagWeight_LHEScaleWeight_muR_zjets_DOWN/flavTagWeight",
                   "CMS_flavTag_LHE_muF_dibosonUp": "flavTagWeight_LHEScaleWeight_muF_diboson_UP/flavTagWeight",
                   "CMS_flavTag_LHE_muF_dibosonDown": "flavTagWeight_LHEScaleWeight_muF_diboson_DOWN/flavTagWeight",
                   "CMS_flavTag_LHE_muR_dibosonUp": "flavTagWeight_LHEScaleWeight_muR_diboson_UP/flavTagWeight",
                   "CMS_flavTag_LHE_muR_dibosonDown": "flavTagWeight_LHEScaleWeight_muR_diboson_DOWN/flavTagWeight",
                   "CMS_flavTag_LHE_PDF_ttbarUp": "flavTagWeight_LHEScaleWeight_PDF_ttbar_UP/flavTagWeight",
                   "CMS_flavTag_LHE_PDF_ttbarDown": "flavTagWeight_LHEScaleWeight_PDF_ttbar_DOWN/flavTagWeight",
                   "CMS_flavTag_LHE_PDF_singletUp": "flavTagWeight_LHEScaleWeight_PDF_singlet_UP/flavTagWeight",
                   "CMS_flavTag_LHE_PDF_singletDown": "flavTagWeight_LHEScaleWeight_PDF_singlet_DOWN/flavTagWeight",
                   "CMS_flavTag_LHE_PDF_wjetsUp": "flavTagWeight_LHEScaleWeight_PDF_wjets_UP/flavTagWeight",
                   "CMS_flavTag_LHE_PDF_wjetsDown": "flavTagWeight_LHEScaleWeight_PDF_wjets_DOWN/flavTagWeight",
                   "CMS_flavTag_LHE_PDF_zjetsUp": "flavTagWeight_LHEScaleWeight_PDF_zjets_UP/flavTagWeight",
                   "CMS_flavTag_LHE_PDF_zjetsDown": "flavTagWeight_LHEScaleWeight_PDF_zjets_DOWN/flavTagWeight",
                   "CMS_flavTag_LHE_PDF_dibosonUp": "flavTagWeight_LHEScaleWeight_PDF_diboson_UP/flavTagWeight",
                   "CMS_flavTag_LHE_PDF_dibosonDown": "flavTagWeight_LHEScaleWeight_PDF_diboson_DOWN/flavTagWeight",
                   "CMS_flavTag_LHE_aS_ttbarUp": "flavTagWeight_LHEScaleWeight_aS_ttbar_UP/flavTagWeight",
                   "CMS_flavTag_LHE_aS_ttbarDown": "flavTagWeight_LHEScaleWeight_aS_ttbar_DOWN/flavTagWeight",
                   "CMS_flavTag_LHE_aS_singletUp": "flavTagWeight_LHEScaleWeight_aS_singlet_UP/flavTagWeight",
                   "CMS_flavTag_LHE_aS_singletDown": "flavTagWeight_LHEScaleWeight_aS_singlet_DOWN/flavTagWeight",
                   "CMS_flavTag_LHE_aS_wjetsUp": "flavTagWeight_LHEScaleWeight_aS_wjets_UP/flavTagWeight",
                   "CMS_flavTag_LHE_aS_wjetsDown": "flavTagWeight_LHEScaleWeight_aS_wjets_DOWN/flavTagWeight",
                   "CMS_flavTag_LHE_aS_zjetsUp": "flavTagWeight_LHEScaleWeight_aS_zjets_UP/flavTagWeight",
                   "CMS_flavTag_LHE_aS_zjetsDown": "flavTagWeight_LHEScaleWeight_aS_zjets_DOWN/flavTagWeight",
                   "CMS_flavTag_LHE_aS_dibosonUp": "flavTagWeight_LHEScaleWeight_aS_diboson_UP/flavTagWeight",
                   "CMS_flavTag_LHE_aS_dibosonDown": "flavTagWeight_LHEScaleWeight_aS_diboson_DOWN/flavTagWeight",
                   "CMS_flavTag_PS_ISR_ttbarUp": "flavTagWeight_PSWeightISR_ttbar_UP/flavTagWeight",
                   "CMS_flavTag_PS_ISR_ttbarDown": "flavTagWeight_PSWeightISR_ttbar_DOWN/flavTagWeight",
                   "CMS_flavTag_PS_FSR_ttbarUp": "flavTagWeight_PSWeightFSR_ttbar_UP/flavTagWeight",
                   "CMS_flavTag_PS_FSR_ttbarDown": "flavTagWeight_PSWeightFSR_ttbar_DOWN/flavTagWeight",
                   "CMS_flavTag_PS_ISR_singletUp": "flavTagWeight_PSWeightISR_singlet_UP/flavTagWeight",
                   "CMS_flavTag_PS_ISR_singletDown": "flavTagWeight_PSWeightISR_singlet_DOWN/flavTagWeight",
                   "CMS_flavTag_PS_FSR_singletUp": "flavTagWeight_PSWeightFSR_singlet_UP/flavTagWeight",
                   "CMS_flavTag_PS_FSR_singletDown": "flavTagWeight_PSWeightFSR_singlet_DOWN/flavTagWeight",
                   "CMS_flavTag_PS_ISR_wjetsUp": "flavTagWeight_PSWeightISR_wjets_UP/flavTagWeight",
                   "CMS_flavTag_PS_ISR_wjetsDown": "flavTagWeight_PSWeightISR_wjets_DOWN/flavTagWeight",
                   "CMS_flavTag_PS_FSR_wjetsUp": "flavTagWeight_PSWeightFSR_wjets_UP/flavTagWeight",
                   "CMS_flavTag_PS_FSR_wjetsDown": "flavTagWeight_PSWeightFSR_wjets_DOWN/flavTagWeight",
                   "CMS_flavTag_PS_ISR_zjetsUp": "flavTagWeight_PSWeightISR_zjets_UP/flavTagWeight",
                   "CMS_flavTag_PS_ISR_zjetsDown": "flavTagWeight_PSWeightISR_zjets_DOWN/flavTagWeight",
                   "CMS_flavTag_PS_FSR_zjetsUp": "flavTagWeight_PSWeightFSR_zjets_UP/flavTagWeight",
                   "CMS_flavTag_PS_FSR_zjetsDown": "flavTagWeight_PSWeightFSR_zjets_DOWN/flavTagWeight",
                   "CMS_flavTag_PS_ISR_dibosonUp": "flavTagWeight_PSWeightISR_diboson_UP/flavTagWeight",
                   "CMS_flavTag_PS_ISR_dibosonDown": "flavTagWeight_PSWeightISR_diboson_DOWN/flavTagWeight",
                   "CMS_flavTag_PS_FSR_dibosonUp": "flavTagWeight_PSWeightFSR_diboson_UP/flavTagWeight",
                   "CMS_flavTag_PS_FSR_dibosonDown": "flavTagWeight_PSWeightFSR_diboson_DOWN/flavTagWeight",
                   "CMS_flavTag_JES_AbsoluteUp": "flavTagWeight_JESRegrouped_Absolute_UP/flavTagWeight",
                   "CMS_flavTag_JES_AbsoluteDown": "flavTagWeight_JESRegrouped_Absolute_DOWN/flavTagWeight",
                   "CMS_flavTag_JES_BBEC1Up": "flavTagWeight_JESRegrouped_BBEC1_UP/flavTagWeight",
                   "CMS_flavTag_JES_BBEC1Down": "flavTagWeight_JESRegrouped_BBEC1_DOWN/flavTagWeight",
                   "CMS_flavTag_JES_FlavorQCDUp": "flavTagWeight_JESRegrouped_FlavorQCD_UP/flavTagWeight",
                   "CMS_flavTag_JES_FlavorQCDDown": "flavTagWeight_JESRegrouped_FlavorQCD_DOWN/flavTagWeight",
                   "CMS_flavTag_JES_RelativeBalUp": "flavTagWeight_JESRegrouped_RelativeBal_UP/flavTagWeight",
                   "CMS_flavTag_JES_RelativeBalDown": "flavTagWeight_JESRegrouped_RelativeBal_DOWN/flavTagWeight",
                   "CMS_flavTag_JES_Absolute_%sUp" % year: "flavTagWeight_JESRegrouped_Absolute_%s_UP/flavTagWeight" % year,
                   "CMS_flavTag_JES_Absolute_%sDown" % year: "flavTagWeight_JESRegrouped_Absolute_%s_DOWN/flavTagWeight" % year,
                   "CMS_flavTag_JES_BBEC1_%sUp" % year: "flavTagWeight_JESRegrouped_BBEC1_%s_UP/flavTagWeight" % year,
                   "CMS_flavTag_JES_BBEC1_%sDown" % year: "flavTagWeight_JESRegrouped_BBEC1_%s_DOWN/flavTagWeight" % year,
                   "CMS_flavTag_JES_RelativeSample_%sUp" % year: "flavTagWeight_JESRegrouped_RelativeSample_%s_UP/flavTagWeight" % year,
                   "CMS_flavTag_JES_RelativeSample_%sDown" % year: "flavTagWeight_JESRegrouped_RelativeSample_%s_DOWN/flavTagWeight" % year,
                   "CMS_flavTag_JEReta0to1p93_%sUp" % year: "flavTagWeight_JEReta0to1p93_UP/flavTagWeight",
                   "CMS_flavTag_JEReta0to1p93_%sDown" % year: "flavTagWeight_JEReta0to1p93_DOWN/flavTagWeight",
                   "CMS_flavTag_JEReta1p93to2p5_%sUp" % year: "flavTagWeight_JEReta1p93to2p5_UP/flavTagWeight",
                   "CMS_flavTag_JEReta1p93to2p5_%sDown" % year: "flavTagWeight_JEReta1p93to2p5_DOWN/flavTagWeight",
                   # Hdamp, b fragmentation, LHE scale, PS weights
                   "topHdampWeight_%sUp" % year: f"TOPMLWeight[1]*TOPMLWeightNorm{suffix}[1]",
                   "topHdampWeight_%sDown" % year: f"TOPMLWeight[3]*TOPMLWeightNorm{suffix}[3]",
                   "bFragWeight_%sUp" % year: f"(TOPMLWeight[4]*TOPMLWeightNorm{suffix}[4])/(TOPMLWeight[5]*TOPMLWeightNorm{suffix}[5])",  # Divide by bFrag nominal and multiply by bFrag up
                   "bFragWeight_%sDown" % year: f"1/(TOPMLWeight[5]*TOPMLWeightNorm{suffix}[5])",  # The standard samples are effectively bFrag down, so here just dividing by bFrag nominal and its renorm weight
                   "bFragPetersonWeight_%sUp" % year: f"(bFragAndDecayWeight[3]*BFragAndDecayWeightNorm{suffix}[3])/(TOPMLWeight[5]*TOPMLWeightNorm{suffix}[5])",  # A one-sided systematic
                   "bFragPetersonWeight_%sDown" % year: f"1.",  # Effectively a one-sided systematic
                   # LHE for large bkgs
                   "LHE_muF_%sUp" % year: f"LHEScaleWeight[5]*LHEScaleWeightNorm{suffix}[5]",
                   "LHE_muF_%sDown" % year: f"LHEScaleWeight[3]*LHEScaleWeightNorm{suffix}[3]",
                   "LHE_muR_%sUp" % year: f"LHEScaleWeight[7]*LHEScaleWeightNorm{suffix}[7]",
                   "LHE_muR_%sDown" % year: f"LHEScaleWeight[1]*LHEScaleWeightNorm{suffix}[1]",
                   # PS for minor bkgs
                   "minorBkg_PS_ISR_%sUp" % year: f"PSWeight[0]*PSWeightNorm{suffix}[0]",
                   "minorBkg_PS_ISR_%sDown" % year: f"PSWeight[2]*PSWeightNorm{suffix}[2]",
                   "minorBkg_PS_FSR_%sUp" % year: f"PSWeight[1]*PSWeightNorm{suffix}[1]",
                   "minorBkg_PS_FSR_%sDown" % year: f"PSWeight[3]*PSWeightNorm{suffix}[3]",
                   # PS-fsr for large bkgs
                   "PS_fsr_G2GG_muR_%sDown" % year: f"PSWeight[6]*PSWeightNorm{suffix}[6]",
                   "PS_fsr_G2GG_muR_%sUp" % year: f"PSWeight[7]*PSWeightNorm{suffix}[7]",
                   "PS_fsr_G2QQ_muR_%sDown" % year: f"PSWeight[8]*PSWeightNorm{suffix}[8]",
                   "PS_fsr_G2QQ_muR_%sUp" % year: f"PSWeight[9]*PSWeightNorm{suffix}[9]",
                   "PS_fsr_Q2QG_muR_%sDown" % year: f"PSWeight[10]*PSWeightNorm{suffix}[10]",
                   "PS_fsr_Q2QG_muR_%sUp" % year: f"PSWeight[11]*PSWeightNorm{suffix}[11]",
                   "PS_fsr_X2XG_muR_%sDown" % year: f"PSWeight[12]*PSWeightNorm{suffix}[12]",
                   "PS_fsr_X2XG_muR_%sUp" % year: f"PSWeight[13]*PSWeightNorm{suffix}[13]",
                   "PS_fsr_G2GG_cNS_%sDown" % year: f"PSWeight[14]*PSWeightNorm{suffix}[14]",
                   "PS_fsr_G2GG_cNS_%sUp" % year: f"PSWeight[15]*PSWeightNorm{suffix}[15]",
                   "PS_fsr_G2QQ_cNS_%sDown" % year: f"PSWeight[16]*PSWeightNorm{suffix}[16]",
                   "PS_fsr_G2QQ_cNS_%sUp" % year: f"PSWeight[17]*PSWeightNorm{suffix}[17]",
                   "PS_fsr_G2QG_cNS_%sDown" % year: f"PSWeight[18]*PSWeightNorm{suffix}[18]",
                   "PS_fsr_G2QG_cNS_%sUp" % year: f"PSWeight[19]*PSWeightNorm{suffix}[19]",
                   "PS_fsr_X2XG_cNS_%sDown" % year: f"PSWeight[20]*PSWeightNorm{suffix}[20]",
                   "PS_fsr_X2XG_cNS_%sUp" % year: f"PSWeight[21]*PSWeightNorm{suffix}[21]",
                   # PS-isr for large bkgs
                   "PS_isr_G2GG_muR_%sDown" % year: f"PSWeight[28]*PSWeightNorm{suffix}[28]",
                   "PS_isr_G2GG_muR_%sUp" % year: f"PSWeight[29]*PSWeightNorm{suffix}[29]",
                   "PS_isr_G2QQ_muR_%sDown" % year: f"PSWeight[30]*PSWeightNorm{suffix}[30]",
                   "PS_isr_G2QQ_muR_%sUp" % year: f"PSWeight[31]*PSWeightNorm{suffix}[31]",
                   "PS_isr_Q2QG_muR_%sDown" % year: f"PSWeight[32]*PSWeightNorm{suffix}[32]",
                   "PS_isr_Q2QG_muR_%sUp" % year: f"PSWeight[33]*PSWeightNorm{suffix}[33]",
                   "PS_isr_X2XG_muR_%sDown" % year: f"PSWeight[34]*PSWeightNorm{suffix}[34]",
                   "PS_isr_X2XG_muR_%sUp" % year: f"PSWeight[35]*PSWeightNorm{suffix}[35]",
                   "PS_isr_G2GG_cNS_%sDown" % year: f"PSWeight[36]*PSWeightNorm{suffix}[36]",
                   "PS_isr_G2GG_cNS_%sUp" % year: f"PSWeight[37]*PSWeightNorm{suffix}[37]",
                   "PS_isr_G2QQ_cNS_%sDown" % year: f"PSWeight[38]*PSWeightNorm{suffix}[38]",
                   "PS_isr_G2QQ_cNS_%sUp" % year: f"PSWeight[39]*PSWeightNorm{suffix}[39]",
                   "PS_isr_G2QG_cNS_%sDown" % year: f"PSWeight[40]*PSWeightNorm{suffix}[40]",
                   "PS_isr_G2QG_cNS_%sUp" % year: f"PSWeight[41]*PSWeightNorm{suffix}[41]",
                   "PS_isr_X2XG_cNS_%sDown" % year: f"PSWeight[42]*PSWeightNorm{suffix}[42]",
                   "PS_isr_X2XG_cNS_%sUp" % year: f"PSWeight[43]*PSWeightNorm{suffix}[43]",
                   }

    return systematics


def applicable_selections(infile, selections, mc_data_obs_5fs, mc_data_obs_4fs_mc_5fs, use5fs=False):
    """
    Same eligibility logic as the inner "for selection_name in selections" loop of
    the original script's process_tree, but evaluated once up front so it can drive
    job construction instead of a runtime skip inside a per-file worker.

    - use5fs: take the ttbb/ttbj/tt2b sub-categories from ttbar-powheg (5FS), like
      every other ttbar sub-category, instead of from the dedicated ttbb-4f (4FS)
      sample. Inspired by hdumper.py's --use5FS: with this on, ttbb-4f produces no
      jobs at all and powheg fills the nominal ttbb/ttbj/tt2b templates directly
      (plain names, full systematics -- not the "_5FS" proxy templates that
      --mc_data_obs_5fs adds alongside the 4FS nominal).
    """
    names = []
    for selection_name in selections:
        if not "base" in selection_name and not any(x in infile for x in tt_file_names):
            continue
        if any(x in infile for x in tt_file_names) and "base" in selection_name:
            continue
        if any(x in selection_name for x in tt4f_strings):
            if use5fs:
                if not "powheg" in infile:
                    continue
            elif not "4f" in infile and not ((mc_data_obs_5fs or mc_data_obs_4fs_mc_5fs) and "powheg" in infile):
                continue
        if any(x in selection_name for x in tt_strings) and not "powheg" in infile:
            continue
        names.append(selection_name)
    return names


def build_jobs(input_files, selections, mc_data_obs_5fs, mc_data_obs_4fs_mc_5fs, use5fs=False):
    """
    One job per (input file, ttbar sub-category) pair, instead of one job per input
    file. A background/data file only ever has one applicable selection ("base"), so
    it still becomes exactly one job; a file like ttbar-powheg that is eligible for
    several sub-categories is split into that many independent jobs, so its total
    work can be spread across several workers instead of monopolizing one.
    """
    jobs = []
    for infile in input_files:
        if "QCD_tree" in infile:
            print(f"{Fore.YELLOW}Skipping QCD multijet file: {infile}{Style.RESET_ALL}")
            continue
        for selection_name in applicable_selections(infile, selections, mc_data_obs_5fs, mc_data_obs_4fs_mc_5fs, use5fs):
            jobs.append((infile, selection_name))
    return jobs


def _ensure_implicit_mt(threads_per_job):
    # Must be called for the first time *inside* each forked worker, never in the
    # parent before mp.Pool is created: enabling ROOT's thread pool before a fork
    # leaves the child with a half-initialized pool (only the forking thread
    # survives fork()), which can deadlock on first use.
    if threads_per_job and threads_per_job > 1 and not ROOT.IsImplicitMTEnabled():
        ROOT.EnableImplicitMT(threads_per_job)


def _job_tag(infile, selection_name):
    digest = hashlib.md5(infile.encode()).hexdigest()[:10]
    base = os.path.basename(infile).replace('.root', '')
    return f"{base}__{selection_name}__{digest}"


def process_tree_job(job, output_files, tree_name, year, selections, adhoc_selection, adhoc_binning,
                      tmp_dir, mc_data_obs_5fs=False, mc_data_obs_4fs_mc_5fs=False,
                      flavtag_sf_json=None, flavtag_sf_name=None, threads_per_job=1):
    """
    Process exactly one (input file, ttbar sub-category) job: same physics content
    (selections, weights, systematics, binning) as the original process_tree, but
    restricted to a single selection_name, with histograms written to a private
    temp file instead of the shared output files. Returns a list of
    (temp_file_path, real_output_file) pairs for the merge step to consume.
    """
    infile, selection_name = job
    _ensure_implicit_mt(threads_per_job)

    print(f"{Fore.RED}Processing file: {infile} [{selection_name}]{Style.RESET_ALL}")

    input_file = ROOT.TFile.Open(infile)
    if not input_file or input_file.IsZombie():
        raise FileNotFoundError(f"Could not open file: {infile}")

    tree = input_file.Get(tree_name)
    if not tree or not isinstance(tree, ROOT.TTree):
        raise ValueError(f"TTree '{tree_name}' not found in file '{infile}'.")

    tree.SetCacheSize(50000000)
    tree.AddBranchToCache("*", True)

    df = ROOT.RDataFrame(tree)

    base_filter = selections["base"]
    if "singlee" in infile:
        base_filter += " && passTrigMu==0"
    df = df.Filter(base_filter)

    is_data = is_data_infile(infile)

    flavtag_prefix = flavTagWeightPlugin.STORED_WEIGHT_NAME
    if flavtag_sf_json and not is_data:
        df, flavtag_prefix = flavTagWeightPlugin.define_flavtag_weights(
            df, year, json_path=flavtag_sf_json, correction_name=flavtag_sf_name,
            systematics=flavTagWeightPlugin.extract_systematics(produce_systematics(year, '').values()))

    df = df.Define("denominator", "score_ttbb + score_tt2b + score_ttbj + score_ttcc + score_tt2c + score_ttcj + score_ttLF") \
        .Define("fscore_ttbb", "score_ttbb / denominator") \
        .Define("fscore_tt2b", "score_tt2b / denominator") \
        .Define("fscore_ttbj", "score_ttbj / denominator") \
        .Define("fscore_ttcc", "score_ttcc / denominator") \
        .Define("fscore_tt2c", "score_tt2c / denominator") \
        .Define("fscore_ttcj", "score_ttcj / denominator") \
        .Define("fscore_ttLF", "score_ttLF / denominator")

    is_5fs_proxy_selection = mc_data_obs_5fs and "powheg" in infile and any(x in selection_name for x in tt4f_strings)
    is_4fs_proxy_selection = mc_data_obs_4fs_mc_5fs and "4f" in infile and "-dps" not in infile and any(x in selection_name for x in tt4f_strings)
    is_5fs_nominal_selection = mc_data_obs_4fs_mc_5fs and "powheg" in infile and any(x in selection_name for x in tt4f_strings)

    suffix = suffix_dict.get(selection_name, '')

    if not "base" in selection_name:
        df_selected = df.Filter(selections[selection_name])
    else:
        df_selected = df

    # Lazy: these are only materialized together with the histograms below, so this
    # progress printout doesn't cost an extra pass over the tree.
    count_after_base = df.Count()
    count_after_selection = df_selected.Count() if not "base" in selection_name else None

    systematics = produce_systematics(year, suffix)
    systematics = {name: flavTagWeightPlugin.remap_expression(expr, flavtag_prefix)
                   for name, expr in systematics.items()}

    # For data the weight never depends on `syst` (it is always the jet-veto-map
    # term), so only the central histogram is meaningful; producing one per
    # systematic name would just be ~150 identical copies that nothing downstream
    # reads (CombineHarvester only pulls the plain "data_obs").
    systs_to_run = ["None"] if is_data else list(systematics.keys())

    perProcessSystsWithoutLHEmuRmuF = [s for s in perProcessSysts
                                        if not (s.startswith("LHE_muR") or s.startswith("LHE_muF") or s.startswith("minorBkg_PS_"))]

    histograms = {}
    for syst in systs_to_run:
        if is_5fs_proxy_selection and syst != "None":
            continue
        if is_4fs_proxy_selection and syst != "None":
            continue
        if any(syst.startswith(procDepSyst) for procDepSyst in perProcessSystsWithoutLHEmuRmuF) and "tt" not in infile:
            continue
        if syst.startswith("minorBkg") and "tt" in infile:
            continue

        if syst == "None":
            weight = assign_event_weight(year, infile, suffix, flavtag_weight_branch=flavtag_prefix)
        else:
            weight = assign_event_weight(year, infile, suffix, systematics[syst], flavtag_weight_branch=flavtag_prefix)

        weight_column = f"weight_{selection_name}_{syst}"
        if not is_data:
            df_selected_w = df_selected.Define(weight_column, weight)
        else:
            df_selected_w = df_selected.Define(weight_column, "1")

        for (score, adhoc_sel), outfile in zip(adhoc_selection.items(), output_files):
            hist_name = infile.split('/')[-1].replace('_tree.root', '')
            if any(x in infile for x in tt_file_names) and "-dps" not in infile:
                hist_name = selection_name
                if is_5fs_proxy_selection:
                    hist_name = f"{hist_name}_5FS"
                elif is_4fs_proxy_selection:
                    hist_name = f"{hist_name}_4FS"
                elif is_5fs_nominal_selection:
                    hist_name = selection_name
            elif any(x in infile for x in tt_file_names) and "-dps" in infile:
                hist_name = selection_name + "-dps"

            if not syst == "None":
                if any(procDepSyst in syst for procDepSyst in perProcessSysts):
                    process_flag = hist_name.split('_')[0]
                    new_syst_name = syst.replace(f"_{year}", f"_{process_flag}_{year}") if "bFrag" not in syst else syst
                    hist_name = f"{hist_name}_{new_syst_name}"
                else:
                    hist_name = f"{hist_name}_{syst}"

            final_df = df_selected_w.Filter(adhoc_sel)
            hist_key = (outfile, hist_name)
            histograms[hist_key] = final_df.Histo1D(
                (hist_name, f"Histogram of {score} for process {hist_name}",
                 len(adhoc_binning[score]) - 1, adhoc_binning[score]),
                score, weight_column
            )

    n_base = count_after_base.GetValue()
    n_sel = count_after_selection.GetValue() if count_after_selection is not None else n_base
    print(f"[{infile} | {selection_name}] events after base selection: {n_base}, after additional selection: {n_sel}")

    print(f"Materializing {len(histograms)} histograms for {infile} [{selection_name}]...")
    materialized = {key: h.GetPtr() for key, h in histograms.items()}

    by_outfile = {}
    for (outfile, hist_name), hist in materialized.items():
        by_outfile.setdefault(outfile, []).append(hist)

    job_tag = _job_tag(infile, selection_name)
    manifest = []
    for outfile, hists in by_outfile.items():
        tmp_path = os.path.join(tmp_dir, f"{job_tag}__{os.path.basename(outfile)}")
        tmp_handle = ROOT.TFile(tmp_path, "RECREATE")
        for hist in hists:
            hist.Write()
        tmp_handle.Close()
        manifest.append((tmp_path, outfile))

    input_file.Close()
    print(f"{Fore.GREEN}Completed processing {infile} [{selection_name}]{Style.RESET_ALL}")
    return manifest


def process_trees_parallel(input_files, output_files, tree_name, year, selections, adhoc_selection, adhoc_binning,
                            tmp_dir, nproc=1, mc_data_obs_5fs=False, mc_data_obs_4fs_mc_5fs=False,
                            flavtag_sf_json=None, flavtag_sf_name=None, threads_per_job=1, use5fs=False):
    jobs = build_jobs(input_files, selections, mc_data_obs_5fs, mc_data_obs_4fs_mc_5fs, use5fs)
    print(f"{Fore.CYAN}Built {len(jobs)} (file, category) jobs from {len(input_files)} input files.{Style.RESET_ALL}")

    process_func = partial(
        process_tree_job,
        output_files=output_files,
        tree_name=tree_name,
        year=year,
        selections=selections,
        adhoc_selection=adhoc_selection,
        adhoc_binning=adhoc_binning,
        tmp_dir=tmp_dir,
        mc_data_obs_5fs=mc_data_obs_5fs,
        mc_data_obs_4fs_mc_5fs=mc_data_obs_4fs_mc_5fs,
        flavtag_sf_json=flavtag_sf_json,
        flavtag_sf_name=flavtag_sf_name,
        threads_per_job=threads_per_job,
    )

    max_procs = min(len(jobs), mp.cpu_count()) if jobs else 1
    use_procs = min(max(1, int(nproc)), max_procs)
    if use_procs <= 1:
        manifests = [process_func(job) for job in jobs]
    else:
        with mp.Pool(processes=use_procs) as pool:
            manifests = pool.map(process_func, jobs)

    return [entry for manifest in manifests for entry in manifest]


def merge_job_outputs(manifest, final_outfiles, mode="UPDATE", cleanup=True):
    """
    Consolidate the per-job temp ROOT files referenced in `manifest` (a list of
    (temp_path, real_outfile) pairs) into the real output files. Histogram names
    are already unique within a given target (they encode the contributing
    physics process/systematic), so a plain read-then-Write per histogram is
    sufficient -- no summing across temp files is needed.
    """
    by_target = {}
    for tmp_path, real_outfile in manifest:
        by_target.setdefault(real_outfile, []).append(tmp_path)

    for real_outfile in final_outfiles:
        tmp_paths = by_target.get(real_outfile, [])
        if not tmp_paths:
            continue
        out_handle = ROOT.TFile(real_outfile, mode)
        for tmp_path in tmp_paths:
            tmp_handle = ROOT.TFile.Open(tmp_path)
            if not tmp_handle or tmp_handle.IsZombie():
                print(f"{Fore.YELLOW}WARNING: could not open temp file {tmp_path}, skipping.{Style.RESET_ALL}")
                continue
            for key in tmp_handle.GetListOfKeys():
                obj = key.ReadObj()
                if isinstance(obj, ROOT.TH1):
                    out_handle.cd()
                    obj.Write(obj.GetName(), ROOT.TObject.kOverwrite)
            tmp_handle.Close()
        out_handle.Close()

    if cleanup:
        for tmp_paths in by_target.values():
            for tmp_path in tmp_paths:
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass


def process_tree_extra_syst_job(job, output_files, tree_name, year, selections, adhoc_selection, adhoc_binning,
                                 tmp_dir, flavtag_sf_json=None, flavtag_sf_name=None, use5fs=False):
    """
    Same content as prepareHistosForCards.process_tree_extra_syst, but for one
    (input file, combine_syst_name) job, writing to a private temp file.
    """
    infile, combine_syst_name = job
    print(f"{Fore.CYAN}Processing external systematic file: {infile} ({combine_syst_name}){Style.RESET_ALL}")

    if "QCD_tree" in infile:
        return []

    try:
        return _process_tree_extra_syst_job_impl(infile, combine_syst_name, output_files, tree_name, year,
                                                  selections, adhoc_selection, adhoc_binning, tmp_dir,
                                                  flavtag_sf_json, flavtag_sf_name, use5fs)
    except Exception as exc:
        # A single problematic external-systematic file (e.g. one missing a branch
        # that only the nominal production carries) shouldn't take down the whole
        # batch and skip sum_data() for every other, already-computed histogram.
        print(f"{Fore.YELLOW}WARNING: skipping {infile} ({combine_syst_name}) due to error: {exc}{Style.RESET_ALL}")
        return []


def _process_tree_extra_syst_job_impl(infile, combine_syst_name, output_files, tree_name, year, selections,
                                       adhoc_selection, adhoc_binning, tmp_dir, flavtag_sf_json=None,
                                       flavtag_sf_name=None, use5fs=False):
    input_file = ROOT.TFile.Open(infile)
    if not input_file or input_file.IsZombie():
        raise FileNotFoundError(f"Could not open file: {infile}")

    tree = input_file.Get(tree_name)
    if not tree or not isinstance(tree, ROOT.TTree):
        raise ValueError(f"TTree '{tree_name}' not found in file '{infile}'.")

    tree.SetCacheSize(50000000)
    tree.AddBranchToCache("*", True)

    df = ROOT.RDataFrame(tree)

    base_filter = selections["base"]
    if "singlee" in infile:
        base_filter += " && passTrigMu==0"
    df = df.Filter(base_filter)

    is_data = is_data_infile(infile)

    # Recompute the central flavour-tagging weight on the fly from an alternate
    # correctionlib SF file, same as the main phase. Only the central value is
    # needed here: these external systematic-shape files (e.g. JES) contribute a
    # single named shape variation, not the full flavTagWeight_<syst>_UP/DOWN set.
    flavtag_prefix = flavTagWeightPlugin.STORED_WEIGHT_NAME
    if flavtag_sf_json and not is_data:
        df, flavtag_prefix = flavTagWeightPlugin.define_flavtag_weights(
            df, year, json_path=flavtag_sf_json, correction_name=flavtag_sf_name)

    df = df.Define("denominator", "score_ttbb + score_tt2b + score_ttbj + score_ttcc + score_tt2c + score_ttcj + score_ttLF") \
        .Define("fscore_ttbb", "score_ttbb / denominator") \
        .Define("fscore_tt2b", "score_tt2b / denominator") \
        .Define("fscore_ttbj", "score_ttbj / denominator") \
        .Define("fscore_ttcc", "score_ttcc / denominator") \
        .Define("fscore_tt2c", "score_tt2c / denominator") \
        .Define("fscore_ttcj", "score_ttcj / denominator") \
        .Define("fscore_ttLF", "score_ttLF / denominator")

    # External systematic-shape productions (e.g. JES) don't always carry the same
    # custom branches as the nominal production (e.g. TOPMLWeight); only append
    # terms that reference branches actually present on this particular tree.
    available_columns = {str(c) for c in df.GetColumnNames()}

    histograms = {}
    for selection_name in selections:
        if not "base" in selection_name and not any(x in infile for x in tt_file_names):
            continue
        if any(x in infile for x in tt_file_names) and "base" in selection_name:
            continue
        if any(x in selection_name for x in tt4f_strings):
            if use5fs:
                if not "powheg" in infile:
                    continue
            elif not "4f" in infile:
                continue
        if any(x in selection_name for x in tt_strings) and not "powheg" in infile:
            continue

        suffix = suffix_dict.get(selection_name, '')

        if not "base" in selection_name:
            df_selected = df.Filter(selections[selection_name])
        else:
            df_selected = df

        weight = assign_event_weight(year, infile, suffix, flavtag_weight_branch=flavtag_prefix,
                                      available_columns=available_columns)
        weight_column = f"weight_{selection_name}_{combine_syst_name}"

        if not is_data_infile(infile):
            df_selected = df_selected.Define(weight_column, weight)
        else:
            df_selected = df_selected.Define(weight_column, "1")

        for (score, adhoc_sel), outfile in zip(adhoc_selection.items(), output_files):
            hist_name = infile.split('/')[-1].replace('_tree.root', '')
            if any(x in infile for x in tt_file_names) and "-dps" not in infile:
                hist_name = selection_name
            elif any(x in infile for x in tt_file_names) and "-dps" in infile:
                hist_name = selection_name + "-dps"

            hist_name = f"{hist_name}_{combine_syst_name}"
            final_df = df_selected.Filter(adhoc_sel)
            hist_key = (outfile, hist_name)
            histograms[hist_key] = final_df.Histo1D(
                (hist_name, f"Histogram of {score} for process {hist_name}",
                 len(adhoc_binning[score]) - 1, adhoc_binning[score]),
                score, weight_column
            )

    materialized = {key: h.GetPtr() for key, h in histograms.items()}

    by_outfile = {}
    for (outfile, hist_name), hist in materialized.items():
        by_outfile.setdefault(outfile, []).append(hist)

    job_tag = _job_tag(infile, f"extrasyst_{combine_syst_name}")
    manifest = []
    for outfile, hists in by_outfile.items():
        tmp_path = os.path.join(tmp_dir, f"{job_tag}__{os.path.basename(outfile)}")
        tmp_handle = ROOT.TFile(tmp_path, "RECREATE")
        for hist in hists:
            hist.Write(hist.GetName(), ROOT.TObject.kOverwrite)
        tmp_handle.Close()
        manifest.append((tmp_path, outfile))

    input_file.Close()
    return manifest


def add_extra_systematic_histograms(extra_syst_dir, output_files, tree_name, year, selections, adhoc_selection,
                                     adhoc_binning, tmp_dir, nproc=1, flavtag_sf_json=None, flavtag_sf_name=None,
                                     use5fs=False):
    """
    Directory layout is expected to be: extra_syst_dir/<syst_dir_name>/*.root
    The histogram suffix is the same as <syst_dir_name>. Each (input file,
    syst_dir) pair is independent, so this is parallelized the same way as the
    main phase.

    - flavtag_sf_json / flavtag_sf_name: same as for the main phase -- if given,
      the flavour-tagging weight is recomputed on the fly from this alternate
      correctionlib SF file for these external systematic-shape files too.
    """
    if not extra_syst_dir:
        return

    if not os.path.isdir(extra_syst_dir):
        print(f"{Fore.YELLOW}WARNING: external syst directory not found: {extra_syst_dir}{Style.RESET_ALL}")
        return

    syst_dirs = sorted([d for d in glob.glob(os.path.join(extra_syst_dir, "*")) if os.path.isdir(d)])
    if len(syst_dirs) == 0:
        print(f"{Fore.YELLOW}WARNING: no systematic subdirectories found in: {extra_syst_dir}{Style.RESET_ALL}")
        return

    def to_combine_syst_name(syst_dir_name):
        if syst_dir_name.endswith("_up"):
            return syst_dir_name[:-3] + "Up"
        if syst_dir_name.endswith("_down"):
            return syst_dir_name[:-5] + "Down"
        return syst_dir_name

    jobs = []
    for syst_dir in syst_dirs:
        syst_dir_name = os.path.basename(syst_dir.rstrip("/"))
        if not (syst_dir_name.endswith("_up") or syst_dir_name.endswith("_down")):
            print(f"{Fore.YELLOW}Skipping non-shape directory: {syst_dir_name}{Style.RESET_ALL}")
            continue

        input_files = sorted(glob.glob(os.path.join(syst_dir, "*_tree.root")))
        if len(input_files) == 0:
            print(f"{Fore.YELLOW}No input ROOT files found in {syst_dir}{Style.RESET_ALL}")
            continue

        combine_syst_name = to_combine_syst_name(syst_dir_name)
        print(f"{Fore.MAGENTA}Adding external systematic {syst_dir_name} -> {combine_syst_name}{Style.RESET_ALL}")
        for infile in input_files:
            jobs.append((infile, combine_syst_name))

    if not jobs:
        return

    process_func = partial(
        process_tree_extra_syst_job,
        output_files=output_files,
        tree_name=tree_name,
        year=year,
        selections=selections,
        adhoc_selection=adhoc_selection,
        adhoc_binning=adhoc_binning,
        tmp_dir=tmp_dir,
        flavtag_sf_json=flavtag_sf_json,
        flavtag_sf_name=flavtag_sf_name,
        use5fs=use5fs,
    )

    max_procs = min(len(jobs), mp.cpu_count())
    use_procs = min(max(1, int(nproc)), max_procs)
    if use_procs <= 1:
        manifests = [process_func(job) for job in jobs]
    else:
        with mp.Pool(processes=use_procs) as pool:
            manifests = pool.map(process_func, jobs)

    manifest = [entry for m in manifests for entry in m]
    merge_job_outputs(manifest, output_files, mode="UPDATE")


def read_csv(csv_file):
    """
    Open and read a csv file containing the name and the range of the variables to be histogrammed.
    Fill in a list of dictionaries containing branch (i.e., variable name), nbins, xmin, and xmax information.
    """
    import csv
    with open(csv_file, mode='r') as f:
        csv_reader = csv.reader(f)
        dict_list = [
            {'branch': line[0], 'nbins': line[1], 'xmin': line[2], 'xmax': line[3]}
            for line in csv_reader if not line[0] == 'Variable'
        ]
    return dict_list


def prepare_output(output_dir, year, categories, prepend, append):
    os.makedirs(output_dir + str(year), exist_ok=True)
    name_list = [prepend + cat for cat in categories]
    name_list = [name + append[1] if 'Wcb' in name else name + append[0] for name in name_list]
    return [f"{output_dir}{year}/{name}.root" for name in name_list]


def sum_data(output_files, mc_data_obs_5fs=False, mc_data_obs_4fs_mc_5fs=False):
    for outfile in output_files:
        fIn = ROOT.TFile.Open(outfile, "UPDATE")
        if not fIn or fIn.IsZombie():
            print(f"Error opening output file: {outfile}")
            continue

        if isinstance(fIn.Get("data_obs"), ROOT.TH1):
            # Already built by a previous run (singlee/singlemu are consumed/deleted
            # once this succeeds), so there's nothing to redo -- and nothing left to
            # rebuild it from even if we wanted to.
            print(f"data_obs already present in {outfile}, skipping.")
            fIn.Close()
            continue

        if mc_data_obs_5fs or mc_data_obs_4fs_mc_5fs:
            data_obs = None
            for process in mc_processes_for_data_obs:
                source_hist_name = process
                if process in tt_5fs_replacement_processes:
                    preferred = f"{process}_5FS" if mc_data_obs_5fs else f"{process}_4FS"
                    if isinstance(fIn.Get(preferred), ROOT.TH1):
                        source_hist_name = preferred
                    else:
                        print(f"WARNING: {preferred} not found in {outfile}. Falling back to {process}.")

                proc_hist = fIn.Get(source_hist_name)
                if not isinstance(proc_hist, ROOT.TH1):
                    continue

                if data_obs is None:
                    data_obs = proc_hist.Clone("data_obs")
                    data_obs.SetDirectory(0)
                else:
                    data_obs.Add(proc_hist)

            if data_obs is None:
                print(f"Error: no MC histograms found to build data_obs in '{outfile}'.")
                fIn.Close()
                continue
        else:
            singlee_hist = fIn.Get("singlee")
            singlemu_hist = fIn.Get("singlemu")
            if not isinstance(singlee_hist, ROOT.TH1) or not isinstance(singlemu_hist, ROOT.TH1):
                print(f"Error: 'singlee' or 'singlemu' in file '{outfile}' is not a histogram.")
                fIn.Close()
                continue
            data_obs = singlee_hist.Clone("data_obs")
            data_obs.SetDirectory(0)
            data_obs.Add(singlemu_hist)

        fIn.cd()
        data_obs.Write("data_obs", ROOT.TObject.kOverwrite)
        fIn.Delete("singlee;*")
        fIn.Delete("singlemu;*")
        fIn.Close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process ROOT TTrees into TH1D histograms (parallel-safe, fast rewrite).")
    parser.add_argument("--input_dirs", nargs='+', required=True, help="List of directories where the ROOT files are fetched.")
    parser.add_argument("--output_dir", type=str, required=True, help="Output directory of the new ROOT files.")
    parser.add_argument("--tree_name", type=str, required=True, help="List of TTree names in the input files.")
    parser.add_argument("--year", type=int, required=True, help="Data taking year.")
    parser.add_argument("--electron", nargs="?", const=1, type=bool, default=False, required=False, help="Process electron channel only.")
    parser.add_argument("--muon", nargs="?", const=1, type=bool, default=False, required=False, help="Process muon channel only.")
    parser.add_argument("--nproc", type=int, help="Number of worker processes. Defaults to min(number of jobs, available cores); jobs no longer share output files, so this now safely uses every core.")
    parser.add_argument("--threads_per_job", type=int, default=1, help="ROOT ImplicitMT threads per worker process. Keep nproc * threads_per_job <= available cores to avoid oversubscription. Default 1 (all parallelism comes from --nproc).")
    parser.add_argument("--tmp_dir", type=str, default=None, help="Directory for per-job temp ROOT files (default: a fresh temp dir next to --output_dir).")
    parser.add_argument("--keep_tmp", nargs="?", const=1, type=bool, default=False, required=False, help="Keep per-job temp files after merging (for debugging).")
    parser.add_argument("--extra_syst_dir", type=str, help="Directory containing extra shape systematics in per-systematic subfolders.")
    parser.add_argument("--extra_syst_only", nargs="?", const=1, type=bool, default=False, required=False,
                        help="Skip the main (file, category) processing phase entirely and only run "
                             "--extra_syst_dir against the output files from a previous run, then rebuild "
                             "data_obs. Use this to backfill extra systematics into existing output files "
                             "without recomputing everything else. --input_dirs is still required by the "
                             "parser but is ignored in this mode.")
    parser.add_argument("--use5FS", nargs="?", const=1, type=bool, default=False, required=False,
                        help="Take the ttbb/ttbj/tt2b sub-categories from ttbar-powheg (5FS), like every "
                             "other ttbar sub-category, instead of from the dedicated ttbb-4f (4FS) sample. "
                             "With this on the ttbb-4f file is not processed at all and powheg fills the "
                             "nominal ttbb/ttbj/tt2b templates directly, with full systematics. Inspired by "
                             "hdumper.py's --use5FS. Mutually exclusive with --mc_data_obs_5fs / "
                             "--mc_data_obs_4fs_mc_5fs.")
    parser.add_argument("--mc_data_obs_5fs", nargs="?", const=1, type=bool, default=False, required=False, help="Build data_obs from summed MC and use 5FS templates for ttbb/ttbj/tt2b when available.")
    parser.add_argument("--mc_data_obs_4fs_mc_5fs", nargs="?", const=1, type=bool, default=False, required=False, help="Build data_obs from summed MC using 4FS ttbb/ttbj/tt2b, while nominal MC templates for ttbb/ttbj/tt2b use 5FS.")
    parser.add_argument("--flavtag_sf_json", type=str, required=False, default=None,
                        help="Path to an alternate flavTaggingSF*.json.gz correctionlib file. If given, "
                             "the flavour-tagging weight and all of its systematic variations are recomputed "
                             "on the fly from this file instead of using the flavTagWeight* branches stored "
                             "in the ntuple.")
    parser.add_argument("--flavtag_sf_name", type=str, required=False, default=None,
                        help="Name of the correction inside --flavtag_sf_json (defaults to the standard "
                             "per-year name, e.g. particleNetAK4_shape or UParTAK4_pseudocontinuous).")

    args = parser.parse_args()

    prepended_ = "Vcb_"
    categories = ["catWcb", "catBB", "cat2B", "catBJ", "catCC", "cat2C", "catCJ", "catLF"]
    appended_ = ["_CR", "_SR"]

    input_files = []
    for input_dir in args.input_dirs:
        input_files += glob.glob(f"{input_dir}*.root")

    output_files = prepare_output(args.output_dir, args.year, categories, prepended_, appended_)
    print(f"Output files: {output_files}")

    selections = {"base": "n_ak4>=4 && n_btagM>=2 && n_ctagM>=1",
                  "ttbb": "genEventClassifier==9",
                  "ttbj": "genEventClassifier==7",
                  "tt2b": "genEventClassifier==8",
                  "ttcc": "genEventClassifier==6",
                  "ttcj": "genEventClassifier==4",
                  "tt2c": "genEventClassifier==5",
                  "ttLF": "tt_category==0"
                  }

    from configs.weights_and_constants import adhoc_selection, adhoc_binning
    adhoc_selection = adhoc_selection.copy()
    adhoc_binning = adhoc_binning.copy()

    if args.electron:
        selections["base"] += " && passTrigEl"
    if args.muon:
        selections["base"] += " && passTrigMu"

    if args.mc_data_obs_5fs and args.mc_data_obs_4fs_mc_5fs:
        raise ValueError("--mc_data_obs_5fs and --mc_data_obs_4fs_mc_5fs are mutually exclusive.")

    if args.use5FS and (args.mc_data_obs_5fs or args.mc_data_obs_4fs_mc_5fs):
        raise ValueError("--use5FS is mutually exclusive with --mc_data_obs_5fs / --mc_data_obs_4fs_mc_5fs.")

    if args.extra_syst_only:
        nprocs = args.nproc if args.nproc else mp.cpu_count()
        print(f"{Fore.CYAN}--extra_syst_only: skipping main-phase processing, only backfilling "
              f"--extra_syst_dir into the existing output files.{Style.RESET_ALL}")
    else:
        jobs_preview = build_jobs(input_files, selections, args.mc_data_obs_5fs, args.mc_data_obs_4fs_mc_5fs, args.use5FS)
        nprocs = args.nproc if args.nproc else min(len(jobs_preview), mp.cpu_count())

    own_tmp_dir = args.tmp_dir is None
    tmp_dir = args.tmp_dir or tempfile.mkdtemp(prefix="prepareHistosForCards_fast_", dir=args.output_dir if os.path.isdir(args.output_dir) else None)
    os.makedirs(tmp_dir, exist_ok=True)
    print(f"{Fore.CYAN}Using temp dir: {tmp_dir}{Style.RESET_ALL}")

    try:
        if not args.extra_syst_only:
            manifest = process_trees_parallel(
                input_files, output_files, args.tree_name, args.year, selections, adhoc_selection, adhoc_binning,
                tmp_dir, nprocs, args.mc_data_obs_5fs, args.mc_data_obs_4fs_mc_5fs,
                args.flavtag_sf_json, args.flavtag_sf_name, args.threads_per_job, args.use5FS,
            )

            print(f"{Fore.CYAN}Merging {len(manifest)} per-job temp files into {len(output_files)} output files...{Style.RESET_ALL}")
            merge_job_outputs(manifest, output_files, mode="UPDATE", cleanup=not args.keep_tmp)

        try:
            add_extra_systematic_histograms(
                args.extra_syst_dir, output_files, args.tree_name, args.year, selections,
                adhoc_selection, adhoc_binning, tmp_dir, nproc=nprocs,
                flavtag_sf_json=args.flavtag_sf_json, flavtag_sf_name=args.flavtag_sf_name,
                use5fs=args.use5FS,
            )
        except Exception as exc:
            # Per-file failures are already caught inside process_tree_extra_syst_job;
            # this is a last-resort net so a problem with the extra-syst phase itself
            # (e.g. a malformed directory) can't skip sum_data() for the main-phase
            # histograms, which are already merged into output_files at this point.
            print(f"{Fore.YELLOW}WARNING: extra-systematics phase failed, continuing without it: {exc}{Style.RESET_ALL}")
    finally:
        if own_tmp_dir and not args.keep_tmp:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    sum_data(output_files, args.mc_data_obs_5fs, args.mc_data_obs_4fs_mc_5fs)
    print(f"All done!")
