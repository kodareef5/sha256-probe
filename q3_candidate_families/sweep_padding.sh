#!/bin/bash
# sweep_padding.sh — Explore M[14]/M[15] padding freedom
#
# Tests a grid of M[14] x M[15] values with base_fill=0xffffffff.
# Each combination gets a full 2^32 M[0] scan.
#
# Usage: ./sweep_padding.sh [threads_per_scan]

set -e

THREADS=${1:-4}
SCANNER="./padding_scanner"
OUTDIR="q3_candidate_families/results/$(date +%Y%m%d_%H%M)_padding"
mkdir -p "$OUTDIR"

# Key M[14] values to test (M[15] varied similarly)
# These are chosen to cover different bit patterns that affect
# the schedule words W[29..56] which determine round-56 state
VALS=(0x00000000 0x80000000 0x00000001 0x12345678 0xdeadbeef 0x01010101)

echo "Padding Freedom Sweep"
echo "Base fill: 0xffffffff, varying M[14] and M[15]"
echo "Grid: ${#VALS[@]} x ${#VALS[@]} = $(( ${#VALS[@]} * ${#VALS[@]} )) combinations"
echo "Threads per scan: $THREADS"
echo "Output: $OUTDIR"
echo ""

PIDS=()
for m14 in "${VALS[@]}"; do
    for m15 in "${VALS[@]}"; do
        fname=$(printf "m14_%08x_m15_%08x" $m14 $m15)
        echo "Launching: m14=$m14 m15=$m15"
        OMP_NUM_THREADS=$THREADS $SCANNER 0xffffffff $m14 $m15 1000 \
            > "$OUTDIR/${fname}.csv" \
            2> "$OUTDIR/${fname}.log" &
        PIDS+=($!)
    done
done

echo ""
echo "Launched ${#PIDS[@]} scans. Waiting..."

for pid in "${PIDS[@]}"; do
    wait $pid 2>/dev/null
done

echo ""
echo "=== ALL SCANS COMPLETE ==="

# Merge results
head -1 "$OUTDIR"/m14_00000000_m15_00000000.csv > "$OUTDIR/all_padding.csv"
for f in "$OUTDIR"/m14_*.csv; do
    tail -n +2 "$f" >> "$OUTDIR/all_padding.csv"
done

TOTAL=$(( $(wc -l < "$OUTDIR/all_padding.csv") - 1 ))
echo "Total candidates: $TOTAL"
echo ""

if [ "$TOTAL" -gt 0 ]; then
    echo "Top by dW[61] constant HW:"
    head -1 "$OUTDIR/all_padding.csv"
    tail -n +2 "$OUTDIR/all_padding.csv" | sort -t, -k6 -n | head -20
    echo ""
    echo "Top by boomerang gap:"
    head -1 "$OUTDIR/all_padding.csv"
    tail -n +2 "$OUTDIR/all_padding.csv" | sort -t, -k7 -n | head -20
fi

echo ""
echo "Results: $OUTDIR/all_padding.csv"
