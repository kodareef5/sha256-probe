"""
W1-GE1 -- Cech / contextuality obstruction of the per-adder cover.

Card probe: "N=4/5: enumerate each adder's LM-compatible local carry patterns;
build the overlap nerve by shared carry-variable; compute H^0/H^1 over Z/2
(boundary-matrix rank). Predict: collision-N => cocycle is a coboundary;
wall-N => class != 0."
Kill: "Dead if the class is nonzero where collisions provably exist or vanishes
at a no-collision N."
Skeptic: "Cech H^1 of a *tree* nerve is always 0 -- must first verify the
carry-overlap nerve has loops (rotations should create them)."

Two things must hold for the card to live:
  (A) the carry-overlap NERVE has loops (b1 of nerve > 0), else H^1 is 0 trivially;
  (B) the *contextual* class (sheaf of LM-compatible diffs) must be nonzero exactly
      at the no-global-section (wall) regime and zero where a collision exists.

We compute both on the genuine 7-adder tail round at width N (rotations included).
"""
import sys, itertools
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb
import adder_diff as ad

# ----------------------------------------------------------------------------
# 1. Build the adder cover of ONE faithful tail round at width N.
#    Each adder is (inputs : set of variable-ids, output : variable-id, kind).
#    Variables: the N-bit difference WORDS that the adders read/write, PLUS the
#    internal carry chain of each adder (carry bit k shared between bit-k and
#    bit-(k+1) constraints -> path inside an adder).  The NERVE node = adder;
#    nerve edge = adders sharing a variable.  Rotations (Sigma) make an adder's
#    input depend on a rotated copy of a register-difference word => cross-links.
# ----------------------------------------------------------------------------

# Variable ids for the 8 register diffs entering a round: da..dh = 0..7
# plus the schedule-word diff dW = 8.  Adders read these (some rotated).
DA,DB,DC,DD,DE,DF,DG,DH,DW = range(9)

def round_adders():
    """The 7 adders of one round as (name, input_var_set, output_'fresh'_id).
    'reads' lists which register-diff WORDS feed each adder (rotated or not);
    sharing a read variable => nerve overlap.  Output of adder i feeds adder i+1
    in the accumulation chain (h+S1, +Ch, +K, +W, then T2=S0+Maj, a'=T1+T2, e'=d+T1)."""
    # accumulation chain variable ids start at 100 (acc1..); T2 chain at 200.
    ACC1,ACC2,ACC3,T1,T2A,ANEW,ENEW = 100,101,102,103,200,300,301
    A = []
    # adder0: h + Sigma1(e)         reads DH, DE(rot via Sigma1)  -> ACC1
    A.append(("h+S1e", {DH, DE}, ACC1))
    # adder1: ACC1 + Ch(e,f,g)      reads ACC1, DE,DF,DG          -> ACC2
    A.append(("+Ch",   {ACC1, DE, DF, DG}, ACC2))
    # adder2: ACC2 + K (const)      reads ACC2                    -> ACC3
    A.append(("+K",    {ACC2}, ACC3))
    # adder3: ACC3 + W   (=T1)      reads ACC3, DW                -> T1
    A.append(("+W=T1", {ACC3, DW}, T1))
    # adder4: Sigma0(a)+Maj(a,b,c)  reads DA(rot),DA,DB,DC        -> T2
    A.append(("S0+Maj=T2", {DA, DB, DC}, T2A))
    # adder5: T1 + T2  (= a')       reads T1, T2                  -> ANEW
    A.append(("a'=T1+T2", {T1, T2A}, ANEW))
    # adder6: d + T1   (= e')       reads DD, T1                  -> ENEW
    A.append(("e'=d+T1", {DD, T1}, ENEW))
    return A

def build_nerve(adders):
    """Nerve: node per adder; an edge for each shared variable; track which
    variable each edge carries (for cocycle restriction)."""
    n = len(adders)
    edges = {}   # (i,j) -> set of shared vars
    for i in range(n):
        for j in range(i+1, n):
            shared = adders[i][1] & adders[j][1]
            # output->input chaining is also a shared variable
            if adders[i][2] in adders[j][1]:
                shared = shared | {adders[i][2]}
            if adders[j][2] in adders[i][1]:
                shared = shared | {adders[j][2]}
            if shared:
                edges[(i, j)] = shared
    return n, edges

