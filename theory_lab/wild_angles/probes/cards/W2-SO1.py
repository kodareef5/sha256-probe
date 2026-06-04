"""
W2-SO1 — Neutral-network percolation: search as drift, plateau as a graph
bottleneck. Does the neutral-net graph actually bottleneck at HW~74, and does
that ADD anything over "132 random bits"?

Card claim: all da=0 messages have equal fitness; adjacent ones (bit-flips that
stay on da=0) form edges. Collision-finding = neutral DRIFT to HW=0, a pure graph
question: does the component reach HW=0, what is its conductance/min-cut. The
HW~74 plateau = a region with no escape edges to lower HW; all solvers stall at
the same HW because they hit the same graph bottleneck.

Probe (per CATALOG): small N, reuse collision lists. Build the da=0 graph (edges =
bit-flips preserving da=0). (a) Are HW=0 collisions in the same component as
high-HW starts? (b) conductance/spectral gap + min-cut location (predict
~0.74N-equivalent). (c) constrained-walk cover time vs diameter; sweep N to see if
conductance collapses.

Kill: Dead if the network is one well-mixed component with constant conductance
and poly drift to HW=0, OR the plateau doesn't coincide with the min-cut.

ADVERSARIAL FRAME (the actual question the lead posed):
  The HW~74 plateau is the repo's MEASURED floor (random 75, SVD 74, hill 78,
  GPU 76) and is fully explained by "132 hard-core bits behave as random draws"
  (writeups/hard_core_132_bits.md). SO1 must ADD a mechanism (a real graph
  bottleneck / conductance collapse located AT the plateau), not RENAME the
  plateau. So the decisive tests are:
    - is the da=0 set a SINGLE connected component under bit-flip-preserving edges?
    - does a genuine graph bottleneck (min-cut / conductance drop) sit AT HW~74,
      or is the HW distribution just Binomial(132, 1/2) re-described as a graph?

CRITICAL SUBTLETY about the edge definition (the card says it is load-bearing):
  In the CASCADE construction, path-2's message tail is DETERMINED by path-1's
  (find_w2 enforces da=0 round-by-round). So da=0 is enforced for EVERY path-1
  tail (w57..w60); the "da=0 manifold" is the WHOLE 4N-bit tail space, and a
  single bit-flip of any tail bit stays on it. => the neutral network is the full
  hypercube Q_{4N} (every tail is a vertex; flip one bit = an edge). Fitness =
  output-difference Hamming weight HW(tail). We test percolation/bottleneck of the
  HW sub-level sets of this hypercube, and whether HW ~ Binomial(c, 1/2).
"""
import sys, math, random, collections
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb
import numpy as np

s = sb.s
MASKN = lambda N: (1 << N) - 1
OFF = dict(a=0, b=1, c=2, d=3, e=4, f=5, g=6, h=7)


# ----------------------------------------------------------------------
# N-bit SHA tail, scaled rotations matching the repo enumerator exactly.
# ----------------------------------------------------------------------
def _scale(k32, N):
    r = int(round(k32 * N / 32.0)); return r if r >= 1 else 1

def make_kit(N):
    m = MASKN(N)
    rS0 = tuple(_scale(k, N) for k in (2, 13, 22))
    rS1 = tuple(_scale(k, N) for k in (6, 11, 25))
    rs0 = (_scale(7, N), _scale(18, N)); ss0 = _scale(3, N)
    rs1 = (_scale(17, N), _scale(19, N)); ss1 = _scale(10, N)
    def ror(x, k): k %= N; return ((x >> k) | (x << (N - k))) & m
    def S0(a): return ror(a, rS0[0]) ^ ror(a, rS0[1]) ^ ror(a, rS0[2])
    def S1(e): return ror(e, rS1[0]) ^ ror(e, rS1[1]) ^ ror(e, rS1[2])
    def s0(x): return ror(x, rs0[0]) ^ ror(x, rs0[1]) ^ ((x >> ss0) & m)
    def s1(x): return ror(x, rs1[0]) ^ ror(x, rs1[1]) ^ ((x >> ss1) & m)
    def Ch(e, f, g): return ((e & f) ^ ((~e & m) & g)) & m
    def Maj(a, b, c): return ((a & b) ^ (a & c) ^ (b & c)) & m
    KN = [s.K[i] & m for i in range(64)]
    IVN = [s.IV[i] & m for i in range(8)]

    def precompute(M16):
        W = [0] * 57
        for i in range(16): W[i] = M16[i] & m
        for i in range(16, 57):
            W[i] = (s1(W[i-2]) + W[i-7] + s0(W[i-15]) + W[i-16]) & m
        a, b, c, d, e, f, g, h = IVN
        for i in range(57):
            T1 = (h + S1(e) + Ch(e, f, g) + KN[i] + W[i]) & m
            T2 = (S0(a) + Maj(a, b, c)) & m
            h = g; g = f; f = e; e = (d + T1) & m
            d = c; c = b; b = a; a = (T1 + T2) & m
        return [a, b, c, d, e, f, g, h], W

    def sha_round(st, k, w):
        a, b, c, d, e, f, g, h = st
        T1 = (h + S1(e) + Ch(e, f, g) + k + w) & m
        T2 = (S0(a) + Maj(a, b, c)) & m
        return [(T1 + T2) & m, a, b, c, (d + T1) & m, e, f, g]

    def find_w2(s1st, s2st, rnd, w1):
        r1 = (s1st[7] + S1(s1st[4]) + Ch(s1st[4], s1st[5], s1st[6]) + KN[rnd]) & m
        r2 = (s2st[7] + S1(s2st[4]) + Ch(s2st[4], s2st[5], s2st[6]) + KN[rnd]) & m
        T21 = (S0(s1st[0]) + Maj(s1st[0], s1st[1], s1st[2])) & m
        T22 = (S0(s2st[0]) + Maj(s2st[0], s2st[1], s2st[2])) & m
        return (w1 + r1 - r2 + T21 - T22) & m

    return dict(m=m, KN=KN, precompute=precompute, sha_round=sha_round,
                find_w2=find_w2, s0=s0, s1=s1)


