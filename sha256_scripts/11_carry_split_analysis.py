#!/usr/bin/env python3
"""
Script 11: Carry Chain Propagation Analysis

Analyzes the bit-level dependency structure of the 7-round tail (rounds 57-63).
Key question: do the low bits of the output depend only on the low bits of the input?

In modular addition, carry propagates strictly upward (LSB to MSB).
Over 7 rounds with ~4 additions per round, worst-case carry propagation
is ~28 bit positions. This means low output bits might depend on a
LIMITED subset of input bits.

If we find independent subproblems, we can decompose the 128-bit search:
  1. Solve low-8-bit subproblem first (2^8 candidates)
  2. Extend each candidate to 16 bits
  3. Continue peeling until full solution

Also analyzes: which output registers depend on which input words,
and whether any output bits are effectively independent.
"""

import random
import time

# SHA-256 functions
def ROR(x, n): return ((x >> n) | (x << (32 - n))) & 0xFFFFFFFF
def SHR(x, n): return x >> n
def Ch(e, f, g): return (e & f) ^ ((~e) & g) & 0xFFFFFFFF
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


def precompute():
    """Precompute state and schedule through round 56."""
    M1 = [0x17149975] + [0xffffffff] * 15
    M2 = M1.copy()
    M2[0] ^= 0x80000000
    M2[9] ^= 0x80000000

    results = []
    for msg in [M1, M2]:
        W = [0] * 57
        for i in range(16): W[i] = msg[i]
        for i in range(16, 57):
            W[i] = (sigma1(W[i-2]) + W[i-7] + sigma0(W[i-15]) + W[i-16]) & M32
        a, b, c, d, e, f, g, h = IV
        for i in range(57):
            T1 = (h + Sigma1(e) + Ch(e, f, g) + K[i] + W[i]) & M32
            T2 = (Sigma0(a) + Maj(a, b, c)) & M32
            h = g; g = f; f = e; e = (d + T1) & M32
            d = c; c = b; b = a; a = (T1 + T2) & M32
        results.append(((a, b, c, d, e, f, g, h), W))

    return results[0], results[1]


(STATE1, W1_PRE), (STATE2, W2_PRE) = precompute()


def run_tail(w1_4, w2_4):
    """Run rounds 57-63 and return final states for both messages."""
    def do_rounds(state, W_pre, free_words):
        w57, w58, w59, w60 = free_words
        w61 = (sigma1(w59) + W_pre[54] + sigma0(W_pre[46]) + W_pre[45]) & M32
        w62 = (sigma1(w60) + W_pre[55] + sigma0(W_pre[47]) + W_pre[46]) & M32
        w63 = (sigma1(w61) + W_pre[56] + sigma0(W_pre[48]) + W_pre[47]) & M32
        W = [w57, w58, w59, w60, w61, w62, w63]

        a, b, c, d, e, f, g, h = state
        for i in range(7):
            T1 = (h + Sigma1(e) + Ch(e, f, g) + K[57+i] + W[i]) & M32
            T2 = (Sigma0(a) + Maj(a, b, c)) & M32
            h = g; g = f; f = e; e = (d + T1) & M32
            d = c; c = b; b = a; a = (T1 + T2) & M32
        return (a, b, c, d, e, f, g, h)

    s1 = do_rounds(STATE1, W1_PRE, w1_4)
    s2 = do_rounds(STATE2, W2_PRE, w2_4)
    return s1, s2


def output_diff(w1_4, w2_4):
    """Return the 8 register diffs after round 63."""
    s1, s2 = run_tail(w1_4, w2_4)
    return tuple((s1[i] ^ s2[i]) for i in range(8))


# =============================================================================
# Analysis 1: Bit-level carry dependency (which input bits affect which output bits)
# =============================================================================

