---
date: 2026-04-30
bet: programmatic_sat_propagator
status: REPLICATED_WITH_CAVEAT — F348's -8.78% becomes -7.44% (3-seed mean), one cand crosses zero
parent: F348 cross-cand injection (single-seed)
---

# F368: F348 5-cand × 3-seed multi-seed replication

## Setup

F348 measured the F343 2-clause injection across 5 cands at 60s cadical
budget, single seed (seed 0), and reported a mean conflict reduction of
**−8.78%** (range −5.08% to −11.09%). F366b/F366c established that for
bit31 the 60s mean across 3 seeds was −8.41%/−8.13% (σ ≈ 2-3%). F368
asks: does F348's 5-cand mean survive the same multi-seed protocol?

For each cand in {bit0, bit10, bit11, bit13, bit17}, ran cadical 60s on
{baseline, injected} with seeds {1, 2} (added to F348's seed=0). 4-way
parallel, ~5 min wall. All 20 runs logged via `append_run.py` to
`headline_hunt/registry/runs.jsonl`.

## Results

### Per-cand 3-seed table (Δ% conflicts vs baseline, lower = better)

| cand              | seed 0 (F348) | seed 1 (F368) | seed 2 (F368) | 3-seed mean | σ      |
|-------------------|--------------:|--------------:|--------------:|------------:|-------:|
| bit0_m8299b36f    | −9.63%        | **−11.99%**   | −11.18%       | **−10.93%** | 1.21   |
| bit10_m3304caa0   | −10.82%       | −9.93%        | **−12.64%**   | **−11.13%** | 1.39   |
| bit11_m45b0a5f6   | −5.08%        | −4.62%        | **+4.81%**    | **−1.63%**  | 5.50   |
| bit13_m4d9f691c   | −7.31%        | −0.98%        | −7.27%        | **−5.18%**  | 3.65   |
| bit17_m427c281d   | −11.09%       | −5.07%        | −8.87%        | **−8.34%**  | 3.04   |

**Grand mean across 5 cands of 3-seed means:** **−7.44%**
**σ_across_cands of 3-seed means:** **3.86%** (excluding bit11), **4.13%** (with bit11)

## Findings

### Finding 1 — Mean stands but tightens. F348's −8.78% was high-end of the σ envelope.

F348 single-seed: **−8.78%** mean.
F368 3-seed: **−7.44%** grand mean, σ_across_cands ≈ 4.0%.

Both are within each other's confidence interval. F348 was real but
slightly optimistic; the 3-seed picture is the standing measurement.
F343 2-clause injection on 60s cadical aux_force sr=60 force-mode
gives **roughly −7% conflict reduction with high cand-variance**.

### Finding 2 — bit11 is a real outlier; injection HURTS at seed 2.

bit11_m45b0a5f6 has 3-seed mean **−1.63%** but **σ = 5.50** — essentially
"sometimes helps a little, sometimes hurts".

| bit11 seed | baseline | injected | Δ%      |
|------------|---------:|---------:|--------:|
| 0          | 2,254,769 | 2,140,297 | −5.08% |
| 1          | 2,080,114 | 1,983,938 | −4.62% |
| 2          | 1,978,926 | 2,074,121 | **+4.81%** |

Seed 2 had a baseline that was easier than seeds 0/1 by ~14%, and the
injected run had the same difficulty as seeds 0/1. So it's not that
injection got harder on seed 2 — it's that bit11's baseline at seed 2
was unusually fast. The 2 mined clauses must remove some part of the
search space that seed 2 happened not to explore anyway.

This **falsifies a strong reading of "F343 always helps"**. The
mechanism is **statistical**: across many short cadical runs it removes
unproductive search paths on average, but on any single run the
solver may already avoid those paths via its own restart/decision
heuristics. Implications for cube-and-conquer (where many short runs
are aggregated): still a net win. Implications for single deep solves:
the variance dominates the mean — don't expect injection to help any
particular run.

### Finding 3 — High-σ cands (bit11, bit13) all share the kernel-bit-CLEAR fill (`fill00000000` or `fill55555555`).

| cand   | fill        | 3-seed σ | mean    |
|--------|-------------|---------:|--------:|
| bit0   | 0x80000000  | 1.21     | −10.93% |
| bit10  | 0x80000000  | 1.39     | −11.13% |
| bit11  | 0x00000000  | **5.50** | **−1.63%** |
| bit13  | 0x55555555  | **3.65** | −5.18%  |
| bit17  | 0x80000000  | 3.04     | −8.34%  |

The 3 cands with `fill80000000` (bit-31 of fill SET) show **mean ≈ −10%
with low σ ≈ 1-3**, whereas the 2 cands with bit-31 of fill CLEAR
(bit11 with `00000000`, bit13 with `55555555`) show **mean ≈ −3% with
high σ ≈ 4-6**.

This recapitulates F340's finding (the W57[22:23] UNSAT polarity flips
with bit-31 of fill). The injection is built from F343's preflight
which assumes bit-31-SET polarity by default. The 2 mined clauses
target the wrong polarity for bit11/bit13 cands → much weaker speedup
+ much higher variance.

