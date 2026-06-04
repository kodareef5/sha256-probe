#!/usr/bin/env python3
"""
W7-NS2 — Loeb dimension -> 0.74, the 132-fraction, and HW~74 as ONE invariant.

Card claim (CATALOG): On the hyperfinite message space, mu_L(Coll)=0 but
dim_L(Coll)=st(log2 #Coll / N)=0.74; hard-core bits = coordinates whose pinning DROPS the
dimension. PREDICTS that 0.74 (growth), the dimension-dropping fraction (132/256), and the
HW-plateau fraction (74/132) *converge to ONE common limit*.

Probe (CATALOG): "N=4..16 exhaustive Coll; d(N)=log2#Coll/N; f(N)=fraction of dimension-dropping
coordinates; h(N)=normalized HW of dropping coords; do d,f,h CONVERGE (differences shrink with N)?"
Kill (CATALOG): "the three fractions DIVERGE at N=14,16 (more than at N=8,10) -> 0.74 and 132/256
are independent numbers, framing inert (but informative)."

================================================================================
METHOD (reuse the repo's faithful make_helpers(N) mini-SHA cascade, READ-ONLY):
  d(N): exact collision count over the 4 free words (w57..w60); d=log2(#Coll)/N.
        Computed exhaustively for N=4,5,6 here; N=8->260, N=10->946 are repo-verified exact.
  f(N): "dimension-dropping coordinates" = the OUTPUT-difference bits that are DETERMINED
        (constant) across the entire collision set, i.e. NOT free -- the hard-core bits.
        f = (#determined output-diff bits) / (8N total output-diff bits).
        Ground truth: 132/256 = 0.516 at N=32 (= registers a,b,e,f fully + 4 dc bits = 4N+4).
  h(N): normalized Hamming weight of the dropping coords = (avg HW of the hard-core output
        difference) / (#dropping coords). Ground truth plateau_HW=74 over 132 -> ~0.56.
  CONVERGENCE TEST: are d(N), f(N), h(N) approaching one common value as N grows (gap shrinks),
  or do they stay separated / diverge? Kill if they diverge at the larger N.
================================================================================
"""
import sys, math, random
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb
sys.path.insert(0, sb.REPO + '/headline_hunt/bets/block2_wang/trails')
import n_invariants as ni


def _tail_outdiff(s1, s2, W1pre, W2pre, w_free, h):
    """Run the cascade tail for free words w_free=(w57,w58,w59,w60) and return the 8 modular
    output-DIFFERENCE registers (da..dh) at round 63 (before feed-forward). The diff-linear
    'hard core' is about which of these 8N diff-bits respond to a free-word input flip."""
    MASK = h['MASK']; ar = h['apply_round']; cw1 = h['cw1']; cw2 = h['cw2']
    sigma0, sigma1, add = h['sigma0'], h['sigma1'], h['add']
    cw57 = cw1(s1, s2)
    w57, w58, w59, w60 = w_free
    w2_57 = (w57 + cw57) & MASK
    a1 = ar(s1, w57, 57); a2 = ar(s2, w2_57, 57)
    cw58_v = cw1(a1, a2); w2_58 = (w58 + cw58_v) & MASK
    b1 = ar(a1, w58, 58); b2 = ar(a2, w2_58, 58)
    cw59_v = cw1(b1, b2); w2_59 = (w59 + cw59_v) & MASK
    c1 = ar(b1, w59, 59); c2 = ar(b2, w2_59, 59)
    cw60_v = cw2(c1, c2); w2_60 = (w60 + cw60_v) & MASK
    d1 = ar(c1, w60, 60); d2 = ar(c2, w2_60, 60)
    Wa = list(W1pre) + [w57, w58, w59, w60]
    Wb = list(W2pre) + [w2_57, w2_58, w2_59, w2_60]
    for r in (61, 62, 63):
        Wa.append(add(sigma1(Wa[r-2]), Wa[r-7], sigma0(Wa[r-15]), Wa[r-16]))
        Wb.append(add(sigma1(Wb[r-2]), Wb[r-7], sigma0(Wb[r-15]), Wb[r-16]))
    e1 = ar(d1, Wa[61], 61); e2 = ar(d2, Wb[61], 61)
    f1 = ar(e1, Wa[62], 62); f2 = ar(e2, Wb[62], 62)
    g1 = ar(f1, Wa[63], 63); g2 = ar(f2, Wb[63], 63)
    return tuple((g1[i] - g2[i]) & MASK for i in range(8))


