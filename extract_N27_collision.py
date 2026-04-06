#!/usr/bin/env python3
"""
Extract and verify the N=27 sr=60 collision certificate.

Candidate: N=27, M[0]=0x2bfb506, fill=0x3ffffff
Steps:
  1. Encode the CNF (same as fast_parallel_solve.py)
  2. Solve with Kissat (capturing variable assignments)
  3. Parse 'v' lines to extract free word values
  4. Verify collision by running tail rounds natively
"""

import sys, os, time, subprocess, tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from q1_barrier_location.homotopy.fast_parallel_solve import encode as _encode_unused
# Import primitives directly
spec = __import__('50_precision_homotopy')
MiniSHA256 = spec.MiniSHA256
MiniCNFBuilder = spec.MiniCNFBuilder
K32 = spec.K32


def encode_and_track_vars(N, m0, fill):
    """
    Encode the sr=60 CNF, returning:
      - cnf_path: path to DIMACS file
      - free_var_ranges: dict mapping name -> (start_var, N) for each free word
      - sha, s1, s2, W1, W2: for verification
    """
    sha = MiniSHA256(N)
    MASK = sha.MASK
    MSB = sha.MSB

    M1 = [m0] + [fill] * 15
    M2 = list(M1)
    M2[0] = m0 ^ MSB
    M2[9] = fill ^ MSB
    s1, W1 = sha.compress(M1)
    s2, W2 = sha.compress(M2)

    if s1[0] != s2[0]:
        print(f"ERROR: s1[0]={s1[0]:#x} != s2[0]={s2[0]:#x}, candidate invalid")
        return None

    ops = {
        'r_Sig0': sha.r_Sig0, 'r_Sig1': sha.r_Sig1,
        'r_sig0': sha.r_sig0, 's_sig0': sha.s_sig0,
        'r_sig1': sha.r_sig1, 's_sig1': sha.s_sig1,
    }
    KT = [k & MASK for k in K32]

    cnf = MiniCNFBuilder(N)

    # Track where free variables start
    # cnf.next_var starts at 2 (var 1 = TRUE)
    free_var_info = {}

    st1 = tuple(cnf.const_word(v) for v in s1)
    st2 = tuple(cnf.const_word(v) for v in s2)

    # Free words: W1[57..60] and W2[57..60]
    w1f = []
    for i in range(4):
        name = f"W1_{57+i}"
        start_var = cnf.next_var
        w = cnf.free_word(name)
        free_var_info[name] = (start_var, w)
        w1f.append(w)

    w2f = []
    for i in range(4):
        name = f"W2_{57+i}"
        start_var = cnf.next_var
        w = cnf.free_word(name)
        free_var_info[name] = (start_var, w)
        w2f.append(w)

    def s1w(x): return cnf.sigma1_w(x, ops['r_sig1'], ops['s_sig1'])
    def s0w(x): return cnf.sigma0_w(x, ops['r_sig0'], ops['s_sig0'])

    # Derived schedule words
    w1_61 = cnf.add_word(cnf.add_word(s1w(w1f[2]), cnf.const_word(W1[54])),
                         cnf.add_word(cnf.const_word(sha.sigma0(W1[46])), cnf.const_word(W1[45])))
    w2_61 = cnf.add_word(cnf.add_word(s1w(w2f[2]), cnf.const_word(W2[54])),
                         cnf.add_word(cnf.const_word(sha.sigma0(W2[46])), cnf.const_word(W2[45])))
    w1_62 = cnf.add_word(cnf.add_word(s1w(w1f[3]), cnf.const_word(W1[55])),
                         cnf.add_word(cnf.const_word(sha.sigma0(W1[47])), cnf.const_word(W1[46])))
    w2_62 = cnf.add_word(cnf.add_word(s1w(w2f[3]), cnf.const_word(W2[55])),
                         cnf.add_word(cnf.const_word(sha.sigma0(W2[47])), cnf.const_word(W2[46])))
    w1_63 = cnf.add_word(cnf.add_word(s1w(w1_61), cnf.const_word(W1[56])),
                         cnf.add_word(cnf.const_word(sha.sigma0(W1[48])), cnf.const_word(W1[47])))
    w2_63 = cnf.add_word(cnf.add_word(s1w(w2_61), cnf.const_word(W2[56])),
                         cnf.add_word(cnf.const_word(sha.sigma0(W2[48])), cnf.const_word(W2[47])))

    W1s = list(w1f) + [w1_61, w1_62, w1_63]
    W2s = list(w2f) + [w2_61, w2_62, w2_63]

    for i in range(7):
        st1 = cnf.sha256_round(st1, KT[57+i], W1s[i], ops)
    for i in range(7):
        st2 = cnf.sha256_round(st2, KT[57+i], W2s[i], ops)
    for i in range(8):
        cnf.eq_word(st1[i], st2[i])

    # Check for trivially UNSAT
    has_empty = any(len(c) == 0 for c in cnf.clauses)
    if has_empty:
        print("ERROR: Encoding is trivially UNSAT!")
        return None

    td = tempfile.mkdtemp(prefix=f"extract_N{N}_")
    f = os.path.join(td, f"m0_{m0:x}_fill_{fill:x}.cnf")
    nv, nc = cnf.write_dimacs(f)
    print(f"Encoded: {nv} vars, {nc} clauses")
    print(f"DIMACS file: {f}")

    return f, free_var_info, sha, s1, s2, W1, W2, M1, M2


