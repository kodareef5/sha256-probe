# BREAKTHROUGH: Algebraic necessary conditions for collision at N=4

ALL 49 sr=60 collisions at N=4 satisfy these algebraic constraints:

## Fixed variables (constant across ALL collisions)
- W1[59] bit 2 = 0 (ALWAYS zero)
- W1[59] bit 3 = 1 (ALWAYS one) 
- W2[59] bit 2 = 0 (ALWAYS zero)
- W2[59] bit 3 = 0 (ALWAYS zero)

## Pairwise constraints (genuine — vary on non-collisions)
- W1[57] bit 0 ≠ W2[57] bit 0 (always differ)
- W1[59] bit 1 ≠ W2[59] bit 1 (always differ)
- W1[60] bit 1 = W2[60] bit 1 (always match)

## What this means
The collision search space at N=4 is NOT 2^32. It's at most 2^28
(after fixing 4 variables) and likely much less with the pairwise
constraints reducing it further.

These are NECESSARY CONDITIONS that any collision must satisfy.
They come from the cascade mechanism: W[59] bits 2-3 being fixed
means the sigma1 cascade input is highly constrained, which in turn
constrains dW[61] and dW[63].

## Key question for N=32
Do analogous fixed-variable conditions exist at N=32? If the MSBs
of W[59] are also constrained at full width, that dramatically
narrows the collision search space.

The other machines should test: does the N=32 collision certificate
(W1[59]=0x9e3ffb08, W2[59]=0x587ffaa6) satisfy bit-level constraints
analogous to what we found at N=4?
