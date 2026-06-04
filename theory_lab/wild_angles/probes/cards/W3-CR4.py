#!/usr/bin/env python3
"""
W3-CR4 — Detailed-balance breaking at the feed-forward ADD

Card claim: Every round is a permutation = reversible/detailed-balanced; the ONE
irreversible 2-to-1 reaction is the Davies-Meyer final ADD (H_out = H_in + state) --
so the entire entropy-production / Wegscheider deficiency is localized there, and the
collision baseline = the ADD's fiber multiplicity.

PROBE (per card): N=4..8 verify the round-core satisfies detailed-balance (cycle
conditions) and that ALL non-detailed-balance concentrates at the ADD; histogram the
ADD fiber sizes |{(A,B): A+B == C}|; does de58 (the lone modular/carry-bearing growing
difference) fingerprint this fold?

KILL: entropy production smeared across rounds, OR ADD fibers unrelated to the collision
baseline.

ADVERSARIAL FRAME: (a) a permutation has NO thermodynamic equilibrium, so "detailed-
balanced round" is at best a loose reading -- the meaningful, checkable content is
"round = bijection (measure-preserving, zero entropy production)"; (b) the modular-add
fiber |{(A,B): A+B = C mod 2^N}| is EXACTLY 2^N for every C (perfectly uniform) -- it
holds NO round structure, so equating it to the collision baseline (2^0.74N count /
2^-2N rate) is the crux. We test all three: round bijectivity, ADD-fiber uniformity,
and whether the ADD fiber multiplicity matches the measured collision baseline.

GROUND TRUTH: collision count ~ 2^0.74N ; per-enforced-round rate 2^-2N (two conditions);
|de58| = 2^hw(db56) (the lone growing modular difference). The Davies-Meyer ADD here is
H_out[lane] = IV[lane] + final_state[lane] mod 2^N (8 independent modular adds).

Throttled, exact enumeration, N in {4,5,6} for the bijection check (8-lane state is huge;
we verify bijectivity of the SINGLE-ROUND map on a reduced faithful state and the ADD
fiber exactly). No SAT.
"""
import sys
from collections import Counter
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb
s = sb.s


def _scale(k, N):
    r = int(round(k * N / 32.0))
    return r if r >= 1 else 1


def make_round(N):
    m = (1 << N) - 1
    S0 = [_scale(k, N) for k in (2, 13, 22)]
    S1 = [_scale(k, N) for k in (6, 11, 25)]

    def ror(x, k):
        k %= N
        return ((x >> k) | (x << (N - k))) & m

    def Sig0(a): return ror(a, S0[0]) ^ ror(a, S0[1]) ^ ror(a, S0[2])
    def Sig1(e): return ror(e, S1[0]) ^ ror(e, S1[1]) ^ ror(e, S1[2])
    def Ch(e, f, g): return ((e & f) ^ ((~e & m) & g)) & m
    def Maj(a, b, c): return ((a & b) ^ (a & c) ^ (b & c)) & m

    def rnd(state, k, w):
        a, b, c, d, e, f, g, h = state
        T1 = (h + Sig1(e) + Ch(e, f, g) + (k & m) + w) & m
        T2 = (Sig0(a) + Maj(a, b, c)) & m
        return ((T1 + T2) & m, a, b, c, (d + T1) & m, e, f, g)
    return rnd, m


def round_image_size(N, k, w, lanes=4):
    """Exact: enumerate a `lanes`-dim sub-state (rest fixed) and count distinct full outputs.
    A bijection => image size == domain size. We use lanes=4 over (a,e,h,d) at N<=5."""
    rnd, m = make_round(N)
    bb, cc, ff, gg = 1, 2, 3, 1
    outs = set()
    dom = (1 << N) ** lanes
    for a in range(1 << N):
        for e in range(1 << N):
            for h in range(1 << N):
                for d in range(1 << N):
                    st = (a, bb, cc, d, e, ff, gg, h)
                    o = rnd(st, k, w)
                    outs.add(o)
    return dom, len(outs)


def add_fiber_histogram(N):
    """Davies-Meyer ADD: C = A + B mod 2^N. Fiber over each C = {(A,B): A+B=C}.
    Exact histogram of |fiber| over all C."""
    m = (1 << N) - 1
    cnt = Counter()
    for A in range(1 << N):
        for B in range(1 << N):
            C = (A + B) & m
            cnt[C] += 1
    sizes = Counter(cnt.values())
    return cnt, sizes


def main():
    print("=" * 78)
    print("W3-CR4: detailed-balance / entropy-production localization at the feed-forward ADD")
    print("=" * 78)

    # (1) round bijectivity (permutation => zero entropy production in the core)
    print("\n[1] Is the round-core a bijection (permutation)? (image size == domain size)")
    for N in (3, 4, 5):
        k = s.K[40] & ((1 << N) - 1)
        w = 5 & ((1 << N) - 1)
        dom, img = round_image_size(N, k, w, lanes=4)
        print(f"   N={N}: domain={dom:>8}  image={img:>8}  bijection={dom == img}")

    # (2) ADD fiber histogram (the claimed 'irreversible 2-to-1' fold)
    print("\n[2] Davies-Meyer ADD fiber |{(A,B): A+B = C mod 2^N}| histogram:")
    for N in (4, 6, 8):
        cnt, sizes = add_fiber_histogram(N)
        # sizes: dict {fiber_size: how_many_C_have_it}
        allC = (1 << N)
        uniform = (set(cnt.values()) == {1 << N})
        print(f"   N={N}: #distinct C={len(cnt)} (=2^N={allC}); fiber-size histogram={dict(sizes)}; "
              f"uniform(all=2^N)={uniform}")

    # (3) does the ADD fiber multiplicity match the collision baseline?
    print("\n[3] ADD fiber multiplicity vs collision baseline:")
    print(f"   {'N':>3} | {'ADD fiber size (per C)':>22} | {'2^0.74N (collision count)':>26} | {'2^-2N (rate)':>14}")
    for N in (4, 6, 8, 10):
        fiber = 1 << N                  # exact, uniform
        coll = 2 ** (0.74 * N)
        rate = 2 ** (-2 * N)
        print(f"   {N:>3} | {fiber:>22} | {coll:>26.1f} | {rate:>14.3e}")
    # also per-lane: 8 independent adds -> total fiber (2^N)^8 = 2^(8N); collision count is 2^0.74N
    print("\n   8-lane DM ADD total fiber = (2^N)^8 = 2^(8N).  Collision count ~ 2^0.74N.")
    print("   Match? compare exponents: ADD-fiber exponent per lane = N (HW slope 1.0);")
    print("   collision-count exponent = 0.74; rate exponent = -2. None equal N or each other.")

    # (4) de58 fingerprint check: |de58| = 2^hw(db56); is that an ADD-fiber count?
    print("\n[4] de58 fingerprint: |de58| vs an ADD fiber.")
    print(f"   DE_SIZES (|de58|): {{N: de58}} = "
          f"{{ {', '.join(f'{N}:{sb.DE_SIZES[N][1]}' for N in (4,6,8,10,11,12))} }}")
    print("   law: |de58| = 2^hw(db56) (XOR-bit-count of a difference), NOT 2^N (the ADD fiber).")
    print("   => de58 fingerprints the Maj-IMAGE under a difference, not the +mod-2^N ADD fold.")

    print("\n" + "=" * 78)
    print("KILL: entropy production smeared across rounds, OR ADD fibers unrelated to baseline.")
    print("=" * 78)


if __name__ == '__main__':
    main()
