"""
ollivier.py — Ollivier-Ricci curvature on a graph (pure python + scipy matching).

kappa(x,y) = 1 - W1(mu_x, mu_y) / d(x,y),  where mu_v = uniform on v's neighbors
(optionally lazy: alpha mass kept at v), d = graph shortest-path distance,
W1 = 1-Wasserstein (earth-mover) computed by min-cost perfect matching of the
two neighbor multisets under the ground (shortest-path) metric.

Negative kappa <=> bottleneck/constriction edge (the card's '0-slack bridge').
Reusable across cards that need discrete curvature on a variable-interaction graph.
"""
import itertools
from collections import deque
try:
    from scipy.optimize import linear_sum_assignment
    import numpy as np
    HAVE_SCIPY = True
except Exception:
    HAVE_SCIPY = False

def bfs_dist(adj, src, cutoff=6):
    """Shortest-path distances from src (unit edges), up to cutoff."""
    dist = {src: 0}
    q = deque([src])
    while q:
        u = q.popleft()
        if dist[u] >= cutoff:
            continue
        for w in adj[u]:
            if w not in dist:
                dist[w] = dist[u] + 1
                q.append(w)
    return dist

def w1_matching(supp_x, supp_y, ground):
    """1-Wasserstein between two uniform distributions on node-lists supp_x, supp_y
    (each uniform mass 1/len). ground(a,b)->distance. Uses balanced min-cost
    matching by replicating to a common size (LCM-free: pad by repetition)."""
    nx, ny = len(supp_x), len(supp_y)
    if nx == 0 or ny == 0:
        return 0.0
    # build cost matrix between the two supports, then solve fractional OT via
    # the standard trick: since both uniform, optimal is min-cost matching scaled.
    # Use exact LP-free approach: replicate to size L = nx*ny (each x-atom mass
    # 1/nx -> ny copies of mass 1/(nx*ny); each y-atom -> nx copies). Match L<->L.
    if not HAVE_SCIPY:
        # greedy fallback (upper bound on W1)
        cost = 0.0
        ys = list(supp_y)
        for a in supp_x:
            best = min(range(len(ys)), key=lambda j: ground(a, ys[j]))
            cost += ground(a, ys[j]) if False else ground(a, ys[best])
        return cost / nx
    xs = [a for a in supp_x for _ in range(ny)]
    ysr = [b for b in supp_y for _ in range(nx)]
    L = len(xs)
    C = np.empty((L, L))
    # cache ground distances
    gc = {}
    for i, a in enumerate(xs):
        for j, b in enumerate(ysr):
            key = (a, b)
            d = gc.get(key)
            if d is None:
                d = ground(a, b); gc[key] = d
            C[i, j] = d
    ri, cj = linear_sum_assignment(C)
    return C[ri, cj].sum() / L

def ollivier_edge(adj, x, y, alpha=0.0, cutoff=6):
    """kappa(x,y).  alpha = lazy mass kept at the node (0 = pure uniform)."""
    nx_ = list(adj[x]); ny_ = list(adj[y])
    if not nx_ or not ny_:
        return 1.0
    # distance oracle via BFS from a small set (cache per call)
    dcache = {}
    def ground(a, b):
        if a == b:
            return 0.0
        if a not in dcache:
            dcache[a] = bfs_dist(adj, a, cutoff)
        if b in dcache[a]:
            return dcache[a][b]
        if b not in dcache:
            dcache[b] = bfs_dist(adj, b, cutoff)
        return dcache[b].get(a, cutoff + 1)
    # lazy random walk supports (alpha at the node, (1-alpha) spread on neighbors)
    if alpha > 0:
        supp_x = [x] + nx_         # crude: include node once + neighbors
        supp_y = [y] + ny_
    else:
        supp_x, supp_y = nx_, ny_
    w1 = w1_matching(supp_x, supp_y, ground)
    dxy = 1.0  # x,y adjacent
    return 1.0 - w1 / dxy

def graph_curvature_stats(adj, edges=None, alpha=0.0, cutoff=6, max_edges=None):
    """Mean / min Ollivier-Ricci over edges. Returns (mean, mn, n, frac_negative)."""
    if edges is None:
        edges = []
        for u in adj:
            for v in adj[u]:
                if u < v:
                    edges.append((u, v))
    if max_edges and len(edges) > max_edges:
        step = len(edges) // max_edges
        edges = edges[::step][:max_edges]
    ks = [ollivier_edge(adj, u, v, alpha, cutoff) for (u, v) in edges]
    if not ks:
        return 0.0, 0.0, 0, 0.0
    mean = sum(ks) / len(ks)
    mn = min(ks)
    fneg = sum(1 for k in ks if k < 0) / len(ks)
    return mean, mn, len(ks), fneg
