#!/bin/bash
# Combine vs rabbit on the four 250826 pre-unblinding models.
# Two configurations only: SR Asimov and CR observed.
#
#   cmsenv && source setup.sh && source setup_rabbit.sh
#   ./runPreUnblindingComparison.sh
#
# BLINDING: every SR configuration is Asimov (-t -1). The observed fits run with
# the signal region masked, so real SR data is never used.
#
# Rabbit runs on two legs, because the two answer different questions:
#   A  analysis/cardToTensor.py on each datacard. Same model combine sees, so a
#      difference is the minimiser or the Hessian and nothing else. Four models
#      in, four results out.
#   B  analysis/prepareTensor.py on the UNSMOOTHED orig shapes, our own pruning,
#      smoothing and symmetrisation. It reads no datacard, so it gives ONE
#      result for all four models. Feeding it the already-Lowess-smoothed
#      shapes would smooth twice, which is why it takes orig/ (as runRabbitFits.sh does).
#
# Leg A runs lean (parameters + scans, no impacts/hists): it only feeds the
# comparison table. Leg B runs full, it is the analysis answer.

set -e

OUT=${OUT:-Comparison_250826_preUnblinding}
JOBS=${JOBS:-16}
SCANPOINTS=${SCANPOINTS:-31}
NSIGMA=${NSIGMA:-4}     # combine scan half-width, in robustHesse sigma

BASE=$(cd "$(dirname "$0")" && pwd)
cd "${BASE}"

# a plain `combine` can resolve to the coreutils lookalike, so prefer the CMSSW one
COMBINE="${CMSSW_BASE}/bin/${SCRAM_ARCH}/combine"
[ -x "${COMBINE}" ] || COMBINE=combine

# tag : datacard directory (holds Vcb_SL_2024.txt + workspace_Vcb_SL_2024.root)
CARDS=(
    "smoothed:Datacards_250826_preUnblinding_simplified/datacards"
    "noFlavTagSymm:Datacards_250826_preUnblinding_noFlavTagSymm_simplified/datacards"
    "nonSmoothed:Datacards_250826_preUnblinding_nonSmoothed_simplified/datacards"
    "orig:Datacards_250826_preUnblinding/orig"
)
SHAPES=${SHAPES:-Datacards_250826_preUnblinding/orig/Vcb_SL_2024_shapes.root}
# leg B is compared against this card's combine result (same unsmoothed shapes)
LEGB_REF=orig

FREENORM="ttbb,ttbj,tt2b,ttcc,ttcj,tt2c,ttLF"
XSEC="xsec_ttbb xsec_ttbj xsec_tt2b xsec_ttcc xsec_ttcj xsec_tt2c xsec_ttLF"
XSEC_CSV=$(echo ${XSEC} | tr ' ' ',')
MASKSR="rgx{mask_.*_SR.*}=1"

PM_A="--paramModel Mu"
PM_B="--paramModel Mu --paramModel analysis.rabbit_models.FreeNorm ${FREENORM}"

mkdir -p ${OUT}/rabbit ${OUT}/combine ${OUT}/compare

# `wait -n` returns the finished job's status, which under `set -e` would kill
# the script on a single failed fit; swallow it and check the outputs instead.
slot() { while [ "$(jobs -rp | wc -l)" -ge "${JOBS}" ]; do wait -n || true; done; }

# ------------------------------------------------------------------ tensors
# The rabbit venv must really be on the path. `cmsenv` after `source
# setup_rabbit.sh` resets PYTHONPATH while leaving RABBIT_ACTIVE set, so
# setup_rabbit.sh returns early and every rabbit job dies on `import wums`.
python3 -c "import wums, rabbit" 2>/dev/null || {
    echo "ERROR: rabbit venv not importable. Run cmsenv FIRST, then source setup_rabbit.sh" >&2
    echo "       (if RABBIT_ACTIVE is set but the path is stale: unset RABBIT_ACTIVE and re-source)" >&2
    exit 1
}

echo "### tensors (JOBS=${JOBS})"
for ENTRY in "${CARDS[@]}"; do
    IFS=: read -r TAG DIR <<< "${ENTRY}"
    CARD=${BASE}/${DIR}/Vcb_SL_2024.txt
    [ -f ${OUT}/rabbit/${TAG}_cardSR.hdf5 ] || { slot; python3 analysis/cardToTensor.py ${CARD} \
        -o ${OUT}/rabbit --outname ${TAG}_cardSR \
        > ${OUT}/rabbit/log_tensor_${TAG}_cardSR.log 2>&1 & }
    [ -f ${OUT}/rabbit/${TAG}_cardCR.hdf5 ] || { slot; python3 analysis/cardToTensor.py ${CARD} \
        -o ${OUT}/rabbit --outname ${TAG}_cardCR --mask '_SR$' \
        > ${OUT}/rabbit/log_tensor_${TAG}_cardCR.log 2>&1 & }
