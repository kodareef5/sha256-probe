#!/usr/bin/env python3
"""n_invariants.py — Parameterized N invariant probe across N in {8, 10, 12, 14}.

Replaces the buggy inline version. Tests:
  Theorem 4 (r=61):  da_61 ≡ de_61 (mod 2^N)
  R63.1:             dc_63 ≡ dg_63
  R63.3:             da_63 - de_63 ≡ dT2_63 (mod 2^N)
  de58 image size + hardlock pattern

Usage: python3 n_invariants.py [N1 N2 ...]
       defaults to {8, 10, 12, 14}.
"""
import random
import sys

K32 = [0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5,
       0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
       0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3,
       0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
       0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc,
       0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
       0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7,
       0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
       0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13,
       0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
       0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3,
       0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
       0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5,
       0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
       0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208,
       0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2]
IV32 = [0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
        0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19]


def make_helpers(N):
    MASK = (1 << N) - 1
    def scale_rot(k32):
        r = round(k32 * N / 32.0)
        return max(1, r)
    rS0 = (scale_rot(2),  scale_rot(13), scale_rot(22))
    rS1 = (scale_rot(6),  scale_rot(11), scale_rot(25))
    rs0 = (scale_rot(7),  scale_rot(18), scale_rot(3))
    rs1 = (scale_rot(17), scale_rot(19), scale_rot(10))
    K = [k & MASK for k in K32]
    IV = [v & MASK for v in IV32]
    def ror(x, k):
        k = k % N
        return ((x >> k) | (x << (N - k))) & MASK
    def Sigma0(a): return ror(a, rS0[0]) ^ ror(a, rS0[1]) ^ ror(a, rS0[2])
    def Sigma1(e): return ror(e, rS1[0]) ^ ror(e, rS1[1]) ^ ror(e, rS1[2])
    def sigma0(x): return ror(x, rs0[0]) ^ ror(x, rs0[1]) ^ ((x >> rs0[2]) & MASK)
    def sigma1(x): return ror(x, rs1[0]) ^ ror(x, rs1[1]) ^ ((x >> rs1[2]) & MASK)
    def Ch(e, f, g): return ((e & f) ^ ((~e) & g)) & MASK
    def Maj(a, b, c): return ((a & b) ^ (a & c) ^ (b & c)) & MASK
    def add(*xs):
        s = 0
        for x in xs: s = (s + x) & MASK
        return s
    def precompute_state(M):
        W = list(M) + [0] * 41
        for i in range(16, 57):
            W[i] = add(sigma1(W[i-2]), W[i-7], sigma0(W[i-15]), W[i-16])
        a, b, c, d, e, f, g, h = IV
        for i in range(57):
            T1 = add(h, Sigma1(e), Ch(e, f, g), K[i], W[i])
            T2 = add(Sigma0(a), Maj(a, b, c))
            h, g, f, e, d, c, b, a = g, f, e, add(d, T1), c, b, a, add(T1, T2)
        return (a, b, c, d, e, f, g, h), W
    def apply_round(s, w, r):
        T1 = add(s[7], Sigma1(s[4]), Ch(s[4], s[5], s[6]), K[r], w)
        T2 = add(Sigma0(s[0]), Maj(s[0], s[1], s[2]))
        return (add(T1, T2), s[0], s[1], s[2], add(s[3], T1), s[4], s[5], s[6])
    def cw1(s1, s2):
        dh = (s1[7] - s2[7]) & MASK
        dSig = (Sigma1(s1[4]) - Sigma1(s2[4])) & MASK
        dCh = (Ch(s1[4], s1[5], s1[6]) - Ch(s2[4], s2[5], s2[6])) & MASK
        T2_1 = (Sigma0(s1[0]) + Maj(s1[0], s1[1], s1[2])) & MASK
        T2_2 = (Sigma0(s2[0]) + Maj(s2[0], s2[1], s2[2])) & MASK
        return (dh + dSig + dCh + T2_1 - T2_2) & MASK
    def cw2(s1, s2):
        dh = (s1[7] - s2[7]) & MASK
        dSig = (Sigma1(s1[4]) - Sigma1(s2[4])) & MASK
        dCh = (Ch(s1[4], s1[5], s1[6]) - Ch(s2[4], s2[5], s2[6])) & MASK
        return (dh + dSig + dCh) & MASK
    return {
        'N': N, 'MASK': MASK, 'K': K, 'IV': IV,
        'Sigma0': Sigma0, 'Sigma1': Sigma1, 'sigma0': sigma0, 'sigma1': sigma1,
        'Ch': Ch, 'Maj': Maj, 'add': add,
        'precompute_state': precompute_state, 'apply_round': apply_round,
        'cw1': cw1, 'cw2': cw2,
    }


def find_eligible(h, fills):
    """Find first cascade-eligible (M0, fill) at N."""
    N, MASK = h['N'], h['MASK']
    pre = h['precompute_state']
    for fill in fills:
        for cand in range(MASK + 1):
            M1 = [cand] + [fill] * 15
            M2 = list(M1); M2[0] ^= 1 << (N - 1); M2[9] ^= 1 << (N - 1)
            s1, _ = pre(M1); s2, _ = pre(M2)
            if s1[0] == s2[0]:
                return cand, fill
    return None, None


