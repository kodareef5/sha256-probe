---
date: 2026-04-29
bet: cascade_aux_encoding × programmatic_sat_propagator
status: STRUCTURAL — entire dW57 row is over-constrained at 2-bit adjacent level
---

# F344: dW57 row is over-constrained — 32 clauses (1 unit + 31 adjacent pairs)

## Setup

F340 found W57[22:23] has exactly one forbidden polarity. F341 found
dW57[0]=1 forced. F344 enumerates ALL 32 single bits + ALL 31 adjacent
pairs (dW57[i], dW57[i+1]) on m17149975/bit31 sr60 force-mode CNF.

13 min wall (32 + 31 = 63 cadical 5s budget probes per bit-config × ~3
sub-probes per).

## Result

```
dW57 single-bit UNSAT positions: 1
  dW57[0]: forced=1 (var12397, inject +12397)
  All other dW57[i] for i ∈ [1, 31]: no fast UNSAT in either polarity

dW57 adjacent-pair UNSAT positions: 31 / 31 (ALL adjacent pairs!)
  (dW57[0], dW57[1]) forbidden=(0, 0) inject [12397, 12398]
  (dW57[1], dW57[2]) forbidden=(0, 1) inject [12398, -12399]
  (dW57[2], dW57[3]) forbidden=(0, 1) inject [12399, -12400]
  (dW57[3], dW57[4]) forbidden=(0, 0) inject [12400, 12401]
  ... all 31 pairs ...
  (dW57[30], dW57[31]) forbidden=(0, 1) inject [12427, -12428]
```

## Findings

### Finding 1 — dW57 row is FULLY over-constrained at 2-bit level

ALL 31 adjacent pairs (dW57[i], dW57[i+1]) for i ∈ [0, 30] have exactly
one forbidden polarity. Cadical fast-UNSATs each in 0.05-0.15s (much
faster than the 5s budget).

This is a UNIVERSALLY DENSE constraint surface. The cascade-1 hardlock
at round 57 produces a chain of 2-bit blocking clauses that, taken
together, restrict dW57 to a small subset of 2^32 possible values.

### Finding 2 — Forbidden-polarity pattern

ALL 31 pairs have forbidden polarities of the form (0, ?) — the LOWER
bit's "0" value is always part of the forbidden combination. The upper
bit varies:

```
i=0:  (0, 0)
i=1:  (0, 1)
i=2:  (0, 1)
i=3:  (0, 0)
i=4:  (0, 0)
i=5:  (0, 1)
i=6:  (0, 0)
i=7:  (0, 0)
i=8:  (0, 1)
i=9:  (0, 0)
i=10: (0, 1)
i=11: (0, 1)
i=12: (0, 0)
i=13: (0, 0)
i=14: (0, 1)
i=15: (0, 0)
i=16: (0, 1)
i=17: (0, 1)
i=18: (0, 0)
i=19: (0, 0)
i=20: (0, 0)
i=21: (0, 1)
i=22: (0, 1)  ← yale F384 finding
i=23: (0, 1)
i=24: (0, 0)
i=25: (0, 1)
i=26: (0, 0)
i=27: (0, 0)
i=28: (0, 0)
i=29: (0, 0)
i=30: (0, 1)
```

The upper-bit pattern (0/1) per i seems irregular. Let me see if it
matches any structural property — bits where (0,1) forbidden vs (0,0)
forbidden — I'll skip detailed algebra here, but worth investigating.

### Finding 3 — Logical equivalent of the constraints

Each forbidden polarity (a, b) at bit pair (i, i+1) translates to a
2-literal clause:
  - (0, 0) forbidden → "dW57[i] OR dW57[i+1]" (at least one must be 1)
  - (0, 1) forbidden → "dW57[i] OR NOT dW57[i+1]" (i=1 implies i+1=1; or contrapositive)

Combined with dW57[0]=1 (forced unit), the system propagates:
  - dW57[0] = 1
  - From (0, 0) at (0, 1): dW57[0] OR dW57[1] is satisfied by dW57[0]=1, so dW57[1] is FREE
  - From (0, 1) at (1, 2): dW57[1] = 0 → dW57[2] = 0; if dW57[1] = 1, dW57[2] is free

