#!/usr/bin/env python3
"""
Script 59: Comprehensive reduced-width sr=60 sweep

HYPOTHESIS: For all non-degenerate word widths, sr=60 is SAT.
The N=9 UNSAT was a rotation-degeneracy artifact.

Known results:
  N=8  SAT    4.2s
  N=9  UNSAT  0.25s  (degenerate -- sigma1 rots map to same value)
  N=10 SAT   70.6s
  N=11 SAT  150.5s
  N=12 SAT  559.6s

This script:
  1. Tests N=13, 14, 15, 16 with 600s timeout each
  2. Checks sigma1 rotation degeneracy for every N tested
  3. For N=8, 10, 12: tests 3 DIFFERENT M[0] candidates to confirm
     universality vs candidate-dependence
  4. Reports any N where no da[56]=0 candidate exists in the 2^N scan

Scope: MSB kernel with all-ones padding.
"""

import sys
import os
import time
import subprocess
import tempfile

# Import the infrastructure from script 50
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from importlib import import_module

# We'll directly import the needed pieces
# Re-derive them here to avoid module-naming issues with the "50_" prefix
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        '50_precision_homotopy.py')).read().split(
    'def main():')[0])

# ============================================================
# Degeneracy checker
# ============================================================

def check_sigma1_degeneracy(N):
    """Check if sigma1's rotation amounts are degenerate at width N.
    Degeneracy means two rotation amounts map to the same value mod N,
    which collapses the XOR and reduces effective diffusion."""
    r0 = max(1, round(17 * N / 32))
    r1 = max(1, round(19 * N / 32))
    s  = max(1, round(10 * N / 32))
    r0_eff = r0 % N
    r1_eff = r1 % N
    degenerate = (r0_eff == r1_eff)
    return degenerate, r0_eff, r1_eff, s

def check_sigma0_degeneracy(N):
    """Check if sigma0's rotation amounts are degenerate at width N."""
    r0 = max(1, round(7 * N / 32))
    r1 = max(1, round(18 * N / 32))
    s  = max(1, round(3 * N / 32))
    r0_eff = r0 % N
    r1_eff = r1 % N
    degenerate = (r0_eff == r1_eff)
    return degenerate, r0_eff, r1_eff, s

def check_Sigma0_degeneracy(N):
    """Check Sigma0 (compression) for rotation degeneracy."""
    r0 = max(1, round(2 * N / 32))
    r1 = max(1, round(13 * N / 32))
    r2 = max(1, round(22 * N / 32))
    vals = [r0 % N, r1 % N, r2 % N]
    degenerate = len(vals) != len(set(vals))
    return degenerate, vals

def check_Sigma1_degeneracy(N):
    """Check Sigma1 (compression) for rotation degeneracy."""
    r0 = max(1, round(6 * N / 32))
    r1 = max(1, round(11 * N / 32))
    r2 = max(1, round(25 * N / 32))
    vals = [r0 % N, r1 % N, r2 % N]
    degenerate = len(vals) != len(set(vals))
    return degenerate, vals

def full_degeneracy_report(N):
    """Return a dict with full degeneracy info for width N."""
    s1_deg, s1_r0, s1_r1, s1_s = check_sigma1_degeneracy(N)
    s0_deg, s0_r0, s0_r1, s0_s = check_sigma0_degeneracy(N)
    S0_deg, S0_vals = check_Sigma0_degeneracy(N)
    S1_deg, S1_vals = check_Sigma1_degeneracy(N)
    any_deg = s1_deg or s0_deg or S0_deg or S1_deg
    return {
        'any_degenerate': any_deg,
        'sigma1': {'degenerate': s1_deg, 'r0': s1_r0, 'r1': s1_r1, 'shr': s1_s},
        'sigma0': {'degenerate': s0_deg, 'r0': s0_r0, 'r1': s0_r1, 'shr': s0_s},
        'Sigma0': {'degenerate': S0_deg, 'vals': S0_vals},
        'Sigma1': {'degenerate': S1_deg, 'vals': S1_vals},
    }

