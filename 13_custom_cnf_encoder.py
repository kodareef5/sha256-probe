#!/usr/bin/env python3
"""
Script 13: Custom DIMACS CNF Encoder for sr=59/sr=60

Generates optimized DIMACS CNF matching the paper's reduced encoding approach:
1. Precomputes rounds 0-56 natively (constant folding)
2. Encodes only rounds 57-63 as SAT circuit
3. Constant propagation: when gate inputs are known, computes result directly
4. Rotation/shift: free (wire routing, no clauses)
5. XOR: 4 clauses per 2-input gate
6. Ch (MUX): 4 clauses, simplified when selector or inputs are constant
7. Maj: 6 clauses, simplified when inputs are constant
8. Addition: ripple-carry full adder chain

Target: ~10K variables, ~60K clauses (matching paper's sr59_cdcl.c)

Usage:
  python3 13_custom_cnf_encoder.py sr59 [kissat_timeout]
  python3 13_custom_cnf_encoder.py sr60 [kissat_timeout]
"""

import sys
import os
import time
import subprocess

# === SHA-256 Constants ===
def ROR(x, n): return ((x >> n) | (x << (32 - n))) & 0xFFFFFFFF
def SHR(x, n): return x >> n
def Ch_py(e, f, g): return ((e & f) ^ ((~e) & g)) & 0xFFFFFFFF
def Maj_py(a, b, c): return (a & b) ^ (a & c) ^ (b & c)
def Sigma0_py(a): return ROR(a, 2) ^ ROR(a, 13) ^ ROR(a, 22)
def Sigma1_py(e): return ROR(e, 6) ^ ROR(e, 11) ^ ROR(e, 25)
def sigma0_py(x): return ROR(x, 7) ^ ROR(x, 18) ^ SHR(x, 3)
def sigma1_py(x): return ROR(x, 17) ^ ROR(x, 19) ^ SHR(x, 10)

K = [
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
]
IV = [0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
      0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19]


# === CNF Builder with Constant Propagation ===

