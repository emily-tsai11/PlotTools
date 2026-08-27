#!/bin/bash
# One proper Combine <-> rabbit validation on a single datacard.
#
#   cmsenv && source setup_rabbit.sh
#   ./validateCombineRabbit.sh Datacards_190826_clean/orig Validation_190826
#
# Three configurations, and the signal region never sees data:
#   SR   CR + SR, Asimov,   POI r / tt-vcb
#   CR   CR only, Asimov,   POI xsec_ttLF, r frozen
#   CRo  CR only, OBSERVED, POI xsec_ttLF, r frozen   (blinded-safe: SR masked)
#
# Two rabbit legs:
#   A  analysis/cardToTensor.py on the datacard  -> identical model to combine,
#      so any difference is the minimiser or the Hessian
#   B  analysis/prepareTensor.py on the shapes   -> our pruning, smoothing and
#      shape->norm decisions
#
# Two combine error modes, because the default Minuit Hessian has been measured
# to be unreliable on this model (see COMBINE_FIXES.md).
#
# No combine goodness of fit: rabbit reports the saturated statistic
# (2*nllvalreduced) for free in every fit, already validated against
# -M GoodnessOfFit --algo=saturated.

set -e

CARDDIR=${1:-Datacards_190826_clean/orig}
OUT=${2:-Validation_190826}
JOBS=${JOBS:-$(nproc)}
SCANPOINTS=${SCANPOINTS:-31}

BASE=$(cd "$(dirname "$0")" && pwd)
CARD=${BASE}/${CARDDIR}/Vcb_SL_2024.txt
WS=${BASE}/${CARDDIR}/workspace_Vcb_SL_2024.root
SHAPES=${BASE}/${SHAPES_REL:-${CARDDIR}/Vcb_SL_2024_shapes.root}
OUT=${BASE}/${OUT}

FREENORM="ttbb,ttbj,tt2b,ttcc,ttcj,tt2c,ttLF"
XSEC="xsec_ttbb xsec_ttbj xsec_tt2b xsec_ttcc xsec_ttcj xsec_tt2c xsec_ttLF"
XSEC_CSV=$(echo ${XSEC} | tr ' ' ',')
MASKSR="rgx{mask_.*_SR.*}=1"

# Setup map (user's A-E):  A/B = combine default/robustHesse (below);
#   C = rabbit our workflow (leg B, ourSR/ourCR);  E = rabbit combineConverter
#   (leg A, cardSR/cardCR);  D = rabbit our workflow with the reduction steps
#   ISOLATED one at a time (matches Fixed_190826). Each D trial isolates one
#   piece; "full" (all pieces on) is setup C.
declare -A DTRIAL=(
    [raw]="--no-smoothing --p-shape 1.0 --thr-total 0.0 --no-symmetrisation"
    [smOnly]="--p-shape 1.0 --thr-total 0.0 --no-symmetrisation"
    [isoNorm]="--no-smoothing --thr-total 0.0 --no-symmetrisation"
    [isoPrune]="--no-smoothing --p-shape 1.0 --no-symmetrisation"
)

mkdir -p ${OUT}/combine ${OUT}/rabbit ${OUT}/plots
cd ${BASE}

# `wait -n` returns the exit status of whichever job finished, so under `set -e`
# one failed scan would kill the whole script without a message.
slot() { while [ "$(jobs -rp | wc -l)" -ge "${JOBS}" ]; do wait -n || true; done; }

# ------------------------------------------------------------------ tensors
echo "### tensors (parallel, JOBS=${JOBS})"
buildprep() {  # <outname> <extra prepareTensor flags...>
    [ -f ${OUT}/rabbit/$1.hdf5 ] && { echo "  $1 tensor exists, reusing it"; return 0; }
    local N=$1; shift
    python3 analysis/prepareTensor.py ${SHAPES} -o ${OUT}/rabbit --outname ${N} "$@"
}
# E = verbatim converter ; C = our full workflow
[ -f ${OUT}/rabbit/cardSR.hdf5 ] || { slot; python3 analysis/cardToTensor.py ${CARD} -o ${OUT}/rabbit --outname cardSR               > ${OUT}/rabbit/log_tensor_cardSR.log 2>&1 & }
[ -f ${OUT}/rabbit/cardCR.hdf5 ] || { slot; python3 analysis/cardToTensor.py ${CARD} -o ${OUT}/rabbit --outname cardCR --mask '_SR$' > ${OUT}/rabbit/log_tensor_cardCR.log 2>&1 & }
slot; buildprep ourSR               > ${OUT}/rabbit/log_tensor_ourSR.log 2>&1 &
slot; buildprep ourCR --mask '_SR$' > ${OUT}/rabbit/log_tensor_ourCR.log 2>&1 &
if [ "${WITH_D:-1}" = "1" ]; then
# D = isolation trials, SR (unmasked) and CR (masked)
for T in "${!DTRIAL[@]}"; do
    slot; buildprep D${T}SR ${DTRIAL[$T]}               > ${OUT}/rabbit/log_tensor_D${T}SR.log 2>&1 &
    slot; buildprep D${T}CR ${DTRIAL[$T]} --mask '_SR$' > ${OUT}/rabbit/log_tensor_D${T}CR.log 2>&1 &
