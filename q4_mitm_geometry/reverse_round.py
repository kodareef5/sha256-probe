#!/usr/bin/env python3
"""
reverse_round.py — Issue #22: Reverse-direction analysis.

SHA-256 compression rounds are bijective given W. We can invert them.
Forward:
  T1 = h + Sigma1(e) + Ch(e,f,g) + K + W
  T2 = Sigma0(a) + Maj(a,b,c)
  a' = T1 + T2
  b' = a
  c' = b
  d' = c
  e' = d + T1
  f' = e
  g' = f
  h' = g

Inverse: given (a', b', c', d', e', f', g', h') and W:
  a = b'
  b = c'
  c = d'
  d = ?
  e = f'
  f = g'
  g = h'
  T1 = a' - T2 where T2 = Sigma0(a) + Maj(a, b, c) = Sigma0(b') + Maj(b', c', d')
  d = e' - T1
  h = T1 - Sigma1(e) - Ch(e, f, g) - K - W
    = T1 - Sigma1(f') - Ch(f', g', h') - K - W

So given the next state and W, we can invert one round. Starting from
(0,0,0,0,0,0,0,0) at round 64 (the collision target after IV addition),
invert backward through W[63], W[62], ..., W[57] for each message.

Forward MITM goes 56 → 63. Reverse MITM goes 63 → 56. The two paths
meet at round 59 or 60.

Reverse exploration: starting from a single point (collision = zero),
the search tree branches based on what W values we choose. Each W
gives a specific predecessor state. So reverse 7 steps from collision
gives us a 7-level tree of (state, W path) candidates.

This is structurally different from forward search because:
1. We start at one point (target collision) instead of 2^128 inputs
2. Each step is deterministic given W (bijection)
3. Branching is in W choice, not state choice
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
from lib.sha256 import K, MASK, Sigma0, Sigma1, sigma0, sigma1, Ch, Maj, hw, add, IV


def forward_round(state, W, round_idx):
    """One round forward: state, W -> new_state."""
    a, b, c, d, e, f, g, h = state
    T1 = (h + Sigma1(e) + Ch(e, f, g) + K[round_idx] + W) & MASK
    T2 = (Sigma0(a) + Maj(a, b, c)) & MASK
    new_a = (T1 + T2) & MASK
    new_e = (d + T1) & MASK
    return (new_a, a, b, c, new_e, e, f, g)


def reverse_round(new_state, W, round_idx):
    """One round backward: new_state, W -> old_state.
    Given (a', b', c', d', e', f', g', h') after round_idx, recover (a,b,c,d,e,f,g,h)."""
    new_a, new_b, new_c, new_d, new_e, new_f, new_g, new_h = new_state
    # Easy: a, b, c, e, f, g come from shift register
    a = new_b
    b = new_c
    c = new_d
    e = new_f
    f = new_g
    g = new_h
    # Compute T2 from recovered a, b, c
    T2 = (Sigma0(a) + Maj(a, b, c)) & MASK
    # T1 from new_a = T1 + T2
    T1 = (new_a - T2) & MASK
    # d from new_e = d + T1
    d = (new_e - T1) & MASK
    # h from T1 = h + Sigma1(e) + Ch(e, f, g) + K + W
    h = (T1 - Sigma1(e) - Ch(e, f, g) - K[round_idx] - W) & MASK
    return (a, b, c, d, e, f, g, h)


def verify_inverse():
    """Verify that reverse_round is the exact inverse of forward_round."""
    import random
    rng = random.Random(42)
    for trial in range(100):
        state = tuple(rng.randint(0, MASK) for _ in range(8))
        W = rng.randint(0, MASK)
        round_idx = rng.randint(0, 63)
        forward = forward_round(state, W, round_idx)
        recovered = reverse_round(forward, W, round_idx)
        if recovered != state:
            print(f"FAIL: state={state}, W={W:08x}, round={round_idx}")
            print(f"  forward={forward}")
            print(f"  recovered={recovered}")
            return False
    print("Inverse verified on 100 random states")
    return True


def reverse_path(start_state, W_sequence, start_round):
    """Apply reverse_round repeatedly. W_sequence applied in reverse order."""
    state = start_state
    for i, W in enumerate(W_sequence):
        round_idx = start_round - i
        state = reverse_round(state, W, round_idx)
    return state


def main():
    if not verify_inverse():
        return

    # Now: start from the collision endpoint and reverse 7 rounds back
    # The "collision" at round 63 in differential terms is (0,0,0,0,0,0,0,0)
    # for both messages. But we need ABSOLUTE state, not differential.
    #
    # For the verified sr=60 cert: at round 63, state1 = state2.
    # The actual values depend on the cert's W[57..63]. Let me compute them.

    from lib.sha256 import precompute_state, build_schedule_tail, run_tail_rounds
    M0 = 0x17149975
    FILL = 0xFFFFFFFF
    M1 = [M0] + [FILL] * 15
    M2 = list(M1); M2[0] ^= 0x80000000; M2[9] ^= 0x80000000
    s1, W1_pre = precompute_state(M1)
    s2, W2_pre = precompute_state(M2)
    W1 = [0x9ccfa55e, 0xd9d64416, 0x9e3ffb08, 0xb6befe82]
    W2 = [0x72e6c8cd, 0x4b96ca51, 0x587ffaa6, 0xea3ce26b]
    W1_tail = build_schedule_tail(W1_pre, W1)
    W2_tail = build_schedule_tail(W2_pre, W2)
    t1 = run_tail_rounds(s1, W1_tail)
    t2 = run_tail_rounds(s2, W2_tail)
    final1 = t1[-1]
    final2 = t2[-1]
    print(f"Forward cert state at round 63 (M1): {[f'0x{w:08x}' for w in final1]}")
    print(f"Forward cert state at round 63 (M2): {[f'0x{w:08x}' for w in final2]}")
    print(f"Match: {final1 == final2}")

    # Now reverse from round 63 back to round 56 using cert's W[57..63]
    # W1_tail = [W57, W58, W59, W60, W61, W62, W63] for M1
    # We want to reverse: from state at round 63, apply W63 inverse, then W62, etc.

    print(f"\nReversing from round 63 back to round 56...")
    state_m1 = final1
    state_m2 = final2
    for i in range(7):
        round_idx = 63 - i
        w_m1 = W1_tail[6 - i]  # W[63] first
        w_m2 = W2_tail[6 - i]
        state_m1 = reverse_round(state_m1, w_m1, round_idx)
        state_m2 = reverse_round(state_m2, w_m2, round_idx)

    print(f"Recovered state at round 56 (M1): {[f'0x{w:08x}' for w in state_m1]}")
    print(f"Recovered state at round 56 (M2): {[f'0x{w:08x}' for w in state_m2]}")
    print(f"Original state at round 56 (M1): {[f'0x{w:08x}' for w in s1]}")
    print(f"Match M1: {state_m1 == s1}")
    print(f"Match M2: {state_m2 == s2}")


if __name__ == "__main__":
    main()