class CNFBuilder:
    """
    Builds a DIMACS CNF with aggressive constant propagation.

    Bit representation:
      - Positive int: SAT variable ID
      - Negative int: negated SAT variable
      - Special: variable 1 is TRUE (unit clause [1])
      - Constants: 1 = True, -1 = False

    When gate inputs are known constants, the output is computed directly
    in Python without creating any SAT variables or clauses.
    """

    def __init__(self):
        self.clauses = []
        self.next_var = 2     # var 1 = TRUE
        self.known = {1: True}
        self.clauses.append([1])  # Unit clause: var 1 = TRUE
        self.free_var_names = {}  # var_id -> name for solution extraction
        self.stats = {'xor': 0, 'and': 0, 'mux': 0, 'maj': 0, 'fa': 0, 'const_fold': 0}

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

    # --- Primitive Gates with Constant Propagation ---

    def xor2(self, a, b):
        """c = a XOR b. 4 clauses (or 0 if constant-folded)."""
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
        self.clauses.append([-a, b, c])
        self.clauses.append([a, -b, c])
        self.clauses.append([a, b, -c])
        return c

    def and2(self, a, b):
        """c = a AND b. 3 clauses."""
        if self._is_known(a) and self._is_known(b):
            self.stats['const_fold'] += 1
            return self._const(self._get_val(a) and self._get_val(b))
        if self._is_known(a):
            self.stats['const_fold'] += 1
            return b if self._get_val(a) else self._const(False)
        if self._is_known(b):
            self.stats['const_fold'] += 1
            return a if self._get_val(b) else self._const(False)
        self.stats['and'] += 1
        c = self.new_var()
        self.clauses.append([a, -c])
        self.clauses.append([b, -c])
        self.clauses.append([-a, -b, c])
        return c

    def mux(self, sel, a, b):
        """result = sel ? a : b (Ch gate). 4 clauses."""
        if self._is_known(sel):
            self.stats['const_fold'] += 1
            return a if self._get_val(sel) else b
        if self._is_known(a) and self._is_known(b):
            va, vb = self._get_val(a), self._get_val(b)
            if va == vb:
                self.stats['const_fold'] += 1
                return self._const(va)
            elif va:  # a=1, b=0 -> result = sel
                self.stats['const_fold'] += 1
                return sel
            else:     # a=0, b=1 -> result = NOT sel
                self.stats['const_fold'] += 1
                return -sel
        self.stats['mux'] += 1
        r = self.new_var()
        self.clauses.append([-sel, -a, r])
        self.clauses.append([-sel, a, -r])
        self.clauses.append([sel, -b, r])
        self.clauses.append([sel, b, -r])
        return r

    def maj(self, a, b, c):
        """result = MAJ(a,b,c). 6 clauses."""
        if self._is_known(a) and self._is_known(b) and self._is_known(c):
            self.stats['const_fold'] += 1
            va, vb, vc = self._get_val(a), self._get_val(b), self._get_val(c)
            return self._const((va and vb) or (va and vc) or (vb and vc))
        # Simplify when one input is known
        if self._is_known(a):
            self.stats['const_fold'] += 1
            if self._get_val(a):
                return self.or2(b, c)  # MAJ(1,b,c) = b OR c
            else:
                return self.and2(b, c)  # MAJ(0,b,c) = b AND c
        if self._is_known(b):
            self.stats['const_fold'] += 1
            if self._get_val(b):
                return self.or2(a, c)
            else:
                return self.and2(a, c)
        if self._is_known(c):
            self.stats['const_fold'] += 1
            if self._get_val(c):
                return self.or2(a, b)
            else:
                return self.and2(a, b)
        self.stats['maj'] += 1
        r = self.new_var()
        self.clauses.append([-a, -b, r])
        self.clauses.append([-a, -c, r])
        self.clauses.append([-b, -c, r])
        self.clauses.append([a, b, -r])
        self.clauses.append([a, c, -r])
        self.clauses.append([b, c, -r])
        return r

    def or2(self, a, b):
        """c = a OR b. 3 clauses."""
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

    def full_adder(self, a, b, cin):
        """(sum, cout) = FA(a, b, cin). sum = XOR3, cout = MAJ."""
        self.stats['fa'] += 1
        t = self.xor2(a, b)
        s = self.xor2(t, cin)
        # cout = MAJ(a, b, cin) = (a&b) | (cin & (a^b)) = (a&b) | (cin & t)
        cout = self.maj(a, b, cin)
        return s, cout

    def half_adder(self, a, b):
        """(sum, cout) = HA(a, b)."""
        s = self.xor2(a, b)
        cout = self.and2(a, b)
        return s, cout

    # --- 32-bit Word Operations (LSB-first bit arrays) ---

    def const_word(self, value):
        """Create a word from a constant 32-bit integer. No variables/clauses."""
        bits = []
        for i in range(32):
            bits.append(self._const(bool((value >> i) & 1)))
        return bits

    def free_word(self, name):
        """Create a free 32-bit word (SAT variables). 32 new variables."""
        bits = []
        for i in range(32):
            v = self.new_var()
            self.free_var_names[v] = f"{name}[{i}]"
            bits.append(v)
        return bits

    def rotr(self, word, n):
        """Rotate right. Free (wire routing)."""
        n = n % 32
        return word[n:] + word[:n]

    def shr_word(self, word, n):
        """Shift right. Upper bits become constant 0."""
        zeros = [self._const(False)] * n
        return word[n:] + zeros

    def xor_word(self, A, B):
        """C = A XOR B (bitwise)."""
        return [self.xor2(A[i], B[i]) for i in range(32)]

    def add_word(self, A, B, track_carries=False):
        """C = A + B (mod 2^32). Ripple-carry addition.
        If track_carries=True, returns (C, carries) where carries[i] is
        the carry-out of column i (variable IDs for cubing)."""
        C = []
        carries = []
        carry = self._const(False)
        for i in range(32):
            if self._is_known(carry) and not self._get_val(carry):
                s, carry = self.half_adder(A[i], B[i])
            else:
                s, carry = self.full_adder(A[i], B[i], carry)
            C.append(s)
            carries.append(carry)
        if track_carries:
            return C, carries
        return C

    def csa_layer(self, A, B, C):
        """
        Carry-Save Adder: reduce 3 words to 2 (sum + carry) WITHOUT
        carry propagation. Each column is independent.

        sum[i] = A[i] XOR B[i] XOR C[i]
        carry[i+1] = MAJ(A[i], B[i], C[i])

        Returns (sum_word, carry_word) where carry is shifted left by 1.
        """
        S = []
        Cout = [self._const(False)]  # carry[0] = 0
        for i in range(32):
            s = self.xor2(self.xor2(A[i], B[i]), C[i])
            c = self.maj(A[i], B[i], C[i])
            S.append(s)
            if i < 31:
                Cout.append(c)
        return S, Cout

    def add5_csa(self, A, B, C, D, E):
        """
        Add 5 words using CSA tree + final ripple carry.

        CSA tree: 5 inputs -> 2 via 3 CSA levels
          Level 1: CSA(A, B, C) -> (s1, c1)     [5 -> 4]
          Level 2: CSA(s1, D, E) -> (s2, c2)     [4 -> 3]
          Level 3: CSA(c1, s2, c2) -> (s3, c3)   [3 -> 2]
          Final:   s3 + c3  (one ripple carry)

        Depth: 3 CSA levels (parallel) + 32-bit carry = ~35
        vs ripple-carry: 4 sequential 32-bit carries = ~128
        """
        s1, c1 = self.csa_layer(A, B, C)
        s2, c2 = self.csa_layer(s1, D, E)
        s3, c3 = self.csa_layer(c1, s2, c2)
        return self.add_word(s3, c3)

    def add5_csa_tracked(self, A, B, C, D, E):
        """Same as add5_csa but returns (result, final_carries)."""
        s1, c1 = self.csa_layer(A, B, C)
        s2, c2 = self.csa_layer(s1, D, E)
        s3, c3 = self.csa_layer(c1, s2, c2)
        return self.add_word(s3, c3, track_carries=True)

    def eq_word(self, A, B):
        """Add equality constraints: A == B."""
        for i in range(32):
            a, b = A[i], B[i]
            if self._is_known(a) and self._is_known(b):
                if self._get_val(a) != self._get_val(b):
                    self.clauses.append([])  # Empty clause = UNSAT
                continue
            if self._is_known(a):
                if self._get_val(a):
                    self.clauses.append([b])
                else:
                    self.clauses.append([-b])
                continue
            if self._is_known(b):
                if self._get_val(b):
                    self.clauses.append([a])
                else:
                    self.clauses.append([-a])
                continue
            self.clauses.append([-a, b])
            self.clauses.append([a, -b])

    # --- SHA-256 Round Functions ---

    def Sigma0(self, a):
        """Big Sigma 0: ROTR(2) XOR ROTR(13) XOR ROTR(22)."""
        return self.xor_word(self.xor_word(self.rotr(a, 2), self.rotr(a, 13)), self.rotr(a, 22))

    def Sigma1(self, e):
        """Big Sigma 1: ROTR(6) XOR ROTR(11) XOR ROTR(25)."""
        return self.xor_word(self.xor_word(self.rotr(e, 6), self.rotr(e, 11)), self.rotr(e, 25))

    def sigma0_w(self, x):
        """Small sigma 0: ROTR(7) XOR ROTR(18) XOR SHR(3)."""
        return self.xor_word(self.xor_word(self.rotr(x, 7), self.rotr(x, 18)), self.shr_word(x, 3))

    def sigma1_w(self, x):
        """Small sigma 1: ROTR(17) XOR ROTR(19) XOR SHR(10)."""
        return self.xor_word(self.xor_word(self.rotr(x, 17), self.rotr(x, 19)), self.shr_word(x, 10))

    def Ch(self, e, f, g):
        """Ch(e,f,g) = e ? f : g (bitwise MUX)."""
        return [self.mux(e[i], f[i], g[i]) for i in range(32)]

    def Maj(self, a, b, c):
        """Maj(a,b,c) = majority (bitwise)."""
        return [self.maj(a[i], b[i], c[i]) for i in range(32)]

    def sha256_round(self, state, Ki, Wi):
        """
        One SHA-256 round. state = (a,b,c,d,e,f,g,h) as bit arrays.
        Ki = round constant (integer), Wi = schedule word (bit array).
        Returns new state.
        """
        a, b, c, d, e, f, g, h = state
        K_word = self.const_word(Ki)

        sig1 = self.Sigma1(e)
        ch = self.Ch(e, f, g)
        # T1 = h + Sigma1(e) + Ch(e,f,g) + K + W
        t1 = self.add_word(h, sig1)
        t1 = self.add_word(t1, ch)
        t1 = self.add_word(t1, K_word)
        t1 = self.add_word(t1, Wi)

        sig0 = self.Sigma0(a)
        mj = self.Maj(a, b, c)
        # T2 = Sigma0(a) + Maj(a,b,c)
        t2 = self.add_word(sig0, mj)

        # New state
        a_new = self.add_word(t1, t2)
        e_new = self.add_word(d, t1)

        return (a_new, b[:], c[:], d[:], e_new, f[:], g[:], h[:])
        # Wait, the shift register is: (a_new, a, b, c, e_new, e, f, g)

    def sha256_round_correct(self, state, Ki, Wi):
        """
        One SHA-256 round with correct shift-register update.
        Uses CSA tree for the 5-input T1 addition (h + Sigma1 + Ch + K + W).
        """
        a, b, c, d, e, f, g, h = state
        K_word = self.const_word(Ki)

        sig1 = self.Sigma1(e)
        ch = self.Ch(e, f, g)

        # T1 = h + Sigma1(e) + Ch(e,f,g) + K + W  -- 5-input via CSA tree
        t1 = self.add5_csa(h, sig1, ch, K_word, Wi)

        sig0 = self.Sigma0(a)
        mj = self.Maj(a, b, c)
        # T2 = Sigma0(a) + Maj(a,b,c)  -- 2-input ripple carry
        t2 = self.add_word(sig0, mj)

        # a_new = T1 + T2, e_new = d + T1  -- 2-input each
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


