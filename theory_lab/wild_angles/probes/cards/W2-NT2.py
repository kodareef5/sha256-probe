"""
W2-NT2 — Weil square-root cancellation -> the origin of the 132 / HW~74 plateau.

CARD CLAIM (CATALOG):
  Each output bit's bias is a sum S = sum_x e^{2pi i (a x + b sigma(x))/2^N} (linear + rotation-
  permuted term, structurally Kloosterman/Salie). Weil: |S| <= C*2^{N/2} for non-degenerate
  frequencies, full 2^N only on a thin degenerate set. #degenerate dirs = biasable "soft" bits
  (~124); sqrt-cancelling dirs = bits pinned near 1/2 = hard-core (~132).
  PROBE: N=8 — exactly compute S(a,b)=sum_x e^{2pi i (a x + b sigma1(x))/2^8} over ALL (a,b);
  classify degenerate (|S|~2^N) vs cancelling (<~2^{N/2}); does cancelling fraction ~ 132/256 ?
  Swap SHR10->SHR9 and check the predicted plateau SHIFT.
KILL: dead if |S| is a smooth continuum (no clean bimodal Weil dichotomy).

PRIOR FINDING (#1, weaponize): "132 = corank" is a CATEGORY ERROR. 132 reproduces ONLY as
the repo's single-bit deterministic-control CENSUS (carry nonlinearity: registers a,b,e,f at
round 63 fully uncontrolled = 128, + 4 scattered dc = 132). It is NOT a GF(2) corank and NOT
a count of Weil-degenerate directions. Any card "deriving 132" must be checked: if it lands on
132 from a character-sum count it is almost certainly COINCIDENCE (132 = 256 - 124; 124 is itself
an artifact of the diff-linear projection). NEVER score CONFIRMED on a near-132 without proving a
real, basis-independent, STABLE structure that equals 132 for the RIGHT reason.

WHAT THIS PROBE DOES (exact, N=8):
  1. Compute S(a,b) = sum_{x=0}^{2^N-1} e^{2pi i (a x + b sigma1(x)) / 2^N} for ALL (a,b) in
     [0,2^N)^2 (65536 sums at N=8). Histogram |S|. Test the card's BIMODAL Weil dichotomy:
     a clean split into a "degenerate" peak near 2^N and a "cancelling" bulk <~ 2^{N/2}.
  2. Count the cancelling fraction (|S| <= C*2^{N/2}) and the degenerate count. Does the
     cancelling fraction land at 132/256 = 0.516 ? And — the weapon — is that the RIGHT object?
     (The 132 census is over 256 OUTPUT BITS, not over 2^{2N} frequency pairs; the units don't
     even match, so a 132/256 fraction here would be a numerical coincidence.)
  3. Robustness: swap sigma1's SHR10->SHR9 (the card's predicted "plateau shift") and re-measure
     the cancelling fraction. The card needs the fraction to MOVE. We report whether it does and
     by how much.
  4. Continuum vs bimodal: measure the gap/bimodality of the |S| histogram (is there a clean
     valley between a degenerate peak and a cancelling bulk, or a smooth continuum -> KILL).
"""
import sys, math, cmath
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb
import transfer_operator as to


def sigma1_fn(N, shr=None):
    """N-scaled sigma1 with optional override of the SHR amount (default = scaled SHR10)."""
    m = (1 << N) - 1
    rp = to._rot_params(N)
    r0, r1, s = rp['s1']  # (ror17-scaled, ror19-scaled, shr10-scaled)
    if shr is not None:
        s = shr

    def ror(x, k):
        k %= N
        return ((x >> k) | (x << (N - k))) & m
    return lambda x: ror(x, r0) ^ ror(x, r1) ^ ((x >> s) & m)


def all_char_sums(N, sigfn):
    """|S(a,b)| for all (a,b). Returns list of magnitudes (length 2^{2N}) and (a,b) for the
    max few. Precompute sigma1(x) once; S(a,b) = sum_x w^{a x + b sig(x)}, w = e^{2pi i/2^N}."""
    Q = 1 << N
    sig = [sigfn(x) for x in range(Q)]
    w = [cmath.exp(2j * math.pi * k / Q) for k in range(Q)]
    mags = []
    # For each (a,b): phase index (a*x + b*sig[x]) mod Q.
    for a in range(Q):
        ax = [(a * x) % Q for x in range(Q)]
        for b in range(Q):
            acc = 0j
            for x in range(Q):
                acc += w[(ax[x] + b * sig[x]) % Q]
            mags.append(abs(acc))
    return mags


def classify(mags, N, C=2.0):
    """Split into degenerate (|S| ~ 2^N) and cancelling (<= C*2^{N/2})."""
    Q = 1 << N
    sqrtN = C * (2 ** (N / 2.0))
    deg = sum(1 for v in mags if v >= 0.75 * Q)        # near-full
    canc = sum(1 for v in mags if v <= sqrtN)           # sqrt-cancelling
    mid = len(mags) - deg - canc
    return dict(deg=deg, canc=canc, mid=mid, total=len(mags),
                sqrt_thr=sqrtN, canc_frac=canc / len(mags), deg_frac=deg / len(mags))


