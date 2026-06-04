# The sr=61 single-block rate is 2^−2N, not 2^−N (Theorem-5 correction)

**2026-05-30, macbook-claude.** Evidence level: **VERIFIED** (exhaustive small-N +
1B-sample independence test). Direction chosen by user: "Theorem-5 coincidence variety."

## Claim

For the cascade-DP construction, the probability that an sr=60 collision is also
sr=61 (one additional schedule equation, W[60], compliant for **both** messages) is
**2^−2N**, not the 2^−N stated in `writeups/sr60_sr61_boundary_proof.md` Theorem 5
(and its "sr=61 needs 2^N × sr=60 cost", line 144). The proof undercounts by a factor
2^N.

## The decomposition

A cascade-DP sr=60 collision has free W[57..60], with W2 = W1 + casoff (forced for
da=0). It is sr=61 iff W[60] equals its schedule value for **both** messages:
- g1 = W1[60] − sched1[60]   (message-1 value match)
- g2 = W2[60] − sched2[60]   (message-2 value match)
Because W2[60] = W1[60] + casoff and sched2 − sched1 is fixed per triple,
  **g2 = g1 + h**,  where  h = casoff − (sched2[60] − sched1[60])  ("compatibility gap").
So  sr=61  ⇔  (g1 = 0)  AND  (g2 = 0)  ⇔  (g1 = 0)  AND  (h = 0).

**Theorem 5 accounts only for h = 0** (the inter-message difference compatibility —
"cascade-required dW matches schedule dW"), which is genuinely 2^−N. It **misses the
independent per-message value match g1 = 0** (another 2^−N). Two independent N-bit
conditions ⇒ 2^−2N.

## Evidence (`gap_analysis.c`, exhaustive cascade-DP enumeration)

| N | sr60 colls | P(h=0) over all triples | P(g1=0) | indep. ratio P(g1=0&h=0)/[P(g1=0)P(h=0)] | sr=61 count |
|---|-----------:|-------------------------|---------|------------------------------------------|------------:|
| 8 | 260  | 0.003931 (2^−8=0.003906) | 0.003924 | **0.923** (16.2M de61=0 hits) | 0 |
| 10| 946  | 0.000973 (2^−10=0.000977)| 0.000979 | **1.005** (1.07B de61=0 hits) | 0 |

- **h is uniform**: P(h=0) = 2^−N to 3 sig figs (16M / 1B samples; max-bin/mean ≈ 1.01).
- **g1 is uniform**: P(g1=0) = 2^−N.
- **g1 ⊥ h**: independence ratio 0.92 (N=8) / 1.005 (N=10) — essentially 1.
- **sr=61 count = 0** at both N: expected under 2^−N is 1.02 / 0.92 (P(0) = 36% / 40%);
  expected under 2^−2N is 0.004 / 0.0009 (P(0) = 99.6% / 99.9%). The 0/0 strongly favors
  2^−2N. (The boundary proof's own N=8 "0/260, consistent with 2^−N" did not distinguish
  the two — both predict ≈0 observed; the independence test does.)

## Why this matters (it strengthens the wall)

Each additional held expansion equation must hold for **both** kernel-related messages,
and the two per-message conditions are independent — so each sr step costs 2^−2N, not
2^−N. At N=32:
- #sr60 ≈ 2^26 (carry-structure law) ⇒ #sr61 ≈ 2^26 · 2^−64 = **2^−38 per candidate**.
- Across the 67-candidate registry: ≈ 67 · 2^−38 ≈ **2^−32 expected sr=61 collisions total.**

So single-block sr=61 is not merely "hard" — it is **2^−2N-rare = effectively
unreachable by any feasible search**, which definitively explains the 1800 CPU-h / 0-SAT
result (the search would need ~2^64 effective tries per candidate, not the ~2^32 the
2^−N estimate implied).

## Honest scope / what this does NOT claim

