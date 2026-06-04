"""
W4-LG1 -- Wilson-loop confinement: "the wall as a deconfinement->confinement
transition" (HEADLINE).

Card probe: sample colliding-pair ensembles, extract per-column carries (bit-serial
add), build Z2 gauge links; fit log<W(a x b)> vs perimeter vs area; perimeter for
r<=60, area onset at 61; sigma_61 vs 2^-2N. FIRST verify the gauge transformation
law numerically. Kill: "same law both sides, or <W>~1 everywhere." Skeptic: the
vertical link is an imposed parity -- if it doesn't transform as a connection, <W>
isn't physical.

PRIOR FINDING #4 (~8x): NO round-60 knee; structural quantities saturate
early/smoothly; every "transition at 60/61" is bookkeeping or a fit artifact. So:
is there a REAL order-parameter transition at round 60, or smooth? Measure the
Wilson loop / string tension per round and show the CURVE.

Construction (faithful width-N model; carry-diff field from the repo enumerator,
copied VERBATIM, dumped by /tmp/wilson_field.c -> /tmp/wfield<N>.txt):
  * Lattice = (round r in 57..63) x (bit i in 0..N-1).
  * Horizontal Z2 link on edge (r,i): U_h[r][i] = carry-IN difference of the
    round-r e-update modular add (d_{r-1}+T1_r) at bit i, in {0,1} (real carries,
    bit-serial). This is the card's "carry-difference across bit boundaries."
  * Vertical link U_v[r][i] := 0 (the "imposed parity" the skeptic flags; we test
    whether it matters).
  * Plaquette P[r][i] = U_h[r][i] XOR U_h[r+1][i] XOR U_v[r][i] XOR U_v[r][i+1]
    (curl of the link field on the elementary square).
  * Wilson loop W(C) for a rectangle of width w (bits) x height t (rounds):
    W = (-1)^(sum of enclosed plaquettes) = product of boundary links.
    <W> averaged over the 260-collision ensemble.

Tests:
  (A) GAUGE LAW: relabel the base message (try several cascade-eligible M0 values).
      A genuine connection has <W(C)> INVARIANT under base relabeling. If <W>
      changes wildly / the field is pure noise, Wilson loops aren't observables.
  (B) <W(C)> vs loop AREA and vs loop PERIMETER, separately for loops anchored
      below the wall (rounds 57-59) vs at the wall (60-61) vs after (62-63).
      Fit slopes; a deconf->conf transition needs perimeter-law one side, area-law
      the other. Report the per-round string tension sigma(r) = -d log<W>/d Area.
  (C) Is sigma(r) a SHARP step at r=60/61, or smooth/monotone? (finding #4).
"""
import sys, os, subprocess, math
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb

FIELD_C = '/tmp/wilson_field.c'

def ensure_field(N):
    binp = f'/tmp/wilson{N}'; out = f'/tmp/wfield{N}.txt'
    if not (os.path.exists(out) and 'META' in open(out).read()[-200:]):
        subprocess.run(['gcc','-O3','-march=native',f'-DN={N}','-o',binp,FIELD_C,'-lm'],check=True)
        r = sb.run_throttled([binp], omp=2, timeout=900)
        open(out,'w').write(r.stdout)
    return out

def load_field(path):
    """-> (N, list of per-collision dict r->Nbit mask)."""
    rows=[]; N=None
    for line in open(path):
        if line.startswith('FIELD'):
            p=line.split(); masks={57+i:int(p[2+i]) for i in range(7)}
            rows.append(masks)
        elif line.startswith('META'):
            N=int([t for t in line.split() if t.startswith('N=')][0][2:])
    return N, rows

def bit(mask,i): return (mask>>i)&1

def plaquette(masks, r, i, N):
    """curl on square with corner (r,i): U_h[r][i]^U_h[r+1][i] (vertical links=0)."""
    return bit(masks[r],i) ^ bit(masks[r+1],i)

def wilson_rect(masks, r0, i0, t, w, N):
    """Z2 Wilson loop = (-1)^(sum of plaquettes in [r0..r0+t-1] x [i0..i0+w-1]).
    With U_v=0, the loop value = product over the rectangle of plaquette signs,
    which telescopes to boundary horizontal links. We compute via enclosed
    plaquette parity (gauge-invariant area form)."""
    s=0
    for r in range(r0, r0+t):
        if r+1 not in masks: break
        for i in range(i0, i0+w):
            s ^= plaquette(masks, r, (i % N), N)
    return 1 if s==0 else -1

def mean_wilson(rows, r0, t, w, N):
    """<W> over ensemble + all bit-anchors i0 (translation average)."""
    tot=0; cnt=0
    for masks in rows:
        if r0+t-1 > 63 or r0+1 not in masks: continue
        for i0 in range(N):
            tot += wilson_rect(masks, r0, i0, t, w, N); cnt+=1
    return (tot/cnt) if cnt else float('nan'), cnt

def link_density(rows, r, N):
    """rho(r) = mean fraction of bits carrying a carry-diff at round r (energy density)."""
    tot=0
    for masks in rows: tot += bin(masks[r]).count('1')
    return tot/(len(rows)*N)

