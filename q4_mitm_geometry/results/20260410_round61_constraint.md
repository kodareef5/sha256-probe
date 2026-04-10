# Round-61 Constraint: The Bottleneck for Cascade Chain Extension

## The constraint

For cascade 1 to extend through round 61, the schedule-derived W[61] must
match the cascade-required dW[61]:

```
sigma1(W2[59]) - sigma1(W1[59]) + sched_const_diff = required_C61
```

Where:
- W2[59] = W1[59] + C59 (cascade chain dependency)
- sched_const_diff = (W1[54] + sigma0(W1[46]) + W1[45]) - (W2[54] + sigma0(W2[46]) + W2[45])
- required_C61 = cascade_dw(state_at_round_60)

This is a constraint on W1[59] of the form:
```
f(W1[59]) := sigma1(W1[59] + C59) - sigma1(W1[59]) = target
```

where target = required_C61 - sched_const_diff.

## Why this is hard

`sigma1` is XOR-linear over GF(2), but `+ C59` introduces carries.
So `sigma1(W1[59] + C59) - sigma1(W1[59])` is a NONLINEAR function of
W1[59]. There's no closed-form inverse.

## Empirical sparsity

For the cert's W1[57], W1[58]:
- 100,000 random W1[59] values: **0 matches** the constraint
- Cert's specific W1[59] (0x9e3ffb08): **matches** (verified)

This means the valid W1[59] set is sparser than 1 in 2^32, even with
the right (W1[57], W1[58]) prefix. We can't find it by random sampling.

## How the cert was found

The cert came from Kissat seed=5 in 12 hours of CDCL search. The SAT
solver implicitly navigated this constraint via backtracking, finding
the rare W1[59] values that work.

## Potential approaches

1. **Solve the constraint directly**: For each (W1[57], W1[58]), enumerate
   W1[59] values that satisfy the round-61 constraint via algebraic
   inversion of the sigma1 difference. This is hard because of the
   carry interaction.

2. **Bit-by-bit propagation**: Start at the LSB of W1[59] and propagate
   constraints upward. Each bit of the constraint determines a few bits
   of W1[59].

3. **Meet-in-the-middle on W1[59]**: Split W1[59] into two halves,
   enumerate each, look for matches.

4. **Use the exact algebraic structure of sigma1**: sigma1(x) = ROR(x,17)
   XOR ROR(x,19) XOR SHR(x,10). The XOR structure may admit pattern
   matching.

## What we know about the constraint

The constraint is the same for ALL random samples (same target, same
C59 given fixed W1[57], W1[58]). So there ARE valid W1[59] values —
they're just sparse. The cert proves at least one exists.

How sparse? If the constraint imposes one 32-bit equation on W1[59]'s
32 bits, the expected number of solutions is 1 (possibly 0 for some
constants). So per (W1[57], W1[58]) we expect ~1 valid W1[59], not many.

That's why random sampling finds nothing: the expected number is 1
in 2^32, and 100K samples is much less than 2^32.

## Implication

The cascade chain framework is correct, but extending it past round 60
requires SOLVING the round-61 constraint, not sampling. This is the
real algorithmic challenge.

## Evidence level

**EVIDENCE**: direct measurement at N=32 with the verified cert.
The constraint is exact, the cert satisfies it, random samples don't.
The sparsity is consistent with one expected solution per
(W1[57], W1[58]) pair.

## Next steps

Build a constraint inverter that, given (C59, target), finds the
W1[59] value(s) satisfying:
   sigma1(W1[59] + C59) - sigma1(W1[59]) = target

Try bit-by-bit forward propagation first.
