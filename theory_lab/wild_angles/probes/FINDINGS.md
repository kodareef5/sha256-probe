# The empirical verdict — what running all 185 cards actually found

This is the result of executing the cheapest small-N probe for every `wild_angles` card (read-only toward
`../../../sha256_review`, no SAT, throttled). The per-card detail is in `cards/`, the ledger in `RESULTS.md`.

> **One-line summary:** the catalog's advertised cross-formalism *convergence* does **not** survive computation.
> Exactly **one** structural fact is real and reproduces across formalisms — `2^-2N` = two independent
> conditions, which was already the repo's own most-solid result. The two largest "convergence" clusters
> (`132`-as-corank and `0.74`) are a **category error** and a **non-sharp fit**, respectively. The 185-card
> catalog's true value was as a *falsification engine*.

## Final tally (185 cards)

| ✅ CONFIRMED | 🟢 SURVIVES (rename/classification) | ❌ KILLED | ⚪ INCONCLUSIVE |
|---|---|---|---|
| **11** (all `2^-2N`) | **25** | **147** | **2** |

(185 cards: 147 KILLED = 79%, 25 SURVIVES = 14%, 11 CONFIRMED = 6%, 2 INCONCLUSIVE. Every confirmed card is
the single `2^-2N` pillar.)

---

## The one thing that is real: `2^-2N` = two independent conditions

`sr=60 → sr=61` costs `2^-2N` because it forces one free schedule word (W[60]) to satisfy the recurrence,
which is **two** independent N-bit conditions: `g1=0` (the per-message value match) **and** `h=0` (the
inter-message difference compatibility), empirically independent (ratio 1.005 / 0.97 / 1.00). The algebraic
core `g2 = g1 + h` holds **exactly for all 946** N=10 collisions, so only 2 of {g1,g2,h} are free — rank 2.

This reproduced **independently from ~12 formalisms**, which is the real (and only) convergence:
- entropy-rank 1.999 (PH1) · correction-word cost jump (IN3) · 2-D additive-character factorization, null-
  calibrated (NT4) · rigidity codim-2 (RG1) · Brenier push-forward exponent 2.013 (OT1) · two IET endpoints
  (IE3) · Moser–Tardos convergent↔divergent at the wall (LL2) · first-moment E[X] crosses 1 at 60→61 (LL5) ·
  Fisher det-rank-2, slope −2.006 (IG2) · CAT(0) empty-square codim-2, ratio 1.00 (HY1) · OSC overlap, fails
  only at 61 (FR2) · Pontryagin "two conditions, one control" — w60 moves g1 but **cannot** move h (OC2) ·
  oriented-matroid corank 1→2 on {g1,h} (MA3).
- **Forward extension (resolved):** `sr=62 = 2^-4N` (measured 3×: CG3, CL2, RD2 — R=32 bits at N=8). The
  sr=60 collision has **four** free words W[57..60]; each sr-step spends one (value-match + diff-compat =
  `2^-2N`), so the two-conditions structure is **per enforced round**. (One agent, WE1, dissented with
  `2^-3N` by measuring the *weak* de-filter ladder and wrongly assuming free words were exhausted after 60.)

Everything else in the catalog either renames this, commits a category error, or dies on the carries.

---

## The big refutations

### 1. `132 = corank of one linear map` — a CATEGORY ERROR (confirmed ~20×)
The flagship convergence (~13 formalisms) is wrong as stated. Every honest, basis-independent dimension —
reachability corank (CT1), observability corank (CT5), rigidity self-stress (RG2), Fisher kernel (IG1),
free-prob spectral corank (FP2), sheaf H¹ (SH2), costate kernel (OC3), **matroid corank via `gf2_eliminate`
(MA1, the DISTRIBUTION flagship)**, do-orphans (CS1), 2-core / frozen-set / k-core shell (KC), discriminant
corank (QW3), zonotope degeneracy (GN3), IB sufficient-statistic (RD3), Galois precision-loss (CA3),
Turing-unstable modes (SO4), Loeb dimension (NS2), meet-irreducibles (FC1) — comes out **0 or 128, never a
stable 132.** The number 132 reproduces **only** as the repo's *single-bit deterministic-control census*
({a,b,e,f}@63 fully + 4 dc), which **tracks word width (4N+4)** — 23/28/46 bits at N=4/5/8, → fraction 0.5 —
so it is a width-scaling census artifact, not a basis-independent invariant. The "corank cluster" was ~13
lenses computing the wrong object or re-running the census. (Also: the *uncontrolled* set {a,b,e,f} is **not**
the *collision-common* set — in collisions a,b carry **zero** difference; HC2.)

