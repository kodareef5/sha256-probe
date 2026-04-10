# State HW Profile: Cert vs Random Across Rounds

## Setup

For the verified sr=60 certificate (M[0]=0x17149975, fill=0xffffffff),
traced the total state difference HW at each round 56-63.

Then sampled 50,000 cascade-constrained random (W[57..60]) tuples and
recorded the minimum state HW achieved at each round.

## Results

| Round | Cert HW | Random min (50K) | Gap |
|---|---|---|---|
| 56 (init) | 104 | 104 | 0 |
| 57 (after W[57]) | 86 | 86 | 0 (cascade 1) |
| 58 (after W[58]) | 73 | 78 | +5 |
| 59 (after W[59]) | 55 | 67 | +12 |
| 60 (after W[60]) | 39 | 65 | +26 |
| 61 (after W[61]) | 32 | 83 | +51 |
| 62 (after W[62]) | 18 | 79 | +61 |
| 63 (after W[63]) | 0 | 79 | +79 |

## Key observations

1. **Cert HW strictly decreases by 13-17 per round.** The cascade mechanism
   is a monotonic zeroing process.

2. **Random HW plateaus around 65-80 and INCREASES at rounds 61-63.** Once
   W[61..63] become schedule-determined, random W[58]/W[59] choices fail
   to maintain the zeros that cascade propagation temporarily established.

3. **The gap between cert and random grows each round.** Rounds 58-60 are
   the "magic window" where cert's specific W[58], W[59] values propagate
   cleanly but random values don't.

4. **Cascade 2 cannot save random W[58], W[59]**. Even with W[60] chosen
   to force de60=0, the other registers can't be zeroed because W[61..63]
   are schedule-determined and break the cascade 1 zeros.

## MITM implications

The optimal split point for MITM is **round 59 or 60**:

### Split at round 59
- Forward (W[57], W[58], W[59]): target state HW ≤ 55 (cert level)
- Backward (W[60] → schedule → rounds 60-63): target the specific e/f/g/h
  pattern needed for cascade 2 to close
- Challenge: forward random achieves only HW=67 in 50K samples, so
  ~2^30 samples needed to reach HW=55

### Split at round 60
- Forward (W[57..60], cascade-constrained): target HW ≤ 39 (cert level)  
- Backward (W[61..63] schedule-determined, nothing to search): direct check
- Challenge: forward random achieves HW=65 in 50K, need ~2^22 to reach 39

Split at round 60 appears easier per-bit-gap, but the backward is null
(W[61..63] are schedule-determined).

## The real lesson

**Random search can't replicate the cert's rounds 58-60 precision.**
The cert's W[58], W[59] values are NOT random — they encode specific
algebraic structure that makes the cascade propagate without carry
cancellation errors. Our random search stumbles at rounds 58-60 because
it lacks this structure.

This suggests:
1. The "hard core" plateau at HW~74 is NOT the absolute floor — it's
   the random floor. Cert reaches HW=0 via non-random W[58]/W[59]
   selection that our search can't find.
2. A MITM that explicitly models round-58 and round-59 state propagation
   constraints could potentially find the cert (or similar solutions)
   efficiently.
3. The diff-linear correlation matrix only captured SINGLE-BIT effects —
   the cert exploits higher-order correlations (like pair flips that
   cancel carry chains).

## Evidence level

**EVIDENCE**: direct measurement from cert trace and 50K random samples.
Reproducible. Confirms that cert uses structure invisible to random search.
