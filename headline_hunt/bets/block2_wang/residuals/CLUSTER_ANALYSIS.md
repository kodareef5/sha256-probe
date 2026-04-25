# Block-1 Residual Corpus — cluster analysis

Analysis of the 104k-record `corpus_msb_200k_hw96.jsonl` for trail-design relevant patterns.

## Universal cascade signature: 100%

All 104,700 residuals have active-register pattern **[a, b, c, _, e, f, g, _]**
(d63 = h63 = 0 by cascade). Zero residuals deviate from this signature. The
cascade structure is rigid at this scale.

## Per-register HW distribution (across all residuals)

| Register | mean HW | median | min | max | std |
|---:|---:|---:|---:|---:|---:|
| a | 15.19 | 15 | 4 | 26 | 2.69 |
| b | 15.17 | 15 | 3 | 28 | 2.70 |
| c | 14.87 | 15 | 5 | 26 | 2.60 |
| e | 15.17 | 15 | 4 | 27 | 2.69 |
| f | 15.16 | 15 | 4 | 25 | 2.69 |
| g | 14.88 | 15 | 4 | 26 | 2.61 |

All 6 active registers have **near-identical** distributions — mean ~15 (close to
the binomial(32, 0.5) expectation of 16), std ~2.7. No register is structurally
"easier" than others. The cascade construction produces uniform-random-looking
residuals across active registers.

## Theorem 4 check at r=63

Theorem 4 of `writeups/sr60_sr61_boundary_proof.md` says **da = de at r ≥ 61**.
This is at round 61 specifically. At round 63, we'd expect drift due to the
2 additional rounds.

Empirical: **0/104,700 records have da63 == de63**. So Theorem 4 does NOT
extend to r=63 — the da/de divergence is observable.

## Lowest-HW residuals (Wang-target candidates)

| HW(da)+HW(de) | a | e | da63 | de63 | full HW63 [a,b,c,d,e,f,g,h] |
|---:|---:|---:|---|---|---|
| 15 | 8 | 7 | 0x0c819044 | 0x20410125 | [8,17,14,0,7,15,16,0] |
| 15 | 5 | 10 | 0x40010045 | 0xc00f3900 | [5,18,14,0,10,14,17,0] |
| 16 | 8 | 8 | 0x00b03890 | 0x04213302 | [8,13,16,0,8,18,15,0] |
| 16 | 9 | 7 | 0x810862a8 | 0x080181c1 | [9,18,18,0,7,18,17,0] |
| 16 | 7 | 9 | 0x088005c2 | 0x4042b190 | [7,14,18,0,9,18,16,0] |

The single record with HW(da)=4 (rare!): da63=0x00480204, de63=0x976b0fa1 (HW=17).

## Population summary

- HW(da63) ≤ 4: 1 record
- HW(da63) ≤ 6: 47 records
- HW(da63) ≤ 8: 633 records
- HW(da)+HW(de) ≤ 18: 51 records
- HW(da)+HW(de) ≤ 16: ~5 records

So **~50 records out of 104k are plausible Wang trail-search starting points**, where the (a, e) part of the residual is small enough to potentially be absorbed by a tailored block-2 differential. The OTHER 4 active registers (b, c, f, g) still carry HW ~14-18 each, so block-2 must absorb ~60+ HW total — still beyond classical Wang on full-round SHA-256.

## Implication for block2_wang

The bet's structural barrier holds:
- Random sampling at N=32 produces ~50 "low-(da, de)" records per 104k
- Classical Wang differential trails handle ~16-24 active bits in the IV diff
- Even our best records have HW > 60 across the 6 active registers
- (a, e) on its own at HW 15 is borderline-feasible; (b, c, f, g) at HW ~60 is the dominant barrier

**To make block2_wang work**, either:
1. **Find residuals with much lower TOTAL HW** (currently min ~60). Hill-climb on TOTAL HW, not just (a, e).
2. **Build a trail engine that absorbs HW=60 IV diff** — cutting-edge Wang-style work, multi-week project.
3. **Combine with cascade_aux_encoding** to constrain residual HW algebraically (extending force-mode to round 61 or 62).

## Saved artifact

`lowest_da_plus_de.jsonl` — top 50 records by HW(da)+HW(de) ascending. Each record carries (W1[57..60], state at round 63 for both messages, full HW per register). Trail-design starter pack.

## Status update

block2_wang stays `blocked` (per the earlier hill-climb negative). This cluster analysis reinforces the kill criterion: even the best 50 records out of 104k have full-residual HW well above Wang threshold. The bet awaits either a fundamentally different residual-finder or a custom trail engine that handles HW-60 absorptions.
