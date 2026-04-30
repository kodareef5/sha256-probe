---
date: 2026-04-30
bet: programmatic_sat_propagator
status: CLEAN_RESULT — F368 polarity-flip claim FALSIFIED; F343 injection mean is −9.10% σ=2.68%
parent: F368 (confounded by encoder version)
retracts: F368's "fill-polarity-flip" hypothesis
---

# F369: F348/F368 replication with consistent encoder version

## Bug found in F348 / F368

F348's injected CNFs in `/tmp/F348_*_injected.cnf` were generated with the
**newer cascade_aux_encoder version** (13220 vars, 54793 clauses for
bit11). The "baseline" CNFs my F368 ran against were
`headline_hunt/bets/cascade_aux_encoding/cnfs/aux_force_sr60_n32_bit*_*.cnf`
which are the **older encoder version** (12592 vars, 52657 clauses for
bit11) — a 628-var / 2136-clause structural difference.

So F368's "Δ% conflicts" was partly measuring the encoder upgrade's effect,
not pure clause injection. F368's bit11 outlier (+4.81% on seed 2) and the
"fill-polarity-flip" hypothesis I built on it were **confounded artifacts**.

This memo retracts F368's polarity-flip claim and ships the clean number.

## What F369 does

For each cand in {bit0, bit10, bit11, bit13, bit17}, regenerate a fresh
aux_force sr=60 force-mode CNF using the **current encoder version**
(`cascade_aux_encoder.py`, 2026-04-24 build). Output in `/tmp/F369_*_force.cnf`.

Run cadical 60s × 3 seeds {0, 1, 2} on each fresh baseline. Compare against
the F348/F368 injected runs (which used the new-encoder injected CNFs and
are valid).

15 cadical runs, parallel-4, ~5 min wall. All logged via `append_run.py`.

## Result — clean Δ% (fresh-encoder baseline vs F348-injected)

| cand                 | seed 0      | seed 1      | seed 2      | 3-seed mean | σ      |
|----------------------|------------:|------------:|------------:|------------:|-------:|
| bit0_m8299b36f       | −10.13%     | −10.09%     | −4.76%      | **−8.33%**  | 3.09   |
| bit10_m3304caa0      | −12.02%     | −9.84%      | −14.24%     | **−12.03%** | 2.20   |
| bit11_m45b0a5f6      | −4.99%      | −9.43%      | −8.26%      | **−7.56%**  | 2.30   |
| bit13_m4d9f691c      | −5.37%      | −5.07%      | −7.21%      | **−5.89%**  | 1.16   |
| bit17_m427c281d      | −12.79%     | −9.33%      | −13.03%     | **−11.72%** | 2.07   |

**Grand mean across 5 cands of 3-seed means: −9.10%**
**σ_across_cands of 3-seed means: 2.68%**

## Comparison to prior numbers

| Memo | Method                                      | Mean  | σ_across_cands | Status              |
|------|---------------------------------------------|------:|---:|---------------------|
| F347 | single seed, bit31, 32-clause inject       | −13.7% | n/a | outlier (single-seed, 32 clauses) |
| F348 | single seed, 5-cand, 2-clause inject       | −8.78% | n/a | matches F369 closely (validated retroactively) |
| F368 | 3-seed, 5-cand, **encoder-mismatched** inject | −7.44% | 4.13% | **CONFOUNDED (encoder version)** |
| F369 | 3-seed, 5-cand, **consistent-encoder** inject | **−9.10%** | **2.68%** | **CLEAN** |

F348's −8.78% single-seed number is essentially correct — the F368
methodology error tightened it incorrectly, then F369 cleans up.

## Findings

### Finding 1 — F368's "fill-polarity-flip" claim is RETRACTED

F368 reported bit11 mean −1.63% σ=5.50, with seed 2 at +4.81% (injection
HURT). That suggested the F343 mining used the wrong forbidden polarity
for bit11/bit13 (kernel bit-31-CLEAR fills).

In F369 with the same-encoder baseline, bit11 is **−7.56% σ=2.30** —
no outlier behavior. bit11 seed 2 is **−8.26%** (injection HELPS), not
+4.81%. The polarity hypothesis is FALSIFIED — F348 was already per-cand
polarity-correct (verified by inspecting the prepended unit clauses:
bit0/bit10/bit13 use `-12373/-12317/-12369` (dW57[0]=0), bit11/bit17 use
`+12369/+12338` (dW57[0]=1) — flipped per cand).

