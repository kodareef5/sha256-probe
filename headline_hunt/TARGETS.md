# Headline Targets

*From GPT-5.5 meta-consultation (2026-04-24). See `consultations/20260424_secondwind/`.*

## The three headline classes we're hunting

Anything that doesn't fit one of these is not a headline. Stop pursuing it.

### 1. Break one more schedule-compliance round

> **A TRUE sr=61 semi-free-start collision at full N=32 SHA-256.**

Why headline-worthy: unambiguous, certificate-verifiable, directly extends
the public boundary, not dependent on mini-SHA extrapolation.

Why hard: previous "sr=61 racing" was on mislabeled sr=60 CNFs (CNF audit
2026-04-18). True sr=61 has had only ~1800 CPU-hours since.

**Bet:** `bets/sr61_n32/` — *budget-capped at 10k additional CPU-h*.

### 2. Turn compactness into construction

> **A SAT-free / compilation-based collision finder that beats the known
> search barrier on a nontrivial reduced-SHA target.**

Why headline-worthy: the BDD O(N^4.8) result says the collision manifold
is structurally polynomial. Constructive evidence would be a TCS+crypto
crossover result.

Why hard: all known compilation paths (BDD Apply, bottom-up SDD, d4,
derived encoding) hit blowup. The construction route is unproven.

**Bets:**
- `bets/cascade_aux_encoding/` — local-offset auxiliaries to escape the encoding/treewidth conflict.
- `bets/kc_xor_d4/` — d4 with XOR-preserving preprocessing on standard CNFs.
- `bets/programmatic_sat_propagator/` — propagator that exposes carry modes, cascade offsets, schedule-derived W[60].

### 3. Change mechanism class

> **A Wang/rebound/multi-block style attack that bypasses the single-block
> cascade boundary entirely.**

Why headline-worthy: Bridges beyond what schedule-compliance arguments cover.

Why hard: requires a real bitcondition/trail engine, not just SAT. Human-time
expensive. Naive multi-block was closed (HW=7 at N=8 too large); Wang with
tailored differential trails is structurally different and untried.

**Bets:**
- `bets/block2_wang/` — **highest EV/CPU-hour per GPT-5.5**.
- `bets/mitm_residue/` — MITM on the 24-bit hard residue (tools exist, not operational).
- `bets/chunk_mode_dp/` — chunk-mode DP with mode variables.

## Clean-stop criteria

If after a bounded, instrumented sprint:
- no SAT,
- no UNSAT proof,
- no solver-behavior improvement from new encodings,
- no structural predictor,

across **all five priority bets** under their stated kill criteria, then:

> Stop hunting. Publish the boundary/paradox paper. Or pause indefinitely.

The clean stop is real and acceptable. The point of the registry is to
make sure we *recognize* it instead of drifting back into seed farming.

## What is NOT a headline

- Another paper section on the existing sr=60 result.
- More seed farming on unchanged CNF encodings.
- Marginal speedup on already-closed approaches.
- Reduced-N results that don't extend or compose to N=32.

If the work doesn't pass one of those filters, log it in the relevant
mechanism entry but don't burn more CPU on it.
