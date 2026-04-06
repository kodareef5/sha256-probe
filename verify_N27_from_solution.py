#!/usr/bin/env python3
"""
Parse a Kissat/CaDiCaL solution file and extract+verify the N=27 collision certificate.
Usage: python3 verify_N27_from_solution.py [solution_file]
Default: /tmp/n27_solution.txt
"""
import sys, os, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
spec = __import__('50_precision_homotopy')
MiniSHA256 = spec.MiniSHA256
MiniCNFBuilder = spec.MiniCNFBuilder
K32 = spec.K32


def parse_solution(text):
    """Parse 'v' lines from solver output to get variable assignments."""
    assignments = {}
    for line in text.split('\n'):
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


def reconstruct_var_mapping(N, m0, fill):
    """Reconstruct the variable mapping by re-encoding (without writing DIMACS)."""
    sha = MiniSHA256(N)
    MASK = sha.MASK
    MSB = sha.MSB

    M1 = [m0] + [fill] * 15
    M2 = list(M1)
    M2[0] = m0 ^ MSB
    M2[9] = fill ^ MSB
    s1, W1 = sha.compress(M1)
    s2, W2 = sha.compress(M2)

    assert s1[0] == s2[0], f"da[56]!=0: s1[0]={s1[0]:#x} != s2[0]={s2[0]:#x}"

    ops = {
        'r_Sig0': sha.r_Sig0, 'r_Sig1': sha.r_Sig1,
        'r_sig0': sha.r_sig0, 's_sig0': sha.s_sig0,
        'r_sig1': sha.r_sig1, 's_sig1': sha.s_sig1,
    }

    cnf = MiniCNFBuilder(N)

    st1 = tuple(cnf.const_word(v) for v in s1)
    st2 = tuple(cnf.const_word(v) for v in s2)

    # Track free word variable arrays
    free_words = {}
    for i in range(4):
        name = f"W1_{57+i}"
        w = cnf.free_word(name)
        free_words[name] = w

    for i in range(4):
        name = f"W2_{57+i}"
        w = cnf.free_word(name)
        free_words[name] = w

    return sha, s1, s2, W1, W2, M1, M2, free_words


def extract_word_value(assignments, bit_vars, N):
    """Extract N-bit word value from variable assignments. LSB-first bit array."""
    value = 0
    for i in range(N):
        v = bit_vars[i]
        if v == 1:  # TRUE constant
            value |= (1 << i)
        elif v == -1:  # FALSE constant
            pass
        else:
            av = abs(v)
            if av in assignments:
                bit_true = assignments[av]
                if v < 0:
                    bit_true = not bit_true
                if bit_true:
                    value |= (1 << i)
    return value


def run_tail_rounds(sha, state, W_ext):
    """Run rounds 57..63 natively."""
    MASK = sha.MASK
    KT = [k & MASK for k in K32]
    a, b, c, d, e, f, g, h = state
    for i in range(57, 64):
        T1 = (h + sha.Sigma1(e) + sha.ch(e, f, g) + KT[i] + W_ext[i]) & MASK
        T2 = (sha.Sigma0(a) + sha.maj(a, b, c)) & MASK
        h = g; g = f; f = e; e = (d + T1) & MASK
        d = c; c = b; b = a; a = (T1 + T2) & MASK
    return (a, b, c, d, e, f, g, h)


