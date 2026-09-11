#!/bin/sh

currentDir=$(pwd)

# workspaceDir=RiccardoTemplatesNew_simplified/datacards/workspace_Vcb_SL_2024.root
# workspaceDir=Datacards_070526_ge2bge1c_simplified/datacards/
# workspaceDir=Datacards_070526_ge2bge1c_fix_simplified/datacards/
# workspaceDir=Datacards_070526_ge2bge1c_fix_smoothed_simplified/datacards/
# workspaceDir=Datacards_070526_ge2bge1c_fix/orig/
# workspaceDir=Datacards_080526_ge2bge1c_fix_clean_simplified/datacards/
# workspaceDir=Datacards_100626_ge2bge1c_fix_clean_simplified/datacards/
workspaceDir=Datacards_100626_ge2bge1c_fix_clean_simplified_forGiacomo/datacards/
cd "${workspaceDir}" || exit 1

COMMON_OPTS="--algo grid --points 250 -m 125.38 \
    --cminDefaultMinimizerStrategy 0 \
    --X-rtd MINIMIZER_MaxCalls=999999999 \
    --cminDefaultMinimizerTolerance 0.1 \
    --X-rtd FAST_VERTICAL_MORPH \
    --cminPreScan \
    --cminPreFit 1 \
    --setParameterRange r=0.2,1.8:xsec_ttbb=-5,5:xsec_ttbj=-5,5:xsec_tt2b=-5,5:xsec_ttcc=-5,5:xsec_ttcj=-5,5:xsec_tt2c=-5,5:xsec_ttLF=-5,5 \
    --setParameters xsec_ttbb=1,xsec_ttbj=1,xsec_tt2b=1,xsec_ttcc=1,xsec_ttcj=1,xsec_tt2c=1,xsec_ttLF=1,r=1 \
    --robustFit 1 \
    -t -1"

#Run first likelihood scan on the POI Vcb
combine -M MultiDimFit -d workspace_Vcb_SL_2024.root ${COMMON_OPTS} \
    --floatOtherPOIs 1 \
    -n VcbScan

    # --saveInactivePOI 1 \


#Run a second scan freezing all systematics. --freezeParameters allConstrainedNuisances should be needed to also freeze the shape nuisances.
combine -M MultiDimFit -d workspace_Vcb_SL_2024.root ${COMMON_OPTS} \
    --freezeNuisanceGroups systematics,autoMCStats \
    --freezeParameters allConstrainedNuisances \
    -n VcbScan_FrozenSys

    # --saveInactivePOI 1 \


#Plot the likelihood scan result
python3 ${currentDir}/plot1DScan.py higgsCombineVcbScan.MultiDimFit.mH125.38.root \
    --POI r \
    --main-label "Total" \
    --others higgsCombineVcbScan_FrozenSys.MultiDimFit.mH125.38.root:Stat:2 \
    --logo-sub "Preliminary"

cd ${currentDir}



# combine -M MultiDimFit -d workspace_Vcb_SL_2024.root -t -1 -n VcbCmp_simp --mass 125.38 --algo grid --points 100 --cminDefaultMinimizerStrategy 0 --X-rtd MINIMIZER_MaxCalls=999999999 --cminDefaultMinimizerTolerance 0.1 --X-rtd FAST_VERTICAL_MORPH --cminPreScan --cminPreFit 1 --floatOtherPOIs 1 --robustFit 1 --setParameterRange r=0.2,1.7:xsec_ttbb=-5,5:xsec_ttbj=-5,5:xsec_tt2b=-5,5:xsec_ttcc=-5,5:xsec_ttcj=-5,5:xsec_tt2c=-5,5:xsec_ttLF=-5,5 --setParameters xsec_ttbb=1,xsec_ttbj=1,xsec_tt2b=1,xsec_ttcc=1,xsec_ttcj=1,xsec_tt2c=1,xsec_ttLF=1,r=1



# combine -M MultiDimFit -d workspace_Vcb_SL_2024.root -t -1 -n VcbCmp_orig --mass 125.38 --algo grid --points 100 --cminDefaultMinimizerStrategy 0 --X-rtd MINIMIZER_MaxCalls=999999999 --cminDefaultMinimizerTolerance 0.1 --X-rtd FAST_VERTICAL_MORPH --cminPreScan --cminPreFit 1 --floatOtherPOIs 1 --robustFit 1 --setParameterRange r=0.2,1.7:xsec_ttbb=-5,5:xsec_ttbj=-5,5:xsec_tt2b=-5,5:xsec_ttcc=-5,5:xsec_ttcj=-5,5:xsec_tt2c=-5,5:xsec_ttLF=-5,5 --setParameters xsec_ttbb=1,xsec_ttbj=1,xsec_tt2b=1,xsec_ttcc=1,xsec_ttcj=1,xsec_tt2c=1,xsec_ttLF=1,r=1

# combine -M MultiDimFit -d workspace_Vcb_SL_2024.root -n VcbCmp_simp_obs --mass 125.38 --algo grid --points 100 --cminDefaultMinimizerStrategy 0 --X-rtd MINIMIZER_MaxCalls=999999999 --cminDefaultMinimizerTolerance 0.1 --X-rtd FAST_VERTICAL_MORPH --cminPreScan --cminPreFit 1 --floatOtherPOIs 1 --robustFit 1 --setParameterRange r=0.2,1.7:xsec_ttbb=-5,5:xsec_ttbj=-5,5:xsec_tt2b=-5,5:xsec_ttcc=-5,5:xsec_ttcj=-5,5:xsec_tt2c=-5,5:xsec_ttLF=-5,5 --setParameters xsec_ttbb=1,xsec_ttbj=1,xsec_tt2b=1,xsec_ttcc=1,xsec_ttcj=1,xsec_tt2c=1,xsec_ttLF=1,r=1