done
fi
echo "### waiting for tensors"
wait || true

rabbit_debug_inputdata.py ${OUT}/rabbit/ourSR.hdf5 2>&1 | sed 's/\x1b\[[0-9;]*m//g' \
    > ${OUT}/debug_inputdata_ourSR.log || true
python3 analysis/systematicsReport.py ${OUT}/rabbit/ourSR_decisions.csv --top 20 \
    > ${OUT}/systematics_report.txt || true

# ------------------------------------------------------------- rabbit fits
# leg A: the converted card has no POIs beyond the signal, the rateParams come
# through as unconstrained lnN (undone by compareCombine.py --rateparam-lnn)
echo "### rabbit fits"
PM_A="--paramModel Mu"
PM_B="--paramModel Mu --paramModel analysis.rabbit_models.FreeNorm ${FREENORM}"

# A rabbit fit creates its output file at the start and fills it at the end, so
# "the file exists" means nothing. Two runs writing the same name corrupt it
# (results survives, meta does not), hence a real readability check.
fitdone() {
    python3 -c "import sys; from rabbit import io_tools; io_tools.get_fitresult(sys.argv[1], meta=True)" \
        "$1" >/dev/null 2>&1
}

runrabbit() {  # <tensor> <outname> <toys> <parammodel> <extra...>
    local T=$1 N=$2 TOY=$3 PM=$4; shift 4
    if fitdone ${OUT}/rabbit/${N}.hdf5; then
        echo "  ${N} already done, reusing it"
        return 0
    fi
    # LEAN=1 drops impacts/hists (much faster); POIs+scans still written, which
    # is all the comparison table and PL intervals need.
    local EXTRA_OUT="--doImpacts --globalImpacts --saveHists --saveHistsPerProcess --computeHistErrors"
    [ "${LEAN:-0}" = "1" ] && EXTRA_OUT=""
    rabbit_fit.py ${T} -o ${OUT}/rabbit --outname ${N} -t ${TOY} ${PM} "$@" ${EXTRA_OUT}
}

slot; runrabbit ${OUT}/rabbit/cardSR.hdf5 A_SR  -1 "${PM_A}" --scan tt-vcb ${XSEC} --scanPoints ${SCANPOINTS} \
    > ${OUT}/rabbit/log_A_SR.log  2>&1 &
slot; runrabbit ${OUT}/rabbit/cardCR.hdf5 A_CR  -1 "${PM_A}" --freezeParameters 'tt-vcb' --scan ${XSEC} --scanPoints ${SCANPOINTS} \
    > ${OUT}/rabbit/log_A_CR.log  2>&1 &
slot; runrabbit ${OUT}/rabbit/cardCR.hdf5 A_CRo  0 "${PM_A}" --freezeParameters 'tt-vcb' --scan ${XSEC} --scanPoints ${SCANPOINTS} \
    > ${OUT}/rabbit/log_A_CRo.log 2>&1 &
slot; runrabbit ${OUT}/rabbit/ourSR.hdf5  B_SR  -1 "${PM_B}" --scan tt-vcb ${XSEC} --scanPoints ${SCANPOINTS} \
    > ${OUT}/rabbit/log_B_SR.log  2>&1 &
slot; runrabbit ${OUT}/rabbit/ourCR.hdf5  B_CR  -1 "${PM_B}" --freezeParameters 'tt-vcb' --scan ${XSEC} --scanPoints ${SCANPOINTS} \
    > ${OUT}/rabbit/log_B_CR.log  2>&1 &
