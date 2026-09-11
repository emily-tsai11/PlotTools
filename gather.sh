# declare -a datacards=("140824_FullSet_smoothedUnweightedspline" "140824_FullSet_smoothedUnweightedspline_part" "140824_FullSet")
# declare -a datacards=("2024-09-20" "2024-09-20_AMCATShapeUnc" "2024-09-20_MergedYears" "2024-09-20_MergedYears_AMCATShapeUnc" "2024-09-20_MergedYears_extrapolationUnc" "2024-09-20_extrapolationUnc")
# declare -a datacards=("2024-09-20_MergedYears" "2024-09-20_MergedYears_AMCATShapeUnc" "2024-09-20_MergedYears_extrapolationUnc")
# declare -a datacards=("2024-10-10_MergedYears" "2024-10-10_MergedYears_AMCATShapeUnc" "2024-10-10_MergedYears_AMCATCorrShapeUnc" "2024-10-10_MergedYears_extrapolationUnc" "2024-10-10_MergedYears_FourierShapeUnc")
# declare -a datacards=("2024-10-15_MergedYears" "2024-10-15_MergedYears_AMCATShapeUnc" "2024-10-15_MergedYears_AMCATCorrShapeUnc" "2024-10-15_MergedYears_extrapolationUnc" "2024-10-15_MergedYears_FourierShapeUnc")
# declare -a datacards=("2024-10-15_MergedYears")
# declare -a datacards=("2024-11-06_MergedYears")
# declare -a datacards=("2024-10-15_MergedYears" "2024-10-15_MergedYears_AMCATShapeUnc" "2024-10-15_MergedYears_AMCATCorrShapeUnc" "2024-10-15_MergedYears_extrapolationUnc" "2024-10-15_MergedYears_FourierShapeUnc")
# declare -a datacards=("2024-11-15_MergedYears" "2024-11-15_MergedYears_pseudoDataHERWIG" "2024-11-15_MergedYears_pseudoData5FS" "2024-11-15_MergedYears_pseudoDataAMCATNLOFXFX" "2024-11-15_MergedYears_pseudoData4FS" "2024-11-15_MergedYears_HERWIGFullCorrShapeUnc_rescaleHERWIG" "2024-11-15_MergedYears_HERWIGFullCorrShapeUnc_pseudoDataHERWIG_rescaleHERWIG" "2024-11-15_MergedYears_HERWIGFullCorrShapeUnc_pseudoData5FS_rescaleHERWIG" "2024-11-15_MergedYears_HERWIGFullCorrShapeUnc_pseudoData4FS_rescaleHERWIG" "2024-11-15_MergedYears_HERWIGFullCorrShapeUnc_pseudoDataAMCATNLOFXFX_rescaleHERWIG")
# declare -a datacards=("2024-11-19_MergedYears_5FSFullCorrShapeUnc_rescaleFIVEFS" "2024-11-19_MergedYears_5FSFullCorrShapeUnc_pseudoData4FS_rescaleFIVEFS" "2024-11-19_MergedYears_5FSFullCorrShapeUnc_pseudoData5FS_rescaleFIVEFS" "2024-11-19_MergedYears_5FSFullCorrShapeUnc_pseudoDataHERWIG_rescaleFIVEFS" "2024-11-19_MergedYears_5FSFullCorrShapeUnc_pseudoDataAMCATNLOFXFX_rescaleFIVEFS" "2024-11-19_MergedYears" "2024-11-19_MergedYears_pseudoData4FS" "2024-11-19_MergedYears_pseudoData5FS" "2024-11-19_MergedYears_pseudoDataHERWIG" "2024-11-19_MergedYears_pseudoDataAMCATNLOFXFX")
# declare -a datacards=("2024-11-19_MergedYears_5FSFullCorrShapeUnc_rescaleFIVEFS_decor" "2024-11-19_MergedYears_5FSFullCorrShapeUnc_rescaleFIVEFS_decorOne")
# declare -a datacards=("2024-11-19_MergedYears_5FSFullCorrShapeUnc_rescaleFIVEFS")
# declare -a datacards=("2024-11-19_MergedYears_5FSFullCorrShapeUnc_rescaleFIVEFS_decor")
# declare -a datacards=("2024-12-17_MergedYears_5FSFullCorrShapeUnc_rescaleFIVEFS_decor")
# declare -a datacards=("2024-12-17_MergedYears_5FSFullCorrShapeUnc_rescaleFIVEFS_decor_fixed" "2024-12-17_MergedYears_5FSFullCorrShapeUnc_rescaleMODEL_decor_fixed" "2024-12-18_MergedYears_5FSFullCorrShapeUnc_rescaleMODEL_decor" "2024-12-18_MergedYears_5FSFullCorrShapeUnc_rescaleFIVEFS_decor")
# declare -a datacards=("2024-12-18_MergedYears_5FSFullCorrShapeUnc_rescaleMODEL_decor" "2024-12-18_MergedYears_5FSFullCorrShapeUnc_rescaleFIVEFS_decor")
# declare -a datacards=("2024-12-17_MergedYears_5FSFullCorrShapeUnc_rescaleFIVEFS_decor_fixed_strategy0")

