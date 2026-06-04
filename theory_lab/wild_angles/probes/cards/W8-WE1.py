#!/usr/bin/env python3
"""
W8-WE1 -- Weihrauch product jump: sr=60 is C_{2^N}, sr=61 is C_{2^N} * C_{2^N}.

CLAIM (CATALOG): sr<=60 = a single bounded closed choice (the cascade IS the
reduction, solution guaranteed); sr=61's (g1=0 AND h=0) = a *parallel product*
of two independent closed choices -> strictly harder. The "independent gating
condition count" Q(r) is the parallel-product arity; predict Q=1 for r in
{57..60}, Q=2 at 61. The advice-bit count A(r)=0->2N and reduction arity K=1->2
agree (triangulation). All step at 61.

PROBE (this script): instrument the cascade tail to COUNT independent gating
conditions Q(r) per round, with independence judged by the memo's ratio test
(P(both)/[P(A)P(B)] ~ 1). Crucially -- ADVERSARIALLY -- also push one round
further and measure the sr=62 step directly: if the Weihrauch degree is a real
*derivation* (not a rename of g1,h), the per-round parallel-product arity Q=2
should hold at the NEXT enforced round too, forecasting sr=62 = 2^-4N. If
instead Q is only defined/observed at the single 61 boundary and "sr=62=2^-4N"
is pure extrapolation, then WE1 adds no derivation over the established g1,h.

KILL_CRITERION: "Q>=2 at some r<=60, or the two conditions are dependent at 61
(collapses to 1), or Q flat/smooth."

We RE-USE the repo's exact cascade-DP enumeration (lib.sha256 primitives via
shabridge). Small N. Throttle the heavy enumeration via run_throttled around the
repo's gap_analysis.c (already validated), and do the per-round arity bookkeeping
in Python here for clarity.
"""
import sys, os
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb
s = sb.s

# ---------------------------------------------------------------------------
# Build a faithful small-N cascade-DP tail in pure python, mirroring the repo's
# gap_analysis.c EXACTLY (scaled rotations, MSB kernel, auto M0). For each round
# r in the tail we ask: is W[r] a FREE word (the cascade sets it, no condition,
# Q=0) or is it SCHEDULE-DETERMINED (must match sched[r] -> coincidence)?  At the
# first schedule-determined round we count the independent per-message value
# match (g) and inter-message compatibility (h) conditions.
# ---------------------------------------------------------------------------
import math

def scale_rot(k, N):
    r = int(round(k * N / 32.0)); return r if r >= 1 else 1

def make_ctx(N):
    MASK = (1 << N) - 1; MSB = 1 << (N - 1)
    rS0 = [scale_rot(x, N) for x in (2, 13, 22)]
    rS1 = [scale_rot(x, N) for x in (6, 11, 25)]
    rs0 = [scale_rot(x, N) for x in (7, 18)]; ss0 = scale_rot(3, N)
    rs1 = [scale_rot(x, N) for x in (17, 19)]; ss1 = scale_rot(10, N)
    def ror(x, k): k %= N; return ((x >> k) | (x << (N - k))) & MASK
    def S0(a): return ror(a, rS0[0]) ^ ror(a, rS0[1]) ^ ror(a, rS0[2])
    def S1(e): return ror(e, rS1[0]) ^ ror(e, rS1[1]) ^ ror(e, rS1[2])
    def s0(x): return ror(x, rs0[0]) ^ ror(x, rs0[1]) ^ ((x >> ss0) & MASK)
    def s1(x): return ror(x, rs1[0]) ^ ror(x, rs1[1]) ^ ((x >> ss1) & MASK)
    def Ch(e, f, g): return ((e & f) ^ ((~e) & g)) & MASK
    def Mj(a, b, c): return ((a & b) ^ (a & c) ^ (b & c)) & MASK
    K32 = s.K; IV32 = s.IV
    KN = [k & MASK for k in K32]; IVN = [v & MASK for v in IV32]
    return dict(N=N, MASK=MASK, MSB=MSB, ror=ror, S0=S0, S1=S1, s0=s0, s1=s1,
                Ch=Ch, Mj=Mj, KN=KN, IVN=IVN)

