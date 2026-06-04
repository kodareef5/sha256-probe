#!/usr/bin/env python3
"""
W4-FP3 -- Asymptotic freeness of the ARX layers -> the round spectrum factorizes.

Card claim (CATALOG):
  If the fixed XOR-rotation layer L and the carry-add layer A are free, then
  mu(AL) = mu_A box-times mu_L -> 64 rounds reduce to box-times of two alternating
  laws.

  probe: sharp test = one mixed moment (1/N) tr((LA)^2) vs the free-prediction
  from tau(L^k), tau(A^k); does the deviation shrink 4->8?
  kill: deviation doesn't shrink, or mu_{AL} != mu_L box-times mu_A.
  skeptic (card's own): L is fixed & shares the bit-lane geometry with A -- SHA's
  layers are *designed to interlock*, the opposite of free; expect detectable
  non-freeness (value = quantifying it).

THE SHARP FREE IDENTITY we test (Voiculescu): for a, b FREE w.r.t. trace tau,
  tau(abab) = tau(a^2) tau(b)^2 + tau(a)^2 tau(b^2) - tau(a)^2 tau(b)^2.
Here a = A (carry-add layer Jacobian), b = L (XOR-rotation layer), both as real
8N x 8N matrices acting on the difference state, tau(.) = (1/8N) tr(.).
We measure tau((AL)^2)=tau(ALAL) directly and compare to the RHS computed from
the marginal moments tau(A),tau(A^2),tau(L),tau(L^2). The freeness DEFECT is
  defect = | tau(ALAL)_measured - tau(ALAL)_free | / |tau(ALAL)_measured|.
Asymptotic freeness => defect -> 0 as N grows. The card's own skeptic predicts it
will NOT (interlocking bit lanes), so we expect KILL; the *value* is the number.

Layer decomposition (faithful, not invented):
  L = the XOR-linearized round operator (Sigma0/Sigma1 + shift-register wiring,
      carries DROPPED) -- the genuine fixed linear ARX "rotation/XOR" layer.
  A = the carry-add correction = J_local @ L^{-1} when L invertible, else we take
      A as the *pure carry-add layer* built directly: the local Jacobian of the
      two modular adders alone (Sigma/Maj/Ch held at the base point), so that
      J_local = A . L exactly. We verify A.L == J_local numerically.
"""
import sys, time
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb
import transfer_operator as TO
import linround as LR
import numpy as np

import warnings
warnings.filterwarnings('ignore', category=RuntimeWarning)


def local_round_jac(N, state, k, w):
    """Exact local GF(2) difference-Jacobian of one full round (real 0/1, 8N)."""
    rnd = TO._make_round(N)
    m = (1 << N) - 1

    def pack(o):
        v = 0
        for bi, word in enumerate(o):
            v |= (word & m) << (bi * N)
        return v

    base = pack(rnd(state, k, w))
    n = 8 * N
    J = np.zeros((n, n))
    for j in range(n):
        blk, bit = divmod(j, N)
        st2 = list(state)
        st2[blk] ^= (1 << bit)
        d = pack(rnd(st2, k, w)) ^ base
        for i in range(n):
            if (d >> i) & 1:
                J[i, j] = 1.0
    return J


def L_layer(N):
    """The fixed XOR-rotation/shift-register layer as a real 8N x 8N matrix:
    the carry-DROPPED round operator (linround), i.e. a'=h^Sigma1(e)^Sigma0(a),
    e'=d^h^Sigma1(e), and the shift-register wiring b'=a,c'=b,d'=c,f'=e,g'=f,h'=g.
    This is the genuine linear ARX layer; carries are A's job."""
    rows = LR.round_matrix(N, include_ch_maj=False)   # 8N row-bitmasks
    n = 8 * N
    M = np.zeros((n, n))
    for i, rmask in enumerate(rows):
        for j in range(n):
            if (rmask >> j) & 1:
                M[i, j] = 1.0
    return M


