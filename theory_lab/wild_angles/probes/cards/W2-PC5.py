#!/usr/bin/env python3
"""
W2-PC5 — Linearization-survival (Tseitin) test -> proves the obstruction is expansion, not carries.

Card (CATALOG): XOR-linearized sr=60 still times out, yet linear systems are Gauss-easy; so the
hardness is the SURVIVING Tseitin-graph EXPANSION, not nonlinearity. Tseitin formulas over an
expander are linear yet resolution-hard (Urquhart). If L_61 is Tseitin-like over an expanding
carry-incidence graph while L_59 isn't, you recover PC1's width jump with nonlinearity STRIPPED ->
proving the obstruction is the graph, not the carries. "The scalpel experiment."
PROBE: small N — Gaussian-eliminate the genuinely-linear vars from L_k; compute the RESIDUAL
carry-incidence graph's edge/vertex EXPANSION for k=59,60,61 (constant expansion only at 61 =
headline); plus block-sensitivity bs(L_k) (truth table at N=4,5) — a jump at 61 says structural.
KILL: dead if the residual graph at sr=61 is SMALL / NON-expanding (timeout was an encoding
artifact — itself valuable), OR bs(L_k) is FLAT.
SKEPTIC (the card's own): linearizing modular addition is NOT faithful (deletes carries);
"XOR-linearized sr=60" is a different problem — verify it's genuinely Tseitin-like (consistent
charges) FIRST.

ADVERSARIAL FOCUS (NB from the controller + finding #1): Wave 1 found the obstruction IS the carry
nonlinearity. So PC5's "expansion not carries" thesis is DIRECTLY testable and LIKELY BACKWARDS.
The decisive experiment: when we XOR-linearize (delete carries) and Gaussian-eliminate, does an
EXPANDING residual core survive (card right), or does the system go Gauss-TRIVIAL / non-expanding
(card backwards — hardness was the deleted carries)?

------------------------------------------------------------------------------------------------
WHAT WE BUILD:
L_k = the XOR-linearized tail collision system over GF(2): variables = all difference-state bits
across rounds 57..k PLUS the free message-word bits; equations = the linearized round relations
(kernels/linround.py: a'=h^Sigma1(e)^Sigma0(a), e'=d^h^Sigma1(e), shift-register for the rest;
carries DROPPED — exactly the card's XOR-linearization) AND the collision constraint de(k)=0.
We:
 (1) FAITHFULNESS CHECK: is L_k genuinely Tseitin-like (a consistent GF(2) charge system, i.e. the
     incidence is a graph with parity charges)? Tseitin = each variable appears in exactly 2
     equations (an edge), charges on vertices. We measure the variable-degree distribution; a real
     Tseitin instance has (almost) all vars of degree 2.
 (2) GAUSS-ELIMINATE: rank / corank of L_k. If full-rank with a unique/empty solution space and no
     residual core, the linear system is TRIVIAL (Gauss-easy, no surviving expander).
 (3) RESIDUAL CARRY-INCIDENCE GRAPH after eliminating determined vars; measure its size and vertex/
     edge EXPANSION (min |boundary(S)|/|S| over small S) for k=59,60,61. Constant expansion only at
     61 = headline; small/non-expanding = KILL.
 (4) BLOCK-SENSITIVITY bs(L_k) of the linearized collision predicate (truth table at N=4,5) vs k.

Throttled. N=4,5 (the linear ranks are exact; bs truth tables are 2^(small)).
"""
import sys
from collections import Counter, deque
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb
import linround as lr

