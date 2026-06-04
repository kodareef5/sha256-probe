#!/usr/bin/env python3
"""
W5-HY3 — delta-hyperbolicity -> collisions rare & rigid; de58 = the tree axis.

Card claim: thin-triangle hyperbolic difference graph => unique geodesic corridors =>
rigid, rare collisions; 132/HW~74 = sphere-concentration; de58-grows/others-constant =
a TREE-GRADED structure with de58 the branching axis.

PROBE (faithful): N=4 (cascade-eligible, exhaustive). Build the difference-state graph
of the cascade tail (vertices = distinct 8-tuple difference states (da..dh) at rounds
56..60 across ALL cascade paths; edges = one-round transitions on a path). Then:
  (1) 4-POINT delta test: delta = max over 4-tuples of (second-largest - largest)/2 of
      the three pair-sum matchings. Report delta AND delta/diameter (skeptic: finite
      graphs are trivially hyperbolic -> the TREND of delta/diam vs N is the real test).
  (2) BRANCHING axis: at which round does the difference state fan out (one parent ->
      many children)? Is it concentrated at the de58 step? Does the branching factor =
      |de58| = 2**hw(db56) (finding #6 bar: DERIVE the number, not restate)?

KILL: delta grows with diameter (flat, not hyperbolic), OR branching not on de58.
Skeptic: report delta/diameter, not raw delta. de58 thread is CLOSED -> only credit if
it reproduces 2**hw(db56).
"""
import sys, importlib.util, os, itertools
KD = '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/cards'
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
sys.path.insert(0, KD)
import shabridge as sb
spec = importlib.util.spec_from_file_location("w5eng", os.path.join(KD, "_w5co_engine.py"))
eng = importlib.util.module_from_spec(spec); spec.loader.exec_module(eng)


def build_diff_graph(N):
    """Vertices = distinct difference states (da..dh, XOR) at rounds 56..60 across all
    cascade paths, tagged by round (so the graph is layered/levelled). Edges = transitions
    that actually occur on some cascade path. Returns adjacency + per-round vertex sets +
    the branching structure + db56."""
    M = eng.make_model(N)
    setup = eng.find_M0(M)
    if setup is None:
        return None
    MASK = M['MASK']; R = MASK + 1
    s1_0, s2_0 = setup['st1'], setup['st2']
    db56 = s1_0[1] ^ s2_0[1]

    def dstate(s1, s2):
        return tuple((s1[i] ^ s2[i]) & MASK for i in range(8))

    # layered vertices: (round, dstate)
    verts = set()
    edges = set()
    # children map per round to measure branching
    children = {}  # (round, parent_dstate) -> set(child_dstate)
    root = (56, dstate(s1_0, s2_0))
    verts.add(root)
    de_by_round = {57: set(), 58: set(), 59: set(), 60: set()}

    for w57 in range(R):
        for w58 in range(R):
            for w59 in range(R):
                for w60 in range(R):
                    s1, s2 = s1_0, s2_0
                    prev = root
                    seq = []
                    for rnd, w in ((57, w57), (58, w58), (59, w59), (60, w60)):
                        wb = eng.find_w2(s1, s2, rnd, w, M) if rnd < 60 else None
                        if rnd == 60:
                            co = eng.find_w2(s1, s2, 60, 0, M)
                            wb = (w + co) & MASK
                        s1 = eng.sha_round(s1, M['KN'][rnd], w, M)
                        s2 = eng.sha_round(s2, M['KN'][rnd], wb, M)
                        ds = dstate(s1, s2)
                        node = (rnd, ds)
                        verts.add(node)
                        edges.add((prev, node))
                        children.setdefault(prev, set()).add(ds)
                        de_by_round[rnd].add(ds[4])  # de = e-register diff
                        prev = node
    # branching factor per round = max #distinct children of any parent at that round
    branch = {}
    for rnd in (57, 58, 59, 60):
        parents_at = [p for p in children if p[0] == rnd - 1]
        bf = max((len(children[p]) for p in parents_at), default=0)
        branch[rnd] = bf

    # --- COLLISION-RESTRICTED de-sets (the repo's actual de57=de59=de60=1, de58 varies) ---
    de_coll = {57: set(), 58: set(), 59: set(), 60: set()}
    for w57 in range(R):
        for w58 in range(R):
            for w59 in range(R):
                for w60 in range(R):
                    r = eng.run_tail(M, setup, w57, w58, w59, w60)
                    if not r['collide']:
                        continue
                    # replay to grab per-round de on this collision path
                    s1, s2 = s1_0, s2_0
                    des = {}
                    for rnd, w in ((57, w57), (58, w58), (59, w59), (60, w60)):
                        if rnd < 60:
                            wb = eng.find_w2(s1, s2, rnd, w, M)
                        else:
                            co = eng.find_w2(s1, s2, 60, 0, M); wb = (w + co) & MASK
                        s1 = eng.sha_round(s1, M['KN'][rnd], w, M)
                        s2 = eng.sha_round(s2, M['KN'][rnd], wb, M)
                        des[rnd] = (s1[4] - s2[4]) & MASK
                    for rnd in (57, 58, 59, 60):
                        de_coll[rnd].add(des[rnd])
    return dict(N=N, verts=verts, edges=edges, db56=db56, hw_db56=sb.hw(db56),
                de_by_round={r: len(de_by_round[r]) for r in de_by_round},
                de_coll={r: len(de_coll[r]) for r in de_coll},
                branch=branch)


