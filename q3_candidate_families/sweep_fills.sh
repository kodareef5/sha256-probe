#!/bin/bash
# sweep_fills.sh — Run MITM scanner across multiple fill patterns
#
# Usage: ./sweep_fills.sh [n_threads_per_fill] [n_mc]
#
# Tests these fill patterns for M[1..15]:
#   - 0xffffffff (all-ones, published candidate family)
#   - 0x00000000 (all-zeros)
#   - 0xaaaaaaaa (alternating bits)
#   - 0x55555555 (alternating bits inverted)
#   - 0x80000000 (MSB only)
#   - 0x7fffffff (all except MSB)
#   - 0x0f0f0f0f (nibble pattern)
#   - 0xf0f0f0f0 (nibble pattern inverted)
#
# Each fill gets its own set of threads. With 24 cores and 8 fills,
# that's 3 threads per fill — takes ~20 min per fill at 3 threads.
# Alternatively run 2 at a time with 12 threads each.

set -e

THREADS=${1:-3}
MC=${2:-5000}
SCANNER="./mitm_scanner"
OUTDIR="q3_candidate_families/results/$(date +%Y%m%d_%H%M)_sweep"
mkdir -p "$OUTDIR"

FILLS=(
    0xffffffff
    0x00000000
    0xaaaaaaaa
    0x55555555
    0x80000000
    0x7fffffff
    0x0f0f0f0f
    0xf0f0f0f0
)

echo "MITM Fill Sweep: ${#FILLS[@]} fills, $THREADS threads/fill, $MC MC samples"
echo "Output: $OUTDIR"
echo ""

PIDS=()
for fill in "${FILLS[@]}"; do
    fname=$(printf "fill_%08x" $fill)
    echo "Launching: $fill ($THREADS threads)"
    OMP_NUM_THREADS=$THREADS $SCANNER $fill $MC \
        > "$OUTDIR/${fname}.csv" \
        2> "$OUTDIR/${fname}.log" &
    PIDS+=($!)
done

echo ""
echo "All ${#FILLS[@]} scans launched. PIDs: ${PIDS[*]}"
echo "Waiting for completion..."

for pid in "${PIDS[@]}"; do
    wait $pid
    echo "  PID $pid done (exit $?)"
done

echo ""
echo "=== AGGREGATE RESULTS ==="
echo ""

# Merge all CSVs (skip header line from all but first)
head -1 "$OUTDIR/fill_ffffffff.csv" > "$OUTDIR/all_candidates.csv"
for f in "$OUTDIR"/fill_*.csv; do
    tail -n +2 "$f" >> "$OUTDIR/all_candidates.csv"
done

TOTAL=$(( $(wc -l < "$OUTDIR/all_candidates.csv") - 1 ))
echo "Total candidates across all fills: $TOTAL"

# Sort by combined g60+h60 HW (column 8 = min_gh60)
echo ""
echo "Top candidates by MITM residue (min g60+h60 HW):"
head -1 "$OUTDIR/all_candidates.csv"
tail -n +2 "$OUTDIR/all_candidates.csv" | sort -t, -k8 -n | head -20

echo ""
echo "Top candidates by dW[61] constant HW:"
head -1 "$OUTDIR/all_candidates.csv"
tail -n +2 "$OUTDIR/all_candidates.csv" | sort -t, -k4 -n | head -20

echo ""
echo "Results saved to: $OUTDIR/all_candidates.csv"
