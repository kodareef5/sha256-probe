# W5-HC2 — Sunflower core: the 132 as the bits common to all collisions   ·   VERDICT: KILLED

**Card claim:** the Sunflower Lemma forces a common core; the 132 hard-core bits =
the carry-difference core shared by ~all collisions (petals = the free 124); anchored
to "42% carry-invariance ≈ 108, a near-miss to 132/256 = 0.516".

**Probe run:** N=4 (49 colls), N=8 (260), N=10 (946) — the exact sr=60 MSB-cascade
collision families (N=4 enumerated; N=8 from re-validated `/tmp/coll_n8.csv`; N=10 from
the repo's read-only `gap_rows.csv`). Three literal readings of "bits common to all
collisions": (R1) forced output/hash bits, (R2) common nonzero internal-difference core
over rounds 57–62, (R3) forced free-input bits. Pure-python, throttled.

**Result (numbers):**
| reading | N=4 | N=8 | N=10 | vs card |
|---|---|---|---|---|
| R1 forced **hash** bits | **0**/32 | **0**/64 | **0**/80 | card says 0.516·8N; actual = 0.000 |
| R2 common **diff** core (r57–62) | 43/192 | 71/384 | 81/480 | width-scaling, in regs **c–h**, never 132 |
| R2 petal pairwise Jaccard | 0.103 | **0.407** | 0.310 | card needs disjoint-ish (~0); high overlap |
| R3 forced **input** bits | 2/16 | **0**/32 | **0**/40 | no stable core |

- R2 core register spread (N=10): c=4 d=9 e=11 f=17 g=18 h=22, and **a=b=0**. Registers
  a,b carry *zero* difference in every collision (the cascade forces da=db=0) — the exact
  *opposite* of the "132 hard core", which names a,b as the *uncontrolled* registers.
- The "132 = 4N+4" census scaling (132 only at N=32) is reproduced as context; the
  collision-common cores here (0, or 43/71/81) match neither 132 nor 4N+4.

**Kill_criterion:** "core fraction unstable across N, petals high-overlap, OR extrapolated
core misses 132/256 by >15%." — **fired? YES** (all three clauses).

**Verdict reasoning:** KILLED. Under every faithful reading, the "bits common to all
collisions" do not equal 132, do not equal {a,b,e,f}+4dc, and are not a stable 0.516
fraction. The literal common output set is *empty* (R1=0 at all N: collisions agree on no
hash bit). The only genuine common-difference structure (R2) lives in registers c–h, scales
with N (43→71→81), and has high-overlap petals (Jaccard 0.31–0.41, not the disjoint petals a
sunflower needs). The 42% "near-miss to 132" does not materialize (no 0.42 fraction appears;
0.516 vs measured 0.000). This is **finding #1**: the 132 is the single-bit-flip *control
census* (a property of the compression map's sensitivity, computed in `hard_core_132_bits.md`
from a diff-linear matrix), **not** a sunflower core of the collision family — and the census
re-count would give 4N+4, not a stable 132 either. The sunflower-lemma framing is the wrong
object for this family.

**Cross-check / skeptic note:** Strongest possible form of the kill on R1 (exactly 0 common
hash bits, at three N). The one structure that *is* "common to all collisions" — da=db=0
everywhere — is the cascade construction (the design constraint), not an emergent Δ-system
core, and it sits on the registers the 132-story calls *un*controlled, so it cannot be the
132. A defender might point to R2's nonzero core as "a core" — but it fails the sunflower test
twice (width-scaling count ≠ 132; high petal overlap ≠ disjoint). Independent corroboration of
finding #1's category error (cf. W2-CT1: 132 is the census, not a basis-independent invariant).

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W5-HC2.py`
