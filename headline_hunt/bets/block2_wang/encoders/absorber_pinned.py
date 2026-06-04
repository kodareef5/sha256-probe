#!/usr/bin/env python3
"""absorber_pinned.py — CV-PINNED feed-forward block-2 absorber.

The meaningful 2-block test: block-2's input chaining values CV1, CV2 are PINNED
to a real block-1 near-collision's outputs (not free). We compute CV1, CV2 by
running block-1 (64 rounds + Davies-Meyer feed-forward) from a concrete witness
(m0/fill + W1[57..60], W2[57..60]), then ask: do block-2 messages M1 != M2 exist
such that the fed-forward block-2 hashes collide (H1 == H2) after R rounds?

This removes the "free CV cheats" loophole of absorber_feedforward.py: with CV
pinned, the only freedom is the block-2 messages. SAT here at R=64 (modulo the
final feed-forward) would be a genuine 2-block step. Reuses lib only.
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "../../../..")))

import lib.cnf_encoder as ce
import lib.sha256 as L
import lib.solver as solver

# First record of residuals/top50_lowest_hw.jsonl (lowest-HW block-1 near-collision).
WITNESS = {
    "m0": 0x17149975, "fill": 0xffffffff, "kernel_bit": 31,
    "W1_57_60": [0x03005549, 0xf92fc14b, 0x7c37f322, 0xb6befe82],
    "W2_57_60": [0xd91778b8, 0x6db78765, 0x693529aa, 0xbda0080f],
}


def block1_outputs(w):
    """Run block-1 for both messages (MSB kernel) and return (CV1, CV2) =
    post-feed-forward chaining values, plus the residual = CV1 ^ CV2."""
    kb = w["kernel_bit"]
    M1 = [w["m0"]] + [w["fill"]] * 15
    M2 = list(M1); M2[0] ^= (1 << kb); M2[9] ^= (1 << kb)

    def run_block1(M, free4):
        _, Wpre = L.precompute_state(M)           # W[0..56]
        tail = L.build_schedule_tail(Wpre, free4)  # W[57..63]
        W = list(Wpre) + list(tail)                # W[0..63]
        a, b, c, d, e, f, g, h = L.IV
        for t in range(64):
            t1 = L.add(h, L.Sigma1(e), L.Ch(e, f, g), L.K[t], W[t])
            t2 = L.add(L.Sigma0(a), L.Maj(a, b, c))
            h, g, f, e, d, c, b, a = g, f, e, L.add(d, t1), c, b, a, L.add(t1, t2)
        fs = (a, b, c, d, e, f, g, h)
        return [L.add(L.IV[j], fs[j]) for j in range(8)]   # Davies-Meyer feed-forward

    CV1 = run_block1(M1, w["W1_57_60"])
    CV2 = run_block1(M2, w["W2_57_60"])
    residual = [CV1[j] ^ CV2[j] for j in range(8)]
    return CV1, CV2, residual


def build_pinned_cnf(CV1, CV2, R):
    """Block-2 with CV1, CV2 pinned (constants); free messages; feed-forward
    collision target H1 == H2 where H = CV + state[R] (mod)."""
    cnf = ce.CNFBuilder()
    cv1 = [cnf.const_word(CV1[j]) for j in range(8)]
    cv2 = [cnf.const_word(CV2[j]) for j in range(8)]

    def schedule(prefix):
        W = [cnf.free_word(f"{prefix}_{t}") for t in range(16)]
        for t in range(16, R):
            W.append(cnf.add_word(cnf.add_word(cnf.sigma1_w(W[t - 2]), W[t - 7]),
                                  cnf.add_word(cnf.sigma0_w(W[t - 15]), W[t - 16])))
        return W

    W1, W2 = schedule("W1"), schedule("W2")
    st1, st2 = tuple(cv1), tuple(cv2)
    for t in range(R):
        st1 = cnf.sha256_round_correct(st1, L.K[t], W1[t])
        st2 = cnf.sha256_round_correct(st2, L.K[t], W2[t])
    for j in range(8):
        h1 = cnf.add_word(cv1[j], list(st1[j]))
        h2 = cnf.add_word(cv2[j], list(st2[j]))
        cnf.eq_word(h1, h2)
    return cnf, {"cv1": CV1, "cv2": CV2, "W1": W1[:16], "W2": W2[:16], "R": R}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--R", type=int, default=None)
    ap.add_argument("--timeout", type=int, default=600)
    ap.add_argument("--info", action="store_true", help="just print CV1/CV2/residual")
    args = ap.parse_args()

    CV1, CV2, residual = block1_outputs(WITNESS)
    hw = sum(bin(r).count("1") for r in residual)
    print(f"block-1 witness (m0=0x{WITNESS['m0']:08x}): post-FF residual HW={hw}")
    print(f"  CV1 = {[hex(x) for x in CV1]}")
    print(f"  CV2 = {[hex(x) for x in CV2]}")
    print(f"  residual = {[hex(x) for x in residual]}")
    if args.info or args.R is None:
        return

    cnf, refs = build_pinned_cnf(CV1, CV2, args.R)
    outdir = os.path.join(HERE, "../results/cnf_pinned"); os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, f"pinned_ff_R{args.R}.cnf")
    nv, ncl = cnf.write_dimacs(path)
    status, out = solver.run_kissat(path, timeout=args.timeout)
    print(f"[CV-pinned feed-forward R={args.R}] {status}  ({nv} vars, {ncl} clauses)")


if __name__ == "__main__":
    main()
