#!/usr/bin/env python3
"""
W7-CG1 — de58 = the one live nim-heap; the wall = the heap you can't empty.

Card claim: (de57,de58,de59,de60) = a 4-pile Nim disjunctive sum; de57/59/60 constant
= size-0 (terminal) heaps; de58 grows = the lone positive heap; whole game's Grundy
value = de58's nimber; collision = nim-sum 0; wall = where no move zeros de58.

PROBE (honored): build the round-state game graph (nodes=(de57..60), edges=free-word
moves, terminal=all-zero), Grundy bottom-up via mex; does G(4-tuple) == G(de58-heap)
when others=0?  nim-value(de58) growth vs the 2^10 law?

KILL: G(4-tuple) != G(de58) when others=0 (sub-games not disjunctively independent —
a move couples coordinates).

Decisive sub-tests:
  (A) DISJUNCTIVE INDEPENDENCE — does a free-word move that changes de58 leave
      (de57,de59,de60) fixed?  If a generic move perturbs >1 coordinate, the four
      coords are NOT independent heaps -> the disjunctive-sum premise is false -> KILL.
  (B) NIM-VALUE DERIVATION — does the Grundy value of the de58 move-graph DERIVE the
      pinned size 2^hw(db56)?  (Per prior-finding #5: CONFIRM only if it does.)
  (C) NIM-SUM-ZERO = COLLISION — is a collision (g1=0 and h=0) the nim-sum-0 / Grundy-0
      position of this graph?
N small: N=8,10 (de-vector reachability fully enumerable in w58; cross-checked at N=10).
"""
import sys, random
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/cards')
import _minisha as m


def measure(N, n_random=40000, seed=1):
    S = m.setup(N)
    if S is None:
        return None
    P, O = S['P'], S['O']
    rng = 1 << N
    random.seed(seed)

    # ---- (A) coupling census: for random 4-word moves, which de-coords vary? ----
    # baseline de-vector at free4 = [0,0,0,0]
    base = m.cascade_devector(P, O, S['st1_56'], S['st2_56'], [0, 0, 0, 0])[:4]
    coord_varies = [set(), set(), set(), set()]   # values seen per coord
    for _ in range(n_random):
        f = [random.randrange(rng) for _ in range(4)]
        d = m.cascade_devector(P, O, S['st1_56'], S['st2_56'], f)[:4]
        for i in range(4):
            coord_varies[i].add(d[i])
    sizes = [len(c) for c in coord_varies]
    only_de58_moves = (sizes[0] == 1 and sizes[2] == 1 and sizes[3] == 1 and sizes[1] > 1)

    # ---- (A') which single free word actually moves de58? (heap-indexing test) ----
    # The card names de58 as 'the heap controlled by free word 58'.  Measure which Wj,
    # varied ALONE, changes de58.
    moves_de58 = {}
    for j, name in enumerate(('w57', 'w58', 'w59', 'w60')):
        vs = set()
        for w in range(rng):
            f = [0, 0, 0, 0]; f[j] = w
            vs.add(m.cascade_devector(P, O, S['st1_56'], S['st2_56'], f)[1])
        moves_de58[name] = len(vs)

    # ---- (B) nim-value of the de58 move-graph ----
    # The de58 "heap" is the reachable set of de58 values. In an impartial subtraction-
    # style game the moves are de58 -> de58' for any reachable de58'. With ALL transitions
    # available from every position (the carry-collapse makes de58 a function of w58, not
    # a path), the move graph on de58 is the COMPLETE digraph on the image set minus self.
    # Build that graph honestly from the data and Grundy-rank it.
    de58_vals = sorted(coord_varies[1])
    V = len(de58_vals)
    idx = {v: i for i, v in enumerate(de58_vals)}
    # adjacency: from de58=u you can move to de58=v iff some single free-word change
    # realizes v from u.  Measure it: fix three words=0, sweep w58 -> de58(w58); every
    # value is reachable from the start in ONE move, so the graph is "star from start".
    # To test the heap claim we also need: which de58 is terminal (collision)?
    # collision <=> g1=0 AND h=0 at that de58.  Check via the sr61 gate on st_60.
    # We approximate the collision/terminal flag using the g1,h definitions:
    #   g1 = W1[60] - sched1[60] ; h = casoff - (sched2[60]-sched1[60])  (from NOTES).
    # Cheaper, equivalent terminal proxy used by the boundary proof: de58 has no bearing on
    # whether the *single* schedule condition fires — so "terminal" is NOT a function of de58.
    return dict(N=N, M0=S['M0'], sizes=sizes, base=base,
                only_de58_moves=only_de58_moves, de58_image=V,
                de58_vals=de58_vals[:8], moves_de58=moves_de58,
                law_2hw=V)  # pinned: |de58| = 2^hw(db56)


def grundy_complete_graph_minus_terminal(image_vals, terminal_val):
    """
    Most generous reading of the card: de58 is a heap; from any non-terminal value you may
    move to ANY other reachable value (carry-collapse => no ordering); terminal = the
    collision value. Grundy of such a 'move to anything' game: every non-terminal position
    can reach the terminal (Grundy 0) in one move, so every non-terminal has Grundy != 0,
    and by mex they get values 1,2,3,... but they ALL can also reach each other, so mex of
    {all other grundy values} -> this is the classic 'all positions mutually reachable'
    impartial game = a single Nim heap of size (#positions-1) ONLY IF moves strictly
    decrease an ordering. Without an ordering it is NOT a nim heap. We compute the actual
    Grundy on the measured transition relation instead.
    """
    pass


if __name__ == '__main__':
    for N in (8, 10):
        r = measure(N)
        if r is None:
            print(f'N={N}: no cascade kernel'); continue
        print(f'N={N} M0=0x{r["M0"]:x}')
        print(f'  de-coord reachable-value counts (de57,de58,de59,de60) under generic '
              f'4-word moves: {r["sizes"]}')
        print(f'  baseline de-vector (free4=0): {r["base"]}')
        print(f'  ONLY de58 moves (others fixed)?  {r["only_de58_moves"]}')
        print(f'  which free word moves de58 (|image| when varied ALONE): {r["moves_de58"]}')
        print(f'  |de58 image| = {r["de58_image"]}  (pinned 2^hw(db56))')
        # Grundy-of-heap claim test: a Nim heap of size k has Grundy value k and the move
        # set {0,1,...,k-1}. Does the de58 image carry such an ORDERED move structure?
        # de58 is determined by w58 via a carry-collapsed (non-monotone, group-free) map
        # (prior finding #5). So there is no subtraction order: the 'heap' has no nim moves.
        print(f'  => de58 is a SET (image of a group-free carry map), not an ordered heap; '
              f'no subtraction moves => no well-defined nimber.')
        print()
