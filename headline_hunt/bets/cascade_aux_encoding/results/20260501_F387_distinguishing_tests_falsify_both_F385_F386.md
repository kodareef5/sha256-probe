---
date: 2026-05-01
bet: cascade_aux_encoding
status: BOTH F385 + F386 FALSIFIED — refined rule m0_bit[31]=1 OR (fill_bit[31]=1 AND fill_HW>1) fits 14/14
parent: F386 (rule "fill > 0x80000000", fit 12/12)
type: distinguishing_tests + new_rule
compute: 2 cadical 30s LRAT runs (bit6_m88fab888, bit0_mf3a909cc)
---

# F387: distinguishing tests falsify both F385 and F386 rules; new rule fits 14/14

## Setup

F385 and F386 made conflicting predictions for these 2 cands:

  - bit6_m88fab888 fill=0x55555555 kbit=6:
    F385 predicts Class A (fill_bit[6]=1)
    F386 predicts Class B (fill_bit[31]=0)
  - bit0_mf3a909cc fill=0xaaaaaaaa kbit=0:
    F385 predicts Class B (fill_bit[0]=0)
    F386 predicts Class A (fill > 0x80000000)

Generated aux_force_sr60 CNFs for both, audited CONFIRMED, ran cadical
30s with --binary=false LRAT proof.

## Result — both rules falsified

```
cand                fill         kbit  F385 pred  F386 pred  observed
bit6_m88fab888      0x55555555      6      A          B       A (ladder=31)
bit0_mf3a909cc      0xaaaaaaaa      0      B          A       A (ladder=31)
```

bit6_m88fab888 is Class A — falsifies F386's "fill > 0x80000000" rule.
bit0_mf3a909cc is Class A — falsifies F385's "fill_bit[kbit]=1" rule.

**Both prior rules need replacement.**

## New rule found — 14/14 fit

Tested all logically simple combinations of (m0_bit, fill_bit, fill_HW)
predicates against the now n=14 fingerprint. Found:

> **`ladder iff (m0_bit[31] = 1) OR (fill_bit[31] = 1 AND fill_HW > 1)`**

Fits 14/14 cands tested. Truth table:

```
cand                m0         fill         m0_b31  fill_b31  fill_HW   rule  observed
bit31_m17149975     0x17149975  0xffffffff      0         1       32      A         A
bit2_ma896ee41      0xa896ee41  0xffffffff      1         1       32      A         A
bit3_m33ec77ca      0x33ec77ca  0xffffffff      0         1       32      A         A
bit28_md1acca79     0xd1acca79  0xffffffff      1         1       32      A         A
msb_m3f239926       0x3f239926  0xaaaaaaaa      0         1       16      A         A
bit13_m4e560940     0x4e560940  0xaaaaaaaa      0         1       16      A         A
bit6_m6781a62a      0x6781a62a  0xaaaaaaaa      0         1       16      A         A
bit0_mf3a909cc      0xf3a909cc  0xaaaaaaaa      1         1       16      A         A
bit6_m88fab888      0x88fab888  0x55555555      1         0       16      A         A   ← NEW (m0 alone)
bit6_m024723f3      0x024723f3  0x7fffffff      0         0       31      B         B
bit11_m45b0a5f6     0x45b0a5f6  0x00000000      0         0        0      B         B
bit13_m4d9f691c     0x4d9f691c  0x55555555      0         0       16      B         B
bit10_m3304caa0     0x3304caa0  0x80000000      0         1        1      B         B
bit17_m427c281d     0x427c281d  0x80000000      0         1        1      B         B
```

The disjunctive rule has TWO PATHS to Class A:

  PATH 1: m0 has bit-31 set
  PATH 2: fill has bit-31 set AND fill is "rich" (HW > 1)

bit6_m88fab888 reaches Class A via Path 1 (m0_bit[31]=1, even though
fill=0x55555555 has bit-31=0).

bit31_m17149975 (m0_bit[31]=0, fill_bit[31]=1, fill_HW=32) reaches via
Path 2.

bit10/bit17 fail BOTH paths: m0 bit-31 is 0, fill is 0x80000000 with HW=1.

## Findings

### Finding 1 — The cascade-aux ladder is REGISTERED as either m0 or fill provides bit-31 + density

Mechanism conjecture (refined): the cascade-1 forward eval propagates
M[0]'s bit-31 through Sigma1/Sigma0 (rotation-then-shift operations).
If M[0]=m0 has bit-31 set, that bit propagates through round 0's
Sigma0(a) and the round function's T1/T2 deterministically. If M[0]
has bit-31=0 but M[1..15]=fill has bit-31=1 with sufficient density,
then later rounds' state-e values (which depend on the schedule recurrence
W[i] = sigma1(W[i-2]) + W[i-7] + sigma0(W[i-15]) + W[i-16]) carry the
bit-31 information through to round 57+ where the cascade-1 hardlock's
Tseitin XOR encoding kicks in.

