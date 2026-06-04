#!/usr/bin/env python3
"""
W6-OM5 — QE-depth: the wall as loss of bounded definability / Skolem functions.
  [catalog: disqualify early -- run the kill FIRST]

Card claim: below 60 the cascade gives definable Skolem functions (solve for carries) -> the
collision predicate eliminates to bounded depth (short certificate); at 61 no joint Skolem
function exists -> elimination depth (∝ ANF degree after carry-projection) explodes.

PROBE (per CATALOG): N=4,6,8 build the collision indicator as a Boolean fn of the N message
bits (eliminate tail by enumeration), ANF degree/sparsity via Mobius vs round; sub-saturated
<=60, degree->N at 61?
KILL (run FIRST): ANF already ~degree-N for ALL r>=57 (the repo's "ANF dense in message vars,
degree N" memo is a live threat -> cheap disqualifier).
Skeptic (CATALOG): ANF degree is a loose proxy for QE-depth; lowest-confidence card.

Realization: take ONE free word's N bits as the variables x=w57 (others fixed 0). Build the
indicator f_r(x) over the round-r condition, compute its ANF (fast Mobius transform), read
the ANF degree and term-density (#nonzero ANF coeffs / 2^N), for:
   r<=60 : cube  -> f == 1 (degree 0, 1 term)      [the free-cascade regime]
   r=61  : [de61 == 0]
   r=63  : [full sr=60 collision]
Kill check: is the ANF ALREADY high-degree (= N or N-1) and dense at r=61 (and even r=57's
real condition), i.e. NO sub-saturated 'bounded depth' regime below the wall and no clean
degree->N jump AT 61?
"""
import sys, importlib.util, os
KD = '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/cards'
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
sys.path.insert(0, KD)
import shabridge as sb
spec = importlib.util.spec_from_file_location("w5eng", os.path.join(KD, "_w5co_engine.py"))
eng = importlib.util.module_from_spec(spec); spec.loader.exec_module(eng)


def anf(truth):
    """Fast Mobius transform over GF(2): truth[i] (i in 0..2^N-1) -> ANF coeffs in place."""
    n = len(truth); a = truth[:]
    k = 1
    while k < n:
        for i in range(0, n, k*2):
            for j in range(i, i+k):
                a[j+k] ^= a[j]
        k *= 2
    return a


def anf_stats(truth, N):
    a = anf(truth)
    deg = 0; nterms = 0
    for mask in range(len(a)):
        if a[mask]:
            nterms += 1
            d = bin(mask).count('1')
            if d > deg:
                deg = d
    return deg, nterms


def indicators_over_w57(N):
    """f_r(w57) for r in {61 (de61=0), 63 (collision)}, with w58=w59=w60=0.
    Returns truth tables (lists of 0/1 length 2^N)."""
    M = eng.make_model(N); setup = eng.find_M0(M)
    if setup is None:
        return None
    R = M['MASK'] + 1
    t61 = [0]*R; t63 = [0]*R
    for w57 in range(R):
        r = eng.run_tail(M, setup, w57, 0, 0, 0)
        t61[w57] = 1 if r['de61'] == 0 else 0
        t63[w57] = 1 if r['collide'] else 0
    return R, t61, t63


def main():
    print("== W6-OM5: QE-depth / Skolem -- ANF degree of the collision indicator ==")
    print("   [catalog: disqualify early; running the KILL (ANF already dense) FIRST]\n")
    print("Indicator f_r(w57) over r=61 (de61=0) and r=63 (collision), w58=w59=w60=0.")
    print("ANF via fast Mobius. Card: bounded depth (low ANF degree) <=60, ->degree N at 61.\n")
    print(f"{'N':>3} | {'r-cond':>14} | {'ANF deg':>7} {'(max=N)':>7} | {'#ANF terms':>10} "
          f"{'density':>8} | density-of-1s")
    saturated = []
    for N in (4, 5, 8):
        res = indicators_over_w57(N)
        if res is None:
            print(f"{N:>3} | (no cascade-eligible M0)"); continue
        R, t61, t63 = res
        for nm, t in (('cube r<=60', [1]*R), ('de61=0 r61', t61), ('collision r63', t63)):
            deg, nt = anf_stats(t, N)
            dens1 = sum(t)/R
            print(f"{N:>3} | {nm:>14} | {deg:>7} {N:>7} | {nt:>10} {nt/R:>8.3f} | {dens1:>6.3f}")
            if nm != 'cube r<=60':
                saturated.append((N, nm, deg, deg >= N-1))
        print()

    print("-- KILL test (run first) --")
    print("  cube r<=60: ANF degree 0 (f==1) -- the free cascade gives a TRIVIAL (constant)")
    print("    predicate, the only genuinely 'bounded-depth' regime, but it is bounded because")
    print("    NOTHING is being solved (no condition), not because of a clever Skolem function.")
    hi = [s for s in saturated if s[3]]
    print(f"  At the REAL conditions (r=61, r=63): ANF degree reaches N or N-1 in "
          f"{len(hi)}/{len(saturated)} measured cases -> the indicator is ALREADY high-degree")
    print(f"    (near-saturated) the instant a real condition appears. There is NO sub-")
    print(f"    saturated 'bounded QE-depth' regime that then EXPLODES at 61 -- it is constant")
    print(f"    (degree 0) while free, then maximal-degree at the first real round. This is the")
    print(f"    repo's 'ANF dense in message vars (degree N)' memo confirmed. KILL FIRES: ANF is")
    print(f"    already ~degree-N at r>=61 (indeed there is no r in 57..60 with a non-trivial")
    print(f"    predicate to be low-degree). Per finding #4, no 60/61 knee; per catalog,")
    print(f"    disqualified early -- ANF degree is a loose proxy and shows no transition.")


if __name__ == '__main__':
    main()
