#!/usr/bin/env python3
"""
cascade_aux_encoder.py — Cascade-auxiliary CNF encoder (N=32, sr=60/sr=61).

See ./SPEC.md for the design rationale (Theorems 1-4, Mode A / Mode B, etc.).

This is an *additive* wrapper around lib.cnf_encoder.CNFBuilder. It replicates the
standard encode_collision flow (because the upstream encoder has a minor bug re:
m1_override and is not directly callable for sr=60), but captures per-round state
so we can emit aux variables dX[r][i] = X1[r][i] XOR X2[r][i].

Usage:
  python3 cascade_aux_encoder.py --sr 60 --m0 0x17149975 --fill 0xffffffff \\
      --mode expose --out /tmp/aux_test.cnf

  python3 cascade_aux_encoder.py --sr 61 --m0 0x3304caa0 --fill 0x80000000 \\
      --kernel-bit 10 --mode force --out /tmp/aux_sr61.cnf

Modes:
  expose  — aux vars + tying only; solution set unchanged from standard.
  force   — aux vars + tying + cascade-structure hard constraints (Theorems 1-4).

Outputs DIMACS CNF with a comment header documenting mode, candidate, aux summary.
"""
import argparse
import os
import sys

# Make lib importable when run from repo root or elsewhere
HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from lib.cnf_encoder import CNFBuilder
from lib.sha256 import K, precompute_state, sigma0 as sigma0_py


REG_NAMES = ["a", "b", "c", "d", "e", "f", "g", "h"]


