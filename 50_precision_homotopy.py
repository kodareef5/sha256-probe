#!/usr/bin/env python3
"""
Script 50: Precision Homotopy -- sr=60 barrier vs word size

Tests whether the sr=60 UNSAT barrier persists at reduced word sizes.
If the barrier is TOPOLOGICAL (structural), it persists at any N.
If it is CARRY-CHAIN-DEPENDENT, it vanishes at small N.

Implements a parametric N-bit "mini-SHA-256":
  - All operations adapted for N-bit words
  - Rotation amounts scaled: ROTR(x, k) -> ROTR(x, round(k*N/32))
  - Constants truncated to N bits
  - Same MSB kernel: bit (N-1) of words 0 and 9

For each word size N in [8, 12, 16, 20, 24]:
  1. Build M1, M2 with MSB kernel
  2. Precompute 57 rounds, scan M[0] for da[56]=0
  3. Encode sr=60 (4 free words) as CNF
  4. Run Kissat with 120s timeout
  5. Report SAT / UNSAT / TIMEOUT
"""

import sys
import os
import time
import subprocess
import tempfile

# ============================================================
# Parametric N-bit SHA-256 primitives
# ============================================================

# SHA-256 round constants (full 32-bit)
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
    """Scale a 32-bit rotation amount to N bits."""
    return max(1, round(k32 * N / 32))


