# SHA-256 Probe: Proposed Repository Layout

## Philosophy

This repo is organized around **research questions**, not script numbers or
generic categories. Each question is a self-contained workstream that a
different machine/agent can tackle independently.

The key insight: there are at least 5 distinct angles of attack on SHA-256,
and sr=60 schedule compliance is only one of them.

## Top-Level Structure

```
sha256-probe/
│
├── CLAUDE.md                     # Agent operating instructions
├── README.md                     # Project overview for humans
├── CLAIMS.md                     # All claims, ranked by evidence level
│
├── reference/                    # Source material
│   ├── paper.pdf                 # Viragh 2026 "We Broke 92% of SHA-256"
│   ├── paper_notes.md            # Our reading notes / critique
│   ├── prior_art.md              # Related work (Wang 2005, Stevens, Li 2024)
│   └── sha256_spec.md            # Quick-reference spec for agents
│
├── lib/                          # Shared code — THE core asset
│   ├── sha256.py                 # Native primitives + precompute()
│   ├── sha256_fast.c             # C primitives (OpenMP)
│   ├── cnf_encoder.py            # CNFBuilder with constant propagation
│   ├── mini_sha.py               # Parametric N-bit mini-SHA-256
│   ├── mini_cnf.py               # N-bit CNF encoder
│   ├── solver.py                 # Solver wrappers (kissat, cadical, cms)
│   └── scoring.py                # Candidate scoring functions
│
├── q1_barrier_location/          # Q: WHERE is the collision barrier?
│   ├── QUESTION.md               # "At what round does collision become
│   │                             #  impossible, and is it the same for
│   │                             #  all candidate families?"
│   ├── homotopy/                 # Precision homotopy (N-bit scaling)
│   │   ├── parallel_solve.py
│   │   ├── fast_scan.c
│   │   ├── extract_collision.py
│   │   └── results/
│   ├── partition_proof/          # Constant-folded UNSAT evidence
│   │   ├── partition_verifier.py
│   │   ├── drat_checker.sh
│   │   └── results/
│   └── claims/
│       ├── sr59_reproduces.md    # VERIFIED: sr=59 collision exists
│       ├── sr60_unsat_family1.md # EVIDENCE: UNSAT for M[0]=0x17149975
│       ├── sr60_sat_mini.md      # PROVEN: SAT at N=8-21
│       └── scaling_estimate.md   # EXTRAPOLATION: N=32 ~21h
│
├── q2_bottleneck_anatomy/        # Q: WHY does the barrier exist?
│   ├── QUESTION.md               # "What structural feature of SHA-256
│   │                             #  makes sr=60 hard? Is it the schedule
│   │                             #  coupling, carry chains, or something
│   │                             #  deeper?"
│   ├── differential_trace.py     # Wang-style round-by-round analysis
│   ├── dw61_analysis.py          # dW[61] compatibility / constant C
│   ├── ghost_carries.py          # Carry divergence necessity
│   ├── boomerang_validation.py   # Algebraic contradiction diagnostic
│   └── claims/
│       ├── dw61_bottleneck.md    # HYPOTHESIS: dW[61] HW predicts SAT
│       ├── carry_divergence.md   # OBSERVATION: carries required
│       └── boomerang_diagnostic.md # FINDING: 20% accuracy, not predictive
│
├── q3_candidate_families/        # Q: Can we find BETTER candidates?
│   ├── QUESTION.md               # "The current candidate is dead at sr=60.
│   │                             #  Can we find candidates where the barrier
│   │                             #  is weaker or absent?"
│   ├── golden_scanner.c          # M[0] scanner + thermo scoring
│   ├── multi_fill_scanner.c      # Vary M[2..15] padding
│   ├── kernel_sweep.c            # All 32 kernel bit positions
│   ├── mitm_scorer.py            # Score by g60/h60 bottleneck metrics
│   ├── padding_freedom.py        # Exploit M[14], M[15] freedom
│   └── results/
│
├── q4_mitm_geometry/             # Q: Can we solve the HARD RESIDUE directly?
│   ├── QUESTION.md               # "The MITM view shows 232/256 bits are
│   │                             #  'easy'. Can we focus all compute on
│   │                             #  the remaining 24 bits?"
│   ├── forward_anchor.py         # Forward partial state tables
│   ├── backward_anchor.py        # Backward partial state tables
│   ├── hybrid_matchmaker.c       # Meet on compressed anchor signatures
│   ├── bit_breakdown.py          # Which bits are the hard ones?
│   └── claims/
│
├── q5_alternative_attacks/       # Q: What if SAT isn't the right tool?
│   ├── QUESTION.md               # "Wang-style modification, MILP trails,
│   │                             #  Groebner bases, multi-block attacks —
│   │                             #  which standard techniques apply?"
│   ├── wang_modification.py      # Message modification rules
│   ├── milp_trail.py             # Differential trail optimizer
│   ├── algebraic_degree.py       # Groebner / XL analysis
│   └── notes/
│       └── unexplored_techniques.md
│
├── q6_verification/              # Q: Are our results actually correct?
│   ├── QUESTION.md               # "Cross-solver validation, DRAT proofs,
│   │                             #  collision certificate checking."
│   ├── verify_collision.py       # Check sr=59 certificate end-to-end
│   ├── cross_solver.py           # Run same CNF on multiple solvers
│   ├── drat_verify.sh            # DRAT proof generation + checking
│   └── results/
│
├── infra/                        # Build, batch, and orchestration
│   ├── compile.sh                # Build all C tools
│   ├── overnight_batch.sh        # Long-running batch orchestrator
│   ├── parallel_runner.sh        # Multi-core job manager
│   └── Makefile
│
├── writeups/                     # Research narratives (small, focused)
│   ├── 01_paper_review.md        # Original paper analysis + critique
│   ├── 02_sr59_reproduction.md   # How we reproduced the sr=59 collision
│   ├── 03_thermodynamic_floor.md # Refactored from THE_THERMODYNAMIC_FLOOR.md
│   ├── 04_precision_homotopy.md  # Scaling results N=8 through N=21+
│   ├── 05_differential_anatomy.md # Why sr=60 fails (dW[61] analysis)
│   ├── 06_sa_validation.md       # Why SA can't find solutions (important negative)
│   └── 07_audit_findings.md      # Code bugs, doc mismatches, fixes applied
│
└── archive/                      # Original numbered scripts (read-only reference)
    ├── 01_neutral_bits.py
    ├── ...
    └── 89_fast_parallel_solve.py
```

