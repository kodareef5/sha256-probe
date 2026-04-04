#!/usr/bin/env python3
"""
Script 26: Internal Carry Cubing Swarm

SHA-256 is an ARX network. Rotations and XORs are linear — SAT solvers
handle them trivially. The ONLY non-linearity is carry propagation in
modular additions.

By fixing the carry bits, we turn A + B = C into A XOR B XOR fixed_carry = C.
The 7-round tail becomes a mostly-linear system that Kissat can rip through.

Strategy:
  1. Generate base sr=60 DIMACS with carry variables EXPOSED
  2. Identify carries from the T1 addition in rounds 57-58 (deepest chains)
  3. Fix the N most significant carry bits (MSB carries propagate most chaos)
  4. Generate 2^N subproblems, each a nearly-linear system
  5. Swarm Kissat instances with short timeouts

Most carry combinations → instant UNSAT (impossible carry chains)
The correct combination → Kissat solves a nearly-linear system in seconds
"""

import sys
import os
import time
import subprocess
import multiprocessing
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from importlib import import_module
enc = import_module('13_custom_cnf_encoder')


def build_sr60_with_tracked_carries():
    """Build sr=60 DIMACS exposing carry variables from T1 additions."""

    M1 = [0x17149975] + [0xffffffff] * 15
    M2 = M1.copy()
    M2[0] ^= 0x80000000
    M2[9] ^= 0x80000000

    state1, W1_pre = enc.precompute_state(M1)
    state2, W2_pre = enc.precompute_state(M2)

    cnf = enc.CNFBuilder()
    s1 = tuple(cnf.const_word(v) for v in state1)
    s2 = tuple(cnf.const_word(v) for v in state2)

    w1_free = [cnf.free_word(f"W1_{57+i}") for i in range(4)]
    w2_free = [cnf.free_word(f"W2_{57+i}") for i in range(4)]

    W1_schedule = list(w1_free)
    W2_schedule = list(w2_free)

    # W[61] enforced
    w1_61 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w1_free[2]), cnf.const_word(W1_pre[54])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W1_pre[46])), cnf.const_word(W1_pre[45])))
    w2_61 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w2_free[2]), cnf.const_word(W2_pre[54])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W2_pre[46])), cnf.const_word(W2_pre[45])))
    W1_schedule.append(w1_61)
    W2_schedule.append(w2_61)

    w1_62 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(W1_schedule[3]), cnf.const_word(W1_pre[55])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W1_pre[47])), cnf.const_word(W1_pre[46])))
    w2_62 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(W2_schedule[3]), cnf.const_word(W2_pre[55])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W2_pre[47])), cnf.const_word(W2_pre[46])))
    w1_63 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(W1_schedule[4]), cnf.const_word(W1_pre[56])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W1_pre[48])), cnf.const_word(W1_pre[47])))
    w2_63 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(W2_schedule[4]), cnf.const_word(W2_pre[56])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W2_pre[48])), cnf.const_word(W2_pre[47])))

    W1_schedule.extend([w1_62, w1_63])
    W2_schedule.extend([w2_62, w2_63])

    # Run rounds with carry tracking on T1's final ripple-carry
    all_carries = {}  # round -> message -> carry list

    for msg_idx, (state_init, W_sched, label) in enumerate([
        (s1, W1_schedule, "M1"), (s2, W2_schedule, "M2")
    ]):
        st = state_init
        for r in range(7):
            a, b, c, d, e, f, g, h = st
            K_word = cnf.const_word(enc.K[57 + r])
            sig1 = cnf.Sigma1(e)
            ch = cnf.Ch(e, f, g)

            # T1 with tracked carries
            s1_csa, c1_csa = cnf.csa_layer(h, sig1, ch)
            s2_csa, c2_csa = cnf.csa_layer(s1_csa, K_word, W_sched[r])
            s3_csa, c3_csa = cnf.csa_layer(c1_csa, s2_csa, c2_csa)
            t1, t1_carries = cnf.add_word(s3_csa, c3_csa, track_carries=True)

            # Store carries for rounds 57-58 (highest leverage)
            if r <= 1:
                key = f"T1_r{57+r}_{label}"
                all_carries[key] = t1_carries

            sig0 = cnf.Sigma0(a)
            mj = cnf.Maj(a, b, c)
            t2 = cnf.add_word(sig0, mj)

            a_new = cnf.add_word(t1, t2)
            e_new = cnf.add_word(d, t1)

            st = (a_new, a, b, c, e_new, e, f, g)

        # Store final state
        if msg_idx == 0:
            st1_final = st
        else:
            st2_final = st

    # Collision constraint
    for i in range(8):
        cnf.eq_word(st1_final[i], st2_final[i])

    return cnf, all_carries


