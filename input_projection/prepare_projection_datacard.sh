#!/bin/sh

mode=$1

addString=""

declare -a StringArray=("110 450 1000 2000 3000 6000")

for scenario in ${StringArray[@]}; do

    basePath=/afs/cern.ch/work/s/sewuchte/private/VCB/CMSSW_15_0_10/src/PlotTools/input_projection/
    # --------------------------------------------------------------------
    inputdc="input/Vcb_SL_2024.txt"
    inputshapes="input/Vcb_SL_2024_shapes.root"

    if [[ "${mode}" == "0" ]]; then
        addString=""
    fi
    if [[ "${mode}" == "1" ]]; then
        addString="_scaleHLTFH"
    fi
    if [[ "${mode}" == "2" ]]; then
        addString="_scaleUPART"
    fi
    if [[ "${mode}" == "3" ]]; then
        addString="_scaleHLTFH_scaleUPART"
    fi
    if [[ "${mode}" == "4" ]]; then
        addString="_scaleUPARTV3"
    fi
    if [[ "${mode}" == "5" ]]; then
        addString="_scaleHLTFH_scaleUPARTV3"
    fi
    if [[ "${mode}" == "6" ]]; then
        addString="_scaleHLTFH_scaleL1T_scaleUPART"
    fi

    outputfolder="scenario_"$scenario$addString/
    outputdc=$outputfolder/$(basename $inputdc)
    mkdir -p $outputfolder

    echo inputdc is $inputdc
    echo inputshapes is $inputshapes
    echo scenario is $scenario
    echo outputfolder is $outputfolder
    echo outputdc is $outputdc

    cp $inputdc $outputdc
    cp $inputshapes $outputfolder/

    declare -A map_scale=(["110"]=1.0 ["450"]=4.5 ["1000"]=9.09 ["2000"]=18.18 ["3000"]=27.27 ["6000"]=54.54)

    lumiscaleParam=${map_scale[${scenario}]}

    echo ${scenario}
    echo ${lumiscaleParam}

    # Add rateparam to scale all signal and bkgs by lumi
    echo 'lumiscale rateParam * * '${lumiscaleParam} >> $outputdc
    echo 'nuisance edit freeze lumiscale' >> $outputdc

    if [[ "${mode}" == "1" ]] || [[ "${mode}" == "3" ]] || [[ "${mode}" == "6" ]]; then
        # scale HLT trigger acceptance for FH because of HH parking
        echo 'scale_FH_HLTeff rateParam *_ttHcc*_FH_* * 2.5' >> $outputdc
        echo 'nuisance edit freeze scale_FH_HLTeff' >> $outputdc
    fi
    if [[ "${mode}" == "6" ]]; then
        # scale HLT trigger acceptance for FH because of HH parking
        echo 'scale_FH_L1Teff rateParam *_ttHcc*_FH_* * 1.5' >> $outputdc
        echo 'nuisance edit freeze scale_FH_L1Teff' >> $outputdc
    fi

    if [[ "${mode}" == "2" ]] || [[ "${mode}" == "3" ]] || [[ "${mode}" == "6" ]]; then

        # alternative way
        # ttHcc SR
        echo 'scale_upartv2_SR_tthcc_tthcc rateParam *Vcb_catWcb_SR tt-vcb 1.32' >> $outputdc
        echo 'scale_upartv2_SR_tthcc_ttcc rateParam *Vcb_catWcb_SR ttcc 1.32' >> $outputdc
        echo 'scale_upartv2_SR_tthcc_ttcj rateParam *Vcb_catWcb_SR ttcj 1.15' >> $outputdc
        echo 'scale_upartv2_SR_tthcc_tt2c rateParam *Vcb_catWcb_SR tt2c 1.15' >> $outputdc
        echo 'nuisance edit freeze scale_upartv2_SR_tthcc_tthcc' >> $outputdc
        echo 'nuisance edit freeze scale_upartv2_SR_tthcc_ttcc' >> $outputdc
        echo 'nuisance edit freeze scale_upartv2_SR_tthcc_ttcj' >> $outputdc
        echo 'nuisance edit freeze scale_upartv2_SR_tthcc_tt2c' >> $outputdc
        # ttcc CR
        echo 'scale_upartv2_SR_ttcc_tthcc rateParam *Vcb_catCC_CR tt-vcb 1.32' >> $outputdc
        echo 'scale_upartv2_SR_ttcc_ttcc rateParam *Vcb_catCC_CR ttcc 1.32' >> $outputdc
        echo 'scale_upartv2_SR_ttcc_ttcj rateParam *Vcb_catCC_CR ttcj 1.15' >> $outputdc
        echo 'scale_upartv2_SR_ttcc_tt2c rateParam *Vcb_catCC_CR tt2c 1.15' >> $outputdc
        echo 'nuisance edit freeze scale_upartv2_SR_ttcc_tthcc' >> $outputdc
        echo 'nuisance edit freeze scale_upartv2_SR_ttcc_ttcc' >> $outputdc
        echo 'nuisance edit freeze scale_upartv2_SR_ttcc_ttcj' >> $outputdc
        echo 'nuisance edit freeze scale_upartv2_SR_ttcc_tt2c' >> $outputdc
        # ttbb CR
        echo 'scale_upartv2_SR_ttbb_tthbb rateParam *Vcb_catBB_CR tt-vcb 1.32' >> $outputdc
        echo 'scale_upartv2_SR_ttbb_ttbb rateParam *Vcb_catBB_CR ttbb 1.32' >> $outputdc
        echo 'scale_upartv2_SR_ttbb_ttbj rateParam *Vcb_catBB_CR ttbj 1.15' >> $outputdc
        echo 'scale_upartv2_SR_ttbb_tt2b rateParam *Vcb_catBB_CR tt2b 1.15' >> $outputdc
        echo 'nuisance edit freeze scale_upartv2_SR_ttbb_tthbb' >> $outputdc
        echo 'nuisance edit freeze scale_upartv2_SR_ttbb_ttbb' >> $outputdc
        echo 'nuisance edit freeze scale_upartv2_SR_ttbb_ttbj' >> $outputdc
        echo 'nuisance edit freeze scale_upartv2_SR_ttbb_tt2b' >> $outputdc
        # ttc CR
        echo 'scale_upartv2_SR_ttcj_tthcc rateParam *Vcb_catCJ_CR tt-vcb 1.32' >> $outputdc
        echo 'scale_upartv2_SR_ttcj_ttcc rateParam *Vcb_catCJ_CR ttcc 1.32' >> $outputdc
        echo 'scale_upartv2_SR_ttcj_ttcj rateParam *Vcb_catCJ_CR ttcj 1.15' >> $outputdc
        echo 'scale_upartv2_SR_ttcj_tt2c rateParam *Vcb_catCJ_CR tt2c 1.15' >> $outputdc
        echo 'nuisance edit freeze scale_upartv2_SR_ttcj_tthcc' >> $outputdc
        echo 'nuisance edit freeze scale_upartv2_SR_ttcj_ttcc' >> $outputdc
        echo 'nuisance edit freeze scale_upartv2_SR_ttcj_ttcj' >> $outputdc
        echo 'nuisance edit freeze scale_upartv2_SR_ttcj_tt2c' >> $outputdc
        # ttb CR
        echo 'scale_upartv2_SR_ttbj_tthbb rateParam *Vcb_catBJ_CR tt-vcb 1.32' >> $outputdc
        echo 'scale_upartv2_SR_ttbj_ttbb rateParam *Vcb_catBJ_CR ttbb 1.32' >> $outputdc
        echo 'scale_upartv2_SR_ttbj_ttbj rateParam *Vcb_catBJ_CR ttbj 1.15' >> $outputdc
        echo 'scale_upartv2_SR_ttbj_tt2b rateParam *Vcb_catBJ_CR tt2b 1.15' >> $outputdc
        echo 'nuisance edit freeze scale_upartv2_SR_ttbj_tthbb' >> $outputdc
        echo 'nuisance edit freeze scale_upartv2_SR_ttbj_ttbb' >> $outputdc
        echo 'nuisance edit freeze scale_upartv2_SR_ttbj_ttbj' >> $outputdc
        echo 'nuisance edit freeze scale_upartv2_SR_ttbj_tt2b' >> $outputdc
    fi


    if [[ "${mode}" == "4" ]] || [[ "${mode}" == "5" ]]; then

        # alternative way
        # ttHcc SR
        echo 'scale_upartv3_SR_tthcc_tthcc rateParam *_ttHcc_*_catHcc_SR ttH_hcc 1.75' >> $outputdc
        echo 'scale_upartv3_SR_tthcc_ttcc rateParam *_ttHcc_*_catHcc_SR ttcc 1.75' >> $outputdc
        echo 'scale_upartv3_SR_tthcc_ttcj rateParam *_ttHcc_*_catHcc_SR ttcj 1.32' >> $outputdc
        echo 'scale_upartv3_SR_tthcc_tt2c rateParam *_ttHcc_*_catHcc_SR tt2c 1.32' >> $outputdc
        echo 'nuisance edit freeze scale_upartv3_SR_tthcc_tthcc' >> $outputdc
        echo 'nuisance edit freeze scale_upartv3_SR_tthcc_ttzcc' >> $outputdc
        echo 'nuisance edit freeze scale_upartv3_SR_tthcc_ttcc' >> $outputdc
        echo 'nuisance edit freeze scale_upartv3_SR_tthcc_ttcj' >> $outputdc
        echo 'nuisance edit freeze scale_upartv3_SR_tthcc_tt2c' >> $outputdc
        # ttHbb SR
        echo 'scale_upartv3_SR_tthbb_tthbb rateParam *_ttHcc_*_catHbb_SR ttH_hbb 1.75' >> $outputdc
        echo 'scale_upartv3_SR_tthbb_ttbb rateParam *_ttHcc_*_catHbb_SR ttbb 1.75' >> $outputdc
        echo 'scale_upartv3_SR_tthbb_ttbj rateParam *_ttHcc_*_catHbb_SR ttbj 1.32' >> $outputdc
        echo 'scale_upartv3_SR_tthbb_tt2b rateParam *_ttHcc_*_catHbb_SR tt2b 1.32' >> $outputdc
        echo 'nuisance edit freeze scale_upartv3_SR_tthbb_tthbb' >> $outputdc
        echo 'nuisance edit freeze scale_upartv3_SR_tthbb_ttzbb' >> $outputdc
        echo 'nuisance edit freeze scale_upartv3_SR_tthbb_ttbb' >> $outputdc
        echo 'nuisance edit freeze scale_upartv3_SR_tthbb_ttbj' >> $outputdc
        echo 'nuisance edit freeze scale_upartv3_SR_tthbb_tt2b' >> $outputdc
        # ttZcc SR
        echo 'scale_upartv3_SR_ttzcc_tthcc rateParam *_ttHcc_*_catHcc_SR ttH_hcc 1.75' >> $outputdc
        echo 'scale_upartv3_SR_ttzcc_ttcc rateParam *_ttHcc_*_catHcc_SR ttcc 1.75' >> $outputdc
        echo 'scale_upartv3_SR_ttzcc_ttcj rateParam *_ttHcc_*_catHcc_SR ttcj 1.32' >> $outputdc
        echo 'scale_upartv3_SR_ttzcc_tt2c rateParam *_ttHcc_*_catHcc_SR tt2c 1.32' >> $outputdc
        echo 'nuisance edit freeze scale_upartv3_SR_ttzcc_tthcc' >> $outputdc
        echo 'nuisance edit freeze scale_upartv3_SR_ttzcc_ttzcc' >> $outputdc
        echo 'nuisance edit freeze scale_upartv3_SR_ttzcc_ttcc' >> $outputdc
        echo 'nuisance edit freeze scale_upartv3_SR_ttzcc_ttcj' >> $outputdc
        echo 'nuisance edit freeze scale_upartv3_SR_ttzcc_tt2c' >> $outputdc
        # ttZbb SR
        echo 'scale_upartv3_SR_ttzbb_tthbb rateParam *_ttHcc_*_catHbb_SR ttH_hbb 1.75' >> $outputdc
        echo 'scale_upartv3_SR_ttzbb_ttbb rateParam *_ttHcc_*_catHbb_SR ttbb 1.75' >> $outputdc
        echo 'scale_upartv3_SR_ttzbb_ttbj rateParam *_ttHcc_*_catHbb_SR ttbj 1.32' >> $outputdc
        echo 'scale_upartv3_SR_ttzbb_tt2b rateParam *_ttHcc_*_catHbb_SR tt2b 1.32' >> $outputdc
        echo 'nuisance edit freeze scale_upartv3_SR_ttzbb_tthbb' >> $outputdc
        echo 'nuisance edit freeze scale_upartv3_SR_ttzbb_ttzbb' >> $outputdc
        echo 'nuisance edit freeze scale_upartv3_SR_ttzbb_ttbb' >> $outputdc
        echo 'nuisance edit freeze scale_upartv3_SR_ttzbb_ttbj' >> $outputdc
        echo 'nuisance edit freeze scale_upartv3_SR_ttzbb_tt2b' >> $outputdc
        # ttcc CR
        echo 'scale_upartv3_SR_ttcc_tthcc rateParam *_ttHcc_*_catCC_SR ttH_hcc 1.75' >> $outputdc
        echo 'scale_upartv3_SR_ttcc_ttcc rateParam *_ttHcc_*_catCC_SR ttcc 1.75' >> $outputdc
        echo 'scale_upartv3_SR_ttcc_ttcj rateParam *_ttHcc_*_catCC_SR ttcj 1.32' >> $outputdc
        echo 'scale_upartv3_SR_ttcc_tt2c rateParam *_ttHcc_*_catCC_SR tt2c 1.32' >> $outputdc
        echo 'nuisance edit freeze scale_upartv3_SR_ttcc_tthcc' >> $outputdc
        echo 'nuisance edit freeze scale_upartv3_SR_ttcc_ttzcc' >> $outputdc
        echo 'nuisance edit freeze scale_upartv3_SR_ttcc_ttcc' >> $outputdc
        echo 'nuisance edit freeze scale_upartv3_SR_ttcc_ttcj' >> $outputdc
        echo 'nuisance edit freeze scale_upartv3_SR_ttcc_tt2c' >> $outputdc
        # ttbb CR
        echo 'scale_upartv3_SR_ttbb_tthbb rateParam *_ttHcc_*_catBB_SR ttH_hbb 1.75' >> $outputdc
        echo 'scale_upartv3_SR_ttbb_ttbb rateParam *_ttHcc_*_catBB_SR ttbb 1.75' >> $outputdc
        echo 'scale_upartv3_SR_ttbb_ttbj rateParam *_ttHcc_*_catBB_SR ttbj 1.32' >> $outputdc
        echo 'scale_upartv3_SR_ttbb_tt2b rateParam *_ttHcc_*_catBB_SR tt2b 1.32' >> $outputdc
        echo 'nuisance edit freeze scale_upartv3_SR_ttbb_tthbb' >> $outputdc
        echo 'nuisance edit freeze scale_upartv3_SR_ttbb_ttzbb' >> $outputdc
        echo 'nuisance edit freeze scale_upartv3_SR_ttbb_ttbb' >> $outputdc
        echo 'nuisance edit freeze scale_upartv3_SR_ttbb_ttbj' >> $outputdc
        echo 'nuisance edit freeze scale_upartv3_SR_ttbb_tt2b' >> $outputdc
        # ttc CR
        echo 'scale_upartv3_SR_ttcj_tthcc rateParam *_ttHcc_*_catCJ_SR ttH_hcc 1.75' >> $outputdc
        echo 'scale_upartv3_SR_ttcj_ttcc rateParam *_ttHcc_*_catCJ_SR ttcc 1.75' >> $outputdc
        echo 'scale_upartv3_SR_ttcj_ttcj rateParam *_ttHcc_*_catCJ_SR ttcj 1.32' >> $outputdc
        echo 'scale_upartv3_SR_ttcj_tt2c rateParam *_ttHcc_*_catCJ_SR tt2c 1.32' >> $outputdc
        echo 'nuisance edit freeze scale_upartv3_SR_ttcj_tthcc' >> $outputdc
        echo 'nuisance edit freeze scale_upartv3_SR_ttcj_ttzcc' >> $outputdc
        echo 'nuisance edit freeze scale_upartv3_SR_ttcj_ttcc' >> $outputdc
        echo 'nuisance edit freeze scale_upartv3_SR_ttcj_ttcj' >> $outputdc
        echo 'nuisance edit freeze scale_upartv3_SR_ttcj_tt2c' >> $outputdc
        # ttb CR
        echo 'scale_upartv3_SR_ttbj_tthbb rateParam *_ttHcc_*_catBJ_SR ttH_hbb 1.75' >> $outputdc
        echo 'scale_upartv3_SR_ttbj_ttbb rateParam *_ttHcc_*_catBJ_SR ttbb 1.75' >> $outputdc
        echo 'scale_upartv3_SR_ttbj_ttbj rateParam *_ttHcc_*_catBJ_SR ttbj 1.32' >> $outputdc
        echo 'scale_upartv3_SR_ttbj_tt2b rateParam *_ttHcc_*_catBJ_SR tt2b 1.32' >> $outputdc
        echo 'nuisance edit freeze scale_upartv3_SR_ttbj_tthbb' >> $outputdc
        echo 'nuisance edit freeze scale_upartv3_SR_ttbj_ttzbb' >> $outputdc
        echo 'nuisance edit freeze scale_upartv3_SR_ttbj_ttbb' >> $outputdc
        echo 'nuisance edit freeze scale_upartv3_SR_ttbj_ttbj' >> $outputdc
        echo 'nuisance edit freeze scale_upartv3_SR_ttbj_tt2b' >> $outputdc

    fi


    # THEORY UNCERTAINTIES 
    echo 'pSigTheory group = tune_CP5 CR1 CR2 bFragWeight_2024 topHdampWeight_tt-vcb_2024 LHE_muF_tt-vcb_2024 LHE_muR_tt-vcb_2024 PS_fsr_G2GG_muR_tt-vcb_2024 PS_isr_G2GG_muR_tt-vcb_2024 PS_fsr_G2QQ_muR_tt-vcb_2024 PS_isr_G2QQ_muR_tt-vcb_2024 PS_fsr_Q2QG_muR_tt-vcb_2024 PS_isr_Q2QG_muR_tt-vcb_2024 PS_fsr_X2XG_muR_tt-vcb_2024 PS_isr_X2XG_muR_tt-vcb_2024 PS_fsr_G2GG_cNS_tt-vcb_2024 PS_isr_G2GG_cNS_tt-vcb_2024 PS_fsr_G2QQ_cNS_tt-vcb_2024 PS_isr_G2QQ_cNS_tt-vcb_2024 PS_fsr_G2QG_cNS_tt-vcb_2024 PS_isr_G2QG_cNS_tt-vcb_2024 PS_fsr_X2XG_cNS_tt-vcb_2024 PS_isr_X2XG_cNS_tt-vcb_2024' >> $outputdc 
    echo 'pBkgTheory group = bFragWeight_2024 norm_singletop norm_ttW norm_ttZ norm_ttbb-dps norm_ttH norm_diboson norm_wjets topHdampWeight_tt2c_2024 topHdampWeight_ttLF_2024 topHdampWeight_ttcc_2024 topHdampWeight_ttcj_2024 LHE_muF_diboson_2024 LHE_muF_singletop_2024 LHE_muF_tt2b-dps_2024 LHE_muF_tt2b_2024 LHE_muF_tt2c_2024 LHE_muF_ttHbb_2024 LHE_muF_ttHcc_2024 LHE_muF_ttLF_2024 LHE_muF_ttW_2024 LHE_muF_ttZ_2024 LHE_muF_ttbb-dps_2024 LHE_muF_ttbb_2024 LHE_muF_ttbj-dps_2024 LHE_muF_ttbj_2024 LHE_muF_ttcc_2024 LHE_muF_ttcj_2024 LHE_muF_wjets_2024 LHE_muR_diboson_2024 LHE_muR_singletop_2024 LHE_muR_tt2b-dps_2024 LHE_muR_tt2b_2024 LHE_muR_tt2c_2024 LHE_muR_ttHbb_2024 LHE_muR_ttHcc_2024 LHE_muR_ttLF_2024 LHE_muR_ttW_2024 LHE_muR_ttZ_2024 LHE_muR_ttbb-dps_2024 LHE_muR_ttbb_2024 LHE_muR_ttbj-dps_2024 LHE_muR_ttbj_2024 LHE_muR_ttcc_2024 LHE_muR_ttcj_2024 LHE_muR_wjets_2024 PS_fsr_G2GG_cNS_tt-vcb_2024 PS_fsr_G2GG_cNS_tt2b-dps_2024 PS_fsr_G2GG_cNS_tt2b_2024 PS_fsr_G2GG_cNS_tt2c_2024 PS_fsr_G2GG_cNS_ttHbb_2024 PS_fsr_G2GG_cNS_ttHcc_2024 PS_fsr_G2GG_cNS_ttLF_2024 PS_fsr_G2GG_cNS_ttW_2024 PS_fsr_G2GG_cNS_ttZ_2024 PS_fsr_G2GG_cNS_ttbb-dps_2024 PS_fsr_G2GG_cNS_ttbb_2024 PS_fsr_G2GG_cNS_ttbj-dps_2024 PS_fsr_G2GG_cNS_ttbj_2024 PS_fsr_G2GG_cNS_ttcc_2024 PS_fsr_G2GG_cNS_ttcj_2024 PS_fsr_G2GG_muR_tt2b-dps_2024 PS_fsr_G2GG_muR_tt2b_2024 PS_fsr_G2GG_muR_tt2c_2024 PS_fsr_G2GG_muR_ttHbb_2024 PS_fsr_G2GG_muR_ttHcc_2024 PS_fsr_G2GG_muR_ttLF_2024 PS_fsr_G2GG_muR_ttW_2024 PS_fsr_G2GG_muR_ttZ_2024 PS_fsr_G2GG_muR_ttbb-dps_2024 PS_fsr_G2GG_muR_ttbb_2024 PS_fsr_G2GG_muR_ttbj-dps_2024 PS_fsr_G2GG_muR_ttbj_2024 PS_fsr_G2GG_muR_ttcc_2024 PS_fsr_G2GG_muR_ttcj_2024 PS_fsr_G2QG_cNS_tt2b-dps_2024 PS_fsr_G2QG_cNS_tt2b_2024 PS_fsr_G2QG_cNS_tt2c_2024 PS_fsr_G2QG_cNS_ttHbb_2024 PS_fsr_G2QG_cNS_ttHcc_2024 PS_fsr_G2QG_cNS_ttLF_2024 PS_fsr_G2QG_cNS_ttW_2024 PS_fsr_G2QG_cNS_ttZ_2024 PS_fsr_G2QG_cNS_ttbb-dps_2024 PS_fsr_G2QG_cNS_ttbb_2024 PS_fsr_G2QG_cNS_ttbj-dps_2024 PS_fsr_G2QG_cNS_ttbj_2024 PS_fsr_G2QG_cNS_ttcc_2024 PS_fsr_G2QG_cNS_ttcj_2024 PS_fsr_G2QQ_cNS_tt2b-dps_2024 PS_fsr_G2QQ_cNS_tt2b_2024 PS_fsr_G2QQ_cNS_tt2c_2024 PS_fsr_G2QQ_cNS_ttHbb_2024 PS_fsr_G2QQ_cNS_ttHcc_2024 PS_fsr_G2QQ_cNS_ttLF_2024 PS_fsr_G2QQ_cNS_ttW_2024 PS_fsr_G2QQ_cNS_ttZ_2024 PS_fsr_G2QQ_cNS_ttbb-dps_2024 PS_fsr_G2QQ_cNS_ttbb_2024 PS_fsr_G2QQ_cNS_ttbj-dps_2024 PS_fsr_G2QQ_cNS_ttbj_2024 PS_fsr_G2QQ_cNS_ttcc_2024 PS_fsr_G2QQ_cNS_ttcj_2024 PS_fsr_G2QQ_muR_tt2b-dps_2024 PS_fsr_G2QQ_muR_tt2b_2024 PS_fsr_G2QQ_muR_tt2c_2024 PS_fsr_G2QQ_muR_ttHbb_2024 PS_fsr_G2QQ_muR_ttHcc_2024 PS_fsr_G2QQ_muR_ttLF_2024 PS_fsr_G2QQ_muR_ttW_2024 PS_fsr_G2QQ_muR_ttZ_2024 PS_fsr_G2QQ_muR_ttbb-dps_2024 PS_fsr_G2QQ_muR_ttbb_2024 PS_fsr_G2QQ_muR_ttbj-dps_2024 PS_fsr_G2QQ_muR_ttbj_2024 PS_fsr_G2QQ_muR_ttcc_2024 PS_fsr_G2QQ_muR_ttcj_2024 PS_fsr_Q2QG_muR_tt2b-dps_2024 PS_fsr_Q2QG_muR_tt2b_2024 PS_fsr_Q2QG_muR_tt2c_2024 PS_fsr_Q2QG_muR_ttHbb_2024 PS_fsr_Q2QG_muR_ttHcc_2024 PS_fsr_Q2QG_muR_ttLF_2024 PS_fsr_Q2QG_muR_ttW_2024 PS_fsr_Q2QG_muR_ttZ_2024 PS_fsr_Q2QG_muR_ttbb-dps_2024 PS_fsr_Q2QG_muR_ttbb_2024 PS_fsr_Q2QG_muR_ttbj-dps_2024 PS_fsr_Q2QG_muR_ttbj_2024 PS_fsr_Q2QG_muR_ttcc_2024 PS_fsr_Q2QG_muR_ttcj_2024 PS_fsr_X2XG_cNS_tt2b-dps_2024 PS_fsr_X2XG_cNS_tt2b_2024 PS_fsr_X2XG_cNS_tt2c_2024 PS_fsr_X2XG_cNS_ttHbb_2024 PS_fsr_X2XG_cNS_ttHcc_2024 PS_fsr_X2XG_cNS_ttLF_2024 PS_fsr_X2XG_cNS_ttW_2024 PS_fsr_X2XG_cNS_ttZ_2024 PS_fsr_X2XG_cNS_ttbb-dps_2024 PS_fsr_X2XG_cNS_ttbb_2024 PS_fsr_X2XG_cNS_ttbj-dps_2024 PS_fsr_X2XG_cNS_ttbj_2024 PS_fsr_X2XG_cNS_ttcc_2024 PS_fsr_X2XG_cNS_ttcj_2024 PS_fsr_X2XG_muR_tt2b-dps_2024 PS_fsr_X2XG_muR_tt2b_2024 PS_fsr_X2XG_muR_tt2c_2024 PS_fsr_X2XG_muR_ttHbb_2024 PS_fsr_X2XG_muR_ttHcc_2024 PS_fsr_X2XG_muR_ttLF_2024 PS_fsr_X2XG_muR_ttW_2024 PS_fsr_X2XG_muR_ttZ_2024 PS_fsr_X2XG_muR_ttbb-dps_2024 PS_fsr_X2XG_muR_ttbb_2024 PS_fsr_X2XG_muR_ttbj-dps_2024 PS_fsr_X2XG_muR_ttbj_2024 PS_fsr_X2XG_muR_ttcc_2024 PS_fsr_X2XG_muR_ttcj_2024 PS_isr_G2GG_cNS_tt2b-dps_2024 PS_isr_G2GG_cNS_tt2b_2024 PS_isr_G2GG_cNS_tt2c_2024 PS_isr_G2GG_cNS_ttHbb_2024 PS_isr_G2GG_cNS_ttHcc_2024 PS_isr_G2GG_cNS_ttLF_2024 PS_isr_G2GG_cNS_ttW_2024 PS_isr_G2GG_cNS_ttZ_2024 PS_isr_G2GG_cNS_ttbb-dps_2024 PS_isr_G2GG_cNS_ttbb_2024 PS_isr_G2GG_cNS_ttbj-dps_2024 PS_isr_G2GG_cNS_ttbj_2024 PS_isr_G2GG_cNS_ttcc_2024 PS_isr_G2GG_cNS_ttcj_2024 PS_isr_G2GG_muR_tt2b-dps_2024 PS_isr_G2GG_muR_tt2b_2024 PS_isr_G2GG_muR_tt2c_2024 PS_isr_G2GG_muR_ttHbb_2024 PS_isr_G2GG_muR_ttHcc_2024 PS_isr_G2GG_muR_ttLF_2024 PS_isr_G2GG_muR_ttW_2024 PS_isr_G2GG_muR_ttZ_2024 PS_isr_G2GG_muR_ttbb-dps_2024 PS_isr_G2GG_muR_ttbb_2024 PS_isr_G2GG_muR_ttbj-dps_2024 PS_isr_G2GG_muR_ttbj_2024 PS_isr_G2GG_muR_ttcc_2024 PS_isr_G2GG_muR_ttcj_2024 PS_isr_G2QG_cNS_tt2b-dps_2024 PS_isr_G2QG_cNS_tt2b_2024 PS_isr_G2QG_cNS_tt2c_2024 PS_isr_G2QG_cNS_ttHbb_2024 PS_isr_G2QG_cNS_ttHcc_2024 PS_isr_G2QG_cNS_ttLF_2024 PS_isr_G2QG_cNS_ttW_2024 PS_isr_G2QG_cNS_ttZ_2024 PS_isr_G2QG_cNS_ttbb-dps_2024 PS_isr_G2QG_cNS_ttbb_2024 PS_isr_G2QG_cNS_ttbj-dps_2024 PS_isr_G2QG_cNS_ttbj_2024 PS_isr_G2QG_cNS_ttcc_2024 PS_isr_G2QG_cNS_ttcj_2024 PS_isr_G2QQ_cNS_tt2b-dps_2024 PS_isr_G2QQ_cNS_tt2b_2024 PS_isr_G2QQ_cNS_tt2c_2024 PS_isr_G2QQ_cNS_ttHbb_2024 PS_isr_G2QQ_cNS_ttHcc_2024 PS_isr_G2QQ_cNS_ttLF_2024 PS_isr_G2QQ_cNS_ttW_2024 PS_isr_G2QQ_cNS_ttZ_2024 PS_isr_G2QQ_cNS_ttbb-dps_2024 PS_isr_G2QQ_cNS_ttbb_2024 PS_isr_G2QQ_cNS_ttbj-dps_2024 PS_isr_G2QQ_cNS_ttbj_2024 PS_isr_G2QQ_cNS_ttcc_2024 PS_isr_G2QQ_cNS_ttcj_2024 PS_isr_G2QQ_muR_tt2b-dps_2024 PS_isr_G2QQ_muR_tt2b_2024 PS_isr_G2QQ_muR_tt2c_2024 PS_isr_G2QQ_muR_ttHbb_2024 PS_isr_G2QQ_muR_ttHcc_2024 PS_isr_G2QQ_muR_ttLF_2024 PS_isr_G2QQ_muR_ttW_2024 PS_isr_G2QQ_muR_ttZ_2024 PS_isr_G2QQ_muR_ttbb-dps_2024 PS_isr_G2QQ_muR_ttbb_2024 PS_isr_G2QQ_muR_ttbj-dps_2024 PS_isr_G2QQ_muR_ttbj_2024 PS_isr_G2QQ_muR_ttcc_2024 PS_isr_G2QQ_muR_ttcj_2024 PS_isr_Q2QG_muR_tt2b-dps_2024 PS_isr_Q2QG_muR_tt2b_2024 PS_isr_Q2QG_muR_tt2c_2024 PS_isr_Q2QG_muR_ttHbb_2024 PS_isr_Q2QG_muR_ttHcc_2024 PS_isr_Q2QG_muR_ttLF_2024 PS_isr_Q2QG_muR_ttW_2024 PS_isr_Q2QG_muR_ttZ_2024 PS_isr_Q2QG_muR_ttbb-dps_2024 PS_isr_Q2QG_muR_ttbb_2024 PS_isr_Q2QG_muR_ttbj-dps_2024 PS_isr_Q2QG_muR_ttbj_2024 PS_isr_Q2QG_muR_ttcc_2024 PS_isr_Q2QG_muR_ttcj_2024 PS_isr_X2XG_cNS_tt2b-dps_2024 PS_isr_X2XG_cNS_tt2b_2024 PS_isr_X2XG_cNS_tt2c_2024 PS_isr_X2XG_cNS_ttHbb_2024 PS_isr_X2XG_cNS_ttHcc_2024 PS_isr_X2XG_cNS_ttLF_2024 PS_isr_X2XG_cNS_ttW_2024 PS_isr_X2XG_cNS_ttZ_2024 PS_isr_X2XG_cNS_ttbb-dps_2024 PS_isr_X2XG_cNS_ttbb_2024 PS_isr_X2XG_cNS_ttbj-dps_2024 PS_isr_X2XG_cNS_ttbj_2024 PS_isr_X2XG_cNS_ttcc_2024 PS_isr_X2XG_cNS_ttcj_2024 PS_isr_X2XG_muR_tt2b-dps_2024 PS_isr_X2XG_muR_tt2b_2024 PS_isr_X2XG_muR_tt2c_2024 PS_isr_X2XG_muR_ttHbb_2024 PS_isr_X2XG_muR_ttHcc_2024 PS_isr_X2XG_muR_ttLF_2024 PS_isr_X2XG_muR_ttW_2024 PS_isr_X2XG_muR_ttZ_2024 PS_isr_X2XG_muR_ttbb-dps_2024 PS_isr_X2XG_muR_ttbb_2024 PS_isr_X2XG_muR_ttbj-dps_2024 PS_isr_X2XG_muR_ttbj_2024 PS_isr_X2XG_muR_ttcc_2024 PS_isr_X2XG_muR_ttcj_2024' >> $outputdc 


    # EXPERIMENTAL UNCERTAINTIES
    echo 'pLumi group = CMS_lumi_13p6TeV_2024' >> $outputdc
    echo 'pPU group = CMS_pileup_2024' >> $outputdc
    echo 'pScaleJAbs group = jes_Absolute jes_Absolute_2024' >> $outputdc
    # echo 'pScaleJPileup group = CMS_scale_j_EC2' >> $outputdc
    echo 'pScaleJRel group = jes_RelativeBal jes_RelativeSample_2024 jes_BBEC1 jes_BBEC1_2024' >> $outputdc
    echo 'pScaleJFlav group = jes_FlavorQCD' >> $outputdc
    # echo 'pScaleJTime group = JESTimePtEta_Y1 JESTimePtEta_Y2 JESTimePtEta_Y3' >> $outputdc
    # echo 'pScaleJMethod group = JESSinglePionECAL JESSinglePionHCAL' >> $outputdc
    echo 'pScaleMet group = met' >> $outputdc
    echo 'pResJ group = jer' >> $outputdc
    echo 'pBTag group = CMS_flavTag_xsec_ttbar CMS_flavTag_xsec_wjets_c CMS_flavTag_xsec_wjets_b CMS_flavTag_xsec_zjets_c CMS_flavTag_xsec_zjets_b CMS_flavTag_xsec_singlet_tCh CMS_flavTag_xsec_singlet_tW CMS_flavTag_xsec_VV CMS_flavTag_EleReco CMS_flavTag_EleScale CMS_flavTag_EleSmear CMS_flavTag_ElePromptMVA CMS_flavTag_EleTrigger CMS_flavTag_MuPromptMVA CMS_flavTag_MuTrigger CMS_flavTag_MuScale CMS_flavTag_MuResol CMS_flavTag_PU_2024 CMS_flavTag_Lumi_2024 CMS_flavTag_LHE_muF_ttbar CMS_flavTag_LHE_muR_ttbar CMS_flavTag_LHE_muF_singlet CMS_flavTag_LHE_muR_singlet CMS_flavTag_LHE_muF_wjets CMS_flavTag_LHE_muR_wjets CMS_flavTag_LHE_muF_zjets CMS_flavTag_LHE_muR_zjets CMS_flavTag_LHE_muF_diboson CMS_flavTag_LHE_muR_diboson CMS_flavTag_PS_ISR_ttbar CMS_flavTag_PS_FSR_ttbar CMS_flavTag_PS_ISR_singlet CMS_flavTag_PS_FSR_singlet CMS_flavTag_PS_ISR_wjets CMS_flavTag_PS_FSR_wjets CMS_flavTag_PS_ISR_zjets CMS_flavTag_PS_FSR_zjets CMS_flavTag_PS_ISR_diboson CMS_flavTag_PS_FSR_diboson CMS_flavTag_JES_Absolute CMS_flavTag_JES_BBEC1 CMS_flavTag_JES_FlavorQCD CMS_flavTag_JES_RelativeBal CMS_flavTag_JES_Absolute_2024 CMS_flavTag_JES_BBEC1_2024 CMS_flavTag_JES_RelativeSample_2024 CMS_flavTag_JES_RelativeSample_2024' >> $outputdc
    # echo 'pBTagLight group = BTAG_LJET_CORR' >> $outputdc
    echo 'pBTagStat group = CMS_flavTag_Stat_flavB_C0_2024 CMS_flavTag_Stat_flavB_C1_2024 CMS_flavTag_Stat_flavB_C2_2024 CMS_flavTag_Stat_flavB_C3_2024 CMS_flavTag_Stat_flavB_C4_2024 CMS_flavTag_Stat_flavB_B0_2024 CMS_flavTag_Stat_flavB_B1_2024 CMS_flavTag_Stat_flavB_B2_2024 CMS_flavTag_Stat_flavB_B3_2024 CMS_flavTag_Stat_flavB_B4_2024 CMS_flavTag_Stat_flavC_C0_2024 CMS_flavTag_Stat_flavC_C1_2024 CMS_flavTag_Stat_flavC_C2_2024 CMS_flavTag_Stat_flavC_C3_2024 CMS_flavTag_Stat_flavC_C4_2024 CMS_flavTag_Stat_flavC_B0_2024 CMS_flavTag_Stat_flavC_B1_2024 CMS_flavTag_Stat_flavC_B2_2024 CMS_flavTag_Stat_flavC_B3_2024 CMS_flavTag_Stat_flavC_B4_2024 CMS_flavTag_Stat_flavL_C0_2024 CMS_flavTag_Stat_flavL_C1_2024 CMS_flavTag_Stat_flavL_C2_2024 CMS_flavTag_Stat_flavL_C3_2024 CMS_flavTag_Stat_flavL_C4_2024 CMS_flavTag_Stat_flavL_B0_2024 CMS_flavTag_Stat_flavL_B1_2024 CMS_flavTag_Stat_flavL_B2_2024 CMS_flavTag_Stat_flavL_B3_2024 CMS_flavTag_Stat_flavL_B4_2024' >> $outputdc
    # echo 'pJetID group = JetPileupIDEff JetPileupIDMistag' >> $outputdc
    echo 'pTrigEff group = CMS_trigEff' >> $outputdc
    # echo 'pPileup group = PU' >> $outputdc
    echo 'pEleID group = CMS_elEff CMS_elSmear CMS_elScale' >> $outputdc
    echo 'pMuonID group = CMS_muEff CMS_muSmear CMS_muScale' >> $outputdc

    # remove uncertainties related to detector malfunctioning
    # echo 'nuisance edit drop * * CMS_l1_prefiring_Phase2' >> $outputdc
    # echo 'nuisance edit drop * * CMS_pileup_Phase2' >> $outputdc
    # echo 'nuisance edit drop * * CMS_HEM_Phase2' >> $outputdc

    # create the workspace in S3 scenario (nominal scenario of systematics uncertainties)
    # the getScenario_comb.py script should be modified to include all the scalings for analysis-specific uncertainties
    systscaling=$(python3 getScenario_comb.py S3 -o)
    echo $systscaling
    text2workspace.py $outputdc --out $outputfolder/workspace_S3.root -m 125.38 -v 0 \
    --channel-masks \
    --for-fits --no-wrappers --use-histsum --X-pack-asympows --optimize-simpdf-constraints=cms $systscaling > $outputfolder/workspace_S3.log
    
    # echo text2workspace.py $outputdc --out $outputfolder/workspace_S3.root -m 125 -v 3 -P HiggsAnalysis.CombinedLimit.PhysicsModel:multiSignalModel -v 0 --channel-masks --PO 'map=.*/ttbarsignal_genRho0to03:rate_ttj0[1.,-10.,10.]' --PO 'map=.*/ttbarsignal_genRho03to045:rate_ttj1[1.,-10.,10.]' --PO 'map=.*/ttbarsignal_genRho045to07:rate_ttj2[1.,-10.,10.]' --PO 'map=.*/ttbarsignal_genRho07to1:rate_ttj3[1.,-10.,10.]' --for-fits --no-wrappers --use-histsum --X-pack-asympows --optimize-simpdf-constraints=cms $systscaling > $outputfolder/workspace_S3.log
    # create the workspace in S2 scenario (nominal scenario of systematics uncertainties)
    # the getScenario_comb.py script should be modified to include all the scalings for analysis-specific uncertainties
    # systscaling=$(python3 getScenario_comb.py S2 -o)
    # echo $systscaling
    # text2workspace.py $outputdc --out $outputfolder/workspace_S2.root -m 125 -v 3 -P HiggsAnalysis.CombinedLimit.PhysicsModel:multiSignalModel -v 0 --channel-masks --PO 'map=.*/ttbarsignal_genRho0to03:rate_ttj0[1.,-10.,10.]' --PO 'map=.*/ttbarsignal_genRho03to045:rate_ttj1[1.,-10.,10.]' --PO 'map=.*/ttbarsignal_genRho045to07:rate_ttj2[1.,-10.,10.]' --PO 'map=.*/ttbarsignal_genRho07to1:rate_ttj3[1.,-10.,10.]' --for-fits --no-wrappers --use-histsum --X-pack-asympows --optimize-simpdf-constraints=cms $systscaling > $outputfolder/workspace_S2.log
    # echo text2workspace.py $outputdc --out $outputfolder/workspace_S2.root -m 125 -v 3 -P HiggsAnalysis.CombinedLimit.PhysicsModel:multiSignalModel -v 0 --channel-masks --PO 'map=.*/ttbarsignal_genRho0to03:rate_ttj0[1.,-10.,10.]' --PO 'map=.*/ttbarsignal_genRho03to045:rate_ttj1[1.,-10.,10.]' --PO 'map=.*/ttbarsignal_genRho045to07:rate_ttj2[1.,-10.,10.]' --PO 'map=.*/ttbarsignal_genRho07to1:rate_ttj3[1.,-10.,10.]' --for-fits --no-wrappers --use-histsum --X-pack-asympows --optimize-simpdf-constraints=cms $systscaling > $outputfolder/workspace_S2.log

    # create the workspace in S1 scenario (keep systematics uncertainties as in Run 2)
    # text2workspace.py $outputdc --out $outputfolder/workspace_S1.root -m 125 -v 3 -P HiggsAnalysis.CombinedLimit.PhysicsModel:multiSignalModel -v 0 --channel-masks --PO 'map=.*/ttbarsignal_genRho0to03:rate_ttj0[1.,-10.,10.]' --PO 'map=.*/ttbarsignal_genRho03to045:rate_ttj1[1.,-10.,10.]' --PO 'map=.*/ttbarsignal_genRho045to07:rate_ttj2[1.,-10.,10.]' --PO 'map=.*/ttbarsignal_genRho07to1:rate_ttj3[1.,-10.,10.]' --for-fits --no-wrappers --use-histsum --X-pack-asympows --optimize-simpdf-constraints=cms  > $outputfolder/workspace_S1.log
    # echo text2workspace.py $outputdc --out $outputfolder/workspace_S1.root -m 125 -v 3 -P HiggsAnalysis.CombinedLimit.PhysicsModel:multiSignalModel -v 0 --channel-masks --PO 'map=.*/ttbarsignal_genRho0to03:rate_ttj0[1.,-10.,10.]' --PO 'map=.*/ttbarsignal_genRho03to045:rate_ttj1[1.,-10.,10.]' --PO 'map=.*/ttbarsignal_genRho045to07:rate_ttj2[1.,-10.,10.]' --PO 'map=.*/ttbarsignal_genRho07to1:rate_ttj3[1.,-10.,10.]' --for-fits --no-wrappers --use-histsum --X-pack-asympows --optimize-simpdf-constraints=cms  > $outputfolder/workspace_S1.log

    # ls
    # pwd

    # nohup ./fitscript.sh ${outputfolder} S1 ${lumiscaleParam} &
    # nohup ./fitscript.sh ${outputfolder} S1_noMCStat ${lumiscaleParam} &
    # nohup ./fitscript.sh ${outputfolder} S1_statOnly ${lumiscaleParam} &
    # nohup ./fitscript.sh ${outputfolder} S2 ${lumiscaleParam} &
    nohup ./fitscript.sh ${outputfolder} S3 ${lumiscaleParam} &

done