#!/usr/bin/env bash
# setup_sat_cas.sh — reproducibly build the SOTA SAT+CAS engine (arXiv 2406.20072)
# and the Nejati collision encoder in this environment, and validate end-to-end.
#
# This imports the standard-metric (step-reduced collision) tooling the repo lacked.
# Rationale: Tier 0 (reports/20260609_metric_bridge_lattice.md +
# 20260609_structural_transfer_verdict.md) showed the repo's sr-metric is orthogonal to
# the field's standard metric and does not transfer; all remaining EV is on the standard
# (R-axis) collision problem, whose record-setting engine is SAT+CAS.
#
# Both upstreams are MIT-licensed. Validated 2026-06-09 on macOS (Apple clang).
set -euo pipefail
WORK=${1:-/tmp}
cd "$WORK"

# 1. SAT+CAS solver: CaDiCaL 1.8.0 fork with embedded SHA-256 CAS routines.
[ -d cadical-sha256 ] || git clone --depth 1 https://github.com/nahiyan/cadical-sha256.git
cd cadical-sha256
# Select the 1-bit Nejati encoding (the fully-implemented path; 4-bit is incomplete
# upstream) and turn on the CAS techniques.
sed -i.bak \
  -e 's/#define IS_1BIT false/#define IS_1BIT true/' \
  -e 's/#define CUSTOM_PROP false/#define CUSTOM_PROP true/' \
  -e 's/#define WORDWISE_PROPAGATE false/#define WORDWISE_PROPAGATE true/' \
  -e 's/#define MENDEL_BRANCHING false/#define MENDEL_BRANCHING true/' \
  src/sha256/types.hpp
# BUGFIX (upstream master, 2026-06-09): sha256.cpp calls mendel_branch_1bit() but never
# includes its header -> "undeclared identifier" build error. Add the missing include.
grep -q '1_bit/mendel_branch.hpp' src/sha256/sha256.cpp || \
  perl -0pi -e 's{(#include "1_bit/wordwise_propagate.hpp"\n)}{$1#include "1_bit/mendel_branch.hpp"\n}' \
  src/sha256/sha256.cpp
cmake -Bbuild . >/dev/null && cmake --build build -j4 >/dev/null
echo "[ok] CAS solver: $WORK/cadical-sha256/build/cadical"

# 2. Nejati collision encoder (generates the differential CNFs the CAS solver expects).
cd "$WORK"
[ -d cryptanalysis ] || git clone --depth 1 https://github.com/nahiyan/cryptanalysis.git
cd cryptanalysis/encoders/nejati-collision
make >/dev/null
echo "[ok] encoder: $(pwd)/encoder   (bundled characteristics in tables/)"

# 3. Validate end-to-end (a 28-step collision; CAS should beat plain CDCL on conflicts).
CNF=/tmp/_validate28.cnf
./encoder -r 28 --diff_desc -d tables/28_nahiyan.txt > "$CNF" 2>/dev/null
echo "[validate] 28-step CNF: $(grep -m1 '^p cnf' "$CNF")"
echo "[validate] CAS engine : $("$WORK"/cadical-sha256/build/cadical "$CNF" 2>&1 | grep -m1 -iE '^s ' ) ($("$WORK"/cadical-sha256/build/cadical "$CNF" 2>&1 | grep -iE '^c conflicts:' | awk '{print $3}') conflicts)"
# Usage to push toward the frontier:
#   ./encoder -r 38 --diff_desc -d tables/38_mendel.txt > sha38.cnf
#   $WORK/cadical-sha256/build/cadical -t 1200 sha38.cnf
