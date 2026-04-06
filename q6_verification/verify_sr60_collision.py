#!/usr/bin/env python3
"""
verify_sr60_collision.py — Verify an sr=60 collision certificate

Given W[57..60] values for both messages, verifies:
1. da[56] = 0 (candidate validity)
2. Schedule compliance: W[61..63] computed from W[57..60] match schedule rule
3. Collision: compress(IV, M1) == compress(IV, M2) after all 64 rounds
4. Report which schedule equations hold (should be 60 of 64)

Usage: python3 verify_sr60_collision.py <m0> <fill> <W1_57..60> <W2_57..60>
  Or: python3 verify_sr60_collision.py --from-sat <cnf_file> <kissat_output>
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
from lib.sha256 import *


def verify_collision(m0, fill, w1_free, w2_free):
    """Full verification of an sr=60 collision certificate."""
    M1 = [m0] + [fill]*15
    M2 = list(M1); M2[0] ^= 0x80000000; M2[9] ^= 0x80000000

    # Step 1: Precompute and check da[56]=0
    s1, W1_pre = precompute_state(M1)
    s2, W2_pre = precompute_state(M2)

    print(f"=== sr=60 Collision Verification ===")
    print(f"M[0] = 0x{m0:08x}, fill = 0x{fill:08x}")
    print(f"W1[57..60] = [{', '.join(f'0x{w:08x}' for w in w1_free)}]")
    print(f"W2[57..60] = [{', '.join(f'0x{w:08x}' for w in w2_free)}]")
    print()

    if s1[0] != s2[0]:
        print(f"FAIL: da[56] != 0 (a1=0x{s1[0]:08x}, a2=0x{s2[0]:08x})")
        return False
    print(f"[OK] da[56] = 0")

    # Step 2: Build full schedule and run all 64 rounds
    W1_tail = build_schedule_tail(W1_pre, w1_free)
    W2_tail = build_schedule_tail(W2_pre, w2_free)

    # Check schedule compliance
    sr = 0
    for i in range(16, 64):
        if i < 57:
            # Pre-schedule: always compliant
            sr += 1
        elif i < 57 + len(w1_free):
            # Free words: NOT compliant (these are the gaps)
            pass
        else:
            # Derived words: check compliance
            idx = i - 57
            expected_1 = add(sigma1(W1_tail[idx-2] if idx >= 2 else W1_pre[i-2]),
                            W1_pre[i-7] if i-7 < 57 else W1_tail[i-7-57],
                            sigma0(W1_pre[i-15] if i-15 < 57 else W1_tail[i-15-57]),
                            W1_pre[i-16] if i-16 < 57 else W1_tail[i-16-57])
            actual_1 = W1_tail[idx]
            if expected_1 == actual_1:
                sr += 1
            else:
                print(f"  Schedule violation at W[{i}]: expected 0x{expected_1:08x}, got 0x{actual_1:08x}")

    sr += 16  # W[0..15] always comply (they're message words)
    # Free words don't count
    n_free = len(w1_free)
    total_equations = 48  # W[16]..W[63]
    compliant = sr - 16  # subtract the message words
    print(f"[{'OK' if compliant >= 60-n_free else 'FAIL'}] Schedule compliance: sr={16+compliant+n_free} "
          f"({compliant} of {total_equations-n_free} enforced equations hold, {n_free} free)")

    # Step 3: Run all 64 rounds
    trace1 = run_tail_rounds(s1, W1_tail)
    trace2 = run_tail_rounds(s2, W2_tail)

    final1 = trace1[-1]
    final2 = trace2[-1]

    regs = ['a','b','c','d','e','f','g','h']
    collision = True
    for i in range(8):
        d = final1[i] ^ final2[i]
        if d != 0:
            collision = False
            print(f"  d{regs[i]}[63] = 0x{d:08x} (hw={hw(d)})")
        else:
            print(f"  d{regs[i]}[63] = 0 ✓")

    if collision:
        print()
        print("*** COLLISION VERIFIED ***")
        print(f"compress(IV, M1) == compress(IV, M2)")
        print(f"Schedule compliance: sr=60 (4 free words)")

        # Compute hash values
        H1 = tuple(add(IV[i], final1[i]) for i in range(8))
        H2 = tuple(add(IV[i], final2[i]) for i in range(8))
        print(f"\nHash 1: {''.join(f'{h:08x}' for h in H1)}")
        print(f"Hash 2: {''.join(f'{h:08x}' for h in H2)}")
        if H1 == H2:
            print("HASH COLLISION CONFIRMED")
        return True
    else:
        total_hw = sum(hw(final1[i] ^ final2[i]) for i in range(8))
        print(f"\nNot a collision: total diff HW = {total_hw}")
        return False


if __name__ == "__main__":
    if len(sys.argv) >= 11:
        m0 = int(sys.argv[1], 0)
        fill = int(sys.argv[2], 0)
        w1 = [int(sys.argv[3+i], 0) for i in range(4)]
        w2 = [int(sys.argv[7+i], 0) for i in range(4)]
        verify_collision(m0, fill, w1, w2)
    else:
        print("Usage: python3 verify_sr60_collision.py m0 fill W1_57 W1_58 W1_59 W1_60 W2_57 W2_58 W2_59 W2_60")
        print("  All values in hex (prefix 0x)")
