"""
W5-CO1 — Backward bisimulation quotient: routes around the killed forward Myhill-Nerode.

Card claim: forward reachability-quotient is near-injective (255/260, killed). Run
partition-refinement BACKWARD from the ds=0 sink under observational equivalence; the
surviving non-singleton block = the colliding basin, a greatest-fixpoint object the
inverse (non-invertible) feed-forward makes genuinely merge.
Probe: N=4,8 backward refinement from ds=0; does the surviving block track the count
(260 at N=8) and COLLAPSE TO SINGLETONS AT sr=61 BUT STAY FAT AT sr=60?
Kill: collapses to singletons at *both* (no richer than the killed forward quotient).

Per prior finding #6: the carry automaton is forward-deterministic but the BACKWARD
direction blows up. Decisive question: does the backward quotient actually COLLAPSE the
state space (a real reduction), or BLOW UP like everything else?

----------------------------------------------------------------------------
Construction — the FULL modular difference-state, layered by round.
Node = (depth, ds) where ds = (da,db,dc,dd,de,df,dg,dh) mod 2^N is the EXACT modular
diff state, and depth = rounds elapsed in the tail (0 = after round 56 .. 7 = after r63).
We enumerate every tail input (w57,w58,w59,w60), carry the exact path-2 cascade words
(including the round-60 offset w60b used to build the schedule words W2[62], W2[63]),
and record every one-round diff-state transition. Sink = (DEPTH, all-zero) = collision.

BACKWARD bisimulation = greatest fixpoint of observational equivalence toward the sink:
two nodes are equivalent iff they have the same one-step behavior into equivalent
blocks (Paige-Tarjan partition refinement on the successor relation, seeded by the
sink). On a LAYERED DAG this is exactly "same forward future modulo block labels",
i.e. the backward/observational quotient the card asks for.

We report, at sr=60 (truncate the graph at round 60) and at sr=63 (full tail):
  * #nodes, #blocks, #singletons, largest non-singleton block (the merged basin),
  * whether it collapses to singletons (blow-up = KILL) or merges (real reduction).
"""
import sys
from collections import defaultdict, Counter
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/cards')
import _w5co_engine as E


def build_layered_graph(N, last_round):
    M = E.make_model(N); setup = E.find_M0(M); R = M['MASK'] + 1; KN = M['KN']
    W1p, W2p = setup['W1'], setup['W2']; MASK = M['MASK']
    s10, s20 = setup['st1'], setup['st2']

    def ds(s1, s2):
        return tuple((s1[i] - s2[i]) & MASK for i in range(8))

    succ = defaultdict(set); pred = defaultdict(set); nodes = set()

    for w57 in range(R):
        for w58 in range(R):
            for w59 in range(R):
                for w60 in range(R):
                    s1, s2 = s10, s20; depth = 0
                    nodes.add((0, ds(s1, s2)))
                    w59b = None; w60b = None
                    for r in range(57, last_round + 1):
                        if r <= 58:
                            w1 = (w57, w58)[r - 57]
                            w2 = E.find_w2(s1, s2, r, w1, M)
                        elif r == 59:
                            w1 = w59
                            w2 = E.find_w2(s1, s2, 59, w59, M); w59b = w2
                        elif r == 60:
                            w1 = w60
                            cas = E.find_w2(s1, s2, 60, 0, M)
                            w2 = (w60 + cas) & MASK; w60b = w2
                        elif r == 61:
                            w1 = (M['s1'](w59) + W1p[54] + M['s0'](W1p[46]) + W1p[45]) & MASK
                            w2 = (M['s1'](w59b) + W2p[54] + M['s0'](W2p[46]) + W2p[45]) & MASK
                        elif r == 62:
                            w1 = (M['s1'](w60) + W1p[55] + M['s0'](W1p[47]) + W1p[46]) & MASK
                            w2 = (M['s1'](w60b) + W2p[55] + M['s0'](W2p[47]) + W2p[46]) & MASK
                        else:  # r == 63
                            W1_61 = (M['s1'](w59) + W1p[54] + M['s0'](W1p[46]) + W1p[45]) & MASK
                            W2_61 = (M['s1'](w59b) + W2p[54] + M['s0'](W2p[46]) + W2p[45]) & MASK
                            w1 = (M['s1'](W1_61) + W1p[56] + M['s0'](W1p[48]) + W1p[47]) & MASK
                            w2 = (M['s1'](W2_61) + W2p[56] + M['s0'](W2p[48]) + W2p[47]) & MASK
                        ns1 = E.sha_round(s1, KN[r], w1, M)
                        ns2 = E.sha_round(s2, KN[r], w2, M)
                        nb = (depth, ds(s1, s2)); na = (depth + 1, ds(ns1, ns2))
                        succ[nb].add(na); pred[na].add(nb)
                        nodes.add(nb); nodes.add(na)
                        s1, s2 = ns1, ns2; depth += 1
    final_depth = last_round - 56
    sink = (final_depth, (0,) * 8)
    return nodes, succ, pred, sink, final_depth, M, setup


