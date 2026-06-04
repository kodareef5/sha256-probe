"""
transfer_operator.py — differential / carry transfer operators for the
dynamical-systems sub-block (W1-DY1..DY4) and Batch-C reuse.

READ-ONLY toward sha256_review. Built on top of shabridge (which re-exports the
repo's N-bit-scalable SHA primitives). NOTHING here reimplements a SHA primitive;
we only build *differential* bookkeeping on top of the round function.

----------------------------------------------------------------------
WHAT THIS IS (and the adversarial caveat baked in)
----------------------------------------------------------------------
The object the DY cards want is a weighted Perron-Frobenius / transfer operator on
per-round STATE DIFFERENTIALS:

    L[d', d] = # of (message word w1, carry / second-message realization) configs
               that take incoming differential d to outgoing differential d'
               through ONE N-bit SHA round.

A "state differential" d = (da,db,dc,dd,de,df,dg,dh) is the per-lane MODULAR
difference s2 - s1 mod 2^N  (the repo uses modular, not XOR — see de58 law).

Because the SHA round is a *shift register*, db'=da, dc'=db, dd'=dc, df'=de,
dg'=df, dh'=dg are forced; only da' and de' are produced by the round's two adders.
So a differential's "head" is (da,de) plus the tail it carries. To keep the
operator FINITE and small (the card's whole point — "de58 low-rank says L is
tiny") we model the operator on the **(da,de) head** and brute-count realizations
by sampling the conditioning state + the free message word.

The realization count for a transition is estimated by Monte-Carlo over:
  * a random conditioning interior state (a..h) for path 1,
  * the partner state for path 2 = path1 + incoming differential,
  * all N-bit message words w (path 1) with the partner word w2 = w + msgdiff.
For each we read off the produced (da', de') and tally.

API
---
build_diff_operator(N, in_diffs=None, samples=..., msgdiff_mode=..., seed=0)
    -> (states, L)  where states is the ordered list of (da,de) differential
       heads and L is a dense numpy matrix L[j,i] = weight(state_i -> state_j),
       i.e. column-stochastic-style (apply as L @ v).
spectral_summary(L) -> dict(lambda_max, log2_lambda, gap, n)
build_carry_sft(N, samples=..., seed=0)
    -> (symbols, A) admissible-transition (0/1) adjacency of per-round carry
       symbols (for DY4 + entropy cross-check with DY1).

All heavy loops are pure-python/numpy and meant to run at N<=12 in seconds.
Throttle the *process* (taskpolicy -b, OMP_NUM_THREADS=2) per the playbook.
"""
import sys, os
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb
import numpy as np
import random

s = sb.s
MASKN = lambda N: (1 << N) - 1


# ----------------------------------------------------------------------
# N-bit SHA round primitives (scaled rotations, matching the repo's mini-SHA
# convention used in backward_construct_n10.c — rint(k*N/32), floored at 1).
# We DERIVE these from the repo rotations; we don't invent new constants.
# ----------------------------------------------------------------------
def _scale_rot(k32, N):
    r = int(round(k32 * N / 32.0))
    return r if r >= 1 else 1

def _rot_params(N):
    return dict(
        S0=tuple(_scale_rot(k, N) for k in (2, 13, 22)),
        S1=tuple(_scale_rot(k, N) for k in (6, 11, 25)),
        s0=tuple(_scale_rot(k, N) for k in (7, 18)) + (_scale_rot(3, N),),
        s1=tuple(_scale_rot(k, N) for k in (17, 19)) + (_scale_rot(10, N),),
    )

def _ror(x, k, N):
    k %= N
    m = MASKN(N)
    return ((x >> k) | (x << (N - k))) & m

