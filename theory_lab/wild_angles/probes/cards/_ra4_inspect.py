"""Adversarial follow-up for W7-RA4: is the de58 reachable set S an additive
COSET/subgroup of Z/2^N (=> AP-richness is a restatement of carry-collapse, NOT
a vdW density-forcing), or a genuine 'excess AP' object?

Tests per N:
  (1) print S sorted; the bit-pattern.
  (2) subgroup test: is (S - s0) a subgroup of (Z/2^N, +)? i.e. closed under +,
      contains 0. If yes, S is a coset -> AP-structure is automatic (group cosets
      are maximally AP-rich) -> NOT a Ramsey/vdW phenomenon.
  (3) which low/high bits are FIXED across S, which are FREE (spans an F2 subspace?).
"""
import sys
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/cards')
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
# module name has a dash; import via spec loader
import importlib.util, os
spec = importlib.util.spec_from_file_location("ra4mod", os.path.join(os.path.dirname(__file__), "W7-RA4.py"))
ra4 = importlib.util.module_from_spec(spec); spec.loader.exec_module(ra4)


def is_coset(S, mod):
    s0 = min(S)
    H = sorted(((x - s0) % mod) for x in S)
    Hset = set(H)
    if 0 not in Hset:
        return False, None
    # closed under addition?
    for a in Hset:
        for b in Hset:
            if (a + b) % mod not in Hset:
                return False, None
    return True, H


def bit_structure(S, N):
    mod = 1 << N
    fixed0 = mod - 1  # bits that are constant 0 across S? track AND / OR
    AND = (1 << N) - 1
    OR = 0
    for x in S:
        AND &= x
        OR |= x
    free_bits = [j for j in range(N) if ((OR >> j) & 1) and not ((AND >> j) & 1)]
    fixed_bits = [j for j in range(N) if j not in free_bits]
    return AND, OR, free_bits, fixed_bits


def is_f2_subspace(S, mod, N):
    """Is (S xor s0) an F2-linear subspace (closed under XOR)?  If so S is an affine
    XOR-subspace -> its 'APs' under +mod are coincidental coding structure."""
    s0 = min(S)
    H = set((x ^ s0) for x in S)
    if 0 not in H:
        return False
    for a in H:
        for b in H:
            if (a ^ b) not in H:
                return False
    return True


for N in (4, 8, 10, 11):
    mod = 1 << N
    S, M = ra4.de58_set(N)
    if S is None:
        print(f"N={N}: no M0; skip"); continue
    Ssort = sorted(S)
    coset, H = is_coset(S, mod)
    AND, OR, free, fixed = bit_structure(S, N)
    f2 = is_f2_subspace(S, mod, N)
    print(f"\nN={N}  |S|={len(S)}  mod=2^{N}")
    print(f"  S = {[hex(x) for x in Ssort]}")
    print(f"  additive coset of Z/2^N (closed under +)? {coset}")
    if coset:
        print(f"    translate H = S - min(S) = {[hex(x) for x in H]}  (a subgroup)")
    print(f"  F2 / XOR affine subspace (closed under ^)? {f2}")
    print(f"  bitwise AND=0x{AND:x}  OR=0x{OR:x}  free bits={free}  fixed bits={fixed}")
    print(f"  => |S| = 2^{len(free)} from {len(free)} free bits? {len(S)==(1<<len(free))}")