def graph_distances(verts, edges):
    """BFS all-pairs shortest path on the undirected layered graph (small)."""
    import collections
    adj = collections.defaultdict(set)
    for u, v in edges:
        adj[u].add(v); adj[v].add(u)
    nodes = list(verts)
    idx = {n: i for i, n in enumerate(nodes)}
    INF = float('inf')
    n = len(nodes)
    D = [[INF] * n for _ in range(n)]
    for src in nodes:
        si = idx[src]
        D[si][si] = 0
        dq = collections.deque([src])
        while dq:
            u = dq.popleft()
            for w in adj[u]:
                if D[si][idx[w]] == INF:
                    D[si][idx[w]] = D[si][idx[u]] + 1
                    dq.append(w)
    return nodes, idx, D


def four_point_delta(nodes, D):
    """Gromov 4-point delta on the (connected component of the) graph: for every 4-tuple,
    sort the three pair-sums S1>=S2>=S3; delta_tuple = (S1 - S2)/2; delta = max. Also
    diameter = max finite distance. Sample 4-tuples if too many."""
    n = len(nodes)
    INF = float('inf')
    finite = [(i, j) for i in range(n) for j in range(n) if i < j and D[i][j] < INF]
    diam = max((D[i][j] for i, j in finite), default=0)
    # restrict to one connected component containing node 0's reachable set
    reach = [j for j in range(n) if D[0][j] < INF]
    delta = 0.0
    quads = list(itertools.combinations(reach, 4))
    import random
    if len(quads) > 20000:
        random.Random(1).shuffle(quads); quads = quads[:20000]
    for (a, b, c, d) in quads:
        s1 = D[a][b] + D[c][d]
        s2 = D[a][c] + D[b][d]
        s3 = D[a][d] + D[b][c]
        S = sorted((s1, s2, s3), reverse=True)
        delta = max(delta, (S[0] - S[1]) / 2.0)
    return delta, diam, len(reach)


def main():
    print("== W5-HY3: delta-hyperbolicity; de58 = tree axis ==\n")
    print("Difference-state graph of the cascade tail; 4-point delta + branching axis.\n")
    for N in (4,):
        g = build_diff_graph(N)
        if g is None:
            print(f"N={N}: (no cascade-eligible M0)")
            continue
        nodes, idx, D = graph_distances(g['verts'], g['edges'])
        delta, diam, ncomp = four_point_delta(nodes, D)
        print(f"N={N}: |V|={len(g['verts'])} |E|={len(g['edges'])} "
              f"db56=0x{g['db56']:x} hw(db56)={g['hw_db56']} 2^hw={2**g['hw_db56']}")
        print(f"  (1) delta={delta}  diameter={diam}  "
              f"delta/diam={delta/diam if diam else float('nan'):.3f}  (component {ncomp} nodes)")
        print(f"  (2) branching factor per round (max #children of any parent):")
        for rnd in (57, 58, 59, 60):
            mark = "  <== de58 axis" if rnd == 58 else ""
            print(f"        round {rnd}: branch={g['branch'][rnd]}  "
                  f"(|de{rnd}|={g['de_by_round'][rnd]}){mark}")
        print(f"  (3) COLLISION-RESTRICTED de-sets (the repo's de57=de59=de60=1, de58 varies):")
        for rnd in (57, 58, 59, 60):
            mark = "  <== only varying axis?" if rnd == 58 else ""
            print(f"        |de{rnd}|_collisions = {g['de_coll'][rnd]}{mark}")
        dc = g['de_coll']
        only58 = (dc[57] == 1 and dc[59] == 1 and dc[60] == 1 and dc[58] > 1)
        print(f"\n  branching-on-all-paths max at round: {max((57,58,59,60), key=lambda r: g['branch'][r])} "
              f"(branch {[g['branch'][r] for r in (57,58,59,60)]}) -- NOT necessarily de58")
        print(f"  collision-restricted: de58 the ONLY varying axis? {only58}  "
              f"(|de58|_coll={dc[58]} vs 2^hw(db56)={2**g['hw_db56']} -> "
              f"{'MATCH' if dc[58]==2**g['hw_db56'] else 'NO'})")
    print()
    print("INTERPRETATION: delta/diameter small+bounded (vs growing) = hyperbolic, not flat.")
    print(" Branching localized at round 58 (= de58 axis) with factor |de58|=2^hw(db56)")
    print(" => tree-graded with de58 the branching axis AND derives the closed-thread number.")
    print(" KILL if delta ~ diameter (flat) or branching is NOT on de58.")


if __name__ == '__main__':
    main()
