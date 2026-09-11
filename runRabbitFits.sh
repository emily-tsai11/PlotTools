#!/bin/bash
# Everything the Combine chain produces, from one merged shapes file, locally.
#
#   cmsenv
#   source setup_rabbit.sh
#   ./runRabbitFits.sh
#
# BLINDING: the signal region is blinded. Data fits run only for configurations
# that mask the SR. Configurations that include the SR run on Asimov only.
# A masked channel is still evaluated, so a CR-only fit still predicts the SR.

set -e

# ---------------------------------------------------------------- settings
SHAPES=Datacards_100626_ge2bge1c_fix_clean_onlySurvivingVeto/orig/Vcb_SL_2024_shapes.root
OUTDIR=RabbitFits_onlySurvivingVeto
JOBS=${JOBS:-8}     # fits run concurrently; each rabbit fit is single core
SCANPOINTS=${SCANPOINTS:-31}   # per scanned parameter, and every free parameter is scanned
PLOTS=${PLOTS:-0}   # PLOTS=1 also writes the per-entry smoothing/lnN diagnostic plots
PLOTCHANNELS=${PLOTCHANNELS:-catLF}   # regex, which categories get diagnostics

FREENORM="ttbb,ttbj,tt2b,ttcc,ttcj,tt2c,ttLF"
# The free normalisations of the tt+X components are real POIs, supplied at fit
# time by analysis/rabbit_models.FreeNorm (value = the norm multiplier itself,
# not exp(ln(kappa)*theta)). They are NOT written into the tensor. On observed
# fits rabbit blinds every POI, so the observed fits below unblind xsec_* while
# tt-vcb stays blinded (see COMBINE_FIXES.md).
PMODEL="--paramModel Mu --paramModel analysis.rabbit_models.FreeNorm ${FREENORM}"
XSECPOIS="xsec_ttbb xsec_ttbj xsec_tt2b xsec_ttcc xsec_ttcj xsec_tt2c xsec_ttLF"
# freeze every parameter that is not a POI -> stat-only (regex is fullmatch)
STATONLY=(--freezeParameters '(?!tt-vcb$|xsec_).*' --noBinByBinStat)

# config : mask regex : data allowed : POI to scan : parameters to freeze
# With the SR masked the signal is unconstrained, so tt-vcb is frozen and a
# control-region normalisation takes over as the parameter of interest.
CONFIGS=(
    "SR::no:tt-vcb:"
    "CR:_SR\$:yes:xsec_ttLF:tt-vcb"
    "CRnolf:_SR\$|catLF:yes:xsec_ttbb:tt-vcb"
)

mkdir -p ${OUTDIR}

# ------------------------------------------------------- plotting one fit
# Called right after each fit, so plots appear while the rest still runs.
# Each rabbit fit saturates exactly one core (raising OPENBLAS_NUM_THREADS does
# nothing: 214x214 matrices are too small for threaded BLAS), so the machine is
# only used by running the independent fits side by side.
slot() { while [ "$(jobs -rp | wc -l)" -ge "${JOBS}" ]; do wait -n; done; }

makeplots() {
    local F=$1
    [ -e "${F}" ] || return 0
    local TAG P D ASIMOV
    TAG=$(basename ${F} .hdf5)
    echo "### plots for ${TAG}"
    case ${TAG} in
        fit_SR_*)     P=tt-vcb ;;
        fit_CRnolf_*) P=xsec_ttbb ;;
        *)            P=xsec_ttLF ;;
    esac
    # _exp/_statonly are Asimov (-t -1); _obs is real (blinding-safe) data
    case ${TAG} in *_obs) ASIMOV=() ;; *) ASIMOV=(--asimov) ;; esac
    D=${OUTDIR}/plots/${TAG}
    mkdir -p ${D}/scans ${D}/impacts ${D}/prepostfit ${D}/categories

    # one figure per scanned parameter, value and interval in the header
    python3 analysis/rabbitPlotScan.py ${F} -o ${D}/scans --postfix ${TAG} "${ASIMOV[@]}" \
        || echo "  (scan plots failed for ${TAG})"

    # a stat-only fit is run without --doImpacts/--saveHists, so it has neither
    # impacts nor histograms to plot
    case ${TAG} in *_statonly) return 0 ;; esac

    # static png/pdf impacts: traditional and global, grouped and ungrouped
    for IT in traditional global; do
        for G in "" --grouped; do
            python3 analysis/rabbitPlotImpacts.py ${F} --poi ${P} -o ${D}/impacts \
                --postfix ${TAG} --impact-type ${IT} ${G} "${ASIMOV[@]}" \
                || echo "  (impact plot ${IT} ${G} failed for ${TAG})"
        done
    done

    # every category stacked and unrolled into one histogram
    python3 analysis/rabbitPlotStack.py ${F} -o ${D}/prepostfit --postfix ${TAG} --logy "${ASIMOV[@]}" \
        || echo "  (stack plot failed for ${TAG})"
    # -m BaseMapping is required: without --mapping the script plots nothing
    rabbit_plot_hists.py ${F} -o ${D}/categories -m BaseMapping \
        || echo "  (per-category plots failed for ${TAG})"
}


