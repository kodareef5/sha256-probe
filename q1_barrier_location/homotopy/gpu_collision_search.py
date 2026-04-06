#!/usr/bin/env python3
"""
GPU collision search for mini-SHA-256 precision homotopy.

Brute-forces or randomly searches free words W[57..60] on GPU using
PyTorch CUDA. Compares against CPU/Kissat pipeline.

Three modes:
  exhaustive  - enumerate all shared-free-word combos (N <= 10)
  random      - sample random free words on GPU (any N)
  benchmark   - run both GPU exhaustive and CPU Kissat, compare

Usage:
    python3 gpu_collision_search.py [N] [mode] [timeout]
    # N: word width (default 8)
    # mode: exhaustive|random|benchmark (default benchmark)
    # timeout: seconds for CPU Kissat (default 120)
"""

import sys, os, time, subprocess, tempfile, math
import torch

_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_root, '..', '..'))

# SHA-256 constants
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


class MiniSHA:
    """N-bit mini-SHA-256 for CPU precomputation."""
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

    def Sigma0(self, a):
        return self.ror(a, self.rS0[0]) ^ self.ror(a, self.rS0[1]) ^ self.ror(a, self.rS0[2])
    def Sigma1(self, e):
        return self.ror(e, self.rS1[0]) ^ self.ror(e, self.rS1[1]) ^ self.ror(e, self.rS1[2])
    def sigma0(self, x):
        return self.ror(x, self.rs0[0]) ^ self.ror(x, self.rs0[1]) ^ ((x >> self.ss0) & self.MASK)
    def sigma1(self, x):
        return self.ror(x, self.rs1[0]) ^ self.ror(x, self.rs1[1]) ^ ((x >> self.ss1) & self.MASK)

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

    def find_candidate(self, fill=None):
        """Find first M[0] producing da[56]=0."""
        if fill is None:
            fill = self.MASK
        max_m0 = min(self.MASK, (1 << 20) - 1)
        for m0 in range(max_m0 + 1):
            M1 = [m0] + [fill]*15
            M2 = list(M1); M2[0] = m0 ^ self.MSB; M2[9] = fill ^ self.MSB
            s1, _ = self.compress57(M1)
            s2, _ = self.compress57(M2)
            if s1[0] == s2[0]:
                return m0, fill
        return None, None


def popcount32(x):
    """Vectorized popcount for int32 tensor."""
    # Bit-parallel popcount (Hamming weight)
    x = x - ((x >> 1) & 0x55555555)
    x = (x & 0x33333333) + ((x >> 2) & 0x33333333)
    x = (x + (x >> 4)) & 0x0F0F0F0F
    x = x + (x >> 8)
    x = x + (x >> 16)
    return x & 0x3F


def gpu_ror(x, k, N, mask):
    """Batched rotation: x is (batch,) int32 tensor."""
    k = k % N
    return ((x >> k) | (x << (N - k))) & mask


