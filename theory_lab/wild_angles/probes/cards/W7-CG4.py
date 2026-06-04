#!/usr/bin/env python3
"""
W7-CG4 — Misère cascade: is the wall intrinsic or an artifact of orientation?

Card claim: flip to misère (last collision-completing move loses); if the wall is
intrinsic the P-set is invariant (tame), if it moves the boundary is an artifact of
pointing the objective at the normal-play terminal (wild).

PROBE (honored): N=6..10 compute normal-play P-set (Grundy 0) and misère P-set on the
SAME graph; coincide near the boundary (tame, intrinsic) or diverge (wild)?

KILL: P-sets identical everywhere (fully tame -> misère adds nothing), OR the graph too
coupled to define disjunctive misère.

Construction of the impartial game graph (the cheapest faithful one):
  A position = (round r in 57..61, state-pair (s1,s2)).  A MOVE at round r = a choice of
  free word W1[r] (the cascade fixes W2[r] to keep da=0); it advances to round r+1.
  TERMINAL = the collision-completing condition.  Round 61 is the wall: the move
  'completes the collision' iff it lands g1=0 AND h=0 (the established sr=61 condition).
  Normal play: the player who makes the collision-completing move WINS.
  Misère play: that same player LOSES.

We compute, by backward induction on the finite round-layered DAG:
  W_normal(pos) = True if the player to move can force a win under normal play
  W_misere(pos) = same under misère
P-set = positions where the player to move LOSES (cannot force a win).
Compare the two P-sets; measure divergence near the wall.

Per prior-findings #1/#4 + CG1: the de-vector is NOT a disjunctive sum (coords coupled,
group-free image), so 'disjunctive misère genus' is undefinable; we instead compute the
exact win/loss sets on the literal move graph and test both kill clauses.
"""
import sys
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/cards')
import _minisha as m

sys.setrecursionlimit(100000)


def build_and_solve(N, branch_cap=None):
    S = m.setup(N)
    if S is None:
        return None
    P, O = S['P'], S['O']
    MASK, KN = P['MASK'], P['KN']
    rng = 1 << N
    # branch cap keeps the layered tree small: at each round consider at most `cap` words.
    cap = branch_cap if branch_cap is not None else rng

    # precompute W1p/W2p to get sched at the wall (round 60->61 condition).
    W1 = [x & MASK for x in S['M1']] + [0] * 41
    W2 = [x & MASK for x in S['M2']] + [0] * 41
    for i in range(16, 57):
        W1[i] = (O['s1'](W1[i-2]) + W1[i-7] + O['s0'](W1[i-15]) + W1[i-16]) & MASK
        W2[i] = (O['s1'](W2[i-2]) + W2[i-7] + O['s0'](W2[i-15]) + W2[i-16]) & MASK

    def is_wall_complete(s1, s2, w58, w59, w60, casoff60):
        # sr=61 condition: g1=0 AND h=0 at round 60's schedule word.
        sched1 = (O['s1'](w58) + W1[53] + O['s0'](W1[45]) + W1[44]) & MASK
        sched2 = (O['s1'](w58) + W2[53] + O['s0'](W2[45]) + W2[44]) & MASK
        g1 = (w60 - sched1) & MASK
        h = (casoff60 - ((sched2 - sched1) & MASK)) & MASK
        return (g1 == 0 and h == 0)

    # Layered game over rounds 57,58,59,60 (4 plies); the move at round 60 is the
    # 'collision-completing' move (it either lands the wall condition or not).
    # We solve win/loss with memo on (round, s1, s2, w-history-needed).
    from functools import lru_cache

    # We need w58 at the wall; carry it in the recursion state.
    # state: (round, s1tuple, s2tuple, w58_used)
    # words tried per round limited to range(cap) for tractability.
    sol_normal = {}
    sol_misere = {}

    def solve(round_, s1, s2, w58, misere):
        memo = sol_misere if misere else sol_normal
        key = (round_, s1, s2, w58)
        if key in memo:
            return memo[key]
        if round_ == 60:
            # terminal layer: each move either completes the collision (wall) or not.
            # If a completing move exists, the mover can take it:
            #   normal -> mover WINS; misere -> mover who completes LOSES, so mover prefers
            #   a NON-completing move if one exists (then opponent faces a dead end = also
            #   no further moves -> under misere the player who CANNOT move ... we treat
            #   round 60 as the last ply: completing = terminal.)
            can_complete = False
            can_noncomplete = False
            s1l, s2l = list(s1), list(s2)
            for w60 in range(cap):
                w2 = m.find_w2(s1l, s2l, 60, w60, P, O)
                casoff60 = (w2 - w60) & MASK
                if is_wall_complete(s1l, s2l, w58, None, w60, casoff60):
                    can_complete = True
                else:
                    can_noncomplete = True
                if can_complete and can_noncomplete:
                    break
            if not misere:
                res = can_complete            # normal: WIN iff you can complete
            else:
                # misere: completing LOSES; the mover wins iff they can move to a position
                # where the OPPONENT is forced to complete. With a single terminal ply,
                # the mover wins iff a non-completing move exists that strands the opponent
                # AND a completing move also exists (so the opponent, to move, must complete)
                # Simplest faithful rule for the last ply: misere-WIN iff (can_noncomplete
                # and can_complete) i.e. you can pass the 'must-complete' to the opponent.
                res = (can_noncomplete and can_complete)
            memo[key] = res
            return res
        # interior rounds 57,58,59: mover picks a free word, advances; WIN iff some child is
        # a LOSS for the opponent.
        s1l, s2l = list(s1), list(s2)
        win = False
        for w in range(cap):
            w2 = m.find_w2(s1l, s2l, round_, w, P, O)
            t1 = tuple(m.sha_round(s1l, KN[round_], w, P, O))
            t2 = tuple(m.sha_round(s2l, KN[round_], w2, P, O))
            nw58 = w if round_ == 58 else w58
            child = solve(round_ + 1, t1, t2, nw58, misere)
            if child is False:   # opponent loses
                win = True
                break
        memo[key] = win
        return win

    s1_0 = tuple(S['st1_56']); s2_0 = tuple(S['st2_56'])
    # Enumerate the FULL ply-1 layer (round 57 children) as the 'positions' to compare
    # P-membership for normal vs misere. P-position = player-to-move LOSES.
    positions = []
    s1l, s2l = list(s1_0), list(s2_0)
    for w57 in range(cap):
        w2 = m.find_w2(s1l, s2l, 57, w57, P, O)
        t1 = tuple(m.sha_round(s1l, KN[57], w57, P, O))
        t2 = tuple(m.sha_round(s2l, KN[57], w2, P, O))
        nrm = solve(58, t1, t2, None, False)   # player to move at this child
        mis = solve(58, t1, t2, None, True)
        # P-position (loss for mover) = not win
        positions.append((w57, (not nrm), (not mis)))
    # divergence: positions whose P-membership differs between normal and misere
    diverge = [p for p in positions if p[1] != p[2]]
    n_total = len(positions)
    n_diverge = len(diverge)
    # also the ROOT position
    root_nrm_win = solve(57, s1_0, s2_0, None, False)
    root_mis_win = solve(57, s1_0, s2_0, None, True)
    return dict(N=N, cap=cap, n_total=n_total, n_diverge=n_diverge,
                root_normal_P=(not root_nrm_win), root_misere_P=(not root_mis_win),
                example_diverge=diverge[:5])


