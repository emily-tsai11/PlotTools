import warnings
warnings.filterwarnings('ignore', category=UserWarning, module='numpy')
import ROOT
import matplotlib.pyplot as plt
import mplhep as hep  # HEP (CMS) extensions/styling on top of mpl
import cmsstyle as CMS
import argparse
import glob
import os
import csv
import numpy as np
from ctypes import c_double

ROOT.TH1.SetDefaultSumw2(True)

def plot_unstacked(input_files, hist_name, output_dir, process, normalization=1, log=False):
    """
    Reads TH1Ds with the same name from multiple files and plots them unstacked.

    Parameters:
    - input_files: List of input ROOT files.
    - hist_name: Name of the histograms to plot.
    - output_dir: Output directory for the plots.
    - normalization: Decide what to normalize the histograms to.
    - log: Use log scale on the Y-axis.
    """

    # Create a figure with two subplots (main and ratio)
    fig, (ax, ax_ratio) = plt.subplots(2, 1, figsize=(10, 12), 
                                     gridspec_kw={'height_ratios': [3, 1], 'hspace': 0.05})

    sum_of_backgrounds = None

    # Create the histograms of Wcb and target process for the ratio
    hist_wcb = None
    hist_process = None
    
    process_name_beautifier = {
        "vcb": "Wcb", 
        "ttLF": "tt+LF", 
        "ttbb": "tt+bb", 
        "tt2b": "tt+2b", 
        "ttbj": "tt+bj", 
        "ttcc": "tt+cc", 
        "tt2c": "tt+2c", 
        "ttcj": "tt+cj"
    }
    
    # Save original process name before conversion
    process_key = process  # ex. "ttcc"
    process_label = process_name_beautifier.get(process, process)  # ex. "tt+cc"

    # Loop through input files and plot histograms
    for infile in input_files:

        if "h_QCD" in infile:
            continue #Skip QCD multijet for now

        # Exctract process name from file name
        proc_name_raw = os.path.basename(infile).replace('.root', '').replace('h_', '')
        
        # Special case handling for ttbb-4f
        #if "ttbb" in proc_name_raw:
        #    proc_name_raw = proc_name_raw.split("_")[1]

        # Compare before conversion to save hist_process
        is_target_process = (proc_name_raw == process_key or process_key in proc_name_raw)
        is_wcb = "vcb" in proc_name_raw or "Wcb" in proc_name_raw
        
        # Now convert for plotting
        proc_name_display = proc_name_raw
        for key, value in process_name_beautifier.items():
            if key in proc_name_raw:
                proc_name_display = value
                break
        
        print(f"Processing file: {infile}")
        print(f"  Process (raw): {proc_name_raw}")
        print(f"  Process (display): {proc_name_display}")
        print(f"  Is target: {is_target_process}, Is Wcb: {is_wcb}")

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
        hist_clone.SetDirectory(0)

        # Normalize if needed
        if hist_clone.Integral() > 0:
            hist_clone.Scale(normalization / hist_clone.Integral())

        # Save histograms for ratio plot
        if is_wcb:
            hist_wcb = hist_clone.Clone("hist_wcb")
            hist_wcb.SetDirectory(0)
        elif is_target_process:
            hist_process = hist_clone.Clone(f"hist_{process_key}")
            hist_process.SetDirectory(0)

        # Sum ALL backgrounds (excluding Wcb and Data)
        if not is_wcb and "Data" not in infile:
            if sum_of_backgrounds is None:
                sum_of_backgrounds = hist_clone.Clone("sum_of_backgrounds")
                sum_of_backgrounds.SetDirectory(0)
            else:
                sum_of_backgrounds.Add(hist_clone)

        # Plot ONLY Wcb and the target process
        if not is_wcb and not is_target_process:
            continue

        # Convert ROOT histogram to numpy array for plotting
        bin_edges = [hist_clone.GetBinLowEdge(i) for i in range(1, hist_clone.GetNbinsX() + 2)]
        y = [hist_clone.GetBinContent(i) for i in range(1, hist_clone.GetNbinsX() + 1)]

        # Plotting in the upper panel
        color = 'royalblue' if is_wcb else 'darkorange'
        ax.hist(bin_edges[:-1], bins=bin_edges, weights=y, histtype='step', 
                label=proc_name_display, linewidth=2, color=color)

    # Plot the sum of backgrounds
    if sum_of_backgrounds is not None and sum_of_backgrounds.Integral() > 0:
        sum_of_backgrounds.Scale(normalization / sum_of_backgrounds.Integral())
        bin_edges = [sum_of_backgrounds.GetBinLowEdge(i) for i in range(1, sum_of_backgrounds.GetNbinsX() + 2)]
        y = [sum_of_backgrounds.GetBinContent(i) for i in range(1, sum_of_backgrounds.GetNbinsX() + 1)]
        ax.hist(bin_edges[:-1], bins=bin_edges, weights=y, histtype='step', 
                label='Sum of bkgs', linewidth=2, color='black')

    # Add code here for the ratio plot
    if hist_wcb and hist_process:
        # Calculate the ratio
        ratio = hist_wcb.Clone("ratio")
        ratio.Divide(hist_process)

        # Convert to array for matplotlib
        bin_centers = [ratio.GetBinCenter(i) for i in range(1, ratio.GetNbinsX() + 1)]
        ratio_values = [ratio.GetBinContent(i) for i in range(1, ratio.GetNbinsX() + 1)]
        ratio_errors = [ratio.GetBinError(i) for i in range(1, ratio.GetNbinsX() + 1)]

        # Plot the ratio
        ax_ratio.errorbar(bin_centers, ratio_values, yerr=ratio_errors, 
                         fmt='o', color='black', markersize=4)

        # Add a horizontal line at y=1
        ax_ratio.axhline(y=1.0, color='gray', linestyle='--', alpha=0.7)

        # Configure ratio plot
        name = hist_name.replace('h_', '').replace('_', ' ')
        ax_ratio.set_ylabel(f'Wcb / {process_label}')  # Usa la versione beautified
        ax_ratio.set_xlabel(name) 
        x = np.arange(0, 1.1, 0.1)
        ax_ratio.set_xticks(x)
        ax_ratio.grid(True, alpha=0.4)     
        ax_ratio.set_xlim(ax.get_xlim())
        ax_ratio.set_ylim(bottom=-5, top=20)  
        ax.set_xlabel('')

    # Set log scale if required
    if log:
        ax.set_yscale('log')
        ax.set_ylim(bottom=1e-5, top=1e2)
    else:
        ax.set_ylim(bottom=0)
    ax.grid(True, alpha=0.4)

    # Add labels and title
    ax.set_ylabel('Normalized events / bin')
    ax.set_title('')
    
    # Add more xticks for better readability
    ax.set_xticks(np.arange(0., 1.1, 0.1))
    ax.set_xticklabels([])
    ax.legend(loc='upper right')
    
    # Add additional legend
    ax.text(0.65, 0.77, '$N_{\mathrm{jet}} > 3$' + '\n' + '$N_{\mathrm{bjet}} > 0$' + '\n' + '$N_{\mathrm{b/cjet}} > 2$', 
             transform=ax.transAxes, fontsize=18, verticalalignment='top')

    hep.cms.label("Preliminary", loc=2, ax=ax, lumi="110", com="13.6")
    
    # Save the plot
    output_file_png = os.path.join(output_dir, f'unstacked_{hist_name}_{process_label.replace("+", "")}.png')
    output_file_pdf = os.path.join(output_dir, f'unstacked_{hist_name}_{process_label.replace("+", "")}.pdf')
    plt.savefig(output_file_png)
    plt.savefig(output_file_pdf)
    plt.close()
    print("")

