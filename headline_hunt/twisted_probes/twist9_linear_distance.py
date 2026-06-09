#!/usr/bin/env python3
"""
TWIST 9 — the "linear distance" of SHA-256.

Ch and Maj are the only true Boolean nonlinearity in the round function
(Sigma0/Sigma1 and the message schedule sigmas are already GF(2)-linear;
the modular adds are nonlinear only via their carries). This probe replaces
Ch/Maj with their best LINEAR (affine-over-GF(2)) approximations and, in the
fully-linear limit, replaces the modular adds with XOR. It measures how the
differential behaviour collapses toward "trivially linear" as nonlinearity
is removed, and partitions the round's nonlinearity budget into
carries vs Ch vs Maj.

Deterministic. Imports primitives from lib/sha256.
"""
import sys, random, itertools
sys.path.insert(0, "lib")
from sha256 import Ch, Maj, Sigma0, Sigma1, K as KCONST, hw

M = 0xFFFFFFFF

# ----------------------------------------------------------------------------
# Round function, parameterised by boolean choices and carry-mode.
#   ch / mj : the (possibly linearised) bitwise gadgets
#   lin_add : if True, every modular add becomes XOR (carries removed)
# ----------------------------------------------------------------------------
def round_fn(s, w, k, ch=Ch, mj=Maj, lin_add=False):
    a, b, c, d, e, f, g, h = s
    def AD(*xs):
        if lin_add:
            r = 0
            for x in xs:
                r ^= x
            return r & M
        r = 0
        for x in xs:
            r = (r + x) & M
        return r
    T1 = AD(h, Sigma1(e), ch(e, f, g), k, w)
    T2 = AD(Sigma0(a), mj(a, b, c))
    return (AD(T1, T2), a, b, c, AD(d, T1), e, f, g)

# ----------------------------------------------------------------------------
# Linear (affine-over-GF(2)) approximations of Ch and Maj.
# Each acts bitwise; the candidates below are themselves GF(2)-linear.
# ----------------------------------------------------------------------------
CH_APPROX = {
    "g            (Ch~g)": lambda e, f, g: g,
    "f            (Ch~f)": lambda e, f, g: f,
    "e            (Ch~e)": lambda e, f, g: e,
    "f^g          (Ch~f^g)": lambda e, f, g: (f ^ g) & M,
    "e^g          (Ch~e^g)": lambda e, f, g: (e ^ g) & M,
    "0            (Ch~0)": lambda e, f, g: 0,
}
MAJ_APPROX = {
    "a^b^c        (Maj~a+b+c)": lambda a, b, c: (a ^ b ^ c) & M,
    "a            (Maj~a)": lambda a, b, c: a,
    "b            (Maj~b)": lambda a, b, c: b,
    "c            (Maj~c)": lambda a, b, c: c,
    "0            (Maj~0)": lambda a, b, c: 0,
}

def bias_exhaustive(true_fn, approx_fn):
    """Agreement fraction over all 2^k single-bit input combos.
    Ch/Maj are bitwise so the per-bit truth table (k=3 inputs) is exhaustive
    and identical across all 32 bit positions."""
    agree = total = 0
    for bits in itertools.product((0, 1), repeat=3):
        x, y, z = bits
        t = true_fn(x, y, z) & 1
        a = approx_fn(x, y, z) & 1
        agree += (t == a)
        total += 1
    return agree / total

# ----------------------------------------------------------------------------
# Determinism / avalanche measurement.
#   For a fixed input difference (1-bit, on a given register/bit) we run R
#   rounds from MANY random bases with random schedule words, and for each
#   of the 256 output-difference bits we record whether it is CONSTANT across
#   all bases (deterministic) or varies. A fully GF(2)-affine round makes the
#   output difference a pure linear function of the input difference => every
#   output-diff bit is deterministic (100%).
#   We report:
#     det_frac  : fraction of 256 output-diff bits constant across bases
#     aval_hw   : mean Hamming weight of the output difference (diffusion)
# ----------------------------------------------------------------------------
def measure(R, Ksamp, seed, diff_reg, diff_off, **kw):
    rnd = random.Random(seed)
    # Use a SHARED schedule per base-sample so the only varying thing across
    # bases is the base state; that is what determinism is about: does the
    # output diff depend on the base? In the affine case it cannot.
    # To be conservative we randomise the schedule per sample too, but the
    # diff is injected only in the state, and W is identical for both members
    # of a pair, so W cancels in the linear case.
    diff_seen = [set() for _ in range(256)]   # observed values of each diff bit
    hw_acc = 0.0
    W = [rnd.getrandbits(32) for _ in range(R)]
    for _ in range(Ksamp):
        s1 = tuple(rnd.getrandbits(32) for _ in range(8))
        s2 = list(s1); s2[diff_reg] ^= (1 << diff_off); s2 = tuple(s2)
        a, b = s1, s2
        for r in range(R):
            a = round_fn(a, W[r], KCONST[r], **kw)
            b = round_fn(b, W[r], KCONST[r], **kw)
        d = [x ^ y for x, y in zip(a, b)]
        hw_acc += sum(hw(x) for x in d)
        for reg in range(8):
            for off in range(32):
                bit = (d[reg] >> off) & 1
                diff_seen[reg * 32 + off].add(bit)
    det = sum(1 for s in diff_seen if len(s) == 1)
    return det / 256.0, hw_acc / Ksamp

