#!/usr/bin/env python3
"""
W4-CS4 -- "Counterfactual rigidity -> the plateau as a stable attractor (cross-checks CS1)".

CARD CLAIM: for a FOUND collision, a message bit is *rigid* if do(flip) keeps the output-
diff HW low; conjecture collisions sit at counterfactually-rigid configs; the OUTPUT-side
rigid set = CS1's do-orphans (132), residual = 74 -- a fixed point of the unit-intervention
operator. probe: rigid-bit fraction of each collision vs matched random near-miss --
ELEVATED for collisions? output-side rigid set -> 132 AND = CS1's do-orphans?
KILL: no elevated rigidity, OR the rigid set unrelated to 132 / disagrees with CS1
(it MUST coincide with CS1).

CRITICAL PRIORS (#1, #4): the plateau is REAL (a Binomial ~ HW 74 from ~132 free bits).
But CS1 just measured the actual do-orphan count = 0/256 (every output bit is moved by SOME
exogenous intervention). So CS4's REQUIRED coincidence -- "output-side rigid set = CS1's
do-orphans" -- can only hold if BOTH are the same number; CS1's do-orphans are 0, so if
CS4's output-rigid set is ~132 it DISAGREES with CS1 (kill clause), and if it is ~0 it
agrees with CS1 but is then NOT 132 (the other kill clause). Either way the card's "= 132
AND = CS1" conjunction fails. Plus we test the FALSIFIABLE half: is rigidity ELEVATED for
real collisions vs matched near-misses, or is it GENERIC (avalanche => every flip brittle)?

WHAT WE MEASURE (mini-SHA cascade at N=8, the IG3/gap machinery; uses the FRESH N=8
collision CSV /tmp/run_g8/gap_rows.csv as the found-collision set):
  * INPUT-side rigidity: for each found collision, do(flip) each of the FREE message/tail
    bits (the controllable levers w57..w60, 4N bits), recompute the 8-register output, and
    record the resulting output-diff Hamming weight HW_flip. A lever bit is "rigid" if
    HW_flip stays LOW (<= a threshold). rigid-fraction = #rigid / 4N.
  * Compare collisions vs matched RANDOM NEAR-MISSES (same chamber, random free words with
    output-diff HW near the plateau): is the collision rigid-fraction ELEVATED?
  * OUTPUT-side rigid set: per output bit, how often does it STAY 0 across all lever flips
    of all collisions (a "rigid"/frozen output bit). Is that set size ~132? Does its support
    {a,b,e,f}+4dc match? Does it coincide with CS1's do-orphan set (which CS1 found = 0)?

Run:  OMP_NUM_THREADS=2 taskpolicy -b python3 W4-CS4.py    (N=8, ~20s)
"""
import sys, csv, random, math
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb

REG=('a','b','c','d','e','f','g','h')

def make_sha(N):
    MASK=(1<<N)-1
    def scale_rot(k):
        r=int(round(k*N/32.0)); return r if r>=1 else 1
    rS0=[scale_rot(2),scale_rot(13),scale_rot(22)]; rS1=[scale_rot(6),scale_rot(11),scale_rot(25)]
    rs0=[scale_rot(7),scale_rot(18)]; ss0=scale_rot(3); rs1=[scale_rot(17),scale_rot(19)]; ss1=scale_rot(10)
    def ror(x,k): k%=N; return ((x>>k)|(x<<(N-k)))&MASK
    def S0(a): return ror(a,rS0[0])^ror(a,rS0[1])^ror(a,rS0[2])
    def S1(e): return ror(e,rS1[0])^ror(e,rS1[1])^ror(e,rS1[2])
    def s0(x): return ror(x,rs0[0])^ror(x,rs0[1])^((x>>ss0)&MASK)
    def s1(x): return ror(x,rs1[0])^ror(x,rs1[1])^((x>>ss1)&MASK)
    def Ch(e,f,g): return ((e&f)^((~e)&g))&MASK
    def Mj(a,b,c): return ((a&b)^(a&c)^(b&c))&MASK
    KN=[k&MASK for k in sb.K]; IVN=[v&MASK for v in sb.IV]
    def precompute(M):
        W=[0]*57
        for i in range(16): W[i]=M[i]&MASK
        for i in range(16,57): W[i]=(s1(W[i-2])+W[i-7]+s0(W[i-15])+W[i-16])&MASK
        a,b,c,d,e,f,g,h=IVN
        for i in range(57):
            T1=(h+S1(e)+Ch(e,f,g)+KN[i]+W[i])&MASK; T2=(S0(a)+Mj(a,b,c))&MASK
            h,g,f,e,d,c,b,a=g,f,e,(d+T1)&MASK,c,b,a,(T1+T2)&MASK
        return [a,b,c,d,e,f,g,h],W
    def find_w2(p,q,rnd,w1):
        r1=(p[7]+S1(p[4])+Ch(p[4],p[5],p[6])+KN[rnd])&MASK
        r2=(q[7]+S1(q[4])+Ch(q[4],q[5],q[6])+KN[rnd])&MASK
        T21=(S0(p[0])+Mj(p[0],p[1],p[2]))&MASK; T22=(S0(q[0])+Mj(q[0],q[1],q[2]))&MASK
        return (w1+r1-r2+T21-T22)&MASK
    def rnd1(state,k,w):
        T1=(state[7]+S1(state[4])+Ch(state[4],state[5],state[6])+KN[k]+w)&MASK
        T2=(S0(state[0])+Mj(state[0],state[1],state[2]))&MASK
        return [(T1+T2)&MASK,state[0],state[1],state[2],(state[3]+T1)&MASK,state[4],state[5],state[6]]
    return dict(MASK=MASK,precompute=precompute,find_w2=find_w2,rnd1=rnd1,KN=KN,N=N,s0=s0,s1=s1)