- Not an UNSAT/impossibility proof: sr=61 collisions can still EXIST (expected ~2^−32 across
  the registry, i.e. essentially never, but not provably zero). It is a sharp **rarity**
  result, correcting 2^−N → 2^−2N.
- Specific to the cascade-DP construction (the one the boundary proof analyzes and the one
  sr=60 collisions come from). A fundamentally different single-block mechanism is not
  covered — but none is known.
- N=32 figures use the extrapolated #sr60 law; the 2^−2N *per-step* factor is the directly
  verified part (exact at N=8, 1B-sample at N=10).

## Recommended corrections

- `writeups/sr60_sr61_boundary_proof.md` Theorem 5: change "P = 2^−N" → "2^−N is the
  inter-message difference-compatibility (h=0); the full sr-step also requires the
  independent per-message value match (2^−N), so the rate is **2^−2N**." Update line 144
  ("2^N × sr=60 cost" → "2^{2N} ×").
- `CLAIMS.md`: the sr=61 barrier entry should read 2^−2N with this verification.

Tool: `headline_hunt/bets/coincidence_variety/gap_analysis.c` (reuses the validated
backward-construction enumeration; cross-checks the repo's 260/946 collision counts).

## Follow-up 1: the 2^−2N wall is UNIVERSAL (no exploitable candidate/kernel)

The only way sr=61 could revert to 2^−N is if some candidate/kernel made g1 and h
*correlated* (g1=0 ⇒ h=0), which would show as an independence ratio R ≫ 1 (toward
1/P(h=0) ≈ 2^N). `coincidence_scan.c` swept 4 kernel-bit positions × all cascade-eligible
M0 at N=8 (~16M de61=0 hits each):

| kernel bit | candidates | independence ratio R range | sr=61 found |
|---|---|---|---|
| 7 (MSB) | 0x67 | 0.92 | 0 |
| 1 | 0x72, 0x9a | 0.92–1.03 | 0 |
| 4 | 0x32, 0x80, 0x8d, 0xe4 | 0.92–1.14 | 0 |
| 0 | (none cascade-eligible in range) | — | — |

**Every R ∈ [0.92, 1.14]** — all consistent with independence (R=1) at the N=8 sample
noise (~6% on the ~250-event `both` bucket). None is anywhere near the R≈2^N signature of
a 2^−N reversion. The gold-standard tight measurement (MSB, N=10, 10⁹ samples) gives
R=1.005. **Conclusion: g1 ⊥ h is universal; the 2^−2N rate holds for every single-block
cascade candidate/kernel tested — there is no "lucky candidate" that makes sr=61 reachable.**
Evidence level: EVIDENCE (broad N=8 sweep + one N=10 gold-standard point; not exhaustive).

## Follow-up 2: the enforcement/coincidence boundary explains the whole sr ladder

Synthesis with the linear_lever_gaps finding. There are two ways to satisfy a boundary
schedule equation:
- **Enforcement** (gap placement, Viragh): a free word at t-2/t-7/… is *set* to satisfy
  the equation. Free for both messages independently (the solver sets W1[t-2] and W2[t-2]
  each). No coincidence cost. This is how sr=57→58→59 are reached (enforce W[63], W[62]).
- **Coincidence**: when no free lever remains, the equation must hold by luck — 2^−2N
  (per-message value g=0 × inter-message compatibility h=0, both independent 2^−N).

The wall is exactly where enforcement runs out (the W57/W60 trigger-counting of
`linear_lever_gaps`): up to sr=59 you can enforce; sr=60 is the last reachable level
(hard — 12h cert — because freedom is squeezed); sr≥61 must pay 2^−2N per step. The full
single-block collision sr=64, reached from sr=60, is **4 coincidence steps ≈ 2^−8N**
relative to sr=60 (≈ 2^−256 at N=32 — i.e. the cascade route to a true collision is
astronomically worse than generic), confirming the cascade structure is a dead end for
sr>60. (The 2^−8N multi-step figure assumes per-step independence, directly verified only
for the first step; the per-step 2^−2N is the solid part.)