# ============================================================
# Find MULTIPLE M[0] candidates
# ============================================================

def find_multiple_m0(N, count=3, fill=None):
    """Find up to `count` distinct M[0] values with da[56]=0 for width N.
    Returns list of (m0, state1, state2, W1, W2) tuples."""
    sha = MiniSHA256(N)
    MASK = sha.MASK
    MSB  = sha.MSB
    max_scan = 1 << N

    if fill is None:
        fill = MASK  # all-ones padding

    results = []
    K = sha.K
    IV = sha.IV
    rS0 = sha.r_Sig0
    rS1 = sha.r_Sig1
    rs0 = sha.r_sig0
    ss0 = sha.s_sig0
    rs1 = sha.r_sig1
    ss1 = sha.s_sig1

    for m0 in range(max_scan):
        # Build M1 and M2
        M1 = [m0] + [fill] * 15
        M2 = [m0 ^ MSB] + [fill] * 8 + [fill ^ MSB] + [fill] * 6

        # Inline compression for M1 -- just check a register
        W1 = list(M1) + [0] * 48
        for i in range(16, 57):
            x = W1[i-2]
            s1v = (((x >> rs1[0]) | (x << (N - rs1[0]))) & MASK) ^ \
                  (((x >> rs1[1]) | (x << (N - rs1[1]))) & MASK) ^ \
                  ((x >> ss1) & MASK)
            x = W1[i-15]
            s0v = (((x >> rs0[0]) | (x << (N - rs0[0]))) & MASK) ^ \
                  (((x >> rs0[1]) | (x << (N - rs0[1]))) & MASK) ^ \
                  ((x >> ss0) & MASK)
            W1[i] = (s1v + W1[i-7] + s0v + W1[i-16]) & MASK

        a, b, c, d, e, f, g, h = IV
        for i in range(57):
            S1 = (((e >> rS1[0]) | (e << (N - rS1[0]))) & MASK) ^ \
                 (((e >> rS1[1]) | (e << (N - rS1[1]))) & MASK) ^ \
                 (((e >> rS1[2]) | (e << (N - rS1[2]))) & MASK)
            chv = ((e & f) ^ ((~e) & g)) & MASK
            T1 = (h + S1 + chv + K[i] + W1[i]) & MASK
            S0 = (((a >> rS0[0]) | (a << (N - rS0[0]))) & MASK) ^ \
                 (((a >> rS0[1]) | (a << (N - rS0[1]))) & MASK) ^ \
                 (((a >> rS0[2]) | (a << (N - rS0[2]))) & MASK)
            T2 = (S0 + ((a & b) ^ (a & c) ^ (b & c))) & MASK
            h = g; g = f; f = e; e = (d + T1) & MASK
            d = c; c = b; b = a; a = (T1 + T2) & MASK
        a1 = a

        # Inline compression for M2
        W2 = list(M2) + [0] * 48
        for i in range(16, 57):
            x = W2[i-2]
            s1v = (((x >> rs1[0]) | (x << (N - rs1[0]))) & MASK) ^ \
                  (((x >> rs1[1]) | (x << (N - rs1[1]))) & MASK) ^ \
                  ((x >> ss1) & MASK)
            x = W2[i-15]
            s0v = (((x >> rs0[0]) | (x << (N - rs0[0]))) & MASK) ^ \
                  (((x >> rs0[1]) | (x << (N - rs0[1]))) & MASK) ^ \
                  ((x >> ss0) & MASK)
            W2[i] = (s1v + W2[i-7] + s0v + W2[i-16]) & MASK

        a, b, c, d, e, f, g, h = IV
        for i in range(57):
            S1 = (((e >> rS1[0]) | (e << (N - rS1[0]))) & MASK) ^ \
                 (((e >> rS1[1]) | (e << (N - rS1[1]))) & MASK) ^ \
                 (((e >> rS1[2]) | (e << (N - rS1[2]))) & MASK)
            chv = ((e & f) ^ ((~e) & g)) & MASK
            T1 = (h + S1 + chv + K[i] + W2[i]) & MASK
            S0 = (((a >> rS0[0]) | (a << (N - rS0[0]))) & MASK) ^ \
                 (((a >> rS0[1]) | (a << (N - rS0[1]))) & MASK) ^ \
                 (((a >> rS0[2]) | (a << (N - rS0[2]))) & MASK)
            T2 = (S0 + ((a & b) ^ (a & c) ^ (b & c))) & MASK
            h = g; g = f; f = e; e = (d + T1) & MASK
            d = c; c = b; b = a; a = (T1 + T2) & MASK
        a2 = a

        if a1 == a2:
            s1, W1f = sha.compress(M1)
            s2, W2f = sha.compress(M2)
            results.append((m0, s1, s2, W1f, W2f))
            if len(results) >= count:
                return results

    return results


