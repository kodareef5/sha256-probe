#!/usr/bin/env python3
"""
Script 57: UNSAT Core Atlas -- Compare UNSAT proof statistics across
known-dead sr=60 partitions.

We have 224 constant-folded partitions of sr=60 (fixing 4 MSBs of both
W1[57] and W2[57]) that are provably UNSAT. The question: do they all
die for the SAME structural reason, or do different MSB regions fail via
different mechanisms?

METHOD:
  For 5 diverse known-UNSAT cells, encode sr=60 with the top 4 bits of
  W1[57] and W2[57] baked in as constants. Run kissat (verbose mode) and
  parse: conflicts, decisions, propagations, variables eliminated during
  preprocessing, and wall-clock time. Compare across cells.

  If all cells show nearly identical conflict counts and solve times, the
  UNSAT reason is structural (same proof skeleton). If they vary widely,
  different regions die for different reasons (different proof cores).

Cells tested (W1_msb, W2_msb as 4-bit values 0-15):
  (0, 0)   -- both zero nibbles
  (5, 5)   -- matched mid-range
  (10,10)  -- matched upper-mid
  (15, 0)  -- maximally asymmetric
  (3, 12)  -- arbitrary diverse pair
"""

import sys
import os
import time
import subprocess
import re

sys.path.insert(0, '/root/bounties/sha256_scripts')
enc = __import__('13_custom_cnf_encoder')

CNF_FILE = '/tmp/sr60_unsat_core_atlas.cnf'
KISSAT_TIMEOUT = 60  # seconds per cell


def build_sr60_fixed_4msb(w1_msb4, w2_msb4):
    """
    Build sr=60 CNF with the top 4 bits of W1[57] and W2[57] fixed.

    w1_msb4, w2_msb4: integers 0-15, the 4 MSB nibble values.
    Bits 31,30,29,28 are fixed; bits 27..0 are free SAT variables.

    Returns: (CNFBuilder, n_vars, n_clauses)
    """
    cnf = enc.CNFBuilder()

    m0 = 0x17149975
    M1 = [m0] + [0xffffffff] * 15
    M2 = M1.copy()
    M2[0] ^= 0x80000000
    M2[9] ^= 0x80000000

    state1, W1_pre = enc.precompute_state(M1)
    state2, W2_pre = enc.precompute_state(M2)

    s1 = tuple(cnf.const_word(v) for v in state1)
    s2 = tuple(cnf.const_word(v) for v in state2)

    def make_w57_word(name, msb4_val):
        """Top 4 bits fixed from msb4_val, bottom 28 bits free."""
        bits = []
        for i in range(32):
            if i >= 28:  # bits 28,29,30,31 are the top 4
                bit_pos_in_nibble = i - 28  # 0,1,2,3
                bit_val = bool((msb4_val >> bit_pos_in_nibble) & 1)
                bits.append(cnf._const(bit_val))
            else:
                v = cnf.new_var()
                cnf.free_var_names[v] = f"{name}[{i}]"
                bits.append(v)
        return bits

    w1_57 = make_w57_word("W1_57", w1_msb4)
    w2_57 = make_w57_word("W2_57", w2_msb4)

    # Remaining free words
    w1_58 = cnf.free_word('W1_58')
    w2_58 = cnf.free_word('W2_58')
    w1_59 = cnf.free_word('W1_59')
    w2_59 = cnf.free_word('W2_59')
    w1_60 = cnf.free_word('W1_60')
    w2_60 = cnf.free_word('W2_60')

    W1 = [w1_57, w1_58, w1_59, w1_60]
    W2 = [w2_57, w2_58, w2_59, w2_60]

    def build_derived(sched, pre):
        # W[61] = sigma1(W[59]) + W[54] + sigma0(W[46]) + W[45]
        w61 = cnf.add_word(
            cnf.add_word(cnf.sigma1_w(sched[2]), cnf.const_word(pre[54])),
            cnf.add_word(cnf.const_word(enc.sigma0_py(pre[46])),
                         cnf.const_word(pre[45])))
        sched.append(w61)
        # W[62] = sigma1(W[60]) + W[55] + sigma0(W[47]) + W[46]
        w62 = cnf.add_word(
            cnf.add_word(cnf.sigma1_w(sched[3]), cnf.const_word(pre[55])),
            cnf.add_word(cnf.const_word(enc.sigma0_py(pre[47])),
                         cnf.const_word(pre[46])))
        sched.append(w62)
        # W[63] = sigma1(W[61]) + W[56] + sigma0(W[48]) + W[47]
        w63 = cnf.add_word(
            cnf.add_word(cnf.sigma1_w(sched[4]), cnf.const_word(pre[56])),
            cnf.add_word(cnf.const_word(enc.sigma0_py(pre[48])),
                         cnf.const_word(pre[47])))
        sched.append(w63)

    build_derived(W1, W1_pre)
    build_derived(W2, W2_pre)

    # 7 rounds for both messages
    st1, st2 = s1, s2
    for i in range(7):
        st1 = cnf.sha256_round_correct(st1, enc.K[57 + i], W1[i])
        st2 = cnf.sha256_round_correct(st2, enc.K[57 + i], W2[i])

    # Collision constraints
    for i in range(8):
        cnf.eq_word(st1[i], st2[i])

    n_vars, n_clauses = cnf.write_dimacs(CNF_FILE)
    return cnf, n_vars, n_clauses


