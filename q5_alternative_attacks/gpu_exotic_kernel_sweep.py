#!/usr/bin/env python3
"""
GPU Exotic Kernel Sweep — test non-(0,9) word pairs at N=10

The standard kernel uses dM[0]=dM[9]=delta. This script tests
alternative word pairs: (0,1), (0,14), (1,4), (1,9), etc.

Key question: does a different word pair unlock more collisions?
"""
import sys, os, time, math
import torch

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

K32 = [0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,
       0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,
       0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,0xefbe4786,
       0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
       0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,
       0x06ca6351,0x14292967,0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,
       0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,
       0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
       0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,
       0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,
       0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2]
IV32 = [0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,
        0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19]


def scale_rot(k32, N):
    r = round(k32 * N / 32)
    return max(1, r)

def ror_n(x, k, N, MASK):
    k = k % N
    return ((x >> k) | (x << (N - k))) & MASK


class Params:
    def __init__(self, N):
        self.N = N
        self.MASK = (1 << N) - 1
        self.rS0 = [scale_rot(2,N), scale_rot(13,N), scale_rot(22,N)]
        self.rS1 = [scale_rot(6,N), scale_rot(11,N), scale_rot(25,N)]
        self.rs1 = [scale_rot(17,N), scale_rot(19,N)]
        self.ss1 = scale_rot(10,N)
        self.rs0 = [scale_rot(7,N), scale_rot(18,N)]
        self.ss0 = scale_rot(3,N)
        self.KN = [k & self.MASK for k in K32]
        self.IVN = [iv & self.MASK for iv in IV32]

    def _ror(self, x, k):
        return ror_n(x, k, self.N, self.MASK)
    def Sigma0(self, a): return self._ror(a, self.rS0[0]) ^ self._ror(a, self.rS0[1]) ^ self._ror(a, self.rS0[2])
    def Sigma1(self, e): return self._ror(e, self.rS1[0]) ^ self._ror(e, self.rS1[1]) ^ self._ror(e, self.rS1[2])
    def sigma0(self, x): return self._ror(x, self.rs0[0]) ^ self._ror(x, self.rs0[1]) ^ ((x >> self.ss0) & self.MASK)
    def sigma1(self, x): return self._ror(x, self.rs1[0]) ^ self._ror(x, self.rs1[1]) ^ ((x >> self.ss1) & self.MASK)
    def Ch(self, e, f, g): return ((e & f) ^ ((~e) & g)) & self.MASK
    def Maj(self, a, b, c): return ((a & b) ^ (a & c) ^ (b & c)) & self.MASK
    def sha_round(self, st, k, w):
        a,b,c,d,e,f,g,h = st
        T1 = (h + self.Sigma1(e) + self.Ch(e,f,g) + k + w) & self.MASK
        T2 = (self.Sigma0(a) + self.Maj(a,b,c)) & self.MASK
        return [(T1+T2)&self.MASK,a,b,c,(d+T1)&self.MASK,e,f,g]
    def cascade_offset(self, s1, s2, rnd):
        r1 = (s1[7]+self.Sigma1(s1[4])+self.Ch(s1[4],s1[5],s1[6])+self.KN[rnd])&self.MASK
        r2 = (s2[7]+self.Sigma1(s2[4])+self.Ch(s2[4],s2[5],s2[6])+self.KN[rnd])&self.MASK
        T21 = (self.Sigma0(s1[0])+self.Maj(s1[0],s1[1],s1[2]))&self.MASK
        T22 = (self.Sigma0(s2[0])+self.Maj(s2[0],s2[1],s2[2]))&self.MASK
        return (r1-r2+T21-T22)&self.MASK
    def precompute(self, M):
        W = list(M[:16])
        for i in range(16,57):
            W.append((self.sigma1(W[i-2])+W[i-7]+self.sigma0(W[i-15])+W[i-16])&self.MASK)
        a,b,c,d = self.IVN[:4]; e,f,g,h = self.IVN[4:]
        for i in range(57):
            T1=(h+self.Sigma1(e)+self.Ch(e,f,g)+self.KN[i]+W[i])&self.MASK
            T2=(self.Sigma0(a)+self.Maj(a,b,c))&self.MASK
            h,g,f,e=g,f,e,(d+T1)&self.MASK; d,c,b,a=c,b,a,(T1+T2)&self.MASK
        return [a,b,c,d,e,f,g,h], W


def find_exotic_candidate(p, word_pair, delta, fill):
    """Find candidate with given word pair and delta."""
    w1, w2 = word_pair
    for m0 in range(p.MASK + 1):
        M1 = [fill] * 16
        M2 = [fill] * 16
        M1[w1] = m0
        M2[w1] = m0 ^ delta
        M2[w2] = fill ^ delta
        s1, W1 = p.precompute(M1)
        s2, W2 = p.precompute(M2)
        if s1[0] == s2[0]:
            return m0, s1, s2, W1, W2
    return None


