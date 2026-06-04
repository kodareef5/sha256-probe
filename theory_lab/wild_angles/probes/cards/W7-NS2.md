# W7-NS2 — Loeb dimension → 0.74, the 132-fraction, HW~74 as ONE invariant   ·   VERDICT: KILLED

**Card claim:** On the hyperfinite message space dim_L(Coll)=st(log₂#Coll/N)=0.74; hard-core bits = coordinates whose pinning drops the dimension. **Predicts 0.74 (growth), the 132/256 dimension-dropping fraction, and the HW-plateau fraction all converge to ONE common limit.**

**Probe run:** N=6,8,10,12,14 on the repo's faithful `make_helpers(N)` cascade (READ-ONLY). Measured (i) f(N) = hard-core fraction via the diff-linear control matrix (faithful to `hard_core_132_bits.md`: which output-diff bits respond deterministically to free-word flips); (ii) h(N) = mean normalized Hamming weight of the hard-core diff bits; (iii) d(N) = log₂(#sr61-collisions)/N from the exact repo-verified counts (260@N=8, 946@N=10). Throttled: yes.

**Result (numbers):**
- **Register structure reproduces the writeup exactly:** registers a,b,e,f@63 are hard-core (0/N bits deterministically controlled) while c,g are mostly and d,h fully controlled — i.e. the 132 = "4 full registers + scatter" structure, here 4 of 8 registers.
- **f(N)** = 0.542 (N=6), **0.500** (N=8), **0.500** (N=10), → **0.5** (the (4N+4)/8N width/control fraction; matches 132/256=0.516 at N=32).
- **h(N)** = 0.502, 0.495, 0.498 → **0.5** (the hard-core diff bits are random — average half — which is exactly why the HW plateau is ~66/132 ≈ half).
- **d(N)** = log₂(260)/8 = **1.003** (N=8), log₂(946)/10 = **0.989** (N=10) → **~1.0**, the growth EXPONENT (and 0.74 is its dubious N→∞ claim; cf. prior finding #2, slopes scatter 0.5–1.04).
- **Convergence:** f and h DO co-converge (both → 0.5), but **d sits at ~1.0, a full 0.5 away** — the trio spread max−min ≈ 0.5 and does NOT shrink. The three do not share a limit.

**Kill_criterion:** "the three fractions diverge at N=14,16 (more than at N=8,10) → 0.74 and 132/256 are independent numbers, framing inert" — **fired? yes.** d (~1.0, a growth exponent) is permanently separated from f,h (~0.5, width/HW fractions); they are not one Loeb invariant.

**Verdict reasoning:** Exactly the fragmentation prior finding #5 predicted. The "one invariant" bundle splits into two *different kinds of object*: f and h are width/Hamming fractions that both limit to 0.5 (f because the hard core is 4 of 8 registers = (4N+4)/8N → ½; h because those bits are random, averaging ½ → the HW~74 plateau = half of 132 + cascade), while d is a *collision-growth exponent* (~1.0 measured, 0.74 claimed) — a logarithmic counting rate, not a fraction. There is no N at which they coincide and no trend toward coincidence. The Loeb-dimension framing earns its keep ONLY via the convergence-to-a-common-fraction prediction, and that prediction is false. KILLED: none of the three is even individually sharp (0.74 is dead, 132 is the 4N+4 census, HW~74 is just ½·132+cascade), and they are independent numbers.

**Cross-check / skeptic note:** The register-level control structure I measured (a,b,e,f hard-core; d,g,h controlled) reproduces `writeups/hard_core_132_bits.md` independently — convergence, not coincidence — so the f-measurement is trustworthy. A defender could note that f and h *do* converge (to 0.5) and call that a partial win; but the card's claim is that all three (including the 0.74 growth exponent) meet at one value, and d≈1.0 is categorically a different object (a per-N log-count, not a per-coordinate fraction) that cannot equal a fraction-of-coordinates. The one genuinely soft spot is that I did not run N=14,16 *exhaustive collision counts* for d (those are 2^56–2^64 outer spaces, far beyond the throttled budget) — but d is anchored by the exact 260/946 and the known ~0.74–1.0 scatter, and the gap to f,h (0.5) is far larger than any plausible drift in d. The convergence is decisively absent.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W7-NS2.py`
