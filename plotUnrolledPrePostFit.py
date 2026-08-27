import ROOT
import argparse
import glob
import math
import csv
import os
import cmsstyle as CMS

ROOT.TH1.SetDefaultSumw2(True)
ROOT.gROOT.SetBatch(True)

BLOCK_GAP_BINS = 1

HIST_ORDER = [
    "h_score_tt_Wcb",
    "h_fscore_ttLF",
    "h_fscore_ttbb",
    "h_fscore_tt2b",
    "h_fscore_ttbj",
    "h_fscore_ttcc",
    "h_fscore_tt2c",
    "h_fscore_ttcj",
]

HIST_LABELS = {
    "h_score_tt_Wcb": "Wcb",
    "h_fscore_ttLF": "ttLF",
    "h_fscore_ttbb": "ttbb",
    "h_fscore_tt2b": "tt2b",
    "h_fscore_ttbj": "ttbj",
    "h_fscore_ttcc": "ttcc",
    "h_fscore_tt2c": "tt2c",
    "h_fscore_ttcj": "ttcj",
}

CATEGORY_ORDER = {
    "h_score_tt_Wcb": "Vcb_catWcb_SR",
    "h_fscore_ttLF": "Vcb_catLF_CR",
    "h_fscore_ttbb": "Vcb_catBB_CR",
    "h_fscore_tt2b": "Vcb_cat2B_CR",
    "h_fscore_ttbj": "Vcb_catBJ_CR",
    "h_fscore_ttcc": "Vcb_catCC_CR",
    "h_fscore_tt2c": "Vcb_cat2C_CR",
    "h_fscore_ttcj": "Vcb_catCJ_CR",
}

OTHERS_COMPONENTS = {
    "wjets",
    "ttHbb",
    "ttHcc",
    "ttW",
    "ttZ",
    "diboson",
    "singletop",
}

IGNORE_PROCESSES = {"TotalBkg", "TotalSig"}

DPS_MERGE_MAP = {
    "ttbb-dps": "ttbb",
    "tt2b-dps": "tt2b",
    "ttbj-dps": "ttbj",
}


def _load_histograms(root_path, hist_names):
    root_file = ROOT.TFile.Open(root_path)
    if not root_file or root_file.IsZombie():
        raise FileNotFoundError(f"Could not open file: {root_path}")

    hists = {}
    for name in hist_names:
        hist = root_file.Get(name)
        if not hist or not isinstance(hist, ROOT.TH1):
            root_file.Close()
            raise ValueError(f"Histogram '{name}' not found in file '{root_path}'.")
        hist_clone = hist.Clone()
        hist_clone.SetDirectory(0)
        hists[name] = hist_clone

    root_file.Close()
    return hists


def _clone_and_detach(hist, name):
    out = hist.Clone(name)
    out.SetDirectory(0)
    return out


def _zero_like(hist, name):
    out = _clone_and_detach(hist, name)
    out.Reset("ICES")
    return out


def _graph_to_hist(graph, name, ref_hist):
    """Convert a TGraphAsymmErrors to a TH1D by extracting points and creating a new histogram."""
    if not isinstance(graph, ROOT.TGraphAsymmErrors):
        return None
    
    n_points = graph.GetN()
    if n_points == 0:
        return None
    
    import array as arr
    
    # Create a new histogram matching the reference structure
    hist = ref_hist.Clone(name)
    hist.SetDirectory(0)  # Detach from file
    hist.Reset("ICES")
    hist.Sumw2()
    
    # Fill histogram from graph points
    for i in range(n_points):
        x = arr.array('d', [0])
        y = arr.array('d', [0])
        graph.GetPoint(i, x, y)
        
        # Find bin and fill
        bin_idx = hist.FindBin(x[0])
        
        # Get asymmetric errors - use average
        eyl = graph.GetErrorYlow(i)
        eyh = graph.GetErrorYhigh(i)
        err = (eyl + eyh) / 2.0
        
        hist.SetBinContent(bin_idx, y[0])
        hist.SetBinError(bin_idx, err)
    
    return hist


def _get_all_hists_in_dir(directory):
    out = {}
    for key in directory.GetListOfKeys():
        obj = key.ReadObj()
        if not isinstance(obj, ROOT.TH1):
            continue
        out[key.GetName()] = _clone_and_detach(obj, f"{directory.GetName()}_{key.GetName()}_clone")
    return out


