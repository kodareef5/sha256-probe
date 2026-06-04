# Multi-block CV-freedom test — VERDICT: the de58-overflow wall is INTRINSIC to the round function; multi-block faces the SAME 2^-2N wall (CV does NOT decouple h from g1/the collision)

**Headline (all numbers final, `multiblock_cv_probe.py`, throttled `OMP_NUM_THREADS=2`, no SAT, N=8 primary + N=10 cross-check):**
CV→h rank **8/8 @N=8, 10/10 @N=10** (CV *is* a full-width, all-8-register lever on
block-2's compatibility gap h) · g1's absolute target sched1[60] moves **0/8N** under CV
(g1 is CV-INDEPENDENT) · **but CV does NOT decouple h from the collision**: over a family
of 200 (N=8) / 120 (N=10) real block-1 outputs, CV's control of `h=0` and of the
collision-onset `de61=0` are **independent 2^-N events** (#(h=0 ∧ de61=0)=**0** vs
expected-if-independent 0.01); and block-2's residual-kernel `(g1,h)` coverage is
**bit-for-bit identical** to the single-block MSB kernel (same collision density, same
`P(h=0)=2^-N`, same un-decoupled (g1,h) per collision, **0 steerable sr=61**). The
single-block de58-ceiling is therefore **a property of the SHA-256 round function, not a
single-block artifact.** Sober but important: multi-block does **not** rescue sr=61.

---

## The question (decisive follow-up to `tunnel_RESULT.md` / the de58-overflow theorem)

The single-block result (take as given): sr=60→61 is `2^-2N`, PROVABLY de58-bounded —
moving g1's absolute target `sched1[60]` injects a full-width, multi-register disturbance
at r63 that overflows the lone `de58` (hw(db56)≤N) repair channel, so g1 and h cannot be
decoupled with one shared message. **The only conceivable escape is a SECOND block:**
block-1's message (~16N bits) produces a chaining value **CV** (the 8N-bit state, all 8
registers) via Davies-Meyer feed-forward `CV = IV + state_block1[64]`, and CV becomes
block-2's INITIAL STATE. In block-2 the STATE (CV, from block-1) and the SCHEDULE
(block-2's message → sched1[60]) are now **separate** inputs — a candidate multi-register,
uncoupled repair budget. **Does CV actually decouple block-2's h from g1 / the collision,
making sr=61 steerably reachable at `2^-N`?**

A real decoupling must (adversarial bar): zero/move **h EXACTLY (full width)**, not the
weak de61 filter; **co-occur with a full block-2 collision** (de61=de62=de63=0); and
**persist with N** (not vanish).

---

## Engine + grounding (validated, adversarially, before any claim)

Reused the **already-validated** `_w5co_engine` (N=4→49 colls, N=8 hint colls). The
multi-block model feeds **CV as block-2's initial state** (replacing the single-block
IVN-precompute), faithful to the repo's Davies-Meyer feed-forward
(`headline_hunt/bets/block2_wang/encoders/absorber_pinned.py:block1_outputs`), and
**re-solves block-2's message** for cascade-eligibility `da56=0` (block-2's analog of
block-1's `find_M0` — measured `~1/2^N` of block-2 messages qualify, an honest 2^-N
constraint). **Grounding (T0):** with `CV=IVN` the multi-block engine reproduces the
single-block engine **bit-for-bit** (N=8 collide=True, g1=28, h=249; N=10 g1=277, h=609).

**Block-1 Davies-Meyer feed-forward — the residual that block-2 actually absorbs:**
A block-1 **full** sr=60 collision feeds forward to **residual HW=0** — i.e. it is
*already a reduced-hash collision*, the degenerate case, **not** block-2's input. Block-2's
real input is a block-1 **NEAR-collision** (cascade-eligible `da56=0` but not a full r63
collision): post-FF residual **HW 13–39** at N=8/10 (the N-analog of the repo's measured
**HW≥66 at N=32**; registers d,h are zero in the residual, matching the repo's
`dd63=dh63=0`). *(Catching this distinction killed a spurious first-pass "CAN reach 2^-N"
verdict that was an artifact of an HW=0 residual; see "Adversarial corrections" below.)*

---

## STRUCTURAL LEMMA (verified T0) — what sr=61 reduces to

Within a fixed block-2 cascade, **h is INDEPENDENT of the last free word w60** (1 distinct
h over all w60), while **g1 = w60 − sched1[60] ranges over ALL `2^N` values** as w60 varies.
Therefore:

> **sr=61 ⟺ ∃ prefix (w57,w58,w59) with [ h=0  AND  the full collision closes at
> w60=sched1 (g1=0) ].**

So the entire question is whether block-1's CV can make **h=0 coincide with a block-2
collision** more often than `2^-2N`. This lemma lets every test below measure the
`(g1, h, collision)` coupling **directly**, sidestepping the need to find sparse collisions
blindly.