def plot_significance(input_files, output_dir, hist_name, cut_pace, log=False):
    """
    Plots the significance as a function of a cut on a given variable.
    Parameters:
    - input_files: List of input ROOT files.
    - output_dir: Output directory for the plots.
    - hist_name: Name of the histogram to plot.
    - cut_variable: The variable to apply the cut on.
    - log: Use log scale on the Y-axis.
    """

    fig, (ax, ax_significance) = plt.subplots(2, 1, figsize=(10, 12), gridspec_kw={'height_ratios': [3, 1], 'hspace': 0.05}, sharex=True)

    signal = None
    sum_of_backgrounds = None

    for infile in input_files:
        file_in = ROOT.TFile.Open(infile)
        if not file_in or file_in.IsZombie():
            raise FileNotFoundError(f"Could not open file: {infile}")

        if "Data" in infile or "data" in infile:
            continue
        print(f"Processing file: {infile}")

        # Retrieve the histogram
        hist = file_in.Get(hist_name)
        if not hist or not isinstance(hist, ROOT.TH1):
            raise ValueError(f"Histogram '{hist_name}' not found in file '{infile}'.")

        # Clone the histogram to avoid issues when the file is closed
        hist_clone = hist.Clone()
        hist_clone.SetDirectory(0)

        if "vcb" in infile:
            signal = hist_clone.Clone("signal")
            signal.SetDirectory(0)
        #elif "ttLF" in infile:
        else:
            if sum_of_backgrounds is None:
                sum_of_backgrounds = hist_clone.Clone("sum_of_backgrounds")
            else:
                sum_of_backgrounds.Add(hist_clone)
            sum_of_backgrounds.SetDirectory(0)
        #else:
        #    continue

        file_in.Close()

    significance = []
    significance_err = []
    # Apply the cut
    for pace in np.arange(cut_pace, 1 + cut_pace, cut_pace):
        sig_err = c_double(0.0)
        bkg_err = c_double(0.0)
        sig= signal.IntegralAndError(1, signal.FindBin(pace), sig_err) # Signal before the cut
        bkg = sum_of_backgrounds.IntegralAndError(1, sum_of_backgrounds.FindBin(pace), bkg_err) # Background before the cut
        significance.append(sig / (bkg)**0.5 if (sig + bkg) > 0 else 0)
        significance_err.append( ( 1./bkg * (sig_err.value**2 + (sig**2 * bkg_err.value**2 / (4*bkg**2))) )**0.5 if bkg > 0 else 0 )

    # Convert signal histogram to numpy array for plotting
    magnify_signal = 100.
    bin_edges_signal = [signal.GetBinLowEdge(i) for i in range(1, signal.GetNbinsX() + 2)]
    y_signal = [signal.GetBinContent(i)*magnify_signal for i in range(1, signal.GetNbinsX() + 1)]
    y_signal_err = [signal.GetBinError(i)*magnify_signal for i in range(1, signal.GetNbinsX() + 1)]
    
    # Convert background histogram to numpy array for plotting
    bin_edges_bkg = [sum_of_backgrounds.GetBinLowEdge(i) for i in range(1, sum_of_backgrounds.GetNbinsX() + 2)]
    y_bkg = [sum_of_backgrounds.GetBinContent(i) for i in range(1, sum_of_backgrounds.GetNbinsX() + 1)]
    y_bkg_err = [sum_of_backgrounds.GetBinError(i) for i in range(1, sum_of_backgrounds.GetNbinsX() + 1)]
    
    # Plot the histograms
    ax.hist(bin_edges_signal[:-1], bins=bin_edges_signal, weights=y_signal, 
            histtype='step', label='Wcb x ' + f"{magnify_signal:.0f}", linewidth=2, color='darkorange')
    ax.hist(bin_edges_bkg[:-1], bins=bin_edges_bkg, weights=y_bkg, 
            histtype='step', label='Sum of bkgs', linewidth=2, color='black')
    
    bin_centers_signal = [(bin_edges_signal[i] + bin_edges_signal[i+1])/2 for i in range(len(bin_edges_signal)-1)]
    bin_centers_bkg = [(bin_edges_bkg[i] + bin_edges_bkg[i+1])/2 for i in range(len(bin_edges_bkg)-1)]
    
    ax.fill_between(bin_centers_signal, 
                    [y - err for y, err in zip(y_signal, y_signal_err)],
                    [y + err for y, err in zip(y_signal, y_signal_err)],
                    alpha=0.3, color='darkorange', step='mid')
    ax.fill_between(bin_centers_bkg,
                    [y - err for y, err in zip(y_bkg, y_bkg_err)],
                    [y + err for y, err in zip(y_bkg, y_bkg_err)],
                    alpha=0.3, color='black', step='mid')

    ax.set_ylabel('Events')
    ax.grid(True, alpha=0.4)    
    if log:
        ax.set_yscale('log')
        ax.set_ylim(top=15*max(max(y_signal), max(y_bkg)), bottom=1e-1)
    ax.legend()
    hep.cms.label("Preliminary", loc=2, ax=ax, lumi="110", com="13.6")

    bin_centers = [0 + cut_pace/2 + i*cut_pace for i in range(int(1/cut_pace))]
    ax_significance.errorbar(bin_centers, significance, yerr=significance_err, 
                         fmt='o', color='royalblue', markersize=4)
    xaxis_name = hist_name.replace('h_', '').replace('_', ' ')
    # Configure the ratio plot
    ax_significance.set_ylabel('S/$\sqrt{B}$')
    ax_significance.set_xlabel(xaxis_name)
    ax_significance.grid(True, alpha=0.4)

    # Save the plot
    print(f"Saving histogram: {output_dir}/significance_{hist_name}.pdf/.png")
    output_file_png = os.path.join(output_dir, f'significance_{hist_name}.png')
    output_file_pdf = os.path.join(output_dir, f'significance_{hist_name}.pdf')
    plt.savefig(output_file_png)
    plt.savefig(output_file_pdf)
    plt.close()

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
               "h_score_tt2b" : np.array([0.,0.]),
               "h_score_ttbj" : np.array([0.,0.]),
               "h_score_ttcc" : np.array([0.,0.]),
               "h_score_tt2c" : np.array([0.,0.]),
               "h_score_ttcj" : np.array([0.,0.])}

    for infile in input_files:

        if "Data" in infile:
            continue

        if "h_QCD" in infile:
            continue #Skip QCD multijet for now

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
    labels = [label.replace('tt2b', 'tt+2b') for label in labels]  # Replace 'tt2b' with 'tt+2b'
    labels = [label.replace('ttbj', 'tt+bj') for label in labels]  # Replace 'ttbj' with 'tt+bj'
    labels = [label.replace('ttcc', 'tt+cc') for label in labels]  # Replace 'ttcc' with 'tt+cc'
    labels = [label.replace('tt2c', 'tt+2c') for label in labels]  # Replace 'tt2c' with 'tt+2c'
    labels = [label.replace('ttcj', 'tt+cj') for label in labels]  # Replace 'ttcj' with 'tt+cj'

    x = np.arange(len(labels))  # the label locations
    width = 0.35  # the width of the bars

    fig, ax = plt.subplots(figsize=(10, 10))
    hep.cms.label("Preliminary", loc=2, ax=ax, lumi="110", com="13.6")
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
               "h_score_tt2b_CR" : np.array([0.,0.]),
               "h_score_tt2b_SR" : np.array([0.,0.]),
               "h_score_ttbj_CR" : np.array([0.,0.]),
               "h_score_ttbj_SR" : np.array([0.,0.]),
               "h_score_ttcc_CR" : np.array([0.,0.]),
               "h_score_ttcc_SR" : np.array([0.,0.]),
               "h_score_tt2c_CR" : np.array([0.,0.]),
               "h_score_tt2c_SR" : np.array([0.,0.]),
               "h_score_ttcj_CR" : np.array([0.,0.]),
               "h_score_ttcj_SR" : np.array([0.,0.]),
               "h_fscore_ttLF_CR" : np.array([0.,0.]),
               "h_fscore_ttbb_CR" : np.array([0.,0.]),
               "h_fscore_tt2b_CR" : np.array([0.,0.]),
               "h_fscore_ttbj_CR" : np.array([0.,0.]),
               "h_fscore_ttcc_CR" : np.array([0.,0.]),
               "h_fscore_tt2c_CR" : np.array([0.,0.]),
               "h_fscore_ttcj_CR" : np.array([0.,0.])}

    for infile in input_files:
        print()
        print(f"Processing file: {infile}")

        if "Data" in infile:
            continue

        if "h_QCD" in infile:
            continue #Skip QCD multijet for now

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
                proc_name = "tt-vcb"

            hist = root_file.Get(hist_name.replace('_' + proc_region, ''))
            if not hist or not isinstance(hist, ROOT.TH1):
                raise ValueError(f"Histogram '{hist_name}' not found in file '{infile}'.")

            # Clone the histogram to avoid issues when the file is closed
            hist_clone = hist.Clone()
            hist_clone.SetDirectory(0)
            #print("")
            print("PROC NAME", proc_name)
            if proc_name in infile.split('h_')[-1]:
                process[hist_name][0] += hist_clone.Integral() 
                print(f"Integral of {hist_name} in {infile}: {hist_clone.Integral()}")
            process[hist_name][1] += hist_clone.Integral()
            print(f"Total integral of {hist_name}: {process[hist_name][1]}")
        

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
    labels = [label.replace('tt_Wcb', r'$\mathrm{W}\to\mathrm{cb}$') for label in labels]  # Replace 'tt_Wcb' with 'W-->cb'
    labels = [label.replace('ttLF', r'$\mathrm{t\bar{t}}$+LF') for label in labels]  # Replace 'ttLF' with 'tt+LF'
    labels = [label.replace('ttbb', r'$\mathrm{t\bar{t}}+j_{b}j_{b}$') for label in labels]  # Replace 'ttbb' with 'tt+j_b j_b'
    labels = [label.replace('tt2b', r'$\mathrm{t\bar{t}}+j_{bb}$') for label in labels]  # Replace 'tt2b' with 'tt+j_bb'
    labels = [label.replace('ttbj', r'$\mathrm{t\bar{t}}+j_{b}$') for label in labels]  # Replace 'ttbj' with 'tt+j_b'
    labels = [label.replace('ttcc', r'$\mathrm{t\bar{t}}+j_{c}j_{c}$') for label in labels]  # Replace 'ttcc' with 'tt+j_c j_c'
    labels = [label.replace('tt2c', r'$\mathrm{t\bar{t}}+j_{cc}$') for label in labels]  # Replace 'tt2c' with 'tt+j_cc'
    labels = [label.replace('ttcj', r'$\mathrm{t\bar{t}}+j_{c}$') for label in labels]  # Replace 'ttcj' with 'tt+j_c'
    

    x = np.arange(len(labels))  # the label locations
    width = 0.35  # the width of the bars

    fig, ax = plt.subplots(figsize=(10, 10))
    hep.cms.label("Preliminary", loc=2, ax=ax, lumi="110", com="13.6")
    bars_CR = ax.bar(x - width/3, values_CR, width, label='CR')
    bars_fscores = ax.bar(x, values_CR_fscores, width, label='CR-fscores')
    bars_SR = ax.bar(x + width/3, values_SR, width, label='SR')


    # Add legend and move it down
    ax.legend(loc='upper right')#, bbox_to_anchor=(0.5, -0.15))
    if raw_evt_number:
        ax.set_ylabel('Events')
        ax.set_yscale('log')
        plt.ylim(1, max(max(values_CR), max(values_SR))*10)
    else:
        ax.set_ylabel('Purity')
        plt.ylim(0, 1)
    ax.set_xlabel('NN category')
    plt.xticks(x, labels, rotation=-20 , ha='center')

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

