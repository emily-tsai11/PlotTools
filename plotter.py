import ROOT
import argparse
import glob
import copy
import cmsstyle as CMS

def stack_histograms(input_files, hist_name, output_dir, sig_norm):
    """
    Reads TH1Ds with the same name from multiple files, stacks them in a THStack, and saves the result.

    Parameters:
    - input_dir: Input directory, where ROOT files are located.
    - hist_name: Name of the histograms to stack.
    - output_dir: Output directory for the TCanvas containing THStacks.
    - sig_norm: Normalization of the signal.
    """
    # Create a THStack and a dictionary {process name : histogram} to feed to the CMS plotting
    stack = ROOT.THStack("stack", f"Stack of {hist_name}")
    phys_process = dict()

    # Define X-axis boundaries for the stack
    x_low, x_high = 0., 1.

    # Create a histogram for the signal to be added separately from the stack
    sig_hist = ROOT.TH1D()

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
        x_low = hist_clone.GetBinLowEdge(1)
        x_high = hist_clone.GetBinLowEdge(hist_clone.GetNbinsX() + 1)

        # Treat the signal sample separately (it will be added as a dashed line to the plots)
        if "Wcb" in infile:
            print(f"W->cb histogram will be added to the plot separately")
            sig_hist = hist_clone
            sig_hist *= sig_norm
            continue # Avoid adding W->cb to the stack

        # Fill dictionary {process name : histogram} to feed to the CMS plotting
        phys_process_name = (infile.split('_')[-1]).replace('.root','')
        phys_process[phys_process_name] = hist_clone

        # Close the file
        root_file.Close()

    # Save the stack in a canvas and add a legend
    print(f"Saving stacked histograms as: {output_dir}{hist_name.replace('h_','')}.pdf")
    canvas = CMS.cmsCanvas('canvas', x_low, x_high, 0, 1, hist_name.replace('h_',''), 'Events', square = CMS.kSquare, extraSpace=0.01, iPos=11)
    legend = CMS.cmsLeg(0.65,0.5,0.85,0.9, textSize=0.04) # Needs to be defined after the cmsCanvas or it won't be plotted
    legend.AddEntry(sig_hist, f"W->cb * {sig_norm}", "l")
    CMS.cmsDrawStack(stack,legend,phys_process)
    CMS.cmsDraw(sig_hist,"same", lstyle = 2, msize = 0, lcolor = ROOT.kRed, lwidth = 4)

    # Set Y-axis range based on maximum value of stacked histograms
    hdf = CMS.GetcmsCanvasHist(canvas)
    hdf.GetYaxis().SetRangeUser(0,stack.GetHistogram().GetMaximum()*1.2)

    # Add error bars
    h_err_temp = stack.GetStack().Last()
    h_err = h_err_temp.Clone()

    # Draw and save
    CMS.cmsDraw(h_err, "e2same0", lcolor = 335, lwidth = 1, msize = 0, fcolor = ROOT.kBlack, fstyle = 3004) 
    CMS.SaveCanvas(canvas,f"{output_dir}{hist_name.replace('h_','')}.pdf")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stack TH1D histograms from multiple ROOT files.")
    parser.add_argument("--input_dir", type=str, required=True, help="Input directory, where ROOT files are located.")
    parser.add_argument("--hist_name", required=True, help="Name of the histograms to stack.")
    parser.add_argument("--output_dir", type=str, required=True, help="Output directory for the TCanvas containing THStacks.")
    parser.add_argument("--sig_norm", nargs="?", const=1, type=int, default=1, required=False, help="Signal normalization.")

    args = parser.parse_args()

    # Set plotting details
    CMS.SetExtraText("Work in progress")
    CMS.SetLumi("59.83")

    # Get input files from the input_dir
    input_files = glob.glob(f"{args.input_dir}*.root")

    stack_histograms(input_files, args.hist_name, args.output_dir, args.sig_norm)
