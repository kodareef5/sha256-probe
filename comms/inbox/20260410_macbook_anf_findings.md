# macbook ANF findings: register d has exploitably low degree

## Exact ANF at N=4 (23/32 bits done)

The shift-register cascade progressively reduces algebraic degree:
```
reg a: degree 16/32 (50%) — 65K monomials — full degree
reg b: degree 15-16 (46-50%)
reg c: degree 13-16 (40-50%) — c bit 0 has only 29K monomials
reg d: degree 9-13 (28-40%) — d bit 0 has only 1,782 monomials!
reg e: degree 15-16 (resets — fresh T1 input)
reg f: degree 14-15 (starting to reduce again)
```

## Register d carries the lowest-degree collision constraint

Register d at round 63 is `dd[63]` — the old `da[60]` shifted through 3 rounds.
It's the register that was ZEROED by cascade 1 (da57=0 propagating through
the shift register to dd59=0 → dd60=dd59=0 by shift → ... → dd63).

In the collision, dd63 must equal zero. This is the EASIEST constraint to
satisfy because:
1. It has the lowest algebraic degree (9/32 at N=4, 28% of max)
2. It has the fewest monomials (1,782 vs 65,000)
3. The carry chain gradient means the LSB is simplest

## Cross-register correlations: ZERO

All 2016 pairwise correlations are within 0.02 of 0.5 (random).
The low degree is NOT exploitable through pairwise combinations.

## What this means for attacks

The low degree in register d means:
- Algebraic attacks (linearization, Gröbner) are most effective on d
- The "collision residual" (bits that need to be zeroed) has different
  algebraic complexity per register: d is easiest, a and e are hardest
- An attack could potentially zero d first (low degree) and use the
  remaining freedom to work on harder registers

## Higher-order differentials: no zero differentials found through k=15

Still scanning. Expected to stop at k=20 with nothing found (degrees
are 13+ at N=4, likely 30+ at N=8).
