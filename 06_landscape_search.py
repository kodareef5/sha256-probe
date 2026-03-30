#!/usr/bin/env python3
"""
Script 06: Stochastic Local Search — Fitness Landscape Analysis

Searches the 128-bit reduced problem (W1[57..60] only, W2 derived)
using multiple strategies:
  1. Random baseline
  2. Steepest-ascent hill-climbing with restarts
  3. Simulated annealing
  4. Tabu search (short-term memory)

Fitness = 256 - hamming_weight(output_diff)
Goal: fitness = 256 (collision)

Collects: fitness distribution, local optima census, autocorrelation,
near-miss catalog.
"""

import time
import random
import struct
import sys

# SHA-256 functions
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

M = 0xFFFFFFFF  # 32-bit mask

def popcount(x):
    """Count set bits."""
    c = 0
    while x:
        c += 1
        x &= x - 1
    return c


def precompute():
    """Precompute states and schedule for both messages through round 56."""
    M1 = [0x17149975] + [0xffffffff] * 15
    M2 = M1.copy()
    M2[0] ^= 0x80000000
    M2[9] ^= 0x80000000

    results = []
    for msg in [M1, M2]:
        W = [0] * 57
        for i in range(16):
            W[i] = msg[i]
        for i in range(16, 57):
            W[i] = (sigma1(W[i-2]) + W[i-7] + sigma0(W[i-15]) + W[i-16]) & M
        a, b, c, d, e, f, g, h = IV
        for i in range(57):
            T1 = (h + Sigma1(e) + Ch(e, f, g) + K[i] + W[i]) & M
            T2 = (Sigma0(a) + Maj(a, b, c)) & M
            h = g; g = f; f = e; e = (d + T1) & M
            d = c; c = b; b = a; a = (T1 + T2) & M
        results.append(((a, b, c, d, e, f, g, h), W))

    return results[0], results[1]


# Precompute once
(STATE1, W1_PRE), (STATE2, W2_PRE) = precompute()


def evaluate_tail(w1_57, w1_58, w1_59, w1_60, w2_57, w2_58, w2_59, w2_60):
    """
    Run rounds 57-63 for both messages and return the output diff hamming weight.
    Lower hw = closer to collision. hw=0 = collision.
    """
    # Build schedule for msg1
    w1_61 = (sigma1(w1_59) + W1_PRE[54] + sigma0(W1_PRE[46]) + W1_PRE[45]) & M
    w1_62 = (sigma1(w1_60) + W1_PRE[55] + sigma0(W1_PRE[47]) + W1_PRE[46]) & M
    w1_63 = (sigma1(w1_61) + W1_PRE[56] + sigma0(W1_PRE[48]) + W1_PRE[47]) & M
    W1 = [w1_57, w1_58, w1_59, w1_60, w1_61, w1_62, w1_63]

    # Build schedule for msg2
    w2_61 = (sigma1(w2_59) + W2_PRE[54] + sigma0(W2_PRE[46]) + W2_PRE[45]) & M
    w2_62 = (sigma1(w2_60) + W2_PRE[55] + sigma0(W2_PRE[47]) + W2_PRE[46]) & M
    w2_63 = (sigma1(w2_61) + W2_PRE[56] + sigma0(W2_PRE[48]) + W2_PRE[47]) & M
    W2 = [w2_57, w2_58, w2_59, w2_60, w2_61, w2_62, w2_63]

    # Run 7 rounds for msg1
    a1, b1, c1, d1, e1, f1, g1, h1 = STATE1
    for i in range(7):
        T1 = (h1 + Sigma1(e1) + Ch(e1, f1, g1) + K[57+i] + W1[i]) & M
        T2 = (Sigma0(a1) + Maj(a1, b1, c1)) & M
        h1 = g1; g1 = f1; f1 = e1; e1 = (d1 + T1) & M
        d1 = c1; c1 = b1; b1 = a1; a1 = (T1 + T2) & M

    # Run 7 rounds for msg2
    a2, b2, c2, d2, e2, f2, g2, h2 = STATE2
    for i in range(7):
        T1 = (h2 + Sigma1(e2) + Ch(e2, f2, g2) + K[57+i] + W2[i]) & M
        T2 = (Sigma0(a2) + Maj(a2, b2, c2)) & M
        h2 = g2; g2 = f2; f2 = e2; e2 = (d2 + T1) & M
        d2 = c2; c2 = b2; b2 = a2; a2 = (T1 + T2) & M

    # Total diff hamming weight
    total_hw = 0
    for v1, v2 in [(a1,a2),(b1,b2),(c1,c2),(d1,d2),(e1,e2),(f1,f2),(g1,g2),(h1,h2)]:
        total_hw += popcount(v1 ^ v2)

    return total_hw