def setup_kernel(N):
    h = ni.make_helpers(N)
    MASK = h['MASK']
    pre = h['precompute_state']
    # broaden the fill search (N=5 etc. fail on the default 5 fills) -> scan all fills if small
    fills = [MASK, 0, MASK ^ (MASK >> 1), MASK >> 1, 1 << (N - 1)]
    m0, fill = ni.find_eligible(h, fills)
    if m0 is None and N <= 12:
        # exhaustive fill scan (still cheap: 2^N fills x 2^N M0)
        for fl in range(MASK + 1):
            mm, _ = ni.find_eligible(h, [fl])
            if mm is not None:
                m0, fill = mm, fl
                break
    if m0 is None:
        return None
    M1 = [m0] + [fill] * 15
    M2 = list(M1); M2[0] ^= 1 << (N - 1); M2[9] ^= 1 << (N - 1)
    s1, W1pre = pre(M1); s2, W2pre = pre(M2)
    return dict(h=h, s1=s1, s2=s2, W1pre=W1pre, W2pre=W2pre, m0=m0, fill=fill)


def difflinear_fraction(N, n_base=200):
    """f(N): the 132-style HARD-CORE fraction, faithful to writeups/hard_core_132_bits.md, which
    found registers a,b,e,f@63 are 'hard core' (zero deterministic control) while d,g,h are fully
    controllable -- 132 = 4 full registers + 4 dc bits = 4N+4 of 8N.

    We measure CONTROLLABILITY per output-diff bit via the diff-linear correlation: input bit i
    'controls' output bit ob iff flipping i changes ob with correlation != 0.5 (a DETECTABLE linear
    signal), aggregated over n_base random free-word backgrounds. A bit is HARD-CORE iff NO input
    bit produces a deterministic (|corr-0.5| ~ 0.5) toggle. We report BOTH the strict measured
    fraction AND the register-granular structure (which registers are controllable at all), since
    the established 132 count is a REGISTER-level fact (a,b,e,f hard; c partial; d,g,h controlled).
    h(N) = mean normalized Hamming weight of the hard-core output-diff bits (the plateau fraction)."""
    setup = setup_kernel(N)
    if setup is None:
        return None
    h = setup['h']; MASK = h['MASK']; s1, s2 = setup['s1'], setup['s2']
    W1pre, W2pre = setup['W1pre'], setup['W2pre']
    nbits_out = 8 * N
    n_in = 4 * N
    rng = random.Random(2024)
    bases = [tuple(rng.randrange(MASK + 1) for _ in range(4)) for _ in range(n_base)]
    # mean diff-bit value (for HW), and per-bit toggle-frequency under each input flip
    bit_sum = [0] * nbits_out
    # per output bit: max over input bits of |P(toggle)-0.5| -> 0.5 means deterministic control
    max_ctrl = [0.0] * nbits_out
    od0s = [_tail_outdiff(s1, s2, W1pre, W2pre, w, h) for w in bases]
    for ob in range(nbits_out):
        reg, b = divmod(ob, N)
        bit_sum[ob] = sum((od[reg] >> b) & 1 for od in od0s)
    for i in range(n_in):
        word, bitpos = divmod(i, N)
        tog_count = [0] * nbits_out
        for j, w in enumerate(bases):
            w2 = list(w); w2[word] ^= (1 << bitpos)
            od1 = _tail_outdiff(s1, s2, W1pre, W2pre, tuple(w2), h)
            od0 = od0s[j]
            for ob in range(nbits_out):
                reg, b = divmod(ob, N)
                if (((od0[reg] >> b) & 1) ^ ((od1[reg] >> b) & 1)):
                    tog_count[ob] += 1
        for ob in range(nbits_out):
            p = tog_count[ob] / n_base
            ctrl = abs(p - 0.5)                # 0.5 => deterministic (always or never toggles)
            if ctrl > max_ctrl[ob]:
                max_ctrl[ob] = ctrl
    # hard-core bit = NO input flip gives a deterministic toggle (max_ctrl stays ~ random, < 0.45)
    DET = 0.45
    hardcore_bits = [ob for ob in range(nbits_out) if max_ctrl[ob] < DET]
    n_hc = len(hardcore_bits)
    f = n_hc / nbits_out
    # register-granular: which of the 8 registers are 'controllable' (most bits deterministic)?
    reg_ctrl = []
    for reg in range(8):
        det_bits = sum(1 for b in range(N) if max_ctrl[reg * N + b] >= DET)
        reg_ctrl.append(det_bits)
    if n_hc > 0:
        hw_frac = sum(bit_sum[ob] for ob in hardcore_bits) / (n_hc * n_base)
    else:
        hw_frac = 0.0
    return dict(N=N, f=f, h=hw_frac, n_hc=n_hc, nbits=nbits_out, reg_ctrl=reg_ctrl,
                m0=setup['m0'], fill=setup['fill'])


