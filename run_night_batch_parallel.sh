#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

STAMP="$(date +%Y%m%d_%H%M%S)"
OUT_DIR="$ROOT_DIR/overnight_parallel_${STAMP}"
mkdir -p "$OUT_DIR"

MAX_JOBS=${MAX_JOBS:-6}

log() {
  echo "[$(date +%H:%M:%S)] $*" | tee -a "$OUT_DIR/run.log"
}

wait_for_slot() {
  while [ "$(jobs -pr | wc -l | tr -d ' ')" -ge "$MAX_JOBS" ]; do
    sleep 5
  done
}

run_job() {
  local name="$1"; shift
  wait_for_slot
  log "START $name"
  ( "$@" | tee -a "$OUT_DIR/${name}.log"; log "END $name" ) &
}

log "Using MAX_JOBS=$MAX_JOBS"

# Step 1: Long runs on partitions 2 and 3 (dual 4-bit), parallel
run_job "step1_p2" python3 sha256_scripts/76_partition_verifier.py \
  --dual --partitions=2 --out="$OUT_DIR/step1_p2.csv" 4 14400 1 0
run_job "step1_p3" python3 sha256_scripts/76_partition_verifier.py \
  --dual --partitions=3 --out="$OUT_DIR/step1_p3.csv" 4 14400 1 0

# Step 2: Random subset of 5-bit dual partitions (32 samples), parallel
PARTS=$(python3 - <<'PY'
import random
rng = random.Random(0x5A5A)
parts = rng.sample(range(1024), 32)
print(','.join(str(p) for p in parts))
PY
)
IFS=',' read -r -a PART_ARR <<< "$PARTS"
idx=0
for p in "${PART_ARR[@]}"; do
  run_job "step2_p${p}" python3 sha256_scripts/76_partition_verifier.py \
    --dual --partitions="$p" --out="$OUT_DIR/step2_p${p}.csv" 5 1800 1 0
  idx=$((idx+1))
  if [ "$idx" -ge 32 ]; then
    break
  fi
done

# Step 3: Seeded reruns on partitions 2 and 3 (parallel)
for SEED in 1 2 3 4 5; do
  run_job "step3_seed${SEED}_p2" python3 sha256_scripts/76_partition_verifier.py \
    --dual --seed="$SEED" --partitions=2 --out="$OUT_DIR/step3_seed_${SEED}_p2.csv" 4 3600 1 0
  run_job "step3_seed${SEED}_p3" python3 sha256_scripts/76_partition_verifier.py \
    --dual --seed="$SEED" --partitions=3 --out="$OUT_DIR/step3_seed_${SEED}_p3.csv" 4 3600 1 0
 done

log "Waiting for all jobs to complete..."
wait
log "Overnight parallel batch complete. Results in $OUT_DIR"