def random_words():
    """Generate 8 random 32-bit words (W1[57..60], W2[57..60])."""
    return tuple(random.getrandbits(32) for _ in range(8))


def flip_bit(words, idx):
    """Flip bit idx in the 256-bit word tuple (8 x 32-bit)."""
    word_idx = idx // 32
    bit_pos = idx % 32
    lst = list(words)
    lst[word_idx] ^= (1 << bit_pos)
    return tuple(lst)


def fitness(words):
    """256 - hw(output_diff). Max 256 = collision."""
    hw = evaluate_tail(*words)
    return 256 - hw


def random_search(n_evals):
    """Pure random baseline."""
    best_fit = 0
    best_words = None
    fits = []

    for _ in range(n_evals):
        w = random_words()
        f = fitness(w)
        fits.append(f)
        if f > best_fit:
            best_fit = f
            best_words = w

    return best_fit, best_words, fits


def hill_climb(n_restarts, max_steps_per_restart):
    """Steepest-ascent hill climbing with random restarts."""
    best_fit = 0
    best_words = None
    all_optima = []
    total_evals = 0

    for restart in range(n_restarts):
        current = random_words()
        current_fit = fitness(current)
        total_evals += 1

        for step in range(max_steps_per_restart):
            # Find best single-bit flip
            best_neighbor_fit = current_fit
            best_neighbor = current

            for bit in range(256):
                neighbor = flip_bit(current, bit)
                nf = fitness(neighbor)
                total_evals += 1
                if nf > best_neighbor_fit:
                    best_neighbor_fit = nf
                    best_neighbor = neighbor

            if best_neighbor_fit <= current_fit:
                break  # Local optimum
            current = best_neighbor
            current_fit = best_neighbor_fit

        all_optima.append(current_fit)
        if current_fit > best_fit:
            best_fit = current_fit
            best_words = current
            print(f"  Restart {restart}: new best = {best_fit}/256 (hw={256-best_fit})")

    return best_fit, best_words, all_optima, total_evals


def simulated_annealing(n_evals, T_start=50.0, T_end=0.01):
    """Simulated annealing with geometric cooling."""
    import math

    current = random_words()
    current_fit = fitness(current)
    best_fit = current_fit
    best_words = current
    fits = []

    alpha = (T_end / T_start) ** (1.0 / n_evals)
    T = T_start

    for i in range(n_evals):
        # Random single-bit flip
        bit = random.randint(0, 255)
        neighbor = flip_bit(current, bit)
        nf = fitness(neighbor)

        delta = nf - current_fit
        if delta > 0 or random.random() < math.exp(delta / T):
            current = neighbor
            current_fit = nf

        if current_fit > best_fit:
            best_fit = current_fit
            best_words = current

        T *= alpha
        fits.append(current_fit)

    return best_fit, best_words, fits


def autocorrelation_sample(n_walks, walk_length):
    """Estimate fitness autocorrelation as a function of Hamming distance."""
    # For each walk: start at random point, flip one bit at a time, record fitness
    corr_data = {}  # distance -> list of (f0, fd) pairs

    for _ in range(n_walks):
        w = random_words()
        f0 = fitness(w)

        current = w
        for d in range(1, walk_length + 1):
            bit = random.randint(0, 255)
            current = flip_bit(current, bit)
            fd = fitness(current)
            if d not in corr_data:
                corr_data[d] = []
            corr_data[d].append((f0, fd))

    return corr_data