def parse_kissat_stats(stdout):
    """
    Parse kissat verbose output for key statistics.
    Returns dict with: conflicts, decisions, propagations, time,
    variables_eliminated, result.
    """
    stats = {
        'conflicts': None,
        'decisions': None,
        'propagations': None,
        'time': None,
        'variables_original': None,
        'variables_remaining': None,
        'variables_eliminated': None,
        'clauses_original': None,
        'clauses_irredundant': None,
        'result': 'UNKNOWN',
    }

    for line in stdout.split('\n'):
        line = line.strip()

        # Result line
        if line.startswith('s UNSATISFIABLE'):
            stats['result'] = 'UNSAT'
        elif line.startswith('s SATISFIABLE'):
            stats['result'] = 'SAT'

        # Statistics section parsing
        # Format: "c conflicts:              12345          678.90 per second"
        m = re.match(r'^c\s+conflicts:\s+(\d+)', line)
        if m:
            stats['conflicts'] = int(m.group(1))

        m = re.match(r'^c\s+decisions:\s+(\d+)', line)
        if m:
            stats['decisions'] = int(m.group(1))

        m = re.match(r'^c\s+propagations:\s+(\d+)', line)
        if m:
            stats['propagations'] = int(m.group(1))

        # process-time format: "c process-time:     5s     4.55 seconds"
        m = re.match(r'^c\s+process-time:\s+\S+\s+([\d.]+)\s+seconds', line)
        if m:
            stats['time'] = float(m.group(1))
        elif re.match(r'^c\s+process-time:', line):
            # Fallback: grab any float on the line
            floats = re.findall(r'([\d.]+)', line)
            if floats:
                stats['time'] = float(floats[-1])

        # Preprocessing: "c eliminated:             1234  12.3% of original"
        m = re.match(r'^c\s+eliminated:\s+(\d+)', line)
        if m:
            stats['variables_eliminated'] = int(m.group(1))

        # "c substituted:            567   5.6% ..."
        m = re.match(r'^c\s+substituted:\s+(\d+)', line)
        if m:
            stats['variables_substituted'] = int(m.group(1))

        # Variables/clauses from header parsing
        # "c   original:             9876  100.00% of original"
        # Sometimes shown as part of summary
        m = re.match(r'^c\s+variables:\s+(\d+)', line)
        if m:
            stats['variables_original'] = int(m.group(1))

        m = re.match(r'^c\s+remaining:\s+(\d+)', line)
        if m:
            stats['variables_remaining'] = int(m.group(1))

        m = re.match(r'^c\s+clauses_original:\s+(\d+)', line)
        if m:
            stats['clauses_original'] = int(m.group(1))

        m = re.match(r'^c\s+irredundant:\s+(\d+)', line)
        if m:
            stats['clauses_irredundant'] = int(m.group(1))

    return stats


