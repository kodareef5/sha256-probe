# W4-CS1 — The 132 hard-core = do-orphans of the cascade mutilation   ·   VERDICT: KILLED

**Card claim:** the cascade replaces M2's free edges with M2:=cascade(M1) — exactly Pearl's do()-surgery on the twin-world difference DAG. A *do-orphan* = an output-diff bit whose every path-in is severed (no admissible *exogenous* do() can move it) → conjecturally the 132 (124 reachable → HW~74).

**Probe run:** Full-width N=32 (the 132 is a 32-bit phenomenon; the card names "256" output bits). On the real cascade tail (rounds 57–63, carries included; lib.sha256 via shabridge) I computed TWO counts on the SAME machinery:
 - **(A) the card's actual object — DO-ORPHAN count:** on the twin-world difference DAG, an output-diff bit is "reached" iff SOME admissible exogenous intervention `do(W_j := v)` on the free tail words W[57..60] (single-word any-value AND joint random vectors) changes it vs baseline. Orphan = reached by NONE. 24 twin bases × (96 joint + 32 single-word) interventions each, re-run on a second independent base-set for stability.
 - **(B) control foil — the repo's deterministic-control census** (W2-CT1 protocol, single path's round-63 register output, 80 base-points): bit "hard" iff no single free-bit flip flips it at every base.

**Result (numbers):**
 - **(A) do-orphan count = 0 / 256** (a,b,e,f = 0/128). **Stable: 0 on the independent base-set too.** Every single output-diff bit is moved by *some* exogenous intervention.
 - **(B) census-hard = 132 / 256**, support exactly {a,b,e,f}@63 = 128 + 4 scattered dc bits — reproduces the repo ground truth 132 perfectly (the foil works).

**Kill_criterion:** "orphan count ↛ 132 (≈0/256) or wildly intervention-set-dependent." — **fired? YES.** The genuine do-orphan count is 0/256, the literal "≈0/256" miss case named in the kill.

**Verdict reasoning:** KILLED, and it is the exact same **category error** the canonical corank card W2-CT1 already nailed (genuine reachability corank = 0/128, never 132). A *real* causal-intervention-orphan count — "is there ANY exogenous do() that moves this output-diff bit?" — is **0**, because the free tail words feed a,b,e,f through the nonlinear T1+T2 and *some* intervention always perturbs every bit. The 132 exists ONLY in the strictly weaker **single-bit deterministic-control census** (no *single* lever moves the bit *deterministically* at *every* base), which is exactly the sample-dependent carry-census number (132 in the writeup, 138 in a 48-base sample). CS1 relabels that census as "do-orphans" without computing an intervention-orphan set — a rename, not a mechanism.

**Cross-check / skeptic note:** The do-orphan = 0 result is robust: identical (0) across two disjoint random base-sets, and it follows necessarily from full controllability under exogenous interventions (W2-CT1's corank-0 finding, independently). The control arm (B=132 with {a,b,e,f}+4dc) proves the discrepancy is real and not a coding artifact — the SAME tail yields 132 under the census protocol and 0 under the do-orphan protocol. To CONFIRM, CS1 would have needed a stable 132-bit intervention-orphan set with {a,b,e,f}+4dc support; it produced 0 instead.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W4-CS1.py`
