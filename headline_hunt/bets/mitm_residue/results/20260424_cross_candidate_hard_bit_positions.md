# Cross-candidate hard-bit positions — sizes consistent, positions NOT

**Date**: 2026-04-24
**Machine**: macbook
**Tool**: `bets/mitm_residue/prototypes/hard_residue_analyzer.py` × 6 candidates
**Sample size**: 200,000 cascade-held samples per candidate
**Status**: addresses the highest-leverage next-action from `20260424_hard_residue_findings.md`.

## Headline finding

**The hard-residue *size* is candidate-independent (~24 bits per candidate),
but the hard-residue *positions* are candidate-dependent.** No single bit
position is uniform across all 6 candidates tested.

This refines the bet's economics: a forward MITM table works *per candidate*
(~17 GB at 2^26 entries) but does NOT amortize across candidates. Memory
budget for a multi-candidate sweep is ~17 GB × number-of-candidates, not 17 GB total.

## Per-candidate uniform-bit counts (round 60)

| Candidate | Uniform bits | g60 | f60 | h60 |
|---|---:|---:|---:|---:|
| bit06_6781a62a | 28 | 21 | 3 | 4 |
| bit10_3304caa0 | 22 | 16 | 3 | 3 |
| bit13_916a56aa | 27 | 20 | 3 | 4 |
| bit17_8c752c40 | 25 | 19 | 3 | 3 |
| bit19_51ca0b34 | 17 | 12 | 3 | 2 |
| msb_17149975 | 28 | 19 | 4 | 5 |

Mean: 24.5 bits, range 17-28. **Empirically validates the bet's "~24 hard bits" hypothesis** — but per candidate, not universal.

g60 holds the majority in every case (12-21 of the uniform bits). f60 contributes 3-4 consistently. h60 contributes 2-5.

## Pairwise Jaccard overlap of uniform-bit sets

|              | bit06 | bit10 | bit13 | bit17 | bit19 | MSB |
|---|---|---|---|---|---|---|
| bit06 | 1.00 | 0.22 | 0.34 | 0.36 | 0.22 | 0.37 |
| bit10 | 0.22 | 1.00 | 0.32 | 0.31 | 0.08 | 0.22 |
| bit13 | 0.34 | 0.32 | 1.00 | 0.44 | 0.22 | 0.31 |
| bit17 | 0.36 | 0.31 | 0.44 | 1.00 | 0.24 | 0.47 |
| bit19 | 0.22 | 0.08 | 0.22 | 0.24 | 1.00 | 0.18 |
| MSB   | 0.37 | 0.22 | 0.31 | 0.47 | 0.18 | 1.00 |

Pairwise overlap is moderate (0.18-0.47, mean ~0.29). bit19 is the outlier
(lowest overlap with everyone, only 17 uniform bits — a more constrained
candidate).

**Zero bits are uniform in all 6 candidates.** The union of uniform bits
across all 6 candidates is 60 — which means each candidate uses its own
roughly-disjoint slice of the available "freedom" bits.

## What's invariant across candidates

The bit positions vary, but several structural patterns hold across every
candidate:

1. **g60 dominance**: g60 always carries 12-21 of the uniform bits. The
   hard residue lives primarily in this register.
2. **f60 small constant**: 3-4 bits per candidate, never more.
3. **h60 small constant**: 2-5 bits per candidate.
4. **a60-e60 always cascade-zero**: no candidate violates this.

So the *register* identity is invariant; only the specific bit positions
within the register vary.

## Implications for the bet

| Aspect | Finding | Bet impact |
|---|---|---|
| Hard-residue size | ~24 bits/candidate | ✓ Confirmed |
| Hard-residue locality | g60-dominant | ✓ Confirmed |
| Cross-candidate amortization | Positions NOT shared | ✗ Refuted |
| Forward table memory | 2^26 (~17GB) per candidate | ✓ Feasible |
| Multi-candidate budget | ~17GB × N candidates | Constraint |

The bet remains **strongly viable for single-candidate attacks**. The
2^26-entry forward table for the MSB candidate could be built and
saved as a one-time artifact, then a backward MITM run would attempt
to find the meet point. ~17 GB on disk is trivial.

The bet's amortization hope (one table across all 35 candidates) is
gone. If the goal is "find sr=61 for ANY candidate", you need 35 separate
tables OR pick the most promising candidate and commit to it.

## What this does NOT mean

- It does NOT mean the bet is killed. Single-candidate MITM remains a
  valid path — and the universal cascade-zero structure (a60-e60 always
  zero) is still a major lever.
- It does NOT mean the cascade is too candidate-specific to be useful.
  All candidates show the same *qualitative* structure (160 cascade-zero,
  ~28 uniform, rest biased) — just quantitatively different bit positions.
- It does NOT rule out a clever encoding that absorbs the position
  variability. The hard-bit positions might be predictable from the
  cascade offsets per candidate — that's worth investigating.

## Open question raised by this result

Are the hard-bit positions per candidate **predictable** from the
candidate's (m0, fill, kernel_bit) tuple, or are they inherently random
relative to the candidate's structure? If predictable, the per-candidate
table can be replaced by an algebraic mapping; if random, each candidate
needs its own empirical table.

Likely answer: predictable (the hard bits are determined by the cascade
state at round 56, which is computed from the candidate). But this is
unverified — would require deriving an algebraic prediction and testing
against the empirical hard-bit positions.

## Next actions (ranked, all <30 min)

1. **Algebraic prediction**: derive (or hypothesize) a formula for which
   bits are uniform at round 60 from the round-56 state. Test against
   the 6 candidates' empirical hard-bit positions. If the prediction
   matches, the table cost collapses back to "one universal mapping +
   per-candidate offsets".
2. **W[60] sweep**: vary W[60] across cascade-2-constrained slack on the
   MSB candidate. If the hard-bit positions are W[60]-stable, the
   per-candidate table is W[60]-independent (good).
3. **Backward analyzer**: implement round-63 → round-60 backward direction
   and intersect with the forward hard-bit set. The MITM-relevant key
   is the intersection.

Item 1 is the most consequential — if it works, the bet's amortization
problem dissolves.

## Reproduce

```
for spec in msb_17149975:0x17149975:0xffffffff:31 \
            bit10_3304caa0:0x3304caa0:0x80000000:10 \
            bit06_6781a62a:0x6781a62a:0xaaaaaaaa:6 \
            bit17_8c752c40:0x8c752c40:0x00000000:17 \
            bit19_51ca0b34:0x51ca0b34:0x55555555:19 \
            bit13_916a56aa:0x916a56aa:0xffffffff:13 ; do
  name=$(echo "$spec" | cut -d: -f1)
  m0=$(echo   "$spec" | cut -d: -f2)
  fill=$(echo "$spec" | cut -d: -f3)
  bit=$(echo  "$spec" | cut -d: -f4)
  python3 headline_hunt/bets/mitm_residue/prototypes/hard_residue_analyzer.py \
    --m0 "$m0" --fill "$fill" --kernel-bit "$bit" \
    --samples 200000 --threshold 0.05 --out /tmp/hr_${name}.md
done
```

~5 minutes total CPU on macbook.
