# F35: Lipmaa-Moriai per-cand cost — bit13 beats bit2 on the LM metric
**2026-04-27 11:50 EDT**

Refines F34's universal 43-active-adder finding via Lipmaa-Moriai 2001
exact per-adder XOR-differential probability accounting. The result
reveals a SURPRISE: bit2_ma896ee41 (F28 NEW CHAMPION at HW=45) is NOT
the LM-cost minimum. **bit13_m4e560940 wins on LM cost (780 vs bit2's 824).**

## Tool

`active_adder_lm_bound.c` — extends F34's tool with:
- Per-adder Lipmaa-Moriai cost: `w(α, β, γ) = HW(~eq(α,β,γ) & 0x7FFFFFFE)`
- Per-adder LM compatibility check (returns -1 if trail is incompatible)
- Per-adder max-HW upper bound (loose ceiling)
- Sums across all active adders → trail-level metrics

LM cost interpretation: for a modular adder `α + β = γ` with given
input/output XOR-differences, `w` is the number of bits where the LM
"all-three-equal" condition fails. The XOR-differential probability
of that adder is `2^-w`.

## Cross-cand result (11 exact-symmetry cands at deep min)

| cand | min HW | active | **LM-sum** | max-HW-sum | LM-incompat |
|---|---:|---:|---:|---:|---:|
| **bit13_m4e560940 (LM champion)** | 47 | 43 | **780** | 641 | 0 |
| bit2_mea9df976 | 48 | 43 | 795 | 656 | 0 |
| bit4_md41b678d | 49 | 43 | 818 | 639 | 0 |
| **bit2_ma896ee41 (HW champion)** | **45** | 43 | **824** | 651 | 0 |
| bit26_m11f9d4c7 | 51 | 43 | 826 | 673 | 0 |
| bit00_md5508363 | 48 | 43 | 831 | 627 | 0 |
| msb_m44b49bc3 | 49 | 43 | 834 | 672 | 0 |
| bit1_m6fbc8d8e | 51 | 43 | 847 | 670 | 0 |
| bit2_m67dd2607 | 48 | 43 | 849 | 665 | 0 |
| bit17_m427c281d | 50 | 43 | 858 | 687 | 0 |
| bit17_mb36375a2 | 48 | 43 | 870 | 684 | 0 |

LM-sum spread: **780 to 870, range 90 bits**.

## Three independent findings

### 1. Cascade-1 trails are LM-compatible across all 11 cands

**LM-incompatible adder count: 0 for all 11 cands.**

This means the cascade-1 trail at slots 57..60 produces, for every
exact-symmetry cand, an XOR-difference characteristic that is
structurally consistent under Lipmaa-Moriai. The trail "could happen"
under random input pairs — the diff propagation doesn't violate the
modular adder's carry constraints.

This is itself a publishable result: the cascade-1 mechanism doesn't
just give us low-HW residuals empirically (F25/F28); it gives us
**LM-COMPATIBLE TRAILS** structurally. There's no hidden carry
violation that would force the trail probability to zero.

### 2. HW-minimum ≠ LM-minimum

The F28 NEW CHAMPION bit2_ma896ee41 wins on HW (45) but loses on LM
(824, mid-pack). bit13_m4e560940 wins on LM (780) but is at HW=47.

This implies:
- **HW-min metric** (used in F25/F26/F27/F28): selects bit2 as primary target.
- **LM-min metric** (introduced in F35): selects bit13 as primary target.
- The two metrics measure DIFFERENT structural properties.

### 3. Cascade-invariance is partially broken at LM level

F34 found 43 active adders is INVARIANT across all 67 cands (cascade
structural property). F35 finds LM-sum is NOT invariant — it varies
by ±90 bits across the 11 exact-symmetry cands.

So cascade-1 fixes WHICH adders are active (always 43) but the
PER-ADDER COST varies based on the cand's specific bit-pattern.

## Reinterpretation of F34's "trail probability" claim

F34's framing ("naive 2^-43 trail-prob lower bound") was loose. The
cascade-1 trail at rounds 57..60 is DETERMINISTIC given the W-witness
(W57..W60). There's no "probability" of the trail occurring — once
we found the witness via deep search, the trail follows.

The proper interpretation:
- **Active-adder count (43)** = structural metric counting "non-trivial
  modular-add steps"
- **LM-sum (824 for bit2)** = bit-count of carry constraints satisfied
  by the W-witness
- The cascade-1 mechanism deterministically satisfies these constraints

For block2_wang's eventual implementation, what matters is the
**SECOND-BLOCK trail's LM cost** (still TBD), not the first-block
trail's. The first block's residual is "free" — given by the W-witness.

## Why the LM-min metric matters anyway

Even though the FIRST-block LM cost isn't a probability, it serves as
a **structural metric**:
- Lower LM-sum ↔ FEWER carry constraints to satisfy
- For Wang-style M-pair construction (where M1, M2 must satisfy
  bitconditions), each LM-cost bit is one bitcondition
- A cand with LM=780 has 780 bits of message constraints to satisfy
- A cand with LM=870 has 870 bits — strictly harder

So **bit13_m4e560940 has 90 fewer bits of constraint than
bit17_mb36375a2**. For Wang attack engineering, bit13 is a
strictly EASIER target than bit17.

## Updated cand ranking for block2_wang

Combining metrics (lower is better in both):

| Rank | cand | HW | LM | combined (HW + LM/100) |
|---:|---|---:|---:|---:|
| 1 | bit13_m4e560940 | 47 | 780 | 54.8 (LM champion) |
| 2 | bit2_mea9df976 | 48 | 795 | 55.95 |
| 3 | bit2_ma896ee41 | **45** | 824 | 53.24 (HW champion) |
| 4 | bit4_md41b678d | 49 | 818 | 57.18 |
| 5 | bit26_m11f9d4c7 | 51 | 826 | 59.26 |

Mixed metric (HW + LM/100): bit2_ma896ee41 still wins overall (53.24),
but the gap is narrow. For PURE LM-cost considerations (most relevant
to per-bitcondition construction effort), bit13 is preferred.

## Implication for paper Section 5

The block2_wang feasibility argument now has TWO independent
quantitative metrics:
1. **HW-min residual**: bit2 at HW=45 (paper claim: lowest residual
   bits to absorb)
2. **LM-cost**: bit13 at 780 bits (paper claim: fewest bitcondition
   constraints)

A rigorous Section 5 would present both and explain the trade-off.
The "best target cand" depends on which axis dominates the second-
block construction effort.

## Surprises for the team

1. **Active count is invariant (43) — cand selection irrelevant at
   that granularity.**
2. **LM cost varies by 90 bits — cand selection IS relevant at this
   granularity.**
3. **The two metrics disagree on cand ranking.**

Most importantly: **the cascade-1 trail is structurally
LM-compatible for all distinguished cands**. No hidden carry
violation. This is a positive result for Wang absorption feasibility.

## Discipline

- Tool: `active_adder_lm_bound.c` (compiled, verified against F32)
- Cross-cand sweep: 11 exact-symmetry cands, ~1.1 sec total compute
- Bug fix incorporated: W1[61..63] recomputation after witness
- Source of truth: F32 deep corpus

EVIDENCE-level: VERIFIED. LM compatibility is structural; LM costs
reproduce on multiple invocations. Forward simulation matches F32.

## Next concrete moves

1. **Run on all 67 cands** (~6 sec) to find global LM-min cand
2. **Apply LM analysis to second-block trails** — this is what
   actually determines absorption probability. Requires constructing
   candidate second-block trails.
3. **Cross-cand kissat speed correlation** — does lower LM-cost
   correlate with faster kissat solve time? Test 1M conflict
   walls per cand and check.
4. **Cross-validate against Mouha 2013 MILP-derived bounds**
   (literature/notes/classical_mouha_arx_framework.md) — check that
   our 780 for bit13 is consistent with their formalism.
