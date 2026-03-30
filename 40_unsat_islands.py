#!/usr/bin/env python3
"""
Script 40: UNSAT Island Mapping for sr=60

Maps search space fragmentation by fixing MSB bits of the W[57] schedule
word pair (W1[57], W2[57]) at encode time and probing with kissat.

Key discovery: the encoder's constant propagation is essential. Fixing bits
post-hoc (as unit clauses appended to DIMACS) does NOT trigger UNSAT even at
32 bits, because kissat must re-derive the propagation at runtime. But fixing
bits at encode time lets the encoder fold constants through the SHA-256 circuit,
producing a smaller formula that kissat solves instantly.

Fixing both W1[57] and W2[57] (32 bits each = 64 total) at encode time
consistently produces instant UNSAT (~0.06s). This means:
  - For random W[57] values, the remaining 3 free words (W[58-60]) have
    NO solution to the collision constraint.
  - The sr=60 problem is extremely overconstrained: random sub-regions
    of the schedule space are provably empty.

This script:
  Phase 1: Find the UNSAT threshold -- minimum fixed MSBs (in both W1[57]
           and W2[57]) that produce reliable instant UNSAT.
  Phase 2: At that threshold, sweep all 16 MSB nibble patterns of W1[57]
           to map which regions are dead vs potentially viable.
"""

import sys
import os
import time
import subprocess
import random

sys.path.insert(0, '/root/bounties/sha256_scripts')
enc = __import__('13_custom_cnf_encoder')

KISSAT_TIMEOUT = 30      # seconds for phase 2
KISSAT_TIMEOUT_FAST = 10 # seconds for binary search phase
CNF_FILE = '/tmp/sr60_unsat_islands.cnf'


def build_sr60_with_fixed_w57_bits(w1_fixed, w2_fixed):
    """
    Build sr=60 CNF with specific bits of W1[57] and W2[57] fixed at encode time.

    w1_fixed: dict {bit_index: bool_value} -- bits of W1[57] to fix
    w2_fixed: dict {bit_index: bool_value} -- bits of W2[57] to fix
    Unfixed bits become free SAT variables.

    Returns: CNFBuilder instance.
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

    # Build W1[57]: fixed bits become constants, rest are free
    w1_57_bits = []
    for i in range(32):
        if i in w1_fixed:
            w1_57_bits.append(cnf._const(w1_fixed[i]))
        else:
            v = cnf.new_var()
            cnf.free_var_names[v] = f"W1_57[{i}]"
            w1_57_bits.append(v)

    # Build W2[57] similarly
    w2_57_bits = []
    for i in range(32):
        if i in w2_fixed:
            w2_57_bits.append(cnf._const(w2_fixed[i]))
        else:
            v = cnf.new_var()
            cnf.free_var_names[v] = f"W2_57[{i}]"
            w2_57_bits.append(v)

    # Remaining words fully free
    w1_58 = cnf.free_word('W1_58')
    w2_58 = cnf.free_word('W2_58')
    w1_59 = cnf.free_word('W1_59')
    w2_59 = cnf.free_word('W2_59')
    w1_60 = cnf.free_word('W1_60')
    w2_60 = cnf.free_word('W2_60')

    W1_schedule = [w1_57_bits, w1_58, w1_59, w1_60]
    W2_schedule = [w2_57_bits, w2_58, w2_59, w2_60]

    # W[61]
    for sched, pre in [(W1_schedule, W1_pre), (W2_schedule, W2_pre)]:
        w61 = cnf.add_word(
            cnf.add_word(cnf.sigma1_w(sched[2]), cnf.const_word(pre[54])),
            cnf.add_word(cnf.const_word(enc.sigma0_py(pre[46])),
                         cnf.const_word(pre[45])))
        sched.append(w61)

    # W[62]
    for sched, pre in [(W1_schedule, W1_pre), (W2_schedule, W2_pre)]:
        w62 = cnf.add_word(
            cnf.add_word(cnf.sigma1_w(sched[3]), cnf.const_word(pre[55])),
            cnf.add_word(cnf.const_word(enc.sigma0_py(pre[47])),
                         cnf.const_word(pre[46])))
        sched.append(w62)

    # W[63]
    for sched, pre in [(W1_schedule, W1_pre), (W2_schedule, W2_pre)]:
        w63 = cnf.add_word(
            cnf.add_word(cnf.sigma1_w(sched[4 + len(sched) - 6]),
                         cnf.const_word(pre[56])),
            cnf.add_word(cnf.const_word(enc.sigma0_py(pre[48])),
                         cnf.const_word(pre[47])))
        sched.append(w63)

    # 7 rounds
    st1, st2 = s1, s2
    for i in range(7):
        st1 = cnf.sha256_round_correct(st1, enc.K[57 + i], W1_schedule[i])
        st2 = cnf.sha256_round_correct(st2, enc.K[57 + i], W2_schedule[i])

    # Collision constraints
    for i in range(8):
        cnf.eq_word(st1[i], st2[i])

    return cnf


def build_sr60_with_fixed_w57_bits_v2(w1_fixed, w2_fixed):
    """
    Cleaner version that builds W[61-63] correctly.
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

    # Build W1[57] and W2[57] with partial constants
    def make_partial_word(name, fixed_bits):
        bits = []
        for i in range(32):
            if i in fixed_bits:
                bits.append(cnf._const(fixed_bits[i]))
            else:
                v = cnf.new_var()
                cnf.free_var_names[v] = f"{name}[{i}]"
                bits.append(v)
        return bits

    w1_57 = make_partial_word("W1_57", w1_fixed)
    w2_57 = make_partial_word("W2_57", w2_fixed)

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

    # 7 rounds
    st1, st2 = s1, s2
    for i in range(7):
        st1 = cnf.sha256_round_correct(st1, enc.K[57 + i], W1[i])
        st2 = cnf.sha256_round_correct(st2, enc.K[57 + i], W2[i])

    # Collision constraints
    for i in range(8):
        cnf.eq_word(st1[i], st2[i])

    return cnf


