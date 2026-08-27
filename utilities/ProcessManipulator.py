from __future__ import absolute_import
from __future__ import print_function
import os
import sys
import ROOT
import json
import gc
gc.set_threshold(0)
cmssw_base = os.environ["CMSSW_BASE"]
ROOT.gROOT.SetBatch(True)
ROOT.PyConfig.IgnoreCommandLineOptions = True

if not os.path.exists(cmssw_base):
    raise ValueError("Could not find CMSSW base!")

from optparse import OptionParser, OptionGroup

ROOT.TH1.AddDirectory(False)
try:
    print("importing CombineHarvester")
    import CombineHarvester.CombineTools.ch as ch
    print("done")
except:
    msg = " ".join("""Could not find package 'CombineHarvester'.
            Are you sure you installed it?""".split())
    raise ImportError(msg)
thisdir = os.path.dirname(os.path.realpath(__file__))
if not thisdir in sys.path:
    sys.path.append(os.path.abspath(thisdir))

class ProcessManipulator(object):
    def __init__(self):
        super(ProcessManipulator, self).__init__()
        # self.background_threshold = 15
        self.background_threshold = 0.001
        # self.__debug = 50
        self.__debug = 0
    @property
    def verbosity(self):
        return self.__debug
    def drop_small_processes(self, harvester, chan = [".*"], era = [".*"], bins = [".*"], processes = [], tot_yield = None):
        """Function to drop processes from a set of process that do not
        contribute to the set significantly. The decision is based on the
        member variables 'background_threshold'.

        The function loops through all processes in the set 'processes'
        and compare the rate of the individual processes with the overall rate.


        Args:
            harvester (CombineHarvester): harvester instance that contains the processes
            chan (list, optional): list of channels to check. Defaults to [".*"].
            era (list, optional): list of eras to check. Defaults to [".*"].
            bins (list, optional): list of bins to check. Defaults to [".*"].
            processes (list, optional): list of bins to check. Defaults to [], in which case
                                        the set of background processes is used.
            tot_yield (float, optional): if provided, use this number as denominator to calculate
                                            contribution of a given process. If none is provided
                                            load the yield from the sum of the processes.
                                            Defaults to None

        Yields:
            None
        """
        # loop through all bins
        these_bins = harvester.cp().bin(bins).bin_set()
        for b in these_bins:
            b = str(b)
            # load the relevant process set. If 'processes' is empty, use set of backgrounds
            if len(processes)== 0:
                all_procs = harvester.cp().channel(chan)\
                                    .era(era).bin([b]).backgrounds()
            else:
                all_procs = harvester.cp().channel(chan)\
                                    .era(era).bin([b]).process(processes)
            # get overall rate
            total_rate = tot_yield if tot_yield else all_procs.GetRate()
            # initialize list with processes to drop
            to_drop = []
            # loop through all processes in the process set and do comparison
            for p in all_procs.process_set():
                p = str(p)
                # get process rate
                proc_rate = abs(all_procs.cp().process([p]).GetRate())
                # compare rate with overall rate
                if proc_rate < self.background_threshold * total_rate:
                    print((" ".join("""
                        Very small background process.
                        In bin {} background process {} has yield {}.
                        Total background rate in this bin is {}
                        (weighted rate with threshold '{}': {})
                        """.format(b, p, proc_rate, total_rate, self.background_threshold, self.background_threshold*total_rate).split())))
                    to_drop.append(p)
            if len(to_drop) > 0:
                self.drop_all_processes(harvester, to_drop = to_drop, eras = era, channels = chan, bins = [b])

            del all_procs, total_rate, to_drop,proc_rate
        del these_bins

    def drop_all_processes(self, harvester, to_drop, eras = [".*"], channels = [".*"], bins = [".*"]):
        # harvester.SetFlag("filters-use-regex", True)
        if self.verbosity >= 50:
                print(("pruning bins '{}'".format(", ".join(bins))))
                print(("to drop: [{}]".format(", ".join(to_drop))))
                print("harvester with era selection:")
                harvester.cp().era(eras).PrintProcs()
                print(("="*130))
                print("harvester with bin selection")
                harvester.cp().era(eras).channel(channels).bin(bins).PrintProcs()
                print(("="*130))
                print("harvester with channel selection")
                harvester.cp().era(eras).channel(channels).PrintProcs()

                print(("="*130))
        harvester.cp().era(eras).channel(channels).bin(bins).ForEachProc(lambda x: \
                harvester.FilterProcs(lambda y: True if self.matching_proc(x, y) and self.drop_procs(harvester, x, to_drop) else False)
                        )

    def matching_proc(self, p,s):
        return ((p.bin()==s.bin()) and (p.process()==s.process()) \
                and (p.signal()==s.signal()) and \
                (p.analysis()==s.analysis()) and (p.era()==s.era()) \
                and (p.channel()==s.channel()) and (p.bin_id()==s.bin_id()) \
                and (p.mass()==s.mass()))

    def drop_procs(self, chob, proc, drop_list):
        if self.verbosity >= 50:
            print(("="*130))
            print("checking process if it should be dropped:")
            print(("\tname: {}".format(proc.process())))
            print(("\tbin: {}".format(proc.bin())))
            print(("\trate: {}".format(proc.rate())))
            # print("\tcurrent bin to prune: {}".format(bin_name))
            print(("\tcurrent list to drop: {}".format(", ".join(drop_list))))
        drop = proc.process() in drop_list
        drop = drop or proc.rate() == 0
        if(drop):
            if self.verbosity >= 10:
                print(("dropping process '{}/{}'".\
                        format(proc.bin(), proc.process())))
            chob.FilterSysts(lambda sys: self.matching_proc(proc,sys))
        return drop
