#!/usr/bin/env python3
"""
W2-PC4 — Definability jump -> "collision exists" stops being local at 61.

Card (CATALOG): bounded-variable / FO+fixed-point definability of "collision through round k" may
collapse at the same k=61 the search does. Below 60 the cascade is a shift register propagating
zeros diagonally (de57/59/60 constant) -> COLL is a bounded-radius LOCAL check (round-independent
pebble count). At 61 da=de kicks in and W[61] couples back via the schedule (t-7, t-16 long-range
feedback) -> the deciding neighborhood RADIUS blows up -> COLL_61 leaves FO^k. An EF/pebble phase
transition.
PROBE: N=4,5 — play the EF/pebble game between a collision and a minimal near-miss; tabulate the
least distinguishing pebble count p*(k); headline = p* flat for k<=60, JUMPS at 61. Cheaper proxy:
Gaifman-locality radius via BFS on the dependency graph (a ready substrate exists in the repo).
KILL: dead if the locality radius / p* is already growing at k<=59 (never local even when easy), OR
flat through 61 (no jump).

ADVERSARIAL FOCUS (lead finding #4 -- this card is SUSPECT): there is NO sharp 60->61 discontinuity
anywhere in the repo (control/rigidity/reachability decay SMOOTHLY; PH2/CT2 KILLED). So I must
compute the ACTUAL per-round deciding-neighborhood radius and decide: real jump at 61, or smooth?

------------------------------------------------------------------------------------------------
PROXY (the card's own cheaper proxy, which is the decidable one): the Gaifman-locality radius of
COLL_k = the graph distance, in the message-schedule dependency graph, from the output constraint
at round k back to the furthest FREE variable (W[57..60]) that influences the collision condition.
COLL_k is "local of radius r" if the de(k)=0 condition is determined by variables within graph
distance r of round k.

Dependency graph G: nodes = schedule slots W[0..k] (and the round-state nodes). Edges from the
recurrence W[r] <- {W[r-2], W[r-7], W[r-15], W[r-16]} (and W[r] feeds round r's state update).
The collision condition de(k)=0 at round k depends on W[k] (and the running state, which depends on
all prior words). The card's "local radius" is specifically the LONG-RANGE FEEDBACK distance: how
far back along the FREE-WORD support chain the round-k condition reaches. We compute, per round k:
  R_free(k) = max over free words w in supp(W[k]) of (k - w)   [rounds of feedback to reach a free
              lever], and the BFS radius in G from node W[k] to the free-word set.
Below the boundary each round's governing free word is ADJACENT (round r uses fresh word r:
distance 0/1). At 61+ round r re-uses word 59/60 reached only THROUGH the recurrence (distance = the
t-2/t-7/t-16 hop count). The headline needs R_free to JUMP at 61; finding #4 predicts it changes
SMOOTHLY (the recurrence reach grows by a constant per round, no cliff).

We ALSO run a small EXACT pebble/definability proxy at N=4,5: for each k, the least number of free
message words that must be FIXED to determine whether de(k)=0 (the "deciding variable count" p*(k))
-- a combinatorial pebble-count surrogate. We measure it by counting the free words in supp(W[k])
under the carry-monotone schedule support (built like PC1).

Throttled. N=4,5 for the support; the dependency graph is N-independent (structural).
"""
import sys
from collections import deque
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb

FREE = (57, 58, 59, 60)

def build_dep_graph(last=63):
    """Undirected Gaifman graph on schedule slots 0..last. Edge between r and each of
    {r-2,r-7,r-15,r-16} (the recurrence parents) for r>=16."""
    adj = {r: set() for r in range(last + 1)}
    for r in range(16, last + 1):
        for off in (2, 7, 15, 16):
            p = r - off
            if p >= 0:
                adj[r].add(p); adj[p].add(r)
    return adj

def bfs_dist(adj, src, targets):
    """min graph distance from src to ANY node in `targets`, and the full dist map."""
    dist = {src: 0}
    q = deque([src])
    while q:
        u = q.popleft()
        for v in adj[u]:
            if v not in dist:
                dist[v] = dist[u] + 1
                q.append(v)
    reach = {t: dist[t] for t in targets if t in dist}
    return reach

