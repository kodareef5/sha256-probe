# de58-only per-chamber hints — 1.31–2.20× speedup (4 cands)
**2026-04-26 19:25 EDT**

A new locked-bit-hint variant that is structurally stronger than the
2026-04-26 13-bit marginal-locked deployment (commits 795bfb3, 88eb025,
557fc42, a95a267).

## Discovery: per-chamber de58_size = 1

The registry's `de58_size` (256 for bit=19, 82826 for idx=0, etc.) is
the image **over all W57**. Per-chamber (fixed W57), de58 is fully
determined.

`/tmp/deep_dig/per_chamber_de58.py` — at fixed W57, vary W58 across
2^18 random samples; check |image| of de58.

| cand | tag | W57 | per-chamber de58_size |
|---|---|---:|---:|
| bit=19 (orig) | 0x51ca0b34 / 0x55555555 / b19 | 0x4f9409ff | **1** |
| bit=8 (idx=0) | 0x17149975 / 0xffffffff / b31 | 0x370fef5f | **1** |
| bit=8 alt | 0x17149975 / 0xffffffff / b31 | 0x7976ba1b | **1** |
| bit=20 (idx=3) | 0x294e1ea8 / 0xffffffff / b20 | 0xe28da599 | **1** |
| bit=20 alt | 0x294e1ea8 / 0xffffffff / b20 | 0xc468740a | **1** |
| bit=3 (idx=8) | 0x33ec77ca / 0xffffffff / b3 | 0xaf07f044 | **1** |
| bit=3 alt | 0x33ec77ca / 0xffffffff / b3 | 0xa707efce | **1** |

All 7 chambers tested → de58_size = 1 per chamber. So at fixed
(m0, fill, kernel_bit, W57), de58 is a single 32-bit value.

**Mechanism**: cascade-1 at slot 57 fixes the round-58 inputs;
da[58]=0 forces the de58 expression to depend only on Sigma1+Ch
applied to inputs already determined by W57. W58 only enters de58
through `de58 = (s1_58[4] - s2_58[4]) = ... + W58 - W58_2 = -cw58`
which is a function of the slot-57 states alone.

## Implication: inject all 32 de58 bits as unit clauses

Compute `de58 = compute_de58_at_W57(m0, fill, bit, W57)` once per
chamber, then write 32 unit clauses on `aux_reg[("e", 58)][bit]`.
Strictly stronger than the 13-bit marginal-locked variant (which
fixed only the always-0/always-1 bits of the cand-aggregate image).

## Decomposition test (bit19, idx8)

`/tmp/deep_dig/full_de58_hint_test.py` — three variants on the same
chamber:
- W57-only fix (32 unit clauses on W1_57)
- de58-only fix (32 unit clauses on aux_reg[("e", 58)])
- both (W57 + de58 = 64 unit clauses)

Kissat 4.0.4, max_conflicts=50000, walls (sec) median of 3 seeds:

| cand | base | W57 only | de58 only | both |
|---|---:|---:|---:|---:|
| bit19 | 3.19 | 2.47 (1.29×) | **1.52 (2.09×)** | 1.97 (1.62×) |
| idx8 | 2.50 | 3.09 (0.81× **regression**) | **1.53 (1.63×)** | 1.83 (1.37×) |

**Findings**:
1. W57-only is unstable — bit19 helps, idx8 regresses 19%.
2. de58-only is the winner on both cands.
3. Combining (de58 + W57) is WORSE than de58 alone — the W57 fix
   over-constrains and degrades search flexibility.

**Why**: a fixed de58 value induces ~2^24 valid W57 choices (out of
2^32), so de58-only is an 8-bit pruning of the W57 search space.
Solver retains flexibility on which W57 to use while excluding 99.6%
of W57s. Pinning W57 explicitly removes that flexibility entirely.

## 4-cand verification (3 seeds each)

Same kissat, same 50k budget, same M5 host:

| cand | base_med | de58only_med | speedup |
|---|---:|---:|---:|
| idx0 | 2.60s | 1.98s | 1.31× |
| idx8 | 2.50s | 1.54s | 1.62× |
| idx17 | 3.24s | 2.16s | 1.50× |
| bit19 | 3.36s | 1.53s | 2.20× |

Median speedup across 4 cands: **1.56×**.

Comparison with previously committed variants:

| variant | scope | median speedup |
|---|---|---:|
| 13-bit marginal-locked (commit a95a267) | n=18 cands × 3 seeds | 1.16× |
| **de58-only per-chamber** (this memo) | n=4 cands × 3 seeds | **1.56×** |

The 13-bit hints fixed only bits where the **aggregate** image was
locked. The de58-only variant fixes all 32 bits at the **chamber**
level — strictly more information.

## Caveats

1. Requires choosing a W57 per chamber (the 13-bit variant did not).
   Yale's GPU off58 chart scan gives multiple valid W57s per cand;
   using the HW4-reaching W57 is one defensible choice.
2. n=4 sample is preliminary; an n=18 deployment (analogous to the
   13-bit n=18 sweep, commit c110556) is the next step.
3. Speedup is preprocessing-only — the same ~50k sweet spot likely
   applies (the 13-bit findings showed budget-invariant regressions
   and 50k peak; expect similar shape here).
4. Mode A wall predictor (Mode B ρ=+0.976, locked-bit ρ=+0.792) was
   not measured for de58-only. If the predictor generalizes again,
   that's another cross-bet leverage win.

## Next actions

1. **Extend to n=18 cands × 3 seeds** at 50k → produce a deployment
   chart matching the 13-bit one (20260426_locked_bit_hints_n18_correction.md).
2. **Update `locked_bit_hint_wrapper.py`** with a `--de58-at-w57 0xHEX`
   mode that injects 32 unit clauses on aux_reg[("e",58)] given the
   de58 value computed at a user-supplied W57.
3. **Test Mode A wall predictor on de58-only**: if it predicts here
   too, the mechanism is unified across all three (Mode B, locked-bit,
   de58-only) variants.
4. **Cross-validate on bit-19 alt chambers**: yale's GPU scan found
   multiple HW4 W57s per cand; do they yield different speedups?
   Per-chamber de58 differs across W57s, so the encoded constraint
   differs even at a fixed cand.

EVIDENCE-level: HYPOTHESIS — 4-cand × 3-seed result is consistent
and the mechanism is well-grounded structurally, but n=18 deployment
is needed before claiming this as the new default.