# ============================================================
# Single SAT test (extracted from script 50 with enhancements)
# ============================================================

def run_sat_test(N, m0, s1, s2, W1, W2, timeout=600, label=""):
    """Encode and solve sr=60 for a specific N and M[0]. Return result dict."""
    sha = MiniSHA256(N)
    ops_params = {
        'r_Sig0': sha.r_Sig0, 'r_Sig1': sha.r_Sig1,
        'r_sig0': sha.r_sig0, 's_sig0': sha.s_sig0,
        'r_sig1': sha.r_sig1, 's_sig1': sha.s_sig1,
    }
    K_trunc = [k & sha.MASK for k in K32]

    t0 = time.time()
    cnf = MiniCNFBuilder(N)

    # Initial states as constants
    st1 = tuple(cnf.const_word(v) for v in s1)
    st2 = tuple(cnf.const_word(v) for v in s2)

    # 4 free schedule words for each message
    n_free = 4
    w1_free = [cnf.free_word(f"W1_{57+i}") for i in range(n_free)]
    w2_free = [cnf.free_word(f"W2_{57+i}") for i in range(n_free)]

    # Derived schedule words: W[61], W[62], W[63]
    w1_61 = cnf.add_word(
        cnf.add_word(
            cnf.sigma1_w(w1_free[2], ops_params['r_sig1'], ops_params['s_sig1']),
            cnf.const_word(W1[54])),
        cnf.add_word(cnf.const_word(sha.sigma0(W1[46])), cnf.const_word(W1[45])))
    w2_61 = cnf.add_word(
        cnf.add_word(
            cnf.sigma1_w(w2_free[2], ops_params['r_sig1'], ops_params['s_sig1']),
            cnf.const_word(W2[54])),
        cnf.add_word(cnf.const_word(sha.sigma0(W2[46])), cnf.const_word(W2[45])))

    w1_62 = cnf.add_word(
        cnf.add_word(
            cnf.sigma1_w(w1_free[3], ops_params['r_sig1'], ops_params['s_sig1']),
            cnf.const_word(W1[55])),
        cnf.add_word(cnf.const_word(sha.sigma0(W1[47])), cnf.const_word(W1[46])))
    w2_62 = cnf.add_word(
        cnf.add_word(
            cnf.sigma1_w(w2_free[3], ops_params['r_sig1'], ops_params['s_sig1']),
            cnf.const_word(W2[55])),
        cnf.add_word(cnf.const_word(sha.sigma0(W2[47])), cnf.const_word(W2[46])))

    w1_63 = cnf.add_word(
        cnf.add_word(
            cnf.sigma1_w(w1_61, ops_params['r_sig1'], ops_params['s_sig1']),
            cnf.const_word(W1[56])),
        cnf.add_word(cnf.const_word(sha.sigma0(W1[48])), cnf.const_word(W1[47])))
    w2_63 = cnf.add_word(
        cnf.add_word(
            cnf.sigma1_w(w2_61, ops_params['r_sig1'], ops_params['s_sig1']),
            cnf.const_word(W2[56])),
        cnf.add_word(cnf.const_word(sha.sigma0(W2[48])), cnf.const_word(W2[47])))

    W1_sched = w1_free + [w1_61, w1_62, w1_63]
    W2_sched = w2_free + [w2_61, w2_62, w2_63]

    for i in range(7):
        st1 = cnf.sha256_round(st1, K_trunc[57 + i], W1_sched[i], ops_params)
    for i in range(7):
        st2 = cnf.sha256_round(st2, K_trunc[57 + i], W2_sched[i], ops_params)

    for i in range(8):
        cnf.eq_word(st1[i], st2[i])

    encode_time = time.time() - t0

    # Check trivially UNSAT
    has_empty = any(len(c) == 0 for c in cnf.clauses)
    if has_empty:
        return {
            'N': N, 'result': 'UNSAT_TRIVIAL', 'time': encode_time,
            'vars': cnf.next_var - 1, 'clauses': len(cnf.clauses),
            'm0': m0, 'encode_time': encode_time, 'label': label,
        }

    # Write DIMACS
    tmpdir = tempfile.mkdtemp()
    dimacs_path = os.path.join(tmpdir, f"sr60_N{N}_m{m0}.cnf")
    n_vars, n_clauses = cnf.write_dimacs(dimacs_path)

    # Run Kissat
    t0 = time.time()
    try:
        proc = subprocess.run(
            ['kissat', '--quiet', dimacs_path],
            capture_output=True, text=True, timeout=timeout
        )
        solve_time = time.time() - t0
        rc = proc.returncode
        if rc == 10:
            result = 'SAT'
        elif rc == 20:
            result = 'UNSAT'
        else:
            result = f'UNKNOWN(rc={rc})'
    except subprocess.TimeoutExpired:
        solve_time = timeout
        result = 'TIMEOUT'

    try:
        os.unlink(dimacs_path)
        os.rmdir(tmpdir)
    except:
        pass

    return {
        'N': N, 'result': result, 'time': solve_time,
        'vars': n_vars, 'clauses': n_clauses, 'm0': m0,
        'encode_time': encode_time, 'label': label,
    }


