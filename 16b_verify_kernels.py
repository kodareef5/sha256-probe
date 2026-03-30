#!/usr/bin/env python3
"""
Script 16b: Verify GF(2) Kernels Against Actual Modular Arithmetic

The GF(2) kernel search found multi-word kernels that zero specific
schedule positions under XOR-only analysis. But SHA-256's schedule
uses modular addition (mod 2^32), which introduces carries.

This script:
1. Takes each GF(2) kernel from script 16
2. Constructs actual messages M1/M2 with that difference
3. Computes the REAL schedule with modular addition
4. Checks if dW[target] is actually 0 or just low Hamming weight
5. Also runs the full 57-round compression to check da[56]

Key question: do any GF(2) kernels survive carries?
The MSB kernel works because bit 31 is carry-free. Multi-bit kernels
will generally NOT be carry-free, but:
  - Low-weight kernels have fewer carry-generating positions
  - Some bit patterns may still cancel carries structurally
"""

import random

def ROR(x, n): return ((x >> n) | (x << (32 - n))) & 0xFFFFFFFF
def SHR(x, n): return x >> n
def Ch(e, f, g): return ((e & f) ^ ((~e) & g)) & 0xFFFFFFFF
def Maj(a, b, c): return (a & b) ^ (a & c) ^ (b & c)
def Sigma0(a): return ROR(a, 2) ^ ROR(a, 13) ^ ROR(a, 22)
def Sigma1(e): return ROR(e, 6) ^ ROR(e, 11) ^ ROR(e, 25)
def sigma0(x): return ROR(x, 7) ^ ROR(x, 18) ^ SHR(x, 3)
def sigma1(x): return ROR(x, 17) ^ ROR(x, 19) ^ SHR(x, 10)

K = [
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
]
IV = [0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
      0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19]
M32 = 0xFFFFFFFF


def compute_schedule(M):
    """Compute full 64-word schedule from 16-word message."""
    W = [0] * 64
    for i in range(16): W[i] = M[i]
    for i in range(16, 64):
        W[i] = (sigma1(W[i-2]) + W[i-7] + sigma0(W[i-15]) + W[i-16]) & M32
    return W


def compress_n_rounds(M, n_rounds):
    """Run n rounds of SHA-256 compression, return state."""
    W = compute_schedule(M)
    a, b, c, d, e, f, g, h = IV
    for i in range(n_rounds):
        T1 = (h + Sigma1(e) + Ch(e, f, g) + K[i] + W[i]) & M32
        T2 = (Sigma0(a) + Maj(a, b, c)) & M32
        h = g; g = f; f = e; e = (d + T1) & M32
        d = c; c = b; b = a; a = (T1 + T2) & M32
    return (a, b, c, d, e, f, g, h)


def hw(x):
    return bin(x).count('1')


