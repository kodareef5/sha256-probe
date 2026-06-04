"""
_w6oc_engine.py — shared Pontryagin / optimal-control engine for the W6-OC* cards.

The W6-OC through-line (CATALOG): the da=0 cascade IS a control law
    x_{r+1} = F_r(x_r, u_r),   x = 8-word state (a..h) mod 2^N,   u_r = schedule word W[r],
steering the DIFFERENCE state to 0 over the tail horizon r=57..63. Pontryagin's
machinery then gives:
    forward trajectory x_r           (the actual cascade collision path)
    finite-diff state Jacobian  J_r = d x_{r+1} / d x_r        (8N x 8N bit-matrix)
    control column              B_r = d x_{r+1} / d u_r        (8N x N  bit-matrix)
    backward costate            lam_r = J_r^T lam_{r+1},  lam_63 = target
    switching function          s_r = lam_{r+1}^T B_r          (Hamiltonian dH/du)

THIS HELPER builds exactly those objects, at width N, reusing the EXACT-carry N-bit
mini-SHA tail from _w5co_engine (which is itself a faithful port of the repo's
backward_construct_n10.c). Every Jacobian is a *Boolean* finite difference at the
trajectory point: flip one input bit, see which output bits flip. That is the honest
GF(2) linearization the cards ask for; the mod-2^N carry kinks make it the local
(per-trajectory-point) tangent map, with the set-valued caveat flagged.

CRITICAL FRAMING (prior finding #4): the round map F_r = sha_round is *identical* for
every r. So J_r and B_r are structurally the same map at every round; the ONLY thing
that changes at r>=61 is that u_r (= W[r]) is no longer a FREE control — it is fixed by
the schedule recurrence. Any "dies at 61 / column drops at 61" is that bookkeeping, not
a property of the round. The engine therefore exposes BOTH:
    B_r^free  — the control column treating W[r] as a free 32-bit input (same every r)
    feasible_dofs(r) — how many independent control DOF the SCHEDULE actually grants
                       at round r (4 free words W57..60; 0 thereafter).

READ-ONLY toward the repo. Throttle callers with shabridge.run_throttled / taskpolicy.
"""
import sys
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/cards')
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import _w5co_engine as eng          # exact N-bit tail (sha_round, find_M0, find_w2, ...)
import shabridge as sb              # noqa: F401  (ground truth pins)

ROUNDS = list(range(57, 64))        # tail rounds 57..63 (round index = K index)
OFF = dict(a=0, b=1, c=2, d=3, e=4, f=5, g=6, h=7)
REG = ('a', 'b', 'c', 'd', 'e', 'f', 'g', 'h')


# --------------------------------------------------------------------------- #
#  pack / unpack 8-word state  <->  8N-bit vector (block X bit j at OFF[X]*N+j)
# --------------------------------------------------------------------------- #
def pack(state, N):
    out = 0
    for k, w in enumerate(state):
        out |= (w & ((1 << N) - 1)) << (N * k)
    return out

def setbits(x):
    """iterate set-bit positions of int x (low to high)."""
    while x:
        b = (x & -x).bit_length() - 1
        yield b
        x &= x - 1


# --------------------------------------------------------------------------- #
#  Boolean finite-diff Jacobians at a trajectory point  (mod-2^N, carries IN)
# --------------------------------------------------------------------------- #
def state_jacobian(state, k, w, M):
    """J = d F_r / d x_r  as an 8N x 8N GF(2) matrix (rows = output bits, list of
    8N-bit column-masks). Boolean tangent at (state, w): flip input bit i, XOR the
    output, every set output bit gets column i. F_r = sha_round (exact carries)."""
    N = M['N']; n = 8 * N
    base = pack(eng.sha_round(state, k, w, M), N)
    cols = [0] * n                         # cols[i] = output-bits-flipped-by-input-i mask
    for blk in range(8):
        s_list = list(state)
        for j in range(N):
            i = blk * N + j
            s2 = list(s_list); s2[blk] ^= (1 << j)
            cols[i] = pack(eng.sha_round(tuple(s2), k, w, M), N) ^ base
    # transpose to row form: rows[o] has bit i set iff input i flips output o
    rows = [0] * n
    for i in range(n):
        for o in setbits(cols[i]):
            rows[o] |= (1 << i)
    return rows                            # 8N rows, each an 8N-bit input-mask

