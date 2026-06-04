# bet: linear_lever_gaps

## The bet

The SHA-256 schedule recurrence `W[t] = σ1(W[t-2]) + W[t-7] + σ0(W[t-15]) + W[t-16]`
has four feedback terms. "Gap placement" (Viragh 2026) and every encoder in this
repo enforce held boundary schedule equations using only the `σ1` (t-2) lever —
the exact term the project's own sr=61 impossibility argument blames for the wall.
The two **linear** terms (`t-7`, `t-16`, which enter as the identity) were never
implemented. **Testable claim:** a linear-lever sr=60 instance (free `{54,55,56,57}`,
levers `54→61, 55→62, 56→63`) that the σ1 cascade provably cannot build solves
materially faster than the σ1 sr=60 baseline (paper: timeout; repo: 12h/seed=5).

## Hypothesis (mechanism)

At N=32 both σ0 and σ1 are full-rank bijections (Phase 0), so the benefit is **not**
escaping σ1's image — it is **decoupling**. The σ1-cascade sr=60 chains W[61] and
W[63] onto the single free word W[59] (W[63] has no free lever → over-determined →
the wall). The linear `t-7` terms reach deep enough that each boundary word gets its
own independent free knob {54,55,56}, all controllable while the boundary equations
still hold. Better-shaped freedom at the same zero-slack point.

## Headline if it works

First sr>59 single-block semi-free-start collision found via a *new* gap-placement
lever — and, if it reaches sr=61, the first crack past the wall the project's
impossibility argument calls "as close to a proof as experimental cryptanalysis
gets." (Null outcome: the wall is lever-independent — we kill and pivot.)

## What's built / TODO

- [x] Phase 0: σ-rank run + `lever_feasibility.py` (sr=60 accounting confirmed;
      wall located; configs ranked). See `results/20260530_phase0_*`.
- [ ] Phase 1: `encoders/lever_gap_encoder.py` + `encoders/test_encoder.py` gate.
- [ ] Phase 2: `native_lever_check.py`; N=32 sr=60 probe (audit + solve + log);
      `verify_lever_collision.py`.
- [ ] Phase 3 (only if sr=60 beats baseline): sr=61 with restored freedom.

## How to join

1. Set `linear_lever_gaps.owner` in `../../registry/mechanisms.yaml`.
2. Update `BET.yaml` `owner` and `machines_assigned`.
3. Read `kill_criteria.md` first.

## Related

- Antagonist: `writeups/sr61_impossibility_argument.md`, `sr60_sr61_boundary_proof.md`
  (Thm 5) — the wall this probe tests.
- Reuses: `lib/cnf_encoder.py`, `lib/sha256.py`, `lib/solver.py`,
  `bets/cascade_aux_encoding/encoders/cascade_aux_encoder.py` (build pattern).
- Pivot target if killed: `bets/block2_wang` (two-block connection).
- Supersedes the abandoned root analyzer `04_alternative_gaps.py`.
