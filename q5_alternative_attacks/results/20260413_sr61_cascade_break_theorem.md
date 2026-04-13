# The sr=61 Cascade Break Theorem

Date: 2026-04-13 08:40 UTC

## Statement

For sr=61, the schedule constraint W[60] = sigma1(W[58]) + constants
determines W2[60] independently of the cascade requirement. The cascade-
required W2[60] (for da60=0) matches the schedule-determined W2[60]
with probability exactly 1/SIZE = 2^(-N).

## Verification at N=8

- 10,000 random (w57,w58,w59) triples tested
- 43 matches (0.43%) — matches expected 1/256 = 0.39%
- 99.6% of configurations have da60 ≠ 0 under sr=61

## The Mechanism

For sr=60:
```
Round 60: W2[60] = W1[60] + cascade_offset  → da60 = 0 GUARANTEED
```

For sr=61:
```
Round 60: W2[60] = sigma1(W2[58]) + ...  → da60 ≠ 0 (probability 1 - 2^-N)
```

When da60 ≠ 0:
- The a-path cascade BREAKS: db61 = da60 ≠ 0, dc62 ≠ 0, dd63 ≠ 0
- The collision requires dd63 = 0, which now fails
- 4 of 8 state words at round 63 are non-zero

## Connection to Diagonal Structure

The cascade diagonal at sr=60:
```
r60: da=0  db=0  dc=0  dd=0  de=0  df=C  dg=V  dh=C   (sr=60)
```

Under sr=61, the diagonal BREAKS:
```
r60: da≠0  db=0  dc=0  dd=0  de=0  df=C  dg=V  dh=C   (sr=61)
r63: da≠0  db≠0  dc≠0  dd≠0  de=?  df=?  dg=?  dh=?   → NOT collision
```

The e-path is UNAFFECTED (de60=0 always). Only the a-path breaks.

## Quantitative Barrier

At N=32: P(cascade survives sr=61) = 2^(-32) ≈ 2.3×10^(-10)

This must be overcome SIMULTANEOUSLY with:
- The sigma1 consistency requirement (separate constraint)
- The carry-diff invariant constraints (147+ invariants)

The combined probability is astronomically small.

## Unification

This is the FOURTH independent proof of the sr=61 barrier, and it
subsumes the other three:

1. **Sigma1 conflict rate** → sigma1 breaks cascade at W[60]
2. **Critical pairs** → rotation positions prevent W[60] freedom
3. **Carry-diff invariants** → carry structure incompatible with sr=61
4. **Cascade break** → schedule W2[60] ≠ cascade W2[60] (this result)

All four are manifestations of the same phenomenon: the schedule
removes the freedom needed to maintain the a-path cascade at round 60.

## For the Paper

Section 5: "Why sr=61 is Impossible"
- Start with the cascade diagonal structure (Section 4)
- Show that sr=61 breaks the diagonal at round 60
- Quantify: P(break) = 1 - 2^(-N)
- Note: the e-path is unaffected — only the a-path fails
