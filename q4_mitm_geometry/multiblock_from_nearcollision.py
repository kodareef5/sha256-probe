#!/usr/bin/env python3
"""
multiblock_from_nearcollision.py — Test if block 2 can absorb the HW=40
near-collision residual from our round-61-viable prefix.

Block 1: our sr=60 prefix gives hash diff dH (HW=40)
Block 2: standard SHA-256 compression with IV1=H1, IV2=H2=H1+dH
         Free: full 512-bit message (16 × 32-bit words)
         Constraint: compress(IV1, M1') = compress(IV2, M2')

Start with reduced rounds (16, 20, 24) to see if it's feasible.
If SAT at reduced rounds → evidence multi-block approach works.
"""
import sys, os, time, subprocess
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
enc = __import__('13_custom_cnf_encoder')

K = enc.K
MASK = 0xFFFFFFFF

def ROR(x, n): return ((x >> n) | (x << (32 - n))) & MASK
def sigma0(x): return ROR(x, 7) ^ ROR(x, 18) ^ (x >> 3)
def sigma1(x): return ROR(x, 17) ^ ROR(x, 19) ^ (x >> 10)

# Near-collision residual from our prefix analysis (best W[60]=0xbe5b4c69)
# Hash diffs per register:
HASH_DIFF = [
    0x1c07c000,  # a: hw=8
    0xa08400e0,  # b: hw=7
    0xc0000200,  # c: hw=3
    0x00000000,  # d: hw=0
    0x1c224cd2,  # e: hw=12
    0x81a20060,  # f: hw=7
    0x40000600,  # g: hw=3
    0x00000000,  # h: hw=0
]

def encode_block2(n_rounds, hash_diff):
    """Encode block 2 as SAT: find M1', M2' absorbing hash_diff."""
    cnf = enc.CNFBuilder()

    # IV1 = some arbitrary value (doesn't matter, can set to 0 for simplicity)
    # IV2 = IV1 + hash_diff (modular addition)
    # For encoding: IV1[i] and IV2[i] are constants
    IV1 = [0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
           0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19]
    IV2 = [(IV1[i] + hash_diff[i]) & MASK for i in range(8)]

    s1 = tuple(cnf.const_word(v) for v in IV1)
    s2 = tuple(cnf.const_word(v) for v in IV2)

    # Free message words for both blocks
    M1 = [cnf.free_word(f"M1_{i}") for i in range(16)]
    M2 = [cnf.free_word(f"M2_{i}") for i in range(16)]

    # Schedule expansion
    W1 = list(M1)
    W2 = list(M2)
    for i in range(16, n_rounds):
        W1.append(cnf.add_word(
            cnf.add_word(cnf.sigma1_w(W1[-2]), W1[-7]),
            cnf.add_word(cnf.sigma0_w(W1[-15]), W1[-16])
        ))
        W2.append(cnf.add_word(
            cnf.add_word(cnf.sigma1_w(W2[-2]), W2[-7]),
            cnf.add_word(cnf.sigma0_w(W2[-15]), W2[-16])
        ))

    # Run rounds
    st1 = s1
    st2 = s2
    for i in range(n_rounds):
        st1 = cnf.sha256_round_correct(st1, K[i], W1[i])
        st2 = cnf.sha256_round_correct(st2, K[i], W2[i])

    # Feed-forward: hash = IV + state
    h1 = tuple(cnf.add_word(cnf.const_word(IV1[i]), st1[i]) for i in range(8))
    h2 = tuple(cnf.add_word(cnf.const_word(IV2[i]), st2[i]) for i in range(8))

    # Collision: h1 == h2
    for i in range(8):
        cnf.eq_word(h1[i], h2[i])

    return cnf

if __name__ == "__main__":
    n_rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 16
    timeout = int(sys.argv[2]) if len(sys.argv) > 2 else 300

    print(f"Encoding block-2 collision absorber: {n_rounds} rounds")
    print(f"IV diff (HW=40): {[hex(d) for d in HASH_DIFF]}")

    t0 = time.time()
    cnf = encode_block2(n_rounds, HASH_DIFF)
    outf = f"/tmp/block2_{n_rounds}r.cnf"
    nv, nc = cnf.write_dimacs(outf)
    t1 = time.time()
    print(f"CNF: {nv} vars, {nc} clauses ({t1-t0:.1f}s) -> {outf}")

    # Try to solve
    print(f"\nRunning Kissat (timeout={timeout}s)...")
    result = subprocess.run(
        ["nice", "-19", "kissat", "-q", f"--time={timeout}", outf],
        capture_output=True, text=True
    )
    if result.returncode == 10:
        print(f"*** SAT *** — Block 2 absorbs the HW=40 residual at {n_rounds} rounds!")
    elif result.returncode == 20:
        print(f"UNSAT — Cannot absorb at {n_rounds} rounds")
    else:
        print(f"TIMEOUT/UNKNOWN (returncode={result.returncode})")
