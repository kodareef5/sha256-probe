#!/usr/bin/env python3
"""
Step 5: Cross-Register Correlation Analysis

Analyze pairwise correlations and combined algebraic degrees across all
64 output difference bits (8 registers x 8 bits at N=8) of the 7-round
SHA-256 tail.

The function: takes 4 free N-bit words per message (2 messages, 8*N total
free bits) and outputs 8*N difference bits (state1 XOR state2).

For ALL C(8N, 2) output bit pairs (i < j):
  1. Compute pairwise correlation: Pr[f_i(x) = f_j(x)] over random x
  2. Estimate degree of f_i XOR f_j via restriction test
  3. Flag pairs where combined degree < min(individual degrees) - 2

Also find minimum-weight linear combinations within each register that
have lowest degree.

Reports: correlation matrix heatmap data, flagged low-degree pairs,
register-internal vs cross-register comparison.

Usage: python3 cross_register_corr.py [N] [n_samples]
  N         -- word width (default 8)
  n_samples -- random samples for correlation/degree (default 50000)
"""

import sys
import os
import time
import random
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
from lib.sha256 import K as K32

# ---------------------------------------------------------------------------
# Setup: load MiniSHA256 for N-bit support
# ---------------------------------------------------------------------------

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
spec = __import__('50_precision_homotopy')


