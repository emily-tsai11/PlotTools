
#!/bin/bash

# declare -a datacards=("Datacards_2025-03-11_MergedYears_5FSFullCorrShapeUnc_rescaleFIVEFS2MU_decor_2muF_PSSplit_simplified" "Datacards_2025-03-11_MergedYears_5FSFullCorrShapeUnc_rescaleFOURFS_decor_PSSplit_5FS_simplified")
# declare -a datacards=("Datacards_280426_smoothed_simplified" "Datacards_280426_simplified")
# declare -a datacards=("Datacards_280426_trial1_simplified")
# declare -a datacards=("Datacards_280426_trial2_simplified")
# declare -a datacards=("Datacards_280426_trial3_simplified")
# declare -a datacards=("Datacards_290426_correctedBnormalization_simplified" "Datacards_290426_correctedBnormalization_noPeterson_simplified")
# declare -a datacards=("Datacards_290426_correctedBnormalization_noPeterson_simplified")
# declare -a datacards=("Datacards_290426_correctedBnormalization_noPeterson_inflateFlav_simplified")
# declare -a datacards=("Datacards_040526_fixes_simplified")
# declare -a datacards=("Datacards_070526_ge2bge1c_simplified")
# declare -a datacards=("Datacards_070526_ge2bge1c_fix_simplified" "Datacards_070526_CRttWcbM0p2m0p8_simplified" "Datacards_070526_ge2bge1c_fix_smoothed_simplified" "Datacards_070526_CRttWcbM0p2m0p8_smoothed_simplified")
# declare -a datacards=("Datacards_070526_CRttWcbM0p2m0p8_simplified" "Datacards_070526_CRttWcbM0p2m0p8_smoothed_simplified")
# declare -a datacards=("Datacards_080526_ge2bge1c_fix_clean_simplified")
# declare -a datacards=("Datacards_080526_ge2bge1c_fix_clean_pseudoData5FS_simplified")
# declare -a datacards=("Datacards_100626_ge2bge1c_fix_clean_simplified")
# declare -a datacards=("Datacards_100626_ge2bge1c_fix_clean_pseudoData5FS_simplified")
# declare -a datacards=("Datacards_100626_ge2bge1c_fix_clean_forJME_simplified")
# declare -a datacards=("Datacards_100626_ge2bge1c_fix_clean_onlySurvivingVeto_simplified")
declare -a datacards=("Datacards_250826_preUnblinding_noFlavTagSymm_simplified" "Datacards_250826_preUnblinding_nonSmoothed_simplified" "Datacards_250826_preUnblinding_simplified")



