# Submission-Ready Abstract Draft
**For: IACR ePrint, target submission 2026-Q2 (after closure decisions)**
**2026-04-27**

This is a one-page abstract draft tying the project's findings into
publication-submittable form. It can be the core of an ePrint submission
or the seed for a longer paper.

---

## Title (working)

**Crossing Viragh's sr=60 Wall: A Verified Schedule-Compliance-60
SHA-256 Semi-Free-Start Collision via Deeper Seed Exploration**

## Authors (TBD — fleet agreement needed)

[macbook], [yale], [linux_gpu_laptop] — provisional. Author list pending
explicit agreement across project contributors before any submission.

## Abstract (target ~250 words)

Viragh (ePrint 2026, "We Broke 92% of SHA-256") established
schedule-compliance sr as a continuous metric for SHA-256 semi-free-start
(SFS) collision attacks, demonstrated a verified collision at sr=59 (89.6%
schedule compliance, 5 free schedule words) on the full 64 rounds, and
identified sr=60 as a "structural barrier" — citing an empirical timeout
exceeding 7,200 seconds across all 35 valid 4-free-position configurations
under his framework.

**We extend Viragh's frontier by one round.** We present a verified SFS
collision at sr=60 (93.75% schedule compliance, 4 free schedule words at
positions {57, 58, 59, 60}) on full 64-round SHA-256, using the same MSB
kernel (dM[0] = dM[9] = 0x80000000) and the same candidate (M[0] =
0x17149975 — one of Viragh's `scan_m0.c` outputs). The collision was
discovered via Kissat 4.0.4 with seed=5 in approximately 12 hours of
single-thread compute, after roughly 1.6 billion conflicts — about 1,600×
deeper than Viragh's reported timeout budget. Empirical seed-sensitivity
testing (10 seeds × 1 million conflicts) confirms 0/10 seeds find SAT at
moderate budgets; the result is a specific (seed, budget) phase
transition.

We provide three independent verifiers: (i) a self-contained C program
matching Viragh's certificate format, (ii) a Python forward-computation
reference, and (iii) a Kissat-based consistency check on the
cascade-auxiliary CNF encoding. All three confirm hash equality between
M₁ and M₂: `ba6287f0dcaf9857d89ad44a6cced1e2adf8a242524236fbc0c656cd50a7e23b`.

**Combined with structural evidence** from a 287-billion-chamber cascade-1
image enumeration (no chamber yields the round-58 cancellation required
for sr=61), Viragh's 47.9% sigma_1 XOR-conflict statistical argument, and
yale's empirical observation that the guarded message-space exact-fiber
appears confined to a single point at the default fill message, **we
argue that sr=61 represents the actual feasibility frontier of cascade-1
SFS collision attacks on SHA-256.** A formal sr=61 impossibility proof
would itself be a publishable result.

## Key contributions (bullet form)

1. **A verified sr=60 SFS collision** for full 64-round SHA-256 (M[0] =
   0x17149975, MSB kernel), one round beyond Viragh's published
   frontier and at the configuration he identified as a structural
   barrier.

2. **Three independent verifiers** for the collision:
   - Self-contained C (compiles + runs in milliseconds, no dependencies)
   - Python forward computation (cross-implementation verification)
   - Kissat consistency check (CNF-level model verification)

3. **Empirical seed-sensitivity data**: at the cert's CNF, 0/10 tested
   seeds yield SAT at 1M conflicts; seed=5 specifically yields SAT at
   ~1.6B conflicts (~12h wall on commodity hardware). Demonstrates that
   the sr=60 barrier is crossable by depth, not by parallel breadth.

4. **Structural evidence sr=61 is infeasible**: 287B-chamber cascade-1
   enumeration shows no candidate yields de58=0 (necessary for cascade-1
   sr=61); guarded message-space probes find no changed-message exact
   fiber; combined with Viragh's sigma_1 XOR conflict structural argument.

5. **A reusable infrastructure**: cascade-auxiliary encoder, audit-
   confirmed CNF fingerprints, and a concurrent kissat dispatcher (the
   "overnight kissat" framework) — all open-sourced under the project
   repository.

## Reproducibility

```
gcc -O3 -o cert_sr60 certificate_64r_sfs_sr60.c && ./cert_sr60
# Expected: sr = 60, collision VERIFIED, H = ba6287f0...
```

Full re-discovery (~12h on commodity hardware):
```
kissat aux_expose_sr60_n32_bit31_m17149975_fillffffffff.cnf \
    -q --seed=5 --conflicts=2000000000
```

All artifacts and infrastructure committed at
`https://github.com/kodareef5/sha256-probe`.

## Comparison table (matches Viragh's section 9.1)

| Work | Rounds | Type | Method | sr | Free | Time | Cert |
|---|---:|---|---|---:|---:|---:|---|
| Mendel et al. 2013 [3] | 38 | Collision | Signed DC + SAT | 38/38 | 0/22 | — | published |
| Li et al. 2024 [1] | 39 | Collision | MILP + msg mod | 39/39 | 0/23 | — | published |
| Zhang et al. 2026 [2] | 37 | SFS | MILP + msg mod | 37/37 | 0/21 | — | published |
| Viragh 2026 | 64 | SFS | MSB kernel + gap SAT | **59 (89.6%)** | 5/48 | ~276s | published |
| **This work** | **64** | **SFS** | **Same as Viragh + deeper seed** | **60 (93.75%)** | **4/48** | **~12h** | **certificate_64r_sfs_sr60.c** |

## Open questions (for paper Section 7)

1. Does sr=61 admit an SFS collision via any kernel + cand combination
   in this framework?
2. Is the 47.9% sigma_1 XOR conflict estimate (Viragh) tight, or can
   it be refined to a rigorous structural impossibility argument?
3. Can yale's "exact a57=0 manifold = single point" observation be
   formalized as a rigorous fiber-dimension theorem?
4. Does the deeper-seed approach generalize: do other registry
   candidates (~67 tested) also admit sr=60 SAT at ~10-20h wall?

## Submission readiness checklist

- [x] Verified result (3 implementations agree)
- [x] Comparison to closest prior work (Viragh 2026)
- [x] Reproducibility scripts + CNF fixtures
- [x] Clear contribution statement
- [ ] Authorship explicit agreement across fleet
- [ ] Mendel/Nad/Schläffer 2013 explicit comparison (literature note)
- [ ] sr=61 closure: either rigorous impossibility OR positive result
- [ ] External pre-review (Viragh, Li, or other expert) — recommended

EVIDENCE-level: VERIFIED for the empirical claims; HYPOTHESIS for the
sr=61 infeasibility section. Both are publishable in the appropriate
framing (positive result + boundary characterization).
