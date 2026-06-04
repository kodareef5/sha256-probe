# W4-SH4 — Spectral-gap order parameter → a rank-2 degeneration at 60→61   ·   VERDICT: KILLED (rank-2 sub-claim CONFIRMED separately)

**Card claim:** sweeping the last-glued round r=57..62, λ₁ is O(1) for r≤60 and **exactly two** eigenvalues cross to zero at 61 (g1=0, h=0), localized on the round-61 g/h slots.

**Probe run:** full real spectrum of L=δᵀδ over the tail sweep R=1..6 (sr 57→62), N=3,4,5, 2 seeds — λ₁(r), near-zero-mode count and its per-step increment (CLAUSE A: the "at 60→61" anomaly). Plus the established structural rank-2 anchor g2≡g1+h on the repo N=10 collision gap data (CLAUSE B: genuine rank-2). Throttled (OMP=2, taskpolicy -b). Scored as two clauses per prior-findings #3/#4.

**Result (numbers):**
- **[CLAUSE A — "at 60→61" anomaly] FAILS.** Per-step near-zero-mode increment is **uniformly N** (4 at N=4; 3,3,3,3,3 at N=3; 5,5,5,5,5 at N=5; identical across 2 seeds) — at EVERY step, not localized at 60→61. The increment at the 60→61 step (R=4→5) = **4**, which is **≠ 2 and ≠ 2N (=8)**. λ₁ is non-monotone with **no drop** at the boundary (ratio λ₁(60)/λ₁(61) = 0.70, i.e. λ₁ *rises*). Increments uniform ⇒ no anomaly at 61.
- **[CLAUSE B — genuine rank-2] CONFIRMED.** g2 ≡ g1 + h (mod 2¹⁰) for **946/946** collisions (EXACT); the empirical (g1,g2) cloud has rank **2**. This is the real codim-2 / rank-2 degeneration (the unimodular [[1,0],[1,1]] map; sr=61 = the origin), converging with IG2 (slope −2.006) and the repo's VERIFIED `RESULT_sr61_is_2minus2N.md`.

**Kill_criterion:** "λ₁ flat (no anomaly at 61), or new-mode count ≠ 2 (and ≠ 2N)." — **fired? YES.** The new-mode count is N (4 at N=4) ≠ 2 and ≠ 2N=8, and the increments are uniform with no λ₁ anomaly at 61.

**Verdict reasoning:** Split verdict exactly as the wave preamble anticipated. The card's **spectral** mechanism — "exactly two eigenvalues cross to zero specifically at 60→61, localized on g/h" — is **KILLED**: the linear sheaf adds *N* near-zero modes per round uniformly (one fresh free word each round), with no special event at the boundary and no λ₁ collapse there. The card's own kill criterion (count ≠ 2 and ≠ 2N) fires. **Separately, the rank-2 fact is CONFIRMED** — but it lives in the *modular* gap data (g2≡g1+h exact), NOT in the linear-sheaf spectrum. So "rank-2 degeneration" is true; "a *spectral*-gap rank-2 degeneration *at 60→61*" is false. Per prior-finding #3 the rank-2 part is real (9th confirmation); per #4 there is no round-60 knee, so the localization-at-61 clause dies.

**Cross-check / skeptic note:** The card's skeptic ("the gap could move at 61 for a trivial one-fewer-free-word reason") is *exactly* what happens — and worse: the spectrum adds N modes EVERY round for that trivial reason, so 61 is not even distinguished. The rank-2 CONFIRM is anchored in 946/946 exact algebra and an independent slope=−2 (IG2), not a fitted spectral coincidence — it survives a skeptic's look because it converges on a previously-established exact structure. The clean separation (modular rank-2 yes; spectral-at-61 no) is the value here: the rank-2 truth does not arise from this card's Hodge construction.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W4-SH4.py`
