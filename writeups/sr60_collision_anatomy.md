# The sr=60 Collision: Anatomy of the Perfect Cascade

## The Certificate

For M[0] = 0x17149975 with fill = 0xFFFFFFFF (MSB kernel):

```
W1[57] = 0x9ccfa55e    W2[57] = 0x72e6c8cd
W1[58] = 0xd9d64416    W2[58] = 0x4b96ca51
W1[59] = 0x9e3ffb08    W2[59] = 0x587ffaa6
W1[60] = 0xb6befe82    W2[60] = 0xea3ce26b
```

Hash: `ba6287f0dcaf9857d89ad44a6cced1e2adf8a242524236fbc0c656cd50a7e23b`

Schedule compliance: 60 of 64 (93.75%). Found by Kissat 4.0.4 --seed=5 in ~12h.

## The Mechanism: Sequential Register Zeroing

The collision uses a **perfect cascade** that zeros exactly one state register
per round. The shift-register structure of SHA-256's compression function
propagates each zero forward automatically:

| Round | Zeros | New zero | Mechanism |
|-------|-------|----------|-----------|
| 56 | 1/8 | da=0 | Candidate property (da[56]=0) |
| 57 | 2/8 | da=0, db=0 | W[57] chosen for da57=0; db57=a56=0 (shift) |
| 58 | 3/8 | +dc=0 | dc58=b57=0 (shift) |
| 59 | 4/8 | +dd=0 | dd59=c58=0 (shift) |
| 60 | 5/8 | +de=0 | W[60] chosen for de60=0 (critical!) |
| 61 | 6/8 | +df=0 | df61=e60=0 (shift) |
| 62 | 7/8 | +dg=0 | dg62=f61=0 (shift) |
| 63 | 8/8 | +dh=0 | dh63=g62=0 → **COLLISION** |

Two free words do the active work:
- **W[57]**: zeros the a-register at round 57
- **W[60]**: zeros the e-register at round 60

The other two (W[58], W[59]) handle schedule compatibility and error management.

## The Two Cascades

The collision works via two overlapping shift-register cascades:

**Cascade 1 (a-path):** da56=0 → db57=0 → dc58=0 → dd59=0

This cascade is "free" — it's a property of the candidate (da56=0) amplified
by the SHA-256 shift register. It costs 1 free word (W[57]) to initiate.

**Cascade 2 (e-path):** de60=0 → df61=0 → dg62=0 → dh63=0

This cascade is triggered by W[60] at round 60, just as the a-path cascade
delivers dd59=0 into the d-register. The timing is perfect: the a-path zeros
reach d just as the e-path needs to begin.

## Why This Matters for sr=61

For sr=61, W[60] becomes schedule-determined: W[60] = sigma1(W[58]) + constants.
The solver loses the ability to freely choose W[60] for de60=0. Instead, W[58]
must serve dual duty: round-58 state propagation AND producing a W[60] that
triggers the second cascade.

This is why sr=61 is fundamentally harder: the two cascades are no longer
independently controllable.

## Schedule Word Differentials

| Word | dW HW | Role |
|------|-------|------|
| dW[57] | 18 | Trigger cascade 1 (da57=0) |
| dW[58] | 12 | Schedule compatibility |
| dW[59] | 11 | Schedule compatibility |
| dW[60] | 14 | Trigger cascade 2 (de60=0) |
| dW[61] | 14 | Schedule-determined |
| dW[62] | 20 | Schedule-determined |
| dW[63] | 18 | Schedule-determined |

Total: 107 active bits across 7 schedule words. None are "weak links" —
the solution distributes error broadly rather than concentrating closure
on a single word.

## Methodological Lesson

The sr=60 collision was found by the PUBLISHED candidate that the original
paper (Viragh 2026) declared UNSAT via constant-folded partitioning. The
timeout was a **single-seed artifact**: Kissat with default seed doesn't find
it, but seed=5 does in 12 hours.

This demonstrates that seed diversity is essential for hard SAT instances.
A single solver run is not evidence of UNSAT.
