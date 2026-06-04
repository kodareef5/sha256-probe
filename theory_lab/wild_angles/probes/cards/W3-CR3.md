# W3-CR3 — Computational-irreducibility onset → a compressibility cliff at ~60   ·   VERDICT: KILLED

**Card claim:** For each round r, P_r(M) = "da=0 admissible at r"; measure minimal representation size of P_r vs r. Reducible early rounds → small circuits; the wall = where size(P_r)/(round cost) plateaus at ~1 (no shortcut), a compressibility cliff scaling toward round 60.

**Probe run:** Truth-tabled P_r(x) = [da=0 at round r] over nvars=9–10 free input bits (perturbing the conditioning state + per-round message word), for r=1..24, at N=3,4,5. For each round computed three compressibility proxies: LZMA-compressed bytes of the packed truth table, ROBDD node count (canonical decision diagram, pure-python reducer), and a greedy subcube-cover term count (circuit proxy). Detected knees via discrete 2nd-difference and quantified pre/post-saturation slope and the N-trend of the saturation round. Throttled, pure-python, N≤5.

**Result (numbers):**
- All three proxies trace a **smooth ramp → plateau**, not a cliff. BDD-nodes rise from 1 to a max (~93/124/94 at N=3/4/5), saturating around r≈10–14, then wobble flat.
- Pre-saturation BDD slope +6.6 to +12.1 nodes/round; **post-saturation slope ≈ 0** (+0.29, +0.15, −0.30) — a leveling-off, not a discontinuity.
- The "knee" = the diffusion-saturation shoulder; its round is **r≈10–14 and does NOT climb toward 60 as N grows** (10→11→14 is the mixing depth, essentially flat).
- "Sharpness" (max|2nd-diff|/mean|1st-diff|) ≈ 5–8 — the curvature of a smooth saturating ramp, not a cliff.

**Kill_criterion:** "smooth/monotone, no knee, OR knee independent of round structure." — **fired? YES**

**Verdict reasoning:** The compressibility-vs-round curve is a smooth saturating ramp. Its only feature is the shoulder where the active differential finishes diffusing (compressibility maxes out), after which the proxy is flat — there is no cliff and no "shortcut suddenly fails" event. Crucially the shoulder round does not scale toward 60 with N; it tracks a fixed mixing depth and is **independent of the sr=60/61 round structure**. Both disqualifying clauses of the kill criterion fire. This adds a sixth+ instance to the project-wide pattern that every claimed "cliff at 60/61" dissolves into smooth saturation / free-word bookkeeping.

**Cross-check / skeptic note:** Three independent compressibility measures (LZMA, ROBDD, greedy cover) agree on the smooth-ramp shape, so the verdict isn't an artifact of one proxy. The honest caveat the card itself raises — "the N=32 knee may be invisible at N=4" — is partially valid: a cliff at literal round 60 cannot be directly observed at N≤5. But the test was about whether a knee EXISTS and whether its round MOVES with N (extrapolatable toward 60); both fail (no sharp knee; shoulder fixed at the mixing depth). To revive this, one would need a proxy showing a knee whose round demonstrably climbs toward 60 across a range of N — the opposite of what's measured.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W3-CR3.py`
