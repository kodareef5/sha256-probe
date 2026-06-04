# W5-HY5 — Boundary-at-infinity → 132 as the Gromov boundary, HW~74 as its visual sphere   ·   VERDICT: KILLED

**Card claim:** The 132 hard-core bits = geodesic rays escaping to ∂X (non-relaxable directions); HW~74 = the visual-sphere radius; the sharp 132/124 split + a **scale-invariant ratio** = a boundary-dimension constant.

**Probe run:** N=4,6,8 (throttled), with a sampling-robustness check at 60/150/400 samples. Ran the deterministic-control census at each width (the W2-CT1 method, parameterized by N): for every output bit at round 63, is there a free input bit (in W[57..60]) that flips it in *every* random base point (BOUNDED) or none (ESCAPING = boundary)? Measured boundary-bits/total and the {a,b,e,f}-only fraction, and compared against the repo's N=32 anchor (132 = 4N+4).

**Result (numbers):**
| N | OUT=8N | escaping | esc/OUT | {a,b,e,f}/8N | d/g/h leak |
|---|---|---|---|---|---|
| 4 | 32 | 23 | 0.7188 | **0.5000** | 3 |
| 6 | 48 | 34 | 0.7083 | **0.5000** | 5 |
| 8 | 64 | 46 | 0.7188 | **0.5000** | 6 |

Counts are stable across 60/150/400 samples (not a sampling artifact). {a,b,e,f} = exactly 4N (fully escaping) at every N → its fraction is **0.5000 exactly**. The total ~0.72 is inflated by a d/g/h leak (3,5,6 bits) + small-N dc. **Repo N=32 anchor: escaping = 132 = 4·32+4 (a,b,e,f=128 + 4 dc, ZERO d/g/h leak) ⇒ fraction 132/256 = 0.5156**, heading to 0.5.

**Kill_criterion:** "no sharp dichotomy (smooth gradient), OR ratios drift with N" — **fired? YES** (the boundary fraction drifts toward 1/2; the small-N ~0.72 is a transient).

**Verdict reasoning:** This card **re-commits the finding-#1 "132 = corank category error."** The escaping set is exactly the deterministic-control census — {a,b,e,f}@output (4N) + scattered dc — i.e. **4N+4 = 132 at N=32**, a *width-scaling count*, not a basis-independent topological invariant. The dominant component {a,b,e,f}/8N is **0.5000 at every N**, so the asymptotic boundary fraction drifts to 1/2 (repo anchor: 0.5156 at N=32), the opposite of a scale-invariant Gromov-boundary dimension. The apparent small-N stability at ~0.72 is a transient produced by the d/g/h leak that the repo's clean N=32 census shows vanishes — and it lands squarely on the known **non-sharp 0.72–0.74** (finding #2: slope 0.673, spread 0.72–1.04), which is *also* not a real constant. So neither "132 = boundary dimension" nor "HW~74/256 = visual-sphere ratio" is scale-invariant; both track the width census.

**Cross-check / skeptic note:** I specifically guarded the surprising-looking 0.72 stability: it is robust to sample count (60→400 unchanged), so the *measurement* is sound — but the *interpretation* fails, because the only component that is a genuine large-N invariant ({a,b,e,f}=4N) gives 0.5 exactly, and the repo's directly-measured N=32 census (132 = 4N+4, no d/g/h leak) pins the asymptote at 0.5156→0.5. The "sharp 132/124 split" is real as a determinism dichotomy (controllers = 0 vs > 0) but that is the control census, not a visual sphere; relabeling 4N+4 as a boundary dimension is exactly the category error flagged 11× before. A real ∂X dimension would be a stable ratio independent of N; this drifts.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W5-HY5.py`
