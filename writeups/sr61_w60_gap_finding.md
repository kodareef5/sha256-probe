# sr=61 W[60] Algebraic Gap: Quantitative Analysis

## Summary

Measured the algebraic distance between the cascade-triggering W[60] (from
the verified sr=60 collision) and the sr=61 schedule-mandated W[60] for the
same message prefix. **The gap is HW ~16 — essentially random distance.**

This means the sr=60 solution does NOT live "near" the sr=61 schedule
manifold. Whatever closes sr=61 (if anything) must use a structurally
different cascade, not a small perturbation of the known sr=60 solution.

## Method

In sr=61, W[60] is no longer free:
```
W[60] = sigma1(W[58]) + W[53] + sigma0(W[45]) + W[44]
```

Of these, W[44], W[45], W[53] are pre-schedule (precomputed from M[0]+fill).
Only W[58] is "tunable" — and it's also a free schedule word, so it has dual
duty: drive round-58 state evolution AND determine W[60].

For the verified sr=60 collision (M[0]=0x17149975, fill=0xffffffff):

| Quantity | M1 | M2 |
|---|---|---|
| W[58] (cert) | 0xd9d64416 | 0x4b96ca51 |
| sigma1(W[58]) | 0xeabfc240 | 0xbc70690b |
| const = W[53]+sigma0(W[45])+W[44] | 0x928f1765 | 0xf41843af |
| **W[60] cert** (cascade trigger) | **0xb6befe82** | **0xea3ce26b** |
| **W[60] rule** (sr=61 mandated) | **0x7d4ed9a5** | **0xb088acba** |
| XOR diff | 0xcbf02727 (HW=17) | 0x5ab44ed1 (HW=16) |
| ADD diff | 0x397024dd (HW=15) | 0x39b435b1 (HW=16) |

The cert W[60] and rule W[60] differ by ~half their bits — random distance.

## sigma1 Bijectivity

Computed sigma1's F_2 rank = **32**. sigma1 is bijective on F_2^32. So for
any target W[60] value, there exists exactly one W[58] that would produce
it via the rule.

For the cert's W[60] targets, the required W[58]_alt values are:

| | M1 | M2 |
|---|---|---|
| W[58]_alt | 0x75cd0ad1 | 0x8f232558 |
| W[58] cert | 0xd9d64416 | 0x4b96ca51 |
| HW(W[58]_alt XOR cert) | 17 | 17 |

So the W[58] needed to make sr=61 reach the cert's W[60] is at random
distance from the cert's W[58]. Substituting W[58]_alt into the cert
breaks rounds 58, 59 entirely.

## Implications

**This rules out:** the sr=60 solution being "almost" an sr=61 solution.
There's no near-neighborhood approach. Any sr=61 solution must use a
fundamentally different (W[57], W[58], W[59]) triple where W[58] simultaneously
drives state evolution AND produces a usable W[60] via the schedule rule.

**This does NOT rule out:** the existence of sr=61 solutions in general.
The 192 bits of freedom (3 free words × 2 messages) against 256 bits of
collision constraint give -64 bits of slack — feasible only if cascade
structure provides enough "free" propagation. The shift-register structure
of SHA-256 can save 32 bits per cascade step, so a 2-step cascade saves
64 bits. So sr=61 is right at the edge of feasibility.

**Why the SAT race is informative:** With ~45 hours × 24 cores on a
candidate where sr=60 took 12 hours on one core, we're running a fair
test. A negative result (eventual UNSAT or persistent timeout with SLS
floor evidence) would be strong evidence that sr=61 is impossible for
this candidate family.

## Next experiments suggested by this finding

1. **Different candidates may give different `const` values.** A candidate
   where `const_M1 - const_M2` happens to align with a useful sigma1 image
   might be much easier. Worth scanning candidate space with this metric.

2. **Single-message cascade analysis.** For each candidate, find the
   W[58]_alt for both messages and compute the resulting round-58 state
   delta. If small, the cascade might still close.

3. **Joint W[58] feasibility region.** The set of (W1[58], W2[58]) such
   that BOTH messages produce cascade-triggering W[60] values is a 2D slice
   of the 64-bit space. Characterizing it could guide a hybrid SAT/MITM.

## Evidence level

**EVIDENCE.** Direct algebraic measurement on the verified sr=60
certificate. Reproducible from `q5_alternative_attacks/sr61_w60_gap_analysis.py`
and `sigma1_linearity.py`. Single candidate — gap might be smaller for
other candidates (untested).
