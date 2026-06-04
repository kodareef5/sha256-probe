#!/usr/bin/env python3
"""
W3-CA3 -- Abstract interpretation -> the 132 hard-core = a Galois precision loss.

CARD CLAIM (CATALOG): a sound {0,1,T} carry abstraction (a Galois connection) propagated
from the cascade pre-conditions marks exactly the uncontrolled output bits as T ->
recovers 132 as a *certified superset*, HW~74 as a provable residual.

PROBE (per the card): a ~150-line 3-valued propagator over masked add/Sigma/Ch/Maj, seed
da57..=0, de60=0, count T bits at round 63; must reproduce the 132/124 PARTITION
(da,db,de,df -> T;  dd,dg,dh -> definite).

KILL: marks FAR MORE than 132 (too coarse to get dd/dg/dh definite).

GROUND TRUTH (writeups/hard_core_132_bits.md): the 132 is the single-bit DETERMINISTIC-
CONTROL census: output bit j is "hard" iff NO single input(W[57..60])-bit flip flips j in
ALL base-points. Support = da[63]=db[63]=de[63]=df[63]=32 (128) + 4 scattered dc[63] = 132.
Controlled (124) = dc(28)+dd(32)+dg(32)+dh(32).

ADVERSARIAL CALL (lead finding #1): "132 = corank" is a CATEGORY ERROR confirmed 5x. A
real, stable, basis-independent linear corank lands on 0/128, NEVER 132. A 3-valued AI
T-count is NOT a linear corank -- but the classic failure mode of a sound {def,T} forward
abstraction over ARX is that T is CONTAGIOUS through XOR and especially carry (T (+) x = T,
T carry-out = T), so once the free words seed T it SMEARS across nearly all bits -> the
sound propagator marks ~256, not 132. That is exactly the card's kill ("too coarse to get
dd/dg/dh definite"). So the test is sharp: a SOUND AI either (a) blows up past 132 (KILL,
the generic ARX outcome), or (b) lands on 132 only by being the deterministic census in
disguise (then it is a RENAME of the carry census, not a new Galois dimension, and #1 says
do not CONFIRM a near-132 as a corank/precision-dimension).

We run BOTH: (1) the genuine SOUND {def,T} abstract interpreter over the real modular tail
(carries included) seeded da57=0,de60=0,W57..60=T,W_sched=def -> count T@round63; and (2)
the repo's deterministic single-bit census at N=32 (the adjudicator) to show what 132
really is.
"""
import sys
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb

N = 32
MASK = (1 << N) - 1
ROR = lambda x, r: ((x >> r) | (x << (N - r))) & MASK
SHR = lambda x, r: (x >> r) & MASK
S0r=(2,13,22); S1r=(6,11,25); s0r=(7,18,3); s1r=(17,19,10)
Sig0 = lambda a: ROR(a,S0r[0])^ROR(a,S0r[1])^ROR(a,S0r[2])
Sig1 = lambda e: ROR(e,S1r[0])^ROR(e,S1r[1])^ROR(e,S1r[2])
sig0 = lambda x: ROR(x,s0r[0])^ROR(x,s0r[1])^SHR(x,s0r[2])
sig1 = lambda x: ROR(x,s1r[0])^ROR(x,s1r[1])^SHR(x,s1r[2])
Ch  = lambda e,f,g: (e&f)^((~e&MASK)&g)
Maj = lambda a,b,c: (a&b)^(a&c)^(b&c)
K = [k & MASK for k in sb.K]; IV = [v & MASK for v in sb.IV]

# ============================================================================
# (1) SOUND 3-valued abstract interpreter on the DIFFERENCE state.
# Per output-DIFF bit lattice: 0 = "def. zero diff" (controlled to 0), T = "unknown"
# (could be 0 or 1 -> uncontrolled). Represent a 32-bit abstract value by ONE int `top`
# = bitmask of T-bits (a bit not in `top` is def. 0-diff). This is the standard
# bit-wise constant/known-bit (Kildall) abstraction with concretization gamma(top) =
# { x : x & ~top == 0 }.
# Sound transformers (worst-case over the carry/Ch/Maj nonlinearity):
#   XOR:   top(a^b) = top(a) | top(b)                         (a def-bit ^ def-bit is def;
#                                                              any T makes result T)
#   ROR/SHR: permute/shift the top-mask the same way.
#   ADD (modular, with carry):  any T bit can, via carry, contaminate ALL more-significant
#          bits. SOUND rule: let lo = lowest set bit of (top(a)|top(b)); then every bit
#          >= lo is T (carry propagates upward). bits below lo stay def.  (This is the
#          tightest position-independent sound carry rule for known-bits addition.)
#   Ch(e,f,g): bit i is def-0 only if it is def in e AND (def in f? value? -> we don't track
#          values, only zero-diff). Sound: Ch-diff bit i is def-0 iff e,f,g all def at i;
#          else T.  -> top(Ch)=top(e)|top(f)|top(g).
#   Maj: top(Maj)=top(a)|top(b)|top(c).
# ============================================================================
def a_xor(*ts):
    r = 0
    for t in ts: r |= t
    return r & MASK
