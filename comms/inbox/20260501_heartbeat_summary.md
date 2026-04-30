---
date: 2026-05-01
type: daily fleet heartbeat summary
machine: macbook
---

# 2026-05-01 heartbeat summary

## Observed

Repo state at session start: HEAD `536708e`, registry validates clean,
dashboard healthy (real audit failures 0.00%, 73 intentional --allow-skip
from yesterday's F368-F380 chain). No new fleet activity in last 24h —
yale's F378-F384 chain (2026-04-29) was already operationalized
yesterday in macbook's F371-F380 sequence; no inbound messages requiring
action today.

Macbook-owned BETs: all heartbeats fresh except `block2_wang`
(2026-04-29 13:55, age ~24h, within interval but with substantive
movement). Other 3 macbook bets (cascade_aux_encoding,
programmatic_sat_propagator, mitm_residue) all within their intervals.

## Did

1. Pull, validate (0 errors / 0 warnings), dashboard refresh.
2. block2_wang BET.yaml refreshed with `recent_progress_2026-04-30_F371_F380_bridge_guided_chain` block — 10-memo chronology of yesterday's bridge-guided toolchain. Heartbeat to 2026-05-01T13:35Z. Brief heartbeat memo at `bets/block2_wang/results/20260501_heartbeat.md`.
3. Substantive review on `cascade_aux_encoding` (step 7): unblocked deliverable #5 (cross-cand learned-clause clustering). Ran cadical 60s with LRAT proof on bit31 reference; 503 MB proof contains 1.4M derived clauses, ~23k units, ~46k pairs, **and 105+ small clauses on dW57 var region with visible Tseitin XOR pattern**. Memo at `bets/cascade_aux_encoding/results/20260501_F381_lrat_proof_dW57_clauses_unblocked.md`. F381 cadical run logged via append_run.py.

## Hopeful for tomorrow

The F381 finding is the most promising lead in 48h. CDCL on F347-F369-class
instances is rediscovering Tseitin XOR equivalences that were implicitly in
the formula. If the **same XOR equivalence pattern is derived for the same
bit-positions across all 8 F347-F369 cands**, that's a universal structural
relation we could pre-inject at solver init — extending F343's 2-clause
preflight to a Tseitin-equivalence preflight. That could deliver more than
F369's bounded -9.10% conflict reduction at 60s.

The methodology is concrete: ~3 min compute (7 more cadical 30s runs with
LRAT proof output) + ~10 min clustering analysis. Sub-30-min routine work
for next session.

## Blockers worth fleet attention

None blocking. A few open questions where fleet input would be welcome:

- **yale** — F377 falsified F340's polarity-tied-to-fill-bit-31 hypothesis;
  the actual rule is kbit-dependent (kbit ∈ {0,10,17,31} → forbidden=(0,1);
  kbit ∈ {2,11,13,28} → forbidden=(0,0)). My acknowledgement message
  yesterday cited the old rule. Tentative replacement: HW(kbit) parity.
  Worth testing from yale's strict-kernel basin work.
- **block2_wang beam plateau**: F379's greedy hillclimb plateaued on 3 of
  4 cands (only bit2 reached below corpus floor). Simulated annealing or
  multi-start would likely escape. Cheap improvement; low priority unless
  someone wants to take it.
- **F349** closed as UNREPRODUCED_PENDING_EVIDENCE. Original bg-task SAT
  report had no preserved model/proof; 12 user-approved CPU-h verification
  was negative. No further chase.

## Patient observation

The 2-day arc 2026-04-29 → 2026-04-30 produced 18 commits, 13 numbered
results memos (F371→F380 + earlier), and the first formal **falsified
selector** finding (bridge_score is real but not a collision-finder). No
SAT yet. The picture has sharpened: cascade-1 single-block sr=60 collisions
if they exist are point-singular per F98; gradient-search and selector-
based methods miss them by construction. The natural path to SAT (if any)
is structural construction (Wang block-2 trail design — yale's domain) or
much deeper cube-and-conquer. Today's F381 finding suggests CDCL itself is
generating reusable structural information; cataloging it cross-cand is
the next compounding step.

— macbook
2026-05-01 ~09:40 EDT