# === Main Encoder ===

def precompute_state(M):
    W = [0] * 57
    for i in range(16): W[i] = M[i]
    for i in range(16, 57):
        W[i] = (sigma1_py(W[i-2]) + W[i-7] + sigma0_py(W[i-15]) + W[i-16]) & 0xFFFFFFFF
    a, b, c, d, e, f, g, h = IV
    for i in range(57):
        T1 = (h + Sigma1_py(e) + Ch_py(e, f, g) + K[i] + W[i]) & 0xFFFFFFFF
        T2 = (Sigma0_py(a) + Maj_py(a, b, c)) & 0xFFFFFFFF
        h = g; g = f; f = e; e = (d + T1) & 0xFFFFFFFF
        d = c; c = b; b = a; a = (T1 + T2) & 0xFFFFFFFF
    return (a, b, c, d, e, f, g, h), W


def encode_collision(mode="sr59", m0=0x17149975, m1_override=None):
    """
    Encode the sr=59 or sr=60 collision problem as DIMACS CNF.

    mode: "sr59" (5 free words) or "sr60" (4 free words)
    """
    # Build messages
    M1 = [m0] + [0xffffffff] * 15
    if m1_override is not None:
        M1[1] = m1_override
    M2 = M1.copy()
    M2[0] ^= 0x80000000
    M2[9] ^= 0x80000000

    state1, W1_pre = precompute_state(M1)
    state2, W2_pre = precompute_state(M2)

    assert state1[0] == state2[0], f"da[56] != 0: {state1[0]:#x} vs {state2[0]:#x}"

    n_free = 5 if mode == "sr59" else 4

    cnf = CNFBuilder()

    # Create initial states as constant words
    s1 = tuple(cnf.const_word(v) for v in state1)
    s2 = tuple(cnf.const_word(v) for v in state2)

    # Create free variables for W[57..57+n_free-1]
    w1_free = [cnf.free_word(f"W1_{57+i}") for i in range(n_free)]
    w2_free = [cnf.free_word(f"W2_{57+i}") for i in range(n_free)]

    # Build schedule for tail rounds
    # For sr=59: free = {57,58,59,60,61}, enforce W[62] and W[63]
    # For sr=60: free = {57,58,59,60}, enforce W[61], W[62], W[63]

    W1_schedule = list(w1_free)
    W2_schedule = list(w2_free)

    if mode == "sr60":
        # W[61] = sigma1(W[59]) + W[54] + sigma0(W[46]) + W[45]
        w1_61 = cnf.add_word(
            cnf.add_word(cnf.sigma1_w(w1_free[2]), cnf.const_word(W1_pre[54])),
            cnf.add_word(cnf.const_word(sigma0_py(W1_pre[46])), cnf.const_word(W1_pre[45]))
        )
        w2_61 = cnf.add_word(
            cnf.add_word(cnf.sigma1_w(w2_free[2]), cnf.const_word(W2_pre[54])),
            cnf.add_word(cnf.const_word(sigma0_py(W2_pre[46])), cnf.const_word(W2_pre[45]))
        )
        W1_schedule.append(w1_61)
        W2_schedule.append(w2_61)

    # W[62] = sigma1(W[60]) + W[55] + sigma0(W[47]) + W[46]
    w60_idx = 3  # W[60] is at index 3 in the free array
    w1_62 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(W1_schedule[w60_idx]), cnf.const_word(W1_pre[55])),
        cnf.add_word(cnf.const_word(sigma0_py(W1_pre[47])), cnf.const_word(W1_pre[46]))
    )
    w2_62 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(W2_schedule[w60_idx]), cnf.const_word(W2_pre[55])),
        cnf.add_word(cnf.const_word(sigma0_py(W2_pre[47])), cnf.const_word(W2_pre[46]))
    )

    # W[63] = sigma1(W[61]) + W[56] + sigma0(W[48]) + W[47]
    w61_idx = 4  # W[61] is at index 4
    w1_63 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(W1_schedule[w61_idx]), cnf.const_word(W1_pre[56])),
        cnf.add_word(cnf.const_word(sigma0_py(W1_pre[48])), cnf.const_word(W1_pre[47]))
    )
    w2_63 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(W2_schedule[w61_idx]), cnf.const_word(W2_pre[56])),
        cnf.add_word(cnf.const_word(sigma0_py(W2_pre[48])), cnf.const_word(W2_pre[47]))
    )

    W1_schedule.append(w1_62)
    W1_schedule.append(w1_63)
    W2_schedule.append(w2_62)
    W2_schedule.append(w2_63)

    # Run 7 rounds for both messages
    print(f"Encoding 7 rounds for message 1...")
    st1 = s1
    for i in range(7):
        st1 = cnf.sha256_round_correct(st1, K[57 + i], W1_schedule[i])
        n = cnf.next_var - 1
        nc = len(cnf.clauses)
        print(f"  Round {57+i}: {n} vars, {nc} clauses")

    print(f"Encoding 7 rounds for message 2...")
    st2 = s2
    for i in range(7):
        st2 = cnf.sha256_round_correct(st2, K[57 + i], W2_schedule[i])
        n = cnf.next_var - 1
        nc = len(cnf.clauses)
        print(f"  Round {57+i}: {n} vars, {nc} clauses")

    # Collision constraint
    print("Adding collision constraints...")
    for i in range(8):
        cnf.eq_word(st1[i], st2[i])

    print(f"\nEncoder statistics:")
    print(f"  XOR gates: {cnf.stats['xor']}")
    print(f"  MUX gates: {cnf.stats['mux']}")
    print(f"  MAJ gates: {cnf.stats['maj']}")
    print(f"  Full adders: {cnf.stats['fa']}")
    print(f"  Constant folds: {cnf.stats['const_fold']}")

    return cnf


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "sr59"
    timeout = int(sys.argv[2]) if len(sys.argv) > 2 else 3600

    print("=" * 70)
    print(f"Custom DIMACS CNF Encoder for {mode}")
    print("=" * 70)

    t0 = time.time()
    cnf = encode_collision(mode)
    t_encode = time.time() - t0

    # Write DIMACS
    cnf_file = f"/tmp/{mode}_custom.cnf"
    n_vars, n_clauses = cnf.write_dimacs(cnf_file)
    file_size = os.path.getsize(cnf_file)

    print(f"\nDIMACS output: {cnf_file}")
    print(f"  Variables: {n_vars}")
    print(f"  Clauses: {n_clauses}")
    print(f"  File size: {file_size // 1024} KB")
    print(f"  Encoding time: {t_encode:.1f}s")

    print(f"\n  Paper's reduced encoding: ~10K vars, ~58K clauses")
    print(f"  Paper's basic encoding:   ~104K vars, ~677K clauses")
    ratio = n_vars / 10000
    print(f"  Our ratio vs paper reduced: {ratio:.1f}x vars")

    # Run kissat
    print(f"\n{'='*70}")
    print(f"Running Kissat (timeout: {timeout}s)")
    print(f"{'='*70}")

    try:
        t0 = time.time()
        result = subprocess.run(
            ["timeout", str(timeout), "kissat", cnf_file],
            capture_output=True, text=True, timeout=timeout + 60
        )
        elapsed = time.time() - t0

        # Parse result
        lines = result.stdout.split('\n')
        sat_line = [l for l in lines if l.startswith('s ')]
        stats_lines = [l for l in lines if 'conflicts' in l.lower() or 'decisions' in l.lower()
                       or 'propagations' in l.lower() or 'process-time' in l.lower()]

        if sat_line:
            print(f"Result: {sat_line[0]}")
        else:
            print(f"Result: timeout/unknown (exit code {result.returncode})")

        for sl in stats_lines[-5:]:
            print(f"  {sl.strip()}")

        print(f"Time: {elapsed:.1f}s")

        if result.returncode == 10:
            print("\n[!!!] SATISFIABLE!")
            # Extract solution
            solution = {}
            for line in lines:
                if line.startswith('v '):
                    for lit in line[2:].split():
                        lit_val = int(lit)
                        if lit_val != 0:
                            solution[abs(lit_val)] = (lit_val > 0)

            # Reconstruct free words
            for word_idx in range(5 if mode == "sr59" else 4):
                for msg in [1, 2]:
                    val = 0
                    for bit in range(32):
                        name = f"W{msg}_{57+word_idx}[{bit}]"
                        for var_id, var_name in cnf.free_var_names.items():
                            if var_name == name and var_id in solution:
                                if solution[var_id]:
                                    val |= (1 << bit)
                    print(f"  W{msg}[{57+word_idx}] = 0x{val:08x}")

        elif result.returncode == 20:
            print("\nUNSATISFIABLE")
            print(f"This candidate CANNOT achieve {mode}.")

    except subprocess.TimeoutExpired:
        print(f"Timeout after {timeout}s")
    except FileNotFoundError:
        print("kissat not found. Install with: cd /tmp && git clone https://github.com/arminbiere/kissat.git && cd kissat && ./configure && make && cp build/kissat /usr/local/bin/")


if __name__ == "__main__":
    main()
