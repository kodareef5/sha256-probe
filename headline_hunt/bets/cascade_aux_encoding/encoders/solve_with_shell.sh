#!/bin/bash
# solve_with_shell.sh — pipeline: shell_eliminate.py | kissat
#
# Operationalizes F211's three-stage decoder design as a working demo:
#   Stage 1: shell_eliminate.py reduces CNF
#   Stage 2: kissat solves reduced CNF
#   Stage 3: report timings; (BP marginal stage TBD)
#
# Usage:
#   ./solve_with_shell.sh CNF_PATH [KISSAT_TIMEOUT]
#
# Demonstrates the speedup over running kissat directly on the
# original CNF (per F220: kissat default eliminates 19% vs
# shell_eliminate's 94%).

set -e

CNF="${1:?need CNF path}"
TIMEOUT="${2:-30}"

if [ ! -f "$CNF" ]; then
    echo "ERROR: $CNF not found" >&2
    exit 1
fi

REPO=/Users/mac/Desktop/sha256_review
PYTHONPATH="$REPO" python3 -c "" 2>/dev/null  # ensure python ok

REDUCED=$(mktemp /tmp/shell_eliminate.XXXXXX.cnf)
trap "rm -f $REDUCED $REDUCED.varmap.json $REDUCED.report.json" EXIT

echo "=== Stage 1: shell_eliminate ==="
START=$(python3 -c "import time; print(time.time())")
python3 "$REPO/headline_hunt/bets/cascade_aux_encoding/encoders/shell_eliminate.py" \
    "$CNF" "$REDUCED" --max-iter 10 2>&1 | grep -E "Final:|Total wall:" | head -5
T1=$(python3 -c "import time; print(time.time())")
DUR_S1=$(python3 -c "print(f'{$T1-$START:.3f}')")
echo "Stage 1 wall: ${DUR_S1}s"

echo ""
echo "=== Stage 2: kissat on reduced ==="
START2=$(python3 -c "import time; print(time.time())")
RESULT=$(kissat --time=$TIMEOUT --quiet "$REDUCED" 2>&1 | tail -3)
T2=$(python3 -c "import time; print(time.time())")
DUR_S2=$(python3 -c "print(f'{$T2-$START2:.3f}')")
echo "$RESULT"
echo "Stage 2 wall: ${DUR_S2}s"

echo ""
echo "=== Total ==="
TOTAL=$(python3 -c "print(f'{$T2-$START:.3f}')")
echo "Pipeline wall: ${TOTAL}s"
echo ""
echo "Comparison: running kissat directly on $CNF would have $TIMEOUT s budget."
echo "F220 found bare cascade_aux instances time-out at 60s with default kissat."
echo "Pipeline wall ${TOTAL}s vs direct >60s: see F220/F223 for benchmark detail."