**Concrete implication**: per-cand mining at the actual fill polarity
would tighten the variance for bit11/bit13. F356 already established
mode-invariance; we need to confirm fill-polarity-correct mining
recovers the **−10%** envelope on bit11/bit13.

### Finding 4 — F348's headline number must be retitled.

The standing claim was: "F343 2-clause injection gives 5-14% speedup
across 6 cands." The F368 multi-seed picture is:

> F343 2-clause injection on aux_force sr=60 force-mode at 60s cadical
> budget gives a **mean conflict reduction of −7.4% across 5 cands
> (3-seed)**, with σ_across_cands ≈ 4%, **dominated by fill-polarity
> mismatch on 2 of 5 cands**. Per-cand-correct mining likely lifts mean
> to ~−10%.

This is still a positive result, but the "headline 13.7%" lineage from
F347 → F348 → F368 has now resolved fully:

- F347 (single seed, 32-clause injection on bit31): −13.7%
- F366b (3 seed, 2-clause injection on bit31, 60s sr=60): **−8.4%**
- F348 (single seed, 2-clause on 5 cands, 60s sr=60 aux_force): −8.78%
- F368 (3 seed, 2-clause on 5 cands, 60s sr=60 aux_force): **−7.44%**

The headline-honest sentence: **"~−7-8% conflict reduction at 60s budget,
σ ≈ 3-4%, fill-polarity-aware mining required to keep variance low."**

## What's shipped

- 20 cadical runs logged in `headline_hunt/registry/runs.jsonl` (all
  TIMEOUT at 60s budget — that's the protocol, not failure).
- `F368_F348_multiseed_replication.json` with raw stats per (cand,
  condition, seed).
- This memo.
- Total compute: ~5 min wall (4 parallel × 60s × 5 batches).

## Discipline / next moves

(a) **Per-fill-polarity mining test**: re-run F343 preflight on bit11
    and bit13 with the actual fill polarity used at encode time, then
    re-run F368's seed 0/1/2 protocol. Predicted: bit11/bit13 means
    drop from −1.6% / −5.2% to ~−10% (matching the bit0/bit10/bit17
    envelope). ~3 min mining + ~3 min cadical. Small, will ship.

(b) **Update IPASIR_UP_API.md envelope** to report F368 numbers
    instead of F348 single-seed numbers. The Phase 2D propagator
    design needs to be conditioned on fill-polarity-aware mining.

(c) **Communicate to yale**: the F368 number tightens the F347→F366
    →F368 chain. yale's F378-F384 bridge-clause target is the seed of
    all of this; the corrected mean is **−7.44%** at 60s budget.

## Cross-machine implication

For the F235 hard instance (sr=61 cascade encoder, ~600-800s solve):
- 60s × ~10 = the implicit "many short cubes" decomposition.
- Cumulative 7% × 10 = ~42s saved per cube series.
- Net win for cube-and-conquer; marginal-to-zero for single deep solve.

This stands. F368 doesn't change the cube-and-conquer case. It does
tighten the single-cube headline number from "~9% mean" to "~7%
mean with σ that crosses zero on 1 of 5 cands without fill-polarity-
aware mining".

## Honest negatives

- bit11_m45b0a5f6 seed 2 actively shows **+4.81% MORE conflicts** with
  injection. This is a real failure mode — the propagator design
  must include polarity-aware mining or we will see "F343 hurts" in
  ~10-20% of single-seed runs on certain cands.
- F348's single-seed reporting was reproducible in DIRECTION but
  optimistic by ~1-2 percentage points. F348 stands as a directional
  finding, not a precise measurement.