for ENTRY in "${CONFIGS[@]}"; do
    IFS=: read -r CFG MASK DATA POI FREEZE <<< "${ENTRY}"
    T=${OUTDIR}/tensor_${CFG}.hdf5

    EXTRA=()
    [ -n "${MASK}" ]   && EXTRA+=(--mask "${MASK}")
    # the diagnostics do not depend on the masking, so write them once
    # PLOTCHANNELS limits the diagnostics; all 8 categories is ~16000 figures
    [ "${PLOTS}" = "1" ] && [ -z "${MASK}" ] && EXTRA+=(--plots --plot-channels "${PLOTCHANNELS}")

    FRZ=()
    [ -n "${FREEZE}" ] && FRZ=(--freezeParameters "${FREEZE}")
    # scan every free parameter, except any that this configuration freezes
    if [ -n "${FREEZE}" ]; then SCANLIST="${XSECPOIS}"; else SCANLIST="tt-vcb ${XSECPOIS}"; fi

    echo "### ${CFG}: tensor (mask='${MASK}')  POI=${POI}"
    # REDO=1 rebuilds a tensor that is already there
    if [ ! -f ${T} ] || [ "${REDO:-0}" = "1" ]; then
        python3 analysis/prepareTensor.py ${SHAPES} -o ${OUTDIR} --outname tensor_${CFG} "${EXTRA[@]}"
    else
        echo "  ${T} exists, reusing it"
    fi

    # upstream sanity check on the tensor (empty bins, extreme variations, ...)
    rabbit_debug_inputdata.py ${T} 2>&1 | sed 's/\x1b\[[0-9;]*m//g' \
        > ${OUTDIR}/debug_inputdata_${CFG}.log
    grep -E "^INFO.*(✗|potential issues)" ${OUTDIR}/debug_inputdata_${CFG}.log | head -3
    # one line per nuisance: shape or norm, how many entries, how large
    if [ -f ${OUTDIR}/tensor_${CFG}_decisions.csv ]; then
        python3 analysis/systematicsReport.py ${OUTDIR}/tensor_${CFG}_decisions.csv \
            --top 20 > ${OUTDIR}/systematics_report_${CFG}.txt
        head -3 ${OUTDIR}/systematics_report_${CFG}.txt
    fi

    echo "### ${CFG}: Asimov fit + scan + impacts + postfit shapes + saturated GoF"
    slot; {
        rabbit_fit.py ${T} -o ${OUTDIR} --outname fit_${CFG}_exp -t -1 ${PMODEL} "${FRZ[@]}" \
            --scan ${SCANLIST} --scanPoints ${SCANPOINTS} \
            --doImpacts --globalImpacts \
            --saveHists --saveHistsPerProcess --computeHistErrors --computeHistImpacts \
            && makeplots ${OUTDIR}/fit_${CFG}_exp.hdf5
    } > ${OUTDIR}/log_${CFG}_exp.log 2>&1 &

    echo "### ${CFG}: Asimov stat-only scan"
    slot; {
        rabbit_fit.py ${T} -o ${OUTDIR} --outname fit_${CFG}_statonly -t -1 ${PMODEL} \
            --scan ${SCANLIST} --scanPoints ${SCANPOINTS} "${STATONLY[@]}" \
            && makeplots ${OUTDIR}/fit_${CFG}_statonly.hdf5
    } > ${OUTDIR}/log_${CFG}_statonly.log 2>&1 &

    if [ "${DATA}" = "yes" ]; then
        echo "### ${CFG}: OBSERVED fit (SR masked, so this is blinded-safe)"
        slot; {
            rabbit_fit.py ${T} -o ${OUTDIR} --outname fit_${CFG}_obs -t 0 ${PMODEL} "${FRZ[@]}" \
                --unblind 'xsec_.*' \
                --scan ${SCANLIST} --scanPoints ${SCANPOINTS} \
                --doImpacts --globalImpacts --saveHists --saveHistsPerProcess \
                --computeHistErrors \
                && makeplots ${OUTDIR}/fit_${CFG}_obs.hdf5
        } > ${OUTDIR}/log_${CFG}_obs.log 2>&1 &
    else
        echo "### ${CFG}: observed fit SKIPPED - SR is not masked and we are blinded"
    fi
done

echo "### waiting for ${JOBS}-way parallel fits (per-fit logs: ${OUTDIR}/log_*.log)"
wait

# ------------------------------------------------------------- 3) summary
echo "### results"
python3 - "${OUTDIR}" <<'PY'
import glob, os, sys
import numpy as np
from scipy import stats
from rabbit import io_tools
from analysis.rabbitResults import read_parameters, poi_names

for f in sorted(glob.glob(os.path.join(sys.argv[1], "fit_*.hdf5"))):
    try:
        pars, pois = read_parameters(f), poi_names(f)
        fr = io_tools.get_fitresult(f)
    except Exception as exc:
        print(f"{os.path.basename(f):28s} unreadable ({exc})")
        continue
    # nllvalreduced is the saturated delta-NLL; the Combine GoF test statistic
    # is 2*deltaNLL (checked against -M GoodnessOfFit --algo=saturated: 52.02 vs
    # 51.40 on the same model)
    chi2, ndf = 2.0 * float(fr["nllvalreduced"]), int(fr["ndfsat"])
    p = stats.chi2.sf(chi2, ndf) if ndf > 0 else float("nan")
    print(f"\n{os.path.basename(f)}")
    print(f"   saturated GoF  chi2/ndf = {chi2:.1f}/{ndf} = {chi2/max(ndf,1):.2f}   p = {p:.3g}")
    for p_ in pois:
        v, e = pars[p_]
        print(f"   {p_:<14s} {v:8.4f} +/- {e:.4f}")
PY

# --------------------------------------------------------------- 4) plots
echo "### done -> ${OUTDIR}"
