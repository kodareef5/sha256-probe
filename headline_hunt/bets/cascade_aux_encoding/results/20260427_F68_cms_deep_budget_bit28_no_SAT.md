# F68: CMS deep-budget on bit28 (Cohort D) — no SAT discovery
**2026-04-27 14:28 EDT**

Tests whether bit28's Cohort D (CMS-only fast) advantage extends to
collision discovery at deeper budgets. Single seed, 1M conflicts on
CMS — would be HEADLINE if SAT.

## Result

```
CMS 5.13.0 on bit28_md1acca79 cascade_aux Mode A sr=60:
  Budget: 1,000,000 conflicts
  Wall: 290.28 seconds (~4.8 min)
  Status: s INDETERMINATE (UNKNOWN — hit conflict cap)
```

**No SAT found.** bit28's Cohort D fast-at-100k advantage doesn't
translate to deep-budget SAT discovery.

## Honest interpretation

Per the F32 deep-min corpus + F65/F66/F67 cert-pin verifications, F32
deep-min residuals across the 67-cand registry are universally
near-residuals (HW > 0). For sr=60 cascade_aux Mode A to be SAT, the
final state diff at round 63 must be ALL ZERO (collision).

The cascade_aux Mode A SAT problem is the FULL collision search,
not just cascade-1 trail finding. Deep budget on a single cand can't
find SAT unless the cand admits a sr=60 collision via cascade-1. The
m17149975 cand IS a sr=60 collision (verified) — that's why its
cert-pin is SAT in 17ms.

Other cands like bit28 have low-HW residuals (HW=33-49) but no known
collision. F68 confirms 1M conflicts isn't enough to find one.

## Scaling estimate

CMS conflict-rate on bit28: ~3,400 conflicts/sec (1M conflicts in 290s).

For potentially sufficient depth to find a collision (per Wang 2005's
collision search complexity ~2^60 for SHA-1, similarly heavy for SHA-2
sr=60):
- 100M conflicts: ~8 hours per seed
- 1B conflicts: ~80 hours per seed
- 10B conflicts: ~800 hours per seed (~33 days)

For comparison, m17149975's collision was found via deep multi-machine
sweep over weeks per session summary. Single-seed single-cand at 1M
is far too shallow.

## What F68 establishes

1. **bit28's Cohort D advantage is moderate-budget specific.** Fast at
   100k doesn't mean fast collision discovery. The 100k advantage
   reflects CMS's preprocessing exploiting bit28's structural
   redundancy (BVA/var-elim), not deep search efficiency.

2. **Deep-budget SAT discovery requires authorization.** Per CLAUDE.md,
   multi-hour kissat/CMS sweeps need user authorization. Single 4.8-min
   single-seed test is exploratory; productive collision search needs
   multi-day multi-machine compute.

3. **The Wang block-2 attack is the right path forward.** Rather than
   brute-force deep-budget on bit28 cascade_aux, design a Wang-style
   block-2 trail that absorbs yale's HW=33 EXACT-sym residual to a
   FULL collision via second-block message modification.

   This is dramatically more efficient: the 2-block CNF would have
   the residual already pinned (via yale's W-witness) and need to
   only find the M_2 message pattern. The probability cost of this
   trail is ~2^-LM (= 2^-679 for HW=33 EXACT-sym) but with
   second-block freedom (~256 bits), expected solutions = 2^(256-679)
   = 2^-423 — still infeasible directly.

   But the structural advantage of yale's HW=33 EXACT-sym (vs random
   HW>=44 trails) means the carry constraints are MUCH cleaner.
   Wang-style message modification can satisfy specific bitconditions
   far more efficiently than random sampling.

## Conclusion: cascade_aux SAT brute force won't reach a collision

Even on the cand most-favorable to deep-budget search (bit28 on CMS),
1M conflicts × 4.8 min wall × 1 seed produces UNKNOWN. The path to a
HEADLINE collision discovery is NOT brute-force SAT on the cascade_aux
Mode A sr=60 CNF. The path is **Wang-style block-2 absorption**.

For yale: yale's online-sampler structural depth (HW=33 EXACT-sym
LM=679 in one day) is the RIGHT axis to push. Each HW reduction
in yale's online sampling is worth orders of magnitude more than
deep-budget SAT.

For block2_wang: F65/F66/F67 verification pipeline + yale's HW=33
target = ready for block-2 trail design. F68 confirms the alternative
path (deep-budget SAT) isn't feasible at single-machine scale.

## Discipline

- 1 CMS run logged via append_run.py
- CNF pre-existing + audited
- Sequential measurement, single seed (exploratory probe)
- No big-compute authorization needed (4.8 min, well under threshold)

EVIDENCE-level: VERIFIED. CMS at 1M conflicts on bit28 returns
INDETERMINATE. Honest negative result.

## Concrete next moves

1. **Ask user for authorization** for multi-hour deep-budget SAT
   sweep on top targets (msb_ma22dc6c7 + bit28 + bit2 at 100M each).
   Big compute, multi-day, but might find a NEW collision cert if
   any exists.

2. **Or: pivot to Wang block-2 trail design** (yale's domain
   expertise). This is the structural path forward.

3. **Or: continue cross-axis discovery** with smaller experiments
   like F61-F66 (cert-pin sweep extensions, cadical/CMS comparisons
   on more cands).

User direction needed for path #1; autonomous flow continues for #3.