def find_M0(N, kit):
    """Auto-discover the cascade-eligible M0 (matches the enumerator)."""
    m = kit['m']; MSB = 1 << (N - 1)
    for cand in range(m + 1):
        M1 = [m] * 16; M2 = [m] * 16
        M1[0] = cand; M2[0] = cand ^ MSB; M2[9] = m ^ MSB
        st1, W1 = kit['precompute'](M1)
        st2, W2 = kit['precompute'](M2)
        if st1[0] == st2[0]:
            return cand, M1, M2, st1, st2, W1, W2
    return None


def output_diff_hw(N, kit, st1_0, st2_0, W1pre, W2pre, w57, w58, w59, w60):
    """For tail (w57,w58,w59,w60): run the cascade (path2 tail = find_w2 each
    round, enforcing da=0), then the schedule-determined rounds 61..63, and
    return (final 8N-bit difference vector as int per-lane, total output HW).
    sr=60 collision <=> de61=0; a FULL collision <=> all-lane diff = 0."""
    m = kit['m']; KN = kit['KN']; rnd = kit['sha_round']; fw2 = kit['find_w2']
    s1f = kit['s1']; s0f = kit['s0']
    s1 = list(st1_0); s2 = list(st2_0)
    W1 = list(W1pre); W2 = list(W2pre)        # W[0..56]
    tail = [w57, w58, w59, w60]
    # cascade rounds 57..60
    for off, w in enumerate(tail):
        rr = 57 + off
        w1 = w & m
        w2 = fw2(s1, s2, rr, w1)
        W1.append(w1); W2.append(w2)
        s1 = rnd(s1, KN[rr], w1)
        s2 = rnd(s2, KN[rr], w2)
    # schedule-determined rounds 61..63 (message schedule recurrence)
    for rr in range(61, 64):
        w1 = (s1f(W1[rr-2]) + W1[rr-7] + s0f(W1[rr-15]) + W1[rr-16]) & m
        w2 = (s1f(W2[rr-2]) + W2[rr-7] + s0f(W2[rr-15]) + W2[rr-16]) & m
        W1.append(w1); W2.append(w2)
        s1 = rnd(s1, KN[rr], w1)
        s2 = rnd(s2, KN[rr], w2)
    # final per-lane modular difference
    diff = [(s2[i] - s1[i]) & m for i in range(8)]
    hw = sum(s.hw(d) for d in diff)
    return diff, hw


# ----------------------------------------------------------------------
# Build the neutral-net data: sample many tails, record HW. The "graph" is the
# 4N-bit hypercube of tails; HW is the fitness. We test:
#   (1) HW distribution shape vs Binomial(132/?, 1/2) -> is it "132 random bits"?
#   (2) is the da=0 set one component? (trivially yes: hypercube is connected) and
#       can neutral DRIFT (bit-flip walk among EQUAL-HW tails) move at all, or are
#       equal-HW neighbors absent (a glass, not a drift)?
#   (3) min-cut / bottleneck location: is there a sharp conductance drop AT the
#       plateau HW, or is the descent to HW=0 just rare-event (Binomial tail)?
# ----------------------------------------------------------------------
def sample_hw(N, kit, ctx, trials=40000, seed=0):
    rng = random.Random(seed)
    m = kit['m']
    st1, st2, W1, W2 = ctx
    hws = []
    for _ in range(trials):
        t = [rng.getrandbits(N) for _ in range(4)]
        _, hw = output_diff_hw(N, kit, st1, st2, W1, W2, *t)
        hws.append(hw)
    return hws


