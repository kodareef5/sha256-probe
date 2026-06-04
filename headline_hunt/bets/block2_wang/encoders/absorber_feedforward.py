#!/usr/bin/env python3
"""absorber_feedforward.py — block-2 absorber with the CORRECT Davies-Meyer
feed-forward collision target.

The existing absorber_cnf.py forces state1[R] == state2[R] (working-state diff
ΔC = 0). But a real 2-block hash collision needs the FED-FORWARD outputs to
collide: H = CV + state[R] (mod 2^32), so

    H1 == H2  <=>  CV1 + state1[R] == CV2 + state2[R]  <=>  ΔC = -Δcv  (modular)

With Δcv ≠ 0 (the block-1 residual) and ΔC = 0, the fed-forward outputs differ by
Δcv ≠ 0 — NOT a collision. So absorber_cnf.py's R=18 result targets the wrong
condition. This script targets the correct one and lets us compare the round
frontier of the two conditions.

Scope of THIS probe: CV is FREE (free-start) — a necessary-condition / cheap
signal. If even free-start feed-forward absorption walls at ~18 like ΔC=0, the
multi-block route is confirmed hard. If it reaches deeper, CV-pinning is the next
question. Reuses lib.cnf_encoder.CNFBuilder + lib.sha256 (no SHA reimpl).
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "../../../..")))

import lib.cnf_encoder as ce
import lib.sha256 as L
import lib.solver as solver

# Same residual clusters as absorber_cnf.py (block-1 round-63 working-state XOR diffs).
CLUSTERS = {
    "bit13_HW35": [0xd8581011, 0xa004804c, 0x80000000, 0, 0x8007828a, 0x1864c, 0x80000000, 0],
    "bit14_HW94": [0x81dd7b67, 0xc8faae8a, 0x89a6ce84, 0, 0x7578f489, 0x9422c625, 0x96a27e84, 0],
    "bit24_HW101":[0xbf540a5e, 0xf28d16c4, 0x1c4d5e75, 0, 0x6ee27f85, 0x9b807e37, 0x03c34dd7, 0],
}


def build_ff_absorber_cnf(residual, R, target="feedforward", diff_words=None):
    """Encode the R-round block-2 absorber.

    target='feedforward' (correct): H1 == H2 where H = CV + state[R] (mod).
    target='working'     (the old absorber_cnf.py condition): state1[R]==state2[R].
    """
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
    if diff_words is not None:
        allow = set(diff_words)
        for t in range(16):
            if t not in allow:
                cnf.eq_word(W1[t], W2[t])
    st1, st2 = tuple(cv1), tuple(cv2)
    for t in range(R):
        st1 = cnf.sha256_round_correct(st1, L.K[t], W1[t])
        st2 = cnf.sha256_round_correct(st2, L.K[t], W2[t])

    if target == "feedforward":
        # H1[j] = cv1[j] + st1[j] (mod), H2[j] = cv2[j] + st2[j]; require H1 == H2.
        for j in range(8):
            h1 = cnf.add_word(cv1[j], list(st1[j]))
            h2 = cnf.add_word(cv2[j], list(st2[j]))
            cnf.eq_word(h1, h2)
    elif target == "working":
        for j in range(8):
            cnf.eq_word(st1[j], st2[j])
    else:
        raise ValueError(target)
    return cnf, {"cv1": cv1, "W1": W1[:16], "W2": W2[:16], "target": target, "R": R,
                 "residual": residual}


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


def oracle_verify_ff(refs, stdout):
    """Confirm via lib.sha256 that the two block-2 messages give H1 == H2
    (fed-forward) with input chaining diff == residual."""
    true = _model_true_vars(stdout)
    if not true:
        return None, "no model in solver output"
    residual, R = refs["residual"], refs["R"]
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
        st = list(cv); Wf = expand(W)
        for t in range(R):
            a, b, c, d, e, f, g, h = st
            t1 = L.add(h, L.Sigma1(e), L.Ch(e, f, g), L.K[t], Wf[t])
            t2 = L.add(L.Sigma0(a), L.Maj(a, b, c))
            st = [L.add(t1, t2), a, b, c, L.add(d, t1), e, f, g]
        return st
    out1, out2 = run(cv1, w1), run(cv2, w2)
    H1 = [L.add(cv1[j], out1[j]) for j in range(8)]
    H2 = [L.add(cv2[j], out2[j]) for j in range(8)]
    in_diff = [a ^ b for a, b in zip(cv1, cv2)]
    ok = (in_diff == residual) and (H1 == H2) and (w1 != w2 or cv1 != cv2)
    return ok, {"in_diff_ok": in_diff == residual, "H_collision": H1 == H2,
                "msg_diff_hw": sum(bin(a ^ b).count("1") for a, b in zip(w1, w2)),
                "working_diff_hw": sum(bin(a ^ b).count("1") for a, b in zip(out1, out2))}


def solve(residual, R, name, target="feedforward", timeout=300, outdir=None):
    outdir = outdir or os.path.join(HERE, "../results/cnf_ff")
    os.makedirs(outdir, exist_ok=True)
    cnf, refs = build_ff_absorber_cnf(residual, R, target=target)
    path = os.path.join(outdir, f"ff_{name}_R{R}_{target}.cnf")
    nv, ncl = cnf.write_dimacs(path)
    status, out = solver.run_kissat(path, timeout=timeout)
    return status, path, refs, out, (nv, ncl)


def _selftest():
    """Low-R feed-forward absorber should be SAT (free CV => ample freedom)."""
    diff = CLUSTERS["bit13_HW35"]
    s, _, refs, out, sz = solve(diff, 8, "bit13_HW35", target="feedforward", timeout=120)
    print(f"feedforward R=8: {s}  ({sz[0]} vars, {sz[1]} clauses)")
    assert s == "SAT", f"R=8 feed-forward expected SAT, got {s}"
    print("absorber_feedforward self-test: PASS (R=8 SAT)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cluster", default="bit13_HW35", choices=list(CLUSTERS))
    ap.add_argument("--R", type=int, required=True)
    ap.add_argument("--target", default="feedforward", choices=["feedforward", "working"])
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        _selftest(); return
    diff = CLUSTERS[args.cluster]
    status, path, refs, out, sz = solve(diff, args.R, args.cluster,
                                        target=args.target, timeout=args.timeout)
    print(f"[{args.cluster} R={args.R} target={args.target}] {status}  "
          f"({sz[0]} vars, {sz[1]} clauses)")
    if status == "SAT":
        ok, info = oracle_verify_ff(refs, out)
        print(f"  oracle: {ok}  {info}")


if __name__ == "__main__":
    main()
