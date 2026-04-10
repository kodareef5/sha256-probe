#!/usr/bin/env python3
"""
Sigma1 bridge MITM for sr=61.

Direction 1 from NOVEL_DIRECTIONS.md. The key insight:

For sr=61, W[60] = sigma1(W[58]) + const. Sigma1 is bijective on GF(2)^32,
so for any TARGET W[60] value, there's exactly ONE W[58] that produces it.

Algorithm:
1. For each W1[57] in 2^32:
   a. Simulate rounds 57, 58, 59 (using arbitrary W[58], W[59] — we'll fix W[58] below)
   b. Determine the state at round 59
   c. From the state, compute the W[60] value that would zero de60 (cascade 2 trigger)
   d. Use sigma1_inv to compute the forced W[58]
   e. RE-SIMULATE round 58 with the forced W[58]
   f. Check if cascade 1 still holds: db58=0 (auto from shift), dc59=0 needs W[58] not too bad
   g. Score the outcome by HW of state delta at round 60

This is a structured enumeration that DIRECTLY tests whether the sr=61
constraint can be navigated. 2^32 ≈ 4B steps, runs in minutes per CPU core.

Actually, the dependency is more subtle: de60 depends on W[58] (via sigma1)
AND on the round-58 state (also via W[58]). So we need to solve:
  de60(W57, W58_forced) = 0, where W58_forced = f(W57, W58_forced)
This is a fixed-point equation, not a closed form. Use iteration.

For now: enumerate W[57], for each compute state through round 59 with
random W[58]/W[59], then compute target W[60] from de60=0, invert sigma1
to get forced W[58], re-evaluate, and report the resulting state delta HW.
"""
import sys, time

K = [
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
]
IV = [0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
      0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19]

MASK = 0xFFFFFFFF


def ror(x, n):
    return ((x >> n) | (x << (32 - n))) & MASK

def Sigma0(a): return ror(a, 2) ^ ror(a, 13) ^ ror(a, 22)
def Sigma1(e): return ror(e, 6) ^ ror(e, 11) ^ ror(e, 25)
def sigma0(x): return ror(x, 7) ^ ror(x, 18) ^ (x >> 3)
def sigma1(x): return ror(x, 17) ^ ror(x, 19) ^ (x >> 10)
def Ch(e, f, g): return (e & f) ^ ((~e & MASK) & g)
def Maj(a, b, c): return (a & b) ^ (a & c) ^ (b & c)
def hw32(x): return bin(x & MASK).count('1')


def precompute_state(M):
    W = list(M) + [0]*48
    for i in range(16, 64):
        W[i] = (sigma1(W[i-2]) + W[i-7] + sigma0(W[i-15]) + W[i-16]) & MASK
    a,b,c,d,e,f,g,h = IV
    for i in range(57):
        T1 = (h + Sigma1(e) + Ch(e,f,g) + K[i] + W[i]) & MASK
        T2 = (Sigma0(a) + Maj(a,b,c)) & MASK
        h,g,f,e,d,c,b,a = g,f,e,(d+T1)&MASK,c,b,a,(T1+T2)&MASK
    return [a,b,c,d,e,f,g,h], W


def round_op(state, Ki, Wi):
    a,b,c,d,e,f,g,h = state
    T1 = (h + Sigma1(e) + Ch(e,f,g) + Ki + Wi) & MASK
    T2 = (Sigma0(a) + Maj(a,b,c)) & MASK
    return [(T1+T2)&MASK, a, b, c, (d+T1)&MASK, e, f, g]