def parse_solution(stdout_text):
    """Parse Kissat 'v' lines to get variable assignments."""
    assignments = {}
    for line in stdout_text.split('\n'):
        line = line.strip()
        if line.startswith('v '):
            parts = line[2:].split()
            for p in parts:
                lit = int(p)
                if lit == 0:
                    break
                var = abs(lit)
                assignments[var] = (lit > 0)
    return assignments


def extract_word_value(assignments, var_list, N):
    """Extract an N-bit word value from variable assignments. LSB-first bit array."""
    value = 0
    for i in range(N):
        var = var_list[i]
        if var == 1:  # TRUE constant
            value |= (1 << i)
        elif var == -1:  # FALSE constant
            pass  # bit is 0
        elif abs(var) in assignments:
            if (var > 0 and assignments[abs(var)]) or (var < 0 and not assignments[abs(var)]):
                value |= (1 << i)
        else:
            # Variable not in solution -- check if it's a constant
            if var > 0:
                if var in assignments and assignments[var]:
                    value |= (1 << i)
            else:
                if abs(var) in assignments and not assignments[abs(var)]:
                    value |= (1 << i)
    return value


def verify_collision(sha, s1, s2, W1, W2, w1_free_vals, w2_free_vals, M1, M2):
    """
    Verify the collision by running the 7 tail rounds natively.
    w1_free_vals = [W1[57], W1[58], W1[59], W1[60]]
    w2_free_vals = [W2[57], W2[58], W2[59], W2[60]]
    """
    N = sha.N
    MASK = sha.MASK

    # Extend W arrays with free words
    W1_ext = list(W1) + [0] * 7
    W2_ext = list(W2) + [0] * 7
    for i in range(4):
        W1_ext[57+i] = w1_free_vals[i]
        W2_ext[57+i] = w2_free_vals[i]

    # Compute derived schedule words
    # W[61] = sigma1(W[59]) + W[54] + sigma0(W[46]) + W[45]
    W1_ext[61] = (sha.sigma1(W1_ext[59]) + W1_ext[54] + sha.sigma0(W1_ext[46]) + W1_ext[45]) & MASK
    W2_ext[61] = (sha.sigma1(W2_ext[59]) + W2_ext[54] + sha.sigma0(W2_ext[46]) + W2_ext[45]) & MASK
    # W[62] = sigma1(W[60]) + W[55] + sigma0(W[47]) + W[46]
    W1_ext[62] = (sha.sigma1(W1_ext[60]) + W1_ext[55] + sha.sigma0(W1_ext[47]) + W1_ext[46]) & MASK
    W2_ext[62] = (sha.sigma1(W2_ext[60]) + W2_ext[55] + sha.sigma0(W2_ext[47]) + W2_ext[46]) & MASK
    # W[63] = sigma1(W[61]) + W[56] + sigma0(W[48]) + W[47]
    W1_ext[63] = (sha.sigma1(W1_ext[61]) + W1_ext[56] + sha.sigma0(W1_ext[48]) + W1_ext[47]) & MASK
    W2_ext[63] = (sha.sigma1(W2_ext[61]) + W2_ext[56] + sha.sigma0(W2_ext[48]) + W2_ext[47]) & MASK

    # Run 7 tail rounds (57..63)
    KT = [k & MASK for k in K32]

    a1, b1, c1, d1, e1, f1, g1, h1 = s1
    for i in range(57, 64):
        T1 = (h1 + sha.Sigma1(e1) + sha.ch(e1, f1, g1) + KT[i] + W1_ext[i]) & MASK
        T2 = (sha.Sigma0(a1) + sha.maj(a1, b1, c1)) & MASK
        h1 = g1; g1 = f1; f1 = e1; e1 = (d1 + T1) & MASK
        d1 = c1; c1 = b1; b1 = a1; a1 = (T1 + T2) & MASK

    a2, b2, c2, d2, e2, f2, g2, h2 = s2
    for i in range(57, 64):
        T1 = (h2 + sha.Sigma1(e2) + sha.ch(e2, f2, g2) + KT[i] + W2_ext[i]) & MASK
        T2 = (sha.Sigma0(a2) + sha.maj(a2, b2, c2)) & MASK
        h2 = g2; g2 = f2; f2 = e2; e2 = (d2 + T1) & MASK
        d2 = c2; c2 = b2; b2 = a2; a2 = (T1 + T2) & MASK

    final1 = (a1, b1, c1, d1, e1, f1, g1, h1)
    final2 = (a2, b2, c2, d2, e2, f2, g2, h2)

    return final1, final2, W1_ext, W2_ext


