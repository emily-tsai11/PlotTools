#!/bin/sh
# This script is used to run the hdumper to make histograms
python3 hdumper.py --input_dirs /eos/cms/store/cmst3/group/top/rsalvatico/29012025_2018_1L/mc/ --output_dir histos_16062025/  --tree_name Events --input_csv hconfig.csv --year 2018
python3 hdumper.py --input_dirs /eos/cms/store/cmst3/group/top/rsalvatico/29012025_2018_1L/data/ --output_dir histos_16062025/  --tree_name Events --input_csv hconfig.csv --year 2018