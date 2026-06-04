#!/usr/bin/env python3
"""
W8-KC1 — Active-difference 2-core collapse -> the wall as a core dissolution, |2-core|=132.

CARD CLAIM: peel the SPARSE differential-support hypergraph (only forced-nonzero dW-bits)
by min-degree; a non-empty rigid 2-core (= the hard core) survives through round 60 and
COLLAPSES at 61; k-core's discontinuous threshold = the sharp wall; |2-core(60)| ~ 132.

PROBE (honored): propagate the active-difference support over the schedule (reuse F839's
schedule_dep_analysis approach on the dW side), build the difference-bit dependency graph,
peel to the 2-core by min-degree. Measure |2-core| as a function of the last constrained
round R (the "sr=R" frontier). Does |2-core| drop >=2x at 60->61 while the full set shrinks
smoothly? Is |2-core(60)| in 100-170 (~132)?
KILL: |2-core(60)| not in 100-170 at N=32, OR the 60->61 drop < 1.3x.

GRAPH (honest active-diff support graph at the true 32-bit width):
  Nodes = schedule difference bits dW[k][b], k=0..63, b=0..31, that are REACHABLE from the
  active injection (kernel injects dM into M[0] and M[9]; dW[k] support computed by the same
  linear sigma0/sigma1/union propagation F839 uses -- this is the forced-nonzero support).
  Edges (undirected) = the schedule recurrence couplings: dW[k] <- sigma1(dW[k-2]), dW[k-7],
  sigma0(dW[k-15]), dW[k-16]. We add an undirected edge between dW[k][b] and each source
  difference bit it actually depends on (per the bit-rotation/shift structure). The 2-core is
  the maximal subgraph with min degree >=2 (standard k-core peeling).
  "Constrained to sr=R" = collision forces dW[k]=0 for the cascade-controlled e-register rounds
  AND the schedule difference bits feeding rounds <=R+? ; operationally we take the subgraph of
  difference bits in schedule words W[0..R] (the support that must be reconciled by round R).

ADVERSARIAL (prior finding #1): every honest core/frozen/shell size is 0 / 128 (=4N) /
width-scaling -- NEVER a stable 132. 132 is the OUTPUT control census (4N+4), not a graph core.
We compute the real 2-core size and check whether it is a stable 132 or width-scaling.

READ-ONLY toward repo: imports lib.sha256 rotation constants via shabridge; reuses the EXACT
linear sigma-support propagation of F839 schedule_dep_analysis.py (read from the repo).
"""
import sys
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb

W = 32  # honest bit width (card asks for the literal 32-bit corank question)

# --- sigma0/sigma1 bit-mixing (SHA-256, from lib via the F839 structure) ---
def sigma0_srcbits(b):
    """positions of W that feed sigma0(W)[b]: ROR7,ROR18,SHR3."""
    out = [(b + 7) % 32, (b + 18) % 32]
    if b + 3 < 32: out.append(b + 3)
    return out

def sigma1_srcbits(b):
    out = [(b + 17) % 32, (b + 19) % 32]
    if b + 10 < 32: out.append(b + 10)
    return out

def build_active_support():
    """Replicate F839's linear support propagation on the DIFFERENCE side.
    Each W[k] bit -> set of source 'active' atoms. The kernel injects a difference into
    M[0] (all bits potentially, via the MSB-kernel) and M[9]. We seed dW[0] and dW[9]
    as fully active (difference present), all other dW[k<16]=inactive (fill words equal).
    Then propagate support by union (carry over-approx, exactly as F839)."""
    # active[k] = set of bit positions b that are forced-nonzero-capable in dW[k]
    active = {k: set() for k in range(64)}
    # TRUE MSB-kernel difference (from the repo enumerator): M2[0]=M0^MSB (differs ONLY in
    # the MSB, bit 31) and M2[9]=MASK^MSB (M1[9]=MASK, differs ONLY in bit 31). So the
    # forced-nonzero INJECTED difference is just 2 bits: dW[0][31] and dW[9][31]. This is the
    # genuinely SPARSE seed the card wants ("only forced-nonzero dW-bits"). Support then
    # spreads by the linear sigma propagation (union over-approx, exactly as F839).
    active[0] = {31}
    active[9] = {31}
    # message words 1..8,10..15 are EQUAL fills -> dW=0 (inactive)
    # edges: list of (node, node) undirected, node = (k,b)
    edges = set()
    for k in range(16, 64):
        srcs = {'s1': (k - 2, sigma1_srcbits), 'p7': (k - 7, None),
                's0': (k - 15, sigma0_srcbits), 'p16': (k - 16, None)}
        for b in range(32):
            contributors = []
            # sigma1(dW[k-2])[b]
            for sb_ in sigma1_srcbits(b):
                if sb_ in active[k - 2]:
                    contributors.append((k - 2, sb_))
            # dW[k-7][b]
            if b in active[k - 7]:
                contributors.append((k - 7, b))
            # sigma0(dW[k-15])[b]
            for sb_ in sigma0_srcbits(b):
                if sb_ in active[k - 15]:
                    contributors.append((k - 15, sb_))
            # dW[k-16][b]
            if b in active[k - 16]:
                contributors.append((k - 16, b))
            if contributors:
                active[k].add(b)
                node = (k, b)
                for c in contributors:
                    edges.add((node, c) if node < c else (c, node))
    return active, edges

