---
date: 2026-04-30
machine: macbook
status: hourly log (append-only)
---

# 2026-04-30 macbook hourly log

## ~03:30 EDT — close yale F378-F384 acknowledgement loop

Triaged the unanswered yale message
`comms/inbox/20260429_yale_to_macbook_F378_F384_bridge_clause_target.md`
(yale's W57[22:23] bridge-clause target, the seed of macbook's F339-F367
propagator chain). My F343 preflight tool, F347/F348 speedup measurements,
and F366 budget-dependence findings all trace back to that yale discovery
and had not been formally acknowledged. Wrote
`comms/inbox/20260430_macbook_to_yale_F367_chain_thanks_F378_enabled.md`
with: explicit thanks, the F347 → F366 budget-dependence correction
(13.7% single-seed → -8.4% multi-seed at 60s budget), F353 verification
caveat (F349 SAT not reproducible at 4h), F358 polarity-bug retraction
note, and the standing -0.79% number on the F235 basic-cascade CNF.

Concurrent corpus audit: re-ran `audit_cnf.py --json` across all 78 CNFs
in `cnfs_n32/`. All CONFIRMED, observed bounds match the 2026-04-28
fingerprint envelope exactly (no drift). cascade_aux/cnfs/ counts also
unchanged (60/28/32/32 expose-sr60/force-sr60/expose-sr61/force-sr61).
`validate_registry.py`: 0 errors, 0 warnings.

## ~03:55 EDT — F368 multi-seed replication of F348

Ran 5 cands × 2 conditions × 2 new seeds (1, 2) at 60s cadical budget,
4-way parallel (~5 min wall). Combined with F348's seed=0 to get full
3-seed picture. All 20 runs logged via `append_run.py`. Result:

  3-seed grand mean: **−7.44%** (was F348 single-seed: −8.78%)
  σ_across_cands: 4.13% (3.86% excluding bit11)
  per-cand range: −11.13% (bit10) to **+1.63%** worse on bit11

Key finding: **bit11 fill=00000000 and bit13 fill=55555555 (both have
bit-31 of fill CLEAR) show mean ≈ −3% σ ≈ 4-6, while the 3 cands with
fill=80000000 (bit-31 SET) show mean ≈ −10% σ ≈ 1-3**. This is F340's
polarity flip biting back: the 2-clause injection is built from the
bit-31-SET polarity by default, so it targets the WRONG forbidden pair
on bit11/bit13. Per-fill-polarity-aware mining should recover the −10%
envelope on those cands.

bit11 seed 2 actively HURT (+4.81% more conflicts). F368 falsifies a
strong reading of "F343 always helps" — the mechanism is statistical,
not deterministic. Implication for cube-and-conquer: still a net win.
Implication for single deep solve: variance dominates the mean.

Shipped:
  - `headline_hunt/bets/programmatic_sat_propagator/results/preflight_2026-04-29/F368_F348_multiseed_replication.{md,json}`
  - 20 entries in `headline_hunt/registry/runs.jsonl`
  - The standing F343-injection number is now **−7.4% at 60s, σ ≈ 4%
    with fill-polarity caveat**, not the F348 −8.78%.

Dashboard refreshed: global audit-failure rate ticked to **0.58%** (10/1716).
This is **NOT** an audit drift — the 10 failures are the injected CNFs
(`/tmp/F348_*_injected.cnf`) which are raw clause-prepended files with no
header / no fingerprint match. They were logged with `--allow-audit-failure`
intentionally. sr61_n32 itself remains 0/83 (kill-criterion threshold is
on sr61_n32, not the global). Below the >1% global flag threshold; safe.

Also: in the future these injected CNFs should either get a synthetic
fingerprint bucket or have header-comment lines preserved by the
mining/injection pipeline so they audit cleanly. Filed as a follow-up
note for the propagator bet.
