#!/usr/bin/env python3
"""
GPU-Ranked Cube-and-Conquer for sr=60 at N=32.

Standard cube-and-conquer splits the SAT problem into subcases by fixing
some variables. The key insight: we can use the GPU to PRE-EVALUATE which
cubes are most promising BEFORE sending them to the SAT solver.

Pipeline:
1. Generate CNF for a candidate (N=32 or any N)
2. Choose cube variables (bits of the free words W1[57], W2[57])
3. GPU evaluates ALL 2^K cube assignments by computing partial collision HW
4. Rank cubes by proximity to collision (lowest HW = most promising)
5. SAT solver only tackles top-M cubes, in parallel on all cores

This exploits the GPU for what it's good at (parallel evaluation) and
SAT for what it's good at (intelligent search in constrained spaces).

Usage:
    python3 gpu_cube_and_conquer.py N [n_cube_bits] [top_cubes] [timeout]
    # N: word width (default 32)
    # n_cube_bits: bits to cube on (default 12 = 4096 cubes)
    # top_cubes: how many top cubes to solve (default 64)
    # timeout: per-cube SAT timeout in seconds (default 3600)
"""

import sys, os, time, subprocess, tempfile, csv
import torch

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

from lib.sha256 import (K, IV, MASK, hw, add, Sigma0, Sigma1, Ch, Maj,
                         precompute_state, sigma0, sigma1)


def to_i32(v):
    v = v & 0xFFFFFFFF
    return v if v < 0x80000000 else v - 0x100000000


def popcount32_gpu(x):
    x = x - ((x >> 1) & 0x55555555)
    x = (x & 0x33333333) + ((x >> 2) & 0x33333333)
    x = (x + (x >> 4)) & 0x0F0F0F0F
    x = x + (x >> 8)
    x = x + (x >> 16)
    return x & 0x3F


def gpu_ror32(x, k):
    return ((x >> k) | (x << (32 - k))) & 0xFFFFFFFF


def gpu_Sigma1(e):
    return gpu_ror32(e, 6) ^ gpu_ror32(e, 11) ^ gpu_ror32(e, 25)

def gpu_Sigma0(a):
    return gpu_ror32(a, 2) ^ gpu_ror32(a, 13) ^ gpu_ror32(a, 22)

def gpu_Ch(e, f, g):
    return ((e & f) ^ ((~e) & g)) & 0xFFFFFFFF

def gpu_Maj(a, b, c):
    return ((a & b) ^ (a & c) ^ (b & c)) & 0xFFFFFFFF


def gpu_round(state, Ki, Wi):
    a, b, c, d, e, f, g, h = state
    ch = gpu_Ch(e, f, g)
    T1 = (h + gpu_Sigma1(e) + ch + Ki + Wi) & 0xFFFFFFFF
    maj = gpu_Maj(a, b, c)
    T2 = (gpu_Sigma0(a) + maj) & 0xFFFFFFFF
    return [(T1 + T2) & 0xFFFFFFFF, a, b, c, (d + T1) & 0xFFFFFFFF, e, f, g]


