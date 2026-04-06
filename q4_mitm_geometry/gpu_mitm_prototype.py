#!/usr/bin/env python3
"""
GPU MITM prototype: meet-in-the-middle on the hard residue (g60, h60).

The MITM analysis shows 232/256 anchor bits are easy. Only g60 and h60
(the oldest e-register differences) are the bottleneck. This tool:

1. FORWARD: enumerate W1[57..60], compute state1 through round 60,
   extract (g1_60, h1_60) = the hard residue bits
2. BACKWARD: for target collision at round 63, work backwards from
   state63=state63' to find what (g60, h60) values are needed
3. MATCH: find W values where forward g60,h60 equals backward requirement

At reduced width N, this is feasible:
  N=8: 4 words × 8 bits = 2^32 forward, 2^32 backward. Tables fit in GPU.
  N=10: 2^40 — too large for tables, but we can do streaming MITM.

Usage: python3 gpu_mitm_prototype.py [N]
"""

import sys, os, time
import torch

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

K32 = [
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5,
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
    0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
]
IV32 = [0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
        0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19]


def scale_rot(k32, N):
    return max(1, round(k32 * N / 32))


def popcount32(x):
    x = x - ((x >> 1) & 0x55555555)
    x = (x & 0x33333333) + ((x >> 2) & 0x33333333)
    x = (x + (x >> 4)) & 0x0F0F0F0F
    x = x + (x >> 8)
    x = x + (x >> 16)
    return x & 0x3F


class MiniSHA:
    def __init__(self, N):
        self.N = N
        self.MASK = (1 << N) - 1
        self.MSB = 1 << (N - 1)
        self.rS0 = [scale_rot(2,N), scale_rot(13,N), scale_rot(22,N)]
        self.rS1 = [scale_rot(6,N), scale_rot(11,N), scale_rot(25,N)]
        self.rs0 = [scale_rot(7,N), scale_rot(18,N)]
        self.ss0 = scale_rot(3,N)
        self.rs1 = [scale_rot(17,N), scale_rot(19,N)]
        self.ss1 = scale_rot(10,N)
        self.K = [k & self.MASK for k in K32]
        self.IV = [v & self.MASK for v in IV32]

    def ror(self, x, k):
        k = k % self.N
        return ((x >> k) | (x << (self.N - k))) & self.MASK

    def Sigma0(self, a): return self.ror(a,self.rS0[0])^self.ror(a,self.rS0[1])^self.ror(a,self.rS0[2])
    def Sigma1(self, e): return self.ror(e,self.rS1[0])^self.ror(e,self.rS1[1])^self.ror(e,self.rS1[2])
    def sigma0(self, x): return self.ror(x,self.rs0[0])^self.ror(x,self.rs0[1])^((x>>self.ss0)&self.MASK)
    def sigma1(self, x): return self.ror(x,self.rs1[0])^self.ror(x,self.rs1[1])^((x>>self.ss1)&self.MASK)

    def compress57(self, M):
        W = list(M) + [0]*41
        for i in range(16, 57):
            W[i] = (self.sigma1(W[i-2]) + W[i-7] + self.sigma0(W[i-15]) + W[i-16]) & self.MASK
        a,b,c,d,e,f,g,h = self.IV
        for i in range(57):
            T1 = (h + self.Sigma1(e) + ((e&f)^((~e)&g)&self.MASK) + self.K[i] + W[i]) & self.MASK
            T2 = (self.Sigma0(a) + ((a&b)^(a&c)^(b&c))) & self.MASK
            h,g,f,e,d,c,b,a = g,f,e,(d+T1)&self.MASK,c,b,a,(T1+T2)&self.MASK
        return [a,b,c,d,e,f,g,h], W


def gpu_ror(x, k, N, mask):
    k = k % N
    return ((x >> k) | (x << (N - k))) & mask


