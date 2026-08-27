#!/bin/sh

INPUT_DIR=/eos/cms/store/cmst3/group/top/rsalvatico/Vcb_analysis_07042026_2024_1L_Wcb
PROD_VERSION=07042026
EXTRA_NAME=
SYST_DIR=/eos/cms/store/cmst3/group/top/rsalvatico/Vcb_analysis_07042026_syst_2024_1L_Wcb/
OUTPUT_DIR=datacard_preparation_07042026_correctTTweights_5FS/
YEAR=2024
FLAVTAG_SF_JSON=$CMSSW_BASE/src/PhysicsTools/NanoTTH/data/flavTagSF/flavTaggingSF_2024.json.gz


python3 prepareHistosForCards_fast.py --input_dirs $INPUT_DIR/data/ --output_dir $OUTPUT_DIR --tree_name Events --year $YEAR --nproc 16 
python3 prepareHistosForCards_fast.py --input_dirs $INPUT_DIR/mc/ --output_dir $OUTPUT_DIR --tree_name Events --year $YEAR --nproc 16 --extra_syst_dir $SYST_DIR --flavtag_sf_json $FLAVTAG_SF_JSON --use5FS

#python3 prepareHistosForCards_fast.py --input_dirs $INPUT_DIR/mc/ --output_dir $OUTPUT_DIR --tree_name Events --year $YEAR --nproc 16 --extra_syst_dir $SYST_DIR --flavtag_sf_json $FLAVTAG_SF_JSON --extra_syst_only