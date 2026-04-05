#!/usr/bin/env python3
"""
signed_diff_model.py — Signed-difference trail search for sr=60

Instead of encoding concrete bit values (like our CNFBuilder), this models
SIGNED DIFFERENCES at each bit position. Following Li et al. (EUROCRYPT 2024):

  Difference symbols:
    '=' : both bits equal (0,0) or (1,1) — zero XOR difference
    'x' : bits differ (0,1) or (1,0) — one XOR difference
    '0' : both zero
    '1' : both one
    'u' : first=1, second=0 (positive difference)
    'n' : first=0, second=1 (negative difference)
    '?' : unknown

Each symbol is encoded as 2 binary variables (v, d):
    '?' = (v=?, d=?)  — no constraint
    '=' = (d=0)       — difference is zero
    'x' = (d=1)       — difference is nonzero
    '0' = (v=0, d=0)  — value 0, no difference
    '1' = (v=1, d=0)  — value 1, no difference
    'u' = (v=1, d=1)  — value 1, differs
    'n' = (v=0, d=1)  — value 0, differs

For the sr=60 problem:
  - Round-56 state is KNOWN (constants from precomputation)
  - Free words W[57..60] are UNKNOWN (the search target)
  - W[61..63] are schedule-determined (functions of W[57..60] + constants)
  - Collision requires final state difference = 0

The trail search finds: what pattern of signed differences through
rounds 57-63 is MAXIMALLY SPARSE (minimum Hamming weight of 'x' symbols)
while being consistent with the schedule constraints and collision requirement?

A sparse trail means fewer active bits, which means a conforming pair
search has a much smaller effective search space.
"""

import sys, os, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
from lib.sha256 import *


def analyze_state56_diffs(m0=0x17149975, fill=0xffffffff):
    """Compute the signed differences at round 56 for a given candidate.

    Since state56 is fully determined by the message, we know the exact
    value of each bit in both messages. This means every state56 bit has
    a known signed difference: '0', '1', 'u', or 'n'.
    """
    M1 = [m0] + [fill]*15
    M2 = list(M1); M2[0] ^= 0x80000000; M2[9] ^= 0x80000000

    s1, W1 = precompute_state(M1)
    s2, W2 = precompute_state(M2)

    assert s1[0] == s2[0], f"da[56] != 0"

    regs = ['a','b','c','d','e','f','g','h']

    print(f"State-56 signed differences for M[0]=0x{m0:08x}, fill=0x{fill:08x}")
    print(f"{'='*70}")

    total_active = 0  # total bits with nonzero difference
    total_zero = 0    # total bits with zero difference

    for r in range(8):
        v1, v2 = s1[r], s2[r]
        diffs = []
        active = 0
        for bit in range(32):
            b1 = (v1 >> bit) & 1
            b2 = (v2 >> bit) & 1
            if b1 == 0 and b2 == 0:
                diffs.append('0')
            elif b1 == 1 and b2 == 1:
                diffs.append('1')
            elif b1 == 1 and b2 == 0:
                diffs.append('u')
                active += 1
            else:  # b1 == 0, b2 == 1
                diffs.append('n')
                active += 1

        total_active += active
        total_zero += (32 - active)

        # Display MSB first (bit 31 on left)
        diff_str = ''.join(reversed(diffs))
        print(f"  d{regs[r]}[56] = {diff_str}  (active={active}/32)")

    print(f"\n  Total: {total_active} active bits, {total_zero} zero bits out of 256")
    print(f"  Note: da[56] has 0 active bits (da[56]=0 requirement)")

    # Also analyze schedule word differences
    print(f"\nSchedule word differences (key words for tail):")
    key_indices = [45, 46, 47, 48, 54, 55, 56]
    for i in key_indices:
        d = W1[i] ^ W2[i]
        active = hw(d)
        print(f"  dW[{i}]: active={active}/32, diff=0x{d:08x}")

    return s1, s2, W1, W2


def count_trail_constraints():
    """Count the degrees of freedom vs constraints in the sr=60 trail.

    This helps understand why a trail search might succeed:
    - How many bits are free (unknown differences)?
    - How many are constrained (by schedule, collision, propagation)?
    """
    print(f"\nsr=60 Trail Constraint Analysis")
    print(f"{'='*70}")

    # Free variables: 4 schedule words × 32 bits × 2 messages = 256 free bits
    # But in signed-diff model: 4 words × 32 bits × 2 vars (v,d) = 256 vars per message
    # Total: 512 signed-diff variables for the 4 free words

    # Collision constraint: 8 registers × 32 bits = 256 bits must have d=0

    # Schedule constraints: W[61..63] determined by W[57..60] + constants
    # That's 3 × 32 = 96 bits of constraint

    print(f"  Free words: W[57..60] = 4 × 32 = 128 bits per message")
    print(f"  In signed-diff: 4 × 32 × 2 vars = 256 signed-diff vars per msg")
    print(f"  Total free signed-diff vars: 512")
    print(f"")
    print(f"  Schedule constraints (W[61..63]):")
    print(f"    W[61] = σ1(W[59]) + W[54] + σ0(W[46]) + W[45]")
    print(f"    W[62] = σ1(W[60]) + W[55] + σ0(W[47]) + W[46]")
    print(f"    W[63] = σ1(W[61]) + W[56] + σ0(W[48]) + W[47]")
    print(f"    = 3 × 32 = 96 constrained bits per message")
    print(f"")
    print(f"  Collision constraint: all 8 final registers equal")
    print(f"    = 8 × 32 = 256 bits of d=0 constraints")
    print(f"")
    print(f"  Compression rounds: 7 rounds × ~350 gates = ~2450 propagation constraints")
    print(f"")
    print(f"  Effective slack: 512 free - 256 collision - 96 schedule = 160 bits")
    print(f"  But Li et al. showed that with sparsity optimization,")
    print(f"  the conforming pair search becomes easy when the trail is fixed.")
    print(f"")
    print(f"  KEY QUESTION: Does a SPARSE trail exist that satisfies all")
    print(f"  propagation rules through 7 rounds while reaching d=0 collision?")
    print(f"  If yes → sr=60 is feasible. If no → it's fundamentally impossible")
    print(f"  for this candidate.")


