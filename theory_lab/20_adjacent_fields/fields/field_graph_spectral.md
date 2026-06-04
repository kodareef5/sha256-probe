# Stub — Spectral graph theory of the round-state dependency graph

**Lens:** `graph-spectral` · **Status:** stub (not yet a register row) · **Novelty:** adjacent-untested

## Structure
The eigenvalues of a graph's adjacency/Laplacian encode connectivity, expansion, and mixing. SHA's
round-state dependency graph (which bit/register feeds which) is a concrete, small graph. april28
tagged spectral graph *weakly promising* (item_34) and only **partially** probed it (via the RMT
round-Jacobian probe_25) — a live wedge.

## Candidate reframe
Compute the spectrum of the round-update dependency graph (or the round Jacobian over GF(2)/R) and look
for a **structural invariant** — a spectral gap, an outlier eigenvalue, or a near-degeneracy at the
N=9 "rotation degeneracy" the repo already noticed — that *predicts* SAT hardness or the kernel-yield
pattern the `kernel_fill_phase_diagram` records.

## Why it's still a stub
- Spectra are easy to compute and easy to over-interpret; the repo's april28 RMT probe found the
  round-Jacobian sparse and **non-Wigner** (one leading eigenvalue ~250), i.e. no clean RMT universality.
- **To promote:** write a kill-criterion tying a spectral feature to an *observable* — e.g. "dead if the
  spectral gap is uncorrelated (|ρ|<0.2) with per-candidate SAT solve-time across the registry's
  candidates." That makes it falsifiable against existing run data.

## Relation to existing rows
Competes with `kernel_fill_phase_diagram` and `rotation_aligned_kernels` (both seek a predictor of
hardness). The N=9 anomaly is the obvious first spectral target.
