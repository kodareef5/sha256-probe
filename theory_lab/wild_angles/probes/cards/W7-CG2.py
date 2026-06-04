#!/usr/bin/env python3
"""
W7-CG2 — Game thermography -> temperature cools to 0 at the wall.

Card claim: each round is a 'hot' move (many free-word options reducing da-distance)
cooling as freedom is spent; the wall = where incentive (best-mean residual improvement)
crosses 0 (no move strictly improves -> pass control to carries). Predicts a MONOTONE
cool-down with the zero-crossing AT the sr=61 analog.

PROBE (honored): N=6..12 per round, 1-ply lookahead best vs mean residual improvement
over free-word options = temperature; monotone cool-down + zero-crossing at the sr=61
analog?

KILL: temperature not monotone, or zero-crossing far from the boundary.

Per prior-finding #4 (no round-60 knee; rounds 57-60 = the FREE cascade, whole cube tame):
expect the temperature to be FLAT/degenerate across 57-60 (every cascade move keeps da=0,
so there is no incentive gradient), with any 'crossing' an artifact of the free-cascade
triviality rather than a genuine cool-down. We test: is the per-round temperature curve
monotone, and is the zero-crossing AT round 61?

Temperature proxy (1-ply, impartial/max-over-successors per the card):
  residual(state-pair) = Hamming weight of the modular de-vector toward collision
      = popcount of the running 'distance to all-diffs-zero' = sum over registers of
        hw(diff). We measure, at each free round r in 57..60, over all 2^N free-word
        options (with the cascade fixing W2): best improvement (max drop in residual) and
        mean improvement. temperature_r := best - mean.
"""
import sys, statistics
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/cards')
import _minisha as m


def residual(s1, s2, MASK):
    """Distance-to-collision: total Hamming weight of register diffs (0 == collision)."""
    tot = 0
    for i in range(8):
        d = (s1[i] - s2[i]) & MASK
        tot += bin(d).count('1')
    return tot


def temperatures(N):
    S = m.setup(N)
    if S is None:
        return None
    P, O = S['P'], S['O']
    MASK, KN = P['MASK'], P['KN']
    rng = 1 << N

    # Walk a single representative cascade line (free words = 0) and at EACH free round
    # measure best/mean residual improvement over the 2^N options for THAT round's word.
    s1 = list(S['st1_56']); s2 = list(S['st2_56'])
    res0 = residual(s1, s2, MASK)
    curve = []
    for rnd in range(57, 61):
        before = residual(s1, s2, MASK)
        improvements = []
        best_state = None
        for w1 in range(rng):
            w2 = m.find_w2(s1, s2, rnd, w1, P, O)
            t1 = list(m.sha_round(s1, KN[rnd], w1, P, O))
            t2 = list(m.sha_round(s2, KN[rnd], w2, P, O))
            after = residual(t1, t2, MASK)
            improvements.append(before - after)   # positive = residual dropped = 'hot'
            if best_state is None or (before - after) > best_state[0]:
                best_state = (before - after, t1, t2)
        best = max(improvements)
        mean = statistics.fmean(improvements)
        temp = best - mean
        curve.append(dict(round=rnd, before=before, best_impr=best, mean_impr=mean,
                          temperature=temp, n_strict_improving=sum(1 for x in improvements if x > 0)))
        # advance along the cascade with the BEST move (greedy 'play')
        s1, s2 = best_state[1], best_state[2]

    # round 61 'analog': the schedule CONDITION. There the cascade-required W2[61] is
    # FORCED to a single value (no free choice that keeps da=0 AND matches schedule);
    # the 'incentive' is structurally a point mass -> temperature undefined as a max-over-
    # free-options because the free option for sr=62 must additionally satisfy g1_61=h_61=0.
    return dict(N=N, res0=res0, curve=curve)


if __name__ == '__main__':
    for N in (6, 8, 10):
        r = temperatures(N)
        if r is None:
            print(f'N={N}: no kernel'); continue
        print(f'N={N}  (initial residual at r56 = {r["res0"]})')
        print(f'  {"round":>5} {"before":>7} {"best_impr":>9} {"mean_impr":>9} '
              f'{"temp=best-mean":>14} {"#strict>0":>9}')
        for c in r['curve']:
            print(f'  {c["round"]:>5} {c["before"]:>7} {c["best_impr"]:>9} '
                  f'{c["mean_impr"]:>9.3f} {c["temperature"]:>14.3f} {c["n_strict_improving"]:>9}')
        temps = [c['temperature'] for c in r['curve']]
        mono = all(temps[i] >= temps[i+1] for i in range(len(temps)-1))
        crossing = next((c['round'] for c in r['curve'] if c['temperature'] <= 1e-9), None)
        print(f'  monotone cool-down across 57-60? {mono};  zero-crossing round: {crossing} '
              f'(boundary analog = 61)')
        print()
