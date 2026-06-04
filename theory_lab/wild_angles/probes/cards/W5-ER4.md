# W5-ER4 — Foster's theorem audit → round-60 resistance-budget depletion   ·   VERDICT: KILLED

**Card claim:** Foster pins Σ_edges w_e·R_eff(e) = n−1 (a conserved budget). Conjecture: early/mid rounds absorb almost all of it (good diffusion), the tail is starved, and that starvation is the cascade's slack; the boundary = where the cumulative Foster share crosses a threshold (a knee near r≈59).

**Probe run:** N=8,12, full 64 rounds, throttled. Built the genuine full-compression resistor network (node per (round, register, bit) over N active lanes; edge conductance = single-bit-flip avalanche of each inter-round transition, measured by real per-round recompute via lib primitives). L⁺ = `pinv`; R_eff per edge; **Foster identity used as a free correctness oracle**; per-round Foster share = Σ_{edges leaving round r} w_e·R_eff(e). Tested two conductance choices (avalanche-sensitivity and uniform) to probe the skeptic's "artifact of the conductance" worry.

**Result (numbers):**

Foster oracle **exact** at every config: Σ w_e·R_eff = 4159.000 = rank(L) at N=8 (rel err 6.6e-16), = 6239.000 at N=12 (rel err 1.5e-16) — validates the entire pipeline.

The per-round Foster share is **flat / uniform**, no tail depletion:

| config | per-8-round share (r0-7 … r56-63) | cum 0.5 at | cum 0.9 at | "knee" |
|---|---|---|---|---|
| N=8 avalanche  | 0.129, 0.123×6, 0.132 | round 32 | round 58 | r62 (boundary) |
| N=8 uniform    | 0.129, 0.123×6, 0.132 | round 32 | round 58 | r62 |
| N=12 avalanche | 0.129, 0.123×6, 0.133 | round 32 | round 58 | r62 |
| N=12 uniform   | 0.129, 0.123×6, 0.132 | round 32 | round 58 | r62 |

Per-**single**-round share (N=8) is 0.0154 ± 0.0002 across rounds 5–61. Rounds 57–60 are statistically indistinguishable from bulk (z-scores −1.45, −0.53, +0.75, +0.13). The only deviation is at r62 (0.0167) and r63 (0.0233) — the **terminal rounds** of the finite chain, where dangling leaf nodes have no downstream edges and thus higher R_eff. The cumulative budget is a straight ramp crossing 0.5 at exactly the midpoint (round 32).

**Kill_criterion:** "featureless curve (no knee within ±3 of 59) across N and all conductance choices, or tail not depleted." — **fired? YES (both clauses).** The curve is featureless (flat per-round share, ramp crosses 0.5 at round 32); the only "knee" (r62) is the chain-terminus boundary artifact, ≥3 away from 59 and present identically for every N and conductance; and the tail is NOT depleted (r57-61 share = bulk share).

**Verdict reasoning:** KILLED. The resistance budget is allocated essentially **uniformly per round** (≈1/64 each), with zero special depletion at the tail and no knee near 57–60. The card's "tail is starved, boundary where cumulative crosses a threshold" picture is not borne out — the budget concentrates nowhere; the cumulative is linear. The lone numerical knee at r62-63 is the generic finite-chain end effect (leaves carry extra R_eff), robust to N and conductance, which is exactly the "artifact, not physics" outcome the card's own skeptic flagged as the weakest-of-four risk. Fully consistent with prior finding #4: structural quantities saturate smoothly; the "round-60 boundary" is bookkeeping, not a resistance event.

**Cross-check / skeptic note:** The Foster oracle matching rank to machine precision (1e-16) rules out a computational error as the cause of the flat curve. Both an avalanche-weighted and a uniform conductance give identical profiles, so the flatness is structural (the round graph is a near-homogeneous chain), not a tuning choice. To "see a knee at 59" one would have to hand-pick a non-physical conductance — the artifact warning realized.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W5-ER4.py`
