# Novel Directions: Thinking From What We Know

## What we uniquely know (that nobody else does)

1. The sr=60 collision uses a TWO-CASCADE mechanism:
   - Cascade 1: W[57] zeros da → shift register propagates db→dc→dd (rounds 57-59)
   - Cascade 2: W[60] zeros de → shift register propagates df→dg→dh (rounds 60-63)
   - W[58], W[59] are "compatibility" words — they don't zero anything, they just
     need to not break the cascades

2. The phase transition is SHARP:
   - sr=60 (W[60] fully free): SAT
   - sr=60.5 (5/8 bits of W[60] enforced at N=8): UNSAT
   - At N=8, the collision needs ≥50% of W[60] bits free
   - At N=10, it needs ≥70% free

3. sigma1 is bijective on GF(2)^32:
   - For any target W[60], there's exactly ONE W[58] that produces it via sigma1
   - The cascade doesn't need W[58] for anything else — it's a "pass-through" word

4. Only 0x17149975 cracked sr=60. Other candidates timed out at 24h.

5. The Jacobian shows W[60] has 33% influence vs 50% for W[57-58] — it does
   targeted work (zeroing de) rather than broad mixing.

## Direction 1: The sigma1 bridge (algebraic MITM)

Since sigma1 is bijective, the MITM bridge is closed-form:

```
Forward: For any W1[57], compute state at round 59.
         This determines what W1[60] NEEDS to be for de60=0.
         Call this target_W1[60].

Bridge:  W1[60] = sigma1(W1[58]) + C1  (schedule rule)
         → W1[58] = sigma1_inv(target_W1[60] - C1)
         There's EXACTLY ONE W1[58] that produces the required W1[60].

Check:   Does this forced W1[58] produce a valid state at round 58?
         Specifically: does it keep the cascade 1 propagation intact?
```

The key insight: W[58] has DUAL DUTY — it drives round 58 AND determines W[60].
But we've shown cascade 1 doesn't need W[58] for zeroing (da58=0 comes from
the shift register, not from W[58]). So W[58] only needs to "not break anything"
at round 58 while also producing the right W[60].

The question: how often does the sigma1-forced W[58] "break" round 58?

THIS IS COMPUTABLE. For each of 2^32 W1[57] values:
1. Compute target_W1[60] for de60=0
2. Invert sigma1 to get forced W1[58]
3. Simulate round 58 with that W[58]
4. Check if cascade 1 still propagates (db58=0 is automatic from shift,
   but does the e-register error stay manageable?)

If even 1 in 2^32 works, we have a collision without SAT.

## Direction 2: Partial schedule compliance (sr=60.5)

The phase transition data says:
- At N=8: 4/8 bits of W[60] enforced → SAT. 5/8 → UNSAT.
- At N=10: transition is at ~3/10 bits.
- Extrapolating: at N=32, the transition might be at ~10-16 bits enforced.

What if we enforce ONLY the MSBs of W[60] via sigma1 (they propagate most
through the cascade) and leave the LSBs free? This gives us:
- More schedule compliance than sr=60
- More freedom than sr=61
- Sits exactly on the phase transition

The encoding: fix the top K bits of W[60] to sigma1(W[58])_{top K}, leave
the bottom 32-K bits free. Sweep K to find the transition at N=32.

This is a PRECISION INSTRUMENT — we can measure exactly how much schedule
freedom the collision needs, to the BIT.

## Direction 3: Why is 0x17149975 unique?

4 other candidates ran 24h with 8 solvers each. Zero SAT. Only 0x17149975
cracked (with seed=5 at 12h). What's different?

Hypothesis: the cascade mechanism has a "resonance" condition. The two
cascades (rounds 57-59 and 60-63) need to ALIGN in timing — cascade 1
must deliver dd59=0 just as cascade 2 begins at round 60. This alignment
depends on the specific round-56 state, which depends on M[0].

Testable: compute the "cascade alignment metric" for each candidate:
- How close is the natural dd59=0 condition to being satisfiable?
- What's the HW of the state difference at round 59 for the best W[57]?
- Does the de57 error correlate with cascade 2's requirements?

If the alignment metric predicts 0x17149975's uniqueness, we can SEARCH
for candidates with even better alignment.

## Direction 4: Multi-block (completely unexplored)

Block 1: Achieve a near-collision at sr=58 (6 free words, very easy).
Leave a small residual (say, 1-2 registers differing by a few bits).

Block 2: The IV for block 2 is the output of block 1. We CHOOSE this IV
by choosing block 1's message. So block 2 starts with a custom IV that
has a small known difference.

Wang-style message modification in block 2 (with full 512-bit message
freedom) can absorb small IV differences. This is literally how all
practical SHA-1 collisions work.

The question: how small does block 1's residual need to be for block 2's
Wang modification to handle it? Stevens (2013) handled SHA-1 IV diffs
with ~60 bits of freedom. We have 512 bits of freedom in block 2.

## Direction 5: Near-collision relaxation

Instead of requiring all 8 registers to match at round 63, require only 7.
This is MUCH easier (one fewer constraint). Then analyze which register
is the "hardest" to match and whether a small additional search can fix it.

From the Jacobian analysis: reg h (the shifted old-e register) has the
LOWEST density (32% at N=32). It's the least influenced by the free words.
So it's the natural candidate to leave unmatched.

Encoding: sr=60 with eq_word for registers a-g only (skip h).
If SAT: we have a 7/8 near-collision. Then search for the h-fix separately.

## Priority

1. **Direction 1 (sigma1 bridge MITM)** — this is the most novel and directly
   exploits our unique knowledge. Can be computed without SAT solvers.
2. **Direction 2 (partial compliance)** — precision measurement, easy to encode
3. **Direction 3 (uniqueness)** — understanding leads to better candidates
4. **Direction 5 (near-collision)** — easy variant, quick experiment
5. **Direction 4 (multi-block)** — hardest to implement, biggest potential payoff