def make_evaluator(N):
    """
    Build a fast evaluation closure for the N-bit 7-round tail difference.

    Returns (eval_fn, n_out_bits) where:
      eval_fn(rng_state) -> numpy array of n_out_bits uint8 values (0 or 1)

    The closure captures the precomputed state and schedule, and inlines
    all arithmetic for speed.
    """
    sha = spec.MiniSHA256(N)
    MASK = sha.MASK
    MSB = sha.MSB

    # Find a valid candidate (da[56]=0)
    m0, state1, state2, W1_full, W2_full = sha.find_m0()
    if m0 is None:
        print(f"ERROR: No da[56]=0 candidate found at N={N}")
        sys.exit(1)
    print(f"Candidate: M[0]=0x{m0:x}, fill=0x{MASK:x} at N={N}")

    W1_pre = W1_full[:57]
    W2_pre = W2_full[:57]

    # Precompute truncated round constants for rounds 57-63
    Kn = [k & MASK for k in K32]
    K57_63 = [Kn[57 + i] for i in range(7)]

    # Cache rotation amounts
    rS0 = sha.r_Sig0
    rS1 = sha.r_Sig1
    rs0 = sha.r_sig0
    ss0 = sha.s_sig0
    rs1 = sha.r_sig1
    ss1 = sha.s_sig1

    # Precompute fixed schedule contributions for W[61], W[62], W[63]
    # W[61] = sigma1(W[59]) + W1_pre[54] + sigma0(W1_pre[46]) + W1_pre[45]
    # The sigma1(W[59]) part depends on free words; the rest is constant per message.
    w1_61_const = (W1_pre[54] + sha.sigma0(W1_pre[46]) + W1_pre[45]) & MASK
    w2_61_const = (W2_pre[54] + sha.sigma0(W2_pre[46]) + W2_pre[45]) & MASK

    # W[62] = sigma1(W[60]) + W1_pre[55] + sigma0(W1_pre[47]) + W1_pre[46]
    w1_62_const = (W1_pre[55] + sha.sigma0(W1_pre[47]) + W1_pre[46]) & MASK
    w2_62_const = (W2_pre[55] + sha.sigma0(W2_pre[47]) + W2_pre[46]) & MASK

    # W[63] depends on W[61] which is variable, so only partial precompute
    # W[63] = sigma1(W[61]) + W1_pre[56] + sigma0(W1_pre[48]) + W1_pre[47]
    w1_63_const = (W1_pre[56] + sha.sigma0(W1_pre[48]) + W1_pre[47]) & MASK
    w2_63_const = (W2_pre[56] + sha.sigma0(W2_pre[48]) + W2_pre[47]) & MASK

    # Local references for inner loop speed
    s1_init = state1
    s2_init = state2

    n_out = 8 * N

    def ror(x, k):
        k = k % N
        return ((x >> k) | (x << (N - k))) & MASK

    def Sigma0(a):
        return ror(a, rS0[0]) ^ ror(a, rS0[1]) ^ ror(a, rS0[2])

    def Sigma1(e):
        return ror(e, rS1[0]) ^ ror(e, rS1[1]) ^ ror(e, rS1[2])

    def sigma1_f(x):
        return ror(x, rs1[0]) ^ ror(x, rs1[1]) ^ ((x >> ss1) & MASK)

    def ch(e, f, g):
        return ((e & f) ^ ((~e) & g)) & MASK

    def maj(a, b, c):
        return ((a & b) ^ (a & c) ^ (b & c)) & MASK

    def run_7_rounds(state_init, sched):
        """Run rounds 57-63, return final (a,b,c,d,e,f,g,h)."""
        a, b, c, d, e, f, g, h = state_init
        for i in range(7):
            T1 = (h + Sigma1(e) + ch(e, f, g) + K57_63[i] + sched[i]) & MASK
            T2 = (Sigma0(a) + maj(a, b, c)) & MASK
            h = g; g = f; f = e; e = (d + T1) & MASK
            d = c; c = b; b = a; a = (T1 + T2) & MASK
        return (a, b, c, d, e, f, g, h)

    def eval_diff(w1, w2):
        """
        Given 4 free words per message, compute 7-round tail and return
        the XOR difference as a tuple of 8 N-bit words.

        w1, w2: each a list/tuple of 4 N-bit ints (W[57..60] for each message)
        """
        # Build schedule tail for message 1
        w1_61 = (sigma1_f(w1[2]) + w1_61_const) & MASK
        w1_62 = (sigma1_f(w1[3]) + w1_62_const) & MASK
        w1_63 = (sigma1_f(w1_61) + w1_63_const) & MASK
        sched1 = (w1[0], w1[1], w1[2], w1[3], w1_61, w1_62, w1_63)

        # Build schedule tail for message 2
        w2_61 = (sigma1_f(w2[2]) + w2_61_const) & MASK
        w2_62 = (sigma1_f(w2[3]) + w2_62_const) & MASK
        w2_63 = (sigma1_f(w2_61) + w2_63_const) & MASK
        sched2 = (w2[0], w2[1], w2[2], w2[3], w2_61, w2_62, w2_63)

        f1 = run_7_rounds(s1_init, sched1)
        f2 = run_7_rounds(s2_init, sched2)

        return tuple(f1[r] ^ f2[r] for r in range(8))

    return eval_diff, n_out, sha


def batch_eval(eval_diff, N, n_samples, rng):
    """
    Evaluate the difference function on n_samples random inputs.
    Returns an (n_samples, 8*N) uint8 array of individual output bits.
    """
    MASK = (1 << N) - 1
    n_out = 8 * N
    results = np.empty((n_samples, n_out), dtype=np.uint8)

    for s in range(n_samples):
        w1 = [rng.getrandbits(N) for _ in range(4)]
        w2 = [rng.getrandbits(N) for _ in range(4)]
        diff = eval_diff(w1, w2)

        idx = 0
        for reg in range(8):
            d = diff[reg]
            for bit in range(N):
                results[s, idx] = (d >> bit) & 1
                idx += 1

    return results