def _make_round(N):
    rp = _rot_params(N)
    m = MASKN(N)
    S0r = rp['S0']; S1r = rp['S1']
    def S0(a): return _ror(a, S0r[0], N) ^ _ror(a, S0r[1], N) ^ _ror(a, S0r[2], N)
    def S1(e): return _ror(e, S1r[0], N) ^ _ror(e, S1r[1], N) ^ _ror(e, S1r[2], N)
    def Ch(e, f, g): return ((e & f) ^ ((~e & m) & g)) & m
    def Maj(a, b, c): return ((a & b) ^ (a & c) ^ (b & c)) & m

    def rnd(state, k, w):
        a, b, c, d, e, f, g, h = state
        T1 = (h + S1(e) + Ch(e, f, g) + (k & m) + w) & m
        T2 = (S0(a) + Maj(a, b, c)) & m
        return ((T1 + T2) & m, a, b, c, (d + T1) & m, e, f, g)
    return rnd


def _make_vround(N):
    """Vectorized N-bit round: each state lane is a numpy uint64 array.
    Returns rnd(state8_arrays, k_int, w_array) -> tuple of 8 arrays (a..h)."""
    rp = _rot_params(N)
    m = np.uint64(MASKN(N))
    Nn = np.uint64(N)
    def vror(x, k):
        k = np.uint64(k % N)
        if k == 0:
            return x & m
        return ((x >> k) | (x << (Nn - k))) & m
    S0r = [np.uint64(r) for r in rp['S0']]
    S1r = [np.uint64(r) for r in rp['S1']]
    def S0(a): return (vror(a, S0r[0]) ^ vror(a, S0r[1]) ^ vror(a, S0r[2])) & m
    def S1(e): return (vror(e, S1r[0]) ^ vror(e, S1r[1]) ^ vror(e, S1r[2])) & m
    def Ch(e, f, g): return ((e & f) ^ ((~e & m) & g)) & m
    def Maj(a, b, c): return ((a & b) ^ (a & c) ^ (b & c)) & m
    def rnd(state, k, w):
        a, b, c, d, e, f, g, h = state
        kk = np.uint64(k & MASKN(N))
        T1 = (h + S1(e) + Ch(e, f, g) + kk + w) & m
        T2 = (S0(a) + Maj(a, b, c)) & m
        return ((T1 + T2) & m, a, b, c, (d + T1) & m, e, f, g)
    return rnd


