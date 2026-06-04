#!/usr/bin/env python3
"""
W3-CR1 — Difference-CRN deficiency -> derives 2^-2N as delta=2

Card claim: Model one round on a difference-pair as a Chemical Reaction Network
(species = difference bits, reactions = XOR-flip / carry-birth gates); a collision =
the all-zero-difference steady state. Feinberg deficiency  delta = n - l - s
(n = #complexes, l = #linkage classes, s = rank of stoichiometric matrix). Conjecture:
delta = 2 at sr-active rounds (== the two conditions g1,h) -> 2^-2N = "2 codim x N bits";
delta jumps to 3 at round 61.

PROBE (per card): N=3,4,5 build the difference-CRN from masked Ch/Maj/Sigma/add, assemble
the stoichiometric matrix, compute delta; does delta(sr-active)=2 and delta(61)=3, tracking
-log2(rate)/N?

KILL: delta constant/zero across rounds, OR unrelated to 2^-2N.

ADVERSARIAL FRAME (per orchestrator prior #1, #3): the real per-round-cost structure is
TWO independent N-bit conditions (g1=0 AND h=0; verified g2=g1+h exactly on 946 N=10
collisions). So the bar is not "does some integer come out 2" — it is "is the deficiency
LITERALLY 2 = the two conditions, AND does it move to 3 exactly at the sr=61 round while
being 2 at sr-active rounds, AND does it track the measured -log2(rate)/N?". A coincidental
2 that does not move across rounds, or that does not equal the codimension, is a KILL.

METHOD
------
The SHA round, as a difference-update map on the modular per-lane differences, is built from
two modular adders (T1 = h + Sigma1(e) + Ch(e,f,g) + K + w ; T2 = Sigma0(a) + Maj(a,b,c) ;
a' = T1+T2 ; e' = d+T1). To get a *reaction network* whose species are difference bits and
whose reactions are the elementary gates, we model the canonical collision regime (msgdiff=0,
the cascade-pinned interior) where a single active modular difference propagates through the
adder carry chain. The elementary "reactions" are the per-bit carry-propagation rules of a
ripple adder acting on a difference:

  species  : per-bit difference indicators d_0..d_{N-1} (lane head), plus carry indicators
             c_1..c_{N-1} (the carry-birth species). all-zero = the collision steady state.
  reactions: for each bit i, the modular-add difference rule couples (d_i, c_i) -> (out_i, c_{i+1}).
             A "carry-birth" reaction creates c_{i+1} from a difference at bit i; an XOR-flip
             reaction toggles out_i. These are EXACTLY the gates the cascade/gap analysis uses.

We assemble the stoichiometric matrix S (rows = species, cols = reactions, entries =
product - reactant multiplicity), then compute:
  s     = rank(S)                          (over the rationals)
  n     = number of distinct complexes (reactant+product vertices)
  l     = number of linkage classes (connected comps of the reaction graph on complexes)
  delta = n - l - s
We compute delta for the round-core network (the recurrent sr-active round) and for the
"round-61" network (the extra inter-message-compatibility reaction h added: the second
condition that only switches on at the sr boundary). We then compare delta to the measured
codimension 2 and to -log2(rate)/N (== 2, from the 2^-2N law).

Throttled, pure-python rational linear algebra, N in {3,4,5}. No SAT.
"""
import sys
from fractions import Fraction
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb
s = sb.s


# ---------------------------------------------------------------------------
# rational matrix rank (exact, no numpy float fuzz)
# ---------------------------------------------------------------------------
def rank_q(rows):
    if not rows:
        return 0
    M = [[Fraction(x) for x in r] for r in rows]
    nr = len(M); nc = len(M[0])
    rank = 0
    pr = 0
    for c in range(nc):
        piv = next((r for r in range(pr, nr) if M[r][c] != 0), None)
        if piv is None:
            continue
        M[pr], M[piv] = M[piv], M[pr]
        pivval = M[pr][c]
        M[pr] = [x / pivval for x in M[pr]]
        for r in range(nr):
            if r != pr and M[r][c] != 0:
                f = M[r][c]
                M[r] = [a - f * b for a, b in zip(M[r], M[pr])]
        pr += 1
        rank += 1
        if pr == nr:
            break
    return rank


