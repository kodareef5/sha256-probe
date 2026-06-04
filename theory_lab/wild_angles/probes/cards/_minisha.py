"""
_minisha.py — faithful parametric mini-SHA-256(N) for the W7-CG de-vector game-graph
cards.  This is NOT a reimplementation of lib.sha256 (which is fixed 32-bit); it is the
project's standard mini-SHA(N) construction, matching exactly the repo C enumerator
`headline_hunt/bets/block2_wang/trails/backward_construct_n10.c`:
  - N-bit truncation (& MASK) of K, IV, all ops
  - scaled rotations (round(r32*N/32), clamp [1,N-1]); shifts clamp [0,N-1]
  - MSB kernel, word-pair (0,9), fill = all-ones (MASK)
  - cascade DP: pick W2[r] s.t. da_{r+1}=0 given W1[r]

Used READ-ONLY toward the repo: we import the 32-bit K/IV from lib.sha256 and truncate,
so the constants are the repo's, not retyped.
"""
import sys
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb
s = sb.s

K32 = list(s.K)
IV32 = list(s.IV)

# base rotation amounts (SHA-256), scaled like the C enumerator / linround
_BASE = dict(S0=(2, 13, 22), S1=(6, 11, 25), s0=(7, 18, 3), s1=(17, 19, 10))


def params(N):
    MASK = (1 << N) - 1
    MSB = 1 << (N - 1)

    def scr(x):  # scale+clamp rotation to [1,N-1]
        return max(1, min(N - 1, round(x * N / 32)))

    def scs(x):  # scale+clamp shift to [0,N-1]
        return max(0, min(N - 1, round(x * N / 32)))

    rot = {}
    rot['S0'] = tuple(scr(x) for x in _BASE['S0'])
    rot['S1'] = tuple(scr(x) for x in _BASE['S1'])
    # sigma small: two rotations + one shift (last entry is a SHR in SHA)
    rot['s0'] = (scr(_BASE['s0'][0]), scr(_BASE['s0'][1]), scs(_BASE['s0'][2]))
    rot['s1'] = (scr(_BASE['s1'][0]), scr(_BASE['s1'][1]), scs(_BASE['s1'][2]))
    KN = [k & MASK for k in K32]
    IVN = [v & MASK for v in IV32]
    return dict(N=N, MASK=MASK, MSB=MSB, rot=rot, KN=KN, IVN=IVN)


def _ror(x, k, N, MASK):
    k %= N
    return ((x >> k) | (x << (N - k))) & MASK


def make_ops(P):
    N, MASK, rot = P['N'], P['MASK'], P['rot']

    def S0(a):
        r = rot['S0']
        return _ror(a, r[0], N, MASK) ^ _ror(a, r[1], N, MASK) ^ _ror(a, r[2], N, MASK)

    def S1(e):
        r = rot['S1']
        return _ror(e, r[0], N, MASK) ^ _ror(e, r[1], N, MASK) ^ _ror(e, r[2], N, MASK)

    def s0(x):
        r = rot['s0']
        return _ror(x, r[0], N, MASK) ^ _ror(x, r[1], N, MASK) ^ ((x >> r[2]) & MASK)

    def s1(x):
        r = rot['s1']
        return _ror(x, r[0], N, MASK) ^ _ror(x, r[1], N, MASK) ^ ((x >> r[2]) & MASK)

    def Ch(e, f, g):
        return ((e & f) ^ ((~e) & g)) & MASK

    def Maj(a, b, c):
        return ((a & b) ^ (a & c) ^ (b & c)) & MASK

    return dict(S0=S0, S1=S1, s0=s0, s1=s1, Ch=Ch, Maj=Maj)