def nerve_b1(n, edges):
    """First Betti number of the 1-skeleton (graph) of the nerve: E - V + C.
    Loops in the nerve are the *necessary condition* for nonzero Cech H^1."""
    E = len(edges)
    # connected components via union-find
    parent = list(range(n))
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    for (i, j) in edges:
        ri, rj = find(i), find(j)
        if ri != rj: parent[ri] = rj
    C = len({find(x) for x in range(n)})
    return E - n + C, E, n, C

# ----------------------------------------------------------------------------
# 2. Contextual (sheaf) class: does a GLOBAL LM-compatible difference assignment
#    exist?  Local sections = per-adder LM-compatible (alpha,beta,gamma).  A
#    global section must agree on shared variables.  We test, for the genuine
#    differential entering the round (kernel diff propagated by repo arithmetic),
#    whether the system of LM constraints across the 7 adders is *jointly*
#    satisfiable when the OUTPUT difference is forced to 0 (collision) vs free.
#    Non-emptiness of the global-section set <=> trivial contextual class.
# ----------------------------------------------------------------------------

def round_diff_propagation(da,db,dc,dd,de,df,dg,dh,dw,N):
    """Propagate input register XOR-diffs through ONE round's 7 adders using the
    repo arithmetic at width N, returning per-adder (alpha,beta,gamma,lmcost) and
    the output register diffs.  Beta of the Sigma/Ch/Maj inputs uses a CONCRETE
    random base point's nonlinear-function diff (XOR-diff of f(x) vs f(x^d))."""
    import random
    m = ad.maskN(N)
    s0r, s1r = ad.sig0_rots(N), ad.sig1_rots(N)
    # pick a concrete base register state to evaluate the nonlinear pieces' diffs
    rng = random.Random(1234 + N)
    a,b,c,d,e,f,g,h = (rng.getrandbits(N) for _ in range(8))
    def Ch_(e,f,g): return (e & f) ^ ((~e & m) & g)
    def Maj_(a,b,c): return (a & b) ^ (a & c) ^ (b & c)
    adders = []
    # adder0: h + Sigma1(e)
    al = dh & m
    be = SigmaN_diff(e, de, s1r, N)
    acc1 = (h + SigmaN(e, s1r, N)) & m
    acc1d = ((h ^ dh) + SigmaN((e ^ de) & m, s1r, N)) & m
    ga = (acc1 ^ acc1d) & m
    adders.append((al, be, ga, ad.lm_cost(al, be, ga, N)))
    # adder1: acc1 + Ch
    al = ga
    be = (Ch_(e,f,g) ^ Ch_((e^de)&m,(f^df)&m,(g^dg)&m)) & m
    acc2 = (acc1 + Ch_(e,f,g)) & m
    acc2d = (acc1d + Ch_((e^de)&m,(f^df)&m,(g^dg)&m)) & m
    ga = (acc2 ^ acc2d) & m
    adders.append((al, be, ga, ad.lm_cost(al, be, ga, N)))
    # adder2: acc2 + K  (K diff = 0; use concrete K)
    K = rng.getrandbits(N)
    al = ga; be = 0
    acc3 = (acc2 + K) & m; acc3d = (acc2d + K) & m
    ga = (acc3 ^ acc3d) & m
    adders.append((al, be, ga, ad.lm_cost(al, be, ga, N)))
    # adder3: acc3 + W (=T1)
    al = ga; be = dw & m
    W = rng.getrandbits(N)
    T1 = (acc3 + W) & m; T1d = (acc3d + ((W ^ dw) & m)) & m
    ga = (T1 ^ T1d) & m
    adders.append((al, be, ga, ad.lm_cost(al, be, ga, N)))
    dT1 = ga
    # adder4: Sigma0(a) + Maj  (=T2)
    al = SigmaN_diff(a, da, s0r, N)
    be = (Maj_(a,b,c) ^ Maj_((a^da)&m,(b^db)&m,(c^dc)&m)) & m
    T2 = (SigmaN(a, s0r, N) + Maj_(a,b,c)) & m
    T2d = (SigmaN((a^da)&m, s0r, N) + Maj_((a^da)&m,(b^db)&m,(c^dc)&m)) & m
    ga = (T2 ^ T2d) & m
    adders.append((al, be, ga, ad.lm_cost(al, be, ga, N)))
    dT2 = ga
    # adder5: T1 + T2 (=a')
    al = dT1; be = dT2
    anew = (T1 + T2) & m; anewd = (T1d + T2d) & m
    da_out = (anew ^ anewd) & m
    adders.append((al, be, da_out, ad.lm_cost(al, be, da_out, N)))
    # adder6: d + T1 (=e')
    al = dd & m; be = dT1
    enew = (d + T1) & m; enewd = ((d ^ dd) + T1d) & m
    de_out = (enew ^ enewd) & m
    adders.append((al, be, de_out, ad.lm_cost(al, be, de_out, N)))
    # output register diffs (shift register): a'=da_out, b'=da, c'=db, d'=dc,
    # e'=de_out, f'=de, g'=df, h'=dg
    out = (da_out, da, db, dc, de_out, de, df, dg)
    return adders, out

