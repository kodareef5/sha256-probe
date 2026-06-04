# Deep dive — `expansion-code-min-distance`

> **Status: `probe-designed` — the probe below is DESIGNED, NOT YET RUN.**
> Register entry: `30_register/ideas.yaml#expansion-code-min-distance`. Lens: coding-theory.
> Spine: *the schedule is a linear code; a sparse compliant difference is a low-weight codeword, so the
> minimum distance is the static sparsity budget any single-block trail must pay.*

## The structure

The SHA-256 message schedule is the recurrence
`W[i] = σ1(W[i-2]) + W[i-7] + σ0(W[i-15]) + W[i-16]` (canonical form in `../sha256_review/lib/sha256.py`:
`sigma0(x)=ROR(x,7)^ROR(x,18)^SHR(x,3)`, `sigma1(x)=ROR(x,17)^ROR(x,19)^SHR(x,10)`). The 16 input words
`W[0..15]` are free; the remaining 48 are forced. **Drop modular addition to XOR** and every term becomes
`GF(2)`-linear (a rotation/shift is a permutation/projection matrix; XOR is the field's addition). The whole
expansion is then a single **linear map `GF(2)^512 → GF(2)^2048`** — 16 free words in, 64 expanded words out —
and `16_gf2_kernel_search.py` already builds exactly this `512×2048` generator (its `build_schedule_expansion_matrix_gf2`
stacks `sigma0_mat`, `sigma1_mat` over the recurrence). The single fact that makes this non-decorative:

- The **image of that map is a linear code** `C ⊆ GF(2)^2048`. A nonzero **schedule-compliant XOR-difference** —
  a difference `ΔW` that the linearized schedule can actually realize — is precisely a **nonzero codeword** of `C`.
- The governing quantity is the code's **minimum distance** `d(C)` = the minimum Hamming weight over nonzero
  codewords. Restricted to the last `K` expanded words, `d_K` **lower-bounds the number of active words a
  differential trail must carry through the last `K` rounds**. That word-count is the raw material the project's
  `~2^{-2N}`-per-round wall is assembled from: more forced-active words ⇒ more independent per-round conditions.

So the lens reframes "how improbable is a late-round trail?" (a per-round probability) into "how sparse *can*
a compliant difference even be?" (a static, message-independent code invariant). It is the *additive-coding*
sibling of the ANF-degree reading, not a competitor to the SAT search.

## First-instinct dismissal

Linearizing **over-counts in both directions**. A low-weight XOR-codeword need **not** be a
modular-addition-compatible trail — carries can extinguish a difference that the XOR model thinks survives,
and equally can spawn one the XOR model thinks is absent. So a *small* `d_K` is **necessary-not-sufficient**:
it exhibits a sparse *linear* difference, but says nothing about whether any modular instantiation of it has
nonzero probability. Symmetrically, a *large* `d_K` is a barrier **only inside the linear approximation** — the
real schedule could (in principle) admit sparse trails the linear code forbids, because carries enlarge the
realizable difference set. The honest read: this measures the **linear sparsity budget**, a bound that brackets
but does not equal the true differential cost. That is the same caveat the register row records
(`necessary-not-sufficient (XOR weight need not survive carries)`).

## Devil's-advocate bridges (the live ones)

**Bridge 1 — last-`K` min-distance LOWER bound as a "why the ~60-round wall" theorem.** Run a Jutla–Patthak-style
*lower* bound (the hard direction: certify that **no** light codeword exists) on `C` restricted to the last `K`
rows for `K ∈ {4,8,16}`. If `d_K` stays **high** into the sr≈60 window, then **sparse late-round trails are
impossible in the linear model** — a structural, conditional-on-linearity explanation of why single-block attacks
stall near round 60, expressed as a code bound rather than an empirical timeout.

**Bridge 2 — a surprisingly LIGHT codeword as a ready-made sparse-trail seed.** The same search, run for an
*upper* bound (exhibit a light codeword), is cheap. If `d_K` comes out **unexpectedly low**, the witnessing
codeword is a concrete sparse schedule-difference the differential/SAT pipeline has not been exploiting — hand it
to the trail-completion line as a seed (does any carry instantiation give it nonzero probability?). This is the
SHA-1 story in reverse: there, `≤44` overall and only `~30` in the last 64 words was the slack the `2^69` attack
rode; here we are asking whether SHA-256's schedule hides an analogous soft spot.

## The adversarial check this angle must pass

`../sha256_review/THE_THERMODYNAMIC_FLOOR.md` (line ~237) reports that the **fully XOR-linearized sr=60 instance
ALSO times out at N=32**, and concludes the barrier is "**0-slack constraint geometry**, regardless of whether
arithmetic is modular or XOR" — i.e. **not** carry-chain length. This is a *direct threat* and the key tension of
this dive, because the expansion code lives **entirely in that same linearized world**. Two outcomes, and they are
not the same finding:

- **(a) `d_K` is high.** Then the code distance *explains* the XOR-only hardness: the linear instance is hard
  *because* every compliant difference is dense, so no sparse certificate exists for a solver to find fast. The
  thermodynamic floor's "0-slack geometry" and this dive's "high min distance" would be **two names for one fact**,
  and the dive earns a genuine "why the wall (linear model)" deliverable.
- **(b) `d_K` is low.** Then the XOR-only hardness is **NOT** about code distance — a sparse compliant difference
  *does* exist, yet the linearized SAT instance still times out, so the difficulty is pure 0-slack constraint
  *geometry* (solver-search hardness) independent of sparsity. That is the more interesting and more dangerous
  finding: it both contradicts the naive "dense ⇒ hard" story and produces a seed (Bridge 2).

State the tension plainly: **does the linear code's minimum distance EXPLAIN the XOR-only N=32 hardness, or is that
hardness 0-slack search geometry independent of code distance?** The probe is precisely the instrument that decides
between (a) and (b). It also cleanly cross-checks `2adic-carry-valuation-newton`, which probes the **2-adic span**
of the *same* linearized schedule — distance (this dive) and span (that one) are two metrics on one linear object,
and they should agree on whether the linear model is "rich" or "rigid."

## Most plausible translation

`d(C)` and the last-`K` restriction `d_K` for `K ∈ {4,8,16}`, computed on the linearized SHA-256 expansion
generator. The cheap, diagnostic deliverable is the **upper bound** (a low-weight-codeword search returns either a
light witness → Bridge 2, or persistent high weights → evidence for Bridge 1). A *certified* lower bound (the
Jutla–Patthak hard direction) is the stretch goal; the upper-bound search alone already resolves the (a)/(b)
tension well enough to act.

## Probe design (cheap, hours-to-a-day; reuses `16_gf2_kernel_search.py` + `lib/sha256.py`, NO SAT)

Inputs: only the schedule's algebraic structure — no certificate, no message instance needed (the code is
message-independent). All primitives from `lib/`; the generator matrix from the existing GF(2) machinery.

