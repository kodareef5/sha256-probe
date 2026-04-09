#!/usr/bin/env python3
"""
f2_linear_schedule.py — F_2-linear (carry-free) baseline of the schedule differential.

The MSB-kernel difference is dW[0]=0x80000000, dW[9]=0x80000000, rest 0.
Since these are XOR differences at the top bit, the F_2-linear propagation
(treating + as XOR, ignoring carries) gives a deterministic baseline dW[i]
sequence independent of M[0].

In reality, carries from + can either cancel or amplify bits. The empirical
distribution of hw_dW[56] is binomial(32,0.5) (mean 16, stdev 2.83), but
the F_2 baseline gives hw_dW[56] = 11.

Our verified sr=60 SAT candidate has hw_dW[56] = 7, which is BELOW the
F_2 baseline — meaning carries productively cancelled bits.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
from lib.sha256 import sigma0, sigma1, hw, MASK


def f2_linear_schedule():
    """Propagate dW through the schedule using XOR (F_2-linear)."""
    dW = [0] * 64
    dW[0] = 0x80000000
    dW[9] = 0x80000000
    for i in range(16, 64):
        # Treat + as XOR (ignore carries)
        dW[i] = sigma1(dW[i-2]) ^ dW[i-7] ^ sigma0(dW[i-15]) ^ dW[i-16]
    return dW


def main():
    dW = f2_linear_schedule()

    print("=== F_2-linear schedule differential (carry-free baseline) ===\n")
    print("Initial: dW[0] = dW[9] = 0x80000000\n")

    print(f"{'i':<5} {'dW[i]_F2':<15} {'hw_F2':<8} {'binomial mean':<15}")
    print("-" * 50)
    for i in range(16, 64):
        print(f"{i:<5} 0x{dW[i]:08x}      {hw(dW[i]):<8} 16")

    print()
    print(f"At round 56: F_2 baseline hw = {hw(dW[56])}")
    print(f"             empirical mean = 16 (carries randomize)")
    print(f"             SAT candidate  = 7 (carries cancelled)")
    print()
    print("Interpretation:")
    print("  - F_2 baseline gives one specific dW[i] sequence (deterministic)")
    print("  - Empirical hw distribution centers on 16 (random binomial)")
    print("  - Carries can cancel OR amplify; the rare candidates with low hw_dW[56]")
    print("    are those where carries productively cancelled bits")
    print("  - There's no F_2-derivable shortcut to find low-hw candidates")


if __name__ == "__main__":
    main()
