# Sigma1 Rotation Boundary Hypothesis

**Date**: 2026-04-11
**Evidence level**: VERIFIED at N=8, testing at N=10,12,16

## The Hypothesis

The sr=60/61 phase transition is controlled by the sigma1 rotation positions.
At each word width N, there is a **critical pair** of W[60] schedule bits
whose enforcement creates an irreconcilable constraint. This pair corresponds
to the two rotation amounts of the sigma1 function.

## Prediction Table

| N  | sigma1 rotations | Predicted critical pair | Result |
|----|-----------------|------------------------|--------|
| 8  | {4, 5, >>2}     | (4, 5)                | **CONFIRMED: SAT in 111s** |
| 10 | {5, 6, >>3}     | (5, 6)                | Testing... |
| 12 | {6, 7, >>4}     | (6, 7)                | Testing... |
| 16 | {9, 10, >>5}    | (9, 10)               | Testing... |
| 32 | {17, 19, >>10}  | (17, 19)              | NOT YET TESTED |

## Evidence at N=8

Full sr=61 (all 8 bits enforced): UNSAT in 63s
Predicted pair (4,5) freed: **SAT in 111s**
Control pair (0,1) freed: UNSAT in 167s

All 28 pairs tested (exhaustive): (4,5) is the ONLY SAT pair.

## Why These Positions?

The sigma1 function at N=8 is: sigma1(x) = ROR(x, 4) XOR ROR(x, 5) XOR (x >> 2)

At bit positions 4 and 5, the two rotated copies of W[58] OVERLAP —
bit 4 of sigma1(W[58]) depends on bits {0, 1, 2} of W[58] via the
two rotations, while bit 5 depends on bits {0, 1, 3}. This creates
CONSTRUCTIVE INTERFERENCE: the same input bits affect both output
positions through different rotation paths.

When we enforce W[60][4] = sigma1(W[58])[4] + C AND W[60][5] = sigma1(W[58])[5] + C,
the two constraints share input bits and create an irreconcilable conflict
with the collision requirement. Freeing either one alone isn't enough
(still UNSAT), but freeing both breaks the deadlock.

## Scaling to N=32

At N=32: sigma1 = ROR(x, 17) XOR ROR(x, 19) XOR (x >> 10)
The rotation overlap zone is at bit positions 17 and 19.
If the hypothesis holds, freeing W[60] bits 17 and 19 from the schedule
would make sr=61 SAT at N=32.

This would mean the sr=61 barrier in full SHA-256 is controlled by
exactly 2 bits at the sigma1 rotation boundary.

## Restricted ANF Confirmation

At N=8 restricted to 32 cascade variables, h[0] has degree 8/32 = 25%.
This exactly matches the N=4 result (degree 8/32 = 25%). The algebraic
degree is invariant to word width when #free_variables is constant.
