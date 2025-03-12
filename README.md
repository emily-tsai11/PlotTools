Plotting tools for the |Vcb| measurement - but not only!

# Examples

```
python3 hdumper.py --input_dirs /eos/cms/store/cmst3/group/top/rsalvatico/29012025_2018_1L/data/ --output_dir histos_02022025_scores/ --tree_name Events --input_csv hconfig_minimal.csv --year 2018
```

```
python3 plotter.py --input_dir histos_02022025_noExtra4Fweight/SR/ --output_dir plots_02022025_noExtra4Fweight/SR/ --input_csv hconfig.csv --sig_norm 5 --blind
```

```
python3 estimateCut.py --input_dir histos_02022025_scores/ --hist_name h_score_tt_Wcb h_fractional_score
```