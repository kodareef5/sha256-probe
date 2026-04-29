#!/usr/bin/env python3
"""
preflight_clause_miner.py — extract CDCL-derived structural clauses from a
cand's cascade_aux force-mode CNF for IPASIR-UP cb_add_external_clause
pre-loading.

Implements the preflight protocol from F341/F342/F340:
  Class 1a-univ: single-bit unit on dW57[0] (universal across cands,
                  polarity per-cand)
  Class 2-univ: 2-bit blocking on (dW57[22], dW57[23]) (universal,
                  polarity per-cand)

Extends to:
  - Probing other dWr[b] single-bit positions for additional Class 1a units.
  - Probing other (dWr[i], dWr[j]) adjacent-bit pairs for additional Class 2.

Output: JSON spec with the forced unit clauses + 2-bit blocking clauses,
ready to be ingested by an IPASIR-UP propagator's cb_add_external_clause
hook at solver init.

Usage:
    python3 preflight_clause_miner.py \
        --cnf path/to/aux_force_sr60_n32_bitB_mM_fillF.cnf \
        --varmap path/to/varmap.json \
        [--budget 5] [--rounds 57] [--out preflight_clauses.json]

Test with the F342 dataset:
    python3 preflight_clause_miner.py \
        --cnf .../aux_force_sr60_n32_bit31_m17149975_fillffffffff.cnf \
        --varmap .../varmap.json --budget 5
"""
import argparse
import json
import os
import subprocess
import sys
import time


def read_cnf(path):
    lines = []
    n_vars = 0
    n_clauses = 0
    with open(path) as f:
        for L in f:
            L = L.strip()
            if not L or L.startswith('c'):
                continue
            if L.startswith('p'):
                parts = L.split()
                n_vars = int(parts[2])
                n_clauses = int(parts[3])
                continue
            lines.append(L + '\n')
    return n_vars, n_clauses, lines


def cadical_run(n_vars, n_clauses, body_lines, assumptions, budget):
    """Append `assumptions` as unit clauses, run cadical with budget seconds.
    Returns ('UNSATISFIABLE'|'SATISFIABLE'|'UNKNOWN', wall_seconds).
    """
    import tempfile
    fd, path = tempfile.mkstemp(suffix='.cnf', prefix='preflight_')
    os.close(fd)
    new_n = n_clauses + len(assumptions)
    try:
        with open(path, 'w') as f:
            f.write(f'p cnf {n_vars} {new_n}\n')
            f.writelines(body_lines)
            for lit in assumptions:
                f.write(f'{lit} 0\n')
        t0 = time.time()
        r = subprocess.run(
            ['cadical', '-t', str(int(budget)), '--no-binary', path],
            capture_output=True, text=True, timeout=int(budget) + 5,
        )
        elapsed = time.time() - t0
        # Prefer 's UNSATISFIABLE/SATISFIABLE' line if present, but fall back
        # to returncode (20=UNSAT, 10=SAT, 0=UNKNOWN/timeout) since cadical
        # can exit faster than stdout flushes for trivial UP-derivable UNSAT.
        verdict = None
        for line in (r.stdout + r.stderr).split('\n'):
            if line.startswith('s '):
                verdict = line[2:].strip()
                break
        if verdict is None:
            if r.returncode == 20:
                verdict = 'UNSATISFIABLE'
            elif r.returncode == 10:
                verdict = 'SATISFIABLE'
            else:
                verdict = 'UNKNOWN'
        return verdict, elapsed
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


def probe_single_bit(n_vars, n_clauses, body, var, budget):
    """Test both polarities of a single var for fast UNSAT.
    Returns the forced value (0 or 1) or None if neither polarity is fast UNSAT.
    """
    res = {}
    for polarity, lit in [(0, -var), (1, +var)]:
        verdict, wall = cadical_run(n_vars, n_clauses, body, [lit], budget)
        res[polarity] = (verdict, wall)
    if res[0][0] == 'UNSATISFIABLE':
        return 1, res
    if res[1][0] == 'UNSATISFIABLE':
        return 0, res
    return None, res


