#!/usr/bin/env python3
"""
W7-CG5 — Octal-game encoding: read the wall off the nim-sequence period.

Card claim: encode carry resolution as an octal/subtraction game on the de58 heap; octal
games are eventually periodic (Guy-Smith), so the wall = where de58's size lands on a
Grundy-0 slot of the (computable, periodic) nim-sequence.

PROBE (honored): derive the octal code from the de58 carry-update at small N; compute
G(n) by mex; eventually periodic? G(de58 at the 61-analog)=0 while G>0 at 60-analog sizes?

KILL: the SHA carry rule corresponds to NO well-defined octal game (move legality
depends on MORE than heap size).

Decisive test for the kill clause (the DEFINING property of an octal/subtraction game):
move legality from a heap depends ONLY on the heap SIZE n. We test whether the de58
'heap' has this property: take many underlying states that share the SAME de58 value;
do they all have the SAME set of reachable next-de58 values?  If two equal-de58 states
have DIFFERENT move sets, legality depends on more than size -> NO octal game -> KILL.
(Forced-fit risk flagged: SHA carries depend on the actual addend bits, not just size.)
N small: N=8,10.
"""
import sys
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/cards')
import _minisha as m


def de58_move_table(N):
    """
    Build, for many cascade states reached just before round 58, the map
        de58_value(state)  ->  set of reachable next-de58 values
    A move = choosing the free word that drives de58 (which CG1 showed is w57's analog at
    the round-58 transition: the word feeding the round whose e-output is de58).  We take
    the canonical de58-driving free word and sweep it over all 2^N values to get the
    reachable next-de58 set FROM that state.  We vary the underlying state by varying the
    EARLIER free words (w-prefix), collecting many states grouped by their current de58.
    """
    S = m.setup(N)
    if S is None:
        return None
    P, O = S['P'], S['O']
    MASK, KN = P['MASK'], P['KN']
    rng = 1 << N

    # Reach states 'before round 58' by running round 57 with a free word w57p, then the
    # state-pair entering round 58 has some de57 (constant) -- but the de58 'heap value' is
    # produced by the round-58 transition driven by its free word.  Per CG1, the word that
    # MOVES de58 is the one feeding the round whose e-output IS de58, i.e. round 58's input
    # which is set by w57 (cascade shifts dependency back one).  To get many DISTINCT states
    # that nonetheless share a de58 value, we enumerate (w57a, w57b-as-state-perturb).
    #
    # Concretely: state entering round 58 = run round 57 with free word u.  Then de58 is a
    # function of that state and the round-58 free word v.  Map: (u) -> state_u ; from
    # state_u, sweep v -> next-de58 set.  Group state_u by de58(state_u, v=0).
    from collections import defaultdict
    by_de58 = defaultdict(list)   # de58_value -> list of move-sets (one per state with that de58)
    for u in range(rng):
        # state entering round 58:
        s1 = list(S['st1_56']); s2 = list(S['st2_56'])
        w2 = m.find_w2(s1, s2, 57, u, P, O)
        s1 = list(m.sha_round(s1, KN[57], u, P, O))
        s2 = list(m.sha_round(s2, KN[57], w2, P, O))
        # current de58 'heap value' (with v=0):
        w2b = m.find_w2(s1, s2, 58, 0, P, O)
        t1 = m.sha_round(s1, KN[58], 0, P, O); t2 = m.sha_round(s2, KN[58], w2b, P, O)
        cur_de58 = (t1[4] - t2[4]) & MASK
        # reachable next-de58 set by sweeping the round-58 free word v:
        reach = set()
        for v in range(rng):
            w2v = m.find_w2(s1, s2, 58, v, P, O)
            r1 = m.sha_round(s1, KN[58], v, P, O); r2 = m.sha_round(s2, KN[58], w2v, P, O)
            reach.add((r1[4] - r2[4]) & MASK)
        by_de58[cur_de58].append(frozenset(reach))
    return dict(N=N, by_de58=by_de58)


def analyze(N):
    r = de58_move_table(N)
    if r is None:
        return None
    by = r['by_de58']
    # octal-game test: for each de58 value occurring from >=2 distinct states, are the
    # move-sets identical? (legality depends only on heap size <=> yes for all)
    size_dependent_only = True
    violators = []
    for de58_val, movesets in by.items():
        uniq = set(movesets)
        if len(uniq) > 1:
            size_dependent_only = False
            violators.append((de58_val, len(uniq)))
    n_values = len(by)
    n_multistate = sum(1 for v in by.values() if len(v) >= 2)
    return dict(N=N, n_values=n_values, n_multistate=n_multistate,
                size_dependent_only=size_dependent_only, violators=violators[:8])


if __name__ == '__main__':
    for N in (8, 10):
        a = analyze(N)
        if a is None:
            print(f'N={N}: no kernel'); continue
        print(f'N={N}: distinct de58 heap-values seen={a["n_values"]}, '
              f'values reached from >=2 distinct states={a["n_multistate"]}')
        print(f'  move legality depends ONLY on heap size (octal-game property)? '
              f'{a["size_dependent_only"]}')
        if a['violators']:
            print(f'  VIOLATORS (de58_value, #distinct move-sets): {a["violators"]}')
            print(f'  => same heap value, DIFFERENT legal moves => NOT a well-defined octal '
                  f'game (legality depends on the underlying state/addend bits).')
        print()