def tau(M):
    return float(np.trace(M)) / M.shape[0]


def free_abab(a2, a1, b2, b1):
    """tau(abab) for FREE a,b from marginals: a1=tau(a),a2=tau(a^2), b1,b2 sim."""
    return a2 * b1 * b1 + a1 * a1 * b2 - a1 * a1 * b1 * b1


def main():
    print("=" * 74)
    print("W4-FP3: asymptotic freeness of ARX layers -> tau(ALAL) free-factorizes?")
    print("=" * 74)
    print("  Sharp test: tau((AL)^2) measured vs free prediction from marginals.")
    print("  Free => defect -> 0 as N grows 4->8.  Layers: L=XOR/rot, A=carry-add.\n")

    rng = np.random.default_rng(13)
    results = []
    for N in (4, 6, 8, 10):
        t0 = time.time()
        k = sb.K[40] & ((1 << N) - 1)
        L = L_layer(N)
        # average the freeness defect over several base points (A depends on point)
        defects = []
        comm_norms = []
        for _ in range(6):
            st = [int(rng.integers(0, 1 << N)) for _ in range(8)]
            w = int(rng.integers(0, 1 << N))
            J = local_round_jac(N, st, k, w)
            # A = carry-add layer s.t. J = A.L  ->  A = J . L^{-1}  (L is a GF(2)
            # bijection lifted to R; it is invertible over R here -- verified).
            try:
                Linv = np.linalg.inv(L)
            except np.linalg.LinAlgError:
                Linv = np.linalg.pinv(L)
            A = J @ Linv
            # sanity: A.L == J
            assert np.allclose(A @ L, J, atol=1e-6)
            a1, a2 = tau(A), tau(A @ A)
            b1, b2 = tau(L), tau(L @ L)
            meas = tau(A @ L @ A @ L)
            free = free_abab(a2, a1, b2, b1)
            defect = abs(meas - free) / (abs(meas) + 1e-12)
            defects.append(defect)
            # also: do A and L commute? (interlocking => small commutator unlikely
            # but freeness is about traces, not commuting; report ||[A,L]||/||AL|| )
            comm = A @ L - L @ A
            comm_norms.append(np.linalg.norm(comm) / (np.linalg.norm(A @ L) + 1e-12))
        d_mean = float(np.mean(defects))
        results.append((N, d_mean, float(np.mean(comm_norms))))
        print(f"  N={N:2d}: tau(ALAL) freeness DEFECT = {d_mean:.4f} "
              f"(mean over 6 base pts; spread {min(defects):.3f}-{max(defects):.3f})  "
              f"||[A,L]||/||AL||={np.mean(comm_norms):.3f}  ({time.time()-t0:.1f}s)")

    print("\n[VERDICT INPUTS] freeness defect vs N (should -> 0 if asymptotically free)")
    for N, d, c in results:
        print(f"    N={N:2d}: defect={d:.4f}")
    ds = [d for _, d, _ in results]
    shrinking = all(ds[i + 1] < ds[i] for i in range(len(ds) - 1))
    halved = ds[-1] < 0.5 * ds[0]
    print(f"    monotone shrinking 4->10? {shrinking}    "
          f"defect(N=10) < 0.5*defect(N=4)? {halved}")
    print(f"    defect range across N = [{min(ds):.3f}, {max(ds):.3f}]")

    print("\n[KILL CRITERION] 'deviation doesn't shrink, or mu_AL != mu_L box-times mu_A'")
    fired = (not shrinking) or (not halved) or (min(ds) > 0.10)
    print(f"    deviation fails to shrink to near-0?  -> KILL FIRES = {fired}")
    print("    (free-prob freeness needs the defect collapsing toward 0 with N;")
    print("     a defect stuck at O(0.1-1) means the layers are NOT free -- exactly")
    print("     the card's own skeptic prediction: interlocking bit-lane geometry.)")


if __name__ == '__main__':
    main()
