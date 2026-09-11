#!/bin/sh

# Run toys
# combine -M HybridNew Vcb_SL_2024.txt \
#     --LHCmode LHC-significance  \
#     --saveToys \
#     --fullBToys \
#     --saveHybridResult \
#     -T 100 \
#     -i 5 \
#     -s 23456 \
#     --expectSignal 1 \
#     --cminDefaultMinimizerStrategy 0 \
#     --cminDefaultMinimizerTolerance 0.1 

datacard=Datacards_080526_ge2bge1c_fix_clean_simplified/datacards/Vcb_SL_2024.txt

# Read the result and exctract the significance. --expectedFromGrid=0.5 is needed to get the median expected significance, otherwise the observed significance will be returned
combine -M HybridNew ${datacard} \
    --LHCmode LHC-significance \
    --readHybridResult \
    --toysFile=toys.root \
    --expectedFromGrid=0.5 \
     --cminDefaultMinimizerStrategy 0 \
    --X-rtd MINIMIZER_MaxCalls=999999999 \
    --cminDefaultMinimizerTolerance 0.1 \
    --X-rtd FAST_VERTICAL_MORPH \
    --cminPreScan \
    --cminPreFit 1 \
    --setParameters rgx{xsec_tt.*}=1.,r=1. \
    --setParameterRanges rgx{xsec_tt.*}=-3.,3. \
    --redefineSignalPOIs r


        # --toysFile=higgsCombineTest.HybridNew.mH120.23456.root \