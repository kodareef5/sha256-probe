# Rule 4 @ r=62 / r=63 — design doc

The unified Theorem 4 (locked at 105k+ samples in mitm_residue):

```
For r ∈ {61, 62, 63}: da_r − de_r ≡ dT2_r (mod 2^32)

where dT2_r = dSigma0(a_{r-1}) + dMaj(a_{r-1}, b_{r-1}, c_{r-1})
            = (Sigma0(a1_{r-1}) − Sigma0(a2_{r-1}))
            + (Maj(a1_{r-1}, b1_{r-1}, c1_{r-1}) − Maj(a2_{r-1}, b2_{r-1}, c2_{r-1}))
```

Rule 4 at r=61 trivially reduces to bit-equality (dT2_61 = 0; SHIPPED in commit `99f09ef`).

Rule 4 at r=62 and r=63 requires actual register values:
- r=62: a_61 (varying), b_61 = a_60 (cascade-zero), c_61 = a_59 (cascade-zero in pair-1, cascade-zero in pair-2 BUT they're EQUAL to each other not necessarily equal in absolute value).
- r=63: a_62 (varying), b_62 = a_61 (varying), c_62 = a_60 (cascade-zero).

Wait — under cascade-1, da_57..60 = 0, meaning a1_r = a2_r for r ∈ {57..60}. So a_60 has the SAME 32-bit value in pair-1 and pair-2 (cascade-zero MEANS both pairs have identical value, not just zero diff). This means when we compute Maj(a1_r, b1_r, c1_r) − Maj(a2_r, b2_r, c2_r), the cascade-zero registers (b_61=a_60, c_62=a_60, etc.) drop out as identical operands.

## Concrete dT2_r expressions under cascade-DP

**dT2_62**:
- a_61 has nonzero diff (= dT1_61, see Theorem-4-original derivation).
- b_61 = a_60 cascade-zero; c_61 = a_59 cascade-zero (BOTH have da_59 = da_60 = 0 in pair-1 and pair-2 separately).
- Therefore dMaj(a_61, b_61, c_61) where b_61 and c_61 are cascade-equal:
  ```
  Maj(a, B, C) − Maj(a', B, C)  where B, C are common between pair-1 and pair-2
  ```
  For Boolean Maj: `Maj(x, y, z) = (x & y) ^ (x & z) ^ (y & z)`. With y=Y and z=Z fixed:
  ```
  Maj(x, Y, Z) − Maj(x', Y, Z) = ((x & Y) ^ (x & Z)) − ((x' & Y) ^ (x' & Z))   [in modular arithmetic, treating XOR as bit-vec]
  ```
  Hmm — XOR in modular arithmetic isn't simply representable. The Maj function output is a 32-bit value computed bitwise; subtracting two such values is modular subtraction.

**dT2_63**:
- a_62 has nonzero diff (= dT1_62).
- b_62 = a_61 (varying!).
- c_62 = a_60 (cascade-zero).
- So dMaj at r=63 has TWO varying inputs (a_62 and b_62=a_61) and one fixed (c_62=a_60).

## Implementation sketch

### Data structures

```cpp
struct PartialReg {
    // Each bit: -1 = unassigned, 0 = false, 1 = true
    std::array<int, 32> bits;
    int n_decided = 0;  // count of bits != -1
};

// Track partial register values for both pairs at relevant rounds.
// Indexed by (reg, round, pair).
std::map<std::tuple<std::string, int, int>, PartialReg> partial_regs;

// Reverse lookup: SAT var -> (reg, round, pair, bit, polarity).
struct ActualVarSide {
    std::string reg;
    int round;
    int pair;   // 1 or 2
    int bit;
    int polarity;
};
std::unordered_map<int, ActualVarSide> actual_var_lookup;
```

### Setup (in main(), after varmap load)

```cpp
// For Rule 4 r=62, r=63: track actual a, b, c registers at r ∈ {59, 60, 61, 62}
// for both pairs. Read from varmap.actual_p1 / varmap.actual_p2.
for (auto& [key, lits] : varmap.actual_p1) {
    auto& [reg, round] = key;  // pseudo-syntax
    if (reg == "a" && round >= 59 && round <= 62) {
        for (int b = 0; b < 32; b++) {
            int lit = lits[b];
            if (abs(lit) > 1) {
                actual_var_lookup[abs(lit)] = {reg, round, 1, b, lit > 0 ? 1 : -1};
                solver.add_observed_var(abs(lit));
            }
        }
    }
    // similar for "b", "c" if needed
}
// Same for pair-2 via varmap.actual_p2.
```

### notify_assignment for Rule 4

```cpp
for (int lit : lits) {
    int var = std::abs(lit);
    auto it = actual_var_lookup.find(var);
    if (it == actual_var_lookup.end()) continue;
    const auto& info = it->second;

    // Convert SAT-lit to bit value via polarity.
    int sat_val = (lit > 0) ? 1 : 0;
    int bit_val = (info.polarity > 0) ? sat_val : (1 - sat_val);

    // Update partial register; record undo for backtrack.
    auto& preg = partial_regs[{info.reg, info.round, info.pair}];
    int prev = preg.bits[info.bit];
    preg.bits[info.bit] = bit_val;
    if (prev == -1) preg.n_decided++;
    rule4_undo_stack.back().push_back({info.reg, info.round, info.pair, info.bit, prev});

    // Check if Rule 4 trigger is now ready (e.g., enough bits of a_61 decided
    // to compute dSigma0(a_61) + dMaj(a_61, ...) at r=62).
    try_fire_rule4_r62();
    try_fire_rule4_r63();
}
```

### try_fire_rule4_r62()

The trigger condition: BOTH pair-1's a_61 AND pair-2's a_61 have the SAME bit decided. Then dSigma0 at that bit position can be computed (via the rotation pattern).

Concretely:
- Sigma0(x) = ROTR(x, 2) ^ ROTR(x, 13) ^ ROTR(x, 22)
- Bit i of Sigma0(x) = x[(i+2)%32] ^ x[(i+13)%32] ^ x[(i+22)%32]

So to know bit i of dSigma0(a_61) = bit i of (Sigma0(a1_61) − Sigma0(a2_61)) (modular), we need to know:
- Bits (i+2), (i+13), (i+22) of BOTH a1_61 AND a2_61.

That's 6 bits to be decided to compute one bit of dSigma0, then we use that to compute one bit of dT2_62.

For the Maj part: Maj(a, b, c) bit i = a[i] AND b[i] OR a[i] AND c[i] OR b[i] AND c[i] (3-of-3 majority). In the cascade-DP setup at r=62, b_61 = a_60 (cascade-zero, so a1_60 = a2_60 = some VALUE). c_61 = a_59 similarly.

So bit i of dMaj(a_61, a_60, a_59) where a_60 and a_59 are common:
```
Maj_bit(a, B, C) − Maj_bit(a', B, C) at bit i depends on bit i of a vs a' and bits i of B, C.
```

This is feasible to compute pointwise. The trigger condition is more relaxed than dSigma0: just need bit i of a1_61, a2_61, a1_60, a2_60 (which are equal!), a1_59, a2_59 (equal) all decided.

Once dT2_62 bit i is known, the modular sum `da_62 − de_62 = dT2_62` propagates: if bit i of (da_62 − de_62) is determined as = the known dT2_62 bit i.

But modular subtraction has carry chains! So bit i of (da_62 − de_62) depends on bit i of da_62, bit i of de_62, AND carry-in from bit i-1. This makes propagation more complex than bit-equality.

### Modular sum reasoning (the hard part)

The modular relation `dA[62] − dE[62] = dT2_62` over 32 bits is encoded by a 32-bit subtractor circuit. Each bit propagates a carry:
```
diff_bit_i = dA_bit_i ⊕ dE_bit_i ⊕ borrow_in_i
borrow_out_i = (¬dA_bit_i ∧ dE_bit_i) ∨ (¬(dA_bit_i ⊕ dE_bit_i) ∧ borrow_in_i)
```

For propagation: when both dT2_bit_i and (k bits of dA, dE up to position i) are decided, can deduce remaining bits via borrow chain.

This is exactly what CNF encodes via aux variables and ripple-carry adder clauses. The propagator's value is doing this implicitly without aux clauses.

**Implementation strategy**: maintain a 32-bit "modular diff state" for `dA[62] − dE[62]` with carry tracking. When dT2 bits arrive, propagate to dA/dE bits and back through the borrow chain. Single ~150-line function.

## Estimated LOC + time

- Data structures: ~80 LOC
- Setup loop: ~50 LOC
- notify_assignment hook for actual vars: ~80 LOC
- try_fire_rule4_r62: ~150 LOC (Sigma0 + Maj + modular sum)
- try_fire_rule4_r63: ~150 LOC (similar but different active inputs)
- Reason clauses: ~80 LOC (need to gather all decided inputs)
- Backtrack handling: ~50 LOC

**Total: ~640 LOC. ~2-3 days of focused implementation.**

## Decision gate (per kill_criteria.md)

After Rules 4@r=62/63 ship:
- Run sr=61 force/expose × propagator on/off across the 9 cross-kernel CNFs.
- Compare conflict counts to SAT (or to budget hit) between propagator-equipped and vanilla.
- **Target: ≥10× conflict-count reduction.** If achieved, scale to multi-hour budgets. If <2×, kill the bet (per existing kill_criteria).

## Why this matters

Rule 4 at r=62/63 enforces a constraint that:
- CNF cannot express directly without 32-bit aux variables and ripple-carry adders (~30-60 clauses per modular sum).
- The aux/ripple encoding bloats Mode A's CNF significantly (Mode A vs Mode B size delta is ~30%).
- A propagator can enforce the same constraint at runtime without the bloat AND with conditional firing only when needed.

If Rule 4 at r=62/63 gives meaningful pruning (≥10× conflict reduction), the propagator becomes the FIRST cascade-DP search mechanism that exposes the structural picture's r=62/r=63 modular invariants directly to CDCL.

If it doesn't, the structural picture is purely descriptive — informative for analysis but not for solving — and the bet's headline-class hypothesis is exhausted.
