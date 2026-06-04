# W5-HC1 — Container exponent: 0.74 as a container-packing size   ·   VERDICT: KILLED

**Card claim:** collisions = independent sets of a sparse conflict hypergraph H on the 4N
free bits (edges = minimal cascade-violating patterns); the container method packs them into
few containers of size ≤ 2^{cN} with c = 0.74.

**Probe run:** the exact sr=60 MSB-cascade collision families at N=4 (49), N=8 (260), N=10
(946), each collision read as its 4N-bit free-word vector. Tested (A) whether the family is
DOWN-CLOSED (the structural prerequisite for "= independent sets of H"), (B) conflict
co-degree, (C) the growth exponent. Pure-python, throttled.

**Result (numbers):**
| N | 4N | \|S\| | down-closed frac | mean 1-bit-erasure ∈ S | Hamming-1 nbr ∈ S | c = log2\|S\|/N |
|---|----|----|----|----|----|----|
| 4 | 16 | 49 | **0.000** | 0.034 | 0.036 | 1.404 |
| 8 | 32 | 260 | **0.000** | 0.0007 | 0.0007 | 1.003 |
| 10| 40 | 946 | **0.000** | 0.0005 | 0.0005 | 0.989 |

- **The collision family is not down-closed in any degree** (0% of collisions have all their
  single-bit-erasures in S; mean erasure-lands-in-S ≈ 0.001 at N=8,10). Independent sets of a
  hypergraph are subset-closed *by definition*, so **no hypergraph H has this family as its
  independent sets** — the container premise is ill-posed.
- Hamming-1 neighbour-in-family ≈ 0.0005–0.036: the family is a sparse *scattered* set (an
  affine-variety-like point cloud), not a dense monotone independent-set family.
- Growth exponent c = 1.40 / 1.00 / 0.99; verified two-point slope 260@8→946@10 = **0.932**;
  repo fit **0.673**; card 0.74 — not reproduced sharply.

**Kill_criterion:** "H has unbounded co-degree (no container bound), OR predicted exponent
off > 0.1 from the slope." — **fired? YES.** The exponent clause fires (c ≈ 0.93–1.4 vs the
0.673 slope, |Δ| ≥ 0.1), *and* — more fundamentally — the hypergraph H whose co-degree the
criterion references **does not exist** (the family is not down-closed), so no container bound
can apply at all.

**Verdict reasoning:** KILLED. The container method counts the independent sets of a
bounded-co-degree hypergraph; it requires the family to *be* the independent sets of some H,
i.e. to be subset/down-closed. The sr=60 collision family has **zero** down-closure at every
reachable N — it is a sparse scattered point set (consistent with a measure-zero
modular-affine variety in the 4N free bits), exactly the "crypto families are not down-closed"
failure the card's own lens-cousins warn about. With the premise false, "pack them into
containers of size 2^{0.74N}" is not a theorem one can even state for this family. The 0.74
also is not a sharp constant (finding #2): the directly measured exponent is the noisy
0.93–1.0 (repo fit 0.673), meaningful only to ±0.1.

**Cross-check / skeptic note:** A clean structural negative — the kill is on the *premise*,
not a marginal number. Honest caveat on the co-degree row: my pairwise-forbidden-pattern
metric returned 0 forbidden pairs at N=8,10 (the spread-out family realizes all 4 patterns on
every coordinate pair), which means the family is *not* described by pairwise (or any bounded)
conflict constraints — the opposite of "sparse conflict hypergraph," reinforcing the kill
rather than rescuing it. A defender could propose a hypergraph over the *output* trace instead
of the free bits, but that is a different object than the card's "conflict hypergraph on the
4N free bits," and the output is identically zero for collisions (no conflicts to encode).
Containers give *upper* bounds anyway (card's own skeptic), so even a valid H could not pin an
*exact* 0.74 without a matching supersaturation lower bound that is not in evidence.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W5-HC1.py`
