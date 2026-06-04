#!/usr/bin/env python3
"""
W2-QI4 — Stabilizer rank chi -> branch count of any case-splitting search saturates
at the wall.

Card claim: the minimum affine-piece cover of each round (its stabilizer rank chi)
counts carry case-split branches; Sum log2 chi_i explodes near round 59.
Probe (N=2..8): per round build the truth table, compute the minimum affine cover chi_i
(greedy set-cover over affine subfunctions); track Sum log2 chi_i; measure chi of the
*cumulative* map (where ranks multiply); does it grow SUPER-LINEARLY toward the budget
near 59? cross-plot vs QI1's mu(i).
Kill: dead if chi_i is O(1) and round-independent even for the cumulative map (merely
linear growth, no saturation).

chi(f) here = number of pieces in a GREEDY affine-piece cover of f on its (small) domain:
scan domain points; a new point joins an existing piece iff f stays consistent with that
piece's fitted affine map on ALL its points so far, else opens a new piece. This is the
card's "greedy set-cover over affine subfunctions". We compute:
  (A) chi of the ISOLATED round components (carry of add, Ch, Maj) at width N -> the
      per-round chi the card concedes is constant.
  (B) chi of the CUMULATIVE compression map x -> state_after_round_r, on a small input
      subspace, and Sum log2 chi(r). The decisive test (finding #4): is the growth
      super-linear with a knee near r~59, or smooth/saturating well before?
"""
import sys, random, itertools
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb

random.seed(20260603)

def make_ops(N):
    MASK = (1 << N) - 1
    def ror(x,r): r%=N; return ((x>>r)|(x<<(N-r)))&MASK
    def shr(x,r): return (x>>r)&MASK
    base = dict(S0=(2,13,22), S1=(6,11,25), s0=(7,18,3), s1=(17,19,10))
    sc = {k: tuple(max(0,min(N-1,round(a*N/32))) for a in t) for k,t in base.items()}
    def Sig0(a): r=sc['S0']; return ror(a,r[0])^ror(a,r[1])^ror(a,r[2])
    def Sig1(e): r=sc['S1']; return ror(e,r[0])^ror(e,r[1])^ror(e,r[2])
    def Ch(e,f,g): return (e&f)^((~e&MASK)&g)
    def Maj(a,b,c): return (a&b)^(a&c)^(b&c)
    def add(*xs):
        s=0
        for x in xs: s=(s+x)&MASK
        return s
    return MASK, Sig0, Sig1, Ch, Maj, add

# ---- GF(2) affine-consistency test for a piece ------------------------------
def affine_fits(points, vals, in_bits, out_bits):
    """Is there a single GF(2)-affine map A x + c agreeing with all (point,val) pairs?
    Solve the linear system over GF(2): for each output coord j, find coefficients
    (a_0..a_{in-1}, const) s.t. for every point p, XOR_i a_i p_i  XOR const = val_j(p).
    Feasible iff each coord's system is consistent. We test consistency by Gaussian
    elimination on the augmented rows [p_0..p_{in-1}, 1 | val_j]."""
    if len(points) <= 1:
        return True
    for j in range(out_bits):
        rows = []
        for p, val in zip(points, vals):
            row = 0
            for i in range(in_bits):
                if (p >> i) & 1: row |= (1 << i)
            row |= (1 << in_bits)            # constant term column
            if (val >> j) & 1: row |= (1 << (in_bits+1))  # rhs as top bit
            rows.append(row)
        # gaussian elim over columns 0..in_bits (coeffs+const); rhs at bit in_bits+1
        ncoef = in_bits + 1
        piv_rows = []
        for col in range(ncoef):
            bit = 1 << col
            sel = next((r for r in rows if (r & bit) and not any(r is pr for pr in piv_rows)), None)
            # simpler: standard elimination
        # do a clean elimination
        rr = [r for r in rows]
        pr = 0
        rhsbit = 1 << (in_bits+1)
        for col in range(ncoef):
            bit = 1 << col
            sel = None
            for i in range(pr, len(rr)):
                if rr[i] & bit: sel = i; break
            if sel is None: continue
            rr[pr], rr[sel] = rr[sel], rr[pr]
            for i in range(len(rr)):
                if i != pr and (rr[i] & bit):
                    rr[i] ^= rr[pr]
            pr += 1
        # inconsistent iff some row has 0 in all coeff cols but 1 in rhs
        coefmask = (1 << ncoef) - 1
        for r in rr:
            if (r & coefmask) == 0 and (r & rhsbit):
                return False
    return True

