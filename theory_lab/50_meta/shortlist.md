# Shortlist — the live footholds (narrative)

_The hand-written companion to the generated `../30_register/views/shortlist.md`. Read this first._

## The spine

One idea unifies the top three angles: **put a metric or algebraic invariant on the carry obstruction,
and attack the invariant — instead of enumerating messages.** SHA-256's only real nonlinearity is the
carry chain; the repo has characterized it combinatorially (a GF(2) carry automaton) and shown that
view is near-injective (zero pruning). The fresh move is to measure the carry obstruction a *different*
way and see whether the measurement is structured.

The three spine angles cross-feed: **2-adic** produces an additive invariant, **lattice** is its solver,
**coding theory** bounds the sparsity both depend on.

## The honest headline

All three are far likelier to yield a **rigorous "why the ~60-round wall exists" theorem** than a
finished collision. For a lab whose mandate is *reframing, not grinding*, that "why" deliverable is the
realistic prize — and all three probes are cheap enough to falsify within a day each.

---

## Foothold 1 — 2-adic valuation / FCSR span  `[P3 · cheap · probe-designed]`
**Reframe:** carry IS the 2-adic carry; the SHA round function is a T-function on `Z_2` (Anashin), and
the FCSR "2-adic span" (Klapper–Goresky) measures how far a carry-coupled sequence is from a short
rational recurrence. If `v2(ΔH)` grows linearly with enforced rounds, the `2^-2N` floor is just an
**additive invariant** in disguise — and additive invariants are attackable.
**Probe:** FCSR-span synthesis on the ΔW of the known sr=60 pair + `v2(ΔH)` trend across N∈{8,10,12,16},
reusing `lib/`. ~1 day. → `../40_deep_dives/dive_2adic-carry-valuation-newton.md`
**Skeptic:** SHR + boundary-crossing rotations break clean `Z_2` structure every round; a good hash has
large span *by design*. Most likely it re-derives the floor rather than beating it.
**Not a repeat of april28:** that scan killed the Hensel-*lift* reading (`repo-killed`); the *span/slope*
reading was never probed.

## Foothold 2 — message-expansion-code minimum distance  `[P3 · cheap · probe-designed]`
**Reframe:** linearize the schedule → a GF(2) code; a low-weight schedule-compliant difference is a
low-weight codeword. A min-distance bound on the last K rounds turns "each round costs `2^-2N`" into a
**static sparsity budget** — possibly a conditional impossibility theorem for sparse late trails.
**Probe:** build the linearized expansion generator matrix (reuse `16_gf2_kernel_search.py`), run a
low-weight-codeword search (Stern / information-set decoding). Hours. →
`../40_deep_dives/dive_expansion-code-min-distance.md`
**Skeptic:** the linear model over-counts (a light XOR-codeword need not survive carries). Pramstaller
et al. pushed linearized-SHA distance and did not break SHA-256 — realistic upside is a wall bound or a
trail seed, not a collision. **This is the Jutla–Patthak technique, never run on SHA-256's schedule.**

## Foothold 3 — carry-lifted lattice  `[P3 · cheap (1-round) · probe-designed]`
**Reframe:** lift `a+b=c (mod 2^32)` to `a+b=c+2^32·carry`; make the **carries** the unknowns. Schedule
compliance becomes "does a lattice coset contain a 0/1-carry vector" — a covering-radius question for
BKZ, deterministic, no per-round probability.
**Probe:** write the integer-lifted carry equations for the *single* open round (sr=60→61), ~tens of
variables, hand to LLL/BKZ (fpylll). → `../40_deep_dives/dive_carry-lifted-lattice.md`
**Skeptic:** dimension. The 7-round tail is ~1000-dim with a brutal box constraint; SHA gives many
equations with the same small coefficient `2^32` (the regime lattices hate). Probe the 1-round residue
first — the only size cheap enough to falsify. **Distinct from april28 item_07** (LLL-as-trail-completion)
and from the repo's MITM bet (attacks the residue's *carry* structure, not a forward table).

---

## Two also-rans worth a cheap afternoon

- **Survey propagation** `[P2 · cheap]` — is the residual *glassy/clustered* or *UNSAT-dense*? Run SP on
  an existing sr=60/61 CNF and read the magnetizations. High odds it doesn't converge on dense
  structured CNF; that non-result is itself informative.
- **Walsh / cLAT pre-SAT oracle** `[P2 · cheap]` — score which tail masks even survive (Wallén), to prune
  trails before SAT. **Caveat:** built for distinguishers over many samples, not for constructing one
  pair — at best a heuristic filter, complementary to Foothold 2 (weight vs correlation).

## The discipline that governs all of them

`../sha256_review/THE_THERMODYNAMIC_FLOOR.md` shows that **even an XOR-only (fully linearized) sr=60
times out at N=32** — so the barrier is "0-slack constraint geometry," *not carry-chain length*. Every
carry-based angle here must explain that, not contradict it. It is the built-in adversarial check: the
2-adic and coding angles both examine the *linearized* schedule precisely so they can speak to it.

## Explicitly parked (don't re-open without new evidence)

Algebraic geometry (= Gröbner, high-degree), additive combinatorics (counts, can't construct), tropical
(latency not existence), quantum/Grover (√ over residual only), tensor networks (**repo-killed**:
high-rank corpus). One-line kill reasons live in `../30_register/ideas.yaml` and `../20_adjacent_fields/CATALOG.md`.

## Next pass

Run the three spine probes (Footholds 1–3) on small N reusing `lib/`; write each verdict back into its
dive and `CHANGELOG.md`; promote survivors to a ready-to-paste repo bet, archive the rest with a
resurrection trigger.
