---
date: 2026-04-28
bet: cascade_aux_encoding
status: PRINCIPLES_FRAMEWORK_GAP_PREDICTION_FALSIFIED
---

# F207: cascade_aux Tanner graph 4-cycle structure — gap-9/11 prediction wrong; quasi-cyclic word-aligned structure dominant

## Why this analysis

F134's "next high-leverage action" memo identified BP-Bethe baseline
implementation as the structural pivot from heuristic CDCL+hints to
poly-time marginal computation. The proposed algorithm was BP-Bethe
with **level-4 cluster correction at gap-9/11**, predicted from the
Σ-Steiner Cayley graph analysis (principles framework).

The same memo identified a sub-30-min sanity check: count 4-cycles
in a real cascade_aux Tanner graph and verify the gap-9/11 cluster
prediction. That check was promised but not executed. F207 executes
it.

## Setup

Tool: `headline_hunt/bets/cascade_aux_encoding/encoders/tanner_4cycle_count.py`

Input: `aux_expose_sr60_n32_bit0_m8299b36f_fill80000000.cnf`
- 12596 variables, 52657 clauses
- Mean clause length 2.94, max 3 (cascade_aux is a 3-SAT encoding
  after BC + Tseitin)

A length-4 cycle in the variable-clause bipartite Tanner graph =
a pair of variables co-occurring in two clauses simultaneously.
Count = sum over var-pairs (v,w) of C(co_occur_count(v,w), 2).

Runtime: 0.04s parse + 0.04s cycle-count.

## Aggregate results

- **259,309 total 4-cycles**
- 39,500 distinct variable pairs participate
- Multiplicity histogram:

| Multiplicity | Pair count | 4-cycle contribution |
|---:|---:|---:|
| 2 | 8,041 | 8,041 |
| 3 | 64 | 192 |
| **4** | **27,752** | **166,512** (64% of total) |
| 5 | 1,339 | 13,390 |
| 6 | 1,908 | 28,620 |
| 9 | 3 | 108 |
| 10 | 74 | 3,330 |
| 14 | 64 | 5,824 |
| 16 | 189 | 22,680 |
| 18 | 64 | 9,792 |
| 20 | 1 | 190 |
| 36 | 1 | 630 |

Multiplicity-4 var-pairs dominate. The "level-4 cluster correction"
prediction matches the multiplicity distribution: most cycles live in
the multiplicity-4 component.

## Gap structure (the predicted gap-9/11 test)

For each 4-cycle-forming pair (v, w) with v < w, gap = w - v.

| Gap | Pair count | 4-cycle count |
|---:|---:|---:|
| 1 | 4,277 | 24,470 |
| 2 | 2,449 | 14,287 |
| 3 | 1,294 | 7,772 |
| 4 | 57 | 342 |
| **9** | **0** | **0** |
| 10 | 203 | 1,218 |
| **11** | **0** | **0** |
| 15 | 108 | 648 |
| 20-31 | scattered, 14-29 each | scattered, 100-200 each |
| **32** | **1,605** | **11,920** |
| 33 | 278 | 1,562 |

**Gap-9 and gap-11 have ZERO pair count.** The principles framework's
prediction that gap-9/11 multiplicity-2 4-cycles dominate is
**empirically falsified** for cascade_aux N=32.

## What the actual data shows

Three structural peaks:

### Peak 1: gap=1, 2, 3 (low-gap dominant)
8,020 pairs with low gap → 46,529 4-cycles (18% of total). These
correspond to **adjacent variables in the encoding's natural ordering**.
Likely reflect within-round variable interactions (carry adjacency,
local Σ/σ schedule).

### Peak 2: gap=32 (sharp word-boundary peak)
1,605 pairs at exactly gap=32 → 11,920 4-cycles. **N=32 = SHA-256
word size**. This is a quasi-cyclic structure aligned with the
8-word state vector (a, b, c, ...).

