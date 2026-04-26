# Kill Criteria

This is a theory/probe bet, not a solver-farming bet.

Kill this first implementation path if:

1. Representative N=32 candidates all have local defect rank 32 under random
   samples and structured fill/chamber samples.
2. Gate-degeneracy metrics (`f=g` for `Ch`, `b=c` for `Maj`, and related
   equality sheets) show no enrichment among low-defect-HW or unusual-rank
   samples.
3. The probe only rediscovers already-known `de58` or hardlock structure
   without touching the actual sr=61 defect map.

Do not kill the broader singular-chamber concept unless nonlinear fiber-size
tests and nonzero gate-invisible trail attempts also fail.

## Redirected path

The naive local-rank version is already weak: sampled full-N candidates kept
rank 32. The currently open path is nonlinear:

```text
D = S(W58) - R(W59)
S(W58) = C + sigma1(W58 + off58) - sigma1(W58)
```

Kill this redirected finite-difference path only if:

1. Compressed `S(W58)` plateaus cannot be predicted from `off58` better than
   direct enumeration.
2. Reachable `off58/off59` chambers do not produce reusable target-alignment
   predictors.
3. The reduced-N posterior carry filters fail to transfer into any
   pre-hit classifier on held-out reduced-N chambers.