def identify_cubeable_carries(all_carries):
    """
    Find carry variables suitable for cubing.
    Returns list of (var_id, name) for the MSB carry bits.
    Only include NON-CONSTANT carries (symbolic variables).
    """
    cubeable = []

    for key in sorted(all_carries.keys()):
        carries = all_carries[key]
        # MSB carries (bits 20-31) propagate the most chaos
        for bit in range(20, 32):
            if bit < len(carries):
                var = carries[bit]
                if not (abs(var) == 1):  # not the TRUE/FALSE constant
                    cubeable.append((var, f"{key}_carry[{bit}]"))

    return cubeable


def solve_cube(args):
    """Solve one cube subproblem."""
    base_file, cube_idx, fixed_vars, fixed_vals, timeout_sec, work_dir = args

    sub_file = os.path.join(work_dir, f"c{cube_idx}.cnf")

    with open(base_file, 'r') as fin:
        header = fin.readline()
        parts = header.split()
        nv, nc = int(parts[2]), int(parts[3])

        with open(sub_file, 'w') as fout:
            fout.write(f"p cnf {nv} {nc + len(fixed_vars)}\n")
            for line in fin:
                fout.write(line)
            for var_id, val in zip(fixed_vars, fixed_vals):
                fout.write(f"{var_id if val else -var_id} 0\n")

    try:
        r = subprocess.run(
            ["kissat", "-q", sub_file],
            capture_output=True, text=True,
            timeout=timeout_sec
        )
        os.unlink(sub_file)

        if r.returncode == 10:
            return "SAT", cube_idx
        elif r.returncode == 20:
            return "UNSAT", cube_idx
        else:
            return "TIMEOUT", cube_idx
    except subprocess.TimeoutExpired:
        try:
            os.unlink(sub_file)
        except:
            pass
        return "TIMEOUT", cube_idx
    except Exception as e:
        return "ERROR", cube_idx


