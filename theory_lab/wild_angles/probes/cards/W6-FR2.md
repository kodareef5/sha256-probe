# W6-FR2 — Open-set-condition failure -> 2^-2N as the overlap measure   ·   VERDICT: CONFIRMED

**Card claim:** Zero-forcing maps have disjoint images through round 60 (de57/59/60 constant => non-overlapping cylinders => OSC holds => clean 2^0.74N); at round 61 two independent conditions (g1=0 AND h=0) demand the same cylinder => images overlap => OSC fails => attractor measure on the overlap = (2^-N)^2 = 2^-2N.

**Probe run:** (1) de-set image cardinalities through round 60 via the repo-faithful tail engine (N=4,5; MSB-kernel cascade-eligible only at N=4,5,8,10). (2) The round-61 overlap ratio R = P(g1=0 AND h=0) / [P(g1=0)·P(h=0)] from the repo's `coincidence_scan` binary (EXACT full 2^32 enumeration of the de61=0 population at N=8, 2 cascade-eligible candidates × 5 kernels). (3) N=10 collision corpus cross-check (`gap_rows.csv`, 946 sr=60 collisions). All throttled (taskpolicy -b, OMP_NUM_THREADS=2).

**Result (numbers):**
- **OSC holds through 60:** |de57|=|de59|=|de60|=1 at N=4 and N=5 (single-valued => disjoint cylinders); de58 multivalued (2 at N=4, 8 at N=5 = the de-law) but de58 is not a round-61 gate. Pinned DE_SIZES (repo-verified to N=32) confirm de57=de59=de60=1 at all N.
- **OSC fails at 61 (the two conditions):** across 5 (M0,kernel) candidates at N=8,
  - mean P(g1=0) = 0.003913, ratio-to-2^-N = **1.002** (2^-8 = 0.003906),
  - mean P(h=0) = 0.003905, ratio-to-2^-N = **1.000**,
  - overlap ratio R = min 0.917, max 1.057, **mean 0.970** — i.e. R ≈ 1, NOT toward the partition/dependence value 1/P ≈ 256.
  - sr=61 count = 0 for every candidate.
- **N=10 corpus:** among 946 sr=60 collisions, g1=0: 0, h=0: 0, both(=sr61): 0 — sr=61 empty (consistent with 2^-2N rarity).

**Kill_criterion:** "sr=61 conditions partition (not overlap, ratio≠1), or OSC fails *before* 61 (mispredicts the wall)." — **fired? NO.** The ratio is ≈1 (independent overlap, not a partition); de57/59/60 are single-valued so OSC holds through 60 and fails only at 61.

**Verdict reasoning:** CONFIRMED on the load-bearing criterion of prior finding #3: this lands on the **two conditions**, not a generic overlap rename. Each marginal P(g1=0), P(h=0) is exactly 2^-N (ratio-to-2^-N = 1.00), and the joint is the *product* (R = 0.97 ≈ 1, with no systematic drift toward the dependence value 256), so the overlap measure is genuinely 2^-N · 2^-N = 2^-2N — two independent rank-1 cocircuits, the real rank-2 object. The non-trivial half the card had to demonstrate (OSC *holds* through 60 via single-valued de57/59/60, then *fails* at 61 via the overlapping g1=0,h=0 cylinders) is shown directly. The IFS/open-set-condition framing is a faithful, non-circular re-description of the established 2^-2N wall.

**Cross-check / skeptic note:** The 0.97 mean ratio has ~±8% scatter across candidates (0.917–1.057), centered on 1 — exactly the empirically-measured g1⊥h independence ratio (repo: 1.005 at N=10 over ~1.07e9 hits). The one cosmetic caveat: the "clean 2^0.74N" the card attaches to the OSC-holds regime is itself not sharp (the collision slope is 0.673, not 0.74 — see W6-FR1), but that does not bear on the 2^-2N overlap claim, which is the actual content of FR2 and is confirmed. A rename-risk would have been R landing at any value (a generic overlap "permits" 2^-2N); instead R=1 *forces* the product structure (independence), which is the rank-2 content.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W6-FR2.py`