def precompute(M, ctx):
    N, MASK = ctx['N'], ctx['MASK']
    W = [M[i] & MASK for i in range(16)]
    for i in range(16, 57):
        W.append((ctx['s1'](W[i-2]) + W[i-7] + ctx['s0'](W[i-15]) + W[i-16]) & MASK)
    a, b, c, d, e, f, g, h = ctx['IVN']
    for i in range(57):
        T1 = (h + ctx['S1'](e) + ctx['Ch'](e, f, g) + ctx['KN'][i] + W[i]) & MASK
        T2 = (ctx['S0'](a) + ctx['Mj'](a, b, c)) & MASK
        h = g; g = f; f = e; e = (d + T1) & MASK; d = c; c = b; b = a; a = (T1 + T2) & MASK
    return [a, b, c, d, e, f, g, h], W

def sha_round2(st, k, w, ctx):
    MASK = ctx['MASK']
    T1 = (st[7] + ctx['S1'](st[4]) + ctx['Ch'](st[4], st[5], st[6]) + k + w) & MASK
    T2 = (ctx['S0'](st[0]) + ctx['Mj'](st[0], st[1], st[2])) & MASK
    ns = st[:]
    ns[7] = st[6]; ns[6] = st[5]; ns[5] = st[4]; ns[4] = (st[3] + T1) & MASK
    ns[3] = st[2]; ns[2] = st[1]; ns[1] = st[0]; ns[0] = (T1 + T2) & MASK
    return ns

def find_w2(s1, s2, rnd, w1, ctx):
    MASK = ctx['MASK']; KN = ctx['KN']
    r1 = (s1[7] + ctx['S1'](s1[4]) + ctx['Ch'](s1[4], s1[5], s1[6]) + KN[rnd]) & MASK
    r2 = (s2[7] + ctx['S1'](s2[4]) + ctx['Ch'](s2[4], s2[5], s2[6]) + KN[rnd]) & MASK
    T21 = (ctx['S0'](s1[0]) + ctx['Mj'](s1[0], s1[1], s1[2])) & MASK
    T22 = (ctx['S0'](s2[0]) + ctx['Mj'](s2[0], s2[1], s2[2])) & MASK
    return (w1 + r1 - r2 + T21 - T22) & MASK

def find_M0(ctx):
    N, MASK, MSB = ctx['N'], ctx['MASK'], ctx['MSB']
    for cand in range(MASK + 1):
        M1 = [MASK] * 16; M2 = [MASK] * 16
        M1[0] = cand; M2[0] = cand ^ MSB; M2[9] = MASK ^ MSB
        st1, _ = precompute(M1, ctx); st2, _ = precompute(M2, ctx)
        if st1[0] == st2[0]:
            return cand, M1, M2
    return None, None, None

# ---------------------------------------------------------------------------
# Per-round gating-condition arity Q(r) over the full cascade-DP enumeration.
# For r=57..60: W[r] is a FREE loop variable -> the cascade always realizes
# de_r=0 for *both* messages (find_w2 solves W2[r]); no coincidence => Q=0.
# We VERIFY this by checking that for every (free) assignment, de_r=0 holds for
# both messages with NO residual condition (the realized-image is full).
# For r=61 (the W[60]-schedule match -> sr=61): two candidate conditions
#   g1 = w60 - sched1[60]   (per-message value match)
#   h  = casoff - (sched2[60]-sched1[60])  (inter-message compatibility)
# Count Q=#{independent ~2^-N conditions}, independence by ratio test.
# For r=62 (the W[61]-schedule match -> sr=62, given sr=61): ADVERSARIAL extra
# round. W[61] is now schedule-determined; analogous g1',h'. Measure whether the
# SAME parallel-product arity Q=2 recurs (forecasting sr=62=2^-4N) by counting,
# among sr=61 configs (or, since those are ~0 at small N, among de61=0 hits) the
# fraction also achieving de62=0, and decomposing it into per-msg + compat.
# ---------------------------------------------------------------------------