### 2. `0.74` — NOT a sharp / derivable constant
Every derivation attempt failed to produce a sharp 0.74: differential transfer-operator (DY1: no
normalization gives log₂λ=0.74), Moran/carry-branching (FR1: gives 2^0.92), Sinkhorn entropy (OT2: floors at
1.0), Fisher–Rao volume (IG5: slope 8.4), Tutte/Greene (MA2: code is trivial), container/VC (HC1/HC4),
Pila–Wilkie (OM2: degenerate split), exchange-graph (CL4), rate-distortion R(0) (RD1). The repo's own
collision table refits to pooled slope **0.673** with per-N-class scatter **0.6–1.04**; 0.74 is an
endpoint-sensitive asymptotic fit, not a universal exponent. "~10 lenses derive 0.74" was meaningless because
the target isn't sharp.

### 3. There is NO round-60 knee (confirmed ~19×)
Rounds 57–60 are the **free cascade** — the solution set is the *entire* cube, perfectly tame (cell count 1,
alternation 0, ANF degree 0, group element present from r55, temperature 0, control/rigidity/reachability
rank full). The "wall" is the single schedule condition first appearing at **round 61** — a degrees-of-freedom
/ counting boundary (a clean **+2.000 integer step**, NS1), **orientation-independent → intrinsic** (CG4),
but **not** a complexity jump. The round function is identical every round, which already forbids a
round-specific jump. Every "dies/blows-up/cools/shatters at 61" claim dissolved into this, or into a
finite-chain terminus artifact at r63, or into free-word bookkeeping.

### 4. The hardness IS the carry nonlinearity
PC5: XOR-linearizing (deleting carries) makes the tail **Gauss-trivial** — no expander, no Tseitin
structure. MA2: the linear collision code `ker(A)` is **trivial (dim 0)** — there are *no* linear collision
codewords; the entire count is carry-nonlinear. Every linear / spectral / geometric / categorical reframing
dies precisely because it discards the carries where all the structure lives.

### 5. The de58 thread — closed
`|de58| = 2^hw(db56)` (de57/59/60 ≡ 1) is a **carry-collapse / Maj-AND image count** — non-monotone in N
(spikes 9@N12, drops 5@N13), **group-free** (the carry monoid is the flip-flop {KILL,PROP,GENERATE}, KR2),
not a subgroup/coset/ergodic/equidistribution/IET-tower/holonomy/TNN/stability invariant. ~9 cards (NT3, QI3,
IE2, CA2, LG3, HY6, FC4, OM4, RD1) reproduce it; **none derives new content** — HY6 confirms the mechanism
(carry-on→collapse) but it is a restatement. There is no deeper invariant to find.

---

## Meta-patterns (why so many failed the same ways)

- **RENAME (most of the 🟢 SURVIVES):** faithful relabelings of g1,h that add no prediction — lens
  PutGet/PutPut (CA1), c-vectors (CL2), Heyting meet ρ=1.0000 (TO2), P/N-density (CG3), Weihrauch product
  (WE1), Hall deficiency (OT5), up-to-context (CO3), free-entropy χ (FP4). The categorical structure fits
  perfectly but computes nothing new.
- **INVERTED mechanism:** cards that hit the real special objects but assign the *backwards* reason — CS2
  (claims rank-1 deficit; truth is full rank-2), ER1 ({a,b,e,f} are *lowest* resistance, not highest), LG1
  (string tension peaks at r57, not 60), TO4/TO5 (the "wall" features peak at r57 and *close* by 61).
- **SCALE mismatch:** RA5 — a Ramsey clique comparable to 64 rounds needs K~2^32, dwarfing SHA's dimensions.

## Genuinely useful byproducts (real findings, even from "failed" cards)
- `132` is a **width-scaling control census** (4N+4), not an invariant — corrects the repo's "CDCL artifact" framing.
- `sr=62 = 2^-4N`: the two-conditions structure is **per enforced round** (answers the Batch-B forward test).
- `de58` is a **carry-collapse Maj-image count** (mechanistic close of the thread).
- **NS3 internal/external partition:** which empirical laws are N-exact identities vs N-drifting counts.
- **LL2:** Moser–Tardos *constructively* finds sr=60 collisions and provably diverges at sr=61 (0 in the space).

## Bottom line
The lab's headline deliverable — the cross-formalism convergence — was an artifact of **un-run reasoning**:
when you compute the objects, `0.74` isn't sharp, `132` isn't a corank, the round-60 knee doesn't exist, and
the exotic lenses die on the carries. What is left standing is a single robust fact (the repo's own `2^-2N`
two-conditions), now corroborated ~12 independent ways and extended forward to `sr=62 = 2^-4N`. That
negative result — delivered by 185 falsifiable probes — is the real output.
