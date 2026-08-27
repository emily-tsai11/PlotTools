#!/bin/bash
# INPUT_DIR="/afs/cern.ch/work/r/rselvati/private/Vcb/CMSSW_15_0_10/src/PhysicsTools/PlotTools/datacards_14032026_v4"
INPUT_DIR="Datacards_070526_ge2bge1c_simplified/datacards/"
# DATACARD="Vcb_SL_2024.txt"
DATACARD="workspace_Vcb_SL_2024.root"
N_TOYS=1000
N_ITER=10
SEEDS=12345,23456,34567

python3 significanceToysCondor.py \
    -i $INPUT_DIR \
    -d $DATACARD \
    -T $N_TOYS \
    --iter $N_ITER \
    -s $SEEDS