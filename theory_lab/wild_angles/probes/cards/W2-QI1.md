# W2-QI1 — Magic saturation → why 92% breaks and the wall sits at ~59   ·   VERDICT: KILLED

**Card claim:** XOR/rotate are Clifford-like (free); the carry is the non-Clifford "magic"; the wall is where cumulative magic rank saturates the free-bit budget. Probe: per round fit the best affine approximation, take the rank of the residual {round(x)⊕affine(x)} = non-affine directions μ(i); plot cumulative M(r); look for saturation near r≈59 — using the *contextual/incremental* magic vs the running affine span.

**Probe run:** N=4,5,6, throttled (`OMP=2 taskpolicy -b`). (A) ISOLATED per-round magic: for each nonlinear round component (carry of modular add, Ch, Maj) at width N, the # non-affine output coordinates and the GF(2) rank of the span of its second differences `D_uD_v f = f⊕f(·+u)⊕f(·+v)⊕f(·+u+v)` (a coord is affine iff all second diffs vanish). (B) CONTEXTUAL/cumulative magic: the REAL mini-SHA round iterated on the 8N-bit state; per round r, M(r) = GF(2) dim of the span of second differences of the cumulative map `x→state_after_round_r` over sampled direction-pairs and base points (the genuine, frame-relative non-affine rank). Increment μ(r)=M(r)−M(r−1). Computed incrementally (states advanced one round at a time, no O(r) re-runs). 24 rounds to expose any plateau before round 59.

**Result (numbers):**
- (A) Isolated magic is **constant in structure**: Ch, Maj each give N non-affine coords (rank N); add-carry gives N−1. (N=4: add=3, Ch=4, Maj=4; N=6: add=5, Ch=6, Maj=6.) Exactly the "naive per-round magic is constant" the card concedes.
- (B) **Cumulative magic rises +N for FOUR rounds then saturates the FULL state dimension 8N and the increment is exactly 0 forever after**:
  - N=4: M(r) = 8,16,24,**32**,32,32,… ; μ(r) = 8,8,8,8,**0,0,…** ; first reaches max (32 of 32) at **round 4**.
  - N=5: M = 10,20,30,**40**,40,… ; saturates at round 4 (40 of 40).
  - N=6: M = 12,24,36,**48**,48,… ; saturates at round 4 (48 of 48).
- Saturation round = **4 ≪ 59**, identical across N; after saturation the contextual increment is flat 0.

**Kill_criterion:** "Dead if even the contextual/cumulative magic increment is constant (then the wall is just free-bit exhaustion, the null hypothesis)." — **fired? YES.**

**Verdict reasoning:** KILLED. The card's whole content is that cumulative magic saturates the free-bit budget *near round 59* — and that is decisively false. The contextual magic rank saturates the entire 8N state by **round 4** (every round mixes a fresh full state-worth of non-affine directions until the state is exhausted) and then the increment is identically 0 for all remaining ~55 rounds. There is no growth toward the wall, no knee, and certainly no saturation *event at* round 59. The increment is effectively the null hypothesis the card itself names — "free-bit exhaustion" — happening immediately, not at the boundary. This directly corroborates lead finding #4 (no round-60 knee; control/rigidity saturates early and smoothly) and the sibling kills W1-PH2 / W2-CT2. Magic-accounting cannot locate "round 59."

**Cross-check / skeptic note:** A skeptic could say the cumulative-map non-affine rank is bounded by 8N so it *must* saturate early — exactly the point: a magic measure that maxes out by round 4 cannot explain a boundary 55 rounds later, so the "magic ≈ free-bit budget at r≈59" mechanism is structurally impossible at any reachable N. One might instead track a *carry-counting* magic (cumulative AND-gate count) that grows unboundedly with rounds — but that is monotone and featureless too (no knee), and it is a different object than the card's affine-residual rank. The isolated per-round magic (A) being flat is the card's own conceded null; the contextual (B) version, which the card stakes its survival on, does not rescue it. The real wall is the carry/T1+T2 nonlinearity intersecting the all-zero output target (finding #1/#4), not a magic-rank threshold crossing.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W2-QI1.py`
