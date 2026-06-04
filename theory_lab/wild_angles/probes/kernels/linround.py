"""
linround.py -- GF(2) XOR-linearized mini-SHA-256 round operator on the 8-word
difference state, parameterized by word width N and the rotation constants.

Reusable across W1-PH2 (RG control-dimension knee), W1-PH3 (carry-coupling matrix),
W1-PH5 (rotation phase sets). READ-ONLY toward the repo: rotation amounts and the
round structure mirror lib.sha256, but here every nonlinear op (modular add, Ch, Maj)
is replaced by its XOR-linear surrogate so the round is an F_2-linear map we can take
ranks of. This is exactly the "XOR-linearize one round" the cards ask for; the carry
nonlinearity is deliberately dropped (and the skeptic notes flag it).

State convention: difference vector d in F_2^(8N), blocks [a,b,c,d,e,f,g,h], each N bits,
bit j of block X at global index off(X)*N + j.

Linear surrogates (standard differential XOR-linearization):
  add(x,y,...)   -> x XOR y XOR ...            (drop carries)
  Ch(e,f,g)      -> (drop; data-dependent) modeled as 0 contribution by default, or as
                    a fixed linear pick -- we use the "transparent" surrogate Ch~ = f XOR g?
                    No: standard linear model treats Ch/Maj differential as worst-case
                    linear; for a CONTROL-DIMENSION probe we want the *deterministic*
                    part, so Ch and Maj contribute 0 (their differential is not linearly
                    forced). This isolates the schedule+rotation+shift skeleton, which is
                    what sets the cascade control structure.
Rotation set: ROTS = (s0a,s0b,s0c, s1a,s1b,s1c) for Sigma0/Sigma1 (big-sigma), scaled.
"""
N_DEFAULT = 8

# SHA-256 big-sigma rotation amounts (Sigma0: 2,13,22 ; Sigma1: 6,11,25), scaled to N.
def scaled_rots(N):
    base = dict(S0=(2,13,22), S1=(6,11,25), s0=(7,18,3), s1=(17,19,10))
    sc = {}
    for k,(a,b,c) in base.items():
        # scale rotation amounts by N/32, round, clamp to [1,N-1] (shifts may be 0..N-1)
        f = lambda x: max(0, min(N-1, round(x * N / 32)))
        sc[k] = (f(a), f(b), f(c))
    return sc

def ror_mat(N, r):
    """N x N GF(2) bit-permutation matrix (as list of row-bitmasks) for ROTR by r."""
    rows = []
    for out_bit in range(N):
        in_bit = (out_bit + r) % N      # (x>>r | x<<(N-r)): out bit i takes in bit (i+r)
        rows.append(1 << in_bit)
    return rows

def shr_mat(N, r):
    rows = []
    for out_bit in range(N):
        in_bit = out_bit + r
        rows.append((1 << in_bit) if in_bit < N else 0)
    return rows

def xor_rows(*mats):
    """XOR several N-row matrices (row-bitmask lists) elementwise."""
    n = len(mats[0])
    return [ (lambda i: __import__('functools').reduce(lambda a,b: a^b, (m[i] for m in mats)))(i) for i in range(n) ]

def _xor(*mats):
    n = len(mats[0]); out=[0]*n
    for m in mats:
        for i in range(n): out[i]^=m[i]
    return out

def Sigma_mat(N, rots):
    """Big-Sigma linear map = ROTR(a)^ROTR(b)^ROTR(c)."""
    a,b,c = rots
    return _xor(ror_mat(N,a), ror_mat(N,b), ror_mat(N,c))

def sigma_small_mat(N, rots):
    """small-sigma = ROTR(a)^ROTR(b)^SHR(c)."""
    a,b,c = rots
    return _xor(ror_mat(N,a), ror_mat(N,b), shr_mat(N,c))

# block offsets in the 8N state
OFF = dict(a=0,b=1,c=2,d=3,e=4,f=5,g=6,h=7)

