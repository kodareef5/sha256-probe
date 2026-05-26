#!/usr/bin/env python3
"""CNF encoding of the block-2 absorber, for a real CDCL solver (kissat).

The naive guess-and-determine search (wang_search.run_search) reaches only R=15 before its
exponential wall, and propagation cannot decide R>=18 either way. A real CDCL solver is the
proper tool for the clean >18-round verdict (and could find a positive/headline result).

Encoding (reuses lib.cnf_encoder.CNFBuilder -- no SHA-256 reimplementation):
  - chaining value CV (instance 1) = 8 free words; instance 2 = CV XOR residual (the block-1
    residual difference enters block 2 as the input state difference);
  - message words W1[0..15], W2[0..15] free and INDEPENDENT (message modification), expanded
    by the real message schedule for t>=16;
  - R rounds of sha256_round_correct per instance;
  - collision target: state1[R] == state2[R]  (a genuine R-round absorber: nonzero input
    difference, zero output difference).
SAT  => an R-round absorber EXISTS (extract+oracle-check the two messages to confirm).
UNSAT => provably no R-round absorber for this residual (clean, not a timeout).

Self-test validates the encoding against the engine's known results: bit13 R=4 is UNSAT
(engine: infeasible) and R=8 is SAT (engine: 8-round absorber, oracle-confirmed).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "../../../..")))

import lib.cnf_encoder as ce
import lib.sha256 as L
import lib.solver as solver

CLUSTERS = {
    "bit13_HW35": [0xd8581011, 0xa004804c, 0x80000000, 0, 0x8007828a, 0x1864c, 0x80000000, 0],
    "bit14_HW94": [0x81dd7b67, 0xc8faae8a, 0x89a6ce84, 0, 0x7578f489, 0x9422c625, 0x96a27e84, 0],
    "bit6_HW93":  [0x0b66bc09, 0x985abf71, 0xc2aa8166, 0, 0xbba8a282, 0x96bf5d52, 0xc75e8322, 0],
    "bit15_HW97": [0x68e89203, 0xb75cba78, 0x458770d6, 0, 0xbdc47d99, 0x607ae1d0, 0xc5fd513a, 0],
    "bit24_HW101":[0xbf540a5e, 0xf28d16c4, 0x1c4d5e75, 0, 0x6ee27f85, 0x9b807e37, 0x03c34dd7, 0],
    "bit28_HW94": [0xfbf3b4e0, 0x51ba3d55, 0xfa1869d3, 0, 0x604e0522, 0x283b4292, 0x7a186e77, 0],
}


def build_absorber_cnf(residual, R):
    """Encode the R-round block-2 absorber. Returns (cnf, refs) where refs holds the
    input free-word variable lists {cv1, W1, W2} for model extraction."""
    cnf = ce.CNFBuilder()
    cv1 = [cnf.free_word(f"CV1_{j}") for j in range(8)]
    cv2 = [cnf.xor_word(cv1[j], cnf.const_word(residual[j])) for j in range(8)]

    def schedule(prefix):
        W = [cnf.free_word(f"{prefix}_{t}") for t in range(16)]
        for t in range(16, R):
            s1 = cnf.sigma1_w(W[t - 2])
            s0 = cnf.sigma0_w(W[t - 15])
            W.append(cnf.add_word(cnf.add_word(s1, W[t - 7]),
                                  cnf.add_word(s0, W[t - 16])))
        return W

    W1, W2 = schedule("W1"), schedule("W2")
    st1, st2 = tuple(cv1), tuple(cv2)
    for t in range(R):
        st1 = cnf.sha256_round_correct(st1, L.K[t], W1[t])
        st2 = cnf.sha256_round_correct(st2, L.K[t], W2[t])
    for j in range(8):
        cnf.eq_word(st1[j], st2[j])         # collision target
    return cnf, {"cv1": cv1, "W1": W1[:16], "W2": W2[:16]}


def solve_absorber(residual, R, name, timeout=600, outdir=None):
    outdir = outdir or os.path.join(HERE, "../results/cnf")
    os.makedirs(outdir, exist_ok=True)
    cnf, refs = build_absorber_cnf(residual, R)
    path = os.path.join(outdir, f"absorber_{name}_R{R}.cnf")
    cnf.write_dimacs(path)
    status, out = solver.run_kissat(path, timeout=timeout)
    return status, path, (cnf, refs, out)


def _model_true_vars(stdout):
    true = set()
    for line in (stdout or "").splitlines():
        if line.startswith("v"):
            for tok in line.split()[1:]:
                v = int(tok)
                if v > 0:
                    true.add(v)
    return true


def _word_val(bits, true):
    return sum((1 << i) for i, b in enumerate(bits) if b in true)


def oracle_verify(residual, R, refs, stdout):
    """Reconstruct CV1, W1[0..15], W2[0..15] from a SAT model and confirm via lib.sha256
    that the two block-2 messages collide after R rounds with input difference = residual.
    Returns (ok, info)."""
    true = _model_true_vars(stdout)
    if not true:
        return None, "no model in solver output (re-run capturing witness)"
    cv1 = [_word_val(w, true) for w in refs["cv1"]]
    cv2 = [c ^ d for c, d in zip(cv1, residual)]
    w1 = [_word_val(w, true) for w in refs["W1"]]
    w2 = [_word_val(w, true) for w in refs["W2"]]

    def expand(W):
        W = list(W)
        for t in range(16, R):
            W.append(L.add(L.sigma1(W[t - 2]), W[t - 7], L.sigma0(W[t - 15]), W[t - 16]))
        return W

    def run(cv, W):
        st = list(cv)
        Wf = expand(W)
        for t in range(R):
            a, b, c, d, e, f, g, h = st
            t1 = L.add(h, L.Sigma1(e), L.Ch(e, f, g), L.K[t], Wf[t])
            t2 = L.add(L.Sigma0(a), L.Maj(a, b, c))
            st = [L.add(t1, t2), a, b, c, L.add(d, t1), e, f, g]
        return st
    out1, out2 = run(cv1, w1), run(cv2, w2)
    in_diff = [a ^ b for a, b in zip(cv1, cv2)]
    out_diff = [a ^ b for a, b in zip(out1, out2)]
    ok = (in_diff == residual) and all(d == 0 for d in out_diff) and (w1 != w2 or cv1 != cv2)
    return ok, {"in_diff_ok": in_diff == residual, "out_collision": all(d == 0 for d in out_diff),
                "msg_diff_hw": sum(bin(a ^ b).count("1") for a, b in zip(w1, w2))}


def _selftest():
    # Validate the encoding against the engine's known results for bit13.
    diff = CLUSTERS["bit13_HW35"]
    s4, _, _ = solve_absorber(diff, 4, "bit13_HW35", timeout=120)
    assert s4 == "UNSAT", f"R=4 expected UNSAT (engine: infeasible), got {s4}"
    s8, _, _ = solve_absorber(diff, 8, "bit13_HW35", timeout=120)
    assert s8 == "SAT", f"R=8 expected SAT (engine: 8-round absorber), got {s8}"
    print("absorber_cnf self-test: PASS")
    print("  bit13 R=4 -> UNSAT, R=8 -> SAT (matches the engine; encoding validated)")


if __name__ == "__main__":
    _selftest()
