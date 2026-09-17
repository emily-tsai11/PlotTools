#!/bin/sh
PROD_VERSION=20260407_withLHEScale
EXTRA_NAME=preselection_ge2bge1c_ttLFm0p1_withSysts
# EXTRA_PATH1=unstacked
# EXTRA_PATH2=unstacked/ttLFm0p1
# EXTRA_PATH3=purity/ttLFm0p1_and_classification_cuts
# EXTRA_PATH4=FS_vs_score
INPUT_DIR=/afs/cern.ch/user/r/rselvati/public/forEmily/
OUTPUT_DIR=/eos/user/e/etsai/www/V_cbMeasurement/analysis/plots_$PROD_VERSION/$EXTRA_NAME/

# Unstacked scores for signal, ttLF, total background
# python3 plotUnstacked.py --input_dir histos_$PROD_VERSION/scores/ --input_csv configs/hconfig_scores.csv --output_dir $OUTPUT_DIR/unstacked/ --process ttLF --log
# python3 plotUnstacked.py --input_dir histos_$PROD_VERSION/scores/ --input_csv configs/hconfig_scores.csv --output_dir $OUTPUT_DIR/unstacked/ --process ttbb --log
# python3 plotUnstacked.py --input_dir histos_$PROD_VERSION/scores/ --input_csv configs/hconfig_scores.csv --output_dir $OUTPUT_DIR/unstacked/ --process tt2b --log
# python3 plotUnstacked.py --input_dir histos_$PROD_VERSION/scores/ --input_csv configs/hconfig_scores.csv --output_dir $OUTPUT_DIR/unstacked/ --process ttbj --log
# python3 plotUnstacked.py --input_dir histos_$PROD_VERSION/scores/ --input_csv configs/hconfig_scores.csv --output_dir $OUTPUT_DIR/unstacked/ --process ttcc --log
# python3 plotUnstacked.py --input_dir histos_$PROD_VERSION/scores/ --input_csv configs/hconfig_scores.csv --output_dir $OUTPUT_DIR/unstacked/ --process tt2c --log
# python3 plotUnstacked.py --input_dir histos_$PROD_VERSION/scores/ --input_csv configs/hconfig_scores.csv --output_dir $OUTPUT_DIR/unstacked/ --process ttcj --log

# python3 plotUnstacked.py --input_dir histos_$PROD_VERSION/scores/$EXTRA_NAME/ --input_csv configs/hconfig_scores.csv --output_dir $OUTPUT_DIR/unstacked/$EXTRA_NAME/ --process ttLF --log
# python3 plotUnstacked.py --input_dir histos_$PROD_VERSION/scores/$EXTRA_NAME/ --input_csv configs/hconfig_scores.csv --output_dir $OUTPUT_DIR/unstacked/$EXTRA_NAME/ --process ttbb --log
# python3 plotUnstacked.py --input_dir histos_$PROD_VERSION/scores/$EXTRA_NAME/ --input_csv configs/hconfig_scores.csv --output_dir $OUTPUT_DIR/unstacked/$EXTRA_NAME/ --process tt2b --log
# python3 plotUnstacked.py --input_dir histos_$PROD_VERSION/scores/$EXTRA_NAME/ --input_csv configs/hconfig_scores.csv --output_dir $OUTPUT_DIR/unstacked/$EXTRA_NAME/ --process ttbj --log
# python3 plotUnstacked.py --input_dir histos_$PROD_VERSION/scores/$EXTRA_NAME/ --input_csv configs/hconfig_scores.csv --output_dir $OUTPUT_DIR/unstacked/$EXTRA_NAME/ --process ttcc --log
# python3 plotUnstacked.py --input_dir histos_$PROD_VERSION/scores/$EXTRA_NAME/ --input_csv configs/hconfig_scores.csv --output_dir $OUTPUT_DIR/unstacked/$EXTRA_NAME/ --process tt2c --log
# python3 plotUnstacked.py --input_dir histos_$PROD_VERSION/scores/$EXTRA_NAME/ --input_csv configs/hconfig_scores.csv --output_dir $OUTPUT_DIR/unstacked/$EXTRA_NAME/ --process ttcj --log

# Purity/evt number plots for CRs and SR
time python3 plotUnstacked.py \
  --input_dir $INPUT_DIR \
  --output_dir $OUTPUT_DIR/CRSR/purity/ \
  --purity \
  --multiRegion
time python3 plotUnstacked.py \
  --input_dir $INPUT_DIR \
  --output_dir $OUTPUT_DIR/CRSR/purity/ \
  --purity \
  --multiRegion \
  --raw_evt_number
python3 /eos/user/e/etsai/www/.bin/pb_copy_index.py -r /eos/user/e/etsai/www/V_cbMeasurement/analysis/plots_$PROD_VERSION/

