#!/usr/bin/env python3
"""
GPU-parallel WalkSAT v4 — fully vectorized flip selection.

v3 bottleneck: Python for-loop over 1024 walkers (5% GPU util, ~2 flips/s).
v4 fix: torch.multinomial for clause sampling, batch var selection, no Python loops.

Key changes:
  - Fully vectorized flip: multinomial sampling + batch indexing
  - Greedy uses n_sat_lits count (no clone+re-eval needed)
  - 4096 walkers (up from 1024), adaptive noise
  - Reports flips/sec for throughput tracking
"""
import sys, time
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
    n_clauses = len(clauses)
    max_len = max(len(c) for c in clauses)

    cl_vars = torch.zeros(n_clauses, max_len, dtype=torch.long, device=device)
    cl_signs = torch.zeros(n_clauses, max_len, dtype=torch.bool, device=device)
    cl_mask = torch.zeros(n_clauses, max_len, dtype=torch.bool, device=device)

    for i, c in enumerate(clauses):
        for j, lit in enumerate(c):
            cl_vars[i, j] = abs(lit) - 1
            cl_signs[i, j] = lit > 0
            cl_mask[i, j] = True

    return cl_vars, cl_signs, cl_mask, max_len


def build_var_to_clause_index(clauses, n_vars, device):
    """For each variable, store (clause_idx, position_in_clause, sign).
    Used for fast break-count computation."""
    from collections import defaultdict
    var_entries = defaultdict(list)  # var -> list of (clause_idx, pos, sign)
    for ci, c in enumerate(clauses):
        for j, lit in enumerate(c):
            v = abs(lit) - 1
            var_entries[v].append((ci, j, 1 if lit > 0 else 0))

    max_occ = max(len(v) for v in var_entries.values()) if var_entries else 1

    # var_cl_idx[v, k] = clause index of k-th occurrence of variable v
    var_cl_idx = torch.zeros(n_vars, max_occ, dtype=torch.long, device=device)
    var_cl_pos = torch.zeros(n_vars, max_occ, dtype=torch.long, device=device)
    var_cl_sign = torch.zeros(n_vars, max_occ, dtype=torch.bool, device=device)
    var_cl_mask = torch.zeros(n_vars, max_occ, dtype=torch.bool, device=device)

    for v, entries in var_entries.items():
        for k, (ci, pos, sign) in enumerate(entries):
            var_cl_idx[v, k] = ci
            var_cl_pos[v, k] = pos
            var_cl_sign[v, k] = bool(sign)
            var_cl_mask[v, k] = True

    return var_cl_idx, var_cl_sign, var_cl_mask, max_occ


def eval_clauses(assignments, cl_vars, cl_signs, cl_mask, chunk=2048):
    """(n_walkers, n_vars) -> (n_walkers, n_clauses) bool. Chunked."""
    n_walkers = assignments.shape[0]
    n_clauses = cl_vars.shape[0]
    device = assignments.device
    clause_sat = torch.empty(n_walkers, n_clauses, dtype=torch.bool, device=device)
    for i in range(0, n_walkers, chunk):
        j = min(i + chunk, n_walkers)
        vals = assignments[i:j][:, cl_vars]
        lit_sat = (cl_signs.unsqueeze(0) == vals) & cl_mask.unsqueeze(0)
        clause_sat[i:j] = lit_sat.any(dim=2)
        del vals, lit_sat
    return clause_sat


def eval_clauses_with_counts(assignments, cl_vars, cl_signs, cl_mask, chunk=2048):
    """Returns (clause_sat, n_true_lits_per_clause). Chunked to avoid OOM."""
    n_walkers = assignments.shape[0]
    device = assignments.device
    n_clauses = cl_vars.shape[0]

    clause_sat = torch.empty(n_walkers, n_clauses, dtype=torch.bool, device=device)
    n_true = torch.empty(n_walkers, n_clauses, dtype=torch.int8, device=device)

    for i in range(0, n_walkers, chunk):
        j = min(i + chunk, n_walkers)
        a = assignments[i:j]
        vals = a[:, cl_vars]  # (chunk, n_clauses, max_len)
        lit_sat = (cl_signs.unsqueeze(0) == vals) & cl_mask.unsqueeze(0)
        clause_sat[i:j] = lit_sat.any(dim=2)
        n_true[i:j] = lit_sat.to(torch.int8).sum(dim=2)
        del vals, lit_sat  # free immediately

    return clause_sat, n_true