done
# prepareTensor.py now defaults to lowess smoothing + flavTag mirror-up OFF
# (this session's noFTS variant). ourSR/ourCR reproduce the OLD default
# (mirror-up ON) by passing --flavtag-mirror explicitly; ourSRnoFTS/ourCRnoFTS
# need no flags at all, they ARE the new default.
[ -f ${OUT}/rabbit/ourSR.hdf5 ] || { slot; python3 analysis/prepareTensor.py ${SHAPES} \
    -o ${OUT}/rabbit --outname ourSR --flavtag-mirror \
    > ${OUT}/rabbit/log_tensor_ourSR.log 2>&1 & }
[ -f ${OUT}/rabbit/ourCR.hdf5 ] || { slot; python3 analysis/prepareTensor.py ${SHAPES} \
    -o ${OUT}/rabbit --outname ourCR --flavtag-mirror --mask '_SR$' \
    > ${OUT}/rabbit/log_tensor_ourCR.log 2>&1 & }
[ -f ${OUT}/rabbit/ourSRnoFTS.hdf5 ] || { slot; python3 analysis/prepareTensor.py ${SHAPES} \
    -o ${OUT}/rabbit --outname ourSRnoFTS \
    > ${OUT}/rabbit/log_tensor_ourSRnoFTS.log 2>&1 & }
[ -f ${OUT}/rabbit/ourCRnoFTS.hdf5 ] || { slot; python3 analysis/prepareTensor.py ${SHAPES} \
    -o ${OUT}/rabbit --outname ourCRnoFTS --mask '_SR$' \
    > ${OUT}/rabbit/log_tensor_ourCRnoFTS.log 2>&1 & }
echo "### waiting for tensors"
wait || true

MISSING=0
for ENTRY in "${CARDS[@]}"; do
    IFS=: read -r TAG DIR <<< "${ENTRY}"
    for C in cardSR cardCR; do
        [ -f ${OUT}/rabbit/${TAG}_${C}.hdf5 ] || { echo "ERROR: no tensor ${TAG}_${C}, see ${OUT}/rabbit/log_tensor_${TAG}_${C}.log" >&2; MISSING=1; }
    done
done
for C in ourSR ourCR; do
    [ -f ${OUT}/rabbit/${C}.hdf5 ] || { echo "ERROR: no tensor ${C}, see ${OUT}/rabbit/log_tensor_${C}.log" >&2; MISSING=1; }
done
[ "${MISSING}" = "0" ] || { echo "aborting: tensors failed, fitting them would be pointless" >&2; exit 1; }

# --------------------------------------------------------------- rabbit fits
# rabbit creates its output file at the start and fills it at the end, so
# "the file exists" proves nothing; check that it actually reads back.
fitdone() {
    python3 -c "import sys; from rabbit import io_tools; io_tools.get_fitresult(sys.argv[1], meta=True)" \
        "$1" >/dev/null 2>&1
}
runrabbit() {  # <tensor> <outname> <toys> <parammodel> <extra...>
    local T=$1 N=$2 TOY=$3 PM=$4; shift 4
    fitdone ${OUT}/rabbit/${N}.hdf5 && { echo "  ${N} already done, reusing it"; return 0; }
    rabbit_fit.py ${T} -o ${OUT}/rabbit --outname ${N} -t ${TOY} ${PM} "$@"
}

echo "### rabbit fits"
for ENTRY in "${CARDS[@]}"; do
    IFS=: read -r TAG DIR <<< "${ENTRY}"
    slot; runrabbit ${OUT}/rabbit/${TAG}_cardSR.hdf5 ${TAG}_A_SR -1 "${PM_A}" \
        --scan tt-vcb ${XSEC} --scanPoints ${SCANPOINTS} \
        > ${OUT}/rabbit/log_${TAG}_A_SR.log 2>&1 &
    slot; runrabbit ${OUT}/rabbit/${TAG}_cardCR.hdf5 ${TAG}_A_CRo 0 "${PM_A}" \
        --freezeParameters 'tt-vcb' --scan ${XSEC} --scanPoints ${SCANPOINTS} \
        > ${OUT}/rabbit/log_${TAG}_A_CRo.log 2>&1 &