def _load_prefit_postfit(root_path, postfit=False):
    root_file = ROOT.TFile.Open(root_path)
    if not root_file or root_file.IsZombie():
        raise FileNotFoundError(f"Could not open file: {root_path}")

    # Support both legacy layout (<category>_prefit/postfit) and fitDiagnostics
    # layout (shapes_prefit/shapes_fit_s with per-category subdirectories).
    fits_dir_prefit = root_file.Get("shapes_prefit")
    fits_dir_postfit = root_file.Get("shapes_fit_s")
    is_fitdiagnostics = isinstance(fits_dir_prefit, ROOT.TDirectory)

    process_blocks = {}
    data_blocks = {}
    total_procs_blocks = {}
    ref_hists = {}

    for block_name in HIST_ORDER:
        category = CATEGORY_ORDER[block_name]
        if is_fitdiagnostics:
            topdir = fits_dir_postfit if postfit else fits_dir_prefit
            if not topdir or not isinstance(topdir, ROOT.TDirectory):
                root_file.Close()
                missing = "shapes_fit_s" if postfit else "shapes_prefit"
                raise ValueError(f"Directory '{missing}' not found in '{root_path}'.")
            directory = topdir.Get(category)
            dir_name = f"{topdir.GetName()}/{category}"
        else:
            stage = "postfit" if postfit else "prefit"
            dir_name = f"{category}_{stage}"
            directory = root_file.Get(dir_name)

        if not directory or not isinstance(directory, ROOT.TDirectory):
            root_file.Close()
            raise ValueError(f"Directory '{dir_name}' not found in '{root_path}'.")

        hists_in_dir = _get_all_hists_in_dir(directory)

        total_name = "total" if "total" in hists_in_dir else "TotalProcs"
        
        # Look for data: first as histogram, then as TGraphAsymmErrors
        data_name = None
        if "data" in hists_in_dir:
            data_name = "data"
        elif "data_obs" in hists_in_dir:
            data_name = "data_obs"
        else:
            # Try to find as TGraphAsymmErrors in directory
            data_graph = directory.Get("data")
            if isinstance(data_graph, ROOT.TGraphAsymmErrors):
                data_name = "data"
            else:
                data_graph = directory.Get("data_obs")
                if isinstance(data_graph, ROOT.TGraphAsymmErrors):
                    data_name = "data_obs"
        
        if total_name not in hists_in_dir:
            root_file.Close()
            raise ValueError(f"Histogram '{total_name}' not found in '{dir_name}' of '{root_path}'.")

        ref_hists[block_name] = _clone_and_detach(hists_in_dir[total_name], f"ref_{block_name}")
        total_procs_blocks[block_name] = _clone_and_detach(hists_in_dir[total_name], f"totalprocs_{block_name}")

        if data_name is not None:
            if data_name in hists_in_dir:
                data_blocks[block_name] = _clone_and_detach(hists_in_dir[data_name], f"data_{block_name}")
                print(f"  Found data histogram '{data_name}' for block '{block_name}'")
            else:
                # Must be TGraphAsymmErrors
                graph = directory.Get(data_name)
                if isinstance(graph, ROOT.TGraphAsymmErrors):
                    data_hist_from_graph = _graph_to_hist(graph, f"data_{block_name}", ref_hists[block_name])
                    if data_hist_from_graph:
                        data_blocks[block_name] = data_hist_from_graph
                        print(f"  Converted TGraphAsymmErrors '{data_name}' to histogram for block '{block_name}'")
                    else:
                        print(f"  WARNING: TGraphAsymmErrors '{data_name}' is empty in block '{block_name}'")
        else:
            print(f"  WARNING: No data histogram or graph found in block '{block_name}'")

        for proc_name, hist in hists_in_dir.items():
            if proc_name in IGNORE_PROCESSES or proc_name in ["TotalProcs", "data_obs", "total", "data", "total_signal", "total_background", "total_covar"]:
                continue

            merged_proc = DPS_MERGE_MAP.get(proc_name, proc_name)
            target_proc = "others" if merged_proc in OTHERS_COMPONENTS else merged_proc
            if target_proc not in process_blocks:
                process_blocks[target_proc] = {}
            if block_name not in process_blocks[target_proc]:
                process_blocks[target_proc][block_name] = _zero_like(ref_hists[block_name], f"{target_proc}_{block_name}")
            process_blocks[target_proc][block_name].Add(hist)

    # Fill missing blocks with zero-content hists to keep unrolling consistent.
    for proc_name in process_blocks:
        for block_name in HIST_ORDER:
            if block_name not in process_blocks[proc_name]:
                process_blocks[proc_name][block_name] = _zero_like(ref_hists[block_name], f"{proc_name}_{block_name}_empty")

    for block_name in HIST_ORDER:
        if block_name not in data_blocks:
            data_blocks[block_name] = _zero_like(ref_hists[block_name], f"data_{block_name}_empty")

    root_file.Close()
    return process_blocks, data_blocks, total_procs_blocks, ref_hists


