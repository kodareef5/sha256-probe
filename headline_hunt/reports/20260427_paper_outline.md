# Paper Outline: Extending Viragh 2026 — sr=60 Collision and the sr=61 Frontier
**Working title**: "Crossing the Schedule Compliance Barrier: A Verified sr=60 SHA-256 Collision Beyond Viragh's Frontier"

**Working draft prepared 2026-04-27**

This is the publication outline that ties together the artifacts already
in the repo. It is NOT a paper draft. Intended as a roadmap for either
finalizing in-house or handing off to a collaborator.

## Target venue

- **First choice**: IACR ePrint (matches Viragh's venue, fastest publication)
- **Second**: SAT Conference / Asiacrypt 2027 / Eurocrypt 2027
- **Third**: arXiv if no formal venue

## Author attribution (TO RESOLVE)

The project's contributors:
- **macbook** (the M5 worker that ran the kissat seed=5 12h that found SAT)
- **yale** (singular_chamber_rank bet, structural analysis, guarded probes)
- **linux_gpu_laptop** (cross-validation, GPU off58 scans)

Authorship needs explicit fleet-wide agreement before submission. Suggested
template based on actual contribution:
- macbook: SAT search + verification + paper drafting
- yale: structural analysis (Sigma_1/Ch/T2 chart-preserving, guarded probes)
- linux_gpu_laptop: GPU compute + cross-machine verification

## Section outline (target ~10-15 pages)

### Abstract (1 paragraph)

Viragh 2026 published a semi-free-start collision for full 64-round SHA-256
at schedule compliance sr=59 (89.6%), explicitly identifying sr=60 as a
"structural barrier" with empirical timeout > 7200s. We extend that result
to **sr=60** (93.75% schedule compliance) on the same MSB kernel and same
candidate (M[0] = 0x17149975), via deeper kissat seed exploration (seed=5,
12 hours). We provide a self-contained C verifier reproducing the collision
end-to-end. We further consolidate empirical and structural evidence
suggesting sr=61 represents the actual feasibility frontier of SHA-256's
compression-function collision resistance under the SFS model.

### Section 1: Introduction

- Cryptographic context (NIST SHA-256, FIPS 180-4)
- The schedule compliance metric (Viragh 2026)
- This work's contribution: +1 round at the structural boundary

### Section 2: Background

- 2.1 SHA-256 compression function (recap from Viragh)
- 2.2 Schedule compliance sr (review Viragh's framework)
- 2.3 The MSB kernel and da[56]=0 condition (Viragh's foundation)
- 2.4 Cascade-1 / cascade-2 mechanism (writeups/sr60_collision_anatomy.md)

### Section 3: The sr=60 result

- 3.1 Certificate: M, W[57..60], hash, schedule_compliance metric
- 3.2 Verification: 3-machine reproduction, standalone C verifier
- 3.3 Comparison to Viragh's sr=60 prediction: same configuration, same
  kernel, broke through via deeper seed search
- 3.4 Search statistics: kissat seed=5 wall ~12h vs Viragh's 7200s timeout

### Section 4: Why this seed succeeded

- 4.1 Empirical observation: 24 prior seeds at the same configuration
  failed (project history). Seed=5 succeeded.
- 4.2 Stochastic interpretation: at slack-zero (sr=60), SAT solutions
  are measure-zero in the kissat decision space. Different seeds explore
  different decision orders; hitting the right order is the bottleneck.
- 4.3 Implication: Viragh's "structural barrier" framing was empirically
  tight (most configurations + most seeds → UNSAT/TIMEOUT) but not
  ABSOLUTE — specific (cand, seed) pairs DO yield SAT.

### Section 5: The sr=61 frontier

- 5.1 Slack analysis: sr=61 requires slack -64 (over-determined). 256-bit
  collision condition vs 192-bit freedom.
- 5.2 Empirical evidence: project's 1800+ CPU-h kissat search across 67
  candidates × multiple seeds × multiple budgets. **0 SAT, 0 UNSAT, all
  UNKNOWN/TIMEOUT.**
- 5.3 Viragh's sigma_1 conflict argument (47.9% XOR conflict statistical
  estimate; reference writeups/sr61_impossibility_argument.md).
- 5.4 Structural evidence from cascade-1 chamber analysis (F-series):
  - F12: 0/67 cands have de58=0 in 287B chambers
  - F14: cascade-1 at 7 slots = full collision iff schedule cooperates
  - F15: 0/67 default messages have cascade-1 alignment at slot 57+
- 5.5 Yale's guarded fiber finding (singular_chamber_rank bet):
  - Best guarded slot-57 prefix: HW=8 across 4 cands × 5M trials
  - Adaptive perturbation: 5M trials × 3.5M improvements, 0 changed-msg
    exact-guard hits
  - Conclusion: exact a57=0 manifold appears to be a single point at the
    default fill message; the guard valley is structurally thin.

### Section 6: Synthesis — what sr=61 evidence suggests

- 6.1 The "70% structurally infeasible" estimate (informal): based on
  weighted evidence above.
- 6.2 What would change the estimate:
  - For infeasibility: rigorous symbolic conflict computation (replacing
    47.9% statistical with exact GF(2)-linear analysis)
  - For feasibility: ANY found (kernel, seed) pair producing sr=61 SAT
- 6.3 Open research directions: alternative kernels, message modification,
  DC-SAT hybrid, GPU-accelerated solvers.

### Section 7: Discussion and conclusion

- 7.1 The sr metric is the right axis: progress is measurable and
  monotone in this dimension.
- 7.2 Each round step appears to require new techniques (sr=58 → sr=59
  needed gap placement; sr=59 → sr=60 needed seed exploration).
- 7.3 sr=61 may genuinely be the frontier. Or may yield to a yet-
  undiscovered technique. Either resolution is publishable.
- 7.4 Implications for SHA-256 deployment: at the SFS model, the safety
  margin is 4 rounds (sr=64 - sr=60). At the standard collision-resistance
  model, full SHA-256 collisions remain out of reach but the safety
  margin in the SFS axis is shrinking.

### Section 8: Reproduction (mirror Viragh's section 12)

- Compile + run the standalone C verifier in seconds
- Re-find via kissat: full M, full W, kissat command line, ~12h wall
- All artifacts in repo / supplementary material

## Artifacts already prepared (in repo)

| Artifact | Location | Purpose |
|---|---|---|
| sr=60 certificate (YAML) | `headline_hunt/datasets/certificates/sr60_n32_m17149975.yaml` | Authoritative cert |
| C verifier | `.../certificate_64r_sfs_sr60.c` | Standalone reviewer artifact |
| Python verifier | `.../verify_sr60_with_relaxed_W.py` | Cross-implementation check |
| Comparison memo | `headline_hunt/reports/20260427_viragh_vs_this_project_sr60.md` | Maps to paper Section 3 |
| sr=61 evidence synthesis | `.../20260427_sr61_evidence_synthesis.md` | Maps to paper Sections 5+6 |
| Cert anatomy writeup | `writeups/sr60_collision_anatomy.md` | Maps to paper Section 2.4 |
| Impossibility argument | `writeups/sr61_impossibility_argument.md` | Maps to Section 5.3 |
| Structural F-series | `headline_hunt/bets/cascade_aux_encoding/results/2026042*` | Maps to Section 5.4 |
| Yale's guarded probe | `headline_hunt/bets/singular_chamber_rank/results/20260427_*` | Maps to Section 5.5 |
| Overnight kissat data | `headline_hunt/bets/sr61_n32/overnight_kissat/results.tsv` | Updates Section 5.2 |

## What's MISSING for a clean draft

1. **Full reproducibility for re-finding the cert from scratch.** The cert
   has W[57..60]; the project's CNF generator + kissat seed=5 should
   re-discover it in ~12h on commodity hardware. Need to verify this
   on a 2nd machine and document the exact commands.

2. **Rigorous symbolic version of Viragh's sigma_1 conflict argument.**
   2000-sample correlation is suggestive but not proof. Replacing it
   with exact GF(2)-linear analysis would strengthen Section 5.3
   substantially. **Estimated effort**: ~1-2 days analytical work.

3. **DRAT proof attempts on small cases.** If any 4-free-position
   configuration at sr=61, N<=12, returns DRAT-verified UNSAT, that's
   a publishable infeasibility result for that subspace. **Estimated
   effort**: 1 day, automated.

4. **Authorship agreement** across fleet. Critical pre-submission step.

5. **Comparison to Mendel/Nad/Schläffer 2013** explicitly. Their work
   is the precedent for SFS reduced-round; Viragh extended; we extend
   further. ~half day of literature reading.

## Next-day action items (post overnight kissat)

1. Run `log_results.py` on `overnight_kissat/results.tsv` once
   dispatcher exits (~14:30 EDT 2026-04-27).
2. Refresh `headline_hunt/reports/dashboard.md`.
3. Write a 1-page status summary for fleet review.
4. Decide on outreach: do we contact Viragh / Li for collaboration,
   or finalize in-house?

EVIDENCE-level (this outline): WORK_PRODUCT — not a publishable artifact
itself, but the roadmap to one.
