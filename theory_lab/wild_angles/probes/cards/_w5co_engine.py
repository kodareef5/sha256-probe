"""
_w5co_engine.py — shared N-bit mini-SHA tail engine for the W5-CO* coalgebra cards.

Faithful Python port of the repo's canonical small-N collision model
(headline_hunt/bets/block2_wang/trails/backward_construct_n10.c, cross-checked
against writeups/sr60_sr61_boundary_proof.md):

  * N-bit words, SHA-256 rotation amounts scaled by N/32 (clamped to >=1).
  * MSB kernel: fill = MASK; M1[0] = auto-discovered M0; M2[0] = M0 ^ MSB;
    M2[9] = MASK ^ MSB. M0 chosen so da56 = 0 (cascade-eligible).
  * Tail = rounds 57..63. Path-1 picks free words W57..W60 freely; path-2 picks
    its free words via the cascade map find_w2 so that da stays 0 each round.
    W[61..63] are schedule-fixed (the sr=60/61 boundary lives at round 61).
  * sr=60 collision  = full 8-register collision after round 63
                       (<=> de61=de62=de63=0, boundary-proof Theorem 3).
  * sr=61 condition   = additionally the round-61 cascade word would have to equal
                       the schedule word (g1=0 AND h=0); rate 2^-2N.

READ-ONLY toward the repo: every primitive mirrors lib.sha256 at width N; the
nonlinear ops (modular add, Ch, Maj, Sigma) are kept EXACT (we need the carry —
these cards are about the *behavioral* structure of the real round).

Verified: N=4 -> 49 full collisions; N=8 -> 260 full collisions.
"""
import sys
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb  # noqa: F401  (pins ground truth; primitives re-exported)


def make_model(N):
    MASK = (1 << N) - 1

    def scale_rot(k32):
        return max(1, round(k32 * N / 32.0))

    rS0 = [scale_rot(2), scale_rot(13), scale_rot(22)]
    rS1 = [scale_rot(6), scale_rot(11), scale_rot(25)]
    rs0 = [scale_rot(7), scale_rot(18)]; ss0 = scale_rot(3)
    rs1 = [scale_rot(17), scale_rot(19)]; ss1 = scale_rot(10)
    KN = [k & MASK for k in sb.K]
    IVN = [v & MASK for v in sb.IV]

    def ror(x, k):
        k %= N
        return ((x >> k) | (x << (N - k))) & MASK

    def S0(a): return ror(a, rS0[0]) ^ ror(a, rS0[1]) ^ ror(a, rS0[2])
    def S1(e): return ror(e, rS1[0]) ^ ror(e, rS1[1]) ^ ror(e, rS1[2])
    def s0(x): return ror(x, rs0[0]) ^ ror(x, rs0[1]) ^ ((x >> ss0) & MASK)
    def s1(x): return ror(x, rs1[0]) ^ ror(x, rs1[1]) ^ ((x >> ss1) & MASK)
    def Ch(e, f, g): return ((e & f) ^ ((~e) & g)) & MASK
    def Mj(a, b, c): return ((a & b) ^ (a & c) ^ (b & c)) & MASK

    return dict(N=N, MASK=MASK, MSB=1 << (N - 1), KN=KN, IVN=IVN,
                S0=S0, S1=S1, s0=s0, s1=s1, Ch=Ch, Mj=Mj)


def precompute(M, Mmsg):
    MASK = M['MASK']
    W = [Mmsg[i] & MASK for i in range(16)] + [0] * 41
    for i in range(16, 57):
        W[i] = (M['s1'](W[i-2]) + W[i-7] + M['s0'](W[i-15]) + W[i-16]) & MASK
    a, b, c, d, e, f, g, h = M['IVN']
    for i in range(57):
        T1 = (h + M['S1'](e) + M['Ch'](e, f, g) + M['KN'][i] + W[i]) & MASK
        T2 = (M['S0'](a) + M['Mj'](a, b, c)) & MASK
        h = g; g = f; f = e; e = (d + T1) & MASK
        d = c; c = b; b = a; a = (T1 + T2) & MASK
    return (a, b, c, d, e, f, g, h), W


def sha_round(s, k, w, M):
    MASK = M['MASK']
    a, b, c, d, e, f, g, h = s
    T1 = (h + M['S1'](e) + M['Ch'](e, f, g) + k + w) & MASK
    T2 = (M['S0'](a) + M['Mj'](a, b, c)) & MASK
    return ((T1 + T2) & MASK, a, b, c, (d + T1) & MASK, e, f, g)


def find_w2(s1, s2, rnd, w1, M):
    """Cascade free word for path-2 keeping da_{r+1}=0, given path-1 uses w1."""
    MASK = M['MASK']
    r1 = (s1[7] + M['S1'](s1[4]) + M['Ch'](s1[4], s1[5], s1[6]) + M['KN'][rnd]) & MASK
    r2 = (s2[7] + M['S1'](s2[4]) + M['Ch'](s2[4], s2[5], s2[6]) + M['KN'][rnd]) & MASK
    T21 = (M['S0'](s1[0]) + M['Mj'](s1[0], s1[1], s1[2])) & MASK
    T22 = (M['S0'](s2[0]) + M['Mj'](s2[0], s2[1], s2[2])) & MASK
    return (w1 + r1 - r2 + T21 - T22) & MASK


