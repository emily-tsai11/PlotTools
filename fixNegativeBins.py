from __future__ import print_function
import argparse
import os
import ROOT
ROOT.PyConfig.IgnoreCommandLineOptions = True

EPSILON = 1e-6


def fixNegativeBins(filename, keep_original=True):
    origfile = filename.replace('.root', '.orig.root')
    os.rename(filename, origfile)
    fout = ROOT.TFile(filename, 'RECREATE')
    f = ROOT.TFile(origfile, 'READ')
    for d in f.GetListOfKeys():
        dirname = d.GetName()
        dir = d.ReadObj()
        if not dir.IsA().InheritsFrom(ROOT.TDirectory.Class()):
            continue
        outdir = fout.mkdir(dirname)
        for e in dir.GetListOfKeys():
            name = e.GetName()
            h = e.ReadObj()
            if h.IsA().InheritsFrom(ROOT.TH1.Class()):
                for i in range(1, h.GetNbinsX() + 1):
                    if h.GetBinContent(i) < 0:
                        # print('!!!', dirname, name, i, h.GetBinContent(i), '+/-', h.GetBinError(i))
                        h.SetBinContent(i, 0)
                    # protect against negative -1 sigma uncertainty
                    if h.GetBinError(i) > h.GetBinContent(i) and not (name.endswith('Up') or name.endswith('Down')):
                        val, err = h.GetBinContent(i), h.GetBinError(i)
                        h.SetBinError(i, val)
                        print('==> Fixing %s %s bin %s from %s+/-%s to %s+/-%s' %
                              (dirname, name, i, val, err, h.GetBinContent(i), h.GetBinError(i)))
                    if h.Integral(1, h.GetNbinsX()) == 0:
                        h.SetBinContent(1, EPSILON)
                        h.SetBinError(1, EPSILON)
                outdir.cd()
                h.Write(name, ROOT.TObject.kOverwrite)
    fout.Close()
    f.Close()
    if not keep_original:
        os.remove(origfile)


if __name__ == '__main__':
    parser = argparse.ArgumentParser('Fix negative bins')
    parser.add_argument('filename', help='Input file.')
    args = parser.parse_args()

    fixNegativeBins(args.filename)