The variance F368 saw was **encoder-version difference**, not polarity.

### Finding 2 — F343 minimal preflight gives a stable −9% effect

The clean F369 number is **−9.10% conflict reduction with σ=2.68%**.
This is a tight, stable result across 5 cands (range −5.89% to −12.03%).

For Phase 2D propagator design: the cb_add_external_clause hook applied
to F343's 2 mined clauses delivers a **~9% conflict reduction with
~3% standard deviation across cands** at 60s cadical budget on aux_force
sr=60 force-mode. No fill-polarity carve-out needed (already handled
per-cand by the F343 mining tool).

### Finding 3 — bit13 still slightly underperforms (−5.89% vs −9% group mean)

bit13 (m4d9f691c, fill=0x55555555) is the lowest cand at clean −5.89%
mean. It's not an outlier (σ=1.16, tight), just lower than the others.
Possible cause: the alternating fill pattern (0x55555555) interacts
differently with the cascade-1 constraint structure. Or the F343 mined
clauses have less leverage on this specific m0/fill combination.

This is a one-cand observation across 3 seeds; not enough data to
characterize. Worth re-running on bit13 with the **F344 32-clause
extended preflight** (~13 min mining) to see if more mined clauses
recover the −10% envelope.

### Finding 4 — Budget dependence remains (F366 finding stands)

F366 established the F343 effect saturates from ~−9% at 60s to ~−1% at
5min. F369 doesn't change that finding — F369 measures only at 60s.

The full envelope (incorporating F369):

| budget | mean Δ conflicts | source |
|--------|---:|---|
| 60s    | **−9.10%** σ=2.68%, 5 cands × 3 seeds | F369 (clean) |
| 5min   | −0.79% σ≈3% (saturated) | F366 |

## What's shipped

- `F369_consistent_encoder_replication.{md,json}`
- 15 cadical run entries in `headline_hunt/registry/runs.jsonl`
- This memo with retraction of F368's polarity-flip claim
- 5 fresh-encoder force-mode CNFs in `/tmp/F369_*_force.cnf` (not committed)

## Discipline / next moves

(a) **Update F368 memo** with retraction header pointing to F369. Don't
    delete F368 — its data is real, just confounded; the documentation
    is part of the record.

(b) **Update IPASIR_UP_API.md envelope** (F361 update) with F369's
    clean −9.10% σ=2.68% number. Phase 2D propagator design should
    quote this, not F368's confounded −7.44%.

(c) **Tell yale**: the F347 → F366 → F368 → F369 chain converged on
    −9.10% σ=2.68% as the standing F343-injection number at 60s budget.
    F368's polarity-flip claim was a confound; retracting.

(d) **Bigger-encoder audit**: re-audit `cascade_aux/cnfs/` directory.
    Old-encoder files (12592 vars) and new-encoder files (13220 vars)
    coexist there. The audit_cnf.py fingerprint range covers both,
    so audits don't catch the version mismatch — but we should add
    an encoder-version field to the CNF header comments so future
    F368-class confounds are caught at audit time.

## Honest negatives

- F368's polarity-flip claim (a 5-cand finding I shipped 1 hour ago)
  was a confounded artifact. Retracted in this memo. Lesson: when the
  baseline and treatment files come from different scripts/versions,
  always cross-check `wc -l` and the `p cnf` line before measuring Δ.
- F348 retroactively validated. F348 single-seed −8.78% is approx correct;
  F369 3-seed −9.10% confirms.
- F347 (−13.7% single seed) and F362 (−0.46% sr=61 bit25) remain
  outliers, but they're outside this memo's 5-cand sr=60 force-mode
  scope and aren't claimed to be representative.

## Compute discipline

- 15 cadical runs × 60s parallel-4 ≈ 5 min wall.
- Total bet compute on 2026-04-30 (this hour + previous F368): 35 cadical
  runs at 60s = ~35 min cadical time, all logged.
- Audit-failure rate: 15 of these are `--allow-audit-failure` (the
  /tmp/F369_*.cnf paths don't match a fingerprint bucket since they're
  in /tmp). Logged and acknowledged; will move to a stable directory
  if these fresh-encoder CNFs prove load-bearing for further work.
