# Established Theoretical Framings (Novelty Baseline)

The working repo has built ~12 interlocking framings of the SHA-256 cascade
collision problem. **An idea is NOT novel against this lab if it merely
re-derives, re-names, or re-instantiates one of these.** Each framing below is
either VERIFIED (exhaustive / cross-validated), EVIDENCE (multi-approach,
gaps remain), or HYPOTHESIS (supported, untested against alternatives) — using
the repo's own `CLAIMS.md` tier vocabulary.

A recurring meta-pattern unifies almost all of them: **the collision *solution
set* is low-dimensional and well-structured (effective dimension ≈ N, polynomial
BDD, single state-diff trajectory), but every constructive route that tries to
exploit that structure collapses to brute force because the structure is a
property of the solutions, not of the search space.** Carry nonlinearity + the
rotation frontier are the shared mechanism behind the collapse.

## Quick reference table

| id | one-liner | core math object | hit-the-wall | tier |
|---|---|---|---|---|
| `cascade_dp` | force `da=0` round-by-round in M2 → O(2^8N)→O(2^4N) | per-round register-diff recurrence; da57=0, de60=0 | wall = the 24-bit g60/h60 residue; full collision still 2^4N | VERIFIED |
| `carry_automaton` | carry-diff pattern *is* the collision (bijection) | finite-state carry transducer; entropy = log2(#coll) | width = #solutions = exponential in N; useless as DP | VERIFIED |
| `transducer_window` | LSB→MSB transducer with rotation-induced lookahead | finite-state transducer / minimal DFA, syntactic monoid | rotation frontier inflates state to 2^{8N+98}; min-DFA size open | HYPOTHESIS |
| `bdd_poly` | collision function has poly-size OBDD: O(N^4.8) | OBDD over 4N vars; node count 0.38·N^4.82 (R²=0.93) | construction stays O(2^4N); bottom-up Apply blows up | VERIFIED |
| `anf_degree` | algebraic degree grows LSB→MSB tracking carry chains | ANF via Möbius transform; degree, monomial count | dense in message basis (degree N); no elimination speedup | EVIDENCE (VERIFIED at N≤8 restricted) |
| `modular_carry` | modular-add carry chains ARE the nonlinearity | carry-out variables; rotation frontier ≈ 25 bits | linearization (GF(2)) finds 0 collisions; carries irreducible | VERIFIED |
| `sr60_61_phase` | sr60→sr61 is a phase transition at rate 2^-2N | schedule constraint W[60]=σ1(W[58])+c; g1=0 AND h=0 | sr=61 ≈ 2^-32-rare per candidate; effectively unreachable | VERIFIED (rate), HYPOTHESIS (smoothness) |
| `hard_core_132` | 132 output bits have zero linear control → HW~74 plateau | per-output-bit deterministic-controller count | the hard core is genuinely random under W[57..60]; only SAT/MITM touches it | EVIDENCE |
| `rotation_kernels` | rotation-aligned kernels: ~20% more candidates, no SAT edge | kernel differential bit position vs σ0/σ1 rotation orbits | REFUTED as structural advantage; 20% is within solver noise | EVIDENCE (refuted) |
| `three_filter_da_de` | 6 register eqns at r61-63 collapse to ONE: dT1_61=0 | da=de identity (r≥61), dT2=0; de61=de62=de63=0 ⇔ collision | tightest reduction; still leaves carry-reachability of dT1_61=0 hard | VERIFIED |
| `kernel_fill_phase_diagram` | (kernel bit, fill) is a phase diagram of #enforced bits / #coll | per-(bit,fill) collision counts; alternating fills (0x55/0xAA) | curated registry was an observation artifact; rate ~2^-31 everywhere | VERIFIED (eligibility), EVIDENCE (fill effect) |
| `n_invariant_scaling` | collisions ~ 2^{0.74N}; structural picture N-invariant | log2(#coll)≈N; Thm4/R63 invariants across N∈{8..32} | the SHAPE lifts across N; the specific solutions do NOT (non-Hensel) | EVIDENCE (VERIFIED at small N) |

---

## Per-framing detail

### `cascade_dp` — round-by-round register-diff cancellation
A semi-free-start sr=60 collision is built as a **perfect register-zeroing
cascade**: choose M2's free schedule words round-by-round so that the
register-difference `da` is forced to 0 at round 57, which then shifts through all
8 register positions (`a→b→c→…→h`) over exactly 7 rounds, absorbing every
pre-cascade state-56 difference (diffs decrease 6→5→4→3→2→1→0). This is what
takes the naive O(2^8N) two-message search down to O(2^4N): once `da=0` is pinned,
only M2's four free words W57–W60 remain.
- **Math objects:** the SHA-256 round-update as a difference recurrence; cascade
  conditions `da57=0`, `de60=0`; the 7-round shift-register absorption pattern.
- **Established:** the exact 7-round absorption schedule; why the boundary lands at
  round 60 (where schedule compliance must begin); the verified N=32 cert mechanism.
- **Wall:** the residual after cascade concentrates in **24 bits** in registers
  g60/h60 (the oldest shifted e-register values) — the "cryptographic fault line."
  The full collision is still 2^4N; cascade-DP gives no sub-2^4N construction.
- **Source:** `../sha256_review/writeups/sr60_collision_anatomy.md`,
  `../sha256_review/q5_alternative_attacks/results/20260416_cascade_absorption_pattern.md`,
  `../sha256_review/writeups/cascade_structure_complete.md`.
- **Tier:** VERIFIED.

### `carry_automaton` — the carry pattern is the collision
Each sr=60 collision has a **unique** carry-difference pattern: the projection
(collision → carry-diff pattern) is an exact bijection, so carry entropy =
log2(#solutions) *exactly* (ratio 1.000 at N=4, 6, 8). Full per-addition carry
extraction shows transitions are **deterministic** (branching ≤ 2; perfect
permutation at N=8). Given the carry state at bit 0, the entire N-bit trajectory
is determined — collision finding is a bounded-width path problem *on the
solution set*. 42% of carry-diff bits are identical across all collisions
(universal across N and kernel-independent).
- **Math objects:** finite-state carry transducer over 49 carry bits; entropy;
  branching factor; invariance fraction.
- **Established:** the bijection (carry ↔ collision), determinism, 42% invariance,
  the a-path 100% invariance from round 59+.
- **Wall:** the bounded width = #solutions, which is **exponential in N**. Over the
  *full input space* (not the solution set) the carry-diff state width is 89–99% of
  2^{4N} (near-injective) → **carry-state DP gives ZERO speedup** (= brute force).
- **Source:** `CLAIMS.md` ("Carry entropy = log2(#solutions)", "Carry automaton
  transitions are deterministic", "42% carry-diff invariance", "Carry-state DP
  provides zero algorithmic speedup");
  `../sha256_review/q5_alternative_attacks/carry_automaton_builder.c`.
- **Tier:** VERIFIED.

### `transducer_window` — LSB→MSB transducer with rotation lookahead
Unifying object: the cascade collision language = strings accepted by a
**finite-state transducer** that processes the 4 words bit-by-bit LSB→MSB. The
carry-automaton, BDD-poly, tree-linearity, and 42%-invariance findings all map
onto this one transducer. The crux is the **rotation frontier**: Σ/σ functions
read bits at positions k+6, k+11, k+25 (mod N) that haven't been processed yet, so
the transducer must carry full register values (a "window"), inflating the state
space from ~2^98 (carries only) to ~2^{8N+98}.
- **Math objects:** finite-state transducer; OBDD of the accepting language;
  Myhill-Nerode equivalence / syntactic monoid; minimal-DFA size.
- **Established:** the framework that ties the empirical findings together; the
  rotation frontier as the reason the state space explodes.
- **Wall / open question:** *is the minimal DFA polynomial or exponential?* If
  polynomial → cascade collision finding ∈ P; if exponential → the poly BDD is an
  OBDD-ordering accident. The repo could not resolve this (later: the
  forward-completion quotient = Myhill-Nerode min layer width peaks near the
  collision count → **exponential** for round-ordered variable orders; see
  `graveyard_digest.md`#`chunk_mode_dp`).
- **Source:** `../sha256_review/writeups/20260416_transducer_framework.md`,
  `../sha256_review/writeups/carry_structure_unified.md`.
- **Tier:** HYPOTHESIS (framework; the central open question is theoretical).

### `bdd_poly` — the collision function has a polynomial OBDD
Represented as an OBDD over 4N Boolean variables (bits of W57–W60), the sr=60
collision function has **polynomial node count**: best fit `nodes ≈ 0.38 · N^4.82`
(R² = 0.93) over N=2..12. At N=12, 92,975 nodes compress a 35 TB truth table by
~3 billion×. The future-completion quotient width forms a perfect bell curve
peaking at ≈ #collisions — proving a constructive O(2^N)-state automaton *exists*.
- **Math objects:** OBDD / reduced ordered BDD; completion quotient; the empirical
  power law.
- **Established:** the polynomial structural complexity; that all collisions can be
  enumerated in O(N^4.8 + #coll) time *given the BDD*.
- **Wall (the "polynomial-BDD paradox"):** **building** the BDD requires O(2^4N)
  (full truth table) or needs the collisions first (collision-list builder). Pure
  incremental construction (BDD/SDD Apply) has **exponential intermediates** (10.5 GB
  SDD at N=4). Whether a polynomial-time *construction* exists is the central open
  question. This is exactly headline class 2 ("turn compactness into construction").
- **Source:** `CLAIMS.md` ("BDD of collision function has polynomial size: O(N^4.8)",
  "BDD completion quotient width = #collisions");
  `../sha256_review/writeups/paper_section4_bdd.md`;
  `../sha256_review/q5_alternative_attacks/bdd_parametric.c`.
- **Tier:** VERIFIED.

### `anf_degree` — algebraic degree grows LSB→MSB with carry chains
Full / restricted ANF via the Möbius transform: the collision function is
**maximally nonlinear** in the message basis. At N=4 the max degree = 16 (= #vars),
linear GF(2) rank is full, ~20K ANF terms per output bit, and all 120/120 variable
pairs interact quadratically (fully connected). The restricted ANF at N=8 shows a
**perfect degree staircase**: each bit position adds exactly 1 to the degree (d[0]
degree 7, h[0] degree 8) — degree tracks the carry chain length from LSB to MSB.
- **Math objects:** ANF / Möbius transform; algebraic degree; monomial count;
  linear (affine) rank.
- **Established:** d[0] is the algebraically weakest output bit; the LSB→MSB degree
  staircase; density in message vars vs sparsity (width 49) in carry vars.
- **Wall:** dense ANF ⇒ no algebraic-elimination speedup in the message basis. "The
  polynomial-time path is through carry space, not algebraic elimination." But carry
  space is itself near-injective (see `carry_automaton`).
- **Source:** `CLAIMS.md` ("d[0] is the algebraically weakest output bit",
  "Collision system is dense in message-variable basis but sparse in carry basis");
  `../sha256_review/writeups/anf_deep_dive.md`;
  `../sha256_review/q5_alternative_attacks/carry_polynomial.c`.
- **Tier:** EVIDENCE (VERIFIED on exhaustive N≤8 restricted ANF; full-SHA untested).

### `modular_carry` — modular-add carry chains are THE nonlinearity
The structural claim that the source of hardness is **arithmetic carry
propagation in modular addition**, not the Boolean Σ/Ch/Maj layer. Forcing
carry-out equality between the two messages at any bit position gives instant UNSAT
even at sr=59 where collisions exist (the "ghost carry" observation) — collisions
*require* carry divergence; linearizing the differential destroys the solution
space. GF(2) linearization of the collision function finds 0 of 49 collisions
(carry nonlinearity is irreducible). The rotation frontier (~25 bits: ROTR by
2,6,7,10,11,13,17,18,19,22,25) spreads carry information across all positions.
- **Math objects:** carry-out variables; XOR-vs-ADD difference algebra; the
  rotation orbit structure.
- **Established:** carry divergence is necessary; modular nonlinearity is the
  collision *mechanism*, not an obstacle; GF(2) linearization fails.
- **Wall:** there is no group/quotient that absorbs the carry structure linearly;
  Gaussian elimination on carries gives zero pruning (the quadratic Maj/Ch do ALL
  the work).
- **Source:** `CLAIMS.md` ("GF(2) linearization ... FAILS", "Carry elimination
  (linear) provides ZERO speedup", "Carry divergence is required ...");
  `../sha256_review/THE_THERMODYNAMIC_FLOOR.md` §4 (Ghost Carry).
- **Tier:** VERIFIED.

### `sr60_61_phase` — the sr=60→sr=61 phase transition at rate 2^-2N
The boundary between sr=60 (reachable) and sr=61 (the frontier) is a **phase
transition**, not a universal wall. The schedule constraint `W[60] = σ1(W[58]) +
constants` removes the free W[60] lever the a-path cascade needs. The
**cascade-break rate is 2^-2N** (corrected 2026-05-30 from an earlier 2^-N): sr=61
requires `g1=0 AND h=0` — an independent **value match** (W1[60]=sched1) *and*
**difference compatibility** — each uniform at 2^-N and independent (ratio 1.005
over 1e9 samples at N=10). So at N=32 the per-candidate rate is ≈ 2^-32-rare across
the whole registry → **effectively unreachable single-block** (explains 1800 CPU-h
/ 0 SAT). The e-path cascade (de60=0) is unaffected; the barrier is purely a-path.
- **Math objects:** the schedule recurrence; two independent per-message
  conditions; Poisson/2^-2N rarity model.
- **Established:** the 2^-2N rate (four independent proofs unified: σ1 conflict,
  critical pairs, carry-diff invariants, cascade-break); sr=61 is SAT at small N
  with partial enforcement (smooth, not a wall).
- **Wall:** this is a **rarity bound, not an UNSAT proof** — sr=61 is not proven
  impossible, just 2^-32-rare. Critical W[60] pairs are kernel-dependent.
- **Source:** `../sha256_review/writeups/sr60_sr61_boundary_proof.md`;
  `CLAIMS.md` ("sr=61 Cascade Break Theorem" + 2026-05-30 correction);
  `../sha256_review/headline_hunt/bets/coincidence_variety/RESULT_sr61_is_2minus2N.md`.
- **Tier:** VERIFIED (the 2^-2N rate); HYPOTHESIS (smooth-transition framing).

### `hard_core_132` — 132 uncontrolled output bits explain the HW~74 plateau
From a 10K diff-linear correlation matrix: **132 of 256 output bits have ZERO
deterministic linear control** by any single input-bit flip (registers da, db, de,
df at round 63, plus ~4 scattered dc bits). Under cascade constraints these behave
as random draws → expected Hamming weight 66 + ~8 = **74**, which matches the
empirical search plateau (random 75, SVD 74, hill-climb 78) *exactly*. This
explains why no single-bit / local search can break HW~66 and why only the SAT
solver (or a MITM that shrinks the hard core) finds collisions.
- **Math objects:** per-output-bit deterministic-controller count; the
  diff-linear correlation matrix; expected-HW-of-random-bits argument.
- **Established:** the 132-bit hard core; the quantitative plateau match; that the
  exploitable structure is ~124-dimensional, not 256.
- **Wall:** the hard core is genuinely random w.r.t. W[57..60] perturbations — any
  productive attack must model carry propagation explicitly (SAT) or split the
  compression function where the hard core is small (MITM).
- **Source:** `../sha256_review/writeups/hard_core_132_bits.md`.
- **Tier:** EVIDENCE.

### `rotation_kernels` — rotation-aligned kernels give no structural SAT advantage
Hypothesis (now **refuted**): kernel differential bits aligned with the σ0/σ1
rotation orbits would be more productive. Fleet scan: rotation-aligned bits average
4.86 candidates each vs 4.33 for non-rotation — a ~20% candidate-yield boost that
is **within SAT solve-time noise**, with no qualitative change in solver behavior.
Every tested non-rotation kernel bit also produces sr=61 candidates. Separately,
the Σ1/σ1 alignment hypothesis (predicting 0 eligible m0 at σ0-aligned bits) was
**falsified** at bits 3 and 18 — the curated 36-candidate registry was an
observation artifact, not a structural ceiling (registry expanded 36→39).
- **Math objects:** kernel bit position vs rotation orbit; candidate-yield counts;
  cascade-eligibility rate (~2^-31, baseline Poisson).
- **Established (negative):** rotation alignment is a ~20% statistical effect, not
  structural; eligibility is ~uniform across bits.
- **Wall:** no (bit, fill, M[0]) class shows >2× solve-time improvement; reopening
  needs kernel-pair *theory*, not more scanning.
- **Source:** `../sha256_review/writeups/rotation_aligned_kernels.md`;
  `negatives.yaml#rotation_aligned_kernels_not_structural`;
  `CLAIMS.md` ("Productive N=32 kernels are rotation-aligned — REFUTED",
  "Σ1/σ1 alignment hypothesis FALSIFIED").
- **Tier:** EVIDENCE (refuted).

### `three_filter_da_de` — da=de identity collapses the tail to one equation
For r ≥ 61, **da_r = de_r** (proven algebraically) and **dT2 = 0** unconditionally.
So the 6 active register equations at rounds 61–63 reduce to **ONE independent
constraint: dT1_61 = 0**; once satisfied, rounds 62–63 propagate deterministically.
Equivalently, `de61 = de62 = de63 = 0` is **exactly equivalent to collision** (zero
false positives) — only 3 e-register checks needed. This yields the "Single DOF
theorem" (7 of 8 register diffs constant at round 61; only dh61 varies) and a
concrete **9.7× structural-solver speedup** at N=8 (de61=0 filter prunes 99.6%).
- **Math objects:** the round-difference identities da=de, dT2=0; the de-filter
  cascade; single-degree-of-freedom state-diff trajectory.
- **Established:** the tightest reduction achievable (6 eqns → 1); exact
  collision-detection via 3 filters; the structural-solver speedup (~2^N).
- **Wall:** the reduction makes the *state-diff* problem trivial but leaves the
  **carry-reachability** of dT1_61=0 hard — collision finding = "find message words
  whose carry chains reach the unique target trajectory." (This is the same hard
  carry core as `carry_automaton`/`modular_carry`.)
- **Source:** `CLAIMS.md` ("da=de Equivalence and Single-Equation Reduction",
  "Three-Filter Collision Equivalence Theorem", "Single DOF Theorem",
  "Structural Solver: de61=0 filter gives 9.7x speedup");
  `../sha256_review/writeups/cascade_structure_complete.md`.
- **Tier:** VERIFIED.

### `kernel_fill_phase_diagram` — (kernel bit, fill) as a phase diagram
The collision count is governed by a 2-parameter phase diagram over the **kernel
differential bit** and the **fill** (padding of non-differential message words),
plus N. The MSB kernel (used throughout Viragh) is **suboptimal at every tested N**
(N=8 bit-6 gives 6.3× more collisions). **Alternating-bit fills** (0x55, 0xAA
variants) unlock huge counts at odd N (N=5 fill=0x15 → 1024 collisions, 27.7×;
N=9 fill=0x55 → 14,263). Non-(0,9) word pairs and even single-word differentials
work (N=8 dM[0]=2^6 → 321 with no word-9 flip). Critical W[60] schedule pairs are
kernel-dependent (bit-3 has the most). The "odd-N zero theorem" was **fill-dependent,
not fundamental**.
- **Math objects:** per-(bit, fill) collision counts; cascade-eligibility rate per
  (bit, fill) cell; alternating-fill carry-propagation favorability.
- **Established:** MSB suboptimality; alternating-fill unlocks; non-(0,9) kernels;
  kernel-dependent critical pairs; eligibility ~2^-31 uniform across bits.
- **Wall:** richer design space does **not** translate to solver tractability — the
  curated registry was an artifact; structural predictors (de58 image, hard-bit LB)
  are **search-irrelevant** at CDCL budgets (Spearman ρ ≈ 0). Compute should
  distribute by candidate *coverage*, not rank.
- **Source:** `CLAIMS.md` ("MSB kernel is suboptimal at every tested N",
  "Alternating fill patterns unlock massive collision counts at odd N",
  "Non-(0,9) word pairs ...", "Critical W[60] schedule pairs are KERNEL-DEPENDENT");
  `../sha256_review/headline_hunt/TARGETS.md` (de58 family findings);
  `../sha256_review/q1_barrier_location/`.
- **Tier:** VERIFIED (eligibility / suboptimality); EVIDENCE (fill mechanism).

### `n_invariant_scaling` — N-invariant scaling laws (collisions ~ 2^{0.74N})
The collision set has **effective dimension N**, not 4N: log2(#collisions) ≈ N (total
≈ 2^N), and the cascade structural picture is **N-invariant and candidate-invariant**.
Theorem 4 (`da_61 ≡ de_61 mod 2^32`) holds with 0 violations over 1,048,576 samples
at N=32 and across N∈{8,10,12,14,16,18}; R63 modular relations (dc=dg, da−de=dT2)
likewise. The cascade tree has branching factor ~1 after the W57 choice. The
empirical growth law is roughly collisions ~ 2^{0.74N} (kernel/fill dependent).
- **Math objects:** log2(#coll) vs N; the Thm4/R63 modular invariants; cascade-tree
  branching factor.
- **Established:** the structural SHAPE (trajectory, invariants, filter mechanism)
  is N-invariant; this is the foundation for "design at small N, scale to N=32."
- **Wall (critical):** the **specific solutions do NOT lift across N** — cascade-1 is
  **HARD non-Hensel** (april28 item 03: 0/1200 lift-compatible; lift residuals
  uniform-random). Only the shape is N-invariant; each N is its own search problem.
  This bounds any small-N→N=32 bootstrap.
- **Source:** `CLAIMS.md` ("Theorem 4 + R63 modular relations hold across N ...",
  "Cascade collision tree has branching factor ~1 ...");
  `../sha256_review/headline_hunt/bets/block2_wang/trails/n_invariants.py`;
  non-Hensel: `../sha256_review/april28_explore/items/item_03_padic.md`.
- **Tier:** EVIDENCE (VERIFIED at small N; the non-Hensel wall is VERIFIED-negative).

---

## How to use this file for novelty triage

Before promoting any idea, ask:
1. **Is it one of these 12 in disguise?** (e.g. "model carries as an automaton" =
   `carry_automaton`; "compile the collision function" = `bdd_poly`; "linearize the
   round function" = `modular_carry`; "lift small-N solutions" = `n_invariant_scaling`
   non-Hensel wall.)
2. **Does it cross a wall already documented above?** If so it needs to explain
   *how* it beats that specific wall, not just re-propose the framing.
3. **Does it respect the shared mechanism?** Any carry-based angle must explain the
   "structure-of-solutions-not-of-search-space" collapse and the 0-slack constraint
   geometry (see `prior_scan_digest.md` on THE_THERMODYNAMIC_FLOOR).
