# CASCADE CHAIN: SAT-FREE collision finder — 49/49 in 2 seconds

## What we built

C implementation that finds sr=60 collisions WITHOUT a SAT solver:
1. Compute dW[57] = constant (from the da57=0 theorem)
2. For each W1[57]: compute dW[58] = f(W1[57]) (from da58=0)
3. Enumerate remaining 4 free words exhaustively

## Results at N=4

- 49/49 collisions found — PERFECT MATCH
- 2 seconds (was ~100s unconstrained)
- Search space: 2^24 (was 2^32) — 256x reduction
- N=5 running now (2^30, estimated ~30s)

## What this means

The cascade constraints are COMPLETE — they characterize the collision
set exactly. Every collision satisfies dW[57]=const and dW[58]=f(W1[57]),
and no collisions are missed.

This is a SAT-FREE collision finder. At larger N, the remaining 4*N free
bits per combination still grow exponentially, but the cascade reduces the
exponent from 8*N to 6*N — which at N=32 means 2^192 instead of 2^256.

## Can we extend further?

The question: can we also constrain W2[59] and W2[60] (like we did for
W2[57] and W2[58])? This would reduce to 2^(4*N) — at N=32 that's 2^128.

The answer depends on whether dd59=0 and de60=0 provide additional
constant relationships. The cascade order shows d zeros at round 59
(from the shift register, not from W[59] directly), so dd59=0 might
not constrain W[59] the same way da57=0 constrains W[57].

Need to check: does the cascade mechanism provide constraints on dW[59]
and dW[60] that further reduce the search space?
