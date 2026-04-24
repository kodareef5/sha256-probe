# Kill criteria — block2_wang

Either of these signals closes the bet (move to `graveyard/closed_bets/`).

## #1 — No cluster yields >18-round absorber after dedicated trail search

**Trigger**: 1 week of dedicated trail-engine development + search complete; no
residual cluster has produced a differential trail satisfying local conditions
through more than 18 schedule-compliant rounds with the given message freedom.

**Why this kills**: 18 rounds is the existing naive-block-2 SAT frontier. If trail
search with message modification cannot push past it, the structural advantage
the bet is supposed to deliver isn't there.

**Required evidence to fire**:
- `results/trail_search_summary.md` documenting per-cluster best-trail-round count.
- At least 5 distinct clusters tried.
- Trail engine confirmed working on a control case (e.g., reproduce a known SHA-1 Wang trail).

## #2 — No improvement over naive SAT frontier on N=8/N=12 analogs

**Trigger**: Reduced-N pilot (N=8 and N=12 cascade-residual + tailored trail vs.
naive block-2 SAT) shows no better than even with naive on solve time or
round-completion.

**Why this kills**: If the tailored trail doesn't outperform naive SAT on small N,
extrapolating to N=32 is unjustified.

**Required evidence to fire**:
- `sat_pilots/n8_results.md` and `sat_pilots/n12_results.md` with side-by-side
  metrics: rounds completed, conflicts, wall time, solver-version-controlled.

## Reopen triggers (see mechanisms.yaml)

- New residual class with HW/register concentration substantially below current best.
- New SHA-256 message-modification paper or tool becomes available (track in
  `literature.yaml` — id `zhang_2026_sha256_round_reduced` is the most likely source).
