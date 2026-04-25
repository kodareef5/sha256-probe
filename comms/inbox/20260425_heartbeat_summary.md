# 2026-04-25 daily heartbeat — summary

**Author**: macbook
**Time**: 13:35Z (09:35 EDT)

## Observations

- **Fleet state**: dormant. No non-macbook commits in last 48h+ (most recent linux-24core message: 2026-04-17, eight days ago). All 16 commits today authored by kodareef5 (macbook).
- **Registry**: 0 errors, 0 warnings. Healthy.
- **Run dashboard**: 125 total runs, 0% audit failures across both active bets.
- **Budget headroom**: cascade_aux_encoding 1.6% used (3.2/200 CPU-h), mitm_residue 0.3% used. Wide open.
- **Heartbeats**: all 3 macbook-owned BETs (cascade_aux_encoding, block2_wang, mitm_residue) refreshed within last 4 hours by inline updates. No stale BETs.

## What I did

This was the autonomous "stay busy" rhythm shipping into a quiet fleet:

1. **Cross-kernel cascade_aux CNF set** (commit `41b62de`): 36 CNFs (9 kernels × 2 sr × 2 modes), all audit-CONFIRMED. Reproducible via `cnfs/regenerate.sh`.
2. **Per-conflict speedup characterization** (multiple commits): Mode B is 2× faster per conflict on kissat at 50k budget, **highly seed-stable** (CV=0.0 across 15 runs), **3.4× on cadical**.
3. **Honest erosion finding** (commits `d3ed48b`, `dfff4b4`): the speedup is *front-loaded* — at 500k+ budgets it converges to ~1×. Reframes the bet's "≥10× SAT speedup" SPEC claim as a 2-6× preprocessing speedup.
4. **Programmatic SAT propagator unblocked** (commits `8138fd3`, `4b649e5`, `2bcfffe`, `56b4c6f`): SPEC, IPASIR-UP API survey, Phase 1 Python prototype, varmap sidecar bridging encoder ↔ propagator.
5. **Registry maintenance**: bit-25 candidate added to candidates.yaml (was missing despite kernel existing). Heartbeat note for cascade_aux_encoding.
6. **This morning's heartbeat work**: integrated `--varmap +` into `cnfs/regenerate.sh` so any worker who picks up the propagator bet gets varmaps automatically. Updated `.gitignore`.

Total today: 19 commits, 125 logged runs, 6 RESULT.md writeups across `comparisons/`.

## What I'm hopeful about tomorrow

- **Path B (propagator) is genuinely actionable now.** SPEC + Python prototype + smoke test + varmap bridge all shipped. A worker with C++ chops can start Phase 2B immediately — the only remaining blocking is engineering, not design.
- **Path A (4h+ fleet kissat runs on the 36-CNF set)** is shovel-ready. Any returning fleet machine can `git pull` and run `bash regenerate.sh` followed by long-budget kissat sweeps without further setup.
- The **honest characterization** of Mode B as front-loaded (vs the SPEC's 10× claim) prevents future workers from chasing a phantom — saves CPU-h on the wrong direction.

## Blockers worth another machine's attention

- The fleet has been dormant for 8+ days. If `linux-24core` or other workers come online, the 36-CNF set + propagator SPEC are immediate pickup opportunities. Suggest they start with cascade_aux_encoding's 4h+ kissat-MSB-cert run (does Mode B's 2× front-loaded gain compound at long budget? Open question.).
- Phase 2B propagator C++ implementation is non-trivial (multi-day) and best done by a worker who's familiar with CaDiCaL internals. Could announce as a pickup opportunity if anyone has C++ experience.
- block2_wang remains BLOCKED on backward-trail-search engine. Multi-week project. No new path forward today.

## What I won't do without explicit user direction

- Launch multi-hour kissat sweeps from heartbeat scripts.
- Modify lib/ shared code.
- Force-push or rewrite history.
- Spawn external service calls (paper fetches, etc.).

The picture sharpens daily. The bet portfolio has moved from "we should test cascade_aux" to "cascade_aux gives 2-6× preprocessing speedup, here's why" — that's a real epistemic step. Quiet day on the fleet but the record is more honest than yesterday.

— macbook
