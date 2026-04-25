# M12 milestone result: TBD — (template, fill in when run completes)
**Started**: 2026-04-25 evening, macbook (M5, 4P+6E cores).
**Run command**: `backward_construct_n12` with M5-targeted `-mcpu=apple-m4` build.
**Status**: IN PROGRESS as of writeup. Update this file when complete.

## Pre-run predictions (from M10 + N=8 baseline)

Predicted N=12 outcomes from extrapolating N=8 (17.12×) and N=10 (15.67×) speedup:
- Speedup factor: ~14× (decay rate ~0.92 per N-bit increment)
- Wall on 10 threads: ~7,500s ≈ 2 hours (extrapolated from N=10's 117s × 64)
- Outer triples: 2^36 = 68B
- de61 hits: ~2^36 / 2^N = ~2^36 / 4096 = ~16M? No wait, the rate at N=10 was 1/2^N of inner+outer = 1.07B / 1.07B = ~1. Empirically pass rate is 1 hit per 256 = 1/2^8 in inner-plus-outer ratio at N=10. At N=12, expected pass rate is 1/2^N = 1/4096? Or is it the same 1/256?

  Re-derive: at N=10 we had 2^30 outer × 2^10 inner = 2^40 total operations,
  1.07B = 2^30 de61 hits. So hit rate per (outer × inner) op = 2^30 / 2^40 = 2^-10 = 1/1024.
  At N=8: 16,211,828 hits / (2^24 × 2^8) = 2^24 / 2^32 = 2^-8 = 1/256.
  Wait that contradicts. Let me re-check.

  Actually at N=8: 16M hits on ~16M outer triples (2^24) × 256 inner = 2^32 total trials.
  hits/trials = 16M/4G = 1/256 = 2^-8. OK 2^-N.
  At N=10: 1.07B hits / (2^30 × 2^10) = 2^30 / 2^40 = 2^-10. Also 2^-N. ✓
  At N=12: predict hits = 2^36 × 2^12 × 2^-12 = 2^36 = 68B.
- Collisions found: scaling argument predicts O(2^(3N)) collisions for full
  cascade-DP problem; at N=10 we saw 946. At N=12: expect ~2^(3×12) / 2^(3×10) × 946 ≈ 64 × 946 ≈ 60,000 collisions.

  But the algorithm finds all of them; only constrained by buffer size
  (currently 4096 in source). **WARNING**: the BC binary may truncate
  output at 4096 collisions. Need to verify or increase buffer.

## Result (fill in)

```
M[0]=0x[?], fill=0x[?], MSB kernel (auto-discovered, N=12)
da56=0: verified

Phase 1: SKIPPED (N=12 outer 2^48 intractable; ~30 hr single-thread BF)
Phase 2:
  Collisions found:     [?]  (NOTE: capped at 4096 if hit; if exactly 4096 → buffer overflow)
  de61=0 hits:          [?]
  Triples evaluated:    68,719,476,736 (2^36)
  Time:                 [?] s on 10 OpenMP threads (CONTENDED with de58 validation matrix Phase B)
Phase 4:
  Verified:             [?] / [?]
```

## Decision gate (M12 from SCALING_PLAN.md)

Required:
- ✅ / ❌ Speedup factor ≥ 4× over brute force (extrapolated benchmark)
- ✅ / ❌ Per-tuple work bounded by O(N × constant)
- ✅ / ❌ 4-d.o.f. residual variety predicts collision count to within 2× factor

Decision: TBD

## What this validates / kills

- If M12 PASSES: algorithm scales correctly through 8→10→12. Algorithmic feasibility ladder cleared at mid-N. Next gate is M16 (algorithm fits or doesn't).
- If M12 FAILS on per-tuple work growth: redirect bet to MITM-only approach; backward-construction overhead would dominate.
- If M12 hits buffer cap at 4096: increase buffer in source (cheap fix), re-run, but counts may already be enough for validation.

## Caveat

Wall time at M12 is CONTENDED — running concurrently with the de58 validation
matrix Phase B (kissat/cadical 10M-conflict runs). Wall numbers should be
treated as upper bounds on true M12 wall. Re-run with clean CPU to get
clean speedup numbers if needed.

## Files

- `backward_construct_n12.c` — source (compiled with `-mcpu=apple-m4 -mtune=apple-m4`)
- `backward_construct_n12` — binary (51KB)
- `M12_RESULT_template.md` — this file (rename to M12_RESULT.md when filled)