def run(N):
    ctx = make_ctx(N); MASK = ctx['MASK']
    M0, M1, M2 = find_M0(ctx)
    if M0 is None:
        return None
    st1, W1p = precompute(M1, ctx); st2, W2p = precompute(M2, ctx)

    # tallies over the de61=0 enumeration (the gating manifold)
    ntrip = 0
    # round-61 (sr=61) conditions:
    nde61 = 0; ng1 = 0; nh = 0; nboth61 = 0
    # round-62 (sr=62) conditions, measured on the de61=0 & de62-evaluable hits:
    nde62_of_de61 = 0          # how many de61=0 hits ALSO have de62=0
    ng1b = 0; nhb = 0; nboth62 = 0   # per-msg / compat / both for the 62-step
    # free-round sanity: the cascade INVARIANT is da=0 (a-register diff), forced
    # for BOTH messages at every free round by find_w2 -> NO coincidence => Q=0.
    # (de_r is NOT individually 0 during the free cascade; only da is. de60=0
    #  comes out automatically -> Theorem 2; the first ENFORCED de is de61.)
    free_da_nonzero = {57: 0, 58: 0, 59: 0, 60: 0}
    de60_nonzero = 0            # Theorem 2: de60 should be 0 automatically

    # precompute per-message constants (mirror gap_analysis.c naming)
    for w57 in range(MASK + 1):
        s57a = st1[:]; s57b = st2[:]
        w57b = find_w2(s57a, s57b, 57, w57, ctx)
        s57a = sha_round2(s57a, ctx['KN'][57], w57, ctx)
        s57b = sha_round2(s57b, ctx['KN'][57], w57b, ctx)
        if (s57a[0] - s57b[0]) & MASK: free_da_nonzero[57] += 1   # da invariant
        for w58 in range(MASK + 1):
            s58a = s57a[:]; s58b = s57b[:]
            w58b = find_w2(s58a, s58b, 58, w58, ctx)
            s58a = sha_round2(s58a, ctx['KN'][58], w58, ctx)
            s58b = sha_round2(s58b, ctx['KN'][58], w58b, ctx)
            if (s58a[0] - s58b[0]) & MASK: free_da_nonzero[58] += 1
            # per-triple sched constants for the 60/61/62 steps
            sched1_60 = (ctx['s1'](w58) + W1p[53] + ctx['s0'](W1p[45]) + W1p[44]) & MASK
            sched2_60 = (ctx['s1'](w58b) + W2p[53] + ctx['s0'](W2p[45]) + W2p[44]) & MASK
            for w59 in range(MASK + 1):
                s59a = s58a[:]; s59b = s58b[:]
                w59b = find_w2(s59a, s59b, 59, w59, ctx)
                s59a = sha_round2(s59a, ctx['KN'][59], w59, ctx)
                s59b = sha_round2(s59b, ctx['KN'][59], w59b, ctx)
                if (s59a[0] - s59b[0]) & MASK: free_da_nonzero[59] += 1
                ntrip += 1
                casoff = find_w2(s59a, s59b, 60, 0, ctx)
                hh = (casoff - ((sched2_60 - sched1_60) & MASK)) & MASK
                # schedule-determined W[61],W[62],W[63] for both messages
                W1_61 = (ctx['s1'](w59) + W1p[54] + ctx['s0'](W1p[46]) + W1p[45]) & MASK
                W2_61 = (ctx['s1'](w59b) + W2p[54] + ctx['s0'](W2p[46]) + W2p[45]) & MASK
                sc62_1 = (W1p[55] + ctx['s0'](W1p[47]) + W1p[46]) & MASK
                sc62_2 = (W2p[55] + ctx['s0'](W2p[47]) + W2p[46]) & MASK
                for w60 in range(MASK + 1):
                    w60b = (w60 + casoff) & MASK
                    a = s59a[:]; b = s59b[:]
                    a = sha_round2(a, ctx['KN'][60], w60, ctx)
                    b = sha_round2(b, ctx['KN'][60], w60b, ctx)
                    if (a[0] - b[0]) & MASK: free_da_nonzero[60] += 1   # da invariant (free)
                    if (a[4] - b[4]) & MASK: de60_nonzero += 1          # Thm2: de60 auto-0
                    a1 = sha_round2(a, ctx['KN'][61], W1_61, ctx)
                    b1 = sha_round2(b, ctx['KN'][61], W2_61, ctx)
                    if ((a1[4] - b1[4]) & MASK) != 0:
                        continue                      # de61=0 filter (gating manifold)
                    nde61 += 1
                    g1 = (w60 - sched1_60) & MASK
                    if g1 == 0: ng1 += 1
                    if hh == 0: nh += 1
                    if g1 == 0 and hh == 0: nboth61 += 1
                    # ---- adversarial 62-step: apply round 62, test de62=0 ----
                    W1_62 = (ctx['s1'](w60) + sc62_1) & MASK
                    W2_62 = (ctx['s1'](w60b) + sc62_2) & MASK
                    a2 = sha_round2(a1, ctx['KN'][62], W1_62, ctx)
                    b2 = sha_round2(b1, ctx['KN'][62], W2_62, ctx)
                    de62 = (a2[4] - b2[4]) & MASK
                    # decompose the 62-step like the 61-step:
                    #   g1' (per-msg value match at the W[61] schedule slot) and
                    #   h'  (inter-msg compat at the 62 slot). The "value" slot for
                    #   the 62 enforcement is W[61] itself (now schedule-fixed): the
                    #   per-message condition is W1[61] hitting its OWN sched value;
                    #   but in the cascade W[61] is already forced =sched, so the
                    #   residual 62 condition is purely the de62=0 coincidence. We
                    #   measure de62=0 directly and also its per-msg/compat split via
                    #   the round-62 difference identity.
                    g1b = ( (a1[4]-b1[4]) ) & MASK  # =0 here by de61 filter (sanity)
                    # the genuine new condition at 62: de62==0
                    if de62 == 0:
                        nde62_of_de61 += 1
                    # per-msg vs compat split for 62 step: emulate g/h via the
                    # round-62 T1 difference. de62 = (dd_in + dT1_62). Use the
                    # same structure: per-msg value match (W1_62 vs its schedule)
                    # is automatic; the residual is the cross-message compat h2.
                    # Count h2==0 and (g already 0) jointly.
                    # h2 := de62 contribution from the schedule mismatch
                    if de62 == 0:
                        nhb += 1
                        if g1 == 0:           # condition on the 61 per-msg match too
                            nboth62 += 1
                    if g1 == 0:
                        ng1b += 1

    res = dict(N=N, M0=M0, fill=MASK, ntrip=ntrip,
               free_da_nonzero=free_da_nonzero, de60_nonzero=de60_nonzero,
               nde61=nde61, ng1=ng1, nh=nh, nboth61=nboth61,
               nde62_of_de61=nde62_of_de61, ng1b=ng1b, nhb=nhb, nboth62=nboth62)
    return res

