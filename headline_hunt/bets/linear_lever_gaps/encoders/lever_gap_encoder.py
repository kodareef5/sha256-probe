#!/usr/bin/env python3
"""
lever_gap_encoder.py — configurable gap-placement CNF encoder (N=32).

Generalizes the hardcoded sr59/sr60 encoders (lib/cnf_encoder.encode_collision,
cascade_aux_encoder) to:
  * an ARBITRARY set of free/relaxed schedule positions (not just the top block);
  * any tail_start (lowest free position), so deep linear levers (t-7/t-16) work;
  * an optional per-held-equation lever_assignment, used only for VALIDATION and
    the DIMACS header — the CNF computes every held word from the full recurrence
    regardless of which feedback term is "the lever" (the lever is implicit in
    which word is free).

It is an additive wrapper over lib.cnf_encoder.CNFBuilder (does NOT touch lib/,
does NOT call the bug-broken encode_collision). Build pattern follows the
bug-free cascade_aux_encoder.build_cascade_aux_cnf resolve_W idiom, generalized.

Schedule recurrence (mod 2^32):
    W[t] = sigma1(W[t-2]) + W[t-7] + sigma0(W[t-15]) + W[t-16]

A position t in [16,63]:
  * t < tail_start          -> precomputed constant (folded; no SAT vars)
  * t in free_positions     -> free SAT word (relaxed: equation NOT enforced)
  * otherwise (computed)     -> built from the recurrence (equation HELD)

sr = 16 + #{t in 16..63 : t not free}.
"""

import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from lib.cnf_encoder import CNFBuilder
from lib.sha256 import (K, IV, MASK, add, sigma0, sigma1, Sigma0, Sigma1,
                        Ch, Maj)

REG = ["a", "b", "c", "d", "e", "f", "g", "h"]
LEVER_OFFSET = {"sigma1_tm2": 2, "linear_tm7": 7, "sigma0_tm15": 15, "linear_tm16": 16}


def precompute_to(M, stop_round):
    """Run rounds 0..stop_round-1 natively; return (state_entering_stop_round,
    native_full_schedule W[0..63]). No free words exist below tail_start, so the
    sub-tail-start schedule and state are fully determined by M.
    """
    W = [w & MASK for w in M] + [0] * 48
    for t in range(16, 64):
        W[t] = add(sigma1(W[t - 2]), W[t - 7], sigma0(W[t - 15]), W[t - 16])
    a, b, c, d, e, f, g, h = IV
    for i in range(stop_round):
        T1 = add(h, Sigma1(e), Ch(e, f, g), K[i], W[i])
        T2 = add(Sigma0(a), Maj(a, b, c))
        h, g, f, e, d, c, b, a = g, f, e, add(d, T1), c, b, a, add(T1, T2)
    return (a, b, c, d, e, f, g, h), W


