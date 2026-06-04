"""
W1-IN2 — XOR/ADD uncertainty principle → a provable "no basis is easy" barrier.

Card conjecture: for a SHA round R, support_⊕(R) · support_+(R) ≥ 2^{cn}, where
support_⊕ = support in the Walsh (XOR/(Z/2)^N character) basis and support_+ =
support in the cyclic-DFT (Z/2^N character) basis. "no basis diagonalizes both."

PROBE (as stated by the card): N=4,6,8,10. Take a single masked lane round bit
e' as a function of ONE input word; compute its Walsh transform (Hadamard over
(Z/2)^N) -> S_⊕ and its cyclic DFT (length-2^N) -> S_+. Plot log2(S_⊕ · S_+)
vs N using an *effective/entropy* support (robust to tiny coefficients). Control:
replace the modular add by XOR -> product should collapse.

KILL: dead if log2(S_⊕ · S_+) is flat / sub-linear in N, or a cheap basis change
drives it below 2^{0.3 N}.

HOW WE BUILD f (honest, real object — not a linearization):
We take the genuine N-bit SHA round (transfer_operator._make_round, scaled
rotations matching the repo mini-SHA). We freeze a random interior state
(a,b,c,d,e,f,g,h) and the round constant k, and let ONE schedule word w vary over
all 2^N values. The round's e-output is  e' = (d + T1) mod 2^N  with
T1 = h + Sigma1(e) + Ch(e,f,g) + k + w. We then pick a single output BIT b* of e'
(masked lane) -> a Boolean function f: (Z/2)^N -> {0,1} (mapped to {+1,-1} for the
spectra, the standard convention so a constant has a single Walsh atom).

The ONLY place w enters e' is additively (e' = const + w mod 2^N, where const
absorbs d and the e-dependent T1 terms that do not involve w). So as a function of
w, e' is literally a modular shift of w by a constant; bit b* of (w+const) is the
canonical "addition mixes the XOR basis" object — exactly what the card wants.

Two transforms of f = (-1)^{bit_b*(w+const)}:
  * Walsh: hat_f_W(a) = sum_w f(w) (-1)^{<a,w>}              (Hadamard)
  * Cyclic: hat_f_C(j) = sum_w f(w) exp(-2pi i j w / 2^N)    (length-2^N FFT)

EFFECTIVE SUPPORT (robust; the card insists on this): for a spectrum vector v,
the *participation-ratio / entropy support*:
    p_k = |v_k|^2 / sum|v|^2 ;  S_eff = exp( H(p) ) where H = -sum p log p  (nats->use 2^H2)
This equals 1 for a single atom, |support| for a flat spectrum, and is robust to
tiny tails (a coefficient contributes ~its probability mass, not a hard count).

We report log2(S_eff_W * S_eff_C) vs N and compare to lines c*N for c in {0.3,0.5,1}.
Control bit*: same construction but e' built with XOR instead of +  (so w enters by
XOR, the Walsh basis diagonalizes it, S_eff_W -> 1, product collapses).
"""
import sys, os, math
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb
import transfer_operator as to
import numpy as np

MASKN = lambda N: (1 << N) - 1


def walsh_hadamard(vec):
    """Fast Walsh-Hadamard transform of a real vector of length 2^N (in place style)."""
    a = vec.astype(np.float64).copy()
    n = len(a)
    h = 1
    while h < n:
        for i in range(0, n, h * 2):
            x = a[i:i+h].copy()
            y = a[i+h:i+2*h].copy()
            a[i:i+h] = x + y
            a[i+h:i+2*h] = x - y
        h *= 2
    return a


def eff_support(spectrum_abs2):
    """Entropy / participation effective support of a power spectrum (|coef|^2).
    Returns exp_2( Shannon entropy in bits ). 1 for a single atom, |G| for flat."""
    tot = spectrum_abs2.sum()
    if tot <= 0:
        return 1.0
    p = spectrum_abs2 / tot
    p = p[p > 0]
    H_bits = -(p * (np.log2(p))).sum()
    return 2.0 ** H_bits


def hard_support(spectrum_abs2, rel_tol=1e-9):
    """Hard support: count of coefficients above rel_tol * max."""
    mx = spectrum_abs2.max()
    if mx <= 0:
        return 1
    return int((spectrum_abs2 > rel_tol * mx).sum())


def round_e_out_as_fn_of_w(N, state, k, use_xor=False):
    """Return array f[w] = e'-output bit (full word) of the genuine N-bit round, as
    a function of the single schedule word w (0..2^N-1), interior state + k frozen."""
    m = MASKN(N)
    rnd = to._make_round(N)
    a, b, c, d, e, f, g, h = state
    out = np.empty(1 << N, dtype=np.int64)
    if not use_xor:
        for w in range(1 << N):
            st2 = rnd((a, b, c, d, e, f, g, h), k, w)
            out[w] = st2[4]   # e' = index 4
    else:
        # XOR-control: identical round but every '+' replaced by '^'. We build it
        # inline (do NOT touch the repo / kernel) to keep the control faithful.
        rp = to._rot_params(N)
        def ror(x, kk):
            kk %= N
            return ((x >> kk) | (x << (N - kk))) & m
        S0r, S1r = rp['S0'], rp['S1']
        S0 = lambda a: ror(a, S0r[0]) ^ ror(a, S0r[1]) ^ ror(a, S0r[2])
        S1 = lambda e: ror(e, S1r[0]) ^ ror(e, S1r[1]) ^ ror(e, S1r[2])
        Ch = lambda e, f, g: ((e & f) ^ ((~e & m) & g)) & m
        for w in range(1 << N):
            T1 = (h ^ S1(e) ^ Ch(e, f, g) ^ (k & m) ^ w) & m   # XOR surrogate
            out[w] = (d ^ T1) & m
    return out


