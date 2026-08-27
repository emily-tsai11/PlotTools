#!/bin/sh

#Initial fit
combineTool.py -M Impacts \
    -d workspace_Vcb_SL_2024.root \
    -m 125.38 \
    --setParameterRange r=0.5,1.5:xsec_ttbb=-5,5:xsec_ttbj=-5,5:xsec_tt2b=-5,5:xsec_ttcc=-5,5:xsec_ttcj=-5,5:xsec_tt2c=-5,5:xsec_ttLF=-5,5 \
    --setParameters xsec_ttbb=1,xsec_ttbj=1,xsec_tt2b=1,xsec_ttcc=1,xsec_ttcj=1,xsec_tt2c=1,xsec_ttLF=1,r=1 \
    --robustFit 1 \
    --doInitialFit \
    --floatOtherPOIs 1 \
    -t -1 \
    --X-rtd REMOVE_CONSTANT_ZERO_POINT=1 \
    --saveFitResult \
    --saveWorkspace \
    --saveNLL \
    --cminDefaultMinimizerStrategy 0 \
    --X-rtd MINIMIZER_MaxCalls=999999999 \
    --cminDefaultMinimizerTolerance 0.1 \
    --cminPreScan \
    --cminPreFit 1 \
    --X-rtd FAST_VERTICAL_MORPH

#Do fits floating the nuisance parameters one at a time
combineTool.py -M Impacts \
    -d workspace_Vcb_SL_2024.root \
    -m 125.38 \
    --setParameterRange r=0.5,1.5:xsec_ttbb=-5,5:xsec_ttbj=-5,5:xsec_tt2b=-5,5:xsec_ttcc=-5,5:xsec_ttcj=-5,5:xsec_tt2c=-5,5:xsec_ttLF=-5,5 \
    --setParameters xsec_ttbb=1,xsec_ttbj=1,xsec_tt2b=1,xsec_ttcc=1,xsec_ttcj=1,xsec_tt2c=1,xsec_ttLF=1,r=1 \
    --robustFit 1 \
    --doFits \
    -t -1 \
    --X-rtd REMOVE_CONSTANT_ZERO_POINT=1 \
    --saveFitResult \
    --saveWorkspace \
    --saveNLL \
    --cminDefaultMinimizerStrategy 0 \
    --X-rtd MINIMIZER_MaxCalls=999999999 \
    --cminDefaultMinimizerTolerance 0.1 \
    --cminPreScan \
    --cminPreFit 1 \
    --X-rtd FAST_VERTICAL_MORPH


#Produce a summary json
combineTool.py -M Impacts \
    -d workspace_Vcb_SL_2024.root \
    -m 125.38 \
    --setParameterRange r=0.5,1.5:xsec_ttbb=-5,5:xsec_ttbj=-5,5:xsec_tt2b=-5,5:xsec_ttcc=-5,5:xsec_ttcj=-5,5:xsec_tt2c=-5,5:xsec_ttLF=-5,5 \
    --setParameters xsec_ttbb=1,xsec_ttbj=1,xsec_tt2b=1,xsec_ttcc=1,xsec_ttcj=1,xsec_tt2c=1,xsec_ttLF=1,r=1 \
    --robustFit 1 \
    -t -1 \
    --X-rtd REMOVE_CONSTANT_ZERO_POINT=1 \
    --saveFitResult \
    --saveWorkspace \
    --saveNLL \
    --cminDefaultMinimizerStrategy 0 \
    --X-rtd MINIMIZER_MaxCalls=999999999 \
    --cminDefaultMinimizerTolerance 0.1 \
    --cminPreScan \
    --cminPreFit 1 \
    --X-rtd FAST_VERTICAL_MORPH \
    -o impacts.json
    
#Plot impacts
plotImpacts.py -i impacts.json -o impacts
