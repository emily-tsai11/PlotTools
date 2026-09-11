#!/usr/bin/env python3
"""
 simple wrapper to organize combine commands in scripts, for submission to the batch system
"""
import argparse
import os
import ROOT

from utilities.auxiliary   import *
# from utilities.utils_datacard import *


def batch_job_HTCondor(**kwargs):

    _OUTPUT_DIR = os.path.abspath(os.path.realpath(kwargs['output_directory']))

    EXE('mkdir -p '+_OUTPUT_DIR+'/'+kwargs['output_subdirectory'], verbose=kwargs['verbose'], dry_run=kwargs['dry_run'])

    _OFILE_ABSPATH = _OUTPUT_DIR+'/'+kwargs['output_basename']+'.sh'

    if os.path.exists(_OFILE_ABSPATH):
       KILL(log_prx+' -- batch_job_HTCondor: target output file already exists: '+_OFILE_ABSPATH)

    # batch configuration options
    _OPTS = [
      'batch_name = '+kwargs['output_basename'],

      'executable = '+_OFILE_ABSPATH,

      'output = '+_OUTPUT_DIR+'/'+kwargs['output_subdirectory']+'/'+kwargs['output_basename']+'.out.$(Cluster).$(Process)',
      'error  = '+_OUTPUT_DIR+'/'+kwargs['output_subdirectory']+'/'+kwargs['output_basename']+'.err.$(Cluster).$(Process)',
      'log    = '+_OUTPUT_DIR+'/'+kwargs['output_subdirectory']+'/'+kwargs['output_basename']+'.log.$(Cluster).$(Process)',

      '#arguments = ',

      'transfer_executable = True',

      # 'universe = vanilla',

      '+AccountingGroup = "group_u_CMST3.all"',

      'getenv = True',

      'should_transfer_files   = IF_NEEDED',
      'when_to_transfer_output = ON_EXIT',

      # 'requirements = (OpSysAndVer == "'+('CentOS7' if kwargs['is_slc7_arch'] else 'SL6')+'")',
      # '#requirements = (OpSysAndVer == "SL6" || OpSysAndVer == "CentOS7")',

      # 'RequestMemory = 2000',
      # '+RequestRuntime = 10800', # 3h
      # '+RequestRuntime = 10799', # 3h
      # '+RequestRuntime = 21600',   # 6h

      # '+MaxRuntime = '+('500000' if kwargs['longjob'] else '10800'),
      # '+MaxRuntime = '+('605000' if kwargs['longjob'] else '10800'), # 1 week
      # '+MaxRuntime = '+('1210000' if kwargs['longjob'] else '10800'),  # 2 weeks
      '+MaxRuntime = '+('432000' if kwargs['longjob'] else '10800'),  # 5 days
      'RequestCpus = '+('10' if kwargs['4cores'] else '1'),

      # 'MY.WantOS = "el7"',

      'queue',
    ]

    _UPDATED_OPTS = []

    _ADDED_OPTS = (kwargs['submit_options'] if 'submit_options' in kwargs else [])

    for _tmp_opt in _OPTS[:-1]:

        _tmp_opt_keyw = _tmp_opt.split('=')[0].replace(' ','')

        _tmp_skip_opt = False

        for _tmp_add_opt in _ADDED_OPTS:

            _tmp_add_opt_keyw = _tmp_add_opt.split('=')[0].replace(' ','')

            if _tmp_opt_keyw == _tmp_add_opt_keyw: _tmp_skip_opt = True; break;

        if _tmp_skip_opt: continue

        _UPDATED_OPTS += [_tmp_opt]

    for _tmp_add_opt in _ADDED_OPTS: _UPDATED_OPTS += [_tmp_add_opt]

    if 'queue' not in _UPDATED_OPTS[-1]: _UPDATED_OPTS += ['queue']

    _o_file = open(_OFILE_ABSPATH, 'w')

    _o_shebang = '#!/bin/bash'
    _o_file.write(_o_shebang+'\n')

    # HTCondor getenv=True does not export LD_LIBRARY_PATH
    # --> added by hand in the script itself
    if 'LD_LIBRARY_PATH' in os.environ:
       _o_file.write('\n'+'export LD_LIBRARY_PATH='+os.environ['LD_LIBRARY_PATH']+'\n')

    _o_file.write('\n'+kwargs['output_string']+'\n')

    _o_file.close()

    print ('\033[1m'+'\033[94m'+'output:'+'\033[0m', os.path.relpath(_OFILE_ABSPATH, os.environ['PWD']))

    EXE('chmod u+x '+_OFILE_ABSPATH, verbose=kwargs['verbose'], dry_run=kwargs['dry_run'])

    _OFCFG_ABSPATH = os.path.splitext(_OFILE_ABSPATH)[0]+'.htc'

    _o_fcfg = open(_OFCFG_ABSPATH, 'w')

    for _tmp in _UPDATED_OPTS: _o_fcfg.write(_tmp+'\n')

    _o_fcfg.close()

    if kwargs['submit']:
       EXE('condor_submit '+_OFCFG_ABSPATH, suspend=False, verbose=kwargs['verbose'], dry_run=kwargs['dry_run'])

    return

