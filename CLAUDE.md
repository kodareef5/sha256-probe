# SHA-256 Probe — Agent Operating Guide

## What This Project Is

A systematic exploration of SHA-256 collision resistance limits. We probe
for weaknesses, characterize barriers, and build tools to push further.

This is **not** about proving a single thesis. It is about generating
reliable evidence across multiple angles of attack on SHA-256.

**Background:** Viragh (2026) demonstrated collisions through round 59 of
SHA-256's 64 rounds ("92% broken"). This project investigates whether the
remaining rounds can be attacked. See `reference/paper.pdf`.

## Before You Start

1. Read `CLAIMS.md` — understand what's established vs hypothesized
2. Read the `QUESTION.md` in whichever `q*_` folder you're working in
3. **Always import from `lib/`** — never reimplement SHA-256 primitives

## Repository Structure

```
lib/                   Shared library (SHA-256, CNF encoder, solvers)
q1_barrier_location/   WHERE is the collision barrier?
q2_bottleneck_anatomy/ WHY does the barrier exist?
q3_candidate_families/ Can we find BETTER candidates?
q4_mitm_geometry/      Can we solve the HARD RESIDUE directly?
q5_alternative_attacks/ What if SAT isn't the right tool?
q6_verification/       Are our results correct?
reference/             Source paper, prior art, specs
writeups/              Focused research narratives
infra/                 Build, batch, orchestration
archive/               Legacy numbered scripts (read-only)
```

## Shared Library (`lib/`)

```python
from lib.sha256 import K, IV, precompute_state, sigma0_py, sigma1_py
from lib.cnf_encoder import CNFBuilder
from lib.mini_sha import MiniSHA256, MiniCNFBuilder
from lib.solver import run_kissat, run_cadical, verify_drat
```

**Never reimplement these.** If you need a variant, extend the library.

## Conventions

### File naming
- No numbered prefixes (multiple agents = name collisions)
- Descriptive names: `padding_freedom_scanner.c` not `77_candidate_mutation.py`
- Results: `results/YYYYMMDD_description/` within each question folder

### Evidence levels
Use these consistently in claims, writeups, and commit messages:
- **VERIFIED**: reproduced, cross-validated, DRAT-checked where applicable
- **EVIDENCE**: consistent from multiple approaches, but gaps remain
- **HYPOTHESIS**: supported by data, not yet tested against alternatives
- **EXTRAPOLATION**: projected from trends, explicitly flagged as uncertain

### Claims
Each testable claim gets its own file in `q*/claims/` with:
- One-sentence statement
- Evidence level
- Supporting scripts/results
- Known caveats
- What would change the assessment

### Commit messages
- State what changed and the evidence level of any new claims
- Reference the question folder: `[q1] N=22 SAT in 1847s`

## What NOT To Do

- Don't say "proof" without DRAT verification and cross-solver confirmation
- Don't extrapolate mini-SHA results to full SHA-256 without explicit caveats
- Don't add scripts that reimplement `lib/` functions
- Don't modify `lib/` without checking downstream consumers
- Don't frame findings as "properties of SHA-256" when they're properties
  of one candidate family under one kernel with one padding scheme
- Don't use "theorem" for experimental observations

## Tools Available

- **Kissat 4.0.4** — primary CDCL SAT solver
- **CaDiCaL** — secondary solver for cross-validation
- **CryptoMiniSat 5** — third solver (slow on these instances)
- **drat-trim** — DRAT proof checker (in `infra/drat-trim/`)
- **gcc + OpenMP** — for C tools. Compile flags:
  `gcc -O3 -march=native -Xclang -fopenmp -I/opt/homebrew/opt/libomp/include -L/opt/homebrew/opt/libomp/lib -lomp`

## Current State (updated by humans, not auto-generated)

### Known candidates (MSB kernel, da[56]=0)
| M[0] | Fill | hw56 | sr=60 Status |
|------|------|------|-------------|
| 0x17149975 | 0xffffffff | 104 | UNSAT (DRAT on 29/32 partitions) |
| 0xa22dc6c7 | 0xffffffff | 115 | Likely UNSAT |
| 0x9cfea9ce | 0x00000000 | 103 | Likely UNSAT |
| 0x3f239926 | 0xaaaaaaaa | 107 | Likely UNSAT |

### Precision homotopy frontier
sr=60 is SAT at every non-degenerate word width N=8 through N=21.
N=22 is currently being solved. See `q1_barrier_location/claims/`.

### Biggest open questions
1. Does any N=32 candidate family produce sr=60 SAT?
2. Can MITM on the 24-bit hard residue bypass the SAT solver entirely?
3. Do Wang-style message modifications apply to this problem?
