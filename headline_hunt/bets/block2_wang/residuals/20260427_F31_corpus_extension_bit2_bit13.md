# F31: Corpus extension — bit2_ma896ee41 (PRIMARY) + bit13_m4e560940 (SECONDARY)
**2026-04-27 07:18 EDT**

Acts on F28's explicit next_action: extend block2_wang residual corpus
to F28's NEW CHAMPION (bit2_ma896ee41) and exact-symmetry runner-up
(bit13_m4e560940).

Prior corpora were msb-only:
- corpus_m189b13c7_fill80000000.jsonl (3787 records, HW≤80)
- corpus_m9cfea9ce_fill00000000.jsonl (3735 records, HW≤80)

## New corpora

| cand | records | HW range | min HW (this run, 1M) | F28 min HW (1B definitive) |
|---|---:|---|---:|---:|
| **cand_n32_bit2_ma896ee41_fillffffffff** | 18,336 | 57..80 | 57 | **45** |
| cand_n32_bit13_m4e560940_fillaaaaaaaa | 18,548 | 61..80 | 61 | 47 |

Both via build_corpus.py: 1M samples, threshold=80, seed=42. ~56s
each. Cascade-1 hit rate 100% (all samples cascade-eligible because the
script enforces the cascade-1 conditions inside run_full).

## Per-HW distinct-vector counts

### bit2_ma896ee41 (HW 57..70 head)

| HW | samples | distinct |
|---:|---:|---:|
| 57 | 1 | 1 |
| 60 | 1 | 1 |
| 62 | 1 | 1 |
| 63 | 5 | 5 |
| 64 | 5 | 5 |
| 65 | 18 | 18 |
| 66 | 26 | 26 |
| 67 | 23 | 23 |
| 68 | 52 | 52 |
| 69 | 100 | 100 |
| 70 | 132 | 132 |

### bit13_m4e560940 (HW 61..70 head)

| HW | samples | distinct |
|---:|---:|---:|
| 61 | 1 | 1 |
| 62 | 1 | 1 |
| 63 | 5 | 5 |
| 64 | 5 | 5 |
| 65 | 7 | 7 |
| 66 | 15 | 15 |
| 67 | 39 | 39 |
| 68 | 50 | 50 |
| 69 | 69 | 69 |
| 70 | 131 | 131 |

**100% distinct at every observed HW level for both cands.** Consistent
with F25's "1 distinct vector at min HW" finding — at 1M samples the
landscape is too sparse for repeats; the min-HW vector hasn't been
hit yet (would need 1B+ per F28).

## Sampling-budget gap

| budget | bit2 min HW | bit13 min HW |
|---|---:|---:|
| 1M (this run) | 57 | 61 |
| 1B (F28) | 45 | 47 |

The 12-bit gap from 1M to 1B sample budgets shows that the **deep
minimum is statistically rare**. At 1M, we sample only the "head" of
the residual distribution — useful for clustering analysis but does
NOT reach the structurally-significant min-HW vector.

For Wang-style trail search, we want residuals near the true min
(within HW + ε). To get there from random sampling, need 1B+ samples.
The block2_lowhw_set.c C tool (43M iter/sec) can produce this in
~25 seconds per cand; build_corpus.py (Python, 17.8k samples/sec)
would take ~16 hours per cand.

## What this corpus IS for

The 1M corpus is useful for:
- **HW-distribution comparison** across cands (bit2 has lower head HW)
- **Clustering by active-register set** (which (a,b,c,e,f,g) registers
  are non-zero, etc.)
- **Sanity baseline** — does kissat behave differently on
  per-cand "natural" residual distribution at non-deep HW?

The 1M corpus is NOT for:
- Min-HW residual analysis (use F28 1B-deep results)
- Wang trail enumeration on truly minimal residuals (too few low-HW
  samples in 1M)
- Symmetry validation at min HW (no min-HW vectors in this corpus)

## Cross-cand HW head comparison

| cand | min HW @ 1M | HW=65 distinct count |
|---|---:|---:|
| msb_m189b13c7 (legacy corpus) | ~75 | (full corpus dist below) |
| msb_m9cfea9ce (legacy corpus) | ~70 | (full corpus dist below) |
| **bit2_ma896ee41** (new) | **57** | 18 |
| bit13_m4e560940 (new) | 61 | 7 |

**bit2 finds lower-HW residuals at 1M than bit13** — consistent with
F28's deep-min ranking (bit2 HW=45 < bit13 HW=47). Even at moderate
sample budgets, the structural ranking is preserved.

## Implication for block2_wang trail design

The corpus gives us 18k+ low-HW (HW 57-80 for bit2, 61-80 for bit13)
distinct residual vectors per cand. Each is a Wang-style "absorb-this"
target for a hypothetical second-block trail.

Per-cand strategy:
1. Pick a low-HW residual (e.g., bit2 HW=57 or HW=63 cluster)
2. Design a second-block differential trail that ends with the
   negation of this residual
3. Probability cost ~ 2^-HW × per-bit-cost
4. Apply Wang-style message modification to satisfy bitconditions
5. Iterate over the corpus to find the residual with shortest trail

For bit2's HW=45 deep min, the absorption probability is ~ 2^-45 (best
case, if every bit independent). Naive: 2^209 expected solutions in
the 256-bit second-block freedom. Per F30 result, NEEDS deep-budget
testing to see if the structural advantage shows in practice.

## Discipline

- Files at `headline_hunt/bets/block2_wang/residuals/by_candidate/`
- Both 18k+ records, JSONL one-per-line
- Reproducible: `build_corpus.py --m0 0xa896ee41 --fill 0xffffffff
  --kernel-bit 2 --samples 1000000 --hw-threshold 80 --seed 42`
- Compute cost: ~56s per cand on Apple M5 (Python)

EVIDENCE-level: VERIFIED at 1M samples. Both files written, distinct
vector counts confirmed, HW distributions logged.

## Next concrete moves

1. **C-tool corpus generator**: port build_corpus.py to C (block2_corpus.c)
   to enable 1B-sample corpora in ~25 sec/cand. Would extend bit2 corpus
   down to HW=45 with hundreds of distinct vectors.
2. **Cluster analysis**: which (active_register_set, hw_per_register)
   pairs dominate? Does bit2 favor a specific cluster?
3. **Trail-search pilot**: pick one bit2 HW=63 vector, attempt
   second-block trail design via Wang-style backward construction.