def mitm_forward_n8(state, W_pre, sha, device):
    """
    FORWARD pass at N=8: enumerate ALL 2^32 (W57,W58,W59,W60) combos.
    For each, compute state through rounds 57-60 (4 rounds).
    Extract (g60, h60) = registers 6,7 after round 60.

    Returns: dict mapping (g60, h60) -> (w57, w58, w59, w60)
    """
    N = sha.N; MASK = sha.MASK
    mask = torch.tensor(MASK, dtype=torch.int32, device=device)
    rS0 = sha.rS0; rS1 = sha.rS1

    def do_S0(a): return gpu_ror(a,rS0[0],N,mask)^gpu_ror(a,rS0[1],N,mask)^gpu_ror(a,rS0[2],N,mask)
    def do_S1(e): return gpu_ror(e,rS1[0],N,mask)^gpu_ror(e,rS1[1],N,mask)^gpu_ror(e,rS1[2],N,mask)
    def do_round(st, Ki, Wi):
        a,b,c,d,e,f,g,h = st
        ch = ((e&f)^((~e)&g))&mask
        T1 = (h+do_S1(e)+ch+Ki+Wi)&mask
        maj = ((a&b)^(a&c)^(b&c))&mask
        T2 = (do_S0(a)+maj)&mask
        return [(T1+T2)&mask,a,b,c,(d+T1)&mask,e,f,g]

    K57 = [torch.tensor(sha.K[57+i], dtype=torch.int32, device=device) for i in range(4)]
    s = [torch.tensor(state[i], dtype=torch.int32, device=device) for i in range(8)]

    # Enumerate all 2^32 combos in batches
    BATCH = 1 << 22  # 4M per batch
    total = (1 << N) ** 4

    # We'll store (g60, h60) packed as a single int for lookup
    # At N=8: g60 and h60 are each 8 bits → packed into 16 bits
    table = {}
    t0 = time.time()

    for batch_start in range(0, total, BATCH):
        bs = min(BATCH, total - batch_start)
        idx = torch.arange(batch_start, batch_start + bs, dtype=torch.int64, device=device)
        w57 = (idx % (1 << N)).to(torch.int32)
        w58 = ((idx >> N) % (1 << N)).to(torch.int32)
        w59 = ((idx >> (2*N)) % (1 << N)).to(torch.int32)
        w60 = ((idx >> (3*N)) % (1 << N)).to(torch.int32)

        # 4 rounds: 57-60
        st = [si.expand(bs) for si in s]
        st = do_round(st, K57[0], w57)
        st = do_round(st, K57[1], w58)
        st = do_round(st, K57[2], w59)
        st = do_round(st, K57[3], w60)

        # Extract g60 (reg 6) and h60 (reg 7)
        g60 = st[6]; h60 = st[7]
        packed = ((g60.to(torch.int64) << N) | h60.to(torch.int64)).cpu()

        for i in range(bs):
            key = packed[i].item()
            if key not in table:
                table[key] = (w57[i].item(), w58[i].item(),
                              w59[i].item(), w60[i].item())

        if batch_start % (BATCH * 64) == 0:
            elapsed = time.time() - t0
            pct = (batch_start + bs) / total * 100
            print(f"  forward: {pct:.1f}%, {len(table)} unique (g60,h60) "
                  f"of {batch_start+bs} tested ({elapsed:.1f}s)", flush=True)

    elapsed = time.time() - t0
    coverage = len(table) / (1 << (2*N)) * 100
    print(f"  Forward complete: {len(table)} unique (g60,h60) out of "
          f"{1<<(2*N)} possible ({coverage:.1f}% coverage) in {elapsed:.1f}s")
    return table


def mitm_analysis(N):
    """Run MITM analysis at word width N."""
    print(f"\n{'='*60}")
    print(f"MITM ANALYSIS: N={N} bits")
    print(f"{'='*60}")

    sha = MiniSHA(N)
    MASK = sha.MASK; MSB = sha.MSB
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    # Find a candidate
    for m0 in range(min(MASK, 1 << 20)):
        M1 = [m0] + [MASK]*15
        M2 = list(M1); M2[0] = m0 ^ MSB; M2[9] = MASK ^ MSB
        s1, W1 = sha.compress57(M1)
        s2, W2 = sha.compress57(M2)
        if s1[0] == s2[0]:
            break
    else:
        print(f"No candidate at N={N}"); return

    print(f"Candidate: M[0]=0x{m0:x}, fill=0x{MASK:x}")
    print(f"Search space: 4 words × {N} bits = {4*N} bits = {(1<<N)**4:,}")
    print(f"Hard residue: (g60, h60) = {2*N} bits = {1<<(2*N):,} possible values")
    print()

    # Forward pass for message 1
    print("FORWARD pass (message 1):", flush=True)
    table1 = mitm_forward_n8(s1, W1, sha, device)

    print()
    print("FORWARD pass (message 2):", flush=True)
    table2 = mitm_forward_n8(s2, W2, sha, device)

    # MITM match: find (g60,h60) values that appear in BOTH tables
    print(f"\nMITM MATCH:")
    keys1 = set(table1.keys())
    keys2 = set(table2.keys())
    matches = keys1 & keys2
    print(f"  Table 1: {len(keys1)} unique (g60,h60)")
    print(f"  Table 2: {len(keys2)} unique (g60,h60)")
    print(f"  Matches: {len(matches)}")

    if matches:
        print(f"\n  *** {len(matches)} MITM MATCHES FOUND ***")
        print(f"  These are (g60,h60) values achievable by BOTH messages.")
        print(f"  Each match is a candidate for collision at rounds 61-63.")
        # Verify a few
        for key in list(matches)[:5]:
            w1 = table1[key]
            w2 = table2[key]
            g60 = (key >> N) & MASK
            h60 = key & MASK
            print(f"    (g60=0x{g60:x}, h60=0x{h60:x}): "
                  f"W1={[hex(x) for x in w1]}, W2={[hex(x) for x in w2]}")
    else:
        print(f"  No matches — g60,h60 spaces don't overlap for these 4 rounds.")
        print(f"  This means the bottleneck is NOT just g60,h60 at round 60.")


if __name__ == "__main__":
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    mitm_analysis(N)