def main():
    solution_file = sys.argv[1] if len(sys.argv) > 1 else "/tmp/n27_solution.txt"

    N = 27
    m0 = 0x2bfb506
    fill = 0x3ffffff

    print(f"=== N={N} Collision Certificate Extraction ===")
    print(f"M[0] = {m0:#x}, fill = {fill:#x}")
    print(f"Solution file: {solution_file}")
    print()

    # Read solution
    with open(solution_file, 'r') as f:
        text = f.read()
    assignments = parse_solution(text)
    print(f"Parsed {len(assignments)} variable assignments")

    # Reconstruct variable mapping
    sha, s1, s2, W1, W2, M1, M2, free_words = reconstruct_var_mapping(N, m0, fill)
    MASK = sha.MASK

    print(f"\nPrecomputed state after 57 rounds:")
    print(f"  s1 = [{', '.join(f'{v:#x}' for v in s1)}]")
    print(f"  s2 = [{', '.join(f'{v:#x}' for v in s2)}]")
    diffs = sum(1 for i in range(8) if s1[i] != s2[i])
    print(f"  State diffs: {diffs}/8")

    # Extract free word values
    print(f"\nFree schedule words:")
    w1_vals = []
    w2_vals = []
    for i in range(4):
        name = f"W1_{57+i}"
        val = extract_word_value(assignments, free_words[name], N)
        w1_vals.append(val)
        print(f"  {name} = {val:#09x} ({val})")

    for i in range(4):
        name = f"W2_{57+i}"
        val = extract_word_value(assignments, free_words[name], N)
        w2_vals.append(val)
        print(f"  {name} = {val:#09x} ({val})")

    # Build extended W arrays
    W1_ext = list(W1) + [0] * 7
    W2_ext = list(W2) + [0] * 7
    for i in range(4):
        W1_ext[57+i] = w1_vals[i]
        W2_ext[57+i] = w2_vals[i]

    # Derived schedule words
    W1_ext[61] = (sha.sigma1(W1_ext[59]) + W1_ext[54] + sha.sigma0(W1_ext[46]) + W1_ext[45]) & MASK
    W2_ext[61] = (sha.sigma1(W2_ext[59]) + W2_ext[54] + sha.sigma0(W2_ext[46]) + W2_ext[45]) & MASK
    W1_ext[62] = (sha.sigma1(W1_ext[60]) + W1_ext[55] + sha.sigma0(W1_ext[47]) + W1_ext[46]) & MASK
    W2_ext[62] = (sha.sigma1(W2_ext[60]) + W2_ext[55] + sha.sigma0(W2_ext[47]) + W2_ext[46]) & MASK
    W1_ext[63] = (sha.sigma1(W1_ext[61]) + W1_ext[56] + sha.sigma0(W1_ext[48]) + W1_ext[47]) & MASK
    W2_ext[63] = (sha.sigma1(W2_ext[61]) + W2_ext[56] + sha.sigma0(W2_ext[48]) + W2_ext[47]) & MASK

    print(f"\nFull schedule (rounds 57-63):")
    for i in range(57, 64):
        src = "free" if i <= 60 else "derived"
        print(f"  W1[{i}] = {W1_ext[i]:#09x}    W2[{i}] = {W2_ext[i]:#09x}  ({src})")

    # Run tail rounds natively
    final1 = run_tail_rounds(sha, s1, W1_ext)
    final2 = run_tail_rounds(sha, s2, W2_ext)

    print(f"\nFinal state after 64 rounds:")
    labels = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
    all_match = True
    for i in range(8):
        match_str = "MATCH" if final1[i] == final2[i] else "DIFF"
        if final1[i] != final2[i]:
            all_match = False
        print(f"  {labels[i]}: s1={final1[i]:#09x}  s2={final2[i]:#09x}  [{match_str}]")

    print()
    if all_match:
        print("*** COLLISION VERIFIED ***")
        print("All 8 state registers match after 64 rounds.")
    else:
        print("*** VERIFICATION FAILED ***")
        n_match = sum(1 for i in range(8) if final1[i] == final2[i])
        print(f"Only {n_match}/8 registers match.")
        return

    # Write results file
    results_path = "/home/yale/sha256_probe/results/collision_N27.txt"
    with open(results_path, 'w') as f:
        f.write(f"N={N} sr=60 Collision Certificate\n")
        f.write(f"{'='*60}\n")
        f.write(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Candidate: M[0]={m0:#x}, fill={fill:#x}\n")
        f.write(f"\n")
        f.write(f"Messages (16 x {N}-bit words):\n")
        f.write(f"  M1[0] = {M1[0]:#09x}   M2[0] = {M2[0]:#09x}   (XOR = {M1[0]^M2[0]:#09x} = MSB)\n")
        for i in range(1, 16):
            diff = "  (XOR = MSB)" if M1[i] != M2[i] else ""
            f.write(f"  M1[{i:2d}] = {M1[i]:#09x}   M2[{i:2d}] = {M2[i]:#09x}{diff}\n")
        f.write(f"\n")
        f.write(f"Precomputed state after 57 rounds (a, b, c, d, e, f, g, h):\n")
        f.write(f"  s1 = [{', '.join(f'{v:#09x}' for v in s1)}]\n")
        f.write(f"  s2 = [{', '.join(f'{v:#09x}' for v in s2)}]\n")
        f.write(f"  State diffs: {diffs}/8 registers differ\n")
        f.write(f"\n")
        f.write(f"Free schedule words (SAT solution):\n")
        for i in range(4):
            f.write(f"  W1[{57+i}] = {w1_vals[i]:#09x}\n")
        for i in range(4):
            f.write(f"  W2[{57+i}] = {w2_vals[i]:#09x}\n")
        f.write(f"\n")
        f.write(f"Full schedule (rounds 57-63):\n")
        for i in range(57, 64):
            src = "FREE" if i <= 60 else "DERIVED"
            f.write(f"  W1[{i}] = {W1_ext[i]:#09x}    W2[{i}] = {W2_ext[i]:#09x}  ({src})\n")
        f.write(f"\n")
        f.write(f"Final state after 64 rounds (a, b, c, d, e, f, g, h):\n")
        for i in range(8):
            f.write(f"  {labels[i]}: {final1[i]:#09x} == {final2[i]:#09x}  [MATCH]\n")
        f.write(f"\n")
        f.write(f"COLLISION VERIFIED: YES\n")
        f.write(f"  All 8 output registers match after all 64 rounds.\n")
        f.write(f"  This constitutes an sr=60 collision for {N}-bit mini-SHA-256.\n")
        f.write(f"\n")
        f.write(f"Evidence level: VERIFIED\n")
        f.write(f"  - SAT solution extracted from Kissat/CaDiCaL\n")
        f.write(f"  - Independently verified by native Python computation\n")

    print(f"\nResults written to: {results_path}")


if __name__ == "__main__":
    main()