# for datacard in ${datacards[@]}; do
#     echo ${datacard}
#     mkdir -p  /eos/home-s/sewuchte/www/ttH/Nov24/BehaviorStudies_${datacard}
#     echo gatherResults.py -i /eos/cms/store/cmst3/group/top/Vcb_trees/HTC_results/ttHcc_ANv4/FitStudies_Datacards_${datacard}_simplified_VR/ -o /eos/home-s/sewuchte/www/ttH/Nov24/BehaviorStudies_${datacard}/ -f results_VR_exp.html
#     python3 gatherResults.py -i /eos/cms/store/cmst3/group/top/Vcb_trees/HTC_results/ttHcc_ANv4/FitStudies_Datacards_${datacard}_simplified_VR/ -o /eos/home-s/sewuchte/www/ttH/Nov24/BehaviorStudies_${datacard}/ -f results_VR_exp.html
#     python3 gatherResults.py -i /eos/cms/store/cmst3/group/top/Vcb_trees/HTC_results/ttHcc_ANv4/FitStudies_Datacards_${datacard}_simplified_VR/ -o /eos/home-s/sewuchte/www/ttH/Nov24/BehaviorStudies_${datacard}/ -f results_VR_obs.html --obs
#     python3 gatherResults.py -i /eos/cms/store/cmst3/group/top/Vcb_trees/HTC_results/ttHcc_ANv4/FitStudies_Datacards_${datacard}_simplified_SR/ -o /eos/home-s/sewuchte/www/ttH/Nov24/BehaviorStudies_${datacard}/ -f results_SR_exp.html
#     # python3 gatherResults.py -i /eos/cms/store/cmst3/group/top/Vcb_trees/HTC_results/ttHcc_ANv4/FitStudies_Datacards_${datacard}_simplified_SR/ -o /eos/home-s/sewuchte/www/ttH/Nov24/BehaviorStudies_${datacard}/ -f results_SR_obs.html --obs
#     python3 gatherResults.py -i /eos/cms/store/cmst3/group/top/Vcb_trees/HTC_results/ttHcc_ANv4/FitStudies_Datacards_${datacard}_simplified_CR/ -o /eos/home-s/sewuchte/www/ttH/Nov24/BehaviorStudies_${datacard}/ -f results_CR_exp.html
#     python3 gatherResults.py -i /eos/cms/store/cmst3/group/top/Vcb_trees/HTC_results/ttHcc_ANv4/FitStudies_Datacards_${datacard}_simplified_CR/ -o /eos/home-s/sewuchte/www/ttH/Nov24/BehaviorStudies_${datacard}/ -f results_CR_obs.html --obs
#     python3 gatherResults.py -i /eos/cms/store/cmst3/group/top/Vcb_trees/HTC_results/ttHcc_ANv4/FitStudies_Datacards_${datacard}_simplified_CRPlusTTZ/ -o /eos/home-s/sewuchte/www/ttH/Nov24/BehaviorStudies_${datacard}/ -f results_CRPlusTTZ_obs.html --obs
#     python3 gatherResults.py -i /eos/cms/store/cmst3/group/top/Vcb_trees/HTC_results/ttHcc_ANv4/FitStudies_Datacards_${datacard}_simplified_CRPlusTTZ/ -o /eos/home-s/sewuchte/www/ttH/Nov24/BehaviorStudies_${datacard}/ -f results_CRPlusTTZ_exp.html
#     # python3 gatherResults.py -i /eos/cms/store/cmst3/group/top/Vcb_trees/HTC_results/ttHcc_ANv4/FitStudies_Datacards_${datacard}_simplified_CRPlusTTH/ -o /eos/home-s/sewuchte/www/ttH/Nov24/BehaviorStudies_${datacard}/ -f results_CRPlusTTH_obs.html --obs
#     python3 gatherResults.py -i /eos/cms/store/cmst3/group/top/Vcb_trees/HTC_results/ttHcc_ANv4/FitStudies_Datacards_${datacard}_simplified_CRPlusTTH/ -o /eos/home-s/sewuchte/www/ttH/Nov24/BehaviorStudies_${datacard}/ -f results_CRPlusTTH_exp.html
# done