def build_cascade_aux_cnf(sr, m0, fill, kernel_bit=31, mode="expose"):
    """
    Build a cascade-auxiliary CNF.

    Args:
        sr: schedule-round level, 60 or 61
        m0: first message word (candidate)
        fill: fill word for M[1..15]
        kernel_bit: bit position of the MSB/kernel difference (31 = MSB kernel)
        mode: "expose" (default) or "force" — see SPEC.md

    Returns:
        (cnf, summary_dict) — CNFBuilder populated; summary has aux stats for header.
    """
    if sr not in (59, 60, 61):
        raise ValueError(f"sr must be 59/60/61, got {sr}")
    if mode not in ("expose", "force"):
        raise ValueError(f"mode must be 'expose' or 'force', got {mode}")

    # --- Build messages (same pattern as encode_collision) ---
    M1 = [m0] + [fill] * 15
    M2 = M1.copy()
    diff_mask = 1 << kernel_bit
    M2[0] ^= diff_mask
    M2[9] ^= diff_mask

    state1, W1_pre = precompute_state(M1)
    state2, W2_pre = precompute_state(M2)

    if state1[0] != state2[0]:
        raise RuntimeError(
            f"da[56] != 0 for this candidate: state1.a = {state1[0]:#x}, "
            f"state2.a = {state2[0]:#x}. This candidate is not cascade-eligible."
        )

    # n_free = number of free message words at rounds 57..
    # sr=59 → 5 free (57-61), sr=60 → 4 free (57-60), sr=61 → 3 free (57-59)
    # Actually encode_collision has: n_free = 5 if sr59 else 4. For sr=61,
    # W[60] is schedule-determined from W[58]. Extending: n_free = 64 - 57 - (64-sr) + 1?
    # Let's use: free rounds are 57..(sr - 1). sr=60 → 57,58,59,60? Hmm.
    # Per boundary proof: sr=60 has 4 free rounds (57-60), sr=61 has "5 free rounds (57-61)
    # BUT W[61] is also schedule-determined." Practically, sr=61 has 4 free rounds (57-60)
    # and the solver tries to solve with W[61] forced.
    # For consistency with existing TRUE_sr61 CNFs in cnfs_n32/, we use:
    # sr=59 → 5 free (57-61), sr=60 → 4 free (57-60), sr=61 → 3 free (57-59),
    # with W[60] schedule-determined for sr=61.
    n_free_map = {59: 5, 60: 4, 61: 3}
    n_free = n_free_map[sr]
    first_sched = 57 + n_free    # first schedule-determined round

    cnf = CNFBuilder()

    # --- Initial state (constants from precomputation) ---
    s1 = tuple(cnf.const_word(v) for v in state1)
    s2 = tuple(cnf.const_word(v) for v in state2)

    # --- Free schedule words ---
    w1_free = [cnf.free_word(f"W1_{57 + i}") for i in range(n_free)]
    w2_free = [cnf.free_word(f"W2_{57 + i}") for i in range(n_free)]

    W1_schedule = list(w1_free)
    W2_schedule = list(w2_free)

    # --- Schedule-determined words for rounds first_sched .. 63 ---
    # W[r] = sigma1(W[r-2]) + W[r-7] + sigma0(W[r-15]) + W[r-16]
    # For r >= first_sched: W[r-2] may be free (tail indexed) or schedule-determined.
    # W[r-7], W[r-15], W[r-16] come from W_pre (constants) when r-7, r-15, r-16 < 57.
    for r in range(first_sched, 64):
        idx_m2 = r - 2
        idx_m7 = r - 7
        idx_m15 = r - 15
        idx_m16 = r - 16

        # Resolve W[r-k] for M1/M2 — either schedule bit-array (if already built) or const.
        def resolve_W(idx, pre, schedule):
            if idx < 57:
                return cnf.const_word(pre[idx])
            # schedule index = idx - 57
            return schedule[idx - 57]

        w1_rm2 = resolve_W(idx_m2, W1_pre, W1_schedule)
        w2_rm2 = resolve_W(idx_m2, W2_pre, W2_schedule)
        # For the addition of precomputed schedule words, encode_collision computes
        # sigma0(W_pre[r-15]) as a constant:
        w1_rm15_sig0_const = cnf.const_word(sigma0_py(W1_pre[idx_m15])) if idx_m15 < 57 \
                              else cnf.sigma0_w(W1_schedule[idx_m15 - 57])
        w2_rm15_sig0_const = cnf.const_word(sigma0_py(W2_pre[idx_m15])) if idx_m15 < 57 \
                              else cnf.sigma0_w(W2_schedule[idx_m15 - 57])
        w1_rm7  = cnf.const_word(W1_pre[idx_m7])  if idx_m7  < 57 else W1_schedule[idx_m7  - 57]
        w2_rm7  = cnf.const_word(W2_pre[idx_m7])  if idx_m7  < 57 else W2_schedule[idx_m7  - 57]
        w1_rm16 = cnf.const_word(W1_pre[idx_m16]) if idx_m16 < 57 else W1_schedule[idx_m16 - 57]
        w2_rm16 = cnf.const_word(W2_pre[idx_m16]) if idx_m16 < 57 else W2_schedule[idx_m16 - 57]

        w1_r = cnf.add_word(cnf.add_word(cnf.sigma1_w(w1_rm2), w1_rm7),
                            cnf.add_word(w1_rm15_sig0_const, w1_rm16))
        w2_r = cnf.add_word(cnf.add_word(cnf.sigma1_w(w2_rm2), w2_rm7),
                            cnf.add_word(w2_rm15_sig0_const, w2_rm16))
        W1_schedule.append(w1_r)
        W2_schedule.append(w2_r)

    # --- Run 7 rounds, capturing per-round state ---
    states1 = [s1]   # states1[i] = state AFTER round 56 + i
    states2 = [s2]
    st1, st2 = s1, s2
    for i in range(7):
        st1 = cnf.sha256_round_correct(st1, K[57 + i], W1_schedule[i])
        states1.append(st1)
        st2 = cnf.sha256_round_correct(st2, K[57 + i], W2_schedule[i])
        states2.append(st2)

    # states1[r - 56] gives state after round r, where r is the round that produced it.
    # Convention used below: `state_at_round(r)` returns states[1 + (r - 57)] = states[r - 56].
    def s_at(states, r):
        return states[r - 56]

    # --- Emit aux variables: dX[r][i] = X1[r][i] XOR X2[r][i] ---
    aux_reg = {}   # aux_reg[(reg_name, r)] = list of 32 literals (var IDs or ±1 constants)
    vars_before_aux = cnf.next_var - 1
    clauses_before_aux = len(cnf.clauses)

    # Also expose ACTUAL register-value literals (pair-1 and pair-2) for the
    # propagator (Rule 4 at r=62, r=63 needs Sigma0/Maj on actual values, not
    # just diffs). These are NOT new variables — they're the existing
    # round-state vars from the encoder; we just record their identity.
    actual_reg_p1 = {}  # actual_reg_p1[(reg_name, r)] = list of 32 literals
    actual_reg_p2 = {}

    for r in range(57, 64):
        for reg_idx, reg_name in enumerate(REG_NAMES):
            w1 = s_at(states1, r)[reg_idx]
            w2 = s_at(states2, r)[reg_idx]
            aux_reg[(reg_name, r)] = [cnf.xor2(w1[i], w2[i]) for i in range(32)]
            actual_reg_p1[(reg_name, r)] = list(w1)
            actual_reg_p2[(reg_name, r)] = list(w2)

    # dW[r] aux
    aux_W = {}
    for r_idx in range(7):
        r = 57 + r_idx
        w1r = W1_schedule[r_idx]
        w2r = W2_schedule[r_idx]
        aux_W[r] = [cnf.xor2(w1r[i], w2r[i]) for i in range(32)]

    aux_vars_added = cnf.next_var - 1 - vars_before_aux
    aux_clauses_added = len(cnf.clauses) - clauses_before_aux

    # --- Force-cascade clauses (Mode B) ---
    force_clauses_added = 0

    def unit_false(lit):
        """Add clause that forces lit to FALSE. Handles constant-folded cases."""
        nonlocal force_clauses_added
        if lit == -1:
            return  # already false; no clause needed
        if lit == 1:
            cnf.clauses.append([])   # UNSAT — force-cascade incompatible with this candidate
            force_clauses_added += 1
            return
        cnf.clauses.append([-lit])
        force_clauses_added += 1

    def eq_bits(a, b):
        """Add clauses a <=> b. Handles constants."""
        nonlocal force_clauses_added
        if a == 1 and b == 1: return
        if a == -1 and b == -1: return
        if a == 1 and b == -1: cnf.clauses.append([]); force_clauses_added += 1; return
        if a == -1 and b == 1: cnf.clauses.append([]); force_clauses_added += 1; return
        if a == 1:  cnf.clauses.append([b]);  force_clauses_added += 1; return
        if a == -1: cnf.clauses.append([-b]); force_clauses_added += 1; return
        if b == 1:  cnf.clauses.append([a]);  force_clauses_added += 1; return
        if b == -1: cnf.clauses.append([-a]); force_clauses_added += 1; return
        # Both are SAT vars
        cnf.clauses.append([-a, b])
        cnf.clauses.append([a, -b])
        force_clauses_added += 2

    if mode == "force":
        # Theorem 1 — cascade diagonal (rounds 57-60)
        diagonal = [("a", range(57, 61)),
                    ("b", range(58, 61)),
                    ("c", range(59, 61)),
                    ("d", range(60, 61))]
        for reg, rs in diagonal:
            for r in rs:
                for lit in aux_reg[(reg, r)]:
                    unit_false(lit)
        # Theorem 2 — dE[60] = 0
        for lit in aux_reg[("e", 60)]:
            unit_false(lit)
        # Theorem 4 — dA[61] = dE[61]
        for i in range(32):
            eq_bits(aux_reg[("a", 61)][i], aux_reg[("e", 61)][i])
        # Theorem 3 — three-filter at r = 61, 62, 63
        for r in (61, 62, 63):
            for lit in aux_reg[("e", r)]:
                unit_false(lit)
        # In force mode, the three-filter at dE[61..63]=0 combined with da=de at r>=61
        # and cascade through r=60 IS EQUIVALENT to the full 8-reg collision (Theorem 3).
        # We skip the explicit collision constraint to avoid redundancy.
    else:
        # Expose mode: standard full-collision constraint at round 63
        for reg_idx in range(8):
            cnf.eq_word(s_at(states1, 63)[reg_idx], s_at(states2, 63)[reg_idx])

    summary = {
        "sr": sr,
        "m0": f"0x{m0:08x}",
        "fill": f"0x{fill:08x}",
        "kernel_bit": kernel_bit,
        "mode": mode,
        "n_free": n_free,
        "total_vars": cnf.next_var - 1,
        "total_clauses": len(cnf.clauses),
        "aux_vars_added": aux_vars_added,
        "aux_clauses_added": aux_clauses_added,
        "force_clauses_added": force_clauses_added,
        "encoder_stats": dict(cnf.stats),
    }
    # aux_reg[(reg, r)] = list of 32 literals (var IDs or ±1 constants)
    # aux_W[r] = list of 32 literals
    # actual_reg_p1[(reg, r)] / actual_reg_p2[(reg, r)] = 32 literals for pair values
    return cnf, summary, aux_reg, aux_W, actual_reg_p1, actual_reg_p2


