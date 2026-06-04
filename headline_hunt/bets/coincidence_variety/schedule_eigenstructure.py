#!/usr/bin/env python3
"""
schedule_eigenstructure.py — invariant-subspace structure of the SHA-256 message
schedule, as a 512-bit GF(2) linear map (carry-free / XOR approximation).

Idea under test: the 2^-2N sr-step tax comes from M1,M2 satisfying each schedule
equation INDEPENDENTLY. A difference Δ in a SMALL S-invariant subspace stays
structured through the schedule, potentially correlating the two messages'
conditions (collapsing 2^-2N -> 2^-N). This needs small invariant subspaces to
exist. We compute the minimal-polynomial / Krylov structure of the one-step
schedule advance map S on the 16-word (512-bit) state.

S: [W_{t-16},...,W_{t-1}] -> [W_{t-15},...,W_t], with
   W_t = sigma1(W_{t-2}) ^ W_{t-7} ^ sigma0(W_{t-15}) ^ W_{t-16}   (GF(2), XOR).
"""
import numpy as np

N = 32

def rot_mat(r):
    M = np.zeros((N, N), dtype=np.uint8)
    for j in range(N):
        M[(j - r) % N, j] = 1   # output bit (j-r) gets input bit j  (ROTR by r)
    return M

def shr_mat(s):
    M = np.zeros((N, N), dtype=np.uint8)
    for j in range(N):
        if j - s >= 0:
            M[j - s, j] = 1
    return M

def sig0_mat():  # ROTR7 ^ ROTR18 ^ SHR3
    return (rot_mat(7) ^ rot_mat(18) ^ shr_mat(3))
def sig1_mat():  # ROTR17 ^ ROTR19 ^ SHR10
    return (rot_mat(17) ^ rot_mat(19) ^ shr_mat(10))

def build_S():
    """512x512 GF(2) one-step schedule advance."""
    s0, s1 = sig0_mat(), sig1_mat()
    DIM = 16 * N
    S = np.zeros((DIM, DIM), dtype=np.uint8)
    # state layout: block i (i=0..15) holds word W_{t-16+i}; bits [i*N:(i+1)*N].
    # after step: new block i = old block i+1 (i=0..14); new block 15 = W_t.
    for i in range(15):
        S[i*N:(i+1)*N, (i+1)*N:(i+2)*N] = np.eye(N, dtype=np.uint8)
    # W_t = sigma1(W_{t-2}) ^ W_{t-7} ^ sigma0(W_{t-15}) ^ W_{t-16}
    # W_{t-2}=block14, W_{t-7}=block9, W_{t-15}=block1, W_{t-16}=block0
    last = slice(15*N, 16*N)
    S[last, 14*N:15*N] ^= s1
    S[last,  9*N:10*N] ^= np.eye(N, dtype=np.uint8)
    S[last,  1*N: 2*N] ^= s0
    S[last,  0*N: 1*N] ^= np.eye(N, dtype=np.uint8)
    return S

def gf2_rank(M):
    A = M.copy() % 2; rows, cols = A.shape; r = 0
    for c in range(cols):
        piv = -1
        for i in range(r, rows):
            if A[i, c]: piv = i; break
        if piv < 0: continue
        A[[r, piv]] = A[[piv, r]]
        for i in range(rows):
            if i != r and A[i, c]: A[i] ^= A[r]
        r += 1
        if r == rows: break
    return r

def krylov_dim(S, v, maxd):
    """dim of span{v, Sv, S^2 v, ...} over GF(2) — the smallest S-invariant
    subspace containing v."""
    DIM = S.shape[0]
    basis = []          # list of pivoted rows
    cur = v.copy() % 2
    vecs = []
    for _ in range(maxd + 1):
        vecs.append(cur.copy())
        cur = (S @ cur) % 2
    M = np.array(vecs, dtype=np.uint8)   # (maxd+1) x DIM
    return gf2_rank(M)

def matpow_order_estimate(S, cap=2000):
    """smallest k<=cap with S^k = I (multiplicative order), else >cap."""
    DIM = S.shape[0]
    I = np.eye(DIM, dtype=np.uint8)
    P = S.copy() % 2
    for k in range(1, cap + 1):
        if np.array_equal(P, I): return k
        P = (P @ S) % 2
    return None

if __name__ == "__main__":
    S = build_S()
    DIM = S.shape[0]
    print(f"schedule advance map S: {DIM}x{DIM} over GF(2)")
    print(f"rank(S) = {gf2_rank(S)} / {DIM}  (full rank => invertible recurrence)")

    # Krylov dimension = degree of the minimal polynomial of v under S.
    # Small Krylov dim for some structured v => small invariant subspace.
    def word_vec(active_words, pattern):
        v = np.zeros(DIM, dtype=np.uint8)
        for w in active_words:
            for b in range(N):
                if (pattern >> b) & 1: v[w*N + b] = 1
        return v

    tests = {
        "MSB kernel (W0,W9 bit31)": word_vec([0, 9], 1 << (N-1)),
        "single bit W0[0]":         word_vec([0], 1),
        "single bit W0[31]":        word_vec([0], 1 << (N-1)),
        "all-ones W0":              word_vec([0], 0xffffffff),
        "random A":                 (np.random.RandomState(1).randint(0,2,DIM).astype(np.uint8)),
        "random B":                 (np.random.RandomState(2).randint(0,2,DIM).astype(np.uint8)),
    }
    print("\nKrylov dim (smallest S-invariant subspace containing v); DIM=512:")
    print(f"  {'vector':32s} krylov_dim")
    maxk = 0
    for name, v in tests.items():
        d = krylov_dim(S, v, DIM)
        maxk = max(maxk, d)
        print(f"  {name:32s} {d}")
    print(f"\nmax Krylov dim seen = {maxk}")
    print("Interpretation: if random vectors give krylov_dim = 512, the minimal")
    print("polynomial has degree 512 (S is CYCLIC) — invariant subspaces only come")
    print("from char-poly factor structure. If structured vectors give SMALL krylov")
    print("dim, those are exploitable invariant differences. Equal-to-512 everywhere")
    print("=> no small invariant subspace => the eigenstructure idea has no substrate.")
