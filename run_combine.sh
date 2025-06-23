#!/bin/sh
combine -M MultiDimFit -d workspace_Vcb_SL_2018.root --algo grid --setParameterRange rate_ratio=0,2:rate_tt=0,2 -P rate_ratio --floatOtherPOIs 1 --saveInactivePOI 1 --robustFit 1 --setParameters rate_ratio=1,rate_tt=1 -t -1
