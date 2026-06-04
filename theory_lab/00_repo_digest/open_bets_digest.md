# Open Bets Digest — the DO-NOT-DUPLICATE list

These are the **active** bets in the working repo's
`../sha256_review/headline_hunt/registry/mechanisms.yaml`. An idea that merely
re-proposes one of these is **not novel** — it's already owned and in flight. If the
lab has a genuine improvement to one of these, the move is to hand it back as a
recommendation against that bet's mechanism entry, not to open a duplicate.

The repo organizes its hunt around three **headline classes**
(`../sha256_review/headline_hunt/TARGETS.md`):
1. **Break one more schedule-compliance round** → a TRUE sr=61 N=32 collision.
2. **Turn compactness into construction** → a SAT-free / compilation-based finder
   that beats the search barrier (exploits the BDD O(N^4.8) result).
3. **Change mechanism class** → a Wang/rebound/multi-block attack that bypasses the
   single-block cascade boundary entirely.

## Active bets

| id | headline class | hypothesis (one line) | status | owner | priority |
|---|---|---|---|---|---|
| `block2_wang` | 3 | structured block-1 residuals can be absorbed by a tailored block-2 Wang differential trail | **in_flight** (paused on direction decision) | macbook-claude | 1 |
| `singular_chamber_rank` | 1 | low-rank sr=61 defect chambers exist where a compressed σ1 plateau aligns with a fat carry-preimage bucket | **in_flight** | linux_gpu_laptop | 8 |
| `math_principles_calibration` | (cross) | REM/tail-law + influence priors + submodular selectors + carry-invariant audits become prescriptive predictors | **in_flight** | yale | 5 |
| `cascade_aux_encoding` | 2 | local-offset auxiliary vars expose cascade structure → drop treewidth without the derived-encoding penalty | **in_flight** | macbook | 2 |
| `true_sr61_n32` | 1 | among 45+ audited N=32 candidates, one is sr=61-SAT within budget | **in_flight** (budget-capped 10k CPU-h) | fleet | 4 |
| `mitm_hard_residue` | 3 | forward/backward MITM keyed on the 24-bit g60/h60 residue finishes in ~2^24 work | **open** | macbook | 5 |
| `kc_xor_d4` (`d4_xor_preprocessing`) | 2 | standard CNF + XOR-aware preprocessing lets d4 compile the N=16+ object | **BLOCKED** | unassigned | 3 |
| `sigma1_aligned_kernel_sweep` | 1 | σ1-aligned N=32 kernels (bits 10/17/19) with best fills solve faster | **open** (deprioritized P7) | unassigned | 7 |

## Per-bet detail

### `block2_wang` — Wang-style block-2 residual absorption  *(highest EV)*
- **Hypothesis:** a single-block cascade boundary does not rule out a **multi-block**
  attack; structured block-1 residuals (d63=h63=0, active set {a,b,c,e,f,g}) can be
  absorbed by a tailored SHA-256 block-2 differential trail using disturbance
  correction, neutral bits, and message modification.
- **Status / what exists:** a real Wang trail engine (`wang_trail_engine.py` +
  `wang_search.py`: condition algebra, carry-aware modular add, fwd+backward
  refinement, constraint-network fixpoint, guess-and-determine), control-validated by
  reproducing the known SHA-256 9-step local collision; plus a CNF encoder validated
  vs the engine. **Result:** an **18-round block-2 absorber EXISTS and is
  oracle-confirmed** (kissat, bit13_HW35, R=18 zero-output-diff) — matches the naive
  SAT 18-round frontier. **R≥19 is a sharp hardness cliff** (UNKNOWN@866s, R=20
  timeout) → the >18 gate is **search-limited, NOT proven-infeasible**. Tailored
  encoding (difference-window + path-pinning) was tried and **both levers fail to beat
  18** (dense HW≥35 residuals admit no sparse characteristic — the never-met HW≤16
  dependency). Caveat: the CNF leaves the chaining value free, so this is a ≥18-round
  absorber TRAIL, **not yet a full 2-block collision pinned to block-1's CV**.
- **PAUSED** pending a user direction decision (pause / tailored CNF / redirect). Kill
  criterion #1 NOT fired.
- **Source:** `mechanisms.yaml#block2_wang_residual_absorption`;
  `../sha256_review/headline_hunt/bets/block2_wang/results/20260526_block2_absorber_VERDICT.md`.

### `singular_chamber_rank` — lower-rank sr=61 defect chambers
- **Hypothesis:** the sr=61 schedule-defect map decomposes as `D = S(W58) − R(W59)`;
  useful chambers occur when sparse-off58 forces a compressed `S` plateau aligned with
  a fat `R` preimage bucket — giving non-uniform (sub-2^-32) local rates the uniform
  cascade proof doesn't bound.
- **Status:** in_flight (joint linux_gpu_laptop + macbook). Iterative descent drove the
  joint frontier from defect61 HW10/tail HW76 down to **defect61 HW4 / tail HW59** at
  full N=32; exact D61 HW4 found on idx0/idx8/idx17. The exact surface is
  carry-fractured; many operator variants (radius-7 ridge, W57-free beam/greedy,
  affine-fiber, GPU off58 chart scans, guard-fiber repair) add d.o.f. but do not beat
  HW4/HW59 or land exact-D60 low-cap representatives. Current wall: a round-56
  T1+T2 modular residue of −8 that radius-4 search can only move to −1 by destroying
  defect57.
- **Source:** `mechanisms.yaml#singular_chamber_rank` (+ ~20 result memos in
  `../sha256_review/headline_hunt/bets/singular_chamber_rank/results/`).

