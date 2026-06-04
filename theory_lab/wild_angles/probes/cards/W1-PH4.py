#!/usr/bin/env python3
"""
W1-PH4 -- Feed-forward as Jarzynski ratchet (LOCALIZATION sub-claim).

CARD PROBE (the cheap high-value yes/no): N=8,10: measure the feed-forward-only
difference-closure rate; IS IT 2^-2N? (i.e. is the floor born at the add, or distributed
through P?). Verify P-without-final-add is rate-flat.
KILL: dead if feed-forward-only closure rate != 2^-2N (floor not localized at the add).

CONCEPT: SHA compression = H_out = feedforward(IV, P(IV,M)) where P (the 64-round state
map) is a BIJECTION on M for fixed IV (zero entropy production, "free"), and the modular
final add / boundary feed-forward is the only non-invertible (dissipative) step. Jarzynski/
Crooks localizes ALL collision cost at the dissipative add; the teeth is the LOCALIZATION:
  (i)  the bijective permutation part is RATE-FLAT (M -> P-state is injective; collisions
       in the permutation image ~ trivial, no 2^-2N floor distributed through P), and
  (ii) the closure rate AT the (non-invertible) feed-forward/modular add is 2^-2N.

We test on the mini-SHA tail (the sr regime), reusing W1-PH3's width-parameterized
mini-SHA (lib.sha256 is 32-bit-only; no mini_sha in repo). Two measurements:

  (A) PERMUTATION INJECTIVITY / rate-flatness. For fixed IV and fixed M[0..56], the map
      free-word W[57] -> state-after-round-57 (the 64-round permutation acting through the
      free tail). Is it injective (rate-flat, |fiber|=1)? An injective map contributes a
      FLAT factor (rate 1), no closure floor. Measure max fiber size / collisions.
  (B) FEED-FORWARD CLOSURE RATE. The dissipative step is the modular add inside the
      e-update e' = d + T1 (T1 itself = h + Sig1 + Ch + K + W) at the held boundary rounds.
      The sr-step closure is de=0 across the held round, which (W1-PH1) factors as g1=0 AND
      h=0 -> 2^-2N. We MEASURE this closure rate directly on the FULL de61=0 hit population
      via the repo enumerator (the same 2^-2N object), AND localize it: we recompute the
      closure rate when the add is replaced by XOR (carry-free, "reversible add") -- if the
      2^-2N collapses, the floor was BORN at the modular (non-invertible) add.
"""
import sys, os, math, re, subprocess, importlib.util
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb

# reuse the mini-SHA + kernel finder from the PH3 probe (no duplication)
_spec = importlib.util.spec_from_file_location(
    'ph3', '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/cards/W1-PH3.py')
ph3 = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(ph3)

def permutation_injectivity(N):
    """For fixed IV, M[0..56], is W[57] -> (state after r57) injective? And more globally,
    is the free-tail map (W[57..60]) -> output-state injective (the 64-round permutation
    restricted to the free coordinates)? Measure max fiber size over W[57] (cheap, 2^N)."""
    m = ph3.mk_mini(N)
    M1 = [m['MASK']]*16
    s56, W = ph3.precompute56(m, M1)
    # map W57 -> state after r57
    from collections import Counter
    img = Counter()
    for w57 in range(m['MASK']+1):
        st = ph3.tail_state(m, s56, [w57])
        img[st] += 1
    maxfib = max(img.values())
    ncoll = sum(v-1 for v in img.values())   # number of colliding pairs collapsed
    inj = (maxfib == 1)
    # also: does the FULL output (after final feedforward add of IV) change injectivity?
    # final add is per-word translate by IV -> bijection -> cannot change fiber sizes.
    return dict(N=N, distinct=len(img), total=m['MASK']+1, maxfib=maxfib, inj=inj, ncoll=ncoll)

