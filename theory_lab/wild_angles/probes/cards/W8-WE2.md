# W8-WE2 — Reverse-math calibration: WKL₀ at sr≤60, ACA₀ at sr=61   ·   VERDICT: KILLED

**Card claim:** sr≤60 existence = a WKL₀ fact (cascade tree extendible at every node — Thm2 de60=0 ∀ words — so König gives a path, no set-formation); sr=61 needs ACA₀ (you must *comprehend* the compatible-W[60] set and intersect two independent ranges before choosing). The 3× ceiling = the WKL-locality payoff.

**Probe run (finite witness-finder memory surrogate, per the card):** Two finders over the repo's exact cascade-DP tail (`lib.sha256` via shabridge), for sr_target ∈ {59, 60, 61}:
- **(A) König / backtracking DFS** — extend ONE partial path word-by-word through the choice tree (w57,w58,w59,w60); at the leaf test the STRONG sr=61 condition g1=0 ∧ g2=0 pointwise (the card's "two independent ranges"); backtrack on failure. Holds a path-stack of ≤5 states ⇒ peak live-set = O(rounds), no set materialized.
- **(B) Comprehension** — per triple, MATERIALIZE the two ranges R1={w60:g1=0}, R2={w60:g2=0} (sets of capacity 2^N held in memory) and form R1∩R2. peak live-set = Θ(2^N).
N=5 (exact) and N=8 (bounded leaf-test cap), both throttled.

**Result (numbers):**

| sr_target | König success | König peak-live | König leaf-tests | Comprehension peak-live | min-memory method |
|----------:|:-------------:|:---------------:|:----------------:|:-----------------------:|:-----------------:|
| 59 | True | **1** | (first path) | 2^N (32 / 256) | **König** |
| 60 | True | **1** | (first path) | 2^N (32 / 256) | **König** |
| 61 | True | **5** | 519 (N=5) · 16378 (N=8) | 2^N (32 / 256) | **König** |

- At **both** N=5 and N=8, the König backtracking DFS **finds a strong sr=61 witness** (g1=0 ∧ g2=0) holding only **5 partial-path states** (peak live-set = O(rounds)), in 519 / 16378 leaf-tests (≈ the 2^2N = 2^10/2^16 expected first-hit distance).
- The comprehension finder also succeeds, but at peak live-set 2^N (gratuitous set materialization).
- The minimal-memory successful method is **König at every level**; the structural peak live-set does **NOT** jump O(rounds)→Θ(2^N) at 61.

**Kill_criterion:** "the König finder also certifies 61 with O(rounds) memory (still WKL₀), or even ≤60 needs comprehension (ladder placement wrong)." — **fired? YES.** König certifies sr=61 with O(rounds) (=5-state) memory, never forming a set.

**Verdict reasoning:** KILLED. The card's whole content is a *logical-strength jump* (WKL₀→ACA₀) at round 61, modelled as a witness-finder memory jump O(rounds)→Θ(2^N). The probe shows no such jump: a bounded backtracking depth-first search — the faithful WKL₀ surrogate (König's lemma = follow/backtrack an extendible path through a finitely-branching tree, no comprehension) — reaches the STRONG sr=61 (g1=0 ∧ g2=0) with O(rounds) live-set at both N. Comprehension (materialize-and-intersect-two-ranges, the ACA₀ surrogate) is *sufficient but not necessary*. So sr=61 is NOT a comprehension boundary; it is the *free-cascade + one counting condition* the repo already characterizes (enforcement runs out at sr=60; sr≥61 pays the 2^-2N coincidence, but the *search structure* to hit it is still local/backtracking, not set-forming). The reverse-math ladder is mis-placed: sr≤60 and sr=61 sit on the **same** WKL₀ rung (path-extension, with backtracking past 60); there is no ACA₀ rung. Highest-vocabulary-risk card in the territory, and the risk realized: a fixed-N collision has no infinite content, and the finite memory surrogate it *does* admit shows WKL-locality all the way through 61.

**Cross-check / skeptic note:** The decisive subtlety: de61=0 (the e-register filter in `gap_analysis.c`, ~2^-N, abundant) is NOT the same as STRONG sr=61 (g1=0 ∧ g2=0, ~2^-2N) — I verified at N=5 that the two events overlap in only 28/26782 (filter) ∩ 978 (strong) cases, and that a FULL 8-register collision through round 61 has 0 instances at N=5 (it is 2^-3N rare). The finders therefore test the *card's* condition (the strong two-range intersection), not the weak filter; both find it with the memory profiles above. One could object that backtracking DFS over 2^2N leaves is "morally" comprehension — but reverse math draws the line at *set-formation/memory*, not time: WKL₀ permits unbounded search along a tree with bounded set-existence, which is exactly what the 5-state DFS does. The comprehension finder's Θ(2^N) live-set is a property of *that implementation*, not a necessity of the problem — the hallmark of a vocabulary rename, here failing its own kill bar.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W8-WE2.py --N 5`  (also `--N 8`).
