#!/usr/bin/env python3
"""m16_mitm_forward_validator.py — independent validation of m16_mitm_forward at N=10.

Reads a sample of records from the forward enumerator binary output and verifies:
  1. da[57]=da[58]=da[59]=0 modular (cascade-1 holds)
  2. state_59 in the record matches what a fresh forward run produces

For each sampled record, this script independently:
  a) Reconstructs the cascade-eligible (M0, fill) (matches m16_mitm_forward's choice).
  b) Runs round-by-round forward up to slot 60 with the record's (W57, W58, W59).
  c) Checks state after round 59 equals the record's state_59.
  d) Checks pair-2 (with cascade-extending W2's) gives same a-register.

Usage:
  python3 m16_mitm_forward_validator.py <fwd_binary_file> [--n=10] [--samples=100]

EVIDENCE-level: 100 random records all matching = forward enumerator passes
sanity check.
"""
import os
import sys
import argparse
import random


def scale_rot(k32, N):
    return max(1, round(k32 * N / 32))


def make_funcs(N):
    MASK = (1 << N) - 1
    rS0 = (scale_rot(2, N), scale_rot(13, N), scale_rot(22, N))
    rS1 = (scale_rot(6, N), scale_rot(11, N), scale_rot(25, N))
    rs0 = (scale_rot(7, N), scale_rot(18, N))
    ss0 = scale_rot(3, N)
    rs1 = (scale_rot(17, N), scale_rot(19, N))
    ss1 = scale_rot(10, N)

    def ror(x, k):
        k = k % N
        return ((x >> k) | (x << (N - k))) & MASK

    def Sigma0(a):
        return (ror(a, rS0[0]) ^ ror(a, rS0[1]) ^ ror(a, rS0[2])) & MASK

    def Sigma1(e):
        return (ror(e, rS1[0]) ^ ror(e, rS1[1]) ^ ror(e, rS1[2])) & MASK

    def sigma0(x):
        return (ror(x, rs0[0]) ^ ror(x, rs0[1]) ^ ((x >> ss0) & MASK)) & MASK

    def sigma1(x):
        return (ror(x, rs1[0]) ^ ror(x, rs1[1]) ^ ((x >> ss1) & MASK)) & MASK

    def Ch(e, f, g):
        return ((e & f) ^ ((~e) & g)) & MASK

    def Maj(a, b, c):
        return ((a & b) ^ (a & c) ^ (b & c)) & MASK

    return MASK, Sigma0, Sigma1, sigma0, sigma1, Ch, Maj


# 32-bit constants masked to N
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
IV32 = [0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19]


def precompute(M, MASK, Sigma0, Sigma1, sigma0, sigma1, Ch, Maj, KN):
    W = [0] * 57
    for i in range(16):
        W[i] = M[i] & MASK
    for i in range(16, 57):
        W[i] = (sigma1(W[i - 2]) + W[i - 7] + sigma0(W[i - 15]) + W[i - 16]) & MASK
    a, b, c, d, e, f, g, h = (v & MASK for v in IV32)
    for i in range(57):
        T1 = (h + Sigma1(e) + Ch(e, f, g) + KN[i] + W[i]) & MASK
        T2 = (Sigma0(a) + Maj(a, b, c)) & MASK
        h, g, f, e, d, c, b, a = g, f, e, (d + T1) & MASK, c, b, a, (T1 + T2) & MASK
    return [a, b, c, d, e, f, g, h], W


def sha_round(s, k, w, MASK, Sigma0, Sigma1, Ch, Maj):
    T1 = (s[7] + Sigma1(s[4]) + Ch(s[4], s[5], s[6]) + k + w) & MASK
    T2 = (Sigma0(s[0]) + Maj(s[0], s[1], s[2])) & MASK
    return [(T1 + T2) & MASK, s[0], s[1], s[2], (s[3] + T1) & MASK, s[4], s[5], s[6]]


def find_w2(s1, s2, rnd, w1, MASK, Sigma1, Ch, Sigma0, Maj, KN):
    r1 = (s1[7] + Sigma1(s1[4]) + Ch(s1[4], s1[5], s1[6]) + KN[rnd]) & MASK
    r2 = (s2[7] + Sigma1(s2[4]) + Ch(s2[4], s2[5], s2[6]) + KN[rnd]) & MASK
    T21 = (Sigma0(s1[0]) + Maj(s1[0], s1[1], s1[2])) & MASK
    T22 = (Sigma0(s2[0]) + Maj(s2[0], s2[1], s2[2])) & MASK
    return (w1 + r1 - r2 + T21 - T22) & MASK