def compute_break_count_batch(assign, cand_vars, n_true,
                               var_cl_idx, var_cl_sign, var_cl_mask):
    """Compute break count for flipping each candidate variable.

    Break count = number of currently-SAT clauses that would become UNSAT.
    A clause breaks if: variable appears in it with a currently-TRUE literal,
    and that literal is the ONLY true literal (n_true == 1).

    assign: (n_walkers, n_vars)
    cand_vars: (n_walkers,) — one candidate variable per walker
    n_true: (n_walkers, n_clauses)
    Returns: (n_walkers,) — break count per walker
    """
    n_walkers = assign.shape[0]
    device = assign.device
    arange_w = torch.arange(n_walkers, device=device)

    # Get clauses containing each candidate variable
    related_cls = var_cl_idx[cand_vars]    # (n_walkers, max_occ)
    related_sign = var_cl_sign[cand_vars]  # (n_walkers, max_occ)
    related_mask = var_cl_mask[cand_vars]  # (n_walkers, max_occ)

    # Current value of candidate variable
    cur_val = assign[arange_w, cand_vars]  # (n_walkers,) bool

    # The literal is TRUE if (sign == cur_val)
    lit_is_true = (related_sign == cur_val.unsqueeze(1))  # (n_walkers, max_occ)

    # Get n_true for related clauses
    # n_true: (n_walkers, n_clauses), related_cls: (n_walkers, max_occ)
    related_n_true = n_true.gather(1, related_cls)  # (n_walkers, max_occ)

    # Clause would break if: literal is true AND it's the only true literal AND valid
    would_break = lit_is_true & (related_n_true == 1) & related_mask

    return would_break.sum(dim=1)  # (n_walkers,)


