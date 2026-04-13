#!/usr/bin/env python3
"""
GPU-accelerated de-set measurement for the macbook's de-pruning analysis.

For each cascade round (57-60), compute the e-register diff (de) and
record which values appear across all collisions. The product of
|de_sets| gives the effective search space reduction.

Uses the compiled cascade DP to find collisions, then extracts de values.
"""
import sys, os, time, math
import torch

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')

from q5_alternative_attacks.gpu_kernel_sweep_compiled import (
    Params, find_candidate, find_all_candidates,
    make_compiled_batch_fn, gpu_cascade_dp
)


def measure_de_sets_gpu(p, s1_56, s2_56, W1p, W2p):
    """
    Find all collisions and extract de values at each round.
    Uses Python cascade DP (not GPU) but with cascade offsets for efficiency.
    """
    N, MASK, SIZE = p.N, p.MASK, 1 << p.N
    de_sets = {57: set(), 58: set(), 59: set(), 60: set()}
    total_coll = 0
    t0 = time.time()

    for w57 in range(SIZE):
        cas57 = p.cascade_offset(s1_56, s2_56, 57)
        w2_57 = (w57 + cas57) & MASK
        st1 = p.sha_round(s1_56, p.KN[57], w57)
        st2 = p.sha_round(s2_56, p.KN[57], w2_57)
        de57 = (st1[4] - st2[4]) & MASK

        for w58 in range(SIZE):
            cas58 = p.cascade_offset(st1, st2, 58)
            w2_58 = (w58 + cas58) & MASK
            st1_58 = p.sha_round(st1, p.KN[58], w58)
            st2_58 = p.sha_round(st2, p.KN[58], w2_58)
            de58 = (st1_58[4] - st2_58[4]) & MASK

            for w59 in range(SIZE):
                cas59 = p.cascade_offset(st1_58, st2_58, 59)
                w2_59 = (w59 + cas59) & MASK
                st1_59 = p.sha_round(st1_58, p.KN[59], w59)
                st2_59 = p.sha_round(st2_58, p.KN[59], w2_59)
                de59 = (st1_59[4] - st2_59[4]) & MASK

                for w60 in range(SIZE):
                    cas60 = p.cascade_offset(st1_59, st2_59, 60)
                    w2_60 = (w60 + cas60) & MASK
                    st1_60 = p.sha_round(st1_59, p.KN[60], w60)
                    st2_60 = p.sha_round(st2_59, p.KN[60], w2_60)

                    W1f = [w57, w58, w59, w60, 0, 0, 0]
                    W2f = [w2_57, w2_58, w2_59, w2_60, 0, 0, 0]
                    W1f[4] = (p.sigma1(W1f[2]) + W1p[54] + p.sigma0(W1p[46]) + W1p[45]) & MASK
                    W2f[4] = (p.sigma1(W2f[2]) + W2p[54] + p.sigma0(W2p[46]) + W2p[45]) & MASK
                    W1f[5] = (p.sigma1(W1f[3]) + W1p[55] + p.sigma0(W1p[47]) + W1p[46]) & MASK
                    W2f[5] = (p.sigma1(W2f[3]) + W2p[55] + p.sigma0(W2p[47]) + W2p[46]) & MASK
                    W1f[6] = (p.sigma1(W1f[4]) + W1p[56] + p.sigma0(W1p[48]) + W1p[47]) & MASK
                    W2f[6] = (p.sigma1(W2f[4]) + W2p[56] + p.sigma0(W2p[48]) + W2p[47]) & MASK

                    fs1, fs2 = list(st1_60), list(st2_60)
                    for r in range(4, 7):
                        fs1 = p.sha_round(fs1, p.KN[57 + r], W1f[r])
                        fs2 = p.sha_round(fs2, p.KN[57 + r], W2f[r])

                    if all(fs1[r] == fs2[r] for r in range(8)):
                        total_coll += 1
                        de_sets[57].add(de57)
                        de_sets[58].add(de58)
                        de_sets[59].add(de59)
                        de60 = (st1_60[4] - st2_60[4]) & MASK
                        de_sets[60].add(de60)

        if w57 % max(1, SIZE // 16) == 0:
            elapsed = time.time() - t0
            pct = 100.0 * (w57 + 1) / SIZE
            print(f"  [{pct:5.1f}%] w57={w57:#x} coll={total_coll} {elapsed:.0f}s", flush=True)

    elapsed = time.time() - t0
    return total_coll, de_sets, elapsed


def main():
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    kernel_bit = int(sys.argv[2]) if len(sys.argv) > 2 else N - 1

    p = Params(N)
    SIZE = 1 << N

    print(f"de-set measurement at N={N}, kernel bit={kernel_bit}")

    cand = find_candidate(p, kernel_bit)
    if not cand:
        print("No candidate found")
        return

    m0, fill, s1, s2, W1, W2 = cand
    print(f"Candidate: M[0]=0x{m0:x}, fill=0x{fill:x}")

    total_coll, de_sets, elapsed = measure_de_sets_gpu(p, s1, s2, W1, W2)

    print(f"\nResults: {total_coll} collisions in {elapsed:.0f}s")
    product = 1
    for rnd in [57, 58, 59, 60]:
        n = len(de_sets[rnd])
        product *= n
        vals = sorted(de_sets[rnd])
        print(f"  de{rnd}: {n}/{SIZE} ({100*n/SIZE:.1f}%)  values: {[hex(v) for v in vals[:10]]}{'...' if n > 10 else ''}")
    print(f"  Product: {product:,} vs {SIZE**4:,} ({product/SIZE**4:.2e}x)")
    print(f"  Effective search: 2^{math.log2(max(1,product)):.1f} vs 2^{4*N}")
    print(f"  Pruning factor: {SIZE**4/max(1,product):,.0f}x")

    # Save
    ts = time.strftime('%Y%m%d_%H%M')
    outdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')
    os.makedirs(outdir, exist_ok=True)
    outpath = os.path.join(outdir, f'{ts}_de_sets_n{N}.md')
    with open(outpath, 'w') as f:
        f.write(f"# de-set measurement — N={N}, bit={kernel_bit}\n\n")
        f.write(f"Collisions: {total_coll}\n\n")
        f.write(f"| Round | |de| | /SIZE | Fraction |\n")
        f.write(f"|-------|------|-------|----------|\n")
        for rnd in [57, 58, 59, 60]:
            n = len(de_sets[rnd])
            f.write(f"| de{rnd} | {n} | {SIZE} | {100*n/SIZE:.1f}% |\n")
        f.write(f"\nProduct: {product:,}\n")
        f.write(f"Pruning: {SIZE**4/max(1,product):,.0f}x\n")
        f.write(f"Effective search: 2^{math.log2(max(1,product)):.1f} vs 2^{4*N}\n")
    print(f"\nSaved: {outpath}")


if __name__ == '__main__':
    main()