def measure_avg_over_input_bits(R, Ksamp, seed, input_bits, **kw):
    """Average determinism & avalanche over a set of input-diff positions."""
    dets = []; hws = []
    for i, (reg, off) in enumerate(input_bits):
        det, av = measure(R, Ksamp, seed + i, reg, off, **kw)
        dets.append(det); hws.append(av)
    return sum(dets) / len(dets), sum(hws) / len(hws)


print("=" * 72)
print("TWIST 9 — linear distance of SHA-256")
print("=" * 72)

# ----------------------------------------------------------------------------
# PART 1 — bias of each linear approximation of Ch and Maj
# ----------------------------------------------------------------------------
print("\n[PART 1] Best linear (affine GF(2)) approximations — exhaustive bias")
print("  Ch(e,f,g) candidates (agreement over all 8 input triples):")
ch_biases = []
for name, fn in CH_APPROX.items():
    b = bias_exhaustive(Ch, fn)
    ch_biases.append((b, name, fn))
    print(f"    {name:24s}: agree {b:.3f}  (|bias-0.5| = {abs(b-0.5):.3f})")
ch_biases.sort(key=lambda t: -abs(t[0] - 0.5))
best_ch = ch_biases[0]
print(f"  -> best Ch approx: {best_ch[1].strip()}  agree {best_ch[0]:.3f}")

print("  Maj(a,b,c) candidates:")
maj_biases = []
for name, fn in MAJ_APPROX.items():
    b = bias_exhaustive(Maj, fn)
    maj_biases.append((b, name, fn))
    print(f"    {name:24s}: agree {b:.3f}  (|bias-0.5| = {abs(b-0.5):.3f})")
maj_biases.sort(key=lambda t: -abs(t[0] - 0.5))
best_maj = maj_biases[0]
# agree 0.25 means the affine COMPLEMENT (e.g. NXOR = a^b^c^1) agrees 0.75;
# the affine offset is a constant and cancels in any difference, so the
# linear *part* a^b^c is the relevant approximation either way.
eff = max(best_maj[0], 1 - best_maj[0])
print(f"  -> best Maj approx: {best_maj[1].strip()}  "
      f"(linear part agrees {eff:.3f} up to affine offset)")

CH_LIN = best_ch[2]
MAJ_LIN = best_maj[2]

# ----------------------------------------------------------------------------
# PART 2 — fully linearized variant: determinism should hit 100%
# ----------------------------------------------------------------------------
print("\n[PART 2] Fully-linearized variant (Ch/Maj->linear AND adds->XOR)")
# sweep input bits across all 8 registers, a handful of offsets, average
INPUT_BITS = [(reg, off) for reg in range(8) for off in (0, 7, 15, 23, 31)]
R_LIST = [2, 3, 4, 6, 8]
print("  R  | full SHA det%  hw   | fully-linear det%  hw")
for R in R_LIST:
    dF, hF = measure_avg_over_input_bits(R, 200, 900 + R, INPUT_BITS)
    dL, hL = measure_avg_over_input_bits(R, 200, 900 + R, INPUT_BITS,
                                         ch=CH_LIN, mj=MAJ_LIN, lin_add=True)
    print(f"  {R:2d} |   {100*dF:5.1f}%   {hF:5.1f} |     {100*dL:5.1f}%   {hL:5.1f}")
print("  (fully-linear det% must be 100.0 — confirms GF(2)-affine: a fixed")
print("   input difference forces a fixed output difference, base-independent)")

