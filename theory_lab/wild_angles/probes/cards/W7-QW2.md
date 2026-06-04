# W7-QW2 — Discriminant top edge → 0.74 = log₂ s_max(D)   ·   VERDICT: KILLED

**Card claim:** The bidirectional search operator's top singular value = per-bit amplification of completable prefixes; 2^{0.74N}=s_max^N, so 0.74 = log₂ s_max(D), computable from local transition stats, and ≠ P's Perron (the non-reversible feed-forward is the only thing saving it).

**Probe run:** N=6,8,10. Built the cascade-pinned (msgdiff=0 — the regime collisions live in) differential transfer operator P, formed D=√(P∘Pᵀ), took s_max(D) and its log₂; compared to 0.74, to 0.673, and to Perron(P). Cross-checked with the RAW-COUNT ("forward weight = #completions", unnormalized) operator. Also computed the *real* 0.74-source: log₂(#Coll)/N from the repo-verified exact census (260@N8, 946@N10). Throttled yes.

**Result (numbers):**
- **log₂ s_max(D) = 0.0000** at N=6,8,10 (s_max(D) = **1.0000** exactly) — misses 0.74 by 0.74 and is **outside [0.6,0.9]**. The transfer operator is conservative (the zero-diff sink is a probability fixed point), so its discriminant top edge is pinned at 1, not 2^0.74.
- Same under the raw-count operand: s_max(D)=1.0000, Perron(C/samp)=1.0000 → no amplification edge appears either way.
- **s_max(D) = Perron(P) = 1.0000**, rev_gap ≈ 0.0001 → D merely √-relabels P (the explicitly *banned* reversible outcome).
- The genuine 0.74-source, collision-growth slope, refits to **0.93** (secant N=8→10) / ~1.0 per-N here — i.e. **not a sharp 0.74** (consistent with the repo's honest 0.673 refit, spread 0.72–1.04).

**Kill_criterion:** "log₂ s_max ∉ [0.6,0.9], or = the round-Jacobian's top singular value (relabel), or = P's Perron value (reversible)." — **fired? yes (clauses 1 and 3).**

**Verdict reasoning:** The discriminant's top edge is structurally 1 (mass-conserving walk), so log₂ s_max(D)=0 — it cannot be 0.74, and D equals a relabel of P (Perron=1) to 4 decimals, the banned case. The 0.74 is a growth-rate of the *collision count*, an external asymptotic that doesn't refit sharply to 0.74 anyway; it is not the top singular value of any survival operator. This is prior-finding #2 (0.74 is dead as a derivable sharp constant) reproduced from the Szegedy angle.

**Cross-check / skeptic note:** Both normalizations (stochastic and raw-count) give s_max(D)=1 — the result is not a normalization artifact. To make 0.74 appear one would have to redefine "s_max" as the count-growth of a non-conserving sub-operator (i.e. re-derive the census slope), which is the banned relabel of the already-non-sharp 0.673. No N-stable sharp 0.74 emerges.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W7-QW2.py`
