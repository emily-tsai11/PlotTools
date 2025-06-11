import ROOT
import matplotlib.pyplot as plt
import mplhep as hep  # HEP (CMS) extensions/styling on top of mpl
import cmsstyle as CMS
import argparse
import glob
import os
import csv
import numpy as np

def plot_unstacked(input_files, hist_name, output_dir, normalization=1, log=False):
    """
    Reads TH1Ds with the same name from multiple files and plots them unstacked.

    Parameters:
    - input_files: List of input ROOT files.
    - hist_name: Name of the histograms to plot.
    - output_dir: Output directory for the plots.
    - normalization: Decide what to normalize the histograms to.
    - log: Use log scale on the Y-axis.
    """
    # Create a figure for plotting
    plt.figure(figsize=(10, 6))
    # Set the style for the plot
    #CMS.SetStyle()

    #canvas = ROOT.TCanvas("canvas", "canvas", 800, 600)

    sum_of_backgrounds = ROOT.TH1D("sum_of_backgrounds", "Sum of backgrounds", 20, 0, 1)  # Example binning

    # Loop through input files and plot histograms
    for infile in input_files:

        proc_name = os.path.basename(infile).replace('.root', '')
        proc_name = proc_name.replace('h_', '')

        #print(f"Reading file: {infile}")
        #print(f"Histogram name: {hist_name}")
        print(f"Processing: {proc_name}")

        if "Wcb" in proc_name:
            proc_name = "Wcb"
        elif "ttLF" in proc_name:
            proc_name = "tt+LF"

        # Open the file
        root_file = ROOT.TFile.Open(infile)
        if not root_file or root_file.IsZombie():
            raise FileNotFoundError(f"Could not open file: {infile}")

        # Retrieve the histogram
        hist = root_file.Get(hist_name)
        if not hist or not isinstance(hist, ROOT.TH1):
            raise ValueError(f"Histogram '{hist_name}' not found in file '{infile}'.")

        # Clone the histogram to avoid issues when the file is closed
        hist_clone = hist.Clone()
        hist_clone.SetDirectory(0)  # Detach from the file

        # Normalize if needed
        hist_clone.Scale(normalization/hist_clone.Integral())

        if not "Wcb" in proc_name and not "Data" in proc_name:
            print(f"Adding {proc_name} to the sum of backgrounds")
            sum_of_backgrounds.Add(hist_clone)

        if not "Wcb" in proc_name and not "tt+LF" in proc_name:
            continue

        # Convert ROOT histogram to numpy array for plotting
        bin_edges = [hist_clone.GetBinLowEdge(i) for i in range(1, hist_clone.GetNbinsX() + 2)]
        y = [hist_clone.GetBinContent(i) for i in range(1, hist_clone.GetNbinsX() + 1)]

        # Plotting
        plt.hist(bin_edges[:-1], bins=bin_edges, weights=y, histtype='step', label=proc_name, linewidth=2)
        #Add uncertinties as error bars. Need to debug 
        #y_err = [hist_clone.GetBinError(i) for i in range(1, hist_clone.GetNbinsX() + 1)]
        #print(y_err)
        #bin_centers = [hist_clone.GetBinCenter(i) for i in range(1, hist_clone.GetNbinsX() + 1)]
        #plt.errorbar(bin_centers, y, yerr=y_err, color='red', fmt='none', capsize=5, capthick=1, ecolor='black')
        

    sum_of_backgrounds.Scale(normalization/sum_of_backgrounds.Integral())
    # Convert the sum of backgrounds to numpy arrays for plotting
    bin_edges = [sum_of_backgrounds.GetBinLowEdge(i) for i in range(1, sum_of_backgrounds.GetNbinsX() + 2)]
    y = [sum_of_backgrounds.GetBinContent(i) for i in range(1, sum_of_backgrounds.GetNbinsX() + 1)]
    # Plot the sum of backgrounds together with the other histograms
    plt.hist(bin_edges[:-1], bins=bin_edges, weights=y, histtype='step', label='Sum of backgrounds', linewidth=2, color='black')
 
    # Set log scale if required
    if log:
        plt.yscale('log')
        plt.ylim(bottom=1e-5)
    else:
        plt.ylim(bottom=0)
    plt.grid(True)

    # Add labels and title
    name = hist_name.replace('h_', '').replace('_', ' ')
    plt.xlabel(name)
    plt.ylabel('Normalized events / bin')
    plt.title(f'{name}')
    # Add more xticks for better readability
    plt.xticks(np.arange(0., 1.1, 0.1))
    plt.legend(loc='upper right')
    # Add additional legend
    plt.text(0.57, 0.97, '$N_{\mathrm{jet}} > 3$' + '\n' + '$N_{\mathrm{bjet}} > 0$' + '\n' + '$N_{\mathrm{b/cjet}} > 2$', 
             transform=plt.gca().transAxes, fontsize=14, verticalalignment='top')

    # Save the plot
    output_file_png = os.path.join(output_dir, f'unstacked_{hist_name}.png')
    output_file_pdf = os.path.join(output_dir, f'unstacked_{hist_name}.pdf')
    plt.savefig(output_file_png)
    plt.savefig(output_file_pdf)
    plt.close()
    print("")