def find_cascade_eligible(N, MASK, KN, Sigma0, Sigma1, sigma0, sigma1, Ch, Maj):
    """Replicate m16_mitm_forward's M0 search."""
    MSB = 1 << (N - 1)
    for cand in range(MASK + 1):
        M1 = [cand] + [MASK] * 15
        M2 = list(M1)
        M2[0] ^= MSB
        M2[9] ^= MSB
        s1, _ = precompute(M1, MASK, Sigma0, Sigma1, sigma0, sigma1, Ch, Maj, KN)
        s2, _ = precompute(M2, MASK, Sigma0, Sigma1, sigma0, sigma1, Ch, Maj, KN)
        if s1[0] == s2[0]:
            return cand, MASK, s1, s2
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("fwd_file")
    ap.add_argument("--n", type=int, default=10)
    ap.add_argument("--samples", type=int, default=100)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    N = args.n
    bw = (N + 7) // 8  # bytes per word
    rec_size = 11 * bw  # state_59 (8 words) + W57 + W58 + W59

    MASK, Sigma0, Sigma1, sigma0, sigma1, Ch, Maj = make_funcs(N)
    KN = [k & MASK for k in K32]

    print(f"N={N}, MASK=0x{MASK:x}, bw={bw}, rec_size={rec_size}")

    eligible = find_cascade_eligible(N, MASK, KN, Sigma0, Sigma1, sigma0, sigma1, Ch, Maj)
    if eligible is None:
        print("No cascade-eligible M0 found; abort.")
        return 1
    M0, fill, state1_56, state2_56 = eligible
    print(f"Cascade-eligible: M0=0x{M0:x}  fill=0x{fill:x}")
    print(f"state1[56].a={state1_56[0]:x}  state2[56].a={state2_56[0]:x}  match={state1_56[0]==state2_56[0]}")

    file_size = os.path.getsize(args.fwd_file)
    n_records = file_size // rec_size
    print(f"File: {args.fwd_file}  size={file_size}  records={n_records}")

    rng = random.Random(args.seed)
    sample_idxs = sorted(rng.sample(range(n_records), min(args.samples, n_records)))

    def unpack_word(buf):
        v = 0
        for i in range(bw):
            v |= buf[i] << (8 * i)
        return v & MASK

    fails = 0
    state_set = set()
    with open(args.fwd_file, "rb") as f:
        for idx in sample_idxs:
            f.seek(idx * rec_size)
            rec = f.read(rec_size)
            state_rec = [unpack_word(rec[i*bw:(i+1)*bw]) for i in range(8)]
            w57 = unpack_word(rec[8*bw:9*bw])
            w58 = unpack_word(rec[9*bw:10*bw])
            w59 = unpack_word(rec[10*bw:11*bw])

            # Run forward independently
            s1 = list(state1_56)
            s2 = list(state2_56)
            w57_2 = find_w2(s1, s2, 57, w57, MASK, Sigma1, Ch, Sigma0, Maj, KN)
            s1 = sha_round(s1, KN[57], w57, MASK, Sigma0, Sigma1, Ch, Maj)
            s2 = sha_round(s2, KN[57], w57_2, MASK, Sigma0, Sigma1, Ch, Maj)
            if s1[0] != s2[0]:
                fails += 1
                print(f"  FAIL idx={idx}: da[57]!=0 modular (s1.a={s1[0]:x} s2.a={s2[0]:x})")
                continue

            w58_2 = find_w2(s1, s2, 58, w58, MASK, Sigma1, Ch, Sigma0, Maj, KN)
            s1 = sha_round(s1, KN[58], w58, MASK, Sigma0, Sigma1, Ch, Maj)
            s2 = sha_round(s2, KN[58], w58_2, MASK, Sigma0, Sigma1, Ch, Maj)
            if s1[0] != s2[0]:
                fails += 1
                print(f"  FAIL idx={idx}: da[58]!=0 modular")
                continue

            w59_2 = find_w2(s1, s2, 59, w59, MASK, Sigma1, Ch, Sigma0, Maj, KN)
            s1 = sha_round(s1, KN[59], w59, MASK, Sigma0, Sigma1, Ch, Maj)
            s2 = sha_round(s2, KN[59], w59_2, MASK, Sigma0, Sigma1, Ch, Maj)
            if s1[0] != s2[0]:
                fails += 1
                print(f"  FAIL idx={idx}: da[59]!=0 modular")
                continue

            if s1 != state_rec:
                fails += 1
                print(f"  FAIL idx={idx}: state mismatch  rec={state_rec}  computed={s1}")

            state_set.add(tuple(state_rec))

    n = len(sample_idxs)
    print(f"\nVerified {n - fails}/{n} sampled records.")
    print(f"Distinct state_59 in sample: {len(state_set)}/{n} ({100*len(state_set)/n:.1f}%)")
    if fails == 0:
        print("ALL PASS — forward enumerator output validated.")
        return 0
    else:
        print(f"{fails} FAILURES — forward enumerator has a bug.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
