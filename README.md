# SHA-256 Probe

Systematic exploration of SHA-256 collision resistance limits.

## Background

Viragh (2026) demonstrated collisions through round 59 of SHA-256's 64 rounds
("92% broken"). This project investigates whether further rounds can be attacked,
characterizes the barrier, and builds tools to push beyond it.

## Key Results

| Claim | Status | Summary |
|-------|--------|---------|
| sr=59 collision | **VERIFIED** | Independently reproduced in 220s |
| sr=60 SAT at N=8-21 | **VERIFIED** | Mini-SHA collisions at every non-degenerate width |
| sr=60 UNSAT for known N=32 candidates | EVIDENCE | 29/32 partitions DRAT-verified |
| dW[61] HW predicts solvability | HYPOTHESIS | HW 3-8 for SAT, 17 for UNSAT |
| N=32 solvable in ~days | EXTRAPOLATION | Fit: T ≈ 0.87 × 1.47^N |

See [CLAIMS.md](CLAIMS.md) for full evidence registry.

## Repository Structure

```
lib/           Shared code (Python + C) — SHA-256, CNF encoder, solvers
q1-q6/         Research workstreams (see QUESTION.md in each)
reference/     Source paper, prior art
writeups/      Focused research narratives
infra/         Build tools, batch runners
archive/       Legacy numbered scripts
```

## Quick Start

```bash
# Build C tools
make

# Run C library tests
gcc -O3 -Ilib lib/test_sha256.c lib/sha256.c lib/scan.c -lm -o test && ./test

# Find candidates at word width N
./fast_scan 20 10

# Parallel SAT solve at word width N
./fast_scan 20 10 | python3 q1_barrier_location/homotopy/fast_parallel_solve.py 20 3600

# Verify UNSAT partitions
python3 q6_verification/partition_verifier.py --dual 4 120 4 16
```

## Requirements

- **SAT solvers:** kissat, cadical, cryptominisat5 (`brew install kissat cadical cryptominisat`)
- **C compiler:** gcc with OpenMP support (`brew install libomp`)
- **Python:** 3.9+
- **DRAT checker:** built from source in `infra/drat-trim/`

## Contributing

See [CLAUDE.md](CLAUDE.md) for agent/contributor conventions.
GitHub Issues #1-#7 track the active research workstreams.
