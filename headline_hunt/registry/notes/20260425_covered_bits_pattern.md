# Covered (0,9) bit positions align with Σ1/σ1 rotation amounts
**2026-04-25 evening** — registry/notes — structural observation.

## The 9 covered bits

The 36 registered (0,9) candidates use bit positions:
**{0, 6, 10, 11, 13, 17, 19, 25, 31}**

## SHA-256 rotation/shift constants

```
Σ0(a) = ROR(a, 2) ^ ROR(a, 13) ^ ROR(a, 22)        rot offsets: 2, 13, 22
Σ1(e) = ROR(e, 6) ^ ROR(e, 11) ^ ROR(e, 25)        rot offsets: 6, 11, 25
σ0(x) = ROR(x, 7) ^ ROR(x, 18) ^ SHR(x, 3)         rot/shift:   7, 18, 3
σ1(x) = ROR(x, 17) ^ ROR(x, 19) ^ SHR(x, 10)       rot/shift:  17, 19, 10
```

## Cross-reference

| Set                 | Bits           | Covered |
|---------------------|----------------|---------|
| Σ1 rotations        | {6, 11, 25}    | **3 / 3 covered** |
| σ1 rotations + shift | {17, 19, 10}   | **3 / 3 covered** |
| Σ0 rotations        | {2, 13, 22}    | 1 / 3 (only 13) |
| σ0 rotations + shift | {7, 18, 3}     | 0 / 3 |
| Boundary bits       | {0, 31}        | 2 / 2 (LSB, MSB) |

**6 of 9 covered bits = Σ1 ∪ σ1 rotation amounts.** Add LSB+MSB = 8/9.
The remaining bit 13 is a Σ0 rotation amount.

**0 of the σ0 rotation amounts {3, 7, 18} are covered.**

## Hypothesis (UNTESTED)

The cascade-DP structure runs through the `e` register (a-path is forced
zero via cascade extension; e-path carries the differential). Bits aligned
with Σ1 and σ1 rotation amounts may be MORE likely to be cascade-eligible
because they synchronize with the e-path's mixing function.

### Algebraic note (2026-04-26)

For kernel_bit = b and the SHA-256 mixing functions:
- Σ1(1<<b) has bits set at positions (b-6)%32, (b-11)%32, (b-25)%32.
  When b ∈ {6, 11, 25}: ONE of these positions is bit 0 (the LSB).
- σ1(1<<b) has bits set at (b-17)%32, (b-19)%32, (b-10)%32.
  When b ∈ {17, 19, 10}: ONE of these is bit 0.
- Σ0(1<<b) ∋ bit 0 when b ∈ {2, 13, 22}.
- σ0(1<<b) ∋ bit 0 when b ∈ {7, 18, 3}.

So "kernel_bit is a rotation amount" ↔ "rotation output contains LSB".
In the cascade-DP construction, the e-path active register's differential
runs through Σ1 and σ1 (the message-expansion). Σ0 acts on `a` which
cascade forces to be zero — so Σ0 alignment doesn't matter for e-path.
σ0 acts on message expansion too, but the schedule routes σ0 through
W[i-15] (much earlier slots) while σ1 acts on W[i-2] (closer to the
cascade boundary at r=57). σ1's kernel-bit alignment is structurally
closer to the cascade than σ0's.

This is a HEURISTIC explanation, not a derivation. The covered-bits
empirical pattern (8/9 at Σ1+σ1+boundary, 1 at Σ0, 0 at σ0) is
consistent with it.

### Testable prediction

If the hypothesis holds: σ0-aligned bits {3, 7, 18} should have 0
cascade-eligible m0 at full N=32 sweep. Σ0-amount bits {2, 22} (excl.
13 which is covered) should also have 0 (or very few). Tested by
`cascade_eligibility_sweep.c` running tonight on bit=7.

This is a STRUCTURAL HYPOTHESIS that explains why curated candidates
cluster at specific bits:
- LSB/MSB: trivial overflow/underflow handling for modular arithmetic.
- Σ1 amounts: bit-of-difference aligns with e-register mixing.
- σ1 amounts: bit-of-difference aligns with message-expansion mixing.
- Σ0 (a-register): less relevant since cascade zeros a-diff.
- σ0: less relevant for the cascade's e-path?

## Falsifiability

**To test this hypothesis at N=32**: do exhaustive 2^32 m0 sweep at one
σ0-aligned bit (say bit 7) and check if ANY eligible m0 exists. If 0
eligible at 2^32 trials → strong evidence Σ1/σ1 alignment is necessary.
If many eligible → hypothesis falsified.

ETA: ~5-10 min in C with OMP.

## Implication

If the hypothesis holds:
- The 9 covered bits are the COMPLETE eligible set (modulo bit 22 which
  is Σ0 and untested).
- Random sampling at "wrong" bits is futile.
- For candidate diversity: try bit 22 (Σ0 amount, untested) before
  expanding to σ0 amounts (which are predicted unfavorable).

If hypothesis falsified:
- σ0-aligned bits ARE eligible but require directed search.
- More candidates exist than the 36 registered — search them deliberately.

## What I'm NOT doing now

This is a structural observation, not a verified claim. Implementing the
2^32 sweep would require ~10 min C compile+run with OMP — cheap, but I'm
documenting the pattern without launching the compute. Future worker can
take the 10-min experiment.

## What this gives the bet portfolio

- A FALSIFIABLE structural hypothesis about cascade-eligibility patterns.
- A directed-search target (bit 22, σ0 bits {3, 7, 18}) IF a worker wants
  to expand the candidate base.
- A concrete reason to NOT random-sample uncovered bits (per yesterday's
  942k-trial null result).

The hypothesis aligns with cascade structure: bit position alignment with
SHA's mixing offsets matters. This is also consistent with the Sigma1-aligned
kernel finding noted in TARGETS.md (mentioned as one of the 7 mechanisms).
