#!/usr/bin/env python3
"""
GPU-accelerated da[56]=0 candidate scanner for large N.

At N >= 26, the CPU scanner (fast_scan.c) finds very few candidates
in the 2^24 range. This GPU scanner can search wider ranges much faster
by parallelizing the 57-round mini-SHA-256 compression on CUDA.

The 57-round precomputation is the bottleneck — each M[0] value requires
two full 57-round compressions (M1 and M2) to check da[56]=0.

Usage:
    python3 gpu_candidate_scanner.py N [max_m0_bits] [fills]
    # N: word width (default 29)
    # max_m0_bits: log2 of M[0] range (default 26, meaning scan 0..2^26)
    # fills: comma-separated list of fill values (hex), or 'auto' for defaults
"""

import sys, os, time
import torch

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


def gpu_scan(N, max_m0, fills, device):
    """
    Scan M[0] range on GPU for da[56]=0 candidates.

    Implements the full 57-round mini-SHA-256 compression in PyTorch,
    operating on batches of M[0] values simultaneously.
    """
    MASK = (1 << N) - 1
    MSB = 1 << (N - 1)
    mask = torch.tensor(MASK, dtype=torch.int32, device=device)

    # Scaled rotation amounts
    rS0 = [scale_rot(2,N), scale_rot(13,N), scale_rot(22,N)]
    rS1 = [scale_rot(6,N), scale_rot(11,N), scale_rot(25,N)]
    rs0 = [scale_rot(7,N), scale_rot(18,N)]
    ss0 = scale_rot(3,N)
    rs1 = [scale_rot(17,N), scale_rot(19,N)]
    ss1 = scale_rot(10,N)

    KN = torch.tensor([k & MASK for k in K32[:57]], dtype=torch.int32, device=device)
    IVN = torch.tensor([v & MASK for v in IV32], dtype=torch.int32, device=device)

    def ror(x, k):
        k = k % N
        return ((x >> k) | (x << (N - k))) & mask

    def Sigma0(a): return ror(a, rS0[0]) ^ ror(a, rS0[1]) ^ ror(a, rS0[2])
    def Sigma1(e): return ror(e, rS1[0]) ^ ror(e, rS1[1]) ^ ror(e, rS1[2])
    def sigma0(x): return ror(x, rs0[0]) ^ ror(x, rs0[1]) ^ ((x >> ss0) & mask)
    def sigma1(x): return ror(x, rs1[0]) ^ ror(x, rs1[1]) ^ ((x >> ss1) & mask)

    def compress_a(m0_batch, fill_val):
        """
        Compute register 'a' after 57 rounds for a batch of M[0] values.
        Returns (a_after_57,) tensor of shape (batch,).
        """
        bs = m0_batch.shape[0]
        fill_t = torch.full((bs,), fill_val & MASK, dtype=torch.int32, device=device)

        # Build schedule W[0..56]
        W = [None] * 57
        W[0] = m0_batch & mask
        for i in range(1, 16):
            W[i] = fill_t.clone()

        for i in range(16, 57):
            W[i] = (sigma1(W[i-2]) + W[i-7] + sigma0(W[i-15]) + W[i-16]) & mask

        # Compression
        a = IVN[0].expand(bs).clone()
        b = IVN[1].expand(bs).clone()
        c = IVN[2].expand(bs).clone()
        d = IVN[3].expand(bs).clone()
        e = IVN[4].expand(bs).clone()
        f = IVN[5].expand(bs).clone()
        g = IVN[6].expand(bs).clone()
        h = IVN[7].expand(bs).clone()

        for i in range(57):
            ch = ((e & f) ^ ((~e) & g)) & mask
            T1 = (h + Sigma1(e) + ch + KN[i] + W[i]) & mask
            maj = ((a & b) ^ (a & c) ^ (b & c)) & mask
            T2 = (Sigma0(a) + maj) & mask
            h, g, f, e = g, f, e, (d + T1) & mask
            d, c, b, a = c, b, a, (T1 + T2) & mask

        return a

    total_found = 0
    results = []
    t0 = time.time()

    batch_size = 1 << 18  # 256K M[0] values per GPU batch

    for fill_val in fills:
        fill_name = f"0x{fill_val:x}"
        m0_offset = 0

        while m0_offset < max_m0:
            bs = min(batch_size, max_m0 - m0_offset)
            m0_batch = torch.arange(m0_offset, m0_offset + bs,
                                     dtype=torch.int32, device=device)

            # Compute a-register for M1 (m0) and M2 (m0 ^ MSB, fill ^ MSB at pos 9)
            a1 = compress_a(m0_batch, fill_val)

            # For M2: M2[0] = m0 ^ MSB, M2[9] = fill ^ MSB
            # We need to recompute with modified schedule
            m0_batch_2 = m0_batch ^ torch.tensor(MSB, dtype=torch.int32, device=device)
            # M2 has fill ^ MSB at position 9 — need custom compression
            fill2 = fill_val ^ MSB

            # Build M2 schedule manually (only positions 0 and 9 differ)
            W2 = [None] * 57
            W2[0] = m0_batch_2 & mask
            for i in range(1, 16):
                if i == 9:
                    W2[i] = torch.full((bs,), fill2 & MASK, dtype=torch.int32, device=device)
                else:
                    W2[i] = torch.full((bs,), fill_val & MASK, dtype=torch.int32, device=device)
            for i in range(16, 57):
                W2[i] = (sigma1(W2[i-2]) + W2[i-7] + sigma0(W2[i-15]) + W2[i-16]) & mask

            a2 = IVN[0].expand(bs).clone()
            b2 = IVN[1].expand(bs).clone()
            c2 = IVN[2].expand(bs).clone()
            d2 = IVN[3].expand(bs).clone()
            e2 = IVN[4].expand(bs).clone()
            f2 = IVN[5].expand(bs).clone()
            g2 = IVN[6].expand(bs).clone()
            h2 = IVN[7].expand(bs).clone()

            for i in range(57):
                ch = ((e2 & f2) ^ ((~e2) & g2)) & mask
                T1 = (h2 + Sigma1(e2) + ch + KN[i] + W2[i]) & mask
                maj = ((a2 & b2) ^ (a2 & c2) ^ (b2 & c2)) & mask
                T2 = (Sigma0(a2) + maj) & mask
                h2, g2, f2, e2 = g2, f2, e2, (d2 + T1) & mask
                d2, c2, b2, a2 = c2, b2, a2, (T1 + T2) & mask

            # Check da[56]=0: a1 == a2
            matches = (a1 == a2).nonzero(as_tuple=True)[0]
            for idx in matches:
                m0_val = m0_offset + idx.item()
                a_val = a1[idx].item()
                results.append((m0_val, fill_val, a_val))
                total_found += 1
                elapsed = time.time() - t0
                print(f"  [{total_found}] M[0]=0x{m0_val:x} fill={fill_name} "
                      f"a={a_val} ({elapsed:.1f}s)", flush=True)

            m0_offset += bs

        elapsed = time.time() - t0
        scanned = m0_offset
        rate = scanned / elapsed if elapsed > 0 else 0
        print(f"  fill={fill_name}: {scanned:,} M[0] scanned, "
              f"{rate:,.0f}/s, {total_found} hits ({elapsed:.1f}s)", flush=True)

    total_time = time.time() - t0
    print(f"\nTotal: {total_found} candidates in {total_time:.1f}s")

    # Output CSV
    print("\nm0,fill,a1")
    for m0, fill, a in results:
        print(f"{m0},{fill},{a}")

    return results


if __name__ == "__main__":
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 29
    m0_bits = int(sys.argv[2]) if len(sys.argv) > 2 else 26
    max_m0 = 1 << m0_bits

    MASK = (1 << N) - 1
    MSB = 1 << (N - 1)
    default_fills = [MASK, 0, MASK >> 1, MSB, 0x55 & MASK, 0xAA & MASK,
                     0x33 & MASK, 0xCC & MASK, 0x0F & MASK, 0xF0 & MASK]

    if len(sys.argv) > 3 and sys.argv[3] != 'auto':
        fills = [int(x, 16) for x in sys.argv[3].split(',')]
    else:
        fills = default_fills

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"GPU Candidate Scanner: N={N}, M[0] range=0..2^{m0_bits}, "
          f"{len(fills)} fills")
    print(f"Device: {device}" +
          (f" ({torch.cuda.get_device_name(0)})" if device.type == 'cuda' else ""))
    print()

    gpu_scan(N, max_m0, fills, device)