def count_collisions_cpu(p, s1_56, s2_56, W1p, W2p):
    """CPU cascade DP count (for validation at small N)."""
    N, MASK, SIZE = p.N, p.MASK, 1 << p.N
    total = 0
    for w57 in range(SIZE):
        cas57 = p.cascade_offset(s1_56, s2_56, 57)
        st1 = p.sha_round(s1_56, p.KN[57], w57)
        st2 = p.sha_round(s2_56, p.KN[57], (w57+cas57)&MASK)
        for w58 in range(SIZE):
            cas58 = p.cascade_offset(st1, st2, 58)
            st1_58 = p.sha_round(st1, p.KN[58], w58)
            st2_58 = p.sha_round(st2, p.KN[58], (w58+cas58)&MASK)
            for w59 in range(SIZE):
                cas59 = p.cascade_offset(st1_58, st2_58, 59)
                st1_59 = p.sha_round(st1_58, p.KN[59], w59)
                st2_59 = p.sha_round(st2_58, p.KN[59], (w59+cas59)&MASK)
                for w60 in range(SIZE):
                    cas60 = p.cascade_offset(st1_59, st2_59, 60)
                    w2_60 = (w60+cas60)&MASK
                    st1_60 = p.sha_round(st1_59, p.KN[60], w60)
                    st2_60 = p.sha_round(st2_59, p.KN[60], w2_60)
                    W1f = [w57,w58,w59,w60,0,0,0]
                    W2f = [(w57+p.cascade_offset(s1_56,s2_56,57))&MASK,
                           (w58+cas58)&MASK,(w59+cas59)&MASK,w2_60,0,0,0]
                    W1f[4] = (p.sigma1(W1f[2])+W1p[54]+p.sigma0(W1p[46])+W1p[45])&MASK
                    W2f[4] = (p.sigma1(W2f[2])+W2p[54]+p.sigma0(W2p[46])+W2p[45])&MASK
                    W1f[5] = (p.sigma1(W1f[3])+W1p[55]+p.sigma0(W1p[47])+W1p[46])&MASK
                    W2f[5] = (p.sigma1(W2f[3])+W2p[55]+p.sigma0(W2p[47])+W2p[46])&MASK
                    W1f[6] = (p.sigma1(W1f[4])+W1p[56]+p.sigma0(W1p[48])+W1p[47])&MASK
                    W2f[6] = (p.sigma1(W2f[4])+W2p[56]+p.sigma0(W2p[48])+W2p[47])&MASK
                    fs1, fs2 = list(st1_60), list(st2_60)
                    for r in range(4,7):
                        fs1 = p.sha_round(fs1, p.KN[57+r], W1f[r])
                        fs2 = p.sha_round(fs2, p.KN[57+r], W2f[r])
                    if all(fs1[r] == fs2[r] for r in range(8)):
                        total += 1
    return total


def main():
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 4

    p = Params(N)
    MASK = p.MASK
    fills = [MASK, 0, MASK >> 1]

    # Word pairs to test
    word_pairs = [
        (0, 9),   # Standard
        (0, 1),   # Adjacent
        (0, 14),  # Far
        (1, 4),   # Schedule-linked
        (1, 9),   # Shifted standard
        (0, 5),   # Mid
        (4, 9),   # Both in schedule window
    ]

    # Kernel deltas to test
    deltas = [1 << b for b in range(min(N, 4))]  # bits 0-3

    print(f"Exotic Kernel Sweep at N={N}")
    print(f"Testing {len(word_pairs)} word pairs × {len(deltas)} deltas × {len(fills)} fills")
    print(f"Device: {device}")
    print()

    results = []

    for wp in word_pairs:
        for delta in deltas:
            bit = delta.bit_length() - 1
            best_coll = 0
            best_m0 = None
            best_fill = None
            for fill in fills:
                cand = find_exotic_candidate(p, wp, delta, fill)
                if cand is None:
                    continue
                m0, s1, s2, W1, W2 = cand
                coll = count_collisions_cpu(p, s1, s2, W1, W2)
                if coll > best_coll:
                    best_coll = coll
                    best_m0 = m0
                    best_fill = fill

            wp_str = f"({wp[0]},{wp[1]})"
            if best_m0 is not None:
                print(f"  {wp_str:8s} bit={bit} M[0]=0x{best_m0:x} fill=0x{best_fill:x} → {best_coll} collisions")
            else:
                print(f"  {wp_str:8s} bit={bit} → no candidate")
            results.append((wp, bit, best_m0, best_fill, best_coll))

    # Summary
    print(f"\n{'='*60}")
    print(f"| Word pair | Bit | Collisions | vs (0,9) best |")
    print(f"|----------|-----|-----------|---------------|")
    std_best = max(r[4] for r in results if r[0] == (0,9))
    for wp, bit, m0, fill, coll in results:
        wp_str = f"({wp[0]},{wp[1]})"
        ratio = f"{coll/std_best:.2f}x" if std_best > 0 and coll > 0 else "—"
        print(f"| {wp_str:8s} | {bit} | {coll:9d} | {ratio:13s} |")

    # Save
    ts = time.strftime('%Y%m%d_%H%M')
    outdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')
    os.makedirs(outdir, exist_ok=True)
    outpath = os.path.join(outdir, f'{ts}_exotic_kernel_sweep_n{N}.md')
    with open(outpath, 'w') as f:
        f.write(f"# Exotic Kernel Sweep — N={N}\n\n")
        f.write(f"| Word pair | Bit | Collisions |\n")
        f.write(f"|----------|-----|------------|\n")
        for wp, bit, m0, fill, coll in results:
            f.write(f"| ({wp[0]},{wp[1]}) | {bit} | {coll} |\n")
    print(f"\nSaved: {outpath}")


if __name__ == '__main__':
    main()
