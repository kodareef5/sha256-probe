# W4-CS4 — Counterfactual rigidity → the plateau as a stable attractor   ·   VERDICT: KILLED

**Card claim:** for a found collision, a message bit is *rigid* if do(flip) keeps output-diff HW low; collisions sit at counterfactually-rigid configs; the **output-side rigid set = CS1's do-orphans (132)**, residual = 74 — a fixed point of the unit-intervention operator. Probe: rigid-bit fraction of collisions vs matched near-miss (elevated?); output-side rigid set → 132 and = CS1's do-orphans?

**Probe run:** Mini-SHA cascade at N=8 (IG3/gap machinery; rotations scaled exactly), found-collision set = the fresh N=8 CSV `/tmp/run_g8/gap_rows.csv` (260 rows, all verified HW=0). Three measurements: (1) INPUT-side rigid-fraction (lever-bit flips keeping out-diff HW ≤ 2) for collisions vs matched random near-misses; (2) OUTPUT-side rigid set = output bits that stay 0 across ALL lever flips of ALL collisions; (3) cross-check vs CS1's do-orphan set (= 0).

**Result (numbers):**
 - **INPUT-side rigidity NOT elevated:** collisions mean rigid-fraction = 0.0016, random near-miss = 0.0000, **delta = +0.0016** (essentially zero — avalanche makes nearly every lever flip brittle, exactly the skeptic's worry).
 - **OUTPUT-side rigid set = 16/64 = 0.250** (NOT 0.516/132). Support = **d = 8/8, h = 8/8**, all other registers 0/8. The frozen-at-0 output bits are the **cascade-locked pass-through registers (dd, dh)** — the *complement* of the hard core {a,b,e,f}.
 - **CS1 cross-check:** CS4 output-rigid fraction 0.250 vs CS1 do-orphan fraction 0.000 — **do not coincide.**

**Kill_criterion:** "no elevated rigidity, or the rigid set unrelated to 132 / disagrees with CS1 (must coincide)." — **fired? YES (all three clauses).**

**Verdict reasoning:** KILLED, and the failure is an **inversion** (the same shape as CS2). (i) Rigidity is **not** elevated for collisions — the input-side rigid-fraction is ~0 for both collisions and near-misses, so counterfactual rigidity does not single out collisions. (ii) The genuinely rigid (frozen-at-0) output set is **{d, h}** — the cascade-controlled pass-through slots — which is the **exact complement** of the card's claimed {a,b,e,f} hard core, and is 16/64 (0.25), nowhere near 132/256. (iii) It disagrees with CS1's do-orphans (0). The card conflates "frozen output bit" (stays 0 = the *controlled* d,h side, what's measured here) with "hard-core/uncontrollable bit" (the 132 = a,b,e,f) — these are complementary sets, so the identification is backwards. The plateau is real (Binomial over the ~132 free bits, per priors), but it is NOT a counterfactual-rigidity attractor in the card's sense.

**Cross-check / skeptic note:** The {d,h}-freeze is structural, not a threshold artifact: dd60 and dh63 are pass-through shift-register slots locked to 0 by the cascade/collision (the recompute-vs-passthrough wiring noted in the catalog's ER1 seed), so they cannot move under any tail-lever flip — hence "rigid." Raising or lowering the HW≤2 bar would not promote a,b,e,f into the rigid set (they respond to *some* lever, consistent with CS1's 0 orphans). The non-elevation result is robust (delta ≈ 0). CS4 cross-checks CS1 and *confirms CS1's verdict in reverse*: because do-orphans are 0, no rigid set of size 132 can coincide with them.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W4-CS4.py`
