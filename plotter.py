import ROOT
import argparse
import glob
import math
import csv
import os
import cmsstyle as CMS

ROOT.TH1.SetDefaultSumw2(True)
ROOT.gROOT.SetBatch(True)

# https://cmsstyle.readthedocs.io/en/latest/reference/#cmsstyle.cmsstyle.p10
colours = {
    "ttWcb": "#ffa90e",
    "ttLF": "#e76300",
    "ttcj": "#b9ac70",
    "tt2c": "#94a4a2",
    "ttcc": "#717581",
    "ttbj": "#92dadd",
    "tt2b": "#3f90da",
    "ttbb": "#832db6",
    "others": "#a96b59",
    "QCD": "#bd1f01",
}

tt_components = ['Wcb', 'ttbb', 'ttbj', 'tt2b', 'ttbb-dps', 'ttbj-dps', 'tt2b-dps', 'ttcc', 'ttcj', 'tt2c', 'ttLF', 'ttZ', 'ttW', 'ttHbb', 'ttHcc'] #Use Wcb because that's the process name in the script, converted from the input file name
tt_components_nobb = ['Wcb', 'ttcc', 'ttcj', 'tt2c', 'ttLF'] #Use Wcb because that's the process name in the script, converted from the input file name
minorBkg_components = ['singletop', 'wjets', 'diboson', 'QCD', 'others']
signal = ['Wcb'] #Use Wcb because that's the process name in the script, converted from the input file name

def build_colour_list(phys_process):
    colour_list = []
    for key in phys_process.keys():
        colour_list.append(colours[key])
    return colour_list