def spectra_for_bit(f_word, bit, N):
    """Given full-word outputs f_word[w], extract bit `bit`, map to +-1, return
    (S_eff_W, S_eff_C, S_hard_W, S_hard_C)."""
    fb = ((f_word >> bit) & 1).astype(np.float64)
    pm = 1.0 - 2.0 * fb                       # {0,1} -> {+1,-1}
    W = walsh_hadamard(pm)
    C = np.fft.fft(pm)
    aW = (W * W)                              # real
    aC = (np.abs(C) ** 2)
    return (eff_support(aW), eff_support(aC),
            hard_support(aW), hard_support(aC))


def run(Ns=(4, 6, 8, 10, 12), seed=12345, n_states=8):
    rng = np.random.default_rng(seed)
    print(f"# W1-IN2  XOR/ADD support-product uncertainty.  seed={seed}, "
          f"{n_states} random interior states per N, all output bits averaged.")
    print(f"{'N':>3} | {'log2 S_W':>9} {'log2 S_C':>9} {'log2 prod':>9} "
          f"{'prod/N':>7} | {'XORctl prod':>11} {'ctl/N':>6} | "
          f"{'hardW':>5} {'hardC':>5}")
    rows = []
    for N in Ns:
        m = MASKN(N)
        prods, swl, scl, hwl, hcl = [], [], [], [], []
        ctl_prods = []
        for _ in range(n_states):
            state = tuple(int(rng.integers(0, 1 << N)) for _ in range(8))
            k = int(rng.integers(0, 1 << N))
            fw = round_e_out_as_fn_of_w(N, state, k, use_xor=False)
            fw_x = round_e_out_as_fn_of_w(N, state, k, use_xor=True)
            for bit in range(N):
                sW, sC, hW, hC = spectra_for_bit(fw, bit, N)
                # guard: a constant bit (all same) has S=1 in both; skip degenerate
                if sW < 1.0 + 1e-9 and sC < 1.0 + 1e-9:
                    continue
                prods.append(math.log2(max(sW * sC, 1e-12)))
                swl.append(math.log2(sW)); scl.append(math.log2(sC))
                hwl.append(hW); hcl.append(hC)
                sWx, sCx, _, _ = spectra_for_bit(fw_x, bit, N)
                ctl_prods.append(math.log2(max(sWx * sCx, 1e-12)))
        if not prods:
            print(f"{N:>3} |  (all bits degenerate)")
            continue
        mp = float(np.mean(prods))
        mctl = float(np.mean(ctl_prods))
        print(f"{N:>3} | {np.mean(swl):9.3f} {np.mean(scl):9.3f} {mp:9.3f} "
              f"{mp/N:7.3f} | {mctl:11.3f} {mctl/N:6.3f} | "
              f"{int(round(np.mean(hwl))):5d} {int(round(np.mean(hcl))):5d}")
        rows.append((N, mp, mp / N, mctl))

    # --- fit slope c of log2(product) ~ c*N (the headline constant) ---
    if len(rows) >= 2:
        xs = np.array([r[0] for r in rows], float)
        ys = np.array([r[1] for r in rows], float)
        A = np.vstack([xs, np.ones_like(xs)]).T
        slope, intercept = np.linalg.lstsq(A, ys, rcond=None)[0]
        # also a pure-power fit log2(prod) = c*N (no intercept), the card's 2^{cN}
        c_noint = float((xs * ys).sum() / (xs * xs).sum())
        print(f"\nFIT  log2(prod) ~= {slope:.4f}*N + {intercept:.4f}   "
              f"(R-implied constant c with intercept)")
        print(f"FIT  log2(prod) ~= {c_noint:.4f}*N   (no-intercept => the 2^(cN) constant c)")
        # control fit
        yc = np.array([r[3] for r in rows], float)
        cc_noint = float((xs * yc).sum() / (xs * xs).sum())
        sc, ic = np.linalg.lstsq(A, yc, rcond=None)[0]
        print(f"CTL  log2(prod_xor) ~= {sc:.4f}*N + {ic:.4f}  (slope ~0 if Walsh diagonalizes XOR)")
        print(f"\nBARRIER CONSTANT c  (ADD round, no-intercept) = {c_noint:.4f}")
        print(f"  vs kill threshold 0.30 :  {'SURVIVES (c>0.30)' if c_noint > 0.30 else 'KILLED (c<=0.30)'}")
        print(f"  control collapse?       :  XOR slope {sc:.4f} (kill predicts ~0)")
    return rows


if __name__ == '__main__':
    run()
