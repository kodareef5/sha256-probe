"""
W7-RA2 — Collision existence as a Hales-Jewett inevitability.   [P3 · cheap]

Card claim: message-difference vectors over a fixed difference-alphabet = points of
[b]^n; color by output-diff class; a collision family with one free word = a
monochromatic combinatorial LINE (a slidable coordinate, matching the cascade's one
free axis).

Probe (CATALOG): b=2 ({no-diff, δ}), n=2..5 free words; enumerate, color by truncated
output-diff class; does the zero-color class contain a combinatorial line? smallest n
vs round count?
Kill: zero-diff points never align into a line at reachable n, OR threshold n*
INDEPENDENT of round count.
Skeptic: HJ(2,k) is enormous; n<=4 is vastly sub-threshold; an observed 'line' is
sigma-linearity leaking through, not HJ forcing.

Setup (faithful + minimal): pick n message-word positions; difference alphabet
{0 -> add nothing, 1 -> XOR delta} applied to those words (a fixed delta). The cube
is {0,1}^n. For a point d, message M2 = M1 with delta XORed into the chosen words
where d_i=1. Output-diff class = truncated modular diff of the state after R rounds
(we vary R = the 'round count' to test n* vs R dependence). COLOR = that class;
zero-color = full collision through R.

Combinatorial line (b=2): choose a nonempty 'active' coordinate set A and fix the
rest; the line = { point with A=all-0 , point with A=all-1 } (the two-element line).
A monochromatic zero-line = a 2-point collision family sharing a slidable axis.
We ALSO check the STRONGER HJ object: a *root* line where MANY points (not just the
2 endpoints) share the color — but for b=2 a line has exactly 2 points.

READ-ONLY toward the repo. Throttle:
  OMP_NUM_THREADS=2 taskpolicy -b python3 W7-RA2.py
"""
import sys, random, itertools
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb
s = sb.s


def make_model(N):
    MASK = (1 << N) - 1
    def sr(k32): return max(1, round(k32 * N / 32.0))
    rS0 = [sr(2), sr(13), sr(22)]; rS1 = [sr(6), sr(11), sr(25)]
    rs0 = [sr(7), sr(18)]; ss0 = sr(3); rs1 = [sr(17), sr(19)]; ss1 = sr(10)
    KN = [k & MASK for k in s.K]; IVN = [v & MASK for v in s.IV]
    def ror(x, k): k %= N; return ((x >> k) | (x << (N - k))) & MASK
    def S0(a): return ror(a, rS0[0]) ^ ror(a, rS0[1]) ^ ror(a, rS0[2])
    def S1(e): return ror(e, rS1[0]) ^ ror(e, rS1[1]) ^ ror(e, rS1[2])
    def sg0(x): return ror(x, rs0[0]) ^ ror(x, rs0[1]) ^ ((x >> ss0) & MASK)
    def sg1(x): return ror(x, rs1[0]) ^ ror(x, rs1[1]) ^ ((x >> ss1) & MASK)
    def Ch(e, f, g): return ((e & f) ^ ((~e) & g)) & MASK
    def Mj(a, b, c): return ((a & b) ^ (a & c) ^ (b & c)) & MASK
    return dict(N=N, MASK=MASK, KN=KN, IVN=IVN, S0=S0, S1=S1, sg0=sg0, sg1=sg1, Ch=Ch, Mj=Mj)


def compress(M, Mmsg, R):
    """Run R rounds from IV; return final state tuple."""
    N, MASK = M['N'], M['MASK']
    W = [Mmsg[i] & MASK for i in range(16)] + [0] * max(0, R - 16)
    for i in range(16, R):
        W[i] = (M['sg1'](W[i-2]) + W[i-7] + M['sg0'](W[i-15]) + W[i-16]) & MASK
    a, b, c, d, e, f, g, h = M['IVN']
    for i in range(R):
        T1 = (h + M['S1'](e) + M['Ch'](e, f, g) + M['KN'][i] + W[i]) & MASK
        T2 = (M['S0'](a) + M['Mj'](a, b, c)) & MASK
        h = g; g = f; f = e; e = (d + T1) & MASK
        d = c; c = b; b = a; a = (T1 + T2) & MASK
    return (a, b, c, d, e, f, g, h)


def out_diff_class(M, base, words, delta, point, R):
    """For a cube point (tuple of 0/1 over chosen word positions), compute the
    truncated output-diff class (the modular diff of all 8 registers after R rounds),
    as a hashable tuple. Color = this class; (0,..,0) = full collision."""
    MASK = M['MASK']
    M2 = list(base)
    for i, bit in zip(words, point):
        if bit:
            M2[i] ^= delta
    s1 = compress(M, base, R)
    s2 = compress(M, M2, R)
    return tuple((s1[k] - s2[k]) & MASK for k in range(8))


