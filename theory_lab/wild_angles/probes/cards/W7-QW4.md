# W7-QW4 — Interference fringe → N=10 bump as a singular-value coalescence   ·   VERDICT: KILLED

**Card claim:** Constructive interference = two eigenphases coalescing (a singular-value crossing in D); the rotations make D's top-two singular values **cross at N=10** (a dip in s₁−s₂), splitting at 9,11 — predicting the next anomalous N.

**Probe run:** N=8..14 (ran 8–12, the decisive window). For each N built the cascade-pinned diff-config chain P, formed D=√(P∘Pᵀ), took its top-two singular values (averaged over 3 seeds to de-noise), and tested whether s₁−s₂ has a local minimum (coalescence dip) at N=10. Also checked the *premise*: is N=10 a collision bump, from the repo's per-N census. Throttled yes.

**Result (numbers):**
- **Premise is false.** Repo yields N=8,9,10,12 = 4322, **52821**, 19677, 92975 → N=9/N=10 = **2.68×**. N=10 is a **TROUGH** (N=9 peaks), not a bump. There is no N=10 collision bump to explain.
- **No dip at N=10.** s₁−s₂(D) runs 0.99671 (N=8) → 0.99931 (N=9) → **0.99988 (N=10)** → 0.99971 (N=11) → 0.99973 (N=12). The gap is *largest* at N=10 (a local **maximum**), the exact opposite of a coalescence dip; the only weak local minimum is at N=11.
- s₁ = 1.00000 throughout (conserved walk), so any "crossing" would require s₂→1, which never happens (s₂ ≤ 0.0033).

**Kill_criterion:** "no local minimum at N=10, or the bump fails to replicate under alternating-fill corrections." — **fired? yes (no local minimum at N=10; and there is no bump to begin with).**

**Verdict reasoning:** The card rests on a false premise (N=10 is a trough, not a bump — prior #4) and its specific prediction inverts the data: the discriminant's top-two singular-value gap is *maximal* at N=10, not minimal, so there is no eigenphase coalescence there. Both the empirical anchor and the spectral signature fail. This is the most story-like / fragile card and it dies cleanly.

**Cross-check / skeptic note:** One data point + 5 N's is admittedly weak, but the result is unambiguous in both directions (yield trough AND gap maximum at N=10), so noise can't rescue it — the std on the gap is ≤0.0024, far smaller than the 0.99671→0.99988 trend. The faint local min at N=11 is not predicted by the card and is within sampling spread; not pursued.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W7-QW4.py`
