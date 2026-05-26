#!/usr/bin/env python3
"""Block-2 absorber sweep across real residual clusters (block2_wang kill_criteria #1).

For each block-1 residual cluster, pin its round-63 state difference as the block-2 INPUT
difference, target a ZERO output difference at round R (a 2-block-collision sub-problem),
allow message modification + the message schedule (t>=16), and search. Record the deepest R
with an oracle-confirmed absorber = "best-trail-round count", compared to the naive-SAT
18-round frontier. Search uses a node budget; BUDGET means search-limited, not proven
infeasible (the naive DFS is weaker than a real SAT solver -- stated honestly).

Reuses wang_search (the control-validated trail engine) and lib.sha256 (oracle).
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "../../../..")))

from wang_search import (Net, build_rounds, build_schedule, run_search,
                         assignment_pair, concrete_rounds, COND, N)
import lib.sha256 as L

REG = "abcdefgh"

# Distinct block-1 residual clusters (round-63 state differences; dd63=dh63=0 by cascade).
# bit13 is the optimized HW35 frontier record; the rest are valid cascade residuals.
CLUSTERS = {
    "bit13_HW35": [0xd8581011, 0xa004804c, 0x80000000, 0, 0x8007828a, 0x1864c, 0x80000000, 0],
    "bit14_HW94": [0x81dd7b67, 0xc8faae8a, 0x89a6ce84, 0, 0x7578f489, 0x9422c625, 0x96a27e84, 0],
    "bit6_HW93":  [0x0b66bc09, 0x985abf71, 0xc2aa8166, 0, 0xbba8a282, 0x96bf5d52, 0xc75e8322, 0],
    "bit15_HW97": [0x68e89203, 0xb75cba78, 0x458770d6, 0, 0xbdc47d99, 0x607ae1d0, 0xc5fd513a, 0],
    "bit24_HW101":[0xbf540a5e, 0xf28d16c4, 0x1c4d5e75, 0, 0x6ee27f85, 0x9b807e37, 0x03c34dd7, 0],
    "bit28_HW94": [0xfbf3b4e0, 0x51ba3d55, 0xfa1869d3, 0, 0x604e0522, 0x283b4292, 0x7a186e77, 0],
}


def try_absorb(diff, R, budget):
    net = Net()
    build_rounds(net, R, L.K[:R])
    if R > 16:
        build_schedule(net, R)
    for j in range(8):
        for i in range(N):
            net.pin((f"{REG[j]}0", i), COND["x"] if (diff[j] >> i) & 1 else COND["-"])
            net.pin((f"{REG[j]}{R}", i), COND["-"])
    try:
        assign, nodes = run_search(net, max_nodes=budget)
    except RuntimeError:
        return "BUDGET", budget, None
    if assign is None:
        return "INFEASIBLE", nodes, None
    # oracle-confirm
    st0 = [assignment_pair(assign, f"{REG[j]}0")[0] for j in range(8)]
    st0s = [assignment_pair(assign, f"{REG[j]}0")[1] for j in range(8)]
    msgs = [assignment_pair(assign, f"W{t}")[0] for t in range(R)]
    msgss = [assignment_pair(assign, f"W{t}")[1] for t in range(R)]
    states = concrete_rounds(st0, msgs, L.K[:R])
    statess = concrete_rounds(st0s, msgss, L.K[:R])
    ok = all(states[R][j] == statess[R][j] for j in range(8)) and \
        [a ^ b for a, b in zip(st0, st0s)] == diff
    return ("ABSORBS" if ok else "ORACLE_FAIL"), nodes, msgs


def main():
    Rs = [8, 12, 15, 16, 18, 20]
    budget = 250_000
    out = {}
    print(f"Absorber sweep (target zero output diff, message-mod + schedule, budget={budget}):")
    print(f"{'cluster':14s} " + " ".join(f"R={r:<2d}" for r in Rs) + "   best")
    for name, diff in CLUSTERS.items():
        row = {}
        best = 0
        for R in Rs:
            status, nodes, _ = try_absorb(diff, R, budget)
            row[R] = {"status": status, "nodes": nodes}
            if status == "ABSORBS":
                best = max(best, R)
        out[name] = {"diff": [f"0x{x:08x}" for x in diff], "rounds": row, "best_absorber_R": best}
        cells = []
        for R in Rs:
            s = row[R]["status"]
            cells.append({"ABSORBS": " A ", "INFEASIBLE": " . ", "BUDGET": " ? ",
                          "ORACLE_FAIL": " X "}.get(s, " ? "))
        print(f"{name:14s} " + " ".join(f"{c:>4s}" for c in cells) + f"   {best}")
    print("\nlegend: A=oracle-confirmed absorber  .=infeasible(propagation)  "
          "?=search budget exceeded  X=oracle mismatch")
    print(f"naive-SAT frontier = 18 rounds; kill #1 fires if no cluster's best > 18 "
          f"after a real search effort.")
    with open(os.path.join(HERE, "../results/absorber_sweep.json"), "w") as f:
        json.dump(out, f, indent=2)


if __name__ == "__main__":
    main()