def restriction_degree_single(eval_diff, N, bit_idx, n_trials=100):
    """
    Estimate degree of a single output bit via restriction test.
    Returns estimated degree (smallest k where the bit is not always constant).
    """
    MASK = (1 << N) - 1
    n_free_bits = 8 * N  # 4 words * N bits * 2 messages
    reg = bit_idx // N
    bpos = bit_idx % N

    k_values = [1, 2, 4, 8, 16, 32]
    k_values = [k for k in k_values if k <= n_free_bits]

    rng = random.Random(bit_idx * 1000 + 7)

    for k in k_values:
        all_constant = True
        for trial in range(n_trials):
            # Random base point
            base_w1 = [rng.getrandbits(N) & MASK for _ in range(4)]
            base_w2 = [rng.getrandbits(N) & MASK for _ in range(4)]
            base_diff = eval_diff(base_w1, base_w2)
            base_val = (base_diff[reg] >> bpos) & 1

            # Pick k random free bit positions
            positions = rng.sample(range(n_free_bits), min(k, n_free_bits))

            found_change = False
            # Try all 2^k combinations (or sample if k too large)
            n_combos = min(1 << k, 32)
            for combo in range(1, n_combos):
                flip_w1 = list(base_w1)
                flip_w2 = list(base_w2)
                for p_idx, pos in enumerate(positions):
                    if not ((combo >> p_idx) & 1):
                        continue
                    if pos < 4 * N:
                        word_idx = pos // N
                        bp = pos % N
                        flip_w1[word_idx] ^= (1 << bp)
                    else:
                        adj = pos - 4 * N
                        word_idx = adj // N
                        bp = adj % N
                        flip_w2[word_idx] ^= (1 << bp)

                flip_diff = eval_diff(flip_w1, flip_w2)
                flip_val = (flip_diff[reg] >> bpos) & 1
                if flip_val != base_val:
                    found_change = True
                    break

            if found_change:
                all_constant = False
                break

        if not all_constant:
            return k

    return n_free_bits  # full degree


def restriction_degree_xor(eval_diff, N, bit_i, bit_j, n_trials=100):
    """
    Estimate degree of f_i XOR f_j via restriction test.
    """
    MASK = (1 << N) - 1
    n_free_bits = 8 * N
    reg_i, bpos_i = bit_i // N, bit_i % N
    reg_j, bpos_j = bit_j // N, bit_j % N

    k_values = [1, 2, 4, 8, 16, 32]
    k_values = [k for k in k_values if k <= n_free_bits]

    rng = random.Random(bit_i * 10000 + bit_j * 100 + 13)

    for k in k_values:
        all_constant = True
        for trial in range(n_trials):
            base_w1 = [rng.getrandbits(N) & MASK for _ in range(4)]
            base_w2 = [rng.getrandbits(N) & MASK for _ in range(4)]
            base_diff = eval_diff(base_w1, base_w2)
            base_val = ((base_diff[reg_i] >> bpos_i) ^ (base_diff[reg_j] >> bpos_j)) & 1

            positions = rng.sample(range(n_free_bits), min(k, n_free_bits))

            found_change = False
            n_combos = min(1 << k, 32)
            for combo in range(1, n_combos):
                flip_w1 = list(base_w1)
                flip_w2 = list(base_w2)
                for p_idx, pos in enumerate(positions):
                    if not ((combo >> p_idx) & 1):
                        continue
                    if pos < 4 * N:
                        word_idx = pos // N
                        bp = pos % N
                        flip_w1[word_idx] ^= (1 << bp)
                    else:
                        adj = pos - 4 * N
                        word_idx = adj // N
                        bp = adj % N
                        flip_w2[word_idx] ^= (1 << bp)

                flip_diff = eval_diff(flip_w1, flip_w2)
                flip_val = ((flip_diff[reg_i] >> bpos_i) ^ (flip_diff[reg_j] >> bpos_j)) & 1
                if flip_val != base_val:
                    found_change = True
                    break

            if found_change:
                all_constant = False
                break

        if not all_constant:
            return k

    return n_free_bits