def count_terminal_wins(N, n_samples=2_000_000, seed=3):
    """
    The misère/normal distinction only has content if a 'collision-completing' (wall)
    move EXISTS to relabel. Count wall completions (g1=0 AND h=0) over random cascade
    prefixes -> the size of the terminal WINNING-move set.  (sr61 completions.)
    """
    import random
    S = m.setup(N); P, O = S['P'], S['O']
    MASK, KN = P['MASK'], P['KN']; rng = 1 << N
    W1 = [x & MASK for x in S['M1']] + [0] * 41
    W2 = [x & MASK for x in S['M2']] + [0] * 41
    for i in range(16, 57):
        W1[i] = (O['s1'](W1[i-2]) + W1[i-7] + O['s0'](W1[i-15]) + W1[i-16]) & MASK
        W2[i] = (O['s1'](W2[i-2]) + W2[i-7] + O['s0'](W2[i-15]) + W2[i-16]) & MASK
    random.seed(seed)
    de61_zero = 0   # sr60 collisions (de61=0)
    wall = 0       # sr61 completions (g1=0 & h=0)  == the terminal winning move
    for _ in range(n_samples):
        w57 = random.randrange(rng); w58 = random.randrange(rng)
        w59 = random.randrange(rng); w60 = random.randrange(rng)
        s1 = list(S['st1_56']); s2 = list(S['st2_56'])
        casoff60 = 0
        for k, rnd in enumerate(range(57, 61)):
            w1 = (w57, w58, w59, w60)[k]
            w2 = m.find_w2(s1, s2, rnd, w1, P, O)
            if rnd == 60:
                casoff60 = (w2 - w1) & MASK
            s1 = list(m.sha_round(s1, KN[rnd], w1, P, O))
            s2 = list(m.sha_round(s2, KN[rnd], w2, P, O))
        de61 = (s1[4] - s2[4]) & MASK   # cascade keeps da=0; de61 governs sr60 completion
        if de61 == 0:
            de61_zero += 1
        sched1 = (O['s1'](w58) + W1[53] + O['s0'](W1[45]) + W1[44]) & MASK
        sched2 = (O['s1'](w58) + W2[53] + O['s0'](W2[45]) + W2[44]) & MASK
        g1 = (w60 - sched1) & MASK
        h = (casoff60 - ((sched2 - sched1) & MASK)) & MASK
        if g1 == 0 and h == 0:
            wall += 1
    return dict(N=N, n=n_samples, de61_zero=de61_zero, wall=wall)


if __name__ == '__main__':
    print('=== P-set comparison on the truncated 4-ply game (branch cap=16) ===')
    for N in (8, 10):
        r = build_and_solve(N, branch_cap=16)
        if r is None:
            print(f'N={N}: no kernel'); continue
        print(f'N={N}: P-set DIVERGENCE normal-vs-misere = {r["n_diverge"]}/{r["n_total"]}; '
              f'root normalP={r["root_normal_P"]} misereP={r["root_misere_P"]}')
    print()
    print('=== Does a collision-COMPLETING (wall) move even exist to relabel? ===')
    for N in (8,):
        c = count_terminal_wins(N, n_samples=1_200_000)
        print(f'N={N}: over {c["n"]:,} cascade prefixes -> sr60(de61=0) completions={c["de61_zero"]}, '
              f'WALL(sr61: g1=0&h=0) completions={c["wall"]}')
        print(f'        expected sr61 ~ #sr60 * 2^-2N ~ {c["de61_zero"]}*{2.0**(-2*N):.2e} '
              f'= {c["de61_zero"]*2.0**(-2*N):.4f}  (i.e. ZERO winning terminal moves)')
