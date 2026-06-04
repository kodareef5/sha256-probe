# W6-OC5 — Min-effort extremal → dT1_61=0 is the switching surface   ·   VERDICT: ❌ KILLED

_(Recovered by the lead: the OC agent was cut off (tool-use limit) before writing this file; W6-OC5.py was complete and re-run throttled to obtain these numbers.)_

**Card claim:** the minimum-control-effort extremal makes `dT1_61=0` the switching surface; collisions should cluster at low control effort, and a switching-gradient descent toward `dT1_61=0` should beat undirected search.

**Probe run:** N=4,5 — measure (i) whether collisions cluster at low control effort, (ii) whether a switching-gradient descent toward the `dT1_61=0` surface beats fair random-improving descent. `cards/W6-OC5.py`, throttled.

**Result (numbers):**
- low-effort clustering? **False** (no collision clustering at low effort vs random mean effort 7.47).
- switching-gradient descent: success 0.00, median evals ∞; random-improving: 0.00; **switching-gradient BEATS random? False**.

**Kill_criterion:** dead if switching-gradient guidance does not beat fair random descent (the surface is true-but-useless as a search guide). — **fired? YES.**

**Verdict reasoning:** ❌ KILLED. That `dT1_61=0` reduces collisions is already established (the known schedule constraint), but the card's NEW claims both fail: collisions do not cluster at low control effort, and switching-gradient descent does no better than random because the carry "kinks" wreck the descent direction. The switching surface is real but useless as a guide — KILLED by the lab's rename/no-new-content standard, and consistent with the carry-nonlinearity finding (a smooth descent cannot see the surface).

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W6-OC5.py`
