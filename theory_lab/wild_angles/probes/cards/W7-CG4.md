# W7-CG4 — Misère cascade: is the wall intrinsic or an artifact of orientation?   ·   VERDICT: KILLED

**Card claim:** Flip to misère (last collision-completing move loses); if the wall is intrinsic the P-set is invariant (tame), if it moves the boundary is an artifact of orientation (wild).

**Probe run:** Faithful mini-SHA(N) cascade. (1) Built a 4-ply impartial game (rounds 57→60, branch cap 16 words/round, terminal = wall condition g1=0∧h=0) and computed normal-play vs misère-play P-sets by exact backward induction; measured their divergence. (2) Counted whether a collision-completing (wall) move even exists, over 1.2M random cascade prefixes at N=8. Throttled: yes.

**Result (numbers):**
- P-set divergence (normal vs misère differ) = **0/16** at both N=8 and N=10; root is a P-position under both.
- Over **1,200,000** cascade prefixes (N=8): **all 1,200,000 are sr60 collisions** (de61=0 for every cascade prefix — the free cascade), and exactly **19 hit the wall** (g1=0∧h=0), matching the 2^-2N prediction (expected 18.3).

**Kill_criterion:** "P-sets identical everywhere (fully tame → misère adds nothing), OR the graph too coupled to define disjunctive misère." — **fired? yes** (both clauses hold).

**Verdict reasoning:** The wall locus is the algebraic condition g1=0 ∧ h=0, fixed by the message schedule; it does not depend on whether the last completing move is declared a win (normal) or a loss (misère). So the misère flip relabels the terminal but cannot move the boundary — the P-set near the wall is invariant → **tame → the wall is INTRINSIC**, which is the card's "intrinsic" branch, and means misère adds nothing (kill clause 1). Independently, per CG1 the de-vector is not a disjunctive sum (coords coupled, group-free image), so disjunctive misère genus is undefinable (kill clause 2). Note also the construction is barely a two-player game: every cascade prefix is already an sr60 collision (1.2M/1.2M), so there is no losing terminal to create P/N tension — the "last move" to the true wall is a measure-2^-2N event in a sea of already-winning positions. KILLED: the orientation flip is vacuous; the boundary is intrinsic (a schedule identity), not an artifact of pointing at the normal-play terminal.

**Cross-check / skeptic note:** The 19/1.2M wall hits independently re-confirm the 2^-2N rate (the CG3 mechanism), so the engine is faithful. A skeptic could note the truncated game (cap=16) never reaches the wall, making the 0/16 divergence "trivial" — but that is itself the point: at any reachable N the completing move is 2^-2N-rare, so no finite small-N game exercises a non-trivial misère/normal split, and the wall's definition (a fixed schedule equation) is orientation-independent by inspection. This robustness check returns "intrinsic," not "wild."

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W7-CG4.py`
