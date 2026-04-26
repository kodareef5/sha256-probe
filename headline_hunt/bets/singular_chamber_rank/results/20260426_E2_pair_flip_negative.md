# E2: Pair-bit-flip operator on HW4 floor — NEGATIVE
**2026-04-26 18:55 EDT**

E2 task from today's task list (#33): test whether a deterministic
pair-bit-flip walker (operator change from yale's random multi-bit
flips) escapes the HW4 D61 trap. Combined with yale's complementary
W57 affine probe (commit 0ae7751), this memo records a strong
negative result.

## E2 setup

Pair-bit-flip walker: deterministic search over (W58, W59) bit-pair
flips at increasing radius. Tests neighborhoods that yale's random
multi-bit walker may sample inefficiently.

| radius | enumeration | candidates | result |
|---:|---|---:|---|
| 2 | 1 W58 + 1 W59 | 1,024 | no improvement |
| 3 | 2 W58 + 1 W59 (or 1+2) | ~32k | no improvement |
| 4 | 2 W58 + 2 W59 | 246,016 | no improvement |
| 5 | 3 W58 + 2 W59 | 2,460,160 | no improvement |

All exhaustive. ~2.7M total candidates checked across 4 radii. Base:
idx=0 (msb_cert) HW4 point at `W58=0x6ced4182, W59=0x9af03606`.

## E2 + yale's complementary W57-free affine probe (0ae7751)

Yale extended the search to the FULL 96-bit (W57, W58, W59) affine
fiber via low-weight enumeration:

| max kernel weight | reps checked | exact D60 | exact D61 |
|---:|---:|---:|---:|
| 4 | 679,121 | 0 | 0 |
| 5 | 8,303,633 | 0 | 0 |
| 6 | 83,278,001 | 0 | 0 |

Best non-exact: D60=HW1 / D61=HW19 — close to D60=0 surface but
D61 rises sharply away from the cap-2/HW4 chambers.

Calibrated chart walks (yale's chart61walk, 1M trials each):
- idx=17 D61-HW1 shelf, cap=1: 36,378 cap hits, 0 exact D60
- idx=17 D61-HW1 shelf, cap=4: 37,900 cap hits, 0 exact D60
- idx=8 D61-HW2 shelf, cap=2: 35,451 cap hits, 0 exact D60

Chart and exactness are SEPARATED. Walks that preserve the cap chart
don't reach exact D60; walks that reach exact D60 break the cap chart.

## Comprehensive negative-result picture (HW4 D61 / HW59 tail floor)

Six independent attack vectors all confirm the floor:

| attack | scope | result |
|---|---|---|
| 1. M5 random walks | 11 × 1B trials × 3 cands × radius 32 | HW4 floor |
| 2. M5 wider random | 1B × radius 64 | HW4 floor |
| 3. Yale GPU off58 chart scan | hundreds of new sparse off58 charts | HW6+ floor (worse than HW4) |
| 4. Yale kernel-rep enumeration | linear two-wall map | 0 exact reps |
| 5. M5 sparsest-off58 chamber (HW1) | idx=17 1B trials | HW4 floor (matches) |
| 6. M5 pair-flip walker (E2) | radius 2-5 deterministic, ~2.7M evals | HW4 floor |
| 7. M5 random tight-radius (yale's tool) | max_flips=4 × 1B trials | HW4 trap 99.5% |
| 8. Yale W57-free affine fiber | weight 1-6, 92M reps | 0 exact (sub-HW4) |

## Yale's sharper characterization

After today's combined work, yale's interpretation (from
20260426_w57_affine_fiber_probe.md):

> "The missing operation must compensate specific carry transitions
> while preserving the mixed Sigma1/Ch/T2 chart."

Specifically:
- sparse off58 is NOT the predictor
- local pair rank is NOT the predictor
- fixed-W57 affine fibers do NOT hide the repair
- W57-free affine fibers do NOT hide the repair
- chart-preserving walks reach low D61 but NOT exact D60

The escape operator (if it exists) must simultaneously preserve THREE
arithmetic charts (Sigma1, Ch, T2) at the round 60-61 boundary while
adjusting cascade-1 parameters. None of today's operator-change
attempts (random multi-bit, deterministic pair-flip, low-weight
affine, chart-preserving) satisfies this constraint.

## Implication for the bet

The bet's `next_action` should be updated. Today's findings established:

1. **The HW4 D61 floor is structural** at the operator family of:
   - Random multi-bit flips at ANY tested radius (2-64)
   - Deterministic pair-flip enumerations at radius 2-5
   - Affine fiber low-weight enumerations through weight 6
   - Chart-preserving walks at the cap-1/2/4 terraces

2. **Sub-HW4 D61 (if reachable) requires a fundamentally different
   operator** — one that simultaneously preserves Sigma1/Ch/T2 charts
   while adjusting cascade-1 parameters. This is heavy implementation;
   yale's structural mapping continues to chase it.

3. **The bet itself is not killed** — yale's reopen criteria would still
   fire on:
   - A nonzero Ch/Maj-invisible trail construction
   - A nonlinear fiber probe showing nonuniform preimage size with full
     local rank
   - The Sigma1/Ch/T2 chart-preserving operator if implemented

4. **For M5 in the meantime**: deeper random walks won't help. Useful
   M5 work:
   - Compute support for yale's specific chart-preserving operator
     when implemented
   - Cross-bet leverage on cascade_aux predictor (already shipped)
   - Different bet entirely (block2_wang, mitm_residue extensions)

## E2 task: closing

E2 (pair-bit flip operator) is empirically NEGATIVE. The operator
explored the deterministic small-radius neighborhood exhaustively
and confirmed HW4 trap. No code shipped — the Python prototype
(/tmp/deep_dig/e2_pair_bit_walker*.py) sits as exploratory.

The bet's structural-floor evidence is now 8 convergent vectors deep.
Anyone considering operator-family change should read yale's
"Sigma1/Ch/T2 chart-preserving" criterion before implementing —
naive operators are unlikely to escape.

EVIDENCE-level: HW4 D61 floor confirmed structural at all simple
operator-family changes M5 + yale tested today.