def gpu_rank_cubes(s1, s2, W1_pre, W2_pre, n_cube_bits, device):
    """
    Evaluate all 2^n_cube_bits cubes by fixing bits of W1[57].

    For each cube (= partial assignment of W1[57] bits), we compute
    round 57 with that partial W1[57] and average over random W2[57].
    The cube's score is the minimum de57_hw found.

    Returns: list of (cube_idx, score) sorted by score ascending.
    """
    K57 = torch.tensor(to_i32(K[57]), dtype=torch.int32, device=device)

    # Compute dW57 for da57=0
    d_h = (s1[7] - s2[7]) & MASK
    d_Sig1 = (Sigma1(s1[4]) - Sigma1(s2[4])) & MASK
    d_Ch = (Ch(s1[4], s1[5], s1[6]) - Ch(s2[4], s2[5], s2[6])) & MASK
    C_T1 = add(d_h, d_Sig1, d_Ch)
    d_Sig0 = (Sigma0(s1[0]) - Sigma0(s2[0])) & MASK
    d_Maj = (Maj(s1[0], s1[1], s1[2]) - Maj(s2[0], s2[1], s2[2])) & MASK
    C_T2 = add(d_Sig0, d_Maj)
    dw57 = (-add(C_T1, C_T2)) & MASK
    dw57_t = torch.tensor(to_i32(dw57), dtype=torch.int32, device=device)

    s1_t = [torch.tensor(to_i32(v), dtype=torch.int32, device=device) for v in s1]
    s2_t = [torch.tensor(to_i32(v), dtype=torch.int32, device=device) for v in s2]

    n_cubes = 1 << n_cube_bits
    n_random = 256  # random samples per cube for scoring

    print(f"  GPU ranking {n_cubes} cubes ({n_cube_bits} bits of W1[57])...")
    t0 = time.time()

    # For each cube, fix the low n_cube_bits of W1[57]
    # and sample the remaining bits randomly
    remaining_bits = 32 - n_cube_bits

    cube_scores = torch.full((n_cubes,), 256, dtype=torch.int32, device=device)

    # Process in batches: each batch evaluates all cubes with one random upper part
    for r in range(n_random):
        # Random upper bits (same for all cubes in this batch)
        upper = torch.randint(0, 1 << remaining_bits, (1,),
                              dtype=torch.int32, device=device)
        upper_shifted = upper << n_cube_bits

        # All cube indices as lower bits
        lower = torch.arange(n_cubes, dtype=torch.int32, device=device)

        # Full W1[57] = upper | lower
        w1_57 = (upper_shifted | lower)
        w2_57 = (w1_57 - dw57_t) & 0xFFFFFFFF

        # Compute round 57
        st1 = gpu_round(s1_t, K57, w1_57)
        st2 = gpu_round(s2_t, K57, w2_57)

        # Total state diff HW after round 57
        total_hw = torch.zeros(n_cubes, dtype=torch.int32, device=device)
        for i in range(8):
            total_hw = total_hw + popcount32_gpu(st1[i] ^ st2[i])

        # Update best score per cube
        cube_scores = torch.minimum(cube_scores, total_hw)

    elapsed = time.time() - t0
    print(f"  Done in {elapsed:.1f}s ({n_cubes * n_random / elapsed:.0f} eval/s)")

    # Sort by score
    sorted_idx = cube_scores.argsort()
    results = [(sorted_idx[i].item(), cube_scores[sorted_idx[i]].item())
               for i in range(n_cubes)]

    # Print distribution
    scores = cube_scores.cpu().numpy()
    print(f"  Score distribution: min={scores.min()}, median={int(scores[len(scores)//2])}, "
          f"max={scores.max()}")
    top10 = results[:10]
    print(f"  Top 10 cubes: {[(hex(c), s) for c, s in top10]}")

    return results, dw57


def encode_cube_cnf(N, m0, fill, cube_idx, n_cube_bits, dw57, output_dir):
    """
    Encode sr=60 CNF with cube assumptions (fixing low bits of W1[57]).
    """
    sys.path.insert(0, '/home/yale/sha256_probe')
    spec = __import__('50_precision_homotopy')
    sha = spec.MiniSHA256(N)
    WMASK = sha.MASK
    MSB = sha.MSB
    K32 = spec.K32

    M1 = [m0] + [fill]*15
    M2 = list(M1); M2[0] = m0 ^ MSB; M2[9] = fill ^ MSB
    s1, W1 = sha.compress(M1)
    s2, W2 = sha.compress(M2)

    ops = {'r_Sig0': sha.r_Sig0, 'r_Sig1': sha.r_Sig1,
           'r_sig0': sha.r_sig0, 's_sig0': sha.s_sig0,
           'r_sig1': sha.r_sig1, 's_sig1': sha.s_sig1}
    KT = [k & WMASK for k in K32]

    cnf = spec.MiniCNFBuilder(N)
    st1 = tuple(cnf.const_word(v) for v in s1)
    st2 = tuple(cnf.const_word(v) for v in s2)
    w1f = [cnf.free_word(f"W1_{57+i}") for i in range(4)]
    w2f = [cnf.free_word(f"W2_{57+i}") for i in range(4)]

    def s1w(x): return cnf.sigma1_w(x, ops['r_sig1'], ops['s_sig1'])

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

    # Add cube assumptions: fix low bits of W1[57]
    # w1f[0] is W1[57], which is a list of N variable IDs (one per bit)
    w1_57_vars = w1f[0]  # list of N variable IDs, bit 0 first
    for bit in range(n_cube_bits):
        var = w1_57_vars[bit]
        val = (cube_idx >> bit) & 1
        if val:
            cnf.clauses.append([var])   # force bit to 1
        else:
            cnf.clauses.append([-var])  # force bit to 0

    f = os.path.join(output_dir, f"cube_{cube_idx:04x}.cnf")
    nv, nc = cnf.write_dimacs(f)
    return f, nv, nc


