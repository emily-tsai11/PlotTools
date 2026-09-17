#!/bin/sh
# This script is used to run the hdumper to make histograms with fscores (i.e., those to fit)
# INPUT_DIR=/eos/cms/store/cmst3/group/top/rsalvatico/Vcb_analysis_07042026_2024_1L_Wcb/
PROD_VERSION=07042026_withLHEScale
CONFIG_FILE=configs/hconfig_fscores.csv
EXTRA_NAME=preselection_ge2bge1c_ttLFm0p1_fscores_withSysts
OUTPUT_DIR=histos_$PROD_VERSION/$EXTRA_NAME/
YEAR=2024
FLAVTAG_SF_JSON=$CMSSW_BASE/src/PhysicsTools/NanoTTH/data/flavTagSF/flavTaggingSF_2024.json.gz



# INPUT_DIR=/eos/cms/store/group/phys_top/Run3Vcb/20260904_trees/_2024_1L_Wcb
# time python3 hdumper_faster.py --input_dirs $INPUT_DIR/LHEWeight/ --output_dir $OUTPUT_DIR --tree_name Events --input_csv $CONFIG_FILE --year $YEAR --eventClassification --systematics
# INPUT_DIR=/eos/cms/store/group/phys_top/Run3Vcb/20260904_trees/customMCV2_2024_1L_Wcb
# time python3 hdumper_faster.py --input_dirs $INPUT_DIR/LHEWeight/ --output_dir $OUTPUT_DIR --tree_name Events --input_csv $CONFIG_FILE --year $YEAR --eventClassification --systematics
# INPUT_DIR=/eos/cms/store/group/phys_top/Run3Vcb/20260904_trees/customMC_ttbb_2024_1L_Wcb
# time python3 hdumper_faster.py --input_dirs $INPUT_DIR/LHEWeight/ --output_dir $OUTPUT_DIR --tree_name Events --input_csv $CONFIG_FILE --year $YEAR --eventClassification --systematics
# INPUT_DIR=/eos/cms/store/cmst3/group/top/rsalvatico/Vcb_analysis_04092026_2024_1L_Wcb
# time python3 hdumper_faster.py --input_dirs $INPUT_DIR/data/ --output_dir $OUTPUT_DIR --tree_name Events --input_csv $CONFIG_FILE --year $YEAR --eventClassification --systematics

INPUT_DIR=/eos/cms/store/user/etsai/storage/V_cbMeasurement/PlotTools/ntuples_07042026
time python3 hdumper_faster.py --input_dirs $INPUT_DIR/mc/ --output_dir $OUTPUT_DIR --tree_name Events --input_csv $CONFIG_FILE --year $YEAR --eventClassification --systematics



# python3 hdumper.py --input_dirs $INPUT_DIR/mc/ --output_dir $OUTPUT_DIR --tree_name Events --input_csv $CONFIG_FILE --year $YEAR --eventClassification
# python3 hdumper.py --input_dirs $INPUT_DIR/data/ --output_dir $OUTPUT_DIR --tree_name Events --input_csv $CONFIG_FILE --year $YEAR --eventClassification