def analyze_bit_dependencies(n_samples=5000):
    """
    For each input bit position (0-127, across W1[57..60]),
    flip it and measure which output bits change.
    This maps the dependency graph.
    """
    print("=" * 70)
    print("Analysis 1: Bit-Level Dependency Map")
    print("(Which input bits affect which output bits?)")
    print("=" * 70)

    # dep_matrix[input_bit][output_word][output_bit] = count of times it changed
    dep_matrix = {}

    for sample in range(n_samples):
        # Random base assignment
        w1_base = tuple(random.getrandbits(32) for _ in range(4))
        w2_base = tuple(random.getrandbits(32) for _ in range(4))
        diff_base = output_diff(w1_base, w2_base)

        # Flip each input bit and see what changes
        for input_bit in range(128):
            word_idx = input_bit // 32
            bit_pos = input_bit % 32

            # Flip in W1
            w1_flip = list(w1_base)
            w1_flip[word_idx] ^= (1 << bit_pos)
            w1_flip = tuple(w1_flip)

            # Also flip in W2 (we're testing BOTH messages' free words)
            # Actually, W1 and W2 are independent. Let's just test W1 flips.
            diff_flip = output_diff(w1_flip, w2_base)

            # Which output bits changed?
            for out_reg in range(8):
                changed = diff_base[out_reg] ^ diff_flip[out_reg]
                if input_bit not in dep_matrix:
                    dep_matrix[input_bit] = [[0]*32 for _ in range(8)]
                for ob in range(32):
                    if changed & (1 << ob):
                        dep_matrix[input_bit][out_reg][ob] += 1

    # Summarize: for each input bit, how many output bits does it affect?
    print(f"\nSampled {n_samples} random base points.")
    print(f"\nInput bit -> Number of output bits affected (out of 256):")
    print(f"{'Input':>8} {'Affected':>10} {'Coverage':>10}")
    print("-" * 35)

    affected_counts = []
    for ib in range(128):
        if ib not in dep_matrix:
            affected_counts.append(0)
            continue
        total_affected = 0
        for oreg in range(8):
            for ob in range(32):
                if dep_matrix[ib][oreg][ob] > n_samples * 0.01:  # >1% change rate
                    total_affected += 1
        affected_counts.append(total_affected)

    for ib in range(0, 128, 8):  # Show every 8th bit
        w = ib // 32
        b = ib % 32
        print(f"  W1[{57+w}] bit {b:2d}: {affected_counts[ib]:4d}/256 ({affected_counts[ib]*100/256:.0f}%)")

    min_aff = min(affected_counts)
    max_aff = max(affected_counts)
    mean_aff = sum(affected_counts) / len(affected_counts)
    print(f"\n  Min affected: {min_aff}, Max: {max_aff}, Mean: {mean_aff:.1f}")

    return dep_matrix, affected_counts


# =============================================================================
# Analysis 2: Low-bit independence test
# =============================================================================

def analyze_low_bit_independence(n_samples=10000):
    """
    Test whether the low k bits of output registers depend ONLY on the low k bits
    of input words. If so, we have an independent subproblem.

    Method: for each k, randomize inputs but keep low k bits fixed.
    Check if low k bits of output also stay fixed.
    """
    print("\n" + "=" * 70)
    print("Analysis 2: Low-Bit Independence Test")
    print("(Do low output bits depend only on low input bits?)")
    print("=" * 70)

    for k in [1, 2, 4, 8, 12, 16, 20, 24]:
        low_mask = (1 << k) - 1
        high_mask = M32 ^ low_mask

        consistent = 0
        total = 0

        for _ in range(n_samples):
            # Fix low k bits, randomize high bits
            w1_base = tuple(random.getrandbits(32) for _ in range(4))
            w2_base = tuple(random.getrandbits(32) for _ in range(4))
            diff_base = output_diff(w1_base, w2_base)

            # New assignment: same low k bits, different high bits
            w1_new = tuple((w1_base[i] & low_mask) | (random.getrandbits(32) & high_mask) for i in range(4))
            w2_new = tuple((w2_base[i] & low_mask) | (random.getrandbits(32) & high_mask) for i in range(4))
            diff_new = output_diff(w1_new, w2_new)

            # Check if low k bits of output match
            match = True
            for reg in range(8):
                if (diff_base[reg] & low_mask) != (diff_new[reg] & low_mask):
                    match = False
                    break

            total += 1
            if match:
                consistent += 1

        pct = consistent * 100.0 / total
        independent = "YES (exploitable!)" if pct > 95 else ("WEAK" if pct > 50 else "NO")
        print(f"  k={k:2d}: low-{k} bits consistent = {pct:.1f}% -> {independent}")


