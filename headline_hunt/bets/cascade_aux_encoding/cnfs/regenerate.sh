#!/bin/bash
# Regenerate the 36-CNF cross-kernel cascade_aux test set, with varmap sidecars.
#
# Output (per kernel × {sr=60,sr=61} × {expose,force}):
#   aux_{mode}_sr{sr}_n32_bit{B}_m{M}_fill{F}.cnf              — DIMACS CNF
#   aux_{mode}_sr{sr}_n32_bit{B}_m{M}_fill{F}.cnf.varmap.json  — SAT-var → diff-bit map
#
# Total: 9 × 2 × 2 = 36 CNFs + 36 varmap sidecars (~33 MB CNFs, ~500 KB varmaps).
# Runtime: ~3 minutes on macbook.
#
# Each CNF audit-CONFIRMs via headline_hunt/infra/audit_cnf.py.
# The varmap is consumed by bets/programmatic_sat_propagator/propagators/varmap_loader.py.
#
# Usage:
#   cd headline_hunt/bets/cascade_aux_encoding/cnfs
#   bash regenerate.sh
#
# CNFs and varmaps are gitignored — they're reproducible artifacts.

set -e

cd "$(dirname "$0")"
HERE=$(pwd)
ENCODER="../../../../headline_hunt/bets/cascade_aux_encoding/encoders/cascade_aux_encoder.py"

declare -a candidates=(
  "31 0x17149975 0xffffffff"   # MSB priority
  "0  0x8299b36f 0x80000000"   # LSB
  "6  0x024723f3 0x7fffffff"
  "10 0x3304caa0 0x80000000"   # sigma1-aligned
  "11 0x45b0a5f6 0x00000000"
  "13 0x4d9f691c 0x55555555"
  "17 0x427c281d 0x80000000"
  "19 0x51ca0b34 0x55555555"
  "25 0x09990bd2 0x80000000"
)

count=0
for entry in "${candidates[@]}"; do
  read -r bit m0 fill <<< "$entry"
  m0_short=${m0#0x}
  fill_short=${fill#0x}
  for sr in 60 61; do
    for mode in expose force; do
      out="aux_${mode}_sr${sr}_n32_bit${bit}_m${m0_short}_fill${fill_short}.cnf"
      python3 "$ENCODER" --sr "$sr" --m0 "$m0" --fill "$fill" \
                          --kernel-bit "$bit" --mode "$mode" --out "$out" \
                          --varmap + --quiet
      count=$((count + 1))
    done
  done
done

echo "Generated $count CNFs in $(pwd)"
echo "Verifying audit..."

audit_pass=0
audit_fail=0
for f in aux_*_sr*_n32_*.cnf; do
  if python3 ../../../../headline_hunt/infra/audit_cnf.py "$f" 2>&1 | grep -q "VERDICT: CONFIRMED"; then
    audit_pass=$((audit_pass + 1))
  else
    audit_fail=$((audit_fail + 1))
    echo "  FAIL: $f"
  fi
done
echo "Audit: $audit_pass CONFIRMED, $audit_fail not-confirmed"