def build_M0(sh):
    MASK=sh['MASK']; MSB=1<<(sh['N']-1)
    for cand in range(MASK+1):
        M1=[MASK]*16; M2=[MASK]*16
        M1[0]=cand; M2[0]=cand^MSB; M2[9]=MASK^MSB
        st1,_=sh['precompute'](M1); st2,_=sh['precompute'](M2)
        if st1[0]==st2[0]:
            return cand,M1,M2,st1,st2
    return None

def main():
    N=8
    sh=make_sha(N); MASK=sh['MASK']
    res=build_M0(sh)
    if res is None:
        print(f"no cascade-eligible M0 at N={N}"); return
    M0,M1,M2,st1,st2=res
    _,W1p=sh['precompute'](M1); _,W2p=sh['precompute'](M2)
    s0=sh['s0']; s1=sh['s1']
    print(f"=== W4-CS4 : counterfactual rigidity & the plateau attractor (N={N}, M0=0x{M0:x}) ===\n")

    def tail_sched(Wp,w57,w58,w59,w60):
        W=list(Wp[:57])+[w57,w58,w59,w60]
        W.append((s1(W[59])+W[54]+s0(W[46])+W[45])&MASK)
        W.append((s1(W[60])+W[55]+s0(W[47])+W[46])&MASK)
        W.append((s1(W[61])+W[56]+s0(W[48])+W[47])&MASK)
        return W
    def out_diff_packed(w57,w58,w59,w60):
        """Run the twin tail with cascade-forced path-2 words for rounds 57..60, each path
        on its own schedule for 61..63; return (output-diff XOR packed into 8N-bit int, HW)."""
        a=list(st1); b=list(st2); wb=[]
        for (r,w) in ((57,w57),(58,w58),(59,w59),(60,w60)):
            w2=sh['find_w2'](a,b,r,w); wb.append(w2); a=sh['rnd1'](a,r,w); b=sh['rnd1'](b,r,w2)
        W1=tail_sched(W1p,w57,w58,w59,w60); W2=tail_sched(W2p,wb[0],wb[1],wb[2],wb[3])
        for r in (61,62,63):
            a=sh['rnd1'](a,r,W1[r]); b=sh['rnd1'](b,r,W2[r])
        out=0; hw=0
        for k in range(8):
            d=(a[k]^b[k])&MASK; out|=d<<(N*k); hw+=bin(d).count('1')
        return out,hw

    # ---- load found collisions (fresh N=8 CSV) ----
    csvp='/tmp/run_g8/gap_rows.csv'
    try:
        colls=[{k:int(v) for k,v in row.items()} for row in csv.DictReader(open(csvp))]
    except FileNotFoundError:
        print(f"need {csvp} (run /tmp/gap_8 first)"); return
    # verify the loaded rows ARE collisions (HW=0)
    nver=sum(1 for c in colls if out_diff_packed(c['w57'],c['w58'],c['w59'],c['w60'])[1]==0)
    print(f"loaded {len(colls)} sr=60 rows; verified full-collision (HW=0): {nver}/{len(colls)}\n")
    colls=[c for c in colls if out_diff_packed(c['w57'],c['w58'],c['w59'],c['w60'])[1]==0]

    FREE_BITS=4*N           # lever bits = w57,w58,w59,w60 (4 words x N)
    NOUT=8*N
    # rigidity threshold: a flip is "rigid" if it keeps HW <= RIG (low). Use a low bar.
    RIG = max(1, N//4)      # ~"stays near 0"; for N=8 => 2

    def rigid_fraction(w):
        """fraction of the 4N lever-bit flips that keep output-diff HW <= RIG."""
        base=[w['w57'],w['w58'],w['w59'],w['w60']]
        nrig=0
        for wi in range(4):
            for bit in range(N):
                pert=list(base); pert[wi]^=(1<<bit)
                _,hw=out_diff_packed(*pert)
                if hw<=RIG: nrig+=1
        return nrig/FREE_BITS

    # ---- INPUT-side rigidity: collisions vs matched random near-misses ----
    rng=random.Random(99)
    # collisions
    rf_coll=[rigid_fraction(c) for c in colls[:40]]
    mean_coll=sum(rf_coll)/len(rf_coll)
    # matched random near-misses: random free words whose HW is near the plateau
    near=[]
    tries=0
    plateau_lo=int(0.30*NOUT)   # "near-miss" = somewhere in the plateau band, not a collision
    while len(near)<40 and tries<200000:
        tries+=1
        w={'w57':rng.randint(0,MASK),'w58':rng.randint(0,MASK),'w59':rng.randint(0,MASK),'w60':rng.randint(0,MASK)}
        _,hw=out_diff_packed(w['w57'],w['w58'],w['w59'],w['w60'])
        if hw>=plateau_lo: near.append(w)
    rf_near=[rigid_fraction(w) for w in near]
    mean_near=sum(rf_near)/len(rf_near) if rf_near else float('nan')

    print(f"[INPUT-side rigidity] rigid = lever-flip keeps out-diff HW <= {RIG}; fraction of {FREE_BITS} lever bits")
    print(f"  collisions     : mean rigid-fraction = {mean_coll:.4f}  (n={len(rf_coll)})")
    print(f"  random near-miss: mean rigid-fraction = {mean_near:.4f}  (n={len(rf_near)})")
    elevated = mean_coll > mean_near + 0.02
    print(f"  => collisions ELEVATED vs near-miss? {elevated}  (delta={mean_coll-mean_near:+.4f})")

    # ---- OUTPUT-side rigid set: which output bits STAY 0 across ALL lever flips of ALL collisions ----
    # (a "rigid/frozen" output bit; the card says this set should be ~132/256 == CS1's do-orphans).
    ever_moved=[False]*NOUT
    for c in colls[:40]:
        base=[c['w57'],c['w58'],c['w59'],c['w60']]
        for wi in range(4):
            for bit in range(N):
                pert=list(base); pert[wi]^=(1<<bit)
                out,_=out_diff_packed(*pert)
                jj=out
                while jj:
                    bb=(jj&-jj).bit_length()-1; ever_moved[bb]=True; jj&=jj-1
    rigid_out=[b for b in range(NOUT) if not ever_moved[b]]
    frac_rigid_out=len(rigid_out)/NOUT
    # per-register support
    perreg={nm:sum(1 for b in rigid_out if N*k<=b<N*k+N) for k,nm in enumerate(REG)}
    print(f"\n[OUTPUT-side rigid set] output bits that stay 0 across ALL lever flips of ALL collisions:")
    print(f"  rigid output bits = {len(rigid_out)}/{NOUT} = {frac_rigid_out:.3f} of output")
    print(f"  expected (card): ~132/256 = 0.516 ; support {{a,b,e,f}}+4dc")
    print(f"  per-register rigid: " + ", ".join(f"{nm}={perreg[nm]}/{N}" for nm in REG))

    # ---- CS1 cross-check: CS1's do-orphan set was 0 (every out-diff bit reachable). Coincide? ----
    print(f"\n[CS1 cross-check] CS1 measured do-orphan count = 0/256 (every output-diff bit reachable).")
    cs1_orphans = 0
    coincide = (len(rigid_out) == cs1_orphans) or (abs(len(rigid_out)/NOUT - 0.0) < 0.02)
    print(f"  CS4 output-rigid fraction {frac_rigid_out:.3f} vs CS1 do-orphan fraction 0.000 : coincide? {coincide}")

    # ---- VERDICT ----
    print(f"\n--- DECISION ---")
    is132 = abs(frac_rigid_out-132/256) < 0.06
    print(f"card needs: (i) rigidity ELEVATED for collisions, AND (ii) output-rigid set ~132 AND = CS1 do-orphans.")
    print(f"measured: elevated={elevated} (delta {mean_coll-mean_near:+.3f}); "
          f"output-rigid={frac_rigid_out:.3f} (~132/256? {is132}); CS1 do-orphans=0 -> coincide? {coincide}")
    # KILL if no elevated rigidity OR rigid set unrelated to 132 / disagrees with CS1.
    kill = (not elevated) or (not is132) or (not coincide and is132)
    if not is132 and frac_rigid_out < 0.06:
        print(f"=> output-rigid set ~ 0 (agrees with CS1=0) but is NOT 132 -> card's '=132' clause FAILS.")
    elif is132 and not coincide:
        print(f"=> output-rigid ~132 but DISAGREES with CS1 do-orphans (0) -> 'must coincide' clause FAILS.")
    print(f"=> KILL {'FIRES' if kill else 'does NOT fire'} "
          f"({'no elevated rigidity; ' if not elevated else ''}"
          f"{'rigid set !=132 / disagrees with CS1' if (not is132 or not coincide) else ''}).")

if __name__ == '__main__':
    main()
