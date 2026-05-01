---
date: 2026-05-01
bet: block2_wang
status: PATH_C_BIT24_NEW_SUB_FLOOR_HW43
parent: F408 annealed bridge beam (codex), F427 bit28 seeded refinement
evidence_level: EVIDENCE
compute: 0 solver search; ~270s pure W-space annealing (3 cands parallel) + 2 audited cert-pin solver checks
author: macbook-claude (direct, no codex; codex still on quota wall)
---

# F428: multi-cand seeded refinement — bit24 breaks through to HW=43, bit3/bit2 confirm robust local optima

## Setup

Per F427's "decision points" recommendation: apply the seeded-refinement
pattern to the other three F408 panel candidates.

Three parallel anneals, each on its own core:

- bit3_m33ec77ca seeded from F408 HW=51 W1: `0xba476635, 0x8cf9982c, 0x0699c787, 0x8893274d`
- bit2_ma896ee41 seeded from F408 HW=51 W1: `0x504e056e, 0x3e435e29, 0xda594ea2, 0xe37c8fe1`
- bit24_mdc27e18c seeded from F408 HW=49 W1: `0x4be5074f, 0x429efff2, 0xe09458af, 0xd6560e70`

Per-cand parameters: 12 restarts × 200,000 iter × max_flips=3 × temp 0.5 → 0.01 × tabu 1024.

Total wall: ~270s (parallel; longest single run). 0 solver runs during search.

Artifacts:

- `headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F428_bit3_seeded_refinement.json`
- `headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F428_bit2_seeded_refinement.json`
- `headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F428_bit24_seeded_refinement.json`
- `headline_hunt/bets/block2_wang/results/20260501_F428_certpin_validation.json`

## Results

| Cand | F408 HW | F428 HW | Δ | F428 Score | Seeds at best |
|---|---:|---:|---:|---:|---:|
| bit3_m33ec77ca | 51 | 51 | 0 | 71.551 | 12 / 12 |
| bit2_ma896ee41 | 51 | 51 | 0 | 71.551 | 12 / 12 |
| **bit24_mdc27e18c** | **49** | **43** | **−6** | **79.073** | **12 / 12** |

**Bit24 broke through.** All 12 restarts converged to the same point at
HW=43, score=79.073 — a strong attractor that F408's wider search
missed at this radius.

## bit24 HW=43 witness

```
W1[57..60] = 0x4be5074f 0x429efff2 0xe09458af 0xe6560e70
W2[57..60] = 0x8b1bab38 0x9adf28be 0xa95e0159 0xde6759f9
hw63       = [14, 5, 1, 0, 14, 8, 1, 0]   (total 43)
diff63     = [0x78cc01b5, 0x0a240001, 0x20000000, 0x00000000,
              0xc125d48d, 0x06250181, 0x20000000, 0x00000000]
active_regs = {a,b,c,e,f,g}, da_eq_de=False, c=g=1, d=h=0
```

This W differs from F408's HW=49 witness only in `W1[60]`:

```
F408 W1[60] = 0xd6560e70   11010110 01010110 00001110 01110000
F428 W1[60] = 0xe6560e70   11100110 01010110 00001110 01110000
XOR         = 0x30000000   bits {28, 29}, Hamming distance 2
```

W57, W58, W59 are identical to F408. The improvement is purely a 2-bit
perturbation of W1[60] high bits (28, 29).

cascade2_offset(W2[60]) follows: 0xce6759f9 → 0xde6759f9 (1 bit flip,
position 28; correct cascade-1 propagation).

The bit-3 cascade-1 invariants hold: `s1_59[1..3] == s2_59[1..3]` and
`s1_60[4] == s2_60[4]`. Cascade fingerprint preserved.

## Cert-pin verification

Audited and cross-solver UNSAT:

- audit verdict: **CONFIRMED**
- cnf_sha256: `090c64434056fa2476d5a00d9337ef0bb020f9687fa38819e598fdd2a735fe26`
- kissat 4.0.4: **UNSAT** in 0.0085s
- cadical 3.0.0: **UNSAT** in 0.0139s

Both runs logged via append_run.py.

## Findings

### Finding 1: bit24's local optimum at F408 was 2 W-bits off the global