def probe_pair(n_vars, n_clauses, body, var_a, var_b, budget):
    """Test all 4 polarity combos of (var_a, var_b) for fast UNSAT.
    Returns (forbidden_polarity, results_dict) where forbidden_polarity is
    a tuple (a_val, b_val) such that the assignment a=a_val, b=b_val is UNSAT.
    Returns (None, results) if no polarity is fast UNSAT.
    """
    res = {}
    for a_val in (0, 1):
        for b_val in (0, 1):
            la = -var_a if a_val == 0 else +var_a
            lb = -var_b if b_val == 0 else +var_b
            verdict, wall = cadical_run(n_vars, n_clauses, body, [la, lb], budget)
            res[(a_val, b_val)] = (verdict, wall)
    forbidden = None
    for k, (v, _) in res.items():
        if v == 'UNSATISFIABLE':
            forbidden = k
            break  # first UNSAT polarity
    return forbidden, res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cnf', required=True)
    ap.add_argument('--varmap', required=True)
    ap.add_argument('--budget', type=float, default=5.0,
                    help='cadical seconds-per-probe budget')
    ap.add_argument('--rounds', default='57',
                    help='comma-separated rounds to probe (default 57)')
    ap.add_argument('--probe-pairs', default='22,23',
                    help='comma-separated bit pair (i,j) to probe per round '
                         '(default: 22,23 — F340 finding)')
    ap.add_argument('--probe-single-bits', default='0',
                    help='comma-separated single-bit positions to probe per round '
                         '(default: 0 — F341/F342 finding)')
    ap.add_argument('--out', default=None,
                    help='output JSON path (default: stdout)')
    args = ap.parse_args()

    print(f'# preflight_clause_miner: cnf={args.cnf}', file=sys.stderr)
    n_vars, n_clauses, body = read_cnf(args.cnf)
    print(f'#   n_vars={n_vars}, clauses={n_clauses}', file=sys.stderr)

    with open(args.varmap) as f:
        vm = json.load(f)
    aux_W = vm['aux_W']

    rounds = [int(x) for x in args.rounds.split(',')]
    single_bits = [int(x) for x in args.probe_single_bits.split(',')]
    pair_bits = [int(x) for x in args.probe_pairs.split(',')]
    if len(pair_bits) != 2:
        raise ValueError('--probe-pairs needs exactly 2 bit indices')

    spec = {
        'cnf': args.cnf,
        'budget_seconds': args.budget,
        'rounds_probed': rounds,
        'unit_clauses': [],
        'pair_clauses': [],
        'preflight_wall_seconds': 0.0,
    }
    t_total = time.time()

    # Single-bit probes
    for r in rounds:
        if str(r) not in aux_W:
            continue
        for b in single_bits:
            var = aux_W[str(r)][b]
            forced, res = probe_single_bit(n_vars, n_clauses, body, var, args.budget)
            entry = {
                'round': r, 'bit': b, 'var': var,
                'forced': forced,
                'probes': {p: {'verdict': v, 'wall_s': round(w, 3)}
                           for p, (v, w) in res.items()},
            }
            spec['unit_clauses'].append(entry)
            if forced is not None:
                # Inject as unit clause (UNSAT polarity is the OPPOSITE of forced)
                lit = +var if forced == 1 else -var
                entry['inject_unit'] = lit
                print(f'#   dW{r}[{b}] forced={forced}, inject lit {lit}',
                      file=sys.stderr)
            else:
                print(f'#   dW{r}[{b}]: no fast UNSAT', file=sys.stderr)

    # Pair probes
    for r in rounds:
        if str(r) not in aux_W:
            continue
        i, j = pair_bits
        var_i = aux_W[str(r)][i]
        var_j = aux_W[str(r)][j]
        forbidden, res = probe_pair(n_vars, n_clauses, body, var_i, var_j, args.budget)
        entry = {
            'round': r, 'bits': [i, j], 'vars': [var_i, var_j],
            'forbidden_polarity': forbidden,
            'probes': {f'{a}{b}': {'verdict': v, 'wall_s': round(w, 3)}
                       for (a, b), (v, w) in res.items()},
        }
        spec['pair_clauses'].append(entry)
        if forbidden is not None:
            # Inject as 2-literal blocking clause: NOT(var_i = forbidden[0] AND var_j = forbidden[1])
            # Equivalent: clause [-var_i if forbidden[0]==1 else +var_i,
            #                     -var_j if forbidden[1]==1 else +var_j]
            la = -var_i if forbidden[0] == 1 else +var_i
            lb = -var_j if forbidden[1] == 1 else +var_j
            entry['inject_pair'] = [la, lb]
            print(f'#   (dW{r}[{i}], dW{r}[{j}]) forbidden={forbidden}, '
                  f'inject [{la}, {lb}]', file=sys.stderr)
        else:
            print(f'#   (dW{r}[{i}], dW{r}[{j}]): no fast UNSAT polarity',
                  file=sys.stderr)

    spec['preflight_wall_seconds'] = round(time.time() - t_total, 2)
    print(f'# preflight wall: {spec["preflight_wall_seconds"]}s', file=sys.stderr)

    # Count actionable
    n_units = sum(1 for u in spec['unit_clauses'] if u['forced'] is not None)
    n_pairs = sum(1 for p in spec['pair_clauses'] if p['forbidden_polarity'] is not None)
    print(f'# extracted: {n_units} unit clauses, {n_pairs} pair clauses',
          file=sys.stderr)

    out_text = json.dumps(spec, indent=2)
    if args.out:
        with open(args.out, 'w') as f:
            f.write(out_text)
        print(f'# wrote {args.out}', file=sys.stderr)
    else:
        print(out_text)


if __name__ == '__main__':
    main()