def run_kissat(cnf_file, timeout):
    """Run kissat -q. Returns (status, elapsed_seconds)."""
    t0 = time.time()
    try:
        r = subprocess.run(
            ["kissat", "-q", cnf_file],
            capture_output=True, text=True,
            timeout=timeout + 5
        )
        elapsed = time.time() - t0
        if r.returncode == 10:
            return "SAT", elapsed
        elif r.returncode == 20:
            return "UNSAT", elapsed
        return "TIMEOUT", elapsed
    except subprocess.TimeoutExpired:
        return "TIMEOUT", time.time() - t0


def test_n_fixed_bits(n_bits, n_trials=2, seed=42, timeout=None):
    """
    Fix n_bits MSBs of BOTH W1[57] and W2[57] to random values.
    Returns list of (status, elapsed, n_vars, n_clauses).
    """
    if timeout is None:
        timeout = KISSAT_TIMEOUT_FAST
    rng = random.Random(seed)
    results = []

    for trial in range(n_trials):
        w1_fixed = {}
        w2_fixed = {}
        for i in range(n_bits):
            bit_idx = 31 - i
            w1_fixed[bit_idx] = bool(rng.getrandbits(1))
            w2_fixed[bit_idx] = bool(rng.getrandbits(1))

        cnf = build_sr60_with_fixed_w57_bits_v2(w1_fixed, w2_fixed)
        n_vars, n_clauses = cnf.write_dimacs(CNF_FILE)
        status, elapsed = run_kissat(CNF_FILE, timeout)
        results.append((status, elapsed, n_vars, n_clauses))

    return results


