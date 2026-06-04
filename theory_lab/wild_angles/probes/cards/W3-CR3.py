#!/usr/bin/env python3
"""
W3-CR3 — Computational-irreducibility onset -> a compressibility cliff at ~60

Card claim: For each round r, P_r(M) = "da=0 admissible at r"; measure the MINIMAL
REPRESENTATION SIZE of P_r vs r. Reducible early rounds -> small circuits; the wall =
where size(P_r)/(cost of r rounds) plateaus at ~1 (no shortcut). The XOR-linearized
sr=60 timeout is "the cheapest shortcut fails at the wall."

PROBE (per card): N=3,4,5 truth-table P_r for r=1..R; plot three compressibility proxies
(LZMA bytes, decision-diagram node count, greedy circuit size) vs r; is there a KNEE
scaling toward 60 as N grows?

KILL: smooth/monotone, no knee, OR knee independent of round structure.

ADVERSARIAL FRAME (orchestrator prior #4): every "cliff at 60/61" so far has been free-word
bookkeeping or a post-hoc fit; structural quantities decay/saturate SMOOTHLY. The bar:
measure the actual compressibility-vs-round CURVE -- is there a real cliff/knee, or smooth?
A knee that just tracks "number of free bits consumed" (linear bookkeeping) is NOT a
computational-irreducibility cliff.

MODEL
-----
We need P_r(M) over a small Boolean input M so we can truth-table it. The card's predicate
is "da=0 admissible at round r" for the difference cascade. We take the genuine N-bit round
(scaled rotations, the repo mini-SHA convention) acting on a difference pair, with:
  * a fixed nonzero starting message/state difference seed (an active differential), and
  * a free Boolean input vector x of `nvars` bits that perturbs the conditioning state /
    free schedule word at each round.
P_r(x) = 1 iff the produced a-lane difference da is 0 at round r (the cascade survives to r).
For each r we get the full truth table (2^nvars bits) and measure THREE proxies:
  (1) LZMA-compressed byte length of the packed truth table  (Kolmogorov-ish upper bound)
  (2) ROBDD node count (canonical decision-diagram size; pure-python reducer below)
  (3) greedy term count: # of prime-ish implicants from a cheap greedy cover (circuit proxy)
We also normalize proxy / r (the card's "size per round cost"), and look for a knee:
discrete 2nd difference of the proxy-vs-r curve. We test whether the knee ROUND scales with
N (toward 60) or is fixed / absent.

Because we cannot reach round 60 at N<=5, the test is about the SHAPE of the curve: does a
sharp knee EXIST at all and does its position move with N (extrapolatable toward 60), or is
the curve smooth/monotone (KILL)?

Throttled, pure python, N in {3,4,5}, nvars<=12. No SAT.
"""
import sys, lzma, random
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb
s = sb.s


# ---------------- N-bit round (repo mini-SHA scaled rotations) ----------------
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


# ---------------- ROBDD node counter (canonical, pure python) ----------------
class BDD:
    """Minimal ROBDD for a single Boolean function given as a truth-table list (len 2^nvars).
    Variable order = bit index. Returns node count of the reduced diagram."""
    def __init__(self, nvars):
        self.nvars = nvars
        self.unique = {}     # (var, lo, hi) -> id
        self.nodes = {0: ('T0',), 1: ('T1',)}  # terminals
        self.next_id = 2

    def mk(self, var, lo, hi):
        if lo == hi:
            return lo
        key = (var, lo, hi)
        if key in self.unique:
            return self.unique[key]
        nid = self.next_id; self.next_id += 1
        self.unique[key] = nid
        self.nodes[nid] = (var, lo, hi)
        return nid

    def build(self, tt):
        memo = {}

        def rec(var, prefix):
            # prefix = assignment to vars 0..var-1 encoded as int over those bits
            if var == self.nvars:
                return tt[prefix]
            key = (var, prefix)
            if key in memo:
                return memo[key]
            lo = rec(var + 1, prefix)               # this var = 0
            hi = rec(var + 1, prefix | (1 << var))  # this var = 1
            r = self.mk(var, lo, hi)
            memo[key] = r
            return r
        root = rec(0, 0)
        return root

    def count(self, root):
        seen = set()
        stack = [root]
        while stack:
            n = stack.pop()
            if n in seen:
                continue
            seen.add(n)
            node = self.nodes[n]
            if node[0] not in ('T0', 'T1'):
                _, lo, hi = node
                stack.append(lo); stack.append(hi)
        # count non-terminal nodes + terminals actually used
        return len(seen)


def robdd_nodes(tt, nvars):
    bdd = BDD(nvars)
    root = bdd.build(tt)
    return bdd.count(root)