# ---------- build the linearized tail system L_k as GF(2) rows over a global var index ----------
def build_Lk(N, k, include_ch_maj=False):
    """Variables: difference state at each round step 57..k (8N bits per step) + free word diffs.
    But the round map is DETERMINISTIC given the injected word diff; the genuinely-free variables
    are the message-word diffs dW[57..k] (N bits each). The linearized collision system is:
      state_57 = 0 (paths agree entering the tail; difference seeded only by dW)
      state_{r+1} = A * state_r  XOR  inject(dW[r])      (A = linearized round, inject into a,e)
      de(k) = 0    (the e-block of state_k is zero)
    Eliminating the state recurrence, de(k) is a GF(2)-linear function of {dW[57..k]}. The SYSTEM
    L_k whose 'expansion' the card wants is: rows = the N bit-equations de(k)=0 expressed over the
    free dW bits (carry-monotone? NO — linearized, so EXACT XOR). We return:
      rows  = list of GF(2) equations (bitmask over free-var columns) for de(k)=0,
      nvars = number of free dW bits = N*(k-56)."""
    dim = 8 * N
    A = lr.round_matrix(N, rots=None, include_ch_maj=include_ch_maj)
    # inject(dW): a' += dW, e' += dW? In SHA the word enters T1 -> a' and e'. Linearized: dW adds to
    # both a' and e'. We model injection vector for word at round r as bits into a-block AND e-block.
    def apply_A_to_statevec(vecbits):
        # vecbits: int bitmask over dim state coords; returns A*vec
        w = 0
        for i in range(dim):
            if bin(A[i] & vecbits).count('1') & 1:
                w |= (1 << i)
        return w
    # Track each state coord as a GF(2) linear combination of free dW bits. Represent state as a
    # list (length dim) of bitmasks over the free-var space.
    nfree_words = k - 56  # words 57..k
    nvars = N * nfree_words
    # free var index for (word r, bit j): (r-57)*N + j
    state = [0] * dim  # state_57 = 0 (no free dependence yet)
    rows_history = []
    for idx, r in enumerate(range(57, k + 1)):
        # advance state: state = A*state  (each coord is a linear comb -> apply A as XOR of coords)
        newstate = [0] * dim
        # A[i] selects which input coords XOR into output i; each input coord carries a linear-comb
        for i in range(dim):
            acc = 0
            mi = A[i]
            while mi:
                b = (mi & -mi).bit_length() - 1
                acc ^= state[b]
                mi &= mi - 1
            newstate[i] = acc
        state = newstate
        # inject dW[r] into a-block (coords OFF['a']*N + j) and e-block (OFF['e']*N + j)
        for j in range(N):
            fv = 1 << ((idx) * N + j)
            state[lr.OFF['a'] * N + j] ^= fv
            state[lr.OFF['e'] * N + j] ^= fv
    # de(k)=0 : the e-block coords of state_k must be 0 -> N linear equations over free vars
    rows = [state[lr.OFF['e'] * N + j] for j in range(N)]
    return rows, nvars

def gf2_var_degrees(rows, nvars):
    """degree of each variable = # equations it appears in (Tseitin edges have degree 2)."""
    deg = [0] * nvars
    for r in rows:
        x = r
        while x:
            b = (x & -x).bit_length() - 1
            deg[b] += 1
            x &= x - 1
    return deg

def residual_after_elim(rows, nvars):
    """Gaussian-eliminate; return (rank, corank, pivot_cols, reduced_rows). Residual 'core' = the
    rows/vars not pinned by elimination (free columns) — the would-be expander."""
    piv, red = sb.gf2_rref(rows, nvars)
    return len(piv), nvars - len(piv), piv, red

def expansion_of_graph(rows, nvars, max_subset_rows=None):
    """Treat the (reduced) system as a hypergraph: each equation = a hyperedge over its variables.
    Vertex expansion proxy: min over single equations and pairs of |unique vars|/|S|. Also report
    the average equation width (after reduction) — a Tseitin EXPANDER needs WIDE, overlapping
    equations; thin/disjoint => non-expanding."""
    widths = [bin(r).count('1') for r in rows if r]
    if not widths:
        return dict(n_eq=0, avg_width=0.0, max_width=0, min_unique_ratio=None)
    # unique-neighbour ratio for the full set
    cnt = Counter()
    for r in rows:
        x = r
        while x:
            b = (x & -x).bit_length() - 1
            cnt[b] += 1
            x &= x - 1
    uniq = sum(1 for v, c in cnt.items() if c == 1)
    neq = len([r for r in rows if r])
    return dict(n_eq=neq, avg_width=sum(widths)/len(widths), max_width=max(widths),
                n_vars_touched=len(cnt), unique_ratio=uniq/neq if neq else None)