# ----------------------------------------------------------------------------
# PART 3 — graded linearization: nonlinearity budget partition
#   Levels (each removes one nonlinearity source, keeping the others intact):
#     L0  full SHA-256
#     L1a linearize Ch only  (Maj nonlinear, carries kept)
#     L1b linearize Maj only (Ch nonlinear, carries kept)
#     L2  linearize both Ch and Maj (carries kept)
#     L3  L2 + adds->XOR (fully linear)
#   Plus the Twist-5 reference points:
#     C   carries removed only (adds->XOR, Ch/Maj nonlinear)
#     B   Ch=Maj=0  (booleans removed, carries kept)
# ----------------------------------------------------------------------------
print("\n[PART 3] Graded linearization — determinism gained per level (avg over input bits)")
LEVELS = [
    ("L0 full SHA-256", dict()),
    ("L1a Ch linear only", dict(ch=CH_LIN)),
    ("L1b Maj linear only", dict(mj=MAJ_LIN)),
    ("L2  Ch+Maj linear", dict(ch=CH_LIN, mj=MAJ_LIN)),
    ("C   carries->XOR only", dict(lin_add=True)),
    ("B   Ch=Maj=0", dict(ch=lambda e, f, g: 0, mj=lambda a, b, c: 0)),
    ("L3  FULLY LINEAR", dict(ch=CH_LIN, mj=MAJ_LIN, lin_add=True)),
]
R_GRADE = 4
print(f"  (R={R_GRADE}, {len(INPUT_BITS)} input-diff positions, 200 bases each)")
print("  level                   | det%   | aval-hw | det-gain vs L0")
base_det = base_hw = None
results = {}
for name, kw in LEVELS:
    det, av = measure_avg_over_input_bits(R_GRADE, 200, 7000, INPUT_BITS, **kw)
    results[name] = (det, av)
    if base_det is None:
        base_det, base_hw = det, av
    print(f"  {name:23s} |  {100*det:5.1f} |  {av:5.1f}  |  {100*(det-base_det):+5.1f} pts")

# Partition the nonlinearity contribution by determinism gained.
l0 = results["L0 full SHA-256"][0]
ch_only = results["L1a Ch linear only"][0] - l0
maj_only = results["L1b Maj linear only"][0] - l0
both = results["L2  Ch+Maj linear"][0] - l0
carries = results["C   carries->XOR only"][0] - l0
print("\n  Nonlinearity-budget partition (determinism pts unlocked, R=4):")
print(f"    linearize Ch  -> +{100*ch_only:.1f} pts")
print(f"    linearize Maj -> +{100*maj_only:.1f} pts")
print(f"    linearize both Ch+Maj -> +{100*both:.1f} pts")
print(f"    remove carries (adds->XOR) -> +{100*carries:.1f} pts")
contributors = sorted(
    [("Ch", ch_only), ("Maj", maj_only), ("carries", carries)],
    key=lambda t: -t[1])
print(f"    biggest single contributor: {contributors[0][0]}  "
      f"(then {contributors[1][0]}, {contributors[2][0]})")

# ----------------------------------------------------------------------------
# PART 4 — how many rounds become "trivial" as nonlinearity is removed?
#   A round is "trivially collidable" if a 1-bit input diff can be cancelled
#   by a 1-word schedule diff with certainty. Proxy: measure determinism vs R
#   for each level; the fully-linear hash is trivial at ALL R (det=100%).
#   For the partial levels, report the largest R at which det stays high
#   (>=50%): the number of rounds that remain near-linear.
# ----------------------------------------------------------------------------
print("\n[PART 4] Rounds-to-trivial: determinism vs R per linearization level")
LEV4 = [
    ("full", dict()),
    ("Ch-lin", dict(ch=CH_LIN)),
    ("Maj-lin", dict(mj=MAJ_LIN)),
    ("both-lin", dict(ch=CH_LIN, mj=MAJ_LIN)),
    ("fully-lin", dict(ch=CH_LIN, mj=MAJ_LIN, lin_add=True)),
]
RS = [1, 2, 3, 4, 5, 6, 8, 12, 16]
hdr = "  level     | " + " ".join(f"R{r:<2d}" for r in RS)
print(hdr)
for name, kw in LEV4:
    row = []
    for R in RS:
        det, _ = measure_avg_over_input_bits(R, 120, 5000 + R, INPUT_BITS, **kw)
        row.append(f"{100*det:4.0f}")
    print(f"  {name:9s} | " + " ".join(f"{v:>3}" for v in row))
print("  (det% = fraction of 256 output-diff bits constant across bases;")
print("   ~100 => round behaves linearly/trivially for that input diff)")

print("\n" + "=" * 72)
print("DONE.")
print("=" * 72)