def main():
    N = 27
    m0 = 0x2bfb506
    fill = 0x3ffffff

    print(f"=== N={N} Collision Certificate Extraction ===")
    print(f"M[0] = {m0:#x}")
    print(f"fill  = {fill:#x}")
    print()

    # Step 1: Encode
    print("Step 1: Encoding CNF...")
    t0 = time.time()
    result = encode_and_track_vars(N, m0, fill)
    if result is None:
        print("FAILED: encoding error")
        sys.exit(1)
    cnf_path, free_var_info, sha, s1, s2, W1, W2, M1, M2 = result
    encode_time = time.time() - t0
    print(f"Encoding took {encode_time:.2f}s")
    print()

    # Show free variable mappings
    print("Free variable mappings:")
    for name, (start_var, bits) in sorted(free_var_info.items()):
        print(f"  {name}: vars {bits[0]}..{bits[-1]} (start={start_var})")
    print()

    # Show precomputed state at round 57
    print("Precomputed state after 57 rounds:")
    print(f"  s1 = [{', '.join(f'{v:#x}' for v in s1)}]")
    print(f"  s2 = [{', '.join(f'{v:#x}' for v in s2)}]")
    diffs = sum(1 for i in range(8) if s1[i] != s2[i])
    print(f"  State diffs: {diffs}/8")
    print()

    # Step 2: Solve with Kissat
    print("Step 2: Solving with Kissat (no -q, capturing assignment)...")
    t0 = time.time()
    proc = subprocess.run(
        ['kissat', cnf_path],
        capture_output=True, text=True, timeout=86400  # 24h timeout
    )
    solve_time = time.time() - t0
    print(f"Kissat returned rc={proc.returncode} in {solve_time:.2f}s")

    if proc.returncode != 10:
        print(f"FAILED: Expected SAT (rc=10), got rc={proc.returncode}")
        if proc.stderr:
            print(f"stderr: {proc.stderr[:500]}")
        sys.exit(1)
    print("Result: SAT!")
    print()

    # Step 3: Parse solution
    print("Step 3: Parsing variable assignments...")
    assignments = parse_solution(proc.stdout)
    print(f"Parsed {len(assignments)} variable assignments")
    print()

    # Extract free word values
    print("Step 4: Extracting free word values...")
    w1_free_vals = []
    w2_free_vals = []

    for i in range(4):
        name = f"W1_{57+i}"
        _, bits = free_var_info[name]
        val = extract_word_value(assignments, bits, N)
        w1_free_vals.append(val)
        print(f"  {name} = {val:#x} ({val})")

    for i in range(4):
        name = f"W2_{57+i}"
        _, bits = free_var_info[name]
        val = extract_word_value(assignments, bits, N)
        w2_free_vals.append(val)
        print(f"  {name} = {val:#x} ({val})")
    print()

    # Step 5: Verify collision
    print("Step 5: Verifying collision by running tail rounds natively...")
    final1, final2, W1_ext, W2_ext = verify_collision(
        sha, s1, s2, W1, W2, w1_free_vals, w2_free_vals, M1, M2
    )

    print(f"\nFinal state after round 63:")
    labels = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
    all_match = True
    for i in range(8):
        match = "MATCH" if final1[i] == final2[i] else "DIFF"
        if final1[i] != final2[i]:
            all_match = False
        print(f"  {labels[i]}: s1={final1[i]:#x}  s2={final2[i]:#x}  [{match}]")

    print()
    if all_match:
        print("*** COLLISION VERIFIED ***")
        print("All 8 state registers match after 64 rounds (sr=60 collision)!")
    else:
        print("*** VERIFICATION FAILED ***")
        print("State registers do not all match!")

    # Write results
    results_path = "/home/yale/sha256_probe/results/collision_N27.txt"
    with open(results_path, 'w') as f:
        f.write(f"N={N} sr=60 Collision Certificate\n")
        f.write(f"{'='*60}\n")
        f.write(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Candidate: M[0]={m0:#x}, fill={fill:#x}\n")
        f.write(f"\n")
        f.write(f"Messages:\n")
        f.write(f"  M1 = [{', '.join(f'{v:#x}' for v in M1)}]\n")
        f.write(f"  M2 = [{', '.join(f'{v:#x}' for v in M2)}]\n")
        f.write(f"  MSB kernel: M1[0] XOR M2[0] = {M1[0]^M2[0]:#x}, M1[9] XOR M2[9] = {M1[9]^M2[9]:#x}\n")
        f.write(f"\n")
        f.write(f"Precomputed state after 57 rounds:\n")
        f.write(f"  s1 = [{', '.join(f'{v:#x}' for v in s1)}]\n")
        f.write(f"  s2 = [{', '.join(f'{v:#x}' for v in s2)}]\n")
        f.write(f"  State diffs: {diffs}/8\n")
        f.write(f"\n")
        f.write(f"Free schedule words (SAT solution):\n")
        for i in range(4):
            f.write(f"  W1[{57+i}] = {w1_free_vals[i]:#x}\n")
        for i in range(4):
            f.write(f"  W2[{57+i}] = {w2_free_vals[i]:#x}\n")
        f.write(f"\n")
        f.write(f"Derived schedule words:\n")
        for i in range(57, 64):
            f.write(f"  W1[{i}] = {W1_ext[i]:#x}    W2[{i}] = {W2_ext[i]:#x}\n")
        f.write(f"\n")
        f.write(f"Final state after 64 rounds:\n")
        for i in range(8):
            match = "MATCH" if final1[i] == final2[i] else "DIFF"
            f.write(f"  {labels[i]}: s1={final1[i]:#x}  s2={final2[i]:#x}  [{match}]\n")
        f.write(f"\n")
        f.write(f"Collision verified: {'YES' if all_match else 'NO'}\n")
        f.write(f"\n")
        f.write(f"Solver: Kissat\n")
        f.write(f"Encode time: {encode_time:.2f}s\n")
        f.write(f"Solve time: {solve_time:.2f}s\n")
        f.write(f"CNF size: see DIMACS file\n")

    print(f"\nResults written to: {results_path}")

    # Cleanup
    try:
        os.unlink(cnf_path)
        os.rmdir(os.path.dirname(cnf_path))
    except:
        pass


if __name__ == "__main__":
    main()