class MiniSHA256:
    """Parametric N-bit SHA-256 for native computation."""

    def __init__(self, N):
        self.N = N
        self.MASK = (1 << N) - 1
        self.MSB  = 1 << (N - 1)

        # Precompute scaled rotation amounts
        self.r_Sig0 = [scale_rot(2, N),  scale_rot(13, N), scale_rot(22, N)]
        self.r_Sig1 = [scale_rot(6, N),  scale_rot(11, N), scale_rot(25, N)]
        self.r_sig0 = [scale_rot(7, N),  scale_rot(18, N)]
        self.s_sig0 = scale_rot(3, N)
        self.r_sig1 = [scale_rot(17, N), scale_rot(19, N)]
        self.s_sig1 = scale_rot(10, N)

        # Precompute truncated constants
        self.K = [k & self.MASK for k in K32]
        self.IV = [v & self.MASK for v in IV32]

    def ror(self, x, k):
        k = k % self.N
        return ((x >> k) | (x << (self.N - k))) & self.MASK

    def Sigma0(self, a):
        return self.ror(a, self.r_Sig0[0]) ^ self.ror(a, self.r_Sig0[1]) ^ self.ror(a, self.r_Sig0[2])

    def Sigma1(self, e):
        return self.ror(e, self.r_Sig1[0]) ^ self.ror(e, self.r_Sig1[1]) ^ self.ror(e, self.r_Sig1[2])

    def sigma0(self, x):
        return self.ror(x, self.r_sig0[0]) ^ self.ror(x, self.r_sig0[1]) ^ ((x >> self.s_sig0) & self.MASK)

    def sigma1(self, x):
        return self.ror(x, self.r_sig1[0]) ^ self.ror(x, self.r_sig1[1]) ^ ((x >> self.s_sig1) & self.MASK)

    def ch(self, e, f, g):
        return ((e & f) ^ ((~e) & g)) & self.MASK

    def maj(self, a, b, c):
        return ((a & b) ^ (a & c) ^ (b & c)) & self.MASK

    def compress(self, M):
        """Run full 57 rounds. M = list of 16 N-bit words. Returns (state, W)."""
        MASK = self.MASK

        W = list(M) + [0] * 48
        for i in range(16, 57):
            W[i] = (self.sigma1(W[i-2]) + W[i-7] + self.sigma0(W[i-15]) + W[i-16]) & MASK

        a, b, c, d, e, f, g, h = self.IV
        K = self.K
        for i in range(57):
            T1 = (h + self.Sigma1(e) + self.ch(e, f, g) + K[i] + W[i]) & MASK
            T2 = (self.Sigma0(a) + self.maj(a, b, c)) & MASK
            h = g; g = f; f = e; e = (d + T1) & MASK
            d = c; c = b; b = a; a = (T1 + T2) & MASK

        return (a, b, c, d, e, f, g, h), W

    def find_m0(self, max_scan=None, fill=None):
        """Scan M[0] for da[56]=0 with MSB kernel. Returns (m0, state1, state2, W1, W2) or None.
        If fill is None, tries multiple fill values."""
        MASK = self.MASK
        MSB  = self.MSB

        if max_scan is None:
            max_scan = 1 << self.N

        fills_to_try = [fill] if fill is not None else [MASK, 0, MASK >> 1, MSB, 0x55 & MASK, 0xAA & MASK]

        for fill_val in fills_to_try:
            result = self._scan_m0_with_fill(fill_val, max_scan)
            if result[0] is not None:
                return result

        return None, None, None, None, None

    def _scan_m0_with_fill(self, fill, max_scan):
        """Scan M[0] with a specific fill value."""
        MASK = self.MASK
        MSB  = self.MSB

        # Tight inner loop -- inline as much as possible
        K = self.K
        IV = self.IV
        N = self.N

        # Precompute rotation amounts locally for speed
        rS0 = self.r_Sig0
        rS1 = self.r_Sig1
        rs0 = self.r_sig0
        ss0 = self.s_sig0
        rs1 = self.r_sig1
        ss1 = self.s_sig1

        for m0 in range(max_scan):
            # Build M1 and M2 inline
            M1 = [m0, fill, fill, fill, fill, fill, fill, fill,
                   fill, fill, fill, fill, fill, fill, fill, fill]
            M2 = [m0 ^ MSB, fill, fill, fill, fill, fill, fill, fill,
                   fill, fill ^ MSB, fill, fill, fill, fill, fill, fill]

            # Inline schedule + compression for M1
            W1 = list(M1) + [0] * 48
            for i in range(16, 57):
                x = W1[i-2]
                s1v = (((x >> rs1[0]) | (x << (N - rs1[0]))) & MASK) ^ \
                      (((x >> rs1[1]) | (x << (N - rs1[1]))) & MASK) ^ \
                      ((x >> ss1) & MASK)
                x = W1[i-15]
                s0v = (((x >> rs0[0]) | (x << (N - rs0[0]))) & MASK) ^ \
                      (((x >> rs0[1]) | (x << (N - rs0[1]))) & MASK) ^ \
                      ((x >> ss0) & MASK)
                W1[i] = (s1v + W1[i-7] + s0v + W1[i-16]) & MASK

            a, b, c, d, e, f, g, h = IV
            for i in range(57):
                S1 = (((e >> rS1[0]) | (e << (N - rS1[0]))) & MASK) ^ \
                     (((e >> rS1[1]) | (e << (N - rS1[1]))) & MASK) ^ \
                     (((e >> rS1[2]) | (e << (N - rS1[2]))) & MASK)
                chv = ((e & f) ^ ((~e) & g)) & MASK
                T1 = (h + S1 + chv + K[i] + W1[i]) & MASK
                S0 = (((a >> rS0[0]) | (a << (N - rS0[0]))) & MASK) ^ \
                     (((a >> rS0[1]) | (a << (N - rS0[1]))) & MASK) ^ \
                     (((a >> rS0[2]) | (a << (N - rS0[2]))) & MASK)
                T2 = (S0 + ((a & b) ^ (a & c) ^ (b & c))) & MASK
                h = g; g = f; f = e; e = (d + T1) & MASK
                d = c; c = b; b = a; a = (T1 + T2) & MASK
            a1 = a

            # Inline schedule + compression for M2
            W2 = list(M2) + [0] * 48
            for i in range(16, 57):
                x = W2[i-2]
                s1v = (((x >> rs1[0]) | (x << (N - rs1[0]))) & MASK) ^ \
                      (((x >> rs1[1]) | (x << (N - rs1[1]))) & MASK) ^ \
                      ((x >> ss1) & MASK)
                x = W2[i-15]
                s0v = (((x >> rs0[0]) | (x << (N - rs0[0]))) & MASK) ^ \
                      (((x >> rs0[1]) | (x << (N - rs0[1]))) & MASK) ^ \
                      ((x >> ss0) & MASK)
                W2[i] = (s1v + W2[i-7] + s0v + W2[i-16]) & MASK

            a, b, c, d, e, f, g, h = IV
            for i in range(57):
                S1 = (((e >> rS1[0]) | (e << (N - rS1[0]))) & MASK) ^ \
                     (((e >> rS1[1]) | (e << (N - rS1[1]))) & MASK) ^ \
                     (((e >> rS1[2]) | (e << (N - rS1[2]))) & MASK)
                chv = ((e & f) ^ ((~e) & g)) & MASK
                T1 = (h + S1 + chv + K[i] + W2[i]) & MASK
                S0 = (((a >> rS0[0]) | (a << (N - rS0[0]))) & MASK) ^ \
                     (((a >> rS0[1]) | (a << (N - rS0[1]))) & MASK) ^ \
                     (((a >> rS0[2]) | (a << (N - rS0[2]))) & MASK)
                T2 = (S0 + ((a & b) ^ (a & c) ^ (b & c))) & MASK
                h = g; g = f; f = e; e = (d + T1) & MASK
                d = c; c = b; b = a; a = (T1 + T2) & MASK
            a2 = a

            if a1 == a2:
                # Found! Do full compression to get states and W arrays
                s1, W1f = self.compress(M1)
                s2, W2f = self.compress(M2)
                return m0, s1, s2, W1f, W2f

        return None, None, None, None, None