def run_kissat_verbose(cnf_file, timeout):
    """Run kissat in verbose mode (no -q) and return parsed stats + raw output."""
    t0 = time.time()
    try:
        r = subprocess.run(
            ["kissat", cnf_file],
            capture_output=True, text=True,
            timeout=timeout + 10
        )
        wall_time = time.time() - t0
        stats = parse_kissat_stats(r.stdout)
        if stats['time'] is None:
            stats['time'] = wall_time
        return stats, r.stdout, r.returncode
    except subprocess.TimeoutExpired:
        return {'result': 'TIMEOUT', 'time': time.time() - t0,
                'conflicts': None, 'decisions': None,
                'propagations': None, 'variables_eliminated': None}, '', -1


def main():
    # 5 diverse test cells: (W1_msb4, W2_msb4)
    test_cells = [
        (0,  0),   # both zero nibbles
        (5,  5),   # matched mid-range
        (10, 10),  # matched upper-mid
        (15, 0),   # maximally asymmetric
        (3,  12),  # arbitrary diverse pair
    ]

    print("=" * 78)
    print("Script 57: UNSAT Core Atlas -- sr=60 partition comparison")
    print("=" * 78)
    print()
    print(f"Fixing top 4 MSBs of W1[57] and W2[57] (224 total partitions, all UNSAT).")
    print(f"Testing 5 diverse cells to compare UNSAT proof characteristics.")
    print(f"Kissat timeout: {KISSAT_TIMEOUT}s per cell.")
    print()

    results = []

    for idx, (w1m, w2m) in enumerate(test_cells):
        label = f"W1={w1m:X},W2={w2m:X}"
        print(f"--- Cell {idx+1}/5: {label} ---")

        # Encode
        t_enc_start = time.time()
        cnf, n_vars, n_clauses = build_sr60_fixed_4msb(w1m, w2m)
        t_enc = time.time() - t_enc_start
        print(f"  Encoded: {n_vars} vars, {n_clauses} clauses ({t_enc:.2f}s)")
        print(f"  Encoder const_folds: {cnf.stats['const_fold']}")

        # Solve
        stats, raw_out, rc = run_kissat_verbose(CNF_FILE, KISSAT_TIMEOUT)
        print(f"  Result: {stats['result']}")
        print(f"  Time: {stats['time']:.3f}s")
        print(f"  Conflicts: {stats['conflicts']}")
        print(f"  Decisions: {stats['decisions']}")
        print(f"  Propagations: {stats['propagations']}")
        if stats.get('variables_eliminated') is not None:
            print(f"  Vars eliminated: {stats['variables_eliminated']}")
        if stats.get('variables_substituted') is not None:
            print(f"  Vars substituted: {stats.get('variables_substituted')}")
        print()

        results.append({
            'label': label,
            'w1_msb': w1m,
            'w2_msb': w2m,
            'n_vars': n_vars,
            'n_clauses': n_clauses,
            'encode_time': t_enc,
            'const_folds': cnf.stats['const_fold'],
            **stats,
        })

    # === Comparison Table ===
    print()
    print("=" * 78)
    print("COMPARISON TABLE")
    print("=" * 78)
    print()

    # Header
    hdr = f"{'Cell':<12} {'Result':<7} {'Time(s)':>8} {'Conflicts':>10} {'Decisions':>10} {'Propag':>12} {'VarsElim':>9} {'Vars':>7} {'Clauses':>8}"
    print(hdr)
    print("-" * len(hdr))

    for r in results:
        conflicts_s = str(r['conflicts']) if r['conflicts'] is not None else '-'
        decisions_s = str(r['decisions']) if r['decisions'] is not None else '-'
        propag_s = str(r['propagations']) if r['propagations'] is not None else '-'
        elim_s = str(r.get('variables_eliminated', '-')) if r.get('variables_eliminated') is not None else '-'
        time_s = f"{r['time']:.3f}" if r['time'] is not None else '-'
        print(f"{r['label']:<12} {r['result']:<7} {time_s:>8} {conflicts_s:>10} {decisions_s:>10} {propag_s:>12} {elim_s:>9} {r['n_vars']:>7} {r['n_clauses']:>8}")

    # === Analysis ===
    print()
    print("=" * 78)
    print("ANALYSIS")
    print("=" * 78)
    print()

    unsat_results = [r for r in results if r['result'] == 'UNSAT']

    if len(unsat_results) < 2:
        print("Insufficient UNSAT results for comparison.")
        return

    times = [r['time'] for r in unsat_results if r['time'] is not None]
    conflicts = [r['conflicts'] for r in unsat_results if r['conflicts'] is not None]
    decisions = [r['decisions'] for r in unsat_results if r['decisions'] is not None]
    propags = [r['propagations'] for r in unsat_results if r['propagations'] is not None]

    def spread_summary(vals, name):
        if not vals:
            return
        mn, mx = min(vals), max(vals)
        avg = sum(vals) / len(vals)
        if avg > 0:
            ratio = mx / mn if mn > 0 else float('inf')
            cv = (sum((v - avg)**2 for v in vals) / len(vals)) ** 0.5 / avg
            print(f"  {name + ':':<20} min={mn:>10}, max={mx:>10}, avg={avg:>10.1f}, max/min={ratio:>6.2f}x, CV={cv:.3f}")
        else:
            print(f"  {name + ':':<20} all zero")

    spread_summary(times, "Time")
    spread_summary(conflicts, "Conflicts")
    spread_summary(decisions, "Decisions")
    spread_summary(propags, "Propagations")

    print()

    # Interpret
    if conflicts:
        mn_c, mx_c = min(conflicts), max(conflicts)
        if mn_c > 0:
            ratio = mx_c / mn_c
        else:
            ratio = float('inf')

        if ratio < 1.5:
            print("CONCLUSION: All cells show SIMILAR conflict profiles (max/min < 1.5x).")
            print("  => The UNSAT proof has a UNIFORM structural skeleton.")
            print("  => All 224 partitions likely die for the SAME reason.")
            print("  => A single UNSAT core characterization would cover the entire space.")
        elif ratio < 3.0:
            print("CONCLUSION: MODERATE variation in conflict profiles (1.5x-3x range).")
            print("  => The proof structure has some regional variation.")
            print("  => Different MSB regions may encounter the contradiction at")
            print("     different depths, but through the same fundamental mechanism.")
        else:
            print("CONCLUSION: WIDE variation in conflict profiles (>3x range).")
            print("  => Different MSB regions die for DIFFERENT reasons.")
            print("  => Multiple distinct UNSAT cores exist in the search space.")
            print("  => Some regions might be closer to satisfiability than others.")

    # Additional: check if any solved during preprocessing (0 conflicts)
    preprocess_kills = [r for r in unsat_results if r['conflicts'] is not None and r['conflicts'] == 0]
    if preprocess_kills:
        print()
        print(f"NOTE: {len(preprocess_kills)} cell(s) proved UNSAT during preprocessing alone (0 conflicts).")
        print("  These cells contain contradictions detectable by unit propagation + subsumption.")

    search_kills = [r for r in unsat_results if r['conflicts'] is not None and r['conflicts'] > 0]
    if search_kills:
        print()
        print(f"NOTE: {len(search_kills)} cell(s) required CDCL search ({min(c for c in conflicts if c > 0)}-{max(conflicts)} conflicts).")

    print()
    print("Done.")


if __name__ == "__main__":
    main()
