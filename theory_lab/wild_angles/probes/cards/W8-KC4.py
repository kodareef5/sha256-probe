#!/usr/bin/env python3
"""
W8-KC4 — k-core onion of the folded gate graph -> inner shell of 128 nucleates at W59/W60.

CARD CLAIM: after the encoder's constant-folding (cascade-zeros prune edges -> sparse), the
gate graph's coreness onion has an INNER SHELL that nucleates at W_59/W_60 = the 128 round-bits,
with the 4 anchors as highest-coreness seeds; sr=61 adds a shell (giant k>=3-core emergence =
the cost jump). F213's elimination data is already a partial onion.

PROBE (honored): build the FOLDED CNFBuilder incidence graph (repo lib.cnf_encoder, sr=60 and
sr=59=one-more-free-round), compute coreness (k-core onion). Checks:
  - is there a max-coreness jump 60->61 (sr60 vs sr59)?  inner-shell size ~= 128 = W59/W60 vars?
  - 4 highest-coreness vars = anchors?
KILL (any): flat max-core (no nucleation), inner shell not in 128+-20, OR -- MANDATORY --
shuffling the encoder's variable-numbering changes the onion (=> allocation order, not
structure; F324 artifact warning).

CRITICAL (the whole point, F324 + prior finding #1): k-coreness is a graph-STRUCTURAL property,
invariant under vertex relabeling BY DEFINITION. So:
  (a) the coreness MULTISET (and the inner-shell SIZE) is permutation-invariant -- a REAL shell
      survives the shuffle;  but
  (b) any 'onion' read off variable-ID ORDER (e.g. F213's deep elimination chain living in
      arithmetic-progression IDs) is NOT invariant -> that reading is allocation, not structure.
We compute the honest coreness onion AND run the mandatory shuffle test, reporting both the
size (vs 128) and whether an ID-ordered reading survives.

READ-ONLY toward repo: imports lib.cnf_encoder.encode_collision (BUILDS the CNF; NO SAT solving).
N=32 (literal width -- this is the 128-round-bits question, allowed per the literal-132 carve-out).
"""
import sys, random
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb
sys.path.insert(0, sb.REPO)
import lib.cnf_encoder as cnfmod
# READ-ONLY workaround: encode_collision() has a latent bug -- it references a free name
# `m1_override` that is neither a parameter nor a module global (NameError on every call).
# We do NOT edit the repo file; we inject the missing global into the imported module's
# namespace at runtime (defaulting to None = no override), which is exactly the intended
# behavior. This keeps the repo READ-ONLY.
cnfmod.m1_override = None
from lib.cnf_encoder import encode_collision
from collections import defaultdict

def incidence_graph(clauses, perm=None):
    """Variable co-occurrence graph from CNF clauses. perm: optional dict relabeling var->newid.
    Returns adj: dict node->set(neighbors). Var 1 (TRUE) is dropped (it's the unit-constant)."""
    adj = defaultdict(set)
    def relabel(v):
        return perm[v] if (perm is not None and v in perm) else v
    for cl in clauses:
        vs = [abs(l) for l in cl if abs(l) != 1]
        vs = [relabel(v) for v in vs]
        for i in range(len(vs)):
            for j in range(i + 1, len(vs)):
                if vs[i] != vs[j]:
                    adj[vs[i]].add(vs[j]); adj[vs[j]].add(vs[i])
        for v in vs:
            adj.setdefault(v, set())
    return adj

def coreness(adj):
    """k-core decomposition: coreness[v] = max k s.t. v is in the k-core.
    Batagelj-Zaversnik O(E). Returns dict node->core number."""
    nodes = list(adj.keys())
    deg = {v: len(adj[v]) for v in nodes}
    order = sorted(nodes, key=lambda v: deg[v])
    pos = {v: i for i, v in enumerate(order)}
    bin_start = {}
    core = {}
    d = dict(deg)
    # bucket by degree
    maxdeg = max(deg.values()) if deg else 0
    # simple iterative peeling (clear and robust for our sizes)
    import heapq
    removed = set()
    cur = dict(deg)
    heap = [(cur[v], v) for v in nodes]
    heapq.heapify(heap)
    k = 0
    while heap:
        dmin, v = heapq.heappop(heap)
        if v in removed:
            continue
        if cur[v] != dmin:
            heapq.heappush(heap, (cur[v], v)); continue
        k = max(k, cur[v])
        core[v] = k
        removed.add(v)
        for u in adj[v]:
            if u not in removed:
                cur[u] -= 1
                heapq.heappush(heap, (cur[u], u))
    return core

def onion_profile(core):
    """coreness multiset -> sorted (k, count). And the inner (max-coreness) shell size."""
    hist = defaultdict(int)
    for v, c in core.items():
        hist[c] += 1
    kmax = max(hist) if hist else 0
    inner = hist[kmax]
    return sorted(hist.items()), kmax, inner