### `math_principles_calibration` — principles → measurement/triage tools
- **Hypothesis:** the April-2026 math-principles framework (REM/tail-law fits,
  influence priors, submodular selectors, carry-invariant audits) can be turned into
  checkable tools that consume existing repo artifacts and yield a **prescriptive**
  (not merely descriptive) predictor on `block2_wang` absorber search and
  `singular_chamber_rank` basin geometry.
- **Status:** in_flight (yale; ~50 commits, 100+ result memos, F340–F384 chain). The
  yale F378–F384 chain produced the W57[22:23] bridge-clause UNSAT pair that seeded
  macbook's propagator chain (clean −9.10% σ=2.68% conflict reduction at 60 s). Kill
  criteria are still **scaffolded/TBD** (created late to close a discipline gap).
- **Source:** `mechanisms.yaml#math_principles_calibration`;
  `../sha256_review/headline_hunt/bets/math_principles/README.md`.

### `cascade_aux_encoding` — cascade-auxiliary CNF encoding
- **Hypothesis:** adding **local-offset auxiliary variables** that mirror the
  cascade-diagonal constraints (instead of full W2 substitution) drops treewidth
  without the derived-encoding penalty (standard ~110 at N=8; derived made it *worse*
  at 181) — enabling either constructive d4 or sr=61 SAT.
- **Status:** in_flight (macbook). SPEC + encoder shipped. Measured Mode-B
  preprocessing speedup is **2–3.4× but front-loaded** (erodes to ~1× by 500k
  conflicts) — the SPEC's "≥10× SAT speedup" was refuted at all tested budgets. Next:
  FlowCutter treewidth on standard+aux CNFs; Kissat on TRUE sr=61 N=10.
- **Source:** `mechanisms.yaml#cascade_auxiliary_encoding`;
  `../sha256_review/headline_hunt/bets/cascade_aux_encoding/encoders/SPEC.md`.

### `true_sr61_n32` — budget-capped fleet sr=61 search
- **Hypothesis:** among 45+ audited N=32 candidates (expanded 2026-04-26), at least one
  is sr=61-SAT reachable in under 10k CPU-hours given encoding/candidate diversity.
- **Status:** in_flight, **budget-capped at 10k additional CPU-h**. ~1800 CPU-h spent
  post-audit with **0 SAT**. EVIDENCE-level closure that de58_size / hard_bit_total_lb
  predictors are search-irrelevant; compute should distribute by candidate coverage,
  not rank. This is the bet "most prone to drifting back into seed farming" — every run
  must be audited and logged. (Note: this is the `bets/sr61_n32/` directory; the
  mechanism id is `true_sr61_n32`.)
- **Source:** `mechanisms.yaml#true_sr61_n32`;
  `../sha256_review/writeups/20260420_project_pause_summary.md`.

### `mitm_hard_residue` — MITM on the 24-bit hard residue
- **Hypothesis:** 232/256 anchor bits are "almost free"; the hard work concentrates in
  g60/h60 (~24 effective bits). A forward/backward MITM keyed on the actual hard residue
  (not the whole state) could complete in ~2^24 work, bypassing SAT.
- **Status:** open (macbook). Tools exist (`cascade_mitm_full.py` recovers the sr=60
  cert at smoke scale; `gpu_mitm_prototype.py` has N=8 feasibility built in but unrun).
  2026-05-25 sub-angle result: the schedule-realizable tail-repair is realizable at the
  round-57..60 interface, but the residue obstacle **reduces to block2_wang's dense
  schedule inverse** and is orthogonal to the gh60 residue — no new tractable path;
  further progress routes through block2_wang's neutral-set machinery.
- **Source:** `mechanisms.yaml#mitm_hard_residue`;
  `../sha256_review/headline_hunt/bets/mitm_residue/results/20260525_schedule_realizable_repair.md`.

### `kc_xor_d4` (mechanism id `d4_xor_preprocessing`) — BLOCKED
- **Hypothesis:** d4 failed at N=8 because the derived encoding broke linear structure;
  standard CNF + XOR-aware preprocessing (Bosphorus/CMS-style XOR recovery) might
  decompose better (the BDD is poly-size, so d-DNNF could be too).
- **Status:** **BLOCKED.** CryptoMiniSat XOR recovery on the cascade CNF returned **0
  clauses** → kill criterion #2 fired. Stays alive only if Bosphorus finds different
  structure. Owner unassigned.
- **Source:** `mechanisms.yaml#d4_xor_preprocessing`;
  `../sha256_review/headline_hunt/bets/kc_xor_d4/results/20260425_xor_recovery_zero.md`.

### `sigma1_aligned_kernel_sweep` — DEPRIORITIZED
- **Hypothesis:** σ1-aligned N=32 kernels (bits 10/17/19) with the best fills give
  faster sr=60 SAT or first sr=61 SAT.
- **Status:** open but **deprioritized (P7, low EV)**. Triaged 2026-05-25: do NOT run
  the fill sweep — its kill criterion is effectively pre-satisfied by
  `negatives.yaml#rotation_aligned_kernels_not_structural` (no structural SAT
  advantage), and the live bit-19 structural-distinction angle is already owned by
  `singular_chamber_rank`. Recommendation: fold the bit-10/17/19 pool into
  `true_sr61_n32`.
- **Source:** `mechanisms.yaml#sigma1_aligned_kernel_sweep`.

---

## Clean-stop criterion (from TARGETS.md)
If, across **all priority bets** under their stated kill criteria, the repo gets *no
SAT, no UNSAT proof, no solver-behavior improvement from new encodings, and no
structural predictor*, the plan is to **stop hunting and publish the boundary/paradox
paper**. The registry exists precisely so the project *recognizes* that clean stop
instead of drifting back into seed farming. The lab's job is to surface a genuinely
new foothold *before* that stop is reached — not to re-energize a bet that has cleanly
stopped.
