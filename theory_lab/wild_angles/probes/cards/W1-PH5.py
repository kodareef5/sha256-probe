#!/usr/bin/env python3
"""
W1-PH5 -- Bragg / phase-matching -> the N=10 interference.

CARD PROBE: compute scaled rotation sets {round(k*N/32)} for N=4..16, define a
commensurability score, correlate with measured collision yield; must PREDICT an
unseen resonant N.
KILL: dead if the score doesn't peak at N=10, or its predicted second resonance shows
no yield anomaly.

GROUND TRUTH / HONEST FRAMING: there is NO independent repo claim that "N=10 is a
constructive-interference peak". The card reframes "N=10 was the gold-standard data
point" as a Bragg resonance. The MEASURED collision yield (paper_figures_data.md Fig 2,
best-kernel) is:
   N : 4    5     6   7    8     9      10    11    12
   C : 146  1024  83  373  1644  14263  1467  2720  ~4900
-> N=10 (1467) is NOT a yield peak; N=9 (14263) dwarfs it. The N-mod-4 oscillation is
the dominant structure, not an N=10 resonance. So the kill test ("score peaks at N=10
AND its 2nd resonance shows a yield anomaly") is a high bar the data already strains.

MODEL: schedule taps at lags {2,7,15,16}; "phases" = scaled big/small-sigma rotation
amounts. A Bragg/commensurability score should be LARGE when the modular path-differences
cancel coherently. We compute SEVERAL principled scores (no single cherry-pick) over the
scaled rotation sets and ask, for each: does it peak at N=10? and does its predicted next
resonance show a yield anomaly? Reporting all of them guards against post-hoc score-fishing.
"""
import sys, math, cmath, statistics as st
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb

TAPS = (2, 7, 15, 16)   # sigma1 lag2, W lag7, sigma0 lag15, W lag16
# full SHA-256 rotation amounts that get scaled:
ROT_SRC = dict(S0=(2,13,22), S1=(6,11,25), s0=(7,18,3), s1=(17,19,10))

FIG2 = {4:146,5:1024,6:83,7:373,8:1644,9:14263,10:1467,11:2720,12:4900}

def scaled_set(N):
    sc = lambda x: round(x * N / 32)
    out = {}
    for k,(a,b,c) in ROT_SRC.items():
        out[k] = (sc(a), sc(b), sc(c))
    return out

def all_rot_amounts(N):
    s = scaled_set(N)
    vals = []
    for k in s: vals.extend(s[k])
    return vals

# ---- candidate commensurability scores (Bragg-style), all on the scaled rotations ----
def score_phase_coherence(N):
    """Structure-factor-like coherence: treat each scaled rotation r as a wave exp(2pi i r/N)
    on the ring Z_N; the bright-fringe (Bragg) condition is constructive sum. Score = |sum|/M."""
    rots = all_rot_amounts(N)
    z = sum(cmath.exp(2j*math.pi*r/N) for r in rots)
    return abs(z)/len(rots)

def score_tap_commensurate(N):
    """Bragg literal: path-difference over a tap-lag L with rotation phase shift cancels when
    (scaled-rotation) is commensurate with N/L. Count rotation amounts r s.t. (r * L) % N is
    near 0 for some tap L -> coherent reflection. Score = fraction of (rot,tap) pairs with
    (r*L) % N in {0} (exact) weighted."""
    rots = all_rot_amounts(N)
    hits = 0; tot = 0
    for r in rots:
        for L in TAPS:
            tot += 1
            if (r * L) % N == 0:
                hits += 1
    return hits / tot

def score_gcd_resonance(N):
    """Commensurability via gcd: a Bragg peak when many scaled rotations share a common
    factor with N (lattice planes commensurate). Score = mean over rotations of
    gcd(r,N)/N (larger gcd => more commensurate => stronger reflection)."""
    rots = [r for r in all_rot_amounts(N) if r > 0]
    if not rots: return 0.0
    return st.mean(math.gcd(r, N)/N for r in rots)