def write_varmap_sidecar(aux_reg, aux_W, summary, out_path,
                          actual_reg_p1=None, actual_reg_p2=None):
    """Emit a JSON sidecar mapping aux differential bits to SAT vars.

    Schema (version 2 adds actual register-value vars for Rule 4 at r=62,r=63):
      {
        "version": 2,
        "summary": {sr, m0, fill, kernel_bit, mode, total_vars, ...},
        "aux_reg": {"<reg>_<round>": [32 ints]},   # diff aux (XOR diff)
        "aux_W":   {"<round>":       [32 ints]},   # W diff aux
        "actual_p1": {"<reg>_<round>": [32 ints]}, # pair-1 actual register vars
        "actual_p2": {"<reg>_<round>": [32 ints]}  # pair-2 actual register vars
      }

    Literal convention: positive int = SAT variable ID; negative = negated;
    1 = constant TRUE; -1 = constant FALSE. Mirrors aux_reg semantics in the
    encoder's in-memory state.

    Backwards compat: version 1 sidecars (no actual_p1/p2) still parse — the
    propagator's varmap_loader treats them as missing and skips Rule 4 r=62/63.
    """
    import json
    out = {
        "version": 2 if actual_reg_p1 is not None else 1,
        "summary": {k: summary[k] for k in
                    ["sr", "m0", "fill", "kernel_bit", "mode", "n_free",
                     "total_vars", "total_clauses", "aux_vars_added",
                     "aux_clauses_added", "force_clauses_added"]},
        "aux_reg": {},
        "aux_W": {},
    }
    for (reg, r), lits in aux_reg.items():
        out["aux_reg"][f"{reg}_{r}"] = [int(x) for x in lits]
    for r, lits in aux_W.items():
        out["aux_W"][str(r)] = [int(x) for x in lits]
    if actual_reg_p1 is not None:
        out["actual_p1"] = {}
        out["actual_p2"] = {}
        for (reg, r), lits in actual_reg_p1.items():
            out["actual_p1"][f"{reg}_{r}"] = [int(x) for x in lits]
        for (reg, r), lits in actual_reg_p2.items():
            out["actual_p2"][f"{reg}_{r}"] = [int(x) for x in lits]
    with open(out_path, "w") as f:
        json.dump(out, f)
    return out_path