for datacard in ${datacards[@]}; do
    echo ${datacard}
    # echo submitAllFitJobs.py -i ${datacard}/datacards/workspace_*_*.root -o ${datacard}_All --output-eos /eos/cms/store/cmst3/group/top/Vcb_trees/HTC_results/ForANv1/FitStudies_${datacard}_All ${datacard}_All -v --observed
    # nohup python3 submitAllFitJobs.py -i ${datacard}/datacards/workspace_*_*.root -o ${datacard}_All --output-eos /eos/cms/store/cmst3/group/top/Vcb_trees/HTC_results/ForANv1/FitStudies_${datacard}_All -v --observed &
    nohup python3 submitAllFitJobs.py -i ${datacard}/datacards/workspace_*_*.root -o ${datacard}_CR --output-eos /eos/cms/store/cmst3/group/top/Vcb_trees/HTC_results/preUnblinding/FitStudies_${datacard}_CR -v --observed --CR --setParameters rgx{mask_.\*_SR.\*}=1 &
    # nohup python3 submitAllFitJobs.py -i ${datacard}/datacards/workspace_*_*.root -o ${datacard}_CR --output-eos /eos/cms/store/cmst3/group/top/Vcb_trees/HTC_results/ForANv1/FitStudies_${datacard}_CR -v --observed --CR --setParameters rgx{mask_.\*_MidScoreVR.\*}=1,rgx{mask_.\*catHbb_SR.\*}=1,rgx{mask_.\*catHcc_SR.\*}=1,rgx{mask_.\*catZbb_SR.\*}=1,rgx{mask_.\*catZcc_SR.\*}=1 &
    # nohup python3 submitAllFitJobs.py -i ${datacard}/datacards/workspace_*_*.root -o ${datacard}_CRPlusTTZ --output-eos /eos/cms/store/cmst3/group/top/Vcb_trees/HTC_results/ForANv1/FitStudies_${datacard}_CRPlusTTZ -v --CRTTZ --observed --setParameters rgx{mask_.\*_MidScoreVR.\*}=1,rgx{mask_.\*catHbb_SR.\*}=1,rgx{mask_.\*catHcc_SR.\*}=1 &
    # nohup python3 submitAllFitJobs.py -i ${datacard}/datacards/workspace_*_*.root -o ${datacard}_CRPlusTTH --output-eos /eos/cms/store/cmst3/group/top/Vcb_trees/HTC_results/ForANv1/FitStudies_${datacard}_CRPlusTTH -v --CRTTH --observed --setParameters rgx{mask_.\*_MidScoreVR.\*}=1,rgx{mask_.\*catZbb_SR.\*}=1,rgx{mask_.\*catZcc_SR.\*}=1 &
    nohup python3 submitAllFitJobs.py -i ${datacard}/datacards/workspace_*_*.root -o ${datacard}_SR --output-eos /eos/cms/store/cmst3/group/top/Vcb_trees/HTC_results/preUnblinding/FitStudies_${datacard}_SR -v --observed &

    # nohup python3 submitAllFitJobs.py -i ${datacard}/datacards/workspace_*_*.root -o ${datacard}_CRbb --output-eos /eos/cms/store/cmst3/group/top/Vcb_trees/HTC_results/ForANv1/FitStudies_${datacard}_CRbb -v --observed --CRbb --setParameters rgx{mask_.\*_SR.\*}=1,mask_Vcb_catBJ_CR=1,mask_Vcb_cat2B_CR=1,mask_Vcb_catCC_CR=1,mask_Vcb_catCJ_CR=1,mask_Vcb_cat2C_CR=1,mask_Vcb_catLF_CR=1 &
    # nohup python3 submitAllFitJobs.py -i ${datacard}/datacards/workspace_*_*.root -o ${datacard}_CRbj --output-eos /eos/cms/store/cmst3/group/top/Vcb_trees/HTC_results/ForANv1/FitStudies_${datacard}_CRbj -v --observed --CRbj --setParameters rgx{mask_.\*_SR.\*}=1,mask_Vcb_catBB_CR=1,mask_Vcb_cat2B_CR=1,mask_Vcb_catCC_CR=1,mask_Vcb_catCJ_CR=1,mask_Vcb_cat2C_CR=1,mask_Vcb_catLF_CR=1 &
    # nohup python3 submitAllFitJobs.py -i ${datacard}/datacards/workspace_*_*.root -o ${datacard}_CR2b --output-eos /eos/cms/store/cmst3/group/top/Vcb_trees/HTC_results/ForANv1/FitStudies_${datacard}_CR2b -v --observed --CR2b --setParameters rgx{mask_.\*_SR.\*}=1,mask_Vcb_catBB_CR=1,mask_Vcb_catBJ_CR=1,mask_Vcb_catCC_CR=1,mask_Vcb_catCJ_CR=1,mask_Vcb_cat2C_CR=1,mask_Vcb_catLF_CR=1 &

    # nohup python3 submitAllFitJobs.py -i ${datacard}/datacards/workspace_*_*.root -o ${datacard}_CRcc --output-eos /eos/cms/store/cmst3/group/top/Vcb_trees/HTC_results/ForANv1/FitStudies_${datacard}_CRcc -v --observed --CRcc --setParameters rgx{mask_.\*_SR.\*}=1,mask_Vcb_catBJ_CR=1,mask_Vcb_cat2B_CR=1,mask_Vcb_catBB_CR=1,mask_Vcb_catCJ_CR=1,mask_Vcb_cat2C_CR=1,mask_Vcb_catLF_CR=1 &
    # nohup python3 submitAllFitJobs.py -i ${datacard}/datacards/workspace_*_*.root -o ${datacard}_CRcj --output-eos /eos/cms/store/cmst3/group/top/Vcb_trees/HTC_results/ForANv1/FitStudies_${datacard}_CRcj -v --observed --CRcj --setParameters rgx{mask_.\*_SR.\*}=1,mask_Vcb_catBB_CR=1,mask_Vcb_cat2B_CR=1,mask_Vcb_catCC_CR=1,mask_Vcb_catBJ_CR=1,mask_Vcb_cat2C_CR=1,mask_Vcb_catLF_CR=1 &
    # nohup python3 submitAllFitJobs.py -i ${datacard}/datacards/workspace_*_*.root -o ${datacard}_CR2c --output-eos /eos/cms/store/cmst3/group/top/Vcb_trees/HTC_results/ForANv1/FitStudies_${datacard}_CR2c -v --observed --CR2c --setParameters rgx{mask_.\*_SR.\*}=1,mask_Vcb_catBB_CR=1,mask_Vcb_catBJ_CR=1,mask_Vcb_catCC_CR=1,mask_Vcb_catCJ_CR=1,mask_Vcb_cat2B_CR=1,mask_Vcb_catLF_CR=1 &

    # nohup python3 submitAllFitJobs.py -i ${datacard}/datacards/workspace_*_*.root -o ${datacard}_CRlf --output-eos /eos/cms/store/cmst3/group/top/Vcb_trees/HTC_results/ForANv1/FitStudies_${datacard}_CRlf -v --observed --CRlf --setParameters rgx{mask_.\*_SR.\*}=1,mask_Vcb_catBB_CR=1,mask_Vcb_catBJ_CR=1,mask_Vcb_catCC_CR=1,mask_Vcb_catCJ_CR=1,mask_Vcb_cat2B_CR=1,mask_Vcb_cat2C_CR=1 &


    # nohup python3 submitAllFitJobs.py -i ${datacard}/datacards/workspace_*_*.root -o ${datacard}_CRnolf --output-eos /eos/cms/store/cmst3/group/top/Vcb_trees/HTC_results/ForANv1/FitStudies_${datacard}_CRnolf -v --observed --CRnolf --setParameters rgx{mask_.\*_SR.\*}=1,mask_Vcb_catLF_CR=1 &
    # nohup python3 submitAllFitJobs.py -i ${datacard}/datacards/workspace_*_*.root -o ${datacard}_SRnolf --output-eos /eos/cms/store/cmst3/group/top/Vcb_trees/HTC_results/ForANv1/FitStudies_${datacard}_SRnolf -v --observed --setParameters mask_Vcb_catLF_CR=1 &
done