def block_apply(N, mat, src_block, dst_index, acc):
    """acc is a dict {global_col: rowmask?} -- instead we build the full 8N x 8N matrix
    as list of 8N row-bitmasks; here we splice an N x N linear map from src_block into
    the dst rows. acc rows are length-8N bitmasks. mat rows are length-N bitmasks over
    src_block's N columns."""
    base_src = OFF[src_block]*N
    for j in range(N):
        # dst row dst_index*N + j gets, for each set input bit k in mat[j], column base_src+k
        m = mat[j]
        col = 0
        while m:
            k = (m & -m).bit_length()-1
            acc[dst_index*N + j] ^= (1 << (base_src + k))
            m &= m-1

def round_matrix(N, rots=None, include_ch_maj=False, w_linear=True):
    """Build the 8N x 8N GF(2) matrix of ONE XOR-linearized round acting on the
    difference state (message-word difference set to 0: dW=0 -> homogeneous part).
    Returns rows = list of 8N row-bitmasks (each a length-8N mask).
    Update (SHA-256 round):
      T1 = h + Sigma1(e) + Ch(e,f,g) + K + W      [K const -> 0 diff; W diff added separately]
      T2 = Sigma0(a) + Maj(a,b,c)
      a' = T1+T2 ; b'=a ; c'=b ; d'=c ; e'=d+T1 ; f'=e ; g'=f ; h'=g
    Linear surrogate: '+' -> XOR; Ch,Maj -> 0 (unless include_ch_maj, then linear pick).
    """
    if rots is None:
        r = scaled_rots(N); rots = (r['S0'], r['S1'])
    S0, S1 = rots
    n = 8*N
    rows = [0]*n
    M_S0 = Sigma_mat(N, S0)
    M_S1 = Sigma_mat(N, S1)
    Id   = [1<<j for j in range(N)]
    # T1_lin (on diff) = h XOR Sigma1(e)   (Ch dropped, W diff homogeneous=0, K const)
    # T2_lin           = Sigma0(a)         (Maj dropped)
    # a' = T1 XOR T2 = h XOR Sigma1(e) XOR Sigma0(a)
    block_apply(N, Id,   'h', OFF['a'], rows)
    block_apply(N, M_S1, 'e', OFF['a'], rows)
    block_apply(N, M_S0, 'a', OFF['a'], rows)
    if include_ch_maj:
        # crude linear surrogate: Ch ~ g (when e=1 path) ; Maj ~ c -- only if requested
        block_apply(N, Id, 'g', OFF['a'], rows)
        block_apply(N, Id, 'c', OFF['a'], rows)
    # b' = a ; c' = b ; d' = c
    block_apply(N, Id, 'a', OFF['b'], rows)
    block_apply(N, Id, 'b', OFF['c'], rows)
    block_apply(N, Id, 'c', OFF['d'], rows)
    # e' = d XOR T1 = d XOR h XOR Sigma1(e)
    block_apply(N, Id,   'd', OFF['e'], rows)
    block_apply(N, Id,   'h', OFF['e'], rows)
    block_apply(N, M_S1, 'e', OFF['e'], rows)
    if include_ch_maj:
        block_apply(N, Id, 'g', OFF['e'], rows)
    # f' = e ; g' = f ; h' = g
    block_apply(N, Id, 'e', OFF['f'], rows)
    block_apply(N, Id, 'f', OFF['g'], rows)
    block_apply(N, Id, 'g', OFF['h'], rows)
    return rows

# --- GF(2) matrix helpers operating on (rows = list of bitmasks over n_cols columns) ---
def matmul(A_rows, B_rows, n):
    """(A . B) over GF(2). A_rows, B_rows are n x n bitmask matrices. Returns n x n.
    (A.B)[i] = XOR over k of A[i,k] * B[k]."""
    out = [0]*n
    for i in range(n):
        ai = A_rows[i]; acc = 0
        while ai:
            k = (ai & -ai).bit_length()-1
            acc ^= B_rows[k]
            ai &= ai-1
        out[i] = acc
    return out

def rank_gf2(rows, n):
    rows = [r for r in rows]
    piv = 0
    for col in range(n):
        bit = 1<<col
        sel = next((i for i in range(piv, len(rows)) if rows[i] & bit), None)
        if sel is None: continue
        rows[piv], rows[sel] = rows[sel], rows[piv]
        for i in range(len(rows)):
            if i != piv and (rows[i] & bit):
                rows[i] ^= rows[piv]
        piv += 1
    return piv

def identity_rows(n):
    return [1<<j for j in range(n)]
