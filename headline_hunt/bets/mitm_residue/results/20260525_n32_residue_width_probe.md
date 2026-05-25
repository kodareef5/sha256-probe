# 2026-05-25: N=32 residue-width probe — single-word freedom ≠ the 24-bit residue

Runner: macbook (kodareef5). Tool: `prototypes/residue_width_n32.py` (reuses
`lib.sha256`: precompute_state / build_schedule_tail / run_tail_rounds).
Evidence level: **EVIDENCE** (full N=32, 20k W57 samples on the sr=60 cert base).

## Question

Does the bet's headline "~24 effective bits in g60/h60; 232/256 anchor bits almost
free" show up as a ~24-bit round-63 residual when we sweep the free words on the
cert base at full N=32?

## Method

On the verified sr=60 cert (`M0=0x17149975`, MSB kernel), sweep `W1[57]`
(W58,W59 = cert; `W2[57]=W1[57]+C_w57` zeros `da57`; per-state `W2[60]=W1[60]+C_w60`
zeros `de60`). Run rounds 57..63, OR the round-63 register diffs into an active-bit
mask over the sweep.

## Result (corrects the framing)

```
cascade-2 efgh63 breaks (efgh63 != 0) : 19999 / 20000
active-bit mask: da..dg63 = 0xffffffff (hw 32 each); dh63 = 0x00000000 (hw 0)
min round-63 total HW = 0 (the cert, trial 0); random W57 -> abcd63 HW ~40-51
```

- **Only `dh63` collides for all W57** (active mask `0x0`), via the diagonal cascade
  chain `de60=0 -> df61=0 -> dg62=0 -> dh63=0`. Verified structural fact at N=32.
- **Every other register avalanches** (~half bits) under W57-only freedom. The cert
  is a lone needle (full collision at trial 0).

## Interpretation

A single free word (W57) + the two cascade offsets buys exactly **one** collided
output register (`dh63`). It does **not** exhibit a 24-bit residue — sweeping W57
alone gives near-full-width (~224-bit) round-63 avalanche. So the "~24 effective
bits" claim is a property of the **joint** W57..W61 free-word MITM (using the other
free words + the backward W60 match to satisfy the 232 "almost free" anchor bits),
**not** of single-word freedom. This is exactly the multi-word round-63 match that
`q4_mitm_geometry/cascade_mitm_full.py` sets up but never completes.

Consistent with the reduced-N picture: there the tail used all of W57/W58/W59 free
plus the cascade; here fixing W58,W59 over-constrains the search.

## Honest takeaway

This probe does **not** measure the 24-bit residue (wrong, too-narrow setup); it
clarifies that the residue is a joint-freedom property and pins one concrete fact
(cascade chain => `dh63=0` for all W57). A real residue-width measurement needs the
full W57..W61 joint MITM with the backward-W60 round-63 match — i.e. completing
`cascade_mitm_full.py`. Logged so the next attempt doesn't repeat the narrow setup.

## Follow-up: JOINT free-word measurement (residue_width_n32_joint.py)

Joint forward sweep — free `W1[57..60]`, message-2 via the full cascade chain
(`da=0` at 57/58/59 via `w2_for_zero_a`, `de60=0` via cascade-2), `da59_breaks=0`
verified. Over 300k samples on the cert base:

```
round-63 active mask: dd63=0 and dh63=0 (collide for ALL samples); other 6 avalanche
abcd63 active=96, efgh63 active=96  -> ~192-bit forward residual (6 registers)
gh60 residue active bits: g60(=e58)=32, h60(=e57)=28  -> 60/64 active (only h60 low 4 fixed)
min round-63 total HW = 62 over 300k  (avalanche tail, not a near-collision floor)
```

**This challenges the bet's headline "~24 effective bits in g60/h60" claim.**
Direct N=32 forward measurement shows:
- The joint cascade buys exactly **2** collided output registers (`dd63`, `dh63`);
  the other 6 avalanche (~192-bit residual). One more than the single-word case.
- `gh60` itself spans **~60 active bits** over a free `(w57,w58)` sweep — NOT 24.
  Only `h60`'s low 4 bits are structurally fixed.

Implication (EVIDENCE level): the "232 almost-free / ~24-hard" decomposition is
**not a forward free-word property**. If the 24-bit residue is real it must be a
**MITM-meet** property — the forward∩backward intersection collapsing the effective
search — which requires the backward-W60/W61 round-63 match that
`cascade_mitm_full.py` sets up but never completes. Until that meet is built and
measured, the ~24-bit headline is unsupported by direct measurement (and these
forward numbers argue the concentration, if any, comes entirely from the meet).

## Decisive: gh60 distinct-value count (gh60_entropy_n32.py)

Distinct-value count is a rigorous LOWER bound on effective dimension (unlike the
active-bit count above). Sweeping random `(W1[57],W1[58])` (cascade da=0) and
counting distinct 64-bit gh60 differences:

```
samples      distinct_gh60   ratio
   65536        65536        1.0000
  262144       262144        1.0000
 1048576      1048545        1.0000
 2097152      2097026        0.9999
 4194304      4193831        0.9999   <- no ceiling; birthday shortfall => space >= ~2^34
```

distinct == samples up to 2^22 (ratio 0.9999). **gh60 has >= ~34 effective bits and
shows NO 24-bit ceiling** — it is essentially injective in `(w57,w58)`.

### Verdict on the headline hypothesis

The bet's literal claim — "the hard work concentrates in g60/h60 with ~24 effective
bits" — is **REFUTED at the forward free-word level** (EVIDENCE, N=32): forward gh60
is high-entropy (>= ~34 bits), not a 24-bit object. Across three probes (single-word,
joint, distinct-count) the forward free-word structure exhibits NO 24-bit residue.

**Careful caveat (do not over-claim a kill-trigger):** this measures FORWARD gh60
entropy. The bet's kill-criterion ("effective-residue width at N=32 substantially
larger than 24 bits") refers to the POST-MEET MITM residue. A meet-in-the-middle
reading — where the forward gh60 distribution intersects a backward-required gh60
distribution in a structured ~24-bit set — is NOT tested here and is the only
surviving route for the ~24-bit claim. So: the *forward/gh60-is-24-bits* reading is
dead; the *post-meet-residue-is-24-bits* reading is untested and now looks less
likely (the forward side provides no concentration to build on).

## Net for the bet

Three session probes consistently find NO 24-bit residue in forward free-word
freedom (gh60 active 60/64, distinct >= 2^22 / >= ~34 effective bits; forward
round-63 residual ~192 bits, only dd63/dh63 collide). The headline hypothesis as
stated is refuted; any surviving ~24-bit claim rests entirely on the unbuilt MITM
meet, whose payoff now looks less likely given the high forward entropy. Highest-
value next step IF pursued: the forward/backward match + post-meet residual. Given
the negative forward evidence and that the bet is priority-5/owned elsewhere, this
may instead inform a kill/de-prioritize discussion (flag for the owner).
