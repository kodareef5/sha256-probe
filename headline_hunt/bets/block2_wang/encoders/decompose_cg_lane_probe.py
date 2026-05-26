#!/usr/bin/env python3
"""Decompose the c63/g63 lane locks: controlled by (w57,w58) or (w59,w60)?

Path C plateaued at HW 43/44/45 with c/g LANE LOCKS (F449) under LOCAL radius-4
W moves: local moves repair one lane while damaging c/g. This session's
mitm_residue work found gh60 = (e58, e57) = f(w57,w58), orthogonal to W60.
Hypothesis: the locked c63/g63 lanes are primarily controlled by (w57,w58) -- a
coordinate Path C only moved LOCALLY -- so a GLOBAL (w57,w58) search can reach
lower c/g than the W60-centric search did.

This probe measures the sensitivity of HW(c63)+HW(g63) to varying (w57,w58) vs
(w59,w60) on the frontier candidates, reusing block2_bridge_beam.run_full
(no SHA reimplementation). If varying (w57,w58) reaches materially lower c+g than
varying (w59,w60), the decomposition lever is real.

Usage: decompose_cg_lane_probe.py [cand=bit24] [n=200000]
"""
import os
import sys
import random
import statistics as st

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
ENCODERS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, REPO)
sys.path.insert(0, ENCODERS)
from block2_bridge_beam import setup_cand, run_full  # noqa: E402

CANDS = {
    "bit24": (0xdc27e18c, 0xffffffff, 24),
    "bit13": (0x916a56aa, 0xffffffff, 13),
    "bit28": (0xd1acca79, 0xffffffff, 28),
}


def cg_hw(diff):
    return bin(diff[2]).count("1") + bin(diff[6]).count("1")   # c=2, g=6


def full_hw(diff):
    return sum(bin(d).count("1") for d in diff)


def main():
    cand = sys.argv[1] if len(sys.argv) > 1 else "bit24"
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 200000
    m0, fill, kbit = CANDS[cand]
    s = setup_cand(m0, fill, kbit)
    assert s, f"{cand} not cascade-eligible"
    s1i, s2i, W1p, W2p = s
    rng = random.Random(1234)

    # a base valid config
    while True:
        b = tuple(rng.getrandbits(32) for _ in range(4))
        r = run_full(s1i, s2i, W1p, W2p, *b)
        if r:
            break
    base_cg = cg_hw(r["diff63"])
    base_full = full_hw(r["diff63"])
    print(f"{cand} (m0=0x{m0:08x} kbit={kbit})  base: c+g HW={base_cg} full HW={base_full}")

    def sweep(vary):
        cg, full = [], []
        for _ in range(n):
            if vary == "5758":
                w = (rng.getrandbits(32), rng.getrandbits(32), b[2], b[3])
            else:
                w = (b[0], b[1], rng.getrandbits(32), rng.getrandbits(32))
            rr = run_full(s1i, s2i, W1p, W2p, *w)
            if not rr:
                continue
            cg.append(cg_hw(rr["diff63"]))
            full.append(full_hw(rr["diff63"]))
        return cg, full

    cgA, fullA = sweep("5758")
    cgB, fullB = sweep("5960")
    print(f"vary (w57,w58), fix (w59,w60): c+g HW  min={min(cgA)} median={st.median(cgA):.1f}  "
          f"| full HW min={min(fullA)}  (n={len(cgA)})")
    print(f"vary (w59,w60), fix (w57,w58): c+g HW  min={min(cgB)} median={st.median(cgB):.1f}  "
          f"| full HW min={min(fullB)}  (n={len(cgB)})")
    verdict = ("c/g lives in (w57,w58) -> global w57,w58 search is the unexplored lever"
               if min(cgA) < min(cgB) - 2 else
               "c/g NOT clearly (w57,w58)-controlled -> decomposition lever weak")
    print(f"VERDICT: {verdict}")


if __name__ == "__main__":
    main()