def SigmaN(x, rots, N):
    out = 0
    for r in rots:
        out ^= ad.rotN(x, r, N)
    return out & ad.maskN(N)

def SigmaN_diff(x, dx, rots, N):
    m = ad.maskN(N)
    return (SigmaN(x, rots, N) ^ SigmaN((x ^ dx) & m, rots, N)) & m

# ----------------------------------------------------------------------------
def run():
    print("=== W1-GE1: Cech / contextuality of the per-adder cover ===\n")
    adders = round_adders()
    n, edges = build_nerve(adders)
    b1, E, V, C = nerve_b1(n, edges)
    print(f"[A] NERVE of the 7-adder cover (one round):")
    print(f"    vertices(adders)={V}  edges(shared-var)={E}  components={C}")
    print(f"    nerve b1 (loops) = E-V+C = {b1}")
    print(f"    -> {'HAS LOOPS (Cech H^1 can be nonzero)' if b1>0 else 'TREE: Cech H^1 == 0 trivially (skeptic kill)'}\n")

    # [B] contextual class: existence of a global LM-compatible section
    #     for the actual kernel difference, across small N, with output forced
    #     toward collision vs not.  We count, per N, how many input-diff choices
    #     admit a fully-LM-compatible 7-adder propagation (no incompatible adder)
    #     AND drive the round output diff to 0 (a local 'collision' of the round).
    print("[B] Global-section (contextual) test per N:")
    print("     For each N: sweep single-bit kernel diffs on (da..dh,dw); count")
    print("     trails that are LM-compatible at EVERY adder, and whether any")
    print("     reaches output-diff 0 (a round-collision => trivial class).")
    print(f"    {'N':>3} {'trials':>7} {'all-LM-compat':>14} {'round-collisions':>17} {'incompat-adders(min)':>21}")
    for N in (4, 5, 6):
        m = ad.maskN(N)
        trials = all_compat = collisions = 0
        min_incompat = 99
        # sweep: kernel acts on word0 & word9 in the real attack; here on the
        # 9 entering diff slots, single-bit, plus a few 2-bit combos.
        diffsets = []
        for slot in range(9):
            for bit in range(N):
                d = [0]*9; d[slot] = (1 << bit)
                diffsets.append(d)
        # the genuine (0,9)-kernel analogue: same bit on two slots
        for bit in range(N):
            d = [0]*9; d[DA] = (1<<bit); d[DW] = (1<<bit)
            diffsets.append(d)
        for d in diffsets:
            trials += 1
            adders_p, out = round_diff_propagation(*d, N)
            incompat = sum(1 for (_,_,_,c) in adders_p if c < 0)
            min_incompat = min(min_incompat, incompat)
            if incompat == 0:
                all_compat += 1
            if all(o == 0 for o in out):
                collisions += 1
        print(f"    {N:>3} {trials:>7} {all_compat:>14} {collisions:>17} {min_incompat:>21}")

    print("\n[interpretation]")
    print("  nerve b1 decides the skeptic gate; [B] decides the kill_criterion:")
    print("  H^1 must be 0 (global section exists) where a collision exists, and")
    print("  the obstruction nonzero only at no-collision N.  Read verdict from")
    print("  whether min-incompat>0 (no global section) tracks collision absence.")

if __name__ == '__main__':
    run()