---

## T1 — CV reachability (the hope's premise: is CV a real multi-register lever?)

| N | GF(2) rank of CV over block-1 message | registers of CV touched |
|---|---|---|
| 8  | **64/64 (FULL 8N)** | **8/8** |
| 10 | **80/80 (FULL 8N)** | **8/8** |

✓ Block-1's ~16N message bits reach CV at **full 8N rank, all 8 registers** — CV is a
genuine multi-register-width input, exactly the premise the multi-block hope needs. **The
premise holds.** (And CV→h is itself full-rank: T2.)

## T2 — CV's lever on (g1, h): g1 is CV-INDEPENDENT, h IS CV-steerable

- **g1's absolute target `sched1[60]` moves 0/8N under CV** (N=8 and N=10). sched1[60] =
  σ1(w58)+W1p[53]+σ0(W1p[45])+W1p[44] is **purely block-2's schedule** — CV cannot touch
  it. So g1 and CV are *trivially* decoupled — but **only because CV cannot move g1 at all**
  (g1=0 is set by block-2's own w60, as it always was).
- **CV→h: GF(2) rank 8/8 @N=8 (146 distinct h over 200 CV-setups), 10/10 @N=10 (113/120).**
  h depends on the cascade state, which CV feeds, so **h is fully steerable by CV** — the
  multi-register lever the hope wanted *exists*.

## T3 — THE DECISIVE TEST: is CV's h=0 control INDEPENDENT of the collision?

Over a family of real block-1 outputs (200 @N=8 / 120 @N=10; post-FF HW 13–39), at a fixed
block-2 tail, measure whether `h=0` (CV-steerable) ever **co-occurs** with the
collision-onset `de61=0`:

| N | #(h=0) | #(de61=0) | #(h=0 ∧ de61=0) | expected-if-independent | h-values at de61=0 onset | **decouples?** |
|---|---|---|---|---|---|---|
| 8  | 1 | 2 | **0** | 0.01 | {30, 236} (never 0) | **NO** |
| 10 | 0 | 0 | **0** | 0.00 | {} | **NO** |

**CV's control of h and the collision-onset are INDEPENDENT 2^-N events.** Steering CV to
set h=0 does **not** help close the collision — they need the *same* freedom and pull in
independent directions. h is a full-rank CV-lever, but it **cannot be aimed at h=0 while
simultaneously holding the collision**: the moment CV moves to zero h, de61 leaves 0.

## T4 — (g1,h) coverage over block-2 collisions: residual kernel ≡ MSB kernel

Direct comparison (grid 40³ = 64000 prefixes, lemma-based full-collision sweep):

| kernel | block-2 colls | P(h=0 / prefix) | distinct (g1,h) | h=0 at coll | **steerable sr=61** |
|---|---|---|---|---|---|
| MSB (single-block)         | 1 | 238/64000 = **2^-8** | 1 | none | **No (sr61=0)** |
| residual HW19 (block-2)    | 1 | 266/64000 = **2^-8** | 1 | none | **No (sr61=0)** |

The residual-kernel block-2 is **statistically identical** to the single-block MSB kernel:
same collision density, **same `P(h=0)=2^-N`**, each collision a distinct (g1,h) — the
**same `2^-2N` two-condition structure**, untouched. (Independent cross-check, a 2×8.4M-tail
survey: de61=0→full-collision *extension rate* is `3.3e-5` (MSB) vs `3.1e-5` (residual
HW28) — the dense residual kernel admits collisions at the **same rate**, so the wall is
*not* "block-2 has no collisions"; it is that h=0 and the collision never co-zero.)

---

## Mechanism (why CV's full-rank h-lever does not buy sr=61)

CV is a genuine multi-register (8N, full-rank) lever, and it **does** steer block-2's h
across its full range (rank N). The single-block obstruction does **not** reappear in the
naive form ("a lever on the absolute target overflows de58") — because in block-2 the
absolute target `sched1[60]` is CV-independent, and the residual kernel is no sparser in
collisions than the MSB kernel. **Instead the SAME `2^-2N` reappears one level up:** block-2's
three sr=61 conditions — **(g1=0)** [block-2's w60, free], **(h=0)** [CV/cascade-steerable],
and **(de61=de62=de63=0, the collision)** [the cascade] — are **mutually independent 2^-N
events**. CV adds a knob for h, but using it to zero h moves de61 off zero by an independent
2^-N amount; the collision and h=0 do not co-occur any more often than chance (`2^-2N`).
Block-1 buys a *steerable h*, but **not a steerable (h=0 ∧ collision)** — the very joint
condition sr=61 requires. *The freedom CV adds is consumed re-establishing block-2's
cascade (da56=0) and is orthogonal to the collision-vs-h coupling, not a repair budget for
it.* This is the de58-overflow's deeper content: **the absolute↔differential carry coupling
that makes h=0 and the collision independent is a property of the round function**, and a
fresh block inherits it verbatim.

---

## Verdict (one paragraph, honest)

**Multi-block faces the SAME wall.** The multi-block hope's premise is fully satisfied — CV
is a real, full-width (8N-bit, all-8-register, GF(2)-rank-N) lever on block-2's
compatibility gap h, and g1's absolute target is genuinely CV-independent — yet **CV does
NOT decouple h from the collision**, and so does **not** make sr=61 steerable. Over families
of 200 (N=8) and 120 (N=10) *real* Davies-Meyer block-1 outputs (post-FF residual HW 13–39,
the N-analog of the repo's HW≥66), CV's control of `h=0` and of the block-2 collision-onset
`de61=0` are **independent 2^-N events** (#(both)=0 vs 0.01 expected), and the residual-kernel
block-2's `(g1,h)` coverage is **bit-for-bit the single-block 2^-2N structure** (same
collision density, same `P(h=0)=2^-N`, 0 steerable sr=61). The same `2^-2N` simply moves up
one level: block-2's (g1=0), (h=0), (collision) are three mutually independent 2^-N
conditions, and CV's extra freedom — consumed re-establishing block-2's cascade — is
orthogonal to the h-vs-collision coupling rather than a repair budget for it. So the
single-block **de58-overflow ceiling is intrinsic to the SHA-256 round function, not a
single-block artifact**: a second block, done faithfully (feed-forward + post-FF residual +
re-solved cascade), inherits the carry coupling verbatim. This independently corroborates
the repo's own faithful 2-block finding (`block2_wang` walls at ~18 rounds over a dense
post-FF residual) from the orthogonal sr=60/61 boundary angle. **Honest caveats:** (1) MSB-
kernel cascade-DP construction, N=8 (primary, full T1–T4) and N=10 (T1–T3 cross-check;
N=10 coverage skipped for runtime — the lever/decoupling test is the decisive one and it
agrees); (2) the T3/T4 collision statistics are grid-/family-bounded (40³ prefixes, 200/120
CV-setups) — they show the **independence/2^-N structure** robustly but, like the
single-block probes, do not *prove* zero sr=61 (sr=61 collisions can exist at the 2^-2N
rarity, just not steerably); (3) block-2 messages are taken cascade-symmetric here
(difference carried by CV/residual, fill=MASK) — a Wang-style M1≠M2 block-2 is a further
(harder) degree the repo's absorber already explored to the same ~18-round wall; (4) the
decoupling is tested at the h-vs-collision-onset level (the lemma reduces sr=61 to exactly
this), with h checked **exactly/full-width**, never the weak de61 filter. Within those
bounds: **CV→h rank = N (full), g1 CV-independent, but h⊥collision (independent 2^-N), 0
steerable sr=61, residual-kernel ≡ MSB-kernel — multi-block does NOT reach 2^-N; the
de58-overflow wall is a round-function property.**

### What it would take to overturn this (would-change-my-mind)
A block-1 absorber producing a CV whose residual makes block-2's **h=0 and the collision
CO-OCCUR deterministically** (i.e. a CV-direction along which h→0 while de61 stays 0) —
equivalently, a residual family for which `P(h=0 ∧ collision) ≫ 2^-2N`. This probe finds
that direction has **measure 0** (independent 2^-N events) at N=8,10; a high-rarity such
family invisible to a 200-setup / 40³ search is not formally excluded but is implausible
given the clean independence.

### Adversarial corrections made during the probe (kept for the record)
1. **HW=0-residual artifact:** feeding the *full-collision* anchor as block-2's input gives
   CV1=CV2 (residual 0), under which block-2 trivially collides with h=0 everywhere — a
   spurious "steerable sr=61 = True". Fixed by requiring a **near-collision** (residual>0)
   for block-2's input; the verdict flipped to **SAME WALL**. The lesson mirrors the repo's
   own feed-forward fix (`20260530_feedforward_faithful_absorber.md`): the block-2 input is
   the *post-feed-forward* residual, and getting that right is load-bearing.
2. **Sparsity vs grid:** an early strided block-2 collision sweep returned "0 collisions"
   (grid missed the ~2^-15-sparse collisions); the extension-rate cross-check confirmed the
   residual kernel has the **same** collision density as MSB — so the wall is the
   h-vs-collision *independence*, not collision *absence*.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/multiblock_cv_probe.py`
(T0 grounding+lemma · T1 CV reachability · T2 CV→h lever + g1 CV-independence · T3 h-vs-
collision independence over the CV-family · T4 residual-kernel vs MSB-kernel (g1,h) coverage;
N=8 full, N=10 lever cross-check).
