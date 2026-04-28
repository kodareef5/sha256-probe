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

---

## Update 2026-04-28 — block2_wang is now heavily active; updated framing for yale

Original note (above) framed block2_wang as "blocked until block-1 produces residual with HW≤24-28." That framing is now superseded by F70-F106 empirical work:

### What's empirically established (F70-F106)

- **Single-block cascade-1 cannot reach HW=0** at our compute scale. 2,512+ cross-solver cells across 67 cands × HW range [44, 120], all UNSAT. Registered as a closed negative in `negatives.yaml` (`single_block_cascade1_sat_at_compute_scale`, F105).
- **Block-1 residual HW distribution is mode-centered at HW=90-99**, not HW≤24 (F101 corpus probe at --hw-threshold 120). Earlier corpora at HW≤80 captured only 1.8% of the natural cascade-eligible space.
- **Yale's online Pareto sampler reaches HW=33 EXACT-sym** at LM=679 on bit28 (F70/F80) — well below the natural mode but above HW=0. This is the strongest single-block residual yale has found through 100B+ samples.
- **Random block-2 W2 amplifies the residual** rather than cancelling it (F106 finding: HW=55 input → HW=127 median output, ~2.3× amplification). This empirically confirms that the absorption requires SPECIFIC W2 modifications, not statistical sampling.

### How Wang's framework maps to yale's block-2 design

Wang's three-step recipe applied to SHA-256 block-2:

1. **Disturbance vector** = pattern of modifications across W2[0..15]. Yale's eventual design specifies which message words get adjusted and how.
2. **Bitconditions** = constraints on internal state diffs at specific block-2 rounds. For absorption: at each round r ∈ [0, 63] of block-2, the state diff must satisfy specific equality / inequality patterns to drive toward zero at r=63.
3. **Message modification** = the actual algorithm for satisfying bitconditions while keeping the trail consistent. For block-2 specifically: given the FIXED block-1 residual diff entering block-2 as input chain-state diff, modify W2[0..15] to satisfy each round's bitconditions.

### F82 SPEC v1 supports all three Wang concepts

Per `headline_hunt/bets/block2_wang/trails/2BLOCK_CERTPIN_SPEC.md`:
- `block2.W2_constraints` accepts 4 constraint types:
  - `exact`: pin W2[r] = specific value (full message-word control)
  - `exact_diff`: pin dW2[r] = W2[r] XOR W2'[r] (Wang-style differential constraint)
  - `modular_relation`: equation between message words (e.g., schedule consistency)
  - `bit_condition`: per-bit constraint (Wang's bitcondition formalism, direct mapping)

The SPEC's `bit_condition` type IS Wang's bitcondition. Yale ships a list of these per round, F104 simulator validates forward consistency, F84 verifies SAT.

### Concrete yale workflow (Wang→F82 mapping)

1. **Pick a block-1 residual** to target. Yale's frontier provides candidates: HW=33 EXACT-sym (lowest), HW=39 LM=720 (low LM-cost), HW=45/LM=637 (NEW LM champion per F80), HW=78 pair_hw=8 (alignment).
2. **Design disturbance vector**: which W2 rounds get modifications. Wang's SHA-1 work used 9-active-bit disturbance vectors in W; SHA-2 with mode-centered HW=90-99 distribution may need denser modification.
3. **Derive bitconditions per round**: for the chosen disturbance vector, propagate forward through block-2 rounds and record the bit-equality / bit-inequality conditions that must hold. Mendel/Nad/Schläffer's SHA-2 trails are the closest prior art for this step.
4. **Encode as F82 trail bundle**: one `bit_condition` entry per (round, bit-position, predicate) tuple.
5. **Validate via F104 simulator**: forward-simulates 100 random W2 samples satisfying constraints; reports COLLISIONS / NEAR_RESIDUALS / FORWARD_BROKEN.
6. **Submit to SAT** (F84) once F104 says NEAR_RESIDUALS or COLLISIONS.

### What's the open structural question

Wang's MD5 / SHA-1 attacks rely on **single-message-block** disturbance vectors that produce near-collisions. The SHA-256 setting is harder for two reasons:
- 64 rounds vs 80 (smaller "modification budget" before downstream divergence)
- Full Sigma functions (Σ0, Σ1, σ0, σ1) mix 4-7 register positions per round, vs SHA-1's circular shift only

For block-2 absorption (vs. single-block collision), the difficulty SHIFTS:
- Block-1 residual is FIXED input (cascade-1 structure dictates the diff at chain-state)
- Block-2 must construct an "anti-trail" that cancels this fixed input through 64 rounds
- The disturbance-vector design must align with the SHA-256 sigma functions to allow cancellation, not amplification (per F106 finding)

This is the **specific structural design problem yale faces**. Wang's framework is the language; yale's structural insight is the algorithm.

### Required follow-up reading (priority for yale)

1. **Mendel/Nad/Schläffer** — SHA-2 differential trails and message modification (SHA-256-specific). The closest prior art. `classical_mendel_nad_schlaffer_sha256` in literature.yaml; notes file exists.
2. **De Cannière/Rechberger** — automated characteristic search (the trail-design TOOL, not just framework). Notes file exists.
3. **Lipmaa/Moriai** — modular addition differential probability. Underpins F36's universal-LM-compatibility finding. Already integrated into yale's online Pareto sampler scoring (LM cost).

### What this note doesn't (and can't) provide

A specific yale block-2 trail design. The Wang framework + F82 SPEC + F104 simulator + F84 SAT verifier are the **TOOLS**. Yale's structural insight on which disturbance vector + bitconditions actually work for SHA-256 absorption is the **ALGORITHM**. That's yale's domain.

literature.yaml `read_status` for `classical_wang_yu_yin_message_modification` remains `background_read` (no full ePrint access; framework + SHA-256 mapping captured for actionable use).