def gpu_tail_search(state1, state2, W1_pre, W2_pre, sha, device,
                    batch_size=1 << 22, max_evals=None, timeout=120.0,
                    mode='exhaustive'):
    """
    GPU search over shared free words W[57..60].

    Returns: (best_hw, best_words, total_evals, elapsed)
    """
    N = sha.N
    MASK = sha.MASK
    total_space = (1 << N) ** 4  # 4 free words, each N bits

    if max_evals is None:
        max_evals = total_space if mode == 'exhaustive' else 10**10

    # Precompute schedule constants on GPU
    # W[61] = sigma1(W[59]) + W_pre[54] + sigma0(W_pre[46]) + W_pre[45]
    # These constants differ between messages
    w1_54 = torch.tensor(W1_pre[54], dtype=torch.int32, device=device)
    w2_54 = torch.tensor(W2_pre[54], dtype=torch.int32, device=device)
    w1_s0_46 = torch.tensor(sha.sigma0(W1_pre[46]), dtype=torch.int32, device=device)
    w2_s0_46 = torch.tensor(sha.sigma0(W2_pre[46]), dtype=torch.int32, device=device)
    w1_45 = torch.tensor(W1_pre[45], dtype=torch.int32, device=device)
    w2_45 = torch.tensor(W2_pre[45], dtype=torch.int32, device=device)
    w1_55 = torch.tensor(W1_pre[55], dtype=torch.int32, device=device)
    w2_55 = torch.tensor(W2_pre[55], dtype=torch.int32, device=device)
    w1_s0_47 = torch.tensor(sha.sigma0(W1_pre[47]), dtype=torch.int32, device=device)
    w2_s0_47 = torch.tensor(sha.sigma0(W2_pre[47]), dtype=torch.int32, device=device)
    w1_46 = torch.tensor(W1_pre[46], dtype=torch.int32, device=device)
    w2_46 = torch.tensor(W2_pre[46], dtype=torch.int32, device=device)
    w1_56 = torch.tensor(W1_pre[56], dtype=torch.int32, device=device)
    w2_56 = torch.tensor(W2_pre[56], dtype=torch.int32, device=device)
    w1_s0_48 = torch.tensor(sha.sigma0(W1_pre[48]), dtype=torch.int32, device=device)
    w2_s0_48 = torch.tensor(sha.sigma0(W2_pre[48]), dtype=torch.int32, device=device)
    w1_47 = torch.tensor(W1_pre[47], dtype=torch.int32, device=device)
    w2_47 = torch.tensor(W2_pre[47], dtype=torch.int32, device=device)

    K57 = [torch.tensor(sha.K[57+i], dtype=torch.int32, device=device) for i in range(7)]

    s1 = [torch.tensor(state1[i], dtype=torch.int32, device=device) for i in range(8)]
    s2 = [torch.tensor(state2[i], dtype=torch.int32, device=device) for i in range(8)]

    mask_t = torch.tensor(MASK, dtype=torch.int32, device=device)

    # Rotation amounts
    rS0 = sha.rS0; rS1 = sha.rS1
    rs1r = sha.rs1; ss1 = sha.ss1

    best_hw = 8 * N  # worst case
    best_words = None
    total_evals = 0
    t0 = time.time()

    def do_sigma1(x):
        return gpu_ror(x, rs1r[0], N, mask_t) ^ gpu_ror(x, rs1r[1], N, mask_t) ^ ((x >> ss1) & mask_t)

    def do_Sigma0(a):
        return gpu_ror(a, rS0[0], N, mask_t) ^ gpu_ror(a, rS0[1], N, mask_t) ^ gpu_ror(a, rS0[2], N, mask_t)

    def do_Sigma1(e):
        return gpu_ror(e, rS1[0], N, mask_t) ^ gpu_ror(e, rS1[1], N, mask_t) ^ gpu_ror(e, rS1[2], N, mask_t)

    def do_round(st, Ki, Wi):
        a,b,c,d,e,f,g,h = st
        ch = ((e & f) ^ ((~e) & g)) & mask_t
        T1 = (h + do_Sigma1(e) + ch + Ki + Wi) & mask_t
        maj = ((a & b) ^ (a & c) ^ (b & c)) & mask_t
        T2 = (do_Sigma0(a) + maj) & mask_t
        return [(T1 + T2) & mask_t, a, b, c, (d + T1) & mask_t, e, f, g]

    eval_idx = 0
    while eval_idx < max_evals:
        if time.time() - t0 > timeout:
            break

        this_batch = min(batch_size, max_evals - eval_idx)

        # Generate free words
        if mode == 'exhaustive':
            # Enumerate: treat eval_idx as a base-(2^N) number for 4 digits
            indices = torch.arange(eval_idx, eval_idx + this_batch,
                                   dtype=torch.int64, device=device)
            w57 = (indices % (1 << N)).to(torch.int32)
            w58 = ((indices >> N) % (1 << N)).to(torch.int32)
            w59 = ((indices >> (2*N)) % (1 << N)).to(torch.int32)
            w60 = ((indices >> (3*N)) % (1 << N)).to(torch.int32)
        else:
            # Random sampling
            w57 = torch.randint(0, 1 << N, (this_batch,), dtype=torch.int32, device=device)
            w58 = torch.randint(0, 1 << N, (this_batch,), dtype=torch.int32, device=device)
            w59 = torch.randint(0, 1 << N, (this_batch,), dtype=torch.int32, device=device)
            w60 = torch.randint(0, 1 << N, (this_batch,), dtype=torch.int32, device=device)

        # Schedule: W[61..63] for each message
        s1_w59 = do_sigma1(w59)
        w1_61 = (s1_w59 + w1_54 + w1_s0_46 + w1_45) & mask_t
        w2_61 = (s1_w59 + w2_54 + w2_s0_46 + w2_45) & mask_t

        s1_w60 = do_sigma1(w60)
        w1_62 = (s1_w60 + w1_55 + w1_s0_47 + w1_46) & mask_t
        w2_62 = (s1_w60 + w2_55 + w2_s0_47 + w2_46) & mask_t

        s1_w61_1 = do_sigma1(w1_61)
        s1_w61_2 = do_sigma1(w2_61)
        w1_63 = (s1_w61_1 + w1_56 + w1_s0_48 + w1_47) & mask_t
        w2_63 = (s1_w61_2 + w2_56 + w2_s0_48 + w2_47) & mask_t

        W1_tail = [w57, w58, w59, w60, w1_61, w1_62, w1_63]
        W2_tail = [w57, w58, w59, w60, w2_61, w2_62, w2_63]

        # Run 7 tail rounds for message 1
        st1 = [s.expand(this_batch) for s in s1]
        for i in range(7):
            st1 = do_round(st1, K57[i], W1_tail[i])

        # Run 7 tail rounds for message 2
        st2 = [s.expand(this_batch) for s in s2]
        for i in range(7):
            st2 = do_round(st2, K57[i], W2_tail[i])

        # Collision check: HW of XOR across all 8 registers
        total_hw = torch.zeros(this_batch, dtype=torch.int32, device=device)
        for i in range(8):
            diff = st1[i] ^ st2[i]
            total_hw = total_hw + popcount32(diff)

        # Check for collision
        min_hw_batch = total_hw.min().item()
        if min_hw_batch < best_hw:
            best_hw = min_hw_batch
            idx = total_hw.argmin().item()
            best_words = (w57[idx].item(), w58[idx].item(),
                          w59[idx].item(), w60[idx].item())
            elapsed = time.time() - t0
            print(f"  new best HW={best_hw} at eval {eval_idx + idx} "
                  f"({elapsed:.2f}s) W=[0x{best_words[0]:x}, 0x{best_words[1]:x}, "
                  f"0x{best_words[2]:x}, 0x{best_words[3]:x}]", flush=True)

        if best_hw == 0:
            break

        eval_idx += this_batch
        total_evals += this_batch

    elapsed = time.time() - t0
    return best_hw, best_words, total_evals, elapsed


