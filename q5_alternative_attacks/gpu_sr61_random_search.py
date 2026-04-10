#!/usr/bin/env python3
"""
GPU random search for sr=61 collision proximity.

Direct test: sample (W57, W58, W59) triples in parallel, compute the
sr=61-implied (W60, W61, W62, W63) via the schedule rules, run all 7
rounds (57-63) for both messages, and report the minimum state delta HW.

Unlike SLS (which counts unsat clauses), this measures the actual SHA-256
collision distance. If random samples can find delta HW < 50, sr=61 is
likely tractable. If even 10B samples plateau at HW > 100, we have a
direct empirical bound on the problem hardness.

Runs on the verified sr=60 candidate by default: M[0]=0x17149975, fill=0xff.
"""
import sys, os, time
import torch

# SHA-256 constants
K32 = [
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
]
IV32 = [0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
        0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19]


def to_signed_i32(v):
    """Convert unsigned 32-bit to signed for PyTorch int32."""
    return v if v < 0x80000000 else v - 0x100000000


def precompute_state(M):
    """CPU SHA-256 compress for 57 rounds, return (state, full_W)."""
    W = list(M) + [0]*48
    for i in range(16, 64):
        s0 = ((W[i-15]>>7|W[i-15]<<25)&0xffffffff) ^ ((W[i-15]>>18|W[i-15]<<14)&0xffffffff) ^ (W[i-15]>>3)
        s1 = ((W[i-2]>>17|W[i-2]<<15)&0xffffffff) ^ ((W[i-2]>>19|W[i-2]<<13)&0xffffffff) ^ (W[i-2]>>10)
        W[i] = (s1 + W[i-7] + s0 + W[i-16]) & 0xffffffff
    a,b,c,d,e,f,g,h = IV32
    for i in range(57):
        S1 = ((e>>6|e<<26)&0xffffffff) ^ ((e>>11|e<<21)&0xffffffff) ^ ((e>>25|e<<7)&0xffffffff)
        ch = (e&f) ^ ((~e&0xffffffff)&g)
        T1 = (h + S1 + ch + K32[i] + W[i]) & 0xffffffff
        S0 = ((a>>2|a<<30)&0xffffffff) ^ ((a>>13|a<<19)&0xffffffff) ^ ((a>>22|a<<10)&0xffffffff)
        maj = (a&b) ^ (a&c) ^ (b&c)
        T2 = (S0 + maj) & 0xffffffff
        h,g,f,e,d,c,b,a = g,f,e,(d+T1)&0xffffffff,c,b,a,(T1+T2)&0xffffffff
    return [a,b,c,d,e,f,g,h], W