# =============================================================================
# Analysis 3: Word-level influence
# =============================================================================

def analyze_word_influence(n_samples=5000):
    """
    Which of the 4 free words (W1[57..60]) has the most influence on which
    output registers? This tells us if any word-register pair is weakly coupled.
    """
    print("\n" + "=" * 70)
    print("Analysis 3: Word-Level Influence on Output Registers")
    print("(Which free word affects which output register most?)")
    print("=" * 70)

    reg_names = "abcdefgh"
    influence = [[0.0]*8 for _ in range(4)]  # [input_word][output_reg]

    for _ in range(n_samples):
        w1_base = tuple(random.getrandbits(32) for _ in range(4))
        w2_base = tuple(random.getrandbits(32) for _ in range(4))
        diff_base = output_diff(w1_base, w2_base)

        for w_idx in range(4):
            # Replace word w_idx with a random value
            w1_mod = list(w1_base)
            w1_mod[w_idx] = random.getrandbits(32)
            diff_mod = output_diff(tuple(w1_mod), w2_base)

            for reg in range(8):
                change = diff_base[reg] ^ diff_mod[reg]
                influence[w_idx][reg] += bin(change).count('1')

    # Normalize
    for w in range(4):
        for r in range(8):
            influence[w][r] /= (n_samples * 32)  # Fraction of bits changed

    print(f"\n  Influence matrix (fraction of output bits changed when input word is randomized):")
    print(f"  {'':>12}", end="")
    for r in range(8):
        print(f"  d{reg_names[r]}   ", end="")
    print()
    for w in range(4):
        print(f"  W1[{57+w}]     ", end="")
        for r in range(8):
            val = influence[w][r]
            marker = "*" if val > 0.45 else (" " if val > 0.3 else ".")
            print(f" {val:.2f}{marker} ", end="")
        print()

    print(f"\n  Legend: * = strong (>0.45), blank = medium (0.3-0.45), . = weak (<0.3)")


# =============================================================================
# Analysis 4: Sigma1 structure in cascade rounds
# =============================================================================

def analyze_sigma1_cascade():
    """
    The cascade rounds (61-63) use sigma1 which involves rotations by 17, 19
    and shift by 10. Analyze how this mixes bits from the free words.
    """
    print("\n" + "=" * 70)
    print("Analysis 4: Sigma1 Cascade Bit Mixing")
    print("(How does sigma1 in rounds 61-63 spread influence?)")
    print("=" * 70)

    # sigma1(x) = ROR(x,17) ^ ROR(x,19) ^ SHR(x,10)
    # For each input bit position, which output positions does it affect?
    print("\n  sigma1 dependency: input bit k -> output bits affected")
    for k in [0, 7, 10, 15, 17, 19, 24, 31]:
        x = 1 << k
        out = sigma1(x)
        affected = [b for b in range(32) if out & (1 << b)]
        print(f"    bit {k:2d} -> bits {affected}")

    # How many bits does sigma1 spread to on average?
    total_spread = 0
    for k in range(32):
        x = 1 << k
        out = sigma1(x)
        total_spread += bin(out).count('1')
    print(f"\n  Average bits affected per input bit: {total_spread/32:.1f}")
    print(f"  (If = 3, sigma1 is a 3-to-1 spread. If > 3, there's overlap.)")


def main():
    print("SHA-256 sr=60 Carry Chain and Dependency Analysis")
    print(f"State diff hw at round 56: {sum(bin(STATE1[i]^STATE2[i]).count('1') for i in range(8))}")
    print()

    # Quick structural analysis
    analyze_sigma1_cascade()

    # Low-bit independence (fastest, most actionable)
    analyze_low_bit_independence(5000)

    # Word-level influence
    analyze_word_influence(2000)

    # Full bit-level dependency (slower)
    analyze_bit_dependencies(1000)

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("If low-bit independence holds for k >= 8:")
    print("  -> Decompose into subproblems: solve k LSBs first, extend upward")
    print("If word influence is uneven:")
    print("  -> Fix the least-influential word, reduce search space")
    print("If bit dependency is sparse:")
    print("  -> Some output bits can be solved independently")


if __name__ == "__main__":
    main()