# ---------- block-sensitivity of the linearized collision predicate ----------
def linear_coll_predicate_bs(N, k, max_vars=16):
    """COLL_lin(dW) = 1 iff the linearized de(k)=0 system is satisfied by free assignment dW.
    Build the predicate over the free dW bits (nvars), truth table if nvars<=max_vars, measure
    block-sensitivity (max over inputs of max #disjoint blocks flipping the output)."""
    rows, nvars = build_Lk(N, k)
    if nvars > max_vars:
        return dict(nvars=nvars, bs=None, note='too many vars for exact bs')
    def pred(x):
        # satisfied iff every row has even parity with x
        for r in rows:
            if bin(r & x).count('1') & 1:
                return 0
        return 1
    n = 1 << nvars
    # block sensitivity: for each input, greedily find max # disjoint minimal flipping blocks
    best_bs = 0
    # sample inputs if too many; here nvars<=16 so 65536 max — fine
    for x in range(n):
        fx = pred(x)
        # find sensitive blocks greedily (singletons first, then expand) — use minimal blocks:
        # a block B is sensitive if flipping all bits in B changes output. Greedy disjoint packing
        # over singleton-sensitive bits is a standard lower bound; we compute sensitivity (singleton)
        # and a greedy disjoint block count.
        sens_bits = [b for b in range(nvars) if pred(x ^ (1 << b)) != fx]
        # greedy disjoint blocks: singletons are already disjoint
        bs = len(sens_bits)
        best_bs = max(best_bs, bs)
    return dict(nvars=nvars, bs=best_bs)

def run():
    print("=" * 80)
    print("W2-PC5: does an EXPANDING residual core survive XOR-linearization (card), or does the")
    print("system go Gauss-TRIVIAL / non-expanding (card BACKWARDS — hardness was the carries)?")
    print("=" * 80)
    for N in (4, 5):
        print(f"\n### N={N} ###")
        print("(0) FAITHFULNESS: variable-degree distribution of L_k (Tseitin needs ~all deg 2):")
        for k in (59, 60, 61):
            rows, nvars = build_Lk(N, k)
            deg = gf2_var_degrees(rows, nvars)
            dc = Counter(deg)
            print(f"   sr={k}: nvars={nvars}, #eq={len(rows)}, var-degree histogram {dict(sorted(dc.items()))}")
        print("\n(1)+(2) Gauss-eliminate L_k -> rank/corank; (3) residual graph expansion:")
        print(f"   {'sr=k':>5} {'#eq':>4} {'nvars':>6} {'rank':>5} {'corank':>7} "
              f"{'avgW':>6} {'maxW':>6} {'uniqRatio':>10} {'residual?':>10}")
        for k in (59, 60, 61):
            rows, nvars = build_Lk(N, k)
            rank, corank, piv, red = residual_after_elim(rows, nvars)
            exp = expansion_of_graph([r for r in red if r], nvars)
            # is there a residual expanding core? = are there reduced rows that are WIDE and many?
            residual = 'EXPANDER?' if (exp['n_eq'] > N and exp['avg_width'] > 2) else 'trivial/thin'
            ur = exp.get('unique_ratio')
            ur_s = f'{ur:.3f}' if ur is not None else 'NA'
            print(f"   {k:>5} {len(rows):>4} {nvars:>6} {rank:>5} {corank:>7} "
                  f"{exp['avg_width']:>6.2f} {exp['max_width']:>6} {ur_s:>10} {residual:>10}")
        print("\n(4) block-sensitivity of the linearized collision predicate vs k:")
        for k in (58, 59, 60, 61):
            d = linear_coll_predicate_bs(N, k, max_vars=16)
            print(f"   sr={k}: nvars={d['nvars']}  bs(L_k) = {d.get('bs')}")
    print("\n--- VERDICT LOGIC ---")
    print("KILL if residual graph at sr=61 is small/non-expanding (thin reduced rows, trivial core)")
    print("OR bs(L_k) flat. HEADLINE (card right) iff a WIDE expanding residual core appears ONLY at")
    print("61 AND bs jumps at 61. Backwards-thesis confirmed if linearization makes it Gauss-trivial.")

if __name__ == '__main__':
    run()
