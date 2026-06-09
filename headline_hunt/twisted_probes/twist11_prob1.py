#!/usr/bin/env python3
"""
Twist 11 — Map the probability-1 (deterministic) differential structure of SHA-256.

For an input STATE difference (with W common across the pair), the output state
difference is generally probabilistic: it depends on absolute base values via
carries (modular add) and via Ch/Maj (data-dependent booleans). This probe
isolates the parts that are DETERMINISTIC: output-difference bits that are
CONSTANT (prob-1) across all random bases. That prob-1 set is the "free"
differential structure an attacker gets with no probabilistic conditions.

Deterministic experiment: all randomness is seeded. Reuses the verified round
function (fwd) exactly as specified in the task / fresh_batch.py.

    from sha256 import Sigma0,Sigma1,Ch,Maj,K  (lib/)
"""
import sys, random
sys.path.insert(0, "lib")
sys.path.insert(0, "../../lib")
from sha256 import Sigma0, Sigma1, Ch, Maj, K as KCONST

M = 0xffffffff
names = "a b c d e f g h".split()


def fwd(s, w, k):
    a, b, c, d, e, f, g, h = s
    T1 = (h + Sigma1(e) + Ch(e, f, g) + k + w) & M
    T2 = (Sigma0(a) + Maj(a, b, c)) & M
    return ((T1 + T2) & M, a, b, c, (d + T1) & M, e, f, g)


def run_pair(s1, delta, W, R):
    """Run R rounds on s1 and s1^delta with common schedule W; return final state diff (8 words)."""
    s2 = tuple((x ^ d) & M for x, d in zip(s1, delta))
    a, b = s1, s2
    for r in range(R):
        a = fwd(a, W[r], KCONST[r])
        b = fwd(b, W[r], KCONST[r])
    return tuple((x ^ y) & M for x, y in zip(a, b))


def determinism_profile(delta, R, Ksamp, seed):
    """
    Over Ksamp random (base, W) draws, accumulate per-output-bit:
      - how often each of the 256 output-diff bits is set.
    A bit is prob-1 if it is ALWAYS 0 or ALWAYS 1 across all samples.
    Returns (prob1_count, const0_count, const1_count, per_bit_ratio[256]).
    256 output bits = 8 registers x 32 bits.
    """
    rnd = random.Random(seed)
    set_count = [0] * 256
    for _ in range(Ksamp):
        s1 = tuple(rnd.getrandbits(32) for _ in range(8))
        W = [rnd.getrandbits(32) for _ in range(R)]
        od = run_pair(s1, delta, W, R)
        for reg in range(8):
            w = od[reg]
            base = reg * 32
            while w:
                lo = w & (-w)
                set_count[base + lo.bit_length() - 1] += 1
                w ^= lo
    const1 = sum(1 for c in set_count if c == Ksamp)
    const0 = sum(1 for c in set_count if c == 0)
    prob1 = const0 + const1
    ratios = [c / Ksamp for c in set_count]
    return prob1, const0, const1, ratios, set_count


def single_bit_delta(reg, off):
    d = [0] * 8
    d[reg] = (1 << off)
    return tuple(d)


