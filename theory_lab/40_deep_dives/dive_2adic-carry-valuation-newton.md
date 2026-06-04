# Deep dive — `2adic-carry-valuation-newton`

> **Status: `probe-designed` — the probe below is DESIGNED, NOT YET RUN.**
> Register entry: `30_register/ideas.yaml#2adic-carry-valuation-newton`. Lens: number-theory-padic.
> Spine: *put a metric on the carry obstruction and attack the metric, not the message space.*

## The structure

The 2-adic integers `Z_2` are the inverse limit `lim Z/2^n`: an element is a coherent tower of
residues. The 2-adic valuation `v_2(x)` is the largest power of 2 dividing `x`; the metric is
`|x|_2 = 2^{-v_2(x)}` — two integers are *2-adically close* when their difference is highly
divisible by 2. The single fact that makes this non-decorative for SHA: **addition with carry is
exactly addition in `Z_2`** (truncated to 32 limbs), so **the carry chain literally *is* the 2-adic
carry**, and it is the *only* obstruction to the round function being 2-adically affine. Two further
facts from the literature make the lens native rather than analogical:

- Each SHA word operation (ADD, XOR, ROTR/SHR) is a **continuous, 1-Lipschitz map on `Z_2`** — i.e.
  a **T-function**. Anashin's non-Archimedean ergodic theory states *explicit* measure-preservation
  and ergodicity criteria for exactly this class (van der Put series). [anashin2006nonarch]
- Klapper–Goresky's **FCSR** is the arithmetic analog of an LFSR; their **2-adic span** is a
  complexity measure, and their synthesis algorithm (a 2-adic Berlekamp–Massey, via De Weger
  rational approximation) builds the *smallest FCSR* generating a given sequence. Their own caveat is
  the tell: when combining rational approximations "the size may grow due to the **carry** from
  addition." Carry is the crux on both sides. [klapperGoresky1997fcsr, klapperGoresky1995rational]

## First-instinct dismissal

SHA-256 is "2-adic" only trivially (it adds mod 2^32). XOR is **not** 2-adic addition, and σ0/σ1 use
**SHR**, which is not a 2-adic isometry near the top limbs, plus rotations that cross the 32-bit
boundary. So the clean `Z_2` structure is *broken every round*. This is precisely april28's
first-instinct dismissal (`item_03_padic.md`), and it is correct — for the *naive* reading.

## What april28 already settled (so we don't repeat it)

`../sha256_review/april28_explore/items/item_03_padic.md` probed **one** 2-adic reading — the
**Hensel-LIFT** question: *do small-N cascade solutions lift to large-N?* Verdict (probes 03/03b/03c):
**STRONG NEGATIVE / hard non-Hensel** — 0/1200 lift-compatible, and the lift residual is
2-adically **uniform-random** (mean XOR-distance 32.06 ≈ N1/2). That reading is **dead**; it is logged
as `repo-killed:cascade1-hard-non-hensel` and must not be re-proposed.

**But** item_03's Bridge C (Newton polygon over `Z_2`) and the **FCSR-span / `v_2(ΔH)`-growth**
readings were *reasoned about and never probed*. This dive scopes itself **strictly** to those
un-probed readings. The distinction is real: "do solutions lift?" (dead) is not "does the carry
obstruction carry a coherent 2-adic metric/slope?" (open).

## Devil's-advocate bridges (the live ones)

**Bridge 1 — 2-adic span of ΔW (FCSR synthesis).** Take the schedule-difference sequence
`ΔW[57..63]` of a *known* sr=60 collision pair and read it as a 2-adic integer; run FCSR/rational
synthesis to get its **2-adic span**. *Small/bounded span* ⇒ the difference propagation is governed
by a short rational recurrence — a genuine foothold (solve a short 2-adic linear system instead of a
`2^{-2N}`-per-round search). *Maximal span* ⇒ carries fully randomize and the lens is decorative.

**Bridge 2 — `v_2(ΔH)` growth as the *additive* form of `2^{-2N}`.** Compute the 2-adic valuation
(or distance) between the two compression outputs at the boundary round as a function of the number
of enforced schedule rounds. If `v_2(ΔH)` grows **linearly** with enforced rounds, *that is the
`2^{-2N}` floor re-expressed as an additive invariant* — and additive invariants are attackable by
**lattice lifting** (this is the explicit hand-off to `carry-lifted-lattice`) in a way a
multiplicative probability is not.

