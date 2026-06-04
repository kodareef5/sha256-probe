"""
W7-RA5 — Ramsey-number clique threshold for the boundary round.   [P2 · cheap]

Card claim: the message-word agreement graph (edge RED iff the pair stays a partial
collision through round r) — a multi-word collision family = a RED clique; the
boundary r* = where the coloring first forces / loses the needed RED clique
(a Ramsey-number-vs-edge-density condition).

Probe (from CATALOG): N=4..10, K=16..64 sampled words; 2-color edges by pairwise
partial-collision through r; max RED clique vs r; a sharp collapse at the sr-analog+1?
clique-size scaling vs the random ~2 log2 K?
Kill: max clique = the random Erdős value with no anomaly at the boundary, OR no
drop at sr+1.
Skeptic: the cliques SHA needs are tiny (a few words) -> Ramsey threshold trivially
met & non-predictive; only a sharp clique collapse at exactly r* redeems it.

Construction (faithful to the cascade engine _w5co_engine):
  * Vertices = K sampled tail free-word vectors v=(w57,w58,w59,w60) of path-1.
  * For each vertex, run the cascade tail (path-1 fixed, path-2 via find_w2 keeping
    da=0) and record the per-round MODULAR diff trace da..dh for rounds 57..63.
    A vertex is a "partial collision through r" iff its diff is all-zero at round r
    (full 8-register match). [the de* trace; de60==0 is the free-cascade plateau.]
  * Edge(i,j) RED-through-r iff BOTH vertex i and vertex j are partial collisions
    through r AND they agree (same state pair) — i.e. mutual pairwise compatibility.
    We take the natural "agreement" = both reach diff 0 at r (the family condition).
  * max RED clique vs r; compare to Erdos random clique ~ 2 log2(K / red-density).
  * The sr-analog boundary here is round 61 (sr=60 collisions; sr=61 is the wall).

READ-ONLY toward the repo. Throttle externally:
  OMP_NUM_THREADS=2 taskpolicy -b python3 W7-RA5.py
"""
import sys, random, math
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/cards')
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import _w5co_engine as E
import _hc_family as HC   # gives full per-round diff traces for real collisions
import shabridge as sb


def trace_for_vertex(M, setup, v):
    """Per-round modular diff trace (rounds 57..63) for free-word vector v.
    Returns dict r-> 8-tuple of (s1-s2) mod 2^N."""
    tr, _ = HC.tail_trace(M, setup, *v)
    return tr


def partial_collision_through(tr, r):
    """True iff diff all-zero at round r (full 8-register partial collision)."""
    return all(x == 0 for x in tr[r])


def de_zero_through(tr, r):
    """Weaker agreement: register-e diff de==0 at round r (the cascade 'still alive'
    signal). de60==0 is the free-cascade plateau; de61 is the boundary."""
    return tr[r][4] == 0   # index 4 = register e


def max_clique(adj, V):
    """Exact max clique on small graph. adj = dict v-> set(neighbors). V = list of
    vertices. Bron-Kerbosch with pivoting; |V|<=64 fine for sparse/structured."""
    best = [0]
    Vset = set(V)
    def bk(R, P, X):
        if not P and not X:
            if len(R) > best[0]:
                best[0] = len(R)
            return
        # pivot
        u = next(iter(P | X)) if (P | X) else None
        cand = P - adj[u] if u is not None else set(P)
        for v in list(cand):
            bk(R | {v}, P & adj[v], X & adj[v])
            P = P - {v}
            X = X | {v}
    bk(set(), set(V), set())
    return best[0]


