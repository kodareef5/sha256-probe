# de61 solver: BUG — XOR-vs-modular conflation. Retract solver, lessons captured.

Wrote `prototypes/de61_solver.py` based on the dCh controllability analysis. Empirical test on 50k triples found 16 "compatible" triples per the solver's check. But verification ran the actual cascade through round 61: **de61 is non-zero on every "compatible" triple** (~0xeffe61d0 etc, not zero).

## The bug

The solver derived:
```
de61 = dh60 + dSigma1(e60) + dCh(e60, f60, g60) + dW[61]   (mod 2^32)
```

and then equated `dCh = (e60 AND ctrl_mask) XOR dg60` (correct in XOR domain) with the modular target `-(dh60 + dW61) mod 2^32`.

**That's wrong.** XOR and modular subtraction differ.

`Ch(e, f1, g1) − Ch(e, f2, g2) (mod 2^32)` is the modular difference of two specific 32-bit integers `A` and `B` whose XOR differs at certain positions. While `A XOR B` has a clean closed form `(e AND df) XOR (NOT e AND dg)`, the modular subtraction `A − B mod 2^32` involves carry chains and does NOT equal the XOR.

Specifically: `A − B = A XOR B − 2·((NOT A) AND B)`, or equivalently `A + 2^32 − B = (A XOR B) + 2·(A AND B)`. The carry adjustment depends on bits where both A and B are 1.

## What's salvageable

The XOR-domain analysis IS correct and IS useful:
- `dCh_xor = (e60 AND ctrl_mask) XOR dg60` ✓
- ctrl_mask HW analysis (~18 bits W1[60]-controllable) ✓

What's NOT correct is the bridge from "control 18 XOR bits of dCh" to "satisfy a 32-bit modular constraint dCh = target."

A real per-triple solver requires Lipmaa-Moriai-style modular-difference analysis:
- For each bit i of dCh (from LSB), determine whether it's:
  - Forced (regardless of W1[60]): if dg60[i] is set and ctrl_mask[i] = 0
  - Bit-i flippable via e60[i]: if ctrl_mask[i] = 1
  - But this is XOR — to map XOR control to modular control, use carry-chain analysis bit-by-bit
- Determine which TARGET modular values are reachable as W1[60] varies

This is genuinely 1-day implementation territory. My 30-minute solver was overconfident.

## Practical implication

The dCh-controllability analysis (~18 bits per triple) DOES give a real complexity signal:
- Per-triple, ~18 bits of XOR control over dCh
- Modular constraint: 32 bits
- True per-triple compatibility rate is determined by carry-chain interactions, NOT by simple "u must fit ctrl_mask"

Empirically (from this attempt's verification): the actual de61=0 hit rate on random samples is much rarer than the solver's 0.039% false-positive rate. Need a CORRECT solver to measure.

## Status

- `de61_solver.py` retained in repo with this bug-note attached. Marked NON-FUNCTIONAL.
- The dch_controllability XOR-domain analysis stands.
- A real solver needs modular-difference algebra; multi-day project documented as TODO.

## Lesson

When the empirical verification fails IMMEDIATELY on the first sample, that's the right time to dig in. Caught in ~5 minutes instead of being treated as truth.

The retraction is the result.