def bimodality(mags, N, nbins=40):
    """Crude bimodality: histogram |S|, find whether there's a clean valley between a low/bulk
    mode and a high (degenerate) mode. Return (is_bimodal, valley_depth_ratio)."""
    Q = 1 << N
    mx = max(mags)
    hist = [0] * nbins
    for v in mags:
        b = min(nbins - 1, int(v / mx * nbins))
        hist[b] += 1
    # smooth peaks: the degenerate mode is the top bin; bulk mode is the argmax of lower half
    top = hist[-1]
    lowhalf = hist[:nbins // 2]
    bulk = max(lowhalf) if lowhalf else 0
    bulk_idx = lowhalf.index(bulk) if lowhalf else 0
    # valley between bulk_idx and last bin
    between = hist[bulk_idx + 1:nbins - 1]
    valley = min(between) if between else 0
    # bimodal if both modes substantial and the valley is much lower than both
    is_bi = (top > 0.001 * len(mags)) and (bulk > 0) and (valley < 0.3 * min(top, bulk) if min(top, bulk) else False)
    return dict(is_bimodal=is_bi, top_bin=top, bulk_bin=bulk, valley=valley, hist=hist)


def run():
    print("# W2-NT2 — Weil bimodal dichotomy in S(a,b)=sum_x e^{2pi i(ax+b sigma1(x))/2^N}?")
    print("# Weapon (#1): 132 is the deterministic-control CENSUS over 256 OUTPUT BITS, not a")
    print("#              Weil-degenerate-direction count over 2^{2N} frequencies. Units differ.\n")
    N = 8
    sig = sigma1_fn(N)
    mags = all_char_sums(N, sig)
    Q = 1 << N
    print(f"[1] N={N}: computed |S(a,b)| for all {len(mags)} = (2^{N})^2 frequency pairs.")
    print(f"    max|S|={max(mags):.1f} (=2^N={Q}?)  min|S|={min(mags):.2f}  "
          f"mean|S|={sum(mags)/len(mags):.2f}  2^(N/2)={2**(N/2):.2f}")

    cls = classify(mags, N)
    print(f"\n[2] Weil classification (degenerate |S|>=0.75*2^N ; cancelling |S|<=2*2^(N/2)={cls['sqrt_thr']:.1f}):")
    print(f"    degenerate = {cls['deg']} ({cls['deg_frac']:.4f})   "
          f"cancelling = {cls['canc']} ({cls['canc_frac']:.4f})   mid = {cls['mid']}")
    # the card's target is a fraction ~132/256 = 0.516
    target = 132 / 256
    print(f"    card target cancelling fraction = 132/256 = {target:.4f}")
    print(f"    |canc_frac - 132/256| = {abs(cls['canc_frac']-target):.4f}")
    # the WEAPON: convert the fraction to an absolute count over 256 'bits' to expose the unit mismatch
    print(f"    NB: there are {len(mags)} frequency pairs, NOT 256 output bits -> the '132'")
    print(f"        census is a DIFFERENT object; canc_frac*256 = {cls['canc_frac']*256:.1f} (vs 132).")

    bi = bimodality(mags, N)
    print(f"\n[3] bimodality of |S| histogram: bimodal? {bi['is_bimodal']}  "
          f"(top-bin={bi['top_bin']}, bulk-bin={bi['bulk_bin']}, valley={bi['valley']})")
    # print a compact histogram profile
    h = bi['hist']
    mxh = max(h) or 1
    print("    |S| histogram (low->high, 40 bins, bar ~ log-scaled):")
    for i in range(0, 40, 2):
        bar = '#' * int(40 * h[i] / mxh)
        print(f"      bin{i:2d} {h[i]:6d} {bar}")

    print(f"\n[4] SHR-swap robustness (card predicts the plateau MOVES when SHR10->SHR9):")
    rp = to._rot_params(N)
    base_shr = rp['s1'][2]
    for shr in sorted(set([base_shr, max(1, base_shr - 1), base_shr + 1])):
        sigx = sigma1_fn(N, shr=shr)
        mg = all_char_sums(N, sigx)
        cx = classify(mg, N)
        tag = " (baseline)" if shr == base_shr else ""
        print(f"    SHR={shr}: cancelling fraction = {cx['canc_frac']:.4f}  "
              f"deg = {cx['deg']}  (canc_frac*256 = {cx['canc_frac']*256:.1f}){tag}")

    print("\n# VERDICT LOGIC:")
    print(f"  - bimodal Weil dichotomy present? {bi['is_bimodal']}  (kill fires if SMOOTH CONTINUUM)")
    print(f"  - cancelling fraction = {cls['canc_frac']:.4f}; 132/256 = {target:.4f}; "
          f"diff = {abs(cls['canc_frac']-target):.4f}")
    print(f"  - UNIT MISMATCH (weapon #1): the 132 is a per-OUTPUT-BIT control census (256 bits),")
    print(f"    this is a per-FREQUENCY-PAIR cancellation count ({len(mags)} pairs). Even if the")
    print(f"    FRACTION grazed 0.516, it would be numerical coincidence, not 'the 132'. A real")
    print(f"    confirmation needs the SAME object (256 output bits) to split 132/124 by Weil.")
    return dict(canc_frac=cls['canc_frac'], bimodal=bi['is_bimodal'], cls=cls)


if __name__ == '__main__':
    run()
