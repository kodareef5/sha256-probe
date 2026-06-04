# Stub — Persistent homology / TDA of the witness landscape

**Lens:** `graph-spectral` (TDA) · **Status:** stub (not yet a register row) · **Novelty:** adjacent-untested

## Structure
Persistent homology summarizes the multi-scale topology of a point cloud or filtered complex (its
connected components, loops, voids across scales). april28 tagged it *mildly promising* (item_20) and
**never probed it** — a live unprobed wedge.

## Candidate reframe
Build a filtration over the corpus of low-HW W-witnesses (or the residual-state cloud) and read its
persistence diagram. The hope: the **0- and 1-dimensional features map the landscape's basins and
the barriers between them** — revealing regions the repo's online sampler never visits, or showing the
solution set is a single basin (explaining why local search plateaus).

## Why it's still a stub
- It is **descriptive** by default: a persistence diagram characterizes the landscape but does not, on
  its own, *construct* a collision. It must be tied to an actionable consequence (e.g. "an unsampled
  basin exists at HW < X").
- **To promote:** write a kill-criterion of the form "dead if the persistence diagram of the
  F-corpus is single-basin / featureless, i.e. no second component or loop survives past noise scale —
  meaning the sampler already covers the landscape." Probe is cheap (~30 min with ripser/gudhi on the
  existing corpus).

## Relation to existing rows
Adjacent to `hard_core_132` (landscape structure) and the repo's empirical backbone/frontier mining.
Pairs naturally with `survey-propagation-factor-graph` (both ask "is the solution set clustered?").