def lzma_bytes(tt):
    # pack truth table bits into bytes, compress
    n = len(tt)
    ba = bytearray((n + 7) // 8)
    for i, v in enumerate(tt):
        if v:
            ba[i >> 3] |= (1 << (i & 7))
    comp = lzma.compress(bytes(ba), preset=9 | lzma.PRESET_EXTREME)
    return len(comp)


def greedy_terms(tt, nvars):
    """Cheap circuit-size proxy: greedy count of axis-aligned subcubes covering the ON-set.
    Repeatedly grab the largest 'don't-care extendable' cube around an uncovered minterm."""
    on = [i for i, v in enumerate(tt) if v]
    if not on:
        return 0
    onset = set(on)
    covered = set()
    terms = 0
    for m in on:
        if m in covered:
            continue
        # grow a cube: try to free each variable if both cofactors are in onset for all combos
        cube_free = 0  # bitmask of free vars
        for var in range(nvars):
            ok = True
            # check: for current cube_free plus this var free, all corners in onset
            free = cube_free | (1 << var)
            base = m & ~free
            corners = [base]
            fb = [v for v in range(nvars) if free & (1 << v)]
            for mask in range(1 << len(fb)):
                cc = base
                for j, vb in enumerate(fb):
                    if mask & (1 << j):
                        cc |= (1 << vb)
                if cc not in onset:
                    ok = False
                    break
            if ok:
                cube_free = free
        # mark covered
        base = m & ~cube_free
        fb = [v for v in range(nvars) if cube_free & (1 << v)]
        for mask in range(1 << len(fb)):
            cc = base
            for j, vb in enumerate(fb):
                if mask & (1 << j):
                    cc |= (1 << vb)
            covered.add(cc)
        terms += 1
    return terms


# ---------------- build P_r truth tables ----------------
def build_Pr_tables(N, nvars, R, seed=20260603):
    """P_r(x) = [da == 0 at round r] for the difference cascade seeded with an active
    differential, where x (nvars bits) perturbs the per-round free schedule word + a slice
    of the conditioning state. Returns list of truth tables tt[r] for r=1..R."""
    rnd, m = make_round(N)
    rng = random.Random(seed)
    # fixed conditioning interior state for path 1 (recurrent mid-schedule)
    base_state = [rng.getrandbits(N) for _ in range(8)]
    # active starting differential on (da,de) head (the thing the cascade must zero)
    seed_da = 1 << (N - 1)
    seed_de = 0
    kconst = s.K[40] & m
    # free schedule words per round (fixed random, shared by both paths -> msgdiff handled via x)
    base_w = [rng.getrandbits(N) for _ in range(R)]

    tts = [[0] * (1 << nvars) for _ in range(R)]
    for x in range(1 << nvars):
        # x perturbs: low nvars bits XOR into the conditioning state e-lane and the round-0 word
        st1 = list(base_state)
        st1[4] ^= (x & m)                       # perturb conditioning e
        st1[2] ^= ((x >> 1) & m)                # perturb conditioning c
        st2 = list(st1)
        st2[0] = (st1[0] + seed_da) & m         # apply starting differential
        st2[4] = (st1[4] + seed_de) & m
        for r in range(R):
            w = base_w[r] ^ ((x >> (r % nvars)) & 1) << (r % N)   # tiny per-round message perturb
            o1 = rnd(st1, (s.K[(40 + r) % 64]) & m, w)
            o2 = rnd(st2, (s.K[(40 + r) % 64]) & m, w)
            da = (o2[0] - o1[0]) & m
            tts[r][x] = 1 if da == 0 else 0
            st1, st2 = list(o1), list(o2)
    return tts


def main():
    print("=" * 78)
    print("W3-CR3: compressibility of P_r ('da=0 admissible at r') vs round r")
    print("=" * 78)
    print("\nADVERSARIAL: is there a real cliff/knee whose round scales toward 60, OR smooth?\n")

    for N in (3, 4, 5):
        nvars = 10 if N >= 4 else 9
        R = 24
        tts = build_Pr_tables(N, nvars, R)
        lz = [lzma_bytes(tt) for tt in tts]
        bd = [robdd_nodes(tt, nvars) for tt in tts]
        gt = [greedy_terms(tt, nvars) for tt in tts]
        onfrac = [sum(tt) / (1 << nvars) for tt in tts]
        print(f"--- N={N}, nvars={nvars}, rounds 1..{R} ---")
        print(f"{'r':>3} | {'ON-frac':>8} | {'LZMA B':>7} | {'BDD nodes':>9} | {'greedy terms':>12} | {'BDD/r':>7}")
        for r in range(R):
            print(f"{r+1:>3} | {onfrac[r]:>8.4f} | {lz[r]:>7} | {bd[r]:>9} | {gt[r]:>12} | {bd[r]/(r+1):>7.2f}")

        # knee detection on each proxy: max discrete 2nd difference (curvature) location
        def knee(series):
            if len(series) < 3:
                return None, 0.0
            d2 = [series[i+1] - 2*series[i] + series[i-1] for i in range(1, len(series)-1)]
            absd2 = [abs(v) for v in d2]
            mx = max(absd2) if absd2 else 0.0
            loc = absd2.index(mx) + 2 if absd2 else None  # round index (1-based)
            return loc, mx
        for name, series in (('LZMA', lz), ('BDD', bd), ('greedy', gt)):
            loc, mag = knee(series)
            # smoothness: ratio max|2nd diff| to mean|1st diff|
            d1 = [abs(series[i+1]-series[i]) for i in range(len(series)-1)]
            meand1 = (sum(d1)/len(d1)) if d1 else 0.0
            sharp = (mag/meand1) if meand1 > 1e-9 else float('inf')
            print(f"   {name:>6}: knee@r={loc}  max|2nd-diff|={mag:.1f}  "
                  f"sharpness(2nd/mean-1st)={sharp:.2f}  (monotone={all(series[i]<=series[i+1] for i in range(len(series)-1)) or all(series[i]>=series[i+1] for i in range(len(series)-1))})")
        print()

    print("=" * 78)
    print("KILL: smooth/monotone, no knee, OR knee independent of round structure.")
    print("Read: does a SHARP knee exist (sharpness>>1) and does its round move with N?")
    print("=" * 78)


if __name__ == '__main__':
    main()
