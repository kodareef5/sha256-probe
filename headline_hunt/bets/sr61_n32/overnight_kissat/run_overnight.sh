#!/bin/bash
# run_overnight.sh — orchestrate overnight kissat sweep.
#
# Steps:
#   1. Build queue (Phase A + B + C) from registry + cnfs_n32.
#   2. Audit all referenced CNFs upfront (fail-fast on MISMATCH).
#   3. Launch dispatcher with N workers + per-job time cap.
#   4. (Morning) Run log_results.py to append all completed runs to runs.jsonl.
#   5. Refresh dashboard.
#
# Usage: bash run_overnight.sh [num_workers] [time_cap_sec]
#   num_workers default 6 (M5 has ~10 cores; leave 4 for system + this orchestrator)
#   time_cap_sec default 1800 (30 min per run)
#
# Run this with `nohup bash run_overnight.sh > overnight.log 2>&1 &` to
# detach from terminal.

set -e
cd "$(dirname "$0")"

NUM_WORKERS=${1:-6}
TIME_CAP_SEC=${2:-1800}

echo "=== overnight_kissat sweep ==="
echo "  workers:    $NUM_WORKERS"
echo "  time_cap:   ${TIME_CAP_SEC}s per job"
echo "  start:      $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo

# 1. Build queue
echo "[1/4] Building queue..."
python3 build_queue.py --phase all --out work_queue.tsv
JOB_COUNT=$(grep -c "^PENDING" work_queue.tsv)
echo "  $JOB_COUNT jobs queued"

# 2. Audit all referenced CNFs
echo "[2/4] Auditing CNFs..."
AUDIT_FAIL=0
while IFS=$'\t' read -r status cnf seed conflicts tag; do
    [ "$status" = "PENDING" ] || continue
    [ -z "$cnf" ] && continue
    verdict=$(python3 ../../../infra/audit_cnf.py "$cnf" 2>&1 | grep "VERDICT:" | awk '{print $NF}')
    if [ "$verdict" != "CONFIRMED" ]; then
        echo "  AUDIT FAIL: $cnf ($verdict)"
        AUDIT_FAIL=1
    fi
done < work_queue.tsv

if [ $AUDIT_FAIL -eq 1 ]; then
    echo "  STOP: audit failures present. Review and fix before proceeding."
    exit 1
fi
echo "  All audits CONFIRMED."

# 3. Launch dispatcher
echo "[3/4] Launching dispatcher (PID will be parent of workers)..."
mkdir -p logs
echo "" > results.tsv

./dispatcher work_queue.tsv "$NUM_WORKERS" --time-cap-sec "$TIME_CAP_SEC"

DONE=$(grep -c "^[^[:space:]#]" results.tsv 2>/dev/null || echo 0)
echo "[4/4] Dispatcher exited. Completed $DONE jobs."
echo "  end: $(date -u +%Y-%m-%dT%H:%M:%SZ)"

# 4. Log results into runs.jsonl
echo "[4/4] Logging results to runs.jsonl..."
python3 log_results.py --results results.tsv

# 5. Refresh dashboard
echo "[5/5] Refreshing dashboard..."
python3 ../../../infra/summarize_runs.py 2>&1 | tail -3

echo
echo "=== overnight_kissat sweep DONE ==="