def _infer_process_name(root_path):
    base = os.path.splitext(os.path.basename(root_path))[0]
    if base.startswith("h_"):
        base = base[2:]
    if base.startswith("ttbar-powheg_"):
        base = base.split("_")[-1]
    return base


def _is_data(process_name):
    return "data" in process_name.lower()


def _is_signal(process_name):
    return "vcb" in process_name.lower()


def _build_kept_bins_map(total_procs_blocks, data_blocks, eps=1e-12):
    kept_bins = {}
    for name in HIST_ORDER:
        total_hist = total_procs_blocks[name]
        data_hist = data_blocks.get(name)  # Use .get() to handle None
        nbins = total_hist.GetNbinsX()
        kept_bins[name] = []
        for i in range(1, nbins + 1):
            total_empty = abs(total_hist.GetBinContent(i)) < eps
            data_empty = True  # Default to empty if data_hist is None
            if data_hist is not None:
                data_empty = abs(data_hist.GetBinContent(i)) < eps
            if not (total_empty and data_empty):
                kept_bins[name].append(i)
    return kept_bins


def _total_bins(kept_bins_map):
    active_blocks = [name for name in HIST_ORDER if len(kept_bins_map[name]) > 0]
    total_content_bins = sum(len(kept_bins_map[name]) for name in active_blocks)
    total_gap_bins = BLOCK_GAP_BINS * max(0, len(active_blocks) - 1)
    return total_content_bins + total_gap_bins


def _block_edges(kept_bins_map):
    edges = [0]
    centers = []
    active_blocks = []
    ranges = []
    running = 0
    names = [name for name in HIST_ORDER if len(kept_bins_map[name]) > 0]
    for idx, name in enumerate(names):
        n_kept = len(kept_bins_map[name])
        start = running
        running += n_kept
        end = running
        edges.append(running)
        centers.append((start + end) / 2.0)
        active_blocks.append(name)
        ranges.append((start, end))
        if idx < len(names) - 1:
            running += BLOCK_GAP_BINS
    return edges, centers, active_blocks, ranges


def _validate_binning(ref_histograms, test_histograms, root_path):
    for name in HIST_ORDER:
        ref_bins = ref_histograms[name].GetNbinsX()
        test_bins = test_histograms[name].GetNbinsX()
        if ref_bins != test_bins:
            raise ValueError(
                f"Histogram '{name}' has {test_bins} bins in '{root_path}', expected {ref_bins}."
            )


def _make_unrolled_hist(histograms, total_bins, name, kept_bins_map):
    unrolled = ROOT.TH1D(name, name, total_bins, 0, total_bins)
    unrolled.Sumw2()

    active_blocks = [hist_name for hist_name in HIST_ORDER if len(kept_bins_map[hist_name]) > 0]
    offset = 0
    for idx, hist_name in enumerate(active_blocks):
        hist = histograms[hist_name]
        for i, in_bin in enumerate(kept_bins_map[hist_name], start=1):
            out_bin = offset + i
            unrolled.SetBinContent(out_bin, hist.GetBinContent(in_bin))
            unrolled.SetBinError(out_bin, hist.GetBinError(in_bin))
        offset += len(kept_bins_map[hist_name])
        if idx < len(active_blocks) - 1:
            offset += BLOCK_GAP_BINS

    return unrolled