def control_column(state, k, w, M):
    """B = d F_r / d u_r  as an 8N x N matrix (rows = output bits, list of N-bit
    masks). Treats the schedule word w as a FREE N-bit control. Same map every round."""
    N = M['N']; n = 8 * N
    base = pack(eng.sha_round(state, k, w, M), N)
    cols = [0] * N
    for j in range(N):
        cols[j] = pack(eng.sha_round(state, k, w ^ (1 << j), M), N) ^ base
    rows = [0] * n
    for j in range(N):
        for o in setbits(cols[j]):
            rows[o] |= (1 << j)
    return rows                            # 8N rows, each an N-bit control-mask


# --------------------------------------------------------------------------- #
#  GF(2) linear algebra on row-mask matrices
# --------------------------------------------------------------------------- #
def rank(rows):
    rows = [r for r in rows if r]
    piv = 0; ncol = max((r.bit_length() for r in rows), default=0)
    rows = list(rows)
    for col in range(ncol):
        bit = 1 << col
        sel = next((i for i in range(piv, len(rows)) if rows[i] & bit), None)
        if sel is None:
            continue
        rows[piv], rows[sel] = rows[sel], rows[piv]
        for i in range(len(rows)):
            if i != piv and (rows[i] & bit):
                rows[i] ^= rows[piv]
        piv += 1
    return piv

def transpose(rows, ncol):
    """transpose a matrix given as row-masks with `ncol` columns -> ncol rows."""
    out = [0] * ncol
    for r, m in enumerate(rows):
        for c in setbits(m):
            out[c] |= (1 << r)
    return out

def matT_vec(rows, ncol, vec_mask):
    """compute A^T . v over GF(2). rows: A as nrow row-masks (ncol cols); vec_mask:
    nrow-bit vector. Returns ncol-bit vector (A^T v)[c] = XOR_r A[r,c] v[r]."""
    res = 0
    for r in setbits(vec_mask):
        res ^= rows[r]                     # row r contributes its column-mask
    return res                             # ncol-bit

def mat_mat_T(A_rows, B_rows):
    """(A^T B) implemented columnwise is overkill; we only need rank/columns, so
    return the list of columns of (A^T B): column c = A^T (B[:,c]). Inputs are row-mask
    matrices with the SAME number of rows (8N). Returns list over B-columns of masks."""
    # transpose B to get its columns, then apply A^T to each.
    raise NotImplementedError  # not needed; cards use matT_vec / explicit builds


# --------------------------------------------------------------------------- #
#  Forward trajectory of the ACTUAL cascade collision  (path-1 states + controls)
# --------------------------------------------------------------------------- #
_MODEL_CACHE = {}

def get_model(N):
    """Cache (model, MSB-kernel setup) per N — find_M0 sweeps 2^N candidates, so we
    do it once. The cascade trajectory only varies the FREE words, not the kernel."""
    if N not in _MODEL_CACHE:
        M = eng.make_model(N)
        _MODEL_CACHE[N] = (M, eng.find_M0(M))
    return _MODEL_CACHE[N]


def cascade_trajectory(N, w57, w58, w59, w60):
    """Replay path-1 of the da=0 cascade with the given free words. Returns:
        states[r]  for r in 57..63 : the 8-word state of path-1 AT THE START of round r
                                     (states[57] = state after round 56, i.e. before r57)
        controls   = the 7 schedule words W[57..63] actually used by path-1
        model M, setup (collision-eligible MSB-kernel pair).
    Mirrors _w5co_engine.run_tail but keeps the per-round states for path-1."""
    M, setup = get_model(N)
    W1p = setup['W1']; s1 = setup['st1']; KN = M['KN']; MASK = M['MASK']
    s0 = M['s0']; s1f = M['s1']

    states = {57: s1}
    # free words 57..60
    s1 = eng.sha_round(s1, KN[57], w57, M); states[58] = s1
    s1 = eng.sha_round(s1, KN[58], w58, M); states[59] = s1
    s1 = eng.sha_round(s1, KN[59], w59, M); states[60] = s1
    s1 = eng.sha_round(s1, KN[60], w60, M); states[61] = s1
    # schedule-fixed words 61..63 (path-1)
    W1_61 = (s1f(w59) + W1p[54] + s0(W1p[46]) + W1p[45]) & MASK
    W1_62 = (s1f(w60) + W1p[55] + s0(W1p[47]) + W1p[46]) & MASK
    s1 = eng.sha_round(s1, KN[61], W1_61, M); states[62] = s1
    s1 = eng.sha_round(s1, KN[62], W1_62, M); states[63] = s1
    W1_63 = (s1f(W1_61) + W1p[56] + s0(W1p[48]) + W1p[47]) & MASK
    s1 = eng.sha_round(s1, KN[63], W1_63, M)               # state after r63 (states[64])
    states[64] = s1
    controls = {57: w57, 58: w58, 59: w59, 60: w60, 61: W1_61, 62: W1_62, 63: W1_63}
    return states, controls, M, setup