def a_ror(t, r): return ((t >> r) | (t << (N - r))) & MASK
def a_shr(t, r): return (t >> r) & MASK
def a_Sig0(t): return a_xor(a_ror(t,S0r[0]),a_ror(t,S0r[1]),a_ror(t,S0r[2]))
def a_Sig1(t): return a_xor(a_ror(t,S1r[0]),a_ror(t,S1r[1]),a_ror(t,S1r[2]))
def a_sig0(t): return a_xor(a_ror(t,s0r[0]),a_ror(t,s0r[1]),a_shr(t,s0r[2]))
def a_sig1(t): return a_xor(a_ror(t,s1r[0]),a_ror(t,s1r[1]),a_shr(t,s1r[2]))
def a_Ch(te,tf,tg): return (te|tf|tg)&MASK
def a_Maj(ta,tb,tc): return (ta|tb|tc)&MASK
def a_add(*ts):
    """Sound modular-add top-mask: carry contaminates all bits at/above the lowest T bit."""
    u = 0
    for t in ts: u |= t
    if u == 0: return 0
    lo = (u & -u).bit_length() - 1
    # every bit >= lo becomes T
    return (MASK & ~((1 << lo) - 1)) & MASK

def abstract_tail():
    """Run the 7-round tail (rounds 57..63) in the {def,T} abstract domain on the DIFF
    state. Seed: cascade holds da=0 through 57..60 (a-diff def-0); the free message words
    W[57..60] are T-sources (full T = all 32 bits unknown); schedule words W[61..63] and
    the incoming register diffs are def-0 EXCEPT we must seed the genuine differential
    entry. The cascade pre-conditions: da57=0 and de60=0. We seed the abstract state at
    round-57 input as the difference the cascade carries: a=def0 (da=0 held), and the
    OTHER registers carry the seed diff -> abstract them as T where the real diff is live.
    Most-honest seed: the only injected freedom is W[57..60]=T; everything else def-0, and
    da is PINNED def-0 each round (cascade), de PINNED def-0 at round 60 (cascade-2).
    Count T bits in each register after round 63."""
    # abstract register diffs at round-57 input: all def-0 (the cascade starts from da=0
    # and we inject difference only via the free words).
    a=b=c=d=e=f=g=h=0
    topW = {57:MASK,58:MASK,59:MASK,60:MASK,61:0,62:0,63:0}  # free words T, sched words def
    for r in range(57,64):
        tW = topW[r]
        # T1 = h + Sig1(e) + Ch(e,f,g) + K + W   (K def-0)
        T1 = a_add(h, a_Sig1(e), a_Ch(e,f,g), tW)
        T2 = a_add(a_Sig0(a), a_Maj(a,b,c))
        a_new = a_add(T1, T2)
        e_new = a_add(d, T1)
        h,g,f,e,d,c,b,a = g,f,e,e_new,c,b,a,a_new
        # cascade pins: da=0 for rounds <=60; de=0 at round 60 (cascade-2 target).
        if r <= 60: a = 0
        if r == 60: e = 0
    return dict(a=a,b=b,c=c,d=d,e=e,f=f,g=g,h=h)

# ============================================================================
# (2) The repo's DETERMINISTIC single-bit control census at N=32 (the adjudicator).
# Output diff-bit j is HARD iff no single W[57..60] bit flip flips j at every base point.
# This is what 132 actually is.
# ============================================================================
def real_tail_diff(W_pre, free, base_state):
    """Run rounds 57..63 from base_state with free words W[57..60]=free[0..3] and
    schedule-extended W[61..63]; return the 8-register output (256 bits packed as 8 ints)."""
    s = list(base_state)
    W = dict()
    for i,r in enumerate((57,58,59,60)): W[r]=free[i]&MASK
    # extend schedule for 61..63 using W_pre (the pre-57 schedule) + the free words
    Wfull = list(W_pre)  # length 61 expected (indices 0..60) with 57..60 placeholder
    for i,r in enumerate((57,58,59,60)):
        if r < len(Wfull): Wfull[r]=free[i]&MASK
        else: Wfull.append(free[i]&MASK)
    while len(Wfull) < 64:
        i=len(Wfull)
        Wfull.append((sig1(Wfull[i-2])+Wfull[i-7]+sig0(Wfull[i-15])+Wfull[i-16])&MASK)
    for r in range(57,64):
        T1=(s[7]+Sig1(s[4])+Ch(s[4],s[5],s[6])+K[r]+Wfull[r])&MASK
        T2=(Sig0(s[0])+Maj(s[0],s[1],s[2]))&MASK
        s=[(T1+T2)&MASK,s[0],s[1],s[2],(s[3]+T1)&MASK,s[4],s[5],s[6]]
    return s

