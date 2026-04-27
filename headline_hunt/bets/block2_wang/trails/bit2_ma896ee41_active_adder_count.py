#!/usr/bin/env python3
"""
bit2_ma896ee41_active_adder_count.py — Mouha-style active adder count
on the bit2_ma896ee41 deep-min residual trail (rounds 57..63).

Forward-simulates the cascade-1 path with the W-witness from F32:
  W[57] = 0x91e0726f
  W[58] = 0x6a166a99
  W[59] = 0x4fe63e5b
  W[60] = 0x8d8e53ed

For each round r in 57..63, computes:
- Per-add input differences (XOR between M1 and M2)
- "Active" if input difference is non-zero
- Probability cost ~ 2^-1 per active adder (Lipmaa-Moriai bound is
  more precise but per-adder ≤ 1-bit cost is a good upper bound on
  probability)

Output: per-round active adder count, total active adders, naive
trail-probability lower bound (2^-N for N active adders).

Reproduces F32 deep-min residual diff63 = (0xa1262506, 0xb0124c02,
0x02000004, 0, 0x68c1c048, 0x5091d405, 0x02000004, 0).
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/../../../.."))
from lib.sha256 import K, IV, MASK, sigma0, sigma1, Sigma0, Sigma1, Ch, Maj, hw

# Cand parameters
M0 = 0xa896ee41
FILL = 0xffffffff
KERNEL_BIT = 2

# F32 deep-min W-witness
W57 = 0x91e0726f
W58 = 0x6a166a99
W59 = 0x4fe63e5b
W60 = 0x8d8e53ed

# Expected diff63 (sanity check)
EXPECTED_DIFF63 = [0xa1262506, 0xb0124c02, 0x02000004, 0,
                   0x68c1c048, 0x5091d405, 0x02000004, 0]


def precompute(M):
    """Run rounds 0..56, return (state, full_W)."""
    W = list(M) + [0] * 48
    for r in range(16, 64):
        W[r] = (sigma1(W[r-2]) + W[r-7] + sigma0(W[r-15]) + W[r-16]) & MASK
    s = list(IV)
    for r in range(57):
        T1 = (s[7] + Sigma1(s[4]) + Ch(s[4], s[5], s[6]) + K[r] + W[r]) & MASK
        T2 = (Sigma0(s[0]) + Maj(s[0], s[1], s[2])) & MASK
        s = [(T1 + T2) & MASK, s[0], s[1], s[2], (s[3] + T1) & MASK, s[4], s[5], s[6]]
    return s, W


def cascade_w(s1, s2, w1, K_r):
    """Compute W2 such that cascade-1 condition (a/b/c/d zero diff at r+1) holds."""
    T1_1 = (s1[7] + Sigma1(s1[4]) + Ch(s1[4], s1[5], s1[6]) + K_r + w1) & MASK
    T2_1 = (Sigma0(s1[0]) + Maj(s1[0], s1[1], s1[2])) & MASK
    a1_new = (T1_1 + T2_1) & MASK
    e1_new = (s1[3] + T1_1) & MASK
    # Need s2 to produce a2_new = a1_new (cascade for "a"), e2_new = e1_new for cascade-1
    # That requires T1_2 + T2_2 = a1_new and s2[3] + T1_2 = e1_new
    T2_2 = (Sigma0(s2[0]) + Maj(s2[0], s2[1], s2[2])) & MASK
    # T1_2 = a1_new - T2_2
    T1_2 = (a1_new - T2_2) & MASK
    # e1_new = s2[3] + T1_2  →  s2[3] = e1_new - T1_2
    # For cascade to hold, s1[3] == s2[3] (already given by the cascade-1 chain)
    # Then T1_2 = e1_new - s2[3] = e1_new - s1[3]
    # Both formulas must agree: a1_new - T2_2 == e1_new - s1[3]
    # If they don't, then this round doesn't admit cascade-1 with this s pair
    # We just compute w2 from T1_2:
    # T1_2 = s2[7] + Sigma1(s2[4]) + Ch(s2[4],s2[5],s2[6]) + K_r + w2
    # → w2 = T1_2 - s2[7] - Sigma1(s2[4]) - Ch(s2[4],s2[5],s2[6]) - K_r
    w2 = (T1_2 - s2[7] - Sigma1(s2[4]) - Ch(s2[4], s2[5], s2[6]) - K_r) & MASK
    return w2


def round_step_count_active(s1, s2, w1, w2, K_r):
    """Run one round on both states, count active modular adders.

    Round structure:
      T1 = h + Σ1(e) + Ch(e,f,g) + K + W   ← 4 adders (h+Σ1, +Ch, +K, +W)
      T2 = Σ0(a) + Maj(a,b,c)               ← 1 adder
      a' = T1 + T2                          ← 1 adder
      e' = d + T1                           ← 1 adder

    Total: 7 modular adders per round in SHA-256.

    Active if input XOR-diff non-zero.
    """
    n_active = 0
    contrib_log = []

    # Add 1: h + Σ1(e) [in T1]
    diff_h = s1[7] ^ s2[7]
    diff_Sigma1 = Sigma1(s1[4]) ^ Sigma1(s2[4])
    if diff_h != 0 or diff_Sigma1 != 0:
        n_active += 1
        contrib_log.append(("h+Σ1(e)", diff_h, diff_Sigma1))
    add1 = (s1[7] + Sigma1(s1[4])) & MASK
    add1_2 = (s2[7] + Sigma1(s2[4])) & MASK

    # Add 2: + Ch(e,f,g)  [in T1]
    diff_Ch = Ch(s1[4], s1[5], s1[6]) ^ Ch(s2[4], s2[5], s2[6])
    diff_acc = add1 ^ add1_2
    if diff_Ch != 0 or diff_acc != 0:
        n_active += 1
        contrib_log.append(("+Ch", diff_Ch, diff_acc))
    add2 = (add1 + Ch(s1[4], s1[5], s1[6])) & MASK
    add2_2 = (add1_2 + Ch(s2[4], s2[5], s2[6])) & MASK

    # Add 3: + K_r  [no diff possible, K is constant]
    diff_acc = add2 ^ add2_2
    if diff_acc != 0:
        n_active += 1
        contrib_log.append(("+K", 0, diff_acc))
    add3 = (add2 + K_r) & MASK
    add3_2 = (add2_2 + K_r) & MASK

    # Add 4: + W  [W diff is the kernel cascade]
    diff_W = w1 ^ w2
    diff_acc = add3 ^ add3_2
    if diff_W != 0 or diff_acc != 0:
        n_active += 1
        contrib_log.append(("+W", diff_W, diff_acc))
    T1_1 = (add3 + w1) & MASK
    T1_2 = (add3_2 + w2) & MASK

    # Add 5: Σ0(a) + Maj(a,b,c)  [T2]
    diff_Sigma0 = Sigma0(s1[0]) ^ Sigma0(s2[0])
    diff_Maj = Maj(s1[0], s1[1], s1[2]) ^ Maj(s2[0], s2[1], s2[2])
    if diff_Sigma0 != 0 or diff_Maj != 0:
        n_active += 1
        contrib_log.append(("Σ0+Maj", diff_Sigma0, diff_Maj))
    T2_1 = (Sigma0(s1[0]) + Maj(s1[0], s1[1], s1[2])) & MASK
    T2_2 = (Sigma0(s2[0]) + Maj(s2[0], s2[1], s2[2])) & MASK

    # Add 6: a' = T1 + T2
    diff_T1 = T1_1 ^ T1_2
    diff_T2 = T2_1 ^ T2_2
    if diff_T1 != 0 or diff_T2 != 0:
        n_active += 1
        contrib_log.append(("a'=T1+T2", diff_T1, diff_T2))
    a1_new = (T1_1 + T2_1) & MASK
    a2_new = (T1_2 + T2_2) & MASK

    # Add 7: e' = d + T1
    diff_d = s1[3] ^ s2[3]
    if diff_d != 0 or diff_T1 != 0:
        n_active += 1
        contrib_log.append(("e'=d+T1", diff_d, diff_T1))
    e1_new = (s1[3] + T1_1) & MASK
    e2_new = (s2[3] + T1_2) & MASK

    s1_new = [a1_new, s1[0], s1[1], s1[2], e1_new, s1[4], s1[5], s1[6]]
    s2_new = [a2_new, s2[0], s2[1], s2[2], e2_new, s2[4], s2[5], s2[6]]

    return s1_new, s2_new, n_active, contrib_log


def main():
    M1 = [M0] + [FILL] * 15
    M2 = list(M1)
    M2[0] ^= (1 << KERNEL_BIT)
    M2[9] ^= (1 << KERNEL_BIT)

    s1, W1 = precompute(M1)
    s2, W2 = precompute(M2)

    print(f"=== bit2_ma896ee41 active-adder count along F32 deep-min trail ===")
    print(f"M0={hex(M0)} fill={hex(FILL)} kernel_bit={KERNEL_BIT}")
    print(f"State at start of round 57:")
    print(f"  s1 = {[hex(x) for x in s1]}")
    print(f"  s2 = {[hex(x) for x in s2]}")
    print(f"  diff = {[hex(s1[i] ^ s2[i]) for i in range(8)]}")
    print(f"  hw_diff = {sum(hw(s1[i] ^ s2[i]) for i in range(8))}")
    print()

    # Override W[57..60] with witness
    W1[57], W1[58], W1[59], W1[60] = W57, W58, W59, W60
    # Cascade-1 W2 for each of these
    cascades = []
    states = [(list(s1), list(s2))]

    total_active = 0
    print(f"{'r':>3} {'W1':>10} {'W2':>10} {'cw':>10} {'active':>6} {'hw_diff_after':>14}")
    for r in range(57, 64):
        s1c, s2c = states[-1]
        w1 = W1[r]
        if r <= 60:
            w2 = cascade_w(s1c, s2c, w1, K[r])
            cascades.append(w2)
            W2[r] = w2
        else:
            # rounds 61+: w2 follows from message expansion
            w2 = W2[r] = (sigma1(W2[r-2]) + W2[r-7] + sigma0(W2[r-15]) + W2[r-16]) & MASK
        s1n, s2n, n_act, contrib = round_step_count_active(s1c, s2c, w1, w2, K[r])
        states.append((s1n, s2n))
        total_active += n_act
        hw_d = sum(hw(s1n[i] ^ s2n[i]) for i in range(8))
        cw = (w2 - w1) & MASK
        print(f"{r:>3} 0x{w1:08x} 0x{w2:08x} 0x{cw:08x} {n_act:>6} {hw_d:>14}")
        for tag, da, db in contrib:
            print(f"      [{tag}]  diff_a=0x{da:08x} (HW={hw(da)})  diff_b=0x{db:08x} (HW={hw(db)})")

    s1_final, s2_final = states[-1]
    diff63 = [s1_final[i] ^ s2_final[i] for i in range(8)]
    print()
    print(f"diff63 (computed) = {[hex(x) for x in diff63]}")
    print(f"diff63 (expected) = {[hex(x) for x in EXPECTED_DIFF63]}")
    matches = diff63 == EXPECTED_DIFF63
    print(f"Match F32 expected: {matches}")

    print()
    print(f"=== Summary ===")
    print(f"Total active adders (rounds 57..63): {total_active}")
    print(f"Of 7 rounds × 7 adders/round = 49 max active")
    print(f"Naive trail-probability LOWER bound: 2^-{total_active}")
    print(f"With 256-bit second-block freedom: 2^{256-total_active} expected solutions")
    print(f"  (if bound is tight)")
    print()
    print(f"Caveat: '1-bit-per-adder' is an UPPER bound on per-adder cost.")
    print(f"Lipmaa-Moriai 2001 gives the exact probability per adder")
    print(f"depending on input HW. For low-HW inputs, often 0 cost (carry-free).")
    print(f"Refined Mouha-style accounting is the next step.")


if __name__ == "__main__":
    main()
