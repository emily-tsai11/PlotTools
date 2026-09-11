import ROOT
import argparse
import glob
import csv
import os
from colorama import Fore, Style
import multiprocessing as mp
from functools import partial
import flavTagWeightPlugin

ROOT.ROOT.EnableImplicitMT()
ROOT.gROOT.SetBatch(True)
ROOT.TTreeCache.SetLearnEntries(100)
ROOT.gEnv.SetValue("TFile.AsyncPrefetching", 1)

suffix_dict = {'base' : '', 'ttLF' : '_0', 'ttcj' : '_41', 'tt2c' : '_42', 'ttcc' : '_43', 'ttbj' : '_51', 'tt2b' : '_52', 'ttbb' : '_53'}
mc_processes_for_data_obs = ['tt-vcb', 'ttbb', 'ttbj', 'tt2b', 'ttcc', 'ttcj', 'tt2c', 'ttLF', 'singletop', 'wjets', 'ttZ', 'ttW', 'diboson', 'ttHbb', 'ttHcc']
tt_5fs_replacement_processes = ['ttbb', 'ttbj', 'tt2b']

JME_scaling_factors = {"ttWcb": 6.26, "ttLF": 4.88, "ttbb": 4.61, "tt2b": 5.02, "ttbj": 5.51, "ttcc": 4.43, "tt2c": 5.13, "ttcj": 5.50}

def process_tree(infile, output_files, tree_name, year, selections, adhoc_selection, adhoc_binning, perProcessSysts, mc_data_obs_5fs=False, mc_data_obs_4fs_mc_5fs=False, flavtag_sf_json=None, flavtag_sf_name=None):
    """
    Processes a TTree, converts it to multiple TH1Ds for specified branches, and saves them to ROOT files.

    Parameters:
    - input_file: Input ROOT file.
    - output_files: List of output ROOT files.
    - tree_name: Name of the TTree to process.
    - year: Data taking year.
    - selections: Dictionary containing event selections.
    - adhoc_selection: Dictionary containing an ad-hoc event selection to fill the scores.
    - adhoc_binning: Dictionary containing ad-hoc binning for the scores.
    - perProcessSysts: List of systematic shape variations that must be produced per process.
    - flavtag_sf_json: Optional path to an alternate flavTaggingSF*.json.gz file; if given,
      the flavour-tagging weight and all of its systematic variations are recomputed on the
      fly from this file instead of using the flavTagWeight* branches stored in the ntuple.
    - flavtag_sf_name: Optional correctionlib correction name inside flavtag_sf_json.
    """

    print(f"{Fore.RED}Processing file: {infile}{Style.RESET_ALL}")

    if "QCD_tree" in infile:
        return #Skip QCD multijet for now

    # Open input file
    input_file = ROOT.TFile.Open(infile)
    if not input_file or input_file.IsZombie():
        raise FileNotFoundError(f"Could not open file: {infile}")

    # Access the TTree
    tree = input_file.Get(tree_name)
    if not tree or not isinstance(tree, ROOT.TTree):
        raise ValueError(f"TTree '{tree_name}' not found in file '{infile}'.")
    
    # Optimize TTree reading
    tree.SetCacheSize(50000000)  # 50MB cache
    tree.AddBranchToCache("*", True)

    # Create RDataFrame from TTree
    df = ROOT.RDataFrame(tree)

    # Apply base selection everywhere (and early, to speed things up)
    base_filter = selections["base"]
    if "singlee" in infile:
        base_filter += " && passTrigMu==0" # Remove from the electron channel the events that fired the muon trigger. Could choose to do vice versa as well.
    df = df.Filter(base_filter)

    # Recompute the flavour-tagging weight (central value and every systematic variation
    # referenced by produce_systematics) on the fly from an alternate correctionlib SF file,
    # instead of relying on the flavTagWeight* branches already stored in the ntuple.
    # The flavour-tagging entries do not depend on the per-category suffix, so the set of
    # needed variations can be collected once from the suffix-less systematics dictionary.
    flavtag_prefix = flavTagWeightPlugin.STORED_WEIGHT_NAME
    if flavtag_sf_json and "data" not in infile and "Data" not in infile:
        df, flavtag_prefix = flavTagWeightPlugin.define_flavtag_weights(
            df, year, json_path=flavtag_sf_json, correction_name=flavtag_sf_name,
            systematics=flavTagWeightPlugin.extract_systematics(produce_systematics(year, '').values()))

    # Define the fractional scores
    df = df.Define("denominator", "score_ttbb + score_tt2b + score_ttbj + score_ttcc + score_tt2c + score_ttcj + score_ttLF") \
        .Define("fscore_ttbb", "score_ttbb / denominator") \
        .Define("fscore_tt2b", "score_tt2b / denominator") \
        .Define("fscore_ttbj", "score_ttbj / denominator") \
        .Define("fscore_ttcc", "score_ttcc / denominator") \
        .Define("fscore_tt2c", "score_tt2c / denominator") \
        .Define("fscore_ttcj", "score_ttcj / denominator") \
        .Define("fscore_ttLF", "score_ttLF / denominator")

    tt_file_names = ["ttbb-4f", "ttbar-powheg"]
    tt4f_strings = ["ttbb", "ttbj", "tt2b"]
    tt_strings   = ["ttcc", "ttcj", "tt2c", "ttLF"]

    histograms = {}
    # Process each selection-output combinations
    for selection_name in selections:

        # Apply the ttbar-specific selection to the right 4f and powheg samples
        if not "base" in selection_name and not any(x in infile for x in tt_file_names): 
            continue
        if any(x in infile for x in tt_file_names) and "base" in selection_name:
            continue
        if any(x in selection_name for x in tt4f_strings) and not "4f" in infile and not ((mc_data_obs_5fs or mc_data_obs_4fs_mc_5fs) and "powheg" in infile):
            continue
        if any(x in selection_name for x in tt_strings) and not "powheg" in infile:
            continue

        is_5fs_proxy_selection = mc_data_obs_5fs and "powheg" in infile and any(x in selection_name for x in tt4f_strings)
        is_4fs_proxy_selection = mc_data_obs_4fs_mc_5fs and "4f" in infile and "-dps" not in infile and any(x in selection_name for x in tt4f_strings)
        is_5fs_nominal_selection = mc_data_obs_4fs_mc_5fs and "powheg" in infile and any(x in selection_name for x in tt4f_strings)

        suffix = suffix_dict.get(selection_name, '')

        # Add event selection for ttbar samples
        print(f"Events after base selection: {df.Count().GetValue()}")
        if not "base" in selection_name:
            print(f"Applying additional selection for {infile}: {selection_name}")
            ttbar_event_selection = f"{selections[selection_name]}"
            df_selected = df.Filter(ttbar_event_selection)

            # Check the number of events after ttbar selection
            print(f"Events passing additional ttbar selection: {df_selected.Count().GetValue()}")
        else:
            df_selected = df

        # Fetch dictionary of systematics and assign event weight based on data taking year and process type
        systematics = produce_systematics(year, suffix)

        # Point the flavour-tagging terms at the recomputed columns, if we are using an
        # alternate SF file (no-op when flavtag_prefix is the stored branch name).
        systematics = {name: flavTagWeightPlugin.remap_expression(expr, flavtag_prefix)
                       for name, expr in systematics.items()}

        for syst in systematics.keys():
            # For the optional MC-based data_obs, produce only nominal 5FS proxy templates.
            if is_5fs_proxy_selection and syst != "None":
                continue
            # For the opposite mode, produce only nominal 4FS proxy templates for data_obs.
            if is_4fs_proxy_selection and syst != "None":
                continue

            # Keep only the explicitly process-dependent nuisances for tt-like samples.
            # startswith serves to avoid catching unrelated names like CMS_flavTag_LHE_muF_*.
            perProcessSystsWithoutLHEmuRmuF = [procDepSyst for procDepSyst in perProcessSysts if not (procDepSyst.startswith("LHE_muR") or procDepSyst.startswith("LHE_muF") or procDepSyst.startswith("minorBkg_PS_"))]
            if any(syst.startswith(procDepSyst) for procDepSyst in perProcessSystsWithoutLHEmuRmuF) and "tt" not in infile:
                continue # Skip certain systematics if the process is not a ttbar one (including signal, ttH, and ttV)
            if syst.startswith("minorBkg") and "tt" in infile:
                continue # Minor background systematics do not pertain to ttbar processes

            if syst == "None":
                weight = assign_event_weight(year, infile, suffix, flavtag_weight_branch=flavtag_prefix)
            else:
                weight = assign_event_weight(year, infile, suffix, systematics[syst], flavtag_weight_branch=flavtag_prefix)

            # If weight is a complex expression, define it as a new column
            weight_column = f"weight_{selection_name}_{syst}"
            if "data" not in infile and "Data" not in infile:
                df_selected = df_selected.Define(weight_column, weight)
            else: 
                df_selected = df_selected.Define(weight_column, "1") # Apply jet veto map for data as well

            final_df = dict()
            for (score, adhoc_sel), outfile in zip(adhoc_selection.items(), output_files):

                hist_name = infile.split('/')[-1].replace('_tree.root','')
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
                    #Keep the process name in the systematic name for process-dependent systematics
                    if any(procDepSyst in syst for procDepSyst in perProcessSysts):
                        process_flag = hist_name.split('_')[0] # Assuming the process name is the first part of the histogram name
                        new_syst_name = syst.replace(f"_{year}", f"_{process_flag}_{year}") if "bFrag" not in syst else syst
                        hist_name = f"{hist_name}_{new_syst_name}"
                    else:
                        hist_name = f"{hist_name}_{syst}"

                final_df[score] = df_selected.Filter(adhoc_sel)

                #JME stuff
                #JME_weight_column = f"JME_weight_{weight_column}"
                #if "data" in infile or "Data" in infile:
                #    JME_weight_column = weight_column
                #elif "data" not in infile and "Data" not in infile and "Wcb" in outfile:    
                #    final_df[score] = final_df[score].Define(JME_weight_column, f"{weight}*6.26")
                #elif "data" not in infile and "Data" not in infile and "LF" in outfile:
                #    final_df[score] = final_df[score].Define(JME_weight_column, f"{weight}*4.88")
                #elif "data" not in infile and "Data" not in infile and "BB" in outfile:
                #    final_df[score] = final_df[score].Define(JME_weight_column, f"{weight}*4.61")
                #elif "data" not in infile and "Data" not in infile and "2B" in outfile:
                #    final_df[score] = final_df[score].Define(JME_weight_column, f"{weight}*5.02")
                #elif "data" not in infile and "Data" not in infile and "BJ" in outfile:
                #    final_df[score] = final_df[score].Define(JME_weight_column, f"{weight}*5.51")
                #elif "data" not in infile and "Data" not in infile and "CC" in outfile:
                #    final_df[score] = final_df[score].Define(JME_weight_column, f"{weight}*4.43")
                #elif "data" not in infile and "Data" not in infile and "2C" in outfile:
                #    final_df[score] = final_df[score].Define(JME_weight_column, f"{weight}*5.13")
                #elif "data" not in infile and "Data" not in infile and "CJ" in outfile:
                #    final_df[score] = final_df[score].Define(JME_weight_column, f"{weight}*5.50")

                hist_key = (selection_name, outfile, hist_name, score)
                histograms[hist_key] = final_df[score].Histo1D(
                    (hist_name, f"Histogram of {score} for process {hist_name}", 
                     len(adhoc_binning[score])-1, adhoc_binning[score]), 
                    score, weight_column
                )

            if "Data" in infile or "data" in infile: break # Do not continue with the systematic variations for collision data

    # Write all histograms to their respective output files
    print(f"Materializing {len(histograms)} histograms...")
    materialized_hists = {}
    for key, hist_lazy in histograms.items():
        materialized_hists[key] = hist_lazy.GetPtr()   

    output_file_handles = {}
    for key, hist in materialized_hists.items():
        selection_name, outfile, hist_name, score = key
        
        if outfile not in output_file_handles:
            output_file_handles[outfile] = ROOT.TFile(outfile, "UPDATE")
        
        output_file_handles[outfile].cd()
        hist.Write()
    
    # Close all files
    for f in output_file_handles.values():
        f.Close()
    
    input_file.Close()
    print(f"{Fore.GREEN}Completed processing {infile}{Style.RESET_ALL}")



