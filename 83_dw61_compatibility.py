#!/usr/bin/env python3
"""
Script 83: dW[61] Compatibility Analysis

The mini-SHA collision analysis revealed:
- Collisions succeed when schedule-determined dW[61] is absorbable
- dW[61] = sigma1(W1[59]) - sigma1(W2[59]) + C_candidate
- C_candidate is a constant determined by M[0] (and padding)

This script:
1. For each known candidate, computes C_candidate
2. Measures how "absorbable" C is (lower HW = better)
3. Analyzes what W[59] pair minimizes |dW[61]|
4. Compares with the mini-SHA cases where collision succeeded

The round-61 collision condition is:
  dT1_61 = dh_60 + dCh_60 + dW[61] = 0  (mod 2^N)
where dCh_60 = e_60 & df_60 ^ ~e_60 & dg_60 (exact when de_60=0)

So dW[61] must cancel -(dh_60 + dCh_60). The achievability depends on
whether sigma1(W1[59]) - sigma1(W2[59]) can reach the required value.
"""

import sys, random

MASK = 0xFFFFFFFF
def ror(x, n): return ((x >> n) | (x << (32 - n))) & MASK
def Ch(e, f, g): return ((e & f) ^ ((~e & MASK) & g))
def Maj(a, b, c): return ((a & b) ^ (a & c) ^ (b & c))
def S0(a): return ror(a,2) ^ ror(a,13) ^ ror(a,22)
def S1(e): return ror(e,6) ^ ror(e,11) ^ ror(e,25)
def s0(x): return ror(x,7) ^ ror(x,18) ^ (x>>3)
def s1(x): return ror(x,17) ^ ror(x,19) ^ (x>>10)
def hw(x): return bin(x & MASK).count('1')
def add(*args):
    s = 0
    for a in args: s = (s + a) & MASK
    return s

K = [0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
     0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
     0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
     0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
     0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
     0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
     0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
     0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2]
IV = [0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,
      0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19]


def precompute(M):
    W = list(M) + [0]*41
    for i in range(16, 57):
        W[i] = add(s1(W[i-2]), W[i-7], s0(W[i-15]), W[i-16])
    a,b,c,d,e,f,g,h = IV
    for i in range(57):
        T1 = add(h, S1(e), Ch(e,f,g), K[i], W[i])
        T2 = add(S0(a), Maj(a,b,c))
        h,g,f,e,d,c,b,a = g,f,e,add(d,T1),c,b,a,add(T1,T2)
    return [a,b,c,d,e,f,g,h], W


def compute_dw61_constant(W1_pre, W2_pre):
    """
    dW[61] = [s1(W1[59]) - s1(W2[59])] + C
    where C = (W1_pre[54] - W2_pre[54]) + (s0(W1_pre[46]) - s0(W2_pre[46])) + (W1_pre[45] - W2_pre[45])
    Returns C (the constant part).
    """
    return add(
        (W1_pre[54] - W2_pre[54]) & MASK,
        (s0(W1_pre[46]) - s0(W2_pre[46])) & MASK,
        (W1_pre[45] - W2_pre[45]) & MASK
    )


def sigma1_diff_range(n_samples=100000):
    """
    Sample the range of s1(x1) - s1(x2) to understand what values are reachable.
    Returns histogram of HW of the difference.
    """
    hw_counts = [0] * 33
    for _ in range(n_samples):
        x1 = random.getrandbits(32)
        x2 = random.getrandbits(32)
        diff = (s1(x1) - s1(x2)) & MASK
        hw_counts[hw(diff)] += 1
    return hw_counts


