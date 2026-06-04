# W5-ER2 — Matrix-tree spanning-forest count → 0.74 as tree-entropy   ·   VERDICT: KILLED

**Card claim:** Each collision ↔ a unique carry vector; admissible carry assignments = weighted spanning forests of the carry-coupling graph; Kirchhoff counts them as a Laplacian-minor det; log₂det ~ 0.74 N.

**Probe run:** N=4,8,10,12, throttled. Built the carry-coupling Laplacian on the N adder carry-lanes under several **a-priori carry-physics** edge weightings (NOT tuned, per the card's own skeptic): W1 fair carry-propagate p=1/2, W2 Lipmaa–Moriai per-lane propagate probability (from `adder_diff` LM physics), W3 measured carry-difference activity per lane. Each on both path- and cycle-topologies. Kirchhoff number = `slogdet` of the (n−1) cofactor. Compared log₂(tree-count) vs N to the known collision counts {49, 260, 946, 2955}; checked slope ∈ [0.70,0.78] and count-tracking r².

**Result (numbers):**

Raw-count reference: the 4 known counts least-squares-fit slope **0.7401** (r²=0.99) — but the per-segment slopes are 0.602 / 0.932 / 0.822, i.e. the "0.74" is a 4-point coincidence over noisy data (prior finding #2: true asymptotic ≈ 0.673).

The matrix-tree determinant slopes (a-priori weightings):

| weighting | log₂(tree-count) per N | slope | in [0.70,0.78]? |
|---|---|---|---|
| W1 fair (path)   | −4, −8, −10, −12          | **−1.000** | no |
| W1 fair (cycle)  | −1.00, −4.00, −5.68, −7.42 | **−0.799** | no |
| W2 LM (path)     | −1.08, −2.01, −2.42, −2.69 | −0.206 | no |
| W2 LM (cycle)    | +1.19, +1.24, +1.15, +1.12 | −0.010 | no |
| W3 active (path) | −4.39, −8.46, −10.45, −12.58 | −1.022 | no |
| W3 active (cycle)| −1.28, −4.39, −6.08, −7.95 | **−0.828** | no |

Determinant slopes are **negative** (conductances are probabilities <1). Even the maximally card-friendly inverse-conductance (c=1/p) cycle framing gives slopes **+1.20 (fair), +1.23 (active), +0.41 (LM)** — still none in [0.70,0.78]. Nine weightings tried; zero land in the band.

**Kill_criterion:** "best-fit slope ∉ [0.70,0.78] for ALL physically-motivated weightings, or r²<0.9 on the 4 points." — **fired? YES (first clause).** No a-priori weighting (and no inverse variant) gives a slope in [0.70,0.78].

**Verdict reasoning:** KILLED. The high count-tracking r² (≈0.99) several weightings show is an artifact — both log₂(tree-count) and log₂(count) are monotone in N, so any monotone surrogate "tracks." But the discriminating quantity, the *slope*, is wrong for every fixed-a-priori carry-physics weighting (negative for direct conductance, 0.41–1.23 for inverse). To force 0.74 one would have to tune a free multiplicative constant on the conductances — exactly the rename the card's skeptic flagged and prior finding #2 warns against. The determinant is the wrong counting class for the (non-XOR-closed, nonlinear) carry set. The genuine slope of the actual counts is ≈0.673–0.74 only as a noisy 4-point average; the matrix-tree object does not derive it.

**Cross-check / skeptic note:** The strongest card-favorable reading is |slope|≈0.80 for the fair/active cycles — suggestively near the noisy raw per-segment slopes — but it has the wrong sign, requires the unphysical 1/p flip to become positive, and even then overshoots to 1.2. No a-priori weighting threads "positive AND in-band AND tracking" simultaneously. Consistent with the broader pattern that 0.74 is not a sharp, mechanism-derived exponent.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W5-ER2.py`
