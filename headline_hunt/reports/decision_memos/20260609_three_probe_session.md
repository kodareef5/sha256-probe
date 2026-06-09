# Decision memo — three-probe session (2026-06-09, fable model test)

User asked "where would you explore next," then directed "do them all, commit your
findings." Three directions were scoped, executed, and recorded. All three resolve to
**negatives that harden the existing structural picture** — none opens a new headline — but
each closes a previously-open lead *rigorously* rather than by timeout-and-assume.

## A. Treewidth LOWER bound — closes the "compactness → construction" route (NO-GO)

The one genuinely unpursued lead in headline class 2 was GPT-5.4's #1 pick: AND/OR /
d-DNNF / separator-based **decomposition** compilation, which the `chunk_mode_dp`
Myhill-Nerode kill did *not* foreclose (that kill bounds only the linear-order forward-DP
frontier). F211/F212 had only treewidth **upper** bounds (480/699), which cannot decide
feasibility. Added a rigorous **minor-min-width LOWER bound** (`core_treewidth_probe.py`,
verified exact on P6/C6/K7/grid): **tw ≥ 46-51** across 3 cascade CNFs. Beating the ~2^32
barrier needs tw ≲ 32, so a width-bounded compiler provably costs ≥ 2^46 — strictly worse
than the barrier. The linear-order width (≈ collision count) and the tree-order width
(≥ 50) now **both** rule out a small-width decomposition in any order. → negatives.yaml.

## B. forward_propagator.cpp reopen — evaluated, does NOT reopen (confirmed negative)

The diff-aux propagator reopen candidate had sat un-evaluated since 2026-04-25. Built it
against CaDiCaL 3.0.0, fixed the harness (the old `alarm()`-only path SIGKILLed before
stats printed), wired a varmap (`fwdprop_varmap.py`). Result: **0 forward runs over 1M
conflicts** — it never fires, because CDCL never atomically completes a 32-bit free word in
deep search (the same silence that killed the Rule-4 propagator). ~9% overhead, zero
benefit. Reopen criterion not met. → graveyard reopen memo.

## C. block2_wang faithful frontier — ~18 wall confirmed target-independent (kill #1 unfired)

Completed the faithful CV-pinned frontier the 2026-05-30 memo left open: R=16 SAT (0.12s),
R=18 timeout (120s), R=19 timeout (240s), post-FF residual HW=95. The ~18 wall holds on the
*correct* feed-forward + pinned-CV condition — not an artifact of the bet's earlier wrong
target/input. R≥19 stays solver-limited (timeouts, no UNSAT proof, no propagation
contradiction); **kill #1 stays unfired**. Recommend pausing block2_wang on its standing
deliverable; the only unexploited lever (a sparse post-FF residual via block-1 steering) is
gated on the unmet HW-floor dependency. → results memo + BET heartbeat.

## Net

The session reinforces the project's central finding: SHA-256's sr=60 wall and the
multi-block ~18 wall are **structural and robust to the specific technique**. Two more
"maybe there's a clever encoding/compiler/propagator" hopes are now closed with rigor
(a lower bound; a zero-firing measurement; a faithful-condition frontier) rather than left
open as "search-limited." No headline opened; the boundary/structure story is stronger.

## Artifacts
- `bets/cascade_aux_encoding/encoders/core_treewidth_probe.py`, `fwdprop_varmap.py`
- `bets/cascade_aux_encoding/results/20260609_core_treewidth_lower_bound.md`
- `bets/block2_wang/results/20260609_faithful_frontier_R16_R19.md`
- `graveyard/closed_bets/programmatic_sat_propagator/REOPEN_forward_propagator_EVALUATED.md`
- `q5_alternative_attacks/forward_propagator.cpp` (harness fix: conflict-budget)
- negatives.yaml: `cascade_cnf_treewidth_lower_bound_exceeds_barrier`