def chi_greedy(func, in_bits, out_bits, domain=None):
    """Greedy affine-piece cover count. domain = iterable of input ints (default full)."""
    if domain is None:
        domain = range(1 << in_bits)
    pts = list(domain)
    # shuffle for a fairer greedy (deterministic seed)
    rnd = random.Random(7)
    rnd.shuffle(pts)
    pieces = []  # each: (list_points, list_vals)
    for x in pts:
        v = func(x)
        placed = False
        for (P, V) in pieces:
            if affine_fits(P + [x], V + [v], in_bits, out_bits):
                P.append(x); V.append(v); placed = True; break
        if not placed:
            pieces.append(([x], [v]))
    return len(pieces)

def isolated_chi(N):
    MASK, Sig0, Sig1, Ch, Maj, add = make_ops(N)
    out = {}
    out['add_carry(a,b)'] = chi_greedy(lambda x: (add(x&MASK,(x>>N)&MASK)^(x&MASK)^((x>>N)&MASK))&MASK, 2*N, N)
    out['Ch(e,f,g)'] = chi_greedy(lambda x: Ch(x&MASK,(x>>N)&MASK,(x>>2*N)&MASK), 3*N, N)
    out['Maj(a,b,c)'] = chi_greedy(lambda x: Maj(x&MASK,(x>>N)&MASK,(x>>2*N)&MASK), 3*N, N)
    return out

def cumulative_chi(N, n_rounds, in_dim=None):
    """chi of x -> state_after_round_r on a small input subspace. We vary `in_dim`
    input bits (the low bits of register a's input, plus a few others) holding the rest
    fixed, enumerate that subspace, and advance round-by-round (incrementally caching
    states). Returns list chi(r)."""
    MASK, Sig0, Sig1, Ch, Maj, add = make_ops(N)
    Kw = [k & MASK for k in sb.K]
    if in_dim is None: in_dim = min(2*N, 12)
    nbits = 8*N
    # input subspace: vary the lowest in_dim bits of the packed 8N-bit state, fixed base
    base_state = random.getrandbits(nbits)
    def int_to_state(v):
        return [ (v>>(i*N))&MASK for i in range(8) ]
    def one_round(s, r):
        a,b,c,d,e,f,g,h = s
        T1 = add(h, Sig1(e), Ch(e,f,g), Kw[r], 0)
        T2 = add(Sig0(a), Maj(a,b,c))
        return (add(T1,T2), a, b, c, add(d,T1), e, f, g)
    domain = list(range(1 << in_dim))
    inputs = [ (base_state & ~((1<<in_dim)-1)) | m for m in domain ]
    states = [int_to_state(v) for v in inputs]
    chis = []
    for r in range(n_rounds):
        states = [one_round(s, r) for s in states]
        # pack output state to int for affine test
        def pack(s):
            v=0
            for i,w in enumerate(s): v |= (w&MASK)<<(i*N)
            return v
        outs = [pack(s) for s in states]
        # chi of the map domain-index -> outs, with input = the m bits (in_dim wide)
        func = lambda m, outs=outs: outs[m]
        chi = chi_greedy(func, in_dim, nbits, domain=domain)
        chis.append(chi)
    return chis

if __name__ == '__main__':
    print("=== W2-QI4: stabilizer rank chi (affine-piece cover) ===\n")
    print("(A) ISOLATED per-round component chi (greedy affine-piece cover)")
    for N in (2, 3, 4):
        c = isolated_chi(N)
        print(f"  N={N}: " + "  ".join(f"{k}={v}" for k,v in c.items()))
    print("\n(B) CUMULATIVE map chi(r) and Sum log2 chi(r) -- does it explode near r~59?")
    print("    (kill fires iff chi(r) is O(1)/round-independent -> no super-linear growth)")
    import math
    for N in (3, 4):
        nr = 24
        chis = cumulative_chi(N, nr, in_dim=min(2*N,10))
        cumlog = []
        acc = 0.0
        for c in chis:
            acc += math.log2(max(c,1)); cumlog.append(round(acc,2))
        print(f"\n  N={N}: chi(r)        = {chis}")
        print(f"        Sum log2 chi  = {cumlog}")
        # super-linear? compare growth in first half vs second half of rounds
        sat = next((i+1 for i in range(len(chis)) if chis[i]==max(chis)), None)
        print(f"        max chi={max(chis)} (domain size {1<<min(2*N,10)}); first reaches max at round {sat} (<<59); "
              f"chi flat after? {len(set(chis[sat:]))<=1}")