def summarize(res):
    N = res['N']; MASK = (1 << N) - 1
    print(f"=== W8-WE1 per-round gating arity  N={N}  M0=0x{res['M0']:x} fill=0x{res['fill']:x} ===")
    print(f"triples (free w57,w58,w59) enumerated: {res['ntrip']}")
    print()
    print("--- FREE rounds 57..60: Q(r) = independent coincidence conditions ---")
    print("    (cascade invariant = da=0, forced for BOTH msgs by find_w2 => Q=0)")
    fdn = res['free_da_nonzero']
    for r in (57, 58, 59, 60):
        flag = "OK (da=0 forced for BOTH msgs => no coincidence => Q=0)" if fdn[r] == 0 \
               else f"VIOLATION: {fdn[r]} da!=0 cases (cascade broke; Q>0!)"
        print(f"  r={r}: da!=0 count = {fdn[r]}   Q({r})=0  [{flag}]")
    print(f"  [Thm2 check] de60!=0 count = {res['de60_nonzero']}  "
          f"(expect 0: de60 auto-zero, the last FREE round)")
    print()
    nde61 = res['nde61']
    pg1 = res['ng1'] / nde61 if nde61 else 0
    ph  = res['nh']  / nde61 if nde61 else 0
    pboth = res['nboth61'] / nde61 if nde61 else 0
    ratio = pboth / (pg1 * ph) if (pg1 * ph) > 0 else float('nan')
    print("--- r=61 (W[60]-schedule match -> sr=61): condition count Q(61) ---")
    print(f"  de61=0 gating hits: {nde61}")
    print(f"  P(g1=0)={pg1:.6f}  (2^-N={1/(MASK+1):.6f})   [per-message value match]")
    print(f"  P(h=0) ={ph:.6f}                              [inter-message compatibility]")
    print(f"  P(g1=0 & h=0)={pboth:.8f}   P(g1=0)*P(h=0)={pg1*ph:.8f}")
    print(f"  independence ratio = {ratio:.3f}  (~1 => INDEPENDENT => Q(61)=2)")
    q61 = 2 if (0.7 < ratio < 1.4 and pg1 > 0 and ph > 0) else 1
    print(f"  => Q(61) = {q61}")
    print()
    print("--- r=62 (W[61]-schedule match -> sr=62, GIVEN sr=61): ADVERSARIAL ---")
    nde62 = res['nde62_of_de61']
    p_de62_given_de61 = nde62 / nde61 if nde61 else 0
    print(f"  among {nde61} de61=0 hits, de62=0 also: {nde62}")
    print(f"  P(de62=0 | de61=0) = {p_de62_given_de61:.6f}  (2^-N={1/(MASK+1):.6f}, 2^-2N={1/(MASK+1)**2:.8f})")
    # Interpret: is the 62-step ONE more 2^-N condition (rate of one round adds
    # 2^-N to the *conditional*), or TWO (2^-2N conditional)?  For sr=62 = 2^-4N
    # *relative to sr=60*, the CONDITIONAL P(de62=0|de61=0) must be 2^-2N.
    import math
    if p_de62_given_de61 > 0:
        cond_exp = -math.log(p_de62_given_de61, 2) / N
        print(f"  conditional 62-step exponent: -log2(P)/N = {cond_exp:.3f}  "
              f"(1.0 => 2^-N/round; 2.0 => 2^-2N/round => sr=62=2^-4N)")
    else:
        print("  P(de62=0|de61=0)=0 at this N (no joint hits) -> exponent unmeasurable here")
        print("  (small-N starvation: sr=61 itself is ~0, so the 62 step is unsamplable)")
    print()
    print("VERDICT INPUTS:")
    print(f"  Q(57..60) all 0 (free)?  {all(v==0 for v in fdn.values())}")
    print(f"  Q(61)=2 (independent g1,h)?  {q61==2}")
    print(f"  62-step measurable to confirm 2^-4N forecast?  {nde62>0}")
    return q61, p_de62_given_de61, nde62

if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--N', type=int, default=8)
    args = ap.parse_args()
    r = run(args.N)
    if r is None:
        print(f"no cascade-eligible M0 at N={args.N}")
        sys.exit(1)
    summarize(r)
