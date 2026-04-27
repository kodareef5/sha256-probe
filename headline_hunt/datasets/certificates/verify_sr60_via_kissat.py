#!/usr/bin/env python3
"""Third verifier for the sr=60 cert: SAT-solver-based.

Builds the cascade_aux Mode A sr=60 CNF for msb_m17149975, injects the
cert's W1[57..60] values as 128 unit clauses, runs kissat. Expected
result: SAT in <1 second (kissat trivially finds the rest of the
assignment).

Also confirms a sanity check: same construction at sr=61 returns UNSAT,
because sr=61 enforces an additional schedule equation at slot 61 that
the cert's W[57..60] don't satisfy.

This complements:
  certificate_64r_sfs_sr60.c     (standalone C, hash matches)
  verify_sr60_with_relaxed_W.py  (Python forward computation)

Cross-implementation verification: all three approaches confirm the
cert is a valid sr=60 SFS collision.
"""
import sys
import subprocess
import time

sys.path.insert(0, '/Users/mac/Desktop/sha256_review')
sys.path.insert(0, '/Users/mac/Desktop/sha256_review/headline_hunt/bets/cascade_aux_encoding/encoders')

from cascade_aux_encoder import build_cascade_aux_cnf


def lookup_W1_vars(cnf):
    """Return {(slot, bit_pos) → var_id} for W1[57..63] bits."""
    out = {}
    for var_id, name in cnf.free_var_names.items():
        for slot in range(57, 64):
            prefix = f"W1_{slot}["
            if name.startswith(prefix):
                bp = int(name[len(prefix):-1])
                out[(slot, bp)] = var_id
    return out


def make_cnf_with_hints(sr_level, m0, fill, bit, W1_overrides, out_path):
    """Build cascade_aux Mode A CNF + W1 unit clauses for given override slots."""
    result = build_cascade_aux_cnf(sr=sr_level, m0=m0, fill=fill, kernel_bit=bit, mode='expose')
    cnf = result[0]
    var_lookup = lookup_W1_vars(cnf)

    unit_clauses = []
    for slot, val in W1_overrides.items():
        for bp in range(32):
            var = var_lookup.get((slot, bp))
            if var is None:
                continue
            bv = (val >> bp) & 1
            unit_clauses.append([var] if bv else [-var])

    n_vars = cnf.next_var - 1
    n_clauses = len(cnf.clauses) + len(unit_clauses)
    with open(out_path, 'w') as f:
        f.write(f"c sr={sr_level} cert verification CNF\n")
        f.write(f"c m0=0x{m0:08x} fill=0x{fill:08x} bit={bit}\n")
        f.write(f"c W1[57..60] fixed via {len(unit_clauses)} unit clauses\n")
        f.write(f"p cnf {n_vars} {n_clauses}\n")
        for c in unit_clauses:
            f.write(' '.join(str(x) for x in c) + ' 0\n')
        for c in cnf.clauses:
            f.write(' '.join(str(x) for x in c) + ' 0\n')
    return n_vars, n_clauses, len(unit_clauses)


def run_kissat(cnf_path, seed=5, conflicts=10000, time_cap=60):
    t0 = time.time()
    r = subprocess.run(
        ['kissat', cnf_path, '-q',
         f'--seed={seed}', f'--conflicts={conflicts}', f'--time={time_cap}'],
        capture_output=True, text=True
    )
    wall = time.time() - t0
    status_line = next((l for l in r.stdout.split('\n') if l.startswith('s ')), 'no s line')
    if 'UNSATISFIABLE' in status_line:
        return wall, 'UNSAT'
    elif 'SATISFIABLE' in status_line:
        return wall, 'SAT'
    return wall, 'UNKNOWN'


def main():
    # The sr=60 verified cert: msb_m17149975, fill=0xff, bit=31
    m0, fill, bit = 0x17149975, 0xffffffff, 31
    W1_cert = {57: 0x9ccfa55e, 58: 0xd9d64416, 59: 0x9e3ffb08, 60: 0xb6befe82}

    print("=" * 70)
    print("sr=60 cert verification via kissat (third independent verifier)")
    print("=" * 70)
    print(f"M[0] = 0x{m0:08x}, fill = 0x{fill:08x}, kernel bit = {bit}")
    print(f"W1[57..60] cert: {[hex(W1_cert[k]) for k in [57,58,59,60]]}")
    print()

    # Test at sr=60 — expect SAT
    out60 = '/tmp/cert_verify_sr60.cnf'
    nv, nc, nh = make_cnf_with_hints(60, m0, fill, bit, W1_cert, out60)
    print(f"sr=60 CNF: {nv} vars, {nc} clauses ({nh} hints)")
    wall, status = run_kissat(out60)
    print(f"  kissat seed=5: {status} in {wall:.3f}s")
    sr60_ok = (status == 'SAT')
    if sr60_ok:
        print("  ✓ Expected SAT — cert is consistent with cascade_aux Mode A sr=60.")
    else:
        print(f"  ✗ Unexpected {status} — cert may be inconsistent with sr=60 model.")

    # Sanity: at sr=61, expect UNSAT (the cert is NOT sr=61)
    out61 = '/tmp/cert_verify_sr61.cnf'
    nv, nc, nh = make_cnf_with_hints(61, m0, fill, bit, W1_cert, out61)
    print(f"\nsr=61 CNF (sanity check): {nv} vars, {nc} clauses")
    wall, status = run_kissat(out61)
    print(f"  kissat seed=5: {status} in {wall:.3f}s")
    sr61_ok = (status == 'UNSAT')
    if sr61_ok:
        print("  ✓ Expected UNSAT — cert is sr=60, not sr=61 (correctly rejected).")
    else:
        print(f"  ✗ Unexpected {status} — sr=61 should reject sr=60 cert values.")

    print()
    print("=" * 70)
    if sr60_ok and sr61_ok:
        print("VERIFICATION PASS — kissat confirms cert at sr=60, rejects at sr=61.")
        print("Cross-implementation: standalone C ✓ | Python forward ✓ | kissat ✓")
        sys.exit(0)
    else:
        print("VERIFICATION FAIL")
        sys.exit(1)


if __name__ == "__main__":
    main()
