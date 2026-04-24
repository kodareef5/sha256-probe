# Hill-climbing on residual HW: NEGATIVE result

**Tool**: `q4_mitm_geometry/cascade_hillclimb.py` — single-bit-flip hill-climb on (W[58], W[59]) with cascade constraints, minimizing total HW at round 63.

| Method | Evaluations | Min total HW | Wall |
|---|---:|---:|---:|
| Random sampling (build_corpus.py) | 200,000 | **62** | 8.5s |
| Hill-climb 5×1000 | 5,000 | 81 | 0.2s |
| Hill-climb 20×50000 | 1,000,000 | **82** | 44s |

Hill-climb does NOT improve on random sampling — it plateaus at HW≈82-85, while random sampling reaches HW=62 in 200k samples.

## Why

The HW landscape over (W[58], W[59]) is hostile to local search:
- Single-bit perturbation in W[58] feeds through CSA adders with carry chains, then through Sigma functions, then through 5 more rounds — every bit flip cascades broadly.
- The output residual at round 63 is essentially uncorrelated for nearby (W[58], W[59]) inputs.
- Local "best HW" is not predictive of global structure.

This is the differential cryptanalyst's classic problem: hash-output HW is not a smooth function of the input, so gradient/perturbation methods don't apply.

## Implication for block2_wang

The hill-climb path is closed. Block2_wang needs a different residual-finder:

1. **Algebraic construction** (cascade-aux force mode): force more cascade structure in the encoding so the residual is low by construction. The current force mode zeros 5 registers at round 60 (a-e). Extending the cascade further (force-zero at round 61, 62) might constrain the round-63 residual algebraically.

2. **Differential trail search** (Wang-style): construct the trail backward from a target residual and find compatible (W[57..60]). This is the engine GPT-5.5 said to build; existing tools don't substitute for it.

3. **Beam search / annealing** (untested here): could marginally improve on hill-climb but unlikely to reach HW≤16 given the landscape roughness.

4. **GPU brute force** at N=8 first to quantify the actual HW distribution analytically, then extrapolate / scale.

## Status update for the bet

The block2_wang README's Phase 1 ("collect block-1 near-collision residuals from existing q5 runs") is partially achieved: we have 200k residuals at HW≥62 documented in `corpus_msb_200k_hw96.jsonl`, with structure characterized (always {a,b,c,e,f,g} active, d/h zero). 

Phase 1 cannot reach HW≤16 with current tools. The bet kill criterion #1 ("no residual cluster yields >18-round absorber") is not yet triggerable because we can't even get a residual small enough to launch a trail search.

**Real bet status update**: block2_wang is not "open with random-sampling phase 1 done" — it's "open with phase 1 BLOCKED on a missing trail-search engine." Updating mechanisms.yaml accordingly.
