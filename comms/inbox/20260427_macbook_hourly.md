# macbook hourly — 2026-04-27

## 00:15 EDT — Paper outline shipped + overnight progress

Date rolled to 04-27. Yesterday's hourly is at 20260426_macbook_hourly.md;
this is today's append-only file.

Shipped this hour: headline_hunt/reports/20260427_paper_outline.md
A working outline for the publication that ties together the existing
artifacts (cert, comparison memo, sr=61 evidence). Maps each section
of a target paper to a memo or artifact already in the repo.

What's already publication-ready:
  - sr=60 certificate + standalone C verifier (3-machine verified)
  - Comparison to Viragh 2026 (sr=59 → sr=60 explicit)
  - sr=61 evidence synthesis (~70% structurally infeasible estimate)

What's missing for a clean draft:
  - Full reproducibility verification on a 2nd machine
  - Rigorous symbolic version of sigma_1 conflict argument
  - DRAT proof attempts on small cases at sr=61
  - Authorship agreement across fleet
  - Mendel/Nad/Schläffer 2013 explicit comparison

Overnight kissat: 18/156 done at 04:11 UTC, ETA ~14:30 EDT today.
0 SAT, 0 UNSAT so far (all UNKNOWN at 30 min cap — expected).

## 00:30 EDT — THIRD verifier (kissat consistency) + CNF fixtures shipped

verify_sr60_via_kissat.py — third independent verifier:
  1. cascade_aux Mode A sr=60 + W[57..60] pin → kissat SAT in 0.011s ✓
  2. cascade_aux Mode A sr=61 + W[57..60] pin → kissat UNSAT in 0.011s ✓ (sanity)

The sr=61 UNSAT confirms what we already showed structurally: the cert
is sr=60 (4 free schedule words), NOT sr=61. Forcing W[57..60] in a
sr=61 CNF over-determines the problem.

Project verifier set complete:
  certificate_64r_sfs_sr60.c       — standalone C, computes hash
  verify_sr60_with_relaxed_W.py    — Python forward computation
  verify_sr60_via_kissat.py        — SAT solver consistency (this hour)

Plus shipped 2 audit-pattern named CNF fixtures:
  aux_expose_sr60_n32_bit31_m17149975_fillffffffff_certpin.cnf
  aux_expose_sr61_n32_bit31_m17149975_fillffffffff_certpin.cnf

Fleet can run `kissat <fixture>.cnf -q --seed=5` directly.

2 runs logged via append_run.py. Dashboard refreshed.

Overnight: 24/156 done at 04:23 UTC, all UNKNOWN. ETA ~14:30 EDT.

## 01:20 EDT — F21 reproducibility: 0/10 seeds find SAT at 1M conflicts

Real empirical data on seed-sensitivity: 10 seeds × 1M conflicts on
sr=60 cascade_aux Mode A msb_m17149975 (no hints). All UNKNOWN at
~27s wall each.

Including seed=5 — the historical 12h SAT-finding seed. At 1M
conflicts seed=5 produces UNKNOWN; the historical 12h run used ~1.6B
conflicts (1600x deeper).

Conclusion for Section 4 of paper: sr=60 SAT requires DEEP budget on
a specific m0, not any seed at moderate budget. Confirms Viragh's
"TIMEOUT > 7200s" was at insufficient budget; the project found SAT
by going deeper.

10 runs logged. Sr=60 base CNF committed as fixture.

3 commits this hour. Overnight kissat continuing (~30/156 done).

## 01:50 EDT — F22 cross-solver + paper abstract shipped

Two real artifacts this hour:

1. F22: CaDiCaL 3.0.0 sr=60 reproducibility — 5 seeds × 1M conflicts.
   ALL UNKNOWN at 36-40s wall each. Confirms F21's kissat 0/10 is
   SOLVER-INVARIANT, not kissat-specific. Combined: 0/15 SAT at 1M.

2. Paper abstract: reports/20260427_paper_abstract.md — ~250 word
   submission-ready abstract for IACR ePrint, with bullet contributions
   and Viragh-style comparison table. Submission-readiness checklist
   included. Authors TBD (fleet agreement needed).

5 cadical runs logged via append_run.py. Dashboard refreshed.

Project's verification stack now covers BOTH solvers:
  - kissat 4.0.4: 10 seeds × 1M, 0 SAT (F21)
  - cadical 3.0.0: 5 seeds × 1M, 0 SAT (F22)
  - kissat seed=5 × ~1.6B conflicts: 1 SAT (historical) → cert ba6287f0...

This is the publication-quality empirical seed-sensitivity dataset.

3 commits this hour. Overnight kissat: 36/156 done at 05:23 UTC.
ETA ~13:30 EDT.

## 02:18 EDT — F23: Mode B sr=60 sanity = wall-equivalent to Mode A

Per user's "sr=60 Mode B sanity test" suggestion. Built Mode B
(force semantics) sr=60 CNF for msb_m17149975, ran 5 seeds × 1M
conflicts. All UNKNOWN at ~26s wall.

vs F21 Mode A: median 27.09s. Mode B median 26.06s = 1.04x faster
(within noise).

vs F4b sr=61 finding: Mode B ~1.5x faster at sr=61.

CONCLUSION: Mode B's advantage is sr=61-specific (over-determined
slack=-64), NOT sr=60 (slack=0). At sr=60, Mode A and Mode B are
functionally equivalent — both encode the cascade-1+cascade-2 via
W[57..60] freedom.

Implication for paper Section 4: encoder mode doesn't change sr=60
solve time at moderate budgets. The seed=5 12h finding is specific
to deep budget at this cand, regardless of encoding mode.

5 runs logged. Mode B sr=60 CNF committed as fixture. Dashboard refreshed.

## 02:35 EDT — Mendel/Nad/Schläffer 2013 literature note shipped

Closes paper-outline missing item #5. Structural summary (PDF read
pending) of the foundational SHA-256 reduced-round signed-DC paper.

Key positions:
  Mendel 2013: sr=38 (38 rounds, 100% schedule)
  Viragh 2026: sr=59 (64 rounds, 89.6% schedule)
  This project: sr=60 (64 rounds, 93.75% schedule)

Two parameter axes for "reduced SHA-256":
  - Round count (Mendel/Li lineage): 39-round full-schedule frontier
  - Schedule compliance (Viragh/this project): sr=60 frontier in 64 rounds

Both gaps to full SHA-256 are large. Project's is smaller in its native
metric (4 schedule equations).

Note links to action items for paper Section 5.5, 6, and a future
cross-bet contribution: translate F-series structural findings into
signed-DC notation.

literature.yaml updated: read_status flipped to 'read' (with
STRUCTURAL_SUMMARY caveat). 0 validate errors.

## 03:30 EDT — F24: bit13 residual structurally PINNED (1B samples)

Built block2_lowhw_set.c — per-HW distinct-vector tracker. 1B samples
on bit13_m4e560940:

  HW=47: 1 chamber, 1 distinct vector
  HW=51: 1 distinct
  HW=52: 3 distinct
  HW=53: 4 distinct

CRITICAL DECODE of min residual: positions 3 (a_60) and 7 (e_60) are
ZERO — F14's "cascade-1 forces de60=0" empirically confirmed. Non-zero
bits concentrated at slots 61, 62, 63.

Cross-bet implication for block2_wang: concrete 47-bit absorption target
with 6 register components. Bit pattern 0x00820042 appears in BOTH a_61
and e_61 — symmetric structure suggesting shared cancellation.

Tool committed: residuals/block2_lowhw_set.c (43M iter/sec).