done
# Lean: only the fitted value and its uncertainty are wanted for the
# comparison table, so no scans, impacts or histograms here either -- those
# cost hours and move neither (see the noFTS fits below for the same call).
slot; runrabbit ${OUT}/rabbit/ourSR.hdf5 B_SR -1 "${PM_B}" \
    > ${OUT}/rabbit/log_B_SR.log 2>&1 &
# -t 0 blinds every POI, so xsec_* must be unblinded explicitly; tt-vcb stays blinded
slot; runrabbit ${OUT}/rabbit/ourCR.hdf5 B_CRo 0 "${PM_B}" \
    --freezeParameters 'tt-vcb' --unblind 'xsec_.*' \
    > ${OUT}/rabbit/log_B_CRo.log 2>&1 &

# flavTag mirror-up off. Only the fitted value and its uncertainty are wanted
# here, so no scans, impacts or histograms: those cost hours and move neither.
slot; runrabbit ${OUT}/rabbit/ourSRnoFTS.hdf5 B_SR_noFTS -1 "${PM_B}" \
    > ${OUT}/rabbit/log_B_SR_noFTS.log 2>&1 &
slot; runrabbit ${OUT}/rabbit/ourCRnoFTS.hdf5 B_CRo_noFTS 0 "${PM_B}" \
    --freezeParameters 'tt-vcb' --unblind 'xsec_.*' \
    > ${OUT}/rabbit/log_B_CRo_noFTS.log 2>&1 &

# -------------------------------------------------------------- combine fits
# --robustHesse 1 is mandatory wherever the errors are used: the default Minuit
# Hessian is measured unreliable on this model (COMBINE_FIXES.md).
echo "### combine fits and scans"
SR_BASE="-t -1 --expectSignal 1"
CRo_BASE="-t 0 --setParameters r=1,${MASKSR} --freezeParameters r"

# Minimiser settings for the grid scans, the same recipe run_likelihoodScan.sh
# uses. They are NOT optional here. RandStartPt.cc:175 commits a scan point only
# `if (ok)`, so a profiled fit that fails to converge is dropped from the output
# tree with no error message at all. With a bare
# `--cminDefaultMinimizerStrategy 0` the smoothed card lost every point above
# r = 1 (15 of 31 written, twice, reproducibly), which left the scan with no
# upper 68% bound. Measured on that card: bare 1/6 points committed above r=1,
# this recipe 6/6, and it is also faster per point.
#
# --X-rtd FAST_VERTICAL_MORPH is deliberately NOT taken from run_likelihoodScan.sh:
# it approximates the vertical template morphing, which would confound a
# numerical Combine-vs-rabbit comparison. Keep the exact morphing here.
SCANMIN="--cminDefaultMinimizerStrategy 0 --cminDefaultMinimizerTolerance 0.1 \
    --X-rtd MINIMIZER_MaxCalls=999999999 --cminPreScan --cminPreFit 1 --robustFit 1"

for ENTRY in "${CARDS[@]}"; do
    IFS=: read -r TAG DIR <<< "${ENTRY}"
    WS=${BASE}/${DIR}/workspace_Vcb_SL_2024.root
    for CFG in SR CRo; do
        case ${CFG} in
            SR)  A="${SR_BASE}";  RD="" ;;
            CRo) A="${CRo_BASE}"; RD="--redefineSignalPOIs xsec_ttLF" ;;
        esac
        # value + error, both for the comparison table and for the scan ranges
        [ -f ${OUT}/combine/multidimfit${TAG}_${CFG}.root ] || { slot; ( cd ${OUT}/combine && \
            ${COMBINE} -M MultiDimFit -d ${WS} ${A} ${RD} --algo none --saveFitResult --robustHesse 1 \
                --cminDefaultMinimizerStrategy 0 -n ${TAG}_${CFG} ) \
            > ${OUT}/combine/log_fit_${TAG}_${CFG}.log 2>&1 & }
    done
done
echo "### waiting for the --algo none fits, they set the scan ranges"
wait || true

# An interrupted combine leaves a perfectly readable file holding half a grid,
# so "the file exists" is not enough: require the points to actually be there.
scandone() {  # <file> <npoints>
    python3 - "$1" "$2" <<'PY' >/dev/null 2>&1
import sys

import numpy as np
import uproot

d = uproot.open(sys.argv[1])["limit"]["deltaNLL"].array(library="np")
sys.exit(0 if np.isfinite(np.asarray(d, dtype=float)).sum() >= int(sys.argv[2]) else 1)
PY
}

