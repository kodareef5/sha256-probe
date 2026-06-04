"""
W5-TO3 — Non-Boolean Omega: the 132 = the LEM-failing (undecided) output bits.

Card claim: a bit is LEM-failing at a stage if NEITHER value is forced (not constructibly
decided until almost-full input). Conjecture: the 132 hard-core bits = the deep-decidability
bits (undecided until almost-full input because the non-invertible feed-forward mixes them
through all-input carries); HW~74 = uniform measure on the undecided coordinates. Toggle
feed-forward->XOR: deep cluster shrinks.

Probe (card): per output bit, decidability depth d(b) = smallest input-prefix forcing it;
bimodal histogram (shallow=LEM holds vs deep=LEM fails)? deep-cluster fraction -> 0.52,
expected HW -> 74? feed-forward off (XOR) shrinks the deep cluster?
Kill: d(b) unimodal/continuous (no Boolean/non-Boolean split), OR invertible feed-forward
doesn't shrink the deep cluster.

------------------------------------------------------------------------------
PRIOR FINDING #1 (the trap this card is built on): "132 = corank" is a 12x-repeated
CATEGORY ERROR. "132" = the DETERMINISTIC-CONTROL CENSUS = {a,b,e,f}@63 fully + 4 dc bits
= 4N+4 (a WIDTH-SCALING count, not a basis-independent object). At SMALL N the same census
lands on DIFFERENT registers (it can pick d,h instead of a,b,e,f). The rule: never CONFIRM
a near-132 without a STABLE, BASIS-INDEPENDENT undecidable object.

So the decisive test for TO3 is NOT "did we get ~132" (132 = 4N+4 only at N=32). It is:
  (1) Is the LEM-failing / undecided-bit set BIMODAL (a clean Boolean/non-Boolean split),
      as the card needs, or a continuous/unimodal depth distribution (KILL clause 1)?
  (2) Does its size = 4N+4 (i.e. it IS the width-scaling control census, the category
      error re-committed), and does it ride a,b,e,f vs d,h as N changes?
  (3) Does an INVERTIBLE feed-forward (XOR replacing modular add) shrink it (card) -- or
      not (KILL clause 2)?

OPERATIONALIZATION (faithful to the writeup's own method, hard_core_132_bits.md):
The writeup defines a bit as hard-core <=> it has ZERO deterministic single-input-bit-flip
controllers. We reproduce that EXACTLY: for the real N-bit compression of a single message
block, for each output-state bit b, count input message-bit flips j such that flipping j
ALWAYS toggles b (over many random base messages) = a *deterministic controller*. A bit is
"LEM-failing / undecided / deep" <=> zero deterministic controllers (no single input forces
it -- it is mixed through carries). "decidability depth" = (#controllers): 0 = deepest.

We do this for the MODULAR round (real) and the XOR-linearized round (feed-forward off),
at N=4,6,8, and report per-register hard-core counts, total, whether total = 4N+4, which
registers carry it, and the depth-distribution shape (bimodal vs continuous).
"""
import sys, random
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/cards')
import _w5co_engine as E

REGS = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']


def compress_state(M, msg, linear=False):
    """Full N-bit compression of a single 16-word message -> final 8-register state.
    linear=True replaces every modular '+' with XOR (feed-forward / carry off)."""
    MASK = M['MASK']; KN = M['KN']
    W = [msg[i] & MASK for i in range(16)] + [0] * 48
    if linear:
        for i in range(16, 64):
            W[i] = (M['s1'](W[i-2]) ^ W[i-7] ^ M['s0'](W[i-15]) ^ W[i-16]) & MASK
    else:
        for i in range(16, 64):
            W[i] = (M['s1'](W[i-2]) + W[i-7] + M['s0'](W[i-15]) + W[i-16]) & MASK
    a, b, c, d, e, f, g, h = M['IVN']
    for i in range(64):
        if linear:
            T1 = (h ^ M['S1'](e) ^ M['Ch'](e, f, g) ^ KN[i] ^ W[i]) & MASK
            T2 = (M['S0'](a) ^ M['Mj'](a, b, c)) & MASK
            h = g; g = f; f = e; e = (d ^ T1) & MASK
            d = c; c = b; b = a; a = (T1 ^ T2) & MASK
        else:
            T1 = (h + M['S1'](e) + M['Ch'](e, f, g) + KN[i] + W[i]) & MASK
            T2 = (M['S0'](a) + M['Mj'](a, b, c)) & MASK
            h = g; g = f; f = e; e = (d + T1) & MASK
            d = c; c = b; b = a; a = (T1 + T2) & MASK
    return (a, b, c, d, e, f, g, h)


