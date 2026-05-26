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
    """Return a CNFBuilder encoding the R-round block-2 absorber for `residual`."""
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
    return cnf


def solve_absorber(residual, R, name, timeout=600, outdir=None):
    outdir = outdir or os.path.join(HERE, "../results/cnf")
    os.makedirs(outdir, exist_ok=True)
    cnf = build_absorber_cnf(residual, R)
    path = os.path.join(outdir, f"absorber_{name}_R{R}.cnf")
    cnf.write_dimacs(path)
    status, _ = solver.run_kissat(path, timeout=timeout)
    return status, path, cnf


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
