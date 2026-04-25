# Priority candidate 17-bit signature distribution — full coverage in 5M samples

The 17 hard bits at round 60 (3 in f, 10 in g, 4 in h) define a 17-bit signature. Built the empirical distribution over (W[57], W[58], W[59]) for the priority candidate `bit19_m51ca0b34_fill55555555`.

## Result

- **5,000,000 samples** processed (~3.5 min CPU at 23.5k samples/s)
- **131,072 distinct signatures = 100% coverage of 2^17**
- Min hits per signature: 12
- Median: 38
- Max: 71
- **Zero singletons** — every signature realized by at least 12 different W-triples

## What this means

The cascade construction compresses 96-bit input space `(W[57], W[58], W[59])` down to 17-bit output space at round 60 by a factor of **2^96 / 2^17 = 2^79**.

Each signature has ~38 average pre-images. The forward map from W-triples to round-60 signatures is many-to-one, surjective onto all 2^17.

## MITM applicability — careful

The bet's MITM hypothesis would say: forward to round 60 (key on signature), backward from r63 collision (key on the same signature), match. If both sides produce the same 17-bit space and the backward direction has 17-bit constraint, MITM completes in ~2^17 work each side.

What's empirically clear: **forward fully covers 2^17 signatures**. Whether backward (round-63 collision target → required signature) gives a clean 17-bit requirement is the open question. Cascade Theorems 3+4 (de61=de62=de63=0 and da=de at r≥61) suggest the backward constraint also collapses to round-60 e-register diff, which is exactly what the f60/g60/h60 hard-residue captures (since f60=de59, g60=de58, h60=de57 propagate forward to e at r≥61 via shift register).

So **the forward and backward target spaces are LIKELY the same 17-bit signature**. This needs the backward analyzer to confirm.

## What's shippable now

- Forward signature distribution: empirically uniform over 2^17, full coverage in 5M samples.
- Forward table can be built: 131k signatures × ~12 bytes/witness ≈ **1.5 MB** to store one witness per signature.
- Or 5 MB to store 4 witnesses per signature for redundancy.

## Open

Building the backward analyzer:
- Given the cascade requirement (de61=de62=de63=0, plus cascade on a-d through round 63), what's the required round-60 signature?
- If the backward direction is a deterministic function of the candidate (no free variables), then there's exactly ONE required signature. Forward table lookup gives ~38 W-triples that produce it. Each is checked for actual collision via the 17-bit-non-uniform-bits matching the determined values.

That's a much cleaner story than "matching a target signature" — the bet might be **2^17 × small factor**, essentially deterministic, IF backward has zero free variables.

This needs ~1 day of careful coding to verify.

## Files

- `priority_signature_distribution.json` — 5M-sample summary (131k sigs, top-10 counts, etc.)
- `priority_candidate_hard_bits.md` — the 17 bit positions

## Forward-table collision sweep (post-build)

Swept all 131,072 witnesses in the forward table through full round-63
computation:
- Time: 5.1s on macbook
- Cascade-sr=61 collisions found: **0**
- Near-collisions (HW<16): **0**
- Best HW achieved: **65** (sig=8787, W1[57]=0x6d8e6421)

Consistent with Theorem 5 (cascade-sr=61 SAT probability = 2^-32 per
candidate; expected 131k × 2^-32 ≈ 3×10^-5 collisions in this sweep).
Consistent with block2_wang's earlier random-sampling finding (min HW
62 in 200k samples).

Conclusion: this candidate (and likely all 35 in the registry) does
NOT have a cascade-sr=61 collision discoverable via forward sampling
at < 2^32 samples. The bet's path forward, if any, requires either:
(a) a true MITM with backward analyzer that genuinely halves the
search exponent, or (b) a fundamentally different attack mechanism
than cascade-DP.