def sigma1_inv_table():
    """Build the sigma1 inverse table (sigma1 is bijective on F_2^32).

    Since sigma1 is F_2-linear, we can solve via Gaussian elimination.
    Returns a function inv(y) that gives x such that sigma1(x) = y.
    """
    # Build the 32x32 GF(2) matrix M where M[i][j] = bit i of sigma1(e_j)
    matrix = []
    for j in range(32):
        e_j = 1 << j
        s = sigma1(e_j)
        col = [(s >> i) & 1 for i in range(32)]
        matrix.append(col)
    # matrix[j][i] = bit i of sigma1(e_j)
    # We want: given y, find x such that sigma1(x) = y
    # sigma1(x) = sum over j of x[j] * matrix[j] (vectors of 32 bits, XOR)
    # In matrix form: y_T = M @ x_T where M[i][j] = matrix[j][i]
    # So we need to invert M

    # Build M as a list of rows
    M = [[0]*32 for _ in range(32)]
    for j in range(32):
        for i in range(32):
            M[i][j] = matrix[j][i]

    # Invert via Gaussian elimination
    # Augment with identity
    aug = [row[:] + [(1 if k == r else 0) for k in range(32)]
           for r, row in enumerate(M)]
    for col in range(32):
        # Find pivot
        pivot = None
        for r in range(col, 32):
            if aug[r][col] == 1:
                pivot = r
                break
        if pivot is None:
            raise ValueError("sigma1 not invertible")
        aug[col], aug[pivot] = aug[pivot], aug[col]
        for r in range(32):
            if r != col and aug[r][col] == 1:
                for k in range(64):
                    aug[r][k] ^= aug[col][k]

    inv_matrix = [row[32:] for row in aug]

    def inv(y):
        x = 0
        for i in range(32):
            bit = 0
            for j in range(32):
                if inv_matrix[i][j]:
                    bit ^= (y >> j) & 1
            x |= (bit << i)
        return x

    # Verify
    for test_x in [0, 1, 0xdeadbeef, 0x12345678]:
        assert inv(sigma1(test_x)) == test_x, f"inv failed on {test_x:#x}"

    return inv


