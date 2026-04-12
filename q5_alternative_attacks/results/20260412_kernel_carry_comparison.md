# Cross-Kernel Carry Structure: Invariants Don't Predict Collision Count!

## Data at N=4

| Kernel | Fill | Collisions | Invariant% | Carry entropy |
|--------|------|-----------|-----------|--------------|
| MSB (bit 3) | 0xf | 49 | 54% | 5.61 |
| MSB (bit 3) | 0x0 | 22 | 73% | 4.46 |
| **Bit 1** | **0x0** | **146** | **67%** | **7.19** |

## Finding: invariant fraction is NOT a universal predictor

Within the MSB kernel: more invariants → fewer collisions (73%→22 vs 54%→49).
ACROSS kernels: more invariants → MORE collisions (67%→146 vs 54%→49)!

The relationship depends on the kernel structure. Different kernels create
different CASCADE GEOMETRIES — some geometries are more constrained AND
more productive simultaneously.

## The bit-1 kernel cascade

Bit 1 enters the round function through the SECOND bit position of
Sigma1(e). At N=4, Sigma1 rotations are {1,1,3}. The bit-1 perturbation
interacts with rotation amount 1 — making the cascade propagation
more ALIGNED with the rotation structure.

The MSB (bit 3) interacts with rotation amount 3 — less alignment,
fewer but more loosely constrained collisions.

## Implication for N=32

The optimal kernel at N=32 is NOT the MSB. Sigma1 rotations at N=32
are {6,11,25}. The bit position that best aligns with these rotations
should be tested. Candidate: bit 6 (matches first Sigma1 rotation at N=32).

MACBOOK CONFIRMED: bit 6 gives 1644 collisions at N=8 (6.3x MSB).
The Sigma1 alignment hypothesis is supported.

## Evidence level: VERIFIED at N=4 (exhaustive)