def main():
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    n_samples = int(sys.argv[2]) if len(sys.argv) > 2 else 50000

    random.seed(42)
    np.random.seed(42)
    rng = random.Random(42)

    n_out = 8 * N
    n_pairs = n_out * (n_out - 1) // 2

    print(f"Cross-Register Correlation Analysis")
    print(f"  N = {N} (word width)")
    print(f"  Output bits: {n_out} (8 registers x {N} bits)")
    print(f"  Output bit pairs: {n_pairs}")
    print(f"  Samples for correlation: {n_samples}")
    print(f"  Restriction trials: 100 per degree estimate")
    print(f"=" * 70)

    # Build evaluator
    t0 = time.time()
    eval_diff, _, sha_obj = make_evaluator(N)
    print(f"Setup time: {time.time() - t0:.2f}s\n")

    # ===================================================================
    # Phase 1: Batch evaluation — compute all output bits on n_samples inputs
    # ===================================================================
    print(f"Phase 1: Evaluating {n_samples} random inputs...")
    t1 = time.time()
    data = batch_eval(eval_diff, N, n_samples, rng)
    print(f"  Evaluation time: {time.time() - t1:.1f}s")
    print(f"  Data shape: {data.shape}")

    # ===================================================================
    # Phase 2: Pairwise correlation matrix
    # ===================================================================
    print(f"\nPhase 2: Pairwise correlations ({n_pairs} pairs)...")
    t2 = time.time()

    # Pr[f_i = f_j] = fraction of samples where bits agree
    # Use vectorized XOR: agreement = 1 - XOR
    # corr_matrix[i][j] = mean(data[:,i] == data[:,j])
    # = mean(1 - (data[:,i] XOR data[:,j]))
    # = 1 - mean(data[:,i] XOR data[:,j])
    corr_matrix = np.zeros((n_out, n_out), dtype=np.float32)
    for i in range(n_out):
        corr_matrix[i, i] = 1.0
        for j in range(i + 1, n_out):
            agree_frac = 1.0 - np.mean(data[:, i] ^ data[:, j])
            corr_matrix[i, j] = agree_frac
            corr_matrix[j, i] = agree_frac

    print(f"  Correlation matrix time: {time.time() - t2:.1f}s")

    # Summary stats
    triu_idx = np.triu_indices(n_out, k=1)
    corr_vals = corr_matrix[triu_idx]
    print(f"\n  Correlation statistics (Pr[f_i = f_j]):")
    print(f"    Mean:   {corr_vals.mean():.6f}")
    print(f"    Std:    {corr_vals.std():.6f}")
    print(f"    Min:    {corr_vals.min():.6f}")
    print(f"    Max:    {corr_vals.max():.6f}")
    print(f"    Median: {np.median(corr_vals):.6f}")

    # Expected for independent balanced bits: 0.5
    bias_from_half = np.abs(corr_vals - 0.5)
    print(f"    |corr - 0.5| > 0.05: {np.sum(bias_from_half > 0.05)}")
    print(f"    |corr - 0.5| > 0.10: {np.sum(bias_from_half > 0.10)}")
    print(f"    |corr - 0.5| > 0.20: {np.sum(bias_from_half > 0.20)}")

    # ===================================================================
    # Phase 3: Register-internal vs cross-register comparison
    # ===================================================================
    print(f"\nPhase 3: Register-internal vs cross-register correlations")
    reg_names = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']

    intra_corrs = []
    inter_corrs = []

    for i in range(n_out):
        for j in range(i + 1, n_out):
            reg_i = i // N
            reg_j = j // N
            c = corr_matrix[i, j]
            if reg_i == reg_j:
                intra_corrs.append(c)
            else:
                inter_corrs.append(c)

    intra_corrs = np.array(intra_corrs)
    inter_corrs = np.array(inter_corrs)

    print(f"  Intra-register pairs: {len(intra_corrs)}")
    if len(intra_corrs) > 0:
        print(f"    Mean corr: {intra_corrs.mean():.6f}")
        print(f"    Std:       {intra_corrs.std():.6f}")
        print(f"    |c-0.5|>0.05: {np.sum(np.abs(intra_corrs - 0.5) > 0.05)}")

    print(f"  Inter-register pairs: {len(inter_corrs)}")
    if len(inter_corrs) > 0:
        print(f"    Mean corr: {inter_corrs.mean():.6f}")
        print(f"    Std:       {inter_corrs.std():.6f}")
        print(f"    |c-0.5|>0.05: {np.sum(np.abs(inter_corrs - 0.5) > 0.05)}")

    # Per-register breakdown
    print(f"\n  Per-register pair correlation (mean |corr - 0.5|):")
    print(f"  {'Reg_i':>6} {'Reg_j':>6} {'Mean corr':>10} {'Mean|c-.5|':>11} {'Max|c-.5|':>10} {'N_pairs':>8}")
    for ri in range(8):
        for rj in range(ri, 8):
            pairs = []
            for i in range(ri * N, (ri + 1) * N):
                j_start = max(i + 1, rj * N)
                for j in range(j_start, (rj + 1) * N):
                    pairs.append(corr_matrix[i, j])
            if len(pairs) == 0:
                continue
            pairs = np.array(pairs)
            bias = np.abs(pairs - 0.5)
            tag = "*" if bias.mean() > 0.02 else " "
            print(f"  {reg_names[ri]:>6} {reg_names[rj]:>6} {pairs.mean():10.6f} "
                  f"{bias.mean():11.6f} {bias.max():10.6f} {len(pairs):8d}{tag}")

    # ===================================================================
    # Phase 4: Individual bit degree estimates
    # ===================================================================
    print(f"\nPhase 4: Individual output bit degree estimates...")
    t4 = time.time()
    individual_degrees = np.zeros(n_out, dtype=np.int32)

    for bit in range(n_out):
        deg = restriction_degree_single(eval_diff, N, bit)
        individual_degrees[bit] = deg
        if bit % N == 0:
            reg = bit // N
            print(f"  Register {reg_names[reg]} (bits {reg*N}-{(reg+1)*N-1}): "
                  f"bit {bit} degree = {deg}", flush=True)

    print(f"  Individual degree time: {time.time() - t4:.1f}s")
    print(f"\n  Degree distribution:")
    for k in sorted(set(individual_degrees)):
        cnt = np.sum(individual_degrees == k)
        print(f"    degree {k:3d}: {cnt} bits")

    # ===================================================================
    # Phase 5: Pairwise XOR degree and flagging
    # ===================================================================
    print(f"\nPhase 5: Pairwise XOR degree estimation ({n_pairs} pairs)...")
    print(f"  (Estimating degree of f_i XOR f_j for all pairs)")
    t5 = time.time()

    flagged_pairs = []
    pair_degrees = {}
    n_checked = 0
    n_total = n_pairs

    # Prioritize pairs with highest correlation bias (most likely to have low degree)
    pair_list = []
    for i in range(n_out):
        for j in range(i + 1, n_out):
            pair_list.append((i, j, abs(corr_matrix[i, j] - 0.5)))
    pair_list.sort(key=lambda x: -x[2])  # highest bias first

    for idx, (i, j, bias) in enumerate(pair_list):
        xor_deg = restriction_degree_xor(eval_diff, N, i, j)
        pair_degrees[(i, j)] = xor_deg
        n_checked += 1

        min_indiv = min(individual_degrees[i], individual_degrees[j])
        # Flag if combined degree is significantly lower than individual
        if xor_deg < min_indiv - 2:
            reg_i, bpos_i = i // N, i % N
            reg_j, bpos_j = j // N, j % N
            flagged_pairs.append({
                'i': i, 'j': j,
                'reg_i': reg_i, 'bit_i': bpos_i,
                'reg_j': reg_j, 'bit_j': bpos_j,
                'deg_i': individual_degrees[i],
                'deg_j': individual_degrees[j],
                'deg_xor': xor_deg,
                'corr': corr_matrix[i, j],
            })

        if idx % 200 == 0:
            elapsed = time.time() - t5
            rate = (idx + 1) / elapsed if elapsed > 0 else 0
            eta = (n_total - idx - 1) / rate if rate > 0 else 0
            print(f"  [{idx+1}/{n_total}] flagged={len(flagged_pairs)} "
                  f"({elapsed:.0f}s elapsed, ~{eta:.0f}s remaining)", flush=True)

    print(f"  Pairwise degree time: {time.time() - t5:.1f}s")

    # ===================================================================
    # Phase 6: Minimum-weight linear combinations per register
    # ===================================================================
    print(f"\nPhase 6: Minimum-weight register-internal XOR combinations")

    for reg in range(8):
        base = reg * N
        bits_in_reg = list(range(base, base + N))

        # Check all pairs within the register
        best_deg = 999
        best_combo = None
        for i in range(len(bits_in_reg)):
            for j in range(i + 1, len(bits_in_reg)):
                bi, bj = bits_in_reg[i], bits_in_reg[j]
                key = (bi, bj)
                if key in pair_degrees:
                    deg = pair_degrees[key]
                    if deg < best_deg:
                        best_deg = deg
                        best_combo = (bi, bj)

        # Also check weight-3 combinations (XOR of 3 bits)
        best3_deg = 999
        best3_combo = None
        if N <= 16:  # only feasible for small N
            for i in range(len(bits_in_reg)):
                for j in range(i + 1, len(bits_in_reg)):
                    for k_idx in range(j + 1, len(bits_in_reg)):
                        bi = bits_in_reg[i]
                        bj = bits_in_reg[j]
                        bk = bits_in_reg[k_idx]
                        # Degree of f_i XOR f_j XOR f_k
                        deg = restriction_degree_triple_xor(
                            eval_diff, N, bi, bj, bk)
                        if deg < best3_deg:
                            best3_deg = deg
                            best3_combo = (bi, bj, bk)

        print(f"  Register {reg_names[reg]} (bits {base}-{base+N-1}):")
        if best_combo is not None:
            print(f"    Best weight-2 XOR: bits {best_combo}, degree = {best_deg}")
        if best3_combo is not None:
            print(f"    Best weight-3 XOR: bits {best3_combo}, degree = {best3_deg}")

    # ===================================================================
    # Report
    # ===================================================================
    print(f"\n{'=' * 70}")
    print(f"SUMMARY")
    print(f"{'=' * 70}")

    print(f"\nTotal pairs analyzed: {n_checked}")
    print(f"Total time: {time.time() - t0:.1f}s")

    # Correlation heatmap data
    print(f"\nCorrelation heatmap (Pr[f_i = f_j], 8x8 register blocks):")
    print(f"  (Values are mean correlation within each register-pair block)")
    header = "       " + "".join(f"{reg_names[r]:>8}" for r in range(8))
    print(header)
    for ri in range(8):
        row = f"  {reg_names[ri]:>4} "
        for rj in range(8):
            vals = []
            for i in range(ri * N, (ri + 1) * N):
                for j in range(rj * N, (rj + 1) * N):
                    if i != j:
                        vals.append(corr_matrix[i, j])
            if vals:
                row += f"{np.mean(vals):8.4f}"
            else:
                row += f"{'---':>8}"
        print(row)

    # Flagged pairs
    if flagged_pairs:
        print(f"\n*** FLAGGED LOW-DEGREE PAIRS: {len(flagged_pairs)} ***")
        print(f"  (Combined degree < min(individual degrees) - 2)")
        print(f"  {'Bit_i':>6} {'Bit_j':>6} {'Reg_i':>6} {'Reg_j':>6} "
              f"{'Deg_i':>6} {'Deg_j':>6} {'Deg_XOR':>8} {'Corr':>8}")
        for p in sorted(flagged_pairs, key=lambda x: x['deg_xor']):
            ri_name = reg_names[p['reg_i']]
            rj_name = reg_names[p['reg_j']]
            print(f"  {p['i']:6d} {p['j']:6d} {ri_name:>6} {rj_name:>6} "
                  f"{p['deg_i']:6d} {p['deg_j']:6d} {p['deg_xor']:8d} "
                  f"{p['corr']:8.4f}")
    else:
        print(f"\nNo flagged low-degree pairs found.")
        print(f"  All pairwise XOR degrees are within 2 of min(individual degrees).")
        print(f"  This suggests no easily exploitable cross-bit cancellations.")

    # Degree distribution for XOR pairs
    xor_degs = list(pair_degrees.values())
    print(f"\nPairwise XOR degree distribution:")
    for k in sorted(set(xor_degs)):
        cnt = sum(1 for d in xor_degs if d == k)
        print(f"  degree {k:3d}: {cnt} pairs")

    # Top correlated pairs
    top_n = min(20, len(pair_list))
    print(f"\nTop {top_n} most correlated pairs (by |corr - 0.5|):")
    print(f"  {'Bit_i':>6} {'Bit_j':>6} {'Reg_i':>6} {'Reg_j':>6} "
          f"{'Corr':>8} {'|c-.5|':>8} {'Deg_XOR':>8}")
    for i, j, bias in pair_list[:top_n]:
        ri_name = reg_names[i // N]
        rj_name = reg_names[j // N]
        deg = pair_degrees.get((i, j), -1)
        print(f"  {i:6d} {j:6d} {ri_name:>6} {rj_name:>6} "
              f"{corr_matrix[i, j]:8.4f} {bias:8.4f} {deg:8d}")


def restriction_degree_triple_xor(eval_diff, N, bit_i, bit_j, bit_k, n_trials=50):
    """
    Estimate degree of f_i XOR f_j XOR f_k via restriction test.
    Fewer trials than pairwise since this is exploratory.
    """
    MASK = (1 << N) - 1
    n_free_bits = 8 * N
    reg_i, bpos_i = bit_i // N, bit_i % N
    reg_j, bpos_j = bit_j // N, bit_j % N
    reg_k, bpos_k = bit_k // N, bit_k % N

    k_values = [1, 2, 4, 8, 16, 32]
    k_values = [k for k in k_values if k <= n_free_bits]

    rng = random.Random(bit_i * 100000 + bit_j * 1000 + bit_k * 10 + 17)

    for k in k_values:
        all_constant = True
        for trial in range(n_trials):
            base_w1 = [rng.getrandbits(N) & MASK for _ in range(4)]
            base_w2 = [rng.getrandbits(N) & MASK for _ in range(4)]
            base_diff = eval_diff(base_w1, base_w2)
            base_val = (((base_diff[reg_i] >> bpos_i) ^
                         (base_diff[reg_j] >> bpos_j) ^
                         (base_diff[reg_k] >> bpos_k)) & 1)

            positions = rng.sample(range(n_free_bits), min(k, n_free_bits))

            found_change = False
            n_combos = min(1 << k, 32)
            for combo in range(1, n_combos):
                flip_w1 = list(base_w1)
                flip_w2 = list(base_w2)
                for p_idx, pos in enumerate(positions):
                    if not ((combo >> p_idx) & 1):
                        continue
                    if pos < 4 * N:
                        word_idx = pos // N
                        bp = pos % N
                        flip_w1[word_idx] ^= (1 << bp)
                    else:
                        adj = pos - 4 * N
                        word_idx = adj // N
                        bp = adj % N
                        flip_w2[word_idx] ^= (1 << bp)

                flip_diff = eval_diff(flip_w1, flip_w2)
                flip_val = (((flip_diff[reg_i] >> bpos_i) ^
                             (flip_diff[reg_j] >> bpos_j) ^
                             (flip_diff[reg_k] >> bpos_k)) & 1)
                if flip_val != base_val:
                    found_change = True
                    break

            if found_change:
                all_constant = False
                break

        if not all_constant:
            return k

    return n_free_bits


if __name__ == "__main__":
    main()