# ---------------------------------------------------------------------------
# Build the difference-CRN for the modular-add carry chain at width N.
# Species: d_0..d_{N-1} (lane diff bits), c_1..c_{N-1} (carry-birth species).
# Reactions are the elementary carry-propagation gates of the ripple adder
# acting on a single active modular difference (the cascade regime).
# A reaction is (reactant_complex -> product_complex), each complex a multiset
# of species. We return (species_index, reactions=[(reactant_dict, product_dict)]).
# ---------------------------------------------------------------------------
def build_diff_crn(N, round61=False):
    # species ordering
    spec = []
    for i in range(N):
        spec.append(('d', i))
    for i in range(1, N):
        spec.append(('c', i))
    sidx = {sp: k for k, sp in enumerate(spec)}

    reactions = []  # list of (reactant_dict, product_dict) over species names

    # carry-birth / propagation gates of the ripple adder on a difference:
    # at bit i, a difference d_i together with an incoming carry c_i can
    #   (R1) consume d_i and emit carry c_{i+1}      (carry-birth)
    #   (R2) flip the output bit out_i (= d_i toggles)  -- the XOR-flip gate
    # We encode the modular-add difference update s2-s1: a set bit at position i
    # propagates to i+1 via carry. This is the genuine nonlinearity (carries).
    for i in range(N):
        d_i = ('d', i)
        c_in = ('c', i) if i >= 1 else None
        c_out = ('c', i + 1) if i + 1 <= N - 1 else None
        # carry-birth reaction: d_i (+ c_i) -> c_{i+1}   (difference moves up the chain)
        react = {d_i: 1}
        if c_in is not None:
            react[c_in] = 1
        prod = {}
        if c_out is not None:
            prod[c_out] = 1
        else:
            # top bit: carry leaves the modular window (absorbed) -> empty complex (0)
            prod = {}
        reactions.append((react, prod))
        # XOR-flip gate: c_i -> d_i (carry lands as a difference bit at i)  -- reversible-ish
        if c_in is not None:
            reactions.append(({c_in: 1}, {d_i: 1}))

    if round61:
        # The sr=61 round switches on a SECOND, independent condition (inter-message
        # compatibility h, distinct from the per-message schedule match g1). Model it as
        # an extra, structurally INDEPENDENT reaction acting on a fresh species 'hbit'
        # that must also drain to zero. This adds one complex in a NEW linkage class.
        spec.append(('h', 0))
        sidx = {sp: k for k, sp in enumerate(spec)}
        hbit = ('h', 0)
        # h-drain reaction: hbit -> 0  (its own independent zeroing condition)
        reactions.append(({hbit: 1}, {}))

    return spec, sidx, reactions


def stoich_and_complexes(spec, sidx, reactions):
    nsp = len(spec)
    S = []  # one row per species, one col per reaction
    # build per-reaction net stoichiometry columns first
    cols = []
    complexes = []  # list of frozenset-able tuples for reactant & product complexes
    # graph edges between complexes (for linkage classes)
    cplx_index = {}

    def cplx_key(d):
        return tuple(sorted((sidx[k], v) for k, v in d.items()))

    edges = []
    for (react, prod) in reactions:
        rk = cplx_key(react)
        pk = cplx_key(prod)
        for k in (rk, pk):
            if k not in cplx_index:
                cplx_index[k] = len(cplx_index)
                complexes.append(k)
        edges.append((cplx_index[rk], cplx_index[pk]))
        col = [0] * nsp
        for k, v in react.items():
            col[sidx[k]] -= v
        for k, v in prod.items():
            col[sidx[k]] += v
        cols.append(col)
    # S rows
    for r in range(nsp):
        S.append([cols[c][r] for c in range(len(cols))])

    # linkage classes: connected components of the complex graph (undirected)
    nc = len(complexes)
    parent = list(range(nc))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        parent[find(a)] = find(b)
    for (a, b) in edges:
        union(a, b)
    roots = set(find(x) for x in range(nc))
    n_linkage = len(roots)
    return S, nc, n_linkage


def deficiency(spec, sidx, reactions):
    S, n_complexes, n_linkage = stoich_and_complexes(spec, sidx, reactions)
    rank_s = rank_q(S)
    delta = n_complexes - n_linkage - rank_s
    return dict(n=n_complexes, l=n_linkage, s=rank_s, delta=delta)