- **A (build the generator).** Reuse `build_schedule_expansion_matrix_gf2` from `16_gf2_kernel_search.py`:
  `sigma0/sigma1` as `32×32` `GF(2)` bit-maps (its `rotr_matrix`/`shr_matrix` XORed exactly as
  `lib/sha256.py` defines them), recurrence rolled to `W[16..63]`, giving the `512×2048` generator `G`. The
  expansion-only block (`W[16..63]`, dropping the identity `W[0..15]`) is the parity object of interest; restrict
  rows to the last `K` words for the windowed distances.
- **B (low-weight codeword search).** Feed `G` to a standard, mature, off-the-shelf low-weight-codeword /
  information-set-decoding routine — **Stern** or **Canteaut–Chabaud** (both small and well-understood). Search the
  full code for `d(C)`, then the last-`K` restrictions for `d_K`, `K ∈ {4,8,16}`. The dimension is only 512, so
  ISD is comfortable.
- **C (optional lower-bound certificate).** If an upper-bound witness is *not* found and the weights look high,
  attempt the Jutla–Patthak-style *lower* bound (partition the information set, certify no codeword below threshold
  in the last `K`). This is the harder direction and only needed to upgrade Bridge 1 from "evidence" to "bound."

No SAT, no solver runs, no carries — strictly the linear object.

### Expected-outcome table

| Observation | Meaning | Action |
|---|---|---|
| `d_K` high in last `K` (sr≈60 window) | sparse late trails impossible in the linear model | **PROMOTE** as a wall bound (conditional on linearity) |
| `d_K` high AND matches the XOR-only N=32 hardness | code distance *is* the "0-slack geometry" | strong "why the wall" note; cross-link THE_THERMODYNAMIC_FLOOR |
| `d_K` surprisingly low (light witness) | a sparse compliant difference exists | **PROMOTE** to repo as a trail-candidate seed → hand to SAT/differential line |
| `d_K` low BUT XOR-only N=32 still times out | hardness is search geometry, not sparsity | flag as a sharp negative against "dense ⇒ hard"; still seed via Bridge 2 |
| `d_K` ≈ the known ANF degree bound | reproduces what's already measured | **ARCHIVE** (fires the kill criterion — neither forbids nor seeds) |
| span (2adic dive) and distance disagree | one metric mis-reads the linear model | re-examine generator construction before trusting either |

## Honest verdict (pre-probe)

Realistic upside is **structural insight or a trail seed, NOT a finished collision**: Pramstaller–Rechberger–Rijmen
pushed "minimum distance of linearized SHA" and Jutla–Patthak certified bounds for SHA-1-style expansion, and
**none of that broke SHA-256**. The most likely outcome is a *high* last-`K` distance that re-expresses the
sr-wall as a linear-code bound — a clean "why the wall" deliverable for a reframing-mandate lab, and the
probable resolution of the (a)/(b) tension toward (a). The genuinely exciting tail is a *light* codeword (Bridge 2),
which would be a free sparse-trail seed; the genuinely *uncomfortable* tail is low distance with the XOR-only
instance still timing out, which would say the linear hardness is search geometry, not sparsity. Either way the
computation is **cheap and decisive**, which is exactly what earns the register row. Plausibility **3**.

`[VERDICT: PROBE-DESIGNED — NOT YET RUN. **This is a DESIGNED probe, not a run result.** Promote on a high last-K min distance (wall bound) or a surprisingly light codeword (trail seed); archive if d_K merely reproduces the known ANF degree bound. Realistic prize is structural explanation or a seed, not a collision.]`