# ============================================================
# Parametric CNF builder (N-bit words)
# ============================================================

class MiniCNFBuilder:
    """CNF builder with constant propagation, parametric in word width N."""

    def __init__(self, N):
        self.N = N
        self.MASK = (1 << N) - 1
        self.clauses = []
        self.next_var = 2
        self.known = {1: True}
        self.clauses.append([1])  # var 1 = TRUE
        self.stats = {'xor': 0, 'mux': 0, 'maj': 0, 'fa': 0, 'const_fold': 0}

    def new_var(self):
        v = self.next_var
        self.next_var += 1
        return v

    def _is_known(self, lit):
        return abs(lit) in self.known

    def _get_val(self, lit):
        val = self.known[abs(lit)]
        return val if lit > 0 else not val

    def _const(self, val):
        return 1 if val else -1

    # --- Primitive gates ---

    def xor2(self, a, b):
        if self._is_known(a) and self._is_known(b):
            self.stats['const_fold'] += 1
            return self._const(self._get_val(a) ^ self._get_val(b))
        if self._is_known(a):
            self.stats['const_fold'] += 1
            return (-b) if self._get_val(a) else b
        if self._is_known(b):
            self.stats['const_fold'] += 1
            return (-a) if self._get_val(b) else a
        self.stats['xor'] += 1
        c = self.new_var()
        self.clauses.append([-a, -b, -c])
        self.clauses.append([-a,  b,  c])
        self.clauses.append([ a, -b,  c])
        self.clauses.append([ a,  b, -c])
        return c

    def and2(self, a, b):
        if self._is_known(a) and self._is_known(b):
            self.stats['const_fold'] += 1
            return self._const(self._get_val(a) and self._get_val(b))
        if self._is_known(a):
            self.stats['const_fold'] += 1
            return b if self._get_val(a) else self._const(False)
        if self._is_known(b):
            self.stats['const_fold'] += 1
            return a if self._get_val(b) else self._const(False)
        c = self.new_var()
        self.clauses.append([ a, -c])
        self.clauses.append([ b, -c])
        self.clauses.append([-a, -b, c])
        return c

    def or2(self, a, b):
        if self._is_known(a) and self._is_known(b):
            return self._const(self._get_val(a) or self._get_val(b))
        if self._is_known(a):
            return self._const(True) if self._get_val(a) else b
        if self._is_known(b):
            return self._const(True) if self._get_val(b) else a
        c = self.new_var()
        self.clauses.append([-a, c])
        self.clauses.append([-b, c])
        self.clauses.append([a, b, -c])
        return c

    def mux(self, sel, a, b):
        """result = sel ? a : b  (Ch gate)."""
        if self._is_known(sel):
            self.stats['const_fold'] += 1
            return a if self._get_val(sel) else b
        if self._is_known(a) and self._is_known(b):
            va, vb = self._get_val(a), self._get_val(b)
            if va == vb:
                self.stats['const_fold'] += 1
                return self._const(va)
            elif va:
                self.stats['const_fold'] += 1
                return sel
            else:
                self.stats['const_fold'] += 1
                return -sel
        self.stats['mux'] += 1
        r = self.new_var()
        self.clauses.append([-sel, -a,  r])
        self.clauses.append([-sel,  a, -r])
        self.clauses.append([ sel, -b,  r])
        self.clauses.append([ sel,  b, -r])
        return r

    def maj3(self, a, b, c):
        if self._is_known(a) and self._is_known(b) and self._is_known(c):
            self.stats['const_fold'] += 1
            va, vb, vc = self._get_val(a), self._get_val(b), self._get_val(c)
            return self._const((va and vb) or (va and vc) or (vb and vc))
        if self._is_known(a):
            self.stats['const_fold'] += 1
            return self.or2(b, c) if self._get_val(a) else self.and2(b, c)
        if self._is_known(b):
            self.stats['const_fold'] += 1
            return self.or2(a, c) if self._get_val(b) else self.and2(a, c)
        if self._is_known(c):
            self.stats['const_fold'] += 1
            return self.or2(a, b) if self._get_val(c) else self.and2(a, b)
        self.stats['maj'] += 1
        r = self.new_var()
        self.clauses.append([-a, -b,  r])
        self.clauses.append([-a, -c,  r])
        self.clauses.append([-b, -c,  r])
        self.clauses.append([ a,  b, -r])
        self.clauses.append([ a,  c, -r])
        self.clauses.append([ b,  c, -r])
        return r

    def full_adder(self, a, b, cin):
        self.stats['fa'] += 1
        t = self.xor2(a, b)
        s = self.xor2(t, cin)
        cout = self.maj3(a, b, cin)
        return s, cout

    def half_adder(self, a, b):
        s = self.xor2(a, b)
        cout = self.and2(a, b)
        return s, cout

    # --- N-bit word operations (LSB-first bit arrays) ---

    def const_word(self, value):
        bits = []
        for i in range(self.N):
            bits.append(self._const(bool((value >> i) & 1)))
        return bits

    def free_word(self, name=""):
        bits = []
        for i in range(self.N):
            v = self.new_var()
            bits.append(v)
        return bits

    def rotr(self, word, k):
        k = k % self.N
        if k == 0:
            return word[:]
        return word[k:] + word[:k]

    def shr_word(self, word, k):
        if k >= self.N:
            return [self._const(False)] * self.N
        zeros = [self._const(False)] * k
        return word[k:] + zeros

    def xor_word(self, A, B):
        return [self.xor2(A[i], B[i]) for i in range(self.N)]

    def add_word(self, A, B):
        C = []
        carry = self._const(False)
        for i in range(self.N):
            if self._is_known(carry) and not self._get_val(carry):
                s, carry = self.half_adder(A[i], B[i])
            else:
                s, carry = self.full_adder(A[i], B[i], carry)
            C.append(s)
        return C

    def eq_word(self, A, B):
        for i in range(self.N):
            a, b = A[i], B[i]
            if self._is_known(a) and self._is_known(b):
                if self._get_val(a) != self._get_val(b):
                    self.clauses.append([])  # UNSAT
                continue
            if self._is_known(a):
                self.clauses.append([b] if self._get_val(a) else [-b])
                continue
            if self._is_known(b):
                self.clauses.append([a] if self._get_val(b) else [-a])
                continue
            self.clauses.append([-a, b])
            self.clauses.append([a, -b])

    # --- Mini-SHA-256 round functions (parametric rotation amounts) ---

    def Sigma0(self, a, rot_amounts):
        r0, r1, r2 = rot_amounts
        return self.xor_word(self.xor_word(self.rotr(a, r0), self.rotr(a, r1)),
                             self.rotr(a, r2))

    def Sigma1(self, e, rot_amounts):
        r0, r1, r2 = rot_amounts
        return self.xor_word(self.xor_word(self.rotr(e, r0), self.rotr(e, r1)),
                             self.rotr(e, r2))

    def sigma0_w(self, x, rot_amounts, shr_amount):
        r0, r1 = rot_amounts
        return self.xor_word(self.xor_word(self.rotr(x, r0), self.rotr(x, r1)),
                             self.shr_word(x, shr_amount))

    def sigma1_w(self, x, rot_amounts, shr_amount):
        r0, r1 = rot_amounts
        return self.xor_word(self.xor_word(self.rotr(x, r0), self.rotr(x, r1)),
                             self.shr_word(x, shr_amount))

    def Ch(self, e, f, g):
        return [self.mux(e[i], f[i], g[i]) for i in range(self.N)]

    def Maj(self, a, b, c):
        return [self.maj3(a[i], b[i], c[i]) for i in range(self.N)]

    def sha256_round(self, state, Ki_val, Wi, ops_params):
        """One mini-SHA-256 round."""
        a, b, c, d, e, f, g, h = state
        K_word = self.const_word(Ki_val)

        sig1 = self.Sigma1(e, ops_params['r_Sig1'])
        ch = self.Ch(e, f, g)

        # T1 = h + Sigma1(e) + Ch(e,f,g) + K + W  (sequential adds)
        t1 = self.add_word(h, sig1)
        t1 = self.add_word(t1, ch)
        t1 = self.add_word(t1, K_word)
        t1 = self.add_word(t1, Wi)

        sig0 = self.Sigma0(a, ops_params['r_Sig0'])
        mj = self.Maj(a, b, c)
        t2 = self.add_word(sig0, mj)

        a_new = self.add_word(t1, t2)
        e_new = self.add_word(d, t1)

        return (a_new, a, b, c, e_new, e, f, g)

    def write_dimacs(self, filename):
        n_vars = self.next_var - 1
        n_clauses = len(self.clauses)
        with open(filename, 'w') as f:
            f.write(f"p cnf {n_vars} {n_clauses}\n")
            for clause in self.clauses:
                f.write(" ".join(str(l) for l in clause) + " 0\n")
        return n_vars, n_clauses


