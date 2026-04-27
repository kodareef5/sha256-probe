# F12: 5-cand FULL 2^32 enumeration — cascade-1 path closed for all
**2026-04-26 20:14 EDT**

Built a C tool (`/tmp/deep_dig/de58_enum.c`, 626M evals/sec on M5,
40,000× Python). Used it to do FULL 2^32-chamber enumeration on the 5
cands of interest from F10/F11.

## Result: definitive cascade-1 elimination

For each of these 5 cands, **all 4,294,967,296 W57 chambers were
checked**. No sampling — exhaustive.

| cand | min HW | min HW W57 | min HW de58 | enum time |
|---|---:|---|---|---:|
| **cand_n32_msb_m189b13c7_fill80000000** | **2** | 0x303567fc | 0x00000108 | 7.3 s |
| cand_n32_bit13_m4e560940_fillaaaaaaaa | 3 | 0x7032b79b | 0x00102040 | 5.2 s |
| cand_n32_bit17_m427c281d_fill80000000 | 3 | 0x11ffa8d7 | 0x00080024 | 6.6 s |
| cand_n32_bit18_m99bf552b_fillffffffff | 4 | 0x000accaf | 0x02160000 | 4.6 s |
| cand_n32_bit19_m51ca0b34_fill55555555 | 11 | (any of 33M) | varied | 7.3 s |

**de58 = 0 count: 0 across all 5 cands × 2^32 = 21.5 BILLION chambers.**

Cascade-1 sr=61 collision is **definitively impossible** for these 5
cands. The minimum HW achievable is the structural barrier:
- msb_m189b13c7: 2 bits off (closest)
- bit13/bit17: 3 bits off
- bit18: 4 bits off
- bit19: 11 bits off (largest gap of fully-enumerated cands)

## C tool details

- Source: `/tmp/deep_dig/de58_enum.c`
- Compile: `gcc -O3 -march=native -o de58_enum de58_enum.c`
- Speed: 580–930M evals/sec on M5 (depends on cand-specific
  branch-prediction; bit18 hits 929 M/s)
- Modes: random sample (xorshift32, with seed) or full deterministic
  enumeration (seed=0, then iterates W57=0..nsamples-1)

## F12 100M registry screen (all 67 cands × 100M = 6.7B evals, ~10s total)

Per-cand 100M screen results, full table at
`headline_hunt/bets/cascade_aux_encoding/runs/20260426_f_series_n18/F12_registry_100M_screen.txt`.

Headline: **0/67 cands have de58=0 in 100M samples.** The 4 cands with
min HW ≤ 4 from this screen are the ones fully-enumerated above.

## Why msb_m189b13c7 is the structural champion

- Only **2 bits short** of cascade-1 collision-eligibility.
- min HW de58 value = 0x00000108 = 1<<3 + 1<<8 (bits 3 and 8 set).
- This cand has ~700k chambers with HW ≤ 5 (densest low-HW region of
  any registry cand at the F12 100M sample).
- If a "Sigma1/Ch/T2 chart-preserving operator" exists that can
  eliminate 2 specific de58 bits while preserving cascade-1, this
  cand is the natural target — only 2 bits of structural distance
  to close.

## Comparison to yale's HW4 D61 floor

Yale's singular_chamber_rank bet found D61 = HW4 across idx=0/8/17
via 8 attack vectors (E2 negative memo, commit d216961). The cands
they tested:
- idx=0 (msb_cert m=0x17149975) — F12 didn't fully-enumerate this;
  100M sample showed min HW = 8.
- idx=8 (m=0x33ec77ca) — F12 100M shows min HW = 5.
- idx=17 (m=0x28c09a5a) — F12 100M shows min HW = 9.

So yale's HW4 floor on idx=0/8/17 IS the de58 image's min HW for
those cands at 100M. **For msb_m189b13c7 that floor would be HW=2**
— 2 bits below yale's measured floor. If yale's chart-preserving
operator works, this cand is closer to a collision than any cand in
their current test set.

## Cross-bet messages out

- **Sent to yale** (commit f5e45a5): bit=17 m=0x427c281d as candidate
  — at 100M sample F12 measured min_HW=4, now at full 2^32 confirmed
  min_HW=3.
- **Update needed**: msb_m189b13c7 at min_HW=2 is the **best registry
  cand for chart-preserving operator probes**. Even closer than bit=17.

## Implications

1. **Cascade-1 sr=61 collision DEFINITIVELY NOT REACHABLE** for any
   of the 5 fully-enumerated cands.
2. The HW2 floor on msb_m189b13c7 is a hard structural barrier from
   cascade-1 alone — escaping it requires non-cascade-1 mechanisms.
3. Registry should mark these 5 cands (and any others with image fully
   enumerated) as `cascade1_sr61: definitively_eliminated` rather than
   `unknown`. This is a registry-level filter for which cands are
   even worth deeper search.
4. **Headline path**: msb_m189b13c7 is the structurally best registry
   cand. Yale's chart-preserving operator on this cand would have
   the smallest residual gap to close.

## Next steps

- **F13**: extend full 2^32 enumeration to ALL 67 cands. ~5-10s per
  cand × 67 = ~5-10 min total. Definitive registry-wide filter.
- **F14**: send msb_m189b13c7 specifically to yale's chart-preserving
  operator track as the closest target.
- **F15**: explore the 700k HW≤5 chambers of msb_m189b13c7. Is there
  a structural pattern in their W57 values? Could it predict the
  chart-preserving operator that eliminates the 2-bit residual?

EVIDENCE-level: VERIFIED for 5 fully-enumerated cands. Structural
fact: cascade-1 sr=61 unreachable for all 5. Open question: is this
true for all 67? F13 will tell us.
