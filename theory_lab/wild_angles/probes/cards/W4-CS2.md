# W4-CS2 — 2^-2N = an instrumental-variable identification order-deficit   ·   VERDICT: KILLED

**Card claim:** sr=61 needs two targets (g1=0, h=0) identified from the residual free words; if the admissible-instrument→target Jacobian has **rank 1** (one exclusion-valid lever), the second target is **under-identified** → 2^-N per missing dimension → 2^-2N.

**Probe run:** Reuse the repo-validated cascade (gap_analysis.c structure; rotations scaled exactly), mini-SHA via shabridge. Two measurements:
 1. **Discrete instrument→(g1,h) Jacobian** at N=8, 40 base-points: flip each bit of each free word w57,w58,w59,w60; record which bits of g1 and of h respond; GF(2) rank + which instruments are exclusion-valid for each target.
 2. **Joint hit-rate** of (g1=0 AND h=0) vs the marginal product: exhaustive triple sweep at NH=5 (h depends only on w57,w58,w59, so this is exact; the g1 marginal is exactly 2^-N by construction since g1 = w60 − const). Cross-checked against the repo N=10 collision CSV (g1,h,g2 columns).

**Result (numbers):**
 - **Identification rank = 2.** g1's exclusion-valid lever = **w60**; h's exclusion-valid levers = **{w57, w59}** (w58 happens to move both, but each target independently has its own lever). g1 and h are NOT confounded onto a single instrument.
 - **Joint factors as a product:** P(g1=0 AND h=0) = 9.327e-04, P(g1=0)·P(h=0) = 9.327e-04, **independence ratio = 1.0000** (priors: 1.005). log2 P(both) = **−10.07 ≈ −2N** at NH=5. Marginals P(g1=0)=2^-N exactly, P(h=0)=2.98e-2 ≈ 2^-N.
 - Rank-2 signature confirmed: **g2 = g1 + h holds for all 946** N=10 collisions.

**Kill_criterion:** "rank=2, or hit-rate exponent ≠ targets−rank." — **fired? YES (rank=2 clause).**

**Verdict reasoning:** KILLED. The card's mechanism is **inverted**. It posits an *order-deficit* — one identifying lever, the second target a free 2^-N ride — but the instrument→target map has **rank 2**: each of g1 and h has its OWN exclusion-valid instrument, so BOTH are *fully* identified. The 2^-2N is therefore **two fully-identified independent N-bit conditions** (2^-N each, independence ratio 1.000), exactly the established two-conditions structure (g1=0 AND g2=0, with g2=g1+h) — NOT an identification deficit. This does **not** land on the two-conditions structure as a derivation that would license a CONFIRM; instead it contradicts the card's specific causal claim. A framing where 2^-2N arises from *full* rank-2 identification is the opposite of the card's "deficit."

**Cross-check / skeptic note:** The discrete Jacobian rank is base-dependent in general, but here the *instrument-disjointness* (g1←w60, h←{w57,w59}) is structural and width-independent: g1 = w60 − sched1[60] is moved by w60; h is a per-triple quantity (w60-independent). The joint independence (ratio 1.000) is an exact full-space enumeration at NH=5, matching the repo's 1.005 at N=10 over ~1e9 hits. The one honest caveat: this is *the* established 2^-2N rank-2 fact (CONFIRMED 9× elsewhere) — CS2 correctly reproduces the number but attributes it to the wrong cause, so the rename/inversion is the result, not a new invariant.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W4-CS2.py`
