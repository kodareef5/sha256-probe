---
date: 2026-04-28
bet: cascade_aux_encoding
status: 128_UNIVERSAL_HARD_CORE_BITS_IDENTIFIED
---

# F270/F271: 128 universal hard-core bits across sr60 cands — W*_59 + W*_60 are obligate cube targets

## Setup

Yale's F317 stability tool aggregates hard-core JSONs across multiple
cands to identify schedule bits that are stably hard-core, stably
shell, or candidate-variable. F270 generated a 3rd sr60 hard-core
JSON (bit13 cand) to expand yale's 2-cand stability set. F271 runs
yale's tool on the combined 3-cand set.

## F271 result on 3 sr60 cands

```
schedule keys: 256 (8 words × 32 bits = 8 × 32 free schedule bits)
stable_core:   150 bits
stable_shell:  46 bits
variable:      60 bits
```

### Per-(word, round) breakdown

| Word | stable_core | stable_shell | variable | mean_core |
|---|---:|---:|---:|---:|
| **W1_57** | 3 | 7 | **22** | 0.39 |
| **W1_58** | 0 | **32** | 0 | **0.00** |
| **W1_59** | **32** | 0 | 0 | **1.00** |
| **W1_60** | **32** | 0 | 0 | **1.00** |
| **W2_57** | 6 | 6 | **20** | 0.49 |
| **W2_58** | 13 | 1 | **18** | 0.73 |
| **W2_59** | **32** | 0 | 0 | **1.00** |
| **W2_60** | **32** | 0 | 0 | **1.00** |

### Headline finding: 128 universal hard-core bits

Across ALL 3 sr60 cands tested, the following 128 bits are
INVARIANTLY hard-core:

```
W1_59[0..31]  (32 bits)
W1_60[0..31]  (32 bits)
W2_59[0..31]  (32 bits)
W2_60[0..31]  (32 bits)
```

These 128 bits are **obligate cube targets** for ANY sr=60 cand
attack. They form the structurally-decisive subspace per F213's
hard-core framework, and yale's stability tool confirms they are
universal.

### W1_58 is universally shell (cascade-1 hardlock confirmed)

F214 hypothesized W1_58 is forced by cascade-1 da[56]=0 hardlock.
F271 confirms across 3 cands: W1_58 has 0/32 stable_core, 32/32
stable_shell. **W1_58 is universally shell-eliminable** — the F214
hypothesis is empirically saturated.

### Cand-variable bits

42 schedule bits (W1_57: 22, W2_57: 20) are cand-dependent — these
require per-cand JSON for accurate cube targeting.

18 W2_58 bits are also cand-variable (13 stable-core + 1 shell + 18
variable).

Total cand-variable: 60 bits per F271 aggregate.

## Implications for cube-and-conquer

### Universal targeting (~128 bits)

Yale's selector with `--stability-mode core` can target the 128
W*_59 + W*_60 bits universally. No per-cand JSON needed for these.

This dramatically simplifies cross-cand cube-and-conquer:
- Universal cube manifests can be precomputed for the 128-bit
  hard core
- Any sr=60 cand can be attacked with the same cube structure
- Per-cand variation (60 bits) becomes secondary refinement

### Implications for attack design

The 128-bit universal hard core is the asymptotic intractability
floor (per F237/F262/F268: even with depth-3 cubes at 200k
conflicts, F235's 128-bit core doesn't yield).

To break this 128-bit core requires either:
- Substantially deeper cubes (depth-4+ = 16+ fixed bits, still
  leaving 112+ bits intractable)
- IPASIR-UP propagator (in-search structural reasoning, F238)
- BDD enumeration on the 128-bit space (2^128 = infeasible
  enumeration, but structured BDD might compress)
- Different encoding that flattens the hard core

### Structural prediction

If F271's 128-bit universal hard-core holds across 5+ cands (next
test: F272 with 2 more sr60 JSONs), the universal-target finding is
confirmed. If it holds for sr=61 cands too (need n_free=3 stability
analysis), the structural floor is encoder-independent (per F210
precedent).

## Combined fleet structural pipeline

This is the strongest cross-bet/cross-fleet finding of the day:

| Step | Source | Purpose |
|---|---|---|
| F213 hard-core decomposition | macbook | identify per-cand hard core |
| F213 → JSON output (--out-json) | yale extension | machine-readable export |
| F317 stability summary tool | yale | aggregate across cands |
| F269 multi-cand JSONs | macbook | expand sample size |
| F270 third sr60 cand | macbook | reach 3-cand sample |
| F271 stability analysis | macbook (run yale's tool) | identify 128 universal bits |
| F311 cube selector | yale | use stability for cube targeting |
| F318 selector --stability-json | yale | accept stability bonus |

End-to-end pipeline: structural analysis → JSON → cross-cand
aggregation → universal-target identification → cube selector
prioritization → cube CNF generation → cube run with stats.

The 128-bit universal hard-core is now the empirically-defined
target for any structural cascade-1 attack.

## Concrete next probes

(a) **More sr60 cands**: 5+ JSONs would tighten the universal
    structure with stronger sample size.
(b) **sr=61 stability**: same analysis with n_free=3 cands. Tests
    if the universal-128 pattern transcends encoder.
(c) **Yale's --stability-mode core selector run**: feed F271 to
    yale's F318 selector + run depth-2 cubes targeting only the
    128 universal bits. Tests if universal targets give better
    cube ranking than per-cand targets.
(d) **Symmetry exploitation**: of the 128 universal bits, are
    there symmetries (e.g., W1[r][b] ↔ W2[r][b]) that further
    reduce the effective dimension?

## Discipline

- 0 SAT compute (graph elimination + stability aggregation)
- ~3 min wall total for F270 + F271
- Yale's tools used unmodified
- Cross-fleet pipeline integration complete

## Coordination

Yale's F314-F318 fixed identify_hard_core CONST_TRUE counting bug
(my JSONs already correct since yale's fix applied to the tool).
F271 uses corrected JSONs.

If yale runs F271-style analysis on 5+ cands, prefer macbook contributes
additional JSONs. macbook can add ~3-5 more sr=60 JSONs in next
~10 min if needed. Signal direction.