### Peak 3: high-multiplicity at gap=128
Top single pair: (var 2, var 130), multiplicity=36, gap=128 =
**4×32**. Several mult-18 pairs at gap=754 (also a multiple of 32).
This indicates **cross-word coupling at 4-word offsets** — likely
reflecting the SHA Σ rotation structure (Σ0 uses rotations 2, 13,
22; Σ1 uses 6, 11, 25 — gap=11 was predicted; **but gap=11 isn't
even present** because the encoded variable layout doesn't preserve
rotation gaps directly).

## Implications for BP-Bethe

The principles framework's level-4 cluster correction at gap-9/11
is **not the right algorithm** for cascade_aux Tanner graphs. The
correct cluster correction targets:

1. **Gap-1, 2, 3 short cycles**: highest-density local correction.
2. **Gap-32 word-aligned cycles**: structural coupling between
   adjacent SHA-256 words.
3. **Gap-128 (= 4×32) cross-word cycles**: the highest-multiplicity
   single pair lives here.

A revised BP-Bethe variant for cascade_aux would use:
- Level-2 generalization for gap-1-3 cycles (covers 18% of cycles).
- **Quasi-cyclic LDPC-style block decoding** for gap-32 structure
  (covers 5% of cycles, but well-aligned with the SHA architecture).
- Word-pair joint marginal at gap-128 for the 1 high-multiplicity
  pair.

This is a different algorithm shape than the principles framework's
prediction. Closer to standard quasi-cyclic LDPC decoding, which has
mature analysis (e.g., Ryan-Lin, "Channel Codes: Classical and
Modern", 2009).

## Implications for the principles framework

The framework predicted Σ-Steiner Cayley graph spectrum (gap-9/11
multiplicity-2) would transfer to cascade_aux Tanner graph. **It
does not.** The cascade_aux encoding's variable layout doesn't
preserve the Σ-Steiner gap structure — the encoding's auxiliary
variables and clause groupings dominate the cycle structure
instead.

Possible reasons:
1. The cascade_aux encoder uses a particular variable-numbering
   scheme that doesn't index by the Σ-Steiner index. Reordering
   variables by Σ-Steiner index might recover the predicted
   structure (worth testing).
2. The Tseitin auxiliary variables introduced for ITE / multi-XOR
   gates dominate the cycle structure. Removing them (e.g., by
   "fusing" Tseitin chains) might reveal the underlying
   Σ-Steiner structure.
3. The gap-9/11 prediction was wrong at the framework level,
   independent of the encoder.

Worth checking: does a smaller mini-SHA encoding (N=8) have the
same gap-32 dominance? If yes, structural property of cascade_aux.
If no (mini-SHA has gap-9/11 visible), then N=32 cascade_aux's
encoding obscures it via quasi-cyclic word structure.

## Concrete next probes

(a) Re-run F207 on N=8 mini-SHA cascade_aux CNF (if exists) to
    check whether gap-32 dominance is N-dependent or universal.

(b) Implement quasi-cyclic LDPC-style BP for gap-32 structure
    (more relevant algorithm than gap-9/11 cluster correction).

(c) Try variable reordering via Σ-Steiner index before computing
    gaps — see if the predicted gap-9/11 structure appears under
    the right indexing.

(d) Profile what the high-mult pairs (gap=128, mult=36) actually
    encode at the SHA-arithmetic level. Likely a specific
    schedule-or-Σ relationship.

## What's NOT being claimed

- That BP-Bethe is dead. The level-2 + quasi-cyclic + word-pair
  joint marginal variant might still work; it's a different
  algorithm shape than predicted.
- That the principles framework is wholly wrong. Just that its
  cluster-correction prediction at gap-9/11 doesn't transfer
  to cascade_aux N=32.
- That this analysis is sufficient to decide BP-Bethe direction.
  Need N=8 verification + variable-reordering check before
  committing to algorithm design.

## Discipline

- 0 SAT compute (pure structural analysis on existing CNF)
- 0 solver runs
- ~0.1s wall-time analysis
- 4 calibration findings + 1 retraction earlier in session;
  this is the day's first **structural** finding (not heuristic
  search calibration). Pivots the bet's strategic direction
  from "BP-Bethe at gap-9/11" to "quasi-cyclic LDPC-style
  decoder at gap-32 + adjacency".