# for datacard in ${datacards[@]}; do
#     echo ${datacard}
#     mkdir -p  /eos/home-s/sewuchte/www/backup/private/BehaviorStudies_${datacard}
#     # echo gatherResults.py -i /eos/cms/store/cmst3/group/top/Vcb_trees/HTC_results/ttHcc_ANv4/FitStudies_Datacards_${datacard}_simplified_VR/ -o /eos/home-s/sewuchte/www/backup/private/BehaviorStudies_${datacard}/ -f results_VR_exp.html
#     python3 gatherResults.py -i /eos/cms/store/cmst3/group/top/Vcb_trees/HTC_results/ttHcc_ANv4/FitStudies_Datacards_${datacard}_simplified_All/ -o /eos/home-s/sewuchte/www/backup/private/BehaviorStudies_${datacard}/ -f results_All_exp.html
#     python3 gatherResults.py -i /eos/cms/store/cmst3/group/top/Vcb_trees/HTC_results/ttHcc_ANv4/FitStudies_Datacards_${datacard}_simplified_All/ -o /eos/home-s/sewuchte/www/backup/private/BehaviorStudies_${datacard}/ -f results_All_obs.html --obs
#     python3 gatherResults.py -i /eos/cms/store/cmst3/group/top/Vcb_trees/HTC_results/ttHcc_ANv4/FitStudies_Datacards_${datacard}_simplified_VR/ -o /eos/home-s/sewuchte/www/backup/private/BehaviorStudies_${datacard}/ -f results_VR_exp.html
#     python3 gatherResults.py -i /eos/cms/store/cmst3/group/top/Vcb_trees/HTC_results/ttHcc_ANv4/FitStudies_Datacards_${datacard}_simplified_VR/ -o /eos/home-s/sewuchte/www/backup/private/BehaviorStudies_${datacard}/ -f results_VR_obs.html --obs
#     python3 gatherResults.py -i /eos/cms/store/cmst3/group/top/Vcb_trees/HTC_results/ttHcc_ANv4/FitStudies_Datacards_${datacard}_simplified_SR/ -o /eos/home-s/sewuchte/www/backup/private/BehaviorStudies_${datacard}/ -f results_SR_exp.html
#     python3 gatherResults.py -i /eos/cms/store/cmst3/group/top/Vcb_trees/HTC_results/ttHcc_ANv4/FitStudies_Datacards_${datacard}_simplified_SR/ -o /eos/home-s/sewuchte/www/backup/private/BehaviorStudies_${datacard}/ -f results_SR_obs.html --obs
#     python3 gatherResults.py -i /eos/cms/store/cmst3/group/top/Vcb_trees/HTC_results/ttHcc_ANv4/FitStudies_Datacards_${datacard}_simplified_CR/ -o /eos/home-s/sewuchte/www/backup/private/BehaviorStudies_${datacard}/ -f results_CR_exp.html
#     python3 gatherResults.py -i /eos/cms/store/cmst3/group/top/Vcb_trees/HTC_results/ttHcc_ANv4/FitStudies_Datacards_${datacard}_simplified_CR/ -o /eos/home-s/sewuchte/www/backup/private/BehaviorStudies_${datacard}/ -f results_CR_obs.html --obs
#     python3 gatherResults.py -i /eos/cms/store/cmst3/group/top/Vcb_trees/HTC_results/ttHcc_ANv4/FitStudies_Datacards_${datacard}_simplified_CRPlusTTZ/ -o /eos/home-s/sewuchte/www/backup/private/BehaviorStudies_${datacard}/ -f results_CRPlusTTZ_obs.html --obs
#     python3 gatherResults.py -i /eos/cms/store/cmst3/group/top/Vcb_trees/HTC_results/ttHcc_ANv4/FitStudies_Datacards_${datacard}_simplified_CRPlusTTZ/ -o /eos/home-s/sewuchte/www/backup/private/BehaviorStudies_${datacard}/ -f results_CRPlusTTZ_exp.html
#     python3 gatherResults.py -i /eos/cms/store/cmst3/group/top/Vcb_trees/HTC_results/ttHcc_ANv4/FitStudies_Datacards_${datacard}_simplified_CRPlusTTH/ -o /eos/home-s/sewuchte/www/backup/private/BehaviorStudies_${datacard}/ -f results_CRPlusTTH_obs.html --obs
#     python3 gatherResults.py -i /eos/cms/store/cmst3/group/top/Vcb_trees/HTC_results/ttHcc_ANv4/FitStudies_Datacards_${datacard}_simplified_CRPlusTTH/ -o /eos/home-s/sewuchte/www/backup/private/BehaviorStudies_${datacard}/ -f results_CRPlusTTH_exp.html
# done












