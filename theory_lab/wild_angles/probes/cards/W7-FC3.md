# W7-FC3 — Duquenne–Guigues base → the wall is the one irreducible 2-premise rule   ·   VERDICT: KILLED

**Card claim:** The cascade's canonical implication base is all UNARY-premise through 60 (single-equation propagation); sr=61 is the FIRST implication with a 2-element pseudo-intent (g1=0 ∧ h=0 jointly) — the FCA twin of 2^-2N. Max premise size ticks 1→2 at the wall.

**Probe run:** N=8, N=10, 20000 sampled free-word objects each, throttled. Computed the Duquenne–Guigues stem base (Ganter next-closure over L-closed sets) over attributes {de_r=0 : r=57..61} ∪ {g1=0, h=0, SR61=(g1∧h)}. Read the premise-size histogram, the minimal premise forcing de61=0 and SR61, and whether any size-2 stem exists strictly below 61. Adversarial control (#4): a synthetic 2^-2N target TT=(P0 ∧ P1) built from two *unrelated* independent ~2^-N message-bit conditions.

**Result (numbers):** Identical at N=8 and N=10:
- Attribute densities: de57=de58=de59=0 *never* hold (extent 0), de60=0 *always* holds, de61=0 ≈ 2^-N (62/20000 at N=8), g1=0,h=0 ≈ 2^-N, SR61=(g1∧h) ≈ 2^-2N → **0 occurrences in 20000** at both N.
- DG premise-size histogram = **{0:1, 2:4, 3:3}** — there are **no size-1 stems at all**; max premise size = **3** at every round-depth. The "1→2 tick at the wall" never occurs.
- **Size-2 stems exist using ONLY below-61 attributes**: `{de57=0,de60=0}`, `{de58=0,de60=0}`, `{de59=0,de60=0}` — 2-premise implications strictly below the wall.
- "Minimal premise forcing SR61" = `{de60=0, SR61}` — circular (de60=0 is constant-true, so SR61 ∈ its own closure); no clean wall-specific 2-premise rule derives SR61.
- **Adversarial control fires**: the synthetic 2^-2N target gets stem `{P0=0, P1=0} ⇒ TT` (size 2), exactly like the wall — a size-2 premise is generic to any conjunction of two independent ~2^-N conditions.

**Kill_criterion:** "2-premise implications already appear below 60" — **fired? YES (both clauses).** Size-2 stems appear below 61 (de57/58/59=0 with de60=0), and the adversarial 2^-2N control also needs a size-2 stem, so the 1→2 tick is not localized at 60→61.

**Verdict reasoning:** The card's "max premise ticks 1→2 at the wall" does not hold. The premise-size histogram is {0,2,3} everywhere — never a clean 1 below and 2 at 61 — because the below-wall coordinate attributes (de57/58/59=0) are *constant* (empty extent), so they generate vacuous size-2 (and size-3) stems below the wall: exactly the card's own skeptic worry that "the base floods with size-2 everywhere, a modeling choice doing the work." More decisively, the adversarial control shows that ANY 2^-2N event = conjunction of two independent ~2^-N conditions gets a size-2 stem; so "the wall is a 2-premise rule" is just a restatement of prior finding #3 (2^-2N = two independent conditions g1,h), not a new localization or prediction. The implication base does not single out round 60→61.

**Cross-check / skeptic note:** The result is granularity-driven exactly as the skeptic predicted — at the per-round-scalar granularity the below-wall constants flood the base with degenerate size-2/3 stems, and at any granularity a 2^-2N target needs a size-2 stem. Identical at N=8 and N=10 (verdict not a sample artifact). Converges with W7-FC2 (the wall = generic chain→square step) and RESULT_sr61_is_2minus2N.md (g1⊥h is the only feature). No NEW number or prediction emerges (per the rename-watch rule), so even the half-true part (sr=61 *is* a 2-condition event) cannot upgrade this to CONFIRMED. To CONFIRM I would have needed a base that is genuinely all-unary ≤60 and acquires its FIRST size-2 stem at 61, with the control staying unary; instead size-2 stems are everywhere and the control matches the wall.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W7-FC3.py`
