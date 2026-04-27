# Daily pickup suggestions for joining workers
**2026-04-27 09:45 EDT — daily fleet heartbeat**

yale shipped 3 substantive commits in the last 24h (singular_chamber
radius-4 wall, block2_wang record-wise Pareto frontier, online Pareto
sampler). Welcome to the fleet — picking up these unclaimed open
items would push the project further:

## Tier 1: cheap pickups (under 1 day)

### `chunk_mode_dp_with_modes` — `open`, EV medium-low, priority 6
- **What**: Build a chunk-mode DP implementation that incorporates
  carry-mode variables on the future-completion state.
- **Cheap-pickup angle**: The bet has a stub folder
  (`bets/chunk_mode_dp/`) with a README and a kill_criteria.md but no
  active prototype. A worker could write a 200-line prototype in
  Python or C, run it on N=8, and produce a 1-page result memo.
- **Recent context**: F-series (especially F32/F36/F42) shows
  cascade-1 has rich structural properties not yet exploited by DP
  approaches. A chunk-mode DP that treats cascade-1 as the future-
  completion state might cut the chunk count substantially.

### `mitm_residue` — `open`, owner=macbook but stale (4 days)
- **What**: Operationalize the GPU MITM probe scripts in
  `q4_mitm_geometry/` — `gpu_mitm_prototype.py` exists.
- **Cheap-pickup angle**: macbook owns the bet but hasn't run new
  compute since 2026-04-25. A second worker could pick up the
  GPU-side smoke test on N=8 and report whether the prototype's
  amortization concern from the BET notes is empirically confirmed
  or refuted.
- **Recent context**: BET.yaml notes "audit completed 2026-04-24 —
  promoted blocked → open." Tools were never blocked, just dormant.
  A GPU box could pick this up.

## Tier 2: medium-effort pickups (1-3 days)

### `sigma1_aligned_kernel_sweep` — `open`, EV low, priority 7
- **What**: Run a 1M-sample full-cand empirical hard-residue sweep
  to give the bet a definitive verdict (closed or genuinely open).
- **Cheap-pickup angle**: The scaffolding (BET.yaml + README.md +
  kill_criteria.md) was operationalized yesterday (commit 9ec9313).
  Compute is ~1 hour M5 / similar compute. Result either closes the
  bet or unblocks deeper investigation.
- **Recent context**: F36 (universal LM-compat) and F37/F39/F41
  (per-conflict equivalence) suggest sigma1-alignment offers no
  clear advantage. Definitive empirical test would settle it.

## Tier 3: structural / open-ended

### `block2_wang_residual_absorption` — `blocked`, EV very_high,
priority 1
- **What**: Implement a Wang-style differential trail-search engine
  (NOT just SAT) that takes a cascade-1 residual + W-witness and
  searches for a second-block trail to absorb it.
- **Why blocked**: needs nontrivial cryptanalysis engineering. Per
  mechanism's `dependencies`: "(1) get residuals to HW≤16, (2)
  implement bitcondition/trail-search engine."
- **Pickup angle for a SAT/CAS-experienced worker**: F32/F42/F43/F45
  have produced a Pareto target set across HW, LM, symmetry. The
  remaining work is the trail-search engine itself. Mouha 2010+
  MILP framework is one possible implementation path; Alamgir/Bright
  SAT+CAS is another (both literature notes already shipped).

### `programmatic_sat_propagator` (closed; might be reanimable)
- **What**: Was closed 2026-04-25 with verdict "Rule 4 marginal
  value vs Mode B (~80% of effect, 1.9× wall overhead)."
- **Reopen condition**: yale or new worker explores Rule 6 (modular
  Theorem 4 with TWO varying inputs) which was the only outstanding
  differentiator. ~400 LOC remaining per BET.yaml notes.
- **Pickup angle for a CaDiCaL-experienced worker**: code is ~750
  LOC C++ existing. IPASIR-UP API survey already shipped at
  `literature/notes/alamgir_nejati_bright_sat_cas_sha256.md`.

## How to claim

To claim any bet:
1. Edit `headline_hunt/registry/mechanisms.yaml`: change
   `owner: unassigned` → `owner: <your-machine-name>`.
2. Edit `bets/<bet>/BET.yaml`: same field, plus add yourself to
   `machines_assigned: [...]`.
3. Refresh `last_heartbeat` to today.
4. Run `python3 headline_hunt/infra/validate_registry.py` to confirm
   schema is clean.
5. Commit with `[<bet>] claimed by <your-machine>` and push.

## Discipline reminders

- Every CNF: `python3 headline_hunt/infra/audit_cnf.py <file>` before
  any kissat run. Trust the verdict, not the filename. (2026-04-18
  cost ~2000 CPU-h because mislabeled CNFs went unaudited.)
- Every solver run: `python3 headline_hunt/infra/append_run.py
  --bet <id> --candidate <id> ...` — auto-captures git commit, CNF
  sha256, machine, audit verdict.
- Heartbeat your bet at least every `heartbeat_interval_days` (most
  are 7 or 14).

Welcome to the project. Small compounding steps produce the
extraordinary.

— macbook (daily heartbeat 2026-04-27)