def build_lever_gap_cnf(m0, fill, free_positions, lever_assignment=None,
                        kernel_bit=31, tail_start=None, collision=True,
                        extra_free_message_word=None):
    """Build a configurable gap-placement CNF.

    Args:
      m0, fill: candidate message words (M = [m0] + [fill]*15).
      free_positions: iterable of expansion positions (16..63) to relax (free).
      lever_assignment: optional {held_pos: (lever_kind, lever_pos)} — validated
        (lever_pos must be free and == held_pos - offset(kind)) and recorded in
        the header. Does not change the clauses.
      kernel_bit: MSB-kernel difference bit (default 31). M2 = M1 ^ kernel at
        words 0 and 9.
      tail_start: lowest bit-blasted round (default min(free_positions)).
      collision: add the 8-register equality at round 63.
      extra_free_message_word: reserved for the sr=61 push (Phase 3); not yet
        implemented.

    Returns: (cnf, summary).
    """
    free_positions = set(free_positions)
    if not free_positions:
        raise ValueError("free_positions must be non-empty")
    if any(t < 16 or t > 63 for t in free_positions):
        raise ValueError("free_positions must lie in [16,63]")
    if extra_free_message_word is not None:
        raise NotImplementedError("extra_free_message_word is a Phase-3 feature")
    if tail_start is None:
        tail_start = min(free_positions)
    if tail_start > min(free_positions):
        raise ValueError("tail_start must be <= min(free_positions)")
    if tail_start < 16:
        raise ValueError("tail_start must be >= 16")

    # Validate lever_assignment if provided (metadata correctness).
    if lever_assignment:
        for held, (kind, lpos) in lever_assignment.items():
            if kind not in LEVER_OFFSET:
                raise ValueError(f"unknown lever kind {kind}")
            if held - LEVER_OFFSET[kind] != lpos:
                raise ValueError(f"lever {kind} for {held} must sit at {held-LEVER_OFFSET[kind]}, got {lpos}")
            if lpos not in free_positions:
                raise ValueError(f"lever word W[{lpos}] for held W[{held}] is not free")
            if held in free_positions:
                raise ValueError(f"held position {held} cannot also be free")

    # --- messages + precomputation ---
    M1 = [m0] + [fill] * 15
    M2 = list(M1)
    M2[0] ^= (1 << kernel_bit)
    M2[9] ^= (1 << kernel_bit)

    state1, W1_pre = precompute_to(M1, tail_start)
    state2, W2_pre = precompute_to(M2, tail_start)
    da_at_tailstart = state1[0] ^ state2[0]   # diagnostic only — NOT asserted

    cnf = CNFBuilder()
    s1 = tuple(cnf.const_word(v) for v in state1)
    s2 = tuple(cnf.const_word(v) for v in state2)

    # --- build schedule words for [tail_start, 63] ---
    Wsched1, Wsched2 = {}, {}

    def resolve(idx, pre, sched):
        return cnf.const_word(pre[idx]) if idx < tail_start else sched[idx]

    for t in range(tail_start, 64):
        if t in free_positions:
            Wsched1[t] = cnf.free_word(f"W1_{t}")
            Wsched2[t] = cnf.free_word(f"W2_{t}")
        else:
            # W[t] = sigma1(W[t-2]) + W[t-7] + sigma0(W[t-15]) + W[t-16]
            # const inputs fold automatically inside sigma1_w/sigma0_w/add_word.
            w1 = cnf.add_word(
                cnf.add_word(cnf.sigma1_w(resolve(t - 2, W1_pre, Wsched1)),
                             resolve(t - 7, W1_pre, Wsched1)),
                cnf.add_word(cnf.sigma0_w(resolve(t - 15, W1_pre, Wsched1)),
                             resolve(t - 16, W1_pre, Wsched1)))
            w2 = cnf.add_word(
                cnf.add_word(cnf.sigma1_w(resolve(t - 2, W2_pre, Wsched2)),
                             resolve(t - 7, W2_pre, Wsched2)),
                cnf.add_word(cnf.sigma0_w(resolve(t - 15, W2_pre, Wsched2)),
                             resolve(t - 16, W2_pre, Wsched2)))
            Wsched1[t] = w1
            Wsched2[t] = w2

    # --- bit-blast compression rounds [tail_start, 63] for both messages ---
    st1, st2 = s1, s2
    for r in range(tail_start, 64):
        st1 = cnf.sha256_round_correct(st1, K[r], Wsched1[r])
        st2 = cnf.sha256_round_correct(st2, K[r], Wsched2[r])

    # --- collision constraint ---
    if collision:
        for i in range(8):
            cnf.eq_word(st1[i], st2[i])

    sr = 16 + sum(1 for t in range(16, 64) if t not in free_positions)
    summary = {
        "sr": sr,
        "m0": f"0x{m0:08x}", "fill": f"0x{fill:08x}", "kernel_bit": kernel_bit,
        "free_positions": sorted(free_positions),
        "tail_start": tail_start,
        "tail_rounds": 64 - tail_start,
        "lever_assignment": {str(k): list(v) for k, v in (lever_assignment or {}).items()},
        "da_at_tailstart": f"0x{da_at_tailstart:08x}",
        "total_vars": cnf.next_var - 1,
        "total_clauses": len(cnf.clauses),
        "encoder_stats": dict(cnf.stats),
    }
    # Handles expose the encoder's internal literal arrays so a test harness can
    # read back the schedule/final-state values under a pinned free-word
    # assignment and compare to an independent native computation (validates the
    # schedule + round wiring for ANY config, incl. deep tail_start).
    handles = {
        "Wsched1": Wsched1, "Wsched2": Wsched2,
        "final1": st1, "final2": st2,
        "free_var_names": cnf.free_var_names,
    }
    return cnf, summary, handles


def write_dimacs_with_header(cnf, summary, out_path):
    """Write DIMACS with a metadata header that audit_cnf.py can read."""
    n_vars = cnf.next_var - 1
    n_clauses = len(cnf.clauses)
    with open(out_path, "w") as f:
        f.write("c lever_gap_encoder v1 — 2026-05-30\n")
        f.write(f"c sr={summary['sr']}  n=32  encoder=lever_gap\n")
        f.write(f"c m0={summary['m0']}  fill={summary['fill']}  kernel_bit={summary['kernel_bit']}\n")
        f.write(f"c free_positions={summary['free_positions']}\n")
        f.write(f"c tail_start={summary['tail_start']}  tail_rounds={summary['tail_rounds']}\n")
        f.write(f"c lever_assignment={summary['lever_assignment']}\n")
        f.write(f"c da_at_tailstart={summary['da_at_tailstart']} (diagnostic, not enforced)\n")
        f.write("c\n")
        f.write(f"p cnf {n_vars} {n_clauses}\n")
        for clause in cnf.clauses:
            f.write(" ".join(str(l) for l in clause) + " 0\n")
    return n_vars, n_clauses


def parse_levers(s):
    """'61:linear_tm7:54,62:linear_tm7:55' -> {61:('linear_tm7',54), ...}"""
    if not s:
        return None
    out = {}
    for part in s.split(","):
        held, kind, lpos = part.split(":")
        out[int(held)] = (kind, int(lpos))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--m0", required=True)
    ap.add_argument("--fill", required=True)
    ap.add_argument("--free", required=True, help="comma-separated free positions, e.g. 54,55,56,57")
    ap.add_argument("--levers", default=None,
                    help="optional, e.g. 61:linear_tm7:54,62:linear_tm7:55,63:linear_tm7:56")
    ap.add_argument("--kernel-bit", type=int, default=31)
    ap.add_argument("--tail-start", type=int, default=None)
    ap.add_argument("--out", required=True)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    m0 = int(args.m0, 16)
    fill = int(args.fill, 16)
    free = {int(x) for x in args.free.split(",")}
    levers = parse_levers(args.levers)

    cnf, summary, _handles = build_lever_gap_cnf(
        m0, fill, free, lever_assignment=levers,
        kernel_bit=args.kernel_bit, tail_start=args.tail_start)
    nv, nc = write_dimacs_with_header(cnf, summary, args.out)
    if not args.quiet:
        print(f"Wrote {args.out}: sr={summary['sr']} tail_start={summary['tail_start']} "
              f"({summary['tail_rounds']}r)  {nv} vars, {nc} clauses", file=sys.stderr)
        print(f"  free={summary['free_positions']}  da@tailstart={summary['da_at_tailstart']}",
              file=sys.stderr)


if __name__ == "__main__":
    main()
