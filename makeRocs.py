import ROOT
import argparse
import glob
import math
import os
import cmsstyle as CMS

def estimate_cut(input_files, hist_name):
    """
    Reads TH1Ds with the same name from multiple files, stacks them in a THStack and estimate the signal and background contributions.

    Parameters:
    - input_dir: Input directory, where ROOT files are located.
    - hist_name: Name of the histograms to stack.
    """
    # Create a THStack and a dictionary {process name : histogram} to feed to the CMS plotting
    stack = ROOT.THStack("stack", f"Stack of {hist_name}")

    # Create a TGraph for the ROC curve
    roc_curve = ROOT.TGraph()

    # Create a TH2D for the signal efficiency as a function of the cut
    #eff_cut = ROOT.TH2D("eff_cut", "Signal efficiency as a function of the cut", 20, 0., 1., 20, 0., 1.)

    # Create a histogram for the signal and the collision data to be added separately from the stack
    sig_hist = ROOT.TH1D("sig_hist", "Signal Histogram", 100, 0., 1.)


    # Open input files and retrieve histograms
    for infile in input_files:

        print(f"Reading file: {infile}")

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

        # Assign X-axis boundaries for the stack
        #x_low = hist_clone.GetBinLowEdge(1)
        #x_high = hist_clone.GetBinLowEdge(hist_clone.GetNbinsX() + 1)

        if "Wcb" in infile:
            #print(f"W->cb histogram will be plotted separately")
            sig_hist = hist.Clone()
            sig_hist.SetDirectory(0)
        if "Data" in infile: continue

        # Add the histogram to the stack
        stack.Add(hist_clone)

        # Close the file
        root_file.Close()

    sum_of_backgrounds = stack.GetStack().Last().Clone()
    sum_of_backgrounds.SetDirectory(0)

    #canvas = ROOT.TCanvas("canvas", "canvas", 800, 600)
    #sum_of_backgrounds.Draw("hist")
    #canvas.SaveAs("stack.png")

    # Scan sum_of_backgrounds with a granularity of 0.1 and calculate the ratio of the integral on the right of the cut to the total integral
    cut = 0.01
    while cut < 1.:
        bkg_integral_right = sum_of_backgrounds.Integral(sum_of_backgrounds.FindBin(cut), sum_of_backgrounds.GetNbinsX())
        bkg_integral_total = sum_of_backgrounds.Integral()
        bkg_ratio = bkg_integral_right / bkg_integral_total
        #print(f"Cut: {cut:.2f}, Bkg Ratio: {bkg_ratio:.3f}")
        # Now find the 
        #if bkg_ratio < 0.01: break
        
        # Find corresponding signal efficiency
        sig_integral_right = sig_hist.Integral(sig_hist.FindBin(cut), sig_hist.GetNbinsX())
        sig_integral_total = sig_hist.Integral()
        sig_ratio = sig_integral_right / sig_integral_total
        #print(f"Cut: {cut:.2f}, Sig Ratio: {sig_ratio:.3f}")

        roc_curve.SetPoint(roc_curve.GetN(), sig_ratio, 1.-bkg_ratio)
        cut += 0.01

    return roc_curve