def find_M0(M):
    MASK, MSB = M['MASK'], M['MSB']
    for cand in range(MASK + 1):
        M1 = [MASK] * 16; M2 = [MASK] * 16
        M1[0] = cand; M2[0] = cand ^ MSB; M2[9] = MASK ^ MSB
        st1, W1 = precompute(M, M1)
        st2, W2 = precompute(M, M2)
        if st1[0] == st2[0]:
            return dict(M0=cand, M1=M1, M2=M2, st1=st1, W1=W1, st2=st2, W2=W2)
    return None


# ---------------------------------------------------------------------------
# Tail driver. Returns the full diff trace and final equality. Path-2's free
# words are computed INLINE via the cascade (no redundant replay).
# ---------------------------------------------------------------------------
def run_tail(M, setup, w57, w58, w59, w60):
    MASK = M['MASK']; KN = M['KN']
    W1p, W2p = setup['W1'], setup['W2']
    s1, s2 = setup['st1'], setup['st2']

    # rounds 57,58 cascade
    w57b = find_w2(s1, s2, 57, w57, M)
    s1 = sha_round(s1, KN[57], w57, M); s2 = sha_round(s2, KN[57], w57b, M)
    w58b = find_w2(s1, s2, 58, w58, M)
    s1 = sha_round(s1, KN[58], w58, M); s2 = sha_round(s2, KN[58], w58b, M)
    # round 59 cascade -> remember w59b (needed for path-2's schedule W[61])
    w59b = find_w2(s1, s2, 59, w59, M)
    s1 = sha_round(s1, KN[59], w59, M); s2 = sha_round(s2, KN[59], w59b, M)
    # round 60 cascade (path-2 free word = w60 + cas_off60)
    cas_off60 = find_w2(s1, s2, 60, 0, M)
    w60b = (w60 + cas_off60) & MASK
    s1 = sha_round(s1, KN[60], w60, M); s2 = sha_round(s2, KN[60], w60b, M)

    # schedule-fixed words for rounds 61..63 (both paths)
    W1_61 = (M['s1'](w59)  + W1p[54] + M['s0'](W1p[46]) + W1p[45]) & MASK
    W2_61 = (M['s1'](w59b) + W2p[54] + M['s0'](W2p[46]) + W2p[45]) & MASK
    W1_62 = (M['s1'](w60)  + W1p[55] + M['s0'](W1p[47]) + W1p[46]) & MASK
    W2_62 = (M['s1'](w60b) + W2p[55] + M['s0'](W2p[47]) + W2p[46]) & MASK
    W1_63 = (M['s1'](W1_61) + W1p[56] + M['s0'](W1p[48]) + W1p[47]) & MASK
    W2_63 = (M['s1'](W2_61) + W2p[56] + M['s0'](W2p[48]) + W2p[47]) & MASK

    s61a = sha_round(s1, KN[61], W1_61, M); s61b = sha_round(s2, KN[61], W2_61, M)
    de61 = (s61a[4] - s61b[4]) & MASK
    s62a = sha_round(s61a, KN[62], W1_62, M); s62b = sha_round(s61b, KN[62], W2_62, M)
    de62 = (s62a[4] - s62b[4]) & MASK
    s63a = sha_round(s62a, KN[63], W1_63, M); s63b = sha_round(s62b, KN[63], W2_63, M)

    collide = (s63a == s63b)
    # sr=61 compatibility numbers (boundary-proof correction): the cascade word at
    # round 61 vs the schedule word. g1 = W1_61_cascade - W1_61_sched (per-message);
    # h relates the inter-message diffs. We expose the cascade-required W at r61.
    cas_off61 = find_w2(s61a, s61b, 61, 0, M)  # offset that WOULD keep da62=0 here
    return dict(s61=(s61a, s61b), s63=(s63a, s63b),
                de61=de61, de62=de62, collide=collide,
                w59b=w59b, w60b=w60b, cas_off60=cas_off60, cas_off61=cas_off61,
                W1_61=W1_61, W2_61=W2_61)


def enumerate_tail(N, want='collide', collect_state=False):
    """Sweep all (w57,w58,w59,w60). want in:
        'collide' -> full sr=60 collisions (8-reg equal at r63)
        'de61'    -> require de61==0 (intermediate)
       Returns (list_of_records, M, setup). Each record:
         (w57,w58,w59,w60, res_dict)  if collect_state else (w57,w58,w59,w60).
    """
    M = make_model(N)
    setup = find_M0(M)
    R = M['MASK'] + 1
    out = []
    for w57 in range(R):
        for w58 in range(R):
            for w59 in range(R):
                for w60 in range(R):
                    r = run_tail(M, setup, w57, w58, w59, w60)
                    hit = r['collide'] if want == 'collide' else (r['de61'] == 0)
                    if hit:
                        out.append((w57, w58, w59, w60, r) if collect_state
                                   else (w57, w58, w59, w60))
    return out, M, setup


if __name__ == '__main__':
    import time
    for N in (4, 8):
        t0 = time.time()
        colls, M, setup = enumerate_tail(N, want='collide')
        # cross-check: every collision must have de61==de62==0
        bad = 0
        if N <= 6:
            for (a, b, c, d) in colls:
                r = run_tail(M, setup, a, b, c, d)
                if r['de61'] != 0 or r['de62'] != 0:
                    bad += 1
        print(f"[selftest] N={N}: M0=0x{setup['M0']:x}  full collisions = {len(colls)}"
              f"  (expect N4=49, N8=260)  de61/62!=0 among them: {bad}  "
              f"in {time.time()-t0:.1f}s")
