# Viragh 2026 — "We Broke 92% of SHA-256: Full 64-Round Semi-Free-Start Collision at sr=59"

**Citation**: Robert Viragh, "We Broke 92% of SHA-256: Full 64-Round
Semi-Free-Start Collision at sr=59", March 27, 2026, self-published.
Local: `reference/paper.pdf` (8 pages, PDF v1.4).

**Status**: foundational paper for this project. Establishes the sr
schedule-compliance framework, the MSB kernel, the da[56]=0 theorem,
and the sr=60 hard-boundary that is the project's central target.

## TL;DR

Viragh introduces a continuous parameter `sr` (schedule-compliance)
interpolating between free-schedule SAT attacks (sr=16, trivial,
seconds) and full SHA-256 collisions (sr=64, the open 25-year-old
problem). The headline result: a hybrid precomputation+SAT method
finds a verified semi-free-start full-64-round collision at **sr=59
(89.6% schedule compliance)** in under 5 minutes on commodity
hardware. The paper identifies sr=60 as the empirical phase-transition
boundary.

## Method outline

### MSB kernel (Section 4)
- Message difference: `dM[0] = dM[9] = 0x80000000` — flipping ONLY
  the MSB of words 0 and 9
- **Carry-free property** (Lemma 1): bit 31 satisfies
  0x80000000 + 0x80000000 = 0 (mod 2^32) with no carry. Schedule
  expansion: `dW[16..23] = 0` follows by induction from the
  schedule recurrence (W[i-7] and W[i-16] both gap-9, cancel
  pairwise).
- **GF(2) optimality**: schedule's GF(2) matrix has full rank 512;
  MSB kernel is the UNIQUE OPTIMAL two-word kernel (longest
  consecutive run of zero-diff schedule words). No three-word
  extension improves it.

### Hybrid precomputation+SAT
1. **Phase 1 (Section 4.3)**: exhaustive scan over 2^32 values of
   M[0] (with M[1..15] fixed). For each candidate, run 57 SHA-256
   rounds and record M[0] when **da[56] = 0** (a-register XOR
   differential at round 56 equals zero). ~2 candidates expected
   per scan (P ≈ 2^{-31}). Throughput: 25M evals/sec → ~180 sec
   total.

2. **Phase 2 (Section 4.4)**: for each candidate, encode a 7-round
   SAT instance for rounds 57-63. With `gap placement` enforcing
   schedule equations for W[62] and W[63], only W[57..61] remain
   free. Reduced encoder: ~10K vars, ~59K clauses.

### The da[56] = 0 theorem (Section 5)
- **Theorem 1 (necessity)**: if da[56] ≠ 0, the 7-round SAT instance
  is unsatisfiable. Verified exhaustively.
- **Theorem 2 (sufficiency)**: if da[56] = 0, the 7-round SAT
  instance is satisfiable. **12 out of 12 candidates** produced
  verified collisions across 3 different M[1..15] configurations
  using PySAT and kissat independently.
- **Structural explanation**: SHA-256 state update is a shift
  register (b[r+1] = a[r], etc.). The a-register is the sole input
  point where T1 (h, e, f, g, K, W) and T2 (a, b, c) contribute.
  When da[56] = 0, the a-register is matched at round 57 entry; 7
  free schedule words give 448 bits of freedom vs 256 bits collision
  condition (slack 192 bits, more than sufficient).

### Gap placement (Section 6)
- **Insight**: free schedule positions need NOT be contiguous. The
  recurrence W[t] = σ_1(W[t-2]) + W[t-7] + σ_0(W[t-15]) + W[t-16]
  has a t-2 dependency through σ_1. If W[t-2] is a free SAT
  variable, W[t] can be ENFORCED — the solver picks W[t-2] to
  satisfy the schedule equation.
- **sr=58**: free = {57, 58, 59, 60, 61, 62} (shift gap one
  earlier). W[63] enforced because W[63] = σ_1(W[61]) + W[56] +
  σ_0(W[48]) + W[47], W[61] is free, others deterministic. Solver
  satisfies BOTH collision and schedule. Kissat solves in 7.0
  seconds.
- **sr=59**: similar with one more enforced equation, harder but
  feasible in ~5 minutes.

### Sharp barrier at sr=60 (Section 8)
- **sr=60 is the SAT phase transition boundary**. Pure SAT succeeds
  for sr ≤ 56; hybrid method extends to sr=57-59; **sr ≥ 60
  becomes infeasible** with current techniques.
- This is the project's central HARD target: the hybrid attack's
  reach plateaus exactly at sr=59. Extending to sr=60 requires
  additional structural insight or compute beyond commodity scale.

## The specific collision (Section 4.5)

```
IV  = standard H0 (6a09e667 ...)
M1[0] = 17149975, M1[1..15] = ffffffff (× 15)
M2 = M1 with M2[0] XOR= 0x80000000 (= 97149975) and
     M2[9] XOR= 0x80000000 (= 7fffffff)

Free words (gap positions 57-61):
  W1[57..61] = 35ff2fce 091194cf 92290bc7 c136a254 c6841268
  W2[57..61] = 0c16533d 8792091f 93a0f3b6 8b270b72 40110184

Schedule compliance: 43/48 equations (sr = 59, 89.6%)
H1 = H2 = edc59a70 12bb36dd b8fbcccc cd2e5445 5957ec4e d6c3c8e0 ff067757 8e7255c5
```