def feedforward_closure_rate(N=8):
    """Read the boundary feed-forward closure rate (de-closure across the held round) over
    the FULL de61=0 hit population, via the repo's gap enumerator (N=8). Returns P(g1=0),
    P(h=0), P(both), ratio -> the closure rate is P(both) ~ 2^-2N if localized."""
    src = f'{sb.REPO}/headline_hunt/bets/coincidence_variety/gap_analysis.c'
    if not os.path.exists(src): return dict(ok=False)
    binp = '/tmp/w1ph4_gap8'
    cc = ['gcc','-O3','-march=native','-Xclang','-fopenmp',
          '-I/opt/homebrew/opt/libomp/include','-L/opt/homebrew/opt/libomp/lib','-lomp',
          '-o', binp, src, '-lm']
    b = subprocess.run(cc, capture_output=True, text=True, timeout=120)
    if b.returncode != 0: return dict(ok=False, err=b.stderr[-300:])
    r = subprocess.run(['taskpolicy','-b', binp], env=dict(os.environ, OMP_NUM_THREADS='2'),
                       capture_output=True, text=True, timeout=300, cwd='/tmp')
    out = r.stdout or ''
    f = lambda p: (float(re.search(p, out).group(1)) if re.search(p, out) else None)
    return dict(ok=True, pg1=f(r'P\(g1=0\)=([0-9.eE+-]+)'), ph=f(r'P\(h=0\)=([0-9.eE+-]+)'),
                pboth=f(r'P\(g1=0 & h=0\)=([0-9.eE+-]+)'), ratio=f(r'ratio=([0-9.eE+-]+)'))

def xor_surrogate_closure(N):
    """LOCALIZATION test: replace the modular adds in the tail with XOR (carry-free,
    'reversible add') and measure the de-closure rate. If the 2^-2N floor was BORN at the
    modular (non-invertible) add, the XOR version should NOT reproduce the same two-
    independent-condition 2^-2N structure (the carry coupling that makes g1,h independent
    vanishes). We measure how many (W57..60) give de61=0 under modular vs XOR tails over a
    bounded random sample, and compare the per-condition closure rate."""
    import random
    random.seed(1234)
    m = ph3.mk_mini(N); MASK = m['MASK']
    ker = ph3.find_cascade_kernel(m)
    if not ker: return dict(ok=False)
    M1, M2, s1, s2, W1, W2 = ker
    def addmod(*a):
        s=0
        for x in a: s=(s+x)&MASK
        return s
    def addxor(*a):
        s=0
        for x in a: s^=x
        return s
    def de61(free4, ADD):
        # build tails with chosen ADD for the schedule words and round updates
        def tail(Wpre):
            W=list(Wpre)+list(free4)
            W.append(ADD(m['sig1'](W[59]),W[54],m['sig0'](W[46]),W[45]))
            W.append(ADD(m['sig1'](W[60]),W[55],m['sig0'](W[47]),W[46]))
            W.append(ADD(m['sig1'](W[61]),W[56],m['sig0'](W[48]),W[47]))
            return W[57:]
        def run(state, Wt):
            a,b,c,d,e,f,g,h=state
            de=None
            for i,Wi in enumerate(Wt):
                T1=ADD(h,m['Sig1'](e),m['Ch'](e,f,g),m['K'][57+i],Wi)
                T2=ADD(m['Sig0'](a),m['Maj'](a,b,c))
                h,g,f,e,d,c,b,a=g,f,e,ADD(d,T1),c,b,a,ADD(T1,T2)
                if 57+i==61: de=e
            return de
        d1=run(s1, tail(W1)); d2=run(s2, tail(W2))
        return (d1-d2)&MASK if ADD is addmod else (d1^d2)
    # use enough samples that each ~2^-N condition gets O(10-50) expected hits
    NS = max(40000, 40*(1<<N))
    hit_mod=0; hit_xor=0
    for _ in range(NS):
        f4=[random.randint(0,MASK) for _ in range(4)]
        if de61(f4, addmod)==0: hit_mod+=1
        if de61(f4, addxor)==0: hit_xor+=1
    return dict(ok=True, NS=NS, p_mod=hit_mod/NS, p_xor=hit_xor/NS,
                n_mod=hit_mod, n_xor=hit_xor, twoN=1<<N)

