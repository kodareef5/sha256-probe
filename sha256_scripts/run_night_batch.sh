#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

STAMP="$(date +%Y%m%d_%H%M%S)"
OUT_DIR="$ROOT_DIR/overnight_${STAMP}"
mkdir -p "$OUT_DIR"

log() {
  echo "[$(date +%H:%M:%S)] $*" | tee -a "$OUT_DIR/run.log"
}

log "Step 1: Long runs on partitions 2 and 3 (dual 4-bit), serial." 
python3 sha256_scripts/76_partition_verifier.py \
  --dual \
  --partitions=2 \
  --out="$OUT_DIR/step1_p2.csv" \
  4 14400 1 0 \
  | tee -a "$OUT_DIR/step1_p2.log"

log "Step 1b: Long run on partition 3 (dual 4-bit), serial." 
python3 sha256_scripts/76_partition_verifier.py \
  --dual \
  --partitions=3 \
  --out="$OUT_DIR/step1_p3.csv" \
  4 14400 1 0 \
  | tee -a "$OUT_DIR/step1_p3.log"

log "Step 2: Random subset of 5-bit dual partitions (32 samples), serial." 
PARTS=$(python3 - <<'PY'
import random
rng = random.Random(0x5A5A)
parts = rng.sample(range(1024), 32)
print(','.join(str(p) for p in parts))
PY
)
python3 sha256_scripts/76_partition_verifier.py \
  --dual \
  --partitions="$PARTS" \
  --out="$OUT_DIR/step2_random_5bit.csv" \
  5 1800 1 0 \
  | tee -a "$OUT_DIR/step2.log"

log "Step 3: Seeded reruns on partitions 2 and 3 (serial)."
for SEED in 1 2 3 4 5; do
  log "Seed $SEED"
  python3 sha256_scripts/76_partition_verifier.py \
    --dual \
    --seed="$SEED" \
    --partitions=2 \
    --out="$OUT_DIR/step3_seed_${SEED}_p2.csv" \
    4 3600 1 0 \
    | tee -a "$OUT_DIR/step3_seed_${SEED}_p2.log"
  python3 sha256_scripts/76_partition_verifier.py \
    --dual \
    --seed="$SEED" \
    --partitions=3 \
    --out="$OUT_DIR/step3_seed_${SEED}_p3.csv" \
    4 3600 1 0 \
    | tee -a "$OUT_DIR/step3_seed_${SEED}_p3.log"
done

log "Overnight batch complete. Results in $OUT_DIR"
