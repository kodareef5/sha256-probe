# W8-KC1 — Active-difference 2-core collapse -> the wall as a core dissolution, |2-core|=132   ·   VERDICT: KILLED

**Card claim:** Peel the sparse differential-support hypergraph (only forced-nonzero dW-bits) by min-degree; a rigid non-empty 2-core (= the hard core) survives through round 60 and COLLAPSES at 61 (the two new conditions strip the last support); k-core's discontinuous threshold = the sharp wall; |2-core(60)| ~ 132.

**Probe run:** Built the active-difference support graph at the honest 32-bit width, reusing F839's `schedule_dep_analysis.py` linear σ0/σ1/union propagation applied to the dW (difference) side. Seeded with the TRUE MSB-kernel injected difference (from the repo enumerator): M2[0]=M0^MSB and M2[9]=MASK^MSB each differ in exactly 1 bit (bit 31) → forced-nonzero seed = {dW[0][31], dW[9][31]}, the genuinely sparse seed. Propagated support, built the difference-bit dependency graph (edges = schedule recurrence couplings), peeled the 2-core (and 3-core) by min-degree as a function of the last-constrained round R. N=32 (literal width, as the 132 question requires). Throttled. Also cross-ran with a full-32-bit seed as a robustness check.

**Result (numbers):**
- The active difference **saturates to all 32 bits/word by the tail** (avalanche fills every bit within ~10 rounds of σ-mixing — exactly the catalog's "saturates by round 4" through-line).
- **|2-core(60)| = 1103** (≈ 34.5 × W) with the sparse 2-bit seed; = 1376 with the full-bit seed. WIDTH-SCALING (grows ~linearly with both W and R), NOT a stable ~132. ∉ [100,170].
- **60→61 drop in |2-core| = 0.97×** — the 2-core GROWS by +32 (one word) going 60→61; there is no collapse. Full active set drops 0.97× too (also grows). The "≥2× collapse" does not occur; the trend is monotone-increasing in R.
- 3-core ≡ 2-core at every R (1103/1135/...): the graph is so dense nothing peels even at k=3 — there is no rigid distinguished core to "dissolve".

**Kill_criterion:** "|2-core(60)| ∉ 100–170 at N=32, or the 60→61 drop < 1.3×" — **fired? YES (both: 1103∉[100,170] AND drop 0.97×<1.3×).**

**Verdict reasoning:** Both kill clauses fire, robustly across two seed choices. The active-difference support graph is dense (avalanche-saturated to 32 bits/word), so its 2-core is essentially the whole graph — a width-scaling object (~34W), exactly the "0/128/width-scaling, never a stable 132" pattern of prior finding #1. There is no discontinuous core dissolution at round 61: the constrained difference-bit set just accumulates +W per round (no round-60/61 knee, prior finding #5). The k-core peeling reveals no rigid 132-bit hard core on the difference side; the repo's 132 remains an OUTPUT control census (4N+4), not a graph core.

**Cross-check / skeptic note:** The card's own skeptic flag — "carry-reachability over-approximates support → the 2-core may be an approximation artifact" — cuts the WRONG way here: even the over-approximation (which would only make the core LARGER/denser) shows no collapse and no 132. A tighter (exact) support would be sparser but still avalanche-saturates by the tail, so the 2-core would remain width-scaling, not crystallize at 132. Robustness: full-bit seed (1376) and sparse 2-bit seed (1103) both width-scale and both show 0.97× "drop". No basis-independent 132 object emerges.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W8-KC1.py`
