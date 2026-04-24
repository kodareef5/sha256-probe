# wang_message_modification — Wang-style techniques (background)

**Citation**: Wang/Yu/Yin (2005) — Collision attacks on MD5, SHA-1
**Read status**: background-summary captured (full original ePrint blocked); deeper read still required if `block2_wang` becomes active.

## TL;DR (5 lines)

Wang's 2005 attack on SHA-1 reduced collision finding from 2^80 to <2^69 operations by **(1)** constructing a careful differential path through the compression function, **(2)** introducing message modifications that steer the algorithm toward internal states satisfying that path, and **(3)** using disturbance vectors + the bitconditions framework to track which bit patterns must hold at which rounds.

The 2017 SHAttered attack by CWI/Google was the practical realization (~2^63 operations, two distinct PDFs colliding). Leurent/Peyrin 2019 added chosen-prefix at ~$100k cloud cost.

## Key concepts (relevance to block2_wang)

- **Differential path** — sequence of state-diff vectors at each round. For our block2_wang, the path is BACKWARDS from a target small-residual collision at round 64 to determine what input differential structure is required.
- **Message modification** — adjust specific bits of W[0..15] to satisfy bitconditions in early rounds without restarting the search. Operates layer-by-layer through rounds. For block2_wang, this is the primary tool — given a fixed IV difference (from block 1's residual), modify the second-block message to drive each round's state diff into the required form.
- **Disturbance vectors** — sparse representation of where the differential path is "active." A SHA-2 disturbance vector at most has ~9 ones across 16 schedule words for tractable attacks.
- **Bitconditions** — Boolean constraints on individual bits at specific rounds. E.g., "bit 17 of e at round 12 must equal bit 17 of e' at round 12." A trail with HW=N bitconditions has roughly 2^N target probability.

## What this means for `block2_wang`

The bet's setup is:
- Block 1 produces near-collision residual (currently HW≥62 at N=32 — too large)
- Block 2 must absorb it: find M2 such that the IV-difference compounds to zero at round 64

Wang's framework gives the trail-design language. Required:
1. **Disturbance vector design** — which rounds get message modifications.
2. **Bitcondition derivation** — for each round, which bits of state must hold to keep the trail viable.
3. **Modification strategy** — sequence of W[0..15] adjustments to satisfy bitconditions.

The HW=62 residual is too dense for direct Wang application; SHA-2 trails with HW around 28 (Mendel/Nad/Schläffer) are the historical sweet spot. Hence the bet's blocked status until block-1 produces a residual with HW≤24-28.

## Required follow-up reading (when block2_wang activates)

Per the bet's classical-references set, in priority order:
1. **Wang/Yu/Yin 2005** — original SHA-1 attack (this note's source)
2. **Mendel/Nad/Schläffer** — SHA-2-specific differential trails and message modification
3. **De Cannière/Rechberger** — automated characteristic search (the trail-design tool)

These exist in our `literature.yaml` with `read_status: should_read`. Updating Wang to "background-read" status — full read is for whoever picks up block2_wang.

## Caveats

- This summary is from Wikipedia's SHA-1 collision section, not the original ePrint (which returned 403 on direct fetch). Specific bitcondition formalism details may differ.
- The Wang 2005 attack targets full SHA-1, not SHA-256. SHA-2's larger word size and additional Sigma/sigma functions make the trail design substantially harder. Mendel's SHA-2 work is the more directly relevant prior art.

literature.yaml `read_status` for `classical_wang_yu_yin_message_modification` updated to `background_read`.