def verify_kernel(kernel_diff, name, targets, n_random_bases=100):
    """
    Verify a GF(2) kernel against actual modular arithmetic.

    kernel_diff: list of 16 uint32 (message word differences)
    targets: list of schedule positions that should be zero
    n_random_bases: how many random base messages to test
    """
    print(f"\n{'='*60}", flush=True)
    print(f"Kernel: {name}", flush=True)
    print(f"Diff words: ", end="", flush=True)
    for i, d in enumerate(kernel_diff):
        if d: print(f"dM[{i}]=0x{d:08x}(hw={hw(d)}) ", end="", flush=True)
    print(flush=True)
    print(f"Targets: dW[{','.join(str(t) for t in targets)}] = 0", flush=True)

    # Test with multiple random base messages
    gf2_match = 0
    actual_zero = 0
    low_hw = 0  # dW[t] has hw <= 5
    da56_zero = 0

    best_total_hw = 999
    best_base = None

    for trial in range(n_random_bases):
        # Random base message
        M1 = [random.getrandbits(32) for _ in range(16)]
        M2 = [(M1[i] ^ kernel_diff[i]) & M32 for i in range(16)]

        W1 = compute_schedule(M1)
        W2 = compute_schedule(M2)

        # Check target positions
        all_zero = True
        total_target_hw = 0
        for t in targets:
            dW = W1[t] ^ W2[t]
            total_target_hw += hw(dW)
            if dW != 0:
                all_zero = False

        if all_zero:
            actual_zero += 1
        if total_target_hw <= len(targets) * 3:
            low_hw += 1

        if total_target_hw < best_total_hw:
            best_total_hw = total_target_hw
            best_base = M1[:]

        # Check da[56] (run compression)
        s1 = compress_n_rounds(M1, 57)
        s2 = compress_n_rounds(M2, 57)
        if s1[0] == s2[0]:
            da56_zero += 1

    print(f"\nResults over {n_random_bases} random base messages:", flush=True)
    print(f"  dW targets all zero: {actual_zero}/{n_random_bases} ({actual_zero*100/n_random_bases:.1f}%)", flush=True)
    print(f"  dW targets low hw (<=3/target): {low_hw}/{n_random_bases}", flush=True)
    print(f"  Best total target hw: {best_total_hw}", flush=True)
    print(f"  da[56]=0: {da56_zero}/{n_random_bases}", flush=True)

    if actual_zero == 0 and best_total_hw > 0:
        print(f"  VERDICT: GF(2) kernel does NOT survive carries.", flush=True)
        print(f"           Modular addition destroys the cancellation.", flush=True)
    elif actual_zero > 0 and actual_zero < n_random_bases:
        print(f"  VERDICT: PARTIALLY survives! {actual_zero*100/n_random_bases:.1f}% of base messages work.", flush=True)
        print(f"           This is message-dependent (carries are input-dependent).", flush=True)
    elif actual_zero == n_random_bases:
        print(f"  VERDICT: FULLY SURVIVES! This kernel is carry-free at targets!", flush=True)
        print(f"           [!!!] This is a viable alternative kernel!", flush=True)

    # Deep analysis of the best case
    if best_base and best_total_hw <= 10:
        M1 = best_base
        M2 = [(M1[i] ^ kernel_diff[i]) & M32 for i in range(16)]
        W1 = compute_schedule(M1)
        W2 = compute_schedule(M2)

        print(f"\n  Best case schedule diffs (positions 48-63):", flush=True)
        for t in range(48, 64):
            dW = W1[t] ^ W2[t]
            marker = " <-- TARGET" if t in targets else ""
            if dW == 0: marker += " ZERO!"
            print(f"    dW[{t}]: hw={hw(dW):2d} val=0x{dW:08x}{marker}", flush=True)

    return actual_zero, da56_zero


def main():
    print("GF(2) Kernel Verification Against Modular Arithmetic", flush=True)
    print("=" * 60, flush=True)

    # Reference: MSB kernel (should be 100% carry-free)
    msb_diff = [0] * 16
    msb_diff[0] = 0x80000000
    msb_diff[9] = 0x80000000
    verify_kernel(msb_diff, "MSB kernel (reference)", [16,17,18,19,20,21,22,23], 200)

    # Kernels from script 16
    kernels = [
        {
            "name": "1-word: dW[56]=0",
            "diff": {0: 0x55b8c2a4},
            "targets": [56],
        },
        {
            "name": "1-word: dW[57]=0",
            "diff": {0: 0x0729ce20},
            "targets": [57],
        },
        {
            "name": "3-word: dW[55,56]=0",
            "diff": {0: 0x00504080, 1: 0x3c830bc5, 2: 0x00000800},
            "targets": [55, 56],
        },
        {
            "name": "3-word: dW[55,56,57]=0",
            "diff": {0: 0xae31773e, 1: 0xfe4d4b31, 2: 0x84dfa72e},
            "targets": [55, 56, 57],
        },
        {
            "name": "4-word: dW[53,54,55,56]=0",
            "diff": {0: 0x52f50bb7, 1: 0xd48ac66e, 2: 0xc0e21087, 3: 0xa9b722e0},
            "targets": [53, 54, 55, 56],
        },
    ]

    for k in kernels:
        diff = [0] * 16
        for idx, val in k["diff"].items():
            diff[idx] = val
        verify_kernel(diff, k["name"], k["targets"], 500)

    # Also test: what if we use the MSB kernel COMBINED with the 1-word dW[56]=0 kernel?
    print("\n\n" + "=" * 60, flush=True)
    print("COMBO: MSB kernel + dW[56]=0 kernel", flush=True)
    combo = [0] * 16
    combo[0] = 0x80000000 ^ 0x55b8c2a4  # XOR both kernels at word 0
    combo[9] = 0x80000000  # MSB kernel word 9
    verify_kernel(combo, "MSB + dW56 combo", [16,17,18,19,20,21,22,23,56], 500)

    # Test MSB kernel alone at positions 55,56,57
    print("\n\n" + "=" * 60, flush=True)
    print("MSB kernel: checking late positions", flush=True)
    msb_diff = [0] * 16
    msb_diff[0] = 0x80000000
    msb_diff[9] = 0x80000000
    verify_kernel(msb_diff, "MSB kernel (late positions)", [55, 56, 57], 500)


if __name__ == "__main__":
    main()
