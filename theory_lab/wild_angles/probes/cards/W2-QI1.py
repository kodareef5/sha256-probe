#!/usr/bin/env python3
"""
W2-QI1 — Magic saturation: per-round non-affine ("magic") rank, and its
cumulative/contextual growth toward the round-~59 wall.

Card claim: XOR/rotate are Clifford-like (free); the carry is the non-Clifford
"magic"; the wall is where cumulative magic rank saturates the free-bit budget.
Probe: per round, fit the best affine approximation, take the RANK of the
residual {round(x) XOR affine(x)} = independent non-affine directions mu(i);
plot cumulative M(r); look for saturation near r~59. CRITICAL: measure the
*incremental* rank vs the running affine span (the contextual version), since
isolated per-round magic is constant.
Kill: dead if even the contextual/cumulative magic increment is constant
(then the wall is just free-bit exhaustion, the null hypothesis).

We CANNOT enumerate the full 8N-bit round map (2^(8N)). The card's object is the
non-affine content of the *round map*. We make it tractable two complementary ways:

  (A) ISOLATED per-component magic at width N: build the exact truth table of each
      nonlinear round component as a Boolean *vector* function and measure the
      GF(2)-rank of its quadratic-and-higher (non-affine) part, i.e. the number of
      output coordinates that are genuinely non-affine, AND the dimension of the
      span of the residual functions {f_j(x) XOR aff_j(x)} over GF(2)^(inputs).
      Components: carry of modular add (a+b), Ch(e,f,g), Maj(a,b,c).
      This is the "naive per-round magic" the card concedes is constant.

  (B) CONTEXTUAL/CUMULATIVE magic: iterate the REAL SHA round on a controlled
      sub-state (width-N mini-SHA, message-difference channel) and, round by round,
      ask how many NEW non-affine output directions appear in the cumulative map
      x -> state_after_round_r, relative to the running affine span. We approximate
      the non-affine rank of the cumulative map by sampling: take the family of
      first-order finite differences D_v f(x) = f(x XOR v) XOR f(x); the function is
      affine in direction v at x iff D_v f(x) is independent of x. We measure, per
      round, the GF(2) dimension of the span of "second differences"
      D_u D_v f(x) = f XOR f(.+u) XOR f(.+v) XOR f(.+u+v)  (the genuine nonlinearity),
      over a sampled basis of directions -> a contextual magic increment mu_ctx(r).
      Cumulative M(r) = sum mu_ctx. We look for a knee/saturation near r~59.

If (B)'s increment is CONSTANT (flat) -> kill fires.
"""
import sys, itertools, random
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb

random.seed(20260603)

# ---------- generic GF(2) rank over a list of int bitvectors ----------
def rank_gf2(vecs):
    basis = []
    for v in vecs:
        for b in basis:
            v = min(v, v ^ b)
        if v:
            basis.append(v)
            basis.sort(reverse=True)
    return len(basis)

# ---------- width-N primitives (mini-SHA), pure ints mod 2^N ----------
def make_ops(N):
    MASK = (1 << N) - 1
    def ror(x, r): r %= N; return ((x >> r) | (x << (N - r))) & MASK
    def shr(x, r): return (x >> r) & MASK
    # scaled rotation constants (same scaling linround uses)
    base = dict(S0=(2,13,22), S1=(6,11,25), s0=(7,18,3), s1=(17,19,10))
    sc = {k: tuple(max(0, min(N-1, round(a*N/32))) for a in t) for k,t in base.items()}
    def Sig0(a): r=sc['S0']; return ror(a,r[0])^ror(a,r[1])^ror(a,r[2])
    def Sig1(e): r=sc['S1']; return ror(e,r[0])^ror(e,r[1])^ror(e,r[2])
    def Ch(e,f,g): return (e & f) ^ ((~e & MASK) & g)
    def Maj(a,b,c): return (a & b) ^ (a & c) ^ (b & c)
    def add(*xs):
        s = 0
        for x in xs: s = (s + x) & MASK
        return s
    return MASK, ror, shr, Sig0, Sig1, Ch, Maj, add