# NOT --autoRange: it takes its width from combine's default Hessian, which is
# unreliable on this model (COMBINE_FIXES.md). Measured on these cards it gave
# windows up to 26x too narrow (orig/SR/xsec_ttLF: width 0.0197 where 3 sigma is
# 0.522), so the grid never reached 2*deltaNLL = 1 and had no interval on it.
# analysis/scanRanges.py builds the window from the robustHesse errors instead.
# Two passes, so the headline parameter of every model is finished first and the
# summary table can be read long before the supplementary scans land.
# Off by default. Each grid point is a full profiled fit over 310-402 shape
# nuisances, so one 31-point scan costs 35 min to 3 h per parameter and the full
# 8+7 POI matrix runs ~4 h. The robustHesse MultiDimFit above already gives the
# value and uncertainty this comparison needs. SCANS=1 to run them anyway.
echo "### combine scans (+-${NSIGMA} robustHesse sigma, ${SCANPOINTS} points)"
for PASS in $([ "${SCANS:-0}" = "1" ] && echo headline rest); do
  echo "###   pass: ${PASS}"
  for ENTRY in "${CARDS[@]}"; do
    IFS=: read -r TAG DIR <<< "${ENTRY}"
    WS=${BASE}/${DIR}/workspace_Vcb_SL_2024.root
    for CFG in SR CRo; do
        case ${CFG} in
            SR)  A="${SR_BASE}";  HEAD="r";         PARAMS="r ${XSEC}"; ALLPOI="r,${XSEC_CSV}" ;;
            CRo) A="${CRo_BASE}"; HEAD="xsec_ttLF"; PARAMS="${XSEC}";   ALLPOI="${XSEC_CSV}" ;;
        esac
        RANGES=${OUT}/combine/ranges_${TAG}_${CFG}.txt
        [ -s ${RANGES} ] || python3 analysis/scanRanges.py \
            ${OUT}/combine/multidimfit${TAG}_${CFG}.root --nsigma ${NSIGMA} > ${RANGES}
        for P in ${PARAMS}; do
            [ "${PASS}" = "headline" ] && [ "${P}" != "${HEAD}" ] && continue
            [ "${PASS}" = "rest" ]     && [ "${P}" = "${HEAD}" ]  && continue
            F=${OUT}/combine/higgsCombine${TAG}_${CFG}_${P}.MultiDimFit.mH120.root
            [ -f ${F} ] && scandone ${F} ${SCANPOINTS} && continue
            RNG=$(awk -v p=${P} '$1==p{printf "--setParameterRange %s=%s,%s",p,$2,$3}' ${RANGES})
            [ -n "${RNG}" ] || { echo "  no range for ${TAG} ${CFG} ${P}, skipped" >&2; continue; }
            rm -f ${F}
            slot; ( cd ${OUT}/combine && \
                ${COMBINE} -M MultiDimFit -d ${WS} ${A} --algo grid --points ${SCANPOINTS} \
                    --redefineSignalPOIs ${ALLPOI} -P ${P} --floatOtherPOIs 1 ${RNG} \
                    ${SCANMIN} -n ${TAG}_${CFG}_${P} ) \
                > ${OUT}/combine/log_scan_${TAG}_${CFG}_${P}.log 2>&1 &
        done
    done
  done
done

echo "### waiting for scans (${JOBS}-way)"
wait || true

# ------------------------------------------------------------------ compare
echo "### parameter comparison"
for ENTRY in "${CARDS[@]}"; do
    IFS=: read -r TAG DIR <<< "${ENTRY}"
    for CFG in SR CRo; do
        python3 analysis/compareCombine.py \
            ${OUT}/combine/multidimfit${TAG}_${CFG}.root ${OUT}/rabbit/${TAG}_A_${CFG}.hdf5 \
            -o ${OUT}/compare/${TAG}_${CFG}_legA.csv > ${OUT}/compare/${TAG}_${CFG}_legA.txt 2>&1 \
            || echo "  (compare failed for ${TAG} ${CFG})"
    done
done
for CFG in SR CRo; do
    python3 analysis/compareCombine.py \
        ${OUT}/combine/multidimfit${LEGB_REF}_${CFG}.root ${OUT}/rabbit/B_${CFG}.hdf5 \
        -o ${OUT}/compare/${LEGB_REF}_${CFG}_legB.csv > ${OUT}/compare/${LEGB_REF}_${CFG}_legB.txt 2>&1 \
        || echo "  (compare failed for legB ${CFG})"
done

echo "### summary"
python3 analysis/preUnblindingSummary.py ${OUT} | tee ${OUT}/summary.txt

echo "### done -> ${OUT}"
