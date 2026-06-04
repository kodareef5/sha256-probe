# Probe sweep — agent playbook + reusable assets

You are running the **cheapest small-N probe** for one (or a few) `wild_angles/` cards and recording a
**verdict against that card's own `kill_criterion`**. This file is everything you need; read it, then work.

## Hard rules
- **READ-ONLY toward `/Users/mac/Desktop/sha256_review`.** Import its `lib/`, read its data/writeups,
  compile its `.c` to a **lab-side** binary if needed — but never write, stage, or commit inside the repo.
- **No SAT solvers.** These are small-N exact/numeric probes only.
- **Compute courtesy (the user is working on this machine):** run every non-trivial computation under
  background QoS with capped threads. From bash:
  ```bash
  OMP_NUM_THREADS=2 taskpolicy -b python3 my_probe.py
  OMP_NUM_THREADS=2 taskpolicy -b ./my_binary
  ```
  or from Python use `shabridge.run_throttled([...])`. **Keep N small** (N≤12 unless a card needs the
  literal 32-bit width, e.g. the 132-corank question). Exact enumerators blow up ~exponentially — a probe
  should finish in seconds-to-low-minutes. If something would run long, shrink N and say so.

## The shared kit — `kernels/shabridge.py`
```python
import sys; sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb
s = sb.s   # == repo lib.sha256
```
Re-exported SHA primitives (use these, never reimplement): `K, IV, MASK, ROR, SHR, Ch, Maj, Sigma0,
Sigma1, sigma0, sigma1, add, hw, precompute_state, build_schedule_tail, run_tail_rounds, full_compression`.
Generic helpers: `gf2_corank(rows, n_cols)`, `gf2_rank`, `gf2_rref`, `top_eigenvalue(mat)`,
`load_gap_rows()`, `run_throttled(cmd, omp=2, timeout=...)`.
Pinned ground truth: `sb.HARDCORE` (132), `sb.DE_SIZES`/`sb.DE_LAW`, `sb.SR61`, `sb.GROWTH_EXPONENT` (0.74).

## Reusable repo assets (paths relative to the repo root)
- `lib/sha256.py` — primitives. `precompute_state(M)`→`(state_after_r56, W[0..56])`;
  `run_tail_rounds(state, sched, start_round=57)`→list of states; `build_schedule_tail(W_pre, free4)`→`W[57..63]`;
  `full_compression(M, free_57_61)`→`(final_state, W[0..63])`.
- `headline_hunt/bets/coincidence_variety/gap_rows.csv` — **N=10 collisions**, cols `w57,w58,w59,w60,g1,g2,h`.
  This is the measured gating data (Batch B / sr=61). `g1=W1[60]−sched1[60]`, `h=casoff−(sched2[60]−sched1[60])`;
  sr=61 ⟺ g1=0 AND h=0.
- `headline_hunt/bets/coincidence_variety/gap_analysis.c` — regenerates gap data at other N. Build:
  `gcc -O3 -march=native -Xclang -fopenmp -I/opt/homebrew/opt/libomp/include -L/opt/homebrew/opt/libomp/lib -lomp -o /tmp/gap gap_analysis.c -lm` then `N=8 taskpolicy -b /tmp/gap`.
- `headline_hunt/bets/block2_wang/trails/backward_construct_n10.c` — exact collision enumerator (N=8/10/12;
  `#define N` at top). 946 collisions / 117 s at N=10. Compile to `/tmp/`, run throttled.
- `headline_hunt/bets/block2_wang/encoders/preimage_lift.py` — `gf2_eliminate(A_rows, B_vals, n_cols)`
  → `(reduced_rows, reduced_b, pivot_cols)`; rank=len(pivots). (Kit's `gf2_corank` is an equivalent local copy.)
- `headline_hunt/bets/cascade_aux_encoding/encoders/schedule_dep_analysis.py` — W[k]→M[i] dependency tables.
- Writeups for ground truth: `writeups/hard_core_132_bits.md`, `writeups/paper_figures_data.md`,
  `writeups/sr60_sr61_boundary_proof.md`, `headline_hunt/bets/coincidence_variety/RESULT_sr61_is_2minus2N.md`.

## Per-card workflow
1. **Read the card.** `grep -n "### <CARD-ID>" wild_angles/CATALOG.md`, read that card block: its `one_liner`,
   the **probe** (your task), and the **kill_criterion** (your stop condition). Honor the card's stated probe.
2. **Implement** the smallest computation that decides it, reusing `shabridge`. Put code in
   `wild_angles/probes/cards/<CARD-ID>.py` (so it's reproducible).
3. **Run it throttled**, small N. Capture the actual numbers.
4. **Judge against the kill_criterion** and assign a verdict (vocab below).
5. **Write** `wild_angles/probes/cards/<CARD-ID>.md` using the template below.
6. **Return** ONE ledger line (exact format under "Return value").

## Verdict vocabulary
- **CONFIRMED** — the probe positively reproduced the card's predicted number/structure (e.g. corank=132,
  λ giving 0.74, codim=2). Strongest outcome.
- **SURVIVES** — kill_criterion did NOT fire, but the probe didn't positively confirm a number either
  (consistent, not proven). Worth promoting to a deeper probe.
- **KILLED** — the kill_criterion fired; the angle is dead as stated. (A clean negative is a real result —
  this is the falsifiability bar working. Do not soften it.)
- **INCONCLUSIVE** — the reachable N (or the cheap probe) genuinely can't decide it. Say what larger probe would.
- **REBUILD-NEEDED** — the card's probe presupposes a kernel that isn't built yet and is too big for this
  agent; describe exactly what's needed. (Use sparingly.)

Be honest and adversarial toward your own card. A surprising CONFIRMED deserves a skeptic's second look
before you claim it. Convergence (an independent probe hitting the same number) is the prize; coincidence isn't.

## Result-file template (`cards/<CARD-ID>.md`)
```markdown
# <CARD-ID> — <title>   ·   VERDICT: <CONFIRMED|SURVIVES|KILLED|INCONCLUSIVE|REBUILD-NEEDED>

**Card claim:** <one line, from CATALOG>
**Probe run:** <what you computed, N used, throttled yes/no>
**Result (numbers):** <the actual output — the load-bearing figures>
**Kill_criterion:** "<quote it>" — **fired? <yes/no>**
**Verdict reasoning:** <2-4 sentences. Why this verdict. What it does/doesn't establish.>
**Cross-check / skeptic note:** <what could make this wrong; any independent corroboration>
**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/<CARD-ID>.py`
```

## Return value (one line, for the ledger)
`<CARD-ID> | <VERDICT> | <≤15-word finding with the key number> | N=<...>`
e.g. `W2-CT1 | CONFIRMED | reachability cokernel dim = 132, matches a,b,e,f@63 + 4 dc | N=32`