def main():
    n_carry_bits = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    timeout_per = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    n_workers = int(sys.argv[3]) if len(sys.argv) > 3 else 20

    n_cubes = 2 ** n_carry_bits

    print("=" * 70, flush=True)
    print("CARRY CUBING SWARM — Dimension 2", flush=True)
    print("Neutralizing SHA-256's non-linearity by fixing carry bits", flush=True)
    print(f"  Carry bits to fix: {n_carry_bits} -> {n_cubes} subproblems", flush=True)
    print(f"  Timeout per cube: {timeout_per}s", flush=True)
    print(f"  Workers: {n_workers}", flush=True)
    print("=" * 70, flush=True)

    # Build encoder with tracked carries
    print("\nBuilding sr=60 with carry tracking...", flush=True)
    cnf, all_carries = build_sr60_with_tracked_carries()

    base_file = "/tmp/sr60_carry_base.cnf"
    cnf.write_dimacs(base_file)
    nv = cnf.next_var - 1
    nc = len(cnf.clauses)
    print(f"  Base: {nv} vars, {nc} clauses", flush=True)

    # Identify cubeable carries
    cubeable = identify_cubeable_carries(all_carries)
    print(f"\n  Cubeable carry variables: {len(cubeable)}", flush=True)
    for var_id, name in cubeable[:20]:
        is_const = abs(var_id) == 1
        print(f"    {name}: var={var_id} {'(CONST)' if is_const else ''}", flush=True)

    if len(cubeable) < n_carry_bits:
        print(f"\n  WARNING: Only {len(cubeable)} non-constant carries available.", flush=True)
        print(f"  Reducing cube bits to {len(cubeable)}", flush=True)
        n_carry_bits = len(cubeable)
        n_cubes = 2 ** n_carry_bits

    # Select the MSB carries (highest impact)
    selected = cubeable[-n_carry_bits:]  # Take the last N (highest bit positions)
    selected_vars = [var_id for var_id, _ in selected]

    print(f"\n  Selected {n_carry_bits} carries for cubing:", flush=True)
    for var_id, name in selected:
        print(f"    {name} (var {var_id})", flush=True)

    # Create work directory
    work_dir = tempfile.mkdtemp(prefix="carry_cube_")

    # Generate tasks
    tasks = []
    for cube_idx in range(n_cubes):
        vals = [bool((cube_idx >> bit) & 1) for bit in range(n_carry_bits)]
        tasks.append((base_file, cube_idx, selected_vars, vals, timeout_per, work_dir))

    # SWARM
    print(f"\nLaunching {n_cubes} subproblems across {n_workers} workers...", flush=True)
    t_start = time.time()

    n_sat = n_unsat = n_timeout = n_error = 0
    sat_cube = None

    with multiprocessing.Pool(n_workers) as pool:
        for status, cube_idx in pool.imap_unordered(solve_cube, tasks):
            if status == "SAT":
                n_sat += 1
                sat_cube = cube_idx
                elapsed = time.time() - t_start
                print(f"\n  [!!!] CUBE {cube_idx} = SAT ({elapsed:.1f}s)", flush=True)
                print(f"  Carry assignment: {cube_idx:0{n_carry_bits}b}", flush=True)
                pool.terminate()
                break
            elif status == "UNSAT":
                n_unsat += 1
            elif status == "TIMEOUT":
                n_timeout += 1
            else:
                n_error += 1

            done = n_sat + n_unsat + n_timeout + n_error
            if done % max(1, n_cubes // 10) == 0:
                elapsed = time.time() - t_start
                rate = done / elapsed if elapsed > 0 else 0
                eta = (n_cubes - done) / rate if rate > 0 else 0
                print(f"  [{done}/{n_cubes}] SAT={n_sat} UNSAT={n_unsat} "
                      f"TO={n_timeout} ({elapsed:.0f}s, ETA {eta:.0f}s)", flush=True)

    t_total = time.time() - t_start
    shutil.rmtree(work_dir, ignore_errors=True)

    # Results
    print(f"\n{'='*70}", flush=True)
    print("RESULTS", flush=True)
    print(f"{'='*70}", flush=True)
    total = n_sat + n_unsat + n_timeout + n_error
    print(f"  Cubes tested: {total}/{n_cubes}", flush=True)
    print(f"  SAT:     {n_sat}", flush=True)
    print(f"  UNSAT:   {n_unsat} ({n_unsat/max(1,total)*100:.1f}%)", flush=True)
    print(f"  TIMEOUT: {n_timeout} ({n_timeout/max(1,total)*100:.1f}%)", flush=True)
    print(f"  ERROR:   {n_error}", flush=True)
    print(f"  Time:    {t_total:.1f}s ({t_total/3600:.2f}h)", flush=True)

    if n_sat > 0:
        print(f"\n  [!!!] SR=60 SOLVED VIA CARRY CUBING!", flush=True)
        print(f"  Lucky cube: {sat_cube}", flush=True)
    else:
        if n_unsat > total * 0.5:
            print(f"\n  HIGH UNSAT rate ({n_unsat/total*100:.0f}%): carry cubing creates dead branches!", flush=True)
            print(f"  This is GOOD — it means fixing carries constrains the problem meaningfully.", flush=True)
            print(f"  Try: more carry bits, longer timeouts, or combine with backbone mining.", flush=True)
        elif n_timeout > total * 0.8:
            print(f"\n  HIGH TIMEOUT rate: subproblems still too hard even with fixed carries.", flush=True)
            print(f"  Try: fix MORE carry bits (from more rounds), or longer per-cube timeout.", flush=True)


if __name__ == "__main__":
    main()