def all_lines(n):
    """All combinatorial lines of {0,1}^n: choose nonempty active set A, fix others.
    Yields (endpoint0, endpoint1) where on A both vary 0->1 together, off A they are
    equal (to the fixed pattern). For b=2 each line = exactly 2 points."""
    coords = list(range(n))
    for ksize in range(1, n + 1):
        for A in itertools.combinations(coords, ksize):
            Aset = set(A)
            fixed_positions = [c for c in coords if c not in Aset]
            for fixmask in range(1 << len(fixed_positions)):
                p0 = [0] * n; p1 = [0] * n
                for bitidx, c in enumerate(fixed_positions):
                    v = (fixmask >> bitidx) & 1
                    p0[c] = v; p1[c] = v
                for c in A:
                    p0[c] = 0; p1[c] = 1
                yield tuple(p0), tuple(p1), tuple(sorted(A))


def find_mono_zero_line(M, base, words, delta, R):
    """Color every cube point; find a combinatorial line both of whose endpoints are
    the ZERO class (full collision). Returns (found, line, n_zero_points, total)."""
    n = len(words)
    color = {}
    pts = list(itertools.product((0, 1), repeat=n))
    for p in pts:
        color[p] = out_diff_class(M, base, words, delta, p, R)
    zero = tuple([0]) * 8  # 8-tuple of zeros
    zero = tuple(0 for _ in range(8))
    n_zero = sum(1 for p in pts if color[p] == zero)
    lines_found = []
    for p0, p1, A in all_lines(n):
        if color[p0] == zero and color[p1] == zero:
            lines_found.append((p0, p1, A))
    # also: ANY monochromatic line (same nonzero color) -> HJ for that color
    mono_any = []
    for p0, p1, A in all_lines(n):
        if color[p0] == color[p1]:
            mono_any.append((p0, p1, A, color[p0] == zero))
    return dict(n=n, n_zero=n_zero, total=len(pts),
                zero_lines=lines_found, mono_any=len(mono_any),
                colors=len(set(color.values())))


if __name__ == '__main__':
    print("W7-RA2 — does the zero-diff (collision) class contain a combinatorial LINE?\n")
    print("Cube {0,1}^n over n chosen message words; delta XORed; color = 8-reg out-diff")
    print("after R rounds. Zero-line = 2-pt collision family sharing a slidable axis.\n")
    N = 8
    M = make_model(N)
    rng = random.Random(42)
    delta = M['MSB'] if False else 1  # delta = LSB diff (a single-bit difference)
    delta = 1
    base = [rng.randint(0, M['MASK']) for _ in range(16)]
    summary = {}
    for R in (8, 12, 16, 32, 57, 64):       # 'round count' axis
        print(f"### R = {R} rounds (round-count axis) ###")
        first_n_with_zero_line = None
        for n in (2, 3, 4, 5):
            words = list(range(n))          # first n message words carry the diff axis
            res = find_mono_zero_line(M, base, words, delta, R)
            has = len(res['zero_lines']) > 0
            if has and first_n_with_zero_line is None:
                first_n_with_zero_line = n
            print(f"  n={n}: cube=2^{n}={res['total']}  #zero(collision) pts={res['n_zero']}  "
                  f"#distinct colors={res['colors']}  zero-LINES={len(res['zero_lines'])}  "
                  f"any-mono-lines={res['mono_any']}")
        summary[R] = first_n_with_zero_line
        print(f"  -> smallest n with a zero(collision) combinatorial line at R={R}: "
              f"{first_n_with_zero_line}\n")

    print("=== n* vs ROUND COUNT (kill prong B: n* INDEPENDENT of R => KILL) ===")
    for R in (8, 12, 16, 32, 57, 64):
        print(f"  R={R:>2}: smallest-n zero-line = {summary[R]}")
    vals = [v for v in summary.values()]
    distinct = set(v for v in vals if v is not None)
    print(f"\n  zero-line ever found at reachable n<=5? {'yes' if any(v for v in vals) else 'NO'}")
    print(f"  does n* DEPEND on R? {'yes (varies)' if len(distinct)>1 else 'NO -> n* independent of round count'}")
    print("  KILL fires if: (a) no zero-line at reachable n, OR (b) n* independent of R.")
    print("  skeptic: any zero-line at n<=5 is sigma-linearity (a single-bit diff that")
    print("  happens to cancel), NOT HJ forcing (HJ(2,5) threshold dwarfs n=5).")