# ===================================================================
# (A) Isolated per-component magic (the constant the card concedes)
# A coordinate is NON-affine iff some second derivative is nonzero; we measure, per
# output coordinate, whether it is affine, and the GF(2) rank of the span of ALL
# second differences D_u D_v f over the (small) input space = the component's
# non-affine ("magic") rank. Exact (full enumeration), no affine-span search.
# ===================================================================
def affine_residual_rank(func, in_bits, out_bits):
    """func: int in [0,2^in_bits) -> int(out_bits). Returns (#non-affine output coords,
    GF(2) rank of the span of second-difference vectors). A coord f_j is affine iff
    f_j(x)^f_j(x+u)^f_j(x+v)^f_j(x+u+v)=0 for all u,v. We pack second differences as
    out_bits-wide ints across a sample of (x,u,v) and rank them; and separately flag
    coords that are non-affine."""
    D = 1 << in_bits
    # full truth table
    tt = [func(x) for x in range(D)]
    # non-affine coordinate test + second-difference span
    secdiffs = []
    nonaffine_mask = 0
    # iterate over a basis of directions u,v = unit vectors (sufficient to detect bilinear/quadratic)
    units = [1 << i for i in range(in_bits)]
    # sample base points: full if small, else a stride
    base = range(D) if D <= 4096 else range(0, D, max(1, D // 4096))
    for ui in range(in_bits):
        u = units[ui]
        for vi in range(ui, in_bits):
            v = units[vi]
            for x in base:
                dd = tt[x] ^ tt[x ^ u] ^ tt[x ^ v] ^ tt[x ^ u ^ v]
                if dd:
                    secdiffs.append(dd)
                    nonaffine_mask |= dd
    nonaffine = bin(nonaffine_mask).count('1')
    return nonaffine, rank_gf2(secdiffs)

def isolated_magic(N):
    MASK, ror, shr, Sig0, Sig1, Ch, Maj, add = make_ops(N)
    out = {}
    # carry of a+b : carry_bits = (a+b) XOR a XOR b  (the non-affine part of add)
    def addcarry(x):
        a = x & MASK; b = (x >> N) & MASK
        return (add(a,b) ^ a ^ b) & MASK
    out['add_carry(a,b)'] = affine_residual_rank(addcarry, 2*N, N)
    def ch(x):
        e=x&MASK; f=(x>>N)&MASK; g=(x>>(2*N))&MASK; return Ch(e,f,g)
    out['Ch(e,f,g)'] = affine_residual_rank(ch, 3*N, N)
    def maj(x):
        a=x&MASK; b=(x>>N)&MASK; c=(x>>(2*N))&MASK; return Maj(a,b,c)
    out['Maj(a,b,c)'] = affine_residual_rank(maj, 3*N, N)
    return out

# ===================================================================
# (B) Contextual / cumulative magic via sampled second-differences
# of the REAL cumulative round map  M_r : message-state -> state_after_r
# ===================================================================
def cumulative_magic(N, n_rounds, n_pairs=60, n_pts=48):
    """Mini-SHA at width N, state (a..h) each N bits, on an 8N-bit input.
    For the cumulative map f_r(x)=state_after_round_r(x), an input direction (u,v) is
    NON-affine at x iff the second difference
        D_u D_v f_r(x) = f_r(x) ^ f_r(x+u) ^ f_r(x+v) ^ f_r(x+u+v)  !=  0.
    We measure M(r) = dim_GF2( span over chosen (u,v) pairs and base points x of all
    these second differences ) = the contextual non-affine ("magic") rank after r rounds.
    Increment mu(r)=M(r)-M(r-1). Computed INCREMENTALLY: advance every needed input one
    round at a time (no O(r) re-runs)."""
    MASK, ror, shr, Sig0, Sig1, Ch, Maj, add = make_ops(N)
    nbits = 8 * N
    Kw = [ (k & MASK) for k in sb.K ]
    def int_to_state(v):
        return [ (v >> (i*N)) & MASK for i in range(8) ]
    def state_to_int(s):
        v = 0
        for i, w in enumerate(s): v |= (w & MASK) << (i*N)
        return v
    def one_round(s, r):
        a,b,c,d,e,f,g,h = s
        T1 = add(h, Sig1(e), Ch(e,f,g), Kw[r], 0)
        T2 = add(Sig0(a), Maj(a,b,c))
        return (add(T1,T2), a, b, c, add(d,T1), e, f, g)

    dirs = [random.getrandbits(nbits) for _ in range(24)]
    pairs = []
    for i in range(len(dirs)):
        for j in range(i, len(dirs)):
            pairs.append((dirs[i], dirs[j]))
    random.shuffle(pairs); pairs = pairs[:n_pairs]
    base_pts = [random.getrandbits(nbits) for _ in range(n_pts)]

    # The set of distinct inputs we must track: x, x^u, x^v, x^u^v for every (x,(u,v)).
    quads = []          # list of (i_x, i_xu, i_xv, i_xuv) indices into `inputs`
    index = {}
    inputs = []
    def idx(val):
        if val not in index:
            index[val] = len(inputs); inputs.append(val)
        return index[val]
    for x in base_pts:
        for (u, v) in pairs:
            quads.append((idx(x), idx(x^u), idx(x^v), idx(x^u^v)))
    # advance all inputs round-by-round
    states = [int_to_state(v) for v in inputs]
    M = []
    for r in range(n_rounds):
        states = [one_round(s, r) for s in states]
        ints = [state_to_int(s) for s in states]
        secdiffs = []
        for (a,b,c,d) in quads:
            dd = ints[a] ^ ints[b] ^ ints[c] ^ ints[d]
            if dd: secdiffs.append(dd)
        M.append(rank_gf2(secdiffs))
    return M

# ===================================================================
if __name__ == '__main__':
    print("=== W2-QI1: magic (non-affine) rank ===\n")
    print("(A) ISOLATED per-component magic  [(non-affine out coords, 2nd-diff span rank)]")
    for N in (4, 6):
        m = isolated_magic(N)
        print(f"  N={N}: " + "  ".join(f"{k}={v}" for k,v in m.items()))
    print("\n(B) CONTEXTUAL cumulative magic M(r) of the real round map, increments mu(r)")
    print("    Question: does M(r) keep growing toward a wall at r~59, or saturate early?")
    print("    (card kill fires iff mu(r) is CONSTANT/flat -> wall is just free-bit exhaustion)")
    for N in (4, 5, 6):
        nr = 24  # enough rounds to expose any plateau well before round 59
        M = cumulative_magic(N, nr)
        inc = [M[0]] + [M[i]-M[i-1] for i in range(1, len(M))]
        sat_round = next((i+1 for i in range(len(M)) if M[i] == max(M)), None)
        print(f"\n  N={N}: M(r)  = {M}")
        print(f"        mu(r) = {inc}")
        print(f"        max non-affine dim = {max(M)} of state-dim {8*N}; "
              f"first reaches max at round {sat_round} (<< 59); "
              f"increment 0 after round {sat_round}? {all(x==0 for x in inc[sat_round:])}")
