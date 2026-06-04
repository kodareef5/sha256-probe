# W7-FC4 — Concept stability → de58 as the unique low-stability (soft) coordinate   ·   VERDICT: KILLED

**Card claim:** High-stability concepts (intent unshaken by object removal) = the 7/8 constant register diffs (cascade-rigid); low-stability = the lone varying de58/dh61 (carry-fragile single DOF). The de58-grows / de57,59,60-constant split = a stability spectrum; low-σ count ~ 2^0.74N.

**Probe run:** N=8, N=10, 8000 sampled free-word objects each, throttled. Built the per-(register,round) modal-value formal context (attribute = "(coord)=its modal diff"); computed Kuznetsov concept stability σ for each de-round modal concept (σ = fraction of random subsets of the extent whose closure equals the concept's intent, 4000-trial Monte-Carlo), plus distinct-value counts per coordinate and the 2^hw(db56) / growth-exponent checks.

**Result (numbers):** Identical structure at both N:
- de-coordinate distinct values per round = **{57:1, 58:8/16, 59:1, 60:1}** — de58 is the unique varying coordinate (8 at N=8, 16 at N=10), confirming the known split.
- **Concept stability σ = 1.0 for ALL four de-rounds, including de58** (extent of de58=modal is 1063 at N=8 / 542 at N=10 — large enough that essentially every subset reproduces the intent). **No separation whatsoever.**
- 2^hw(db56) law: hw(db56)=4 at both N → 2^4=16; measured |de58| = **8 at N=8 (≠16, law FAILS)**, 16 at N=10 (matches). So even the raw 2^hw(db56) identity is inconsistent at N=8 with this db56 — and concept stability plays **no** role in producing |de58|.
- Growth exponent: |de58| 8→16 over N=8→10 ⇒ **c = 0.500**, not the card's 0.74.

**Kill_criterion:** "de58 concepts have the SAME stability as de57/59/60 (no separation)" — **fired? YES.** σ(de58) = σ(de57) = σ(de59) = σ(de60) = 1.0; the Kuznetsov stability index does not distinguish the soft coordinate at all.

**Verdict reasoning:** The card's "stability spectrum" does not exist. de58 IS the unique varying coordinate (re-confirmed — known per prior-finding #5), but concept stability gives a flat σ=1.0 across all coordinates: the varying coordinate's modal concept is just as intent-robust as the constant ones (its extent is still ~1000 objects, and they all share the constant-coordinate attributes), so Kuznetsov stability cannot mark de58 as "soft." Per finding #5's explicit rule — CONFIRM only if concept-stability DERIVES 2^hw(db56)/2^0.74N — it derives neither: σ is constant, the 2^hw(db56) value (16) even mismatches the measured |de58| (8) at N=8, and the genuine growth is 2^0.5N, not 2^0.74N. The only true content (de58 varies, others constant) is a restatement of established fact through an FCA lens that adds no separation and no derivation.

**Cross-check / skeptic note:** The card's own skeptic note is vindicated: "constant diffs → σ≈1 is near-tautological; the only payload is the de58-vs-others separation + N-growth" — and that payload is exactly what fails (no separation, wrong exponent, no derivation). The σ=1.0-for-all is not a Monte-Carlo artifact: the de58=modal extent (~1000 objects) shares the seven constant-coordinate modal attributes, so any subset reproduces the intent — high stability is forced by extent size, identically for all coordinates. Converges with finding #5 (de58 thread CLOSED; |de58|=2^hw(db56) is a carry/Maj-image count, non-monotone — here the hw(db56)=4 is constant 8→10 while |de58| changes, confirming non-monotone/not-cleanly-derivable). To CONFIRM I would have needed σ(de58) distinctly below σ(de57/59/60) AND the low-σ count to derive 2^hw(db56) or 2^0.74N; instead σ is flat at 1.0 and the growth is 0.5N.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W7-FC4.py`
