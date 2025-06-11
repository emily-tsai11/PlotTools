#!/bin/sh
python3 plotUnstacked.py --input_dir histos_03062025_scores/ --input_csv hconfig_scores.csv --output_dir purity_plots/CRSR/ --purity --multiRegion
python3 plotUnstacked.py --input_dir histos_03062025_scores/ --input_csv hconfig_scores.csv --output_dir purity_plots/CRSR/ --purity --multiRegion --raw_evt_number
