#!/usr/bin/env python3
"""
W2-QI3 — Feed-forward monogamy: why de58 carries all the differential freedom.

Card claim: the feed-forward "clones" internal state into the output; a monogamy
inequality forces all slack into the de58 channel. Probe (N=4..10): measure
corr(Delta_int, Delta_in) + corr(Delta_int, Delta_out) and per-channel slack;
PREDICT slack ~= 0 in de57/59/60, all in de58.
Kill: dead if the correlation sum has no consistent ceiling, or slack is spread
evenly across de57-60.

GROUND TRUTH to beat (finding #5): de57 = de59 = de60 = 1 ALWAYS; de58 = 2^hw(db56)
for N<=14. The OPEN question is which mechanism PREDICTS that growth law. So a clean
CONFIRMED requires the monogamy quantity to be (a) non-vacuous, (b) localize ALL slack
to de58, and ideally (c) the per-channel "slack" to equal log2|de_k| (i.e. predict the
growth). Merely re-deriving "de58 varies, others frozen" is restating ground truth.

We reproduce the exact mini-SHA cascade of de58_enum.c at width N:
  - M1 = [m0, fill, fill, ...]; M2 flips one kernel bit in words 0 and 9.
  - cascade-1 correction: at each round r, cw_r = cascade1_offset(s1,s2) injected into
    the W of path-2 so that da stays 0 (cascade locks register a).
  - run rounds 57,58 with this correction.
  - de_k (k=57..60) = difference in registers h,g,f,e at ROUND 60 which equal, by the
    shift register, e@57, e@58, e@59, e@60 respectively:
        dh60 = de57, dg60 = de58, df60 = de59, de60 = de60.
  We enumerate W57 over [0,2^N) (full at N<=12) and collect the de_k images.

THE MONOGAMY LEDGER we actually test:
  * Delta_int = the internal round-60 difference vector (de57,de58,de59,de60 packed).
  * Delta_in  = the fixed input message difference (db, constant per (m0,fill,bit)).
  * Delta_out = the cascade target (all-zero output is the collision goal); equivalently
    the de60=0 cascade constraint.
  * per-channel "image dimension" log2 |de_k set| = the realized differential freedom.
  * "monogamy slack" S_k = log2|de_k| (how many bits of freedom that channel holds).
  We check: is S_57 = S_59 = S_60 = 0 (frozen) and S_58 = hw(db56)? i.e. does ALL the
  slack sit in de58 AND equal the growth law? And is the "correlation sum" bounded?
"""
import sys, itertools
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb
import math

def make_ops(N):
    MASK = (1 << N) - 1
    def ror(x, r): r %= N; return ((x >> r) | (x << (N - r))) & MASK
    def shr(x, r): return (x >> r) & MASK
    base = dict(S0=(2,13,22), S1=(6,11,25), s0=(7,18,3), s1=(17,19,10))
    sc = {k: tuple(max(0, min(N-1, round(a*N/32))) for a in t) for k,t in base.items()}
    def Sig0(a): r=sc['S0']; return ror(a,r[0])^ror(a,r[1])^ror(a,r[2])
    def Sig1(e): r=sc['S1']; return ror(e,r[0])^ror(e,r[1])^ror(e,r[2])
    def sig0(x): r=sc['s0']; return ror(x,r[0])^ror(x,r[1])^shr(x,r[2])
    def sig1(x): r=sc['s1']; return ror(x,r[0])^ror(x,r[1])^shr(x,r[2])
    def Ch(e,f,g): return (e & f) ^ ((~e & MASK) & g)
    def Maj(a,b,c): return (a & b) ^ (a & c) ^ (b & c)
    def add(*xs):
        s = 0
        for x in xs: s = (s + x) & MASK
        return s
    def sub(a,b): return (a - b) & MASK
    return locals()

def build(N):
    o = make_ops(N); MASK=o['MASK']; add=o['add']; sub=o['sub']
    Sig0=o['Sig0']; Sig1=o['Sig1']; sig0=o['sig0']; sig1=o['sig1']; Ch=o['Ch']; Maj=o['Maj']
    Kw = [ (k & MASK) for k in sb.K ]
    def sha_round(s, r, w):
        a,b,c,d,e,f,g,h = s
        T1 = add(h, Sig1(e), Ch(e,f,g), Kw[r], w)
        T2 = add(Sig0(a), Maj(a,b,c))
        return [add(T1,T2), a, b, c, add(d,T1), e, f, g]
    def precompute_state(M, k_target):
        W = list(M) + [0]*(64-len(M))
        for i in range(16, 64):
            W[i] = add(sig1(W[i-2]), W[i-7], sig0(W[i-15]), W[i-16])
        s = [v & MASK for v in sb.IV]  # IV mod 2^N
        for r in range(k_target):
            s = sha_round(s, r, W[r])
        return s, W
    def cascade1_offset(s1, s2):
        dh = sub(s1[7], s2[7])
        dSig1 = sub(Sig1(s1[4]), Sig1(s2[4]))
        dCh = sub(Ch(s1[4],s1[5],s1[6]), Ch(s2[4],s2[5],s2[6]))
        T2_1 = add(Sig0(s1[0]), Maj(s1[0],s1[1],s1[2]))
        T2_2 = add(Sig0(s2[0]), Maj(s2[0],s2[1],s2[2]))
        return add(dh, dSig1, dCh, sub(T2_1, T2_2))
    return MASK, sha_round, precompute_state, cascade1_offset, sub

