#!/usr/bin/env python3
"""
diff_propagation.py — Signed-difference propagation rules for SHA-256

Implements the signed-difference algebra from Li et al. (EUROCRYPT 2024).
Each bit position has a signed difference from {=, x, 0, 1, u, n, ?}.

For bitwise operations (XOR, Ch, Maj, Sigma, sigma), propagation is
exact and independent per bit position.

For modular addition, propagation requires tracking carries, which
introduces inter-bit dependencies. This is the hard part.

This module:
1. Enumerates all valid signed-diff transitions for each operation
2. Builds truth tables for SAT encoding
3. Tests whether specific differential patterns are achievable
"""

# Signed difference values and their concrete bit-pair meanings
# (v1, v2) = the bit values in message 1 and message 2
DIFF_VALS = {
    '?': [(0,0), (0,1), (1,0), (1,1)],  # anything
    '=': [(0,0), (1,1)],                  # equal
    'x': [(0,1), (1,0)],                  # different
    '0': [(0,0)],                          # both zero
    '1': [(1,1)],                          # both one
    'u': [(1,0)],                          # first=1, second=0
    'n': [(0,1)],                          # first=0, second=1
}

def xor_diff(da, db):
    """Compute signed diff of a XOR b given signed diffs of a and b.
    XOR is exact: d(a XOR b) is determined by d(a) and d(b)."""
    results = set()
    for (a1, a2) in DIFF_VALS[da]:
        for (b1, b2) in DIFF_VALS[db]:
            c1 = a1 ^ b1
            c2 = a2 ^ b2
            results.add((c1, c2))
    # Map back to signed diff
    return _pairs_to_diff(results)

def ch_diff(de, df, dg):
    """Compute signed diff of Ch(e,f,g) = e?f:g given signed diffs."""
    results = set()
    for (e1, e2) in DIFF_VALS[de]:
        for (f1, f2) in DIFF_VALS[df]:
            for (g1, g2) in DIFF_VALS[dg]:
                c1 = (e1 & f1) ^ ((1-e1) & g1)
                c2 = (e2 & f2) ^ ((1-e2) & g2)
                results.add((c1, c2))
    return _pairs_to_diff(results)

def maj_diff(da, db, dc):
    """Compute signed diff of Maj(a,b,c) given signed diffs."""
    results = set()
    for (a1, a2) in DIFF_VALS[da]:
        for (b1, b2) in DIFF_VALS[db]:
            for (c1, c2) in DIFF_VALS[dc]:
                m1 = (a1 & b1) ^ (a1 & c1) ^ (b1 & c1)
                m2 = (a2 & b2) ^ (a2 & c2) ^ (b2 & c2)
                results.add((m1, m2))
    return _pairs_to_diff(results)

def addition_bit_diff(da, db, dc_in):
    """Compute signed diff of one bit of modular addition.

    Given signed diffs of addend bits a, b and carry-in c:
    sum = a XOR b XOR c
    carry_out = MAJ(a, b, c)

    Returns (d_sum, d_carry_out) as signed diffs.
    """
    sum_results = set()
    carry_results = set()
    for (a1, a2) in DIFF_VALS[da]:
        for (b1, b2) in DIFF_VALS[db]:
            for (c1, c2) in DIFF_VALS[dc_in]:
                s1 = a1 ^ b1 ^ c1
                s2 = a2 ^ b2 ^ c2
                co1 = (a1 & b1) | (a1 & c1) | (b1 & c1)
                co2 = (a2 & b2) | (a2 & c2) | (b2 & c2)
                sum_results.add((s1, s2))
                carry_results.add((co1, co2))
    return _pairs_to_diff(sum_results), _pairs_to_diff(carry_results)


def _pairs_to_diff(pairs):
    """Convert a set of (v1,v2) pairs to the tightest signed diff symbol."""
    pairs = frozenset(pairs)
    for sym, vals in DIFF_VALS.items():
        if sym == '?':
            continue
        if pairs == frozenset(vals):
            return sym
    # Check if it's a subset of a known symbol
    for sym in ['=', 'x', '0', '1', 'u', 'n']:
        if pairs.issubset(frozenset(DIFF_VALS[sym])):
            return sym
    return '?'


