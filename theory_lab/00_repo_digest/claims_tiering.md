# Claims Tiering (mirror of `../sha256_review/CLAIMS.md`)

The repo ranks every testable claim by an **evidence tier**. The lab uses the
same vocabulary so novelty/confidence comparisons are apples-to-apples.

## Tier vocabulary (repo's own definitions)

| tier | meaning |
|---|---|
| **VERIFIED** | reproduced, cross-validated, DRAT-checked where applicable (exhaustive at the tested scale) |
| **EVIDENCE** | consistent from multiple approaches, but gaps remain |
| **HYPOTHESIS** | supported by data, not yet tested against alternatives |
| **EXTRAPOLATION** | projected from trends, explicitly flagged as uncertain |
| **RETRACTED / DOWNGRADED** | previously claimed at a higher tier, demoted with reason |

Source for all of the below: `../sha256_review/CLAIMS.md`.

---

## VERIFIED (load-bearing)

- **sr=60 collision at full SHA-256 (N=32)** — *the principal result.* MSB kernel,
  M[0]=0x17149975, all-ones padding; certificate W1/W2[57..60] published; Kissat
  --seed=5 SAT ~12 h; cross-verified on 3 machines. Extends Viragh sr=59 → sr=60.
  Still **semi-free-start** (4 free schedule words) — NOT a standard collision.
- **sr=59 collision independently reproduced** — custom CSA-tree encoder, 220.5 s,
  assignment verified by native SHA-256.
- **sr=61 is SAT at N=6,8,10–14,16,18,20 with partial (single-bit W[60]) enforcement**
  — sr=61 is a smooth phase transition, not a universal wall (full-width N=32 sr=61
  remains genuinely open).
- **sr=60 is SAT at all non-degenerate word widths N=8–32** — continuous homotopy,
  no phase transition (gaps at N=26,29,31 timeouts; N=9 rotation-degenerate).
- **SA cannot find sr=60 collisions even where they provably exist** — 50K restarts ×
  500K steps best HW=8 at N=8; Kissat SAT in 4.3 s. SA "thermodynamic floor" is
  meaningless for feasibility; only CDCL navigates it.
