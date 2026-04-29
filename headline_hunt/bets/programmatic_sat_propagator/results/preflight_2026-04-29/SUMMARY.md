---
date: 2026-04-29
bet: programmatic_sat_propagator
status: TOOL_SHIPPED — preflight_clause_miner across 6 cands
---

# F343: preflight_clause_miner shipped + 6-cand mining results

## Tool

`preflight_clause_miner.py` (in `propagators/`) — runs cadical 5s
probes per cand to extract:

- Class 1a-univ unit clauses on dW57[0] (per F341/F342)
- Class 2-univ pair clauses on W57[22:23] (per F340/F384)

Output: per-cand JSON with `inject_unit` / `inject_pair` literals
ready for IPASIR-UP `cb_add_external_clause` injection.

Per-cand wall: ~20s (5 cadical runs at 5s budget each, of which 1-3
fast-UNSAT in <0.1s and 2-3 hit budget at 5s).

## Mining results across 6 cands

| Cand | M[0] | fill | dW57[0] forced | W57[22:23] forbidden |
|---|---|---|:---:|:---:|
| bit0  | 8299b36f | 0x80000000 | **0** | (0, 1) |
| bit10 | 3304caa0 | 0x80000000 | **0** | (0, 1) |
| bit11 | 45b0a5f6 | 0x00000000 | **1** | (0, 0) |
| bit13 | 4d9f691c | 0x55555555 | **0** | (0, 0) |
| bit17 | 427c281d | 0x80000000 | **1** | (0, 1) |
| bit31 | 17149975 | 0xffffffff | **1** | (0, 1) |

(W57[22:23] polarity matches F340 perfectly: fill bit-31 set → (0, 1),
fill bit-31 unset → (0, 0). dW57[0] polarity does NOT track fill bit-31
alone.)

## What this enables

For any cascade-1 collision instance (sr60 force-mode), running this
preflight tool yields 2 ready-to-inject clauses for an IPASIR-UP
propagator:

1. Unit clause at dW57[0]: 1 literal
2. Blocking clause at W57[22:23]: 2 literals

Both are CDCL-derivable but NOT in the original Tseitin (per F324-F326
search-invariant thesis). Pre-loading saves cadical's redundant
re-derivation cost on every solve attempt.

## Compute discipline

- ~120s total wall (6 cands × 20s preflight).
- 30 cadical solver runs (5 polarity probes per cand × 6 cands).
- All probes at 5s budget — no long compute.
- All 6 input CNFs were freshly generated + audited (CONFIRMED) per F326.

## Bug fix during shipping

Initial preflight tool emitted `cadical -t 5.0` (float) which cadical
3.0.0 rejects with "invalid argument in '-d 5.0'". Fixed to `-t 5`
(integer). Caught the bug via direct cadical reproduction vs subprocess
invocation comparison. Tool now produces correct results matching
F340/F341/F342 verdicts.

## What's next

(a) **Extend to more (round, bit) probes**: F341 only found dW57[0] as
fast single-bit; F340 only tested W57[22:23] adjacent pair. Try
dW57[i] for i ∈ {1..31} on 1 cand to see if more single-bits exist.
Try (dW57[i], dW57[i+1]) adjacent pairs for i ∈ {0..30}. ~10-15 min
total.

(b) **Test on sr=61 CNFs**: F330 confirmed sr=61 fits the same UP-free
schedule pattern. Does the universal-with-flip mining transfer to
sr=61? Cascade location shifts to W*_57+W*_58+W*_59 (per F271/F273),
so probably need to probe W56/W57 pairs at sr=61 instead of W57[22:23].

(c) **Phase 2D propagator implementation**: with the preflight tool +
mining results, the IPASIR-UP propagator's `cb_add_external_clause`
hook can ingest the per-cand JSON and inject the clauses at solver
init. This is the concrete next implementation step for the
programmatic_sat_propagator bet's reopen.

## Cross-machine status

The yale → macbook → preflight chain:

1. yale F378-F384 (conflict-guided cube + UNSAT minimization)
2. macbook F339 (cross-validation)
3. macbook F340 (cross-cand generalization)
4. macbook F341 (single-bit dW57[0] discovery)
5. macbook F342 (cross-cand single-bit validation)
6. macbook F343 (preflight tool + 6-cand mining; this memo)

The Phase 2D propagator design (F327) is now structurally backed by
6 concrete cand-specific clause sets ready for testing.
