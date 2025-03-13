import ROOT
import argparse
import glob
import csv
import os
from colorama import Fore, Style

ROOT.ROOT.EnableImplicitMT()

def process_trees(input_files, output_files, tree_name, score_map, year, selections, syst_list):
    """
    Processes multiple TTrees, converts them to multiple TH1Ds for specified branches, and saves them to ROOT files.

    Parameters:
    - input_files: List of input ROOT files.
    - output_files: List of output ROOT files.
    - tree_names: List of TTree names corresponding to input files.
    - score_map: Dictionary containing the branch name, number of bins, xmin, and xmax for the histograms.
    - year: Data taking year.
    - selections: Dictionary containing event selections.
    """

    for infile in input_files:
        print(f"{Fore.RED}Processing file: {infile}{Style.RESET_ALL}")

        # Open input file
        input_file = ROOT.TFile.Open(infile)
        if not input_file or input_file.IsZombie():
            raise FileNotFoundError(f"Could not open file: {infile}")

        # Access the TTree
        tree = input_file.Get(tree_name)
        if not tree or not isinstance(tree, ROOT.TTree):
            raise ValueError(f"TTree '{tree_name}' not found in file '{infile}'.")

        # Create RDataFrame from TTree
        df = ROOT.RDataFrame(tree)

        tt_file_names = ["ttbb-4f","ttbar-powheg"]
        tt4f_strings = ["ttbb", "ttbj"]
        tt_strings   = ["ttcc", "ttcj", "ttLF"]

        # Process each selection-output combinations
        for selection_name in selections:

            # Apply base selection to every sample; apply the ttbar-specific selection to the right 4f and powheg samples
            if not "base" in selection_name and not any(x in infile for x in tt_file_names): 
                continue
            if any(x in infile for x in tt_file_names) and "base" in selection_name:
                continue
            if any(x in selection_name for x in tt4f_strings) and not "4f" in infile: 
                continue
            if any(x in selection_name for x in tt_strings) and not "powheg" in infile:
                continue

            # Add event selection making sure that the "base" selection is applied everywhere
            event_selection = f"{selections['base']}{selections[selection_name]}" if not "base" in selection_name else f"{selections[selection_name]}"
            if "singlee" in infile:
                event_selection += " && passTrigMu==0" # Remove from the electron channel the events that fired the muon trigger. Could choose to do vice versa as well.
            #print(f"Applying selection: {event_selection} -> Producing output file: {output_file}")
            df_selected = df.Filter(event_selection)

            # Assign event weight based on data taking year and process type
            for syst in syst_list:
                if syst == "":
                    weight = assign_event_weight(year, infile)
                else:
                    weight = assign_event_weight(year, infile, syst)

                # If weight is a complex expression, define it as a new column
                weight_column = "weight_column" + syst
                if not "data" in infile:
                    print(f"Event weight: {weight}")
                    df_selected = df_selected.Define(weight_column, weight)
                else: # Keep the weight 1 for collision data
                    df_selected = df_selected.Define(weight_column, "1")

                for (cat, score), outfile in zip(score_map.items(), output_files):
                    fOut = ROOT.TFile(outfile, "UPDATE")
                    fOut.cd()
                    print(f"Creating histogram for category: {cat} and selection: {Fore.GREEN}{selection_name}{Style.RESET_ALL}")
                    hist_name = infile.split('/')[-1].replace('_tree.root','')
                    if any(x in infile for x in tt_file_names):
                        hist_name = selection_name
                    if "Data" in hist_name:
                        hist_name = "data_obs"
                    if not syst == "":
                        hist_name = f"{hist_name}_{syst}"
                    hist = df_selected.Histo1D((f"{hist_name}", f"Histogram of {score[0]} for process {hist_name}", score[1], score[2], score[3]), score[0], weight_column)
                    hist.Write()

                    print(f"Saved histograms to: {outfile}\n")
                    fOut.Close()

        input_file.Close()


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

