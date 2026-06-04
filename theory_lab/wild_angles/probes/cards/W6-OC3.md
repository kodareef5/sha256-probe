# W6-OC3 — The 132 hard-core bits = the costate's kernel   ·   VERDICT: KILLED

**Card claim:** A final bit with zero costate support is unsteerable to first order; conjecture 132 = ker of the pulled-back costate map (da,db,de,df at r63), zeroed only by 2nd-order carry; HW~74 = kernel-dim/2 + small.

**Probe run:** N=8 and N=10, throttled. Built S[out_bit, ctrl_bit] = ∂(final bit)/∂(free control bit in W[57..60]) by exact finite difference on the cascade. Computed BOTH (i) the deterministic-control CENSUS (output bits no free control flips in every seed, the W2-CT1 object) and (ii) the honest first-order costate/Jacobian KERNEL (corank of the control→output tangent map).

**Result (numbers):**
- **Honest KERNEL** dim = **4N exactly** (= 32 at N=8, 40 at N=10); image rank = 4N (32, 40). The kernel SCALES with N → at width 32 it is 128 = {a,b,e,f} (4 registers × 32), the *uncontrollable* set — not a frozen 132.
- **CENSUS** (deterministic-all-seeds) zero-control bits = 46 (N=8), 55 (N=10) — does NOT equal the clean 4N+4 (36, 44): {a,b,e,f} all zero (4N) plus dc=8 and g=6–7 extra carry-blocked bits. The crisp "{a,b,e,f}+4dc = 132" structure is a width-32 phenomenon; at small N the honest linear kernel is exactly 4N while the deterministic census overshoots.
- **Plateau check:** kernel-dim/2 = 2N = **64** at width 32, NOT 74. census/2 = 23 (N=8) tracks neither. The HW~74 plateau (≈132/2 + 8) is not predicted by kernel-dim/2.

**Kill_criterion:** "zero-rows don't match the measured hard core, or kernel-dim/2 mispredicts the plateau beyond noise" — **fired? YES** (both clauses).

**Verdict reasoning:** This is the "132 = corank" CATEGORY ERROR (prior finding #1, now 13×). The honest, basis-independent costate/Jacobian kernel is **4N** (= 128 at width 32 = the {a,b,e,f} registers), a WIDTH-SCALING quantity — not a stable 132. The extra +4 dc bits that make 128→132 appear only in the deterministic-control census, and even that census is noisier at small N (46/55, not 36/44). Critically, the kernel reproduces the {a,b,e,f} = 128 *uncontrollable* set, and finding #1 flags that the uncontrolled set {a,b,e,f} is NOT the collision-common set (in collisions a,b carry zero difference — opposite role), so even the structural identification is the census's, not a Pontryagin kernel's. And kernel-dim/2 = 64 ≠ 74, so the plateau sub-claim independently fails.

**Cross-check / skeptic note:** The skeptic note ("a bit could be costate-supported yet need carries") is exactly why I separated the first-order tangent kernel (clean 4N) from the all-seeds deterministic census (messier 46/55) — they disagree at small N, confirming the 132 is not a single clean kernel object but the deterministic census plus carry artifacts. The 4N image rank is unambiguous (GF(2) rank, basis-independent). To CONFIRM I would have needed a basis-independent kernel that equals the hard core AND kernel/2 = 74; neither holds.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W6-OC3.py`
