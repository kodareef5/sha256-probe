---
date: 2026-05-25
bet: mitm_residue
status: CLOSURE (24-bit / MITM-meet question)
author: macbook-claude
evidence_level: EVIDENCE (N=32 measurement + structural argument)
---

# The MITM-meet is degenerate; the 24-bit residue is definitively refuted

## Question

mitm_residue's headline hypothesis: the hard work concentrates in g60/h60 with
**~24 effective bits**, so a forward/backward MITM keyed on that residue completes in
~2^24. The forward probes (20260525_n32_residue_width_probe.md) refuted this at the
forward level (gh60 >= ~34 effective bits). This note settles the remaining "but the
24 bits might be a MITM-MEET property" escape, which the loop queued as the final test.

## Why there is no valid forward/backward meet here

1. **The cascade is sequential, not splittable.** The free words drive *consecutive*
   rounds: W57→r57, W58→r58, W59→r59, W60→r60. A meet-in-the-middle needs a shared
   intermediate state computed independently from a forward half and a backward half.
   Here there is no such shared state split into independent halves — it is one
   forward chain. Varying any free word is a forward operation.

2. **The bet's own "backward W60" is degenerate.** `q4_mitm_geometry/cascade_mitm_full.py`
   notes that for `de60=0`, cascade-2 gives **exactly one** `W1[60]` per forward
   round-59 state. So the "backward" enumeration is *determined*, not a free matching
   axis. (And treating W60 as genuinely free is just another forward search axis,
   already swept in residue_width_n32_joint.py — it does not create a meet.)

3. **The meet's matching residue would BE gh60.** Any forward/backward MITM keyed on
   the hard residue matches on gh60 = (g60,h60). I measured (gh60_entropy_n32.py)
   that gh60 has **>= ~34 effective bits** over a (w57,w58) sweep (distinct == samples
   to 2^22, no ceiling; birthday shortfall => space >= ~2^34). A 2^24 MITM requires the
   matching residue to be ~24 bits. gh60 is >= ~34 bits and high-entropy, so the meet
   cannot be 2^24.

## Counting (independent confirmation)

A full sr=63 collision in the free-word model requires the 6 active round-63 lanes
(a,b,c,e,f,g) = 0, i.e. ~192 bits of condition. The free-word freedom is W57..W60 =
128 bits, of which the cascade consumes ~3-4 words to hold da=0/de60=0. So the model
is deeply UNDER-constrained for a full collision — the residual floors at ~HW35
(block2_wang's deeply-searched frontier) and never reaches 0. There is no surplus
freedom to be exploited by a meet.

## Verdict — DEFINITIVE

The 24-bit hard-residue hypothesis is refuted in BOTH readings:
- forward: gh60 >= ~34 effective bits (no 24-bit concentration);
- meet: no valid independent forward/backward split exists (sequential cascade,
  degenerate backward), and the meet residue is gh60 itself (>= ~34 bits).

Therefore the mitm_residue "~2^24 MITM keyed on g60/h60" is not achievable as stated.
This is consistent with the earlier decision memo (20260525_DECISION_forward_angle_exhausted.md)
and the cross-validation with block2_wang's universal residual floor (~HW35). The
24-bit question is closed; no MITM-meet escape remains.