def gpu_search(m0=0x17149975, fill=0xffffffff, kernel=0x80000000,
               batch_size=1<<22, hours=4.0):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"GPU sr=61 random search", flush=True)
    print(f"Candidate: M[0]=0x{m0:08x}, fill=0x{fill:08x}, kernel=0x{kernel:08x}", flush=True)
    print(f"Device: {device}, batch={batch_size}, hours={hours}", flush=True)

    # Build M1, M2 and precompute states + schedule constants
    M1 = [m0] + [fill] * 15
    M2 = list(M1)
    M2[0] ^= kernel
    M2[9] ^= kernel
    state1, W1_pre = precompute_state(M1)
    state2, W2_pre = precompute_state(M2)
    assert state1[0] == state2[0], "da[56] != 0"
    print(f"da[56]=0 verified. State1[0]={state1[0]:#x}", flush=True)

    # Schedule constants for W[60..63] computation
    # W[60] = sigma1(W[58]) + W[53] + sigma0(W[45]) + W[44]
    # W[61] = sigma1(W[59]) + W[54] + sigma0(W[46]) + W[45]
    # W[62] = sigma1(W[60]) + W[55] + sigma0(W[47]) + W[46]
    # W[63] = sigma1(W[61]) + W[56] + sigma0(W[48]) + W[47]
    def sched_const(W_pre, target):
        if target == 60: return (W_pre[53] + sigma0(W_pre[45]) + W_pre[44]) & 0xffffffff
        if target == 61: return (W_pre[54] + sigma0(W_pre[46]) + W_pre[45]) & 0xffffffff
        if target == 62: return (W_pre[55] + sigma0(W_pre[47]) + W_pre[46]) & 0xffffffff
        if target == 63: return (W_pre[56] + sigma0(W_pre[48]) + W_pre[47]) & 0xffffffff

    def sigma0(x):
        return (((x>>7|x<<25)&0xffffffff) ^ ((x>>18|x<<14)&0xffffffff) ^ (x>>3))

    sched_C1 = [sched_const(W1_pre, t) for t in [60,61,62,63]]
    sched_C2 = [sched_const(W2_pre, t) for t in [60,61,62,63]]

    # Move constants to GPU as int32
    K_gpu = torch.tensor([to_signed_i32(K32[57+i]) for i in range(7)],
                          dtype=torch.int32, device=device)
    state1_gpu = torch.tensor([to_signed_i32(s) for s in state1],
                               dtype=torch.int32, device=device)
    state2_gpu = torch.tensor([to_signed_i32(s) for s in state2],
                               dtype=torch.int32, device=device)
    sched_C1_gpu = torch.tensor([to_signed_i32(c) for c in sched_C1],
                                 dtype=torch.int32, device=device)
    sched_C2_gpu = torch.tensor([to_signed_i32(c) for c in sched_C2],
                                 dtype=torch.int32, device=device)

    # GPU helper functions
    def ror(x, k):
        # Bitwise rotation right for int32
        return ((x >> k) & ((1 << (32-k)) - 1)) | ((x << (32-k)))

    def Sigma0_gpu(x):
        return ror(x, 2) ^ ror(x, 13) ^ ror(x, 22)
    def Sigma1_gpu(x):
        return ror(x, 6) ^ ror(x, 11) ^ ror(x, 25)
    def sigma0_gpu(x):
        return ror(x, 7) ^ ror(x, 18) ^ ((x >> 3) & 0x1FFFFFFF)
    def sigma1_gpu(x):
        return ror(x, 17) ^ ror(x, 19) ^ ((x >> 10) & 0x003FFFFF)

    def do_round(state, Ki, Wi):
        a, b, c, d, e, f, g, h = state
        S1 = Sigma1_gpu(e)
        ch = (e & f) ^ (~e & g)
        T1 = h + S1 + ch + Ki + Wi
        S0 = Sigma0_gpu(a)
        maj = (a & b) ^ (a & c) ^ (b & c)
        T2 = S0 + maj
        return [T1+T2, a, b, c, d+T1, e, f, g]

    # Stats tracking
    best_hw = 256
    best_W = None
    total_samples = 0
    t0 = time.time()
    log_interval = 5  # seconds
    last_log = t0

    while time.time() - t0 < hours * 3600:
        # Sample W57, W58, W59 uniformly random
        w57 = torch.randint(-(1<<31), (1<<31)-1, (batch_size,),
                            dtype=torch.int32, device=device)
        w58 = torch.randint(-(1<<31), (1<<31)-1, (batch_size,),
                            dtype=torch.int32, device=device)
        w59 = torch.randint(-(1<<31), (1<<31)-1, (batch_size,),
                            dtype=torch.int32, device=device)

        # Compute sr=61 schedule words for both messages
        # W[60] = sigma1(W[58]) + sched_C
        w1_60 = sigma1_gpu(w58) + sched_C1_gpu[0]
        w2_60 = sigma1_gpu(w58) + sched_C2_gpu[0]
        # W[61] = sigma1(W[59]) + sched_C
        w1_61 = sigma1_gpu(w59) + sched_C1_gpu[1]
        w2_61 = sigma1_gpu(w59) + sched_C2_gpu[1]
        # W[62] = sigma1(W[60]) + sched_C
        w1_62 = sigma1_gpu(w1_60) + sched_C1_gpu[2]
        w2_62 = sigma1_gpu(w2_60) + sched_C2_gpu[2]
        # W[63] = sigma1(W[61]) + sched_C
        w1_63 = sigma1_gpu(w1_61) + sched_C1_gpu[3]
        w2_63 = sigma1_gpu(w2_61) + sched_C2_gpu[3]

        # Run 7 rounds for message 1
        s1 = [state1_gpu[i].expand(batch_size) for i in range(8)]
        for i, Wi in enumerate([w57, w58, w59, w1_60, w1_61, w1_62, w1_63]):
            s1 = do_round(s1, K_gpu[i], Wi)

        # Run 7 rounds for message 2
        s2 = [state2_gpu[i].expand(batch_size) for i in range(8)]
        for i, Wi in enumerate([w57, w58, w59, w2_60, w2_61, w2_62, w2_63]):
            s2 = do_round(s2, K_gpu[i], Wi)

        # Compute state delta and HW
        delta = [s1[i] ^ s2[i] for i in range(8)]
        # Popcount each int32 in delta, sum across 8 registers
        hw = torch.zeros(batch_size, dtype=torch.int32, device=device)
        for d in delta:
            x = d
            x = x - ((x >> 1) & 0x55555555)
            x = (x & 0x33333333) + ((x >> 2) & 0x33333333)
            x = (x + (x >> 4)) & 0x0F0F0F0F
            x = (x * 0x01010101) >> 24
            hw = hw + (x & 0xFF)

        # Find minimum
        min_idx = hw.argmin().item()
        min_hw = hw[min_idx].item()
        total_samples += batch_size

        if min_hw < best_hw:
            best_hw = min_hw
            best_W = (w57[min_idx].item() & 0xFFFFFFFF,
                      w58[min_idx].item() & 0xFFFFFFFF,
                      w59[min_idx].item() & 0xFFFFFFFF)
            elapsed = time.time() - t0
            rate = total_samples / elapsed
            print(f"  NEW BEST: HW={best_hw}/256 W57=0x{best_W[0]:08x} "
                  f"W58=0x{best_W[1]:08x} W59=0x{best_W[2]:08x} "
                  f"[{elapsed:.0f}s, {total_samples/1e9:.2f}B samples, "
                  f"{rate/1e6:.0f}M/s]", flush=True)

        # Periodic status
        now = time.time()
        if now - last_log > 60:
            elapsed = now - t0
            rate = total_samples / elapsed
            print(f"  status: {total_samples/1e9:.2f}B samples, "
                  f"best={best_hw}/256, {rate/1e6:.0f}M/s, "
                  f"{elapsed/3600:.2f}h", flush=True)
            last_log = now

    elapsed = time.time() - t0
    print(f"\n{'='*60}", flush=True)
    print(f"COMPLETE: {total_samples/1e9:.2f}B samples in {elapsed/3600:.2f}h", flush=True)
    print(f"Rate: {total_samples/elapsed/1e6:.0f}M samples/s", flush=True)
    print(f"Best HW: {best_hw}/256", flush=True)
    if best_W:
        print(f"Best W: W57=0x{best_W[0]:08x} W58=0x{best_W[1]:08x} W59=0x{best_W[2]:08x}",
              flush=True)
    print(f"{'='*60}", flush=True)


if __name__ == "__main__":
    m0 = int(sys.argv[1], 0) if len(sys.argv) > 1 else 0x17149975
    fill = int(sys.argv[2], 0) if len(sys.argv) > 2 else 0xffffffff
    hours = float(sys.argv[3]) if len(sys.argv) > 3 else 24.0
    kernel = int(sys.argv[4], 0) if len(sys.argv) > 4 else 0x80000000
    gpu_search(m0, fill, kernel=kernel, hours=hours)