def process_trees_parallel(input_files, output_files, tree_name, year, selections, adhoc_selection, adhoc_binning, perProcessSysts, nproc=1, mc_data_obs_5fs=False, mc_data_obs_4fs_mc_5fs=False, flavtag_sf_json=None, flavtag_sf_name=None):

    process_func = partial(
        process_tree,
        output_files=output_files,
        tree_name=tree_name,
        year=year,
        selections=selections,
        adhoc_selection=adhoc_selection,
        adhoc_binning=adhoc_binning,
        perProcessSysts=perProcessSysts,
        mc_data_obs_5fs=mc_data_obs_5fs,
        mc_data_obs_4fs_mc_5fs=mc_data_obs_4fs_mc_5fs,
        flavtag_sf_json=flavtag_sf_json,
        flavtag_sf_name=flavtag_sf_name
    )

    # ROOT files are not safe for concurrent UPDATE writes from multiple processes.
    # Keep serial execution by default unless explicitly requested.
    max_procs = min(len(input_files), mp.cpu_count())
    use_procs = min(max(1, int(nproc)), max_procs)
    if use_procs == 1:
        for infile in input_files:
            process_func(infile)
    else:
        with mp.Pool(processes=use_procs) as pool:
            pool.map(process_func, input_files)


def process_tree_extra_syst(infile, output_files, tree_name, year, selections, adhoc_selection, adhoc_binning, extra_syst_name):
    """
    Process one tree file corresponding to an externally-produced shape variation
    and write histograms with suffix `extra_syst_name` into existing output files.
    """
    print(f"{Fore.CYAN}Processing external systematic file: {infile} ({extra_syst_name}){Style.RESET_ALL}")

    if "QCD_tree" in infile:
        return

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

    df = df.Define("denominator", "score_ttbb + score_tt2b + score_ttbj + score_ttcc + score_tt2c + score_ttcj + score_ttLF") \
        .Define("fscore_ttbb", "score_ttbb / denominator") \
        .Define("fscore_tt2b", "score_tt2b / denominator") \
        .Define("fscore_ttbj", "score_ttbj / denominator") \
        .Define("fscore_ttcc", "score_ttcc / denominator") \
        .Define("fscore_tt2c", "score_tt2c / denominator") \
        .Define("fscore_ttcj", "score_ttcj / denominator") \
        .Define("fscore_ttLF", "score_ttLF / denominator")

    tt_file_names = ["ttbb-4f", "ttbar-powheg"]
    tt4f_strings = ["ttbb", "ttbj", "tt2b"]
    tt_strings = ["ttcc", "ttcj", "tt2c", "ttLF"]

    #flavTag_renormalization = {"base": "*1",
    #                       "ttbb": "*0.9393",
    #                       "tt2b": "*1.0024",
    #                       "ttbj": "*0.9541",
    #                       "ttcc": "*0.9908",
    #                       "tt2c": "*0.9388",
    #                       "ttcj": "*1.0094",
    #                       "ttLF": "*0.9974"
    #                       }

    histograms = {}
    for selection_name in selections:
        if not "base" in selection_name and not any(x in infile for x in tt_file_names):
            continue
        if any(x in infile for x in tt_file_names) and "base" in selection_name:
            continue
        if any(x in selection_name for x in tt4f_strings) and not "4f" in infile:
            continue
        if any(x in selection_name for x in tt_strings) and not "powheg" in infile:
            continue

        suffix = suffix_dict.get(selection_name, '')

        if not "base" in selection_name:
            ttbar_event_selection = f"{selections[selection_name]}"
            df_selected = df.Filter(ttbar_event_selection)
        else:
            df_selected = df

        # Keep same weight convention as nominal histogram production.
        weight = assign_event_weight(year, infile, suffix)
        weight_column = f"weight_{selection_name}_{extra_syst_name}"

        #if not "data" in infile and not "Data" in infile:
        #    weight = weight + flavTag_renormalization[selection_name] #FIXME
        #    print(f"weight is {weight}")

        if "data" not in infile and "Data" not in infile:
            df_selected = df_selected.Define(weight_column, weight)
        else:
            df_selected = df_selected.Define(weight_column, "1")

        final_df = {}
        for (score, adhoc_sel), outfile in zip(adhoc_selection.items(), output_files):
            hist_name = infile.split('/')[-1].replace('_tree.root', '')
            if any(x in infile for x in tt_file_names) and "-dps" not in infile:
                hist_name = selection_name
            elif any(x in infile for x in tt_file_names) and "-dps" in infile:
                hist_name = selection_name + "-dps"

            hist_name = f"{hist_name}_{extra_syst_name}"
            final_df[score] = df_selected.Filter(adhoc_sel)

            #JME stuff
            #JME_weight_column = f"JME_weight_{weight_column}"
            #if "data" in infile or "Data" in infile:
            #    JME_weight_column = weight_column
            #elif "data" not in infile and "Data" not in infile and "Wcb" in outfile:    
            #    final_df[score] = final_df[score].Define(JME_weight_column, f"{weight}*6.26")
            #elif "data" not in infile and "Data" not in infile and "LF" in outfile:
            #    final_df[score] = final_df[score].Define(JME_weight_column, f"{weight}*4.88")
            #elif "data" not in infile and "Data" not in infile and "BB" in outfile:
            #    final_df[score] = final_df[score].Define(JME_weight_column, f"{weight}*4.61")
            #elif "data" not in infile and "Data" not in infile and "2B" in outfile:
            #    final_df[score] = final_df[score].Define(JME_weight_column, f"{weight}*5.02")
            #elif "data" not in infile and "Data" not in infile and "BJ" in outfile:
            #    final_df[score] = final_df[score].Define(JME_weight_column, f"{weight}*5.51")
            #elif "data" not in infile and "Data" not in infile and "CC" in outfile:
            #    final_df[score] = final_df[score].Define(JME_weight_column, f"{weight}*4.43")
            #elif "data" not in infile and "Data" not in infile and "2C" in outfile:
            #    final_df[score] = final_df[score].Define(JME_weight_column, f"{weight}*5.13")
            #elif "data" not in infile and "Data" not in infile and "CJ" in outfile:
            #    final_df[score] = final_df[score].Define(JME_weight_column, f"{weight}*5.50")

            hist_key = (selection_name, outfile, hist_name, score)
            histograms[hist_key] = final_df[score].Histo1D(
                (hist_name, f"Histogram of {score} for process {hist_name}",
                 len(adhoc_binning[score]) - 1, adhoc_binning[score]),
                score, weight_column
            )

    materialized_hists = {key: hist_lazy.GetPtr() for key, hist_lazy in histograms.items()}

    output_file_handles = {}
    for key, hist in materialized_hists.items():
        _, outfile, _, _ = key
        if outfile not in output_file_handles:
            output_file_handles[outfile] = ROOT.TFile(outfile, "UPDATE")

        output_file_handles[outfile].cd()
        hist.Write(hist.GetName(), ROOT.TObject.kOverwrite)

    for f in output_file_handles.values():
        f.Close()

    input_file.Close()


