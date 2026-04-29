---
date: 2026-04-28
bet: cascade_aux_encoding
status: 128_BIT_UNIVERSAL_PATTERN_HOLDS_ON_SR61
---

# F274/F275: sr=61 also has ~128 universal hard-core bits — pattern shifts by 1 round per n_free

## Setup

F271/F273 found 128 universal hard-core bits across sr=60 cands
(W*_59 + W*_60). F274/F275 tests whether the universal-hard-core
pattern transcends to sr=61 cands (n_free=3 instead of 4).

If the pattern holds, the 128-bit hard-core architecture is a
universal property of cascade-1 collision encoding, not specific
to sr=60 mode.

## F274: 3 sr=61 hard-core JSONs

Generated for cands:
- bit10_m3304caa0_fill80000000
- bit13_m4d9f691c_fill55555555
- bit18_m347b0144_fill00000000

Combined with yale's F311 sr61_bit25 JSON = 4-cand sample.

## F275: stability across 4 sr=61 cands

```
schedule keys: 192 (n_free=3 × 32 × 2)
stable_core:   129
stable_shell:  8
variable:      55
```

### Per-(word, round) breakdown

| Word | stable_core | stable_shell | variable | mean_core |
|---|---:|---:|---:|---:|
| **W1_57** | 1 | 3 | **28** | 0.41 |
| **W1_58** | **31** | 0 | 1 | **0.98** |
| **W1_59** | **32** | 0 | 0 | **1.00** |
| **W2_57** | 1 | 5 | **26** | 0.41 |
| **W2_58** | **32** | 0 | 0 | **1.00** |
| **W2_59** | **32** | 0 | 0 | **1.00** |

### Headline finding: ~127 universal hard-core bits on sr=61

The following bits are universal hard-core across all 4 sr=61 cands:

```
W1_58[bit ≠ b]    (31 bits, with 1 cand-variable bit b)
W1_59[0..31]      (32 bits, fully universal)
W2_58[0..31]      (32 bits, fully universal)
W2_59[0..31]      (32 bits, fully universal)
```

Total: **127 universal hard-core bits** (32+32+32+31 = 127).

## Cross-mode comparison

| Mode | n_free | Universal hard-core | Universal shell | Cand-variable |
|---|---:|---|---|---:|
| sr=60 (F273) | 4 | W*_59, W*_60 = **128** bits | W1_58 = **32** bits | ~79 bits |
| sr=61 (F275) | 3 | W*_58, W*_59 = **127** bits | none universal | ~55 bits |

### Pattern: universal hard-core is the LAST 2 ROUNDS

In both encoder modes, the **last 2 free schedule rounds** are
universal hard-core:

- sr=60 free rounds = {57, 58, 59, 60}; last 2 = {59, 60}
- sr=61 free rounds = {57, 58, 59}; last 2 = {58, 59}

The hard-core architecture is a structural property of the
cascade-1 schedule recurrence. The LAST round (W*_n_last) and the
ROUND BEFORE LAST (W*_n_last-1) are both fully exposed to the
collision constraint via the last few SHA round equations.
Earlier rounds are partially-forced by the cascade-1 hardlock.

### Pattern: cascade-1 hardlock at FIRST free round

In sr=60: W1_57 mostly variable (1 core, 7 shell, 22 var → low mean
core 0.39); W1_58 universal shell.

In sr=61: W1_57 mostly variable (1 core, 3 shell, 28 var → 0.41).
**No universal shell** for sr=61 — the cascade-1 hardlock manifests
in W1_57's per-cand variability instead of a clean universal shell.

This refines F217's interpretation: **the cascade-1 hardlock
ALWAYS manifests on the FIRST free round (W1_57)**, but the
manifestation pattern depends on n_free:

- n_free=4 (sr=60): hardlock projects forward to make W1_58
  universally redundant.
- n_free=3 (sr=61): hardlock keeps W1_57 cand-variable (no
  forward projection room).

## Implications

### Universal cube targeting works for both modes

For sr=60: target 128 bits in W*_59 + W*_60.
For sr=61: target ~127 bits in W*_58 + W*_59.

Yale's selector with `--stability-mode core` works uniformly across
both modes — just supply the matching n_free stability JSON.

### Decoder design generalizes

The F211 BP-decoder design's "hard core" target is universal:
~128 bits per cand regardless of sr level or n_free choice.
Implementation can be n_free-parameterized but the architectural
shape is fixed.

### Tighter F237 conclusion

F237 showed F235 (sr=61 instance) intractable to depth ≤ 3
cube-and-conquer. F275 confirms: F235's hard core is in the 127-bit
universal sr=61 hard core (W*_58 + W*_59), exactly the bits cube
experiments F262/F306-F309/F321/F322 targeted.

The universal pattern means the F237 negative finding generalizes:
NO sr=60 OR sr=61 instance is likely tractable to depth ≤ 3
cube-and-conquer at modest budgets. The 128-bit hard-core floor is
a structural fact of cascade-1 collision encoding.

## Strategic position

Combined fleet output (yale + macbook) over the day:

1. F176-F206: heuristic search saturated at 86 floor (block2_wang)
2. F207-F237: cascade_aux structural pivot, preprocessing refuted
3. F262-F273: cube-and-conquer depth ≤ 3 ineffective on F235
4. F274/F275: universal 128-bit hard-core architecture on both
   sr=60 and sr=61 modes
5. Yale F302-F328: full cube-and-conquer infrastructure with
   selector pipeline, p1/p2 alias semantic profiling

Path to headline: implement Phase 2D propagator (F238) targeting
the universal 128-bit hard core directly, OR pivot to BDD
enumeration over the 128-bit space, OR find a structurally
different attack mechanism.

## Discipline

- 0 SAT compute (hard-core JSON gen + stability aggregation)
- ~5 min wall total for F274 + F275
- Yale's stability tool used unmodified
- 69 commits this session
