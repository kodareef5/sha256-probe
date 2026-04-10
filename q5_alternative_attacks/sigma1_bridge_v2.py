#!/usr/bin/env python3
"""
sigma1_bridge_v2.py — Proper sigma1 bridge MITM for sr=61.

Algorithm:
1. Enumerate (W[57], W[59]) candidates that satisfy cascade 1
2. For each, compute the round-59 state WITHOUT W[58] applied yet
   (this requires a TWO-step computation from round 57 to round 59,
    where we backward-solve for W[58])
3. Compute the W[60] = sigma1(W[58]) + const that would make de60=0
4. Invert sigma1 to get the W[58] that produces this W[60]
5. Apply the forced W[58] to verify consistency and measure residual HW

This is actually harder than it sounds because W[58] affects round 58
which affects round 59 state. So we have a fixed-point problem:
  w58 = sigma1_inv(desired_w60(w57, w58, w59) - const)

For a tractable version: fix W[57], W[59] and treat W[58] as the only
free variable constrained by the sigma1 rule. Then iterate or directly
solve.

This is an EXPERIMENTAL exploration — we don't expect it to find a
collision, but the residual HW landscape will tell us whether the
sigma1 constraint can even be satisfied simultaneously with de60=0.
"""

import sys, os, time, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
from lib.sha256 import *


def build_sigma1_inverse():
    """Build sigma1_inv as a closed-form via Gaussian elimination on F_2."""
    # sigma1 is F_2-linear with rank 32 (bijective)
    # Build the matrix: each column i is sigma1(unit_i)
    cols = [sigma1(1 << i) for i in range(32)]
    # Matrix form: M[row, col] = bit(row) of cols[col]
    # We want sigma1(x) = y. Solve for x.
    # x[col] contributes to y via cols[col]
    # y = sum over col of x[col] * cols[col]  (XOR-summed)
    # To invert: Gauss eliminate
    M = [[((cols[c] >> r) & 1) for c in range(32)] for r in range(32)]
    # Extended matrix for augment: identity
    aug = [[M[r][c] for c in range(32)] + [1 if c == r else 0 for c in range(32)]
           for r in range(32)]

    # Gauss-Jordan
    for col in range(32):
        # Find pivot
        pivot = None
        for r in range(col, 32):
            if aug[r][col] == 1:
                pivot = r
                break
        if pivot is None:
            raise ValueError("sigma1 not invertible??")
        aug[col], aug[pivot] = aug[pivot], aug[col]
        for r in range(32):
            if r != col and aug[r][col] == 1:
                for c in range(64):
                    aug[r][c] ^= aug[col][c]

    # Extract inverse
    inv = [[aug[r][c] for c in range(32, 64)] for r in range(32)]

    def sigma1_inv(y):
        x = 0
        for i in range(32):
            bit = 0
            for j in range(32):
                if inv[i][j] and ((y >> j) & 1):
                    bit ^= 1
            if bit:
                x |= (1 << i)
        return x

    # Verify
    assert sigma1_inv(sigma1(0x12345678)) == 0x12345678
    assert sigma1(sigma1_inv(0xDEADBEEF)) == 0xDEADBEEF
    return sigma1_inv


def one_round(s, w, i):
    T1 = add(s[7], Sigma1(s[4]), Ch(s[4], s[5], s[6]), K[i], w)
    T2 = add(Sigma0(s[0]), Maj(s[0], s[1], s[2]))
    return (add(T1, T2), s[0], s[1], s[2], add(s[3], T1), s[4], s[5], s[6])