def plot_unrolled(input_root, output_dir, sig_norm=1.0, log=False, blind=False, show_blocks=True, postfit=False):
    stack = ROOT.THStack("stack", "Unrolled stack")
    phys_process = {}

    process_blocks, data_blocks, total_procs_blocks, ref_hists = _load_prefit_postfit(input_root, postfit=postfit)
    kept_bins_map = _build_kept_bins_map(total_procs_blocks, data_blocks)
    total_bins = _total_bins(kept_bins_map)
    block_edges, block_centers, active_blocks, block_ranges = _block_edges(kept_bins_map)
    if total_bins <= 0:
        raise ValueError("All bins are empty in both TotalProcs and data_obs after pruning.")
    data_hist = None
    sig_line = None
    total_mc_hist = None
    block_guides = []

    print(f"Reading file: {input_root}")

    data_hist = _make_unrolled_hist(data_blocks, total_bins, "data_unrolled", kept_bins_map)
    total_mc_hist = _make_unrolled_hist(total_procs_blocks, total_bins, "totalprocs_unrolled", kept_bins_map)

    print(f"\nData histogram created:")
    print(f"  Total bins in unrolled histogram: {total_bins}")
    print(f"  Data histogram integral (before blind): {data_hist.Integral()}")

    if blind:
        blind_bins = len(kept_bins_map[HIST_ORDER[0]])
        for i in range(1, blind_bins + 1):
            data_hist.SetBinContent(i, 0.0)
            data_hist.SetBinError(i, 0.0)
        print(f"  Data histogram integral (after blind): {data_hist.Integral()}")
        print(f"  Blinded bins 1-{blind_bins} (first block)")

    for process_name, block_hists in process_blocks.items():
        unrolled = _make_unrolled_hist(block_hists, total_bins, f"{process_name}_unrolled", kept_bins_map)
        if _is_signal(process_name):
            sig_line = unrolled.Clone("sig_line")
            sig_line.Scale(sig_norm)
            sig_line.SetDirectory(0)
            sig_line.SetLineStyle(ROOT.kDashed)
            sig_line.SetLineWidth(2)
            sig_line.SetLineColor(ROOT.kRed)
            sig_line.SetFillStyle(0)
            sig_line.SetFillColor(0)
            sig_line.SetMarkerSize(0)
            for i in range(1, sig_line.GetNbinsX() + 1):
                sig_line.SetBinError(i, 0.0)

        phys_process[process_name] = unrolled

    x_low, x_high = 0, total_bins

    print(f"Saving stacked histograms as: {output_dir}unrolled.pdf/.png")
    canvas = CMS.cmsDiCanvas("canvas", x_low, x_high, 0, 1, 0.7, 1.3, "Unrolled score distributions", "Events", "Data/MC", square=CMS.kRectangular, extraSpace=0.01, iPos=11)
    canvas.cd(1)
    legend = CMS.cmsLeg(0.55, 0.5, 0.85, 0.87, textSize=0.04, columns=2)
    if data_hist is not None:
        legend.AddEntry(data_hist, "Data", "pe")
    if sig_line is not None:
        legend.AddEntry(sig_line, f"W#rightarrow cb #times {sig_norm:.0f}", "l")

    CMS.cmsDrawStack(stack, legend, phys_process)

    if sig_line is not None:
        sig_line.Draw("HIST SAME")
    if data_hist is not None:
        CMS.cmsDraw(data_hist, "E1X0", mcolor=ROOT.kBlack, msize=0.7)

    hist_from_canvas = CMS.GetcmsCanvasHist(canvas.GetPad(1))
    stack_max = stack.GetHistogram().GetMaximum() if stack.GetHistogram() else 0
    data_max = data_hist.GetMaximum() if data_hist else 0
    y_max = max(stack_max, data_max) * 2.0 if max(stack_max, data_max) > 0 else 1.0
    hist_from_canvas.GetYaxis().SetRangeUser(0.01, y_max)
    hist_from_canvas.GetYaxis().SetMaxDigits(3)
    if log:
        ROOT.gPad.SetLogy()
        max_val = max(stack_max, data_max) if max(stack_max, data_max) > 0 else 1.0
        hist_from_canvas.GetYaxis().SetRangeUser(1, max_val * 1000)
        #hist_from_canvas.GetYaxis().SetRangeUser(0.1, max_val * 100000)

    if show_blocks and block_edges is not None:
        y_top = hist_from_canvas.GetYaxis().GetXmax()
        for edge in block_edges[1:-1]:
            line = ROOT.TLine(edge, 0, edge, y_top)
            line.SetLineStyle(ROOT.kDashed)
            line.SetLineColor(ROOT.kBlue + 2)
            line.Draw("same")
            block_guides.append(line)

        pad1 = canvas.GetPad(1)
        x_span = (x_high - x_low) if (x_high - x_low) > 0 else 1.0
        x_left_ndc = pad1.GetLeftMargin()
        x_right_ndc = 1.0 - pad1.GetRightMargin()
        y_text_ndc = pad1.GetBottomMargin() + 0.035

        latex = ROOT.TLatex()
        latex.SetTextAlign(22)
        latex.SetTextSize(0.03)
        for center, name in zip(block_centers, active_blocks):
            label = HIST_LABELS.get(name, name.replace("h_", ""))
            frac_center = (center - x_low) / x_span
            x_center_ndc = x_left_ndc + frac_center * (x_right_ndc - x_left_ndc)
            latex.DrawLatexNDC(x_center_ndc, y_text_ndc, label)
        block_guides.append(latex)



    if data_hist is not None:
        bkg_hist = stack.GetStack().Last()
        # Keep the uncertainty band centered on the actually stacked MC sum.
        # If available, use TotalProcs uncertainties as band errors.
        err_hist = bkg_hist.Clone("total_mc_unc")
        if total_mc_hist is not None:
            for i in range(1, err_hist.GetNbinsX() + 1):
                err_hist.SetBinError(i, total_mc_hist.GetBinError(i))
        CMS.cmsDraw(err_hist, "e2same0", lcolor=335, lwidth=2, msize=0, fcolor=ROOT.kBlack, fstyle=3004)
        legend.AddEntry(err_hist, "Stat. + Syst. Unc.", "f")

        canvas.cd(2)
        denom_hist = bkg_hist

        ratio = data_hist.Clone("ratio")
        ratio.Divide(denom_hist)

        for i in range(1, ratio.GetNbinsX() + 1):
            denom = denom_hist.GetBinContent(i)
            if denom > 0:
                ratio.SetBinError(i, math.sqrt(data_hist.GetBinContent(i)) / denom) #Here assume no MC uncertainty
            else:
                ratio.SetBinContent(i, 0.0)
                ratio.SetBinError(i, 0.0)

        ratio_unc = denom_hist.Clone("ratio_mc_unc")
        for i in range(1, ratio_unc.GetNbinsX() + 1):
            mc = denom_hist.GetBinContent(i)
            mc_err = total_mc_hist.GetBinError(i) if total_mc_hist is not None else denom_hist.GetBinError(i)
            ratio_unc.SetBinContent(i, 1.0 if mc > 0 else 0.0)
            ratio_unc.SetBinError(i, (mc_err / mc) if mc > 0 else 0.0)
        CMS.cmsDraw(ratio_unc, "e2same0", lcolor=335, lwidth=1, msize=0, fcolor=ROOT.kBlack, fstyle=3004)

        CMS.cmsDraw(ratio, "E1X0", mcolor=ROOT.kBlack, msize=0.7)
        ref_line = ROOT.TLine(x_low, 1, x_high, 1)
        CMS.cmsDrawLine(ref_line, lcolor=ROOT.kBlack, lstyle=ROOT.kDotted)
        ratio_from_canvas = CMS.GetcmsCanvasHist(canvas.GetPad(2))
        ratio_from_canvas.GetYaxis().SetRangeUser(0.8, 1.2)

    plot_name = f"{output_dir}unrolled" if not log else f"{output_dir}/log/unrolled"
    CMS.SaveCanvas(canvas, f"{plot_name}.png", False)
    CMS.SaveCanvas(canvas, f"{plot_name}.pdf", False)
    print()


