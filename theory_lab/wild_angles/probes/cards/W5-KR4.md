# W5-KR4 — Wreath-length / first group factor: the hard part is one localized group gate   ·   VERDICT: KILLED

**Card claim:** KR coordinatizes the tail map into a flip-flop cascade with group factors at specific levels; the FIRST group factor appears at round 61, at the top level, with order m (~4 = two conditions x 2) — a constructive circuit whose one group gate is the precise hard part. gamma(r) should jump 0->1 at 61.

**Probe run:** N=2 (tiny, per the card's "moderate" cost flag; throttled). Computed a decidable lower bound on the KR group complexity gamma(r) of the ACCUMULATED tail transform T_r (round head-maps composed over rounds 55..r), using gamma(r) >= 1 <=> the transition monoid is non-aperiodic <=> it has an element of functional period > 1. Reported the accumulated max period m for r=55..63, and separately the single-round group factor m(r) for r=58..62.

**Result (numbers):**
- Accumulated T_r: **gamma(r) >= 1 (max period m = 12) for EVERY r from 55 to 63** — |M|=36864 constant. gamma is already >= 1 at r=55, with NO 0->1 jump at 61.
- Single-round group factor: m(r) = 12 identically at r = 58, 59, 60, 61, 62 (each single round monoid |M|=36864). Not ~4, not localized to 61, not a huge prime — a constant 12 every round.

**Kill_criterion:** "gamma>=1 at r<=59, OR gamma(61)=0, OR m a huge prime." — **fired? YES** (gamma>=1 at r=55<=59).

**Verdict reasoning:** The kill fires on the first clause: gamma(r) >= 1 at r=55 (and every round), six+ rounds before the predicted r=61 onset. There is no first-group-factor-at-61: the group factor is present from the start and is round-invariant (period exactly 12 every round, accumulated size frozen at 36864). The predicted "one localized group gate at the top level, order m~4" is contradicted — every round carries the same group factor (m=12), so the group complexity is distributed/round-invariant, not a single localized gate, and m does not equal ~4 nor relate to the 2^-2N "two conditions x 2". The hardness is NOT one localized group gate at round 61. This is prior finding #4 (no round-60 knee): the round operation is identical each round so no round can be the unique first group level.

**Cross-check / skeptic note:** N is kept tiny (2) as instructed; the head-carrier (pinned tail) gives a lower bound on group complexity (restriction can only quotient), so gamma(r)>=1 is sound — a genuine group element of period 12 is exhibited. m=12 (=lcm of a 3-cycle and 4-cycle on the 16 head states) is a real cyclic-group witness, the same one W5-KR1/KR5 found, confirming round-invariance across three independent probes. A larger-N probe (N=3,4) would refine the exact wreath length but cannot revive a 0->1-at-61 jump given gamma>=1 already holds at r=55.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W5-KR4.py`
