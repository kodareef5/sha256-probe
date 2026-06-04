# Prior Scan Digest — `../sha256_review/april28_explore/`

The repo already ran a **one-shot** survey (2026-04-28, ~3–4 h wall) of **36
mathematical structures** against SHA-256 collision finding. This digest captures
its verdicts, flags what was actually *probed* vs only reasoned, and — most
importantly — lists the **live unprobed wedges** the lab should pick up rather than
re-survey. The scan's own meta-diagnosis (it went too shallow and stale) is the
reason the lab exists as a *living* register instead of another one-shot.

Sources: `../sha256_review/april28_explore/01_ITEM_LIST.md`,
`.../99_FINAL_REPORT.md`, `.../principles/META_LESSONS.md`,
`.../items/item_03_padic.md`.

## (a) The 36 items with verdicts

Verdict scale used by the scan: **DEAD** / **WEAK** / **MILDLY-PROMISING** /
**PROMISING** / **STRONG-NEGATIVE**.  **P** marks an item that was actually probed
with code (not just reasoned).

| # | item | verdict | one-line |
|--:|---|---|---|
| 01 | Prime distribution / zeta zeros | WEAK **(P)** | k=64 forced bits (=d63=h63=0) fits the F101 HW distribution exactly |
| 02 | Continued fractions | DEAD | descriptive only |
| 03 | **p-adic / Hensel** | **STRONG-NEGATIVE (P)** | cascade-1 is HARD non-Hensel; formally explains the F91 retraction |
| 04 | Modular forms / theta | DEAD | needs a lattice; SHA isn't (directly) a lattice |
| 05 | Galois theory | DEAD | needs a field; SHA mixes XOR + ADD |
| 06 | Elliptic curves over F_p | DEAD | categorical mismatch |
| 07 | **LLL / lattice reduction** | PROMISING-TOOL **(P)** | fast linear-completion step for a trail; not a novel attack |
| 08 | Algebraic geometry / schemes | DEAD | needs smoothness (= item 03) |
| 09 | **Tropical algebra (max,+) / Dijkstra** | **PROMISING** | could find a provably global LM-min trail; beats the sampler — **NOT probed** |
| 10 | K-theory / vector bundles | DEAD | finite K-theory = Z-counting |
| 11 | Hopf algebras / quantum groups | DEAD | no comultiplication |
| 12 | Schubert calculus | DEAD | wrong shape |
| 13 | Quasigroups / Latin squares | DEAD | no cancellation structure |
| 14 | Catalan / Dyck paths | DEAD | descriptive; peak-and-converge ≈ Dyck |
| 15 | Symmetric functions / Young tableaux | DEAD | wrong group symmetry |
| 16 | Combinatorial species | DEAD | counting without algebra |
| 17 | Ramsey theory | DEAD | existence proof, not finding |
| 18 | Chromatic / Tutte polynomial | DEAD | too expensive; treewidth = d4 negatives |
| 19 | Knot theory / braid groups | DEAD | no braid structure |
| 20 | **Persistent homology / TDA** | **MILDLY-PROMISING** | structural map of the W-witness landscape — **NOT probed** |
| 21 | Cobordism theory | DEAD | no manifold |
| 22 | Penrose tilings / aperiodic order | DEAD | SHA designed random-looking |
| 23 | Brownian motion / SDE | DEAD | descriptive language |
| 24 | Percolation theory | DEAD | descriptive language |
| 25 | **Random matrix theory** | **MILDLY-PROMISING** | round-Jacobian spectrum probe possible — only partially touched |
| 26 | Free probability / R-transform | DEAD | overkill |
| 27 | Information geometry / Fisher | DEAD | Fisher metric uncomputable |
| 28 | Wavelet / multiresolution | DEAD | no clear payoff |
| 29 | **Fourier on finite groups (non-XOR)** | WEAKLY-PROMISING **(P)** | Walsh + Z/2^32 mismatch is SHA's strength; Bohr-set methods maybe novel |
| 30 | Cellular automata | DEAD | wrong scale |
| 31 | Synchronizing automata / Černý | DEAD | wrong scale |
| 32 | Kolmogorov complexity | DEAD | uncomputable |
| 33 | Surreal numbers / CGT | DEAD | wrong structure (1- vs 2-player) |
| 34 | **Spectral graph theory** | WEAKLY-PROMISING | dependency-graph spectrum probe possible — **NOT probed** (partly via #25) |
| 35 | **Tensor networks / MPS** | STRONG-NEGATIVE **(P)** | "most novel" → cascade-1 MPS-hostile; bond dim linear in corpus, ~80× slower |
| 36 | Causal sets / discrete spacetime | DEAD | renamed dependency graph |

**Tally:** 27 DEAD, ~5 weak/mildly-promising, 2 strong-negatives (03, 35), 1
promising-tool (07), 1 promising-unprobed (09). The scan did **not** yield a
"SHA-is-broken-via-X" result; it yielded 2 paper-class structural **negatives** and a
short list of unprobed threads.

## (b) Probed vs not probed

**Actually probed with code (5 items):**
- **01** (prime/RMT bit-frequency) — confirmed 64 forced bits = d63⊕h63 at 70.7σ.
- **03** (Hensel lift) — 0/1200 compatible; STRONG-NEGATIVE. *(Only the LIFT reading.)*
- **07** (LLL) — usable as a linear-completion tool.
- **29** (Walsh-Hadamard / bit-frequency) — exactly 64 bits forced (d, h registers).
- **35** (MPS bond dimension) — linear-in-corpus scaling; STRONG-NEGATIVE.

**Reasoned but NOT probed (the rest of the 36)** — including, importantly, several
tagged promising. The scan's verdicts on unprobed items are *analytic guesses*, not
empirical results.

## (c) The LIVE unprobed wedges  *(the actionable part)*

These are threads the scan flagged as promising but **never tested**. They are the
lab's most concrete starting points because they are *not* yet covered by any repo bet
or negative:

1. **item 03 — Newton-polygon / 2-adic-valuation SLOPE reading.** *The Hensel-LIFT
   reading was probed and killed; the SLOPE reading was only reasoned.* item_03_padic.md
   sketches it (Bridge C): each round's polynomial over Z_2 has a Newton polygon whose
   slopes (0 from ROTR/XOR, 1 from ADD-carry) control 2-adic precision; non-decreasing
   slopes through the schedule would *explain* the non-Hensel failure structurally
   rather than just observing it. **This is a genuinely open wedge** — distinct from the
   killed lift result. (Reopen trigger for the non-Hensel negative, per
   `graveyard_digest.md`.)
2. **item 09 — tropical (max,+) Dijkstra for a provably GLOBAL LM-min trail.** Yale's
   online sampler finds a *local* LM-minimum (HW=33/LM=679 on bit28). A Dijkstra over
   the F32 corpus + LM-cost graph would return the **provable global** optimum
   (~500 LOC, ~10 min). The scan explicitly recommended building it; never built.
3. **item 20 — persistent homology of the W-witness landscape.** ~30–50 LOC + ~30 min;
   could reveal unsampled regions of the F101 W-witness corpus. Never probed.
4. **item 25 — random-matrix theory on the round-Jacobian spectrum.** Only partially
   touched (sparse matrix doesn't match Wigner; one leading eigenvalue ≈ 250). A proper
   round-Jacobian spectral probe is open.
5. **item 34 — spectral graph theory of the dependency graph.** Tagged weakly-promising,
   never probed (partly overlaps #25).

> Triage note: items 09, 20, 25, 34 are *measurement* wedges (map structure, possibly
> beat the sampler); item 03-slope is an *explanatory* wedge (turn an empirical negative
> into a structural theorem). None duplicate an open bet. The MPS (35) and Hensel-lift
> (03) hopes are **dead** — do not re-propose them as attacks.

## (d) The `principles/` sub-scan and its self-diagnosis

Beyond the 36 items, the scan spawned a `principles/` sub-arc: ~100 derived
cross-pollination files (17+ syntheses, 25+ deep dives). `META_LESSONS.md` records
both what worked and a candid self-diagnosis:

**What worked:** cross-pollination *across* items was the real unit of insight (single
items were shallow); pure-thought derivations yielded quantitative invariants from SHA's
published parameters (Σ-Steiner Cayley independence number α=4, treewidth ≈ 28, spectral
gap = 2/3, Galton-Watson branching ≈ 2.92); multiple independent derivations cross-checked
to the same numbers (MW rank ≈ 108 ≈ class-group log); every synthesis specified explicit
falsifiers (and several got DEAD-confirmed by existing data — KPZ β=0, Lévy sub-exponential
tails).

**Self-diagnosed failure modes (why this is a *baseline*, not a result):**
- **Minutes-per-item was too shallow** — first-pass dismissals were systematically too
  quick; ~15 items got revised *upward* on re-engagement. Budget HOURS, not minutes.
- **Literature was thin** — "novel relative to SHA cryptanalysis" was claimed *without*
  an exhaustive lit search; the "12 novel framings" count is uncalibrated against prior art.
- **Cross-pollination came late** — identified only after all individual items, not early.
- **One-shot went stale and sprawled** to ~100 terminal files — directly motivates the
  lab's living-register design (`30_register/ideas.yaml` as single source of truth +
  CHANGELOG heartbeat).
- **Implementation gap** — the 8 algorithmic candidates have pseudocode only; "actionable"
  ≠ "executable" (weeks-to-months from pseudocode to a benchmarked result).

## (e) THE_THERMODYNAMIC_FLOOR — the constraint any carry angle must explain

`../sha256_review/THE_THERMODYNAMIC_FLOOR.md` (the sr=60 MSB-kernel impossibility study)
carries one finding the lab should treat as a hard constraint on *all* carry-based ideas:

> **The "Carry Homotopy Correction" (§7.3):** replacing every modular addition with XOR
> — i.e. the **fully linearized** model with no carry chains at all — *still times out*
> on sr=60 at N=32. This **falsifies "carry-chain length is the primary barrier."** The
> real obstruction is **0-slack constraint geometry** at 32-bit scale (256 bits of
> freedom vs 256 bits of collision constraint), independent of whether the arithmetic is
> modular or XOR. The precision-homotopy SAT results at small N reflect scale reduction
> (fewer variables), not shorter carry chains.

Implication for the lab: any angle whose pitch is "tame the carry chains / linearize the
carries / exploit carry locality" **must explain why the XOR-only instance is also hard.**
The barrier is geometric (slack/constraint count), not arithmetic-depth. (This sits
alongside `modular_carry` in `established_framings.md`: carries are the *mechanism* of
collision propagation and the source of nonlinearity, yet *removing* them does not make
sr=60 easy — both can be true because the hardness is the zero-slack geometry.)

Supporting context from the same document the lab can cite: the MITM geometry localizes
the obstruction to **24 bits in g60/h60** (232/256 cone-intersection), and the
constant-folding insight (fixing bits at *encode* time vs via unit clauses gives
qualitatively different instances) is the methodological backbone of the UNSAT evidence.