# declare -a datacards=("280426" "280426_smoothed")
# declare -a datacards=("280426_trial1")
# declare -a datacards=("280426_trial2")
# declare -a datacards=("280426_trial3")
# declare -a datacards=("290426_correctedBnormalization" "290426_correctedBnormalization_noPeterson")
# declare -a datacards=("290426_correctedBnormalization_noPeterson")
# declare -a datacards=("290426_correctedBnormalization_noPeterson_inflateFlav")
# declare -a datacards=("040526_fixes")
# declare -a datacards=("070526_ge2bge1c")
# declare -a datacards=("070526_ge2bge1c_fix" "070526_CRttWcbM0p2m0p8" "070526_ge2bge1c_fix_smoothed" "070526_CRttWcbM0p2m0p8_smoothed")
# declare -a datacards=("080526_ge2bge1c_fix_clean" "080526_ge2bge1c_fix_clean_pseudoData5FS")
# declare -a datacards=("080526_ge2bge1c_fix_clean_pseudoData5FS")
# declare -a datacards=("100626_ge2bge1c_fix_clean_forJME")
declare -a datacards=("100626_ge2bge1c_fix_clean_onlySurvivingVeto")



for datacard in ${datacards[@]}; do
    echo ${datacard}
    mkdir -p  /eos/home-s/sewuchte/www/Vcb/Apr26/BehaviorStudies_${datacard}

    # echo gatherResults.py -i /eos/cms/store/cmst3/group/top/Vcb_trees/HTC_results/ForANv1/FitStudies_Datacards_${datacard}_simplified_VR/ -o /eos/home-s/sewuchte/www/ttH/Jan25/BehaviorStudies_${datacard}/ -f results_VR_exp.html
    # python3 gatherResults.py -i /eos/cms/store/cmst3/group/top/Vcb_trees/HTC_results/ForANv1/FitStudies_Datacards_${datacard}_simplified_All/ -o /eos/home-s/sewuchte/www/ttH/Jan25/BehaviorStudies_${datacard}/ -f results_All_exp.html
    # python3 gatherResults.py -i /eos/cms/store/cmst3/group/top/Vcb_trees/HTC_results/ForANv1/FitStudies_Datacards_${datacard}_simplified_All/ -o /eos/home-s/sewuchte/www/ttH/Jan25/BehaviorStudies_${datacard}/ -f results_All_obs.html --obs
    # python3 gatherResults.py -i /eos/cms/store/cmst3/group/top/Vcb_trees/HTC_results/ForANv1/FitStudies_Datacards_${datacard}_simplified_VR/ -o /eos/home-s/sewuchte/www/ttH/Jan25/BehaviorStudies_${datacard}/ -f results_VR_exp.html
    # python3 gatherResults.py -i /eos/cms/store/cmst3/group/top/Vcb_trees/HTC_results/ForANv1/FitStudies_Datacards_${datacard}_simplified_VR/ -o /eos/home-s/sewuchte/www/ttH/Jan25/BehaviorStudies_${datacard}/ -f results_VR_obs.html --obs
    python3 gatherResults.py -i /eos/cms/store/cmst3/group/top/Vcb_trees/HTC_results/ForANv1/FitStudies_Datacards_${datacard}_simplified_SR/ -o /eos/home-s/sewuchte/www/Vcb/Apr26/BehaviorStudies_${datacard}/ -f results_SR_exp.html
    # python3 gatherResults.py -i /eos/cms/store/cmst3/group/top/Vcb_trees/HTC_results/ForANv1/FitStudies_Datacards_${datacard}_simplified_SR/ -o /eos/home-s/sewuchte/www/Vcb/Apr26/BehaviorStudies_${datacard}/ -f results_SR_obs.html --obs
    python3 gatherResults.py -i /eos/cms/store/cmst3/group/top/Vcb_trees/HTC_results/ForANv1/FitStudies_Datacards_${datacard}_simplified_CR/ -o /eos/home-s/sewuchte/www/Vcb/Apr26/BehaviorStudies_${datacard}/ -f results_CR_exp.html
    python3 gatherResults.py -i /eos/cms/store/cmst3/group/top/Vcb_trees/HTC_results/ForANv1/FitStudies_Datacards_${datacard}_simplified_CR/ -o /eos/home-s/sewuchte/www/Vcb/Apr26/BehaviorStudies_${datacard}/ -f results_CR_obs.html --obs
    # python3 gatherResults.py -i /eos/cms/store/cmst3/group/top/Vcb_trees/HTC_results/ForANv1/FitStudies_Datacards_${datacard}_simplified_CRPlusTTZ/ -o /eos/home-s/sewuchte/www/Vcb/Apr26/BehaviorStudies_${datacard}/ -f results_CRPlusTTZ_obs.html --obs
    # python3 gatherResults.py -i /eos/cms/store/cmst3/group/top/Vcb_trees/HTC_results/ForANv1/FitStudies_Datacards_${datacard}_simplified_CRPlusTTZ/ -o /eos/home-s/sewuchte/www/Vcb/Apr26/BehaviorStudies_${datacard}/ -f results_CRPlusTTZ_exp.html
    # python3 gatherResults.py -i /eos/cms/store/cmst3/group/top/Vcb_trees/HTC_results/ForANv1/FitStudies_Datacards_${datacard}_simplified_CRPlusTTH/ -o /eos/home-s/sewuchte/www/Vcb/Apr26/BehaviorStudies_${datacard}/ -f results_CRPlusTTH_obs.html --obs
    # python3 gatherResults.py -i /eos/cms/store/cmst3/group/top/Vcb_trees/HTC_results/ForANv1/FitStudies_Datacards_${datacard}_simplified_CRPlusTTH/ -o /eos/home-s/sewuchte/www/Vcb/Apr26/BehaviorStudies_${datacard}/ -f results_CRPlusTTH_exp.html


    # python3 gatherResults.py -i /eos/cms/store/cmst3/group/top/Vcb_trees/HTC_results/ForANv1/FitStudies_Datacards_${datacard}_simplified_CRbb/ -o /eos/home-s/sewuchte/www/Vcb/Apr26/BehaviorStudies_${datacard}/ -f results_CRbb_obs.html --obs
    # python3 gatherResults.py -i /eos/cms/store/cmst3/group/top/Vcb_trees/HTC_results/ForANv1/FitStudies_Datacards_${datacard}_simplified_CRbj/ -o /eos/home-s/sewuchte/www/Vcb/Apr26/BehaviorStudies_${datacard}/ -f results_CRbj_obs.html --obs
    # python3 gatherResults.py -i /eos/cms/store/cmst3/group/top/Vcb_trees/HTC_results/ForANv1/FitStudies_Datacards_${datacard}_simplified_CRcc/ -o /eos/home-s/sewuchte/www/Vcb/Apr26/BehaviorStudies_${datacard}/ -f results_CRcc_obs.html --obs
    # python3 gatherResults.py -i /eos/cms/store/cmst3/group/top/Vcb_trees/HTC_results/ForANv1/FitStudies_Datacards_${datacard}_simplified_CRcj/ -o /eos/home-s/sewuchte/www/Vcb/Apr26/BehaviorStudies_${datacard}/ -f results_CRcj_obs.html --obs
    # python3 gatherResults.py -i /eos/cms/store/cmst3/group/top/Vcb_trees/HTC_results/ForANv1/FitStudies_Datacards_${datacard}_simplified_CR2b/ -o /eos/home-s/sewuchte/www/Vcb/Apr26/BehaviorStudies_${datacard}/ -f results_CR2b_obs.html --obs
    # python3 gatherResults.py -i /eos/cms/store/cmst3/group/top/Vcb_trees/HTC_results/ForANv1/FitStudies_Datacards_${datacard}_simplified_CR2c/ -o /eos/home-s/sewuchte/www/Vcb/Apr26/BehaviorStudies_${datacard}/ -f results_CR2c_obs.html --obs
    # python3 gatherResults.py -i /eos/cms/store/cmst3/group/top/Vcb_trees/HTC_results/ForANv1/FitStudies_Datacards_${datacard}_simplified_CRlf/ -o /eos/home-s/sewuchte/www/Vcb/Apr26/BehaviorStudies_${datacard}/ -f results_CRlf_obs.html --obs

    # python3 gatherResults.py -i /eos/cms/store/cmst3/group/top/Vcb_trees/HTC_results/ForANv1/FitStudies_Datacards_${datacard}_simplified_CRnolf/ -o /eos/home-s/sewuchte/www/Vcb/Apr26/BehaviorStudies_${datacard}/ -f results_CRnolf_obs.html --obs
    # python3 gatherResults.py -i /eos/cms/store/cmst3/group/top/Vcb_trees/HTC_results/ForANv1/FitStudies_Datacards_${datacard}_simplified_SRnolf/ -o /eos/home-s/sewuchte/www/Vcb/Apr26/BehaviorStudies_${datacard}/ -f results_SRnolf_obs.html

    pb_copy_index.py /eos/home-s/sewuchte/www/Vcb/Apr26/BehaviorStudies_${datacard}/ -r
done
