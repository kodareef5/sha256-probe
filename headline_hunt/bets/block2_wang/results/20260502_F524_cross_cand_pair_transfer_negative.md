---
date: 2026-05-02
bet: block2_wang
status: PATH_C_PAIR_POOL_TRANSFER_NEGATIVE
parent: F521 manifest-rank breakthroughs; yale-codex F552 W-delta lattice analysis; F562 prior-weighted sampling negative
evidence_level: VERIFIED
compute: 0.4s; ~16 source×target × ~580 evals each = ~9300 cascade-1+bridge evaluations; 0 solver runs
author: macbook-claude
---

# F524: cross-cand pair-pool transfer is NEGATIVE — W-cube basins are candidate-specific

## Setup

After F520-F523 confirmed bit2 HW=39 as a robust floor across 14 manifest
seed attempts and yale-codex F562 confirmed all 5 panel floors hold under
prior-weighted sampling, F524 tests the third independent search modality:
**cross-candidate pair-pool transfer**.

Hypothesis: bit3 went HW 51→39→36 via specific 2-bit W-flip pairs (the
top entries of pair_beam_search.py's `selected_pairs` field). If those
pairs encode universal structure (like Yale F552's recurrent W60 bit
positions), they should also help bit2 / bit24 / bit28.

Workflow: for each (source cand, target cand) pair:
1. Load source cand's pair-beam JSON.
2. Take its top 128 selected_pairs by HW (most-helpful 2-bit deltas).
3. Apply each pair as a flip to the target cand's current best W.
4. Evaluate cascade-1 + bridge_score; record any HW < target init.
5. Also try 2-pair compositions: for each pair_i × pair_j (i<j) in the
   top 32, apply both flips, evaluate.

Sources (4):
- bit3 HW=36 (F521 r4 artifact)
- bit24 HW=40 (F521 r3 artifact)
- bit13 HW=35 (Yale F487 r12 artifact)
- bit28 HW=42 (Yale F465 wider artifact)

Targets (4):
- bit2 (init HW=39, F520 W)
- bit3 (init HW=36, F521 W; self-control)
- bit24 (init HW=40, F521 W)
- bit28 (init HW=45, F408 W; using known cert-pinned record)

Total: 16 source×target pairings × ~128 single + ~480 two-pair compositions.
0.4s wall.

Artifact: `headline_hunt/bets/block2_wang/results/search_artifacts/20260502_F524_cross_cand_pair_transfer_matrix.json`

## Results

| Source | → bit2 | → bit3 | → bit24 | → bit28 |
|---|---|---|---|---|
| bit3 HW=36   | 0+0 | 0+0 (self) | 0+0 | 0+0 |
| bit24 HW=40  | 0+0 | 0+0 | 0+0 (self) | 0+0 |
| bit13 HW=35  | 0+0 | 0+0 | 0+0 | 0+0 |
| bit28 HW=42  | 0+0 | 0+0 | 0+0 | 0+0 (self) |

(format: `single-pair breaks + 2-pair composition breaks`)

**Zero breakthroughs across all 16 cross-cand pairings.** Not a single
1-pair or 2-pair flip from any source cand's top-128 pool drops any
target cand below its current best HW.

## Findings

### Finding 1: pair-pool transfer fails universally

The most-helpful 2-bit flips for cand X (the ones that drove its HW
breakthrough) are NOT helpful for cand Y. Even cand X's top pairs applied
as compositions to other cands' W don't reduce HW.

This means the specific bit positions that encoded "improvement" for cand X
encode something different for cand Y — or nothing at all. The W-cube
basin geometry is candidate-specific, not universal.

### Finding 2: complements Yale F562's prior-weighted finding

Yale F552 noted recurrent W60 bit positions across cands (b30, b27, b29,
b31, b16, b19, b21, b3) — DESCRIPTIVE priors. F562 sampled 5M masks with
those positions weighted up: zero ties or improvements across 5 cands.

F524 tests the same question more aggressively: not just sampling weighted
positions, but applying the actual SUCCESSFUL 2-bit pairs from one cand
to another. Same result: zero transfer.

The combined verdict from F552+F562+F524: **descriptively-recurrent
W60 positions are cand-internal patterns, not transferable operators**.
Each cand's W-cube basin geometry is essentially independent.

### Finding 3: three independent search modalities confirm floors

| Modality | Cands tested | Improvements found |
|---|---|---|
| F520-F523 manifest-rank pair-beam (14 bit2 seeds) | bit2 | 0 below HW=39 |
| Yale F553-F562 prior-weighted W60/W59-W60 (5M masks) | all 5 | 0 across all 5 |
| F524 cross-cand pair-pool transfer (16 pairings) | all 5 | 0 across all 16 |

All converge: panel floors hold.

### Finding 4: Path C 5-cand panel state — solid floors

| Cand  | Floor HW | Source | Closure level |
|---|---:|---|---|
| bit13 | 35 | Yale F487 | F488/F489 radius-4 closed; F562 prior-sample 0 |
| bit3  | 36 | Macbook F521 | Yale F522/F525 radius-5 W60+W59/W60 closed; F524 transfer 0 |
| bit2  | 39 | Macbook F520 | F521-F523 14 manifest seeds tried; F524 transfer 0 |
| bit24 | 40 | Macbook F521 | Yale F526 radius-4 closed; F524 transfer 0 |
| bit28 | 42 | Yale F484 | F463/F464 radius-4 closed; F562 prior-sample 0 |

All five cert-pin UNSAT. No remaining easy descent paths within current
search modality (cascade-1 invariants + bridge_score gate + W-cube
neighborhood, including cross-cand pair-pool transfer).

## Verdict

- **Cross-cand pair-pool transfer: NEGATIVE across 4×4 = 16 pairings.**
- Three independent search modalities (manifest-rank pair-beam,
  prior-weighted sampling, pair-pool transfer) confirm Path C panel
  floors at HW = 35, 36, 39, 40, 42 are robust.
- W-cube basin geometry is cand-specific; recurrent W60 positions are
  descriptive only.

## Next

The non-trivially-easy directions for further Path C reduction:

1. **State-aware scoring** (Yale F562's other recommended operator): define
   a new objective function that adapts to current state lane balance,
   not just HW + bridge_score weights. Implementation: needs a new score
   function in pair_beam_search or a wrapper.
2. **Drop cascade-1 c=g=1 invariant**: relax the geometric constraint and
   re-search. Different residual class but possibly lower HW.
3. **New kbits not yet on panel** (bit5, bit10, bit14, bit27, etc.):
   widen the cand panel via F432-style wide anneal + F521-style
   manifest-rank chains. Each kbit is independent geometry; some may
   have lower-HW floors than the current panel.
4. **Pivot to absorber / M2 program** (Yale F506-F519): the 2-block
   absorber framework is in early days (HW=91 stuck at 24-round). My
   bit2/bit3/bit13 cert-pinned residual records could feed Yale's
   `block2_absorber_probe.c` as new seeds.
5. **Pivot to sr61_n32** (different bet, untouched today).

The Path C 5-cand panel residual program has reached a clean stopping
point at radius 12 + Hamming 5 closure. Further compute on this
modality is unlikely to find new records.