slot; runrabbit ${OUT}/rabbit/ourCR.hdf5  B_CRo  0 "${PM_B}" --freezeParameters 'tt-vcb' --unblind 'xsec_.*' --scan ${XSEC} --scanPoints ${SCANPOINTS} \
    > ${OUT}/rabbit/log_B_CRo.log 2>&1 &

if [ "${WITH_D:-1}" = "1" ]; then
# D: isolation trials, fit like leg B (FreeNorm xsec POIs)
for T in "${!DTRIAL[@]}"; do
    slot; runrabbit ${OUT}/rabbit/D${T}SR.hdf5 D${T}_SR  -1 "${PM_B}" --scan tt-vcb ${XSEC} --scanPoints ${SCANPOINTS} \
        > ${OUT}/rabbit/log_D${T}_SR.log  2>&1 &
    slot; runrabbit ${OUT}/rabbit/D${T}CR.hdf5 D${T}_CR  -1 "${PM_B}" --freezeParameters 'tt-vcb' --scan ${XSEC} --scanPoints ${SCANPOINTS} \
        > ${OUT}/rabbit/log_D${T}_CR.log  2>&1 &
    slot; runrabbit ${OUT}/rabbit/D${T}CR.hdf5 D${T}_CRo  0 "${PM_B}" --freezeParameters 'tt-vcb' --unblind 'xsec_.*' --scan ${XSEC} --scanPoints ${SCANPOINTS} \
        > ${OUT}/rabbit/log_D${T}_CRo.log 2>&1 &
done
fi

# ------------------------------------------------------------ combine fits
echo "### combine fits (default Hesse and robustHesse)"
SR_BASE="-t -1 --expectSignal 1"
CR_BASE="-t -1 --setParameters r=1,${MASKSR} --freezeParameters r"
CRo_BASE="-t 0 --setParameters r=1,${MASKSR} --freezeParameters r"
SR_ARGS="${SR_BASE}"
CR_ARGS="${CR_BASE} --redefineSignalPOIs xsec_ttLF"
CRo_ARGS="${CRo_BASE} --redefineSignalPOIs xsec_ttLF"

for CFG in SR CR CRo; do
    case ${CFG} in
        SR)  A="${SR_ARGS}" ;;
        CR)  A="${CR_ARGS}" ;;
        CRo) A="${CRo_ARGS}" ;;
    esac
    for MODE in default robust; do
        RH=""; [ "${MODE}" = "robust" ] && RH="--robustHesse 1"
        [ -f ${OUT}/combine/multidimfit${CFG}_${MODE}.root ] && continue
        slot; ( cd ${OUT}/combine && \
            combine -M MultiDimFit -d ${WS} ${A} --algo none --saveFitResult ${RH} \
                --cminDefaultMinimizerStrategy 0 -n ${CFG}_${MODE} ) \
            > ${OUT}/combine/log_${CFG}_${MODE}.log 2>&1 &
    done
done

# ----------------------------------------------------------- combine scans
echo "### combine scans"
for CFG in SR CR CRo; do
    # the base args must NOT carry --redefineSignalPOIs: combine rejects it twice
    case ${CFG} in
        SR)  A="${SR_BASE}";  PARAMS="r ${XSEC}"; ALLPOI="r,${XSEC_CSV}" ;;
        CR)  A="${CR_BASE}";  PARAMS="${XSEC}";   ALLPOI="${XSEC_CSV}" ;;
        CRo) A="${CRo_BASE}"; PARAMS="${XSEC}";   ALLPOI="${XSEC_CSV}" ;;
    esac
    for P in ${PARAMS}; do
        [ -s ${OUT}/combine/higgsCombinescan_${CFG}_${P}.MultiDimFit.mH120.root ] && continue
        # --autoRange scans +-N sigma around the minimum; without it combine walks
        # the whole declared parameter range (r up to 20) and wastes every point
        slot; ( cd ${OUT}/combine && \
            combine -M MultiDimFit -d ${WS} ${A} --algo grid --points ${SCANPOINTS} \
                --redefineSignalPOIs ${ALLPOI} -P ${P} --floatOtherPOIs 1 --autoRange 3 \
                --cminDefaultMinimizerStrategy 0 -n scan_${CFG}_${P} ) \
            > ${OUT}/combine/log_scan_${CFG}_${P}.log 2>&1 &
    done
done

echo "### waiting (${JOBS}-way)"
wait || true
echo "### done -> ${OUT}"