def run_N(N, K, seed=0):
    """Build agreement graph over K random vertices; report max RED clique vs r and
    RED edge density vs r. Boundary round = 61."""
    M = E.make_model(N); setup = E.find_M0(M)
    if setup is None:
        return None
    MASK = M['MASK']
    rng = random.Random(seed + N)
    # sample K distinct free-word vectors
    verts = set()
    while len(verts) < K:
        verts.add((rng.randint(0, MASK), rng.randint(0, MASK),
                   rng.randint(0, MASK), rng.randint(0, MASK)))
    verts = list(verts)
    traces = [trace_for_vertex(M, setup, v) for v in verts]
    Vidx = list(range(K))

    out = {}
    for r in range(57, 64):
        # "partial collision through r" membership
        pc = [partial_collision_through(traces[i], r) for i in range(K)]
        dez = [de_zero_through(traces[i], r) for i in range(K)]
        # RED edge(i,j) iff both are partial collisions through r (mutual family member)
        # -> the RED graph is a CLIQUE on the pc-true set by construction; the
        #    interesting quantity is |pc| (how many vertices survive to round r).
        # We ALSO build the weaker de-agreement graph: edge iff both de==0 at r AND
        #    they share the same de-value at r-... -> use full-state pc as the honest one.
        adj = {i: set() for i in Vidx}
        red_edges = 0
        for i in range(K):
            for j in range(i + 1, K):
                if pc[i] and pc[j]:
                    adj[i].add(j); adj[j].add(i); red_edges += 1
        mc = max_clique(adj, Vidx)
        dens = red_edges / (K * (K - 1) / 2) if K > 1 else 0.0
        n_pc = sum(pc); n_de = sum(dez)
        # Erdos/random clique baseline at this edge density p: ~ 2 log2(K)/log2(1/p)...
        # for p->0 expected max clique ~ 2 (or floor); compute random-graph G(K,p) ref
        out[r] = dict(n_pc=n_pc, n_de=n_de, red_edges=red_edges, density=dens,
                      max_clique=mc)
    return out, verts


def erdos_random_clique(K, p, trials=200, seed=1):
    """Empirical max clique of G(K,p) for a fair 'random Erdos value' baseline."""
    if p <= 0:
        return 0, 0
    rng = random.Random(seed)
    best = []
    for _ in range(trials):
        adj = {i: set() for i in range(K)}
        for i in range(K):
            for j in range(i + 1, K):
                if rng.random() < p:
                    adj[i].add(j); adj[j].add(i)
        best.append(max_clique(adj, list(range(K))))
    best.sort()
    return best[len(best) // 2], best[-1]  # median, max


if __name__ == '__main__':
    print("W7-RA5 — Ramsey clique threshold on the message-word agreement graph\n")
    print("Vertices = random tail free-word vectors; RED edge through r iff BOTH are")
    print("full 8-register partial collisions through round r. Boundary round = 61.\n")
    SR_BOUNDARY = 61
    for N in (4, 8, 10):
        for K in (32, 64):
            res = run_N(N, K, seed=11)
            if res is None:
                print(f"N={N}: no cascade M0; skip"); continue
            out, verts = res
            print(f"--- N={N}  K={K} ---")
            print("  r : #partial-coll(full) : #de=0 : RED-edges : density : maxRED-clique : rand-clique(med,max)")
            prev_clique = None
            for r in range(57, 64):
                o = out[r]
                med, mx = erdos_random_clique(K, o['density'], trials=120, seed=5)
                mark = ""
                if r == SR_BOUNDARY:
                    mark = "  <== sr-boundary (61)"
                if r == SR_BOUNDARY + 1 - 1:  # 61 same; flag 60->61 transition below
                    pass
                print(f"  {r}: {o['n_pc']:>5} : {o['n_de']:>5} : {o['red_edges']:>6} : "
                      f"{o['density']:.3f} : {o['max_clique']:>3}  : ({med},{mx}){mark}")
            # boundary diagnostic: drop in max clique from 60 -> 61?
            c60 = out[60]['max_clique']; c61 = out[61]['max_clique']
            pc60 = out[60]['n_pc']; pc61 = out[61]['n_pc']
            print(f"  boundary check: maxclique 60->61 = {c60}->{c61}  "
                  f"(#full-collisions 60->61 = {pc60}->{pc61})")
            print(f"  sharp collapse AT 61 only (vs general decline)? "
                  f"{'see trace' }\n")
    print("=== INTERPRETATION ===")
    print("Kill fires if: (a) max RED clique tracks the random Erdos value, with no")
    print("anomaly at the boundary, OR (b) no drop specifically at sr+1 (round 61).")
    print("Scale check (finding #4): Ramsey R(s,t) forcing a size-s RED clique needs")
    print("K ~ 2^(s/2); SHA's needed clique s is a HANDFUL of words -> threshold trivially")
    print("met at tiny K -> non-predictive unless a SHARP collapse lands exactly at 61.")