def enumerate_w57(m0=0x17149975, fill=0xffffffff,
                   max_w57=1<<24, sample_stride=1):
    """Enumerate W[57] values, using sigma1 bridge to fix W[58], measure HW."""
    M1 = [m0] + [fill] * 15
    M2 = list(M1)
    M2[0] ^= 0x80000000
    M2[9] ^= 0x80000000

    state1, W1_pre = precompute_state(M1)
    state2, W2_pre = precompute_state(M2)
    assert state1[0] == state2[0]

    # Schedule constants for sr=61
    sched_C1 = (W1_pre[53] + sigma0(W1_pre[45]) + W1_pre[44]) & MASK
    sched_C2 = (W2_pre[53] + sigma0(W2_pre[45]) + W2_pre[44]) & MASK

    sigma1_inv = sigma1_inv_table()
    print(f"sigma1 inverse table built. Test: sigma1_inv(sigma1(0x12345678)) = {sigma1_inv(sigma1(0x12345678)):#x}",
          flush=True)

    print(f"\nEnumerating W[57] for {m0:#x}/{fill:#x}", flush=True)
    print(f"Range: 0..{max_w57:#x} stride {sample_stride}", flush=True)
    print(f"Sched constants: C1={sched_C1:#x} C2={sched_C2:#x}", flush=True)
    print(f"State1[4..7] = e,f,g,h = {state1[4]:#x} {state1[5]:#x} {state1[6]:#x} {state1[7]:#x}",
          flush=True)
    print(flush=True)

    best_hw = 256
    best = None
    t0 = time.time()
    last_log = t0
    n_evaluated = 0

    # For each W57, compute state after round 57 (only one round, using w57)
    # Then we need W58, W59 to get to round 59 state
    # The sigma1 bridge requires W58 to be forced to satisfy de60=0
    # For now, do a simpler experiment: enumerate W57, fix W58/W59 from cert, see what happens

    # Use cert W58, W59 from the verified sr=60 collision
    cert_W1_58 = 0xd9d64416
    cert_W1_59 = 0x9e3ffb08
    cert_W2_58 = 0x4b96ca51
    cert_W2_59 = 0x587ffaa6

    for w57_idx in range(0, max_w57, sample_stride):
        n_evaluated += 1
        # Use the cert's known good W57 as the BASE, perturb by w57_idx
        # This explores the neighborhood of the known sr=60 solution
        base_W1_57 = 0x9ccfa55e
        base_W2_57 = 0x72e6c8cd
        w1_57 = base_W1_57 ^ w57_idx
        w2_57 = base_W2_57 ^ w57_idx

        # Run rounds 57, 58, 59 with cert W58, W59
        s1 = list(state1)
        s1 = round_op(s1, K[57], w1_57)
        s1 = round_op(s1, K[58], cert_W1_58)
        s1 = round_op(s1, K[59], cert_W1_59)

        s2 = list(state2)
        s2 = round_op(s2, K[57], w2_57)
        s2 = round_op(s2, K[58], cert_W2_58)
        s2 = round_op(s2, K[59], cert_W2_59)

        # Compute W[60] via sr=61 schedule rule
        w1_60 = (sigma1(cert_W1_58) + sched_C1) & MASK
        w2_60 = (sigma1(cert_W2_58) + sched_C2) & MASK

        # Apply round 60
        s1 = round_op(s1, K[60], w1_60)
        s2 = round_op(s2, K[60], w2_60)

        # Compute W[61] via sr=61 schedule rule
        sched_C1_61 = (W1_pre[54] + sigma0(W1_pre[46]) + W1_pre[45]) & MASK
        sched_C2_61 = (W2_pre[54] + sigma0(W2_pre[46]) + W2_pre[45]) & MASK
        w1_61 = (sigma1(cert_W1_59) + sched_C1_61) & MASK
        w2_61 = (sigma1(cert_W2_59) + sched_C2_61) & MASK

        s1 = round_op(s1, K[61], w1_61)
        s2 = round_op(s2, K[61], w2_61)

        # W[62], W[63] depend on computed W[60], W[61]
        sched_C1_62 = (W1_pre[55] + sigma0(W1_pre[47]) + W1_pre[46]) & MASK
        sched_C2_62 = (W2_pre[55] + sigma0(W2_pre[47]) + W2_pre[46]) & MASK
        w1_62 = (sigma1(w1_60) + sched_C1_62) & MASK
        w2_62 = (sigma1(w2_60) + sched_C2_62) & MASK

        s1 = round_op(s1, K[62], w1_62)
        s2 = round_op(s2, K[62], w2_62)

        sched_C1_63 = (W1_pre[56] + sigma0(W1_pre[48]) + W1_pre[47]) & MASK
        sched_C2_63 = (W2_pre[56] + sigma0(W2_pre[48]) + W2_pre[47]) & MASK
        w1_63 = (sigma1(w1_61) + sched_C1_63) & MASK
        w2_63 = (sigma1(w2_61) + sched_C2_63) & MASK

        s1 = round_op(s1, K[63], w1_63)
        s2 = round_op(s2, K[63], w2_63)

        # Compute state delta HW
        delta = [(s1[i] ^ s2[i]) & MASK for i in range(8)]
        hw = sum(hw32(d) for d in delta)

        if hw < best_hw:
            best_hw = hw
            best = (w1_57, w2_57, w57_idx)
            elapsed = time.time() - t0
            rate = n_evaluated / elapsed if elapsed > 0 else 0
            print(f"  NEW BEST: HW={best_hw}/256 perturb={w57_idx:#x} "
                  f"W1[57]={w1_57:#x} W2[57]={w2_57:#x} "
                  f"[{elapsed:.0f}s, {n_evaluated:,} eval, {rate:.0f}/s]",
                  flush=True)

        now = time.time()
        if now - last_log > 30:
            elapsed = now - t0
            rate = n_evaluated / elapsed
            print(f"  status: {n_evaluated:,} eval, best={best_hw}/256, {rate:.0f}/s, {elapsed:.0f}s",
                  flush=True)
            last_log = now

    elapsed = time.time() - t0
    print(f"\n{'='*60}", flush=True)
    print(f"COMPLETE: {n_evaluated:,} W57 perturbs in {elapsed:.0f}s", flush=True)
    print(f"Best HW: {best_hw}/256", flush=True)
    if best:
        print(f"Best W1[57]={best[0]:#x} W2[57]={best[1]:#x} (perturb={best[2]:#x})", flush=True)
    print(f"{'='*60}", flush=True)


if __name__ == "__main__":
    m0 = int(sys.argv[1], 0) if len(sys.argv) > 1 else 0x17149975
    fill = int(sys.argv[2], 0) if len(sys.argv) > 2 else 0xffffffff
    max_w57 = int(sys.argv[3], 0) if len(sys.argv) > 3 else 1<<24
    enumerate_w57(m0, fill, max_w57=max_w57)