def stack_histograms(
        input_files,
        hist_name,
        syst_list,
        output_dir,
        sonly,
        sig_norm,
        log,
        blind,
        verbosity,
        x_low = None,
        x_high = None,
    ):
    """
    Reads TH1Ds with the same name from multiple files, stacks them in a THStack, and saves the result.

    Parameters:
    - input_dir: Input directory, where ROOT files are located.
    - hist_name: Name of the histograms to stack.
    - x_low: lower x axis bound for plotting
    - x_high: upper x axis bound for plotting
    - syst_list: List of systematic uncertainties to include in the plots.
    - output_dir: Output directory for the TCanvas containing THStacks.
    - sonly: Decide whether to plot only the signal.
    - sig_norm: Normalization of the signal.
    - log: Use log scale on the Y-axis.
    - blind: Decide whether to blind the data in the ttWcb score histogram.
    """
    # Create a THStack and a dictionary {process name : histogram} to feed to the CMS plotting
    stack = ROOT.THStack("stack", f"Stack of {hist_name}")
    phys_process = dict()
    hist_total = None
    bin_errors_down = None
    bin_errors_up = None

    # Define X-axis boundaries for the stack
    # x_low, x_high = 0., 1.

    # Create a histogram for the signal and the collision data to be added separately from the stack
    sig_hist = ROOT.TH1D()
    data_hist = ROOT.TH1D()

    if sonly:
        print(f"Plotting only the signal")

    # Decide whether to blind the data in the invariant mass histogram
    isBlind = True if (hist_name == "h_score_tt_Wcb" and blind) else False

    # Open input files and retrieve histograms
    for infile in input_files:

        if sonly and "vcb" not in infile:
            continue

        if verbosity > 0:
            print(f"Reading file: {infile}")

        # Open the file
        root_file = ROOT.TFile.Open(infile)
        if not root_file or root_file.IsZombie():
            raise FileNotFoundError(f"Could not open file: {infile}")

        # Retrieve the nominal histogram
        hist = root_file.Get(hist_name)
        if not hist or not isinstance(hist, ROOT.TH1):
            raise ValueError(f"Histogram '{hist_name}' not found in file '{infile}'.")

        # Clone the histogram to avoid issues when the file is closed
        hist_clone = hist.Clone()
        hist_clone.SetDirectory(0) # Detach from the file

        # Assign X-axis boundaries for the stack
        if x_low is None:
            x_low = hist_clone.GetBinLowEdge(1)
        if x_high is None:
            x_high = hist_clone.GetBinLowEdge(hist_clone.GetNbinsX() + 1)

        infile_short = infile.split("/")[-1]
        if "Data" not in infile_short:
            if hist_total is None:
                hist_total = hist.Clone()
                hist_total.SetDirectory(0) # Detach from the file
            else:
                hist_total.Add(hist_clone)

        # Get bin midpoints, width from the histogram
        binwidths = ROOT.TVectorF(hist_clone.GetNbinsX())
        midpoints = ROOT.TVectorF(hist_clone.GetNbinsX())
        for i in range(1, hist_clone.GetNbinsX() + 1):
            low = hist_clone.GetBinLowEdge(i)
            high = hist_clone.GetBinLowEdge(i + 1)
            binwidths[i - 1] = (high - low) / 2.0
            midpoints[i - 1] = (low + high) / 2.0

        # Treat the signal sample separately (it will be added also as a dashed line to the plots)
        if "vcb" in infile:
            print(f"W->cb x {sig_norm} histogram will be also added to the plot separately")
            sig_hist = hist.Clone()
            sig_hist.SetDirectory(0)
            sig_hist *= sig_norm
            if sonly: continue # Avoid adding W->cb to the stack when plotting signal only
        if "Data" in infile:
            print(f"Data histogram will be added to the plot separately")
            if isBlind: continue
            data_hist = hist_clone
            continue

        # Fill dictionary {process name : histogram} to feed to the CMS plotting
        phys_process_name = (infile.split('_')[-1]).replace('.root', '').replace('-vcb', 'Wcb')
        phys_process[phys_process_name] = hist_clone

        if bin_errors_down is None:
            bin_errors_down = ROOT.TVectorF(hist_clone.GetNbinsX())
            bin_errors_up = ROOT.TVectorF(hist_clone.GetNbinsX())
            for i in range(1, hist_clone.GetNbinsX() + 1):
                bin_errors_down[i - 1] = 0.0
                bin_errors_up[i - 1] = 0.0

        # Get the statistical uncertainties on the nominal histogram
        for i in range(1, hist_clone.GetNbinsX() + 1):
            bin_errors_down[i - 1] = bin_errors_down[i - 1] + hist_clone.GetBinError(i) * hist_clone.GetBinError(i)
            bin_errors_up[i - 1] = bin_errors_up[i - 1] + hist_clone.GetBinError(i) * hist_clone.GetBinError(i)

        for syst in syst_list:
            # Retrieve the systematic variation histograms
            found = True

            # Make sure to just apply certain systematics to certain processes (basically, as in prepareDatacards.py)
            if syst.startswith("minorBkg") and not any(name in phys_process_name for name in minorBkg_components):
                continue
            if syst.startswith("PS_fsr") and not any(name in phys_process_name for name in tt_components):
                continue
            if syst.startswith("PS_isr") and not any(name in phys_process_name for name in tt_components):
                continue
            if syst.startswith("bFrag") and not any(name in phys_process_name for name in tt_components):
                continue
            if syst.startswith("tune") and not any(name in phys_process_name for name in signal):
                continue
            if syst.startswith("CR") and not any(name in phys_process_name for name in signal):
                continue


            hist_syst_down = root_file.Get(f"{hist_name}_{syst}Down")
            if not hist_syst_down or not isinstance(hist_syst_down, ROOT.TH1):
                if verbosity > 1:
                    print(f"WARNING: Histogram '{hist_name}_{syst}Down' not found in file '{infile_short}'.")
                found = False
            hist_syst_up = root_file.Get(f"{hist_name}_{syst}Up")
            if not hist_syst_up or not isinstance(hist_syst_up, ROOT.TH1):
                if verbosity > 1:
                    print(f"WARNING: Histogram '{hist_name}_{syst}Up' not found in file '{infile_short}'.")
                found = False
            if not found:
                if verbosity > 0:
                    print(
                        f"WARNING: Skipping '{hist_name}_{syst}Down' / '{hist_name}_{syst}Up' for {infile_short}."
                    )
                continue

            # Clone the histogram to avoid issues when the file is closed
            hist_syst_down_clone = hist_syst_down.Clone()
            hist_syst_down_clone.SetDirectory(0) # Detach from the file
            hist_syst_up_clone = hist_syst_up.Clone()
            hist_syst_up_clone.SetDirectory(0) # Detach from the file

            if hist_clone.GetNbinsX() != hist_syst_down_clone.GetNbinsX():
                raise RuntimeError(
                    f"'{hist_name}_{syst}Down' has a different number of bins from the nominal histogram."
                )
            if hist_clone.GetNbinsX() != hist_syst_up_clone.GetNbinsX():
                raise RuntimeError(
                    f"'{hist_name}_{syst}Up' has a different number of bins from the nominal histogram."
                )

            for i in range(1, hist_clone.GetNbinsX() + 1):
                diff = hist_clone.GetBinContent(i) - hist_syst_down_clone.GetBinContent(i)
                bin_errors_down[i - 1] += diff * diff
                diff = hist_syst_up_clone.GetBinContent(i) - hist_clone.GetBinContent(i)
                bin_errors_up[i - 1] += diff * diff

        # Close the file
        root_file.Close()

    for i in range(len(bin_errors_down)):
        bin_errors_down[i] = math.sqrt(bin_errors_down[i])
        bin_errors_up[i] = math.sqrt(bin_errors_up[i])

    # Sort processes from largest to smallest
    phys_process = {
        key: value
        for key, value in sorted(
            phys_process.items(),
            key=lambda item: item[1].Integral(),
        )
    }
    # del phys_process["QCD"]

    # Save the stack in a canvas and add a legend
    print(f"Saving stacked histograms as: {output_dir}{hist_name.replace('h_', '')}.pdf / .png")
    canvas = CMS.cmsDiCanvas(
        'canvas',
        x_low,
        x_high,
        0,
        1,
        0.7,
        1.3,
        hist_name.replace('h_', ''),
        'Events',
        'Data/MC',
        square=CMS.kSquare,
        extraSpace=0.01,
        iPos=0,
    )
    # canvas = CMS.cmsDiCanvas(
    #     'canvas',
    #     x_low,
    #     x_high,
    #     0,
    #     1,
    #     0.7,
    #     1.3,
    #     hist_name.replace('h_', ''),
    #     'Events',
    #     'Sig/Bkg',
    #     square=CMS.kSquare,
    #     extraSpace=0.01,
    #     iPos=11,
    # )
    canvas.cd(1)
    # Make this legend of three columns
    legend = CMS.cmsLeg(
        0.41,
        0.65,
        0.93,
        0.89,
        textSize=0.04,
        columns=3,
    ) # Needs to be defined after the cmsCanvas or it won't be plotted
    if not sonly and not isBlind:
        legend.AddEntry(data_hist, "Data", "pe")
    legend.AddEntry(sig_hist, f"W#rightarrowcb#times{sig_norm}", "l")

    CMS.cmsDrawStack(stack, legend, phys_process, palette=build_colour_list(phys_process))
    if not sonly:
        CMS.cmsDraw(sig_hist, "same", lstyle=2, msize=0, lcolor=ROOT.kRed, lwidth=4)
    else:
        CMS.cmsDraw(sig_hist, "same, hist", msize=0, fcolor=ROOT.kRed, lcolor=ROOT.kRed, fstyle=3018)
    CMS.cmsDraw(data_hist, "E1X0", mcolor=ROOT.kBlack)

    # Get y values of MC stack
    y_stack = ROOT.TVectorF(hist_total.GetNbinsX())
    for i in range(1, hist_total.GetNbinsX() + 1):
        y_stack[i - 1] = hist_total.GetBinContent(i)

    # Set Y-axis range based on maximum value of stacked histograms
    hist_from_canvas = CMS.GetcmsCanvasHist(canvas.GetPad(1))
    hist_from_canvas.GetYaxis().SetRangeUser(
        0.0,
        max(stack.GetHistogram().GetMaximum(), data_hist.GetMaximum()) * 1.9,
    )
    if sonly:
        hist_from_canvas.GetYaxis().SetRangeUser(0.01, sig_hist.GetMaximum() * 1.2)
    hist_from_canvas.GetYaxis().SetMaxDigits(2) # Force scientific notation above 3 digits on the Y-axis
    if not log:
        # Shift multiplier position
        ROOT.TGaxis.SetExponentOffset(-0.085, 0.01, "Y")
    # Draw the stack in log scale
    if log:
        ROOT.gPad.SetLogy()
        hist_from_canvas.GetYaxis().SetRangeUser(
            0.1,
            max(stack.GetHistogram().GetMaximum(), data_hist.GetMaximum()) * 0.3e4,
        )
        if sonly:
            hist_from_canvas.GetYaxis().SetRangeUser(
                0.01,
                sig_hist.GetMaximum() * 1e3,
            )

    # Add error bars
    if not sonly:
        bkg_hist = stack.GetStack().Last()
        err_hist = bkg_hist.Clone()
        CMS.cmsDraw(
            err_hist,
            "e2same0",
            # lcolor=ROOT.kBlack,
            # lwidth=1,
            msize=0,
            fcolor=ROOT.kBlack,
            # fstyle=3004,
            alpha=0.25,
        )
        legend.AddEntry(err_hist, "Stat. Unc.", "f")

        asym_errors = ROOT.TGraphAsymmErrors(
            midpoints,
            y_stack,
            binwidths,
            binwidths,
            bin_errors_down,
            bin_errors_up,
        )
        asym_errors.SetFillColor(ROOT.kBlack)
        asym_errors.SetLineColor(ROOT.kBlack)
        asym_errors.SetLineWidth(1)
        asym_errors.SetFillStyle(3005)
        asym_errors.Draw("e2same0")
        legend.AddEntry(asym_errors, "Stat.#oplusSyst.", "f")

        # Ratio plot
        canvas.cd(2)
        ratio = data_hist.Clone("ratio")
        ratio.Divide(bkg_hist)

        for i in range(1, ratio.GetNbinsX() + 1):
            if ratio.GetBinContent(i):
                ratio.SetBinError(i, math.sqrt(data_hist.GetBinContent(i)) / bkg_hist.GetBinContent(i))
            else:
                ratio.SetBinError(i, 10**(-99))

        rel_err_y = ROOT.TVectorF(hist_total.GetNbinsX())
        rel_err_down = ROOT.TVectorF(hist_total.GetNbinsX())
        rel_err_up = ROOT.TVectorF(hist_total.GetNbinsX())
        for i in range(1, hist_total.GetNbinsX() + 1):
            rel_err_y[i - 1] = 1.0
            if y_stack[i - 1]:
                rel_err_down[i - 1] = bin_errors_down[i - 1] / y_stack[i - 1]
                rel_err_up[i - 1] = bin_errors_up[i - 1] / y_stack[i - 1]
            else:
                rel_err_down[i - 1] = 10**(-99)
                rel_err_up[i - 1] = 10**(-99)
        asym_errors_ratio = ROOT.TGraphAsymmErrors(
            midpoints,
            rel_err_y,
            binwidths,
            binwidths,
            rel_err_down,
            rel_err_up,
        )
        asym_errors_ratio.SetFillColor(ROOT.kBlack)
        asym_errors_ratio.SetFillStyle(3005)
        asym_errors_ratio.Draw("e2same0")

        prediction_ratio = bkg_hist.Clone()
        prediction_ratio.Divide(bkg_hist)
        CMS.cmsDraw(
            prediction_ratio,
            "e2same0",
            # lwidth=100,
            msize=0,
            fcolor=ROOT.kBlack,
            # fstyle=3004,
            alpha=0.25,
        )
        if not isBlind:
            CMS.cmsDraw(ratio, "E1X0", mcolor=ROOT.kBlack)
        ref_line = ROOT.TLine(x_low, 1, x_high, 1)
        CMS.cmsDrawLine(ref_line, lcolor=ROOT.kBlack, lstyle=ROOT.kDotted)
        ratio_from_canvas = CMS.GetcmsCanvasHist(canvas.GetPad(2))
        ratio_from_canvas.GetYaxis().SetRangeUser(0.4, 1.6)

        # Ratio plot
        # canvas.cd(2)
        # sig_hist_clone = sig_hist.Clone()
        # bkg_hist_clone = bkg_hist.Clone()
        # sig_hist_clone.Scale(1.0 / sig_hist_clone.Integral())
        # bkg_hist_clone.Scale(1.0 / bkg_hist_clone.Integral())

        # ratio = sig_hist_clone.Clone("ratio")
        # ratio.Divide(bkg_hist_clone)

        # for i in range(1, ratio.GetNbinsX() + 1):
        #    ratio.SetBinError(i, 0)

        # prediction_ratio = bkg_hist.Clone()
        # prediction_ratio.Divide(bkg_hist)
        # CMS.cmsDraw(
        #     prediction_ratio,
        #     "e2same0",
        #     lwidth=100,
        #     msize=0,
        #     fcolor=ROOT.kBlack,
        #     fstyle=3004,
        # )
        # CMS.cmsDraw(ratio, "P", mcolor=ROOT.kBlack)
        # ref_line = ROOT.TLine(x_low, 1, x_high, 1)
        # CMS.cmsDrawLine(ref_line, lcolor=ROOT.kBlack, lstyle=ROOT.kDotted)
        # ratio_from_canvas = CMS.GetcmsCanvasHist(canvas.GetPad(2))
        # # ROOT.gPad.SetLogy()
        # ratio_from_canvas.GetYaxis().SetRangeUser(0.0, 100.0)

    # Save the canvas in pdf and png formats
    canvas.cd(0).RedrawAxis()
    canvas.cd(1).RedrawAxis()
    plot_name = (
        f"{output_dir}{hist_name.replace('h_', '')}"
        if not log else
        f"{output_dir}/log/{hist_name.replace('h_', '')}"
    )
    CMS.SaveCanvas(canvas, f"{plot_name}.png", False) # The False is needed not to close the canvas
    CMS.SaveCanvas(canvas, f"{plot_name}.pdf", False)
    print()

