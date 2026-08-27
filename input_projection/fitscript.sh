#!/bin/sh

workspacePath=$1
# outFolder=$2
scenario=$2
lumiscaleParam=$3

echo ${workspacePath}
echo ${scenario}

combineArguments="--cminDefaultMinimizerTolerance 0.1 --cminDefaultMinimizerStrategy 1 --setParameters lumiscale=${lumiscaleParam},rgx{xsec_tt*}=1.,r=1 --setParameterRanges rgx{xsec_tt*}=0.,2. --X-rtd MINIMIZER_MaxCalls=999999999 --cminDefaultMinimizerPrecision 1E-12 --X-rtd FAST_VERTICAL_MORPH --mass 125.38 -t -1 --X-rtd REMOVE_CONSTANT_ZERO_POINT=1 --cminPreScan --cminPreFit 1 --redefineSignalPOIs r "
# combineArguments_ttH="--cminDefaultMinimizerTolerance 0.1 --cminDefaultMinimizerStrategy 1 --setParameters lumiscale=${lumiscaleParam},rgx{CMS_HIG24018_SFnorm_*}=1.,rgx{mask_.*_MidScoreVR.*}=1,rgx{mask_.*_vhcc_.*}=1 --setParameterRanges rgx{CMS_*SFnorm_*}=0.,2.:rgx{CMS_*SF_norm_ttZbb.*}=0.,5.:rgx{CMS_*SF_norm_ttZcc.*}=0.,10. --X-rtd MINIMIZER_MaxCalls=999999999 --cminDefaultMinimizerPrecision 1E-12 --X-rtd FAST_VERTICAL_MORPH --redefineSignalPOIs rate_Hcc --mass 125.38 -t -1 --X-rtd REMOVE_CONSTANT_ZERO_POINT=1 --cminPreScan --cminPreFit 1"
# combineArguments_VH="--cminDefaultMinimizerTolerance 0.1 --cminDefaultMinimizerStrategy 1 --setParameters lumiscale=${lumiscaleParam},rgx{CMS_HIG24018_SFnorm_*}=1.,rgx{mask_.*_MidScoreVR.*}=1,rgx{mask_.*_ttHcc_.*}=1 --setParameterRanges rgx{CMS_*SFnorm_*}=0.,2.:rgx{CMS_*SF_norm_ttZbb.*}=0.,5.:rgx{CMS_*SF_norm_ttZcc.*}=0.,10. --X-rtd MINIMIZER_MaxCalls=999999999 --cminDefaultMinimizerPrecision 1E-12 --X-rtd FAST_VERTICAL_MORPH --redefineSignalPOIs rate_Hcc --mass 125.38 -t -1 --X-rtd REMOVE_CONSTANT_ZERO_POINT=1 --cminPreScan --cminPreFit 1"

# nomFitArguments="--saveFitResult --saveWorkspace --robustHesse 1 -v 3"
# nomFitArguments="--saveFitResult --saveWorkspace -v 3"
# --robustFit 1 --stepSize 0.001 --cminPoiOnlyFit
# --cminPreScan --cminPreFit 1
nomFitArguments=""

cd $workspacePath

if [[ "${scenario}" == "S3" ]]; then

    # projections of upper limits to 3000/fb in S3 scenario (freezing all MCstat)

    # for combination
    echo combineTool.py -M AsymptoticLimits workspace_S3.root ${combineArguments} ${nomFitArguments} \
    -n _nominal_exp_limit_${scenario} --run blind \
    --freezeParameters rgx{prop.*} \
    >& performFit_exp_limit_${scenario}.txt > performFit_exp_limit_${scenario}.sh
    chmod u+x performFit_exp_limit_${scenario}.sh

    nohup combineTool.py -M AsymptoticLimits workspace_S3.root ${combineArguments} ${nomFitArguments} \
    -n _nominal_exp_limit_${scenario} --run blind \
    --freezeParameters rgx{prop.*} \
    >& performFit_exp_limit_${scenario}.txt &

    echo combineTool.py -M Significance workspace_S3.root ${combineArguments} ${nomFitArguments} \
    -n _nominal_exp_sig_${scenario} \
    --freezeParameters rgx{prop.*},r \
    >& performFit_exp_sig_${scenario}.txt > performFit_exp_sig_${scenario}.sh
    chmod u+x performFit_exp_sig_${scenario}.sh

    nohup combineTool.py -M Significance workspace_S3.root ${combineArguments} ${nomFitArguments} \
    -n _nominal_exp_sig_${scenario} \
    --freezeParameters rgx{prop.*},r \
    >& performFit_exp_sig_${scenario}.txt &

    # and multidimfit

    echo combine -M MultiDimFit workspace_S3.root ${combineArguments} ${nomFitArguments} \
     -n _nominal_exp_fit_${scenario} \
    --freezeParameters rgx{prop.*} \
    >& performFit_exp_${scenario}.txt > performFit_exp_${scenario}.sh
    chmod u+x performFit_exp_${scenario}.sh

    nohup combine -M MultiDimFit workspace_S3.root ${combineArguments} ${nomFitArguments} \
     --algo singles \
    -n _nominal_exp_fit_${scenario} --robustFit 1 \
    --freezeParameters rgx{prop.*} \
    >& performFit_exp_${scenario}.txt &
fi