def analyze_candidate(m0, fill=0xffffffff):
    """Full dW[61] compatibility analysis for one candidate."""
    M1 = [m0] + [fill]*15
    M2 = list(M1); M2[0] ^= 0x80000000; M2[9] ^= 0x80000000

    state1, W1_pre = precompute(M1)
    state2, W2_pre = precompute(M2)

    if state1[0] != state2[0]:
        return None

    C = compute_dw61_constant(W1_pre, W2_pre)
    C_hw = hw(C)

    # Also compute the constant parts for W[62] and W[63]
    C62 = add(
        (W1_pre[55] - W2_pre[55]) & MASK,
        (s0(W1_pre[47]) - s0(W2_pre[47])) & MASK,
        (W1_pre[46] - W2_pre[46]) & MASK
    )
    C63_partial = add(
        (W1_pre[56] - W2_pre[56]) & MASK,
        (s0(W1_pre[48]) - s0(W2_pre[48])) & MASK,
        (W1_pre[47] - W2_pre[47]) & MASK
    )

    # State diff at round 56
    state_hw = sum(hw(state1[i] ^ state2[i]) for i in range(8))

    # Run the sr=59 collision trail to see state at round 60
    # (Use the known sr=59 free words if available, else random)
    sr59_W1 = [0x35ff2fce, 0x091194cf, 0x92290bc7, 0xc136a254, 0xc6841268]
    sr59_W2 = [0x0c16533d, 0x8792091f, 0x93a0f3b6, 0x8b270b72, 0x40110184]

    if m0 == 0x17149975 and fill == 0xffffffff:
        # Use known sr=59 collision
        W1_free4 = sr59_W1[:4]
        W2_free4 = sr59_W2[:4]
    else:
        W1_free4 = [random.getrandbits(32) for _ in range(4)]
        W2_free4 = [random.getrandbits(32) for _ in range(4)]

    # Run 4 rounds (57-60) to get state at round 60
    a1,b1,c1,d1,e1,f1,g1,h1 = state1
    a2,b2,c2,d2,e2,f2,g2,h2 = state2
    for i in range(4):
        T1a = add(h1, S1(e1), Ch(e1,f1,g1), K[57+i], W1_free4[i])
        T2a = add(S0(a1), Maj(a1,b1,c1))
        h1,g1,f1,e1,d1,c1,b1,a1 = g1,f1,e1,add(d1,T1a),c1,b1,a1,add(T1a,T2a)
        T1b = add(h2, S1(e2), Ch(e2,f2,g2), K[57+i], W2_free4[i])
        T2b = add(S0(a2), Maj(a2,b2,c2))
        h2,g2,f2,e2,d2,c2,b2,a2 = g2,f2,e2,add(d2,T1b),c2,b2,a2,add(T1b,T2b)

    # At round 60, compute what dW[61] NEEDS to be for da[61]=0
    # dCh_60 = e_60 & df_60 ^ ~e_60 & dg_60 (exact when de_60=0)
    dh_60 = (h1 ^ h2) & MASK  # XOR diff
    df_60 = f1 ^ f2
    dg_60 = g1 ^ g2
    de_60 = e1 ^ e2

    # For additive diff: we need dT1 = 0
    # dT1 = (h1 - h2) + (Ch1 - Ch2) + (W1[61] - W2[61]) = 0
    # This is modular arithmetic, not XOR
    Ch1_60 = Ch(e1, f1, g1)
    Ch2_60 = Ch(e2, f2, g2)
    dCh_add = (Ch1_60 - Ch2_60) & MASK
    dh_add = (h1 - h2) & MASK

    # Required: dW[61] = -(dh_add + dCh_add) mod 2^32
    required_dW61 = (-(dh_add + dCh_add)) & MASK
    required_hw = hw(required_dW61)

    # What dW[61] actually is: s1_diff + C
    # We need: s1(W1[59]) - s1(W2[59]) = required_dW61 - C
    needed_s1_diff = (required_dW61 - C) & MASK
    needed_hw = hw(needed_s1_diff)

    return {
        'm0': m0, 'fill': fill,
        'state_hw56': state_hw,
        'C_dw61': C, 'C_hw': C_hw,
        'C_dw62': C62, 'C62_hw': hw(C62),
        'de_60': de_60, 'de_60_hw': hw(de_60),
        'required_dW61': required_dW61, 'required_hw': required_hw,
        'needed_s1_diff': needed_s1_diff, 'needed_hw': needed_hw,
    }