def solve_cubes(N, m0, fill, ranked_cubes, n_cube_bits, dw57,
                top_m=64, timeout=3600, max_parallel=20):
    """Solve top-M cubes in parallel."""
    output_dir = tempfile.mkdtemp(prefix=f"cnc_N{N}_")
    print(f"\nEncoding top {top_m} cubes...")

    cnf_files = []
    for i, (cube_idx, score) in enumerate(ranked_cubes[:top_m]):
        f, nv, nc = encode_cube_cnf(N, m0, fill, cube_idx, n_cube_bits,
                                     dw57, output_dir)
        cnf_files.append((cube_idx, score, f, nv, nc))
        if i == 0:
            print(f"  CNF size: {nv} vars, {nc} clauses per cube")

    print(f"Launching {len(cnf_files)} solvers (max {max_parallel} parallel, "
          f"{timeout}s timeout each)...")

    procs = []
    results = []
    launched = 0
    t0 = time.time()

    while launched < len(cnf_files) or procs:
        # Launch new procs up to limit
        while launched < len(cnf_files) and len(procs) < max_parallel:
            cube_idx, score, f, nv, nc = cnf_files[launched]
            p = subprocess.Popen(["kissat", "-q", f],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            procs.append((launched, cube_idx, score, p, time.time()))
            launched += 1

        # Check for completion
        for j, (idx, cube_idx, score, p, pt0) in enumerate(procs):
            ret = p.poll()
            if ret is not None:
                elapsed = time.time() - pt0
                if ret == 10:
                    print(f"\n*** SAT *** cube 0x{cube_idx:x} (score={score}) "
                          f"in {elapsed:.1f}s — COLLISION FOUND!", flush=True)
                    # Kill all others
                    for k, (_, _, _, p2, _) in enumerate(procs):
                        if k != j:
                            p2.kill()
                    return "SAT", cube_idx, elapsed
                elif ret == 20:
                    results.append(("UNSAT", cube_idx, elapsed))
                    if len(results) % 10 == 0:
                        total_elapsed = time.time() - t0
                        print(f"  {len(results)}/{top_m} done, "
                              f"{sum(1 for r in results if r[0]=='UNSAT')} UNSAT, "
                              f"{total_elapsed:.0f}s", flush=True)
                else:
                    results.append(("TIMEOUT", cube_idx, elapsed))
                procs.pop(j)
                break
            elif time.time() - pt0 > timeout:
                p.kill()
                p.wait()
                results.append(("TIMEOUT", cube_idx, time.time() - pt0))
                procs.pop(j)
                break
        else:
            time.sleep(1)

    total_elapsed = time.time() - t0
    n_unsat = sum(1 for r in results if r[0] == "UNSAT")
    n_timeout = sum(1 for r in results if r[0] == "TIMEOUT")
    print(f"\nAll {top_m} cubes done: {n_unsat} UNSAT, {n_timeout} TIMEOUT "
          f"in {total_elapsed:.0f}s")
    return "EXHAUSTED", None, total_elapsed


def main():
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    n_cube_bits = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    top_cubes = int(sys.argv[3]) if len(sys.argv) > 3 else 32
    timeout = int(sys.argv[4]) if len(sys.argv) > 4 else 3600
    max_parallel = int(sys.argv[5]) if len(sys.argv) > 5 else 20

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    # Find a candidate
    sys.path.insert(0, '/home/yale/sha256_probe')
    spec = __import__('50_precision_homotopy')
    sha = spec.MiniSHA256(N)

    # Use fast_scan via C for larger N
    import subprocess as sp
    result = sp.run(["./fast_scan", str(N), "1"], capture_output=True, text=True,
                    cwd="/home/yale/sha256_probe")
    lines = [l for l in result.stdout.strip().split('\n') if l and not l.startswith('m0,')]
    if not lines:
        print(f"No candidate at N={N}")
        return
    parts = lines[0].split(',')
    m0, fill = int(parts[0]), int(parts[1])

    print(f"GPU Cube-and-Conquer: N={N}")
    print(f"  Candidate: M[0]=0x{m0:x}, fill=0x{fill:x}")
    print(f"  Cube bits: {n_cube_bits} ({1 << n_cube_bits} cubes)")
    print(f"  Top cubes to solve: {top_cubes}")
    print(f"  Timeout per cube: {timeout}s")
    print(f"  Max parallel: {max_parallel}")
    print(f"  Device: {device}")
    print()

    # Precompute
    M1 = [m0] + [fill]*15
    M2 = list(M1); M2[0] = m0 ^ sha.MSB; M2[9] = fill ^ sha.MSB
    s1, W1 = sha.compress(M1)
    s2, W2 = sha.compress(M2)
    assert s1[0] == s2[0]

    # Phase 1: GPU rank cubes
    ranked, dw57 = gpu_rank_cubes(s1, s2, W1, W2, n_cube_bits, device)

    # Phase 2: Solve top cubes
    result, cube, elapsed = solve_cubes(N, m0, fill, ranked, n_cube_bits,
                                         dw57, top_cubes, timeout, max_parallel)
    if result == "SAT":
        print(f"\n{'='*60}")
        print(f"COLLISION FOUND at N={N}!")
        print(f"Cube 0x{cube:x} in {elapsed:.1f}s")
        print(f"{'='*60}")


if __name__ == "__main__":
    main()
