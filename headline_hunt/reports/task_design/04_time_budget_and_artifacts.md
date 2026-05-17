# Time Budget And Artifact Queue

Purpose: translate the task portfolio into concrete time spend.

## First 72 hours

1. Build the sr=61 assumption ladder spec.
   - Output: `sr61_assumption_ladder.md`
   - Success: audited matrix of bit/slice constraints ready for compute.

2. Start the defect-surface bridge atlas.
   - Output: `defect_surface_bridge_atlas.md`
   - Success: list of exact-D60 low-D61 chambers with carry signatures.

3. Write the energy/zeta experiment harness design.
   - Output: `zeta_energy_atlas.md`
   - Success: fixed energy definitions and first N=4..8 exact table plan.

4. Audit MITM residue status.
   - Output: `mitm_residue/prototypes/audit_summary.md`
   - Success: exact statement of which scripts work and what the residue key is.

## First 2 weeks

| Artifact | Owner type | Budget | Done when |
|---|---|---:|---|
| sr61 assumption ladder | compute + SAT | 300 to 800 CPU-h | L1/L2/L3 table with clear easy/hard slices |
| defect chamber atlas v2 | algebra + GPU/CPU walk | 3 to 5 human days | carry signatures explain low-D61 terraces or fail to |
| sr60 inverse-lift | algebra + local search | 2 to 4 human days | Pareto front of message-space seeds |
| bitcondition calculus | human algebra | 2 human days | 10 reusable local lemmas with CNF forms |
| zeta energy atlas | exact enumeration | 1 to 2 human days | reduced-N weight enumerators and ranking check |
| MITM residue audit | code audit | 1 human day | go/no-go for operational N=10 prototype |

## Weeks 3 to 6

Spend more time only where the first 2 weeks produce signal.

High-signal continuation:

- sr61 ladder finds non-random easy slices: build stronger CNFs around them.
- defect atlas finds low-rank or low-floor chambers: feed them into A1 and A5.
- inverse-lift finds near-certificate message seeds: launch targeted sr61 runs.
- bitcondition calculus yields transferable lemmas: implement programmatic SAT
  hooks or static clauses.
- zeta/2-adic atlas predicts candidates: use it as a selector.
- MITM N=10 beats baseline: scale to N=12/N=16 before touching N=32.

Low-signal response:

- If all sr61 variants look identical, reduce compute and move to non-cascade.
- If carry chambers explain nothing, treat cascade as a local dead end.
- If zeta/spectral tools do not rank candidates, archive as diagnostics.
- If MITM does not beat N=10 baselines, do not spend N=32 effort on it.

## Compute allocation

| Compute class | Use |
|---|---|
| Short SAT runs | L1/L2 assumption ladder, lemma evaluation |
| Long SAT runs | only after a changed encoding/candidate has reduced-N evidence |
| GPU/random walks | defect-surface bridge search and chamber transitions |
| Exact enumeration | N=4..12 zeta, carry chamber, BDD, and lift studies |
| Human algebra | bitconditions, defect-map factorization, non-cascade trail design |

## Stop-doing list

- Do not run more unchanged sr=61 seed sweeps.
- Do not optimize wording, dashboards, or publishability.
- Do not do more generic candidate scanning without a new selector.
- Do not treat Riemann/zeta/manifold language as progress unless it emits data.
- Do not spend N=32 compute on a mechanism that has not won at N=8/N=10.

## Best next artifact order

1. `sr61_assumption_ladder.md`
2. `defect_surface_bridge_atlas.md`
3. `free_word_shaping_mitm.md`
4. `bitcondition_calculus.md`
5. `sr60_certificate_inverse_lift.md`
6. `zeta_energy_atlas.md`
7. `mitm_residue/prototypes/audit_summary.md`
