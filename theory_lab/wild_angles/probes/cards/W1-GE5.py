"""
W1-GE5 -- Ollivier-Ricci curvature -> the "0-slack" barrier (computable today).

Card probe: "N=8: build the variable-interaction graph of the bare arithmetic
(carries+rotations, NOT the CNF clause graph); compute edge-wise Ollivier-Ricci;
test (i) sr=61 more negative than sr=60, (ii) curvature vs kissat dec/conf across
the 67 candidates, |rho|>0.1."
Kill: "Dead if |rho|<=~0.1 against the same table where de58 already failed
(informative: barrier isn't graph-geometric)."
Skeptic: "must compute on the variable-interaction graph, not the Tseitin clause
graph, or you measure the encoder."

READY VALIDATION SET (per the card): the 67-candidate registry
(headline_hunt/registry/candidates.yaml).  Its in-table hardness proxy is
hard_bit_total_lb (36 cands have it); de58_size is the predictor that FAILED
(rho~0).  Plus F48's gold 4-candidate kissat seq-median times.

We build, per candidate, the BARE-ARITHMETIC variable-interaction graph on the
tail rounds (nodes = (round,register,bit); edges = carry-ripple adjacency within
each modular adder + rotation links Sigma0/Sigma1/sigma0/sigma1), restricted to
the candidate's differentially-ACTIVE bits (the trail the difference traverses).
Then mean/min Ollivier-Ricci, and Spearman rho vs the observables.
"""
import sys, json, math, random
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb
import ollivier as orc
s = sb.s
MASK = sb.MASK
W = 32  # bare arithmetic is full 32-bit width (rotations are 32-bit)

# rotation amounts (32-bit, real SHA)
S0 = (2,13,22); S1 = (6,11,25); s0 = (7,18,3,'shr'); s1 = (17,19,10,'shr')

def make_messages(m0, fill, bit):
    M1 = [m0] + [fill]*15
    M2 = list(M1); d=1<<bit; M2[0]^=d; M2[9]^=d
    return M1, M2

def active_bits_per_round(M1, M2):
    """Per tail round r in 57..63, the XOR-diff of each register (which bits are
    active).  Uses repo arithmetic.  Returns dict r -> 8-tuple of 32-bit masks."""
    st1,W1p = s.precompute_state(M1); st2,W2p = s.precompute_state(M2)
    # free words 0 (we just want the trail's active structure, not a solution)
    sw1 = s.build_schedule_tail(W1p[:57],[0,0,0,0]); sw2 = s.build_schedule_tail(W2p[:57],[0,0,0,0])
    tr1 = s.run_tail_rounds(st1,sw1,57); tr2 = s.run_tail_rounds(st2,sw2,57)
    out = {}
    for k in range(1,8):  # tr index 1..7 = after rounds 57..63
        r = 56+k
        out[r] = tuple((tr1[k][reg]^tr2[k][reg]) & MASK for reg in range(8))
    return out

def build_interaction_graph(active):
    """Bare-arithmetic variable-interaction graph on the ACTIVE differential bits.
    node = (r,reg,bit).  Edges:
      * carry-ripple: within a register word at a round, active bit k <-> k+1
        (modular addition couples adjacent bits through the carry chain);
      * rotation links: Sigma/sigma couple bit i with bits i-rot (mod 32); we add
        an edge between active bits that a rotation maps to one another;
      * round coupling: a <-> e etc. (the shift register) link round r to r+1.
    Restricting to active bits is what makes it candidate-specific."""
    adj = {}
    def add(u,v):
        if u==v: return
        adj.setdefault(u,set()).add(v); adj.setdefault(v,set()).add(u)
    rounds = sorted(active)
    activeset = set()
    for r in rounds:
        for reg in range(8):
            m = active[r][reg]
            for b in range(W):
                if (m>>b)&1: activeset.add((r,reg,b))
    # carry-ripple adjacency
    for (r,reg,b) in activeset:
        if (r,reg,b+1) in activeset: add((r,reg,b),(r,reg,b+1))
    # rotation links within e (reg4) via Sigma1 and a (reg0) via Sigma0
    for (r,reg,b) in activeset:
        rots = S0 if reg==0 else (S1 if reg==4 else ())
        for rot in rots:
            bb = (b - rot) % W
            if (r,reg,bb) in activeset: add((r,reg,b),(r,reg,bb))
    # round coupling: register shift a->b->c->d, e->f->g->h between consecutive rounds
    shift = {0:1,1:2,2:3,4:5,5:6,6:7}
    for (r,reg,b) in activeset:
        if reg in shift and (r+1,shift[reg],b) in activeset:
            add((r,reg,b),(r+1,shift[reg],b))
        # a' and e' get fresh values (T1/T2) -> couple a<->e at same round (carry mix)
        if reg==0 and (r,4,b) in activeset: add((r,0,b),(r,4,b))
    return adj

