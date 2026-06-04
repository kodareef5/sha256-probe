# W5-TO4 — Sheafification gap: locally-consistent fragments that fail to glue, blowing up at 61   ·   VERDICT: KILLED

**Card claim:** on a round-window site, local sections = collision fragments (presheaf F); the sheaf F⁺ keeps only those that glue to a global collision; the gap |F|−|F⁺| is small through 60 and BLOWS UP at 61 (many locally-consistent fragments disagree on the g1∧h overlap); 2^-2N = the gluing-success rate there. (Catalog flags this the "best fan-out".)

**Probe run:** Exact full-grid enumeration of the cascade-DP tail at N=4 (65536 inputs, 49 global collisions). A "local section through window r" = a fragment locally consistent at every CONSTRAINT round ≤ r (the collision's only constraints are de61=de62=de63=0, boundary-proof Thm 3; rounds 57-60 are cascade-free → every fragment locally consistent). L_r = #locally-consistent, G_r = #that glue to a global collision, gap = L_r−G_r, gluing rate g_r = G_r/L_r. Carry-free (XOR) control also run. Throttled.

**Result (numbers):**
- gluing rate g_r: r57=0.00075, r58=0.00075, r59=0.00075, r60=0.00075, r61=**0.0101**, r62=**0.106**, r63=**1.000**. The rate RISES at the schedule rounds — it does not "drop sharply at 61".
- sheaf gap |F|−|F⁺|: r57=**65487**, r60=**65487**, r61=4799, r62=415, r63=0. The gap is MAXIMAL at the widest window (57) and monotonically CLOSES through the schedule rounds.
- Ratio g61/g60 = 13.5 (an increase, not a 2^-N drop). The un-gluable count through 60 is the full 65487 background, NOT a 2^-2·width object.

**Kill_criterion:** "g_i smooth/featureless across rounds, OR un-gluable count doesn't scale like 2^-2N." — **fired? yes.** The un-gluable count does not scale like 2^-2N (it is the full 65487 background, constant through 60). And the feature that does exist runs the WRONG way (g rises at 61, the gap closes), which is the opposite of the card's "blows up at 61".

**Verdict reasoning:** The card has the mechanism inverted. It predicts the gap is small through 60 and blows up at 61; in fact the gap is already maximal at the widest window (every one of 65536 fragments is "locally consistent" since rounds 57-60 impose no constraint, yet only 49 glue), and the schedule constraints at 61-63 PRUNE the non-gluable fragments, so the gap CLOSES and the gluing rate climbs to 1. The only "61 feature" is L_r first dropping there — i.e. the known free→schedule constraint onset (de61=0 ≈ 2^-N), re-described. So "fails to glue at 61" dissolves into the message-schedule constraint exactly per prior finding #4. KILLED.

**Cross-check / skeptic note:** The 49→49→49 column (G_r constant) confirms gluing is governed entirely by the de61/62/63 filters, matching the boundary proof's three-filter equivalence. The XOR control gives 0 collisions (carry-free cascade is degenerate), so it cannot exhibit the card's "linear toy g≈1" — uninformative, not confirming. Exact enumeration is N=4-only (degenerate M0 at N=6,7,9; N=8 grid infeasible), but the constraint structure (free 57-60, schedule 61-63) is N-invariant (Thm 1-4). A skeptic might define "local section" on a sliding window rather than a growing prefix; but any honest local-consistency notion must call rounds 57-60 unconstrained (de60=0 is automatic, Thm 2), so the gap is necessarily back-loaded to the widest window and closes — the blow-up-at-61 shape cannot arise.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W5-TO4.py`
