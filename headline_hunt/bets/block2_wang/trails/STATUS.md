# Block2_wang trails/ — Milestone status as of 2026-04-26 04:30 EDT

| Milestone | Status        | Result / Outcome                                           |
|-----------|---------------|------------------------------------------------------------|
| M0 (N=8)  | ✅ DONE        | q5/backward_construct.c. 260 collisions, 17.12× speedup, 100% verified. |
| M10       | ✅ DONE        | backward_construct_n10. 946 collisions at N=10, 100% verified, 117s wall on 10 OMP threads. |
| M10-strat | ✅ VERIFIED    | Stratified BF (w57∈[0,64)): 72/72 BF↔BC matched, 15.67× wall speedup. |
| N-inv probe| ✅ EVIDENCE   | Theorem 4 + R63.1 + R63.3 hold 8192/8192 at N ∈ {8,10,12,14,16,18}. |
| Hardlock  | ✅ EVIDENCE    | de58 hardlock fraction is candidate-specific (8-57%), not N-specific. |
| M12       | ⏸️ PARTIAL PASS | 32 collisions in first 1/128 of W57 space at N=12 over 43 wall-min on contended M5; ALGORITHMICALLY VALIDATED. Full sweep aborted (extrapolated 92hr contended / 8hr clean). Schedule overnight when CPU is quiet, with buffer cap raised. |
| M16       | ⏸️ DESIGN-STUCK | Naive enumerate-all has 6.6 PB storage at N=16. Signature reduction needed before implementation. |
| M16-MITM forward | ✅ VALIDATED  | m16_mitm_forward at N=8 + N=10: 200/200 records pass cascade-1 + state_59 verification. State_59 is full-resolution (10K samples → 100% distinct). 2026-04-26. |
| M16-MITM backward | ❌ DESIGN-GAP | Foundation memo design fails: cascade-2 trigger is 1-bit modular constraint on (pair1.s59, pair2.s59), giving codim-1 surface as "required state." No filtering advantage. Do NOT implement as written. 2026-04-26. |
| M32-MITM  | ⏸️ FUTURE      | Multi-machine compute, multi-day. Needs M16-MITM design first. |

## Open question (the BET's hard problem right now)

**At N=16+, what signature scheme produces non-trivial MITM match-hits?**

The naive state_59 signature is too wide (8N bits at N=16 = 128, vs 2^48 forward
records → 2^-80 hit probability). Need ≤48 effective signature bits.

Candidate signature reductions (untested):
- **Cascade-zeroed bits**: cascade-1 forces da[57..59]=0, so the differential
  signature is concentrated in (e, f, g, h, b, c, d). Signature width drops
  from 8N → ~4N (still 64 at N=16; insufficient).
- **R63 modular relations**: R63.1 (dc=dg) and R63.3 (da-de=dT2) reduce
  effective signature dimensionality. At r=63 down to 4 d.o.f. = 4N bits =
  64 at N=16. Still insufficient.
- **Rounded signature**: hash state_59 to k-bit signature (k = 32 ideal).
  Requires accepting false-positive matches that get verified post-hoc.
  Worth pricing out: 2^48 forward × 2^48 backward / 2^32 sig = 2^64 candidate
  pairs to verify. Per-pair ~1µs verify = 2^64 × 1µs = ~600 yr. Not a fix.
- **Constraint-narrowed enumeration**: only emit forward records whose
  state_59 satisfies cascade-extending W's exactly (which is automatic in
  our setup), AND whose state_59 falls in a SPECIFIC subspace targeted by the
  backward enumeration. Requires designing what subspace.

## Recommendation

The block2_wang bet's NEXT sharp decision is the M16-MITM signature design. Not
implementation. **Ship a design memo before any more code.** Then either:
- Find a working signature → implement → run → check.
- Conclude no working signature exists in this architecture → graveyard the
  bet honestly with a kill memo about MITM signature sparseness at N=16.

Either is a real result. The DESIGN is the gate.

## What we know for sure (EVIDENCE-level)

- Backward construction algorithm is correct at N=8, N=10. Theorem 4 + R63
  relations hold at all tested N. Algorithmic foundation is solid.
- Speedup ~15× at N=10, decay ~0.92 per N-bit increment. Predicts diminishing
  but positive returns through N=12.
- M12 is feasible single-machine in ~8 hr.
- M16 single-machine pure-BC is INFEASIBLE (350+ days).
- MITM at N=16+ requires SIGNATURE REDUCTION, not naive port.
- M16-MITM forward enumerator IS correct at N=8 + N=10 (200/200 each;
  10K samples confirm state_59 is full-resolution = 100% distinct).
- M16-MITM backward design as foundation-memo-written: filter has 0 power.
  See M16_BACKWARD_DESIGN_GAP.md.

## What we DON'T yet know

- Whether M12 produces a useful collision count (still running).
- Whether ANY signature reduction makes MITM match-fire at N=16.
- Whether block2_wang reaches headline at N=32 or stalls before.

## Files

- `backward_construct_n10.c` / `_n10` — N=10 BC solver (M10 PASS).
- `backward_construct_n10_strat.c` / `_strat` — stratified BF + BC for speedup verification.
- `backward_construct_n12.c` / `_n12` — N=12 source + binary (M12 in flight).
- `m16_mitm_forward.c` / `_n10` / `_n8` — M16 forward enumerator (VALIDATED 2026-04-26; m16_mitm_forward_validator.py + M16_FORWARD_VALIDATED.md).
- `m16_mitm_forward_validator.py` — independent Python re-runs each forward record's cascade-1 chain to confirm correctness.
- `M16_FORWARD_VALIDATED.md` — N=8 + N=10 validation memo (200/200 each).
- `M16_BACKWARD_DESIGN_GAP.md` — explicit critique of foundation-memo backward design; recommends NOT implementing as written.
- `n_invariants.py` — parameterized N invariant probe (Theorem 4, R63.1, R63.3).
- `n10_invariants.py`, `n10_hardlock.py` — N=10-specific scripts.
- `M10_RESULT.md` — M10 outcome with stratified-BF speedup VERIFIED.
- `M12_RESULT_template.md` — fill-in-the-numbers when M12 completes.
- `M16_MITM_FOUNDATION.md` — q5/mitm_cascade_sr60.py linkage + design-stuck honest assessment.
- `STATUS.md` — this file (durable summary of where we are).
