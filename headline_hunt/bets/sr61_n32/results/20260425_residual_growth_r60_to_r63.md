# Residual dimension growth from r=60 to r=63 — empirical
**2026-04-25** — sr61_n32 bet — extends `multi_residual_compression.py` through r=63 with the actual SHA-256 message schedule (no cascade-extending past r=60).

## Setup

For each candidate, sample W57 (random 32-bit), apply cascade-1 through r=59 (W2[58,59] = cascade1_offset; W1[58,59] = 0), apply cascade-2 at r=60 (W2[60] = cascade2_offset, W1[60] = 0). For r=61..63: use the actual SHA-256 message schedule for both W1 and W2. Measure register-diff image at each round.

Sample size: 16384 → 262144 → 1048576 across runs, depending on what we wanted to resolve.

## Results

### At r=60 (cascade boundary): residual is 1-D in W57

Confirms multi_residual finding: only **g_60 = de58** varies. All other registers are constant per candidate.

```
register: a  b  c  d  e  f  g     h
image:    1  1  1  1  1  1  ≤2^N  1
```

### At r=61: a_61 = e_61 modular (Theorem 4 confirmed at full N=32)

```
register: a       b  c  d  e       f  g  h
image:    sat     1  1  1  sat     1  1  =g_60
```

`sat` = saturated at sample size (≥2^14 at 16k samples). At 1M samples: `da_61` and `de_61` both saturate at 2^20 — and **da_61 == de_61 always** (verified across 1M samples). This is Theorem 4 (`da_r ≡ de_r mod 2^32`) confirmed empirically at r=61 for full N=32.

### At r=62, r=63: register shifts, no new compression

```
r=62: a=NEW, b=a_61, c=1, d=1, e=NEW, f=e_61, g=1, h=1
r=63: a=NEW, b=a_62, c=a_61, d=1, e=NEW, f=e_62, g=e_61, h=1
```

Each round introduces ONE new d.o.f. (in a/e jointly via Theorem 4). Old d.o.f. shift into b/c (and f/g via the e-chain). d_r and h_r stay 0 because they're shifted from cascade-zero registers.

### **Key finding**: full residual at r=63 is 1-D in W57

Joint image of (da_63, db_63, dc_63, de_63, df_63, dg_63) at 262k samples:

| Candidate            | de58 image | da_63 image | joint full residual |
|----------------------|-----------:|------------:|--------------------:|
| bit-19 (TOP)         | 2^8        | 2^18 (sat)  | 2^18 (sat)          |
| msb_m9cfea9ce_fill0  | 2^12       | 2^18 (sat)  | 2^18 (sat)          |
| bit-25               | 2^12       | 2^18 (sat)  | 2^18 (sat)          |
| MSB cert             | 2^16.79    | 2^18 (sat)  | 2^18 (sat)          |
| msb_m189b13c7_BOTTOM | 2^17.98    | 2^18 (sat)  | 2^18 (sat)          |

**The full 6-component residual at r=63 saturates at sample size for ALL candidates.** This means W57 → r=63 residual is essentially injective. The cascade-DP residual at r=63 is parameterized entirely by W57 (32 bits).

## Per-de58-class probe at bit-19

Within each de58 class (256 classes, ~4096 W57 samples per class out of true ~2^24):

```
de58=0x76ad5469: 4241 samples → da_63 image=4241 = 2^12.05
de58=0x80c54b89: 4240 samples → da_63 image=4240 = 2^12.05
de58=0x70bd5469: 4227 samples → da_63 image=4227 = 2^12.05
de58=0x68b54b69: 4222 samples → da_63 image=4222 = 2^12.04
de58=0x6ec55369: 4221 samples → da_63 image=4220 = 2^12.04
```

Within each de58 class, W57 → da_63 is essentially injective. **The de58 compression does NOT propagate to r=63.** bit-19's 24-bit compression applies ONLY to de58; downstream registers see no further structural reduction.

## Recasts the bit-19 finding

**Earlier claim** (de58 predictor writeup): "bit-19 has 24-bit compression → 2^32/2^24 = 2^8 expected work to find sr=61 SAT".

