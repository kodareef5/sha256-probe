#!/usr/bin/env python3
"""
W3-CR2 — The da=0 cascade is a stoichiometric siphon

Card claim: A SIPHON = a species set that, once empty, can never refill (every
producing reaction also consumes one in the set) -- verbatim the cascade's
"da=0 propagates forward as 0." Minimal siphons + moiety conservation laws
(left-nullspace of S) are the invariants the cascade exploits; a *second* siphon
may be the leftover tail-gap.

PROBE (per card): N=4..8 compute moiety laws (Smith normal form / left-nullspace of S)
+ enumerate minimal siphons; does the minimal Delta-a siphon = the da=0 cascade front
bit-for-bit? a second siphon over the tail? conserved-moiety dim vs 132?

KILL: siphons bear no relation to the cascade, OR no nontrivial siphon exists.

GROUND TRUTH (writeups/cascade_structure_complete.md, sr60_sr61_boundary_proof.md):
After precompute (da56=0), the cascade DP forces da=0 every round; with the SHA
shift register (b<-a, c<-b, d<-c, f<-e, g<-f, h<-g) a DIAGONAL zero wave runs:
  r57: da db = 0
  r58: da db dc = 0
  r59: da db dc dd = 0
  r60: da..de = 0  (de60=0 ALWAYS, e-path free)
The a-path zero front {da,db,dc,dd} and the e-path zero front {de,df,dg,dh} are the
two converging waves. The claim: each is a SIPHON of the difference-reaction network.

MODEL
-----
Species = the per-round MODULAR-DIFFERENCE lanes at bit granularity:
   d<lane>_<bit>  for lane in {a,b,c,d,e,f,g,h}, bit in 0..N-1.
A "reaction" is an elementary difference-production gate of ONE round:
  shift-register copies (exact, no carry):  da_i -> db_i ; db_i -> dc_i ; dc_i -> dd_i ;
                                            de_i -> df_i ; df_i -> dg_i ; dg_i -> dh_i
  a-path adder:  da'_i produced from { da_*, db_*, dc_* (Maj/Sigma0 fan-in), de_*,df_*,dg_*
                 (Sigma1/Ch fan-in), dd_* , carry }   (the new head da')
  e-path adder:  de'_i produced from { dd_i (d+T1) , and the T1 fan-in de_*,df_*,dg_* }
We do NOT need carry *magnitudes* for the siphon question -- a siphon is about the
PRODUCTION/CONSUMPTION INCIDENCE (which species appear as reactant vs product of each
reaction), i.e. the bipartite species<->reaction structure. So we build the incidence
exactly from the round's data-flow (who feeds whom), using the genuine masked
Sigma/Ch/Maj fan-in (from lib.sha256 rotation amounts), and ask the pure combinatorial
siphon question.

A SIPHON Z (subset of species): for every reaction R, if (product(R) intersect Z) is
nonempty then (reactant(R) intersect Z) is nonempty.  Minimal siphons are found by
checking support sets; we test the two CANDIDATE cascade fronts directly (a-path,
e-path) and also brute-search minimal siphons at small N to see if the cascade fronts
ARE the minimal ones.

Moiety conservation laws = left-nullspace of the stoichiometric matrix S (here S is the
net difference-stoichiometry; we report dim of left-nullspace and compare to 132).

Throttled, exact integer/rational algebra, N in {4,5,6}. No SAT.
"""
import sys
from fractions import Fraction
from itertools import combinations
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb
s = sb.s

LANES = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']


def rotset(k32, N):
    """scaled rotation amount (>=1), mirroring repo mini-SHA convention."""
    r = int(round(k32 * N / 32.0))
    return r if r >= 1 else 1


def build_round_incidence(N):
    """Return (species_list, reactions) where each reaction is (reactant_set, product_set)
    of species names 'd<lane>_<bit>'. Built from the genuine round data-flow."""
    spec = [f"d{L}_{i}" for L in LANES for i in range(N)]
    sset = set(spec)

    def lane(L, i):
        return f"d{L}_{i % N}"

    rx = []  # (reactant_set, product_set)

    # --- shift-register copy reactions (exact, no carry): old lane -> new lane bit-for-bit
    # new b = old a, new c = old b, new d = old c, new f = old e, new g = old f, new h = old g
    for (src, dst) in [('a', 'b'), ('b', 'c'), ('c', 'd'), ('e', 'f'), ('f', 'g'), ('g', 'h')]:
        for i in range(N):
            rx.append(({lane(src, i)}, {lane(dst, i)}))

    # --- a-path adder: new a (= T1+T2). Fan-in of T1: h, Sigma1(e), Ch(e,f,g), w(=0 diff), K.
    #     Fan-in of T2: Sigma0(a), Maj(a,b,c). Carry couples bits i-1 -> i within the adder.
    S0 = [rotset(k, N) for k in (2, 13, 22)]
    S1 = [rotset(k, N) for k in (6, 11, 25)]
    for i in range(N):
        react = set()
        # Sigma0(a): a rotated by S0 amounts
        for r in S0:
            react.add(lane('a', i + r))   # bit i of Sigma0 reads a at i+r (rotation)
        # Maj(a,b,c) at bit i reads a_i,b_i,c_i
        react |= {lane('a', i), lane('b', i), lane('c', i)}
        # Sigma1(e): e rotated by S1
        for r in S1:
            react.add(lane('e', i + r))
        # Ch(e,f,g) at bit i
        react |= {lane('e', i), lane('f', i), lane('g', i)}
        # h_i
        react.add(lane('h', i))
        # carry into bit i from bit i-1 of the produced head (ripple): reads da'_{i-1}
        if i >= 1:
            react.add(f"da_{i-1}")  # intra-adder carry coupling (the nonlinearity)
        rx.append((react, {lane('a', i)}))

    # --- e-path adder: new e = d + T1. Fan-in: d_i and the T1 fan-in (h,Sigma1(e),Ch(e,f,g)).
    for i in range(N):
        react = {lane('d', i)}
        for r in S1:
            react.add(lane('e', i + r))
        react |= {lane('e', i), lane('f', i), lane('g', i), lane('h', i)}
        if i >= 1:
            react.add(f"de_{i-1}")  # intra-adder carry coupling
        rx.append((react, {lane('e', i)}))

    return spec, rx


