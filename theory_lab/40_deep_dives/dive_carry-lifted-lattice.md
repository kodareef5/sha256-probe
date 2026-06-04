# Deep dive — `carry-lifted-lattice`

> **Status: `probe-designed` — the probe below is DESIGNED, NOT YET RUN.**
> Register entry: `30_register/ideas.yaml#carry-lifted-lattice`. Lens: lattice.
> Depends on: `2adic-carry-valuation-newton` (this is its natural *solver*).
> Spine: *lift every modular add to an integer identity, make the carries the unknowns, and ask one deterministic question — does a lattice coset hold a 0/1-carry vector?*

## The structure

Every SHA-256 modular addition `a + b = c (mod 2^32)` is the truncation of an exact integer
identity `a + b = c + 2^32 · γ`, where `γ` is a **small nonnegative carry integer** (here `γ ∈ {0,1}`
for a two-input add; a `k`-input add chains into `γ ∈ {0,…,k-1}`). The round function and message
schedule are stacks of such adds, so **enforcing schedule compliance over the tail rounds is a system
of integer-linear equations** whose *fixed* part is the message/state differential and whose
**unknowns are the carry integers** `γ`. Collect them: `M · γ ≡ t (mod / over Z)` with `M` sparse and
every nonzero coefficient equal to the *same* constant `2^32`. The integer solution set is an
**affine sublattice (a coset) `v0 + L`** of `Z^d`, and a valid collision is exactly a lattice point of
that coset **inside the box** `γ ∈ {0,1}^d` (or `{0,…,k-1}^d`).

That is *precisely* CVP/enumeration territory. The box-constraint-on-a-coset is the canonical input
to **LLL/BKZ enumeration** (fpylll off the shelf): reduce a basis of `L`, then enumerate coset points
within the box. The two reframes that make this native rather than analogical:

- **The collision SET becomes a lattice coset.** Not a probability — a geometric object with a basis,
  a covering radius, and a shortest-vector gap.
- **"Schedule-compliance boundary" becomes "does the coset contain a 0/1-carry vector."** The
  sr=60→61 wall is no longer "does a 2^{-2N}-rare event happen" but "is the box `{0,1}^d` reachable
  inside `v0 + L`" — a deterministic, BKZ-attackable decision.

## The hand-off from the 2-adic angle

This is the **solver** for what `2adic-carry-valuation-newton` only *measures*. That dive's Bridge 2
asks whether `v_2(ΔH)` grows linearly with enforced rounds — i.e. whether the multiplicative
`2^{-2N}`-per-round penalty is secretly an **additive/geometric** invariant carried by the carry
chain. If it is, you do not attack it probabilistically: you attack it **here**, because an additive
valuation invariant is exactly a statement about how deep into `L` the carry coset sits. The 2-adic
angle hands over a *number*; the lattice turns that number into a **single fixed lattice's
covering-radius / shortest-vector-gap question** — one deterministic object, not a per-round dice roll.

## First-instinct dismissal

**Dimension, and the wrong coefficient regime.** One round of SHA-256 has on the order of `32 ×`
(several adds: `T1` alone chains `h, Σ1, Ch, K, W`; plus `d+T1`, `T1+T2`, `Σ0/Σ1/Maj/Ch` internal
adds) carry positions. The full 7-round tail lattice plausibly lands near **~1000-dimensional** with a
**brutal box constraint**, where BKZ enumeration is hopeless (enumeration cost is super-exponential in
the gap-to-dimension ratio). Worse, lattices are *easy* exactly when there are **few equations with
large, varied coefficients** (knapsack, Coppersmith, RSA-small-`d`). SHA gives the **opposite**:
**many** equations all sharing the **same small** coefficient `2^32`. Uniform-coefficient,
high-codimension lattices are the regime where LLL gives no useful reduction and the box is too loose
to enumerate. The naive reading is therefore correctly dismissed — at full tail dimension.

## Devil's-advocate bridges (the live ones)

**Bridge 1 — restrict to the SMALLEST open residue.** Do *not* lift seven rounds. The only open gap
is **sr=60→61**, which is *one* round and a *handful* of words. From the certificate the live region
is the depth-1 `h60/d60` cross-section (the cascades realign here, and the W1/W2 differential is
pinned at rounds 57–60). One round of carry-lifting is **tens** of carry variables, not a thousand —
small enough that the dimension objection may simply not bite.

**Bridge 2 — the carry box is *tight*.** `γ ∈ {0,1}` is the tightest possible integer box. In low
dimension a tight box makes **enumeration fast**: the number of coset points to check is bounded by
the box volume against the reduced fundamental domain, and `2^d` for small `d` is trivially
enumerable even before any reduction earns its keep.

**Bridge 3 — BKZ as a pure decision oracle.** We do not need a short vector for its own sake; we need a
yes/no: *does a 0/1-carry coset point exist for the sr=60→61 residue?* BKZ-with-enumeration answers
exactly that decision, and a **no** is a *certificate* (the box is provably empty in `v0 + L`), not a
timeout.

## The adversarial check this angle must pass