def feasible_dofs(r):
    """How many INDEPENDENT free control DOF the message schedule grants at round r.
    W[57..60] are the 4 free tail words (1 DOF each); W[61..63] are pinned by the
    schedule recurrence => 0 DOF. This is the schedule bookkeeping, identical for
    every kernel; the round FUNCTION is the same at every r."""
    return 1 if 57 <= r <= 60 else 0


# --------------------------------------------------------------------------- #
#  Backward costate sweep along a trajectory.  lam_64 = target (8N-bit vector or
#  identity set of basis vectors).  Returns dict r -> lam_r and switching weights.
# --------------------------------------------------------------------------- #
def costate_sweep(N, w57, w58, w59, w60, target='Iout'):
    """Propagate lam_r = J_r^T lam_{r+1} backward over the tail. With target='Iout' we
    carry the FULL 8N-dim costate basis (the identity at r=64), so lam_r is itself an
    8N x 8N matrix (its rank = dim of output directions still first-order reachable from
    state x_r). Returns:
        states, controls, M
        Jrows[r], Brows[r] : the per-round state-Jacobian / free-control column
        Lam[r]             : costate matrix at round r (row-mask list, 8N cols), r=57..64
        srank[r]           : rank of the switching map  s_r = lam_{r+1}^T B_r
                             (how many control directions have nonzero Hamiltonian grad).
    """
    states, controls, M, setup = cascade_trajectory(N, w57, w58, w59, w60)
    n = 8 * N
    Jrows = {}; Brows = {}
    for r in ROUNDS:
        Jrows[r] = state_jacobian(states[r], M['KN'][r], controls[r], M)
        Brows[r] = control_column(states[r], M['KN'][r], controls[r], M)
    # backward costate, full identity basis at r=64
    Lam = {64: [1 << i for i in range(n)]}        # identity (each basis costate)
    srank = {}
    for r in reversed(ROUNDS):                      # 63,62,...,57
        Lnext = Lam[r + 1]                          # 8N x 8N (rows = basis costates)
        Jr = Jrows[r]                               # 8N x 8N, rows=out bits, cols=in bits
        # lam_r = J_r^T lam_{r+1}: for each basis costate (row p of Lnext, an 8N out-mask)
        # apply J_r^T => sum of J_r columns selected by that out-mask. J_r^T v has
        # entry i = XOR_o J[o,i] v[o] = (XOR of rows o in v) -> exactly matT_vec.
        Lr = [matT_vec(Jr, n, Lnext[p]) for p in range(n)]
        Lam[r] = Lr
        # switching map s_r = lam_{r+1}^T B_r : columns = control bits, rows = costate
        # directions. col j = (B_r[:,j]) pulled back by lam_{r+1}; its rank tells how
        # many control directions move the (still-live) costate.
        Bcols = transpose(Brows[r], N)             # N rows, each an 8N out-mask (col j)
        s_cols = [matT_vec_rowmask(Lnext, Bcols[j]) for j in range(N)]
        srank[r] = rank(s_cols)
    return dict(states=states, controls=controls, M=M, setup=setup,
                Jrows=Jrows, Brows=Brows, Lam=Lam, srank=srank, n=n)


def matT_vec_rowmask(Lrows, out_mask):
    """L is 8N x 8N (rows = costate basis index, cols = output bit). out_mask is an
    8N-bit output vector (a column of B). Return the 8N-bit vector whose entry p =
    XOR_o L[p,o] out_mask[o] = does costate basis p see this control column. = for each
    output bit set in out_mask, XOR column o of L; but L is row-mask form so column o is
    gathered. Equivalent: result bit p set iff popcount(Lrows[p] & out_mask) is odd."""
    res = 0
    for p in range(len(Lrows)):
        if bin(Lrows[p] & out_mask).count('1') & 1:
            res |= (1 << p)
    return res


if __name__ == '__main__':
    import time
    for N in (5, 8):
        t0 = time.time()
        D = costate_sweep(N, 0, 0, 0, 0)
        n = D['n']
        print(f"[selftest] N={N}  ({n}-dim state)  in {time.time()-t0:.2f}s")
        print(f"   round | rank J_r | free-ctrl rank B_r | switch-rank s_r | sched DOF")
        for r in ROUNDS:
            print(f"   {r:5d} | {rank(D['Jrows'][r]):8d} | {rank(D['Brows'][r]):17d} |"
                  f" {D['srank'][r]:15d} | {feasible_dofs(r):9d}")
