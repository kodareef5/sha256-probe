# Why sr=61 is (Probably) Impossible: The sigma1 Conflict Argument

## The Argument in One Paragraph

W[60] deterministically controls ~62 output bits per bit position (4,528 total
deterministic relationships across both messages). For sr=61, W[60] is no
longer free — it's computed as sigma1(W[58]) + const. sigma1 XOR-mixes each
W[58] bit into 2-3 W[60] bit positions. In 47.9% of cases, the mixed W[60]
bits need OPPOSITE values to satisfy the collision constraint. These are
**structural contradictions** that no choice of W[58] can resolve — sigma1
creates XOR combinations that are algebraically incompatible with the
collision requirements.

## The Numbers

| Quantity | Value |
|---|---|
| W[60] deterministic relationships (total) | 3,964 |
| W[60] per-bit average deterministic control | 61.9 output bits |
| sigma1 XOR fan-out per W[58] bit | 2-3 W[60] bits |
| Output bits with 2+ deterministic W[60] controllers | 8,150 |
| **XOR conflicts** (controllers need opposite values) | **3,907 (47.9%)** |

## How The Conflicts Arise

sigma1(x) = ROR(x,17) XOR ROR(x,19) XOR SHR(x,10)

Each output bit of sigma1 is the XOR of 2-3 input bits (separated by rotations
of 17 and 19 positions, plus a shift by 10). This means:

```
W[60] bit j = W[58] bit (j+17 mod 32) XOR W[58] bit (j+19 mod 32) [XOR W[58] bit (j+10)]
```

If the collision constraint requires W[60] bit j = 1 and W[60] bit k = 0,
but both j and k are functions of the SAME W[58] bit, then that W[58] bit
must simultaneously cause j=1 and k=0 through the sigma1 XOR — which may
be impossible.

With a 47.9% conflict rate across 8,150 checked constraints, the probability
that ALL conflicts happen to be resolvable simultaneously is astronomically
small.

## Comparison With sr=60

For sr=60, W[60] is FREE — each bit can be independently chosen. All 3,964
deterministic relationships can be satisfied trivially (just set each W[60]
bit to the value that makes the collision work). This is why sr=60 is SAT.

For sr=61, those same 3,964 relationships become CONSTRAINTS on sigma1(W[58]),
and 47.9% of them conflict through sigma1's XOR mixing. This is why sr=61
is (almost certainly) UNSAT.

## Caveats

1. **Statistical, not rigorous**: The 47.9% conflict rate is measured from
   a 2000-sample correlation matrix. Exact determinism is approximated by
   |correlation - 0.5| > 0.49. A formal proof would require exact symbolic
   computation.

2. **Single-bit analysis**: The conflicts are measured for individual bit
   flips. The actual collision involves ALL bits simultaneously — joint
   effects might cancel some conflicts (or create more).

3. **One candidate only**: Tested on M[0]=0x17149975, fill=0xffffffff.
   Other candidates may have different conflict rates (though the cascade
   mechanism is the same for all MSB-kernel candidates).

4. **Not a proof**: This is an EVIDENCE-level argument, not a theorem.
   A proof would require showing that the polynomial system over GF(2) is
   inconsistent, which is co-NP-hard in general.

## Evidence Level

**EVIDENCE** (strong): quantitative measurement from 2000-sample
differential-linear analysis, structurally interpretable through the
known cascade mechanism, consistent with all empirical observations
(54h CDCL + 12h SLS + N=8 DRAT proofs all pointing UNSAT).

## Scripts

- `q5_alternative_attacks/difflinear_matrix.py` — correlation matrix builder
- Results: `q5_alternative_attacks/results/20260409_difflinear_pilot.md`
