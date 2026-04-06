#!/usr/bin/env python3
"""
GPU hill-climbing collision search for mini-SHA-256.

Instead of differentiable relaxation (slow carry chains), uses parallel
bit-flip optimization on integer operations:

1. Sample K random starting points (free words for both messages)
2. For each, try ALL single-bit flips (8*N neighbors per point)
3. Keep the best neighbor if it improves HW
4. Repeat until no improvement, then restart

This is MUCH faster than gradient descent through carry chains because
it uses native integer SHA-256 operations on GPU.

ROUND8_PLAN Experiment L alternative implementation.

Usage:
    python3 gpu_hill_climb.py [N] [n_parallel] [max_iterations]
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


class GPUHillClimber:
    def __init__(self, N, state1, state2, W1_pre, W2_pre, device):
        self.N = N
        self.device = device
        MASK = (1 << N) - 1
        self.mask = torch.tensor(MASK, dtype=torch.int32, device=device)

        rS0 = [scale_rot(2,N), scale_rot(13,N), scale_rot(22,N)]
        rS1 = [scale_rot(6,N), scale_rot(11,N), scale_rot(25,N)]
        rs1 = [scale_rot(17,N), scale_rot(19,N)]
        ss1 = scale_rot(10,N)
        self.rS0=rS0; self.rS1=rS1; self.rs1=rs1; self.ss1=ss1

        spec = __import__('50_precision_homotopy').MiniSHA256(N)
        def t(v): return torch.tensor(v, dtype=torch.int32, device=device)
        self.K57 = [t(K32[57+i] & MASK) for i in range(7)]
        self.s1 = [t(state1[i]) for i in range(8)]
        self.s2 = [t(state2[i]) for i in range(8)]

        self.w1c = {k: t(W1_pre[k]) for k in [45,46,47,48,54,55,56]}
        self.w2c = {k: t(W2_pre[k]) for k in [45,46,47,48,54,55,56]}
        self.w1c['s46']=t(spec.sigma0(W1_pre[46]))
        self.w2c['s46']=t(spec.sigma0(W2_pre[46]))
        self.w1c['s47']=t(spec.sigma0(W1_pre[47]))
        self.w2c['s47']=t(spec.sigma0(W2_pre[47]))
        self.w1c['s48']=t(spec.sigma0(W1_pre[48]))
        self.w2c['s48']=t(spec.sigma0(W2_pre[48]))

    def ror(self, x, k):
        k = k % self.N
        return ((x >> k) | (x << (self.N - k))) & self.mask

    def sigma1(self, x):
        return self.ror(x,self.rs1[0])^self.ror(x,self.rs1[1])^((x>>self.ss1)&self.mask)
    def Sigma0(self, a):
        return self.ror(a,self.rS0[0])^self.ror(a,self.rS0[1])^self.ror(a,self.rS0[2])
    def Sigma1(self, e):
        return self.ror(e,self.rS1[0])^self.ror(e,self.rS1[1])^self.ror(e,self.rS1[2])

    def sha_round(self, st, Ki, Wi):
        a,b,c,d,e,f,g,h = st
        ch = ((e&f)^((~e)&g))&self.mask
        T1 = (h+self.Sigma1(e)+ch+Ki+Wi)&self.mask
        maj = ((a&b)^(a&c)^(b&c))&self.mask
        T2 = (self.Sigma0(a)+maj)&self.mask
        return [(T1+T2)&self.mask,a,b,c,(d+T1)&self.mask,e,f,g]

    def eval_hw(self, w1, w2):
        """
        Evaluate collision HW for a batch of free word assignments.
        w1, w2: each (batch, 4) int32 tensors (4 free words per message)
        Returns: (batch,) int32 tensor of total Hamming weight
        """
        bs = w1.shape[0]
        m = self.mask

        # Schedule
        w1_61=(self.sigma1(w1[:,2])+self.w1c[54]+self.w1c['s46']+self.w1c[45])&m
        w2_61=(self.sigma1(w2[:,2])+self.w2c[54]+self.w2c['s46']+self.w2c[45])&m
        w1_62=(self.sigma1(w1[:,3])+self.w1c[55]+self.w1c['s47']+self.w1c[46])&m
        w2_62=(self.sigma1(w2[:,3])+self.w2c[55]+self.w2c['s47']+self.w2c[46])&m
        w1_63=(self.sigma1(w1_61)+self.w1c[56]+self.w1c['s48']+self.w1c[47])&m
        w2_63=(self.sigma1(w2_61)+self.w2c[56]+self.w2c['s48']+self.w2c[47])&m

        W1t=[w1[:,0],w1[:,1],w1[:,2],w1[:,3],w1_61,w1_62,w1_63]
        W2t=[w2[:,0],w2[:,1],w2[:,2],w2[:,3],w2_61,w2_62,w2_63]

        st1=[s.expand(bs) for s in self.s1]
        for i in range(7): st1=self.sha_round(st1,self.K57[i],W1t[i])
        st2=[s.expand(bs) for s in self.s2]
        for i in range(7): st2=self.sha_round(st2,self.K57[i],W2t[i])

        hw=torch.zeros(bs,dtype=torch.int32,device=self.device)
        for i in range(8): hw=hw+popcount32(st1[i]^st2[i])
        return hw

    def hill_climb(self, n_parallel=10000, max_iters=1000, max_restarts=100,
                   timeout=120.0):
        """
        Parallel hill climbing with random restarts.

        For each point, try flipping each of the 8*N bits (one at a time).
        Keep the flip that gives the best improvement. Repeat until stuck.
        Then restart from a new random point.
        """
        N = self.N
        n_bits = 8 * N  # 4 words × N bits × 2 messages
        device = self.device

        global_best_hw = 8 * N
        global_best_w1 = None
        global_best_w2 = None
        total_evals = 0
        t0 = time.time()

        for restart in range(max_restarts):
            if time.time() - t0 > timeout:
                break

            # Random starting points
            w1 = torch.randint(0, 1 << N, (n_parallel, 4),
                               dtype=torch.int32, device=device)
            w2 = torch.randint(0, 1 << N, (n_parallel, 4),
                               dtype=torch.int32, device=device)
            current_hw = self.eval_hw(w1, w2)
            total_evals += n_parallel

            improved = True
            step = 0
            while improved and step < max_iters and time.time() - t0 < timeout:
                improved = False
                step += 1

                # Try ALL single-bit flips for ALL parallel points
                # For each of 8 words (4 per message) × N bits per word
                for word_idx in range(8):  # 0-3: w1, 4-7: w2
                    for bit in range(N):
                        flip_mask = torch.tensor(1 << bit, dtype=torch.int32,
                                                 device=device)

                        # Create flipped copies
                        w1_new = w1.clone()
                        w2_new = w2.clone()
                        if word_idx < 4:
                            w1_new[:, word_idx] = w1[:, word_idx] ^ flip_mask
                        else:
                            w2_new[:, word_idx - 4] = w2[:, word_idx - 4] ^ flip_mask

                        new_hw = self.eval_hw(w1_new, w2_new)
                        total_evals += n_parallel

                        # Keep improvement
                        better = new_hw < current_hw
                        if better.any():
                            improved = True
                            w1[better] = w1_new[better]
                            w2[better] = w2_new[better]
                            current_hw[better] = new_hw[better]

            # Check for global best
            batch_min = current_hw.min().item()
            if batch_min < global_best_hw:
                global_best_hw = batch_min
                idx = current_hw.argmin().item()
                global_best_w1 = w1[idx].cpu().tolist()
                global_best_w2 = w2[idx].cpu().tolist()
                elapsed = time.time() - t0
                print(f"  restart {restart}: best_hw={global_best_hw} "
                      f"(step {step}, {total_evals:,} evals, {elapsed:.1f}s)",
                      flush=True)
                if global_best_hw == 0:
                    print(f"  *** COLLISION FOUND ***")
                    break
            elif restart % 10 == 0:
                elapsed = time.time() - t0
                print(f"  restart {restart}: batch_min={batch_min}, "
                      f"global_best={global_best_hw} "
                      f"({total_evals:,} evals, {elapsed:.1f}s)", flush=True)

        elapsed = time.time() - t0
        return global_best_hw, global_best_w1, global_best_w2, total_evals, elapsed


def main():
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    n_parallel = int(sys.argv[2]) if len(sys.argv) > 2 else 5000
    timeout = int(sys.argv[3]) if len(sys.argv) > 3 else 60

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    spec = __import__('50_precision_homotopy')
    sha = spec.MiniSHA256(N)
    MASK = sha.MASK; MSB = sha.MSB

    # Find candidate
    for m0 in range(min(MASK, 1 << 20)):
        M1 = [m0]+[MASK]*15; M2 = list(M1); M2[0]=m0^MSB; M2[9]=MASK^MSB
        s1, W1 = sha.compress(M1); s2, W2 = sha.compress(M2)
        if s1[0] == s2[0]:
            break
    else:
        print(f"No candidate at N={N}"); return

    print(f"GPU Hill Climbing: N={N}, M[0]=0x{m0:x}")
    print(f"Parallel points: {n_parallel}, timeout: {timeout}s")
    print(f"Device: {device}")
    print()

    climber = GPUHillClimber(N, s1, s2, W1, W2, device)
    best_hw, w1, w2, evals, elapsed = climber.hill_climb(
        n_parallel=n_parallel, max_restarts=1000, timeout=timeout)

    print(f"\n{'='*60}")
    print(f"RESULT N={N}: best_hw={best_hw}, {evals:,} evals in {elapsed:.1f}s")
    print(f"Throughput: {evals/elapsed:,.0f} evals/s")
    if w1 and w2:
        print(f"W1={[hex(x) for x in w1]}")
        print(f"W2={[hex(x) for x in w2]}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
