# Phase 2C Rule 3 — Mode FORCE three-filter `dE[61..63] = 0`

## What this adds

Rule 3 of SPEC.md: enforce `dE[61] = dE[62] = dE[63] = 0` (Theorem 3 three-filter — the cascade-DP equivalent of full r=63 collision per the boundary proof).

Implementation: 96 bit-level zero-forcings (3 rounds × 32 bits) added to the existing zero_regs list. Same machinery as Rules 1+2.

## Test (sr=61 expose, bit-10, 50k conflicts)

| Mode | wall | cb_propagate fires |
|---|---:|---:|
| Propagator OFF | 7s | 0 |
| Propagator ON (Rules 1+2+3+5+4@r=61) | **3s** | **480** |

Of the 480 fires:
- 416 from zero-forcing (Rules 1+2+3): cascade diagonal + dE[60]=0 + dE[61..63]=0
- 32 from Rule 5 (dc_63 = dg_63)
- 32 from Rule 4@r=61 (dA[61] = dE[61])

Note: 416 zero-forcings is less than the 352 + 96 = 448 expected. The encoder's constant propagation folded ~32 dE[63] bits to const-FALSE (because the Mode A expose CNF includes the r=63 collision constraint, which forces dE[63]=0 at compile time). The propagator correctly skips those — `n_const_already += 1` in the setup loop.

## Speedup is now 2.3×, down from 4× in Phase 2B

The Phase 2B (Rules 1+2 only) speedup was 4×. After adding Rules 3+5+4@r=61, it's 2.3×. Why?
- Each additional Rule fires N propagations at level 0, each with reason-clause bookkeeping. CaDiCaL has to process those before normal CDCL.
- The added rules don't open new CDCL shortcuts on this particular CNF — they enforce constraints already implied by the r=63 collision in expose mode.
- So the fixed setup cost slightly outweighs the marginal pruning benefit.

This is a real but expected pattern: **adding more rules helps only if they unlock NEW pruning beyond Mode B**. Rules 3+5+4@r=61 are by-construction equivalent to Mode B's cascade structure → same solution space → no NEW pruning.

The genuine gains will come from **Rule 4 at r=62 and r=63** (modular Theorem 4 with actual register values), which CNF cannot express directly. That's the value-bearing rule and the next phase.

## Cumulative Phase 2 status

| Phase | Rules in propagator | LOC | Mode A speedup |
|---|---|---:|---:|
| 2A | API smoke | n/a | — |
| 2B | 1+2 | 280 | 4.0× |
| 2C-Rule5 | 1+2+5 | 370 | 4.0× |
| 2C-Rule4@r61 | 1+2+5+4(r=61) | 400 | 3.5× |
| **2C-Rule3** | **1+2+3+5+4(r=61)** | **400** | **2.3×** |
| 2C-Rule4@r62/63 | + 4@r=62, r=63 | TBD | **TBD — value-bearing** |

## Build artifact

Same single-file C++ source, ~400 LOC. No new build deps.

## Why this is still useful

The propagator now provides Mode B-equivalent cascade structure DYNAMICALLY, without modifying the CNF. Future use cases:
1. **Fleet workers can run Mode A (expose) CNFs through the propagator and get Mode B-equivalent solving.** No need to regenerate CNFs.
2. **Composability**: can layer additional structural rules without re-encoding.
3. **Phase 2C-Rule4@r62/63 is unblocked** by the v2 varmap shipped earlier this session — actual register values are now exposed, enabling modular sum reasoning.

## What's NOT yet shown

The propagator hasn't yet found SAT faster than vanilla cadical on a hard instance. That would require:
- A long enough budget to find SAT in some encoding.
- Rules that expose pruning CNF cannot derive (Rule 4 at r=62/63).

Both are dedicated multi-day work. Phase 2C closes Mode B parity; Phase 2C-Rule4@r62/63 starts the value-add.