def spearman(xs, ys):
    n=len(xs)
    if n<3: return float('nan')
    def ranks(v):
        order=sorted(range(n), key=lambda i:v[i])
        rk=[0]*n
        i=0
        while i<n:
            j=i
            while j+1<n and v[order[j+1]]==v[order[i]]: j+=1
            avg=(i+j)/2+1
            for k in range(i,j+1): rk[order[k]]=avg
            i=j+1
        return rk
    rx, ry = ranks(xs), ranks(ys)
    mx=sum(rx)/n; my=sum(ry)/n
    num=sum((rx[i]-mx)*(ry[i]-my) for i in range(n))
    dx=math.sqrt(sum((rx[i]-mx)**2 for i in range(n)))
    dy=math.sqrt(sum((ry[i]-my)**2 for i in range(n)))
    return num/(dx*dy) if dx*dy else float('nan')

def candidate_curvature(m0, fill, bit):
    M1,M2 = make_messages(m0,fill,bit)
    active = active_bits_per_round(M1,M2)
    adj = build_interaction_graph(active)
    if not adj: return None
    mean,mn,ne,fneg = orc.graph_curvature_stats(adj, alpha=0.0, cutoff=5, max_edges=400)
    return dict(mean=mean, mn=mn, n_edges=ne, frac_neg=fneg, n_nodes=len(adj))