# ============================================================================
# PART 1 — Per-output-bit determinism, all 256 single-bit input diffs, R=1,2,3
# ============================================================================
print("=" * 74)
print("PART 1: prob-1 (deterministic) output-diff bits per single-bit input diff")
print("=" * 74)
KS = 2000
results = {}  # (R) -> list of (prob1, reg, off)
for R in (1, 2, 3):
    rows = []
    for bit in range(256):
        reg, off = divmod(bit, 32)
        delta = single_bit_delta(reg, off)
        p1, c0, c1, _, _ = determinism_profile(delta, R, KS, seed=1000 + bit)
        rows.append((p1, c1, reg, off))
    results[R] = rows
    avg = sum(r[0] for r in rows) / len(rows)
    # const1 means a deterministically-FLIPPED output bit (the interesting "free" structure)
    avg_c1 = sum(r[1] for r in rows) / len(rows)
    print(f"\n--- R={R} ---  (256 output bits total per input diff)")
    print(f"  mean prob-1 output bits over all 256 input diffs: {avg:6.1f} / 256"
          f"   ({100*avg/256:4.1f}% deterministic)")
    print(f"  mean *const-1* (deterministically flipped) bits : {avg_c1:6.2f}")
    rows_sorted = sorted(rows, reverse=True)
    print(f"  most-deterministic input diffs (highest prob-1 output count):")
    for p1, c1, reg, off in rows_sorted[:6]:
        print(f"     {names[reg]}[{off:2d}] : prob-1={p1:3d}/256  (const-1 flipped={c1})")
    print(f"  least-deterministic input diffs:")
    for p1, c1, reg, off in rows_sorted[-4:]:
        print(f"     {names[reg]}[{off:2d}] : prob-1={p1:3d}/256  (const-1 flipped={c1})")


# ============================================================================
# PART 2 — Determinism-vs-bit-position profile; the MSB channel
# ============================================================================
print("\n" + "=" * 74)
print("PART 2: determinism vs bit position (the MSB channel)")
print("=" * 74)
# For each register, build prob-1(output) as a function of input bit offset 0..31, R=1.
print("\nprob-1 output-diff bits (/256) at R=1, by input bit position (per register):")
R = 1
prof = {}  # reg -> [p1 for off in 0..31]
for reg in range(8):
    row = []
    for off in range(32):
        delta = single_bit_delta(reg, off)
        p1, c0, c1, _, _ = determinism_profile(delta, R, KS, seed=2000 + reg * 32 + off)
        row.append(p1)
    prof[reg] = row

# Compare MSB (off=31) vs mid (off=15) vs low (off=0) averaged over registers
def avg_at(off):
    return sum(prof[reg][off] for reg in range(8)) / 8.0
print(f"  MSB  (bit 31) mean prob-1 over 8 regs : {avg_at(31):6.1f} / 256")
print(f"  mid  (bit 15) mean prob-1 over 8 regs : {avg_at(15):6.1f} / 256")
print(f"  low  (bit  0) mean prob-1 over 8 regs : {avg_at(0):6.1f} / 256")

# Full per-register MSB vs non-MSB picture
print("\n  per-register: prob-1 at bit31 (MSB) vs mean over bits 0..30 (non-MSB):")
for reg in range(8):
    msb = prof[reg][31]
    nonmsb = sum(prof[reg][:31]) / 31.0
    print(f"     {names[reg]}: MSB={msb:3d}/256   non-MSB mean={nonmsb:6.1f}/256   "
          f"({'MSB more det.' if msb > nonmsb else 'no MSB edge'})")

# ----- Deterministic corridor: bit positions whose diff stays prob-1 across R -----
print("\n  Deterministic corridor — how many rounds does FULL output determinism survive?")
print("  (R at which prob-1 output count first drops below 256, per single-bit input diff)")
print("  Testing the slow registers' MSB and a control low bit:")
KS2 = 3000


def survives_full_det(delta, max_R, ks, seed0):
    """Largest R (1..max_R) for which output diff is FULLY deterministic (all 256 prob-1)."""
    last = 0
    for R in range(1, max_R + 1):
        p1, _, _, _, _ = determinism_profile(delta, R, ks, seed=seed0 + R)
        if p1 == 256:
            last = R
        else:
            break
    return last


probe_bits = [("a", 31), ("b", 31), ("c", 31), ("d", 31),
              ("e", 31), ("f", 31), ("g", 31), ("h", 31),
              ("b", 0), ("e", 0)]
