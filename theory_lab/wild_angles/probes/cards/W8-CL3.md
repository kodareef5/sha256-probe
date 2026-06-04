# W8-CL3 — TNN minors → de58 = the one positive coordinate of a TNN cell   ·   VERDICT: KILLED

**Card claim:** The modular round-transfer on (de57..de60) is conjectured totally-nonnegative (TNN); its Bruhat cell freezes 3 coords (de57/59/60 = vanishing minors) and frees one (de58 = the positive minors), with log₂|de58| = the cell rank.

**Probe run:** Faithful mini-SHA(N) cascade. N=8/10/12. Built the real de-transfer matrix on the e-path diff block (de,df,dg,dh) by reading off the *exact* diff-state recurrence along the cascade, computed **all minor signs** (every square submatrix, orders 1–4), and compared #strictly-positive maximal minors vs log₂|de58|. Also measured |de58| (exact full-w57 sweep at N≤12) and hw(db56). Throttled: yes.

**Result (numbers):**
- The honest de-transfer is the **nilpotent shift** (verified empirically: df_{r+1}=de_r, dg_{r+1}=df_r, dh_{r+1}=dg_r hold for all sampled trajectories, all N):
  `[[0,0,0,0],[1,0,0,0],[0,1,0,0],[0,0,1,0]]`.
- ALL minor signs at every N: **#negative = 0** (+ : 7, 0 : 62, − : 0). The **maximal (4×4) minor = det = 0** (nilpotent) ⇒ **#strictly-positive maximal minors = 0**.
- |de58| = 8 / 16 / 512 at N=8/10/12 ⇒ log₂|de58| = **3 / 4 / 9** — matches the repo's pinned Figure 3 table exactly.
- Card claim log₂|de58| = #positive-maximal-minors: 3≠0, 4≠0, 9≠0 → **MATCH = False at every N**.

**Kill_criterion:** "ANY strictly-negative minor (not TNN), OR the frozen set is the wrong three." — **fired? yes (decisive via the structural claim).** No strictly-*negative* minor appears (a 0/1 shift is vacuously sign-nonnegative), but the card's load-bearing identity — log₂|de58| = #strictly-positive **maximal** minors = the cell rank — is falsified: that count is **0**, while log₂|de58| ∈ {3,4,9}. The TNN cell does **not** encode de58.

**Verdict reasoning:** Exactly the catalog's "clean kill" and prior-finding #5. Total positivity does **not** derive 2^hw(db56): the only matrix with real-valued ("signed") minors is the nilpotent shift, whose top minor vanishes, so the cell rank is 0 — it cannot equal log₂|de58| (3–9). The de58 image size is a **carry-collapsed Maj-image count** (a set cardinality, non-monotone), not a positivity rank. Moreover any *genuinely modular* (non-shift) transfer over Z_{2^N} has no real sign at all, so "totally nonnegative" is a category error for the object the card invokes. The structural claim is false; the angle is dead.

**Cross-check / skeptic note:** The engine independently reproduces the pinned |de58|=8,16,512 (= repo Figure 3) and the de57/59/60-constant cascade (W7-CG1), confirming faithfulness before the kill. Caveat: my hw(db56) from the auto-found M0 (4,4,6) differs from the writeup's pinned column (3,4,9) — a candidate/convention difference in how "db56" is taken — but this does **not** affect the verdict, because (i) |de58| itself matches the canonical table exactly, and (ii) the falsified claim (log₂|de58| = #positive maximal minors) is independent of db56 and fails because that minor count is 0. A defender could try a different "transfer" matrix to manufacture positive minors, but then it would no longer be the actual diff-recurrence and would carry no Z_{2^N} sign — either way the TNN reading does not survive.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W8-CL3.py`