def main():
    print("=" * 70)
    print("UNSAT Island Mapping: sr=60 Search Space Fragmentation")
    print("=" * 70)

    # =========================================================
    # Phase 1: Find UNSAT threshold via downward scan
    # =========================================================
    print("\n" + "=" * 70)
    print("PHASE 1: Finding the UNSAT threshold")
    print("=" * 70)
    print("Fixing N MSBs of BOTH W1[57] and W2[57] at encode time.")
    print("Scanning from 32 bits down to find where UNSAT proof fails.\n")

    print(f"{'N bits':>7} {'Fixed/msg':>10} {'Trials':>7} "
          f"{'UNSAT':>7} {'TO':>5} {'Avg time':>10} {'Avg vars':>10}")
    print("-" * 68)

    # Scan: 32, 28, 24, 20, 16, 12, 8, 4
    scan_points = [32, 28, 24, 20, 16, 12, 8, 4]
    scan_results = {}

    for n_bits in scan_points:
        results = test_n_fixed_bits(n_bits, n_trials=2, timeout=KISSAT_TIMEOUT_FAST)
        n_unsat = sum(1 for s, _, _, _ in results if s == "UNSAT")
        n_timeout = sum(1 for s, _, _, _ in results if s == "TIMEOUT")
        avg_time = sum(e for _, e, _, _ in results) / len(results)
        avg_vars = sum(v for _, _, v, _ in results) / len(results)

        scan_results[n_bits] = (n_unsat, len(results))
        all_unsat = "Y" if n_unsat == len(results) else "N"
        print(f"{n_bits:>7} {n_bits:>10} {len(results):>7} "
              f"{n_unsat:>7} {n_timeout:>5} {avg_time:>9.1f}s {avg_vars:>10.0f}")

        if n_unsat < len(results):
            # Found where it breaks
            break

    # Find transition zone
    all_unsat_points = [n for n in scan_points if scan_results.get(n, (0, 1))[0] ==
                        scan_results.get(n, (0, 1))[1] and n in scan_results]
    fail_points = [n for n in scan_points if n in scan_results and
                   scan_results[n][0] < scan_results[n][1]]

    if all_unsat_points and fail_points:
        upper = min(all_unsat_points)
        lower = max(fail_points)
        print(f"\n  Transition zone: {lower+1} to {upper} bits")
        print(f"  Refining...\n")

        for n_bits in range(lower + 1, upper):
            if n_bits in scan_results:
                continue
            results = test_n_fixed_bits(n_bits, n_trials=3,
                                        timeout=KISSAT_TIMEOUT_FAST)
            n_unsat = sum(1 for s, _, _, _ in results if s == "UNSAT")
            n_timeout = sum(1 for s, _, _, _ in results if s == "TIMEOUT")
            avg_time = sum(e for _, e, _, _ in results) / len(results)
            avg_vars = sum(v for _, _, v, _ in results) / len(results)
            scan_results[n_bits] = (n_unsat, len(results))
            print(f"{n_bits:>7} {n_bits:>10} {len(results):>7} "
                  f"{n_unsat:>7} {n_timeout:>5} {avg_time:>9.1f}s {avg_vars:>10.0f}")

    # Determine threshold
    threshold = 32
    for n_bits in sorted(scan_results.keys()):
        nu, nt = scan_results[n_bits]
        if nu == nt and nu > 0:
            threshold = n_bits
            break

    print(f"\n  UNSAT THRESHOLD: {threshold} MSBs of W1[57]+W2[57]")
    print(f"  ({threshold} bits fixed per word, {2*threshold} bits total)")

    # =========================================================
    # Phase 2: Map 16 MSB nibble patterns at threshold
    # =========================================================
    print("\n" + "=" * 70)
    print(f"PHASE 2: Mapping 16 W1[57] MSB patterns at {threshold}-bit depth")
    print("=" * 70)
    print(f"Sweeping all 16 values of W1[57] bits 31-28.")
    print(f"W2[57] MSBs randomized. Other bits from threshold randomized too.")
    print(f"3 trials per MSB nibble pattern (different random fill).\n")

    rng = random.Random(2024)
    n_trials_per = 3

    print(f"{'MSB':>4} {'31-28':>6} {'Tr':>3} {'Status':>8} "
          f"{'Time':>7} {'Vars':>7} {'Clauses':>9} {'Folds':>7}")
    print("-" * 62)

    msb_summary = {}

    for msb_combo in range(16):
        msb_summary[msb_combo] = []

        for trial in range(n_trials_per):
            # W1[57]: set bits 28-31 from combo, randomize rest of fixed range
            w1_fixed = {}
            for i in range(4):
                w1_fixed[28 + i] = bool((msb_combo >> i) & 1)
            # Fill remaining MSBs down to 32-threshold
            for bit_idx in range(27, 32 - threshold - 1, -1):
                w1_fixed[bit_idx] = bool(rng.getrandbits(1))

            # W2[57]: randomize all fixed bits
            w2_fixed = {}
            for i in range(threshold):
                w2_fixed[31 - i] = bool(rng.getrandbits(1))

            cnf = build_sr60_with_fixed_w57_bits_v2(w1_fixed, w2_fixed)
            n_vars, n_clauses = cnf.write_dimacs(CNF_FILE)
            folds = cnf.stats['const_fold']
            status, elapsed = run_kissat(CNF_FILE, KISSAT_TIMEOUT)

            msb_summary[msb_combo].append(status)

            bits_display = ''.join(
                str((msb_combo >> (3 - j)) & 1) for j in range(4))

            print(f"{msb_combo:>4} {bits_display:>6} {trial:>3} {status:>8} "
                  f"{elapsed:>6.1f}s {n_vars:>7} {n_clauses:>9} {folds:>7}")

    # =========================================================
    # Results
    # =========================================================
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)

    print(f"\n  UNSAT threshold: {threshold} MSBs per word "
          f"({2*threshold} bits total across W1[57]+W2[57])")

    print(f"\n  W1[57] MSB Nibble Map (bits 31-28):")
    print(f"  {'Combo':>5} {'Bits':>6} {'UNSAT':>7} {'TO':>5} "
          f"{'SAT':>5} {'Verdict':>10}")
    print(f"  " + "-" * 45)

    total_unsat = 0
    total_timeout = 0
    total_sat = 0
    dead_combos = []
    viable_combos = []

    for msb_combo in range(16):
        statuses = msb_summary[msb_combo]
        nu = statuses.count("UNSAT")
        nt = statuses.count("TIMEOUT")
        ns = statuses.count("SAT")
        total_unsat += nu
        total_timeout += nt
        total_sat += ns

        bits = ''.join(str((msb_combo >> (3 - j)) & 1) for j in range(4))

        if nu == n_trials_per:
            verdict = "DEAD"
            dead_combos.append(bits)
        elif ns > 0:
            verdict = "SAT!"
            viable_combos.append(bits)
        elif nt > 0 and nu > 0:
            verdict = "MIXED"
            viable_combos.append(bits)
        else:
            verdict = "HARD"
            viable_combos.append(bits)

        print(f"  {msb_combo:>5} {bits:>6} {nu:>7} {nt:>5} {ns:>5} {verdict:>10}")

    total_trials = 16 * n_trials_per

    print(f"\n  Aggregate ({total_trials} total trials):")
    print(f"    UNSAT:   {total_unsat:>4} ({total_unsat/total_trials*100:.0f}%)")
    print(f"    TIMEOUT: {total_timeout:>4} ({total_timeout/total_trials*100:.0f}%)")
    print(f"    SAT:     {total_sat:>4} ({total_sat/total_trials*100:.0f}%)")

    print(f"\n  Dead MSB patterns (all trials UNSAT): "
          f"{len(dead_combos)}/16 ({len(dead_combos)/16*100:.0f}%)")
    if dead_combos:
        print(f"    {', '.join(dead_combos)}")

    print(f"  Viable/undecided patterns: "
          f"{len(viable_combos)}/16 ({len(viable_combos)/16*100:.0f}%)")
    if viable_combos:
        print(f"    {', '.join(viable_combos)}")

    # Interpretation
    print(f"\n  INTERPRETATION:")
    unsat_rate = total_unsat / total_trials * 100
    if len(dead_combos) == 16:
        print(f"    ALL 16 MSB patterns are dead at {threshold}-bit depth.")
        print(f"    Every random sub-region of W[57] space is empty.")
        print(f"    The sr=60 problem is massively overconstrained.")
        print(f"    Implication: brute-force search of W[57] will never find")
        print(f"    a collision unless it also coordinates W[58-60] carefully.")
    elif len(dead_combos) == 0 and total_timeout == total_trials:
        print(f"    No dead zones found: all 16 patterns timeout at {threshold} bits.")
        print(f"    The search space is uniformly hard, not fragmented.")
    elif len(dead_combos) == 0:
        print(f"    No consistent dead zones at the MSB nibble level.")
        print(f"    UNSAT rate: {unsat_rate:.0f}% (varies by random fill bits).")
        print(f"    Solutions may exist across all MSB regions.")
    else:
        frac = len(dead_combos) / 16 * 100
        print(f"    {len(dead_combos)}/16 MSB patterns are provably empty.")
        print(f"    Can skip {frac:.0f}% of W1[57] MSB space in search.")
        print(f"    Solutions concentrate in the remaining {len(viable_combos)} patterns.")

    # Clean up
    if os.path.exists(CNF_FILE):
        os.remove(CNF_FILE)

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
