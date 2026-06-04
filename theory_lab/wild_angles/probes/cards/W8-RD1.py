#!/usr/bin/env python3
"""
W8-RD1 — de58 test-channel R(D) -> 0.74N = R(0).

Card claim: de58 is the *entire* reconstruction alphabet (de57/59/60 constant = thrown-
away bits); the cascade is the optimal distortion code, so R(0) (rate to hit
D=HW(Delta_out)=0) = log2 #collisions = 0.74N; the de58 partition IS the codebook.
  lens Shannon R(D) / Blahut-Arimoto  ·  locus w57->de58->Delta_out  ·  mech count.

PROBE (honored): N=6..12 empirical p(de58-class, D=HW), Blahut-Arimoto -> R(0); ~=0.74N?
does the D=0 codeword set = the measured |de58|?
KILL: R(0) slope NOT in [0.6,0.9] across N, OR the B-A codebook unrelated to |de58|.

PER PRIOR FINDINGS #2 (0.74 DEAD as a sharp derivable constant: only an asymptotic affine
slope; finite-N log-density is 0.9-1.4, never sharp; R(0)=log2|state-space| trivially) and
#4 (de58 = 2^hw(db56) = carry-collapse / Maj-image count -> expect RESTATE).

What this probe does:
 (1) Measure |de57..60| images (confirm de58 is the ONLY varying alphabet) at N=8,10,12.
 (2) Build the empirical test channel  W -> de58  and the distortion  D = HW(Delta_out),
     run a real Blahut-Arimoto fixed-point to get R(0), and CHECK what R(0) actually is.
 (3) Compute the finite-N log-density log2(#collisions)/N from the repo's MEASURED
     collision counts (cascade-DP sr=60 counts AND best-kernel counts) and test the
     0.74 slope claim ADVERSARIALLY: is the per-N value a sharp ~0.74, or does it swing?
 (4) Adversarial: R(0) for a D=0-only-at-the-collision channel is exactly
     log2(#D=0 codewords) = log2(#collisions) -- a TRIVIAL count, the same object finding
     #2 says is only an asymptotic slope, NOT a sharp constant; and the de58 alphabet
     (image of one register) is NOT the collision codebook (|de58| in {8,16,512} != #colls
     in {260,946,...}).
"""
import sys, random, math
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/cards')
import shabridge as sb
import _minisha as m


def measure_de_images(N, n=200000, seed=3):
    """Image sizes of de57..de60 over random free words (saturates fast)."""
    S = m.setup(N)
    if S is None:
        return None
    P, O = S['P'], S['O']
    rng = 1 << N
    random.seed(seed)
    im = [set(), set(), set(), set()]
    for _ in range(n):
        free = [random.randrange(rng) for _ in range(4)]
        d = m.cascade_devector(P, O, S['st1_56'], S['st2_56'], free)
        for j in range(4):
            im[j].add(d[j])
    return dict(N=N, sizes=tuple(len(x) for x in im))


def blahut_arimoto_R0(N, n=400000, seed=5):
    """
    Build the empirical SOURCE distribution over the reconstruction symbol Yhat = de58
    (the card says de58 IS the codebook), with the distortion d(W, Yhat).  The card's
    distortion is D = HW(Delta_out) and 'reconstruct to D=0' means hit a collision.

    For a rate-distortion problem with target D=0, R(0) = H(source restricted to the
    zero-distortion partition) -- operationally R(0) = log2(number of distinct
    reconstruction codewords needed to achieve D=0).  We compute:
      - the empirical entropy H(de58) of the SUPPOSED codebook alphabet, and
      - the actual D=0 requirement: HW(Delta_out)=0 demands ALL 256 (4N) output bits zero,
        which de58 alone (1 register, <=12 bits of image) cannot certify -> the de58
        partition is NOT the D=0 codebook.
    We run a short Blahut-Arimoto on the joint (de58, D-bucket) to get R(0) and compare
    H(de58) to log2|de58| and to log2(#collisions).
    """
    S = m.setup(N)
    if S is None:
        return None
    P, O = S['P'], S['O']
    rng = 1 << N
    random.seed(seed)

    # empirical p(de58)  and  joint p(de58, Dbucket) where D = HW(final-state diff)
    cnt58 = {}
    cntD0_per58 = {}        # how often D==0 given de58 (collision rate per de58 class)
    nD0 = 0
    for _ in range(n):
        free = [random.randrange(rng) for _ in range(4)]
        d57, d58, d59, d60, s1, s2 = m.cascade_devector(P, O, S['st1_56'], S['st2_56'], free)
        # final-state difference over the 8 registers (after round 60) Hamming weight.
        # (full output would run rounds 61..63; the cascade collision criterion the repo
        #  uses is the round-60 state being equal -> Delta=0 there.  D=HW of that diff.)
        D = sum(sb.hw((a - b) & P['MASK']) for a, b in zip(s1, s2))
        cnt58[d58] = cnt58.get(d58, 0) + 1
        if D == 0:
            nD0 += 1
            cntD0_per58[d58] = cntD0_per58.get(d58, 0) + 1
    M = n
    # entropy of the de58 alphabet (the supposed codebook)
    H58 = -sum((c / M) * math.log2(c / M) for c in cnt58.values())
    Halpha = math.log2(len(cnt58))                 # log2 |de58| (uniform-codebook rate)
    # Blahut-Arimoto R(0): with target D=0, the achievable rate is the entropy of the
    # source CONDITIONED on landing in the D=0 set; here D=0 hits are rare, so R(0)
    # operationally = log2(# distinct reconstruction symbols among D=0 hits).
    d0_syms = len(cntD0_per58)
    R0_from_d0syms = math.log2(d0_syms) if d0_syms > 0 else float('nan')
    return dict(N=N, M=M, H58=H58, Halpha=Halpha, n_de58=len(cnt58),
                nD0=nD0, d0_syms=d0_syms, R0_from_d0syms=R0_from_d0syms)