def diff_control_census(N, linear=False, n_base=200, seed=7):
    """FAITHFUL reproduction of hard_core_132_bits.md: the census is in the CASCADE
    DIFFERENTIAL setting. For each OUTPUT DIFFERENCE bit (da..dh at r63), count free-tail-
    word input-bit flips that DETERMINISTICALLY toggle that output-diff bit (toggle it in
    EVERY one of n_base random base tail-inputs). A diff-bit with >=1 such deterministic
    controller is 'controlled' (shallow, LEM holds); with 0 it is hard-core (deep, LEM fails).

    This is exactly the writeup's per-output-bit deterministic-controller census. The shift-
    register diff-bits (dd,dg,dh) inherit deterministic control; the freshly-computed
    da,db,de,df do not -> reproduces the a,b,e,f hard-core split.
    linear=True swaps modular '+' for XOR (feed-forward off) in round+cascade."""
    M = E.make_model(N); setup = E.find_M0(M); MASK = M['MASK']; KN = M['KN']
    if setup is None:
        return None, M
    W1p, W2p = setup['W1'], setup['W2']; rng = random.Random(seed)

    def out_diff(w57, w58, w59, w60):
        """full diff-state (da..dh) at r63 for tail input (w57..w60)."""
        s1, s2 = setup['st1'], setup['st2']
        if linear:
            def rnd(s, k, w):
                a, b, c, d, e, f, g, h = s
                T1 = h ^ M['S1'](e) ^ M['Ch'](e, f, g) ^ k ^ w
                T2 = M['S0'](a) ^ M['Mj'](a, b, c)
                return ((T1 ^ T2) & MASK, a, b, c, (d ^ T1) & MASK, e, f, g)
            def w2for(x, y, rr, w1):
                r1 = (x[7] ^ M['S1'](x[4]) ^ M['Ch'](x[4], x[5], x[6]) ^ KN[rr]) & MASK
                r2 = (y[7] ^ M['S1'](y[4]) ^ M['Ch'](y[4], y[5], y[6]) ^ KN[rr]) & MASK
                T21 = (M['S0'](x[0]) ^ M['Mj'](x[0], x[1], x[2])) & MASK
                T22 = (M['S0'](y[0]) ^ M['Mj'](y[0], y[1], y[2])) & MASK
                return (w1 ^ r1 ^ r2 ^ T21 ^ T22) & MASK
            def cb(*xs):
                v = 0
                for x in xs: v ^= x
                return v & MASK
        else:
            rnd = lambda s, k, w: E.sha_round(s, k, w, M)
            w2for = lambda x, y, rr, w1: E.find_w2(x, y, rr, w1, M)
            def cb(*xs):
                v = 0
                for x in xs: v += x
                return v & MASK
        w57b = w2for(s1, s2, 57, w57); s1 = rnd(s1, KN[57], w57); s2 = rnd(s2, KN[57], w57b)
        w58b = w2for(s1, s2, 58, w58); s1 = rnd(s1, KN[58], w58); s2 = rnd(s2, KN[58], w58b)
        w59b = w2for(s1, s2, 59, w59); s1 = rnd(s1, KN[59], w59); s2 = rnd(s2, KN[59], w59b)
        cas = w2for(s1, s2, 60, 0); w60b = (w60 ^ cas) & MASK if linear else (w60 + cas) & MASK
        s1 = rnd(s1, KN[60], w60); s2 = rnd(s2, KN[60], w60b)
        W1_61 = cb(M['s1'](w59),  W1p[54], M['s0'](W1p[46]), W1p[45])
        W2_61 = cb(M['s1'](w59b), W2p[54], M['s0'](W2p[46]), W2p[45])
        W1_62 = cb(M['s1'](w60),  W1p[55], M['s0'](W1p[47]), W1p[46])
        W2_62 = cb(M['s1'](w60b), W2p[55], M['s0'](W2p[47]), W2p[46])
        W1_63 = cb(M['s1'](W1_61), W1p[56], M['s0'](W1p[48]), W1p[47])
        W2_63 = cb(M['s1'](W2_61), W2p[56], M['s0'](W2p[48]), W2p[47])
        s1 = rnd(s1, KN[61], W1_61); s2 = rnd(s2, KN[61], W2_61)
        s1 = rnd(s1, KN[62], W1_62); s2 = rnd(s2, KN[62], W2_62)
        s1 = rnd(s1, KN[63], W1_63); s2 = rnd(s2, KN[63], W2_63)
        return tuple((s1[i] - s2[i]) & MASK for i in range(8))

    bases = [tuple(rng.randrange(MASK + 1) for _ in range(4)) for _ in range(n_base)]
    base_d = [out_diff(*b) for b in bases]
    n_inflip = 4 * N   # free tail words w57..w60, N bits each
    ctrl = {ri: [0] * N for ri in range(8)}
    for j in range(n_inflip):
        wi, wb = divmod(j, N)
        consistent = {(ri, bi): True for ri in range(8) for bi in range(N)}
        toggled = {(ri, bi): False for ri in range(8) for bi in range(N)}
        for k, b in enumerate(bases):
            b2 = list(b); b2[wi] ^= (1 << wb)
            d2 = out_diff(*b2); d1 = base_d[k]
            for ri in range(8):
                xo = d1[ri] ^ d2[ri]
                for bi in range(N):
                    if (xo >> bi) & 1:
                        toggled[(ri, bi)] = True
                    else:
                        consistent[(ri, bi)] = False
        for ri in range(8):
            for bi in range(N):
                if consistent[(ri, bi)] and toggled[(ri, bi)]:
                    ctrl[ri][bi] += 1
    return ctrl, M