for nm, off in probe_bits:
    reg = names.index(nm)
    delta = single_bit_delta(reg, off)
    last = survives_full_det(delta, 6, KS2, seed0=3000 + reg * 32 + off)
    # also report prob-1 count at R=1 and R=2 for context
    p1_1, _, c1_1, _, _ = determinism_profile(delta, 1, KS2, seed=9000 + reg * 32 + off)
    p1_2, _, c1_2, _, _ = determinism_profile(delta, 2, KS2, seed=9100 + reg * 32 + off)
    print(f"     {nm}[{off:2d}]: full-det survives through R={last}   "
          f"| R1 prob-1={p1_1:3d}/256 (flip={c1_1})  R2 prob-1={p1_2:3d}/256 (flip={c1_2})")


# ============================================================================
# PART 3 — Maximal prob-1 differential (single bit, MSB patterns, small combos)
# ============================================================================
print("\n" + "=" * 74)
print("PART 3: maximal prob-1 differential (most-deterministic 1-round output)")
print("=" * 74)
KS3 = 4000
candidates = {}

# (a) all single bits (R=1)
for bit in range(256):
    reg, off = divmod(bit, 32)
    candidates[f"{names[reg]}[{off}]"] = single_bit_delta(reg, off)

# (b) MSB patterns: all subsets of {a..h}[31] up to size 3, plus a few large ones
msb_regs = list(range(8))
import itertools
for k in (2, 3):
    for combo in itertools.combinations(msb_regs, k):
        d = [0] * 8
        for r in combo:
            d[r] = 0x80000000
        candidates["MSB{" + ",".join(names[r] for r in combo) + "}"] = tuple(d)
# all-8 MSB
candidates["MSB{all8}"] = tuple([0x80000000] * 8)

# (c) MSB-adjacent small combos on the slow register b
for d in (single_bit_delta(1, 31),):
    pass
candidates["b[31]+b[30]"] = (0, 0xC0000000, 0, 0, 0, 0, 0, 0)
candidates["b[31]+a[31]"] = (0x80000000, 0x80000000, 0, 0, 0, 0, 0, 0)

# Evaluate at R=1
scored = []
for nm, delta in candidates.items():
    p1, c0, c1, _, _ = determinism_profile(delta, 1, KS3, seed=hash(nm) & 0xffff)
    scored.append((p1, c1, nm, delta))
scored.sort(reverse=True)

print(f"\nMost-deterministic 1-round differentials (prob-1 output bits /256), Ksamp={KS3}:")
for p1, c1, nm, delta in scored[:12]:
    print(f"   {nm:16s}: prob-1={p1:3d}/256  (deterministically-flipped const-1={c1})")
print(f"\nLeast-deterministic:")
for p1, c1, nm, delta in scored[-5:]:
    print(f"   {nm:16s}: prob-1={p1:3d}/256  (flip={c1})")

# Take the top winner and measure how long its determinism survives across rounds
best_p1, best_c1, best_nm, best_delta = scored[0]
print(f"\nWinner: {best_nm}  (prob-1={best_p1}/256 at R=1)")
print("Determinism survival across rounds for the winner:")
for R in range(1, 8):
    p1, c0, c1, _, _ = determinism_profile(best_delta, R, KS3, seed=7000 + R)
    print(f"   R={R}: prob-1={p1:3d}/256   const-1(flipped)={c1:3d}   "
          f"({100*p1/256:4.1f}% deterministic)")

# Also report the longest FULL-determinism survival across the whole single-bit set
print("\nLongest FULL (256/256) output determinism survival, scan over single bits:")
best_surv = (0, None)
for bit in range(256):
    reg, off = divmod(bit, 32)
    delta = single_bit_delta(reg, off)
    last = survives_full_det(delta, 5, 2000, seed0=11000 + bit)
    if last > best_surv[0]:
        best_surv = (last, f"{names[reg]}[{off}]")
print(f"   best: {best_surv[1]} keeps ALL 256 output bits deterministic through R={best_surv[0]}")

print("\n[done]")
