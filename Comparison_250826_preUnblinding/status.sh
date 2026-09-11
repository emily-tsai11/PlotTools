#!/bin/bash
# Progress of the pre-unblinding Combine scan matrix.
#   Comparison_250826_preUnblinding/status.sh
cd "$(dirname "$0")/combine" || exit 1

TOT=60
LAUNCHED=$(ls log_scan_*.log 2>/dev/null | wc -l)
RUNNING=$(pgrep -c -f 'combine -M MultiDimFit')

# a scan counts as done only when its process is gone AND the tree holds 31 points
DONE=0; PTS=0
for f in log_scan_*.log; do
    [ -e "$f" ] || continue
    n=$(grep -oE 'Point [0-9]+/31' "$f" | tail -1 | grep -oE '[0-9]+' | head -1)
    PTS=$((PTS + ${n:-0}))
    [ "${n:-0}" = "30" ] && DONE=$((DONE + 1))
done

START=$(stat -c %Y ../run.log 2>/dev/null)
NOW=$(date +%s)
EL=$(( (NOW - START) / 60 ))
RATE=$(awk -v p=$PTS -v e=$EL 'BEGIN{printf "%.1f", (e>0)?(p/e):0}')
REM=$(awk -v p=$PTS -v t=$((TOT*31)) -v r=$RATE 'BEGIN{printf "%.1f", (r>0)?((t-p)/r/60):-1}')
echo "======================================================================"
echo " elapsed ${EL} min | running ${RUNNING}/16 | launched ${LAUNCHED}/${TOT}"
echo " scans finished ${DONE}/${TOT} | grid points ${PTS}/$((TOT*31)) | ${RATE} pts/min"
echo " rough ETA for all 60: ~${REM} h"
echo "----------------------------------------------------------------------"
printf " %-15s %-4s %-11s %s\n" MODEL CFG PARAM PROGRESS
for t in smoothed noFlavTagSymm nonSmoothed orig; do
    for cp in SR:r CRo:xsec_ttLF; do
        c=${cp%%:*}; p=${cp##*:}
        s=$(grep -oE 'Point [0-9]+/31' log_scan_${t}_${c}_${p}.log 2>/dev/null | tail -1)
        [ "$s" = "Point 30/31" ] && s="done"
        printf " %-15s %-4s %-11s %s\n" "$t" "$c" "$p" "${s:-queued}"
    done
done
echo "----------------------------------------------------------------------"
echo " (headline scans above; the other 52 are supplementary xsec_* scans)"
echo "======================================================================"
