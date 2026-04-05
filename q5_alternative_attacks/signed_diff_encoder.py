#!/usr/bin/env python3
"""
signed_diff_encoder.py — Signed-difference SAT encoder for sr=60 trail search

Adapts Li et al.'s constraint tables for our 7-round SHA-256 tail problem.
Instead of encoding concrete bit values for two messages, this encodes
signed differences at each bit position: (v, d) pairs where v=value, d=diff.

The constraints come directly from Li et al.'s truth tables (constrain_condition.py),
which enumerate all valid signed-diff transitions for each SHA-256 operation.

Variable encoding per bit position:
  v = value bit (of message 1)
  d = difference flag (1 if messages differ at this bit)

Operations modeled:
  - XOR (bitwise): 11 variables per bit (3 inputs × (v,d) + 2 outputs × (v,d) + ???)
    Actually: xor_full_constrain has 11-char patterns
  - IF/Ch (bitwise): ifz_full_constrain has 11-char patterns
  - MAJ (bitwise): maj_full_constrain has 11-char patterns
  - Modular addition: modular_addition_constrain has 10-char patterns per bit
  - Expand model: expand_model_constrain has 8-char patterns
"""

import sys, os

# Import Li et al.'s constraint tables
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                '..', 'reference', 'sha_2_attack', 'find_dc', 'configuration'))
from constrain_condition import (
    modular_addition_constrain,
    expand_model_constrain_1,
    expand_model_constrain_2,
    xor_full_constrain,
    ifz_full_constrain,
    maj_full_constrain,
    modular_addition_value_constrain,
    xor_value_constrain,
    ifx_value_constrain,
    maj_value_constrain,
)


class SignedDiffCNF:
    """CNF builder for signed-difference constraints."""

    def __init__(self):
        self.clauses = []
        self.next_var = 1
        self.var_names = {}

    def new_var(self, name=""):
        v = self.next_var
        self.next_var += 1
        if name:
            self.var_names[v] = name
        return v

    def new_bit(self, name=""):
        """Create a (value, diff) pair for one bit position."""
        v = self.new_var(f"{name}_v")
        d = self.new_var(f"{name}_d")
        return (v, d)

    def new_word(self, name="", N=32):
        """Create N (value, diff) pairs for a word. LSB first."""
        return [self.new_bit(f"{name}_{i}") for i in range(N)]

    def fix_bit(self, bit, symbol):
        """Fix a (v, d) pair to a specific signed-diff symbol."""
        v, d = bit
        if symbol == '0':
            self.clauses.append([-v])  # v=0
            self.clauses.append([-d])  # d=0
        elif symbol == '1':
            self.clauses.append([v])   # v=1
            self.clauses.append([-d])  # d=0
        elif symbol == 'u':
            self.clauses.append([v])   # v=1
            self.clauses.append([d])   # d=1
        elif symbol == 'n':
            self.clauses.append([-v])  # v=0
            self.clauses.append([d])   # d=1
        elif symbol == '=':
            self.clauses.append([-d])  # d=0 (no diff)
        elif symbol == 'x':
            self.clauses.append([d])   # d=1 (has diff)
        # '?' = no constraint

    def fix_word_from_values(self, word, val1, val2):
        """Fix a word's signed diffs from concrete message values."""
        for i, (v, d) in enumerate(word):
            b1 = (val1 >> i) & 1
            b2 = (val2 >> i) & 1
            if b1 == 0 and b2 == 0:
                self.fix_bit((v, d), '0')
            elif b1 == 1 and b2 == 1:
                self.fix_bit((v, d), '1')
            elif b1 == 1 and b2 == 0:
                self.fix_bit((v, d), 'u')
            else:
                self.fix_bit((v, d), 'n')

    def _add_constraint_table(self, variables, patterns):
        """Add constraints from a Li et al. pattern table.

        Each pattern is a string of '0', '1', '-' characters.
        '1' at position i means variable[i] must be FALSE for this clause.
        '0' at position i means variable[i] must be TRUE.
        '-' means don't care (variable not in clause).

        Each pattern is one clause (disjunction). All clauses must be satisfied.
        """
        for pattern in patterns:
            clause = []
            for i, c in enumerate(pattern):
                if c == '1':
                    clause.append(-variables[i])
                elif c == '0':
                    clause.append(variables[i])
                # '-' = not in clause
            if clause:
                self.clauses.append(clause)

    def constrain_xor_full(self, a, b, out):
        """Constrain out = a XOR b in signed-diff model.
        a, b, out are (v, d) tuples for one bit position.

        xor_full_constrain has 11-variable patterns. Variable order from
        Li et al.: [av, ad, bv, bd, cv, cd, outv, outd, ?, ?, ?]
        Actually need to figure out the exact variable mapping.
        """
        # The xor_full_constrain patterns have 11 characters.
        # From studying the code: the pattern maps to
        # [xv, xd, yv, yd, zv, zd, outv, outd, ...extra carry/internal vars]
        # For XOR (no carries), the extra vars might be for the "expansion" model.
        #
        # Actually, looking more carefully at Li et al.'s code:
        # xor_full is for XOR with BOTH value and diff model.
        # Variables: [in1_v, in1_d, in2_v, in2_d, in3_v, in3_d, out_v, out_d, ?, ?, ?]
        # This is for 3-input XOR (like Sigma functions use).
        #
        # For 2-input XOR we can use: out_d = in1_d XOR in2_d, out_v = in1_v XOR in2_v
        # which is exact and doesn't need truth tables.
        pass

    def constrain_xor2_diff(self, a, b, out):
        """Constrain out = a XOR b (2-input) in signed-diff model.
        XOR propagation of differences is exact:
          out_d = a_d XOR b_d
          out_v = a_v XOR b_v (when both diffs are known)
        """
        av, ad = a
        bv, bd = b
        ov, od = out

        # d_out = d_a XOR d_b (exact for XOR)
        # Encode: od <-> ad XOR bd
        self.clauses.append([-ad, -bd, -od])
        self.clauses.append([-ad, bd, od])
        self.clauses.append([ad, -bd, od])
        self.clauses.append([ad, bd, -od])

        # v_out = v_a XOR v_b (exact)
        self.clauses.append([-av, -bv, -ov])
        self.clauses.append([-av, bv, ov])
        self.clauses.append([av, -bv, ov])
        self.clauses.append([av, bv, -ov])

    def constrain_modadd_bit(self, a, b, cin, out, cout):
        """Constrain one bit of modular addition in signed-diff model.

        Uses Li et al.'s modular_addition_constrain (37 patterns, 10 vars).
        Variable order: [av, ad, bv, bd, cinv, cind, outv, outd, coutv, coutd]
        """
        av, ad = a
        bv, bd = b
        cv, cd = cin
        ov, od = out
        cov, cod = cout
        variables = [av, ad, bv, bd, cv, cd, ov, od, cov, cod]
        self._add_constraint_table(variables, modular_addition_constrain)

    def constrain_ch_bit(self, e, f, g, out):
        """Constrain one bit of Ch(e,f,g) = e?f:g in signed-diff model.

        Uses ifz_full_constrain. Variable order needs to be determined
        from Li et al.'s code.
        """
        # ifz_full_constrain has 11-char patterns
        # From the code: [ev, ed, fv, fd, gv, gd, outv, outd, ?, ?, ?]
        # The extra 3 might be internal variables. Need to check.
        # For now, use direct propagation:
        ev, ed = e
        fv, fd = f
        gv, gd = g
        ov, od = out
        # When ed=0 (e equal in both messages): out_d = e_v ? f_d : g_d
        # This is the MUX propagation we already have.
        # For the full model we'd use ifz_full_constrain.
        # Placeholder: just use the truth table
        pass  # TODO: map variable order correctly

    def constrain_modadd_word(self, A, B, Out, N=32):
        """Constrain Out = A + B (mod 2^N) in signed-diff model.

        Creates carry chain variables and applies per-bit constraints.
        """
        # Carry chain: carry[0] is fixed to (v=0, d=0), carry[N] is discarded
        carries = [self.new_bit(f"carry_{i}") for i in range(N + 1)]

        # carry[0] = (0, 0)
        self.fix_bit(carries[0], '0')

        for i in range(N):
            self.constrain_modadd_bit(A[i], B[i], carries[i], Out[i], carries[i+1])

    def count_active_bits(self, word):
        """Return a list of d-variables for counting active bits in a word."""
        return [d for (v, d) in word]

    def write_dimacs(self, filename):
        """Write DIMACS CNF."""
        n_vars = self.next_var - 1
        n_clauses = len(self.clauses)
        with open(filename, 'w') as f:
            f.write(f"p cnf {n_vars} {n_clauses}\n")
            for clause in self.clauses:
                f.write(" ".join(str(l) for l in clause) + " 0\n")
        return n_vars, n_clauses