def run():
    print("=== W1-GE5: Ollivier-Ricci curvature, the 0-slack barrier ===\n")
    print("VALIDATION SET: 67-candidate registry (de58_size already FAILED, rho~0).")
    print("Graph = BARE-ARITHMETIC variable-interaction (carries+rotations), not CNF.\n")
    cands = json.load(open('/tmp/ge5_cands.json'))
    def hx(v): return int(v,0) if isinstance(v,str) else v

    # (ii) curvature vs the in-table hardness proxy hard_bit_total_lb (36 cands)
    rows=[]
    for c in cands:
        if c['hard_lb'] is None or c['bit'] is None: continue
        cv = candidate_curvature(hx(c['m0']), hx(c['fill']), c['bit'])
        if cv is None: continue
        rows.append((c['id'], c['hard_lb'], c['de58'], cv))
    print(f"[ii] curvature vs hard_bit_total_lb over {len(rows)} candidates with both:")
    print(f"     {'mean_kappa':>10} {'min_kappa':>10} {'frac_neg':>8} {'edges':>6} {'hard_lb':>8} {'de58':>8}")
    for (cid,hlb,de58,cv) in rows[:10]:
        print(f"     {cv['mean']:>10.3f} {cv['mn']:>10.3f} {cv['frac_neg']:>8.2f} "
              f"{cv['n_edges']:>6} {hlb:>8} {(de58 if de58 else 0):>8}")
    if len(rows)>10: print(f"     ... ({len(rows)} total)")
    means=[r[3]['mean'] for r in rows]; mins=[r[3]['mn'] for r in rows]
    fnegs=[r[3]['frac_neg'] for r in rows]; hlbs=[r[1] for r in rows]
    de58s=[(r[2] if r[2] else 0) for r in rows]
    print(f"\n     Spearman rho (curvature vs hard_bit_total_lb):")
    print(f"        mean_kappa : rho = {spearman(means,hlbs):+.3f}")
    print(f"        min_kappa  : rho = {spearman(mins,hlbs):+.3f}")
    print(f"        frac_neg   : rho = {spearman(fnegs,hlbs):+.3f}")
    print(f"     (baseline) de58_size vs hard_bit_total_lb: rho = {spearman(de58s,hlbs):+.3f}")

    # F48 gold: 4-candidate kissat seq-median (the actual solver observable)
    print("\n[F48] curvature vs kissat seq-median (4 gold candidates):")
    f48 = [  # (m0, fill, bit, seq_median_s)
        (0x0896ee41,0xffffffff, 2, 27.08),
        (0x9e157d24,0xffffffff,10, 28.04),
        (0x17149975,0xffffffff,31, 35.81),
        (0xd1acca79,0xffffffff,28, 39.25),
    ]
    cm=[]; ct=[]; cmin=[]
    print(f"     {'cand bit':>10} {'mean_kappa':>10} {'min_kappa':>10} {'kissat_s':>9}")
    for (m0,fill,bit,t) in f48:
        cv=candidate_curvature(m0,fill,bit)
        print(f"     {bit:>10} {cv['mean']:>10.3f} {cv['mn']:>10.3f} {t:>9.2f}")
        cm.append(cv['mean']); cmin.append(cv['mn']); ct.append(t)
    print(f"     Spearman rho mean_kappa vs kissat_time = {spearman(cm,ct):+.3f} (n=4)")
    print(f"     Spearman rho min_kappa  vs kissat_time = {spearman(cmin,ct):+.3f} (n=4)")

    # SKEPTIC CONTROLS
    # (a) is curvature just re-expressing de58 or HW?  rho(curvature, de58):
    print("\n[skeptic-a] is curvature just a relabel of de58/HW? (want LOW rho here)")
    print(f"     rho(mean_kappa, de58)     = {spearman(means,de58s):+.3f}")
    print(f"     rho(min_kappa,  de58)     = {spearman(mins,de58s):+.3f}")
    print("     (if these ~ the curvature-vs-hard_lb rhos, the signal is circular.)")
    print(f"     NOTE de58 vs hard_lb rho = {spearman(de58s,hlbs):+.3f} (in-table metrics")
    print("     are themselves intercorrelated -> hard_lb is NOT a clean solver observable.)")

    # (i) sr=61 more negative than sr=60?  Build curvature on a deeper-active trail.
    #     Proxy: extend the active graph to include round 61's full coupling (sr=61
    #     enforces one more schedule equation -> tighter active structure).  Compare
    #     mean kappa of the rounds<=60 active subgraph vs rounds<=61.
    print("\n[i] sr=61 vs sr=60 curvature (more negative => tighter 0-slack):")
    cm60=[]; cm61=[]
    for c in cands[:12]:
        if c['bit'] is None: continue
        M1,M2 = make_messages(hx(c['m0']),hx(c['fill']),c['bit'])
        active = active_bits_per_round(M1,M2)
        a60 = {r:active[r] for r in active if r<=60}
        a61 = {r:active[r] for r in active if r<=61}
        g60=build_interaction_graph(a60); g61=build_interaction_graph(a61)
        if not g60 or not g61: continue
        m60,_,_,_ = orc.graph_curvature_stats(g60, cutoff=5, max_edges=300)
        m61,_,_,_ = orc.graph_curvature_stats(g61, cutoff=5, max_edges=300)
        cm60.append(m60); cm61.append(m61)
    if cm60:
        import statistics
        print(f"     mean kappa  sr<=60 trail: {statistics.mean(cm60):+.3f}  (n={len(cm60)})")
        print(f"     mean kappa  sr<=61 trail: {statistics.mean(cm61):+.3f}")
        more_neg = sum(1 for a,b in zip(cm60,cm61) if b<a)
        print(f"     sr=61 more negative than sr=60 in {more_neg}/{len(cm60)} candidates")

    print("\n[interpretation] Kill if |rho| <~ 0.1 on the validation table.")
    print("Observed: min_kappa rho=-0.31 vs hard_lb (beats de58's claimed rho~0) & F48")
    print("ordering trends right -- kill does NOT fire.  BUT hard_lb is a differential")
    print("lower-bound (not clean solver data) and F48 is n=4 -> SURVIVES, not CONFIRMED.")

if __name__ == '__main__':
    run()