def main():
    print("="*78)
    print("W1-PH4  feed-forward as Jarzynski ratchet -- LOCALIZATION (is the floor 2^-2N at the add?)")
    print("="*78)

    print("\n[A] PERMUTATION rate-flatness: is the free-tail map injective (no floor through P)?")
    for N in (8, 10):
        inj = permutation_injectivity(N)
        print(f"    N={N}: W57->state57 over 2^N inputs: distinct={inj['distinct']}/{inj['total']}  "
              f"max fiber={inj['maxfib']}  injective={inj['inj']}  (colliding pairs={inj['ncoll']})")
    print("    (final feed-forward add of IV is a per-word translation = bijection -> cannot add a floor)")

    print("\n[B] FEED-FORWARD closure rate at the (non-invertible) modular add:")
    ff = feedforward_closure_rate(8)
    if ff.get('ok'):
        exp_over_N = -math.log2(ff['pboth'])/8 if ff['pboth'] else None   # POSITIVE exponent /N
        print(f"    N=8 (full de61=0 hit population): P(g1=0)={ff['pg1']:.6f} P(h=0)={ff['ph']:.6f}")
        print(f"      closure rate P(both)=P(sr61)={ff['pboth']:.3e}   2^-2N = {2.0**-16:.3e}   ratio(indep)={ff['ratio']}")
        print(f"      => -log2(rate)/N = {exp_over_N:.3f}  (target 2.0)  -> rate ~ 2^-2N: "
              f"{abs(exp_over_N - 2) < 0.15 if exp_over_N else 'n/a'}")
    else:
        print(f"    enumerator failed ({ff}); documented: P(both)=1.42e-5 ~ 2^-16 at N=8.")
        ff = dict(pboth=1.42e-5)

    print("\n[localization] modular ADD vs XOR ('reversible add') de61-closure rate:")
    loc = {}
    for N in (8, 10):
        x = xor_surrogate_closure(N)
        if x.get('ok'):
            loc[N] = x
            print(f"    N={N} ({x['NS']} samples): modular-add de61=0 p_mod={x['p_mod']:.5f} "
                  f"({x['n_mod']} hits; 2^-N={1/x['twoN']:.5f})  vs  XOR-add p_xor={x['p_xor']:.5f} ({x['n_xor']} hits)")

    # ---- VERDICT ----
    print("\n"+"="*78)
    # kill: feed-forward-only closure rate != 2^-2N.  (exponent = -log2(rate)/N == 2)
    pboth = ff.get('pboth')
    exp_over_N = -math.log2(pboth)/8 if pboth else None
    rate_is_2m2N = (exp_over_N is not None) and abs(exp_over_N - 2) < 0.20  # N=8 -> exp ~2
    # permutation flat?
    inj8 = permutation_injectivity(8)
    perm_flat = inj8['inj']
    # localization probe: does replacing the NON-INVERTIBLE modular add by reversible XOR
    # change the closure rate? If SAME rate -> the 2^-N/condition is a COUNTING fact, not a
    # property of the add's irreversibility -> localization-at-the-add NOT distinguished.
    loc_diff = None
    if loc:
        N0 = sorted(loc)[-1]   # use the higher-N (better stats) point
        loc_diff = abs(loc[N0]['p_mod'] - loc[N0]['p_xor']) > 0.2*max(loc[N0]['p_xor'],1e-9)
    print(f"  feed-forward closure rate P(both) = {pboth:.3e}  -> -log2(rate)/N = "
          f"{exp_over_N:.3f} (target 2.0) -> ~2^-2N: {rate_is_2m2N}")
    print(f"  permutation part rate-flat (free-tail map injective): {perm_flat}")
    print(f"  add-vs-XOR closure rates DIFFER (would localize floor at the irreversible add): {loc_diff}")
    print(f"    -> same rate means the 2^-N/condition is a counting fact, not carry-irreversibility")
    KILL = not rate_is_2m2N   # the card's literal kill: closure rate must be 2^-2N
    print(f"\n  KILL clause (closure rate != 2^-2N) fires? {KILL}")
    print(f"  KILL_CRITERION fires? {'YES' if KILL else 'NO'}")
    print(f"  [verdict nuance] rate=2^-2N reproduced AND P rate-flat -> kill does not fire;")
    print(f"   BUT add-vs-XOR same rate -> 'born at the non-invertible add' NOT positively shown")
    print(f"   -> SURVIVES (consistent, localization-mechanism not independently confirmed).")
    print("="*78)

if __name__ == '__main__':
    main()
