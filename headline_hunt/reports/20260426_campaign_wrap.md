# 2026-04-26 campaign wrap — singular_chamber × cascade_aux × negatives

**52 commits today** (yale ~14, macbook ~38) across the
singular_chamber_rank bet, cascade_aux_encoding refinements, and
cross-bet synthesis. Real collaborative output. This memo captures
the full narrative arc.

## The day in three arcs

### Arc 1 (morning) — cascade_aux predictor model solidifies

Began with extending yesterday's n=16 ρ=+0.976 cascade_aux predictor
across more dimensions:

| commit | finding |
|---|---|
| 16d9c30 | sr=60 generalization: ρ(saving) = +1.000 (n=5) |
| 799dc38 | cadical cross-solver: ρ = +1.000 (n=5) |
| 032f51a | Mode B decay curve at 200k: 36-60% saving retained |

The cascade_aux predictor model (Mode A wall predicts Mode B speedup)
is now characterized:
- ρ ≥ +0.99 across kissat sr=61 n=16, kissat sr=60 n=5, cadical sr=61 n=5
- Mode B converges to constant wall (~1.20s sr=61, ~0.94s sr=60), solver-agnostic
- Speedup at 50k: 1.5-3×; decays gradually to ~1× by 1M
- Half-life ~150-300k conflicts

The morning's work established the predictor as deployable.

### Arc 2 (afternoon early) — yale ships singular_chamber_rank bet

Yale arrived and built a NEW bet from scratch in 14 commits over 2 hours:

**The mathematical decomposition** (yale's first-principles move):

```
D(W57, W58, W59) = (W2_sched60 - W1_sched60) - cascade_required_offset60
                 = S(W58) - R(W59)

S(W58) = C + sigma1(W58 + off58) - sigma1(W58)   ← schedule finite-diff
R(W59) = post-round-59 cascade-required offset    ← carry-driven
```

D=0 is the sr=61 compatibility condition. Yale's iterative descent:

1. **Local rank probe**: defect map has full Jacobian rank everywhere (negative).
2. **Fiber count probe**: nonlinear chamber variance — Fano factors 23-60 at N=12.
3. **Schedule finite-difference probe**: S(W58) compresses to image fraction 0.0264-0.0723 in reduced N. Sparse off58 deltas give extreme schedule compression.
4. **Full-N sparse offset probe**: at full N=32, sparse off58 chambers REACHABLE; **exact D60=0 points found** — sr=61 compatibility broken at full N.
5. **Radius-6 + 7 ridge enumeration**: low-D60-HW + low-D61-HW ridges around the exact-D60 surface. Greedy repair from these ridges crosses to new exact basins.

Yale's frontier when M5 entered the campaign: D61=HW10 / tail HW76.

### Arc 3 (afternoon mid) — M5 raw 1B-trial depth pushes the frontier

Joint M5 + yale descent over 13 1B-trial walks (~13B trials, ~3h M5
wall):

| step | commit | frontier |
|---|---|---|
| Initial yale frontier | (yale) | HW10 / HW76 |
| M5 100M HW7 base | (cddef23) | HW5 / HW68 |
| M5 1B from HW67 tail | (c28c1bb) | HW5 / HW60 |
| Yale ridge-repair / GPU chart scan | (5f5e06a, cf9cd74) | HW5 / HW70 |
| M5 1B idx=0 HW5 base | (37b721a) | **HW4** / HW70 |
| M5 1B yale's HW59 base | (c14c587) | HW4 (idx=8) / HW59 |
| Cross-cand confirmation (idx=17 sparsest) | (96a5c18) | HW4 universal |
| Yale d60 fiber exhaustion + cross_chamber_pool | (2bc9e4d, 3335040) | HW4 / HW59 (yale) |

**Final joint frontier: D61 = HW4 / tail HW59. 6-bit D61 + 17-bit tail
improvement from yale's start.**

5 convergent attack vectors all bottom at HW4/HW59:
1. M5 raw 1B greedy-flip (×11 walks across 3 cands)
2. M5 wider radius (radius=64)
3. Yale GPU off58 chart scan + alt-chamber walks
4. Yale kernel-rep enumeration in linear two-wall map
5. M5 walk in HW1 sparsest off58 chamber

### Arc 4 (afternoon late) — cross-bet leverage

Three cheap probes from a structured task list:

**B1** (commit b760423): bit=19 1B walk floors at HW5, **NOT HW4**.
The "extreme compression" cand has the HIGHEST D61 floor under
random-flip walks. Invalidates mitm_residue's "priority MITM target"
framing.

**C1** (commit 0605195): cascade_aux Mode B speedup at singular_chamber
HW4 W57 chambers = 2.82-3.18× at 50k — **top quartile** of the
cascade_aux distribution. Cross-bet leverage validated.

**D2** (commit 505859b): bit=19's de58 image marginals are STRONGLY
non-uniform — 13 fully locked + 5 partial-locked = 18 of 32 bits
structurally distinguished. **REOPENED `bdd_marginals_uniform`**
negative with refined scope.

**Cross-bet synthesis G1** (commit ef56416): the three findings
together restructure 3 bets. The productive ranking metric is Mode A
wall + locked-bit count, not de58_size or off58 sparsity directly.

### Arc 5 (afternoon late, cont'd) — locked-bit hint follow-up

Motivated by D2, tested whether locked-bit unit clauses on
aux_reg[("e",58)] speed up kissat. **Single-seed result**: Mode A +
13 locked-bit hints = 1.71-1.75× speedup at 50k on bit=19. Mode B +
hints: negligible (already captures it).

**Scaling across 5 cands** (commit 88eb025): speedup correlates
inversely with de58 image size — bit=19 (de58=256) gets 1.75×;
bit=3 (de58=51k) gets 1.01×.

**Full-image vs simple unit clauses** (commit 557fc42): full 256-image
Tseitin-OR disjunction is WORSE than 13 simple unit clauses (1.46×
vs 1.75×). CDCL prefers direct unit propagation over disjunctive
encoding.

**Multi-seed honesty** (commit a95a267): 3-seed median speedup is
1.57× with HIGH variance (0.70× to 1.75×). Single-seed claims overstate.

**Refined deployment story** for cascade_aux:

| Mode | Solution set | Speedup (median, multi-seed) |
|---|---|---|
| A (expose) | unchanged | 1× (control) |
| A + locked-bit hints | unchanged | ~1.5× (de58-dependent, noisy) |
| B (force) | restricted to cascade-DP | ~1.5-3× (more stable) |

Mode A + hints is a probabilistic preprocessing optimization with net
positive expected value but per-run variance. Mode B remains the
more stable preprocessing path.

## What's the bragable finding?

Today's "amazing" finding is NOT a SAT collision (still nothing
solved). It's a **structural restructuring of attack-vector beliefs**:

1. **bit=19's de58_size=256 IS real structure**, but it doesn't help
   the attack vectors mitm_residue assumed (forward-table) or that
   random-flip walks use. It DOES help SAT preprocessing via
   redundant unit clauses on the locked bits — yielding 1.5×
   median speedup at 50k conflicts.

2. **The greedy-flip + Newton-repair operator family hits a
   structural floor at HW4 D61 / HW59 tail** across 5 convergent
   attack vectors. To go below requires operator change — yale's
   carry-aware repair track is the natural next move.

3. **Predictor models extend cleanly across structurally-related
   CNFs**: cascade_aux's Mode A → Mode B speedup relationship holds
   at singular_chamber's structurally-chosen W57 chambers (top
   quartile). Cross-bet leverage validated.

4. **negatives.yaml refinement**: closed negatives don't always stay
   closed when applied to NEW classes of cands. `bdd_marginals_uniform`
   was right for generic cands, wrong for structurally distinguished
   ones. Reopening keeps the registry honest.

5. **Predictor closure refinement**: yesterday's validation matrix
   (de58_size and hard_bit_total_lb are search-irrelevant) holds for
   MAJOR speedups at high budgets. But for early-conflict
   preprocessing speedups, the actual locked-bit pattern (different
   per-cand metric than de58_size scalar) IS extractable and
   useful — modulo seed variance.

## Run inventory (today)

- M5 1B-trial walks: 13 (~13B trials)
- M5 + linux_gpu_laptop GPU OpenCL chart scans: 5+
- Cross-bet kissat tests: 24 (3 cands × 2 modes × 2 budgets + 4×3 multi-seed + 2×3 full-image)
- Yale structural enumerations: radius-7 + bridge + pool + fiber-exhaustion + GPU off58
- Total compute: ~3.5 hours M5 wall + linux_gpu_laptop's runs

## Bets touched

- **singular_chamber_rank**: 14 yale commits, 5 M5 commits. Frontier
  HW10/HW76 → HW4/HW59. Mechanism characterized; operator family is
  the gate.
- **cascade_aux_encoding**: 8 commits. Predictor model (n=16 ρ=+0.976)
  validated cross-solver, cross-sr-level, cross-budget; locked-bit
  hints discovered as new Mode A → Mode B transformation.
- **mitm_residue**: priority-target framing invalidated for random-
  flip walks (B1), nuanced for SAT preprocessing (locked-bit scaling).
- **negatives.yaml**: `bdd_marginals_uniform` reopened with scoped
  criterion.

## What's still pending

From the task list:
- E1/E2: operator-family change (carry-aware perturbation, pair-bit flips). Yale is on the structural track; M5 should pair when yale ships specific carry-preserving proposals to brute-force-verify.
- D1: N-scaling probe of S/R compression. Foundational structural homework.
- F1: HW1 chart discovery on cands 4-17. Marginal value per yale's "off58 sparsity ≠ ranking function" finding.
- D2 fully closed via locked-bit-hint testing; updated negatives.yaml.

## Closing

Today produced the cleanest cross-bet leverage of the project so far.
Three findings (B1, C1, D2) connected to refine three bets and reopen
a closed negative. The collaboration between yale (structural mapping)
and macbook (raw 1B depth) demonstrated the kind of complementary work
the headline_hunt registry was designed to enable.

The HW4/HW59 floor isn't a headline. The structural reproduction
across cands and chambers IS substantial empirical evidence that the
current operator family has reached its information limit, AND that
structure-aware tools (locked-bit hints, Mode B preprocessing,
yale's carry-aware repair-in-progress) are the natural next layer.

Tomorrow's work: yale's carry-aware repair operator is the
highest-leverage path. M5 stands ready for compute support when
yale's specific carry-preserving moves are ready to brute-force-test.
The bet's central question — does an operator that explicitly
preserves carry chambers escape the HW4 floor? — is now the
well-posed next question.