def neutral_drift_test(N, kit, ctx, trials=6000, seed=1):
    """For random tails, count how many of the 4N single-bit-flip neighbors are
    NEUTRAL (same HW), DOWN (lower HW), UP (higher HW). Neutral drift needs
    neutral edges; a real bottleneck needs DOWN edges to vanish at the plateau."""
    rng = random.Random(seed); m = kit['m']
    st1, st2, W1, W2 = ctx
    by_hw = collections.defaultdict(lambda: [0, 0, 0, 0])  # [#samples, neutral, down, up]
    for _ in range(trials):
        t = [rng.getrandbits(N) for _ in range(4)]
        _, hw0 = output_diff_hw(N, kit, st1, st2, W1, W2, *t)
        rec = by_hw[hw0]; rec[0] += 1
        for bit in range(4 * N):
            wi = bit // N; bj = bit % N
            t2 = list(t); t2[wi] ^= (1 << bj)
            _, hw1 = output_diff_hw(N, kit, st1, st2, W1, W2, *t2)
            if hw1 == hw0: rec[1] += 1
            elif hw1 < hw0: rec[2] += 1
            else: rec[3] += 1
    return by_hw


def run(N=10):
    print("=" * 74)
    print("W2-SO1  neutral-network percolation  —  plateau as graph bottleneck?")
    print("=" * 74)
    kit = make_kit(N)
    got = find_M0(N, kit)
    if got is None:
        print(f"  no cascade-eligible M0 at N={N}"); return
    M0, M1, M2, st1, st2, W1, W2 = got
    ctx = (st1, st2, W1, W2)
    print(f"  N={N}  M0=0x{M0:x} fill=0x{kit['m']:x}  (cascade da57..60=0 enforced)\n")

    # sanity: confirm CSV collisions are HW=0 under this exact construction
    rows = sb.load_gap_rows()
    nchk = 0; nz = 0
    for r in rows[:50]:
        t = (int(r['w57']), int(r['w58']), int(r['w59']), int(r['w60']))
        diff, hw = output_diff_hw(N, kit, st1, st2, W1, W2, *t)
        nchk += 1
        if hw == 0: nz += 1
    print(f"  [sanity] CSV collision tails reproduce HW=0: {nz}/{nchk} "
          f"(da57=0 cascade + de61=0 => full output diff 0)\n")

    # (1) HW distribution vs Binomial
    hws = sample_hw(N, kit, ctx, trials=40000, seed=0)
    arr = np.array(hws)
    print(f"  (1) output-difference HW over 40k random tails (the 'fitness'):")
    print(f"      mean={arr.mean():.2f} std={arr.std():.2f} min={arr.min()} "
          f"max={arr.max()}  (8N={8*N} output bits)")
    # The 'plateau' analog at this N: the typical (modal/mean) HW the search floor
    # would sit at. Repo's 132/256*... -> here mean HW is the analog of 74.
    # Compare to Binomial(k,1/2): mean=k/2, std=sqrt(k)/2 -> infer effective k.
    k_eff_mean = 2 * arr.mean()
    k_eff_std = (2 * arr.std()) ** 2
    print(f"      if HW~Binomial(k,1/2): k from mean={k_eff_mean:.1f}, "
          f"k from var={k_eff_std:.1f}  (agree => plain random bits, NO graph mechanism)")
    # histogram around the mode
    vals, cnts = np.unique(arr, return_counts=True)
    mode = vals[np.argmax(cnts)]
    print(f"      modal HW={mode}; fraction at HW<=mean-2std (a 'descent' event): "
          f"{(arr <= arr.mean()-2*arr.std()).mean():.4f}")

    # (2)/(3) neutral-drift + bottleneck-vs-HW
    by_hw = neutral_drift_test(N, kit, ctx, trials=4000, seed=1)
    print(f"\n  (2)/(3) per-HW neighbor census (neutral/down/up edge fractions):")
    print(f"      HW :  #samp  neutral%  down%   up%    (DOWN edges = escape to lower HW)")
    for hw in sorted(by_hw):
        n, neu, dn, up = by_hw[hw]
        tot = neu + dn + up
        if n < 5 or tot == 0: continue
        print(f"      {hw:3d} : {n:5d}   {100*neu/tot:5.1f}   {100*dn/tot:5.1f}   "
              f"{100*up/tot:5.1f}")
    print(f"\n  -> A real graph BOTTLENECK at the plateau requires DOWN% -> 0 (no")
    print(f"     escape edges) sharply AT the modal HW. If DOWN% degrades SMOOTHLY")
    print(f"     toward the mean (Binomial drift), the plateau is just the random-")
    print(f"     bit mode RENAMED, not a graph mechanism.")
    return dict(mean=float(arr.mean()), std=float(arr.std()),
                k_mean=k_eff_mean, k_var=k_eff_std, by_hw=dict(by_hw))


if __name__ == '__main__':
    run(N=10)