def cpu_kissat_solve(N, m0, fill, timeout):
    """Run the CPU pipeline: encode CNF + Kissat."""
    spec = __import__('50_precision_homotopy',
                      fromlist=['MiniSHA256', 'MiniCNFBuilder'])
    MiniSHA256 = spec.MiniSHA256
    MiniCNFBuilder = spec.MiniCNFBuilder

    sha = MiniSHA256(N)
    MASK = sha.MASK; MSB = sha.MSB
    M1 = [m0] + [fill]*15
    M2 = list(M1); M2[0] = m0 ^ MSB; M2[9] = fill ^ MSB
    s1, W1 = sha.compress(M1)
    s2, W2 = sha.compress(M2)
    if s1[0] != s2[0]:
        return None, None

    ops = {'r_Sig0':sha.r_Sig0, 'r_Sig1':sha.r_Sig1,
           'r_sig0':sha.r_sig0, 's_sig0':sha.s_sig0,
           'r_sig1':sha.r_sig1, 's_sig1':sha.s_sig1}
    KT = [k & MASK for k in K32]

    cnf = MiniCNFBuilder(N)
    st1 = tuple(cnf.const_word(v) for v in s1)
    st2 = tuple(cnf.const_word(v) for v in s2)
    w1f = [cnf.free_word(f"W1_{57+i}") for i in range(4)]
    w2f = [cnf.free_word(f"W2_{57+i}") for i in range(4)]

    def s1w(x): return cnf.sigma1_w(x, ops['r_sig1'], ops['s_sig1'])
    def s0w(x): return cnf.sigma0_w(x, ops['r_sig0'], ops['s_sig0'])

    w1_61 = cnf.add_word(cnf.add_word(s1w(w1f[2]),cnf.const_word(W1[54])),
                         cnf.add_word(cnf.const_word(sha.sigma0(W1[46])),cnf.const_word(W1[45])))
    w2_61 = cnf.add_word(cnf.add_word(s1w(w2f[2]),cnf.const_word(W2[54])),
                         cnf.add_word(cnf.const_word(sha.sigma0(W2[46])),cnf.const_word(W2[45])))
    w1_62 = cnf.add_word(cnf.add_word(s1w(w1f[3]),cnf.const_word(W1[55])),
                         cnf.add_word(cnf.const_word(sha.sigma0(W1[47])),cnf.const_word(W1[46])))
    w2_62 = cnf.add_word(cnf.add_word(s1w(w2f[3]),cnf.const_word(W2[55])),
                         cnf.add_word(cnf.const_word(sha.sigma0(W2[47])),cnf.const_word(W2[46])))
    w1_63 = cnf.add_word(cnf.add_word(s1w(w1_61),cnf.const_word(W1[56])),
                         cnf.add_word(cnf.const_word(sha.sigma0(W1[48])),cnf.const_word(W1[47])))
    w2_63 = cnf.add_word(cnf.add_word(s1w(w2_61),cnf.const_word(W2[56])),
                         cnf.add_word(cnf.const_word(sha.sigma0(W2[48])),cnf.const_word(W2[47])))

    W1s = list(w1f)+[w1_61,w1_62,w1_63]
    W2s = list(w2f)+[w2_61,w2_62,w2_63]

    for i in range(7):
        st1 = cnf.sha256_round(st1, KT[57+i], W1s[i], ops)
    for i in range(7):
        st2 = cnf.sha256_round(st2, KT[57+i], W2s[i], ops)
    for i in range(8):
        cnf.eq_word(st1[i], st2[i])

    td = tempfile.mkdtemp(prefix=f"bench_N{N}_")
    f = os.path.join(td, f"m0_{m0:x}.cnf")
    nv, nc = cnf.write_dimacs(f)
    print(f"  CNF: {nv} vars, {nc} clauses", flush=True)

    t0 = time.time()
    try:
        r = subprocess.run(["kissat", "-q", f], capture_output=True, timeout=timeout)
        elapsed = time.time() - t0
        if r.returncode == 10:
            return "SAT", elapsed
        elif r.returncode == 20:
            return "UNSAT", elapsed
        else:
            return f"rc={r.returncode}", elapsed
    except subprocess.TimeoutExpired:
        return "TIMEOUT", timeout