def run_sls(cnf_path, n_walkers=4096, max_flips=200000, max_restarts=10000,
            noise_init=0.45, hours=48.0):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    n_vars, clauses = parse_cnf(cnf_path)
    n_clauses = len(clauses)
    print(f"SLS v4 on {cnf_path}: {n_vars} vars, {n_clauses} clauses", flush=True)
    print(f"Device: {device}, Walkers: {n_walkers}", flush=True)
    print(f"Noise: {noise_init}, Max flips/restart: {max_flips}", flush=True)
    print(f"Running for {hours}h", flush=True)

    cl_vars, cl_signs, cl_mask, max_len = build_clause_tensors(clauses, n_vars, device)
    var_cl_idx, var_cl_sign, var_cl_mask, max_occ = \
        build_var_to_clause_index(clauses, n_vars, device)
    print(f"Built tensors: max_clause_len={max_len}, max_var_occ={max_occ}", flush=True)

    # Memory estimate
    mem_mb = torch.cuda.memory_allocated() / 1e6 if device.type == 'cuda' else 0
    print(f"Tensor memory: {mem_mb:.0f} MB", flush=True)

    best_ever_unsat = n_clauses
    best_ever_assign = None
    t0 = time.time()
    total_flips = 0
    noise = noise_init
    stale_count = 0  # flips without improvement

    for restart in range(max_restarts):
        if time.time() - t0 > hours * 3600:
            break

        assign = torch.randint(0, 2, (n_walkers, n_vars),
                               dtype=torch.bool, device=device)
        restart_best = n_clauses

        for flip in range(max_flips):
            if time.time() - t0 > hours * 3600:
                break

            # Evaluate
            sat, n_true = eval_clauses_with_counts(assign, cl_vars, cl_signs, cl_mask)
            unsat_count = (~sat).sum(dim=1)
            min_unsat = unsat_count.min().item()
            total_flips += 1

            if min_unsat < best_ever_unsat:
                best_ever_unsat = min_unsat
                best_idx = unsat_count.argmin().item()
                best_ever_assign = assign[best_idx].clone()
                elapsed = time.time() - t0
                rate = total_flips / elapsed if elapsed > 0 else 0
                stale_count = 0
                print(f"  r={restart} f={flip}: NEW BEST unsat={best_ever_unsat}/{n_clauses} "
                      f"({100*(1-best_ever_unsat/n_clauses):.2f}%) "
                      f"[{elapsed:.0f}s, {rate:.1f} fl/s, noise={noise:.2f}]", flush=True)
            else:
                stale_count += 1

            if min_unsat < restart_best:
                restart_best = min_unsat

            if min_unsat == 0:
                elapsed = time.time() - t0
                print(f"\n{'='*60}", flush=True)
                print(f"*** SAT *** restart={restart} flip={flip} "
                      f"time={elapsed:.0f}s ({elapsed/3600:.2f}h)", flush=True)
                print(f"{'='*60}", flush=True)
                sat_idx = unsat_count.argmin().item()
                sol = assign[sat_idx]
                with open('/tmp/sls_v4_solution.txt', 'w') as sf:
                    for v in range(n_vars):
                        val = sol[v].item()
                        sf.write(f"{v+1 if val else -(v+1)} 0\n")
                print(f"Solution: /tmp/sls_v4_solution.txt", flush=True)
                return True

            # --- Vectorized WalkSAT flip ---
            arange_w = torch.arange(n_walkers, device=device)

            # 1. Sample one unsatisfied clause per walker
            unsat_mask = ~sat
            unsat_float = unsat_mask.float()
            has_unsat = unsat_float.sum(dim=1) > 0

            if not has_unsat.any():
                continue

            unsat_float[~has_unsat] = 1.0  # dummy for multinomial
            clause_idx = torch.multinomial(unsat_float, 1).squeeze(1)

            # 2. Get literals from selected clause
            sel_vars = cl_vars[clause_idx]   # (n_walkers, max_len)
            sel_mask = cl_mask[clause_idx]   # (n_walkers, max_len)

            # 3. Random walk: sample random valid literal
            sel_mask_f = sel_mask.float()
            sel_mask_f[sel_mask_f.sum(dim=1) == 0, 0] = 1.0
            rand_pos = torch.multinomial(sel_mask_f, 1).squeeze(1)
            rand_vars = sel_vars[arange_w, rand_pos]

            # 4. Greedy: pick literal with minimum break count
            #    Evaluate break count for each of max_len candidate positions
            best_break = torch.full((n_walkers,), n_clauses + 1,
                                    dtype=torch.long, device=device)
            greedy_vars = sel_vars[:, 0]  # fallback

            for li in range(max_len):
                cand = sel_vars[:, li]
                valid = sel_mask[:, li]
                if not valid.any():
                    continue

                bc = compute_break_count_batch(
                    assign, cand, n_true, var_cl_idx, var_cl_sign, var_cl_mask)

                better = valid & (bc < best_break)
                best_break = torch.where(better, bc, best_break)
                greedy_vars = torch.where(better, cand, greedy_vars)

                # Freebie: if break count is 0, no need to check more
                # (but we do anyway since it's vectorized and cheap)

            # 5. Choose: noise → random, else → greedy
            noise_mask = torch.rand(n_walkers, device=device) < noise
            flip_vars = torch.where(noise_mask, rand_vars, greedy_vars)

            # 6. Apply flips
            flip_idx = arange_w[has_unsat]
            flip_v = flip_vars[has_unsat]
            assign[flip_idx, flip_v] = ~assign[flip_idx, flip_v]

            # --- Adaptive noise ---
            if stale_count > 0 and stale_count % 2000 == 0:
                noise = min(0.7, noise + 0.02)

            # --- Logging ---
            if flip % 200 == 199:
                elapsed = time.time() - t0
                rate = total_flips / elapsed if elapsed > 0 else 0
                gpu_mem = torch.cuda.memory_allocated() / 1e6 if device.type == 'cuda' else 0
                print(f"  r={restart} f={flip}: unsat={min_unsat}/{n_clauses} "
                      f"best={best_ever_unsat} ({100*(1-best_ever_unsat/n_clauses):.2f}%) "
                      f"[{elapsed:.0f}s, {rate:.1f} fl/s, {gpu_mem:.0f}MB, n={noise:.2f}]",
                      flush=True)

        # End of restart
        elapsed = time.time() - t0
        rate = total_flips / elapsed if elapsed > 0 else 0
        print(f"  restart {restart} done: best_this={restart_best} best_ever={best_ever_unsat} "
              f"[{elapsed:.0f}s, {rate:.1f} fl/s, {elapsed/3600:.1f}h]", flush=True)

        # Reset noise on restart
        noise = noise_init

    elapsed = time.time() - t0
    print(f"\n{'='*60}", flush=True)
    print(f"SLS v4 COMPLETE: {restart+1} restarts, {total_flips} total flips", flush=True)
    print(f"best_ever={best_ever_unsat}/{n_clauses} "
          f"({100*(1-best_ever_unsat/n_clauses):.2f}%)", flush=True)
    print(f"Time: {elapsed:.0f}s ({elapsed/3600:.1f}h)", flush=True)
    print(f"{'='*60}", flush=True)

    if best_ever_assign is not None:
        with open('/tmp/sls_v4_best.txt', 'w') as sf:
            for v in range(n_vars):
                val = best_ever_assign[v].item()
                sf.write(f"{v+1 if val else -(v+1)} 0\n")
        print(f"Best assignment: /tmp/sls_v4_best.txt", flush=True)

    return False


if __name__ == "__main__":
    cnf = sys.argv[1] if len(sys.argv) > 1 else '/tmp/sr61_m17149975_fffffffff.cnf'
    hours = float(sys.argv[2]) if len(sys.argv) > 2 else 48.0
    walkers = int(sys.argv[3]) if len(sys.argv) > 3 else 4096
    run_sls(cnf, n_walkers=walkers, hours=hours)