def assign_event_weight(year, infile, syst=""):
    """
    Define the MC event weight according to the year. Collision data should be handled separately.

    Parameters:
    - year: Data taking year.
    - infile: Input file.
    - syst: Systematic uncertainty string.
    """
    weight = "1"
    if year == 2018:
        weight = "lumiwgt*genWeight*xsecWeight*l1PreFiringWeight*puWeight*muEffWeight*elEffWeight*flavTagWeight*(((abs(lep1_pdgId)==11 && passTrigEl && ((year!=2018) || (year==2018 && !(lep1_phi>-1.57 && lep1_phi<-0.87 && lep1_eta<-1.3)))) || (abs(lep1_pdgId)==13 && passTrigMu)) && passmetfilters)"
    if "ttbar" in infile:
        weight = f"{weight}*topptWeight"
    if "4f" in infile:
        weight = f"{weight}*topptWeight"#*0.7559" # 5FS / 4FS for tt+B component
    
    if syst == "CMS_puWeight_Up":
        weight = f"{weight}*puWeightUp/puWeight"
    if syst == "CMS_puWeight_Down":
        weight = f"{weight}*puWeightDown/puWeight"
    
    return weight

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process ROOT TTrees into TH1D histograms.")
    parser.add_argument("--input_dirs", nargs='+', required=True, help="List of directories where the ROOT files are fetched.")
    parser.add_argument("--output_dir", type=str, required=True, help="Output directory of the new ROOT files.")
    parser.add_argument("--tree_name", type=str, required=True, help="List of TTree names in the input files.")
    parser.add_argument("--year", type=int, required=True, help="Data taking year.")
    parser.add_argument("--electron", nargs="?", const=1, type=bool, default=False, required=False, help="Process electron channel only.")
    parser.add_argument("--muon", nargs="?", const=1, type=bool, default=False, required=False, help="Process muon channel only.")

    args = parser.parse_args()

    # Categories for combine datacards
    prepended_ = "Vcb_"
    categories = ["catWcb", "catBB", "catBJ", "catCC", "catCJ", "catLF"]
    appended_ = ["_CR", "_SR"]

    score_map = {"catWcb" : ["score_tt_Wcb", 20, 0., 1.], "catBB" : ["score_ttbb", 20, 0., 1.], "catBJ" : ["score_ttbj", 20, 0., 1.], "catCC" : ["score_ttcc", 20, 0., 1.], "catCJ" : ["score_ttcj", 20, 0., 1.], "catLF" : ["score_ttLF", 20, 0., 1.]}

    # Get input files from the input_dirs list
    for input_dir in args.input_dirs:
        input_files = glob.glob(f"{input_dir}*.root")

    # Prepare list of output files based on the name of the input files
    output_files = prepare_output(args.output_dir, args.year, categories, prepended_, appended_)
    print(f"Output files: {output_files}")

    # Define event selections. Some are process-specific.
    selections = {"base": "n_ak4>=4 && (n_btagM+n_ctagM)>=3 && n_btagM>=1",
                 #"base": "n_ak4>=4 && (n_btagM+n_ctagM)>=3 && n_btagM>=1 && score_tt_Wcb<=0.9",  
                 "ttbb" : " && genEventClassifier==9 && wcb==0",
                 "ttbj" : " && (genEventClassifier==7 || genEventClassifier==8) && wcb==0",
                 "ttcc" : " && genEventClassifier==6 && wcb==0",
                 "ttcj" : " && (genEventClassifier==4 || genEventClassifier==5) && wcb==0",
                 "ttLF" : " && tt_category==0 && higgs_decay==0 && wcb==0"
    }

    # Apply trigger selection to separate channels if requested
    if args.electron:
        selections["base"] += " && passTrigEl"
    if args.muon:
        selections["base"] += " && passTrigMu"

    # Define list of systematic variations to include
    syst_list = ["","CMS_puWeight_Up", "CMS_puWeight_Down"]    

    process_trees(input_files, output_files, args.tree_name, score_map, args.year, selections, syst_list)

    # Merge some of the output files
    #ttV_list = ["h_ttW.root", "h_ttZ.root"]
    #merge_files(args.output_dir, ttV_list, "h_ttV.root")
    #ttH_list = ["h_ttHbb.root", "h_ttHcc.root", "h_ttV.root"]
    #merge_files(args.output_dir, ttH_list, "h_ttH-ttV.root")
    #ttbb_list = ["h_ttbb-4f_ttbb.root", "h_ttbb-dps.root"]
    #merge_files(args.output_dir, ttbb_list, "h_ttbb-withDPS.root")
    #ttbb_list = ["h_TWZ.root", "h_diboson.root"]
    #merge_files(args.output_dir, ttbb_list, "h_diboson-tWZ.root")
    #data_list = ["h_singlee.root", "h_singlemu.root"]
    #merge_files(args.output_dir, data_list, "h_Data.root")"