def probe_at(N, n_samples=8192):
    h = make_helpers(N)
    MASK = h['MASK']
    pre = h['precompute_state']
    apply_round = h['apply_round']
    cw1, cw2 = h['cw1'], h['cw2']
    sigma0, sigma1 = h['sigma0'], h['sigma1']
    Sigma0, Maj = h['Sigma0'], h['Maj']
    add = h['add']

    fills = [MASK, 0, MASK ^ (MASK >> 1), MASK >> 1, 1 << (N - 1)]
    m0, fill = find_eligible(h, fills)
    if m0 is None:
        return f"N={N:2d}: no cascade-eligible (M0, fill) in {len(fills)} fill choices"

    M1 = [m0] + [fill] * 15
    M2 = list(M1); M2[0] ^= 1 << (N - 1); M2[9] ^= 1 << (N - 1)
    s1, W1pre = pre(M1); s2, W2pre = pre(M2)
    cw57 = cw1(s1, s2)

    rng = random.Random(42)
    th4_v = r631_v = r633_v = 0
    image = set()
    n_kept = 0
    for _ in range(n_samples):
        w57 = rng.randrange(MASK + 1)
        w2_57 = (w57 + cw57) & MASK
        s1_57 = apply_round(s1, w57, 57); s2_57 = apply_round(s2, w2_57, 57)
        if (s1_57[0] - s2_57[0]) & MASK != 0:
            continue
        cw58_v = cw1(s1_57, s2_57)
        s1_58 = apply_round(s1_57, 0, 58); s2_58 = apply_round(s2_57, cw58_v, 58)
        d58 = (s1_58[4] - s2_58[4]) & MASK
        image.add(d58)
        cw59_v = cw1(s1_58, s2_58)
        s1_59 = apply_round(s1_58, 0, 59); s2_59 = apply_round(s2_58, cw59_v, 59)
        cw60_v = cw2(s1_59, s2_59)
        s1_60 = apply_round(s1_59, 0, 60); s2_60 = apply_round(s2_59, cw60_v, 60)
        W1 = list(W1pre) + [w57, 0, 0, 0]
        W2 = list(W2pre) + [w2_57, cw58_v, cw59_v, cw60_v]
        for r in (61, 62, 63):
            W1.append(add(sigma1(W1[r-2]), W1[r-7], sigma0(W1[r-15]), W1[r-16]))
            W2.append(add(sigma1(W2[r-2]), W2[r-7], sigma0(W2[r-15]), W2[r-16]))
        s1_61 = apply_round(s1_60, W1[61], 61); s2_61 = apply_round(s2_60, W2[61], 61)
        s1_62 = apply_round(s1_61, W1[62], 62); s2_62 = apply_round(s2_61, W2[62], 62)
        s1_63 = apply_round(s1_62, W1[63], 63); s2_63 = apply_round(s2_62, W2[63], 63)

        da61 = (s1_61[0] - s2_61[0]) & MASK
        de61 = (s1_61[4] - s2_61[4]) & MASK
        if da61 != de61: th4_v += 1

        dc63 = (s1_63[2] - s2_63[2]) & MASK
        dg63 = (s1_63[6] - s2_63[6]) & MASK
        if dc63 != dg63: r631_v += 1

        da63 = (s1_63[0] - s2_63[0]) & MASK
        de63 = (s1_63[4] - s2_63[4]) & MASK
        dSig0 = (h['Sigma0'](s1_62[0]) - h['Sigma0'](s2_62[0])) & MASK
        dMaj = (h['Maj'](s1_62[0], s1_62[1], s1_62[2])
                - h['Maj'](s2_62[0], s2_62[1], s2_62[2])) & MASK
        dT2_63 = (dSig0 + dMaj) & MASK
        if ((da63 - de63) & MASK) != dT2_63: r633_v += 1

        n_kept += 1

    or_all = 0; and_all = MASK
    for v in image:
        or_all |= v; and_all &= v
    locked_mask = (~(or_all ^ and_all)) & MASK
    n_locked = bin(locked_mask).count('1')

    return (f"N={N:2d} M0=0x{m0:0{(N+3)//4}x} fill=0x{fill:0{(N+3)//4}x}: "
            f"image={len(image):>5}, locked={n_locked}/{N} ({n_locked*100//N}%), "
            f"Th4 ok={n_kept-th4_v}/{n_kept}, "
            f"R63.1 ok={n_kept-r631_v}/{n_kept}, "
            f"R63.3 ok={n_kept-r633_v}/{n_kept}")


def main():
    if len(sys.argv) > 1:
        Ns = [int(x) for x in sys.argv[1:]]
    else:
        Ns = [8, 10, 12, 14]
    print(f"Parameterized N invariant probe across {Ns}:")
    for N in Ns:
        print("  " + probe_at(N))


if __name__ == "__main__":
    main()