def build_diff_operator_fast(N, msgdiff=0, samples=20000, k=None, seed=0,
                             max_heads=400, full_state_diff=0, return_counts=False):
    """Vectorized differential transfer operator on the (da,de) head with the
    message differential FIXED. Same object as build_diff_operator but uses numpy
    to draw `samples` conditioning states at once per head — fast enough for
    N up to ~12 in a few seconds. See build_diff_operator docstring for semantics.
    """
    vrnd = _make_vround(N)
    m = MASKN(N)
    if k is None:
        k = s.K[40] & m
    rng = np.random.default_rng(seed)
    md = msgdiff & m
    fsd = full_state_diff & m

    def rand_states(n):
        return [rng.integers(0, 1 << N, size=n, dtype=np.uint64) for _ in range(8)]

    def step_head(da, de, n_samp):
        st = rand_states(n_samp)
        d = [np.uint64(da), np.uint64(fsd), np.uint64(fsd), np.uint64(fsd),
             np.uint64(de), np.uint64(fsd), np.uint64(fsd), np.uint64(fsd)]
        mm = np.uint64(m)
        st2 = [(st[i] + d[i]) & mm for i in range(8)]
        w = rng.integers(0, 1 << N, size=n_samp, dtype=np.uint64)
        o1 = vrnd(st, k, w)
        o2 = vrnd(st2, k, (w + np.uint64(md)) & mm)
        dap = (o2[0] - o1[0]) & mm
        dep = (o2[4] - o1[4]) & mm
        # pack (da',de') into a single key for counting
        key = (dap.astype(np.uint64) << np.uint64(N)) | dep.astype(np.uint64)
        vals, cnts = np.unique(key, return_counts=True)
        out = {}
        for v, c in zip(vals.tolist(), cnts.tolist()):
            out[(v >> N, v & m)] = c
        return out

    # Phase 1: BFS to find reachable head set (small probe budget).
    seeds = {(0, 0), (1 << (N - 1), 0), (0, 1 << (N - 1))}
    if md:
        seeds.add((md, 0)); seeds.add((0, md))
    reach = set(seeds)
    frontier = list(seeds)
    for _depth in range(10):
        new = set()
        for (da, de) in frontier:
            for h2 in step_head(da, de, max(2000, samples // 4)):
                if h2 not in reach:
                    new.add(h2)
        if not new:
            break
        reach |= new
        frontier = list(new)
        if len(reach) > max_heads:
            # keep only the most-visited? just cap deterministically
            reach = set(sorted(reach)[:max_heads])
            break

    states = sorted(reach)
    idx = {hsd: i for i, hsd in enumerate(states)}
    n = len(states)
    L = np.zeros((n, n), dtype=float)
    counts = np.zeros((n, n), dtype=float)
    for (da, de) in states:
        i = idx[(da, de)]
        tally = step_head(da, de, samples)
        tot = sum(tally.values())
        for h2, c in tally.items():
            j = idx.get(h2)
            if j is not None:
                counts[j, i] = c
                L[j, i] = c / tot
    if return_counts:
        return states, L, counts
    return states, L


# ----------------------------------------------------------------------
# Differential transfer operator on the (da, de) head.
# ----------------------------------------------------------------------
def _enumerate_heads(N, in_diffs):
    """Order the differential 'head' states. By the de-law and shift-register
    structure the recurrent variety of *produced* heads is small; we discover
    it by sampling and union with any caller-provided seeds."""
    if in_diffs is not None:
        base = set(tuple(d) for d in in_diffs)
    else:
        base = set()
    return base


def build_diff_operator(N, msgdiff=0, samples=3000, k=None, seed=0,
                        max_heads=600, return_counts=False, full_state_diff=0):
    """Empirical differential transfer operator on the (da,de) differential head,
    with the MESSAGE DIFFERENTIAL FIXED (msgdiff).

    This is the object the DY1 card actually wants: L[d',d] = (mean over
    conditioning states) of the indicator that ONE N-bit round, applied to a
    pair of states differing by the head d (+ a fixed carried tail differential
    `full_state_diff` on the b,c,d,f,g,h lanes) under a FIXED message difference
    msgdiff, produces outgoing head d'. With msgdiff fixed the realization count
    is over the *carries* (the conditioning state) only — exactly the de58
    'count carry realizations' object, and the reachable head set is SMALL
    (de-law: |produced de| collapses), so L is genuinely low-rank/finite.

    msgdiff=0 models the cascade-pinned interior (paths share the message word,
    the canonical collision-trail regime). A nonzero msgdiff models a kernel
    input difference. The matrix entry is a *probability* in [0,1]; row-sums are
    1 only if all out-heads stay in the tracked set (they do, by the de-law).

    Returns (states, L) with L[j,i] = P(head_i -> head_j). column-stochastic-ish.
    """
    rnd = _make_round(N)
    m = MASKN(N)
    if k is None:
        k = s.K[40] & m  # a mid-schedule round constant (recurrent interior)
    rng = random.Random(seed)
    md = msgdiff & m
    # carried tail differential on (b,c,d,f,g,h); da,de supplied by the head.
    fsd = full_state_diff & m

    def step_head(da, de, n_samp):
        """Tally produced (da',de') over n_samp random conditioning states."""
        tally = {}
        for _c in range(n_samp):
            st = [rng.getrandbits(N) for _ in range(8)]
            d = [da, fsd, fsd, fsd, de, fsd, fsd, fsd]
            st2 = [(st[ii] + d[ii]) & m for ii in range(8)]
            w = rng.getrandbits(N)
            o1 = rnd(st, k, w)
            o2 = rnd(st2, k, (w + md) & m)
            h2 = ((o2[0] - o1[0]) & m, (o2[4] - o1[4]) & m)
            tally[h2] = tally.get(h2, 0) + 1
        return tally

    # Phase 1: discover the reachable head set by forward BFS under fixed msgdiff.
    seeds = {(0, 0), (1 << (N - 1), 0), (0, 1 << (N - 1))}
    if md:
        seeds.add((md, 0)); seeds.add((0, md))
    reach = set(seeds)
    frontier = list(seeds)
    probe_n = max(200, samples // 4)
    for _depth in range(8):
        new = set()
        for (da, de) in frontier:
            for h2 in step_head(da, de, probe_n):
                if h2 not in reach:
                    new.add(h2)
        if not new:
            break
        reach |= new
        frontier = list(new)
        if len(reach) > max_heads:
            break

    states = sorted(reach)
    idx = {hsd: i for i, hsd in enumerate(states)}
    n = len(states)
    L = np.zeros((n, n), dtype=float)
    counts = np.zeros((n, n), dtype=float)

    # Phase 2: estimate transition probabilities (carry realizations / trials).
    for (da, de) in states:
        i = idx[(da, de)]
        tally = step_head(da, de, samples)
        tot = sum(tally.values())
        for h2, c in tally.items():
            j = idx.get(h2)
            if j is not None:
                counts[j, i] = c
                L[j, i] = c / tot
    if return_counts:
        return states, L, counts
    return states, L


def diff_operator_counts(N, msgdiff=0, samples=20000, k=None, seed=0,
                         max_heads=400, full_state_diff=0):
    """RAW-COUNT version of the differential transfer operator: entries are the
    *number* of realizing conditioning states (carries) for head_i -> head_j,
    NOT normalized to a probability. This is literally the card's
    L[d',d] = #(carry/message configs realizing d -> d'). Its Perron eigenvalue
    measures multiplicative growth in the NUMBER of realizations per round.
    Returns (states, C) with C[j,i] = raw count (out of `samples` trials)."""
    states, _, C = build_diff_operator_fast(
        N, msgdiff=msgdiff, samples=samples, k=k, seed=seed,
        max_heads=max_heads, full_state_diff=full_state_diff, return_counts=True)
    return states, C


def spectral_summary(L):
    """Perron eigenvalue + log2 + spectral gap of a (real, nonneg) operator."""
    ev = np.linalg.eigvals(L)
    mag = np.abs(ev)
    order = np.argsort(mag)[::-1]
    mag = mag[order]
    lam = float(mag[0])
    second = float(mag[1]) if len(mag) > 1 else 0.0
    return dict(lambda_max=lam,
                log2_lambda=(float(np.log2(lam)) if lam > 0 else float('-inf')),
                second=second,
                gap=(lam - second),
                n=L.shape[0])


# ----------------------------------------------------------------------
# Differential Jacobian + Lyapunov cocycle (DY3 + Batch-C reuse).
# ----------------------------------------------------------------------
def diff_jacobian(N, k, rng, samples=4000, msgdiff=0):
    """Empirical 2N x 2N differential Jacobian on the (da||de) head.
    A[i,j] = P(output-head bit i flips when input-head bit j is flipped),
    averaged over random conditioning states + message words (msgdiff fixed,
    carried tail differential = 0: the cascade fixed point). Rows/cols 0..N-1 =
    da bits, N..2N-1 = de bits."""
    vrnd = _make_vround(N)
    m = np.uint64(MASKN(N))
    md = np.uint64(msgdiff & MASKN(N))
    n2 = 2 * N
    A = np.zeros((n2, n2), dtype=float)

    def heads_out(da_arr, de_arr, st, w):
        st2 = list(st)
        st2[0] = (st[0] + da_arr) & m
        st2[4] = (st[4] + de_arr) & m
        o1 = vrnd(st, k, w)
        o2 = vrnd(st2, k, (w + md) & m)
        return (o2[0] - o1[0]) & m, (o2[4] - o1[4]) & m

    st = [rng.integers(0, 1 << N, size=samples, dtype=np.uint64) for _ in range(8)]
    w = rng.integers(0, 1 << N, size=samples, dtype=np.uint64)
    zero = np.zeros(samples, dtype=np.uint64)
    base_da, base_de = heads_out(zero, zero, st, w)
    for j in range(n2):
        if j < N:
            da_p, de_p = (zero ^ np.uint64(1 << j)), zero
        else:
            da_p, de_p = zero, (zero ^ np.uint64(1 << (j - N)))
        out_da, out_de = heads_out(da_p, de_p, st, w)
        flip_da = out_da ^ base_da
        flip_de = out_de ^ base_de
        for i in range(N):
            A[i, j] = np.mean(((flip_da >> np.uint64(i)) & np.uint64(1)).astype(float))
            A[N + i, j] = np.mean(((flip_de >> np.uint64(i)) & np.uint64(1)).astype(float))
    return A


def lyapunov_qr(N, R=40, samples=4000, seed=5, msgdiff=0, kfun=None):
    """Numerically-stable Lyapunov spectrum of the differential cocycle via QR
    reorthonormalization each step (avoids the raw-matmul over/underflow). Returns
    sorted-descending chi (bits/round). kfun(r)->round constant; default cycles K."""
    rng = np.random.default_rng(seed)
    n2 = 2 * N
    if kfun is None:
        kfun = lambda r: s.K[(40 + r) % 64] & MASKN(N)
    Q = np.eye(n2)
    logsum = np.zeros(n2)
    for r in range(R):
        A = diff_jacobian(N, kfun(r), rng, samples=samples, msgdiff=msgdiff)
        Z = A @ Q
        Q, Rm = np.linalg.qr(Z)
        d = np.diag(Rm).copy()
        sign = np.sign(d); sign[sign == 0] = 1
        Q = Q * sign
        logsum += np.log2(np.maximum(np.abs(d), 1e-300))
    return np.sort(logsum / R)[::-1]


# ----------------------------------------------------------------------
# Carry subshift (per-round carry symbol SFT) for DY4 + entropy cross-check.
# ----------------------------------------------------------------------
def _carry_symbol(N, st, k, w):
    """The per-round 'carry pattern' symbol: the carry-out bits of the round's
    two modular adders (T1 chain and the d+T1, T1+T2 adds), packed small.
    We summarise by the Hamming weight class of the produced (a,e) low bits and
    the adder carry — a coarse, finite alphabet (so the SFT is small)."""
    rnd = _make_round(N)
    o = rnd(st, k, w)
    # coarse symbol: (popcount(a') parity-ish bucket, popcount(e') bucket)
    return (s.hw(o[0]) % 3, s.hw(o[4]) % 3)


def build_carry_sft(N, samples=20000, k=None, seed=0):
    """Admissible-transition graph of coarse carry symbols across one round.
    Returns (symbols, A) with A[j,i]=1 if symbol_i can be followed by symbol_j."""
    rnd = _make_round(N)
    m = MASKN(N)
    if k is None:
        k = s.K[40] & m
    rng = random.Random(seed)
    seen_edges = set()
    symset = set()
    st = [rng.getrandbits(N) for _ in range(8)]
    prev = _carry_symbol(N, st, k, rng.getrandbits(N))
    symset.add(prev)
    for _ in range(samples):
        w = rng.getrandbits(N)
        st = list(rnd(st, k, w))
        cur = _carry_symbol(N, st, k, rng.getrandbits(N))
        symset.add(cur)
        seen_edges.add((prev, cur))
        prev = cur
    symbols = sorted(symset)
    idx = {sy: i for i, sy in enumerate(symbols)}
    nsym = len(symbols)
    A = np.zeros((nsym, nsym), dtype=float)
    for (pa, cb) in seen_edges:
        A[idx[cb], idx[pa]] = 1.0
    return symbols, A


if __name__ == '__main__':
    import time
    for N in (4, 6, 8):
        t0 = time.time()
        # cascade regime: shared message (msgdiff=0), active differential present
        states, L = build_diff_operator_fast(N, msgdiff=0, samples=20000,
                                             seed=1, max_heads=400)
        info = spectral_summary(L)
        print(f"[selftest] N={N}: heads={len(states)} "
              f"lambda_max={info['lambda_max']:.4f} "
              f"log2={info['log2_lambda']:.4f} gap={info['gap']:.4f} "
              f"({time.time()-t0:.1f}s)")
    syms, A = build_carry_sft(6, samples=5000)
    print(f"[selftest] carry-SFT N=6: symbols={len(syms)} edges={int(A.sum())} "
          f"top_eig={sb.top_eigenvalue(A.tolist())[0]:.4f}")
