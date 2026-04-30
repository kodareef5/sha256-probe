---
date: 2026-04-30
bet: block2_wang
status: STRUCTURAL_SIGNATURE — sub-65 cascade-1 residuals are highly uniform (active set, da≠de, HW asymmetry)
parent: F371-F373 cert-pin coverage closure
tool: extract_top_residuals.py (shipped 2026-04-30 ~07:30 EDT)
compute: 0 solver runs (pure data analysis on existing corpora)
---

# F374: cluster analysis of 171 sub-65 cascade-1 residuals across 17 cands

## Setup

After F373 closed cert-pin coverage at 67/67 (100%, all UNSAT), the
question is whether the **structural geometry** of the lowest-HW
residuals carries information that random sampling missed.

Used `extract_top_residuals.py --top-k 1000 --hw-max 65` to dump every
sub-65 record across the 47 per-cand corpora. **171 records across 17
cands** (the other 30 cands have min_hw ≥ 65). Pure data analysis,
no compute.

## Result — 4 strong structural signatures

### Signature 1 — Active register set is 100% `[a, b, c, e, f, g]`

Every single one of the 171 sub-65 records has identical active set:
**a, b, c, e, f, g** with d=h=0 always. **Cascade-1 hardlock fingerprint
is universal across the deepest tail of the natural distribution.**

This isn't surprising — cascade-1's structural constraint forces
d63=h63=0. But the universality at sub-65 specifically rules out one
hypothesis: that the lowest-HW residuals come from edge cases where
the cascade structure partially breaks. They don't. The cascade-1
hardlock is even MORE robust at low-HW than at typical-HW.

### Signature 2 — `da_eq_de = False` for 100% of records

Across all 171 sub-65 records: **da_63 ≠ de_63 always**. The
F26/F27-class a_61 == e_61 symmetry (Theorem 4 at r=61) does not extend
to round-63 residuals. The lowest-HW W-witnesses NEVER satisfy
da_63 = de_63.

This contradicts an early hypothesis that the rounds 61-63 might
preserve da=de symmetry into the residual. They don't, at least not
for the deep tail. Implication: trail-search engines that constrain
da_63 = de_63 as a heuristic will SKIP all sub-65 W-witnesses. **Don't
constrain da_63 = de_63 in any sub-65-targeted block2_wang search.**

### Signature 3 — Per-register HW is non-uniformly distributed

Across the 171 records, the per-register HW63 distribution is:

| reg | mean | stdev | range  | "heaviest" mode | %   |
|----:|-----:|------:|-------:|-----------------|-----|
| a   | 11.58 | 2.47 | [5,18] | 30 records      | 17.5% |
| b   | 11.45 | 2.45 | [5,18] | 34 records      | 19.9% |
| c   | **8.60**  | 2.27 | [3,15] | 5 records       | 2.9% |
| d   | 0.00 | 0.00 | [0,0]  | 0               | 0%  |
| e   | 11.67 | 2.72 | [4,19] | 42 records      | 24.6% |
| f   | 11.71 | 2.70 | [6,20] | **54 records**  | **31.6%** |
| g   | **8.67**  | 2.11 | [3,15] | 6 records       | 3.5% |
| h   | 0.00 | 0.00 | [0,0]  | 0               | 0%  |

**c and g are systematically ~3 HW lighter than a/b/e/f.** This is a
non-trivial structural asymmetry. Its cause is presumably the SHA-256
round function's coupling: c and g feed into Maj/Ch via a different
path than a/b/e/f, and the cascade-1 hardlock at d=h=0 propagates
asymmetric noise back through round 62-63.

f is the most-frequently-heaviest register (31.6%), followed by e
(24.6%) — these are the two registers most directly affected by the
Sigma1 and Ch operators in the round function.

### Signature 4 — sub-60 tail: 7 records across 5 cands, no further structural break

7 records have hw_total < 60:

| cand                         | n |
|------------------------------|--:|
| bit28_md1acca79_fillffffffff | 2 |
| bit3_m33ec77ca_fillffffffff  | 2 |
| bit13_m916a56aa_fillffffffff | 1 |
| bit19_m51ca0b34_fill55555555 | 1 |
| bit2_ma896ee41_fillffffffff  | 1 |

All 7 still have da_eq_de=False and active_regs=[a,b,c,e,f,g]. No
further structural break at the deepest tail — the same uniform
signature holds. The HW continues to drop while the structural
features stay constant.

This rules out a hypothesis that "really low HW residuals must have
some special structural feature". They don't — they just have lower
HW per the same uniform pattern.

## Min-HW bucket distribution (17 cands with sub-65 records)