def enumerate_round57_diff_patterns():
    """Explore what happens at round 57 in the signed-difference model.

    Round 57 takes:
      State: (a56, b56, c56, d56, e56, f56, g56, h56) — all known signed diffs
      Schedule: W[57] — UNKNOWN (free)
      Constant: K[57] — known value

    Computes:
      T1 = h56 + Σ1(e56) + Ch(e56,f56,g56) + K[57] + W[57]
      T2 = Σ0(a56) + Maj(a56,b56,c56)
      New state: (T1+T2, a56, b56, c56, d56+T1, e56, f56, g56)

    In signed-diff model:
      - Σ0, Σ1 are bitwise (XOR + rotation) → signed diff propagates exactly
      - Ch, Maj are bitwise → signed diff propagates exactly
      - Addition is where carries create uncertainty

    The question is: how many bits of the new state have DETERMINED
    signed differences (= or x) vs UNKNOWN (?)?
    """
    print(f"\nRound 57 Signed-Difference Propagation")
    print(f"{'='*70}")

    # Since da[56]=0, the a-path (T2) has important simplifications:
    # Σ0(a56): since da56=0, dΣ0(a56)=0 (all zero diff)
    # Maj(a56,b56,c56): da56=0, so Maj diff depends only on db56, dc56

    print(f"  Since da[56]=0:")
    print(f"    dΣ0(a56) = 0 (rotation/XOR of zero diff = zero diff)")
    print(f"    dMaj depends on db56, dc56 only (a56 is equal in both messages)")
    print(f"    dT2 = dΣ0(a56) + dMaj = 0 + dMaj = dMaj(b56,c56)")
    print(f"")
    print(f"  For the e-path:")
    print(f"    dΣ1(e56) is determined (e56 values are known)")
    print(f"    dCh(e56,f56,g56) is determined (all values known)")
    print(f"    dT1 = dh56 + dΣ1(e56) + dCh + dK[57] + dW[57]")
    print(f"         = (known) + (known) + (known) + 0 + dW[57]")
    print(f"         = C_known + dW[57]")
    print(f"")
    print(f"  New state after round 57:")
    print(f"    a57 = T1 + T2 → diff = dT1 + dT2 = (C_known + dW[57]) + dMaj")
    print(f"    b57 = a56     → diff = 0 (da56=0!)")
    print(f"    c57 = b56     → diff = db56 (known)")
    print(f"    d57 = c56     → diff = dc56 (known)")
    print(f"    e57 = d56+T1  → diff = dd56 + dT1 = dd56 + C_known + dW[57]")
    print(f"    f57 = e56     → diff = de56 (known)")
    print(f"    g57 = f56     → diff = df56 (known)")
    print(f"    h57 = g56     → diff = dg56 (known)")
    print(f"")
    print(f"  INSIGHT: After round 57, 6 of 8 registers have KNOWN diffs!")
    print(f"  Only a57 and e57 depend on the free word W[57].")
    print(f"  And b57 = 0 (zero diff) — this is the 'register zeroing' pattern.")
    print(f"")
    print(f"  For the collision to succeed, we need all 8 final diffs = 0.")
    print(f"  The register shift means b57→c58→d59→[absorbed into e60 via d+T1].")
    print(f"  Since b57=0, this 'zero' propagates forward for 3 rounds before")
    print(f"  being absorbed. This is the mechanism the collision relies on.")


if __name__ == "__main__":
    s1, s2, W1, W2 = analyze_state56_diffs()
    count_trail_constraints()
    enumerate_round57_diff_patterns()

    print(f"\n{'='*70}")
    print(f"NEXT STEP: Build SAT model over signed differences")
    print(f"  1. Encode propagation rules for each SHA-256 operation")
    print(f"  2. Add schedule constraints (W[61..63] from W[57..60])")
    print(f"  3. Add collision constraint (all final diffs = '=' )")
    print(f"  4. Minimize Hamming weight of active bits")
    print(f"  5. If a sparse trail exists → encode conforming pair with trail constraints")
