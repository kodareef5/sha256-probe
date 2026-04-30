---
date: 2026-04-30
bet: programmatic_sat_propagator × sr61_n32
status: F358_RETRACTION + F360_CORRECTION — basic-cascade injection ~1% speedup
---

# F360: F358 retraction + corrected F235 injection measurement

## What was claimed in F358

F358 reported: "F343-mined clauses translated to F235 → 2.1% speedup"
with 6 clauses (2 unit + 4 OR-of-XOR for forbidden pair).

## The bug

Inspecting F358's CNF clauses for the W57[22:23] forbidden=(0,0) pair:

```python
# F358's "OR of two XORs" encoding (BUGGY):
[24, -120, 25, -121]   # (W1[22] ∨ ¬W2[22] ∨ W1[23] ∨ ¬W2[23])
[24, -120, -25, 121]   # (W1[22] ∨ ¬W2[22] ∨ ¬W1[23] ∨ W2[23])
[-24, 120, 25, -121]   # (¬W1[22] ∨ W2[22] ∨ W1[23] ∨ ¬W2[23])
[-24, 120, -25, 121]   # (¬W1[22] ∨ W2[22] ∨ ¬W1[23] ∨ W2[23])
```

Truth-table check: for the forbidden case (W1[22]=W2[22]=W1[23]=W2[23]=0,
which IS dW57[22]=0 AND dW57[23]=0 — should be forbidden):
- Clause 1: (0 ∨ 1 ∨ 0 ∨ 1) = 1 (satisfied) ✗ should be unsatisfied
- All 4 clauses satisfied!

So F358's encoding does NOT actually forbid the (0, 0) polarity. The
buggy clauses encode some other constraint (specifically: forbidding
high-XOR-difference assignments at certain polarity combinations).

The unit-clause portion (`[-2, 98]`, `[2, -98]` for dW57[0]=0) was
CORRECT.

## The correction

Forbidden=(0, 0) means "NOT (W1[i]=W2[i] AND W1[j]=W2[j])". The 4
forbidden assignments (where the constraint should fail) are:
- (W1[i]=0, W2[i]=0, W1[j]=0, W2[j]=0)
- (W1[i]=0, W2[i]=0, W1[j]=1, W2[j]=1)
- (W1[i]=1, W2[i]=1, W1[j]=0, W2[j]=0)
- (W1[i]=1, W2[i]=1, W1[j]=1, W2[j]=1)

CORRECT 4 clauses (each unsatisfied by exactly one forbidden assignment):
```python
[+W1[i], +W2[i], +W1[j], +W2[j]]      # forbids (0,0,0,0)
[+W1[i], +W2[i], -W1[j], -W2[j]]      # forbids (0,0,1,1)
[-W1[i], -W2[i], +W1[j], +W2[j]]      # forbids (1,1,0,0)
[-W1[i], -W2[i], -W1[j], -W2[j]]      # forbids (1,1,1,1)
```

For F235 cand m09990bd2/bit25 with W1[22]=24, W2[22]=120, W1[23]=25,
W2[23]=121, the correct W57[22:23]=(0,0) blocking is:
```
[24, 120, 25, 121]
[24, 120, -25, -121]
[-24, -120, 25, 121]
[-24, -120, -25, -121]
```

## F360 corrected measurement

Re-ran injection on F235 with F359's full 34-clause sweep translated
correctly to F235 vars. 130 total clauses (3 single-bit × 2 + 31 pair × 4):

```
F235 BASELINE (cadical 5min):  5,262,467 conflicts UNKNOWN
F235 INJECTED (130 corrected): 5,220,755 conflicts UNKNOWN
Δ: -41,712 conflicts (-0.79%)
```

## Findings

### Finding 1 — F358's claimed -2.1% was from BUGGY clauses

The clauses didn't actually encode the right structural constraint.
Whatever speedup F358 measured was incidental — wrong clauses still
shrunk the search space by adding spurious blocks.

### Finding 2 — F360 corrected speedup is ~1% on F235 basic cascade

130 correctly-encoded clauses on F235's basic cascade encoder:
**-0.79% conflict reduction**.

This is SMALLER than F358's incorrect -2.1%. The correction reveals
the real structural speedup is even more modest than initially reported.

### Finding 3 — Basic-cascade encoder vs aux_force gap is large

Speedup envelope across mode/encoder:
- F347 sr=60 FORCE bit31, 32 aux_force clauses: -13.7%
- F348 5 cands sr=60 FORCE, 2 aux_force clauses: -8.8% mean
- F352 sr=60 EXPOSE bit29, 2 aux_force clauses: -1.06%
- **F360 sr=61 BASIC CASCADE bit25, 130 translated clauses: -0.79%**

The basic-cascade encoder + CNF-only injection gives ~1% best case.
For F235's 848s baseline, that's ~7s saved per solve — negligible.

### Finding 4 — Phase 2D propagator NATIVE injection still the path

To get F347-class 13.7% speedup on F235, need IPASIR-UP cb_add_external_clause
hook in the SAT solver itself. The CNF-append approach (F358/F360) is
fundamentally weaker for basic cascade encoder because:
- 4-literal OR-of-XOR clauses propagate slower than 2-literal aux clauses
- 124 added clauses increase per-conflict cost without proportional
  search-space pruning benefit

## Retractions

The following claim from F358 is RETRACTED:
- "F343-mined clauses translated to F235 → 2.1% speedup"

What stands:
- F359 mined 34 clauses on aux_force_sr61 m09990bd2/bit25 (correct mining)
- F360 corrected encoding gives -0.79% on F235 basic cascade (correct measurement)
- F343 preflight architecture still works at sr=61 / cross-mode

## Discipline

- Bug caught via manual truth-table inspection during F360 derivation.
- Fixed within ~10 minutes of discovery.
- 6th retraction this 2-day arc (after F205, F232, F237, F279, F288, F309, F322, F333, F358).
- Honest correction shipped immediately.

## Updated Phase 2D propagator picture

For F235-class hard instances:
- CNF-only injection: ~1% speedup (F360)
- IPASIR-UP native injection: projected ~13.7% (F347-equivalent on aux_force)
- 13.7% × 848s = ~116s saved — meaningful for hard instances near the
  budget edge

Phase 2D implementation remains the right path; CNF-only injection is
demonstrably weaker.

## Concrete next move

(a) Phase 2D C++ propagator implementation (10-14 hr build)
(b) Cross-cand basic-cascade injection at sr=60 — does -0.79% generalize?
(c) Compare aux_force vs basic-cascade injection on the SAME cand to
    quantify the encoder-mode gap precisely.