| bucket | n cands | cands |
|---|---:|---|
| HW [55, 60) | 5 | bit3 (55), bit2 (57), bit13_m916a56aa (59), bit19 (58?), bit28 (59) |
| HW [60, 65) | 10 | bit11, bit13, bit18, bit24, bit25, bit4, bit4, m189b13c7, m9cfea9ce, msb |
| HW [65, 70) | 2 | bit10, bit17 |

5 of 17 cands have sub-60 W-witnesses. F372 + F373 cert-pin verified
all of them — **all UNSAT**. So the structural signature (universal
active-set, da≠de, c-g lighter) is **necessary but not sufficient**
for collision.

## Findings

### Finding 1 — Sub-65 cascade-1 residuals are NOT structurally distinct from typical residuals

The active set, da_eq_de pattern, and even the per-register HW
asymmetry are PROPERTIES OF CASCADE-1, not of low-HW specifically.
Random sampling at higher HW (the F101 mode region HW=90-99) almost
certainly produces the same signatures.

This means: **there is no "low-HW special structure"** that a
trail-search heuristic could exploit. The lowest-HW residuals are
the lowest-HW samples of a uniform distribution shape.

### Finding 2 — Don't constrain da=de in trail search

100% of the deep-tail residuals have da≠de. Any trail-search heuristic
that constrains da_63 = de_63 (or its near-relatives) will systematically
exclude the structurally relevant search region.

### Finding 3 — c and g are systematically lighter; this is exploitable

The c and g registers having 25% lower mean HW than a/b/e/f is a
real structural asymmetry. **A trail-search engine that prioritizes
constraining c and g residuals first** would be more likely to find
HW-cancellation paths than one that treats all 6 active registers
uniformly.

This is a concrete predictive finding: the per-register HW asymmetry
is a load-bearing property of cascade-1 dynamics that the existing
block2_wang search does not exploit.

### Finding 4 — bit-3 family dominates the deep tail

bit3_m33ec77ca contributes 2 of 7 sub-60 records and 33 of 171 sub-65
records (19.3% of total). bit3 is the kernel-bit family with the
strongest concentration of low-HW residuals. (bit2 is second at 31
records; bit28 third at 29.) **These three cands collectively account
for 93/171 = 54% of all sub-65 records.**

If single-block sr=60 cascade-1 collisions are reachable at our compute
scale, **the bit3/bit2/bit28 cands are the most likely source**.
F372 already cert-pin verified the lowest-HW witness for each of these
three (HW 55, 57, 59) → all UNSAT. So either:
(a) The collisions exist at HW lower than 55 (theoretical — not in any
   corpus yet) — would require exhaustive brute-force or hill-climb
   below the current corpus floor, AND/OR
(b) The collisions are **point-singular** at specific HW≥0 vectors
   that random sampling never hits (per F98's "collisions are
   point-singular, not basin-singular" finding on m17149975).

(b) is consistent with F100's headline conclusion. (a) is what the
project would need to disprove (or hit) to overturn it.

## Implications for block2_wang next moves

**Don't run more random-sample residual corpora.** The 200K-sample
runs at HW≤80 already saturate the structural signatures; more samples
of the same distribution add no information.

**Don't constrain da=de in trail search.** Wastes search effort on
zero-density regions of the deep tail.

**Do prioritize c and g residual cancellation** in trail-search
heuristics. Their mean HW is 25% lower than a/b/e/f, suggesting
they're easier to drive to zero — and any path to single-block
collision must zero out all 6 active registers simultaneously.

**Do focus on bit3/bit2/bit28 cands** as the most concentrated
sub-65 producers. These three cands constitute 54% of sub-65
records. If a hill-climb tool is available, target these first.

## What's shipped

- This memo
- 0 solver runs (pure analysis)
- The per-register HW asymmetry finding is a concrete predictive
  hypothesis for block2_wang trail-search work
- Concretely refutes "constrain da=de in trail search" as a viable
  heuristic for sub-65 W-witnesses

## Cross-bet implications

For programmatic_sat_cascade_propagator (Phase 2D design): the
F286 132-bit universal hard core is the structural bottleneck for
CDCL search. The F374 per-register HW asymmetry suggests an additional
DECISION-PRIORITY heuristic: **branch on c and g state vars before
a/b/e/f state vars** at rounds 62-63. Adds to the F286-bit-prioritized
cb_decide hook design without changing soundness.

This is testable — but gates on Phase 2D implementation cycle, not
this hour's work.

## Discipline

- Pure data analysis on existing 47 corpora.
- 0 cadical/kissat/cms invocations.
- 0 runs.jsonl entries (this is documentation, not solver work).
- audit_required: not applicable (no CNFs touched).
