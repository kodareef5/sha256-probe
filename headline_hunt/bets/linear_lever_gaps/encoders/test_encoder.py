#!/usr/bin/env python3
"""
test_encoder.py — HARD validation gate for lever_gap_encoder.py.

No new-config solve counts until this is green. Three independent checks:

  A. SELF-CONSISTENCY (schedule + round wiring, ANY config incl. deep tail_start):
     pin the free words to random values, collision=False, solve (unique model),
     read back the encoder's internal W[t] and final-state literals, and compare
     to an INDEPENDENT native recomputation. Run for the top-block config
     (tail_start=57) AND the linear-lever config (tail_start=54) — the latter is
     the only thing that exercises the deep t-7 lever / rounds 54..56 wiring.

  B. CERT-ACCEPTANCE (collision constraint, known-good): pin the known sr=60
     certificate witness and confirm the encoder's collision instance is SAT —
     for the top-block sr=60 (free {57..60}) and its sr=59 relaxation (free
     {57..61}, W[61] taken from the cert schedule).

  C. NEGATIVE CONTROL: flip one bit of the cert witness -> top-block sr=60
     collision instance must be UNSAT (the collision constraint actually bites).

A is the off-by-one catcher; B+C prove the collision constraint is correct and
non-vacuous. Independent oracle = verify_lever_collision.verify.
"""

import os
import random
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
BET = os.path.dirname(HERE)
REPO_ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
for p in (REPO_ROOT, BET):
    if p not in sys.path:
        sys.path.insert(0, p)

from lib.sha256 import MASK
from lever_gap_encoder import build_lever_gap_cnf, precompute_to
from verify_lever_collision import build_schedule, run64

CAND = dict(m0=0x17149975, fill=0xFFFFFFFF, kernel_bit=31)
CERT_W1 = {57: 0x9ccfa55e, 58: 0xd9d64416, 59: 0x9e3ffb08, 60: 0xb6befe82}
CERT_W2 = {57: 0x72e6c8cd, 58: 0x4b96ca51, 59: 0x587ffaa6, 60: 0xea3ce26b}


# ---------- low-level kissat-with-model helper ----------

def solve_with_model(cnf, extra_units=(), seed=1, timeout=120):
    """Write cnf (+ extra unit clauses) to a temp file, run kissat WITHOUT -q to
    capture the model. Returns (status, assignment dict {var: bool} or None)."""
    nv = cnf.next_var - 1
    clauses = cnf.clauses + [list(u) for u in extra_units]
    with tempfile.NamedTemporaryFile("w", suffix=".cnf", delete=False) as f:
        path = f.name
        f.write(f"p cnf {nv} {len(clauses)}\n")
        for c in clauses:
            f.write(" ".join(str(l) for l in c) + " 0\n")
    try:
        cmd = ["kissat", f"--seed={seed}", path]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if r.returncode == 20:
            return "UNSAT", None
        if r.returncode != 10:
            return ("TIMEOUT" if r.returncode == 0 else "UNKNOWN"), None
        assign = {}
        for line in r.stdout.splitlines():
            if line.startswith("v "):
                for tok in line[2:].split():
                    v = int(tok)
                    if v != 0:
                        assign[abs(v)] = (v > 0)
        return "SAT", assign
    finally:
        os.unlink(path)


def lit_val(lit, assign):
    if lit == 1:
        return True
    if lit == -1:
        return False
    val = assign[abs(lit)]
    return val if lit > 0 else (not val)


def word_val(arr, assign):
    """LSB-first 32-literal array -> int."""
    return sum((1 << i) for i in range(32) if lit_val(arr[i], assign))


def free_word_units(cnf, msg, pos, value):
    """Unit clauses pinning free word <msg>_<pos> (e.g. W1_57) to value."""
    inv = {name: var for var, name in cnf.free_var_names.items()}
    units = []
    for i in range(32):
        var = inv[f"{msg}_{pos}[{i}]"]
        units.append([var] if (value >> i) & 1 else [-var])
    return units


# ---------- A. self-consistency ----------