# ============================================================
# Main: precision homotopy test
# ============================================================

def run_one_wordsize(N, timeout=120):
    """Run the full sr=60 test at word width N. Return result dict."""
    flush = lambda s: (print(s), sys.stdout.flush())

    flush(f"\n{'='*60}")
    flush(f"  Word size N = {N}")
    flush(f"{'='*60}")

    sha = MiniSHA256(N)

    flush(f"  Rotation amounts (Sigma0): {sha.r_Sig0}")
    flush(f"  Rotation amounts (Sigma1): {sha.r_Sig1}")
    flush(f"  sigma0 rot/shr: {sha.r_sig0}, {sha.s_sig0}")
    flush(f"  sigma1 rot/shr: {sha.r_sig1}, {sha.s_sig1}")

    ops_params = {
        'r_Sig0': sha.r_Sig0,
        'r_Sig1': sha.r_Sig1,
        'r_sig0': sha.r_sig0,
        's_sig0': sha.s_sig0,
        'r_sig1': sha.r_sig1,
        's_sig1': sha.s_sig1,
    }

    # Step 1: Find M[0] with da[56] = 0
    scan_limit = min(1 << N, 1 << 24)  # Cap at 16M (needed for N>20)
    flush(f"\n  Scanning M[0] over {scan_limit} values for da[56]=0 ...")
    t0 = time.time()
    m0, s1, s2, W1, W2 = sha.find_m0(max_scan=scan_limit)
    scan_time = time.time() - t0

    if m0 is None:
        flush(f"  NO M[0] found with da[56]=0 in {scan_limit} values ({scan_time:.2f}s)")
        return {
            'N': N, 'result': 'NO_M0', 'time': scan_time,
            'vars': 0, 'clauses': 0, 'm0': None,
        }

    flush(f"  Found M[0] = {m0:#x} after scanning {m0+1} values in {scan_time:.2f}s")
    flush(f"  State1 a={s1[0]:#x} e={s1[4]:#x}")
    flush(f"  State2 a={s2[0]:#x} e={s2[4]:#x}")

    diffs = sum(1 for i in range(8) if s1[i] != s2[i])
    flush(f"  State diffs (of 8 registers): {diffs}")

    # Step 2: Encode sr=60 (4 free words: W[57..60])
    flush(f"\n  Encoding sr=60 (4 free words) as CNF ...")
    t0 = time.time()

    K_trunc = [k & sha.MASK for k in K32]

    cnf = MiniCNFBuilder(N)

    # Initial states as constants
    st1 = tuple(cnf.const_word(v) for v in s1)
    st2 = tuple(cnf.const_word(v) for v in s2)

    # 4 free schedule words for each message: W1[57..60], W2[57..60]
    n_free = 4
    w1_free = [cnf.free_word(f"W1_{57+i}") for i in range(n_free)]
    w2_free = [cnf.free_word(f"W2_{57+i}") for i in range(n_free)]

    # Build derived schedule words
    # W[61] = sigma1(W[59]) + W[54] + sigma0(W[46]) + W[45]
    w1_61 = cnf.add_word(
        cnf.add_word(
            cnf.sigma1_w(w1_free[2], ops_params['r_sig1'], ops_params['s_sig1']),
            cnf.const_word(W1[54])),
        cnf.add_word(
            cnf.const_word(sha.sigma0(W1[46])),
            cnf.const_word(W1[45]))
    )
    w2_61 = cnf.add_word(
        cnf.add_word(
            cnf.sigma1_w(w2_free[2], ops_params['r_sig1'], ops_params['s_sig1']),
            cnf.const_word(W2[54])),
        cnf.add_word(
            cnf.const_word(sha.sigma0(W2[46])),
            cnf.const_word(W2[45]))
    )

    # W[62] = sigma1(W[60]) + W[55] + sigma0(W[47]) + W[46]
    w1_62 = cnf.add_word(
        cnf.add_word(
            cnf.sigma1_w(w1_free[3], ops_params['r_sig1'], ops_params['s_sig1']),
            cnf.const_word(W1[55])),
        cnf.add_word(
            cnf.const_word(sha.sigma0(W1[47])),
            cnf.const_word(W1[46]))
    )
    w2_62 = cnf.add_word(
        cnf.add_word(
            cnf.sigma1_w(w2_free[3], ops_params['r_sig1'], ops_params['s_sig1']),
            cnf.const_word(W2[55])),
        cnf.add_word(
            cnf.const_word(sha.sigma0(W2[47])),
            cnf.const_word(W2[46]))
    )

    # W[63] = sigma1(W[61]) + W[56] + sigma0(W[48]) + W[47]
    w1_63 = cnf.add_word(
        cnf.add_word(
            cnf.sigma1_w(w1_61, ops_params['r_sig1'], ops_params['s_sig1']),
            cnf.const_word(W1[56])),
        cnf.add_word(
            cnf.const_word(sha.sigma0(W1[48])),
            cnf.const_word(W1[47]))
    )
    w2_63 = cnf.add_word(
        cnf.add_word(
            cnf.sigma1_w(w2_61, ops_params['r_sig1'], ops_params['s_sig1']),
            cnf.const_word(W2[56])),
        cnf.add_word(
            cnf.const_word(sha.sigma0(W2[48])),
            cnf.const_word(W2[47]))
    )

    # Full schedule for 7 rounds: indices 57..63
    W1_sched = w1_free + [w1_61, w1_62, w1_63]  # 4 free + 3 derived = 7
    W2_sched = w2_free + [w2_61, w2_62, w2_63]

    # Run 7 rounds for both messages
    for i in range(7):
        st1 = cnf.sha256_round(st1, K_trunc[57 + i], W1_sched[i], ops_params)
    for i in range(7):
        st2 = cnf.sha256_round(st2, K_trunc[57 + i], W2_sched[i], ops_params)

    # Collision constraint: all 8 output registers must match
    for i in range(8):
        cnf.eq_word(st1[i], st2[i])

    encode_time = time.time() - t0

    # Check for trivially UNSAT (empty clause inserted)
    has_empty = any(len(c) == 0 for c in cnf.clauses)
    if has_empty:
        flush(f"  Encoding produced empty clause -- TRIVIALLY UNSAT")
        flush(f"  Encode time: {encode_time:.2f}s")
        flush(f"  Variables: {cnf.next_var - 1}, Clauses: {len(cnf.clauses)}")
        return {
            'N': N, 'result': 'UNSAT_TRIVIAL', 'time': encode_time,
            'vars': cnf.next_var - 1, 'clauses': len(cnf.clauses), 'm0': m0,
        }

    # Write DIMACS
    tmpdir = tempfile.mkdtemp()
    dimacs_path = os.path.join(tmpdir, f"sr60_N{N}.cnf")
    n_vars, n_clauses = cnf.write_dimacs(dimacs_path)

    flush(f"  Variables: {n_vars}, Clauses: {n_clauses}")
    flush(f"  Stats: XOR={cnf.stats['xor']} MUX={cnf.stats['mux']} "
          f"MAJ={cnf.stats['maj']} FA={cnf.stats['fa']} fold={cnf.stats['const_fold']}")
    flush(f"  Encode time: {encode_time:.2f}s")
    flush(f"  DIMACS: {dimacs_path}")

    # Step 3: Run Kissat
    flush(f"\n  Running Kissat (timeout={timeout}s) ...")
    t0 = time.time()
    try:
        proc = subprocess.run(
            ['kissat', '--quiet', dimacs_path],
            capture_output=True, text=True, timeout=timeout
        )
        solve_time = time.time() - t0
        rc = proc.returncode

        if rc == 10:
            result = 'SAT'
            flush(f"  *** SAT *** in {solve_time:.2f}s")
        elif rc == 20:
            result = 'UNSAT'
            flush(f"  UNSAT in {solve_time:.2f}s")
        else:
            result = f'UNKNOWN(rc={rc})'
            flush(f"  Unknown result (rc={rc}) in {solve_time:.2f}s")
            if proc.stderr:
                flush(f"  stderr: {proc.stderr[:200]}")

    except subprocess.TimeoutExpired:
        solve_time = timeout
        result = 'TIMEOUT'
        flush(f"  TIMEOUT after {timeout}s")

    # Cleanup
    try:
        os.unlink(dimacs_path)
        os.rmdir(tmpdir)
    except:
        pass

    return {
        'N': N, 'result': result, 'time': solve_time,
        'vars': n_vars, 'clauses': n_clauses, 'm0': m0,
        'encode_time': encode_time,
    }