def score_pairwise_diff(N):
    """Bright fringe when rotation DIFFERENCES (phase delays between slits) vanish mod N.
    Score = fraction of rotation pairs with equal scaled amount (degenerate phases)."""
    rots = all_rot_amounts(N)
    tot = 0; eq = 0
    for i in range(len(rots)):
        for j in range(i+1, len(rots)):
            tot += 1
            if (rots[i]-rots[j]) % N == 0: eq += 1
    return eq/tot if tot else 0.0

SCORES = {
    'phase_coherence': score_phase_coherence,
    'tap_commensurate': score_tap_commensurate,
    'gcd_resonance':   score_gcd_resonance,
    'pairwise_diff':   score_pairwise_diff,
}

def main():
    print("="*78)
    print("W1-PH5  Bragg / phase-matching -> N=10 interference   (commensurability score)")
    print("="*78)
    Ns = list(range(4, 17))
    print(f"\nscaled rotation sets {{round(k*N/32)}} (taps={TAPS}):")
    for N in Ns:
        s = scaled_set(N)
        print(f"  N={N:2d}: S0={s['S0']} S1={s['S1']} s0={s['s0']} s1={s['s1']}")

    print(f"\n{'N':>3} | " + " | ".join(f"{nm[:9]:>9}" for nm in SCORES) + " |   yield(log2)")
    table = {nm: {} for nm in SCORES}
    for N in Ns:
        row = []
        for nm, fn in SCORES.items():
            v = fn(N); table[nm][N] = v; row.append(f"{v:9.4f}")
        y = math.log2(FIG2[N]) if N in FIG2 else float('nan')
        print(f"{N:>3} | " + " | ".join(row) + f" |   {y:8.3f}")

    # --- does any score peak at N=10? ---
    print(f"\n[peak test: does the score's MAXIMUM over N=4..16 land on N=10?]")
    peaks = {}
    for nm in SCORES:
        argmax = max(table[nm], key=lambda n: table[nm][n])
        peaks[nm] = argmax
        # second-highest (predicted second resonance)
        ranked = sorted(table[nm], key=lambda n: table[nm][n], reverse=True)
        second = ranked[1] if len(ranked) > 1 else None
        print(f"  {nm:16s}: peak N={argmax}  (2nd N={second})  -> peaks at 10? {argmax==10}")

    # --- correlate score with measured yield (must track the bright fringes) ---
    print(f"\n[correlation of each score with measured log2(yield) over N=4..12]")
    yv = [math.log2(FIG2[n]) for n in FIG2]
    for nm in SCORES:
        sv = [table[nm][n] for n in FIG2]
        # Pearson r
        mx=st.mean(sv); my=st.mean(yv)
        num=sum((a-mx)*(b-my) for a,b in zip(sv,yv))
        den=math.sqrt(sum((a-mx)**2 for a in sv)*sum((b-my)**2 for b in yv)) or 1
        print(f"  {nm:16s}: Pearson r(score, yield) = {num/den:+.3f}")

    # --- VERDICT ---
    print("\n"+"="*78)
    any_peak_at_10 = any(p == 10 for p in peaks.values())
    # the empirical fact: N=10 is not a yield peak (N=9 is). State it.
    yield_argmax = max(FIG2, key=lambda n: FIG2[n])
    print(f"  measured yield peak is at N={yield_argmax} (C={FIG2[yield_argmax]}); N=10 yield={FIG2[10]} is NOT a peak")
    print(f"  any commensurability score peaks at N=10? {any_peak_at_10}  (peaks: {peaks})")
    # KILL: score doesn't peak at N=10 (clause A) OR predicted 2nd resonance shows no yield anomaly (clause B)
    clauseA = not any_peak_at_10
    print(f"  KILL clause A (no score peaks at N=10) fires? {clauseA}")
    print(f"  KILL clause B (N=10 isn't even a yield anomaly to begin with) -> the premise fails")
    KILL = clauseA or True   # premise (N=10 = bright fringe) is empirically false
    print(f"\n  KILL_CRITERION fires? {'YES' if KILL else 'NO'}")
    print("="*78)

if __name__ == '__main__':
    main()
