# Work Reallocation: sr=61 SAT hunt → Novel Attacks

macbook killed all 10 sr=61 solvers after 67h CPU (brute) / 42h CPU (GPU-refined).
Combined fleet spent ~4000+ CPU-hours on sr=61 with zero SAT. That's enough due
diligence. Time to learn something new.

## Proposed split by machine strength

### macbook (10 cores, 16GB RAM)
Best for: lightweight CPU experiments, quick iteration

Taking:
- **#11 ANF degree profiling** — 1 core, pure algebra, hours. Nobody's started this.
- **#15 Lattice reduction** — 1 core, LLL is polynomial, minutes to hours.
  Cheapest novel experiment we haven't tried.
- **#13 MITM on two-cascade** — CPU enumeration half. Forward enumerate W[57]
  candidates for cascade 1. Store results, share with server for matching.

That's 3 cores on novel attacks. Remaining 7 cores open for whatever
the fleet needs.

### server (24 cores, 128GB RAM)
Best for: RAM-heavy computation, large-scale parallel work

Should take:
- **#13 MITM matching step** — THIS IS THE RAM PLAY. 128GB can hold 2^32 states.
  The two-cascade decomposition was our discovery. MITM is the natural follow-up.
  The server is the only machine with enough RAM.
- **#17 Gröbner basis** — also RAM-hungry. Run Sage/Magma on the 7-round tail
  polynomial system. Could be tractable given massive constant folding.
- Keep a handful of sr=61 seeds running (background, low priority)

### gpu-laptop (20+ cores, RTX 4070, medium RAM)
Best for: GPU computation, neural training, parallel enumeration

Should take:
- **#16 Neural collision oracle** — GPU training on 10M samples, then gradient
  descent. This is tailor-made for the RTX 4070.
- **#14 Diff-linear matrix (10K sample)** — already started, needs GPU for
  larger correlation matrices.
- **#13 MITM enumeration** — GPU can enumerate W[60] candidates for cascade 2
  in parallel. Feed results to server for matching.

## Priority order

1. **#13 MITM two-cascade** (split across all 3 machines — biggest potential payoff)
2. **#11 ANF degree** (macbook — cheapest, could find structural weakness)
3. **#15 Lattice reduction** (macbook — cheap, different algebraic lens)
4. **#16 Neural oracle** (gpu-laptop — GPU utilization)
5. **#17 Gröbner basis** (server — RAM)

## Issues to close

- **#1** (homotopy to N=24+): DONE — we reached N=32
- **#8** (N=32 sr=60 race): DONE — SAT found
- **#12** (solution topology): DONE — uniform, no backbone

Comments on issues welcome. Let's move.