## CLAUDE.md: Agent Operating Instructions

```markdown
# How to Work in This Repo

## Project Goal
Systematic exploration of SHA-256 collision resistance limits.
We probe for weaknesses, characterize barriers, and build tools to push further.
This is NOT about proving one thesis — it's about generating reliable evidence.

## Before You Start
1. Read CLAIMS.md to understand what's established vs hypothesized
2. Read the QUESTION.md in the workstream you're touching
3. Import from lib/ — never reimplement SHA-256 primitives

## Conventions
- Scripts go in the question folder they serve (q1_*, q2_*, etc.)
- Results go in results/ subfolders with timestamps
- New claims go in claims/ with evidence level: VERIFIED/EVIDENCE/HYPOTHESIS/EXTRAPOLATION
- Use lib/solver.py to call SAT solvers (handles timeout, proof logging, cross-validation)
- C tools: add compilation to infra/compile.sh and infra/Makefile

## Evidence Levels
- VERIFIED: independently reproduced, cross-validated, DRAT-checked where applicable
- EVIDENCE: consistent results from multiple approaches, but gaps remain
- HYPOTHESIS: supported by data but not yet tested against alternatives
- EXTRAPOLATION: projected from trends, explicitly flagged as uncertain

## Naming
- No numbered prefixes (multiple agents = collisions)
- Descriptive names: `padding_freedom_scanner.c` not `77_candidate_mutation.py`
- Results: `results/YYYYMMDD_description/`

## What NOT To Do
- Don't claim "proof" without DRAT verification
- Don't extrapolate mini-SHA results to full SHA-256 without caveats
- Don't add scripts that reimplement lib/ functions
- Don't modify lib/ without testing downstream consumers
```

## CLAIMS.md Structure

Each claim gets:
- Statement (one sentence)
- Evidence level
- Supporting scripts/results
- Known caveats
- What would change the assessment

Example:
```
### sr=60 collisions exist at reduced word widths

**Level: VERIFIED**
**Statement:** For every non-degenerate word width N=8 through N=21,
there exists a candidate M[0] and free words W[57..60] that produce
an sr=60 collision in mini-SHA-256(N).

**Evidence:** SAT solver (Kissat 4.0.4) returns SAT with valid assignment.
Collision verified by native computation in extract_collision.py.

**Caveats:**
- Mini-SHA-256 uses scaled rotations and truncated constants
- N=9 is degenerate (rotation cancellation) and excluded
- Does NOT prove sr=60 is SAT at N=32

**Would change if:** A verified UNSAT result at some N>21 with non-degenerate
rotations would establish a transition point.
```

## Writeup Decomposition

THE_THERMODYNAMIC_FLOOR.md is currently one monolithic doc mixing
proven facts, hypotheses, and overclaims. Break it into:

1. **Paper review** — What Viragh claimed, what we verified
2. **sr=59 reproduction** — Clean reproduction narrative
3. **Thermodynamic floor** — Just the partition evidence, properly caveated
4. **Precision homotopy** — Scaling results with honest extrapolation
5. **Differential anatomy** — The dW[61] bottleneck discovery
6. **SA validation** — Important negative result (SA can't find known solutions)
7. **Audit findings** — Code bugs found and fixed

Each writeup is 1-3 pages, self-contained, with explicit evidence levels.
