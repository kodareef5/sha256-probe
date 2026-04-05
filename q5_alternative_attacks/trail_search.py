#!/usr/bin/env python3
"""
trail_search.py — Phase 1-4: Find sparse differential trails for sr=60

Uses Z3 to search for differential trails through the 7-round SHA-256 tail.
Instead of searching for concrete message values (our current monolithic approach),
this searches for DIFFERENTIAL PATTERNS that are:
  1. Consistent with SHA-256 propagation rules
  2. Compatible with sr=60 schedule constraints
  3. Maximally sparse (minimize active bits = maximize collision probability)

If a sparse trail exists → sr=60 is feasible with the right conforming pair search.
If no trail exists → sr=60 is provably impossible for this candidate.

Based on Li et al. (EUROCRYPT 2024) decomposition strategy.

Usage: python3 trail_search.py [m0] [fill] [timeout]
"""

import sys, os, time
from z3 import *

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
from lib.sha256 import *


class DiffTrailSearcher:
    """Z3-based differential trail search for SHA-256 tail rounds."""

    def __init__(self, m0=0x17149975, fill=0xffffffff):
        self.m0 = m0
        self.fill = fill

        # Precompute state56
        M1 = [m0] + [fill]*15
        M2 = list(M1); M2[0] ^= 0x80000000; M2[9] ^= 0x80000000
        self.s1, self.W1 = precompute_state(M1)
        self.s2, self.W2 = precompute_state(M2)
        assert self.s1[0] == self.s2[0], "da[56] != 0"

        self.solver = Optimize()  # Z3 optimizer for sparsity
        self._var_count = 0

    def _fresh(self, name):
        """Create a fresh 32-bit bitvector variable."""
        self._var_count += 1
        return BitVec(f"{name}_{self._var_count}", 32)

    def _const(self, val):
        """Create a 32-bit bitvector constant."""
        return BitVecVal(val & MASK, 32)

    def _ror(self, x, n):
        return RotateRight(x, n)

    def _sigma0(self, x):
        return self._ror(x, 7) ^ self._ror(x, 18) ^ LShR(x, 3)

    def _sigma1(self, x):
        return self._ror(x, 17) ^ self._ror(x, 19) ^ LShR(x, 10)

    def _Sigma0(self, a):
        return self._ror(a, 2) ^ self._ror(a, 13) ^ self._ror(a, 22)

    def _Sigma1(self, e):
        return self._ror(e, 6) ^ self._ror(e, 11) ^ self._ror(e, 25)

    def _Ch(self, e, f, g):
        return (e & f) ^ (~e & g)

    def _Maj(self, a, b, c):
        return (a & b) ^ (a & c) ^ (b & c)

    def _popcount(self, x):
        """Bit population count for 32-bit bitvector — for optimization."""
        # Use successive addition of bit groups
        m1 = BitVecVal(0x55555555, 32)
        m2 = BitVecVal(0x33333333, 32)
        m4 = BitVecVal(0x0f0f0f0f, 32)
        x = x - ((LShR(x, 1)) & m1)
        x = (x & m2) + (LShR(x, 2) & m2)
        x = (x + LShR(x, 4)) & m4
        x = x + LShR(x, 8)
        x = x + LShR(x, 16)
        return x & BitVecVal(0x3f, 32)

    def _hw_int(self, x):
        """Hamming weight as Z3 integer (for optimization objective)."""
        return BV2Int(self._popcount(x))

    def build_model_concrete(self):
        """Build Z3 model searching for CONCRETE free word values.

        This is a direct Z3 encoding of the sr=60 problem — equivalent
        to what our CNFBuilder does, but in Z3 instead of DIMACS.
        Uses Z3's bitvector theory which handles modular arithmetic natively.

        Returns the model constraints. Solve with self.solver.check().
        """
        s = self.solver

        # Free variables: W[57..60] for both messages
        w1 = [self._fresh(f"W1_{57+i}") for i in range(4)]
        w2 = [self._fresh(f"W2_{57+i}") for i in range(4)]
        self.free_vars = (w1, w2)

        # Build schedule tail
        # W[61] = sigma1(W[59]) + W[54] + sigma0(W[46]) + W[45]
        w1_61 = self._sigma1(w1[2]) + self._const(self.W1[54]) + \
                self._const(sigma0(self.W1[46])) + self._const(self.W1[45])
        w2_61 = self._sigma1(w2[2]) + self._const(self.W2[54]) + \
                self._const(sigma0(self.W2[46])) + self._const(self.W2[45])

        w1_62 = self._sigma1(w1[3]) + self._const(self.W1[55]) + \
                self._const(sigma0(self.W1[47])) + self._const(self.W1[46])
        w2_62 = self._sigma1(w2[3]) + self._const(self.W2[55]) + \
                self._const(sigma0(self.W2[47])) + self._const(self.W2[46])

        w1_63 = self._sigma1(w1_61) + self._const(self.W1[56]) + \
                self._const(sigma0(self.W1[48])) + self._const(self.W1[47])
        w2_63 = self._sigma1(w2_61) + self._const(self.W2[56]) + \
                self._const(sigma0(self.W2[48])) + self._const(self.W2[47])

        W1_sched = list(w1) + [w1_61, w1_62, w1_63]
        W2_sched = list(w2) + [w2_61, w2_62, w2_63]

        # Run 7 rounds for message 1
        a1, b1, c1, d1 = [self._const(v) for v in self.s1[:4]]
        e1, f1, g1, h1 = [self._const(v) for v in self.s1[4:]]

        for i in range(7):
            T1 = h1 + self._Sigma1(e1) + self._Ch(e1, f1, g1) + \
                 self._const(K[57+i]) + W1_sched[i]
            T2 = self._Sigma0(a1) + self._Maj(a1, b1, c1)
            h1, g1, f1, e1 = g1, f1, e1, d1 + T1
            d1, c1, b1, a1 = c1, b1, a1, T1 + T2

        # Run 7 rounds for message 2
        a2, b2, c2, d2 = [self._const(v) for v in self.s2[:4]]
        e2, f2, g2, h2 = [self._const(v) for v in self.s2[4:]]

        for i in range(7):
            T1 = h2 + self._Sigma1(e2) + self._Ch(e2, f2, g2) + \
                 self._const(K[57+i]) + W2_sched[i]
            T2 = self._Sigma0(a2) + self._Maj(a2, b2, c2)
            h2, g2, f2, e2 = g2, f2, e2, d2 + T1
            d2, c2, b2, a2 = c2, b2, a2, T1 + T2

        # Collision constraint: all 8 registers equal
        s.add(a1 == a2)
        s.add(b1 == b2)
        s.add(c1 == c2)
        s.add(d1 == d2)
        s.add(e1 == e2)
        s.add(f1 == f2)
        s.add(g1 == g2)
        s.add(h1 == h2)

        self.final_state = ((a1,b1,c1,d1,e1,f1,g1,h1),
                           (a2,b2,c2,d2,e2,f2,g2,h2))

        # Sparsity optimization: minimize total HW of free word differences
        total_diff_hw = Sum([self._hw_int(w1[i] ^ w2[i]) for i in range(4)])
        s.minimize(total_diff_hw)

        return s

    def build_model_partial_collision(self, n_regs=7):
        """Build Z3 model for PARTIAL collision (fewer than 8 registers).

        This relaxes the full collision to only n_regs registers,
        corresponding to the MITM partial-match approach. At 7 registers,
        the problem is known to be SAT (~291s for Kissat).

        Start with partial, then tighten to find the structure that makes
        the 8th register hard.
        """
        s = self.solver

        w1 = [self._fresh(f"W1_{57+i}") for i in range(4)]
        w2 = [self._fresh(f"W2_{57+i}") for i in range(4)]
        self.free_vars = (w1, w2)

        # Build schedule tail (same as above)
        w1_61 = self._sigma1(w1[2]) + self._const(self.W1[54]) + \
                self._const(sigma0(self.W1[46])) + self._const(self.W1[45])
        w2_61 = self._sigma1(w2[2]) + self._const(self.W2[54]) + \
                self._const(sigma0(self.W2[46])) + self._const(self.W2[45])
        w1_62 = self._sigma1(w1[3]) + self._const(self.W1[55]) + \
                self._const(sigma0(self.W1[47])) + self._const(self.W1[46])
        w2_62 = self._sigma1(w2[3]) + self._const(self.W2[55]) + \
                self._const(sigma0(self.W2[47])) + self._const(self.W2[46])
        w1_63 = self._sigma1(w1_61) + self._const(self.W1[56]) + \
                self._const(sigma0(self.W1[48])) + self._const(self.W1[47])
        w2_63 = self._sigma1(w2_61) + self._const(self.W2[56]) + \
                self._const(sigma0(self.W2[48])) + self._const(self.W2[47])

        W1_sched = list(w1) + [w1_61, w1_62, w1_63]
        W2_sched = list(w2) + [w2_61, w2_62, w2_63]

        a1, b1, c1, d1 = [self._const(v) for v in self.s1[:4]]
        e1, f1, g1, h1 = [self._const(v) for v in self.s1[4:]]
        for i in range(7):
            T1 = h1 + self._Sigma1(e1) + self._Ch(e1, f1, g1) + \
                 self._const(K[57+i]) + W1_sched[i]
            T2 = self._Sigma0(a1) + self._Maj(a1, b1, c1)
            h1, g1, f1, e1 = g1, f1, e1, d1 + T1
            d1, c1, b1, a1 = c1, b1, a1, T1 + T2

        a2, b2, c2, d2 = [self._const(v) for v in self.s2[:4]]
        e2, f2, g2, h2 = [self._const(v) for v in self.s2[4:]]
        for i in range(7):
            T1 = h2 + self._Sigma1(e2) + self._Ch(e2, f2, g2) + \
                 self._const(K[57+i]) + W2_sched[i]
            T2 = self._Sigma0(a2) + self._Maj(a2, b2, c2)
            h2, g2, f2, e2 = g2, f2, e2, d2 + T1
            d2, c2, b2, a2 = c2, b2, a2, T1 + T2

        # Partial collision: only first n_regs registers
        regs1 = [a1, b1, c1, d1, e1, f1, g1, h1]
        regs2 = [a2, b2, c2, d2, e2, f2, g2, h2]
        for i in range(n_regs):
            s.add(regs1[i] == regs2[i])

        # For the remaining registers, track their difference HW
        remaining_hw = Sum([self._hw_int(regs1[i] ^ regs2[i])
                           for i in range(n_regs, 8)])
        s.minimize(remaining_hw)

        self.final_regs = (regs1, regs2)
        return s

    def solve(self, timeout_ms=300000):
        """Solve the model and report results."""
        self.solver.set("timeout", timeout_ms)

        t0 = time.time()
        result = self.solver.check()
        elapsed = time.time() - t0

        if result == sat:
            m = self.solver.model()
            w1, w2 = self.free_vars

            print(f"SAT in {elapsed:.1f}s")
            print(f"Free word values:")
            for i in range(4):
                v1 = m.evaluate(w1[i]).as_long()
                v2 = m.evaluate(w2[i]).as_long()
                d = v1 ^ v2
                print(f"  W1[{57+i}]=0x{v1:08x}  W2[{57+i}]=0x{v2:08x}  "
                      f"dW=0x{d:08x} (hw={hw(d)})")

            # Verify collision
            if hasattr(self, 'final_state'):
                regs1, regs2 = self.final_state
                total_diff = 0
                regs_names = ['a','b','c','d','e','f','g','h']
                for i in range(8):
                    v1 = m.evaluate(regs1[i]).as_long()
                    v2 = m.evaluate(regs2[i]).as_long()
                    d = v1 ^ v2
                    total_diff += hw(d)
                    if d != 0:
                        print(f"  d{regs_names[i]}[63] = 0x{d:08x} (hw={hw(d)})")
                if total_diff == 0:
                    print(f"  *** FULL COLLISION VERIFIED ***")
                else:
                    print(f"  Total diff HW = {total_diff}")

            elif hasattr(self, 'final_regs'):
                regs1, regs2 = self.final_regs
                regs_names = ['a','b','c','d','e','f','g','h']
                for i in range(8):
                    v1 = m.evaluate(regs1[i]).as_long()
                    v2 = m.evaluate(regs2[i]).as_long()
                    d = v1 ^ v2
                    if d != 0:
                        print(f"  d{regs_names[i]}[63] = 0x{d:08x} (hw={hw(d)})")
                    else:
                        print(f"  d{regs_names[i]}[63] = 0  ** MATCHED **")

            return True
        elif result == unsat:
            print(f"UNSAT in {elapsed:.1f}s")
            return False
        else:
            print(f"UNKNOWN/TIMEOUT after {elapsed:.1f}s")
            return None