def add_extra_systematic_histograms(extra_syst_dir, output_files, tree_name, year, selections, adhoc_selection, adhoc_binning):
    """
    Add extra systematic-shape histograms from an external production directory.
    Directory layout is expected to be:
      extra_syst_dir/<syst_dir_name>/*.root
    The histogram suffix is the same as <syst_dir_name>.
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

    for syst_dir in syst_dirs:
        syst_dir_name = os.path.basename(syst_dir.rstrip("/"))

        # Keep only explicit up/down shape variations; skip helper folders.
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
            process_tree_extra_syst(
                infile,
                output_files,
                tree_name,
                year,
                selections,
                adhoc_selection,
                adhoc_binning,
                combine_syst_name,
            )



def read_csv(csv_file):
    """
    Open and read a csv file containing the name and the range of the variables to be histogrammed. 
    Fill in a list of dictionaries containing branch (i.e., variable name), nbins, xmin, and xmax information.

    Parameters:
    - csv_file: The csv file containing variable names and binning for the respective histograms.
    """
    with open(csv_file, mode='r') as f:
        csv_reader = csv.reader(f) 
        dict_list = [
            {'branch': line[0], 'nbins': line[1], 'xmin': line[2], 'xmax': line[3]}
            for line in csv_reader if not line[0] == 'Variable'
        ]

    return dict_list


def prepare_output(output_dir, year, categories, prepend, append):
    """
    Prepare the output files that will contain the histograms used to create combine datacards.

    Parameters:
    - output_dir: Output directory for the new ROOT files.
    - categories: The name of the categories.
    - prepend: String to prepend to the file name.
    - append: String to append to the file name.
    """
    os.makedirs(output_dir + str(year), exist_ok=True)

    name_list = [prepend + cat for cat in categories]
    name_list = [name + append[1] if 'Wcb' in name else name + append[0] for name in name_list]

    return [
        f"{output_dir}{year}/{name}.root"
        for name in name_list
    ]



def assign_event_weight(year, infile, suffix, syst="", flavtag_weight_branch="flavTagWeight"):
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
    """
    weight = "1"
    if year == 2024 or year == 2025:
        weight = f"lumiwgt*genWeight*xsecWeight*puWeight*muEffWeight*elEffWeight*{flavtag_weight_branch}*(((abs(lep1_pdgId)==11 && passTrigEl) || (abs(lep1_pdgId)==13 && passTrigMu)) && passmetfilters)"
    if "ttbar" in infile or "4f" in infile or "tt-vcb" in infile:
        weight = f"{weight}*TopPtWeight[1]*TopPtWeightNorm{suffix}[1]*TOPMLWeight[5]*TOPMLWeightNorm{suffix}[5]" #TOPMLWeight[5] is b-fragmentation nominal
    
    if not syst == "":
        weight = f"{weight}*{syst}"
    
    return weight