def make_rocs(input_files, hist_name, sig_name, bkg_name):
    """
    Reads TH1Ds with the same name from multiple files, stacks them in a THStack and estimate the signal and background contributions.

    Parameters:
    - input_dir: Input directory, where ROOT files are located.
    - hist_name: Name of the histogram to consider.
    - sig_name: Name of the signal process
    - bkg_name: Name of the background process.
    """
    # Create a THStack
    stack = ROOT.THStack("stack", f"Stack of {hist_name}")

    # Create a TGraph for the ROC curve
    roc_curve = ROOT.TGraph()

    # Create a TH2D for the signal efficiency as a function of the cut
    #eff_cut = ROOT.TH2D("eff_cut", "Signal efficiency as a function of the cut", 20, 0., 1., 20, 0., 1.)

    # Create a histogram for the signal and the collision data to be added separately from the stack
    sig_hist = ROOT.TH1D("sig_hist", "Signal Histogram", 100, 0., 1.)
    bkg_hist = ROOT.TH1D("bkg_hist", "Background Histogram", 100, 0., 1.)


    # Open input files and retrieve histograms
    for infile in input_files:

        print(f"Reading file: {infile}")

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

        if sig_name in infile:
            sig_hist = hist.Clone()
            sig_hist.SetDirectory(0)
        elif bkg_name in infile:
            bkg_hist = hist.Clone()
            bkg_hist.SetDirectory(0)

        # Close the file
        root_file.Close()

    # Scan bkg_hist with a granularity of 0.1 and calculate the ratio of the integral on the right of the cut to the total integral
    cut = 0.01
    while cut < 1.:
        bkg_integral_right = bkg_hist.Integral(bkg_hist.FindBin(cut), bkg_hist.GetNbinsX())
        bkg_integral_total = bkg_hist.Integral()
        bkg_ratio = bkg_integral_right / bkg_integral_total
        #print(f"Cut: {cut:.2f}, Bkg Ratio: {bkg_ratio:.3f}")
        # Now find the 
        #if bkg_ratio < 0.01: break
        
        # Find corresponding signal efficiency
        sig_integral_right = sig_hist.Integral(sig_hist.FindBin(cut), sig_hist.GetNbinsX())
        sig_integral_total = sig_hist.Integral()
        sig_ratio = sig_integral_right / sig_integral_total
        #print(f"Cut: {cut:.2f}, Sig Ratio: {sig_ratio:.3f}")

        roc_curve.SetPoint(roc_curve.GetN(), sig_ratio, 1.-bkg_ratio)
        cut += 0.01


    # Calculate the area under the ROC curve
    area = 0.0
    n_points = roc_curve.GetN()
    print("n_points:", n_points)
    for i in range(1, n_points):
        x1 = roc_curve.GetPointX(i - 1)
        y1 = roc_curve.GetPointY(i - 1)
        x2 = roc_curve.GetPointX(i)
        y2 = roc_curve.GetPointY(i)
        #print(f"x2 - x1: {x2} - {x1}, y2 + y1: {y2} + {y1}")
        area += - ((x2 - x1) * (y2 + y1) / 2.0)
    print(f"Area under the ROC curve for {sig_name} vs {bkg_name}: {area:.3f}")
    return roc_curve, area

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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stack TH1D histograms from multiple ROOT files.")
    parser.add_argument("--input_dir", type=str, required=True, help="Input directory, where ROOT files are located.")
    parser.add_argument("--output_dir", type=str, required=True, help="Output directory, where plots will be stored.")
    parser.add_argument("--hist_name", type=str, required=False, help="Name of the histogram to read.")
    parser.add_argument("--sig_name", type=str, required=False, help="Name of the signal process.")
    parser.add_argument("--bkg_names", nargs='+', required=False, help="List of background process names.")

    args = parser.parse_args()

    # Set plotting details
    CMS.SetExtraText("Work in progress")
    CMS.SetLumi(59.83)

    # Get input files from the input_dir
    input_files = glob.glob(f"{args.input_dir}*.root")

    # Create the output directory if it does not exist
    # create_output_dir(args.output_dir)

    # Set up a TLegend for the canvas
    legend = ROOT.TLegend(0.15, 0.15, 0.35, 0.35)
    legend.SetBorderSize(0)
    legend.SetFillColor(0)
    legend.SetFillStyle(0)
    legend.SetTextFont(42)
    legend.SetTextSize(0.03)

    hist_name = args.hist_name
    sig_name = args.sig_name
    bkg_names = args.bkg_names
    print(f"Signal name: {sig_name}, Background names: {bkg_names}")

    # Plot either all histograms from the csv file or a single histogram
    rocs = []
    for bkg_name in args.bkg_names:
        roc, area = make_rocs(input_files, hist_name, sig_name, bkg_name)
        rocs.append(roc)
        legend.AddEntry(roc, f"Wcb vs {bkg_name.replace('h_','')} -- AUC: {area:.3f}", "L")

    # Save the ROC curves
    canvas_roc = ROOT.TCanvas("canvas_roc", "ROC Curves", 800, 600)
    ROOT.gPad.SetLogy()
    for i, roc in enumerate(rocs):
        if i == 0:
            roc.SetLineColor(ROOT.kRed)
            roc.GetYaxis().SetTitle("1 - Background efficiency")
            roc.GetXaxis().SetTitle("Signal efficiency")
            roc.Draw("AL")
        else:
            roc.SetLineColor(i+2)
            roc.Draw("L")
    legend.Draw("SAME")
    canvas_roc.SaveAs(f"{args.output_dir}/roc_curve_tagger_performance.pdf")
    canvas_roc.SaveAs(f"{args.output_dir}/roc_curve_tagger_performance.png")
