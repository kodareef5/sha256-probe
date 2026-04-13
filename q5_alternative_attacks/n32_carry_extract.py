#!/usr/bin/env python3
"""
Extract carry-diff values from the known N=32 sr=60 collision certificate.
Identifies structurally invariant carries based on the pattern verified at N=8-12.

Uses full SHA-256 (not mini-SHA) via lib/sha256.py.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from lib.sha256 import K, IV, Sigma0, Sigma1, sigma0, sigma1, Ch, Maj, add, MASK

# Known N=32 sr=60 collision certificate (from CLAIMS.md)
M0_VAL = 0x17149975
FILL = 0xFFFFFFFF
W1_FREE = [0x9ccfa55e, 0xd9d64416, 0x9e3ffb08, 0xb6befe82]
W2_FREE = [0x72e6c8cd, 0x4b96ca51, 0x587ffaa6, 0xea3ce26b]

def precompute_state(M):
    """Run 57 rounds, return (state, W[0..56])"""
    W = list(M) + [0]*41
    for i in range(16, 57):
        W[i] = add(sigma1(W[i-2]), W[i-7], sigma0(W[i-15]), W[i-16])
    a, b, c, d, e, f, g, h = IV
    for i in range(57):
        T1 = add(h, Sigma1(e), Ch(e, f, g), K[i], W[i])
        T2 = add(Sigma0(a), Maj(a, b, c))
        h, g, f, e, d, c, b, a = g, f, e, add(d, T1), c, b, a, add(T1, T2)
    return [a, b, c, d, e, f, g, h], W

def extract_carries_2op(a, b, N=32):
    """Extract carry bits from a+b mod 2^N. Returns carry[0..N-1]."""
    carries = []
    c = 0
    for k in range(N):
        ak = (a >> k) & 1
        bk = (b >> k) & 1
        s = ak + bk + c
        c = s >> 1
        carries.append(c)
    return carries

def sha_round_with_carries(state, k_val, w_val):
    """Run one SHA-256 round, returning (new_state, carries_dict)."""
    a, b, c, d, e, f, g, h = state
    sig1_e = Sigma1(e)
    ch_efg = Ch(e, f, g)
    sig0_a = Sigma0(a)
    maj_abc = Maj(a, b, c)

    # T1 chain
    t0 = add(h, sig1_e)
    c_hsig1 = extract_carries_2op(h, sig1_e)
    t1 = add(t0, ch_efg)
    c_ch = extract_carries_2op(t0, ch_efg)
    t2 = add(t1, k_val)
    c_k = extract_carries_2op(t1, k_val)
    T1 = add(t2, w_val)
    c_w = extract_carries_2op(t2, w_val)

    # T2
    T2 = add(sig0_a, maj_abc)
    c_sig0maj = extract_carries_2op(sig0_a, maj_abc)

    # new_e = d + T1
    new_e = add(d, T1)
    c_dt1 = extract_carries_2op(d, T1)

    # new_a = T1 + T2
    new_a = add(T1, T2)
    c_t1t2 = extract_carries_2op(T1, T2)

    new_state = [new_a, a, b, c, new_e, e, f, g]
    carries = {
        'h+Sig1': c_hsig1,
        '+Ch': c_ch,
        '+K': c_k,
        '+W': c_w,
        'S0+Maj': c_sig0maj,
        'd+T1': c_dt1,
        'T1+T2': c_t1t2,
    }
    return new_state, carries

ADD_NAMES = ['h+Sig1', '+Ch', '+K', '+W', 'S0+Maj', 'd+T1', 'T1+T2']

def main():
    # Build messages
    M1 = [M0_VAL] + [FILL]*15
    M2 = list(M1)
    M2[0] = M1[0] ^ (1 << 31)  # MSB kernel
    M2[9] = FILL ^ (1 << 31)

    # Precompute
    state1, W1pre = precompute_state(M1)
    state2, W2pre = precompute_state(M2)

    print(f"da[56] = {state1[0] ^ state2[0]:08x} (should be 0)")
    if state1[0] != state2[0]:
        print("ERROR: da[56] != 0!")
        return

    # Build W[57..63] for both paths
    W1 = W1_FREE[:4]
    W2 = W2_FREE[:4]
    # Schedule: W[61] = sigma1(W[59]) + W[54] + sigma0(W[46]) + W[45]
    W1.append(add(sigma1(W1[2]), W1pre[54], sigma0(W1pre[46]), W1pre[45]))  # W1[61]
    W2.append(add(sigma1(W2[2]), W2pre[54], sigma0(W2pre[46]), W2pre[45]))
    W1.append(add(sigma1(W1[3]), W1pre[55], sigma0(W1pre[47]), W1pre[46]))  # W1[62]
    W2.append(add(sigma1(W2[3]), W2pre[55], sigma0(W2pre[47]), W2pre[46]))
    W1.append(add(sigma1(W1[4]), W1pre[56], sigma0(W1pre[48]), W1pre[47]))  # W1[63]
    W2.append(add(sigma1(W2[4]), W2pre[56], sigma0(W2pre[48]), W2pre[47]))

    # Verify collision
    s1 = list(state1)
    s2 = list(state2)
    for r in range(7):
        s1, _ = sha_round_with_carries(s1, K[57+r], W1[r])
        s2, _ = sha_round_with_carries(s2, K[57+r], W2[r])
    diff = 0
    for i in range(8):
        diff |= s1[i] ^ s2[i]
    print(f"Collision verified: {'YES' if diff == 0 else 'NO (diff=%08x)' % diff}\n")

    # Extract carries for both paths
    s1 = list(state1)
    s2 = list(state2)
    all_carries1 = []
    all_carries2 = []
    for r in range(7):
        s1, c1 = sha_round_with_carries(s1, K[57+r], W1[r])
        s2, c2 = sha_round_with_carries(s2, K[57+r], W2[r])
        all_carries1.append(c1)
        all_carries2.append(c2)

    # Compute carry-diffs
    print("=== Carry-Diff Extraction at N=32 ===\n")
    total_bits = 0
    total_invariant_by_structure = 0

    # Structural invariance pattern (verified at N=8, 10, 12):
    # Round 57: h+Sig1, +Ch, +K, S0+Maj are invariant
    # Round 59+: S0+Maj, d+T1, T1+T2 are invariant
    # (Round 58 is mostly variable)
    structural_invariant = {}
    for r in range(7):
        for add_name in ADD_NAMES:
            rnd = 57 + r
            is_inv = False
            if rnd == 57 and add_name in ['h+Sig1', '+Ch', '+K', 'S0+Maj']:
                is_inv = True
            if rnd >= 59 and add_name in ['S0+Maj', 'd+T1', 'T1+T2']:
                is_inv = True
            structural_invariant[(r, add_name)] = is_inv

    print(f"{'Round':>5}  {'Addition':>10}  {'Inv?':>5}  {'HW(cdiff)':>10}  {'cdiff[0]':>8}  {'cdiff[31]':>9}")
    print("-" * 60)

    invariant_carry_diffs = {}
    for r in range(7):
        for add_name in ADD_NAMES:
            c1 = all_carries1[r][add_name]
            c2 = all_carries2[r][add_name]
            cdiff = [c1[k] ^ c2[k] for k in range(32)]
            hw = sum(cdiff)
            is_inv = structural_invariant[(r, add_name)]
            if is_inv:
                total_invariant_by_structure += 32
                # Store for SAT encoding
                invariant_carry_diffs[(57+r, add_name)] = cdiff
            total_bits += 32
            tag = "***" if is_inv else ""
            print(f"  {57+r}  {add_name:>10}  {tag:>5}  {hw:>10}  {cdiff[0]:>8}  {cdiff[31]:>9}")

    print(f"\nTotal carry-diff bits: {total_bits}")
    print(f"Structurally invariant: {total_invariant_by_structure} ({100*total_invariant_by_structure/total_bits:.1f}%)")
    print(f"Free: {total_bits - total_invariant_by_structure}")

    # Verify invariant carries are actually 0 (expected from cascade structure)
    print("\n=== Invariant Carry-Diff Values ===\n")
    n_zero = 0
    n_nonzero = 0
    for (rnd, add_name), cdiff in sorted(invariant_carry_diffs.items()):
        hw = sum(cdiff)
        if hw == 0:
            n_zero += 1
        else:
            n_nonzero += 1
            # This would mean the carry-diff is constant but NONZERO
            cdiff_hex = sum(b << k for k, b in enumerate(cdiff))
            print(f"  Round {rnd} {add_name}: HW={hw}, value=0x{cdiff_hex:08x}")

    print(f"\nInvariant additions with zero carry-diff: {n_zero}")
    print(f"Invariant additions with nonzero carry-diff: {n_nonzero}")
    print(f"(Nonzero = constant but != 0 — still usable as unit clauses)")

    # Summary for SAT encoder
    print("\n=== SAT Encoder Guidance ===\n")
    print(f"For carry-conditioned SAT at N=32:")
    print(f"  - Fix {total_invariant_by_structure} carry-diff bits as unit clauses")
    print(f"  - Search over {total_bits - total_invariant_by_structure} free carry-diff bits")
    print(f"  - This is {total_bits - total_invariant_by_structure} variables vs ~10K in standard encoding")

if __name__ == '__main__':
    main()
