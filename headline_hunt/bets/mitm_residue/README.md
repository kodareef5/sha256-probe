# bet: mitm_residue — MITM on the 24-bit hard residue

**Priority 5** per GPT-5.5. Status `blocked` — tools exist but not operational.

## The bet

The pause summary identifies a **24-bit effective bottleneck** in the cascade
hard residue (g60/h60). 232/256 anchor bits are "almost free." A forward/backward
MITM keyed on the actual 24 bits — not the whole state — could complete in 2^24-ish
work and bypass the SAT solver entirely.

## Why blocked

Existing partial implementations:
- `q4_mitm_geometry/` scripts 71, 74, 75 — partial / not operational at N=32.

Need to verify what's there, what's stubbed, and what the gap-to-operational is
before this bet can become `open`.

## Headline if it works

> "Sub-2^32 deterministic construction of cascade collision residue at N=32 —
> bypasses SAT entirely."

A constructive cryptanalytic path. Higher novelty even than sr=61 because it changes
the algorithmic class.

## What's built / TODO

- [ ] **Audit q4_mitm_geometry/.** What scripts exist, what works, what's stub.
  Output: `prototypes/audit_summary.md`.
- [ ] **Bit-budget analysis.** Which 24 bits exactly? What's their joint distribution?
  Concrete answer required before tables.
- [ ] **Forward table** keyed on the actual residue.
- [ ] **Backward table** symmetric.
- [ ] **N=8 / N=10 prototype** — must be measurably faster than existing structural
  solver on those scales OR the 2^24 estimate at N=32 is suspect.

## Related

- Independent of `block2_wang` mechanism class (both bypass single-block boundary differently).
- If both succeed, double headline; if one succeeds the other's priority drops.
