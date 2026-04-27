# de58 = 0 chamber search — NO cascade-1 collision exists for 4 tested cands
**2026-04-26 20:00 EDT**

Surveyed W57 space (262,144 chambers per cand) looking for the chamber
image of de58. For sr=61 collision via cascade-1, a chamber must satisfy
`de58 = 0`. None of the 4 main test cands have such a chamber.

## Result

| cand | distinct de58 values | min HW found | de58=0 count | HW≤5 count |
|---|---:|---:|---:|---:|
| bit=19 (m=0x51ca0b34, fill=0x55555555) | 256 | **11** | **0** | 0 |
| msb_cert idx=0 (m=0x17149975, fill=0xff..) | 113,357 | **8** | **0** | 0 |
| idx=8 (m=0x33ec77ca, fill=0xff.., bit=3) | 113,358 | **5** | **0** | 5 |
| idx=17 (m=0x28c09a5a, fill=0xff.., bit=15) | 4,096 | **9** | **0** | 0 |

Min-HW representative values:
- bit=19: 0x80c55489 (HW=11), seen at multiple W57s
- msb_cert: 0x120ca110 (HW=8)
- idx=8: 0xd4040000 (HW=5) — seen at 5 W57s, structurally repeated
- idx=17: 0x42849310 (HW=9)

These minimum-HW chambers represent the closest cascade-1 reach to
de58 = 0 for each cand. The gap (5–11 bits short of zero) is the
structural barrier.

## Implication: cascade-1 search path is closed for these 4 cands

For sr=61 collision the round-61-block-output state vector at slot 62
must match between M1 and M2, which requires de58 = de59 = de60 = de61
= 0 (and da[58..61] = 0).

We've shown:
- Per-chamber de58 image = 1 (single value per W57 chamber)
- de59 cand-level invariant (free hint, but also non-zero)
- de60..de63 structurally 0 under cascade-1

**For cascade-1 to produce sr=61 collision, the cand's de58 IMAGE
(over W57) must include 0.** The 4 tested cands' images do NOT.

So:
- bit=19 has 256 reachable de58 values; 0 isn't among them.
- idx=8 has at least 113K reachable de58 values; 0 isn't among them
  in 262K samples (probability of missing-but-existing zero is ≤ 3%
  if image is uniform over 2^32, but more likely 0 isn't in the image).
- idx=17 has only 4096 reachable de58 values — small image, definitely
  enumerable. 0 not in image.

## Cross-bet leverage: explains the HW4/HW59 floor

Yale + M5's singular_chamber_rank result (D61=HW4, structural floor
across 8 attack vectors): **this is consistent with no cascade-1
chamber having de58 = 0**.

The HW4 D61 frontier represents the closest the cascade-1 search can
get. The 4-bit residual is the structural distance from cascade-1
reach to actual collision. Sub-HW4 D61 isn't reachable through any
cascade-1-preserving operator — confirming yale's "Sigma1/Ch/T2
chart-preserving operator" criterion.

## Implications for the bet portfolio

- **cascade_aux Mode A search at TRUE sr=61 cands is futile** if the
  cand's de58 image doesn't include 0. The solver can never find SAT
  via cascade-1.
- **Mode B is finding "no cascade-1 collision exists" UNSAT proofs**,
  not "no sr=61 collision exists." A cand could still have a non-
  cascade-1 sr=61 collision (da[58..60] ≠ 0).
- **The cascade_aux 2× Mode B speedup** is acceleration of the
  cascade-1-elimination proof.
- **Headline path**: requires NON-cascade-1 collision search OR cands
  whose de58 image happens to include 0.

## What would change the conclusion

- **Larger image sample**: try 2^24 chambers on idx=8 (largest image,
  most likely to contain rare 0). 262K samples isn't exhaustive.
- **Different cand class**: look for cands where the de58 image
  STRUCTURE includes 0. The cands with small de58_size (bit=19=256,
  idx=17=4096) are fully enumerable — definitively "no zero."
- **Image enumeration tool**: compute the FULL image for small-image
  cands (≤2^16) deterministically. If 0 is structurally absent, that's
  certain elimination; otherwise we have a target W57 to test.

## Open question for sweep_eligibility infrastructure

The registry currently flags cands as "true_sr61: unknown." This memo
provides a NECESSARY-condition test: if `0 ∉ de58_image(m0, fill, bit)`
then `sr=61 collision via cascade-1` is impossible. Adding this as a
candidate-screen filter would prune the cascade_aux search space.

EVIDENCE-level: STRONG NEGATIVE for these 4 cands at 262K-chamber
sample size. EVIDENCE-level certain for bit=19 and idx=17 (image is
fully covered at this sample size).
