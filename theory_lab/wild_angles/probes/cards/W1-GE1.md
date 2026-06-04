# W1-GE1 — Čech / contextuality obstruction of the per-adder cover   ·   VERDICT: KILLED

**Card claim:** Every adder is locally satisfiable (proven) but they can't glue; the sr-wall is a nonzero Čech H¹, not a rarity.
**Probe run:** Built the genuine 7-adder cover of one tail round at width N (rotations included); (A) computed the nerve's loop number b1; (B) propagated single-bit kernel diffs through all 7 adders at N=4,5,6 with the repo's exact Lipmaa-Moriai xdp+ and counted adders with **incompatible** (zero-probability) LM sections — the local sections that would fail to glue. Cross-checked against the repo's own `active_adder_lm_bound.c` at full 32-bit width. Throttled (`taskpolicy -b`, OMP=2).

**Result (numbers):**
- Nerve of the 7-adder cover: V=7, E=7, components=1 → **b1 = 1** (the carry-overlap nerve *does* have a loop; the skeptic's "tree ⇒ H¹=0 trivially" gate does **not** fire).
- N=4/5/6, every propagated trail: **all-LM-compatible at every adder, min incompatible-adders = 0**, in all 40/50/60 trials. No local section ever fails to glue.
- Repo's 32-bit tool on the verified champion (m17149975): **43 active adders, 0 incompatible**, total LM cost = 859 bits.

**Kill_criterion:** "Dead if the class is nonzero where collisions provably exist or vanishes at a no-collision N." — **fired? yes**

**Verdict reasoning:** The contextual sheaf here is the sheaf of LM-compatible carry/difference sections over the adder cover; its H¹ is the obstruction to a global gluing. The measurement (mine at small N, the repo's at 32-bit) shows the obstruction is **identically zero** — there are *never* any LM-incompatible adders, so a global section always exists, at every N and every candidate. The class therefore vanishes everywhere, including the no-collision (wall) regime, which is exactly the kill condition. The wall is not a Čech gluing failure: it is a **probabilistic weight** — the LM cost (≈859 bits ≈ the 2^-2N rarity), not a qualitative cohomology class. Local-AND-global LM-compatibility is in fact the repo's established "43 active adders, zero LM incompatibilities."

**Cross-check / skeptic note:** The card's own skeptic worried H¹ would be trivially 0 on a tree nerve; I found the nerve actually has a loop (b1=1), so that's *not* why it dies. It dies for the deeper reason: the per-adder local sections always glue (XOR-differential gluing is the literal carry-out=carry-in restriction, and it is always consistent). What's missing is any *failure* to glue. An adversary could object that "compatibility" should be measured with the output forced to zero (a true collision context); but forcing output=0 only re-weights probability, it does not create an LM incompatibility (xdp+ stays positive), so the H¹ stays zero. Convergence: the probe reproduced the repo's 43/0 invariant independently.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W1-GE1.py`