def convert_args_to_lines(args):

    _tmp_lines = []

    _tmp_idxs = [0] + [i_idx for i_idx, i_opt in enumerate(args) if i_opt.startswith('-') and not (is_int(i_opt) or is_float(i_opt))] + [len(args)]
    _tmp_idxs = sorted(list(set(_tmp_idxs)))

    for j_idx in range(len(_tmp_idxs)-1):
        _tmp_lines += [' '.join(args[_tmp_idxs[j_idx]:_tmp_idxs[j_idx+1]])]

    del _tmp_idxs

    return _tmp_lines

#### main
if __name__ == '__main__':
    ### args
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('-o', '--output', dest='output', action='store', default=None,
                        help='path to output directory')

    parser.add_argument('--output-eos', dest='output_eos', action='store', default=None,
                        help='path to output directory on eos for real files')

    parser.add_argument('--output-postfix', dest='output_postfix', action='store', default=None,
                        help='post-fix to output basename (example: seed number when generating toys)')

    parser.add_argument('--batch', dest='batch', choices=['htc'], action='store', default='htc',
                        help='type of batch system for job submission')

    parser.add_argument('--htc-opts', dest='htc_opts', nargs='+', default=[],
                        help='list of options for HTCondor submission script')

    parser.add_argument('--submit', dest='submit', action='store_true', default=False,
                        help='submit job(s) on the batch system')

    parser.add_argument('--local', dest='local', action='store_true', default=False,
                        help='execute job(s) locally')

    parser.add_argument('--Impacts', dest='Impacts', action='store_true', default=False,
                        help='implements Impacts workflow (requires combineTool.py from package CombineHarvester/)')

    parser.add_argument('--NLLScans', dest='NLLScans', action='store_true', default=False,
                        help='implements NLL-Scans workflow (base command: "combine -M MultiDimFit --algo grid")')

    parser.add_argument('--dry-run', dest='dry_run', action='store_true', default=False,
                        help='enable dry-run mode')

    opts, opts_unknown = parser.parse_known_args()
    ### -------------------------

    log_prx = os.path.basename(__file__)+' -- '

    ### opts --------------------

    combine_exe = 'combine'

    which(combine_exe)

    if opts.batch != None:
       if opts.submit and (not opts.dry_run):
          if opts.batch == 'sge': which('qsub')
          else: which('condor_submit')

    if not opts.output:
       KILL(log_prx+'unspecified path to output directory [-o]')

   #  is_slc7_arch = False
   #  if os.environ['SCRAM_ARCH'].startswith('slc7'): is_slc7_arch = True
   #  elif os.environ['SCRAM_ARCH'].startswith('slc6'): pass
   #  else:
   #     KILL(log_prx+'could not infer architecture from environment variable "SCRAM_ARCH": '+str(os.environ['SCRAM_ARCH']))

    ### -d option validation
    if '-d' in opts_unknown:
       dcard_idx = opts_unknown.index('-d')+1
       if dcard_idx >= len(opts_unknown):
          KILL(log_prx+'argument of option "-d" not available')

       f_dcard = opts_unknown[dcard_idx]
       if not os.path.isfile(f_dcard):
          KILL(log_prx+'path to input datacard (argument "-d") not found: '+f_dcard)

       opts_unknown[dcard_idx] = os.path.abspath(os.path.realpath(f_dcard))

    else:
       KILL(log_prx+'option "-d" not provided (required by submitCombineJobs, add it before the path to the datacard)')

    ### -M option validation
    if opts.Impacts and opts.NLLScans:
       KILL(log_prx+'input error, conflict: both options "--Impacts" and "--NLLScans" provided')

    if opts.Impacts:

       if '-M' in opts_unknown:
          KILL(log_prx+'input error, conflict: both option "-M" and "--Impacts" provided')

       OPT_MODE = 'Impacts'

    elif opts.NLLScans:

       if '-M' in opts_unknown:
          KILL(log_prx+'input error, conflict: both option "-M" and "--NLLScans" provided')

       OPT_MODE = 'NLLScans'

    else:

       if '-M' in opts_unknown:
          mode_idx = opts_unknown.index('-M')+1
          if mode_idx >= len(opts_unknown):
             KILL(log_prx+'argument of option "-M" not available')

          OPT_MODE = opts_unknown[mode_idx]

       else:
          KILL(log_prx+'option "-M" not provided (required by combine)')

    ### -n option validation
    if '-n' in opts_unknown:
       name_idx = opts_unknown.index('-n')+1
       if name_idx >= len(opts_unknown):
          KILL(log_prx+'argument of option "-n" not available')

       OPT_NAME = opts_unknown[name_idx]

    else:
       KILL(log_prx+'option "-n" not provided (required by combine)')

    ### -m option validation
    if '-m' in opts_unknown:
       mass_idx = opts_unknown.index('-m')+1
       if mass_idx >= len(opts_unknown):
          KILL(log_prx+'argument of option "-m" not available')

       OPT_MASS = opts_unknown[mass_idx]

    else:
       KILL(log_prx+'option "-m" not provided (required by submitCombineJobs)')

    ### -v option validation
    OPT_VERB = 0

    if '-v' in opts_unknown:
       verb_idx = opts_unknown.index('-v')+1
       if verb_idx >= len(opts_unknown):
          KILL(log_prx+'argument of option "-v" not available')

       OPT_VERB = opts_unknown[verb_idx]

    ### convert valid file paths to absolute paths
    for i_idx, i_opt in enumerate(opts_unknown):

        if os.path.isfile(i_opt): opts_unknown[i_idx] = os.path.abspath(os.path.realpath(i_opt))

    VERBOSE = bool((int(OPT_VERB) > 0) and not opts.submit)

    ### -------------------------

    OFILE_NAME = 'higgsCombine'+OPT_NAME+'.'+OPT_MODE+'.'+'mH'+OPT_MASS.replace('.','p')
    if opts.output_postfix != None: OFILE_NAME += '.'+opts.output_postfix

    if VERBOSE: print ('\n'+'-'*3+' submitCombineJobs', '[NAME='+OPT_NAME+'] [MASS='+OPT_MASS+']'+'\n')

    printout_sep1 =      '-'*50+'\n'
    printout_sep2 = '\n'+'*'*28+'\n'

    if VERBOSE: print ('*'*3+' mode: '+OPT_MODE+'\n')

    OUT_DIR = os.path.abspath(os.path.realpath(opts.output))
    OUT_DIR_EOS = os.path.abspath(os.path.realpath(opts.output_eos))

    EXE('mkdir -p '+OUT_DIR, verbose=VERBOSE)
    EXE('mkdir -p '+OUT_DIR_EOS, verbose=VERBOSE)

    OUTPUTS = []

    if opts.Impacts:

       which('combineTool.py')

       # if .txt input, run --doFits in one single job
       # (not possible to access full list of nuisances in the statistical model from .txt file)
       if opts_unknown[dcard_idx].endswith('.txt'):

          COMBINE_OPTS = convert_args_to_lines(opts_unknown)

          output_dict = {

            'output_basename': OFILE_NAME,

            'shell_commands': [

              [ 'set -e' ],
              ['ulimit -s unlimited'],
              [ 'cd '+OUT_DIR ],
              [ 'eval `scramv1 runtime -sh`' ],
              [ 'cd '+OUT_DIR_EOS ],
              ['combineTool.py'] + COMBINE_OPTS+['-M '+OPT_MODE, '--doInitialFit']           + ['&> '+OFILE_NAME+'.doInitialFit.out.txt'],
              ['combineTool.py'] + COMBINE_OPTS+['-M '+OPT_MODE, '--doFits', '--parallel 4'] + ['&> '+OFILE_NAME+'.doFits.out.txt'],
              ['combineTool.py'] + COMBINE_OPTS+['-M '+OPT_MODE, '-o '+OFILE_NAME+'.json']   + ['&> '+OFILE_NAME+'.json.out.txt'],
            #   ['plotImpacts.py'] + ['--blind'] + ['-i '+OFILE_NAME+'.json'] + ['-o '+OFILE_NAME],
              ['plotImpacts.py'] + ['-i '+OFILE_NAME+'.json'] + ['-o '+OFILE_NAME],
            #   ['touch '+OFILE_NAME+'.completed'],
              ['touch '+OUT_DIR+"/"+OFILE_NAME+'.completed'],
            ],
          }

          OUTPUTS.append(output_dict)

       # if .root input, read list of nuisances and POIs from RooWorkspace
       elif opts_unknown[dcard_idx].endswith('.root'):

          tmp_file = ROOT.TFile(opts_unknown[dcard_idx])

          tmp_ws = tmp_file.Get('w')
          if not tmp_ws:
             KILL(log_prx+'RooWorkspace in input datacard not found: '+opts_unknown[dcard_idx]+':w')

          params_POIs    = ws_keys_from_set      (workspace=tmp_ws, set_key='ModelConfig_POI')
          params_nonPOIs = ws_keys_all_parameters(workspace=tmp_ws, model_config='ModelConfig', skip=params_POIs)

          tmp_file.Close()

          if len(params_nonPOIs) == 0:
             log_msg  = 'RooWorkspace in input datacard has no parameters (other than POIs='+str(params_POIs)+')'
             log_msg += ' in object "ModelConfig".'
             log_msg += ' Ignoring --Impacts.'
             WARNING(log_prx+log_msg)

          elif len(params_POIs) == 0:
             log_msg  = 'RooWorkspace in input datacard has no parameters'
             log_msg += ' in RooArgSet="ModelConfig_POI".'
             log_msg += ' Ignoring --Impacts.'
             WARNING(log_prx+log_msg)

          elif len(params_POIs) != 1:
             log_msg  = 'RooWorkspace in input datacard has more than 1 parameter ('+str(len(params_POIs))+')'
             log_msg += ' in RooArgSet="ModelConfig_POI".'
             log_msg += ' Ignoring --Impacts (unsupported case).'
             WARNING(log_prx+log_msg)

          else:
             ### Impacts: initial fit to POI

             # replace arg of -n option
             initialFit_opts = opts_unknown[:]
             initialFit_opts[name_idx] = '_initialFit_'+initialFit_opts[name_idx]

             initialFit_optLines = convert_args_to_lines(initialFit_opts)

             initialFit_optLines += [
               '-M MultiDimFit',
               '--redefineSignalPOIs '+params_POIs[0],
               '--algo singles',
               # '--robustFit 1',
             ]

             initialFit_outfileBasename = 'higgsCombine'+initialFit_opts[name_idx]+'.MultiDimFit.mH'+OPT_MASS.replace('.','p')
             if opts.output_postfix != None: initialFit_outfileBasename += '.'+opts.output_postfix

             output_dict = {

               'output_basename': initialFit_outfileBasename,

               'shell_commands': [

                 [ 'set -e' ],
                 ['ulimit -s unlimited'],
                 [ 'cd '+OUT_DIR ],
                 [ 'eval `scramv1 runtime -sh`' ],
                 [ 'cd '+OUT_DIR_EOS ],
                 [combine_exe] + initialFit_optLines + ['&> '+initialFit_outfileBasename+'.out.txt'],
               #   ['touch '+initialFit_outfileBasename+'.completed'],
                 ['touch '+OUT_DIR+"/"+initialFit_outfileBasename+'.completed'],
               ],
             }

             OUTPUTS.append(output_dict)
             ### ------------------------------------------

             ### Impacts: impact of each nuisance parameter
             for i_nuip in params_nonPOIs:

                 # replace arg of -n option
                 nuipImpact_opts = opts_unknown[:]
                 nuipImpact_opts[name_idx] = '_paramFit_'+nuipImpact_opts[name_idx]+'_'+i_nuip

                 nuipImpact_optLines = convert_args_to_lines(nuipImpact_opts)

                 nuipImpact_optLines += [
                   '-M MultiDimFit',
                   '--redefineSignalPOIs '+params_POIs[0],
                   '--floatOtherPOIs 1',
                   '--saveInactivePOI 1',
                   '--algo impact',
                   '-P '+i_nuip,
                 ]

                 nuipImpact_outfileBasename = 'higgsCombine'+nuipImpact_opts[name_idx]+'.MultiDimFit.mH'+OPT_MASS.replace('.','p')
                 if opts.output_postfix != None: nuipImpact_outfileBasename += '.'+opts.output_postfix

                 output_dict = {

                   'output_basename': nuipImpact_outfileBasename,

                   'shell_commands': [

                     [ 'set -e' ],
                     ['ulimit -s unlimited'],
                     [ 'cd '+OUT_DIR ],
                     [ 'eval `scramv1 runtime -sh`' ],
                     [ 'cd '+OUT_DIR_EOS ],
                     [combine_exe] + nuipImpact_optLines + ['&> '+nuipImpact_outfileBasename+'.out.txt'],
                     # ['touch '+nuipImpact_outfileBasename+'.completed'],
                     ['touch '+OUT_DIR+"/"+nuipImpact_outfileBasename+'.completed'],
                   ],
                 }

                 OUTPUTS.append(output_dict)
             ### ------------------------------------------

             ### Helper script to create impacts.json file (once jobs are finished)

             out_file = open(OUT_DIR+'/'+OFILE_NAME+'.sh', 'w')

             out_file.write('#!/bin/bash'+'\n')

             out_cmds = [

               'set -e',
               'ulimit -s unlimited',
               'cd '+OUT_DIR,
               'combineTool.py -M Impacts -n '+OPT_NAME+' -m '+OPT_MASS+' -o '+OFILE_NAME+'.json \\\n -d '+opts_unknown[dcard_idx],
               'plotImpacts.py -i '+OFILE_NAME+'.json -o '+OFILE_NAME,
               # 'plotImpacts.py --blind -i '+OFILE_NAME+'.json -o '+OFILE_NAME,
             ]

             for _tmp in out_cmds: out_file.write('\n'+_tmp+'\n')

             out_file.close()

             EXE('chmod u+x '+OUT_DIR+'/'+OFILE_NAME+'.sh', verbose=VERBOSE, dry_run=opts.dry_run)

             ### ------------------------------------------

       else:
          KILL(log_prx+'invalid extension for input datacard (must be .txt or .root): '+opts_unknown[dcard_idx])

    elif opts.NLLScans:

       # if .root input, read list of nuisances and POIs from RooWorkspace
       if opts_unknown[dcard_idx].endswith('.root'):

          tmp_file = ROOT.TFile(opts_unknown[dcard_idx])

          tmp_ws = tmp_file.Get('w')
          if not tmp_ws:
             KILL(log_prx+'RooWorkspace in input datacard not found: '+opts_unknown[dcard_idx]+':w')

          params_POIs    = ws_keys_from_set      (workspace=tmp_ws, set_key='ModelConfig_POI')
          params_nonPOIs = ws_keys_all_parameters(workspace=tmp_ws, model_config='ModelConfig', skip=params_POIs)

          tmp_file.Close()

          if len(params_nonPOIs) == 0:
             log_msg  = 'RooWorkspace in input datacard has no parameters (other than POIs='+str(params_POIs)+')'
             log_msg += ' in object "ModelConfig".'
             log_msg += ' Ignoring --NLLScans.'
             WARNING(log_prx+log_msg)

          elif len(params_POIs) == 0:
             log_msg  = 'RooWorkspace in input datacard has no parameters'
             log_msg += ' in RooArgSet="ModelConfig_POI".'
             log_msg += ' Ignoring --NLLScans.'
             WARNING(log_prx+log_msg)

          elif len(params_POIs) != 1:
             log_msg  = 'RooWorkspace in input datacard has more than 1 parameter ('+str(len(params_POIs))+')'
             log_msg += ' in RooArgSet="ModelConfig_POI".'
             log_msg += ' Ignoring --NLLScans (unsupported case).'
             WARNING(log_prx+log_msg)

          else:

             ### NLLScans: NLL-scan of each nuisance parameter
             for i_nuip in params_nonPOIs:

                 # replace arg of -n option
                 nuipNLLScan_opts = opts_unknown[:]
                 nuipNLLScan_opts[name_idx] = '_grid'+nuipNLLScan_opts[name_idx]+'_'+i_nuip

                 nuipNLLScan_optLines = convert_args_to_lines(nuipNLLScan_opts)

                 nuipNLLScan_optLines += [
                   '-M MultiDimFit',
                   '--algo grid',
                   '-P '+i_nuip,
                 ]

                 nuipNLLScan_outfileBasename = 'higgsCombine'+nuipNLLScan_opts[name_idx]+'.MultiDimFit.mH'+OPT_MASS.replace('.','p')
                 if opts.output_postfix != None: nuipNLLScan_outfileBasename += '.'+opts.output_postfix

                 output_dict = {

                   'output_basename': nuipNLLScan_outfileBasename,

                   'shell_commands': [

                     [ 'set -e' ],
                     ['ulimit -s unlimited'],
                     [ 'cd '+OUT_DIR ],
                     [combine_exe] + nuipNLLScan_optLines + ['&> '+nuipNLLScan_outfileBasename+'.out.txt'],
                     # ['touch '+nuipNLLScan_outfileBasename+'.completed'],
                     ['touch '+OUT_DIR+"/"+nuipNLLScan_outfileBasename+'.completed'],
                   ],
                 }

                 OUTPUTS.append(output_dict)
             ### ------------------------------------------

       else:
          KILL(log_prx+'invalid extension for input datacard (must be .root for --NLLScans): '+opts_unknown[dcard_idx])

    else:

       COMBINE_OPTS = convert_args_to_lines(opts_unknown)

       output_dict = {

         'output_basename': OFILE_NAME,

         'shell_commands': [

           [ 'BATCH_DIR=${PWD}' ],
           [ 'set -e' ],
           ['ulimit -s unlimited'],
           [ 'cd '+OUT_DIR ],
           [ 'eval `scramv1 runtime -sh`' ],
           ['tempDir=${BATCH_DIR}/local/batch/myCombineCondorJob/'],
           ['echo ${tempDir}'],
           ['mkdir -p ${tempDir}'],
           ['cd ${tempDir}'],
           [combine_exe] + COMBINE_OPTS + ['&> '+OFILE_NAME+'.out.txt'],
           [ 'cp *.root *.txt '+OUT_DIR_EOS+'/' ],
           [ 'rm -rf *.root *.txt' ],
           ['touch '+OUT_DIR+"/"+OFILE_NAME+'.completed'],
         ],
       }

       OUTPUTS.append(output_dict)

    ### create outputs
    for i_output_dict in OUTPUTS:

        i_shell_commands  = i_output_dict['shell_commands']
        i_output_basename = i_output_dict['output_basename']

        if opts.local:
           EXECS = [' '.join(_tmp) for _tmp in i_shell_commands]
           print (' && '.join(EXECS))
           EXE(' && '.join(EXECS), verbose=VERBOSE, dry_run=opts.dry_run)

        else:

           if opts.batch == 'htc':

              batch_job_HTCondor(**{

                'output_string': '\n\n'.join([' \\\n '.join(_tmp) for _tmp in i_shell_commands]),
                'output_basename': i_output_basename,
                'output_directory': OUT_DIR,
                'output_directory_eos': OUT_DIR_EOS,
                'output_subdirectory': opts.batch,

                'submit' : opts.submit,

                'verbose': VERBOSE,
                'dry_run': opts.dry_run,

                'submit_options': opts.htc_opts,

               #  'is_slc7_arch': is_slc7_arch,
                '4cores': ('Impacts' in i_output_basename),
               #  'longjob': ('Impacts' in i_output_basename or 'GoodnessOfFit' in i_output_basename or 'FitDiagnostics' in i_output_basename),
                'longjob': ('Impacts' in i_output_basename or 'GoodnessOfFit' in i_output_basename or 'FitDiagnostics' in i_output_basename or 'FrequentistToys' in i_output_basename),
              })

    ## ----------------

    if VERBOSE: print (printout_sep1)
#### ----
