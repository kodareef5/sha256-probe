"""
W7-RA4 — Van der Waerden APs on the de58 axis.   [P3 · cheap]

Card claim: de58 sits at the modular feed-forward; conjecture its reachable set
S ⊂ Z/2^N contains EXCESS arithmetic progressions (structured generators),
explaining why de58 alone grows.

Probe (from CATALOG): N=4..14 collect the *modular* de58 reachable set S_N; count
3-APs and the longest AP vs a random equal-density subset; excess APs + a recurring
common difference?
Kill: AP statistics indistinguishable from random at all N.
Skeptic: at density 2^-22 APs are NOT vdW-forced; only empirical AP-excess matters.

This is a faithful port (at width N) of the repo's de58 enumerator
  headline_hunt/bets/cascade_aux_encoding/encoders/de58_enum.c
S_N = { e1[58]-e2[58]  mod 2^N : w57 in [0,2^N) }, MSB kernel, cascade-1 path-2.
de57=de59=de60 constant (we don't touch them); only de58 varies — Fig.3.

READ-ONLY toward the repo. Throttle externally:
  OMP_NUM_THREADS=2 taskpolicy -b python3 W7-RA4.py
"""
import sys, random
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/cards')
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import _w5co_engine as E
import shabridge as sb

# Expected |de58| from repo Fig.3 (writeups/paper_figures_data.md) — sanity gate.
EXP_DE58 = {4: 2, 6: 8, 8: 8, 10: 16, 11: 32, 12: 512, 13: 32, 14: 32}


def de58_set(N):
    """Reachable de58 set S_N as w57 sweeps [0,2^N).  Mirrors de58_enum.c:
       cascade-1 at round 57 (path-2 word = w57 + off57); round 58 path-1 word=0,
       path-2 word=off58; de58 = e1 - e2  (register index 4)."""
    M = E.make_model(N)
    setup = E.find_M0(M)
    if setup is None:
        return None, M
    MASK = M['MASK']; KN = M['KN']
    s1_0, s2_0 = setup['st1'], setup['st2']
    S = set()
    for w57 in range(MASK + 1):
        s1 = E.sha_round(s1_0, KN[57], w57, M)
        off57 = E.find_w2(s1_0, s2_0, 57, w57, M)  # path-2 word keeping da57->58 = 0
        s2 = E.sha_round(s2_0, KN[57], off57, M)
        # round 58: path-1 word 0, path-2 cascade word
        off58 = E.find_w2(s1, s2, 58, 0, M)
        s1b = E.sha_round(s1, KN[58], 0, M)
        s2b = E.sha_round(s2, KN[58], off58, M)
        S.add((s1b[4] - s2b[4]) & MASK)
    return S, M


def count_3aps(S, mod):
    """Number of (ordered) nontrivial 3-APs (a, a+d, a+2d) with d!=0 fully inside S,
       all arithmetic mod `mod`. Counts a triple once per (a,d)."""
    Sset = S
    c = 0
    for a in Sset:
        for x in Sset:
            d = (x - a) % mod
            if d == 0:
                continue
            if (a + 2 * d) % mod in Sset:
                c += 1
    return c


def longest_ap(S, mod):
    """Longest AP (any common difference d!=0) contained in S, arithmetic mod `mod`.
       Brute (small |S|): for each (start,d) walk while in S."""
    Sset = S
    best, bestd = 1, 0
    for a in Sset:
        for d in range(1, mod):
            L = 1
            x = (a + d) % mod
            while x in Sset:
                L += 1
                x = (x + d) % mod
                if L > mod:  # safety (full cycle)
                    break
            if L > best:
                best, bestd = L, d
    return best, bestd


def common_diff_hist(S, mod):
    """Histogram of common differences appearing in 3-APs — looking for a *recurring*
       dominant d (the 'structured generator' the card predicts)."""
    from collections import Counter
    cd = Counter()
    Sset = S
    for a in Sset:
        for x in Sset:
            d = (x - a) % mod
            if d == 0:
                continue
            if (a + 2 * d) % mod in Sset:
                cd[d] += 1
    return cd


def random_baseline(size, mod, trials=200, seed=12345):
    """Mean/max #3-APs and mean longest-AP over `trials` random size-`size` subsets
       of Z/mod (equal density)."""
    rng = random.Random(seed)
    universe = list(range(mod))
    aps, lens = [], []
    for _ in range(trials):
        R = set(rng.sample(universe, size))
        aps.append(count_3aps(R, mod))
        L, _ = longest_ap(R, mod)
        lens.append(L)
    aps.sort(); lens.sort()
    import statistics as st
    return dict(ap_mean=st.mean(aps), ap_max=max(aps),
                ap_p95=aps[int(0.95 * (len(aps) - 1))],
                len_mean=st.mean(lens), len_max=max(lens))


if __name__ == '__main__':
    print("W7-RA4 — vdW arithmetic progressions on the de58 reachable set\n")
    Ns = [4, 6, 8, 10, 11, 13, 14]   # skip 12 (|de58|=512 -> 3-AP count is O(|S|^2 ) heavy)
    rows = []
    for N in Ns:
        mod = 1 << N
        S, M = de58_set(N)
        if S is None:
            print(f"N={N}: no M0 (cascade-eligible) found; skip")
            continue
        size = len(S)
        exp = EXP_DE58.get(N, '?')
        gate = 'OK' if exp == size else f'!! expected {exp}'
        ap = count_3aps(S, mod)
        L, Ld = longest_ap(S, mod)
        cd = common_diff_hist(S, mod)
        top_cd = cd.most_common(3)
        # density-matched random baseline (cheap; size is tiny)
        base = random_baseline(size, mod, trials=300, seed=999 + N)
        rows.append((N, size, ap, L, Ld, top_cd, base, gate))
        print(f"N={N:>2}  |S|={size:>4} [{gate}]  mod=2^{N}")
        print(f"      de58 3-APs (real)   = {ap}")
        print(f"      random equal-density: mean={base['ap_mean']:.2f}  "
              f"p95={base['ap_p95']:.1f}  max={base['ap_max']}")
        print(f"      longest AP (real)   = {L}  (common diff d={Ld})")
        print(f"      random longest AP   : mean={base['len_mean']:.2f}  max={base['len_max']}")
        print(f"      top common-diffs(real,3): {top_cd}")
        # is real AP count an outlier vs random?  flag excess
        excess = ap > base['ap_p95']
        # is there a single dominant recurring common difference?
        dominant = (top_cd and cd.most_common(1)[0][1] >= 0.5 * ap and ap > 0)
        print(f"      EXCESS vs random p95? {excess}   single dominant d? {bool(dominant)}\n")

    # Verdict signal aggregation
    print("=== AGGREGATE ===")
    any_excess = False
    any_dominant = False
    for (N, size, ap, L, Ld, top_cd, base, gate) in rows:
        ex = ap > base['ap_p95']
        from collections import Counter
        cdcount = Counter(dict(top_cd))
        dom = bool(top_cd) and (top_cd[0][1] >= 0.5 * ap) and ap > 0
        any_excess |= ex
        any_dominant |= dom
        print(f"  N={N:>2}: 3AP real={ap:<5} rand_p95={base['ap_p95']:<6.1f} "
              f"excess={ex}  longestAP real={L} rand_max={base['len_max']} dom_d={dom}")
    print(f"\nANY N with AP-excess over random p95? {any_excess}")
    print(f"ANY N with single dominant recurring common difference? {any_dominant}")
    print("KILL fires iff AP stats are indistinguishable from random at ALL N "
          f"(i.e. no excess anywhere): kill={'YES' if not any_excess else 'no'}")
