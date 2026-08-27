#!/usr/bin/env python3
"""
    simple wrapper to organize combine commands in scripts, for submission to the batch system
"""

import argparse
import os
import glob
import ROOT

from utilities.auxiliary   import *
# from utilities.utils_datacard import *


#### main
if __name__ == '__main__':
    ### args --------------
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--inputs', dest='inputs', required=True, nargs='+', default=[],
                    help='path to input .root file(s)')
    parser.add_argument('-o', '--output', dest='output', action='store', default=None,
                    help='path to output directory')
    parser.add_argument('--output-eos', dest='output_eos', action='store', default=None,
                    help='path to eos output directory')
    parser.add_argument('-d', '--dry-run', dest='dry_run', action='store_true', default=False,
                        help='enable dry-run mode')
    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true', default=False,
                        help='enable verbose mode')
    parser.add_argument('--observed', dest='observed', action='store_true', default=False,
                        help='observed fits?')
    parser.add_argument('--CR', dest='CR', action='store_true', default=False,
                        help='CR fits? Then I change the POIs.')
    parser.add_argument('--CRbb', dest='CRbb', action='store_true', default=False,
                        help='CR fits? Then I change the POIs.')
    parser.add_argument('--CRbj', dest='CRbj', action='store_true', default=False,
                        help='CR fits? Then I change the POIs.')
    parser.add_argument('--CR2b', dest='CR2b', action='store_true', default=False,
                        help='CR fits? Then I change the POIs.')
    parser.add_argument('--CRcc', dest='CRcc', action='store_true', default=False,
                        help='CR fits? Then I change the POIs.')
    parser.add_argument('--CRcj', dest='CRcj', action='store_true', default=False,
                        help='CR fits? Then I change the POIs.')
    parser.add_argument('--CR2c', dest='CR2c', action='store_true', default=False,
                        help='CR fits? Then I change the POIs.')
    parser.add_argument('--CRlf', dest='CRlf', action='store_true', default=False,
                        help='CR fits? Then I change the POIs.')
    parser.add_argument('--CRnolf', dest='CRnolf', action='store_true', default=False,
                        help='CR fits? Then I change the POIs.')
    
    opts, opts_unknown = parser.parse_known_args()

    log_prx = os.path.basename(__file__)+' -- '

    # inputs
    INPUT_FILES = []

    for i_inp in opts.inputs:
        _tmp_list = glob.glob(i_inp)

        for _tmp in _tmp_list:
            
            if not os.path.isfile(_tmp):
                WARNING(log_prx+'invalid path to input .root file (will be skipped) [-i]: '+i_inp)
                continue
            
            if "classic" in _tmp:
                WARNING(log_prx+'classic workspace for postfitplots detected (will be skipped) [-i]: '+i_inp)
                continue

            INPUT_FILES += [_tmp]

    INPUT_FILES = sorted(list(set(INPUT_FILES)))

    output = 'FitStudies_'+opts.output
    output_eos = opts.output_eos

    # output
    # if os.path.exists(output):
    #     KILL(log_prx+'target path to output directory already exists [-o]: '+output)
    # if os.path.exists(output_eos):
    #     KILL(log_prx+'target path to eos output directory already exists [-o]: '+output_eos)

    isPseudoData = False
    if "pseudoData" in output:
        isPseudoData = True

    OUTPUT_DIR = os.path.realpath(os.path.abspath(output))
    OUTPUT_DIR_EOS = os.path.realpath(os.path.abspath(output_eos))

    if len(opts_unknown)>0:
        print ("Append the following unknown options to all fits:",opts_unknown)

    OPT_setPar = None
    if "--setParameters" in opts_unknown:
        setParIdx = opts_unknown.index("--setParameters")+1
        OPT_setPar = opts_unknown[setParIdx]
        opts_unknown.pop(setParIdx)
        opts_unknown.pop(setParIdx-1)
        
    addFitOption = " --X-rtd FAST_VERTICAL_MORPH"


    ### -------------------
    which('submitCombineJobs.py')

        # --setParameterRanges rate_ttHcc=0.,5.:rate_ttHbb=0.,5.:rate_ttZcc=0.,5.:rate_ttHbb=0.,5.../../workspace_${channel}_${year}.root -t -1  >& performFit_exp_sig_ttHcc.txt &
    POIs = ['r']
    # rangesString = "rgx{SF_norm_.*}=-3.,3.:rgx{rate_ttZbb.*}=-5.,5.:rgx{rate_ttZcc.*}=-5.,5.:rgx{rate_ttHbb.*}=-5.,5.:rgx{rate_ttHcc.*}=-50.,50."
    rangesString = "rgx{xsec_tt.*}=-3.,3."
    paramString  = "rgx{xsec_tt.*}=1.,r=1."


    for i_inpf in INPUT_FILES:

        if not i_inpf.endswith('.root'):
            KILL(log_prx+'invalid extension for input datacard (must be .root): '+i_inpf)

        i_inpf_basename_woExt = os.path.splitext(os.path.basename(i_inpf))[0]

        i_outdir = OUTPUT_DIR+'/'+i_inpf_basename_woExt
        i_outdir_eos = OUTPUT_DIR_EOS+'/'+i_inpf_basename_woExt

        if opts.observed:

            # GOF
            ### GoodnessOfFit [Data]
            gof_Data_cmd  = 'submitCombineJobs.py'
            gof_Data_cmd += ' -M GoodnessOfFit --algo=saturated'
            gof_Data_cmd += ' -m 125.38'
            gof_Data_cmd += ' --setParameters '+paramString
            if OPT_setPar:
                gof_Data_cmd += ','+OPT_setPar
            gof_Data_cmd += ' --setParameterRanges '+rangesString
            gof_Data_cmd += ' --cminDefaultMinimizerStrategy 0 --X-rtd MINIMIZER_MaxCalls=999999999 --cminDefaultMinimizerTolerance 0.1'+addFitOption
            gof_Data_cmd += ' --cminPreScan --cminPreFit 1'
            gof_Data_cmd += ' -o '+i_outdir+'/GoodnessOfFit/Data'
            gof_Data_cmd += ' --output-eos '+i_outdir_eos+'/GoodnessOfFit/Data'
            gof_Data_cmd += ' -n _'+i_inpf_basename_woExt
            gof_Data_cmd += ' -d '+i_inpf


            if opts.CR:
                gof_Data_cmd += ' --redefineSignalPOIs xsec_ttcc,xsec_ttcj,xsec_ttbb,xsec_ttbj,xsec_ttLF,xsec_tt2b,xsec_tt2c'
                gof_Data_cmd += ' --freezeParameters r'
            elif opts.CRbb:
                gof_Data_cmd += ' --redefineSignalPOIs xsec_ttbb'
                gof_Data_cmd += ' --freezeParameters r'
            elif opts.CRbj:
                gof_Data_cmd += ' --redefineSignalPOIs xsec_ttbj'
                gof_Data_cmd += ' --freezeParameters r'
            elif opts.CRcj:
                gof_Data_cmd += ' --redefineSignalPOIs xsec_ttcj'
                gof_Data_cmd += ' --freezeParameters r'
            elif opts.CRcc:
                gof_Data_cmd += ' --redefineSignalPOIs xsec_ttcc'
                gof_Data_cmd += ' --freezeParameters r'
            elif opts.CRlf:
                gof_Data_cmd += ' --redefineSignalPOIs xsec_ttLF'
                gof_Data_cmd += ' --freezeParameters r'
            elif opts.CR2b:
                gof_Data_cmd += ' --redefineSignalPOIs xsec_tt2b'
                gof_Data_cmd += ' --freezeParameters r'
            elif opts.CR2c:
                gof_Data_cmd += ' --redefineSignalPOIs xsec_tt2c'
                gof_Data_cmd += ' --freezeParameters r'
            elif opts.CRnolf:
                gof_Data_cmd += ' --redefineSignalPOIs xsec_ttcc,xsec_ttcj,xsec_ttbj,xsec_ttbb,xsec_tt2b,xsec_tt2c'
                gof_Data_cmd += ' --freezeParameters r'
            else:
                gof_Data_cmd += ' --redefineSignalPOIs '
                for ipar, par in enumerate(POIs):
                    if ipar == len(POIs)-1:
                        gof_Data_cmd += par
                    else:
                        gof_Data_cmd += par+','

            for ou in opts_unknown:
                gof_Data_cmd += ' '+ou

            # if not isPseudoData:
            if True:
                EXE(gof_Data_cmd, verbose=opts.verbose, dry_run=opts.dry_run)

            ### GoodnessOfFit [Toys]
            for gof_toys_seed in range(101, 131):

                gof_toys_cmd  = 'submitCombineJobs.py'
                gof_toys_cmd += ' -M GoodnessOfFit --algo=saturated --toysFrequentist'
                gof_toys_cmd += ' -m 125.38'
                gof_toys_cmd += ' --cminDefaultMinimizerStrategy 0 --X-rtd MINIMIZER_MaxCalls=999999999 --cminDefaultMinimizerTolerance 0.1'+addFitOption
                gof_toys_cmd += ' --cminPreScan --cminPreFit 1'
                gof_toys_cmd += ' --setParameters '+paramString
                if OPT_setPar:
                    gof_toys_cmd += ','+OPT_setPar
                gof_toys_cmd += ' --setParameterRanges '+rangesString
                gof_toys_cmd += ' -o '+i_outdir+'/GoodnessOfFit/Toys'
                gof_toys_cmd += ' --output-eos '+i_outdir_eos+'/GoodnessOfFit/Toys'
                gof_toys_cmd += ' -n _'+i_inpf_basename_woExt
                gof_toys_cmd += ' -d '+i_inpf
                gof_toys_cmd += ' --toys 100'
                gof_toys_cmd += ' --seed '+str(gof_toys_seed)
                gof_toys_cmd += ' --output-postfix '+str(gof_toys_seed)

                if opts.CR:
                    gof_toys_cmd += ' --redefineSignalPOIs xsec_ttcc,xsec_ttcj,xsec_ttbb,xsec_ttbj,xsec_ttLF,xsec_tt2b,xsec_tt2c'
                    gof_toys_cmd += ' --freezeParameters r'
                elif opts.CRbb:
                    gof_toys_cmd += ' --redefineSignalPOIs xsec_ttbb'
                    gof_toys_cmd += ' --freezeParameters r'
                elif opts.CRbj:
                    gof_toys_cmd += ' --redefineSignalPOIs xsec_ttbj'
                    gof_toys_cmd += ' --freezeParameters r'
                elif opts.CRcj:
                    gof_toys_cmd += ' --redefineSignalPOIs xsec_ttcj'
                    gof_toys_cmd += ' --freezeParameters r'
                elif opts.CRcc:
                    gof_toys_cmd += ' --redefineSignalPOIs xsec_ttcc'
                    gof_toys_cmd += ' --freezeParameters r'
                elif opts.CRlf:
                    gof_toys_cmd += ' --redefineSignalPOIs xsec_ttLF'
                    gof_toys_cmd += ' --freezeParameters r'
                elif opts.CR2b:
                    gof_toys_cmd += ' --redefineSignalPOIs xsec_tt2b'
                    gof_toys_cmd += ' --freezeParameters r'
                elif opts.CR2c:
                    gof_toys_cmd += ' --redefineSignalPOIs xsec_tt2c'
                    gof_toys_cmd += ' --freezeParameters r'
                elif opts.CRnolf:
                    gof_toys_cmd += ' --redefineSignalPOIs xsec_ttcc,xsec_ttcj,xsec_ttbj,xsec_ttbb,xsec_tt2b,xsec_tt2c'
                    gof_toys_cmd += ' --freezeParameters r'
                else:
                    gof_toys_cmd += ' --redefineSignalPOIs '
                    for ipar, par in enumerate(POIs):
                        if ipar == len(POIs)-1:
                            gof_toys_cmd += par
                        else:
                            gof_toys_cmd += par+','

                for ou in opts_unknown:
                    gof_toys_cmd += ' '+ou

                # if not isPseudoData:
                if True:
                    EXE(gof_toys_cmd, verbose=opts.verbose, dry_run=opts.dry_run)

        #######################################################################################################################
        # if opts.observed:

        #     # GOF
        #     ### GoodnessOfFit [Data] - fixed signal 1
        #     gof_Data_cmd  = 'submitCombineJobs.py'
        #     gof_Data_cmd += ' -M GoodnessOfFit --algo=saturated'
        #     gof_Data_cmd += ' -m 125.38'
        #     gof_Data_cmd += ' --fixedSignalStrength 1'
        #     gof_Data_cmd += ' --setParameters '+paramString
        #     if OPT_setPar:
        #         gof_Data_cmd += ','+OPT_setPar
        #     gof_Data_cmd += ' --setParameterRanges '+rangesString
        #     gof_Data_cmd += ' --cminDefaultMinimizerStrategy 0 --X-rtd MINIMIZER_MaxCalls=999999999 --cminDefaultMinimizerTolerance 0.1'+addFitOption
        #     gof_Data_cmd += ' --cminPreScan --cminPreFit 1'
        #     gof_Data_cmd += ' -o '+i_outdir+'/GoodnessOfFitFixedSignal/Data'
        #     gof_Data_cmd += ' --output-eos '+i_outdir_eos+'/GoodnessOfFitFixedSignal/Data'
        #     gof_Data_cmd += ' -n _'+i_inpf_basename_woExt
        #     gof_Data_cmd += ' -d '+i_inpf


        #     if opts.CR:
        #             gof_Data_cmd += ' --redefineSignalPOIs xsec_ttcc,xsec_ttcj,xsec_ttbb,xsec_ttbj,xsec_ttLF,xsec_tt2b,xsec_tt2c'
        #             gof_Data_cmd += ' --freezeParameters r'\
        #     else:
        #         gof_Data_cmd += ' --redefineSignalPOIs '
        #         for ipar, par in enumerate(POIs):
        #             if ipar == len(POIs)-1:
        #                 gof_Data_cmd += par
        #             else:
        #                 gof_Data_cmd += par+','

        #     for ou in opts_unknown:
        #         gof_Data_cmd += ' '+ou

        #     # if not isPseudoData:
        #     if True:
        #         EXE(gof_Data_cmd, verbose=opts.verbose, dry_run=opts.dry_run)

        #     ### GoodnessOfFit [Toys] FixedSignal 1 
        #     for gof_toys_seed in range(101, 131):

        #         gof_toys_cmd  = 'submitCombineJobs.py'
        #         gof_toys_cmd += ' -M GoodnessOfFit --algo=saturated --toysFrequentist'
        #         gof_toys_cmd += ' -m 125.38'
        #         gof_toys_cmd += ' --fixedSignalStrength 1'
        #         gof_toys_cmd += ' --cminDefaultMinimizerStrategy 0 --X-rtd MINIMIZER_MaxCalls=999999999 --cminDefaultMinimizerTolerance 0.1'+addFitOption
        #         gof_toys_cmd += ' --cminPreScan --cminPreFit 1'
        #         gof_toys_cmd += ' --setParameters '+paramString
        #         if OPT_setPar:
        #             gof_toys_cmd += ','+OPT_setPar
        #         gof_toys_cmd += ' --setParameterRanges '+rangesString
        #         gof_toys_cmd += ' -o '+i_outdir+'/GoodnessOfFitFixedSignal/Toys'
        #         gof_toys_cmd += ' --output-eos '+i_outdir_eos+'/GoodnessOfFitFixedSignal/Toys'
        #         gof_toys_cmd += ' -n _'+i_inpf_basename_woExt
        #         gof_toys_cmd += ' -d '+i_inpf
        #         gof_toys_cmd += ' --toys 100'
        #         gof_toys_cmd += ' --seed '+str(gof_toys_seed)
        #         gof_toys_cmd += ' --output-postfix '+str(gof_toys_seed)

        #         if opts.CR:
        #                 gof_toys_cmd += ' --redefineSignalPOIs xsec_ttcc,xsec_ttcj,xsec_ttbb,xsec_ttbj,xsec_ttLF,xsec_tt2b,xsec_tt2c'
        #                 gof_toys_cmd += ' --freezeParameters r'
        #         else:
        #             gof_toys_cmd += ' --redefineSignalPOIs '
        #             for ipar, par in enumerate(POIs):
        #                 if ipar == len(POIs)-1:
        #                     gof_toys_cmd += par
        #                 else:
        #                     gof_toys_cmd += par+','

        #         for ou in opts_unknown:
        #             gof_toys_cmd += ' '+ou

        #         # if not isPseudoData:
        #         if True:
        #             EXE(gof_toys_cmd, verbose=opts.verbose, dry_run=opts.dry_run)

        #######################################################################################################################
        #######################################################################################################################
        #######################################################################################################################
        # Impacts [expected]
        n_ = 'nominal_exp_impacts'
        command_Impacts = 'submitImpacts.py '
        command_Impacts += ' -o '+i_outdir+'/ImpactsExpected/'
        command_Impacts += ' --output-eos '+i_outdir_eos+'/ImpactsExpected/'
        command_Impacts += ' -m 125.38'
        command_Impacts += ' --cminDefaultMinimizerStrategy 0 --X-rtd MINIMIZER_MaxCalls=999999999 --cminDefaultMinimizerTolerance 0.1'+addFitOption
        command_Impacts += ' --cminPreScan --cminPreFit 1'
        # command_Impacts += ' --saveFitResult --saveWorkspace --saveNLL --X-rtd REMOVE_CONSTANT_ZERO_POINT=1'
        command_Impacts += ' -d '+i_inpf
        command_Impacts += ' -n _'+n_
        command_Impacts += ' -t -1'
        command_Impacts += ' --setParameters '+paramString
        if OPT_setPar:
            command_Impacts += ','+OPT_setPar
        command_Impacts += ' --setParameterRanges '+rangesString
        if opts.CR:
            command_Impacts += ' --redefineSignalPOIs xsec_ttcc,xsec_ttcj,xsec_ttbb,xsec_ttbj,xsec_ttLF,xsec_tt2b,xsec_tt2c'
            command_Impacts += ' --freezeParameters r'
        elif opts.CRbb:
            command_Impacts += ' --redefineSignalPOIs xsec_ttbb'
            command_Impacts += ' --freezeParameters r'
        elif opts.CRbj:
            command_Impacts += ' --redefineSignalPOIs xsec_ttbj'
            command_Impacts += ' --freezeParameters r'
        elif opts.CR2b:
            command_Impacts += ' --redefineSignalPOIs xsec_tt2b'
            command_Impacts += ' --freezeParameters r'
        elif opts.CRcc:
            command_Impacts += ' --redefineSignalPOIs xsec_ttcc'
            command_Impacts += ' --freezeParameters r'
        elif opts.CRcj:
            command_Impacts += ' --redefineSignalPOIs xsec_ttcj'
            command_Impacts += ' --freezeParameters r'
        elif opts.CR2c:
            command_Impacts += ' --redefineSignalPOIs xsec_tt2c'
            command_Impacts += ' --freezeParameters r'
        elif opts.CRlf:
            command_Impacts += ' --redefineSignalPOIs xsec_ttLF'
            command_Impacts += ' --freezeParameters r'
        elif opts.CRnolf:
            command_Impacts += ' --redefineSignalPOIs xsec_ttcc,xsec_ttcj,xsec_ttbj,xsec_ttbb,xsec_tt2b,xsec_tt2c'
            command_Impacts += ' --freezeParameters r'
        else:
            command_Impacts += ' --redefineSignalPOIs '
            for ipar, par in enumerate(POIs):
                if ipar == len(POIs)-1:
                    command_Impacts += par
                else:
                    command_Impacts += par+','


        for ou in opts_unknown:
            command_Impacts += ' '+ou
        # command_Impacts += ' --htc-opts +RequestRuntime=21600'

        if not isPseudoData:
            EXE(command_Impacts, verbose = opts.verbose, dry_run = opts.dry_run)


        # Impacts [expected - a posteriori]
        n_ = 'nominal_exp_impacts_freq'
        command_Impacts = 'submitImpacts.py '
        command_Impacts += ' -o '+i_outdir+'/ImpactsExpectedFreq/'
        command_Impacts += ' --output-eos '+i_outdir_eos+'/ImpactsExpectedFreq/'
        command_Impacts += ' -m 125.38'
        command_Impacts += ' --cminDefaultMinimizerStrategy 0 --X-rtd MINIMIZER_MaxCalls=999999999 --cminDefaultMinimizerTolerance 0.1'+addFitOption
        command_Impacts += ' --cminPreScan --cminPreFit 1'
        # command_Impacts += ' --saveFitResult --saveWorkspace --saveNLL --X-rtd REMOVE_CONSTANT_ZERO_POINT=1'
        command_Impacts += ' -d '+i_inpf
        command_Impacts += ' -n _'+n_
        command_Impacts += ' -t -1'
        command_Impacts += ' --toysFrequentist'
        command_Impacts += ' --setParameters '+paramString
        if OPT_setPar:
            command_Impacts += ','+OPT_setPar
        command_Impacts += ' --setParameterRanges '+rangesString
        if opts.CR:
            command_Impacts += ' --redefineSignalPOIs xsec_ttcc,xsec_ttcj,xsec_ttbb,xsec_ttbj,xsec_ttLF,xsec_tt2b,xsec_tt2c'
            command_Impacts += ' --freezeParameters r'
        elif opts.CRbb:
            command_Impacts += ' --redefineSignalPOIs xsec_ttbb'
            command_Impacts += ' --freezeParameters r'
        elif opts.CRbj:
            command_Impacts += ' --redefineSignalPOIs xsec_ttbj'
            command_Impacts += ' --freezeParameters r'
        elif opts.CR2b:
            command_Impacts += ' --redefineSignalPOIs xsec_tt2b'
            command_Impacts += ' --freezeParameters r'
        elif opts.CRcc:
            command_Impacts += ' --redefineSignalPOIs xsec_ttcc'
            command_Impacts += ' --freezeParameters r'
        elif opts.CRcj:
            command_Impacts += ' --redefineSignalPOIs xsec_ttcj'
            command_Impacts += ' --freezeParameters r'
        elif opts.CR2c:
            command_Impacts += ' --redefineSignalPOIs xsec_tt2c'
            command_Impacts += ' --freezeParameters r'
        elif opts.CRlf:
            command_Impacts += ' --redefineSignalPOIs xsec_ttLF'
            command_Impacts += ' --freezeParameters r'
        elif opts.CRnolf:
            command_Impacts += ' --redefineSignalPOIs xsec_ttcc,xsec_ttcj,xsec_ttbj,xsec_ttbb,xsec_tt2b,xsec_tt2c'
            command_Impacts += ' --freezeParameters r'
        else:
            command_Impacts += ' --redefineSignalPOIs '
            for ipar, par in enumerate(POIs):
                if ipar == len(POIs)-1:
                    command_Impacts += par
                else:
                    command_Impacts += par+','


        for ou in opts_unknown:
            command_Impacts += ' '+ou
        # command_Impacts += ' --htc-opts +RequestRuntime=21600'

        if not isPseudoData:
            EXE(command_Impacts, verbose = opts.verbose, dry_run = opts.dry_run)

        if opts.observed:
            # Impacts [observed]
            n_ = 'nominal_obs_impacts'
            command_Impacts = 'submitImpacts.py '
            command_Impacts += ' -o '+i_outdir+'/ImpactsObserved/'
            command_Impacts += ' --output-eos '+i_outdir_eos+'/ImpactsObserved/'
            command_Impacts += ' -m 125.38'
            command_Impacts += ' --cminDefaultMinimizerStrategy 0 --X-rtd MINIMIZER_MaxCalls=999999999 --cminDefaultMinimizerTolerance 0.1'+addFitOption
            command_Impacts += ' --cminPreScan --cminPreFit 1'
            # command_Impacts += ' --saveFitResult --saveWorkspace --saveNLL --X-rtd REMOVE_CONSTANT_ZERO_POINT=1'
            command_Impacts += ' -d '+i_inpf
            command_Impacts += ' -n _'+n_
            command_Impacts += ' --setParameters '+paramString
            if OPT_setPar:
                command_Impacts += ','+OPT_setPar
            command_Impacts += ' --setParameterRanges '+rangesString
            if opts.CR:
                command_Impacts += ' --redefineSignalPOIs xsec_ttcc,xsec_ttcj,xsec_ttbb,xsec_ttbj,xsec_ttLF,xsec_tt2b,xsec_tt2c'
                command_Impacts += ' --freezeParameters r'
            elif opts.CRbb:
                command_Impacts += ' --redefineSignalPOIs xsec_ttbb'
                command_Impacts += ' --freezeParameters r'
            elif opts.CRbj:
                command_Impacts += ' --redefineSignalPOIs xsec_ttbj'
                command_Impacts += ' --freezeParameters r'
            elif opts.CR2b:
                command_Impacts += ' --redefineSignalPOIs xsec_tt2b'
                command_Impacts += ' --freezeParameters r'
            elif opts.CRcc:
                command_Impacts += ' --redefineSignalPOIs xsec_ttcc'
                command_Impacts += ' --freezeParameters r'
            elif opts.CRcj:
                command_Impacts += ' --redefineSignalPOIs xsec_ttcj'
                command_Impacts += ' --freezeParameters r'
            elif opts.CR2c:
                command_Impacts += ' --redefineSignalPOIs xsec_tt2c'
                command_Impacts += ' --freezeParameters r'
            elif opts.CRlf:
                command_Impacts += ' --redefineSignalPOIs xsec_ttLF'
                command_Impacts += ' --freezeParameters r'
            elif opts.CRnolf:
                command_Impacts += ' --redefineSignalPOIs xsec_ttcc,xsec_ttcj,xsec_ttbj,xsec_ttbb,xsec_tt2b,xsec_tt2c'
                command_Impacts += ' --freezeParameters r'
            else:
                command_Impacts += ' --redefineSignalPOIs '
                for ipar, par in enumerate(POIs):
                    if ipar == len(POIs)-1:
                        command_Impacts += par
                    else:
                        command_Impacts += par+','


            for ou in opts_unknown:
                command_Impacts += ' '+ou


            # command_Impacts += ' --htc-opts +RequestRuntime=21600'
            # if not isPseudoData:
            if True:
                EXE(command_Impacts, verbose = opts.verbose, dry_run = opts.dry_run)

        #######################################################################################################################
        #######################################################################################################################
        #######################################################################################################################
        # # 1D Scans [expected]
        # for POI in POIs:
        #     command_significance = 'submitScans.py '
        #     command_significance += ' -m 125.38'
        #     command_significance += ' --cminDefaultMinimizerStrategy 0 --X-rtd MINIMIZER_MaxCalls=999999999 --cminDefaultMinimizerTolerance 0.1'+addFitOption
        #     command_significance += ' --cminPreScan --cminPreFit 1'
        #     command_significance += ' --floatOtherPOIs'
        #     command_significance += ' -o '+i_outdir+'/1DScanExpected/'+POI+'/'
        #     command_significance += ' --output-eos '+i_outdir_eos+'/1DScanExpected/'+POI+'/'
        #     command_significance += ' -d '+i_inpf
        #     command_significance += ' -t -1'
        #     command_significance += ' --setParameters '+paramString
        #     if OPT_setPar:
        #         command_significance += ','+OPT_setPar
        #     command_significance += ' --setParameterRanges '+rangesString
        #     if opts.CR:
        #         command_significance += ' --freezeParameters r'
        #     command_significance += ' --redefineSignalPOIs '+POI
        #     command_significance += ' --POI '+POI

        #     for ou in opts_unknown:
        #         command_significance += ' '+ou
        #     if not isPseudoData:
        #         EXE(command_significance, verbose = opts.verbose, dry_run = opts.dry_run)

        # # 1D Scans [expected-a-posteriori]
        # for POI in POIs:
        #     command_significance = 'submitScans.py '
        #     command_significance += ' -m 125.38'
        #     command_significance += ' --cminDefaultMinimizerStrategy 0 --X-rtd MINIMIZER_MaxCalls=999999999 --cminDefaultMinimizerTolerance 0.1'+addFitOption
        #     command_significance += ' --cminPreScan --cminPreFit 1'
        #     command_significance += ' --floatOtherPOIs'
        #     command_significance += ' -o '+i_outdir+'/1DScanExpectedFreq/'+POI+'/'
        #     command_significance += ' --output-eos '+i_outdir_eos+'/1DScanExpectedFreq/'+POI+'/'
        #     command_significance += ' -d '+i_inpf
        #     command_significance += ' -t -1'
        #     command_significance += ' --toysFrequentist'
        #     command_significance += ' --setParameters '+paramString
        #     if OPT_setPar:
        #         command_significance += ','+OPT_setPar
        #     command_significance += ' --setParameterRanges '+rangesString
        #     if opts.CR:
        #         command_significance += ' --freezeParameters r'
        #     command_significance += ' --redefineSignalPOIs '+POI
        #     command_significance += ' --POI '+POI

        #     for ou in opts_unknown:
        #         command_significance += ' '+ou
        #     if not isPseudoData:
        #         EXE(command_significance, verbose = opts.verbose, dry_run = opts.dry_run)

        # if opts.observed:
        #     # 1D Scans [observed]
        #     for POI in POIs:
        #         command_significance = 'submitScans.py '
        #         command_significance += ' -M Significance'
        #         command_significance += ' -m 125.38'
        #         command_significance += ' --cminDefaultMinimizerStrategy 0 --X-rtd MINIMIZER_MaxCalls=999999999 --cminDefaultMinimizerTolerance 0.1'+addFitOption
        #         command_significance += ' --cminPreScan --cminPreFit 1'
        #         command_significance += ' --floatOtherPOIs'
        #         command_significance += ' -o '+i_outdir+'/1DScanObserved/'+POI+'/'
        #         command_significance += ' --output-eos '+i_outdir_eos+'/1DScanObserved/'+POI+'/'
        #         command_significance += ' -d '+i_inpf
        #         command_significance += ' --setParameters '+paramString
        #         if OPT_setPar:
        #             command_significance += ','+OPT_setPar
        #         command_significance += ' --setParameterRanges '+rangesString
        #         command_significance += ' --redefineSignalPOIs '+POI
        #         command_significance += ' --POI '+POI
        #         for ou in opts_unknown:
        #             command_significance += ' '+ou

        #         if not isPseudoData:
        #             EXE(command_significance, verbose = opts.verbose, dry_run = opts.dry_run)


        #######################################################################################################################
        #######################################################################################################################
        #######################################################################################################################
        # Significance [expected]
        for POI in POIs:
            n_ = 'nominal_exp_significance_'+POI
            command_significance = 'submitCombineJobs.py '
            command_significance += ' -M Significance'
            command_significance += ' -m 125.38'
            command_significance += ' --cminDefaultMinimizerStrategy 0 --X-rtd MINIMIZER_MaxCalls=999999999 --cminDefaultMinimizerTolerance 0.1'+addFitOption
            command_significance += ' --cminPreScan --cminPreFit 1'
            command_significance += ' -o '+i_outdir+'/SignificanceExpected/'+POI+'/'
            command_significance += ' --output-eos '+i_outdir_eos+'/SignificanceExpected/'+POI+'/'
            command_significance += ' -n _'+n_
            command_significance += ' -d '+i_inpf
            command_significance += ' -t -1'
            command_significance += ' --setParameters '+paramString
            if OPT_setPar:
                command_significance += ','+OPT_setPar
            command_significance += ' --setParameterRanges '+rangesString
            # if opts.CR:
            if opts.CR or opts.CRbb or opts.CRbj or opts.CRcc or opts.CRcj or opts.CRlf or opts.CR2b or opts.CR2c or opts.CRnolf:
                command_significance += ' --freezeParameters r'
            # else:
            command_significance += ' --redefineSignalPOIs '+POI

            for ou in opts_unknown:
                command_significance += ' '+ou
            if not isPseudoData:
                EXE(command_significance, verbose = opts.verbose, dry_run = opts.dry_run)

        # Significance [expected-a-posteriori]
        for POI in POIs:
            n_ = 'nominal_exp_significance_freq_'+POI
            command_significance = 'submitCombineJobs.py '
            command_significance += ' -M Significance'
            command_significance += ' -m 125.38'
            command_significance += ' --cminDefaultMinimizerStrategy 0 --X-rtd MINIMIZER_MaxCalls=999999999 --cminDefaultMinimizerTolerance 0.1'+addFitOption
            command_significance += ' --cminPreScan --cminPreFit 1'
            command_significance += ' -o '+i_outdir+'/SignificanceExpectedFreq/'+POI+'/'
            command_significance += ' --output-eos '+i_outdir_eos+'/SignificanceExpectedFreq/'+POI+'/'
            command_significance += ' -n _'+n_
            command_significance += ' -d '+i_inpf
            command_significance += ' -t -1'
            command_significance += ' --toysFrequentist'
            command_significance += ' --setParameters '+paramString
            if OPT_setPar:
                command_significance += ','+OPT_setPar
            command_significance += ' --setParameterRanges '+rangesString
            if opts.CR or opts.CRbb or opts.CRbj or opts.CRcc or opts.CRcj or opts.CRlf or opts.CR2b or opts.CR2c or opts.CRnolf:
                command_significance += ' --freezeParameters r'
            # else:
            command_significance += ' --redefineSignalPOIs '+POI

            for ou in opts_unknown:
                command_significance += ' '+ou
            if not isPseudoData:
                EXE(command_significance, verbose = opts.verbose, dry_run = opts.dry_run)

        if opts.observed:
            # Significance [observed]
            for POI in POIs:
                n_ = 'nominal_obs_significance_'+POI
                command_significance = 'submitCombineJobs.py '
                command_significance += ' -M Significance'
                command_significance += ' -m 125.38'
                command_significance += ' --cminDefaultMinimizerStrategy 0 --X-rtd MINIMIZER_MaxCalls=999999999 --cminDefaultMinimizerTolerance 0.1'+addFitOption
                command_significance += ' --cminPreScan --cminPreFit 1'
                command_significance += ' -o '+i_outdir+'/SignificanceObserved/'+POI+'/'
                command_significance += ' --output-eos '+i_outdir_eos+'/SignificanceObserved/'+POI+'/'
                command_significance += ' -n _'+n_
                command_significance += ' -d '+i_inpf
                command_significance += ' --setParameters '+paramString
                if OPT_setPar:
                    command_significance += ','+OPT_setPar
                command_significance += ' --setParameterRanges '+rangesString
                command_significance += ' --redefineSignalPOIs '+POI
                for ou in opts_unknown:
                    command_significance += ' '+ou

                if not isPseudoData:
                    EXE(command_significance, verbose = opts.verbose, dry_run = opts.dry_run)

        #######################################################################################################################
        #######################################################################################################################
        #######################################################################################################################
        # SignificanceToys [expected]
        # for POI in POIs:
        #     # for bias_toys_seed in range(101, 131):
        #     for bias_toys_seed in range(101, 131):
        #         n_ = 'nominal_exp_significancetoys_'+POI
        #         command_significance = 'submitCombineJobs.py '
        #         command_significance += ' -M HybridNew'
        #         command_significance += ' -m 125.38'
        #         command_significance += ' --LHCmode LHC-significance'
        #         command_significance += ' --cminDefaultMinimizerStrategy 0 --X-rtd MINIMIZER_MaxCalls=999999999 --cminDefaultMinimizerTolerance 0.1'+addFitOption
        #         command_significance += ' --cminPreScan --cminPreFit 1'
        #         command_significance += ' -o '+i_outdir+'/SignificanceToysExpected/'+POI+'/'
        #         command_significance += ' --output-eos '+i_outdir_eos+'/SignificanceToysExpected/'+POI+'/'
        #         command_significance += ' -n _'+n_
        #         # command_significance += ' -d '+i_inpf
        #         command_significance += ' -d '+i_inpf.replace('workspace_Vcb_SL_2024.root', 'Vcb_SL_2024.txt')
        #         command_significance += ' -T 500'
        #         command_significance += ' --saveToys'
        #         command_significance += ' --fullBToys'
        #         command_significance += ' --saveHybridResult'
        #         command_significance += ' --expectSignal 1'
        #         command_significance += ' --seed '+str(bias_toys_seed)
        #         command_significance += ' --output-postfix '+str(bias_toys_seed)
        #         command_significance += ' --setParameters '+paramString
        #         if OPT_setPar:
        #             command_significance += ','+OPT_setPar
        #         command_significance += ' --setParameterRanges '+rangesString
        #         # if opts.CR:
        #         if opts.CR or opts.CRbb or opts.CRbj or opts.CRcc or opts.CRcj or opts.CRlf or opts.CR2b or opts.CR2c or opts.CRnolf:
        #             command_significance += ' --freezeParameters r'
        #         # else:
        #         command_significance += ' --redefineSignalPOIs '+POI

        #         for ou in opts_unknown:
        #             command_significance += ' '+ou
        #         if not isPseudoData:
        #             EXE(command_significance, verbose = opts.verbose, dry_run = opts.dry_run)

        # # Significance [expected-a-posteriori]
        # for POI in POIs:
        #     n_ = 'nominal_exp_significance_freq_'+POI
        #     command_significance = 'submitCombineJobs.py '
        #     command_significance += ' -M HybridNew'
        #     command_significance += ' -m 125.38'
        #     command_significance += ' --cminDefaultMinimizerStrategy 0 --X-rtd MINIMIZER_MaxCalls=999999999 --cminDefaultMinimizerTolerance 0.1'+addFitOption
        #     command_significance += ' --cminPreScan --cminPreFit 1'
        #     command_significance += ' -o '+i_outdir+'/SignificanceExpectedFreq/'+POI+'/'
        #     command_significance += ' --output-eos '+i_outdir_eos+'/SignificanceExpectedFreq/'+POI+'/'
        #     command_significance += ' -n _'+n_
        #     command_significance += ' -d '+i_inpf
        #     command_significance += ' -T 100'
        #     command_significance += ' --saveToys'
        #     command_significance += ' --fullBToys'
        #     command_significance += ' --toysFrequentist'
        #     command_significance += ' --seed '+str(bias_toys_seed)
        #     command_significance += ' --output-postfix '+str(bias_toys_seed)
        #     command_significance += ' --setParameters '+paramString
        #     if OPT_setPar:
        #         command_significance += ','+OPT_setPar
        #     command_significance += ' --setParameterRanges '+rangesString
        #     if opts.CR or opts.CRbb or opts.CRbj or opts.CRcc or opts.CRcj or opts.CRlf or opts.CR2b or opts.CR2c or opts.CRnolf:
        #         command_significance += ' --freezeParameters r'
        #     # else:
        #     command_significance += ' --redefineSignalPOIs '+POI

        #     for ou in opts_unknown:
        #         command_significance += ' '+ou
        #     if not isPseudoData:
        #         EXE(command_significance, verbose = opts.verbose, dry_run = opts.dry_run)

        # if opts.observed:
        #     # Significance [observed]
        #     for POI in POIs:
        #         n_ = 'nominal_obs_significance_'+POI
        #         command_significance = 'submitCombineJobs.py '
        #         command_significance += ' -M Significance'
        #         command_significance += ' -m 125.38'
        #         command_significance += ' --cminDefaultMinimizerStrategy 0 --X-rtd MINIMIZER_MaxCalls=999999999 --cminDefaultMinimizerTolerance 0.1'+addFitOption
        #         command_significance += ' --cminPreScan --cminPreFit 1'
        #         command_significance += ' -o '+i_outdir+'/SignificanceObserved/'+POI+'/'
        #         command_significance += ' --output-eos '+i_outdir_eos+'/SignificanceObserved/'+POI+'/'
        #         command_significance += ' -n _'+n_
        #         command_significance += ' -d '+i_inpf
        #         command_significance += ' --setParameters '+paramString
        #         if OPT_setPar:
        #             command_significance += ','+OPT_setPar
        #         command_significance += ' --setParameterRanges '+rangesString
        #         command_significance += ' --redefineSignalPOIs '+POI
        #         for ou in opts_unknown:
        #             command_significance += ' '+ou

        #         if not isPseudoData:
        #             EXE(command_significance, verbose = opts.verbose, dry_run = opts.dry_run)

        #######################################################################################################################
        #######################################################################################################################
        #######################################################################################################################
        # Limits [expected]
        for POI in POIs:
            n_ = 'nominal_exp_limit_'+POI
            command_limits = 'submitCombineJobs.py '
            command_limits += ' -M AsymptoticLimits'
            command_limits += ' -m 125.38'
            command_limits += ' --cminDefaultMinimizerStrategy 0 --X-rtd MINIMIZER_MaxCalls=999999999 --cminDefaultMinimizerTolerance 0.1'+addFitOption
            command_limits += ' --cminPreScan --cminPreFit 1'
            command_limits += ' -o '+i_outdir+'/LimitsExpected/'+POI+'/'
            command_limits += ' --output-eos '+i_outdir_eos+'/LimitsExpected/'+POI+'/'
            command_limits += ' -n _'+n_
            command_limits += ' -d '+i_inpf
            command_limits += ' -t -1  --run blind'
            command_limits += ' --setParameters '+paramString
            if OPT_setPar:
                command_limits += ','+OPT_setPar
            command_limits += ' --setParameterRanges '+rangesString
            command_limits += ' --redefineSignalPOIs '+POI
            for ou in opts_unknown:
                command_limits += ' '+ou

            if not isPseudoData:
                EXE(command_limits, verbose = opts.verbose, dry_run = opts.dry_run)

        # Limits [expected-a posteriori]
        for POI in POIs:
            n_ = 'nominal_exp_limit_freq_'+POI
            command_limits = 'submitCombineJobs.py '
            command_limits += ' -M AsymptoticLimits'
            command_limits += ' -m 125.38'
            command_limits += ' --cminDefaultMinimizerStrategy 0 --X-rtd MINIMIZER_MaxCalls=999999999 --cminDefaultMinimizerTolerance 0.1'+addFitOption
            command_limits += ' --cminPreScan --cminPreFit 1'
            command_limits += ' -o '+i_outdir+'/LimitsExpectedFreq/'+POI+'/'
            command_limits += ' --output-eos '+i_outdir_eos+'/LimitsExpectedFreq/'+POI+'/'
            command_limits += ' -n _'+n_
            command_limits += ' -d '+i_inpf
            command_limits += ' -t -1'
            command_limits += ' --toysFrequentist'
            command_limits += ' --setParameters '+paramString
            if OPT_setPar:
                command_limits += ','+OPT_setPar
            command_limits += ' --setParameterRanges '+rangesString
            command_limits += ' --redefineSignalPOIs '+POI
            for ou in opts_unknown:
                command_limits += ' '+ou

            if not isPseudoData:
                EXE(command_limits, verbose = opts.verbose, dry_run = opts.dry_run)

        if opts.observed:
            # Limits [observed]
            for POI in POIs:
                n_ = 'nominal_obs_limit_'+POI
                command_limits = 'submitCombineJobs.py '
                command_limits += ' -M AsymptoticLimits'
                command_limits += ' -m 125.38'
                command_limits += ' --cminDefaultMinimizerStrategy 0 --X-rtd MINIMIZER_MaxCalls=999999999 --cminDefaultMinimizerTolerance 0.1'+addFitOption
                command_limits += ' --cminPreScan --cminPreFit 1'
                command_limits += ' -o '+i_outdir+'/LimitsObserved/'+POI+'/'
                command_limits += ' --output-eos '+i_outdir_eos+'/LimitsObserved/'+POI+'/'
                command_limits += ' -n _'+n_
                command_limits += ' -d '+i_inpf
                command_limits += ' --setParameters '+paramString
                if OPT_setPar:
                    command_limits += ','+OPT_setPar
                command_limits += ' --setParameterRanges '+rangesString
                command_limits += ' --redefineSignalPOIs '+POI
                for ou in opts_unknown:
                    command_limits += ' '+ou

                if not isPseudoData:
                    EXE(command_limits, verbose = opts.verbose, dry_run = opts.dry_run)

        #######################################################################################################################
        #######################################################################################################################
        #######################################################################################################################
        # Fit [expected]
        n_ = 'nominal_exp_fit'
        command_fit = 'submitCombineJobs.py '
        command_fit += ' -M MultiDimFit'
        command_fit += ' --algo singles --saveFitResult --saveWorkspace --saveNLL --X-rtd REMOVE_CONSTANT_ZERO_POINT=1'
        command_fit += ' -m 125.38'
        command_fit += ' --robustFit 1'
        command_fit += ' --cminDefaultMinimizerStrategy 0 --X-rtd MINIMIZER_MaxCalls=999999999 --cminDefaultMinimizerTolerance 0.1'+addFitOption
        command_fit += ' --cminPreScan --cminPreFit 1'
        command_fit += ' -o '+i_outdir+'/FitExpected/'
        command_fit += ' --output-eos '+i_outdir_eos+'/FitExpected/'
        command_fit += ' -n _'+n_
        command_fit += ' -d '+i_inpf
        command_fit += ' -t -1'
        command_fit += ' --setParameters '+paramString
        if OPT_setPar:
                command_fit += ','+OPT_setPar
        command_fit += ' --setParameterRanges '+rangesString
                
        if opts.CR:
            command_fit += ' --redefineSignalPOIs xsec_ttcc,xsec_ttcj,xsec_ttbb,xsec_ttbj,xsec_ttLF,xsec_tt2b,xsec_tt2c'
            command_fit += ' --freezeParameters r'
        elif opts.CRbb:
            command_fit += ' --redefineSignalPOIs xsec_ttbb'
            command_fit += ' --freezeParameters r'
        elif opts.CRbj:
            command_fit += ' --redefineSignalPOIs xsec_ttbj'
            command_fit += ' --freezeParameters r'
        elif opts.CR2b:
            command_fit += ' --redefineSignalPOIs xsec_tt2b'
            command_fit += ' --freezeParameters r'
        elif opts.CRcc:
            command_fit += ' --redefineSignalPOIs xsec_ttcc'
            command_fit += ' --freezeParameters r'
        elif opts.CRcj:
            command_fit += ' --redefineSignalPOIs xsec_ttcj'
            command_fit += ' --freezeParameters r'
        elif opts.CR2c:
            command_fit += ' --redefineSignalPOIs xsec_tt2c'
            command_fit += ' --freezeParameters r'
        elif opts.CRlf:
            command_fit += ' --redefineSignalPOIs xsec_ttLF'
            command_fit += ' --freezeParameters r'
        elif opts.CRnolf:
            command_fit += ' --redefineSignalPOIs xsec_ttcc,xsec_ttcj,xsec_ttbj,xsec_ttbb,xsec_tt2b,xsec_tt2c'
            command_fit += ' --freezeParameters r'
        else:
            command_fit += ' --redefineSignalPOIs '
            for ipar, par in enumerate(POIs):
                if ipar == len(POIs)-1:
                    command_fit += par
                else:
                    command_fit += par+','


        for ou in opts_unknown:
            command_fit += ' '+ou

        if not isPseudoData:
            EXE(command_fit, verbose = opts.verbose, dry_run = opts.dry_run)

        # Fit [expected - a posteriori]
        n_ = 'nominal_exp_fit_freq'
        command_fit = 'submitCombineJobs.py '
        command_fit += ' -M MultiDimFit'
        command_fit += ' --algo singles --saveFitResult --saveWorkspace --saveNLL --X-rtd REMOVE_CONSTANT_ZERO_POINT=1'
        command_fit += ' -m 125.38'
        command_fit += ' --robustFit 1'
        command_fit += ' --cminDefaultMinimizerStrategy 0 --X-rtd MINIMIZER_MaxCalls=999999999 --cminDefaultMinimizerTolerance 0.1'+addFitOption
        command_fit += ' --cminPreScan --cminPreFit 1'
        command_fit += ' -o '+i_outdir+'/FitExpectedFreq/'
        command_fit += ' --output-eos '+i_outdir_eos+'/FitExpectedFreq/'
        command_fit += ' -n _'+n_
        command_fit += ' -d '+i_inpf
        command_fit += ' -t -1'
        command_fit += ' --toysFrequentist'
        command_fit += ' --setParameters '+paramString
        if OPT_setPar:
                command_fit += ','+OPT_setPar
        command_fit += ' --setParameterRanges '+rangesString
                
        if opts.CR:
            command_fit += ' --redefineSignalPOIs xsec_ttcc,xsec_ttcj,xsec_ttbb,xsec_ttbj,xsec_ttLF,xsec_tt2b,xsec_tt2c'
            command_fit += ' --freezeParameters r'
        elif opts.CRbb:
            command_fit += ' --redefineSignalPOIs xsec_ttbb'
            command_fit += ' --freezeParameters r'
        elif opts.CRbj:
            command_fit += ' --redefineSignalPOIs xsec_ttbj'
            command_fit += ' --freezeParameters r'
        elif opts.CR2b:
            command_fit += ' --redefineSignalPOIs xsec_tt2b'
            command_fit += ' --freezeParameters r'
        elif opts.CRcc:
            command_fit += ' --redefineSignalPOIs xsec_ttcc'
            command_fit += ' --freezeParameters r'
        elif opts.CRcj:
            command_fit += ' --redefineSignalPOIs xsec_ttcj'
            command_fit += ' --freezeParameters r'
        elif opts.CR2c:
            command_fit += ' --redefineSignalPOIs xsec_tt2c'
            command_fit += ' --freezeParameters r'
        elif opts.CRlf:
            command_fit += ' --redefineSignalPOIs xsec_ttLF'
            command_fit += ' --freezeParameters r'
        elif opts.CRnolf:
            command_fit += ' --redefineSignalPOIs xsec_ttcc,xsec_ttcj,xsec_ttbj,xsec_ttbb,xsec_tt2b,xsec_tt2c'
            command_fit += ' --freezeParameters r'
        else:
            command_fit += ' --redefineSignalPOIs '
            for ipar, par in enumerate(POIs):
                if ipar == len(POIs)-1:
                    command_fit += par
                else:
                    command_fit += par+','


        for ou in opts_unknown:
            command_fit += ' '+ou

        if not isPseudoData:
            EXE(command_fit, verbose = opts.verbose, dry_run = opts.dry_run)

        if opts.observed:
            # Fit [observed]
            n_ = 'nominal_obs_fit'
            command_fit = 'submitCombineJobs.py '
            command_fit += ' -M MultiDimFit'
            command_fit += ' --algo singles --saveFitResult --saveWorkspace --saveNLL --X-rtd REMOVE_CONSTANT_ZERO_POINT=1'
            command_fit += ' -m 125.38'
            command_fit += ' --robustFit 1'
            command_fit += ' --cminDefaultMinimizerStrategy 0 --X-rtd MINIMIZER_MaxCalls=999999999 --cminDefaultMinimizerTolerance 0.1'+addFitOption
            command_fit += ' --cminPreScan --cminPreFit 1'
            command_fit += ' -o '+i_outdir+'/FitObserved/'
            command_fit += ' --output-eos '+i_outdir_eos+'/FitObserved/'
            command_fit += ' -n _'+n_
            command_fit += ' -d '+i_inpf
            command_fit += ' --setParameters '+paramString
            if OPT_setPar:
                command_fit += ','+OPT_setPar
            command_fit += ' --setParameterRanges '+rangesString

            if opts.CR:
                command_fit += ' --redefineSignalPOIs xsec_ttcc,xsec_ttcj,xsec_ttbb,xsec_ttbj,xsec_ttLF,xsec_tt2b,xsec_tt2c'
                command_fit += ' --freezeParameters r'
            elif opts.CRbb:
                command_fit += ' --redefineSignalPOIs xsec_ttbb'
                command_fit += ' --freezeParameters r'
            elif opts.CRbj:
                command_fit += ' --redefineSignalPOIs xsec_ttbj'
                command_fit += ' --freezeParameters r'
            elif opts.CR2b:
                command_fit += ' --redefineSignalPOIs xsec_tt2b'
                command_fit += ' --freezeParameters r'
            elif opts.CRcc:
                command_fit += ' --redefineSignalPOIs xsec_ttcc'
                command_fit += ' --freezeParameters r'
            elif opts.CRcj:
                command_fit += ' --redefineSignalPOIs xsec_ttcj'
                command_fit += ' --freezeParameters r'
            elif opts.CR2c:
                command_fit += ' --redefineSignalPOIs xsec_tt2c'
                command_fit += ' --freezeParameters r'
            elif opts.CRlf:
                command_fit += ' --redefineSignalPOIs xsec_ttLF'
                command_fit += ' --freezeParameters r'
            elif opts.CRnolf:
                command_fit += ' --redefineSignalPOIs xsec_ttcc,xsec_ttcj,xsec_ttbj,xsec_ttbb,xsec_tt2b,xsec_tt2c'
                command_fit += ' --freezeParameters r'
            else:
                command_fit += ' --redefineSignalPOIs '
                for ipar, par in enumerate(POIs):
                    if ipar == len(POIs)-1:
                        command_fit += par
                    else:
                        command_fit += par+','



            for ou in opts_unknown:
                command_fit += ' '+ou

            # if not isPseudoData:
            if True:
                EXE(command_fit, verbose = opts.verbose, dry_run = opts.dry_run)


        #######################################################################################################################
        #######################################################################################################################
        #######################################################################################################################
        # # FitDiagnostics [expected]
        # n_ = 'nominal_exp_FitDiagnostics'
        # command_fit = 'submitCombineJobs.py '
        # command_fit += ' -M FitDiagnostics'
        # command_fit += ' --saveNormalizations --saveShapes --saveOverallShapes --saveWithUncertainties'
        # command_fit += ' --numToysForShapes 100'
        # command_fit += ' -m 125.38'
        # command_fit += ' --robustFit 1'
        # command_fit += ' --cminDefaultMinimizerStrategy 0 --X-rtd MINIMIZER_MaxCalls=999999999 --cminDefaultMinimizerTolerance 0.1'+addFitOption
        # command_fit += ' --cminPreScan --cminPreFit 1'
        # command_fit += ' -o '+i_outdir+'/FitDiagnosticsExpected/'
        # command_fit += ' --output-eos '+i_outdir_eos+'/FitDiagnosticsExpected/'
        # command_fit += ' -n _'+n_
        # command_fit += ' -d '+i_inpf
        # command_fit += ' -t -1'
        # command_fit += ' --setParameters '+paramString
        # if OPT_setPar:
        #         command_fit += ','+OPT_setPar
        # command_fit += ' --setParameterRanges '+rangesString

        # if opts.CR:
        #         command_fit += ' --redefineSignalPOIs xsec_ttcc,xsec_ttcj,xsec_ttbb,xsec_ttbj,xsec_ttLF,xsec_tt2b,xsec_tt2c'
        #         command_fit += ' --freezeParameters r'
        # else:
        #     command_fit += ' --redefineSignalPOIs '
        #     for ipar, par in enumerate(POIs):
        #         if ipar == len(POIs)-1:
        #             command_fit += par
        #         else:
        #             command_fit += par+','


        # for ou in opts_unknown:
        #     command_fit += ' '+ou

        # if not isPseudoData:
        #     EXE(command_fit, verbose = opts.verbose, dry_run = opts.dry_run)

        # if opts.observed:
        #     # FitDiagnostics [observed]
        #     n_ = 'nominal_obs_FitDiagnostics'
        #     command_fit = 'submitCombineJobs.py '
        #     command_fit += ' -M FitDiagnostics'
        #     command_fit += ' --saveNormalizations --saveShapes --saveOverallShapes --saveWithUncertainties'
        #     command_fit += ' --numToysForShapes 100'
        #     command_fit += ' -m 125.38'
        #     command_fit += ' --robustFit 1'
        #     command_fit += ' --cminDefaultMinimizerStrategy 0 --X-rtd MINIMIZER_MaxCalls=999999999 --cminDefaultMinimizerTolerance 0.1'+addFitOption
        #     command_fit += ' --cminPreScan --cminPreFit 1'
        #     command_fit += ' -o '+i_outdir+'/FitDiagnosticsObserved/'
        #     command_fit += ' --output-eos '+i_outdir_eos+'/FitDiagnosticsObserved/'
        #     command_fit += ' -n _'+n_
        #     command_fit += ' -d '+i_inpf
        #     # command_fit += ' -t -1'
        #     command_fit += ' --setParameters '+paramString
        #     if OPT_setPar:
        #             command_fit += ','+OPT_setPar
        #     command_fit += ' --setParameterRanges '+rangesString

        #     if opts.CR:
        #             command_fit += ' --redefineSignalPOIs xsec_ttcc,xsec_ttcj,xsec_ttbb,xsec_ttbj,xsec_ttLF,xsec_tt2b,xsec_tt2c'
        #             command_fit += ' --freezeParameters r'
        #     else:
        #         command_fit += ' --redefineSignalPOIs '
        #         for ipar, par in enumerate(POIs):
        #             if ipar == len(POIs)-1:
        #                 command_fit += par
        #             else:
        #                 command_fit += par+','


        #     for ou in opts_unknown:
        #         command_fit += ' '+ou

        #     if not isPseudoData:
        #         EXE(command_fit, verbose = opts.verbose, dry_run = opts.dry_run)

        #######################################################################################################################
        #######################################################################################################################
        #######################################################################################################################
        # # Toys
        for bias_toys_seed in range(101, 131):
            n_ = 'nominal_FrequentistToys'
            command_fit = 'submitCombineJobs.py '
            command_fit += ' -M MultiDimFit'
            command_fit += ' --algo singles --saveFitResult --saveWorkspace --saveNLL --X-rtd REMOVE_CONSTANT_ZERO_POINT=1'
            command_fit += ' -t 100 --toysFrequentist'
            command_fit += ' --trackParameters rgx{xsec_.*}'
            command_fit += ' -m 125.38'
            command_fit += ' --robustFit 1'
            command_fit += ' --cminDefaultMinimizerStrategy 0 --X-rtd MINIMIZER_MaxCalls=999999999 --cminDefaultMinimizerTolerance 0.1'+addFitOption
            command_fit += ' --cminPreScan --cminPreFit 1'
            command_fit += ' -o '+i_outdir+'/FrequentistToys/'
            command_fit += ' --output-eos '+i_outdir_eos+'/FrequentistToys/'
            command_fit += ' -n _'+n_
            command_fit += ' -d '+i_inpf
            command_fit += ' --seed '+str(bias_toys_seed)
            command_fit += ' --output-postfix '+str(bias_toys_seed)
            command_fit += ' --setParameters '+paramString
            if OPT_setPar:
                    command_fit += ','+OPT_setPar
            command_fit += ' --setParameterRanges '+rangesString

            if opts.CR:
                    command_fit += ' --redefineSignalPOIs xsec_ttcc,xsec_ttcj,xsec_ttbb,xsec_ttbj,xsec_ttLF,xsec_tt2b,xsec_tt2c'
                    command_fit += ' --freezeParameters r'
            else:
                command_fit += ' --redefineSignalPOIs '
                for ipar, par in enumerate(POIs):
                    if ipar == len(POIs)-1:
                        command_fit += par
                    else:
                        command_fit += par+','


            for ou in opts_unknown:
                command_fit += ' '+ou

            if isPseudoData:
                EXE(command_fit, verbose = opts.verbose, dry_run = opts.dry_run)