def main():
    word_sizes = [8, 9, 10, 11, 12]
    if '--extended' in sys.argv:
        word_sizes = [8, 9, 10, 11, 12, 16, 20, 24]
    if '--include-32' in sys.argv:
        word_sizes.append(32)

    timeout = 600
    for arg in sys.argv[1:]:
        if arg.startswith('--timeout='):
            timeout = int(arg.split('=')[1])

    print("Precision Homotopy: sr=60 barrier vs word size")
    print(f"Word sizes: {word_sizes}")
    print(f"Kissat timeout: {timeout}s")
    sys.stdout.flush()

    results = []
    for N in word_sizes:
        r = run_one_wordsize(N, timeout=timeout)
        results.append(r)

    # Summary table
    print(f"\n{'='*72}")
    print(f"  SUMMARY: sr=60 barrier vs word size")
    print(f"{'='*72}")
    print(f"{'N':>4} {'M[0]':>10} {'Vars':>8} {'Clauses':>10} {'Result':>12} {'Solve(s)':>10} {'Encode(s)':>10}")
    print(f"{'-'*4} {'-'*10} {'-'*8} {'-'*10} {'-'*12} {'-'*10} {'-'*10}")

    for r in results:
        m0_str = f"{r['m0']:#x}" if r['m0'] is not None else "N/A"
        enc_str = f"{r.get('encode_time', 0):.2f}"
        print(f"{r['N']:>4} {m0_str:>10} {r['vars']:>8} {r['clauses']:>10} "
              f"{r['result']:>12} {r['time']:>10.2f} {enc_str:>10}")

    print()

    # Interpretation
    sat_results   = [r for r in results if r['result'] == 'SAT']
    unsat_results = [r for r in results if 'UNSAT' in r['result']]
    to_results    = [r for r in results if r['result'] == 'TIMEOUT']
    nom0_results  = [r for r in results if r['result'] == 'NO_M0']

    if sat_results and unsat_results:
        sat_ns = sorted([r['N'] for r in sat_results])
        unsat_ns = sorted([r['N'] for r in unsat_results])
        print(f"PHASE TRANSITION detected!")
        print(f"  SAT at N = {sat_ns}")
        print(f"  UNSAT at N = {unsat_ns}")
        if max(sat_ns) < min(unsat_ns):
            print(f"  Barrier appears at N > {max(sat_ns)}, N <= {min(unsat_ns)}")
            print(f"  => CARRY-CHAIN DEPENDENT: barrier needs sufficient precision")
        else:
            print(f"  Mixed pattern -- further investigation needed")
    elif sat_results and not unsat_results:
        print(f"ALL SAT: barrier does NOT persist at small word sizes")
        print(f"  => CARRY-CHAIN DEPENDENT")
    elif unsat_results and not sat_results:
        if to_results:
            print(f"UNSAT where solved, TIMEOUT elsewhere:")
            print(f"  UNSAT at N = {sorted([r['N'] for r in unsat_results])}")
            print(f"  TIMEOUT at N = {sorted([r['N'] for r in to_results])}")
            print(f"  => Likely TOPOLOGICAL (barrier persists)")
        else:
            print(f"ALL UNSAT: barrier persists at all tested word sizes")
            print(f"  => TOPOLOGICAL")
    else:
        print(f"Inconclusive: SAT={len(sat_results)} UNSAT={len(unsat_results)} "
              f"TIMEOUT={len(to_results)} NO_M0={len(nom0_results)}")

    sys.stdout.flush()


if __name__ == '__main__':
    main()
