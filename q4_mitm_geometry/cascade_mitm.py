#!/usr/bin/env python3
"""
Issue #13: MITM on the Two-Cascade Mechanism

We KNOW the sr=60 collision mechanism from the collision anatomy:
  Cascade 1: W[57] zeros the a-path (da57=0) → db58=0 → dc59=0 → dd59=0
  Cascade 2: W[60] zeros the e-path (de60=0) → df61=0 → dg62=0 → dh63=0

MITM decomposition:
  FORWARD:  enumerate W[57] values that make cascade 1 work
            (compute state at round 59 for each, store (dd59, de59, df59, dg59, dh59))
  BACKWARD: enumerate W[60] values that make cascade 2 work
            (compute backward from round 63 collision requirement)
  BRIDGE:   find (W[58], W[59]) pairs that connect forward and backward states
            through the schedule rule

This reduces the 2^128 brute search to forward(2^32) + backward(2^32) + bridge.

Phase 1 (this script): Forward enumeration. For each of 2^32 possible W1[57]
values, compute the state at round 59 and check if da57=0 (the cascade 1
requirement). Store all hits.
"""

import sys, os, time, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
from lib.sha256 import *


def forward_cascade1_enumerate(state1, state2, W1_pre, W2_pre,
                                sample_size=None, output_file=None):
    """
    For each W1[57] value, compute:
    1. What dW[57] is needed to make da57 = 0
    2. The resulting state at round 57 for both messages
    3. Whether the cascade naturally propagates (db58=0 from shift register is automatic)

    Since da57=0 requires a SPECIFIC dW[57] for each W1[57], we compute:
      dW[57] = -(dh56 + dSigma1(e56) + dCh(e56,f56,g56) + dSigma0(a56) + dMaj(a56,b56,c56))

    Wait — that's the additive condition. Let me think more carefully.

    At round 57:
      a57_msg1 = T1_1 + T2_1  where T1_1 = h56_1 + Sigma1(e56_1) + Ch(e56_1,f56_1,g56_1) + K[57] + W1[57]
      a57_msg2 = T1_2 + T2_2  where T1_2 = h56_2 + Sigma1(e56_2) + Ch(e56_2,f56_2,g56_2) + K[57] + W2[57]

    For da57 = 0: a57_msg1 = a57_msg2
    → T1_1 + T2_1 = T1_2 + T2_2

    Since da56=0 (candidate property): a56_1 = a56_2, so Sigma0 and Maj terms are equal → T2_1 = T2_2
    → T1_1 = T1_2
    → (h56_1 + Sigma1(e56_1) + Ch_1 + K + W1[57]) = (h56_2 + Sigma1(e56_2) + Ch_2 + K + W2[57])
    → W2[57] = W1[57] + (h56_1 - h56_2) + (Sigma1(e56_1) - Sigma1(e56_2)) + (Ch_1 - Ch_2)

    So for ANY W1[57], there's exactly ONE W2[57] that makes da57=0!
    """
    # Compute the constant offset: W2[57] = W1[57] + C
    dh = (state1[7] - state2[7]) & MASK
    dSig1 = (Sigma1(state1[4]) - Sigma1(state2[4])) & MASK
    dCh = (Ch(state1[4], state1[5], state1[6]) - Ch(state2[4], state2[5], state2[6])) & MASK
    C_w57 = (dh + dSig1 + dCh) & MASK

    print(f"Cascade 1 offset: W2[57] = W1[57] + 0x{C_w57:08x}")
    print(f"  dh56 = 0x{dh:08x} (hw={hw(dh)})")
    print(f"  dSigma1 = 0x{dSig1:08x} (hw={hw(dSig1)})")
    print(f"  dCh = 0x{dCh:08x} (hw={hw(dCh)})")
    print(f"\nEvery W1[57] value gives da57=0 with the corresponding W2[57].")
    print(f"This means cascade 1 is FREE — 2^32 choices, all valid.\n")

    # Now: for each W1[57], compute the full state at round 57
    # and measure what the e-path looks like (de57)
    print(f"Sampling forward states to characterize de57 distribution...")

    import random
    random.seed(42)
    n_samples = sample_size or 100000

    de57_hws = []
    best_de57_hw = 33
    best_w1_57 = None

    for trial in range(n_samples):
        if sample_size is None or sample_size > 2**32:
            w1_57 = trial  # exhaustive if small enough
        else:
            w1_57 = random.getrandbits(32)

        w2_57 = (w1_57 + C_w57) & MASK

        # Compute round 57 state for both messages
        T1_1 = add(state1[7], Sigma1(state1[4]), Ch(state1[4], state1[5], state1[6]),
                    K[57], w1_57)
        T2_1 = add(Sigma0(state1[0]), Maj(state1[0], state1[1], state1[2]))
        a57_1 = add(T1_1, T2_1)
        e57_1 = add(state1[3], T1_1)

        T1_2 = add(state2[7], Sigma1(state2[4]), Ch(state2[4], state2[5], state2[6]),
                    K[57], w2_57)
        T2_2 = add(Sigma0(state2[0]), Maj(state2[0], state2[1], state2[2]))
        a57_2 = add(T1_2, T2_2)
        e57_2 = add(state2[3], T1_2)

        # Verify da57=0
        assert a57_1 == a57_2, f"da57!=0 at W1[57]=0x{w1_57:08x}"

        de57 = e57_1 ^ e57_2
        de57_hw_val = hw(de57)
        de57_hws.append(de57_hw_val)

        if de57_hw_val < best_de57_hw:
            best_de57_hw = de57_hw_val
            best_w1_57 = w1_57

            # Full state at round 57
            st57_1 = (a57_1, state1[0], state1[1], state1[2],
                      e57_1, state1[4], state1[5], state1[6])
            st57_2 = (a57_2, state2[0], state2[1], state2[2],
                      e57_2, state2[4], state2[5], state2[6])

            total_hw = sum(hw(st57_1[r] ^ st57_2[r]) for r in range(8))
            if trial < 100 or de57_hw_val < 15:
                print(f"  [{trial}] W1[57]=0x{w1_57:08x}: de57=0x{de57:08x} (hw={de57_hw_val}), "
                      f"total_hw={total_hw}")

    # Distribution analysis
    import collections
    hw_dist = collections.Counter(de57_hws)
    mean_hw = sum(de57_hws) / len(de57_hws)
    min_hw = min(de57_hws)
    max_hw = max(de57_hws)

    print(f"\nde57 distribution over {n_samples} samples:")
    print(f"  min={min_hw}, max={max_hw}, mean={mean_hw:.1f}")
    print(f"  Best: W1[57]=0x{best_w1_57:08x} with de57 hw={best_de57_hw}")

    print(f"\n  hw  count   pct")
    for h in sorted(hw_dist.keys()):
        pct = 100 * hw_dist[h] / n_samples
        bar = '#' * int(pct)
        if pct > 0.1:
            print(f"  {h:2d}  {hw_dist[h]:6d}  {pct:5.1f}%  {bar}")

    # For the MITM: we want W1[57] values where de57 is LOW (easier for cascade 2)
    low_de57 = [(h, c) for h, c in hw_dist.items() if h <= best_de57_hw + 2]
    n_low = sum(c for _, c in low_de57)
    print(f"\n  W1[57] values with de57 hw ≤ {best_de57_hw + 2}: "
          f"{n_low}/{n_samples} ({100*n_low/n_samples:.2f}%)")
    print(f"  At 2^32 scale: ~{int(n_low/n_samples * 2**32)} forward hits to store")

    return C_w57, best_w1_57, best_de57_hw


if __name__ == "__main__":
    n_samples = int(sys.argv[1]) if len(sys.argv) > 1 else 1000000

    M1 = [0x17149975] + [0xffffffff] * 15
    M2 = list(M1)
    M2[0] ^= 0x80000000
    M2[9] ^= 0x80000000

    state1, W1_pre = precompute_state(M1)
    state2, W2_pre = precompute_state(M2)

    print(f"MITM Cascade Forward Enumeration")
    print(f"Candidate: M[0]=0x17149975, N=32")
    print(f"Samples: {n_samples}\n")

    C_w57, best_w1, best_hw = forward_cascade1_enumerate(
        state1, state2, W1_pre, W2_pre, sample_size=n_samples)
