#!/usr/bin/env python3
"""
sigma1_linearity.py — Determine sigma1's F_2 linear rank.

sigma1(x) = ROR(x,17) ^ ROR(x,19) ^ SHR(x,10) is F_2-linear.
If rank=32, sigma1 is bijective and every target has exactly 1 preimage.
If rank<32, the image is a 2^rank subspace; some targets are unreachable.

This determines whether the sr=61 W[60] schedule rule
W[60] = sigma1(W[58]) + const can theoretically reach any target
(by choice of W[58]) or whether some W[60] values are forbidden.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
from lib.sha256 import sigma1, sigma0, MASK


def f2_rank(linear_func):
    """Compute F_2 rank of a 32-bit linear function over F_2^32."""
    # Build basis matrix: column i = f(e_i) where e_i is the i-th unit vector.
    cols = [linear_func(1 << i) for i in range(32)]
    # Gaussian elimination over F_2
    basis = []
    for v in cols:
        for b in basis:
            if v & -v >= b & -b:  # not the right pivot logic; do it properly
                pass
        # Reduce v against basis pivots
        for b in basis:
            if v & b & -(b & -b):  # if v has the pivot bit
                v ^= b
        if v:
            basis.append(v)
            basis.sort(key=lambda x: -(x & -x))  # sort by lowest set bit
    return len(basis)


def f2_rank_proper(linear_func):
    """Cleaner F_2 rank via Gaussian elimination."""
    rows = [linear_func(1 << i) for i in range(32)]
    rank = 0
    used = [False] * 32
    for col in range(32):  # iterate columns (bit positions)
        pivot = -1
        for r in range(32):
            if not used[r] and (rows[r] >> col) & 1:
                pivot = r
                break
        if pivot < 0:
            continue
        used[pivot] = True
        rank += 1
        for r in range(32):
            if r != pivot and (rows[r] >> col) & 1:
                rows[r] ^= rows[pivot]
    return rank


def main():
    # Verify sigma1 is F_2-linear
    a, b = 0x12345678, 0xfedcba98
    if sigma1(a ^ b) != sigma1(a) ^ sigma1(b):
        print("ERROR: sigma1 is not F_2-linear?!")
        return
    print("sigma1 is F_2-linear (verified)")

    rank = f2_rank_proper(sigma1)
    print(f"sigma1 F_2 rank = {rank} / 32")
    if rank == 32:
        print("  -> sigma1 is BIJECTIVE on F_2^32")
        print("  -> Every target has exactly 1 preimage")
        print("  -> sr=61 W[60] = sigma1(W[58]) + const can reach ANY value of W[60]")
    else:
        print(f"  -> sigma1 image is a 2^{rank} subspace ({100*2**rank/2**32:.4f}% of F_2^32)")
        print(f"  -> 2^{32-rank} targets are unreachable")

    print()
    rank0 = f2_rank_proper(sigma0)
    print(f"sigma0 F_2 rank = {rank0} / 32")

    # If sigma1 is bijective, find the preimage for our verified targets
    if rank == 32:
        from lib.sha256 import precompute_state, add
        M0 = 0x17149975
        FILL = 0xFFFFFFFF
        M1 = [M0] + [FILL] * 15
        M2 = list(M1); M2[0] ^= 0x80000000; M2[9] ^= 0x80000000
        s1, W1_pre = precompute_state(M1)
        s2, W2_pre = precompute_state(M2)
        W1_CERT = [0x9ccfa55e, 0xd9d64416, 0x9e3ffb08, 0xb6befe82]
        W2_CERT = [0x72e6c8cd, 0x4b96ca51, 0x587ffaa6, 0xea3ce26b]

        # Build inverse table by computing sigma1 of all 32 unit vectors
        # and using Gaussian elimination
        def sigma1_inverse(target):
            # Augmented matrix: solve sigma1(x) = target
            # Each row = (basis_image | basis_origin)
            rows = []
            for i in range(32):
                rows.append((sigma1(1 << i), 1 << i))
            # Reduce target using basis
            x = 0
            t = target
            used_bits = [False] * 32
            ordered = []
            for col in range(31, -1, -1):  # MSB first
                pivot = -1
                for r in range(len(rows)):
                    if r in [o[0] for o in ordered]:
                        continue
                    if (rows[r][0] >> col) & 1:
                        pivot = r
                        break
                if pivot < 0:
                    continue
                ordered.append((pivot, col))
                # Eliminate this bit from other rows
                for r in range(len(rows)):
                    if r != pivot and (rows[r][0] >> col) & 1:
                        rows[r] = (rows[r][0] ^ rows[pivot][0],
                                   rows[r][1] ^ rows[pivot][1])
            # Now rows is in echelon form. Solve for x.
            for pivot, col in ordered:
                if (t >> col) & 1:
                    t ^= rows[pivot][0]
                    x ^= rows[pivot][1]
            if t == 0:
                # Verify
                if sigma1(x) == target:
                    return x
            return None

        for tag, W_pre, W_cert in [("M1", W1_pre, W1_CERT),
                                    ("M2", W2_pre, W2_CERT)]:
            const = add(W_pre[53], sigma0(W_pre[45]), W_pre[44])
            w60_target = W_cert[3]
            needed_sig = (w60_target - const) & MASK
            preimage = sigma1_inverse(needed_sig)
            print(f"\n{tag}:")
            print(f"  W[60] target = 0x{w60_target:08x}")
            print(f"  needed sigma1(x) = 0x{needed_sig:08x}")
            if preimage is not None:
                print(f"  W[58]_alt = 0x{preimage:08x}  (verified: sigma1 = 0x{sigma1(preimage):08x})")
                print(f"  cert W[58] = 0x{W_cert[1]:08x}")
                from lib.sha256 import hw
                d = preimage ^ W_cert[1]
                print(f"  HW(W[58]_alt XOR cert W[58]) = {hw(d)}")
            else:
                print(f"  NO PREIMAGE EXISTS (impossible — sigma1 should be bijective)")


if __name__ == "__main__":
    main()