def main():
    n_samples = int(sys.argv[1]) if len(sys.argv) > 1 else 10000

    M0 = 0x17149975
    FILL = 0xFFFFFFFF
    M1 = [M0] + [FILL] * 15
    M2 = list(M1); M2[0] ^= 0x80000000; M2[9] ^= 0x80000000
    s1_init, W1_pre = precompute_state(M1)
    s2_init, W2_pre = precompute_state(M2)

    # sr=61 schedule constants for W[60]
    sched_C1 = (W1_pre[53] + sigma0(W1_pre[45]) + W1_pre[44]) & MASK
    sched_C2 = (W2_pre[53] + sigma0(W2_pre[45]) + W2_pre[44]) & MASK

    # Cascade 1 offset for W2[57]
    dh = (s1_init[7] - s2_init[7]) & MASK
    dSig1 = (Sigma1(s1_init[4]) - Sigma1(s2_init[4])) & MASK
    dCh = (Ch(s1_init[4], s1_init[5], s1_init[6]) - Ch(s2_init[4], s2_init[5], s2_init[6])) & MASK
    T2_1 = (Sigma0(s1_init[0]) + Maj(s1_init[0], s1_init[1], s1_init[2])) & MASK
    T2_2 = (Sigma0(s2_init[0]) + Maj(s2_init[0], s2_init[1], s2_init[2])) & MASK
    dT2 = (T2_1 - T2_2) & MASK
    C_w57 = (dh + dSig1 + dCh + dT2) & MASK
    print(f"Cascade 1 C_w57 = 0x{C_w57:08x}")

    sigma1_inv = build_sigma1_inverse()
    print("sigma1 inverse built\n")

    print(f"=== sr=61 with sigma1 bridge ===")
    print(f"Strategy: pick random W[57], W[59], enumerate W[58],")
    print(f"each W[58] produces a specific sr=61 W[60] via sigma1 rule,")
    print(f"measure residual HW after all 7 rounds.\n")

    rng = random.Random(42)
    min_hw = 256
    best_state = None
    hw_distribution = []

    t0 = time.time()
    for trial in range(n_samples):
        # Random W1[57], forced W2[57]
        w1_57 = rng.getrandbits(32)
        w2_57 = (w1_57 + C_w57) & MASK

        # Random W[59] for both messages (independent)
        w1_59 = rng.getrandbits(32)
        w2_59 = rng.getrandbits(32)

        # Pick W[58] — for now, random (we'll test constrained-W[58] later)
        w1_58 = rng.getrandbits(32)
        w2_58 = rng.getrandbits(32)

        # Compute W[60] via sr=61 rule
        w1_60 = (sigma1(w1_58) + sched_C1) & MASK
        w2_60 = (sigma1(w2_58) + sched_C2) & MASK

        # Run rounds 57-60
        s1 = one_round(s1_init, w1_57, 57)
        s2 = one_round(s2_init, w2_57, 57)
        s1 = one_round(s1, w1_58, 58)
        s2 = one_round(s2, w2_58, 58)
        s1 = one_round(s1, w1_59, 59)
        s2 = one_round(s2, w2_59, 59)
        s1 = one_round(s1, w1_60, 60)
        s2 = one_round(s2, w2_60, 60)

        # For sr=61, W[61..63] are schedule-determined
        # W[61] = sigma1(W[59]) + W[54] + sigma0(W[46]) + W[45]
        sched_C1_61 = (W1_pre[54] + sigma0(W1_pre[46]) + W1_pre[45]) & MASK
        sched_C2_61 = (W2_pre[54] + sigma0(W2_pre[46]) + W2_pre[45]) & MASK
        w1_61 = (sigma1(w1_59) + sched_C1_61) & MASK
        w2_61 = (sigma1(w2_59) + sched_C2_61) & MASK
        s1 = one_round(s1, w1_61, 61)
        s2 = one_round(s2, w2_61, 61)

        # W[62] = sigma1(W[60]) + W[55] + sigma0(W[47]) + W[46]
        sched_C1_62 = (W1_pre[55] + sigma0(W1_pre[47]) + W1_pre[46]) & MASK
        sched_C2_62 = (W2_pre[55] + sigma0(W2_pre[47]) + W2_pre[46]) & MASK
        w1_62 = (sigma1(w1_60) + sched_C1_62) & MASK
        w2_62 = (sigma1(w2_60) + sched_C2_62) & MASK
        s1 = one_round(s1, w1_62, 62)
        s2 = one_round(s2, w2_62, 62)

        # W[63] = sigma1(W[61]) + W[56] + sigma0(W[48]) + W[47]
        sched_C1_63 = (W1_pre[56] + sigma0(W1_pre[48]) + W1_pre[47]) & MASK
        sched_C2_63 = (W2_pre[56] + sigma0(W2_pre[48]) + W2_pre[47]) & MASK
        w1_63 = (sigma1(w1_61) + sched_C1_63) & MASK
        w2_63 = (sigma1(w2_61) + sched_C2_63) & MASK
        s1 = one_round(s1, w1_63, 63)
        s2 = one_round(s2, w2_63, 63)

        # Total diff HW
        total_hw = sum(hw((s1[r] - s2[r]) & MASK) for r in range(8))
        # Actually let me use XOR diff for consistency
        total_hw = sum(hw(s1[r] ^ s2[r]) for r in range(8))
        hw_distribution.append(total_hw)
        if total_hw < min_hw:
            min_hw = total_hw
            best_state = (w1_57, w1_58, w1_59, total_hw)
            if trial < 100 or total_hw < 90:
                print(f"  [{trial:>7}] NEW BEST: HW={total_hw}", flush=True)

        if trial and trial % 2000 == 0:
            rate = trial / (time.time() - t0)
            print(f"  [{trial:>7}/{n_samples}] {rate:.0f}/s, min={min_hw}", flush=True)

    t1 = time.time() - t0
    print(f"\nDone in {t1:.1f}s")
    print(f"Minimum HW: {min_hw}")
    if best_state:
        print(f"Best (W[57], W[58], W[59]): (0x{best_state[0]:08x}, 0x{best_state[1]:08x}, 0x{best_state[2]:08x})")

    # Distribution
    import statistics
    print(f"Mean HW: {statistics.mean(hw_distribution):.1f}")
    print(f"Stdev HW: {statistics.stdev(hw_distribution):.1f}")


if __name__ == "__main__":
    main()