def create_output_dir(output_dir, log):
    """
    Create the output directory if it does not exist.

    Parameters:
    - output_dir: The directory where the output files will be saved.
    - log: Boolean indicating whether a log directory should be created.
    """
    os.makedirs(output_dir, exist_ok=True)
    if log:
        os.makedirs(os.path.join(output_dir, 'log'), exist_ok=True)

def read_csv(csv_file):
    """
    Open and read a csv file containing the name and the range of the variables to be plotted. 
    Fill in a list of histogram names.

    Parameters:
    - csv_file: The csv file containing variable names and binning for the respective histograms.
    """
    with open(csv_file, mode='r') as f:
        csv_reader = csv.reader(f)
        if "systs" not in csv_file:
            hist_list = [line for line in csv_reader if not line[0]=='Variable']
            hist_list = [[f"h_{hist[0]}", hist[2], hist[3]] for hist in hist_list]
        else:
            hist_list = [line[0] for line in csv_reader if not line[0]=='Variable']
    return hist_list

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stack TH1D histograms from multiple ROOT files.")
    parser.add_argument(
        "--input_dir",
        type=str,
        required=True,
        help="Input directory, where ROOT files are located.",
    )
    parser.add_argument(
        "--hist_name",
        required=False,
        help="Name of the histograms to stack.",
    )
    parser.add_argument(
        "--input_csv",
        type=str,
        required=True,
        help="The csv file to read variables and ranges from.",
    )
    parser.add_argument(
        "--systs_csv",
        type=str,
        default="configs/systs.csv",
        required=False,
        help="The csv file to read a list of systematics from.",
    )
    parser.add_argument(
        "--output_dir",
        type=str, required=True,
        help="Output directory for the TCanvas containing THStacks.",
    )
    parser.add_argument(
        "--sonly",
        nargs="?",
        const=1,
        type=bool,
        default=False,
        required=False,
        help="Decide whether to plot only the signal.",
    )
    parser.add_argument(
        "--sig_norm",
        nargs="?",
        const=1,
        type=int,
        default=1,
        required=False,
        help="Signal normalization.",
    )
    parser.add_argument(
        "--log",
        nargs="?",
        const=1,
        type=bool,
        default=False,
        required=False,
        help="Decide whether to use log scale on the Y-axis.",
    )
    parser.add_argument(
        "--blind",
        nargs="?",
        const=1,
        type=bool,
        default=False,
        required=False,
        help="Decide whether to blind the data in a certain histogram.",
    )
    parser.add_argument(
        "--verbosity",
        type=int,
        default=0,
        required=False,
        help="The verbosity, for debugging.",
    )

    args = parser.parse_args()

    # Set plotting details
    CMS.SetExtraText("Work in progress")
    CMS.SetLumi("110")
    # CMS.SetLumi("220")
    CMS.SetEnergy("13.6")

    # Get input files from the input_dir
    input_files = glob.glob(f"{args.input_dir}*.root")
    # Sort the input files to ensure consistent ordering
    input_files.sort()

    # Create the output directory if it does not exist
    create_output_dir(args.output_dir, args.log)

    # Plot either all histograms from the csv file or a single histogram
    syst_list = read_csv(args.systs_csv)
    if not args.hist_name:
        hist_list = read_csv(args.input_csv)
        for hist_info in hist_list:
            stack_histograms(
                input_files,
                hist_info[0],
                syst_list,
                args.output_dir,
                args.sonly,
                args.sig_norm,
                args.log,
                args.blind,
                args.verbosity,
                float(hist_info[1]),
                float(hist_info[2]),
            )
    else:
        stack_histograms(
            input_files,
            args.hist_name,
            syst_list,
            args.output_dir,
            args.sonly,
            args.sig_norm,
            args.log,
            args.blind,
            args.verbosity,
        )