if __name__ == "__main__":
    print("=" * 80)
    print("dW[61] COMPATIBILITY ANALYSIS")
    print("=" * 80)

    # Analyze known candidates
    candidates = [
        (0x17149975, 0xffffffff, "published (all-ones)"),
        (0xa22dc6c7, 0xffffffff, "second (all-ones)"),
        (0x9cfea9ce, 0x00000000, "zero-fill"),
        (0x3f239926, 0xaaaaaaaa, "alt-fill"),
    ]

    print(f"\n{'Candidate':>12} {'Fill':>12} {'hw56':>5} {'C_hw':>5} {'C62_hw':>6} "
          f"{'de60_hw':>7} {'req_hw':>6} {'need_hw':>7} Notes")
    print("-" * 90)

    for m0, fill, label in candidates:
        r = analyze_candidate(m0, fill)
        if r is None:
            print(f"0x{m0:08x}  0x{fill:08x}  da[56]!=0")
            continue

        notes = ""
        if r['de_60_hw'] == 0:
            notes += "de60=0! "
        if r['C_hw'] < 10:
            notes += "LOW C! "
        if r['needed_hw'] < 10:
            notes += "ACHIEVABLE? "

        print(f"0x{m0:08x}  0x{fill:08x}  {r['state_hw56']:4d}  {r['C_hw']:4d}   {r['C62_hw']:5d}  "
              f"{r['de_60_hw']:6d}  {r['required_hw']:5d}   {r['needed_hw']:6d}  {notes}{label}")

    # sigma1 difference reachability analysis
    print(f"\n{'='*60}")
    print("sigma1 DIFFERENCE REACHABILITY")
    print("How achievable is a target s1(x1)-s1(x2) value?")
    print(f"{'='*60}")

    hw_hist = sigma1_diff_range(500000)
    print(f"\nHW distribution of random s1(x1)-s1(x2):")
    print(f"{'HW':>4} {'Count':>8} {'Pct':>6}")
    total = sum(hw_hist)
    for h in range(33):
        if hw_hist[h] > 0:
            print(f"{h:4d} {hw_hist[h]:8d} {100*hw_hist[h]/total:5.1f}%")

    # For the published candidate, check if the required sigma1 diff is achievable
    print(f"\n{'='*60}")
    print("TARGETED SEARCH: Can we find W[59] pairs that match?")
    print(f"{'='*60}")

    for m0, fill, label in candidates:
        r = analyze_candidate(m0, fill)
        if r is None:
            continue

        target = r['needed_s1_diff']
        target_hw = r['needed_hw']

        # Random search for sigma1 diff close to target
        best_miss = 32
        best_pair = None
        for trial in range(2000000):
            x1 = random.getrandbits(32)
            x2 = random.getrandbits(32)
            actual = (s1(x1) - s1(x2)) & MASK
            miss = hw(actual ^ target)
            if miss < best_miss:
                best_miss = miss
                best_pair = (x1, x2)
                if miss == 0:
                    break

        print(f"\n{label} (M[0]=0x{m0:08x}):")
        print(f"  Target s1 diff: 0x{target:08x} (hw={target_hw})")
        print(f"  Best match after 2M trials: miss={best_miss} bits")
        if best_pair:
            x1, x2 = best_pair
            actual = (s1(x1) - s1(x2)) & MASK
            print(f"  W1[59]=0x{x1:08x}, W2[59]=0x{x2:08x}")
            print(f"  Actual s1 diff: 0x{actual:08x} (hw={hw(actual)})")
            dW61 = add(actual, r['C_dw61'])
            print(f"  Resulting dW[61]: 0x{dW61:08x} (hw={hw(dW61)})")