Both paths supply bit-31 information to the cascade-1 region in round
57+; if neither path is available, the Tseitin encoder's output lacks
the per-slot symmetry that produces the 31-rung ladder.

### Finding 2 — Project's 10th iterative rule narrowing

The chain F381 → F387:

  F381 (n=1):  discovered XOR ladder structure
  F382 (n=3):  fill-bit-31 axis                      — falsified
  F383 (n=6):  fill=0xffffffff axis                  — narrowed
  F384 (n=8):  fill=0xffffffff specifically          — narrowed
  F385 (n=11): fill_bit[kbit]=1 (10/11)              — falsified
  F386 stage2 (n=12): fill_bit[31] AND fill_bit[kbit] — falsified within 10 min
  F386 stage3 (n=12): fill > 0x80000000              — provisional
  F387 (n=14): m0_b31=1 OR (fill_b31=1 AND fill_HW>1) — fits 14/14 ← CURRENT BEST

10 iterations across 5 hours, ~270s of cadical compute, 14 cands. The
core finding (XOR ladder structure exists) is robust; the precise
class boundary keeps refining as new data arrives.

### Finding 3 — Class A coverage under refined rule

Per registry's m0/fill distribution:

  fill=0xffffffff (31 cands): all have fill_bit[31]=1, fill_HW=32 → all Class A
  fill=0xaaaaaaaa (6 cands):  all have fill_bit[31]=1, fill_HW=16 → all Class A
  fill=0x55555555 (6 cands):  fill_bit[31]=0; depends on m0_bit[31]
                              (need to check each m0)
  fill=0x80000000 (11 cands): fill_bit[31]=1 but HW=1; depends on m0_bit[31]
  fill=0x7fffffff (3 cands):  fill_bit[31]=0; depends on m0_bit[31]
  fill=0x00000000 (10 cands): fill_bit[31]=0; depends on m0_bit[31]

Total Class A = 31 + 6 + (6 + 11 + 3 + 10) × Pr(m0_bit[31] = 1).

Without testing each m0, can't compute exactly. But upper bound:
  if all m0s had bit-31=1: 31 + 6 + 30 = **67 cands (100%)**
  if no m0 had bit-31=1: 31 + 6 = 37 cands (55%)

A quick check on the 30 "depends" cands' m0_bit[31] would settle it.

### Finding 4 — Phase 2D pre-injection becomes deterministic at last

Per F387 rule, the Phase 2D propagator can decide ladder injection per
cand from (m0, fill) alone:

```python
def class_a(m0: int, fill: int) -> bool:
    return ((m0 >> 31) & 1) or (((fill >> 31) & 1) and bin(fill).count("1") > 1)
```

For Class A cands: pre-inject the 31-rung Tseitin XOR ladder via
`cb_add_external_clause` at solver init.

For Class B cands: F343's 2-clause baseline preflight only.

The rule is **purely structural** — no per-cand mining needed beyond
F343's existing tool. That's the deployable specification.

## What's shipped

- 2 cadical 30s LRAT runs (bit6_m88fab888, bit0_mf3a909cc), logged
- 2 new aux_force CNFs audited CONFIRMED
- This memo with 14-cand truth table + 14/14 rule
- Phase 2D class-decision function as pseudo-code

## Compute discipline

- 2 cadical runs logged via append_run.py
- 2 new aux_force CNFs in cascade_aux/cnfs/ (audit CONFIRMED)
- audit_cnf fingerprint_observed_n unchanged (range envelope already covers)
- Real audit fail rate stays 0%

## Open questions for next session

(a) **Compute m0_bit[31] for the 30 "depends" cands** (those with
    fill ∉ {ffffffff, aaaaaaaa}). ~30s of grep work, no compute.
    Gives definitive Class A count for the registry.

(b) **Test 1-2 cands per "depends" subgroup** to confirm the rule
    extends. Especially: a fill=0x80000000 cand with m0_bit[31]=1
    (predicted Class A under F387, contradicts F386 directly).

(c) **Algebraically derive** the rule from cascade-aux encoder source.
    The "either m0 or fill provides bit-31 with density" pattern likely
    has a clean derivation from the schedule recurrence + sigma1/sigma0
    bit-flow.

(d) **Build the deployable propagator extension** (F343 + ladder for
    Class A). Sub-30-min coding work.

The F387 rule is the strongest empirically-backed statement yet about
when the cascade-aux Tseitin XOR ladder appears. Phase 2D pre-injection
is now a deterministic per-(m0, fill) decision.
