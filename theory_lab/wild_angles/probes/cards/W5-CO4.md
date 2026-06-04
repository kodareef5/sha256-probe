# W5-CO4 — Final coalgebra: collision count as fiber sizes; power-of-2 quantization   ·   VERDICT: KILLED

**Card claim:** The behavior map to the final coalgebra has fibers = collisions; image size = 2^(domain − 0.74N). Sharp test: are fiber sizes *quantized to powers of 2* — a bisimulation-class regularity a random oracle lacks?

**Probe run:** Built the faithful N-bit cascade-tail model (validated: N=4→49, N=8→260 full collisions, matching the repo C enumerator `backward_construct_n10.c`). Computed (a) the fiber-size histogram of the natural behavior map B: (w57,w58,w59,w60)→final 8-register output; (b) the cross-path collision count and its per-(w57,w58,w59)-triple solution-count histogram; (c) the growth slope across N. N=4 exhaustive in Python (throttled); N=8 collision set from the repo C enumerator (throttled).

**Result (numbers):**
- Behavior map B is **injective**: at N=4, image = domain = 2^16, **every fiber has size 1**. Mean fiber = 1.000 = 2^0, empirical slope log2(domain/image)/N = **0.000**, not 0.74. There is *no* nontrivial fiber structure to quantize — the path-1 hash is a bijection on the 4N free bits.
- The actual collisions are the **cross-path** object (M vs its da=0 cascade partner). Per-(w57,w58,w59)-triple solution-count histogram:
  - **N=4: sizes {1:14, 2:13, 3:3} — contains 3, NOT a power of 2.**
  - N=8: sizes {1:242, 2:9} — powers of 2, but this is *not robust across N* (broke at N=4).
- Total collision counts **49 (N=4)** and **260 (N=8)** are themselves **not powers of 2** (49 = 7²).
- Growth slope log2(260/49)/(8−4) = **0.602**, not 0.74 (consistent with prior finding #2: 0.74 not sharp).
- Random-oracle Poisson null (codomain 2^{8N}): expected self-collision pairs 0.5, observed 0 — the injective B is *less* collisional than the oracle, not more.

**Kill_criterion:** "indistinguishable from the random-oracle Poisson." — **fired? yes** (in the sharper sense: the predicted regularity is absent). The natural behavior-map fibers are all singletons (no quantization object at all), and the only collision fibers that exist (cross-path) are **not** power-of-2 quantized at N=4 and do **not** reproduce 0.74. The coalgebra DERIVES no count.

**Verdict reasoning:** KILLED. Per prior finding #5, CO4 may only CONFIRM if the final coalgebra *derives a specific count* (0.74 slope or |de58|), not merely restates "fibers are powers of 2." It does neither: (i) the honest behavior map is injective, so "fibers = collisions" only holds under the trivial M↔M' cascade pairing the skeptic note flagged ("true of any function"); (ii) the cross-path fiber sizes include 3 at N=4, so they are not even power-of-2 quantized; (iii) the measured growth exponent is 0.60, not 0.74. The genuine powers of 2 in this system (|de58| = 2^hw(db56) = 8 here) come from a GF(2)/modular image count that the coalgebra framing does not reconstruct.

**Cross-check / skeptic note:** Could a different "behavior" (e.g. truncated output, or the de57..de60 difference vector) give power-of-2 fibers? The de-vector route is exactly |de58| = 2^hw — real but already known and *not produced by the coalgebra*. The N=8 per-triple counts being all-powers-of-2 is a coincidence of that width (it fails at N=4), which is precisely the "power-of-2 is real but shallow" warning. Independent corroboration: the repo's own enumerator gives the same 49/260 and the same triple structure.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W5-CO4.py`
