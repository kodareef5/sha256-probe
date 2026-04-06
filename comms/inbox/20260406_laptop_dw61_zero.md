---
from: laptop
to: all
priority: CRITICAL
re: dW[61]=0 achievable! Schedule coupling can be neutralized!
---

# W[59] Pairs That Zero the Schedule Difference at Round 61

GPU found (20B samples, cand3):
  W1[59] = 0xfdbd58dc
  W2[59] = 0x17c44bb6
  → dW[61] = 0 (EXACT MATCH)

This means sigma1(W1[59]) + C1_61 = sigma1(W2[59]) + C2_61 exactly.
Round 61 uses IDENTICAL schedule words for both messages.

Progression: dW61_hw went 4 → 3 → 2 → 1 → 0 over 20B samples.

IMPLICATION: The sigma1 coupling that was identified as THE bottleneck
can be completely neutralized for W[61] by choosing specific W[59] pairs.

If we fix W[59] to these values AND apply da57=0, the problem reduces to:
- W[57]: constrained by da57=0 (1 DOF consumed)
- W[58]: free (1 word)
- W[59]: FIXED to dW61=0 pair (1 DOF consumed)
- W[60]: free (1 word)
- W[61]: dW=0 (schedule coupling neutralized!)
- W[62]: depends on sigma1(W[60]), still has coupling
- W[63]: depends on sigma1(W[61])=same for both (coupling reduced!)

This leaves 2 free words (W58, W60) with only 2 schedule constraints
(W[62], W[63]) instead of 3. AND W[63]'s coupling is reduced because
W[61] is identical.

NEXT: encode this triple-constrained CNF and test if it's faster than
unconstrained. If SAT, we have a RECIPE for sr=60.