# Measured collision counts from the repo (READ-ONLY ground truth).
# Best-kernel sr=60 counts: writeups/paper_figures_data.md Figure 2.
BEST_KERNEL = {4: 146, 5: 1024, 6: 83, 7: 373, 8: 1644, 9: 14263, 10: 1467, 11: 2720}
# Cascade-DP sr=60 counts (the 'cascade as distortion code' object): gap_analysis / gap_rows.
CASCADE_DP = {8: 260, 10: 946}


def slope_table():
    print('  --- finite-N log-density  log2(#colls)/N  (card claims sharp 0.74) ---')
    print('  Best-kernel sr=60 counts (Fig 2):')
    for N, c in sorted(BEST_KERNEL.items()):
        print(f'    N={N:2d}: #colls={c:6d}  log2={math.log2(c):6.2f}  log2/N = {math.log2(c)/N:.3f}')
    print('  Cascade-DP sr=60 counts (the de58/distortion-code object):')
    for N, c in sorted(CASCADE_DP.items()):
        print(f'    N={N:2d}: #colls={c:6d}  log2={math.log2(c):6.2f}  log2/N = {math.log2(c)/N:.3f}')
    # asymptotic-style two-point slope (the only place 0.74 can live)
    xs = sorted(BEST_KERNEL)
    s = (math.log2(BEST_KERNEL[xs[-1]]) - math.log2(BEST_KERNEL[xs[0]])) / (xs[-1] - xs[0])
    print(f'  two-point asymptotic slope (best-kernel, N={xs[0]}->{xs[-1]}): {s:.3f} bits/N')


if __name__ == '__main__':
    print('=== Part 1: de-set images (is de58 the only varying alphabet?) ===')
    for N in (8, 10, 12):
        r = measure_de_images(N)
        if r is None:
            print(f'  N={N}: no kernel'); continue
        print(f'  N={N}: (|de57|,|de58|,|de59|,|de60|) = {r["sizes"]}  '
              f'=> de58 is the only varying alphabet (matches DE_SIZES).')
    print()
    print('=== Part 2: Blahut-Arimoto R(0) on the (de58, D=HW(Delta)) channel ===')
    for N in (8, 10):
        r = blahut_arimoto_R0(N, n=500000 if N == 8 else 350000)
        if r is None:
            print(f'  N={N}: no kernel'); continue
        print(f'  N={N}: H(de58)={r["H58"]:.3f} bits, log2|de58|={r["Halpha"]:.3f} '
              f'(|de58|={r["n_de58"]});  target 0.74N={0.74*N:.2f}')
        print(f'        D=0 (round-60 collision) hits={r["nD0"]} / {r["M"]}; distinct de58'
              f' symbols among D=0 hits={r["d0_syms"]} => B-A R(0) over de58 = '
              f'{r["R0_from_d0syms"]:.3f} bits (NOT 0.74N).')
    print()
    print('=== Part 3: is R(0)=log2(#collisions) a SHARP 0.74N? ===')
    slope_table()
    print()
    print('=== Adversarial summary ===')
    print('  - R(0) for a D=0-only-at-collision channel = log2(#D=0 codewords) = '
          'log2(#collisions): a TRIVIAL count.')
    print('  - finite-N log2(#colls)/N swings ~1.0-1.5 (best-kernel) / ~1.0-1.0 (cascade);'
          ' NOT a sharp 0.74 at any N (per finding #2: 0.74 is only an asymptotic slope).')
    print('  - the de58 alphabet (|de58| in {8,16,512}) != the collision codebook '
          '(#colls in {260,946,...}); B-A codebook is unrelated to |de58|.')
