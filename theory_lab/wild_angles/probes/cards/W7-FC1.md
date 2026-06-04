# W7-FC1 — The 132 = the meet-irreducibles of the output-agreement lattice   ·   VERDICT: KILLED

**Card claim:** Objects = message pairs, attributes = "output bit b agrees"; controlled bits (dd,dg,dh) agree as the *meet* of upstream agreements (meet-REDUCIBLE), hard-core bits (da,db,de,df + 4 dc; zero controllers) are meet-IRREDUCIBLE; so 132 = the meet-irreducible rank of the output-agreement lattice, concentrated on {da,db,de,df}, fraction → 132/256.

**Probe run:** N=4, N=8 (N=6 has no cascade-eligible M0 in the standard mini-SHA kernel), throttled (`OMP_NUM_THREADS=2 taskpolicy -b`). Built the 8N-column round-63 output-agreement context over ~280 same-kernel message pairs (cascade near-collisions + random free-word pairs, da pinned 0 each round 57-60, schedule tail 61-63). CLARIFIED + REDUCED the attribute side (standard FCA attribute reduction): an attribute is meet-REDUCIBLE iff its object-extent equals the intersection (meet) of the strictly-larger extents containing it. Counted & named the surviving meet-IRREDUCIBLE attributes per register. 3 seeds each.

**Result (numbers):** Bit-exactly stable across all 3 seeds at each N:

| N | objs | 8N | meet-IRR attrs | per-register breakdown | census 4N+4 |
|---|---|---|---|---|---|
| 4 | ~277 | 32 | **23** | a4 b4 **c4** d**0** e4 f4 **g3** h**0** | 20 |
| 8 | ~280 | 64 | **47** | a8 b8 **c8** d**0** e8 f8 **g7** h**0** | 36 |

- Meet-irreducible count = **6N − 1** (23 at N=4, 47 at N=8) — width-scaling, NOT 4N+4 and NOT 132.
- The irreducibles are **{a,b,c,e,f} fully + g (N−1 of N)**. Register **c is fully meet-irreducible** and **g is (N−1)/N irreducible** — both are exactly the "dg/dc appear" / "spread" condition.
- Only **d and h are fully meet-REDUCIBLE** (extent = intersection of others): dd and dh are the cascade-controlled tail registers, so they alone collapse as meets. dg does NOT collapse.
- Fraction = (6N−1)/8N → **0.75**, not 0.5 (=132/256).

**Kill_criterion:** "irreducibles not concentrated on {da,db,de,df} (spread, or dd/dg/dh appear)" — **fired? YES.** dc is fully irreducible, dg is (N−1)/N irreducible; the irreducibles span 6 of 8 registers (6N−1), not the 4 hard-core registers.

**Verdict reasoning:** The lattice-closure notion (meet-irreducible attribute) and the linear notion (zero single-flip controller) do NOT coincide — exactly the skeptic's worry. The honest meet-irreducible attribute count is **6N−1** (width-scaling), the hard-core {a,b,e,f}=4N is only a *subset* of it, and the controlled registers dc (fully) and dg (mostly) are *also* meet-irreducible. So "132 = meet-irreducibles" is the prior-finding-#1 CATEGORY ERROR once more: there is no stable basis-independent 132 here; the count is 6N−1, fraction 0.75, and the irreducible support is the wrong set ({a,b,c,e,f,g} not {a,b,e,f}). The card's clean mechanism (controlled⇒reducible) is only half-true: dd, dh reduce (meet of upstream), but dg does not, and dc — claimed reducible — is fully irreducible.

**Cross-check / skeptic note:** Result is bit-identical across 3 random object samples at each N (sample-size-stable, addressing the card's stability worry) and scales cleanly as 6N−1 across N=4→8, ruling out a coincidental near-132. The d/h-collapse matches ground truth (dd, dh are the deepest cascade-shift registers, so their agreement IS the meet of upstream register agreements); the failure is dc and dg, which the card predicted reducible but measure irreducible. Converges with W6-MA1 / W2-CT1 / W6-OC3: every honest "132" object is a width-scaling census, never a stable invariant. To CONFIRM I would have needed meet-IRR = 4N+4 stable, concentrated on {a,b,e,f}; instead 6N−1, spread over {a,b,c,e,f,g}.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W7-FC1.py`