def gpu_independent_search(state1, state2, W1_pre, W2_pre, sha, device,
                           batch_size=1 << 20, timeout=120.0):
    """
    GPU search with INDEPENDENT free words for each message.
    Uses random sampling since 2^(8N) is too large for exhaustive.
    """
    N = sha.N
    MASK = sha.MASK
    mask_t = torch.tensor(MASK, dtype=torch.int32, device=device)

    # Precompute constants (same as above)
    consts = {}
    for key, idx in [('w1_54',54),('w2_54',54),('w1_45',45),('w2_45',45),
                     ('w1_55',55),('w2_55',55),('w1_46',46),('w2_46',46),
                     ('w1_56',56),('w2_56',56),('w1_47',47),('w2_47',47)]:
        pre = W1_pre if key.startswith('w1') else W2_pre
        consts[key] = torch.tensor(pre[idx], dtype=torch.int32, device=device)
    for key, idx in [('w1_s0_46',46),('w2_s0_46',46),('w1_s0_47',47),
                     ('w2_s0_47',47),('w1_s0_48',48),('w2_s0_48',48)]:
        pre = W1_pre if key.startswith('w1') else W2_pre
        consts[key] = torch.tensor(sha.sigma0(pre[idx]), dtype=torch.int32, device=device)

    K57 = [torch.tensor(sha.K[57+i], dtype=torch.int32, device=device) for i in range(7)]
    s1 = [torch.tensor(state1[i], dtype=torch.int32, device=device) for i in range(8)]
    s2 = [torch.tensor(state2[i], dtype=torch.int32, device=device) for i in range(8)]

    rS0 = sha.rS0; rS1 = sha.rS1
    rs1r = sha.rs1; ss1 = sha.ss1

    def do_sigma1(x):
        return gpu_ror(x, rs1r[0], N, mask_t) ^ gpu_ror(x, rs1r[1], N, mask_t) ^ ((x >> ss1) & mask_t)
    def do_Sigma0(a):
        return gpu_ror(a, rS0[0], N, mask_t) ^ gpu_ror(a, rS0[1], N, mask_t) ^ gpu_ror(a, rS0[2], N, mask_t)
    def do_Sigma1(e):
        return gpu_ror(e, rS1[0], N, mask_t) ^ gpu_ror(e, rS1[1], N, mask_t) ^ gpu_ror(e, rS1[2], N, mask_t)
    def do_round(st, Ki, Wi):
        a,b,c,d,e,f,g,h = st
        ch = ((e & f) ^ ((~e) & g)) & mask_t
        T1 = (h + do_Sigma1(e) + ch + Ki + Wi) & mask_t
        maj = ((a & b) ^ (a & c) ^ (b & c)) & mask_t
        T2 = (do_Sigma0(a) + maj) & mask_t
        return [(T1 + T2) & mask_t, a, b, c, (d + T1) & mask_t, e, f, g]

    best_hw = 8 * N
    best_words = None
    total_evals = 0
    t0 = time.time()

    while time.time() - t0 < timeout:
        # Random independent free words for each message
        w1_57 = torch.randint(0, 1 << N, (batch_size,), dtype=torch.int32, device=device)
        w1_58 = torch.randint(0, 1 << N, (batch_size,), dtype=torch.int32, device=device)
        w1_59 = torch.randint(0, 1 << N, (batch_size,), dtype=torch.int32, device=device)
        w1_60 = torch.randint(0, 1 << N, (batch_size,), dtype=torch.int32, device=device)
        w2_57 = torch.randint(0, 1 << N, (batch_size,), dtype=torch.int32, device=device)
        w2_58 = torch.randint(0, 1 << N, (batch_size,), dtype=torch.int32, device=device)
        w2_59 = torch.randint(0, 1 << N, (batch_size,), dtype=torch.int32, device=device)
        w2_60 = torch.randint(0, 1 << N, (batch_size,), dtype=torch.int32, device=device)

        # Schedule W[61..63]
        w1_61 = (do_sigma1(w1_59) + consts['w1_54'] + consts['w1_s0_46'] + consts['w1_45']) & mask_t
        w2_61 = (do_sigma1(w2_59) + consts['w2_54'] + consts['w2_s0_46'] + consts['w2_45']) & mask_t
        w1_62 = (do_sigma1(w1_60) + consts['w1_55'] + consts['w1_s0_47'] + consts['w1_46']) & mask_t
        w2_62 = (do_sigma1(w2_60) + consts['w2_55'] + consts['w2_s0_47'] + consts['w2_46']) & mask_t
        w1_63 = (do_sigma1(w1_61) + consts['w1_56'] + consts['w1_s0_48'] + consts['w1_47']) & mask_t
        w2_63 = (do_sigma1(w2_61) + consts['w2_56'] + consts['w2_s0_48'] + consts['w2_47']) & mask_t

        W1_tail = [w1_57, w1_58, w1_59, w1_60, w1_61, w1_62, w1_63]
        W2_tail = [w2_57, w2_58, w2_59, w2_60, w2_61, w2_62, w2_63]

        st1 = [s.expand(batch_size) for s in s1]
        for i in range(7):
            st1 = do_round(st1, K57[i], W1_tail[i])
        st2 = [s.expand(batch_size) for s in s2]
        for i in range(7):
            st2 = do_round(st2, K57[i], W2_tail[i])

        total_hw = torch.zeros(batch_size, dtype=torch.int32, device=device)
        for i in range(8):
            total_hw = total_hw + popcount32(st1[i] ^ st2[i])

        min_hw = total_hw.min().item()
        if min_hw < best_hw:
            best_hw = min_hw
            idx = total_hw.argmin().item()
            best_words = ([w1_57[idx].item(), w1_58[idx].item(),
                           w1_59[idx].item(), w1_60[idx].item()],
                          [w2_57[idx].item(), w2_58[idx].item(),
                           w2_59[idx].item(), w2_60[idx].item()])
            print(f"  new best HW={best_hw} at eval {total_evals + idx} "
                  f"({time.time()-t0:.2f}s)", flush=True)
        if best_hw == 0:
            break
        total_evals += batch_size

    return best_hw, best_words, total_evals, time.time() - t0


