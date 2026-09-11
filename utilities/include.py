#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# import sys
# if sys.version_info[:2] != (3, 8):
#     print ("include.py: Initialize correct python version first!")
#     print (sys.version_info[:2])
#     sys.exit()



# import suppressor
# with suppressor.suppress_stdout_stderr():
#     import ROOT
import ROOT
from ROOT import gROOT
ROOT.PyConfig.IgnoreCommandLineOptions = False
ROOT.gROOT.gPrintViaErrorHandler = True
gROOT.gPrintViaErrorHandler = True

gROOT.SetBatch(True)
ROOT.gROOT.SetBatch(True)

import array
import argparse
import collections
import math
import os.path
import optparse
import re
import subprocess

# private libs
import ratio
import style
import multiplot
import auxiliary as aux
# from datasets import *
# import cmsstyle as CMS
