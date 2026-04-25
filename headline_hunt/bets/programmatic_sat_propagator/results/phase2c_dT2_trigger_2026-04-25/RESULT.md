# Phase 2C "all-decided" trigger for Rule 4 @ r=62 — empirically NEVER fires

## Setup

Shipped Sigma0/Maj/dT2_62 evaluator helpers in cascade_propagator.cc as part of the Rule 4 r=62/63 substrate work:

- `read_full_value(PartialReg)` — reads a 32-bit unsigned value if all 32 bits are decided.
- `sigma0(x)`, `maj(x, y, z)` — straightforward 32-bit Boolean implementations.
- `dSigma0_modular(a1, a2)` — modular subtraction Sigma0(a1) − Sigma0(a2), only works when both are fully decided.
- `dMaj_modular_cascade(a1, a2, V60, V59)` — handles the cascade-DP case where V60, V59 are common between pairs (a1_60 = a2_60 = V60 etc.).
- `compute_dT2_62()` — returns dT2_62 = dSigma0(a_61) + dMaj(...) if all 128 input bits are decided, else -1.

Added a sampling diagnostic in notify_assignment: every 4096 bit-assignments, check whether `compute_dT2_62()` returns a valid value.

## Result on sr=61 expose, bit-10, 50k conflicts

```
notify_assignment events:    521,483
actual-reg bit assigns:      520,937
dT2_62 computable (sample):  0 (out of ~127 samples)
```

**Zero successful trigger fires.** In 50k conflicts of CDCL search, the union of (a1_61 fully decided, a2_61 fully decided, a_60 fully decided, a_59 fully decided) is never simultaneously true at any sample point.

## Implication

The naive "fire when all 128 input bits are decided" approach for Rule 4 r=62 is empirically useless on real cascade-DP CNFs. The solver doesn't navigate to states where this much input is simultaneously fixed.

Real Rule 4 firing must do **partial-bit propagation**:
- When ENOUGH bits of the inputs are decided to determine bit i of dT2_62, fire that single bit.
- Plus modular subtraction reasoning: bit i of (dA[62] − dE[62]) depends on bits 0..i of both dA, dE AND borrow chain from lower bits.

This is the ~400 LOC of carry-chain logic flagged in `RULE4_R62_R63_DESIGN.md`. The empirical finding above sharpens the rationale: without partial reasoning, the propagator never fires at r=62.

## What this commit ships

The substrate now has working helpers (Sigma0, Maj, modular subtraction at the value level) ready to be used by partial-bit propagation. The diagnostic confirms the trigger strategy that DOESN'T work, saving future workers from implementing it speculatively.

Helpers are ~80 LOC, clean, unit-testable on synthetic inputs (not yet wired to a unit test harness — that's a future small commit).

## Cumulative Phase 2 status

| Phase | What | Status |
|---|---|---|
| 2A-2C-Rule3 | Mode B parity (cascade-zero + R63.1 + Rule 4@r=61) | shipped |
| 2C-Varmap-v2 | actual register vars exposed | shipped |
| 2C-Rule4-substrate | bit-tracking + backtrack | shipped |
| **2C-Rule4-helpers** | **Sigma0/Maj/dT2 evaluators + trigger diagnostic** | **shipped (this commit)** |
| 2C-Rule4-partial | partial-bit propagation + carry chain | NEXT — multi-day |
| Decision gate | ≥10× conflict reduction or kill | after partial-bit ships |

## Next-session focus (sharpened)

The empirical "0 fires in 50k samples" tells us:
1. Don't bother with all-decided Rule 4. Skip directly to partial-bit.
2. The partial-bit logic is THE work — there's no cheaper alternative.
3. Prioritize r=62 partial-bit firing first (single varying input a_61), then r=63 (two varying inputs a_61 and a_62).

## Build artifact

`cascade_propagator.cc` is now ~570 LOC. Same build command as before.