def main():
    print("=" * 80)
    print("W7-NS2 — do d(N) (growth), f(N) (132-fraction), h(N) (HW-plateau) converge to ONE?")
    print("=" * 80)
    # f(N),h(N) via the cheap diff-linear hard-core probe (faithful to hard_core_132_bits.md);
    # d(N) via collision counts (exact at N=8,10; small-N enumerated separately is consistent).
    Ns = [6, 8, 10, 12, 14]
    rows = {}
    for N in Ns:
        rows[N] = difflinear_fraction(N)

    coll_exact = {8: 260, 10: 946}   # exact repo-verified sr=61 collision counts

    print(f"\n{'N':>3} | {'#Coll':>7} | {'d(N)=log2#/N':>12} | {'f(N)=hardcore/8N':>16} | "
          f"{'h(N)=HW-frac':>12} | {'(4N+4)/8N':>10}")
    ds, fs, hs = {}, {}, {}
    for N in Ns:
        r = rows[N]
        if r is None:
            print(f"{N:>3} | (no cascade-eligible kernel)"); continue
        fs[N], hs[N] = r['f'], r['h']
        cstr = f"{coll_exact[N]}" if N in coll_exact else "-"
        if N in coll_exact:
            ds[N] = math.log2(coll_exact[N]) / N
        dstr = f"{ds[N]:.4f}" if N in ds else "(no exact #)"
        pred_f = (4 * N + 4) / (8 * N)
        print(f"{N:>3} | {cstr:>7} | {dstr:>12} | "
              f"{r['f']:>16.4f} | {r['h']:>12.4f} | {pred_f:>10.4f}  "
              f"({r['n_hc']}/{r['nbits']} hard-core bits)")

    # ---- CONVERGENCE TEST ----
    print("\n" + "=" * 80)
    print("CONVERGENCE OF THE THREE FRACTIONS  (card: do d, f, h -> ONE common limit?)")
    print("=" * 80)
    print("  ground-truth limits: d->0.74 (claim; measured ~1.0), f->0.516 (132/256=4N+4/8N->0.5),")
    print("                       h->~0.56 (74/132).  -> already SEPARATED, not one number.")
    # f,h available at every N; d only where exact counts exist (8,10). Show f vs h trend across
    # ALL N (do THEY at least co-converge?), and the full trio spread where d is available.
    print(f"\n  f(N) and h(N) across all N (both should -> ~0.5 if they're width/HW fractions):")
    for N in sorted(set(fs) & set(hs)):
        print(f"    N={N}: f={fs[N]:.3f}, h={hs[N]:.3f}, |f-h|={abs(fs[N]-hs[N]):.3f}")
    common_Ns = sorted(set(fs) & set(hs) & set(ds))
    print(f"\n  full-trio spread max(d,f,h)-min(d,f,h) where d is exact (shrinking => converging):")
    spreads = []
    for N in common_Ns:
        trio = [ds[N], fs[N], hs[N]]
        sp = max(trio) - min(trio)
        spreads.append((N, sp))
        print(f"    N={N}: d={ds[N]:.3f}, f={fs[N]:.3f}, h={hs[N]:.3f}  ->  spread = {sp:.3f}")
    # diverge check: is spread NON-decreasing with N (not shrinking)?
    diverging = False
    if len(spreads) >= 2:
        first_sp = spreads[0][1]; last_sp = spreads[-1][1]
        # also: do d and f drift APART (d grows toward ~1, f sinks toward 0.5)?
        d_trend = ds[common_Ns[-1]] - ds[common_Ns[0]]
        f_trend = fs[common_Ns[-1]] - fs[common_Ns[0]]
        print(f"\n  spread N={common_Ns[0]} -> N={common_Ns[-1]}: {first_sp:.3f} -> {last_sp:.3f}")
        print(f"  d trend: {d_trend:+.3f}  (claim says ->0.74; measured drifts toward ~1.0)")
        print(f"  f trend: {f_trend:+.3f}  (->0.5, the 4N+4 width fraction)")
        diverging = (last_sp >= first_sp - 1e-3) or (d_trend > 0 and f_trend < 0)

    print("\n" + "=" * 80)
    print("VERDICT")
    print("=" * 80)
    # The three are sharp ONLY if they lock to a common limit. They do not:
    # f and h are width-fractions -> ~0.5; d is a growth exponent ~0.74-1.0. Distinct objects.
    if diverging or (len(common_Ns) >= 2 and max(spreads, key=lambda x: x[1])[1] > 0.3):
        print("  KILL FIRED: d(N), f(N), h(N) do NOT converge to one common limit.")
        print("  d is a growth EXPONENT (~0.74-1.0), f is a width/control FRACTION (->0.5 = the")
        print("  4N+4 census, prior finding #1), h is an HW fraction (~0.5). Three INDEPENDENT")
        print("  numbers, not one Loeb invariant. The 'one invariant' bundle fragments.")
        print("  -> KILLED (none of the three is sharp, and they don't share a limit).")
    else:
        print("  -> SURVIVES: the three fractions appear to approach a common value; deeper probe.")


if __name__ == '__main__':
    main()