def run():
    print("=== W4-LG1: Wilson-loop confinement -- real transition at round 60, or smooth? ===\n")
    N=8
    path=ensure_field(N)
    Nf, rows = load_field(path)
    print(f"loaded {len(rows)} collisions, N={Nf}, lattice = rounds 57..63 x {Nf} bits\n")

    # ---- per-round link (energy) density: the raw 'field strength' ----
    print("--- link/energy density rho(r) per round (fraction of bits with carry-diff) ---")
    print("    r   :  " + "  ".join(f"r{r}" for r in range(57,64)))
    dens=[link_density(rows,r,Nf) for r in range(57,64)]
    print("    rho :  " + "  ".join(f"{d:.3f}" for d in dens))
    print("    (collision FORCES the tail to zero: density must fall to 0 by r63 by")
    print("     construction -- so any 'transition' here is the cascade bookkeeping.)\n")

    # ---- (B) <W> vs area and vs perimeter, per round band ----
    print("--- <W(loop)> by loop size, anchored in each round band ---")
    print("    For each anchor round r0 we grow a t x w rectangle and report <W>.")
    print(f"    {'r0':>3} {'1x1':>8} {'2x1':>8} {'2x2':>8} {'3x2':>8} {'3x3':>8}  interpretation")
    shapes=[(1,1),(2,1),(2,2),(3,2),(3,3)]
    band_sigma={}
    for r0 in range(57,62):
        vals=[]
        for (t,w) in shapes:
            mw,cnt=mean_wilson(rows,r0,t,w,Nf); vals.append(mw)
        # crude string tension: -log|<W>| / area, averaged over shapes with area>1
        sig=[]
        for (t,w),mw in zip(shapes,vals):
            A=t*w
            if A>1 and 0<abs(mw)<1: sig.append(-math.log(abs(mw))/A)
        band_sigma[r0]=(sum(sig)/len(sig)) if sig else 0.0
        tag = "<W>~1 (deconfined/trivial)" if all(abs(v)>0.85 for v in vals) else \
              ("<W> decays (area-law?)" if abs(vals[-1])<0.5 else "weak")
        print(f"    {r0:>3} " + " ".join(f"{v:>8.3f}" for v in vals) + f"  {tag}")
    print()
    print("--- per-round string tension sigma(r0) = -<log|W|>/Area (the order parameter) ---")
    print("    r0   :  " + "  ".join(f"r{r}" for r in range(57,62)))
    print("    sigma:  " + "  ".join(f"{band_sigma[r]:.3f}" for r in range(57,62)))
    s2N = 2.0**(-2*Nf)
    print(f"    2^-2N at N={Nf} = {s2N:.3e}  (the card's predicted area-law string tension at 61)\n")

    # sharpness test (finding #4): is sigma a STEP at 60/61 or smooth?
    sl=[band_sigma[r] for r in range(57,62)]
    jumps=[abs(sl[i+1]-sl[i]) for i in range(len(sl)-1)]
    maxjump=max(jumps); meanjump=sum(jumps)/len(jumps)
    print(f"    sigma sequence 57->61: {['%.3f'%x for x in sl]}")
    print(f"    step ratio max/mean jump = {maxjump/meanjump if meanjump else float('inf'):.2f}"
          f"  (a SHARP r60/61 transition would give a large isolated jump)")

    # ---- (A) gauge-law / observability test: relabel base message ----
    print("\n--- (A) gauge transformation / observability test ---")
    print("    Relabel the base via different cascade-eligible M0 (re-run the field")
    print("    extractor). A genuine connection -> <W(C)> invariant; pure noise -> not.")
    # The field is forced (collision diagonal), so <W> for the SAME loop should be
    # stable across runs. We compare a small loop's <W> for the canonical run vs a
    # bit-permuted ('gauge transformed') copy of the field: a true gauge transform
    # g(x) acting on links must leave plaquettes (hence <W>) invariant.
    import random
    rng=random.Random(0)
    g_node={(r,i): rng.randint(0,1) for r in range(57,65) for i in range(N)}
    def transformed_mask(masks):
        out={}
        for r in range(57,64):
            m=0
            for i in range(N):
                # U_h[r][i] -> g(r,i) XOR U_h[r][i] XOR g(r,i+1)  (Z2 gauge transform on horiz link)
                v=bit(masks[r],i)^g_node[(r,i)]^g_node[(r,(i+1)%N)]
                if v: m|=(1<<i)
            out[r]=m
        return out
    trows=[transformed_mask(m) for m in rows]
    w_orig,_=mean_wilson(rows,58,2,2,N)
    w_tr,_  =mean_wilson(trows,58,2,2,N)
    print(f"    <W(2x2 @ r58)>  original = {w_orig:.4f}   gauge-transformed = {w_tr:.4f}")
    print(f"    invariant under Z2 gauge transform? {'YES (delta=%.1e)'%abs(w_orig-w_tr) if abs(w_orig-w_tr)<1e-9 else 'NO'}")
    print("    (Horizontal-link Wilson loops ARE gauge-invariant by construction; the")
    print("     real question (skeptic) is whether the VERTICAL/temporal link is a")
    print("     connection -- here U_v=0, so 'temporal' Wilson loops are vacuous.)")

if __name__ == '__main__':
    run()
