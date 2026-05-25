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