def census(n_base=40, seed=99):
    """Per output-diff-bit deterministic-control census at N=32. Returns per-register
    count of HARD (zero-control) bits and the total."""
    import random
    rng=random.Random(seed)
    REG=['a','b','c','d','e','f','g','h']
    # build base points: random pre-57 schedules (random M -> precompute) and random free
    bases=[]
    for _ in range(n_base):
        M=[rng.getrandbits(N) for _ in range(16)]
        st,Wpre=sb.precompute_state(M)  # state after round 56, W[0..56]
        free=[rng.getrandbits(N) for _ in range(4)]
        bases.append((st,Wpre[:57],free))
    # for each output bit, is there a single W[57..60] bit flip that flips it at EVERY base?
    # "controlled" bit = exists a single (word,pos) flip flipping it in all bases.
    # hard = NOT controlled.
    controlled=[[False]*N for _ in range(8)]  # controlled[reg][bit]
    # reference outputs
    refs=[real_tail_diff(Wpre,free,st) for (st,Wpre,free) in bases]
    for widx in range(4):       # which free word W[57+widx]
        for pos in range(N):    # which bit
            flips_all=None
            for bi,(st,Wpre,free) in enumerate(bases):
                f2=list(free); f2[widx]^=(1<<pos)
                out=real_tail_diff(Wpre,f2,st)
                diff=[(out[r]^refs[bi][r])&MASK for r in range(8)]
                if flips_all is None:
                    flips_all=[[(diff[r]>>p)&1 for p in range(N)] for r in range(8)]
                else:
                    for r in range(8):
                        for p in range(N):
                            flips_all[r][p] &= (diff[r]>>p)&1
            for r in range(8):
                for p in range(N):
                    if flips_all[r][p]: controlled[r][p]=True
    hard_counts={REG[r]: sum(1 for p in range(N) if not controlled[r][p]) for r in range(8)}
    total_hard=sum(hard_counts.values())
    return hard_counts, total_hard

if __name__ == '__main__':
    print("=== W3-CA3: abstract interpretation {0,1,T} -> 132 hard-core as Galois precision loss ===")
    print("    Ground truth: 132 = da,db,de,df@63 (128) + 4 dc = single-bit deterministic census.")
    print("    Finding #1: a real linear corank lands on 0/128, NEVER 132. Is AI a sound corank or the census?\n")

    print("--- (1) SOUND {def,T} abstract interpreter, count T bits at round 63 (N=32) ---")
    res = abstract_tail()
    order=['a','b','c','d','e','f','g','h']
    tops={r:bin(res[r]).count('1') for r in order}
    total_top=sum(tops.values())
    for r in order:
        print(f"    d{r}[63]:  T-bits = {tops[r]:2d} / 32")
    print(f"    TOTAL T (certified-uncontrolled superset) = {total_top} / 256")
    print(f"    (card target: 132, with da,db,de,df=32 each ->T and dd,dg,dh=0 ->definite)\n")

    print("--- (2) Repo deterministic single-bit control census (the adjudicator), N=32 ---")
    hc, tot = census(n_base=40)
    for r in order:
        print(f"    d{r}[63]:  HARD (zero-control) bits = {hc[r]:2d} / 32")
    print(f"    TOTAL hard = {tot} / 256   (repo ground truth: 132 = 128 + 4 dc)\n")

    print("=== Adjudication ===")
    print(f"    sound-AI T-count = {total_top};  deterministic census = {tot}.")
    if total_top > 140:
        print("    => AI T-count BLOWS UP past 132 (T contagious through carry/XOR): KILL clause fires.")
    print("    Per finding #1: 132 is the carry/deterministic-control CENSUS, not a Galois precision")
    print("    dimension. A sound forward AI over ARX cannot keep dd/dg/dh definite once free words")
    print("    seed T (carry smears T upward), so it over-marks; matching 132 would require BEING the")
    print("    census, not a new abstract-interpretation corank.")