# Purity/evt number plots for 4FS vs 5FS in ttbb, tt2b, and ttbj
# python3 plotUnstacked.py --input_dir histos_$PROD_VERSION/$EXTRA_NAME/ --output_dir $OUTPUT_DIR/purity/$EXTRA_NAME/FS/ --plot_4F5F --process ttbb
# python3 plotUnstacked.py --input_dir histos_$PROD_VERSION/$EXTRA_NAME/ --output_dir $OUTPUT_DIR/purity/$EXTRA_NAME/FS/ --plot_4F5F --process ttbb --raw_evt_number
# python3 plotUnstacked.py --input_dir histos_$PROD_VERSION/$EXTRA_NAME/ --output_dir $OUTPUT_DIR/purity/$EXTRA_NAME/FS/ --plot_4F5F --process tt2b
# python3 plotUnstacked.py --input_dir histos_$PROD_VERSION/$EXTRA_NAME/ --output_dir $OUTPUT_DIR/purity/$EXTRA_NAME/FS/ --plot_4F5F --process tt2b --raw_evt_number
# python3 plotUnstacked.py --input_dir histos_$PROD_VERSION/$EXTRA_NAME/ --output_dir $OUTPUT_DIR/purity/$EXTRA_NAME/FS/ --plot_4F5F --process ttbj
# python3 plotUnstacked.py --input_dir histos_$PROD_VERSION/$EXTRA_NAME/ --output_dir $OUTPUT_DIR/purity/$EXTRA_NAME/FS/ --plot_4F5F --process ttbj --raw_evt_number

# 4FS vs 5FS comparison of ttbb+ttbj+tt2b in the ttWcb score
# python3 plotUnstacked.py --input_dir histos_$PROD_VERSION/$EXTRA_NAME/score_tt_Wcb/ --output_dir $OUTPUT_DIR/$EXTRA_PATH4/ --plot_4F5F_vs_score --process ttbx
# python3 plotUnstacked.py --input_dir histos_$PROD_VERSION/$EXTRA_NAME/score_tt_Wcb/ --output_dir $OUTPUT_DIR/$EXTRA_PATH4/ --plot_4F5F_vs_score --process ttbb
# python3 plotUnstacked.py --input_dir histos_$PROD_VERSION/$EXTRA_NAME/score_tt_Wcb/ --output_dir $OUTPUT_DIR/$EXTRA_PATH4/ --plot_4F5F_vs_score --process ttbj
# python3 plotUnstacked.py --input_dir histos_$PROD_VERSION/$EXTRA_NAME/score_tt_Wcb/ --output_dir $OUTPUT_DIR/$EXTRA_PATH4/ --plot_4F5F_vs_score --process tt2b

# Plot significance
# python3 plotUnstacked.py --input_dir histos_01102025/scores/ --hist_name h_score_tt_Wcb --output_dir plots_01102025/unstacked/ttLFm0p1/ --significance --log

# mkdir -p /eos/user/r/rselvati/www/Vcb/Run3/$PROD_VERSION/$EXTRA_PATH1
# mkdir -p /eos/user/r/rselvati/www/Vcb/Run3/$PROD_VERSION/$EXTRA_PATH2
# mkdir -p /eos/user/r/rselvati/www/Vcb/Run3/$PROD_VERSION/$EXTRA_PATH3
# mkdir -p /eos/user/r/rselvati/www/Vcb/Run3/$PROD_VERSION/$EXTRA_PATH4
# cp /eos/user/r/rselvati/www/index.php /eos/user/r/rselvati/www/Vcb/Run3/$PROD_VERSION/
# cp /eos/user/r/rselvati/www/index.php /eos/user/r/rselvati/www/Vcb/Run3/$PROD_VERSION/$EXTRA_PATH1/
# cp /eos/user/r/rselvati/www/index.php /eos/user/r/rselvati/www/Vcb/Run3/$PROD_VERSION/$EXTRA_PATH2/
# cp /eos/user/r/rselvati/www/index.php /eos/user/r/rselvati/www/Vcb/Run3/$PROD_VERSION/$EXTRA_PATH3/
# cp /eos/user/r/rselvati/www/index.php /eos/user/r/rselvati/www/Vcb/Run3/$PROD_VERSION/$EXTRA_PATH4/
# cp $OUTPUT_DIR/$EXTRA_PATH1/* /eos/user/r/rselvati/www/Vcb/Run3/$PROD_VERSION/$EXTRA_PATH1/
# cp $OUTPUT_DIR/$EXTRA_PATH2/* /eos/user/r/rselvati/www/Vcb/Run3/$PROD_VERSION/$EXTRA_PATH2/
# cp $OUTPUT_DIR/purity/$EXTRA_NAME/CRSR/* /eos/user/r/rselvati/www/Vcb/Run3/$PROD_VERSION/$EXTRA_PATH3/
# cp $OUTPUT_DIR/purity/$EXTRA_NAME/FS/* /eos/user/r/rselvati/www/Vcb/Run3/$PROD_VERSION/$EXTRA_PATH3/
# cp $OUTPUT_DIR/$EXTRA_PATH4/* /eos/user/r/rselvati/www/Vcb/Run3/$PROD_VERSION/$EXTRA_PATH4/