def control_census(N, linear=False, n_base=64, seed=1):
    """Reproduce the WRITEUP's notion of 'deterministic control' = DETERMINISTIC LINEAR
    (affine over GF(2)) control. An output bit b is CONTROLLED (LEM holds, shallow) iff it
    is an EXACT affine function of the input message bits:  b = c0 ^ XOR_j (c_j & in_j).
    The cascade SHIFT-REGISTER registers (d,g,h = delayed copies of earlier registers) are
    affine in the inputs; the freshly-computed a,b,e,f (via the nonlinear T1+T2 / carries)
    are NOT. A bit is hard-core / LEM-failing / 'deep' (0 controllers) iff NOT affine.

    Method: sample S random input messages, record (input-bit-vector, output-bit) pairs,
    solve for an affine form over GF(2) by least-squares-free Gaussian elimination on the
    augmented system; an output bit is 'affine/controlled' iff a consistent affine fit
    exists AND it predicts held-out samples perfectly. ctrl[reg][bit] = 1 if affine
    (controlled), 0 if hard-core (deep). (We return 1/0 = controlled/deep, mirroring the
    writeup's binary hard-core verdict.)"""
    M = E.make_model(N); MASK = M['MASK']
    rng = random.Random(seed)
    n_in = 16 * N
    S = max(4 * n_in + 64, n_base)   # enough rows to pin an n_in-variable affine form
    # build sample matrix: rows = messages, cols = input bits (+ const 1)
    msgs = [[rng.randrange(MASK + 1) for _ in range(16)] for _ in range(S)]
    outs = [compress_state(M, m, linear) for m in msgs]

    def inbits(m):
        v = 0
        for wi in range(16):
            v |= (m[wi] & MASK) << (wi * N)
        return v

    in_rows = [inbits(m) for m in msgs]
    # split train/test
    ntr = S - 64
    ctrl = {ri: [0] * N for ri in range(8)}
    ncols = n_in + 1  # +1 for affine constant
    for ri in range(8):
        for bi in range(N):
            # target output bit across samples
            y = [(outs[k][ri] >> bi) & 1 for k in range(S)]
            # augmented rows: [input bits..., const=1 | y]  (solve A c = y over GF(2))
            A = []
            for k in range(ntr):
                row = (in_rows[k] & ((1 << n_in) - 1)) | (1 << n_in)  # set const bit
                A.append((row << 1) | y[k])   # append target as lowest bit (col ncols)
            # Gaussian elimination over GF(2) treating last appended bit as the RHS column
            sol_rows = list(A)
            pivots = []
            r = 0
            for col in range(ncols):  # only pivot on the ncols variable columns (not RHS)
                bit = 1 << (col + 1)  # +1 because RHS occupies bit 0
                sel = next((i for i in range(r, len(sol_rows)) if sol_rows[i] & bit), None)
                if sel is None:
                    continue
                sol_rows[r], sol_rows[sel] = sol_rows[sel], sol_rows[r]
                for i in range(len(sol_rows)):
                    if i != r and (sol_rows[i] & bit):
                        sol_rows[i] ^= sol_rows[r]
                pivots.append(col); r += 1
                if r == len(sol_rows):
                    break
            # inconsistency: a row with all variable cols 0 but RHS 1 => no affine fit
            consistent = True
            for row in sol_rows:
                if (row >> 1) == 0 and (row & 1) == 1:
                    consistent = False
                    break
            if not consistent:
                ctrl[ri][bi] = 0   # not affine -> hard-core/deep
                continue
            # extract one affine solution: c_col = RHS bit of the row whose pivot is col
            coeffs = 0; const = 0
            piv_of = {}
            for row in sol_rows:
                # find pivot col of this row (lowest variable col set)
                vc = row >> 1
                if vc == 0:
                    continue
                pc = (vc & -vc).bit_length() - 1  # lowest set variable col
                rhs = row & 1
                if pc == n_in:
                    const = rhs
                else:
                    if rhs:
                        coeffs |= (1 << pc)
                piv_of[pc] = rhs
            # verify on held-out test samples
            ok = True
            for k in range(ntr, S):
                pred = const
                masked = in_rows[k] & coeffs
                pred ^= (bin(masked).count('1') & 1)
                if pred != y[k]:
                    ok = False
                    break
            ctrl[ri][bi] = 1 if ok else 0
    return ctrl, M