- **Carry entropy = log2(#solutions) exactly** at N=4,6,8 — carry-diff pattern is a
  bijective fingerprint of the collision (ratio 1.000).
- **Carry automaton transitions are deterministic (branching ≤ 2)** — given carry
  state at bit 0, the whole N-bit trajectory is determined.
- **42% carry-diff invariance is universal across N and kernel-independent.**
- **MSB kernel is suboptimal at every tested N** — bit-6 gives 6.3× more collisions
  at N=8.
- **Alternating fill patterns unlock massive collision counts at odd N** — N=5
  fill=0x15 → 1024; N=9 fill=0x55 → 14,263. "Odd-N zero theorem" was fill-dependent.
- **Non-(0,9) word pairs produce sr=60 collisions** — even single-word dM[0]=2^6 → 321.
- **Register h is determined by registers a–g at N=4** — 7 independent register
  constraints, not 8 (cascade-2 automatic).
- **d[0] is the algebraically weakest output bit** (degree 7, N=8 restricted ANF);
  perfect degree staircase LSB→MSB.
- **Critical W[60] schedule pairs are KERNEL-DEPENDENT** — kernel bit-3 has the most
  (4); bit-1 of W[60] is a universal repair coordinate.
- **BDD of collision function has polynomial size: O(N^4.8)** — nodes ≈ 0.38·N^4.82,
  R²=0.93, N=2..12; construction still O(2^4N).
- **BDD completion-quotient width = #collisions** — constructive O(2^N)-state automaton
  EXISTS (bell curve peaking at #coll).
- **Carry-state DP provides zero algorithmic speedup** — carry-diff width 89–99% of
  search space (near-injective).
- **GF(2) linearization of collision function FAILS** — 0/49 collisions; carry
  nonlinearity is fundamental.
- **sr=60 is UNSAT for M[0]=0x17149975 (MSB kernel, all-ones padding)** — 29/32 sampled
  5-bit partitions UNSAT, Kissat+DRAT, CaDiCaL-confirmed (3 partitions timeout).
  *(Note: this is the SINGLE-block sr=60 cascade-1 result for this specific candidate;
  the verified N=32 sr=60 cert above is a different, satisfiable candidate vector.)*
- Plus the structural theorems carried in the RETRACTED/DOWNGRADED section but tagged
  VERIFIED: **Cascade Diagonal Structure Theorem**, **sr=61 Cascade Break Theorem**
  (rate corrected to 2^-2N), **Single DOF Theorem**, **da=de Equivalence /
  Single-Equation Reduction (dT1_61=0)**, **Structural Solver de61=0 filter (9.7×)**,
  **Three-Filter Collision Equivalence Theorem**.

## EVIDENCE

- **Theorem 4 + R63 modular relations hold across N∈{8,10,12,14,16,18,32}** — 0
  violations (1,048,576 samples at N=32). Cascade picture is N- and candidate-invariant.
- **Backward-construction algorithm correct at N=8, N=10, partial-pass N=12** — 946
  collisions at N=10 (100% verified); stratified BF speedup 15.67×. Pure block2 BC at
  M16 single-machine is INFEASIBLE (~80 days).
- **Σ1/σ1 alignment hypothesis FALSIFIED** — σ0-aligned bits 3 and 18 DO have eligible
  m0; curated 36-candidate registry was an observation artifact (expanded 36→39).
- **de58 image-size and hard_bit_total_lb predictors are SEARCH-IRRELEVANT** — Spearman
  ρ ≈ 0 (even mildly inverse) vs CDCL dec/conf; distribute compute by coverage not rank.
- **sr=60 is UNSAT for M[0]=0x17149975** (listed VERIFIED above; CLAIMS files it under
  EVIDENCE for the *partition-sampling* phrasing — 32/1024 partitions sampled).
- **Carry divergence is required for MSB-kernel collisions** (one candidate; "observation
  not theorem").
- **Collision system is dense in message-variable basis but sparse in carry basis**
  (N=4 ANF; width 49).
- **Cascade collision tree has branching factor ~1 after W57 choice** (N=8/N=10).
- **W[59] is the cascade's internal bottleneck** in direct and differential form.
- **sr=61 schedule mismatch is uniformly random at bit level** (N=10; no easy bits;
  partial K-bit enforcement succeeds with prob 2^-K).
- **Carry elimination (linear) provides ZERO speedup** — affine rank maximal; quadratic
  Maj/Ch do all the pruning.
- **Cascade absorption: register diffs decrease 6→5→4→3→2→1→0 over 7 rounds.**

## HYPOTHESIS

- **The barrier is candidate-dependent, not fundamental** — non-monotonic scaling,
  3–5× variance within the same N (could be solver-specific).

## EXTRAPOLATION

- **sr=60 at N=32 may be solvable in ~days of compute** — fit T = 0.87·1.47^N → ~21 h
  for N=32. Heavily caveated (mini-SHA→full-SHA unreliable; possible phase transition
  between N=21 and N=32). *(Note: this predates the achieved ~12 h N=32 sr=60 cert.)*

## RETRACTED / DOWNGRADED

- **"sr=60 bottleneck is dW[61] hamming weight"** → RETRACTED. Constant-HW dW[61] is
  anti-correlated with solve speed (worst candidate solves fastest).
- **"Productive N=32 kernels are rotation-aligned"** → REFUTED. ~20% candidate-yield,
  within noise, no structural advantage.
- **"Ghost Carry Theorem"** → downgraded to *observation* (one candidate/kernel/padding).
- **"Boomerang Algebraic Contradiction"** as primary explanation → 20% predictive
  accuracy; retained as family-specific diagnostic only.
- **"Thermodynamic Floor"** as a property of SHA-256 → it's a property of one candidate
  family under one kernel.
- **sr=61 Cascade Break rate** was stated 2^-N → **CORRECTED to 2^-2N** (2026-05-30):
  sr=61 ⟺ `g1=0 AND h=0`, independent (ratio 1.005 / 1e9 samples). This is a rarity
  bound, not an UNSAT proof.

---

### Caveat-tier reminders the lab should carry forward
- Almost every VERIFIED structural result is **exhaustive only at mini-SHA (N≤8–14)**;
  full-SHA (N=32) versions are EVIDENCE or EXTRAPOLATION. Don't quote a mini-SHA result
  as a property of SHA-256.
- The principal sr=60 cert is **semi-free-start with 4 free schedule words** — repeatedly
  flagged as NOT a standard collision.
