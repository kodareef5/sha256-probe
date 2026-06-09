---
date: 2026-06-09
status: T1.3 COMPLETE — SOTA SAT+CAS engine imported, built, validated end-to-end on the standard metric
author: macbook-claude (fable model test)
evidence_level: VERIFIED (engine builds + solves real reduced-round SHA-256 collisions; conflict-advantage measured)
---

# T1.3: importing the SOTA SAT+CAS engine into the repo's environment

The four-agent review and Tier 0 both pointed here: the field's record-setting engine for
step-reduced SHA-256 collisions is **SAT+CAS / programmatic CDCL via IPASIR-UP** (arXiv
2406.20072 — plain CaDiCaL stalls at 28 steps, +CAS reaches 38), and the repo had never used
it (it used plain kissat/cadical). This task imports and validates it.

## What was done
1. **Built the CAS solver** `nahiyan/cadical-sha256` (CaDiCaL 1.8.0 + embedded SHA-256
   routines, MIT). Two fixes were required to compile on clang/macOS:
   - Select an encoding in `src/sha256/types.hpp` (the default builds nothing — use the
     **1-bit** Nejati encoding; the 4-bit path is incomplete upstream, missing
     `mendel_branch_4bit` etc.), and enable CUSTOM_PROP + WORDWISE_PROPAGATE + MENDEL_BRANCHING.
   - **Upstream bug**: `sha256.cpp` calls `mendel_branch_1bit()` but never includes
     `1_bit/mendel_branch.hpp` → undeclared-identifier error. Added the include (the fix is
     baked into `setup_sat_cas.sh`).
2. **Built the Nejati collision encoder** (`nahiyan/cryptanalysis/encoders/nejati-collision`)
   and copied its bundled published characteristics into `characteristics/`.
3. **Validated end-to-end.**

## Results — the engine works and the CAS advantage is real

| Instance | CAS engine (cadical-sha256) | plain cadical 3.0.0 |
|---|---|---|
| 21-step (Prokop) | SAT, 201 conflicts | — |
| 24-step (Prokop) | SAT, 239 conflicts | SAT |
| **28-step (Nahiyan)** | **SAT, 361 conflicts** | **SAT, 1044 conflicts** |
| 38-step (Mendel) | hard (no quick solve) | hard |
| 39-step (Nahiyan) | hard (no solve in 90s) | hard |

**At 28-step the CAS engine is ~2.9× more conflict-efficient** (361 vs 1044) — the
programmatic two-bit/wordwise-carry propagation paying off exactly as the paper reports. The
38/39-step frontier instances are genuinely hard for both (consistent with 2406.20072's
hours-to-days timeouts); reaching them is a dedicated-compute task, not a quick benchmark.

## Significance and honest limits
- The repo now has a **working, validated standard-metric collision pipeline** (encoder +
  characteristics + CAS solver) — the R-axis tool it lacked, reproducible via
  `setup_sat_cas.sh`.
- The engine natively solves **standard reduced-round collisions** (Nejati differential
  encoding). Pointing it at a **repo-specific** object (the block-2 absorber) is NOT plug-and-
  play: that object must first be expressed in the Nejati `∇A/∇E/∇W` differential format. That
  encoding bridge is the concrete next R-axis task.
- This **supersedes** the original T1.1 (counting gate) and T1.2 (cb_decide A/B) plans, which
  were about whether CAS-style propagation helps the repo's **cascade** CNFs. Tier 0
  established the cascade direction is a dead end, and this task shows the CAS engine works on
  the standard metric directly — so instrumenting the cascade CNFs for CAS firing is moot.
  The live question is no longer "does CAS help the cascade" but "encode the standard/block-2
  problem for this engine," which is Tier 2 work.

## Reproduce
```
bash headline_hunt/standard_metric/setup_sat_cas.sh
```