# ============================================================
# Main sweep
# ============================================================

def main():
    TIMEOUT = 600

    print("=" * 72)
    print("  Script 59: Comprehensive reduced-width sr=60 sweep")
    print("  Scope: MSB kernel, all-ones padding")
    print(f"  Timeout per test: {TIMEOUT}s")
    print("=" * 72)
    sys.stdout.flush()

    # ---- Phase 0: Degeneracy survey for N=8..16 ----
    print("\n--- Phase 0: Rotation degeneracy survey ---\n")
    print(f"{'N':>4}  {'sig1_deg':>8}  sig1_rots    {'sig0_deg':>8}  sig0_rots    "
          f"{'Sig0_deg':>8}  Sig0_rots       {'Sig1_deg':>8}  Sig1_rots")
    print("-" * 110)
    sys.stdout.flush()

    degenerate_ns = []
    for N in range(8, 17):
        dr = full_degeneracy_report(N)
        s1 = dr['sigma1']
        s0 = dr['sigma0']
        S0 = dr['Sigma0']
        S1 = dr['Sigma1']
        tag = " ***DEGENERATE***" if dr['any_degenerate'] else ""
        print(f"{N:>4}  {'YES' if s1['degenerate'] else 'no':>8}  "
              f"rot({s1['r0']},{s1['r1']}) shr {s1['shr']}  "
              f"{'YES' if s0['degenerate'] else 'no':>8}  "
              f"rot({s0['r0']},{s0['r1']}) shr {s0['shr']}  "
              f"{'YES' if S0['degenerate'] else 'no':>8}  "
              f"rot{tuple(S0['vals'])}  "
              f"{'YES' if S1['degenerate'] else 'no':>8}  "
              f"rot{tuple(S1['vals'])}{tag}")
        if dr['any_degenerate']:
            degenerate_ns.append(N)
    sys.stdout.flush()

    if degenerate_ns:
        print(f"\nDegenerate word sizes in [8..16]: {degenerate_ns}")
    else:
        print(f"\nNo degenerate word sizes in [8..16].")
    sys.stdout.flush()

    # ---- Phase 1: New width tests N=13,14,15,16 ----
    print("\n\n--- Phase 1: New width tests N=13,14,15,16 ---\n")
    sys.stdout.flush()

    # Fill values to try if all-ones doesn't produce a candidate
    FILL_OPTIONS = None  # will be set per-N below

    new_results = []
    for N in [13, 14, 15, 16]:
        deg = full_degeneracy_report(N)
        deg_tag = " [DEGENERATE]" if deg['any_degenerate'] else ""
        print(f"\n{'='*60}")
        print(f"  N={N}{deg_tag}")
        print(f"{'='*60}")
        sys.stdout.flush()

        sha = MiniSHA256(N)
        MASK = sha.MASK
        MSB  = sha.MSB
        scan_limit = 1 << N
        expected_hits = scan_limit / (1 << (N - 1))  # rough estimate: p ~ 2^(-N+1)
        print(f"  Scanning {scan_limit} M[0] values (expect ~{expected_hits:.0f} da[56]=0 hits)")

        # Try multiple fill values
        fill_values = [MASK, 0, MASK >> 1, MSB, 0x55 & MASK, 0xAA & MASK,
                       0x33 & MASK, 0xCC & MASK, 0x0F & MASK, 0xF0 & MASK]
        candidates = []
        fill_used = None
        t0 = time.time()
        for fv in fill_values:
            print(f"  Trying fill={fv:#x}...", end="", flush=True)
            cands = find_multiple_m0(N, count=1, fill=fv)
            if cands:
                candidates = cands
                fill_used = fv
                print(f" FOUND M[0]={cands[0][0]:#x}")
                break
            else:
                print(f" no hits")
        scan_time = time.time() - t0
        sys.stdout.flush()

        if not candidates:
            print(f"  NO M[0] found with da[56]=0 across {len(fill_values)} fills ({scan_time:.1f}s)")
            new_results.append({
                'N': N, 'result': 'NO_M0', 'time': scan_time,
                'vars': 0, 'clauses': 0, 'm0': None,
                'encode_time': 0, 'label': f'N={N}',
                'degenerate': deg['any_degenerate'],
                'fill': None,
            })
            sys.stdout.flush()
            continue

        m0, s1, s2, W1, W2 = candidates[0]
        print(f"  Found M[0]={m0:#x} with fill={fill_used:#x} (scan: {scan_time:.1f}s)")
        print(f"  State1 a={s1[0]:#x}  State2 a={s2[0]:#x}")
        diffs = sum(1 for i in range(8) if s1[i] != s2[i])
        print(f"  State diffs: {diffs}/8")
        sys.stdout.flush()

        print(f"  Encoding + solving sr=60 (timeout {TIMEOUT}s)...")
        sys.stdout.flush()
        r = run_sat_test(N, m0, s1, s2, W1, W2, timeout=TIMEOUT, label=f'N={N}')
        r['degenerate'] = deg['any_degenerate']
        r['fill'] = fill_used
        new_results.append(r)
        print(f"  Result: {r['result']}  Vars: {r['vars']}  Clauses: {r['clauses']}  "
              f"Encode: {r['encode_time']:.1f}s  Solve: {r['time']:.1f}s")
        sys.stdout.flush()

    # ---- Phase 2: Multi-candidate tests for N=8,10,12 ----
    print("\n\n--- Phase 2: Multi-candidate tests (N=8,10,12) ---\n")
    sys.stdout.flush()

    multi_results = []
    for N in [8, 10, 12]:
        print(f"\n  N={N}: finding M[0] candidates across multiple fills...")
        sys.stdout.flush()

        sha = MiniSHA256(N)
        MASK = sha.MASK
        MSB  = sha.MSB

        # Collect candidates from multiple fills to get diversity
        all_candidates = []
        fills_tried = [MASK, 0, MASK >> 1, MSB, 0x55 & MASK, 0xAA & MASK]
        for fv in fills_tried:
            cands = find_multiple_m0(N, count=1, fill=fv)
            for c in cands:
                # c = (m0, s1, s2, W1, W2), tag with fill
                all_candidates.append((c, fv))
            if len(all_candidates) >= 3:
                break

        print(f"  Found {len(all_candidates)} candidates across fills")
        if not all_candidates:
            print(f"  ERROR: no candidates found for N={N}")
            continue

        for idx, ((m0, s1, s2, W1, W2), fv) in enumerate(all_candidates[:3]):
            label = f"N={N} cand#{idx} M[0]={m0:#x} fill={fv:#x}"
            print(f"\n  Testing {label}...")
            sys.stdout.flush()

            # Use shorter timeout for multi-candidate (we already know N=8,10 are fast)
            to = min(TIMEOUT, 300 if N <= 10 else TIMEOUT)
            r = run_sat_test(N, m0, s1, s2, W1, W2, timeout=to, label=label)
            r['degenerate'] = False  # N=8,10,12 are not degenerate
            r['candidate_idx'] = idx
            r['fill'] = fv
            multi_results.append(r)
            print(f"    Result: {r['result']}  Vars: {r['vars']}  Clauses: {r['clauses']}  "
                  f"Solve: {r['time']:.1f}s")
            sys.stdout.flush()

    # ============================================================
    # Summary tables
    # ============================================================

    print(f"\n\n{'='*80}")
    print(f"  SUMMARY: Comprehensive sr=60 width sweep")
    print(f"  Scope: MSB kernel, all-ones padding")
    print(f"{'='*80}")

    # Table 1: Primary results (one per N, including known)
    known = [
        {'N': 8,  'result': 'SAT',   'time': 4.2,   'vars': 0, 'clauses': 0, 'm0': None, 'degenerate': False, 'encode_time': 0, 'label': 'known'},
        {'N': 9,  'result': 'UNSAT', 'time': 0.25,  'vars': 0, 'clauses': 0, 'm0': None, 'degenerate': True,  'encode_time': 0, 'label': 'known'},
        {'N': 10, 'result': 'SAT',   'time': 70.6,  'vars': 0, 'clauses': 0, 'm0': None, 'degenerate': False, 'encode_time': 0, 'label': 'known'},
        {'N': 11, 'result': 'SAT',   'time': 150.5, 'vars': 0, 'clauses': 0, 'm0': None, 'degenerate': False, 'encode_time': 0, 'label': 'known'},
        {'N': 12, 'result': 'SAT',   'time': 559.6, 'vars': 0, 'clauses': 0, 'm0': None, 'degenerate': False, 'encode_time': 0, 'label': 'known'},
    ]

    all_primary = known + new_results
    all_primary.sort(key=lambda r: r['N'])

    print(f"\nTable 1: Primary sr=60 results by word width")
    print(f"{'N':>4} {'Degen?':>7} {'M[0]':>10} {'Vars':>8} {'Clauses':>10} "
          f"{'Result':>12} {'Solve(s)':>10} {'Encode(s)':>10} {'Note':>12}")
    print(f"{'-'*4} {'-'*7} {'-'*10} {'-'*8} {'-'*10} {'-'*12} {'-'*10} {'-'*10} {'-'*12}")
    for r in all_primary:
        m0_str = f"{r['m0']:#x}" if r.get('m0') is not None else "N/A"
        deg_str = "YES" if r.get('degenerate') else "no"
        enc_str = f"{r.get('encode_time', 0):.1f}"
        note = "known" if r.get('label') == 'known' else "new"
        print(f"{r['N']:>4} {deg_str:>7} {m0_str:>10} {r['vars']:>8} {r['clauses']:>10} "
              f"{r['result']:>12} {r['time']:>10.1f} {enc_str:>10} {note:>12}")
    sys.stdout.flush()

    # Table 2: Multi-candidate results
    if multi_results:
        print(f"\nTable 2: Multi-candidate tests (universality check)")
        print(f"{'N':>4} {'Cand#':>6} {'M[0]':>10} {'Vars':>8} {'Clauses':>10} "
              f"{'Result':>12} {'Solve(s)':>10}")
        print(f"{'-'*4} {'-'*6} {'-'*10} {'-'*8} {'-'*10} {'-'*12} {'-'*10}")
        for r in multi_results:
            m0_str = f"{r['m0']:#x}" if r.get('m0') is not None else "N/A"
            print(f"{r['N']:>4} {r.get('candidate_idx', 0):>6} {m0_str:>10} "
                  f"{r['vars']:>8} {r['clauses']:>10} "
                  f"{r['result']:>12} {r['time']:>10.1f}")
        sys.stdout.flush()

    # ---- Interpretation ----
    print(f"\n{'='*80}")
    print("  INTERPRETATION")
    print(f"{'='*80}")

    # Count non-degenerate SAT/UNSAT
    non_deg = [r for r in all_primary if not r.get('degenerate')]
    nd_sat = [r for r in non_deg if r['result'] == 'SAT']
    nd_unsat = [r for r in non_deg if 'UNSAT' in r['result']]
    nd_timeout = [r for r in non_deg if r['result'] == 'TIMEOUT']
    nd_nom0 = [r for r in non_deg if r['result'] == 'NO_M0']

    deg_all = [r for r in all_primary if r.get('degenerate')]

    print(f"\n  Non-degenerate widths tested: {sorted([r['N'] for r in non_deg])}")
    print(f"    SAT:     {sorted([r['N'] for r in nd_sat])}")
    print(f"    UNSAT:   {sorted([r['N'] for r in nd_unsat])}")
    print(f"    TIMEOUT: {sorted([r['N'] for r in nd_timeout])}")
    print(f"    NO_M0:   {sorted([r['N'] for r in nd_nom0])}")
    print(f"  Degenerate widths: {sorted([r['N'] for r in deg_all])}")

    if nd_unsat:
        print(f"\n  FINDING: Non-degenerate UNSAT detected at N={sorted([r['N'] for r in nd_unsat])}")
        print(f"  => There is a component beyond carry length.")
    elif nd_sat and not nd_unsat and not nd_timeout:
        print(f"\n  FINDING: ALL non-degenerate widths are SAT.")
        print(f"  => Confirms carry-length-only barrier. N=9 UNSAT was rotation-degeneracy artifact.")
        print(f"  => Extrapolation to N=32: sr=60 barrier is carry-chain + precision dependent.")
    elif nd_timeout:
        print(f"\n  PARTIAL: Some non-degenerate widths timed out.")
        print(f"  => Cannot fully confirm hypothesis. Need longer timeout or better encoding.")
    else:
        print(f"\n  Inconclusive.")

    # Multi-candidate analysis
    if multi_results:
        by_n = {}
        for r in multi_results:
            by_n.setdefault(r['N'], []).append(r['result'])
        print(f"\n  Multi-candidate results by N:")
        for n, results in sorted(by_n.items()):
            all_same = len(set(results)) == 1
            print(f"    N={n}: {results}  {'(universal)' if all_same else '(CANDIDATE-DEPENDENT!)'}")
        if all(len(set(rs)) == 1 for rs in by_n.values()):
            print(f"  => Result is candidate-independent (universal for each N).")
        else:
            print(f"  => CANDIDATE DEPENDENCE detected!")

    # Growth rate analysis
    sat_timed = [(r['N'], r['time']) for r in all_primary
                 if r['result'] == 'SAT' and r['time'] > 0 and r.get('label') != 'known']
    if len(sat_timed) >= 2:
        print(f"\n  Solve time growth (new results):")
        for n, t in sorted(sat_timed):
            print(f"    N={n}: {t:.1f}s")

    print()
    sys.stdout.flush()


if __name__ == '__main__':
    main()