def sum_data(output_files, mc_data_obs_5fs=False, mc_data_obs_4fs_mc_5fs=False):
    for outfile in output_files:
        fIn = ROOT.TFile.Open(outfile, "UPDATE")
        if not fIn or fIn.IsZombie():
            print(f"Error opening output file: {outfile}")
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
        #delete the singlee and singlemu histograms to save space
        fIn.Delete("singlee;*")
        fIn.Delete("singlemu;*")
        fIn.Close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process ROOT TTrees into TH1D histograms.")
    parser.add_argument("--input_dirs", nargs='+', required=True, help="List of directories where the ROOT files are fetched.")
    parser.add_argument("--output_dir", type=str, required=True, help="Output directory of the new ROOT files.")
    parser.add_argument("--tree_name", type=str, required=True, help="List of TTree names in the input files.")
    parser.add_argument("--year", type=int, required=True, help="Data taking year.")
    parser.add_argument("--electron", nargs="?", const=1, type=bool, default=False, required=False, help="Process electron channel only.")
    parser.add_argument("--muon", nargs="?", const=1, type=bool, default=False, required=False, help="Process muon channel only.")
    parser.add_argument("--nproc", type=int, help="Number of worker processes. Use 1 to avoid concurrent ROOT file writes.")
    parser.add_argument("--extra_syst_dir", type=str,help="Directory containing extra shape systematics in per-systematic subfolders.")
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

    # Categories for combine datacards
    prepended_ = "Vcb_"
    categories = ["catWcb", "catBB", "cat2B", "catBJ", "catCC", "cat2C", "catCJ", "catLF"]
    appended_ = ["_CR", "_SR"]

    # Get input files from the input_dirs list
    input_files = []
    for input_dir in args.input_dirs:
        input_files += glob.glob(f"{input_dir}*.root")

    # Prepare list of output files based on the name of the input files
    output_files = prepare_output(args.output_dir, args.year, categories, prepended_, appended_)
    print(f"Output files: {output_files}")

    # Define event selections. Some are process-specific.
    selections = {#"base": "n_ak4>=4 && (n_btagM+n_ctagM)>=3 && n_btagM>=1",
                 "base": "n_ak4>=4 && n_btagM>=2 && n_ctagM>=1",
                 "ttbb" : "genEventClassifier==9",
                 "ttbj" : "genEventClassifier==7",
                 "tt2b" : "genEventClassifier==8",
                 "ttcc" : "genEventClassifier==6",
                 "ttcj" : "genEventClassifier==4",
                 "tt2c" : "genEventClassifier==5",
                 "ttLF" : "tt_category==0"
    }

    from configs.weights_and_constants import adhoc_selection, adhoc_binning
    adhoc_selection = adhoc_selection.copy()
    adhoc_binning = adhoc_binning.copy()
    
    # Apply trigger selection to separate channels if requested
    if args.electron:
        selections["base"] += " && passTrigEl"
    if args.muon:
        selections["base"] += " && passTrigMu"

    #year = args.year
    # Define list of systematic variations to include

    def produce_systematics(year, suffix):

        systematics = {"None" : "", 
                   #Pileup and lepton efficiencies
                   "CMS_pileup_%sUp"   % year  : "puWeightUp/puWeight", 
                   "CMS_pileup_%sDown" % year  : "puWeightDown/puWeight",
                   "CMS_trigEffUp"   : "trigEffWeightUp/trigEffWeight",
                   "CMS_trigEffDown" : "trigEffWeightDown/trigEffWeight",
                   "CMS_muEffUp"     : "muEffWeight_UP/muEffWeight",
                   "CMS_muEffDown"   : "muEffWeight_DOWN/muEffWeight",
                   "CMS_elEffUp"     : "elEffWeight_UP/elEffWeight",
                   "CMS_elEffDown"   : "elEffWeight_DOWN/elEffWeight",
                   "CMS_elSmearUp"   : "elSmear_UP",
                   "CMS_elSmearDown" : "elSmear_DOWN",
                   "CMS_elScaleUp"   : "elScale_UP",
                   "CMS_elScaleDown" : "elScale_DOWN",
                   "CMS_muSmearUp"   : "muSmear_UP",
                   "CMS_muSmearDown" : "muSmear_DOWN",
                   "CMS_muScaleUp"   : "muScale_UP",
                   "CMS_muScaleDown" : "muScale_DOWN",
                   # Flavor tagging
                   "CMS_flavTag_TTWeight_ttbarUp"     : "flavTagWeight_TTWeight_ttbar_UP/flavTagWeight",
                   "CMS_flavTag_TTWeight_ttbarDown"   : "flavTagWeight_TTWeight_ttbar_DOWN/flavTagWeight",
                   "CMS_flavTag_HDamp_ttbarUp"        : "flavTagWeight_HDamp_ttbar_UP/flavTagWeight",
                   "CMS_flavTag_HDamp_ttbarDown"      : "flavTagWeight_HDamp_ttbar_DOWN/flavTagWeight",
                   "CMS_flavTag_BDecay_ttbarUp"       : "flavTagWeight_BDecay_ttbar_UP/flavTagWeight",
                   "CMS_flavTag_BDecay_ttbarDown"     : "flavTagWeight_BDecay_ttbar_DOWN/flavTagWeight",
                   "CMS_flavTag_CDecay_ttbarUp"       : "flavTagWeight_CDecay_ttbar_UP/flavTagWeight",
                   "CMS_flavTag_CDecay_ttbarDown"     : "flavTagWeight_CDecay_ttbar_DOWN/flavTagWeight",
                   "CMS_flavTag_xsec_ttbarUp"         : "flavTagWeight_XSec_ttbar_UP/flavTagWeight",
                   "CMS_flavTag_xsec_ttbarDown"       : "flavTagWeight_XSec_ttbar_DOWN/flavTagWeight",
                   "CMS_flavTag_xsec_wjets_cUp"       : "flavTagWeight_XSec_WJets_c_UP/flavTagWeight",
                   "CMS_flavTag_xsec_wjets_cDown"     : "flavTagWeight_XSec_WJets_c_DOWN/flavTagWeight",
                   "CMS_flavTag_xsec_wjets_bUp"       : "flavTagWeight_XSec_WJets_b_UP/flavTagWeight",
                   "CMS_flavTag_xsec_wjets_bDown"     : "flavTagWeight_XSec_WJets_b_DOWN/flavTagWeight",
                   "CMS_flavTag_xsec_zjets_cUp"       : "flavTagWeight_XSec_ZJets_c_UP/flavTagWeight",
                   "CMS_flavTag_xsec_zjets_cDown"     : "flavTagWeight_XSec_ZJets_c_DOWN/flavTagWeight",
                   "CMS_flavTag_xsec_zjets_bUp"       : "flavTagWeight_XSec_ZJets_b_UP/flavTagWeight",
                   "CMS_flavTag_xsec_zjets_bDown"     : "flavTagWeight_XSec_ZJets_b_DOWN/flavTagWeight",
                   "CMS_flavTag_xsec_singlet_tChUp"   : "flavTagWeight_XSec_singlet_tCh_UP/flavTagWeight",
                   "CMS_flavTag_xsec_singlet_tChDown" : "flavTagWeight_XSec_singlet_tCh_DOWN/flavTagWeight",
                   "CMS_flavTag_xsec_singlet_tWUp"    : "flavTagWeight_XSec_singlet_tW_UP/flavTagWeight",
                   "CMS_flavTag_xsec_singlet_tWDown"  : "flavTagWeight_XSec_singlet_tW_DOWN/flavTagWeight",
                   "CMS_flavTag_xsec_VVUp"            : "flavTagWeight_XSec_VV_UP/flavTagWeight",
                   "CMS_flavTag_xsec_VVDown"          : "flavTagWeight_XSec_VV_DOWN/flavTagWeight",
                   "CMS_flavTag_PU_%sUp"     % year   : "flavTagWeight_PUWeight_UP/flavTagWeight",
                   "CMS_flavTag_PU_%sDown"   % year   : "flavTagWeight_PUWeight_DOWN/flavTagWeight",
                   "CMS_flavTag_Lumi_%sUp"   % year   : "flavTagWeight_Lumi_13p6TeV_%s_UP/flavTagWeight" % year,
                   "CMS_flavTag_Lumi_%sDown" % year   : "flavTagWeight_Lumi_13p6TeV_%s_DOWN/flavTagWeight" % year,
                   "CMS_flavTag_EleRecoUp"            : "flavTagWeight_Ele_Reco_UP/flavTagWeight",
                   "CMS_flavTag_EleRecoDown"          : "flavTagWeight_Ele_Reco_DOWN/flavTagWeight",
                   "CMS_flavTag_EleScaleUp"           : "flavTagWeight_Ele_Scale_UP/flavTagWeight",
                   "CMS_flavTag_EleScaleDown"         : "flavTagWeight_Ele_Scale_DOWN/flavTagWeight",
                   "CMS_flavTag_EleSmearUp"           : "flavTagWeight_Ele_Smear_UP/flavTagWeight",
                   "CMS_flavTag_EleSmearDown"         : "flavTagWeight_Ele_Smear_DOWN/flavTagWeight",
                   "CMS_flavTag_EleIDUp"              : "flavTagWeight_Ele_ID_UP/flavTagWeight",
                   "CMS_flavTag_EleIDDown"            : "flavTagWeight_Ele_ID_DOWN/flavTagWeight",
                   "CMS_flavTag_EleTriggerUp"         : "flavTagWeight_Ele_Trigger_UP/flavTagWeight",
                   "CMS_flavTag_EleTriggerDown"       : "flavTagWeight_Ele_Trigger_DOWN/flavTagWeight",
                   "CMS_flavTag_MuIDUp"               : "flavTagWeight_Mu_ID_UP/flavTagWeight",
                   "CMS_flavTag_MuIDDown"             : "flavTagWeight_Mu_ID_DOWN/flavTagWeight",
                   "CMS_flavTag_MuIsoUp"              : "flavTagWeight_Mu_Iso_UP/flavTagWeight",
                   "CMS_flavTag_MuIsoDown"            : "flavTagWeight_Mu_Iso_DOWN/flavTagWeight",
                   "CMS_flavTag_MuScaleUp"            : "flavTagWeight_Mu_Scale_UP/flavTagWeight",
                   "CMS_flavTag_MuScaleDown"          : "flavTagWeight_Mu_Scale_DOWN/flavTagWeight",
                   "CMS_flavTag_MuResolUp"            : "flavTagWeight_Mu_Resol_UP/flavTagWeight",
                   "CMS_flavTag_MuResolDown"          : "flavTagWeight_Mu_Resol_DOWN/flavTagWeight",
                   "CMS_flavTag_MuTriggerUp"          : "flavTagWeight_Mu_Trigger_UP/flavTagWeight",
                   "CMS_flavTag_MuTriggerDown"        : "flavTagWeight_Mu_Trigger_DOWN/flavTagWeight",
                   "CMS_flavTag_MET_UnclEnergyUp"     : "flavTagWeight_MET_UnclEnergy_UP/flavTagWeight",
                   "CMS_flavTag_MET_UnclEnergyDown"   : "flavTagWeight_MET_UnclEnergy_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavB_C0_%sUp"   % year : "flavTagWeight_Stat_flavB_C0_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavB_C0_%sDown" % year : "flavTagWeight_Stat_flavB_C0_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavB_C1_%sUp"   % year : "flavTagWeight_Stat_flavB_C1_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavB_C1_%sDown" % year : "flavTagWeight_Stat_flavB_C1_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavB_C2_%sUp"   % year : "flavTagWeight_Stat_flavB_C2_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavB_C2_%sDown" % year : "flavTagWeight_Stat_flavB_C2_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavB_C3_%sUp"   % year : "flavTagWeight_Stat_flavB_C3_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavB_C3_%sDown" % year : "flavTagWeight_Stat_flavB_C3_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavB_C4_%sUp"   % year : "flavTagWeight_Stat_flavB_C4_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavB_C4_%sDown" % year : "flavTagWeight_Stat_flavB_C4_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavB_B0_%sUp"   % year : "flavTagWeight_Stat_flavB_B0_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavB_B0_%sDown" % year : "flavTagWeight_Stat_flavB_B0_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavB_B1_%sUp"   % year : "flavTagWeight_Stat_flavB_B1_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavB_B1_%sDown" % year : "flavTagWeight_Stat_flavB_B1_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavB_B2_%sUp"   % year : "flavTagWeight_Stat_flavB_B2_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavB_B2_%sDown" % year : "flavTagWeight_Stat_flavB_B2_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavB_B3_%sUp"   % year : "flavTagWeight_Stat_flavB_B3_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavB_B3_%sDown" % year : "flavTagWeight_Stat_flavB_B3_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavB_B4_%sUp"   % year : "flavTagWeight_Stat_flavB_B4_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavB_B4_%sDown" % year : "flavTagWeight_Stat_flavB_B4_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavC_C0_%sUp"   % year : "flavTagWeight_Stat_flavC_C0_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavC_C0_%sDown" % year : "flavTagWeight_Stat_flavC_C0_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavC_C1_%sUp"   % year : "flavTagWeight_Stat_flavC_C1_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavC_C1_%sDown" % year : "flavTagWeight_Stat_flavC_C1_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavC_C2_%sUp"   % year : "flavTagWeight_Stat_flavC_C2_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavC_C2_%sDown" % year : "flavTagWeight_Stat_flavC_C2_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavC_C3_%sUp"   % year : "flavTagWeight_Stat_flavC_C3_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavC_C3_%sDown" % year : "flavTagWeight_Stat_flavC_C3_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavC_C4_%sUp"   % year : "flavTagWeight_Stat_flavC_C4_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavC_C4_%sDown" % year : "flavTagWeight_Stat_flavC_C4_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavC_B0_%sUp"   % year : "flavTagWeight_Stat_flavC_B0_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavC_B0_%sDown" % year : "flavTagWeight_Stat_flavC_B0_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavC_B1_%sUp"   % year : "flavTagWeight_Stat_flavC_B1_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavC_B1_%sDown" % year : "flavTagWeight_Stat_flavC_B1_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavC_B2_%sUp"   % year : "flavTagWeight_Stat_flavC_B2_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavC_B2_%sDown" % year : "flavTagWeight_Stat_flavC_B2_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavC_B3_%sUp"   % year : "flavTagWeight_Stat_flavC_B3_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavC_B3_%sDown" % year : "flavTagWeight_Stat_flavC_B3_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavC_B4_%sUp"   % year : "flavTagWeight_Stat_flavC_B4_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavC_B4_%sDown" % year : "flavTagWeight_Stat_flavC_B4_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavL_C0_%sUp"   % year : "flavTagWeight_Stat_flavL_C0_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavL_C0_%sDown" % year : "flavTagWeight_Stat_flavL_C0_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavL_C1_%sUp"   % year : "flavTagWeight_Stat_flavL_C1_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavL_C1_%sDown" % year : "flavTagWeight_Stat_flavL_C1_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavL_C2_%sUp"   % year : "flavTagWeight_Stat_flavL_C2_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavL_C2_%sDown" % year : "flavTagWeight_Stat_flavL_C2_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavL_C3_%sUp"   % year : "flavTagWeight_Stat_flavL_C3_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavL_C3_%sDown" % year : "flavTagWeight_Stat_flavL_C3_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavL_C4_%sUp"   % year : "flavTagWeight_Stat_flavL_C4_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavL_C4_%sDown" % year : "flavTagWeight_Stat_flavL_C4_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavL_B0_%sUp"   % year : "flavTagWeight_Stat_flavL_B0_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavL_B0_%sDown" % year : "flavTagWeight_Stat_flavL_B0_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavL_B1_%sUp"   % year : "flavTagWeight_Stat_flavL_B1_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavL_B1_%sDown" % year : "flavTagWeight_Stat_flavL_B1_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavL_B2_%sUp"   % year : "flavTagWeight_Stat_flavL_B2_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavL_B2_%sDown" % year : "flavTagWeight_Stat_flavL_B2_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavL_B3_%sUp"   % year : "flavTagWeight_Stat_flavL_B3_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavL_B3_%sDown" % year : "flavTagWeight_Stat_flavL_B3_DOWN/flavTagWeight",
                   "CMS_flavTag_Stat_flavL_B4_%sUp"   % year : "flavTagWeight_Stat_flavL_B4_UP/flavTagWeight",
                   "CMS_flavTag_Stat_flavL_B4_%sDown" % year : "flavTagWeight_Stat_flavL_B4_DOWN/flavTagWeight",
                   "CMS_flavTag_LHE_muF_ttbarUp"     : "flavTagWeight_LHEScaleWeight_muF_ttbar_UP/flavTagWeight",
                   "CMS_flavTag_LHE_muF_ttbarDown"   : "flavTagWeight_LHEScaleWeight_muF_ttbar_DOWN/flavTagWeight",
                   "CMS_flavTag_LHE_muR_ttbarUp"     : "flavTagWeight_LHEScaleWeight_muR_ttbar_UP/flavTagWeight",
                   "CMS_flavTag_LHE_muR_ttbarDown"   : "flavTagWeight_LHEScaleWeight_muR_ttbar_DOWN/flavTagWeight",
                   "CMS_flavTag_LHE_muF_singletUp"   : "flavTagWeight_LHEScaleWeight_muF_singlet_UP/flavTagWeight",
                   "CMS_flavTag_LHE_muF_singletDown" : "flavTagWeight_LHEScaleWeight_muF_singlet_DOWN/flavTagWeight",
                   "CMS_flavTag_LHE_muR_singletUp"   : "flavTagWeight_LHEScaleWeight_muR_singlet_UP/flavTagWeight",
                   "CMS_flavTag_LHE_muR_singletDown" : "flavTagWeight_LHEScaleWeight_muR_singlet_DOWN/flavTagWeight",
                   "CMS_flavTag_LHE_muF_wjetsUp"     : "flavTagWeight_LHEScaleWeight_muF_wjets_UP/flavTagWeight",
                   "CMS_flavTag_LHE_muF_wjetsDown"   : "flavTagWeight_LHEScaleWeight_muF_wjets_DOWN/flavTagWeight",
                   "CMS_flavTag_LHE_muR_wjetsUp"     : "flavTagWeight_LHEScaleWeight_muR_wjets_UP/flavTagWeight",
                   "CMS_flavTag_LHE_muR_wjetsDown"   : "flavTagWeight_LHEScaleWeight_muR_wjets_DOWN/flavTagWeight",
                   "CMS_flavTag_LHE_muF_zjetsUp"     : "flavTagWeight_LHEScaleWeight_muF_zjets_UP/flavTagWeight",
                   "CMS_flavTag_LHE_muF_zjetsDown"   : "flavTagWeight_LHEScaleWeight_muF_zjets_DOWN/flavTagWeight",
                   "CMS_flavTag_LHE_muR_zjetsUp"     : "flavTagWeight_LHEScaleWeight_muR_zjets_UP/flavTagWeight",
                   "CMS_flavTag_LHE_muR_zjetsDown"   : "flavTagWeight_LHEScaleWeight_muR_zjets_DOWN/flavTagWeight",
                   "CMS_flavTag_LHE_muF_dibosonUp"   : "flavTagWeight_LHEScaleWeight_muF_diboson_UP/flavTagWeight",
                   "CMS_flavTag_LHE_muF_dibosonDown" : "flavTagWeight_LHEScaleWeight_muF_diboson_DOWN/flavTagWeight",
                   "CMS_flavTag_LHE_muR_dibosonUp"   : "flavTagWeight_LHEScaleWeight_muR_diboson_UP/flavTagWeight",
                   "CMS_flavTag_LHE_muR_dibosonDown" : "flavTagWeight_LHEScaleWeight_muR_diboson_DOWN/flavTagWeight",
                   "CMS_flavTag_LHE_PDF_ttbarUp"     : "flavTagWeight_LHEScaleWeight_PDF_ttbar_UP/flavTagWeight",
                   "CMS_flavTag_LHE_PDF_ttbarDown"   : "flavTagWeight_LHEScaleWeight_PDF_ttbar_DOWN/flavTagWeight",
                   "CMS_flavTag_LHE_PDF_singletUp"   : "flavTagWeight_LHEScaleWeight_PDF_singlet_UP/flavTagWeight",
                   "CMS_flavTag_LHE_PDF_singletDown" : "flavTagWeight_LHEScaleWeight_PDF_singlet_DOWN/flavTagWeight",
                   "CMS_flavTag_LHE_PDF_wjetsUp"     : "flavTagWeight_LHEScaleWeight_PDF_wjets_UP/flavTagWeight",
                   "CMS_flavTag_LHE_PDF_wjetsDown"   : "flavTagWeight_LHEScaleWeight_PDF_wjets_DOWN/flavTagWeight",
                   "CMS_flavTag_LHE_PDF_zjetsUp"     : "flavTagWeight_LHEScaleWeight_PDF_zjets_UP/flavTagWeight",
                   "CMS_flavTag_LHE_PDF_zjetsDown"   : "flavTagWeight_LHEScaleWeight_PDF_zjets_DOWN/flavTagWeight",
                   "CMS_flavTag_LHE_PDF_dibosonUp"   : "flavTagWeight_LHEScaleWeight_PDF_diboson_UP/flavTagWeight",
                   "CMS_flavTag_LHE_PDF_dibosonDown" : "flavTagWeight_LHEScaleWeight_PDF_diboson_DOWN/flavTagWeight",
                   "CMS_flavTag_LHE_aS_ttbarUp"      : "flavTagWeight_LHEScaleWeight_aS_ttbar_UP/flavTagWeight",
                   "CMS_flavTag_LHE_aS_ttbarDown"    : "flavTagWeight_LHEScaleWeight_aS_ttbar_DOWN/flavTagWeight",
                   "CMS_flavTag_LHE_aS_singletUp"    : "flavTagWeight_LHEScaleWeight_aS_singlet_UP/flavTagWeight",
                   "CMS_flavTag_LHE_aS_singletDown"  : "flavTagWeight_LHEScaleWeight_aS_singlet_DOWN/flavTagWeight",
                   "CMS_flavTag_LHE_aS_wjetsUp"      : "flavTagWeight_LHEScaleWeight_aS_wjets_UP/flavTagWeight",
                   "CMS_flavTag_LHE_aS_wjetsDown"    : "flavTagWeight_LHEScaleWeight_aS_wjets_DOWN/flavTagWeight",
                   "CMS_flavTag_LHE_aS_zjetsUp"      : "flavTagWeight_LHEScaleWeight_aS_zjets_UP/flavTagWeight",
                   "CMS_flavTag_LHE_aS_zjetsDown"    : "flavTagWeight_LHEScaleWeight_aS_zjets_DOWN/flavTagWeight",
                   "CMS_flavTag_LHE_aS_dibosonUp"    : "flavTagWeight_LHEScaleWeight_aS_diboson_UP/flavTagWeight",
                   "CMS_flavTag_LHE_aS_dibosonDown"  : "flavTagWeight_LHEScaleWeight_aS_diboson_DOWN/flavTagWeight",
                   "CMS_flavTag_PS_ISR_ttbarUp"      : "flavTagWeight_PSWeightISR_ttbar_UP/flavTagWeight",
                   "CMS_flavTag_PS_ISR_ttbarDown"    : "flavTagWeight_PSWeightISR_ttbar_DOWN/flavTagWeight",
                   "CMS_flavTag_PS_FSR_ttbarUp"      : "flavTagWeight_PSWeightFSR_ttbar_UP/flavTagWeight",
                   "CMS_flavTag_PS_FSR_ttbarDown"    : "flavTagWeight_PSWeightFSR_ttbar_DOWN/flavTagWeight",
                   "CMS_flavTag_PS_ISR_singletUp"    : "flavTagWeight_PSWeightISR_singlet_UP/flavTagWeight",
                   "CMS_flavTag_PS_ISR_singletDown"  : "flavTagWeight_PSWeightISR_singlet_DOWN/flavTagWeight",
                   "CMS_flavTag_PS_FSR_singletUp"    : "flavTagWeight_PSWeightFSR_singlet_UP/flavTagWeight",
                   "CMS_flavTag_PS_FSR_singletDown"  : "flavTagWeight_PSWeightFSR_singlet_DOWN/flavTagWeight",
                   "CMS_flavTag_PS_ISR_wjetsUp"      : "flavTagWeight_PSWeightISR_wjets_UP/flavTagWeight",
                   "CMS_flavTag_PS_ISR_wjetsDown"    : "flavTagWeight_PSWeightISR_wjets_DOWN/flavTagWeight",
                   "CMS_flavTag_PS_FSR_wjetsUp"      : "flavTagWeight_PSWeightFSR_wjets_UP/flavTagWeight",
                   "CMS_flavTag_PS_FSR_wjetsDown"    : "flavTagWeight_PSWeightFSR_wjets_DOWN/flavTagWeight",
                   "CMS_flavTag_PS_ISR_zjetsUp"      : "flavTagWeight_PSWeightISR_zjets_UP/flavTagWeight",
                   "CMS_flavTag_PS_ISR_zjetsDown"    : "flavTagWeight_PSWeightISR_zjets_DOWN/flavTagWeight",
                   "CMS_flavTag_PS_FSR_zjetsUp"      : "flavTagWeight_PSWeightFSR_zjets_UP/flavTagWeight",
                   "CMS_flavTag_PS_FSR_zjetsDown"    : "flavTagWeight_PSWeightFSR_zjets_DOWN/flavTagWeight",
                   "CMS_flavTag_PS_ISR_dibosonUp"    : "flavTagWeight_PSWeightISR_diboson_UP/flavTagWeight",
                   "CMS_flavTag_PS_ISR_dibosonDown"  : "flavTagWeight_PSWeightISR_diboson_DOWN/flavTagWeight",
                   "CMS_flavTag_PS_FSR_dibosonUp"    : "flavTagWeight_PSWeightFSR_diboson_UP/flavTagWeight",
                   "CMS_flavTag_PS_FSR_dibosonDown"  : "flavTagWeight_PSWeightFSR_diboson_DOWN/flavTagWeight",
                   "CMS_flavTag_JES_AbsoluteUp"      : "flavTagWeight_JESRegrouped_Absolute_UP/flavTagWeight",
                   "CMS_flavTag_JES_AbsoluteDown"    : "flavTagWeight_JESRegrouped_Absolute_DOWN/flavTagWeight",
                   "CMS_flavTag_JES_BBEC1Up"         : "flavTagWeight_JESRegrouped_BBEC1_UP/flavTagWeight",
                   "CMS_flavTag_JES_BBEC1Down"       : "flavTagWeight_JESRegrouped_BBEC1_DOWN/flavTagWeight",
                   "CMS_flavTag_JES_FlavorQCDUp"     : "flavTagWeight_JESRegrouped_FlavorQCD_UP/flavTagWeight",
                   "CMS_flavTag_JES_FlavorQCDDown"   : "flavTagWeight_JESRegrouped_FlavorQCD_DOWN/flavTagWeight",
                   "CMS_flavTag_JES_RelativeBalUp"   : "flavTagWeight_JESRegrouped_RelativeBal_UP/flavTagWeight",
                   "CMS_flavTag_JES_RelativeBalDown" : "flavTagWeight_JESRegrouped_RelativeBal_DOWN/flavTagWeight",
                   "CMS_flavTag_JES_Absolute_%sUp"   % year : "flavTagWeight_JESRegrouped_Absolute_%s_UP/flavTagWeight" % year,
                   "CMS_flavTag_JES_Absolute_%sDown" % year : "flavTagWeight_JESRegrouped_Absolute_%s_DOWN/flavTagWeight" % year,
                   "CMS_flavTag_JES_BBEC1_%sUp"      % year : "flavTagWeight_JESRegrouped_BBEC1_%s_UP/flavTagWeight" % year,
                   "CMS_flavTag_JES_BBEC1_%sDown"    % year : "flavTagWeight_JESRegrouped_BBEC1_%s_DOWN/flavTagWeight" % year,
                   "CMS_flavTag_JES_RelativeSample_%sUp"   % year : "flavTagWeight_JESRegrouped_RelativeSample_%s_UP/flavTagWeight" % year,
                   "CMS_flavTag_JES_RelativeSample_%sDown" % year : "flavTagWeight_JESRegrouped_RelativeSample_%s_DOWN/flavTagWeight" % year,
                   "CMS_flavTag_JEReta0to1p93_%sUp"   % year : "flavTagWeight_JEReta0to1p93_UP/flavTagWeight",
                   "CMS_flavTag_JEReta0to1p93_%sDown" % year : "flavTagWeight_JEReta0to1p93_DOWN/flavTagWeight",
                   "CMS_flavTag_JEReta1p93to2p5_%sUp"   % year : "flavTagWeight_JEReta1p93to2p5_UP/flavTagWeight",
                   "CMS_flavTag_JEReta1p93to2p5_%sDown" % year : "flavTagWeight_JEReta1p93to2p5_DOWN/flavTagWeight",
                   # Hdamp, b fragmentation, LHE scale, PS weights
                   "topHdampWeight_%sUp"   % year : f"TOPMLWeight[1]*TOPMLWeightNorm{suffix}[1]",
                   "topHdampWeight_%sDown" % year : f"TOPMLWeight[3]*TOPMLWeightNorm{suffix}[3]",
                   "bFragWeight_%sUp"   % year : f"(TOPMLWeight[4]*TOPMLWeightNorm{suffix}[4])/(TOPMLWeight[5]*TOPMLWeightNorm{suffix}[5])", #Divide by bFrag nominal and multiply by bFrag up
                   "bFragWeight_%sDown" % year : f"1/(TOPMLWeight[5]*TOPMLWeightNorm{suffix}[5])", #The standard samples are effectively bFrag down, so here just dividing by bFrag nominal and its renorm weight
                   "bFragPetersonWeight_%sUp"   % year : f"(bFragAndDecayWeight[3]*BFragAndDecayWeightNorm{suffix}[3])/(TOPMLWeight[5]*TOPMLWeightNorm{suffix}[5])", #A one-sided systematic
                   "bFragPetersonWeight_%sDown" % year : f"1.", #Effectively a one-sided systematic
                   # LHE for minor bkgs
                   #"LHE_minorBkg_muF_%sUp" % year : "LHEScaleWeight[5]*LHEScaleWeightNorm[5]",
                   #"LHE_minorBkg_muF_%sDown" % year : "LHEScaleWeight[3]*LHEScaleWeightNorm[3]",
                   #"LHE_minorBkg_muR_%sUp" % year : "LHEScaleWeight[7]*LHEScaleWeightNorm[7]",
                   #"LHE_minorBkg_muR_%sDown" % year : "LHEScaleWeight[1]*LHEScaleWeightNorm[1]",
                   # LHE for large bkgs
                   "LHE_muF_%sUp"   % year : f"LHEScaleWeight[5]*LHEScaleWeightNorm{suffix}[5]",
                   "LHE_muF_%sDown" % year : f"LHEScaleWeight[3]*LHEScaleWeightNorm{suffix}[3]",
                   "LHE_muR_%sUp"   % year : f"LHEScaleWeight[7]*LHEScaleWeightNorm{suffix}[7]",
                   "LHE_muR_%sDown" % year : f"LHEScaleWeight[1]*LHEScaleWeightNorm{suffix}[1]",
                   # PS for minor bkgs
                   "minorBkg_PS_ISR_%sUp"   % year : f"PSWeight[0]*PSWeightNorm{suffix}[0]",
                   "minorBkg_PS_ISR_%sDown" % year : f"PSWeight[2]*PSWeightNorm{suffix}[2]",
                   "minorBkg_PS_FSR_%sUp"   % year : f"PSWeight[1]*PSWeightNorm{suffix}[1]",
                   "minorBkg_PS_FSR_%sDown" % year : f"PSWeight[3]*PSWeightNorm{suffix}[3]",
                   # PS-fsr for large bkgs
                   "PS_fsr_G2GG_muR_%sDown" %year : f"PSWeight[6]*PSWeightNorm{suffix}[6]",
                   "PS_fsr_G2GG_muR_%sUp"   %year : f"PSWeight[7]*PSWeightNorm{suffix}[7]",
                   "PS_fsr_G2QQ_muR_%sDown" %year : f"PSWeight[8]*PSWeightNorm{suffix}[8]",
                   "PS_fsr_G2QQ_muR_%sUp"   %year : f"PSWeight[9]*PSWeightNorm{suffix}[9]",                              
                   "PS_fsr_Q2QG_muR_%sDown" %year : f"PSWeight[10]*PSWeightNorm{suffix}[10]",
                   "PS_fsr_Q2QG_muR_%sUp"   %year : f"PSWeight[11]*PSWeightNorm{suffix}[11]",                              
                   "PS_fsr_X2XG_muR_%sDown" %year : f"PSWeight[12]*PSWeightNorm{suffix}[12]",
                   "PS_fsr_X2XG_muR_%sUp"   %year : f"PSWeight[13]*PSWeightNorm{suffix}[13]",
                   "PS_fsr_G2GG_cNS_%sDown" %year : f"PSWeight[14]*PSWeightNorm{suffix}[14]",
                   "PS_fsr_G2GG_cNS_%sUp"   %year : f"PSWeight[15]*PSWeightNorm{suffix}[15]",
                   "PS_fsr_G2QQ_cNS_%sDown" %year : f"PSWeight[16]*PSWeightNorm{suffix}[16]",
                   "PS_fsr_G2QQ_cNS_%sUp"   %year : f"PSWeight[17]*PSWeightNorm{suffix}[17]",
                   "PS_fsr_G2QG_cNS_%sDown" %year : f"PSWeight[18]*PSWeightNorm{suffix}[18]",
                   "PS_fsr_G2QG_cNS_%sUp"   %year : f"PSWeight[19]*PSWeightNorm{suffix}[19]",
                   "PS_fsr_X2XG_cNS_%sDown" %year : f"PSWeight[20]*PSWeightNorm{suffix}[20]",
                   "PS_fsr_X2XG_cNS_%sUp"   %year : f"PSWeight[21]*PSWeightNorm{suffix}[21]",
                   # PS-isr for large bkgs
                   "PS_isr_G2GG_muR_%sDown" %year : f"PSWeight[28]*PSWeightNorm{suffix}[28]",
                   "PS_isr_G2GG_muR_%sUp"   %year : f"PSWeight[29]*PSWeightNorm{suffix}[29]",
                   "PS_isr_G2QQ_muR_%sDown" %year : f"PSWeight[30]*PSWeightNorm{suffix}[30]",
                   "PS_isr_G2QQ_muR_%sUp"   %year : f"PSWeight[31]*PSWeightNorm{suffix}[31]",
                   "PS_isr_Q2QG_muR_%sDown" %year : f"PSWeight[32]*PSWeightNorm{suffix}[32]",
                   "PS_isr_Q2QG_muR_%sUp"   %year : f"PSWeight[33]*PSWeightNorm{suffix}[33]",
                   "PS_isr_X2XG_muR_%sDown" %year : f"PSWeight[34]*PSWeightNorm{suffix}[34]",
                   "PS_isr_X2XG_muR_%sUp"   %year : f"PSWeight[35]*PSWeightNorm{suffix}[35]",
                   "PS_isr_G2GG_cNS_%sDown" %year : f"PSWeight[36]*PSWeightNorm{suffix}[36]",
                   "PS_isr_G2GG_cNS_%sUp"   %year : f"PSWeight[37]*PSWeightNorm{suffix}[37]",
                   "PS_isr_G2QQ_cNS_%sDown" %year : f"PSWeight[38]*PSWeightNorm{suffix}[38]",
                   "PS_isr_G2QQ_cNS_%sUp"   %year : f"PSWeight[39]*PSWeightNorm{suffix}[39]",
                   "PS_isr_G2QG_cNS_%sDown" %year : f"PSWeight[40]*PSWeightNorm{suffix}[40]",
                   "PS_isr_G2QG_cNS_%sUp"   %year : f"PSWeight[41]*PSWeightNorm{suffix}[41]",
                   "PS_isr_X2XG_cNS_%sDown" %year : f"PSWeight[42]*PSWeightNorm{suffix}[42]",
                   "PS_isr_X2XG_cNS_%sUp"   %year : f"PSWeight[43]*PSWeightNorm{suffix}[43]",
               }
        
        return systematics

    perProcessSysts = ["topHdampWeight_", "bFragWeight_", "bFragPetersonWeight_", "LHE_muF_", "LHE_muR_", "PS_fsr_", "PS_isr_", "minorBkg_PS_ISR_", "minorBkg_PS_FSR_"]

    nprocs = args.nproc if args.nproc else len(input_files)

    if args.mc_data_obs_5fs and args.mc_data_obs_4fs_mc_5fs:
        raise ValueError("--mc_data_obs_5fs and --mc_data_obs_4fs_mc_5fs are mutually exclusive.")

    process_trees_parallel(input_files, output_files, args.tree_name, args.year, selections, adhoc_selection, adhoc_binning, perProcessSysts, nprocs, args.mc_data_obs_5fs, args.mc_data_obs_4fs_mc_5fs, args.flavtag_sf_json, args.flavtag_sf_name)

    add_extra_systematic_histograms(
        args.extra_syst_dir,
        output_files,
        args.tree_name,
        args.year,
        selections,
        adhoc_selection,
        adhoc_binning,
    )

    sum_data(output_files, args.mc_data_obs_5fs, args.mc_data_obs_4fs_mc_5fs)
    print(f"All done!")
