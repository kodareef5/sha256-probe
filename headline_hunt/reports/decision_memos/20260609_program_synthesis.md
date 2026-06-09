# Program synthesis: the standard-metric pivot (2026-06-09, fable model test)

A full top-to-bottom pass (Tier 0 → Tier 3) of the angles the four-agent frontier review
produced. The arc is coherent and the conclusion is a **strategic redirect**.

## The one-paragraph version

The repo spent its life optimizing **Viragh's "sr / schedule-compliance" metric**, which a
desk analysis (T0.1) proved is **orthogonal** to the metric the entire field uses (standard
step-reduced collisions: 37 practical / 39 SFS). The repo's deep structural assets (carry
automaton, de58 law, treewidth, sr boundary) are properties of **one construction's solution
manifold** and **do not transfer** (T0.2, H_dead). Meanwhile the field's record-setting
**SAT+CAS** engine — which the repo had never used — was imported, built, and validated here
(T1.3), along with the **decoupling local-collision finder** and **new Boolean-function
models** (T2.1/T2.2). Two tempting angles were cleanly closed (quantum SFS→full T3.1; SMT
"different ring" T3.3). **The project should pivot from the sr-axis to the standard (R-axis)
metric, where it now has the full SOTA toolchain.**

## What each tier established

- **T0.1 (VERIFIED):** Three orthogonal relaxation axes — rounds R / IV-freedom / schedule S.
  sr=60 relaxes only S (4 free words, full 64 rounds, standard IV). The paper's metric is
  internally inconsistent (prefix vs count; gap placement forces the non-contiguous count) and
  its "39 steps = sr 39/39" table is a category error. sr=60 does **not** beat or compare to
  37/39 steps. → `reports/20260609_metric_bridge_lattice.md`.
- **T0.2 (EVIDENCE, H_dead):** The 42% carry invariance is 12%/3% on generic differentials —
  a cascade-manifold property, not a round-function one. Plus metric orthogonality, the repo's
  own ρ≈0 predictor data, and signed-DC subsumption. The sr program characterized one
  construction; it does not transfer. → `reports/20260609_structural_transfer_verdict.md`.
- **T1.3 (VERIFIED):** Imported + built the SOTA SAT+CAS engine (cadical-sha256 + Nejati
  encoder + characteristics; fixed an upstream build bug). Solved 21/24/28-step collisions;
  **CAS is ~2.9× more conflict-efficient than plain cadical at 28-step**. → `standard_metric/`.
- **T2.1/T2.2 (operational):** The decoupling local-collision finder runs (STP-backed) and the
  new Ch/Maj models are in-hand — the message-expansion-first split the repo's monolithic
  block-2 SAT never did.
- **T3.1 / T3.3 (closed):** quantum needs a differential SFS the repo doesn't have; SMT over
  Z/2^32 bit-blasts to the same CNF+SAT. No ring advantage.

## Recommended go-forward (R-axis)

1. **Adopt the standard metric as the project's frame.** Re-baseline TARGETS.md headline
   classes against 37/39 steps, not sr.
2. **First R-axis experiment:** encode a repo-relevant object (a reduced-round collision, or a
   block-2-derived local collision) in the Nejati differential format and drive it with the
   imported CAS engine — the natural use of the `standard_metric/` toolchain.
3. **Run the decoupling pipeline:** local-collision finder (T2.1) → fixed difference-word
   pattern → CAS state search, using the proven 7-round absorption depth to bound the span.
4. **Publish the sr clarification regardless:** the T0.1 lattice + the honest "orthogonal axes"
   framing is a standalone contribution (the "sr Rosetta" note), independent of any new result.

## What NOT to keep doing
- sr=61 grinding, cascade structural analysis, residual-HW minimization, knowledge-compilation
  on the cascade — all either closed (treewidth ≥ 50, Myhill-Nerode, predictors ρ≈0) or shown
  non-transferring. The EV there is spent.

## Artifacts (this session, 2 prior + this program)
- Tier 0: `reports/20260609_metric_bridge_lattice.md`, `reports/20260609_structural_transfer_verdict.md`
- Tier 1/2/3: `standard_metric/` (setup_sat_cas.sh, characteristics/, 3 memos)
- negatives.yaml: `quantum_sfs_to_full_needs_differential_sfs_not_sr` (+ the earlier
  `cascade_cnf_treewidth_lower_bound_exceeds_barrier`)