def test_modadd_constraint():
    """Test: does the modular addition constraint work correctly?

    Encode A + B = C where A has known signed diff and B is free.
    Check that the constraint produces valid results.
    """
    cnf = SignedDiffCNF()

    # 4-bit test
    N = 4
    A = cnf.new_word("A", N)
    B = cnf.new_word("B", N)
    C = cnf.new_word("C", N)

    # Fix A to a known signed diff: A = [u, =, =, =] (diff only in LSB)
    cnf.fix_bit(A[0], 'u')
    for i in range(1, N):
        cnf.fix_bit(A[i], '=')

    # Fix B to all-equal (no diff)
    for i in range(N):
        cnf.fix_bit(B[i], '=')

    # Constrain C = A + B
    cnf.constrain_modadd_word(A, B, C, N)

    # The result should have C[0]='u' (diff propagates through LSB)
    # and C[1..3] should be '=' (no carry since B has no diff)

    import tempfile, subprocess
    with tempfile.NamedTemporaryFile(suffix='.cnf', delete=False, mode='w') as f:
        fname = f.name
    nv, nc = cnf.write_dimacs(fname)
    print(f"Test: 4-bit modadd, {nv} vars, {nc} clauses")

    r = subprocess.run(['kissat', '-q', fname], capture_output=True, text=True, timeout=10)
    if r.returncode == 10:
        # Parse solution
        assignment = {}
        for line in r.stdout.splitlines():
            if line.startswith('v'):
                for lit in line[1:].split():
                    v = int(lit)
                    if v != 0:
                        assignment[abs(v)] = (v > 0)

        print("  SAT — solution:")
        for name, word in [("A", A), ("B", B), ("C", C)]:
            diffs = []
            for i, (v_var, d_var) in enumerate(word):
                v_val = assignment.get(v_var, False)
                d_val = assignment.get(d_var, False)
                if not d_val:
                    diffs.append('1' if v_val else '0')
                else:
                    diffs.append('u' if v_val else 'n')
            print(f"    {name} = {''.join(diffs)} (LSB first)")
    elif r.returncode == 20:
        print("  UNSAT — constraint is too tight")
    else:
        print(f"  rc={r.returncode}")

    os.unlink(fname)


if __name__ == "__main__":
    test_modadd_constraint()