**Bridge 3 — Newton-polygon slope (item_03's un-probed Bridge C).** Build the per-round round
polynomial over `Z_2`. ADD contributes **slope-1** faces in the carry direction; XOR/ROTR contribute
**slope-0**. A **monotone** slope trend through the schedule would force *no solution at high 2-adic
precision* (= the N=32 case): a structural impossibility mechanism, not just an observation.

## The adversarial check this angle must pass

`../sha256_review/THE_THERMODYNAMIC_FLOOR.md` reports that **even a fully XOR-linearized sr=60 instance
times out at N=32** — so the barrier is "0-slack constraint geometry," **not carry-chain length**.
This is a *direct threat* to any carry-based angle. Resolution: the 2-adic claim is **not** about
carry-chain length; it is about the **2-adic span of the schedule recurrence** and the **valuation
invariant** — distinct quantities. In fact the XOR-only timeout *sharpens* the probe: if even the
linear model is hard, is the 2-adic span of the **linearized** schedule also large? (That is a clean
cross-check against `expansion-code-min-distance`, which measures the *linear* sparsity budget.) An
honest probe therefore runs Bridge 1 on **both** the true and the linearized schedule.

## Most plausible translation

Bridge 2 (`v_2(ΔH)` growth) is the cheapest and most concrete, and it directly feeds the lattice
angle. Bridge 1 (span) is the most diagnostic. Run both; treat Bridge 3 as the stretch.

## Probe design (cheap, ~1 day; reuses `../sha256_review/lib/sha256.py` + the sr=60 certificate)

Inputs: `../sha256_review/headline_hunt/datasets/certificates/sr60_n32_m17149975.yaml` (the known
N=32 pair, for ΔW); parametric mini-SHA at `N ∈ {8,10,12,16}` (for valuation-vs-round trends). All
primitives imported from `lib/` — **no reimplementation**, no SAT.

- **A (span).** Extract `ΔW[57..63]` from the certificate; run a 2-adic rational-approximation /
  FCSR synthesis (implement the short De Weger recurrence if no library); record the 2-adic span.
  Repeat on the **XOR-linearized** schedule for the cross-check.
- **B (valuation).** For each N, sample a few hundred cascade differences `dm`; at each round `r`
  compute `v_2` of the *modular* register difference; test for a monotone trend vs `r` / enforced
  rounds (linear fit + slope CI).
- **C (slope).** Construct the per-round carry polynomial; compute Newton-polygon slopes over `Z_2`;
  test slope monotonicity through the schedule.

### Expected-outcome table

| Observation | Meaning | Action |
|---|---|---|
| Span small / bounded (true schedule) | short rational recurrence governs ΔW | **PROMOTE** — real foothold |
| Span bounded only for linearized, maximal for true | carries are exactly what kills it | strong "why the wall" note; consider lattice |
| Span ~maximal both | carries randomize 2-adically | toward **archive** |
| `v_2(ΔH)` grows linearly w/ enforced rounds | `2^{-2N}` re-expressed as an additive invariant | **PROMOTE** → feed `carry-lifted-lattice` |
| `v_2` flat / random | no precision structure | toward **archive** (cite probe_03c as deeper cause) |
| Newton slope monotone | high-precision obstruction = impossibility mechanism | **PROMOTE** as a bound |
| Newton slopes mixed / flat | no coherent precision trend | archive the slope reading only |

## Honest verdict (pre-probe)

Most likely outcome: the lens **re-derives the `2^{-2N}` floor as a clean 2-adic invariant** rather
than beating it. For a theory lab whose mandate is *reframing*, that "why the wall" deliverable is the
realistic prize, and it is cheap to obtain. The likely fizzle is the skeptic's: SHR + boundary-crossing
rotations break clean `Z_2` structure every round, and a well-designed hash has **large 2-adic span by
construction** — so Bridge 1 probably returns maximal span and Bridge 3 probably returns mixed slopes.
The one genuinely exciting branch is a **linear `v_2(ΔH)` trend**, because it converts a probability
into geometry and hands the result straight to `carry-lifted-lattice`.

`[VERDICT: PROBE-DESIGNED — NOT YET RUN. Promote only on a bounded span, a linear v_2 trend, or a monotone Newton slope; otherwise archive citing april28 probe_03c as the deeper cause.]`