def propagate_addition_word(dA, dB, N=32):
    """Propagate signed diffs through N-bit modular addition A + B.

    dA, dB: lists of N signed-diff symbols (LSB first).
    Returns: list of N signed-diff symbols for the sum (LSB first).

    This is the simplified version — it tracks the carry signed diff
    through the addition chain. When the carry becomes '?', all
    subsequent sum bits become '?' too.
    """
    result = []
    carry = '0'  # carry-in for LSB is always 0

    for i in range(N):
        d_sum, carry = addition_bit_diff(dA[i], dB[i], carry)
        result.append(d_sum)

    return result


def test_propagation():
    """Test propagation rules against concrete examples."""
    print("Testing signed-difference propagation rules")
    print("=" * 60)

    # Test XOR
    print("\nXOR propagation:")
    for da in ['=', 'x', '0', '1', 'u', 'n']:
        for db in ['=', 'x', '0', '1', 'u', 'n']:
            dc = xor_diff(da, db)
            if dc != '?':
                print(f"  {da} XOR {db} = {dc}")

    # Test Ch with known e
    print("\nCh propagation (selected cases):")
    for de in ['0', '1', '=', 'x']:
        for df in ['=', 'x']:
            for dg in ['=', 'x']:
                dc = ch_diff(de, df, dg)
                if dc != '?':
                    print(f"  Ch({de},{df},{dg}) = {dc}")

    # Test addition bit
    print("\nAddition bit propagation (carry-in = '0'):")
    for da in ['=', 'x', '0', '1']:
        for db in ['=', 'x', '0', '1']:
            ds, dc = addition_bit_diff(da, db, '0')
            print(f"  {da} + {db} (cin=0): sum={ds}, cout={dc}")

    # Test when carry uncertainty kills propagation
    print("\nAddition carry uncertainty:")
    da_word = ['x'] + ['='] * 31  # diff only in LSB
    db_word = ['='] * 32           # no diff
    result = propagate_addition_word(da_word, db_word)
    active = sum(1 for d in result if d not in ['=', '0', '1'])
    print(f"  A=[x,=,=,...] + B=[=,=,...]: {active} uncertain bits in sum")
    print(f"  Sum pattern: {''.join(result[:8])}...")

    da_word2 = ['='] * 31 + ['x']  # diff only in MSB
    result2 = propagate_addition_word(da_word2, db_word)
    active2 = sum(1 for d in result2 if d not in ['=', '0', '1'])
    print(f"  A=[=,...,=,x] + B=[=,=,...]: {active2} uncertain bits in sum")
    print(f"  Sum pattern: ...{''.join(result2[-8:])}")


def analyze_carry_propagation_depth():
    """How far does carry uncertainty propagate through addition?

    This is the key question for understanding the sr=60 obstruction.
    If carry uncertainty propagates far, modular addition makes the
    signed-diff model lose precision quickly, degrading to '?' everywhere.
    If it stays contained, the signed-diff model retains useful information.
    """
    print("\n\nCarry Propagation Depth Analysis")
    print("=" * 60)

    # Test: single active bit at position k, all other bits '='
    for k in [0, 1, 7, 15, 16, 24, 31]:
        da = ['='] * 32
        da[k] = 'x'
        db = ['='] * 32

        result = propagate_addition_word(da, db)
        first_uncertain = -1
        last_determined = -1
        for i in range(32):
            if result[i] in ['?']:
                if first_uncertain == -1:
                    first_uncertain = i
            elif result[i] not in ['=', '0', '1']:
                last_determined = i

        uncertain = sum(1 for d in result if d == '?')
        print(f"  Active bit at position {k:2d}: {uncertain} uncertain, "
              f"first ?={first_uncertain}")

    # Test: random pattern of active bits
    import random
    random.seed(42)
    for trial in range(5):
        n_active = random.randint(8, 20)
        positions = random.sample(range(32), n_active)
        da = ['='] * 32
        for p in positions:
            da[p] = random.choice(['x', 'u', 'n'])
        db = ['='] * 32
        for p in random.sample(range(32), random.randint(5, 15)):
            db[p] = random.choice(['x', 'u', 'n'])

        result = propagate_addition_word(da, db)
        uncertain = sum(1 for d in result if d == '?')
        active_in = sum(1 for d in da if d not in ['=', '0', '1'])
        active_in += sum(1 for d in db if d not in ['=', '0', '1'])
        print(f"  Trial {trial}: {active_in} active input bits → {uncertain} uncertain sum bits")


if __name__ == "__main__":
    test_propagation()
    analyze_carry_propagation_depth()
