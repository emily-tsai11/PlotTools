
#!/bin/bash

declare -a datacards=("Datacards_100626_ge2bge1c_fix_clean_simplified")

export currentDir=$PWD

fitResultBasePath=/eos/cms/store/cmst3/group/top/Vcb_trees/HTC_results/ForANv1/FitStudies_


for datacard in ${datacards[@]}; do
    echo ${datacard}
    # nohup python3 submitAllFitJobs.py -i ${datacard}/datacards/workspace_*_*.root -o ${datacard}_CR --output-eos /eos/cms/store/cmst3/group/top/Vcb_trees/HTC_results/ForANv1/FitStudies_${datacard}_CR -v --observed --VR --setParameters rgx{mask_.\*_MidScoreVR.\*}=1,rgx{mask_.\*catHbb_SR.\*}=1,rgx{mask_.\*catHcc_SR.\*}=1,rgx{mask_.\*catZbb_SR.\*}=1,rgx{mask_.\*catZcc_SR.\*}=1 &
    # nohup python3 submitAllFitJobs.py -i ${datacard}/datacards/workspace_*_*.root -o ${datacard}_SR --output-eos /eos/cms/store/cmst3/group/top/Vcb_trees/HTC_results/ForANv1/FitStudies_${datacard}_SR -v --observed &

    fitResultPath_CR=${fitResultBasePath}${datacard}_CR/workspace_Vcb_SL_2024/FitObserved/
    fitResultPath_SR=${fitResultBasePath}${datacard}_SR/workspace_Vcb_SL_2024/FitExpected/
    workspacePath_CR=${currentDir}/${datacard}/datacards/workspace_Vcb_SL_2024_classic.root
    workspacePath_SR=${currentDir}/${datacard}/datacards/workspace_Vcb_SL_2024_classic.root

    cd ${datacard}
    mkdir -p PrePostFitShapes_CR
    cd PrePostFitShapes_CR
    
    # echo combineTool.py -M PostFitShapesFromWorkspace -w ${workspacePath_CR} -f ${fitResultPath_CR}/multidimfit_nominal_obs_fit.root:fit_mdf --postfit --sampling --skip-proc-errs --outdir $PWD --samples 1000 --job-mode condor  --sub-opts '+AccountingGroup = "group_u_CMST3.all"\n+JobFlavour = "tomorrow"'   #--parallel 6
    combineTool.py -M PostFitShapesFromWorkspace -w ${workspacePath_CR} -f ${fitResultPath_CR}/multidimfit_nominal_obs_fit.root:fit_mdf --postfit --sampling --skip-proc-errs --outdir $PWD --samples 1000 --job-mode condor  --sub-opts '+AccountingGroup = "group_u_CMST3.all"\n+JobFlavour = "tomorrow"'   #--parallel 6


    cd ${currentDir}

    cd ${datacard}

    mkdir -p PrePostFitShapes_SR
    cd PrePostFitShapes_SR

    # echo combineTool.py -M PostFitShapesFromWorkspace -w ${workspacePath_SR} -f ${fitResultPath_SR}/multidimfit_nominal_exp_fit.root:fit_mdf --postfit --sampling --skip-proc-errs --outdir $PWD --samples 1000 --job-mode condor  --sub-opts '+AccountingGroup = "group_u_CMST3.all"\n+JobFlavour = "tomorrow"'   #--parallel 6
        combineTool.py -M PostFitShapesFromWorkspace -w ${workspacePath_SR} -f ${fitResultPath_SR}/multidimfit_nominal_exp_fit.root:fit_mdf --postfit --sampling --skip-proc-errs --outdir $PWD --samples 1000 --job-mode condor  --sub-opts '+AccountingGroup = "group_u_CMST3.all"\n+JobFlavour = "tomorrow"'   #--parallel 6

    cd ${currentDir}

done
