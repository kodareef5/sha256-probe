# W6-OM3 — NIP→IP dividing line → the wall as the independence property   ·   VERDICT: KILLED   [HEADLINE]

**Card claim:** "two independent conditions g1=0 ∧ h=0" is the literal recipe for IP (an AND of independent predicates shatters index sequences); the alternation rank of R_r(x,y)=[collide] along a structured (cascade-shift) sequence is BOUNDED (NIP, tame) for rounds ≤60 and BLOWS UP (IP, wild) at round 61.

**Probe run:** N=4,5,8 exact (throttled). Built the full 2^N×2^N collision relation R_r(w57,w58) (w59=w60=0) for r∈{≤60 (cube), 61 (de61=0), 63 (collision)}. For cascade-shift w57 progressions a_i=(i·step) mod 2^N (steps 1,3,5,7) and every test parameter b=w58, counted sign-changes (alternation) of R_r(a_i,b); reported max/mean alternation, its fraction of m=2^N, and a literal VC/IP shatter index (#distinct 0/1 patterns the columns realize on the first 4 indices vs 2^4). Also measured the **non-degenerate r63 marginal** R(w57,w58)=∃(w59,w60) collision from the 260 verified N=8 collisions.

**Result (numbers):**
| N | alt(r≤60) | alt(r61) max/mean | dens61 | alt(r61)/m | shatter61 | shatter63 |
|---|---|---|---|---|---|---|
| 4 | 0 | 2 / 0.62 | 0.0195 | 0.133 | 4/16 | 1/16 |
| 5 | 0 | 8 / 1.29 | 0.0215 | 0.258 | 3/16 | 1/16 |
| 8 | 0 | 8 / 1.79 | 0.0035 | 0.031 | 4/16 | 1/16 |

N=8 r63 **marginal** relation: density 0.0038, alt max/mean = 8/1.94, alt/m = 0.031, shatter(block 4) = **2/16**.

**Kill_criterion:** "already ~Θ(m) for r≤58, no upward break at 61, OR alternation DECREASES at 61." — **fired? yes.**

**Verdict reasoning:** KILLED — the strongest negative for the headline. (i) alt(r≤60)=0 at every N: the free cascade makes the relation constant-TRUE, trivially NIP, but for the structural reason that nothing is constrained, not "tame geometry." (ii) At the wall (r=61) and at r=63 the relation is a **sparse, shrinking** sieve: density → 0 as N grows (0.020→0.0035 for de61; 0.0038 for the r63 marginal), so the alternation **as a fraction of m DECREASES** with N (0.133→0.031), the exact opposite of an IP blow-up — and "alternation decreases at 61" is a literal kill clause. (iii) The literal IP claim is tested and fails: the first index block is **not shattered** (4/16 and 2/16, never 16/16), so "g1=0 ∧ h=0 shatters index sequences" is not exhibited. There is no NIP→IP *transition* at 61; the round function is identical each round (finding #4).

**Cross-check / skeptic note:** The skeptic's caveat (only N-scaling carries content; arithmetic progressions aren't truly indiscernible) is honored — the verdict rests on the scaling (alt/m shrinking, density→0, shatter capped well below 2^block), not on a single fixed-N alternation. The w59=w60=0 slice for r63 is degenerate (zero collisions there), so the decisive r63 evidence is the *marginal* relation over the full 260-collision support, which is equally sparse and unshattered. Several sequence families (steps 1,3,5,7) agree. A truly indiscernible sequence (vs an arithmetic progression) could in principle expose more alternation, but the relation's vanishing density caps any alternation at o(m) — IP is structurally precluded by sparsity.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W6-OM3.py` (N=8 marginal reads /tmp/coll_n8.txt from the verified enumerator at `#define N 8`).