def de_channels(N, m0, fill, bit, full_cap=1<<13):
    """Reproduce the repo's de-set measurement EXACTLY (de58_enum.c / de60_enum.c):
    de_k := (s1[4] - s2[4]) AFTER running cascade-1 round k, over W57 (W58=W59=W60=0
    for path 1, cw injected on path 2). Enumerate W57 fully if 2^N<=full_cap else sample.
    Return sets de57,de58,de59,de60, hw(db56) where db56 = the e-register difference at
    round-57 input that SEEDS the cascade (the quantity the growth law 2^hw(db56) uses)."""
    MASK, sha_round, precompute_state, cascade1_offset, sub = build(N)
    M1 = [m0 & MASK] + [fill & MASK]*15
    M2 = list(M1)
    M2[0] ^= (1 << bit) & MASK
    M2[9] ^= (1 << bit) & MASK
    s1_56, W1 = precompute_state(M1, 57)
    s2_56, W2 = precompute_state(M2, 57)
    held = (s1_56[0] == s2_56[0])  # cascade-1 holds at round-57 input iff da=0
    # db56 = the e-register (s[4]) difference at round-57 input -- this seeds de58.
    db56 = sub(s1_56[4], s2_56[4])
    hw_db56 = bin(db56).count('1')
    de = {57:set(), 58:set(), 59:set(), 60:set()}
    total = 1 << N
    step = 1 if total <= full_cap else max(1, total // full_cap)
    for w57 in range(0, total, step):
        s1 = list(s1_56); s2 = list(s2_56)
        # round 57: cascade-1 correction injected on path 2
        cw57 = cascade1_offset(s1, s2)
        s1 = sha_round(s1, 57, w57)
        s2 = sha_round(s2, 57, (w57 + cw57) & MASK)
        de[57].add(sub(s1[4], s2[4]))                 # e-diff after round 57
        # round 58
        cw58 = cascade1_offset(s1, s2)
        s1 = sha_round(s1, 58, 0); s2 = sha_round(s2, 58, cw58)
        de[58].add(sub(s1[4], s2[4]))                 # e-diff after round 58
        # round 59
        cw59 = cascade1_offset(s1, s2)
        s1 = sha_round(s1, 59, 0); s2 = sha_round(s2, 59, cw59)
        de[59].add(sub(s1[4], s2[4]))                 # e-diff after round 59
        # round 60
        cw60 = cascade1_offset(s1, s2)
        s1 = sha_round(s1, 60, 0); s2 = sha_round(s2, 60, cw60)
        de[60].add(sub(s1[4], s2[4]))                 # e-diff after round 60
    return de, hw_db56, held

def find_held_cases(N, n_want=6, seed=12345):
    """Scan (m0,fill,bit) for combos where cascade-1 HOLDS at round-57 input (da=0)
    AND seeds a nonzero difference (hw(db56)>0). These are the legitimate cascade
    chambers the de-sets are defined on. Deterministic xorshift scan."""
    MASK, sha_round, precompute_state, cascade1_offset, sub = build(N)
    found = []
    st = seed & 0xffffffff
    def nxt():
        nonlocal st
        st ^= (st << 13) & 0xffffffff; st ^= st >> 17; st ^= (st << 5) & 0xffffffff
        return st
    tries = 0
    while len(found) < n_want and tries < 400000:
        tries += 1
        m0 = nxt() & MASK; fill = nxt() & MASK; bit = nxt() % N
        M1 = [m0] + [fill]*15
        M2 = list(M1); M2[0] ^= (1<<bit)&MASK; M2[9] ^= (1<<bit)&MASK
        s1,_ = precompute_state(M1, 57); s2,_ = precompute_state(M2, 57)
        if s1[0] == s2[0] and sub(s1[4], s2[4]) != 0:
            found.append((m0, fill, bit))
    return found

if __name__ == '__main__':
    print("=== W2-QI3: feed-forward monogamy — per-channel slack S_k = log2|de_k| ===")
    print("    GROUND TRUTH (finding #5): de57=de59=de60=1 (S=0); de58=2^hw(db56).")
    print("    de_k := e-reg diff after cascade-1 round k (exactly de58_enum.c/de60_enum.c).")
    print("    Monogamy CONFIRMS iff ALL slack localizes to de58 AND S_58 tracks hw(db56).\n")
    for N in (4, 6, 8, 10, 12):
        cases = find_held_cases(N, n_want=6)
        print(f"--- N={N}  ({len(cases)} held-cascade chambers found) ---")
        law_ok = 0; n_chk = 0
        for (m0, fill, bit) in cases:
            de, hw_db56, held = de_channels(N, m0, fill, bit)
            sizes = {k: len(v) for k,v in de.items()}
            slack = {k: (math.log2(s) if s>0 else 0.0) for k,s in sizes.items()}
            allslack = sum(slack.values())
            in58 = slack[58]
            loc = (in58 / allslack) if allslack>0 else float('nan')
            others = sizes[57]+sizes[59]+sizes[60]   # ==3 iff all frozen to 1
            growth = (sizes[58] == 2**hw_db56)
            n_chk += 1; law_ok += int(growth)
            print(f"  m0={m0:#010x} fill={fill:#010x} bit={bit:2d}: "
                  f"|de|={{57:{sizes[57]},58:{sizes[58]},59:{sizes[59]},60:{sizes[60]}}}  "
                  f"S58={in58:.2f} hw(db56)={hw_db56}  frac_in_de58={loc:.2f}  "
                  f"others_frozen={others==3}  de58==2^hw? {growth}")
        print(f"  => growth law de58==2^hw(db56) held {law_ok}/{n_chk} chambers\n")
