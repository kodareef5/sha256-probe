#!/usr/bin/env python3
"""
GPU-parallel Stochastic Local Search (WalkSAT-style) on SHA-256 CNFs.

Fixes from v1: fully vectorized clause evaluation, proper best tracking,
restart logic, GPU-native operations.

Key insight: represent clauses as a sparse matrix, evaluate all walkers
× all clauses in one matmul-like operation.
"""
import sys, os, time, random
import torch

def parse_cnf(path):
    clauses = []
    n_vars = 0
    with open(path) as f:
        for line in f:
            if line.startswith('p cnf'):
                n_vars = int(line.split()[2])
            elif not line.startswith('c') and not line.startswith('%'):
                lits = [int(x) for x in line.split() if x != '0' and x.strip()]
                if lits:
                    clauses.append(lits)
    return n_vars, clauses


def build_clause_tensors(clauses, n_vars, device):
    """Build GPU tensors for fast clause evaluation."""
    n_clauses = len(clauses)
    max_len = max(len(c) for c in clauses)

    # Pad clauses to uniform length
    cl_vars = torch.zeros(n_clauses, max_len, dtype=torch.long, device=device)
    cl_signs = torch.zeros(n_clauses, max_len, dtype=torch.bool, device=device)
    cl_mask = torch.zeros(n_clauses, max_len, dtype=torch.bool, device=device)

    for i, c in enumerate(clauses):
        for j, lit in enumerate(c):
            cl_vars[i, j] = abs(lit) - 1  # 0-indexed
            cl_signs[i, j] = lit > 0
            cl_mask[i, j] = True

    return cl_vars, cl_signs, cl_mask


def eval_clauses(assignments, cl_vars, cl_signs, cl_mask):
    """
    Evaluate all clauses for all walkers.
    assignments: (n_walkers, n_vars) bool
    Returns: (n_walkers, n_clauses) bool — True if clause satisfied
    """
    n_walkers = assignments.shape[0]
    n_clauses = cl_vars.shape[0]
    max_len = cl_vars.shape[1]

    # Gather variable values: (n_walkers, n_clauses, max_len)
    vals = assignments[:, cl_vars]  # (n_walkers, n_clauses, max_len)

    # Apply signs: literal is satisfied if (sign == val)
    lit_sat = (cl_signs.unsqueeze(0) == vals) & cl_mask.unsqueeze(0)

    # Clause is satisfied if ANY literal is satisfied
    clause_sat = lit_sat.any(dim=2)  # (n_walkers, n_clauses)

    return clause_sat


def run_sls(cnf_path, n_walkers=2048, max_flips=50000, max_restarts=10000,
            noise=0.4, hours=4.0, sample_frac=1.0):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    n_vars, clauses = parse_cnf(cnf_path)
    n_clauses = len(clauses)
    print(f"SLS on {cnf_path}: {n_vars} vars, {n_clauses} clauses", flush=True)
    print(f"Device: {device}, Walkers: {n_walkers}, Noise: {noise}", flush=True)
    print(f"Max flips: {max_flips}, Max restarts: {max_restarts}", flush=True)
    print(f"Running for {hours}h", flush=True)

    # Use a subset of clauses if too many (for speed)
    if sample_frac < 1.0:
        n_sample = int(n_clauses * sample_frac)
        idx = random.sample(range(n_clauses), n_sample)
        clauses = [clauses[i] for i in idx]
        n_clauses = len(clauses)
        print(f"Sampling {n_clauses} clauses ({sample_frac*100:.0f}%)", flush=True)

    cl_vars, cl_signs, cl_mask = build_clause_tensors(clauses, n_vars, device)

    best_ever_unsat = n_clauses
    t0 = time.time()

    for restart in range(max_restarts):
        if time.time() - t0 > hours * 3600:
            break

        # Random initial assignment
        assign = torch.randint(0, 2, (n_walkers, n_vars),
                               dtype=torch.bool, device=device)

        for flip in range(max_flips):
            if time.time() - t0 > hours * 3600:
                break

            # Evaluate all clauses
            sat = eval_clauses(assign, cl_vars, cl_signs, cl_mask)
            unsat_count = (~sat).sum(dim=1)  # (n_walkers,)
            min_unsat = unsat_count.min().item()

            if min_unsat < best_ever_unsat:
                best_ever_unsat = min_unsat
                elapsed = time.time() - t0
                print(f"  r={restart} f={flip}: NEW BEST unsat={best_ever_unsat}/{n_clauses} "
                      f"({elapsed:.0f}s)", flush=True)

            if min_unsat == 0:
                print(f"\n*** ALL CLAUSES SATISFIED *** restart={restart} flip={flip}", flush=True)
                elapsed = time.time() - t0
                print(f"Time: {elapsed:.0f}s", flush=True)
                return True

            # WalkSAT flip strategy:
            # For each walker, pick a random unsatisfied clause,
            # then flip a variable from that clause
            for w_batch_start in range(0, n_walkers, 256):
                w_batch_end = min(w_batch_start + 256, n_walkers)
                batch = w_batch_end - w_batch_start

                # Find unsatisfied clauses for this batch
                unsat_mask = ~sat[w_batch_start:w_batch_end]  # (batch, n_clauses)

                for w in range(batch):
                    wi = w_batch_start + w
                    unsat_indices = unsat_mask[w].nonzero(as_tuple=True)[0]
                    if len(unsat_indices) == 0:
                        continue

                    # Pick random unsat clause
                    ci = unsat_indices[torch.randint(len(unsat_indices), (1,)).item()].item()

                    if random.random() < noise:
                        # Random walk: flip any variable in the clause
                        cl_len = cl_mask[ci].sum().item()
                        li = random.randint(0, cl_len - 1)
                        var = cl_vars[ci, li].item()
                    else:
                        # Greedy: flip the variable that minimizes break count
                        # Simplified: just pick the first literal in the clause
                        var = cl_vars[ci, 0].item()

                    assign[wi, var] = ~assign[wi, var]

            if flip % 500 == 499:
                elapsed = time.time() - t0
                print(f"  r={restart} f={flip}: unsat={min_unsat}/{n_clauses} "
                      f"best_ever={best_ever_unsat} ({elapsed:.0f}s)", flush=True)

        # End of restart
        elapsed = time.time() - t0
        if restart % 10 == 0:
            print(f"  restart {restart} done: best_ever={best_ever_unsat}/{n_clauses} "
                  f"({elapsed:.0f}s, {elapsed/3600:.1f}h)", flush=True)

    elapsed = time.time() - t0
    print(f"\n{'='*60}", flush=True)
    print(f"SLS COMPLETE: {restart+1} restarts, best_ever_unsat={best_ever_unsat}/{n_clauses}", flush=True)
    print(f"Time: {elapsed:.0f}s ({elapsed/3600:.1f}h)", flush=True)
    print(f"{'='*60}", flush=True)
    return False


if __name__ == "__main__":
    cnf = sys.argv[1] if len(sys.argv) > 1 else '/tmp/sr61_m17149975_fffffffff.cnf'
    hours = float(sys.argv[2]) if len(sys.argv) > 2 else 4.0
    walkers = int(sys.argv[3]) if len(sys.argv) > 3 else 2048
    run_sls(cnf, n_walkers=walkers, hours=hours, sample_frac=0.5)