def is_siphon(Z, reactions):
    """Z (set of species) is a siphon iff every reaction that PRODUCES a species in Z
    also CONSUMES a species in Z."""
    for (react, prod) in reactions:
        if prod & Z:                # this reaction makes something in Z
            if not (react & Z):     # ...but consumes nothing in Z  -> Z can refill -> NOT a siphon
                return False
    return True


def stoich_matrix(spec, reactions):
    """Net stoichiometric matrix S (species x reactions), entries = #prod - #react.
    Difference species are 0/1 (presence), so multiplicities are 1."""
    idx = {sp: k for k, sp in enumerate(spec)}
    nsp = len(spec)
    cols = []
    for (react, prod) in reactions:
        col = [0] * nsp
        for sp in react:
            col[idx[sp]] -= 1
        for sp in prod:
            col[idx[sp]] += 1
        cols.append(col)
    # S[i][j]
    return [[cols[j][i] for j in range(len(cols))] for i in range(nsp)]


def left_nullspace_dim(S):
    """dim of left-nullspace of S = nsp - rank(S) (rank over rationals)."""
    nsp = len(S)
    return nsp - rank_q(S)


def rank_q(rows):
    if not rows or not rows[0]:
        return 0
    M = [[Fraction(x) for x in r] for r in rows]
    nr = len(M); nc = len(M[0]); pr = 0; rank = 0
    for c in range(nc):
        piv = next((r for r in range(pr, nr) if M[r][c] != 0), None)
        if piv is None:
            continue
        M[pr], M[piv] = M[piv], M[pr]
        pv = M[pr][c]; M[pr] = [x / pv for x in M[pr]]
        for r in range(nr):
            if r != pr and M[r][c] != 0:
                f = M[r][c]; M[r] = [a - f * b for a, b in zip(M[r], M[pr])]
        pr += 1; rank += 1
        if pr == nr:
            break
    return rank


def main():
    print("=" * 76)
    print("W3-CR2: is the da=0 cascade a stoichiometric siphon of the diff-network?")
    print("=" * 76)

    for N in (4, 5, 6):
        spec, rx = build_round_incidence(N)
        print(f"\n--- N={N}: species={len(spec)}  reactions={len(rx)} ---")

        # Candidate cascade fronts (bit-level): a-path front {da,db,dc,dd}, e-path {de,df,dg,dh}.
        a_front = {f"d{L}_{i}" for L in ('a', 'b', 'c', 'd') for i in range(N)}
        e_front = {f"d{L}_{i}" for L in ('e', 'f', 'g', 'h') for i in range(N)}
        full = set(spec)

        print(f"  a-path front {{da,db,dc,dd}} is a siphon?  {is_siphon(a_front, rx)}")
        print(f"  e-path front {{de,df,dg,dh}} is a siphon?  {is_siphon(e_front, rx)}")
        print(f"  full species set is a siphon (trivial)?   {is_siphon(full, rx)}")

        # Per-lane single-lane siphon test (which individual lanes are self-siphons?)
        single = {}
        for L in LANES:
            Z = {f"d{L}_{i}" for i in range(N)}
            single[L] = is_siphon(Z, rx)
        print(f"  single-lane siphons: {[L for L in LANES if single[L]]}")

        # moiety conservation laws
        S = stoich_matrix(spec, rx)
        ln = left_nullspace_dim(S)
        print(f"  moiety conservation-law dim (left-nullspace of S) = {ln}")

        # minimal siphon search at the lane granularity (2^8 lane subsets, cheap)
        lane_species = {L: {f"d{L}_{i}" for i in range(N)} for L in LANES}
        minimal = []
        # enumerate nonempty lane-subsets, smallest first; keep those that are siphons
        siphon_subsets = []
        for k in range(1, len(LANES) + 1):
            for combo in combinations(LANES, k):
                Z = set().union(*[lane_species[L] for L in combo])
                if is_siphon(Z, rx):
                    siphon_subsets.append(frozenset(combo))
        # minimal = not containing a smaller siphon-subset
        minimal = [z for z in siphon_subsets
                   if not any((other < z) for other in siphon_subsets)]
        minimal = sorted(set(minimal), key=lambda z: (len(z), sorted(z)))
        print(f"  minimal lane-siphons: {[sorted(z) for z in minimal]}")

        if N == 6:
            # check: does the a-front decompose into the SHIFT cascade order? Is {a} alone a
            # siphon or does it need its downstream lanes (the diagonal wave)?
            print(f"  is {{a}} alone a siphon (the head)? {is_siphon(lane_species['a'], rx)}")
            print(f"  is {{a,b}} a siphon? {is_siphon(lane_species['a'] | lane_species['b'], rx)}")
            print(f"  is {{a,b,c,d}} (a-path wave) minimal-closed? "
                  f"{is_siphon(set().union(*[lane_species[L] for L in 'abcd']), rx)}")

    print("\n" + "=" * 76)
    print("KILL: siphons bear no relation to the cascade, OR no nontrivial siphon exists.")
    print("=" * 76)


if __name__ == '__main__':
    main()