def compare_FSs(input_files, output_dir, process, raw_evt_number=False):
    """
    Plot the number of tt+bb, tt+2b, and tt+bj events that populate the score and fscore histograms in the 4FS and 5FS cases.
    """

    # Dictionary to hold the weighted number of events for each process in a given category (first array element)
    # and the total number of events in the same category (second array element).
    category = {"h_score_tt_Wcb_4F" : np.array([0.,0.]),
                "h_score_tt_Wcb_5F" : np.array([0.,0.]),
                "h_fscore_ttLF_4F" : np.array([0.,0.]),
                "h_fscore_ttLF_5F" : np.array([0.,0.]),
                "h_fscore_ttbb_4F" : np.array([0.,0.]),
                "h_fscore_ttbb_5F" : np.array([0.,0.]),
                "h_fscore_tt2b_4F" : np.array([0.,0.]),
                "h_fscore_tt2b_5F" : np.array([0.,0.]),
                "h_fscore_ttbj_4F" : np.array([0.,0.]),
                "h_fscore_ttbj_5F" : np.array([0.,0.]),
                "h_fscore_ttcc_4F" : np.array([0.,0.]),
                "h_fscore_ttcc_5F" : np.array([0.,0.]),
                "h_fscore_tt2c_4F" : np.array([0.,0.]),
                "h_fscore_tt2c_5F" : np.array([0.,0.]),
                "h_fscore_ttcj_4F" : np.array([0.,0.]),
                "h_fscore_ttcj_5F" : np.array([0.,0.])}

    for infile in input_files:
        print(f"Processing file: {infile}")

        if "Data" in infile:
            continue

        if "h_QCD" in infile:
            continue #Skip QCD multijet for now

        # Open the file
        root_file = ROOT.TFile.Open(infile)
        if not root_file or root_file.IsZombie():
            raise FileNotFoundError(f"Could not open file: {infile}")
        
        for hist_name in category.keys():

            # Retrieve the histogram
            proc_name = hist_name.split('_')[-2]
            proc_region = hist_name.split('_')[-1]
            if not proc_region in infile:
                continue

            print(f"Processing histogram: {hist_name}")

            hist = root_file.Get(hist_name.replace('_' + proc_region, ''))
            if not hist or not isinstance(hist, ROOT.TH1):
                raise ValueError(f"Histogram '{hist_name.replace('_' + proc_region, '')}' not found in file '{infile}'.")

            # Clone the histogram to avoid issues when the file is closed
            hist_clone = hist.Clone()
            hist_clone.SetDirectory(0)

            if process in infile: # Select if you want to plot the contribution of ttbb or ttbj, for example
                print(f"Integral of {hist_name} in {infile}: {hist_clone.Integral()}")
                category[hist_name][0] += hist_clone.Integral() 
            category[hist_name][1] += hist_clone.Integral()
        
    labels_4F = [key for key in category.keys() if '4F' in key]
    labels_5F = [key for key in category.keys() if '5F' in key]

    # Create matplotlib histogram with six bins, one for each process
    if raw_evt_number:
        values_4F = [category[proc][0] for proc in labels_4F]
        values_5F = [category[proc][0] for proc in labels_5F]
    else:
        values_4F = [category[proc][0] / category[proc][1] if category[proc][1] > 0 else 0 for proc in labels_4F]
        values_5F = [category[proc][0] / category[proc][1] if category[proc][1] > 0 else 0 for proc in labels_5F]

    # Create a ratio plot comparing 4FS and 5FS
    ratio_4Fto5F = [v4F / v5F if v5F > 0 else 0 for v4F, v5F in zip(values_4F, values_5F)]

    labels = [label.replace('h_score_', '') for label in labels_4F]  # Remove 'h_score_' prefix for better readability
    labels = [label.replace('h_fscore_', '') for label in labels]  # Remove 'h_fscore_' prefix for better readability
    labels = [label.replace('_4F', '') for label in labels]  # Remove the "_4F" suffix
    labels = [label.replace('tt_Wcb', 'Wcb') for label in labels]  # Replace 'tt_Wcb' with 'Wcb'
    labels = [label.replace('ttLF', 'tt+LF') for label in labels]  # Replace 'ttLF' with 'tt+LF'
    labels = [label.replace('ttbb', 'tt+bb') for label in labels]  # Replace 'ttbb' with 'tt+bb'
    labels = [label.replace('tt2b', 'tt+2b') for label in labels]  # Replace 'ttbb' with 'tt+bb'
    labels = [label.replace('ttbj', 'tt+bj') for label in labels]  # Replace 'ttbj' with 'tt+bj'
    labels = [label.replace('ttcc', 'tt+cc') for label in labels]  # Replace 'ttcc' with 'tt+cc'
    labels = [label.replace('tt2c', 'tt+2c') for label in labels]  # Replace 'ttcc' with 'tt+cc'
    labels = [label.replace('ttcj', 'tt+cj') for label in labels]  # Replace 'ttcj' with 'tt+cj'

    x = np.arange(len(labels_4F))  # the label locations
    width = 0.35  # the width of the bars

    fig, (ax, ax_ratio) = plt.subplots(2, 1, figsize=(10, 12), 
                                       gridspec_kw={'height_ratios': [3, 1], 
                                                   'hspace': 0.05})  
    
    hep.cms.label("Preliminary", loc=2, ax=ax, lumi="110", com="13.6")
    
    # Main plot
    bars4F = ax.bar(x - width/2, values_4F, width, label=process + ' 4FS', color='blue', alpha=0.7)
    bars5F = ax.bar(x + width/2, values_5F, width, label=process + ' 5FS', color='red', alpha=0.7)
    
    # Main plot config
    ax.legend(loc='upper right')
    ax.text(0.72, 0.64,'AR\n' + '$N_{\mathrm{jet}} > 3$' + '\n' + '$N_{\mathrm{bjet}} > 0$' + '\n' + '$N_{\mathrm{b/cjet}} > 2$', 
            transform=ax.transAxes, fontsize=20)
    
    if raw_evt_number:
        ax.set_yscale('log')
        ax.set_ylim(1, max(max(values_4F), max(values_5F))*100)
        ax.set_ylabel('Events')
    else:
        ax.set_ylim(0, 1)
        ax.set_ylabel('Purity')

    ax.set_xticklabels([]) 
    
    # Ratio
    ax_ratio.scatter(x, ratio_4Fto5F, color='green', s=80, zorder=3)  # s=80 sets the dot size, zorder=3 brings it to the front
    
    # Horizontal line at y=1
    ax_ratio.axhline(y=1, color='black', linestyle='--', alpha=0.5)
    
    # Ratio plot configuration  
    ax_ratio.set_ylabel('4F/5F')
    ax_ratio.set_ylim(0, 2) 
    ax_ratio.set_xlabel('NN category')
    ax.set_xticks(x)
    ax_ratio.set_xticks(x)
    ax_ratio.set_xlim(ax.get_xlim())
    ax_ratio.set_xticklabels(labels, rotation=-20, ha='center')

    # Save the plot
    if raw_evt_number:
        output_file_png = os.path.join(output_dir, f'raw_evt_number_{process}_4F5F.png')
        output_file_pdf = os.path.join(output_dir, f'raw_evt_number_{process}_4F5F.pdf')
    else:
        output_file_png = os.path.join(output_dir, f'purity_{process}_4F5F.png')
        output_file_pdf = os.path.join(output_dir, f'purity_{process}_4F5F.pdf')

    #plt.tight_layout()
    plt.savefig(output_file_png)
    plt.savefig(output_file_pdf)
    plt.close()
    print("")
    