def main():
    n_evals = int(sys.argv[1]) if len(sys.argv) > 1 else 100000
    print("=" * 70)
    print("SHA-256 sr=60 Fitness Landscape Analysis")
    print(f"Total budget: ~{n_evals} evaluations")
    print("=" * 70)

    # Verify precomputation
    assert STATE1[0] == STATE2[0], f"da[56] must be 0, got {STATE1[0]^STATE2[0]:#x}"
    print(f"da[56] = 0 verified. State diff hw at round 56:")
    total_hw = sum(popcount(STATE1[i] ^ STATE2[i]) for i in range(8))
    for i, name in enumerate("abcdefgh"):
        d = STATE1[i] ^ STATE2[i]
        print(f"  d{name}[56] = {d:08x} (hw={popcount(d)})")
    print(f"  Total: {total_hw}")

    # 1. Random baseline
    print(f"\n{'='*70}")
    print("1. Random Search Baseline")
    print(f"{'='*70}")
    n_random = min(n_evals // 4, 50000)
    t0 = time.time()
    best_rand, _, rand_fits = random_search(n_random)
    t_rand = time.time() - t0
    print(f"  {n_random} evals in {t_rand:.1f}s ({n_random/t_rand:.0f} evals/sec)")
    print(f"  Best fitness: {best_rand}/256 (hw={256-best_rand})")
    print(f"  Mean fitness: {sum(rand_fits)/len(rand_fits):.1f}")
    print(f"  Min hw: {256 - max(rand_fits)}")

    # Fitness distribution
    hist = {}
    for f in rand_fits:
        bucket = f // 4 * 4
        hist[bucket] = hist.get(bucket, 0) + 1
    print(f"\n  Fitness distribution (bucketed by 4):")
    for bucket in sorted(hist.keys()):
        bar = "#" * (hist[bucket] * 60 // max(hist.values()))
        print(f"    {bucket:3d}-{bucket+3:3d}: {hist[bucket]:5d} {bar}")

    # 2. Hill Climbing
    print(f"\n{'='*70}")
    print("2. Steepest-Ascent Hill Climbing")
    print(f"{'='*70}")
    n_restarts = 20
    max_steps = 50
    t0 = time.time()
    best_hc, best_hc_words, optima, hc_evals = hill_climb(n_restarts, max_steps)
    t_hc = time.time() - t0
    print(f"  {n_restarts} restarts, {hc_evals} total evals in {t_hc:.1f}s")
    print(f"  Best fitness: {best_hc}/256 (hw={256-best_hc})")
    print(f"  Local optima distribution: min={min(optima)}, max={max(optima)}, "
          f"mean={sum(optima)/len(optima):.1f}")

    # 3. Simulated Annealing
    print(f"\n{'='*70}")
    print("3. Simulated Annealing")
    print(f"{'='*70}")
    n_sa = min(n_evals // 2, 500000)
    t0 = time.time()
    best_sa, best_sa_words, sa_fits = simulated_annealing(n_sa)
    t_sa = time.time() - t0
    print(f"  {n_sa} evals in {t_sa:.1f}s")
    print(f"  Best fitness: {best_sa}/256 (hw={256-best_sa})")
    # Show trajectory: fitness at 10%, 25%, 50%, 75%, 90%
    for pct in [10, 25, 50, 75, 90, 100]:
        idx = min(int(n_sa * pct / 100) - 1, len(sa_fits) - 1)
        print(f"    At {pct:3d}%: fitness={sa_fits[idx]}")

    # 4. Autocorrelation
    print(f"\n{'='*70}")
    print("4. Fitness Autocorrelation")
    print(f"{'='*70}")
    corr_data = autocorrelation_sample(200, 20)
    print(f"  Distance vs correlation (r):")
    for d in sorted(corr_data.keys()):
        pairs = corr_data[d]
        if len(pairs) < 10:
            continue
        f0s = [p[0] for p in pairs]
        fds = [p[1] for p in pairs]
        mean0 = sum(f0s) / len(f0s)
        meand = sum(fds) / len(fds)
        var0 = sum((x - mean0)**2 for x in f0s) / len(f0s)
        vard = sum((x - meand)**2 for x in fds) / len(fds)
        if var0 > 0 and vard > 0:
            cov = sum((f0s[i] - mean0) * (fds[i] - meand) for i in range(len(pairs))) / len(pairs)
            r = cov / (var0 * vard) ** 0.5
        else:
            r = 0
        bar = "#" * int(max(0, r) * 40)
        print(f"    d={d:2d}: r={r:.3f} {bar}")

    # 5. Near-miss catalog
    print(f"\n{'='*70}")
    print("5. Best Results (Near-Miss Catalog)")
    print(f"{'='*70}")
    overall_best = max(best_rand, best_hc, best_sa)
    print(f"  Overall best fitness: {overall_best}/256 (hw={256-overall_best})")
    print(f"  Bits from collision: {256 - overall_best}")

    if best_hc == overall_best and best_hc_words:
        print(f"\n  Best assignment (from hill-climbing):")
        for i in range(4):
            print(f"    W1[{57+i}] = 0x{best_hc_words[i]:08x}")
        for i in range(4):
            print(f"    W2[{57+i}] = 0x{best_hc_words[4+i]:08x}")

    print(f"\n{'='*70}")
    print("INTERPRETATION")
    print(f"{'='*70}")
    if overall_best < 200:
        print("  The cascade rounds act as a strong pseudo-random barrier.")
        print("  Gradient-based and SLS approaches are unlikely to bridge the gap.")
        print("  --> Focus on exact methods (SAT/SMT) or structural decomposition.")
    elif overall_best < 240:
        print("  The landscape has reachable near-misses.")
        print("  --> Worth investing in larger SA runs or hybrid SLS+SAT.")
    elif overall_best < 256:
        print("  Very close! Near-miss with only a few bits off.")
        print("  --> Try SAT solver seeded with this assignment.")
    else:
        print("  [!!!] COLLISION FOUND via SLS!")


if __name__ == "__main__":
    main()
