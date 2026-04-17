# Cascade Absorption Pattern: diff_regs = 6→5→4→3→2→1→0

**Date**: 2026-04-16 ~23:00 UTC
**Evidence level**: VERIFIED (from the known N=32 sr=60 collision)

## Discovery

The N=32 sr=60 collision (M[0]=0x17149975, fill=0xff, MSB kernel) shows
a perfect linear decrease in the number of differing registers:

| Round | diff_regs | da | Notes |
|-------|-----------|-----|-------|
| 56    | 7/8       | 0x00000000 | Cascade candidate: only a-reg matches |
| 57    | 6/8       | 0x00000000 | Cascade round 1: b absorbs da56=0 |
| 58    | 5/8       | 0x00000000 | Cascade round 2: c absorbs |
| 59    | 4/8       | 0x00000000 | Cascade round 3: d absorbs |
| 60    | 3/8       | 0x00000000 | Cascade round 4: e absorbs (dd→0) |
| 61    | 2/8       | 0x00000000 | Schedule round: f,g absorb |
| 62    | 1/8       | 0x00000000 | Schedule round: g absorbs |
| 63    | 0/8       | 0x00000000 | **COLLISION** |

## Mechanism

The shift register (a,b,c,d) = (T1+T2, a_prev, b_prev, c_prev) acts as
a delay line. The cascade (da=0 at each round) feeds "zero diff" into
position a, which shifts through b→c→d over 3 rounds.

Similarly, (e,f,g,h) = (d+T1, e_prev, f_prev, g_prev) shifts the
pre-cascade diffs out through h over 4 rounds.

After 7 rounds: all pre-cascade state56 diffs have shifted out through h,
and da=0 has filled the entire register file.

This is why the cascade needs exactly 7 rounds (the SHA-256 register
file has 8 positions, and the shift register absorbs 1 diff per round,
starting with 7 non-zero diffs at round 56 [only a is zero]).

## Key Property: da=0 holds at ALL 7 rounds

The cascade directly enforces da=0 at rounds 57-60 (via free words).
But da=0 ALSO holds at rounds 61-63 (schedule-determined words)!

This is because the SAT solver found W[57]-W[60] values that make the
ENTIRE 7-round computation consistent. It's not a coincidence — the
cascade structure propagates through the schedule words.

## sr=61 Schedule Mismatch

| Quantity | Value |
|----------|-------|
| W1[60] collision | 0xb6befe82 |
| W1[60] schedule  | 0x7d4ed9a5 |
| XOR mismatch     | 0xcbf02727 (hw=17) |
| Modular distance | 963,650,781 (~2^30) |

The mismatch is essentially random (expected hw≈16 for random 32-bit XOR).
The sr=60 collision's W[60] has no special relationship to the schedule value.

## Multi-Block Analysis

Since the sr=60 collision produces state_63_msg1 = state_63_msg2,
the Merkle-Damgård feedforward gives:

  H_1 = IV + state_63 (same for both messages)
  dH = 0

**The sr=60 collision IS a hash collision for the compress function.**
No block-2 cancellation is needed — the issue is purely schedule compliance
(W[57]-W[60] don't follow the message schedule).

## Implications

1. The cascade is a PERFECT mechanism for absorbing register diffs through
   the shift register. 7 rounds suffices because 8 registers - 1 (da=0) = 7.

2. For sr=61 (3 free words), the absorption has 6 rounds instead of 7.
   But da=0 must also hold at rounds 61-63, which requires W[61]-W[63]
   (schedule-determined) to produce zero T1-diff. This is the hard constraint.

3. The 17-bit schedule mismatch means the sr=60 collision is "maximally far"
   from sr=61 compatibility. Finding an sr=61 collision requires a completely
   different set of W[57]-W[59] values, not a small perturbation.

4. Multi-block attacks don't help because the sr=60 collision already has dH=0.
   The bottleneck is schedule compliance, which is the same for single or multi-block.