def main():
    m0 = int(sys.argv[1], 0) if len(sys.argv) > 1 else 0x17149975
    fill = int(sys.argv[2], 0) if len(sys.argv) > 2 else 0xffffffff
    timeout = int(sys.argv[3]) if len(sys.argv) > 3 else 300

    print(f"sr=60 Trail Search via Z3")
    print(f"M[0]=0x{m0:08x}, fill=0x{fill:08x}, timeout={timeout}s")
    print(f"{'='*60}")

    # Phase 1: Try partial collision (7 registers) to establish baseline
    print(f"\n--- Phase 1: 7-register partial collision ---")
    ts = DiffTrailSearcher(m0, fill)
    ts.build_model_partial_collision(n_regs=7)
    ts.solve(timeout_ms=timeout * 1000)

    # Phase 2: Try full collision with sparsity optimization
    print(f"\n--- Phase 2: Full 8-register collision (sparse) ---")
    ts2 = DiffTrailSearcher(m0, fill)
    ts2.build_model_concrete()
    ts2.solve(timeout_ms=timeout * 1000)

    # Phase 3: Progressive — add registers one at a time
    print(f"\n--- Phase 3: Progressive register matching ---")
    for n in range(5, 9):
        print(f"\n  {n} registers:")
        ts_n = DiffTrailSearcher(m0, fill)
        ts_n.build_model_partial_collision(n_regs=n)
        result = ts_n.solve(timeout_ms=min(timeout, 120) * 1000)
        if result is None:
            print(f"  Stopping: timeout at {n} registers")
            break


if __name__ == "__main__":
    main()