def create_output_dir(output_dir):
    """
    Create the output directory if it does not exist.

    Parameters:
    - output_dir: The directory where the output files will be saved.
    - log: Boolean indicating whether a log directory should be created.
    """
    os.makedirs(output_dir, exist_ok=True)

def read_csv(csv_file):
    """
    Open and read a csv file containing the name and the range of the variables to be plotted. 
    Fill in a list of histogram names.

    Parameters:
    - csv_file: The csv file containing variable names and binning for the respective histograms.
    """
    with open(csv_file, mode = 'r') as f:
        csv_reader = csv.reader(f) 
        hist_list = [line[0] for line in csv_reader if not line[0] == 'Variable']
        hist_list = [f"h_{hist}" for hist in hist_list]

    return hist_list

def plot_purity(input_files, output_dir):
    """
    Plots the fraction of events of a given process over the total in the category that should constrain such process.

    Parameters:
    - input_files: List of input ROOT files.
    - output_dir: Output directory for the plots.
    """

    # Dictionary to hold the weighted number of events for each process in a given category (first array element)
    # and the total number of events in the same category (second array element).
    process = {"h_score_tt_Wcb" : np.array([0.,0.]),
               "h_score_ttLF" : np.array([0.,0.]),
               "h_score_ttbb" : np.array([0.,0.]),
               "h_score_ttbj" : np.array([0.,0.]),
               "h_score_ttcc" : np.array([0.,0.]),
               "h_score_ttcj" : np.array([0.,0.])}

    for infile in input_files:

        if "Data" in infile:
            continue

        # Open the file
        root_file = ROOT.TFile.Open(infile)
        if not root_file or root_file.IsZombie():
            raise FileNotFoundError(f"Could not open file: {infile}")

        # Retrieve the histogram
        for hist_name in process.keys():

            proc_name = hist_name.split('_')[-1]
            if "Wcb" in proc_name:
                proc_name = "ttWcb"

            hist = root_file.Get(hist_name)
            if not hist or not isinstance(hist, ROOT.TH1):
                raise ValueError(f"Histogram '{hist_name}' not found in file '{infile}'.")

            # Clone the histogram to avoid issues when the file is closed
            hist_clone = hist.Clone()
            hist_clone.SetDirectory(0)

            if proc_name in infile:
                process[hist_name][0] += hist_clone.Integral() 
            process[hist_name][1] += hist_clone.Integral()

    labels = list(process.keys())
    # Create matplotlib histogram with six bins, one for each process
    values = [process[proc][0] / process[proc][1] if process[proc][1] > 0 else 0 for proc in labels]

    labels = [label.replace('h_score_', '') for label in labels]  # Remove 'h_score_' prefix for better readability
    labels = [label.replace('tt_Wcb', 'Wcb') for label in labels]  # Replace 'ttWcb' with 'Wcb'
    labels = [label.replace('ttLF', 'tt+LF') for label in labels]  # Replace 'ttLF' with 'tt+LF'
    labels = [label.replace('ttbb', 'tt+bb') for label in labels]  # Replace 'ttbb' with 'tt+bb'
    labels = [label.replace('ttbj', 'tt+bj') for label in labels]  # Replace 'ttbj' with 'tt+bj'
    labels = [label.replace('ttcc', 'tt+cc') for label in labels]  # Replace 'ttcc' with 'tt+cc'
    labels = [label.replace('ttcj', 'tt+cj') for label in labels]  # Replace 'ttcj' with 'tt+cj'

    x = np.arange(len(labels))  # the label locations
    width = 0.35  # the width of the bars
    hep.style.use("CMS")
    fig, ax = plt.subplots(figsize=(10, 10))
    hep.cms.label("Work in progress", loc=2, ax=ax, lumi="59.8")
    bars = ax.bar(x, values, width, label='Purity')
    ax.set_ylabel('Purity')
    ax.set_xlabel('NN category')
    plt.xticks(x, labels, rotation=-20 , ha='center')
    plt.ylim(0, 1)

    # Save the plot
    output_file_png = os.path.join(output_dir, f'purity.png')
    output_file_pdf = os.path.join(output_dir, f'purity.pdf')
    plt.savefig(output_file_png)
    plt.savefig(output_file_pdf)
    plt.close()
    print("")


