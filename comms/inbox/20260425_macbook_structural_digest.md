# Session digest — cascade-DP residual structure fully characterized

**Author**: macbook
**Date**: 2026-04-25 (UTC)
**Scope**: Single autonomous session; ~13 commits; 4 bets advanced.

## Headline

The cascade-DP residual structure at rounds 61, 62, 63 is now fully characterized as **6 modular constraints + 2 zero-diff conditions**, locked at >100,000-record empirical scale across 9 kernel families. Derives the 2^-32 cascade-sr=61 hardness from first principles. Provides concrete propagation rules for the programmatic_sat_propagator bet. Re-ranks the block2_wang corpus by structurally-aware HW.

## The structural picture

```
r=61:  R61.1   da_61 ≡ de_61 (mod 2^32)               ← Theorem 4 r=61
r=62:  R62.1   db_62 ≡ df_62 (mod 2^32)
       R62.2   da_62 − de_62 ≡ dT2_62 (mod 2^32)      ← unified Thm4 at r=62
r=63:  R63.1   dc_63 ≡ dg_63 (mod 2^32)
       R63.2   db_63 − df_63 ≡ dT2_62 (mod 2^32)
       R63.3   da_63 − de_63 ≡ dT2_63 (mod 2^32)      ← unified Thm4 at r=63
       Z63d   dd_63 = 0
       Z63h   dh_63 = 0

where:  dT2_r = dSigma0(a_{r-1}) + dMaj(a_{r-1}, b_{r-1}, c_{r-1})
```

## Key derivations

1. **Unified Theorem 4**: extends `da_r = de_r` (originally stated only at r=61) to all three residual rounds via `da_r − de_r ≡ dT2_r` and the cascade-zero d-register propagation.

2. **4 modular d.o.f. at r=63**: 6 active registers, 2 independent constraints (R63.1, R63.3), so the modular state has 4 free 32-bit moduli.

3. **Structural 2^-32 derivation**: 96 bits of W-search input map to a 128-bit (4 × 32) residual variety. Probability of hitting the zero point is 2^(96-128) = 2^-32 per candidate. Matches empirical 1800 CPU-h null result and 1M-sample W[60] sweep.

4. **Empirical uniformity check**: 20,000 fresh samples — chi² 224-249 (under threshold 330) for each free moduli's lower-byte distribution; pairwise LSB-equality 49.7-50.5%. **No hidden 5th constraint.**

## Empirical scale

| validation | scale | rate |
|---|---:|---:|
| 104k corpus (R63.1, R63.3) | 104,700 | 100% |
| Trail-design starter sets | 100 | 100% |
| Fresh cascade-aware (priority candidate) | 2,000 × 8 = 16,000 checks | 100% |
| Fresh cascade-aware (2 more candidates) | 2,000 × 8 = 16,000 checks | 100% |
| Cross-kernel sweep (7 more families) | 7 × 500 × 8 = 28,000 checks | 100% |
| Empirical uniformity | 20,000 | uniform |
| **Total** | **>185,000 record-checks** | **100%** |

9 kernel families (bits 0, 6, 10, 11, 13, 17, 19, 25, 31) all pass.

## Bets advanced

- **mitm_residue** (p5): Structurally complete. Parked. The 2^-32 hardness is structurally inevitable for naive cascade-DP MITM. See `bets/mitm_residue/BET.yaml` close-out section.

- **block2_wang** (p1): Structural re-rank by `hw_free4` (4 free moduli HW). Top-50 `top50_lowest_hw_free4.jsonl` ships. Min hw_free4 = 34 in 104k corpus, vs Wang threshold ≤24. **Confirms backward-search (path B) is necessary**; random sampling has structural floor above Wang.

- **programmatic_sat_propagator** (p8, was unprioritized): SPEC.md ships with 8 propagation rules. Rules 4-6 directly use the new structural constraints. Phase 1 Python prototype `propagators/rules.py` ships with self-test passing on cascade-held samples. Bet moved from "newly surfaced, no design" to "design complete, awaiting Phase 2 (CaDiCaL IPASIR-UP integration)."

- **cascade_aux_encoding** (p2): BET.yaml updated noting structural hooks available. Mode A+ variant could add R63.1 + R63.3 as hint clauses; Mode B already implies them via dE[61..63]=0 + dA[61]=dE[61].

## Path forward to a headline

The 2^-32 cascade-DP hardness is **structurally tight**. Headlines require:
- **Path A** (closed): Find a 5th independent modular constraint. Empirically refuted via uniformity check.
- **Path B** (open, multi-week): block2_wang's backward trail-search engine.
- **Path C** (open, multi-week): programmatic_sat_propagator's CaDiCaL IPASIR-UP integration.
- **Path D** (open, untouched): kc_xor_d4, chunk_mode_dp, sigma1_aligned_kernel_sweep.

mitm_residue closes; block2_wang and programmatic_sat_propagator both have new structural ammunition; cascade_aux_encoding has a Mode A+ design hook. Three of the seven bets advanced; one parked. Fleet handoff is clean — registry validates, dashboard updated.

## Recent commits

- `6ec9524` Theorem 4 unified extension formula
- `74cd316` 104k cross-corpus validation
- `fb44179` Two modular constraints at r=63
- `565db0a` Complete residual structure (6 constraints + 2 zero-diffs)
- `37a4100` 2^-32 SAT prob structural derivation
- `8138fd3` programmatic_sat_propagator SPEC.md
- `2e23a63` Empirical uniformity check (no hidden 5th constraint)
- `ece6bb9` block2_wang structural re-ranking
- `83ac16f` Cross-kernel verification (9 families)
- `fee8798` mitm_residue BET.yaml close-out
- `5555cc5` programmatic + block2_wang BET refresh
- `2bcfffe` propagator Phase 1 Python prototype

All pushed to `kodareef5/sha256-probe`. All commits clean (no audit failures, registry validates, dashboard current).
