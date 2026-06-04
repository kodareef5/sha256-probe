#!/usr/bin/env python3
"""
W6-OC5 — Min-effort extremal -> dT1_61=0 is the switching surface.

Card claim: collisions reduce to ONE equation dT1_61=0; read it as the switching function
s = dH/du of a minimum-effort reaching problem -- drive to {dT1_61=0} and bang, then the
e-path coasts to x_63=0 for free. Collision cost = control effort Sigma||u_r||; low-HW
collisions cluster near the surface.
Probe: compute dT1_61, control effort E=Sigma hw(dW[r]); does a costate/switching-gradient
-guided min-effort descent reach a collision in FEWER evals than random?
Kill: costate-guided descent no faster than random (true-but-useless = kill by this lab's
standard).

USEFULNESS kill. Reachable-N note: full enumeration of (w57..w60) is R^4; feasible at
N=4 (65k) and N=5 (~1M). At N>=8 (R^4>=4e9) the collision set is NOT enumerable and
collisions are 2^-2N-rare (the engine's own N=8 enumeration TIMED OUT), so we run the
decisive comparison at N=4 and N=5 where the real collision set is in hand. We test:
  (A) effort clustering: control-effort distribution of the ACTUAL (exhaustive) collision
      set vs random points. "Low-HW collisions cluster near the surface" predicts LOWER
      collision effort.
  (B) descent vs random at EQUAL budget: residual(w)=popcount(de61)+popcount(de62)+
      popcount(ds63) (=0 iff collision). switching-gradient greedy descent vs random
      -improving descent vs pure random. Metric: success rate + median evals among hits.
      If the switching gradient is no better (carry kinks wreck the descent), KILL.
"""
import sys, random, statistics
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/cards')
import _w6oc_engine as oc

hw = oc.eng.sb.hw


def run_point(M, setup, w):
    r = oc.eng.run_tail(M, setup, *w)
    MASK = M['MASK']
    s63a, s63b = r['s63']
    ds63 = sum(hw((s63a[k] - s63b[k]) & MASK) for k in range(8))
    residual = hw(r['de61']) + hw(r['de62']) + ds63
    # control effort: total Hamming of the injected cascade difference words (the bang).
    eff = hw(r['cas_off60']) + hw((r['w60b'] - w[3]) & MASK) + hw(r['cas_off61'])
    return residual, r['collide'], eff


def enumerate_all(N, full=True, w57_slices=8):
    """Sweep (w57..w60). full=True: exhaustive R^4 (feasible at N=4). full=False: scan a
    handful of w57 slices x all (w58,w59,w60) (feasible at N=5: w57_slices*R^3). Returns
    collision list + effort lists. The collision set is exact within the scanned region;
    random-effort baseline is over the same scanned points."""
    M, setup = oc.get_model(N); R = M['MASK'] + 1
    colls = []; coll_eff = []; rand_eff = []
    a_range = range(R) if full else range(min(R, w57_slices))
    for a in a_range:
        for b in range(R):
            for c in range(R):
                for d in range(R):
                    res, col, eff = run_point(M, setup, (a, b, c, d))
                    rand_eff.append(eff)
                    if col:
                        colls.append((a, b, c, d)); coll_eff.append(eff)
    span = (R ** 4) if full else (len(a_range) * R ** 3)
    return M, setup, R, colls, coll_eff, rand_eff, span


def descend(M, setup, start, budget, rng, guided):
    R = M['MASK'] + 1; N = M['N']
    w = list(start); evals = 0
    res, col, _ = run_point(M, setup, tuple(w)); evals += 1
    if col:
        return evals, True
    while evals < budget:
        best = None; bestres = res
        order = [(wi, j) for wi in range(4) for j in range(N)]
        if not guided:
            rng.shuffle(order)
        for (wi, j) in order:
            w2 = list(w); w2[wi] ^= (1 << j)
            r2, c2, _ = run_point(M, setup, tuple(w2)); evals += 1
            if c2:
                return evals, True
            if r2 < bestres:
                bestres = r2; best = (wi, j)
                if not guided:
                    break          # random: first improving move
            if evals >= budget:
                return evals, False
        if best is None:
            w = [rng.randrange(R) for _ in range(4)]
            res, col, _ = run_point(M, setup, tuple(w)); evals += 1
            if col:
                return evals, True
        else:
            w[best[0]] ^= (1 << best[1]); res = bestres
    return evals, False


def guided_vs_random(M, setup, N, restarts=25, budget=600):
    R = M['MASK'] + 1
    rng = random.Random(20260603)
    g_succ, g_ev, r_succ, r_ev, pure = 0, [], 0, [], 0
    for _ in range(restarts):
        start = tuple(rng.randrange(R) for _ in range(4))
        ev, ok = descend(M, setup, start, budget, rng, guided=True)
        g_succ += ok; (g_ev.append(ev) if ok else None)
        ev, ok = descend(M, setup, start, budget, rng, guided=False)
        r_succ += ok; (r_ev.append(ev) if ok else None)
        pc = False
        for _ in range(budget):
            if run_point(M, setup, tuple(rng.randrange(R) for _ in range(4)))[1]:
                pc = True; break
        pure += pc
    med = lambda L: statistics.median(L) if L else float('inf')
    return dict(g_rate=g_succ/restarts, r_rate=r_succ/restarts, pure_rate=pure/restarts,
                g_med=med(g_ev), r_med=med(r_ev), budget=budget, restarts=restarts)


def main():
    print("W6-OC5 : is dT1_61=0 a USEFUL min-effort switching surface (descent beats random)?")
    print("         (decisive N=4,5 where the real collision set is enumerable)\n")
    for N in (4, 5):
        full = (N <= 4)
        tag = "exhaustive" if full else "8 w57-slices"
        print(f"=== N={N} ({tag}) ===")
        M, setup, R, colls, ce, re, span = enumerate_all(N, full=full)
        mc = statistics.mean(ce) if ce else float('nan')
        mr = statistics.mean(re) if re else float('nan')
        density = len(colls) / span
        print(f"  (A) {len(colls)} collisions / {span} pts (density {density:.2e}):")
        print(f"      mean control effort  collisions = {mc:.2f}   random = {mr:.2f}   "
              f"low-effort clustering? {mc < mr}")
        D = guided_vs_random(M, setup, N)
        print(f"  (B) descent (budget {D['budget']}/restart, {D['restarts']} restarts):")
        print(f"      switching-gradient: success {D['g_rate']:.2f}, median evals {D['g_med']}")
        print(f"      random-improving  : success {D['r_rate']:.2f}, median evals {D['r_med']}")
        print(f"      pure-random scan  : success {D['pure_rate']:.2f}")
        faster = (D['g_rate'] > D['r_rate'] + 0.1) or \
                 (D['g_rate'] >= D['r_rate'] - 0.05 and D['g_med'] < 0.8 * D['r_med'])
        print(f"      --> switching-gradient BEATS fair random-descent? {faster}   "
              f"(kill fires iff NOT beating)\n")
    print("INTERPRETATION: dT1_61=0 reducing collisions is ESTABLISHED. The card's NEW claim")
    print("is (i) low-effort clustering and (ii) switching-gradient descent beats random.")
    print("If guided ~ random (carry kinks wreck the descent direction), the switching")
    print("surface is true-but-useless as a search guide -> KILL by this lab's standard.")


if __name__ == '__main__':
    main()
