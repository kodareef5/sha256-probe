# block2_wang residual scan — bit13_m4e560940 is structurally lowest
**2026-04-26 21:18 EDT (sourced from cross-bet F12 work)**

100M random (W1[57..60]) samples per cand under cascade-1 + cascade-2
enforcement, forwarded through rounds 61-63 with schedule extension.
Tracked min residual HW (sum across 8 registers of state difference at
slot 64).

## Result

| cand | min residual HW @100M | min-HW W1[57..60] |
|---|---:|---|
| **cand_n32_bit13_m4e560940_fillaaaaaaaa** | **47** | 0xaffb9373 / 0x6f262a99 / 0xe4deabc3 / 0x057cb110 |
| cand_n32_msb_m189b13c7_fill80000000 | 51 | 0x033939d8 / 0xa44750f9 / 0x8552ad75 / 0xcf70c46b |
| cand_n32_msb_m17149975_fillffffffff (verified sr=60) | 53 | 0x7e59c538 / 0x99222ea7 / 0x4222bb5c / 0xbc6f0ef8 |
| cand_n32_bit17_m427c281d_fill80000000 | 54 | 0x49ad55fa / 0x815eea13 / 0xdf8827bd / 0xb482aa42 |
| cand_n32_bit18_m99bf552b_fillffffffff | 54 | 0xdd9b8918 / 0x3ba337c4 / 0xf628b449 / 0xf49d6739 |
| cand_n32_bit19_m51ca0b34_fill55555555 | 54 | 0x96373cd3 / 0x4401e4a5 / 0x6a3a650f / 0xf5e95e02 |

## Why bit13_m4e560940 is structurally distinguished

- **HW=47** is 6 bits below the next-best (msb_m189b13c7 at HW=51).
- Lower residual HW = fewer non-zero state-difference bits at round 63
  = easier Wang-style second-block absorption (fewer bits to cancel
  via the second block's message).
- bit13_m4e560940 had min HW=3 in F12 cascade-1 chamber image, AND now
  min HW=47 in round-63 residual. Both metrics rank it top-2 in registry.

## Cross-bet leverage

This bit13_m4e560940 cand:
- F12 (cascade_aux): 2nd-place HW=3 cascade-1 chamber min (after
  msb_m189b13c7 at HW=2)
- block2_wang (this finding): 1st-place HW=47 round-63 residual min

The cand is structurally distinguished on TWO independent metrics.
Worth registering as a primary block2_wang corpus target.

## Tool

`headline_hunt/bets/block2_wang/residuals/block2_residual_counter.c`
- 62M samples/sec on M5
- Compile: `gcc -O3 -march=native -o block2_residual_counter block2_residual_counter.c`
- Usage: `./block2_residual_counter <m0> <fill> <bit> <nsamples> [seed]`

## Caveats

- 100M is a STATISTICAL sample — actual min across 2^96 (W1[57..60])
  free space could be lower. The relative ordering across cands is
  the stable signal.
- All cands tested are cascade-eligible (verified at slot 56).
- Residual = state diff at SLOT 64 (after round 63), not at slot 61
  (Wang's "first-block residual" might prefer slot 61 framing).

## What block2_wang should do with this

1. Add bit13_m4e560940 to the bet's primary corpus list.
2. Run extended sample (1B-10B) on bit13 to find sub-HW-47 residuals.
3. Apply Wang-style second-block message-modification to absorb
   the 47-bit residual into a full collision.

EVIDENCE-level: HYPOTHESIS — 100M samples is a small fraction of the
2^96 (W1[57..60]) space. Relative ordering is suggestive but needs
larger sample for definitive ranking.
