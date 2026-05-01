---
date: 2026-05-01
machine: macbook-claude
status: active
---

# macbook-claude status

Direct Claude execution on the same Macbook that hosts macbook-codex's
tmux session. macbook-codex hit its 5h gpt-5.5-xhigh quota wall around
08:43 EDT after pushing F421 (6237322); user directed me to proceed
without codex while quota recovers (reset 13:22 EDT).

## 2026-05-01 ~09:50 EDT

Continuing Path C from F408. Codex's F408 memo recommended a "narrower
second annealing panel around bit28 with more restarts or seed-from-best
perturbations" — that is exactly F427.

- Extended `block2_bridge_beam.py` with a new `--init-W` flag so the
  annealer can seed every restart from a known witness (F408 HW=45
  bit28 witness in this run).
- Ran 24 restarts × 500,000 iterations × max_flips=3 × temp 0.5→0.01
  on bit28 only, seeded from `0x307cf0e7,0x853d504a,0x78f16a5e,0x41fc6a74`.

F427 result: no improvement below HW=45 at this 3-bit-flip radius.
Side finding worth noting: the bridge selector has a higher score peak
at a 3-bit neighbor (HW=47, score=75.333) — bridge_score and HW are
not isomorphic in this geometry. Cert-pin verified (kissat+cadical
UNSAT, audit CONFIRMED, both logged via append_run.py).

This is a clean negative on the headline objective and a useful
mechanism observation on bridge_score's structural reward terms.

Next options (waiting on user direction): wider second-anneal
(max_flips 6-8), seeded refinement of bit3/bit2/bit24, or a
bridge_score-mechanism deep-dive.

## 2026-05-01 ~10:05 EDT — F428

Did the seeded-refinement extension to the other 3 cands in parallel.

bit3 / bit2: stayed at F408 HW=51 (12/12 seeds; robust local optima
at 3-bit flip radius, matching F427's bit28 result).

bit24 BREAKTHROUGH: HW 49 -> 43 (-6). All 12/12 seeds converged to a
single HW=43 W vector. The improvement is a 2-bit W1[60] perturbation
that F408's wider search missed; W57/W58/W59 unchanged. Score also
improves (73.447 -> 79.073). Cert-pin: kissat + cadical both UNSAT,
audited CONFIRMED, logged.

Path C now has TWO sub-floor deep records (bit24 HW=43, bit28 HW=45),
both >12 points below their pre-F408 corpus floors. The W1[60]
dominance across all four cand breakthroughs is suggestive: block-2
residual surface seems to live primarily in W[60].

## Coordination notes

- macbook-codex tmux session `sha256_codex` is still alive and waiting
  on its quota reset; I am not running anything in that session.
- Yale (yale-ROG-Strix-G814JI) shipped F422-F426 on bit24 hotspot
  decomposition while codex was paused. Their F426 closed the bit24
  question — bit24 high-cluster cap96 priority -13.20%, F343 stays best
  for sparse-low-bit cands. F427 (this work) is orthogonal: residual
  W-space search, not CDCL priority.
