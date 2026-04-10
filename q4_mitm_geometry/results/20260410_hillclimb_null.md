# Hill Climbing NULL Result — Cascade-Constrained Landscape is Flat

## Setup

`cascade_hillclimb.py` runs single-bit-flip hill climbing on
(W[57], W[58], W[59], W[60]) with cascade constraints applied. Each
step flips one random bit of one of 6 free words (192 perturbable bits
total), evaluates the residual HW at round 63, accepts if improved.

Candidate: M[0]=0x17149975, fill=0xffffffff (same as forward scan).

## Results

| Run | Restarts | Steps/restart | Total eval | Best HW |
|---|---|---|---|---|
| Pilot | 30 | 1,500 | 45,000 | 81 |
| Big | 200 | 10,000 | 2,000,000 | **78** |

## Comparison with random sampling

| Method | Samples | Best HW |
|---|---|---|
| Random (cascade forward scan) | 500,000 | **75** |
| Hill climbing | 2,000,000 | 78 |
| GPU brute force (gpu-laptop) | 110,000,000,000 | 76 |

**Hill climbing is empirically WORSE than random sampling** at this scale.
4x more evaluations and yet 3 HW points higher.

## Interpretation

The cascade-constrained landscape has no exploitable gradient at the
single-bit level:
- Most single-bit flips are rejected (output HW unchanged or increased)
- The few accepted moves reach a local minimum around HW=85-88
- Different random restarts find different local minima, all in 78-95 range
- None break through to the HW~50 region

This is consistent with:
1. **Diff-linear SVD** showing 34-dimensional low-rank structure — single bits
   are poor search directions because the real structure is 34-dimensional
2. **ANF degree profile** at round 63 being 6% — the collision function is
   ALGEBRAICALLY low-degree but combinatorially rough
3. **sigma1 conflict rate** 10.8% — ~208 per-message structural contradictions
   that can't be resolved by local moves

## What would work (hypothesis)

1. **Multi-bit perturbations**: flip 4-8 bits simultaneously to jump out of
   local minima. Standard SA technique.
2. **Gradient over the 34-dim subspace**: project perturbations onto the
   SVD principal directions instead of raw bit coordinates.
3. **Constraint propagation**: maintain the 4528 deterministic bit
   relationships during search — reject any state that violates them.
4. **Simulated annealing**: accept worse moves probabilistically to escape
   local minima.

## Evidence level

**EVIDENCE** (strong null result): direct empirical comparison on 2M hill
climb evaluations vs 500K random samples. Hill climbing can be ruled out
as a productive search strategy in the raw bit space.
