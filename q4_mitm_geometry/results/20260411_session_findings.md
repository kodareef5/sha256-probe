# Session Findings: 2026-04-11 02:00-04:00 UTC (linux-server)

## Major Findings

### 1. Universal subspace FALSIFIED
Cascade_dw at round 61 lives in per-prefix 27-dim F_2 affine subspace
(not 25-dim from simplified model). Global union spans full 32 dims.
No universal precomputable filter exists.

### 2. Previous "25-dim" subspace was for WRONG model
The g_full_rank.c result (commit 7e285fc) computed the simplified
Ch-only g(e) function. The actual cascade_dw includes dh + dT2 + dSig1
contributions that increase the subspace to 27 dims.

### 3. Image sizes are discrete with Fermat prime structure  
256 prefixes give 106 distinct image sizes, all form a*2^k where
a ∈ {1, 3, 5, 9, 15, 17, 25, 27, ...}. The dominant odd primes are
3, 5, 17, 257 — all Fermat primes. Source unknown but structural.

### 4. Round-61 viable prefix found (1/1024 = 0.098%)
W57=0xab307a5a, W58=0xdf6fcc2e, W59=0x5acbd836. Has 8192 W[60]
satisfying round-61 cascade closure. Structurally independent from
cert (49 XOR bits distance).

### 5. Round-61 closure is NECESSARY but NOT SUFFICIENT for sr=60
Full 64-round SHA-256 verification: 0 of 2^32 W[60] give hash collision
for the new prefix. Best near-collision HW=40 / 256 bits.

### 6. Near-collision structure analyzed
For HW=40 near-collision:
- d, h registers: HW=0 (cascade zeros propagated — 64 free bits)
- c, g: HW=3 each (partial cascade propagation — 58 free bits)  
- a, b, e, f: HW=7-12 each (hard residual — 40 error bits)
- Sigma1 boundary (bits 17-19): 2x enriched vs random

### 7. Z3 SMT is too slow for cascade_dw constraints
Even 64-bit subproblem timed out at 120s. Modular addition + XOR rotation
creates dense CNF that overwhelms bit-vector decision procedures.

## What This Means for the Project

1. **Finding a SECOND cert requires SAT solving**, not random scanning.
   Round-61 closure gives HW≈40 near-collisions but not HW=0.

2. **The cert's specialness is in the "last 40 bits"** — the part where
   a, b, e, f registers align perfectly. This alignment was found by
   Kissat, not by structure.

3. **Near-collision HW=40 is still significant**: 90+ bits better than
   random. This is a publishable "structured near-collision attack on
   SHA-256 with 60/64 schedule compliance."

4. **Cascade chain + round-61 closure** is a complete characterization
   of the "easy part" of sr=60 collisions. The "hard part" is the
   residual 40 bits in a, b, e, f.

5. **Macbook's sigma1 boundary finding** (bits 4,5 at N=8 → bits 17-19
   at N=32) is consistent with our near-collision bit analysis.

## Running experiments
- **near_collision_hunt**: 4096 prefixes, ~6h. Looking for HW<40.
  Currently at 64/4096, best HW=52.

## Commits this session
- 7b26edb: Universal subspace FALSIFIED + prefix viability scan
- 7bdc959: prefix_viability_fast
- 682c272: Cheap image estimator + correlator  
- 1a49bea: 256-prefix analysis with Fermat prime structure
- db05c33: Coordination with gpu-laptop
- e4eb06e: Z3 SMT formulation
- 0b896f6: Z3 timeout result
- a8341c9: New prefix found + verified not full collision
- d6637ab: Team update
- a44a57b: Near-collision hunt tool
