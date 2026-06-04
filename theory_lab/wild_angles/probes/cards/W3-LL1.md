# W3-LL1 — LLL slack crossing → the boundary as e·p(d+1)=1   ·   VERDICT: SURVIVES (but fit, not predicted)

**Card claim:** One bad event per round (unlikely-to-fail given the freedom, sparse dependency from taps {2,7,15,16}); LLL guarantees a collision when S=e·p·(d+1)≤1. Conjecture: slack <1 through sr=60, ≥1 at sr=61.

**Probe run:** N=8,10, throttled (OMP=2, taskpolicy -b), 2000 conditioned prefixes each. Width-N validated mini-SHA round (`transfer_operator._make_round`), msg-2 = MSB-flip cascade kernel so a genuine de-difference exists. Static dependency degree d_sr computed from the tap graph {2,7,15,16}. Per-round bad-event probability p_sr measured under the cascade-conditioned measure: FREE rounds 57–60 (an attacker word exists → de(sr) is affine in W[sr] → solvable, residual p=2^-N) vs DETERMINED rounds 61–63 (word forced by the recurrence → de=0 only by coincidence → p=1−2^-N).

**Result (numbers):**
- Tap-graph degrees are tiny and flat: d_sr ∈ {1,2} for sr=58..63 (max d=2).
- S(sr)=e·p·(d+1): **S(58,59,60)=0.021,0.032,0.032** (FREE, p=2^-N); **S(61,62,63)=8.12,5.42,5.42** (DETERMINED, p≈1). At N=10: S(60)=0.0080, S(61)=8.15.
- **S does cross 1 exactly at the 60→61 step** (S(60)≪1<S(61)) at both N. Measured p_bad confirms the model: ~0 on free rounds, 0.996–0.998 on determined rounds. Bound is NOT vacuous (p≠1 on free rounds).
- **Skeptic decisive test:** the crossing location is **invariant to d** — set d=0,1,5,50 and the crossing still sits at the free→determined boundary every time (S_free=e·2^-N·(d+1)≪1 for any plausible d at N≥8; S_det=e·(1−2^-N)·(d+1)>1 for d≥0). The tap-graph degree contributes nothing to *where* the crossing lands.

**Kill_criterion:** "Dead if no crossing, or p≈1 makes the bound vacuous everywhere." — **fired? no** (a crossing exists at 60→61; p is 2^-N on free rounds, not vacuous).

**Verdict reasoning:** The literal kill criterion does NOT fire — S genuinely crosses 1 at 60→61 and the bound is non-vacuous — so this SURVIVES the card's own falsification test. **But the crossing is FIT, not predicted** (lead guidance #1): it is driven entirely by p jumping 2^-N→≈1 at the round where the cascade's 4 free tail words (W[57..60]) run out, and it is **independent of the LLL ingredients** — d=0 through d=50 all place the crossing at the same step, so e·(d+1) and the tap graph {2,7,15,16} add zero falsifiable content. The "boundary at 60→61" is the construction's free-DOF cutoff relabeled as an LLL inequality. Were the cascade given 5 free tail words, the same algebra would put the "crossing" at 61→62. So the angle is *consistent* (not killed) but the LLL mechanism is a rename of "free words exhausted," not a derivation of the boundary from the dependency structure.

**Cross-check / skeptic note:** This is the same blind spot seen in RG1-A (no isostatic knee — the floppy(r) zero-crossing was the DOF/constraint counting midpoint, not a rigidity event) and W2-CT3 (no N=10 resonance). The free/determined cutoff is where every "boundary at 60" story bottoms out. What would upgrade SURVIVES→CONFIRMED: a version where the *dependency degree itself* (not the DOF count) moves the predicted boundary and that prediction matches data at a perturbed schedule — i.e. the tap graph doing real work. As stated it does not.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W3-LL1.py`