def precompute(M, P, O):
    """Run 57 rounds; return (state_after_56, W[0..56])."""
    N, MASK, KN, IVN = P['N'], P['MASK'], P['KN'], P['IVN']
    W = [m & MASK for m in M] + [0] * 41
    for i in range(16, 57):
        W[i] = (O['s1'](W[i - 2]) + W[i - 7] + O['s0'](W[i - 15]) + W[i - 16]) & MASK
    a, b, c, d, e, f, g, h = IVN
    for i in range(57):
        T1 = (h + O['S1'](e) + O['Ch'](e, f, g) + KN[i] + W[i]) & MASK
        T2 = (O['S0'](a) + O['Maj'](a, b, c)) & MASK
        h, g, f, e, d, c, b, a = g, f, e, (d + T1) & MASK, c, b, a, (T1 + T2) & MASK
    return (a, b, c, d, e, f, g, h), W


def sha_round(st, k, w, P, O):
    MASK = P['MASK']
    a, b, c, d, e, f, g, h = st
    T1 = (h + O['S1'](e) + O['Ch'](e, f, g) + k + w) & MASK
    T2 = (O['S0'](a) + O['Maj'](a, b, c)) & MASK
    return ((T1 + T2) & MASK, a, b, c, (d + T1) & MASK, e, f, g)


def find_w2(s1, s2, rnd, w1, P, O):
    """Cascade offset: W2 s.t. da_{r+1}=0 given W1=w1."""
    MASK, KN = P['MASK'], P['KN']
    r1 = (s1[7] + O['S1'](s1[4]) + O['Ch'](s1[4], s1[5], s1[6]) + KN[rnd]) & MASK
    r2 = (s2[7] + O['S1'](s2[4]) + O['Ch'](s2[4], s2[5], s2[6]) + KN[rnd]) & MASK
    T21 = (O['S0'](s1[0]) + O['Maj'](s1[0], s1[1], s1[2])) & MASK
    T22 = (O['S0'](s2[0]) + O['Maj'](s2[0], s2[1], s2[2])) & MASK
    return (w1 + r1 - r2 + T21 - T22) & MASK


def find_kernel_M0(P, O):
    """Auto-search a cascade-eligible M[0] like the C enumerator (MSB kernel, (0,9))."""
    N, MASK, MSB = P['N'], P['MASK'], P['MSB']
    for cand in range(1 << N):
        M1 = [cand] + [MASK] * 15
        M2 = [cand ^ MSB] + [MASK] * 15
        M2[9] = MASK ^ MSB
        st1, _ = precompute(M1, P, O)
        st2, _ = precompute(M2, P, O)
        if st1[0] == st2[0]:  # da56 == 0 (cascade input)
            return cand, M1, M2
    return None, None, None


def cascade_devector(P, O, st1_56, st2_56, free4):
    """
    Given the two precomputed states and 4 free words W1[57..60], run the cascade
    (W2[r] chosen so da_{r+1}=0) and return the de-vector (de57,de58,de59,de60)
    as MODULAR differences (e1-e2 mod 2^N) at the e-register of each round-state.
    Index convention: state after round r has e at position 4.  de_r := e1_r - e2_r.
    Returns (de57,de58,de59,de60, st1_60, st2_60).
    """
    MASK, KN = P['MASK'], P['KN']
    s1 = list(st1_56)
    s2 = list(st2_56)
    de = {}
    for k, rnd in enumerate(range(57, 61)):
        w1 = free4[k] & MASK
        w2 = find_w2(s1, s2, rnd, w1, P, O)
        s1 = list(sha_round(s1, KN[rnd], w1, P, O))
        s2 = list(sha_round(s2, KN[rnd], w2, P, O))
        de[rnd] = (s1[4] - s2[4]) & MASK
    return (de[57], de[58], de[59], de[60], tuple(s1), tuple(s2))


def setup(N):
    P = params(N)
    O = make_ops(P)
    M0, M1, M2 = find_kernel_M0(P, O)
    if M0 is None:
        return None
    st1_56, _ = precompute(M1, P, O)
    st2_56, _ = precompute(M2, P, O)
    return dict(P=P, O=O, M0=M0, M1=M1, M2=M2, st1_56=st1_56, st2_56=st2_56)