def main():
    print("=== W8-KC4: k-core onion of the folded gate graph (N=32 literal) ===\n")
    results = {}
    for mode, lbl in (("sr60", "sr=60 (free W57..60)"), ("sr59", "sr=61-equiv (free W57..61)")):
        cnf = encode_collision(mode=mode)
        adj = incidence_graph(cnf.clauses)
        core = coreness(adj)
        prof, kmax, inner = onion_profile(core)
        results[mode] = (cnf, adj, core, prof, kmax, inner)
        print(f"\n--- {lbl} ---")
        print(f"  vars(graph nodes) = {len(adj)} ; clauses = {len(cnf.clauses)} ; free vars named = {len(cnf.free_var_names)}")
        print(f"  max coreness (k_max) = {kmax} ; inner-shell |k==k_max| = {inner}")
        print(f"  onion profile (k: count), top shells:")
        for k, c in sorted(prof, reverse=True)[:8]:
            print(f"     k={k:>3}: {c} vars")

    # --- max-core jump 60 -> 61? ---
    k60 = results['sr60'][4]; k61 = results['sr59'][4]
    in60 = results['sr60'][5]; in61 = results['sr59'][5]
    print(f"\n--- max-core nucleation check ---")
    print(f"  k_max: sr60={k60}  sr61={k61}   (jump? {k61-k60:+d})")
    print(f"  inner-shell size: sr60={in60}  sr61={in61}   (claim inner ~128 round-bits)")
    print(f"  is inner-shell(60)={in60} in 128+-20 ([108,148])? {'YES' if 108<=in60<=148 else 'NO'}")

    # --- are the 4 highest-coreness vars the 4 anchors? (free vars are the round bits) ---
    cnf60, adj60, core60, _, kmax60, _ = results['sr60']
    top = sorted(core60.items(), key=lambda kv: -kv[1])[:8]
    named = cnf60.free_var_names
    print(f"\n  top-8 coreness vars (id, core, name-if-free):")
    for v, c in top:
        print(f"     var {v}: core={c}  {named.get(v,'(internal gate wire)')}")
    # how many FREE (round-bit) vars are in the inner shell?
    inner_vars = {v for v, c in core60.items() if c == kmax60}
    free_in_inner = sum(1 for v in inner_vars if v in named)
    print(f"  free(round-bit) vars among the {len(inner_vars)} inner-shell vars: {free_in_inner}")

    # ============ MANDATORY SHUFFLE TEST ============
    print(f"\n=== MANDATORY SHUFFLE TEST (F324) ===")
    cnf = results['sr60'][0]
    allvars = sorted({abs(l) for cl in cnf.clauses for l in cl if abs(l) != 1})
    random.seed(12345)
    shuffled = allvars[:]; random.shuffle(shuffled)
    perm = {old: new for old, new in zip(allvars, shuffled)}
    adj_sh = incidence_graph(cnf.clauses, perm=perm)
    core_sh = coreness(adj_sh)
    prof_sh, kmax_sh, inner_sh = onion_profile(core_sh)
    # (a) is the coreness MULTISET invariant? (a real shell must be)
    orig_prof = sorted(results['sr60'][3])
    same_multiset = (orig_prof == sorted(prof_sh))
    print(f"  (a) coreness MULTISET invariant under shuffle? {same_multiset}")
    print(f"      orig k_max={results['sr60'][4]} inner={results['sr60'][5]} | "
          f"shuffled k_max={kmax_sh} inner={inner_sh}")
    # (b) does an ID-ORDERED reading (the 'deep chain in arithmetic-progression IDs', F213)
    #     survive? Measure: among the inner shell, are the var IDs an arithmetic-progression
    #     contiguous block originally, and is that block destroyed by the shuffle?
    inner_ids_orig = sorted(v for v, c in results['sr60'][2].items() if c == results['sr60'][4])
    # contiguity score = fraction of consecutive-ID gaps == small (allocation-order signature)
    def contiguity(ids):
        if len(ids) < 2: return 0.0
        gaps = [ids[i+1]-ids[i] for i in range(len(ids)-1)]
        small = sum(1 for g in gaps if g <= 4)
        return small/len(gaps)
    inner_ids_sh = sorted(perm[v] for v in inner_ids_orig)
    c_orig = contiguity(inner_ids_orig)
    c_sh = contiguity(inner_ids_sh)
    print(f"  (b) inner-shell var-ID contiguity (allocation-order signature):")
    print(f"      original IDs: {c_orig:.2f}  ->  shuffled IDs: {c_sh:.2f}")
    print(f"      (if the 'onion structure' people see is the contiguous ID block, it is")
    print(f"       DESTROYED by shuffle while true coreness is untouched.)")

    print(f"\n=== KILL CHECK ===")
    k_flat = (k61 == k60)            # no nucleation/jump
    k_size = not (108 <= in60 <= 148)
    k_shuffle = not same_multiset    # would only fire if our coreness impl were ID-dependent (it's not)
    print(f"  flat max-core (no 60->61 nucleation)? k60={k60} k61={k61} -> {'FLAT->KILL' if k_flat else 'jump exists'}")
    print(f"  inner shell {in60} NOT in 128+-20? {'YES->KILL' if k_size else 'in-band'}")
    print(f"  shuffle changes the (true) onion? {'YES->KILL' if k_shuffle else 'no (coreness invariant)'}")
    print(f"  NOTE: the *honest* coreness is shuffle-invariant by construction; any 'shell' that")
    print(f"        people read off ID-order (contiguity {c_orig:.2f}->{c_sh:.2f}) is allocation, not structure.")
    print(f"  KILL FIRES: {k_flat or k_size or k_shuffle}")

if __name__ == '__main__':
    main()
