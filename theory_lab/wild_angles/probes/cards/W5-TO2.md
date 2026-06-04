# W5-TO2 — Heyting-meet measure: 2^-2N as μ(U_A)·μ(U_B), anchored to the 1.005 ratio   ·   VERDICT: SURVIVES (as a rename of g1⊥h — adds no new number)

**Card claim:** the two sr=61 conditions are two opens U_A={g1=0}, U_B={h=0} in Ω; the collision truth value is the meet U_A∩U_B, whose measure factors as 2^-N·2^-N *iff* the opens are independent — exactly the measured ratio 1.005. The deviation of ρ_r from 1 across rounds = a *map of which conditions share a carry chain* (a lever).

**Probe run:** EXACT full-grid enumeration at N=4 (no Monte-Carlo noise) of the per-round Heyting meet. For each boundary round r∈{58,59,60,61}, enumerate all R^(r-56) free-word tuples, compute the two opens A={g1_r=0}, B={h_r=0}, and the meet measure ρ_r = μ(A∧B)/(μ(A)μ(B)). (An initial 600K-sample Monte-Carlo at N=8 was too noisy — single-digit joint counts — so it was replaced by exact enumeration; r=61 grid = 16⁵ = 1.05M.) Also attempted the N=10 gap_rows.csv anchor. Throttled.

**Result (numbers):**
- **ρ_r = 1.0000 EXACTLY at every round 58, 59, 60, 61** (spread = 0.0000). Joint counts healthy: r60 both=259/65536, r61 both=4848/1048576. The meet factors as a product at every round.
- P(A)=2^-N exactly (0.0625); P(B)≈2^-N (0.0625–0.074). The product μ(A)μ(B) reproduces the rate; the independence is exact, not merely ≈1.005.
- The card's ADD prediction — a *round-structured* ρ_r departing from 1 to fingerprint carry-sharing — does NOT appear: ρ_r is flat at 1 across all rounds.
- N=10 gap_rows.csv anchor: all 946 sr=60 collisions have g1≠0 and h≠0 (this file is the sr=60-but-not-61 set; sr=61 is 2^-2N≈2^-20-rare), so ρ_60 is undefined from it — expected, not a contradiction.

**Kill_criterion:** "ρ_r ≈ 1 for *every* round (independence generic, no fingerprint), OR ρ noisy/unstable." — **fired? yes (first clause).** ρ_r ≈ 1 for every round, with NO round-dependent fingerprint. Independence is generic, not a carry-sharing map.

**Verdict reasoning:** Per prior finding #3 and the explicit RENAME rule for this card: the topos meet-as-product language DOES reproduce the established substrate (the meet U_A∩U_B factors → 2^-2N), exactly because g1⊥h is genuinely rank-2 — here shown EXACT (ρ=1.0000) at N=4. But CONFIRMED requires the card to ADD a new number/prediction beyond restating g1⊥h, and its own candidate ADD (the round-dependent ρ_r−1 carry-sharing fingerprint) is falsified — ρ_r is flat 1. So this is **SURVIVES-as-rename**, NOT CONFIRMED: it is the topos-language restatement of the already-established g1⊥h independence, with no new content. (I mark SURVIVES rather than KILLED because the meet-factorization the card centers on is genuinely true and consistent; it simply isn't new.)

**Cross-check / skeptic note:** The exact ρ=1.0000 at N=4 is a cleaner independence statement than the published 1.005 (which is a 1.07e9-sample estimate at N=10 with finite-sample slack); both say the same thing — g1 and h are independent, rate 2^-2N. The flatness across rounds is itself a (negative) finding: there is no per-round carry-sharing structure to exploit as "a lever". A skeptic could argue larger N might reveal a small ρ_r−1 modulation; but the established N=10 ratio is already 1.005 (≈1), and the exact N=4 value is dead-on 1, so a round-structured fingerprint is not in evidence at any N reached. Does TO2 add anything beyond g1⊥h? No — it re-expresses it. SURVIVES strictly as a rename.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W5-TO2.py`
