"""
CNFBuilder: DIMACS CNF encoder with aggressive constant propagation.

This is the core encoding engine. The CNFBuilder class constructs
SAT circuits for SHA-256 tail rounds with constant folding.

Import SHA-256 primitives from lib.sha256 for the native precomputation step.
"""

from lib.sha256 import K, sigma0 as sigma0_py, sigma1 as sigma1_py, precompute_state


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


def encode_collision(mode="sr59", m0=0x17149975, fill=0xffffffff):
    """
    Encode the sr=59 or sr=60 collision problem as DIMACS CNF.
    mode: "sr59" (5 free words) or "sr60" (4 free words)
    Returns a CNFBuilder instance with the collision constraints.
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