def kcore_size(nodes, adj, k=2):
    """Standard k-core: iteratively remove nodes with degree < k. Returns surviving node set."""
    deg = {n: len(adj[n]) for n in nodes}
    alive = set(nodes)
    changed = True
    # use a simple queue-based peel
    from collections import deque
    q = deque(n for n in alive if deg[n] < k)
    while q:
        n = q.popleft()
        if n not in alive:
            continue
        alive.discard(n)
        for m in adj[n]:
            if m in alive:
                deg[m] -= 1
                if deg[m] < k:
                    q.append(m)
    return alive

def main():
    print(f"=== W8-KC1: active-difference 2-core, honest 32-bit width ===\n")
    active, edges = build_active_support()
    # full active support size per round
    print("--- active (forced-nonzero) dW-bit count per schedule word ---")
    for k in range(54, 64):
        print(f"  dW[{k}]: |active bits| = {len(active[k])}")

    # Build adjacency for the difference graph restricted to schedule words W[0..R].
    # The "sr=R" frontier: difference bits that must be reconciled to make rounds up to R
    # collide are those in W[0..R]. We peel the 2-core of that induced subgraph.
    def graph_upto(R):
        keep = set()
        for (k, b) in {n for e in edges for n in e}:
            if k <= R:
                keep.add((k, b))
        adj = {n: set() for n in keep}
        for (u, v) in edges:
            if u in keep and v in keep:
                adj[u].add(v); adj[v].add(u)
        return keep, adj

    print("\n--- 2-core size vs last-constrained round R (the sr=R frontier) ---")
    print(f"{'R':>4} | {'|full active graph|':>18} | {'|2-core|':>9} | {'|3-core|':>9}")
    sizes = {}
    for R in range(56, 64):
        nodes, adj = graph_upto(R)
        c2 = kcore_size(nodes, adj, 2)
        c3 = kcore_size(nodes, adj, 3)
        sizes[R] = (len(nodes), len(c2), len(c3))
        print(f"{R:>4} | {len(nodes):>18} | {len(c2):>9} | {len(c3):>9}")

    # the card's specific claims:
    full60, core60, _ = sizes[60]
    full61, core61, _ = sizes[61]
    print(f"\n--- card-specific checks ---")
    print(f"  |2-core(60)| = {core60}   (claim ~132; kill if not in 100-170)")
    print(f"  |2-core(61)| = {core61}")
    drop = (core60 / core61) if core61 else float('inf')
    print(f"  60->61 drop in |2-core| = {drop:.2f}x   (claim >=2x; kill if <1.3x)")
    fulldrop = (full60 / full61) if full61 else float('inf')
    print(f"  60->61 drop in FULL active set = {fulldrop:.2f}x  (claim: shrinks smoothly)")

    # compare to the 4N census and 132
    print(f"\n  context: 4N (a,b,e,f census) = {4*W} = 128 ; repo HARDCORE 132 = 4N+4")
    print(f"  is |2-core(60)|={core60} a stable 132, or 0/128/width-scaling?")

    print(f"\n=== KILL CHECK ===")
    k1 = not (100 <= core60 <= 170)
    k2 = drop < 1.3
    print(f"  |2-core(60)|={core60} in [100,170]? {'NO->KILL' if k1 else 'yes'}")
    print(f"  60->61 drop {drop:.2f}x >= 1.3x? {'NO->KILL' if k2 else 'yes'}")
    print(f"  KILL FIRES: {k1 or k2}")

if __name__ == '__main__':
    main()