def write_dimacs_with_header(cnf, summary, out_path):
    """Write DIMACS to file with a metadata comment header."""
    n_vars = cnf.next_var - 1
    n_clauses = len(cnf.clauses)
    with open(out_path, "w") as f:
        # Metadata comments
        f.write(f"c cascade_aux_encoder v1 — 2026-04-24\n")
        f.write(f"c sr={summary['sr']}  n=32  mode={summary['mode']}\n")
        f.write(f"c m0={summary['m0']}  fill={summary['fill']}  kernel_bit={summary['kernel_bit']}\n")
        f.write(f"c n_free={summary['n_free']}\n")
        f.write(f"c aux_vars={summary['aux_vars_added']}  aux_clauses={summary['aux_clauses_added']}"
                f"  force_clauses={summary['force_clauses_added']}\n")
        f.write(f"c\n")
        if summary['mode'] == 'force':
            f.write(f"c MODE=force: cascade structure is enforced via Theorems 1-4.\n")
            f.write(f"c   Solution set is restricted to cascade-DP solutions.\n")
            f.write(f"c   For sr=61, a fast UNSAT under this encoding proves only that no\n")
            f.write(f"c   CASCADE-DP solution exists — non-cascade routes are out of scope.\n")
        else:
            f.write(f"c MODE=expose: aux vars + tying only; solution set unchanged.\n")
        f.write(f"c\n")
        f.write(f"p cnf {n_vars} {n_clauses}\n")
        for clause in cnf.clauses:
            f.write(" ".join(str(l) for l in clause) + " 0\n")
    return n_vars, n_clauses


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sr", type=int, required=True, choices=[59, 60, 61])
    ap.add_argument("--m0", required=True, help="M[0] as 0x... hex")
    ap.add_argument("--fill", required=True, help="fill word for M[1..15] as 0x...")
    ap.add_argument("--kernel-bit", type=int, default=31,
                    help="Kernel difference bit (31=MSB, 0=LSB, etc). Default 31.")
    ap.add_argument("--mode", choices=["expose", "force"], default="expose")
    ap.add_argument("--out", required=True, help="output .cnf path")
    ap.add_argument("--varmap", default=None,
                    help="Also emit JSON varmap sidecar to this path. "
                         "If '+' or 'auto', use <out>.varmap.json. "
                         "Useful for hooking the propagator to the CNF.")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    m0 = int(args.m0, 16)
    fill = int(args.fill, 16)

    if not args.quiet:
        print(f"Building cascade-aux CNF: sr={args.sr} m0={m0:#x} fill={fill:#x} "
              f"bit={args.kernel_bit} mode={args.mode}", file=sys.stderr)

    cnf, summary, aux_reg, aux_W, actual_p1, actual_p2 = build_cascade_aux_cnf(
        args.sr, m0, fill, args.kernel_bit, args.mode)
    n_vars, n_clauses = write_dimacs_with_header(cnf, summary, args.out)

    varmap_path = None
    if args.varmap is not None:
        varmap_path = (args.out + ".varmap.json"
                       if args.varmap in ("+", "auto") else args.varmap)
        write_varmap_sidecar(aux_reg, aux_W, summary, varmap_path,
                             actual_p1, actual_p2)

    if not args.quiet:
        print(f"Wrote {args.out}: {n_vars} vars, {n_clauses} clauses", file=sys.stderr)
        print(f"  aux vars: {summary['aux_vars_added']}  "
              f"aux clauses: {summary['aux_clauses_added']}  "
              f"force clauses: {summary['force_clauses_added']}", file=sys.stderr)
        if varmap_path:
            print(f"  varmap: {varmap_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
