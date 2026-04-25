#!/usr/bin/env python3
"""analyze_de58_validation.py — Process de58 validation matrix runs.

Reads runs.jsonl, filters runs from the 2026-04-25 de58 validation matrix,
correlates outcome (status, wall time at fixed conflict budget) against
de58-rank metrics from the candidate registry.

Outcome:
  - If any SAT/UNSAT in 10M cell → headline / definitive answer; stop.
  - If timing/conflict_count correlates with de58 rank → predictor validated.
  - If null correlation → de58 marked "structurally interesting but search-irrelevant".

Usage: python3 analyze_de58_validation.py
"""
import json
import os
import sys
from collections import defaultdict


REPO = os.path.abspath(os.path.dirname(__file__) + "/../../..")


def load_runs():
    path = os.path.join(REPO, "headline_hunt/registry/runs.jsonl")
    rows = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            rows.append(json.loads(line))
    return rows


def load_candidates():
    import yaml
    with open(os.path.join(REPO, "headline_hunt/registry/candidates.yaml")) as f:
        return yaml.safe_load(f)


def main():
    runs = load_runs()
    cands = load_candidates()
    # by candidate id, get de58 metrics
    metrics = {c['id']: c.get('metrics', {}) for c in cands}

    # filter validation-matrix runs (those with notes containing "de58 validation matrix")
    matrix = [r for r in runs if "de58 validation matrix" in (r.get('notes') or '')]
    if not matrix:
        print("No de58 validation matrix runs in runs.jsonl yet.")
        print("(Re-run after the matrix completes.)")
        return

    # group by (candidate, solver, budget)
    print(f"Found {len(matrix)} validation-matrix runs.")
    print()

    # candidates of interest
    target = ['cand_n32_bit19_m51ca0b34_fill55555555',
              'cand_n32_bit25_m09990bd2_fill80000000',
              'cand_n32_msb_m9cfea9ce_fill00000000',
              'cand_n32_msb_m189b13c7_fill80000000',
              'cand_n32_msb_m17149975_fillffffffff']
    # extract budget from notes
    def budget_of(r):
        n = r.get('notes', '')
        for tok in n.split():
            if tok.startswith('budget='):
                return int(tok.split('=')[1].rstrip(';'))
        return None

    table = defaultdict(dict)  # table[cand_id][(solver, budget)] = (status, wall, conflicts)
    for r in matrix:
        cand = r['candidate_id']
        solver = r['solver']
        budget = budget_of(r)
        wall = r.get('wall_seconds')
        status = r['status']
        # parse conflicts_actual from notes
        conflicts = None
        for tok in r['notes'].split():
            if tok.startswith('conflicts_actual='):
                v = tok.split('=')[1].rstrip(';')
                if v.isdigit(): conflicts = int(v)
        table[cand][(solver, budget)] = (status, wall, conflicts)

    # print structured table — order matches the cells loop (kissat 1M, kissat 10M, cadical 1M, cadical 10M)
    print(f"{'Candidate':42s} {'de58sz':>7} {'lockbits':>8}  k1M       k10M      c1M       c10M")
    rows = []
    for cand in target:
        m = metrics.get(cand, {})
        size = m.get('de58_size') or '?'
        lockb = m.get('de58_hardlock_bits') or '?'
        cells = []
        for solver in ('kissat', 'cadical'):
            for budget in (1000000, 10000000):
                v = table.get(cand, {}).get((solver, budget))
                if v is None:
                    cells.append((None, None, None))
                else:
                    cells.append(v)
        rows.append((cand, size, lockb, cells))

    for cand, size, lockb, cells in rows:
        line = f"{cand[-40:]:42s} {str(size):>7} {str(lockb):>8}"
        for status, wall, _ in cells:
            stcode = (status or '?')[0]
            wallstr = f"{int(wall)}s" if wall is not None else "  ?"
            line += f"  {stcode} {wallstr:>5}"
        print(line)

    # Decision rule
    print()
    sat_runs = [r for r in matrix if r['status'] == 'SAT']
    unsat_runs = [r for r in matrix if r['status'] == 'UNSAT']
    if sat_runs:
        print(f"!! SAT FOUND in {len(sat_runs)} cells — STOP, this is the headline. Cells:")
        for r in sat_runs:
            print(f"   {r['candidate_id']}, {r['solver']}, budget={budget_of(r)}, wall={r['wall_seconds']}s")
        return
    if unsat_runs:
        print(f"!! UNSAT FOUND in {len(unsat_runs)} cells — definitive answer for those candidates:")
        for r in unsat_runs:
            print(f"   {r['candidate_id']}, {r['solver']}, budget={budget_of(r)}, wall={r['wall_seconds']}s")

    # CPU-rate-independent metric: decisions per conflict from solver logs.
    print("\nDecisions/conflict from kissat 1M-conflict runs:")
    print("(CPU-rate-independent metric: lower = stronger propagation, smarter search)")
    print(f"{'Candidate':45s} {'de58sz':>7} {'lockbits':>8} {'dec/conf':>9} {'conf/s':>8}")
    by_dec = []
    for cand, size, lockb, cells in rows:
        # Find the kissat 1M log file
        logpath = None
        for r in matrix:
            if (r['candidate_id'] == cand and r['solver'] == 'kissat'
                    and budget_of(r) == 1000000):
                logpath = r.get('artifacts', [None])[0] if isinstance(r.get('artifacts'), list) else None
                if not logpath:
                    logpath = r.get('log')
                if not logpath:
                    # try canonical path
                    for tag, c, _, _ in [
                        ('bit19',     'cand_n32_bit19_m51ca0b34_fill55555555', 0, 0),
                        ('bit25',     'cand_n32_bit25_m09990bd2_fill80000000', 0, 0),
                        ('msb_surp',  'cand_n32_msb_m9cfea9ce_fill00000000', 0, 0),
                        ('msb_bot',   'cand_n32_msb_m189b13c7_fill80000000', 0, 0),
                        ('msb_cert',  'cand_n32_msb_m17149975_fillffffffff', 0, 0),
                    ]:
                        if c == cand:
                            logpath = f"headline_hunt/bets/sr61_n32/runs/de58_validation_2026-04-25/{tag}_kissat_1000000.log"
                            break
                break
        dec = conf_rate = None
        if logpath:
            try:
                with open(os.path.join(REPO, logpath)) as f:
                    for line in f:
                        # kissat format: "c decisions:    5036746     5.04 per conflict"
                        # cadical format different — kissat-only here
                        if line.startswith('c decisions:'):
                            parts = line.split()
                            for p in parts:
                                try:
                                    val = float(p)
                                    if val > 0 and val < 100:  # dec/conf is small
                                        dec = val
                                        break
                                except ValueError:
                                    pass
                        elif line.startswith('c conflicts:'):
                            parts = line.split()
                            for p in parts:
                                try:
                                    val = float(p)
                                    if 1000 < val < 1e9:  # conf/s is reasonable range
                                        conf_rate = val
                                        break
                                except ValueError:
                                    pass
            except FileNotFoundError:
                pass
        line = f"{cand[-43:]:45s} {str(size):>7} {str(lockb):>8} {str(dec or '?'):>9} {str(conf_rate or '?'):>8}"
        print(line)
        if size != '?' and dec is not None:
            try:
                by_dec.append((int(size), dec, cand))
            except (TypeError, ValueError):
                pass

    if by_dec:
        sizes = [s for s, _, _ in by_dec]
        decs = [d for _, d, _ in by_dec]
        if max(decs) - min(decs) > 0:
            spread = (max(decs) - min(decs)) / (sum(decs) / len(decs))
            print(f"\ndec/conf spread (max-min)/mean: {spread:.2%}")
            if spread < 0.20:
                print("  → SPREAD < 20%: weak signal. Likely no de58-rank prediction at this budget.")
            else:
                print("  → SPREAD > 20%: candidate-rank may matter; check direction below.")
        # Spearman rank correlation, rough
        sorted_by_size = sorted(zip(sizes, decs))
        ranks_size = list(range(len(sorted_by_size)))
        sorted_by_dec = sorted(zip(decs, sizes))
        # ... (skip full Spearman; just print sorted views)
    print()
    print("If wall is essentially flat across de58 sizes → de58 rank is structurally")
    print("interesting but search-irrelevant. Mark 'closed predictor' in TARGETS.md.")
    print("If wall correlates monotonically with de58 size → predictor validated, prioritize")
    print("compute on top-de58 candidates.")


if __name__ == "__main__":
    main()