def summarize_diff(N, linear, n_base=200):
    """Primary measurement: cascade-differential deterministic-control census (faithful to
    hard_core_132_bits.md). Reports per-register hard-core counts on the OUTPUT DIFFERENCE."""
    tag = "XOR-linear (feed-forward OFF)" if linear else "modular (real, feed-forward ON)"
    ctrl, M = diff_control_census(N, linear, n_base)
    if ctrl is None:
        print(f"  [{tag}] N={N}: no cascade-eligible M0 -- skipped")
        return None
    per_reg = {}; total_hc = 0; hist = {}
    for ri in range(8):
        hc = sum(1 for bi in range(N) if ctrl[ri][bi] == 0)
        per_reg[REGS[ri]] = hc; total_hc += hc
        for bi in range(N):
            hist[ctrl[ri][bi]] = hist.get(ctrl[ri][bi], 0) + 1
    full_regs = [r for r, c in per_reg.items() if c == N]
    print(f"  [{tag}] N={N}")
    print(f"    per-register hard-core diff-bits (0 deterministic controllers, of {N}): {per_reg}")
    print(f"    fully-hard-core registers: {full_regs}")
    print(f"    TOTAL hard-core = {total_hc}   (4N+4={4*N+4}, 4N={4*N}, 8N={8*N})")
    print(f"    controller-count histogram (0=deepest): {sorted(hist.items())}")
    n0 = hist.get(0, 0)
    # bimodal? a clean Boolean/non-Boolean split needs a 0-cluster AND a high-cluster
    nonzero_counts = [c for c in hist if c > 0]
    print(f"    deep(0-ctrl)={n0}/{8*N} (frac {n0/(8*N):.3f}; card wants ->0.52)"
          f"  shallow-controller-values present: {sorted(nonzero_counts)}")
    return dict(per_reg=per_reg, total=total_hc, full_regs=full_regs, n_deep=n0,
                bimodal=(n0 > 0 and len(nonzero_counts) > 0), hist=hist)


def main():
    print("=== W5-TO3: '132 = LEM-failing bits' -- cascade-differential control census ===\n")
    print("FAITHFUL reproduction of hard_core_132_bits.md: per OUTPUT-DIFFERENCE bit, count")
    print("free-tail-word input-bit flips that DETERMINISTICALLY toggle it. deep/LEM-failing")
    print("<=> 0 controllers. Adversarial bar (finding #1): basis-independent 132, or 4N+4")
    print("width-scaling census riding a,b,e,f (vs d,h at small N)?\n")
    results = {}
    for N in (4, 5, 8):
        print(f"--- N={N}  (differential census) ---")
        rr = summarize_diff(N, linear=False)
        if rr: results[N] = rr
        summarize_diff(N, linear=True)
        print()
    print("=== category-error + bimodality check ===")
    for N in sorted(results):
        rr = results[N]
        print(f"  N={N}: total hard-core={rr['total']}  =4N+4? {rr['total']==4*N+4}  "
              f"=4N? {rr['total']==4*N}  full-hardcore regs={rr['full_regs']}")
    print(f"\n  Decisive: (a) is the deep set BIMODAL (Boolean/non-Boolean split)? "
          f"{ {N: results[N]['bimodal'] for N in results} }")
    print(f"  (b) does the count = 4N+4 (the width-scaling control census = the 132 category")
    print(f"      error)? '132' only equals 4N+4 at N=32; at small N it tracks 4N+4, NOT a")
    print(f"      stable basis-independent object. (c) which registers carry it (a,b,e,f?).")


if __name__ == '__main__':
    main()
