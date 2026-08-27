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

      '+AccountingGroup = "group_u_CMST3.all"',

      'getenv = True',

      'should_transfer_files   = IF_NEEDED',
      'when_to_transfer_output = ON_EXIT',

      # 'requirements = (OpSysAndVer == "'+('CentOS7' if kwargs['is_slc7_arch'] else 'SL6')+'")',
      # '#requirements = (OpSysAndVer == "SL6" || OpSysAndVer == "CentOS7")',

      # 'RequestMemory  =  2000',
      # '+RequestRuntime = 10800', # 3h
      # '+RequestRuntime = 21600',   # 6h
      # '+MaxRuntime = '+('500000' if kwargs['longjob'] else '10800'), # 1 week
      # '+MaxRuntime = '+('1210000' if kwargs['longjob'] else '10800'), # 2 weeks
      # '+MaxRuntime = '+('432000' if kwargs['longjob'] else '10800'), # 5 days
      '+MaxRuntime = '+('432000' if kwargs['longjob'] else '21600'), # 5 days
      # 'RequestCpus = '+('4' if kwargs['4cores'] else '1'),
      # 'RequestCpus = '+('24' if kwargs['4cores'] else '1'),
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

    parser.add_argument('--dry-run', dest='dry_run', action='store_true', default=False,
                        help='enable dry-run mode')

    parser.add_argument('--POI', dest='POI', action='store', default="")

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
       KILL(log_prx+'option "-d" not provided (required by submitScans, add it before the path to the datacard)')

    ### -M option validation

    if '-M' in opts_unknown:
      KILL(log_prx+'input error, conflict: both option "-M" and "--Impacts" provided')

    OPT_MODE = 'MultiDimFit'

    ### -n option validation
    if '-n' in opts_unknown:
       name_idx = opts_unknown.index('-n')+1
       if name_idx >= len(opts_unknown):
          KILL(log_prx+'argument of option "-n" not available')

       OPT_NAME = opts_unknown[name_idx]

   #  else:
   #     KILL(log_prx+'option "-n" not provided (required by combine)')

    ### -m option validation
    if '-m' in opts_unknown:
       mass_idx = opts_unknown.index('-m')+1
       if mass_idx >= len(opts_unknown):
          KILL(log_prx+'argument of option "-m" not available')

       OPT_MASS = opts_unknown[mass_idx]

   #  else:
   #     KILL(log_prx+'option "-m" not provided (required by submitScans)')

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

    if VERBOSE: print ('\n'+'-'*3+' submitScans', '[NAME='+OPT_NAME+'] [MASS='+OPT_MASS+']'+'\n')

    printout_sep1 =      '-'*50+'\n'
    printout_sep2 = '\n'+'*'*28+'\n'

    if VERBOSE: print ('*'*3+' mode: '+OPT_MODE+'\n')

    OUT_DIR = os.path.abspath(os.path.realpath(opts.output))
    OUT_DIR_EOS = os.path.abspath(os.path.realpath(opts.output_eos))

    EXE('mkdir -p '+OUT_DIR, verbose=VERBOSE)
    EXE('mkdir -p '+OUT_DIR_EOS, verbose=VERBOSE)

    OUTPUTS = []

    which('combineTool.py')

    if opts_unknown[dcard_idx].endswith('.root'):

       COMBINE_OPTS = convert_args_to_lines(opts_unknown)
       opts_unknown_noCard = opts_unknown
       opts_unknown_noCard[dcard_idx] = "higgsCombine_fit_"+args.POI+".MultiDimFit.mH125.38.root"
       COMBINE_OPTS_noCard = convert_args_to_lines(opts_unknown_noCard)
       
       output_dict = {
         'output_basename': OFILE_NAME,

         'shell_commands': [

            ['BATCH_DIR=${PWD}'],
            ['set -e'],
            ['ulimit -s unlimited'],
            ['cd '+OUT_DIR ],
            ['eval `scramv1 runtime -sh`'],
            ['tempDir=${BATCH_DIR}/local/batch/myCombineCondorJob/'],
            ['echo ${tempDir}'],
            ['mkdir -p ${tempDir}'],
            ['cd ${tempDir}'],
            ['combineTool.py'] + COMBINE_OPTS+['-M '+OPT_MODE, '--algo grid --points 100 --robustFit 1 --saveFitResult --saveWorkspace --saveNLL --X-rtd REMOVE_CONSTANT_ZERO_POINT=1 -n _fit_scan_'+args.POI] + ['&> '+OFILE_NAME+'.doTotalScan.out.txt'],
            ['combineTool.py'] + COMBINE_OPTS+['-M '+OPT_MODE, '--algo singles --robustFit 1 --saveFitResult --saveWorkspace --saveNLL --X-rtd REMOVE_CONSTANT_ZERO_POINT=1 -n _fit_'+args.POI] + ['&> '+OFILE_NAME+'.doMultiDimFit.out.txt'],
            ['combineTool.py'] + COMBINE_OPTS+['-M '+COMBINE_OPTS_noCard, '--algo grid --points 100 --robustFit 1 --saveFitResult --saveWorkspace --saveNLL --X-rtd REMOVE_CONSTANT_ZERO_POINT=1 --freezeParameters allConstrainedNuisances,rgx{xsec_tt.*} --snapshotName MultiDimFit -n _fit_scan_'+args.POI+'_stat'] + ['&> '+OFILE_NAME+'.doStatScan.out.txt'],
            ['plot1DScan.py'] + ['higgsCombine_fit_scan_'+args.POI+".MultiDimFit.mH125.38.root"] + ['--main-label Total --POI '+args.POI] + ['--others higgsCombine_fit_scan_'+args.POI+"_stat.MultiDimFit.mH125.38.root:StatOnly:2 -o scan_"+args.POI],
            ['cp *.root *.txt *.pdf *.png *.json '+OUT_DIR_EOS+'/' ],
            ['rm -rf *.root *.txt *.pdf *.png *.json' ],
            ['touch '+OUT_DIR+"/"+OFILE_NAME+'.completed'],
         ],
       }

       OUTPUTS.append(output_dict)

    else:
       KILL(log_prx+'invalid extension for input datacard (must be .root): '+opts_unknown[dcard_idx])

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

               #  '4cores': ('Scans' in i_output_basename),
                '4cores': (False),
                'longjob': ('Scans' in i_output_basename or 'GoodnessOfFit' in i_output_basename),
              })

    ## ----------------

    if VERBOSE: print (printout_sep1)
#### ----
