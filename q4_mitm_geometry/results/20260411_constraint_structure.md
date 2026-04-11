# sr=60 Cascade Closure Constraint Structure (Empirical)

## The full picture

For sr=60 collisions in the 4-level cascade chain framework:

### Per-prefix structure (for cert prefix)
| Constraint | Matches |
|---|---|
| Round 61 closure | 8,192 (= 2^13) |
| Round 62 closure | 1 |
| Round 63 closure | 1 |
| Full collision | 1 |

The cert (W1[60]=0xb6befe82) is the unique survivor.

### Random prefix sweep
70 random (W1[57], W1[58], W1[59]) prefixes tested with full 2^32 W1[60]
enumeration:

| Metric | Count |
|---|---|
| Prefixes with round-61 match | 2 of 70 (~3%) |
| Round-61 matches per "good" prefix | 8,192 |
| Prefixes with round-62 match | **0 of 70** |
| Prefixes with round-63 match | **0 of 70** |
| Collisions found | **0** |

## Density analysis

Round 61 alone: ~3% of prefixes have any matches, each gives 8192.
- Total round-61 family: 2^96 prefixes × 0.03 × 8192 ≈ 2^96 / 2^5 × 2^13 = 2^104 candidates
- Wait, that doesn't make sense. Let me recompute.

Actually: round-61 closure has 8192/2^32 = 2^-19 acceptance rate per
(prefix, W1[60]) combo. For random (prefix, W1[60]): ~1 in 2^19 satisfies
round 61.

Per prefix (varying W1[60]): 2^32 / 2^19 = 2^13 = 8192 expected. ✓

But we observed: 2 of 70 prefixes have ANY round-61 matches, the rest
have ZERO. This means the 8192/2^32 rate is HIGHLY non-uniform across
prefixes — some prefixes have ALL the round-61 matches concentrated in
them, others have NONE.

This is a structural property: round-61 closure requires the (W1[57..59])
prefix to satisfy SOMETHING beyond cascade chain (which all prefixes
satisfy).

## What determines round-61-closure-having prefixes?

**Key open question**: what feature of (W1[57], W1[58], W1[59]) determines
whether ANY round-61 closure exists for that prefix?

If we can find a fast check (independent of W1[60] enumeration), we can
filter prefixes much more efficiently. Currently we enumerate 2^32 W1[60]
per prefix at 3 sec to know if any pass — too expensive.

## Round 62 difficulty

Round 62 cuts 8192 → 1 deterministically (cert). For random prefixes,
even when round-61 has matches, round-62 fails (we observed 0 in 70 prefixes).

This suggests round-62 closure requires VERY specific prefix structure.
The cert is in a measure-zero set that satisfies all 3 constraints jointly.

## Round 63 implications

Round 63 cuts ~1 → 1 (or 0). For the cert it maintains; for random it
doesn't because round 62 already eliminates everything.

## Algorithmic implications

To find sr=60 collisions efficiently, we need:
1. **Round-61 prefix filter**: identify which (W1[57..59]) admit any
   round-61 match WITHOUT enumerating W1[60]. Filter density ~3%.
2. **Round-62 prefix filter**: identify which round-61-pass prefixes
   ALSO admit a round-62 match. Filter density unknown, very rare.
3. **Round-62 W[60] inverter**: given a prefix, find the unique W1[60]
   that satisfies round-62 (if any) without enumerating 2^32.

Steps 1-2 are the bottleneck. Step 3 is "easy" if we have a structural
characterization.

## Estimated difficulty

Probability cert-like prefix exists: ~1 in 2^96 (if the cert is a
generic point in cascade chain space) or ~1 in fewer if there's
density boost.

We found 1 collision in the 4 known sr=60 cert candidates (0x17149975).
The 4 known da[56]=0 candidates × 2^96 prefixes / cert family = ~2^94
prefixes per known collision = density 2^-94.

At 100M cascade-chain samples/sec on 24 cores, time for 1 collision:
2^94 / 2.4×10^9 = 6×10^18 seconds = 200 billion years. Infeasible.

The cert was found by Kissat in 12 hours because CDCL navigates the
constraint structure intelligently, not by sampling.

## Path forward

Build a CONSTRUCTIVE round-62 W1[60] inverter:
1. Given (W1[57..59]) prefix, derive what W1[60] must satisfy for round-62
2. If a closed-form solution exists, find it directly
3. Then use round-61 and round-63 as fast filters

This requires understanding the algebraic structure of the round-62
cascade closure, which depends on:
- state61 (which depends on W1[60] and schedule W[61])
- schedule W[62] = sigma1(W[60]) + const
- The two must combine to give cascade_dw matching schedule_dW62

## Evidence level

**EVIDENCE**: direct empirical sweep of 70 random prefixes. The "0 round-62
matches in 70 prefixes" finding is robust. The "8192 round-61 matches per
good prefix" is exact for the cert and 1 other prefix observed.

The constraint structure is now known empirically. The algorithmic
challenge is making it constructive.
