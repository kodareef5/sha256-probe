# Kill criteria — linear_lever_gaps

Scope reminder: this is a **fail-fast SAT probe**, not a campaign. The null
hypothesis is that linear levers confirm the wall. We chase SAT; we do not invest
in writing up the negative.

## #1 — Encoder untrusted (hard gate, blocks everything)

**Trigger**: `encoders/test_encoder.py` fails to reproduce the known paper sr=59
(`free={57..61}`, σ1 levers) and repo sr=60 (`free={57..60}`, σ1 levers) CNFs —
either var/clause counts diverge from the inlined reference builder, OR a solved
model fails independent oracle re-verification (`verify_lever_collision.py`:
state collision at r63 AND measured sr == claimed sr).

**Required evidence**: the test harness output. Until green, no new-config solve
counts — the `t-7`/`t-16` code paths are new and an off-by-one would make any
"SAT" meaningless.

## #2 — No lever advantage (primary kill)

**Trigger**: the linear-lever sr=60 instance (`free={54,55,56,57}`) shows neither
SAT nor a clear speed/conflict advantage over the σ1-cascade sr=60 baseline,
across seeds {1,5,7,11,13} × {kissat, cadical} within the fail-fast window
(tiered 300s → 1h per run).

**Required evidence**: ≥10 logged runs (`runs.jsonl`, audited CONFIRMED) all
TIMEOUT/UNKNOWN or no faster than baseline. Then KILL and pivot (candidate next
threads: block2_wang two-block connection; σ1-image/kernel-alignment angle).

## #3 — Freedom collapse (early kill before N=32 compute)

**Trigger**: `native_lever_check.py` shows the linear-lever construction's
collision freedom collapses toward 0 as N grows (mirroring the σ1 W[60]-tolerance
→0 curve in sr61_impossibility_argument.md), i.e. no collisions found at N=12/16
even with the decoupled levers.

**Required evidence**: native enumeration counts per N.

## Reopen triggers

- A new lever family (e.g. combining t-7 AND t-16 on one boundary word, or a
  σ0 t-15 lever) that the feasibility analyzer scores above current best.
- A `da[56]=0`-layered or extra-free-message-word sr=61 variant that the analyzer
  predicts has nonzero, well-shaped collision freedom.