This exactly matches the project's verified-collision candidate
**m17149975_fillffffffff** at the MSB kernel. The project's
`headline_hunt/datasets/certificates/sr60_n32_m17149975.yaml` is the
re-verifiable artifact corresponding to this collision (and its sr=60
extension).

## Project's relationship to this paper

The project (`sha256-probe`) extends Viragh's framework as follows:

1. **Boundary push**: Viragh's empirical infeasibility at sr ≥ 60 is
   the project's hard target. The cascade-1 / mitm_residue / block2_wang
   bets all aim at sr=60 collisions as the next step beyond Viragh.

2. **Structural cascade-1**: the project's "cascade-1" structure
   generalizes Viragh's da[56]=0 condition. Cascade-1 forces 64 bits
   (d63=h63=0); these are 2× Viragh's 32-bit single-register condition.

3. **Multi-cand exploration**: where Viragh focused on the MSB kernel
   (m17149975), the project has built a 67-cand registry across many
   bit positions (kernels.yaml). The F70-F102 cert-pin sweep verified
   that the SAT tail is empirically infeasible across all 67 cands,
   not just MSB.

4. **Yale's heuristic**: yale's online Pareto sampler reaches HW=33
   EXACT-sym at LM=679 — going beyond Viragh's brute-force 2^32 M[0]
   scan with structural sampling. Yale's 10⁹ effective sample
   advantage is the project's empirical signature beyond Viragh.

5. **Algorithmic alternatives**: the principles framework has
   surfaced 8 polynomial-time algorithm candidates (matroid
   intersection, BP-Bethe, Σ-aligned F4 Gröbner, etc.) that might
   bridge Viragh's sr ≥ 60 barrier with rigorous guarantees.

## Key terminology this paper introduces

- **Schedule compliance sr**: number of the 48 schedule expansion
  equations (W[i] for i ≥ 16) that hold. Range [16, 64]; 16 = free
  schedule, 64 = full collision.
- **MSB kernel**: dM[0] = dM[9] = 0x80000000.
- **Gap placement**: enforcing schedule equations at non-contiguous
  positions by leveraging the σ_1(W[t-2]) recurrence.
- **da[r] condition**: constraint on a-register XOR differential at
  round r.
- **Hybrid precomputation+SAT**: combining brute-force scan over a
  small subset of variables (M[0]) with SAT for the remaining tail.
- **Domain-specific encoder**: SAT encoding optimized for SHA-256
  structure (3.3× faster than generic).

## Notable quantitative values

- Phase 1 throughput: ~25 million evaluations/sec (10-core OpenMP)
- Total Phase 1 wall: ~180 seconds
- Expected da[56]=0 candidates per 2^32 scan: ~2
- Tail SAT instance: ~10K vars, ~59K clauses (reduced encoder)
- Full attack wall time: < 5 minutes commodity hardware
- Phase transition: pure SAT ≤ sr=56, hybrid sr=57-59, infeasible
  ≥ sr=60

## Connection to project's principles framework

The recent principles arc (april28_explore/principles/) derived
multiple structural facts that complement Viragh's:

- **Σ-Steiner partial cover** (probe 72): the (32, 3, 1)-packing
  structure of SHA's Σ functions on Z/32. Viragh uses bit-31's
  carry-free property; the principles work generalizes the Σ
  pair-coverage structure across all bits.
- **Iwasawa Z₂-towers**: Viragh's a-pipeline / e-pipeline observation
  is reframed as a literal Z_2-tower with cascade Iwasawa
  λ-invariant = 22.
- **MW rank ≈ 108**: cascade-1's algebraic rank measures non-linear
  constraints beyond Viragh's da[56] linear condition. Viragh's
  condition is degree 1; cascade-1 has degree-1 + ~108 effective
  degree-≥2 constraints.

The project's principles work treats Viragh as the EMPIRICAL
STARTING POINT and seeks to characterize the structural rich content
between sr=59 (achieved) and sr=64 (open).

## Open questions raised by the paper

1. Why does sr ≥ 60 become infeasible at commodity scale? The
   paper observes the phase transition but doesn't fully explain
   it. The project's principles framework offers candidate
   explanations (cluster structure, dilute-glass criticality,
   Iwasawa invariants).

2. Are the 12 known sufficient conditions (da[56] = 0 candidates)
   the COMPLETE set, or do other conditions support collisions at
   sr=59-64? Project's empirical work has explored a much broader
   cand space (67 cands) and found cascade-1 universal across them.

3. Could gap placement be extended further (3+ positions)? The
   paper extends from sr=57 → sr=58 → sr=59. Beyond sr=59, the
   t-2 recurrence is exhausted and additional structure is needed.

## What this means for the project

Viragh + the project together establish:
- sr ≤ 56: pure SAT
- sr = 57-59: hybrid precomputation+SAT (Viragh)
- **sr = 60**: open, project's verified SAT exists at m17149975
  (this IS the same collision as Viragh's, just verified at the
  next sr level)
- sr = 61: project's HARD target; phase-transition prediction from
  principles framework says might be in different complexity class
- sr = 62-64: completely open

The project's headline-eligible result is sr ≥ 61 collision finding,
or alternatively a rigorous proof that sr ≥ 60 is fundamentally
infeasible (closing the open question).

## Status

Note written 2026-04-28. Paper read in full from `reference/paper.pdf`.
This note completes the literature.yaml `read_status: read` entry
that was missing a notes file. Future fleet machines can refer here
for a structured summary instead of re-reading the PDF.

The Viragh 2026 paper is the project's structural starting point.
Every empirical finding in the project's F-series log builds on or
extends Viragh's framework.