def plot_purity_multiregion(input_files, output_dir, raw_evt_number=False):
    """
    Plots the fraction of events of a given process over the total in the category that should constrain such process.

    Parameters:
    - input_files: List of input ROOT files.
    - output_dir: Output directory for the plots.
    """

    # Dictionary to hold the weighted number of events for each process in a given category (first array element)
    # and the total number of events in the same category (second array element).
    process = {"h_score_tt_Wcb_CR" : np.array([0.,0.]),
               "h_score_tt_Wcb_SR" : np.array([0.,0.]),
               "h_score_ttLF_CR" : np.array([0.,0.]),
               "h_score_ttLF_SR" : np.array([0.,0.]),
               "h_score_ttbb_CR" : np.array([0.,0.]),
               "h_score_ttbb_SR" : np.array([0.,0.]),
               "h_score_ttbj_CR" : np.array([0.,0.]),
               "h_score_ttbj_SR" : np.array([0.,0.]),
               "h_score_ttcc_CR" : np.array([0.,0.]),
               "h_score_ttcc_SR" : np.array([0.,0.]),
               "h_score_ttcj_CR" : np.array([0.,0.]),
               "h_score_ttcj_SR" : np.array([0.,0.]),
               "h_fscore_ttLF_CR" : np.array([0.,0.]),
               "h_fscore_ttbb_CR" : np.array([0.,0.]),
               "h_fscore_ttbj_CR" : np.array([0.,0.]),
               "h_fscore_ttcc_CR" : np.array([0.,0.]),
               "h_fscore_ttcj_CR" : np.array([0.,0.])}

    for infile in input_files:
        print(f"Processing file: {infile}")

        if "Data" in infile:
            continue

        # Open the file
        root_file = ROOT.TFile.Open(infile)
        if not root_file or root_file.IsZombie():
            raise FileNotFoundError(f"Could not open file: {infile}")

        # Retrieve the histogram
        for hist_name in process.keys():

            proc_name = hist_name.split('_')[-2]
            proc_region = hist_name.split('_')[-1]
            if not proc_region in infile:
                continue
            if "fscore" in hist_name and not "fscore" in infile:
                continue
            if not "Wcb" in proc_name:
                if "fscore" in infile and not "fscore" in hist_name:
                    continue

            print(f"Processing histogram: {hist_name} for process: {proc_name} in region: {proc_region}")

            if "Wcb" in proc_name:
                proc_name = "ttWcb"

            hist = root_file.Get(hist_name.replace('_' + proc_region, ''))
            if not hist or not isinstance(hist, ROOT.TH1):
                raise ValueError(f"Histogram '{hist_name}' not found in file '{infile}'.")

            # Clone the histogram to avoid issues when the file is closed
            hist_clone = hist.Clone()
            hist_clone.SetDirectory(0)

            if proc_name in infile:
                process[hist_name][0] += hist_clone.Integral() 
            process[hist_name][1] += hist_clone.Integral()

    labels_CR = [key for key in process.keys() if ('CR' in key) and ('fscore' not in key)]
    labels_fscores = [key for key in process.keys() if 'fscore' in key or "Wcb_CR" in key]
    labels_SR = [key for key in process.keys() if 'SR' in key]

    # Create matplotlib histogram with six bins, one for each process
    if raw_evt_number:
        values_CR = [process[proc][0] for proc in labels_CR]
        values_SR = [process[proc][0] for proc in labels_SR]
        values_CR_fscores = [process[proc][0] for proc in labels_fscores]
    else:
        values_CR = [process[proc][0] / process[proc][1] if process[proc][1] > 0 else 0 for proc in labels_CR]
        values_SR = [process[proc][0] / process[proc][1] if process[proc][1] > 0 else 0 for proc in labels_SR]
        values_CR_fscores = [process[proc][0] / process[proc][1] if process[proc][1] > 0 else 0 for proc in labels_fscores]


    labels = [label.replace('h_score_', '') for label in labels_CR]  # Remove 'h_score_' prefix for better readability
    labels = [label.replace('_CR', '') for label in labels]  # Remove the "_CR" suffix
    labels = [label.replace('tt_Wcb', 'Wcb') for label in labels]  # Replace 'ttWcb' with 'Wcb'
    labels = [label.replace('ttLF', 'tt+LF') for label in labels]  # Replace 'ttLF' with 'tt+LF'
    labels = [label.replace('ttbb', 'tt+bb') for label in labels]  # Replace 'ttbb' with 'tt+bb'
    labels = [label.replace('ttbj', 'tt+bj') for label in labels]  # Replace 'ttbj' with 'tt+bj'
    labels = [label.replace('ttcc', 'tt+cc') for label in labels]  # Replace 'ttcc' with 'tt+cc'
    labels = [label.replace('ttcj', 'tt+cj') for label in labels]  # Replace 'ttcj' with 'tt+cj'
    

    x = np.arange(len(labels))  # the label locations
    width = 0.35  # the width of the bars
    hep.style.use("CMS")
    fig, ax = plt.subplots(figsize=(10, 10))
    hep.cms.label("Work in progress", loc=2, ax=ax, lumi="59.8")
    # Plot two sets of bars for CR and SR
    bars_CR = ax.bar(x - width/3, values_CR, width, label='Purity in CR')
    #print(f"Purity in CR fscores: {values_CR_fscores}")
    #print(f"Purity in CR: {values_CR}")
    bars_fscores = ax.bar(x, values_CR_fscores, width, label='Purity in CR-fscores')
    bars_SR = ax.bar(x + width/3, values_SR, width, label='Purity in SR')
    # Add legend and move it down
    ax.legend(loc='center right')#, bbox_to_anchor=(0.5, -0.15))

    ax.set_ylabel('Purity')
    ax.set_xlabel('NN category')
    plt.xticks(x, labels, rotation=-20 , ha='center')
    if not raw_evt_number:
        plt.ylim(0, 1)

    # Save the plot
    if raw_evt_number:
        output_file_png = os.path.join(output_dir, f'raw_evt_number_CRSR.png')
        output_file_pdf = os.path.join(output_dir, f'raw_evt_number_CRSR.pdf')
    else:
        output_file_png = os.path.join(output_dir, f'purity_CRSR.png')
        output_file_pdf = os.path.join(output_dir, f'purity_CRSR.pdf')
    plt.savefig(output_file_png)
    plt.savefig(output_file_pdf)
    plt.close()
    print("")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stack TH1D histograms from multiple ROOT files.")
    parser.add_argument("--input_dir", type=str, required=True, help="Input directory, where ROOT files are located.")
    parser.add_argument("--hist_name", required=False, help="Name of the histograms to stack.")
    parser.add_argument("--input_csv", type=str, required=True, help="The csv file to read variables and ranges from.")
    parser.add_argument("--output_dir", type=str, required=True, help="Output directory for the plot containing histograms.")
    parser.add_argument("--normalization", type=int, default=1, help="Decide the histogram normalization.")
    parser.add_argument("--log", nargs="?", const=1, type=bool, default=False, required=False, help="Decide whether to use log scale on the Y-axis.")
    parser.add_argument("--purity", nargs="?", const=1, type=bool, default=False, required=False, help="Decide whether to plot purity.")
    parser.add_argument("--multiRegion", nargs="?", const=1, type=bool, default=False, required=False, help="Decide whether to plot the purity for multiple regions.")
    parser.add_argument("--raw_evt_number", nargs="?", const=1, type=bool, default=False, required=False, help="Decide whether to plot the raw event numbers.")

    args = parser.parse_args()

    # Set plotting details
    #CMS.SetExtraText("Work in progress")
    #CMS.SetLumi("59.83")

    # Get input files from the input_dir
    if args.multiRegion:
        input_files = glob.glob(f"{args.input_dir}/CR/*.root") + glob.glob(f"{args.input_dir}/SR/*.root") + glob.glob(f"{args.input_dir}/CRfscores/*.root")

    else:
        input_files = glob.glob(f"{args.input_dir}*.root")

    # Create the output directory if it does not exist
    create_output_dir(args.output_dir)

    # Plot either all histograms from the csv file or a single histogram. Decide whether to plot purity.
    if args.purity:
        if args.multiRegion:
            plot_purity_multiregion(input_files, args.output_dir, args.raw_evt_number)
        else:
            plot_purity(input_files, args.output_dir)

    else:
        if not args.hist_name:
            hist_list = read_csv(args.input_csv)
            for hist_name in hist_list:
                plot_unstacked(input_files, hist_name, args.output_dir, args.normalization, args.log)
        else:
            plot_unstacked(input_files, args.hist_name, args.output_dir, args.normalization, args.log)