**Corrected**: bit-19's 24-bit compression applies to de58 (= dg_60) image. For cascade-DP r=61 SAT we need `da_61 = 0 modular`. da_61's image at bit-19 is 2^32 (un-compressed). So cascade-DP r=61 SAT search at bit-19 requires ~2^32 W57 trials, **same as any other candidate**.

The de58 compression buys you a 24-bit reduction in `de58 = 0` (or any specific de58-target) search, but cascade-DP r=61 doesn't target de58 — it targets `da_61 = 0`.

So bit-19's structural extreme is a **measurement artifact at r=60** that doesn't translate to cascade-DP advantage. Where it WOULD help: if a downstream algorithm explicitly partitions search by de58 class, the per-class W57 search is 2^24 not 2^32.

## Cost of cascade-DP "r=61" SAT brute force — corrected

**Initial naïve estimate:** "1 modular constraint at r=61 → 2^32 W57 trials → ~30s in C."

**Why that estimate is wrong:** the actual `encode_sr61_cascade.py` encoder demands ALL EIGHT registers to match at slot 64 (full SHA-256 state collision), not just `da_61 = 0`. With 3 free words (W[57..59]) in the cascade-DP relaxed model, we have 3×32 = 96 free bits, but cascade-extending W2 absorbs about 128 bits worth of intermediate da-equality. The remaining "final 8-register equality at slot 64" amounts to many more independent bits than just da_61.

**Empirical confirmation:** at 4,194,304 random W57 trials (W1[58..60]=0 canonical) for bit-19, **0 W57 produced da_61=0 modular**. Consistent with probability ≈ 2^-32 just for the *first* of multiple constraint-bits.

**Implication:** the "1000× faster brute force" idea evaporates once you account for the full collision constraint at slot 64. The hours of kissat reflect real problem hardness — not encoding overhead. The cascade-DP r=61 search remains expensive precisely *because* the residual at r=63 is 1-D in W57: that 1 d.o.f. has to satisfy ~8×32 bits of equality conditions simultaneously.

## Verification of Theorem 4 at full N=32

The 1M-sample run verified `da_61 ≡ de_61 (mod 2^32)` for every sample. This was previously stated as theorem but only verified at small N. At N=32 with bit-19 candidate: 1,048,576 samples, 0 violations.

## What this means for the bet portfolio

- The cascade-DP r=63 residual being 1-D in W57 is itself a **structural pillar** for any future encoding work. It says: any propagator/encoding for sr=61 only needs to track 32 bits of state at the cascade boundary.
- The `programmatic_sat_propagator` graveyard memo can incorporate this: even with perfect state tracking, the actual problem's constraint count is what makes it hard, NOT the lack of structural insight.
- bit-19's de58 compression IS real but doesn't propagate to r=63. Useful only if a downstream algorithm uses de58 explicitly as a search axis (currently none does in the active bets).
- **NEW kill criterion data point for `sr61_n32`:** if 4M random W57 trials at bit-19 (the "best" candidate by de58 compression) yield 0 da_61=0 hits, expect the SAT solver to need ≥ ~2^32 work just to satisfy the FIRST of ~8 collision-bit constraints. The 1800 CPU-h baseline is consistent with real problem hardness, not encoding waste.

## Open question — revised

The earlier framing ("why does cnfs_n32 take hours?") rested on a wrong cost estimate. The corrected picture: the encoder's final 8-register collision at slot 64 imposes constraints whose joint probability is much smaller than 2^-32 per random W57. The hours of kissat are doing real work against real problem hardness.

What's still genuinely **interesting** is that the residual at r=63 is 1-D in W57 (modular Theorem 4 verified). This means the CDCL solver doesn't actually need to search over full state vars — it needs to search over W57 alone (32 bits) plus check whether the resulting state collides at slot 64. A propagator-style encoding that explicitly parametrizes the search by W57 alone could in principle outpace standard CDCL — but that's exactly what the killed `programmatic_sat_propagator` tried, and the hardness comes from constraint-side, not search-side.

## Files

- `residual_dimension_growth.py` — sweep script, multiple candidates
- `results/residual_growth_2026-04-25.jsonl` — raw output
- This writeup
