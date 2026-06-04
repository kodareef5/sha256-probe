# W5-ER1 — Davies–Meyer ground node → 132 = high-resistance (recompute) registers   ·   VERDICT: KILLED

**Card claim:** Make the message-input layer the electrical ground; controllability = 1/R_eff-to-ground. The recompute registers {da,db,de,df}+4dc @63 are screened from input by the T1+T2 carry-bottleneck (long thin resistor ⇒ HIGH R_eff ⇒ hard-core); pass-through registers {dd,dg,dh} wire near-directly to earlier a/e (LOW R_eff). Top-132 R_eff bits should = the named recompute set.

**Probe run:** N=8,10,12, throttled. Built the genuine round×register-bit resistor network over the real modular tail (rounds 57→63, carries included): one node per register-bit at each tail-round state, plus a single GROUND node = the message-input (free-schedule) layer. Edge conductances measured by avalanche census — ground→layer-1 from free-input-bit flips, layer→layer from single-bit single-round recompute flips. L⁺ = `np.linalg.pinv(Laplacian)`; R_eff(out63-bit, ground) = L⁺_uu + L⁺_gg − 2L⁺_ug. Ranked all 8N round-63 bits; AUC of R_eff as a classifier for {a,b,e,f} vs {d,g,h}.

**Result (numbers):** The partition is **exactly inverted** from the card, at all three N:

| N | mean R_eff {a,b,e,f} (recompute) | mean R_eff {d,g,h} (passthru) | GAP (rec−pass) | AUC | top-4N frac in {a,b,e,f} |
|---|---|---|---|---|---|
| 8  | 5.238 | 6.106 | **−0.867** | **0.000** | 0.000 |
| 10 | 4.179 | 5.046 | **−0.867** | **0.000** | 0.000 |
| 12 | 3.571 | 4.453 | **−0.882** | **0.000** | 0.000 |

The recompute registers a,e have the **lowest** R_eff (da[63]=3.07, de[63]=3.11 at N=12); the pass-through dd[63]=4.64 is **highest**. Perfect anti-ranking (AUC=0.000), stable across N.

**Kill_criterion:** "top-132 overlap ≤ chance (AUC ≤ 0.55) at N=12, or no recompute/pass-through R_eff gap." — **fired? YES (both clauses).** AUC=0.000 ≤ 0.55 at N=12, and the gap is negative (recompute is LOW resistance, not high).

**Verdict reasoning:** KILLED, and not merely null — the effective-resistance-to-ground ordering is the **reverse** of the card's mechanism. Mechanistically clear: registers a and e are *written fresh* by each round's T1/T2, so a single-bit perturbation of the immediately-preceding state couples to them through many short paths (low R_eff); the pass-through registers d,g,h only inherit a value via the shift one extra hop away (higher R_eff). The "long thin resistor screening the recompute registers" picture is upside-down. There is no stable-132 high-resistance set — consistent with prior finding #1 (a real network/resistance partition does NOT reproduce the 132 census; that number is only the single-bit deterministic-control census, which is a different, sample-dependent object).

**Cross-check / skeptic note:** The card's own skeptic warned R_eff might just echo a raw sensitivity column-sum; here even that fear is moot because the *direction* is wrong. One could object that restricting graph nodes to N active lanes (vs full 32-bit) loses the named dc-scatter — true, but the discriminating question is the register-LEVEL recompute-vs-passthru split, and that is cleanly inverted at every N. Convergence with the W2-CT1 finding (132 is the deterministic-control census, not a linear/structural invariant) is strong corroboration. No reasonable reweighting flips a 0.000 AUC to >0.55.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W5-ER1.py`