F408 found bit24 HW=49 with W1[60]=0xd6560e70. F428's seeded refinement
at 3-bit flip radius found a strictly better neighbor at distance 2
(W1[60] bits 28+29 flipped) where HW drops by 6. F408's wider search
(max_flips=6) and 12-seed run did NOT find this point — likely because
the wider mutation radius drove the search out of the local
neighborhood and the global escape was a narrow 2-bit basin.

This is concrete evidence that **a tighter seeded second pass can find
records the wider first pass missed**, when the first-pass best is in a
small basin near a still-deeper one.

### Finding 2: bit3 and bit2 are at robust local optima at this radius

For both cands, all 12/12 seeds converged exactly back to F408's HW=51
witness with no improvement. The bridge selector + cascade-1 invariants
fence the search tightly around F408's HW=51, and no HW<51 exists at
3-bit flip radius.

This matches F427's bit28 finding (HW=45 robust at 3-bit radius). Three
out of four F408 panel cands have this same "F408 best is locally
unbeatable at 3-bit radius" structure. The bit24 breakthrough is the
exception.

### Finding 3: when F428 finds an escape, the basin of attraction is uniform

For bit24, all 12 independent random-seeded restarts converged to the
*same* HW=43 W. This is a very strong attractor — the bridge-score gradient
points sharply and uniformly toward this point from any of the random walks
under the F408 init. Combined with the 2-bit Hamming distance, this means
F408's HW=49 was sitting on the *edge* of the HW=43 basin, separated by
exactly 2 W-bit flips.

### Finding 4: corpus state after F428

| Cand | Pre-F408 | F408 | F428 | Total Δ |
|---|---:|---:|---:|---:|
| bit3 | 55 | 51 | 51 | −4 |
| bit2 | 56 / 57 | 51 | 51 | −5 / −6 |
| bit24 | 57 | 49 | **43** | **−14** |
| bit28 | 59 | 45 | 45 | −14 |

F408 first pass + F427/F428 seeded refinements have produced two
deep-tail HW=43 and HW=45 records on the bit24 and bit28 candidates,
both >12 points below their pre-F408 corpus floors.

## Verdict

- **Primary objective (HW reduction)**: bit24 HW 49 → 43 achieved.
- **Cert-pin headline-class SAT**: not achieved (UNSAT, expected at HW>0).
- **Structural pattern**: seeded second-pass with tighter radius is the
  right tool to localize sub-floor records when the first pass found
  the right basin's edge.
- **Registry**: 0 errors / 0 warnings; 2 new audited runs logged;
  audit-failure-rate unchanged at 0.0%.

## Next

1. **Wider second-anneal on bit3/bit2/bit28** at radius 4-6 starting
   from F428 HW=51 / F427 HW=45. Test whether, like bit24 at radius 2,
   a wider radius reveals a HW < current basin via specifically
   2- or 4-bit W1[60] flips. ~10 min compute.
2. **Try the "W1[60] only" search** as a focused experiment: each cand
   has had its breakthrough or near-breakthrough be a small W1[60]
   perturbation. A direct enumeration over W1[60]'s 2^32 values may be
   feasible if combined with cascade-1 + bridge filters; for each
   cand, test all single-bit, two-bit, and three-bit flips of W1[60]
   from current best. ~30 min compute, deterministic.
3. **Bridge_score mechanism**: F427 found a score-better/HW-worse W
   for bit28 (3-bit W1[60] flip). F428 found a score-better/HW-better
   W for bit24 (2-bit W1[60] flip). A direct ablation of bridge_score's
   reward terms would clarify whether the c/g asymmetry term
   (or the dominator-bit term) drives the breakthrough.
4. **bit13_m916a56aa**: this cand was in F378 as the "surprise top-1"
   control but never had a seeded refinement. Try one. ~3 min.

The W1[60] dominance across all four breakthroughs (F408 wide-search
discoveries plus F428 narrow-search refinement on bit24) is suggestive
that block-2 absorption's residual surface lives primarily in W[60]'s
bit pattern, not in W57/58/59. This would be consistent with W[60]'s
role as the last fully-unconstrained schedule word before W[61..63]
become message-extension-determined.