def main():
    print("=" * 74)
    print("W3-CR1: difference-CRN deficiency delta = n - l - s, per round, vs N")
    print("=" * 74)
    print("\nGround truth: per enforced sr round costs 2^-2N == TWO independent N-bit")
    print("conditions (g1=0 AND h=0). -log2(rate)/N = 2. codim = 2.\n")

    print(f"{'N':>3} | {'sr-active: n':>12} {'l':>3} {'s':>4} {'delta':>6} || "
          f"{'round61: n':>11} {'l':>3} {'s':>4} {'delta':>6}")
    print("-" * 74)
    results = {}
    for N in (3, 4, 5):
        sp0, ix0, rx0 = build_diff_crn(N, round61=False)
        d0 = deficiency(sp0, ix0, rx0)
        sp1, ix1, rx1 = build_diff_crn(N, round61=True)
        d1 = deficiency(sp1, ix1, rx1)
        results[N] = (d0, d1)
        print(f"{N:>3} | {d0['n']:>12} {d0['l']:>3} {d0['s']:>4} {d0['delta']:>6} || "
              f"{d1['n']:>11} {d1['l']:>3} {d1['s']:>4} {d1['delta']:>6}")

    print("\n--- adversarial readout ---")
    deltas_active = [results[N][0]['delta'] for N in (3, 4, 5)]
    deltas_61 = [results[N][1]['delta'] for N in (3, 4, 5)]
    print(f"delta(sr-active) over N=3,4,5 : {deltas_active}")
    print(f"delta(round61)   over N=3,4,5 : {deltas_61}")
    print(f"target (the two conditions / codim / -log2 rate per N) : 2 -> 3")
    const_active = len(set(deltas_active)) == 1
    is_two = all(d == 2 for d in deltas_active)
    jumps_to_three = all(d == 3 for d in deltas_61)
    print(f"\ndelta(sr-active) constant across N?  {const_active}  (value set {set(deltas_active)})")
    print(f"delta(sr-active) == 2 (the two conditions)?  {is_two}")
    print(f"delta jumps to 3 at round 61?  {jumps_to_three}")
    print(f"delta zero anywhere? {0 in deltas_active or 0 in deltas_61}")

    # ---- encoding-robustness: does delta depend on arbitrary reaction choices? ----
    # The card fixes "species=diff bits, reactions=XOR-flip/carry-birth gates" but the
    # exact reaction set is a modeling choice. To make the KILL robust (not an artifact
    # of one encoding), recompute delta under three reasonable variants at N=4:
    #   V0 = baseline (carry-birth + xor-flip)
    #   V1 = + reverse carry reactions (reversible adder)         -> changes l, s
    #   V2 = + full bimolecular product complexes (d_i + c_i -> d_i' + c_{i+1})
    print("\n--- encoding robustness (N=4): delta under reaction-set variants ---")

    def crn_variant(N, variant):
        sp = [('d', i) for i in range(N)] + [('c', i) for i in range(1, N)]
        ix = {s_: k for k, s_ in enumerate(sp)}
        rx = []
        for i in range(N):
            d_i = ('d', i); c_in = ('c', i) if i >= 1 else None
            c_out = ('c', i + 1) if i + 1 <= N - 1 else None
            react = {d_i: 1}
            if c_in is not None:
                react[c_in] = 1
            prod = {c_out: 1} if c_out is not None else {}
            if variant == 2 and c_out is not None:
                # full bimolecular: keep d_i' on product side too (XOR survivor)
                prod = {c_out: 1, d_i: 1}
            rx.append((react, prod))
            if c_in is not None:
                rx.append(({c_in: 1}, {d_i: 1}))
                if variant == 1:
                    rx.append(({d_i: 1}, {c_in: 1}))  # reverse
        return sp, ix, rx

    for v in (0, 1, 2):
        sp, ix, rx = crn_variant(4, v)
        d = deficiency(sp, ix, rx)
        print(f"   variant {v}: n={d['n']} l={d['l']} s={d['s']} delta={d['delta']}")

    print("\nKILL test: delta constant/zero across rounds OR unrelated to 2^-2N.")
    if all(d == 0 for d in deltas_active):
        verdict = "KILLED (delta==0: network is deficiency-zero, encodes no codim-2)"
    elif deltas_active == deltas_61:
        verdict = "KILLED (delta does NOT move sr-active->61; cannot be the switching condition)"
    elif is_two and jumps_to_three:
        verdict = "candidate-CONFIRMED pending skeptic (delta=2->3 matches two-conditions)"
    else:
        verdict = "see reasoning (delta nonzero & moves, but value != codim-2 target)"
    print("PRELIM VERDICT:", verdict)


if __name__ == '__main__':
    main()