So the constraints are conditional implications, not forced unit chains.
The combined system has many SAT models; CDCL still has work to do at
the rest of the search space.

### Finding 4 — Structural interpretation: subtraction carry chain

dW57 = W2[57] - W1[57] mod 2^32 in cascade_aux force-mode is encoded
via a ripple-borrow subtractor (per encoder source). Each bit position
involves:
- a borrow IN from lower bit
- producing a borrow OUT to higher bit

The 31 adjacent-pair constraints are likely Tseitin clauses for the
borrow chain. CDCL conflict analysis finds:
- For some carry configurations, the values (dW57[i]=0, dW57[i+1]=fixed)
  would require IMPOSSIBLE borrow propagation (given the cascade target
  cascade1_offset_57).
- That's why exactly ONE polarity per pair is UNSAT.

### Finding 5 — Combined clause count for Phase 2D propagator

Per cand, dW57 row alone provides:
- 1 unit clause (dW57[0])
- 31 pair clauses ((dW57[i], dW57[i+1]) for i ∈ [0, 30])
- Total: 32 forced/blocking clauses

For W58 / W59 / W60, similar enumeration would likely find more clauses
(though F342 showed dW58[0]/dW59[0]/dW60[0] are NOT single-bit forced —
adjacent pairs not yet tested).

## Why dW57 is densely constrained

The cascade-1 hardlock at round 57 is the FIRST round of cascade
absorption. The subtraction `W2[57] - W1[57] = cascade1_offset_57`
(mod 2^32) is a 32-bit equation with a known RHS (computed from the
schedule pre-round-57). For any specific RHS, there's typically ONE
valid pair of (W1[57], W2[57]) values per cascade kernel — meaning
dW57 takes a SPECIFIC 32-bit value for each cand.

So dW57 is essentially DETERMINED by the cand metadata. The 32 clauses
F344 mined are a sound (but maybe not complete) characterization of
that determination expressed as 2-bit constraints.

If the cand's dW57 were FULLY determined by these 32 clauses (which
remains to be verified), the propagator could pin all 32 dW57 bits
immediately at solver init — saving ALL of CDCL's eventual derivation
of those bits. Major potential speedup.

## What's next

(a) **Verify dW57 is FULLY determined by the 32 mined clauses**:
    enumerate the SAT solutions to the constraint system, see if dW57
    has a unique value or a small family. If unique, propagator can
    inject 32 unit clauses (one per bit) directly.

(b) **Mine W58/W59/W60 adjacent pairs**: F344 only swept dW57. The
    cascade hardlock extends through rounds 58-60. Worth a similar
    sweep on those rounds (~10 min each).

(c) **Cross-cand mining**: extend F344 sweep to other 5 cands
    (F340/F342 dataset). Rough estimate: 6 × 13 min = ~80 min total.

(d) **Algebraic derivation**: compute dW57 directly from cand metadata
    (M[0], fill, kernel-bit, sr) algebraically. Skip the cadical
    preflight entirely if formula is closed-form.

## Compute discipline

- 13 min wall (32 single + 31 pair × ~5s avg cadical budget on m17149975/bit31).
- 0 long compute beyond 5s/probe.
- All 63 probe results saved in JSON.

## Implication for cascade-1 search

If dW57 is fully determined by these 32 clauses, then **the cascade-1
collision search at the W57 differential level is structurally
solved**. The propagator could inject all dW57 values immediately,
freeing CDCL to focus on dW58/dW59/dW60 + the absorber compatibility.

This is a major potential propagator speedup. The empirical question
is whether 32 clauses fully determine dW57 (= 32 implicit unit clauses)
or only partially (= ~31 valid SAT solutions remain).

## What's shipped

- F344 full-scan JSON: 1 unit + 31 pair clauses on dW57 row.
- This memo.
- Tool extension (commit `290c7f3`) with `--probe-single-bits scan_all`
  and `--probe-pairs scan_adjacent` modes.