The repo already runs **`mitm_hard_residue`** (`../sha256_review/headline_hunt/registry/mechanisms.yaml`),
which targets the **24-bit `gh60` residue** with a *forward/backward table* meet-in-the-middle. This
angle must be **demonstrably different**, or it is redundant. The distinction is sharp: MITM keys on
the *value* of the hard residue and searches a hash-keyed table; **the carry-lifted lattice attacks
the *carry structure* of that same residue** — the integer-overflow degrees of freedom `γ` that *make*
those 24 bits hard — and replaces table-lookup with a covering-radius geometry. One enumerates state
values; the other enumerates carries. They can even compose (MITM fixes the residue value; the lattice
asks whether a carry assignment realizes it), but they are not the same object.

It must also clear the codebase's own lattice prior art. **`april28` item_07** (read the file:
`../sha256_review/april28_explore/items/item_07_lll.md` — note the register's `item_07_lattice.md`
pointer resolves to this `_lll.md` file) found LLL useful **only as a linear trail-COMPLETION step**:
its unknowns were the **message differences `dW`** (a ~16-dim `Z/2^32` lattice), and its own refined
verdict is *"LLL is a tool for the linear-completion step, not the trail-design step… replaces SAT for
the linear part."* The carry-lifting construction here is **categorically different and not in the
codebase**: the lattice unknowns are the **carries `γ`, not the messages**, and the question is a
box-decision on a coset, not a shortest-`dW` search. That inversion — *carries as the lattice
variables* — is the genuinely-new, non-obvious part.

Finally it must beat the dimension objection head-on, and the only honest way is to **probe the
1-round residue first** and *measure the dimension that is actually produced* before claiming anything
about scaling.

## Most plausible translation

The sr=60→61 one-round residue, carry-lifted to integers, with the `{0,1}` box handed to fpylll as a
**decision** problem. Bridge 1 sets the size (one round), Bridge 2 makes enumeration cheap, Bridge 3
fixes the deliverable (yes/no/empty-certificate). No SAT anywhere.

## Probe design (cheap; reuses `../sha256_review/lib/sha256.py` + the sr=60 certificate)

Inputs: `../sha256_review/headline_hunt/datasets/certificates/sr60_n32_m17149975.yaml` (W1/W2 at
rounds 57–60, MSB kernel `(0,9)` bit 31; the round-60→61 residue is the live region) and the round
primitives from `lib/sha256.py` (`add`, `Sigma0/1`, `Ch`, `Maj` — **no reimplementation**).

- **A (lift one round).** Write the integer-lifted carry equations for **the sr=60→61 round ONLY** —
  the depth-1 `h60/d60` region, a handful of words. Each `T1`/`T2`/`d+T1` add becomes
  `Σ inputs = output + 2^32·γ`; the differential (h60, d60, the pinned W) is the *fixed* part; the
  `γ` are the **~tens of** unknowns. Emit the basis of `L` and the coset offset `v0`.
- **B (reduce + decide).** Hand `(L, v0)` to **fpylll** (LLL, then BKZ-with-enumeration). Ask the
  decision: is there a coset point with all `γ ∈ {0,1}` (resp. `{0,…,k-1}`)? Record (i) the **lattice
  dimension actually produced** for one round, and (ii) whether enumeration finds a valid 0/1-carry
  coset point. No SAT, no solver — geometry only.

### Expected-outcome table

| Observation | Meaning | Action |
|---|---|---|
| BKZ finds a 0/1-carry coset point in **seconds** where SAT timed out | the residue is geometrically solvable; carry structure is the right handle | **PROMOTE / dig deep** — enormous signal |
| **1-round** lattice dimension already in the **hundreds** | uniform-`2^32` regime + dimension confirmed; won't scale | **ARCHIVE** the angle, cite the dimension/coefficient reason |
| BKZ runs, finds **no** point, **cheaply certifies** the box empty | a cheap UNSAT-certificate method for the residue | note for repo (UNSAT-cert tool), partial-keep |
| BKZ neither finds a point nor terminates (loose box, no reduction) | wrong regime, no decision | **ARCHIVE**, cite enumeration blow-up |
| Dimension small **and** point exists at sr=60→61 but not beyond | foothold at the boundary, scaling unknown | keep, scope next probe to 2 rounds |

## Honest verdict (pre-probe)

Most likely outcome: **fizzle on dimension / coefficient-regime** — even one round may already produce a
high-dimensional, uniform-`2^32` lattice with a box too loose for enumeration to bite, which is exactly
the unfavorable lattice regime. The **1-round residue is the only size cheap enough to falsify this
decisively**, which is why the probe refuses to lift the full tail. If it survives, the realistic prize
is **not a collision** but a **cheap UNSAT certificate** for the sr=60→61 residue (a provably-empty
carry box) or a **structural reason** the box is empty — a "why the wall" deliverable in geometric
language, handed over from the 2-adic angle's additive invariant. The genuinely-exciting-but-unlikely
branch is a fast 0/1-carry point where SAT timed out. Plausibility **3**.

**This angle is DESIGNED, NOT RUN.** No fpylll has been invoked, no lattice has been built, no
dimension has been measured; every claim above is a prediction awaiting the 1-round probe.

`[VERDICT: PROBE-DESIGNED — NOT YET RUN. Probe the sr=60→61 one-round carry lattice ONLY; promote on a fast 0/1-carry point or a cheap empty-box certificate, archive immediately if the single-round dimension is already in the hundreds (the uniform-2^32 regime). DESIGNED, NOT RUN.]`