def compare_4F5F_vs_score(input_files, output_dir, process):
    """
    Plot the number of tt+bb + tt+bj + tt+2c events that populate the tt_Wcb score histograms in the 4FS and 5FS cases.
    """
    # Create a figure with two subplots (main and ratio)
    fig, (ax, ax_ratio) = plt.subplots(2, 1, figsize=(10, 12), 
                                     gridspec_kw={'height_ratios': [3, 1], 'hspace': 0.05})

    hep.cms.label("Preliminary", loc=2, ax=ax, lumi="110", com="13.6")
    
    category = {"h_score_tt_Wcb_4F" : ROOT.TH1D("h_score_tt_Wcb_4F", "", 20, 0, 1),
                "h_score_tt_Wcb_5F" : ROOT.TH1D("h_score_tt_Wcb_5F", "", 20, 0, 1)}
    
    for infile in input_files:
        print(f"Processing file: {infile}")

        if "QCD_tree" in infile:
            continue #Skip QCD multijet for now

        if process == "ttbx":
            if not "bb" in infile and not "bj" in infile and not "2b" in infile:
                continue
        else:
            if not process in infile:
                continue

        # Open the file
        root_file = ROOT.TFile.Open(infile)
        if not root_file or root_file.IsZombie():
            raise FileNotFoundError(f"Could not open file: {infile}")
        
        for hist_name in category.keys():

            # Retrieve the histogram
            proc_name = hist_name.split('_')[-2]
            proc_region = hist_name.split('_')[-1]
            if not proc_region in infile:
                continue

            print(f"Processing histogram: {hist_name}")

            hist = root_file.Get(hist_name.replace('_' + proc_region, ''))
            if not hist or not isinstance(hist, ROOT.TH1):
                raise ValueError(f"Histogram '{hist_name.replace('_' + proc_region, '')}' not found in file '{infile}'.")

            # Clone the histogram to avoid issues when the file is closed
            hist_clone = hist.Clone()
            hist_clone.SetDirectory(0)

            print(f"name1: {hist_clone.GetName()}, nbins1: {hist_clone.GetNbinsX()}, nbins2: {category['h_score_tt_Wcb_4F'].GetNbinsX()}")

            if "4F" in infile:
                category["h_score_tt_Wcb_4F"] += hist_clone
            else:
                category["h_score_tt_Wcb_5F"] += hist_clone

    # Convert ROOT histogram to numpy array for plotting
    bin_edges = [category["h_score_tt_Wcb_4F"].GetBinLowEdge(i) for i in range(1, category["h_score_tt_Wcb_4F"].GetNbinsX() + 2)]
    y_4F = [category["h_score_tt_Wcb_4F"].GetBinContent(i) for i in range(1, category["h_score_tt_Wcb_4F"].GetNbinsX() + 1)]
    #bin_edges_5F = [category["h_score_tt_Wcb_5F"].GetBinLowEdge(i) for i in range(1, category["h_score_tt_Wcb_5F"].GetNbinsX() + 2)]
    y_5F = [category["h_score_tt_Wcb_5F"].GetBinContent(i) for i in range(1, category["h_score_tt_Wcb_5F"].GetNbinsX() + 1)]

    # Plotting in the upper panel
    ax.hist(bin_edges[:-1], bins=bin_edges, weights=y_4F, histtype='step', label='4F', linewidth=2)
    ax.hist(bin_edges[:-1], bins=bin_edges, weights=y_5F, histtype='step', label='5F', linewidth=2, linestyle='--')
    ax.set_yscale('log')
    ax.set_ylim(top=15*max(max(y_4F), max(y_5F)))
    ax.legend(loc='upper right')
    ax.set_ylabel('Events / 0.01')
    ax.set_xlabel('') # Hide x-axis labels of the main plot
    ax.set_xticks([])

    # Calculate the ratio
    ratio = category["h_score_tt_Wcb_4F"].Clone("ratio")
    ratio.Divide(category["h_score_tt_Wcb_5F"])

    # Convert to array for matplotlib
    bin_centers = [ratio.GetBinCenter(i) for i in range(1, ratio.GetNbinsX() + 1)]
    ratio_values = [ratio.GetBinContent(i) for i in range(1, ratio.GetNbinsX() + 1)]
    ratio_errors = [ratio.GetBinError(i) for i in range(1, ratio.GetNbinsX() + 1)]

    # Plot the ratio
    ax_ratio.errorbar(bin_centers, ratio_values, yerr=ratio_errors, 
                         fmt='o', color='black', markersize=4)

    # Add a horizontal line at y=1
    ax_ratio.axhline(y=1.0, color='gray', linestyle='--', alpha=0.7)

    # Configure ratio plot
    ax_ratio.set_ylabel(f'4FS / 5FS')
    ax_ratio.set_xlabel('score ttWcb') 
    x = np.arange(0,1.1,0.1)
    ax_ratio.set_xticks(x)
    ax_ratio.grid(True, alpha=0.4)     
    ax_ratio.set_xlim(ax.get_xlim()) # Same x-limits for both plots
    ax_ratio.set_ylim(bottom=0, top=2)  

    # Save the plot
    output_file_png = os.path.join(output_dir, f'compare_4F5F_vs_score_ttWcb_{process}.png')
    output_file_pdf = os.path.join(output_dir, f'compare_4F5F_vs_score_ttWcb_{process}.pdf')
    #plt.tight_layout()
    plt.savefig(output_file_png)
    plt.savefig(output_file_pdf)
    plt.close()
    print("")
    
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stack TH1D histograms from multiple ROOT files.")
    parser.add_argument("--input_dir", type=str, required=True, help="Input directory, where ROOT files are located.")
    parser.add_argument("--hist_name", required=False, help="Name of the histograms to stack.")
    parser.add_argument("--input_csv", type=str, required=False, help="The csv file to read variables and ranges from.")
    parser.add_argument("--output_dir", type=str, required=True, help="Output directory for the plot containing histograms.")
    parser.add_argument("--normalization", type=int, default=1, help="Decide the histogram normalization.")
    parser.add_argument("--log", nargs="?", const=1, type=bool, default=False, required=False, help="Decide whether to use log scale on the Y-axis.")
    parser.add_argument("--purity", nargs="?", const=1, type=bool, default=False, required=False, help="Decide whether to plot purity.")
    parser.add_argument("--significance", nargs="?", const=1, type=bool, default=False, required=False, help="Decide whether to plot significance.")
    parser.add_argument("--multiRegion", nargs="?", const=1, type=bool, default=False, required=False, help="Decide whether to plot the purity for multiple regions.")
    parser.add_argument("--raw_evt_number", nargs="?", const=1, type=bool, default=False, required=False, help="Decide whether to plot the raw event numbers.")
    parser.add_argument("--plot_4F5F", nargs="?", const=1, type=bool, default=False, required=False, help="Decide whether to plot a 4F-5F comparison in every NN category.")
    parser.add_argument("--plot_4F5F_vs_score", nargs="?", const=1, type=bool, default=False, required=False, help="Decide whether to plot a 4F-5F comparison of ttbb+ttbj in the ttWcb score.")
    parser.add_argument("--process", type=str, required=False, help="Decide if you want to plot ttbb, tt2b, or ttbj in the 4F-5F comparison.")

    args = parser.parse_args()

    # Get input files from the input_dir
    if args.multiRegion:
        input_files = glob.glob(f"{args.input_dir}/CR/*.root") + glob.glob(f"{args.input_dir}/SR/*.root") + glob.glob(f"{args.input_dir}/CRfscores/*.root")
    elif args.plot_4F5F:
        input_files = glob.glob(f"{args.input_dir}/4FS/*.root") + glob.glob(f"{args.input_dir}/5FS/*.root")
    elif args.plot_4F5F_vs_score:
        input_files = glob.glob(f"{args.input_dir}/*4FS/*.root") + glob.glob(f"{args.input_dir}/*5FS/*.root")
    else:
        input_files = glob.glob(f"{args.input_dir}*.root")

    input_processes = ["tt-vcb", "ttbar-powheg_ttLF", "ttbar-powheg_ttcc", "ttbar-powheg_tt2c", "ttbar-powheg_ttcj", "ttbb", "tt2b", "ttbj", "others"]
    #input_processes = ["ttWcb", "diboson-tWZ", "singletop", "ttH-ttV", "ttbar-powheg_ttLF", "ttbb-withDPS", "ttbj-withDPS", "ttbar-powheg_ttcc", "ttbar-powheg_ttcj", "wjets"]

    # Create the output directory if it does not exist
    create_output_dir(args.output_dir)

    # Set the style for the plot
    hep.style.use("CMS")

    # Plot either all histograms from the csv file or a single histogram. Decide whether to plot purity.
    if args.purity:
        if args.multiRegion:
            plot_purity_multiregion(input_files, args.output_dir, args.raw_evt_number)
        else:
            plot_purity(input_files, args.output_dir)
    elif args.plot_4F5F:
        compare_FSs(input_files, args.output_dir, args.process, args.raw_evt_number)
    elif args.plot_4F5F_vs_score:
        compare_4F5F_vs_score(input_files, args.output_dir, args.process)
    elif args.significance:
            plot_significance(input_files, args.output_dir, args.hist_name, cut_pace=0.02, log=args.log)
    else:
        if not args.hist_name:
            hist_list = read_csv(args.input_csv)
            for hist_name in hist_list:
                plot_unstacked(input_files, hist_name, args.output_dir, args.process, args.normalization, args.log)
        else:
            plot_unstacked(input_files, args.hist_name, args.output_dir, args.process, args.normalization, args.log)