def check_self_consistency(free_positions, tail_start, label, rng):
    M1 = [CAND["m0"]] + [CAND["fill"]] * 15
    M2 = list(M1)
    M2[0] ^= (1 << CAND["kernel_bit"])
    M2[9] ^= (1 << CAND["kernel_bit"])

    free1 = {p: rng.getrandbits(32) for p in free_positions}
    free2 = {p: rng.getrandbits(32) for p in free_positions}

    cnf, summary, h = build_lever_gap_cnf(
        CAND["m0"], CAND["fill"], free_positions, kernel_bit=CAND["kernel_bit"],
        tail_start=tail_start, collision=False)

    units = []
    for p in free_positions:
        units += free_word_units(cnf, "W1", p, free1[p])
        units += free_word_units(cnf, "W2", p, free2[p])
    status, assign = solve_with_model(cnf, units)
    if status != "SAT":
        print(f"  [A:{label}] FAIL: pinned instance not SAT ({status})")
        return False

    # Independent native schedules/states for the SAME free words.
    W1n = build_schedule(M1, free1)
    W2n = build_schedule(M2, free2)
    fin1n = run64(W1n)
    fin2n = run64(W2n)

    ok = True
    # schedule words (held computed positions only)
    for t in range(tail_start, 64):
        if t in free_positions:
            continue
        e1 = word_val(h["Wsched1"][t], assign)
        e2 = word_val(h["Wsched2"][t], assign)
        if e1 != W1n[t] or e2 != W2n[t]:
            print(f"  [A:{label}] FAIL: W[{t}] encoder=(0x{e1:08x},0x{e2:08x}) "
                  f"native=(0x{W1n[t]:08x},0x{W2n[t]:08x})")
            ok = False
    # final state
    for i in range(8):
        e1 = word_val(h["final1"][i], assign)
        e2 = word_val(h["final2"][i], assign)
        if e1 != fin1n[i] or e2 != fin2n[i]:
            print(f"  [A:{label}] FAIL: final reg{i} encoder=(0x{e1:08x},0x{e2:08x}) "
                  f"native=(0x{fin1n[i]:08x},0x{fin2n[i]:08x})")
            ok = False
    # da@tailstart diagnostic sanity
    st1, _ = precompute_to(M1, tail_start)
    st2, _ = precompute_to(M2, tail_start)
    if summary["da_at_tailstart"] != f"0x{(st1[0]^st2[0]):08x}":
        print(f"  [A:{label}] FAIL: da_at_tailstart mismatch")
        ok = False

    if ok:
        print(f"  [A:{label}] PASS  sr={summary['sr']} tail_start={tail_start} "
              f"({summary['total_vars']} vars, {summary['total_clauses']} clauses) "
              f"— encoder schedule+state match native for random free words")
    return ok


# ---------- B. cert-acceptance ----------

def check_cert_acceptance():
    ok = True
    # top-block sr=60: free {57,58,59,60} = cert witness
    cnf60, s60, _ = build_lever_gap_cnf(
        CAND["m0"], CAND["fill"], {57, 58, 59, 60}, tail_start=57, collision=True)
    assert s60["sr"] == 60, f"expected sr=60, got {s60['sr']}"
    units = []
    for p in (57, 58, 59, 60):
        units += free_word_units(cnf60, "W1", p, CERT_W1[p])
        units += free_word_units(cnf60, "W2", p, CERT_W2[p])
    status, _ = solve_with_model(cnf60, units)
    if status == "SAT":
        print(f"  [B:sr60] PASS — top-block sr=60 collision instance accepts the cert witness")
    else:
        print(f"  [B:sr60] FAIL — cert witness gives {status} (encoder over-constrains?)")
        ok = False

    # sr=59 relaxation: free {57..61}; W[61] from the cert's own schedule.
    M1 = [CAND["m0"]] + [CAND["fill"]] * 15
    M2 = list(M1); M2[0] ^= (1 << 31); M2[9] ^= (1 << 31)
    W1c = build_schedule(M1, CERT_W1)
    W2c = build_schedule(M2, CERT_W2)
    f59_1 = dict(CERT_W1); f59_1[61] = W1c[61]
    f59_2 = dict(CERT_W2); f59_2[61] = W2c[61]
    cnf59, s59, _ = build_lever_gap_cnf(
        CAND["m0"], CAND["fill"], {57, 58, 59, 60, 61}, tail_start=57, collision=True)
    assert s59["sr"] == 59, f"expected sr=59, got {s59['sr']}"
    units = []
    for p in (57, 58, 59, 60, 61):
        units += free_word_units(cnf59, "W1", p, f59_1[p])
        units += free_word_units(cnf59, "W2", p, f59_2[p])
    status, _ = solve_with_model(cnf59, units)
    if status == "SAT":
        print(f"  [B:sr59] PASS — sr=59 relaxation accepts the cert-derived witness")
    else:
        print(f"  [B:sr59] FAIL — {status}")
        ok = False
    return ok


# ---------- C. negative control ----------

def check_negative_control():
    cnf60, s60, _ = build_lever_gap_cnf(
        CAND["m0"], CAND["fill"], {57, 58, 59, 60}, tail_start=57, collision=True)
    bad = dict(CERT_W1); bad[57] ^= 1   # flip one bit
    units = []
    for p in (57, 58, 59, 60):
        units += free_word_units(cnf60, "W1", p, bad[p])
        units += free_word_units(cnf60, "W2", p, CERT_W2[p])
    status, _ = solve_with_model(cnf60, units)
    if status == "UNSAT":
        print(f"  [C:neg] PASS — perturbed witness is UNSAT (collision constraint bites)")
        return True
    print(f"  [C:neg] FAIL — perturbed witness gives {status}, expected UNSAT")
    return False


def main():
    rng = random.Random(20260530)
    print("=== lever_gap_encoder validation gate ===")
    results = []
    print("A. self-consistency (encoder schedule+state vs independent native):")
    results.append(check_self_consistency({57, 58, 59, 60}, 57, "top-block sr60", rng))
    results.append(check_self_consistency({57, 58, 59, 60, 61}, 57, "top-block sr59", rng))
    results.append(check_self_consistency({54, 55, 56, 57}, 54, "LINEAR-LEVER sr60", rng))
    results.append(check_self_consistency({54, 55, 56}, 54, "LINEAR-LEVER sr61", rng))
    print("B. cert-acceptance (collision constraint, known-good):")
    results.append(check_cert_acceptance())
    print("C. negative control:")
    results.append(check_negative_control())

    ok = all(results)
    print(f"\nGATE {'PASSED' if ok else 'FAILED'} ({sum(results)}/{len(results)} checks)")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