def benchmark(N, timeout_cpu=120):
    print(f"\n{'='*60}")
    print(f"BENCHMARK: N={N} bits  (search space: shared=2^{4*N}, indep=2^{8*N})")
    print(f"{'='*60}\n")

    sha = MiniSHA(N)
    m0, fill = sha.find_candidate()
    if m0 is None:
        print(f"No da[56]=0 candidate found at N={N}")
        return

    print(f"Candidate: M[0]=0x{m0:x}, fill=0x{fill:x}")

    M1 = [m0] + [fill]*15
    M2 = list(M1); M2[0] = m0 ^ sha.MSB; M2[9] = fill ^ sha.MSB
    state1, W1 = sha.compress57(M1)
    state2, W2 = sha.compress57(M2)
    print(f"da[56] = 0x{(state1[0] ^ state2[0]):x} (should be 0)")

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"GPU device: {device}" + (f" ({torch.cuda.get_device_name(0)})" if device.type == 'cuda' else ""))

    # --- GPU shared free words (exhaustive if feasible) ---
    total_shared = (1 << N) ** 4
    gpu_mode = 'exhaustive' if 4*N <= 32 else 'random'
    print(f"\n--- GPU shared free words ({gpu_mode}, space=2^{4*N}={total_shared:,}) ---")
    t0 = time.time()
    hw, words, evals, elapsed = gpu_tail_search(
        state1, state2, W1, W2, sha, device,
        batch_size=min(1 << 22, total_shared),
        max_evals=total_shared if gpu_mode == 'exhaustive' else 10**9,
        timeout=timeout_cpu, mode=gpu_mode)
    print(f"  Result: best HW={hw}, evals={evals:,}, time={elapsed:.2f}s")
    print(f"  Throughput: {evals/elapsed:,.0f} evals/sec")
    if hw == 0:
        print(f"  *** COLLISION FOUND *** W={words}")

    # --- GPU independent free words (random) ---
    print(f"\n--- GPU independent free words (random, space=2^{8*N}) ---")
    hw2, words2, evals2, elapsed2 = gpu_independent_search(
        state1, state2, W1, W2, sha, device,
        batch_size=1 << 20, timeout=min(timeout_cpu, 30))
    print(f"  Result: best HW={hw2}, evals={evals2:,}, time={elapsed2:.2f}s")
    print(f"  Throughput: {evals2/elapsed2:,.0f} evals/sec")
    if hw2 == 0:
        print(f"  *** COLLISION FOUND *** W1={words2[0]}, W2={words2[1]}")

    # --- CPU Kissat ---
    print(f"\n--- CPU Kissat (SAT solver) ---")
    # Need to be in the homotopy directory for imports
    old_cwd = os.getcwd()
    os.chdir(_root)
    try:
        result, cpu_time = cpu_kissat_solve(N, m0, fill, timeout_cpu)
    except Exception as e:
        result, cpu_time = f"ERROR: {e}", 0
    os.chdir(old_cwd)
    print(f"  Result: {result} in {cpu_time:.2f}s")

    # --- Summary ---
    print(f"\n{'='*60}")
    print(f"SUMMARY N={N}:")
    print(f"  GPU shared ({gpu_mode}): HW={hw}, {elapsed:.2f}s, {evals/elapsed:,.0f} eval/s")
    print(f"  GPU independent (random): HW={hw2}, {elapsed2:.2f}s, {evals2/elapsed2:,.0f} eval/s")
    print(f"  CPU Kissat: {result}, {cpu_time:.2f}s")
    if hw == 0 and result == "SAT":
        speedup = cpu_time / elapsed if elapsed > 0 else float('inf')
        print(f"  GPU speedup: {speedup:.1f}x")
    print(f"{'='*60}")


if __name__ == "__main__":
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    mode = sys.argv[2] if len(sys.argv) > 2 else 'benchmark'
    timeout = int(sys.argv[3]) if len(sys.argv) > 3 else 120

    if mode == 'benchmark':
        benchmark(N, timeout)
    elif mode == 'sweep':
        for n in range(8, min(N+1, 15)):
            benchmark(n, timeout)
    else:
        sha = MiniSHA(N)
        m0, fill = sha.find_candidate()
        if m0 is None:
            print(f"No candidate at N={N}")
            sys.exit(1)
        M1 = [m0] + [fill]*15
        M2 = list(M1); M2[0] = m0 ^ sha.MSB; M2[9] = fill ^ sha.MSB
        state1, W1 = sha.compress57(M1)
        state2, W2 = sha.compress57(M2)
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        if mode == 'exhaustive':
            hw, w, ev, t = gpu_tail_search(state1, state2, W1, W2, sha, device,
                                           timeout=timeout, mode='exhaustive')
        else:
            hw, w, ev, t = gpu_tail_search(state1, state2, W1, W2, sha, device,
                                           timeout=timeout, mode='random')
        print(f"N={N}: best HW={hw}, evals={ev:,}, time={t:.2f}s")
