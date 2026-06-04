# W7-CG2 — Game thermography → temperature cools to 0 at the wall   ·   VERDICT: KILLED

**Card claim:** Each round is a 'hot' move (many free-word options reducing da-distance) cooling as freedom is spent; the wall = where the best−mean residual-improvement incentive crosses 0. Predicts a MONOTONE cool-down with the zero-crossing AT the sr=61 analog.

**Probe run:** Faithful mini-SHA(N) cascade. At each free round 57→60, over ALL 2^N free-word options (cascade fixing W2), measured best vs mean drop in residual = "temperature" (residual = total Hamming weight of the 8 register diffs, 0 = collision). Greedy-played the best move forward. Also a finer de-only-residual check. N=8 and N=10. Throttled: yes.

**Result (numbers):**
- Temperature = best−mean ≡ **0.000 at every free round** (57, 58, 59, 60), at both N=8 and N=10. ALL 2^N options give the *identical* residual drop (best = mean; #strictly-improving = 256/256 at N=8, 1024/1024 at N=10).
- Finer check: at each free round the produced de-difference is a **single value** regardless of the free word (#distinct de over the free word = 1) — the cascade's W2 choice absorbs all variation.
- "Zero-crossing" lands at round **57** (the first free round), not at the boundary (61).

**Kill_criterion:** "temperature not monotone, or zero-crossing far from the boundary." — **fired? yes** (both clauses: temperature is constant-zero not a cool-down, and the crossing is at 57, far from 61).

**Verdict reasoning:** This is prior-finding #4 made exact. Rounds 57–60 are the FREE cascade: the cascade forces da=0 for every free word, so every option yields the same residual drop — there is **no incentive gradient and no "hotness"** to cool. The temperature is identically 0 across the whole free region, not a monotone decline that reaches 0 at the wall, and the only "crossing" is at round 57 where freedom begins. The genuine feature (the W[61] schedule condition) is a discontinuous point-mass wall, not the endpoint of a cooling curve. KILLED: the cooling/thermography picture has no referent here — the proxy is a degenerate flat zero, exactly the free-cascade triviality the card was warned to avoid.

**Cross-check / skeptic note:** Two independent residual definitions (full 8-register Hamming distance and de-only distance) both show flatness, so the verdict isn't an artifact of one proxy. A defender might say "the real CGT temperature comes from game *values*, not option counts" — but that is precisely the card's own skeptic note, and the value-flatness (single reachable de per round) removes the value gradient too. There is no round-60 knee; the wall is a schedule condition at 61, reached discontinuously, not cooled into.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W7-CG2.py`