def _expand_inputs(input_files, input_pattern):
    if input_files:
        return input_files
    if input_pattern:
        return sorted(glob.glob(input_pattern))
    return []


def main():
    parser = argparse.ArgumentParser(description="Make unrolled plots from ROOT files.")
    parser.add_argument("--input-file", type=str, required=True, help="Input ROOT file with prefit/postfit directories.")
    parser.add_argument("--output-dir", required=True, help="Output directory for plots")
    parser.add_argument("--sig-norm", type=float, default=1.0, help="Signal normalization factor")
    parser.add_argument("--log", action="store_true", help="Use log scale on Y axis")
    parser.add_argument("--blind", action="store_true", help="Blind data histogram")
    parser.add_argument("--no-blocks", action="store_true", help="Disable block separators/labels")
    parser.add_argument("--postfit", action="store_true", default=False, help="Plot postfit distributions")
    parser.add_argument("--gap-bins", type=int, default=1, help="Number of empty bins between unrolled blocks")
    args = parser.parse_args()

    if args.gap_bins < 0:
        raise ValueError("--gap-bins must be >= 0")

    global BLOCK_GAP_BINS
    BLOCK_GAP_BINS = args.gap_bins

    # Set plotting details
    CMS.SetExtraText("Preliminary")
    CMS.SetLumi("110")
    #CMS.SetLumi("220")
    CMS.SetEnergy("13.6")

    os.makedirs(args.output_dir, exist_ok=True)
    if args.log:
        os.makedirs(os.path.join(args.output_dir, "log"), exist_ok=True)

    plot_unrolled(
        args.input_file,
        args.output_dir,
        sig_norm=args.sig_norm,
        log=args.log,
        blind=args.blind,
        show_blocks=not args.no_blocks,
        postfit=args.postfit,
    )


if __name__ == "__main__":
    main()