def backward_bisim(nodes, succ, sink):
    """Greatest-fixpoint observational equivalence toward the sink (backward bisimulation
    on a layered DAG): refine by (is-sink, multiset of successor block-labels)."""
    label = {n: (1 if n == sink else 0) for n in nodes}
    for _ in range(len(nodes) + 5):
        sig = {n: (label[n], frozenset(label[s] for s in succ.get(n, ()))) for n in nodes}
        uniq = {}; new = {}
        for n in nodes:
            uniq.setdefault(sig[n], len(uniq))
            new[n] = uniq[sig[n]]
        if new == label:
            break
        label = new
    blocks = defaultdict(list)
    for n in nodes:
        blocks[label[n]].append(n)
    return blocks


def analyze(N, last_round, tag):
    nodes, succ, pred, sink, fd, M, setup = build_layered_graph(N, last_round)
    by_depth = Counter(d for (d, _) in nodes)
    blocks = backward_bisim(nodes, succ, sink)
    sizes = sorted((len(v) for v in blocks.values()), reverse=True)
    n_sing = sum(1 for v in blocks.values() if len(v) == 1)
    # focus on the FINAL layer (the collision sink's layer) — that is where the forward
    # quotient was 'near-injective'; does backward merge it?
    final_nodes = [n for n in nodes if n[0] == fd]
    # which blocks contain final-layer nodes, and how big are those blocks restricted to
    # the final layer?
    blk_of = {}
    for bl, mem in blocks.items():
        for n in mem:
            blk_of[n] = bl
    final_blocks = Counter(blk_of[n] for n in final_nodes)
    final_block_sizes = sorted(final_blocks.values(), reverse=True)
    print(f"--- N={N}  {tag} ---")
    print(f"  nodes per depth                 : {dict(sorted(by_depth.items()))}")
    print(f"  total nodes / backward-bisim blocks : {len(nodes)} / {len(blocks)}")
    print(f"  singleton blocks                : {n_sing} of {len(blocks)}")
    print(f"  top overall block sizes         : {sizes[:6]}")
    print(f"  final layer (the sink's layer)  : {len(final_nodes)} distinct diff-states")
    print(f"     -> backward-bisim classes within final layer: {len(final_blocks)} "
          f"(sizes {final_block_sizes[:6]})")
    merged_final = sum(s for s in final_block_sizes if s > 1)
    print(f"     -> final-layer nodes that MERGE (non-singleton): {merged_final}/{len(final_nodes)}")
    collapse = (len(final_blocks) == len(final_nodes))  # every final node its own class
    print(f"  FINAL-LAYER COLLAPSES TO SINGLETONS? "
          f"{'YES -> backward blows up like forward (KILL clause)' if collapse else 'NO -> backward genuinely merges the basin'}")
    print()
    return collapse, len(final_nodes), len(final_blocks)


def main():
    print("=== W5-CO1: backward bisimulation quotient of the full diff-state tail ===\n")
    for N in (4,):
        analyze(N, 60, 'sr=60 (truncate at round 60: cascade-free regime)')
        analyze(N, 63, 'sr=63 (full tail through the schedule-fixed rounds)')


if __name__ == '__main__':
    main()