# carry-monotone schedule SUPPORT over free words (reuse PC1-style construction) -------------
def sched_rots(N):
    base = dict(s0=(7, 18, 3), s1=(17, 19, 10))
    f = lambda x: max(0, min(N - 1, round(x * N / 32)))
    return {k: tuple(f(v) for v in t) for k, t in base.items()}

def _small_sigma(word_bits, N, rots):
    a, b, c = rots
    out = []
    for j in range(N):
        s = set()
        s ^= word_bits[(j - a) % N]
        s ^= word_bits[(j - b) % N]
        sj = j - c
        if sj >= 0:
            s ^= word_bits[sj]
        out.append(s)
    return out

def free_word_support(N, last=63):
    r = sched_rots(N); s0r, s1r = r['s0'], r['s1']
    W = [[set() for _ in range(N)] for _ in range(last + 1)]
    for w in FREE:
        W[w] = [{(w, j)} for j in range(N)]
    for rr in range(61, last + 1):
        s1 = _small_sigma(W[rr - 2], N, s1r)
        wm7 = W[rr - 7]
        s0 = _small_sigma(W[rr - 15], N, s0r)
        wm16 = W[rr - 16]
        W[rr] = [s1[j] ^ wm7[j] ^ s0[j] ^ wm16[j] for j in range(N)]
    # free words touched by W[rr]
    fw = {}
    for rr in range(57, last + 1):
        words = set(a[0] for j in range(N) for a in W[rr][j])
        fw[rr] = sorted(words)
    return fw

def run():
    print("=" * 80)
    print("W2-PC4: deciding-neighbourhood radius of COLL_k per round — jump at 61, or smooth?")
    print("=" * 80)
    adj = build_dep_graph(63)
    print("\n(proxy 1) Gaifman feedback radius: graph distance from round-k word to nearest FREE")
    print("word, and the 'long-range feedback reach' = max rounds back to a free lever in supp(W[k]).")
    fw4 = free_word_support(4)
    fw5 = free_word_support(5)
    print(f"\n  {'k':>4} {'free words in supp(W[k])':>26} {'minGraphDist→free':>18} "
          f"{'feedbackReach=k-minfree':>24}")
    radii = {}
    for k in range(57, 64):
        # graph distance from slot k to the free set
        reach = bfs_dist(adj, k, FREE)
        mind = min(reach.values()) if reach else None
        words = fw4.get(k, [])
        fb = (k - min(words)) if words else None  # rounds of feedback to reach earliest free word
        radii[k] = fb
        print(f"  {k:>4} {str(words):>26} {str(mind):>18} {str(fb):>24}")
    # is feedbackReach flat-then-jump at 61, or smooth?
    seq = [radii[k] for k in range(57, 64)]
    steps = [seq[i+1]-seq[i] for i in range(len(seq)-1)]
    print(f"\n  feedback-reach sequence (k=57..63): {seq}")
    print(f"  per-round step (57->58 .. 62->63):  {steps}")
    print(f"  60->61 step = {steps[3]}; max |step| = {max(abs(x) for x in steps)}  "
          f"(jump at 61 'real' iff 60->61 step >> others)")

    print("\n(proxy 2) pebble-count surrogate p*(k) = # FREE WORDS that determine de(k)=0:")
    print(f"  {'k':>4} {'p*(N=4)':>8} {'p*(N=5)':>8}")
    p4 = {}; p5 = {}
    for k in range(57, 64):
        p4[k] = len(fw4.get(k, [])); p5[k] = len(fw5.get(k, []))
        print(f"  {k:>4} {p4[k]:>8} {p5[k]:>8}")
    s4 = [p4[k] for k in range(57, 64)]
    print(f"\n  p*(k) N=4: {s4}   steps {[s4[i+1]-s4[i] for i in range(len(s4)-1)]}")
    # verdict logic
    print("\n  --- verdict logic ---")
    grew_below = any(steps[i] != 0 for i in range(3))  # any change among 57->58,58->59,59->60
    jump_at_61 = steps[3] != 0 and abs(steps[3]) > max(abs(steps[i]) for i in range(3) if True) if True else False
    print(f"  radius growing already at k<=59?  {grew_below}")
    print(f"  60->61 step strictly bigger than every k<=59 step?  "
          f"{steps[3] > max([abs(s) for s in steps[:3]] + [0])}")
    print("  KILL if radius grows at k<=59 (never local even when easy) OR flat through 61 (no jump).")

if __name__ == '__main__':
    run()
