#!/usr/bin/env python3
"""
Twist 8 — hunt for SHA-256's slowest-diffusing differential "eigen-mode".

We search the RICHER (multi-bit) input STATE-difference space for a delta
(256-bit, across the 8 registers a..h) that diffuses MINIMALLY (stays low
Hamming weight) over R rounds, averaged over random base states + messages.

Two complementary searches:
  (1) GREEDY / local hill-climb: start from the best single-bit (register-b
      high bits, per Twist 4); add/remove difference bits to REDUCE the
      R-round avalanche HW. Settle at a local minimum.
  (2) STRUCTURED candidates: differences aligned with SHA-256 structure —
      MSB-only patterns (XOR == modular at the top bit), b-confined
      differences, rotation-symmetric patterns, etc.

Honest framing (project lesson): slow diffusion != exploitable without
control leverage. We measure diffusion, not exploitability.

Deterministic: all randomness is seeded. Reuses lib/sha256 primitives.
"""
import sys, random
sys.path.insert(0, "lib")
from sha256 import Sigma0, Sigma1, Ch, Maj, K as KCONST

M = 0xffffffff
NAMES = "a b c d e f g h".split()

def hw(x):
    return bin(x & M).count("1")

# --- verified round function (exactly as headline_hunt/twisted_probes/fresh_batch.py) ---
def fwd(s, w, k):
    a, b, c, d, e, f, g, h = s
    T1 = (h + Sigma1(e) + Ch(e, f, g) + k + w) & M
    T2 = (Sigma0(a) + Maj(a, b, c)) & M
    return ((T1 + T2) & M, a, b, c, (d + T1) & M, e, f, g)

# ------------------------------------------------------------------
# Difference representation: delta is an 8-tuple of 32-bit words (XOR mask).
# We evaluate average R-round avalanche HW for state-difference delta,
# applying it via XOR to a random base state, over random messages.
# ------------------------------------------------------------------
def avalanche(delta, R=4, Ksamp=2000, seed=0):
    """Mean total Hamming weight of the output state difference after R rounds."""
    rnd = random.Random(seed)
    acc = 0.0
    for _ in range(Ksamp):
        s1 = tuple(rnd.getrandbits(32) for _ in range(8))
        s2 = tuple((x ^ d) & M for x, d in zip(s1, delta))
        W = [rnd.getrandbits(32) for _ in range(R)]
        a, b = s1, s2
        for r in range(R):
            a = fwd(a, W[r], KCONST[r])
            b = fwd(b, W[r], KCONST[r])
        acc += sum(hw(x ^ y) for x, y in zip(a, b))
    return acc / Ksamp

def delta_hw(delta):
    return sum(hw(d) for d in delta)

def delta_str(delta):
    parts = []
    for i, d in enumerate(delta):
        if d:
            bits = [str(b) for b in range(32) if (d >> b) & 1]
            parts.append(f"{NAMES[i]}={'|'.join(bits)}")
    return "  ".join(parts) if parts else "(zero)"

def bit_to_delta(reg, off):
    d = [0] * 8
    d[reg] = (1 << off)
    return tuple(d)

def flip_bit(delta, reg, off):
    d = list(delta)
    d[reg] ^= (1 << off)
    return tuple(d)

# ------------------------------------------------------------------
# Establish the single-bit baseline (best/slowest single-bit input diff).
# Per Twist 4: register-b high bits diffuse slowest. We confirm here over a
# focused scan so the baseline number is internally consistent with this run.
# ------------------------------------------------------------------
def scan_single_bits(R, Ksamp, seed):
    rows = []
    for reg in range(8):
        for off in range(32):
            d = bit_to_delta(reg, off)
            rows.append((avalanche(d, R=R, Ksamp=Ksamp, seed=seed), reg, off))
    rows.sort()
    return rows  # ascending: slowest first

# ------------------------------------------------------------------
# (1) Greedy hill-climb in difference space.
# At each step, evaluate every single-bit flip (add or remove a diff bit)
# and take the one that most reduces the avalanche HW. Stop at local min.
# To keep it deterministic and bounded, we cap iterations and re-evaluate
# the incumbent with a FIXED seed (so the landscape is stable per call).
# ------------------------------------------------------------------
def hill_climb(start_delta, R, Ksamp, seed, max_iters=40, verbose=False):
    cur = start_delta
    cur_av = avalanche(cur, R=R, Ksamp=Ksamp, seed=seed)
    history = [(cur_av, delta_hw(cur))]
    for it in range(max_iters):
        best_av = cur_av
        best_move = None
        for reg in range(8):
            for off in range(32):
                cand = flip_bit(cur, reg, off)
                # forbid the all-zero difference (trivial, av==0)
                if delta_hw(cand) == 0:
                    continue
                av = avalanche(cand, R=R, Ksamp=Ksamp, seed=seed)
                if av < best_av - 1e-9:
                    best_av = av
                    best_move = (reg, off)
        if best_move is None:
            break
        cur = flip_bit(cur, *best_move)
        cur_av = best_av
        history.append((cur_av, delta_hw(cur)))
        if verbose:
            print(f"    iter {it+1}: HW(delta)={delta_hw(cur):3d}  av={cur_av:6.1f}  +bit {NAMES[best_move[0]]}[{best_move[1]}]")
    return cur, cur_av, history

# ------------------------------------------------------------------
# (2) Structured candidate families.
# ------------------------------------------------------------------
def structured_families():
    fams = {}
    # MSB-only in each single register (XOR==modular add at top bit)
    for reg in range(8):
        fams[f"MSB-only {NAMES[reg]}[31]"] = bit_to_delta(reg, 31)
    # MSB on ALL registers
    fams["MSB-all (0x80000000 x8)"] = tuple([1 << 31] * 8)
    # MSB on the four 'message-path' registers a,b,c,d and on e,f,g,h
    fams["MSB abcd"] = tuple([1 << 31] * 4 + [0] * 4)
    fams["MSB efgh"] = tuple([0] * 4 + [1 << 31] * 4)
    # b-confined patterns (Twist-4 said b high bits slowest)
    fams["b high nibble (b[28..31])"] = bit_to_delta(1, 28)[:1] and tuple(
        [0, sum(1 << k for k in range(28, 32)), 0, 0, 0, 0, 0, 0])
    fams["b top byte (b[24..31])"] = tuple([0, sum(1 << k for k in range(24, 32)), 0, 0, 0, 0, 0, 0])
    fams["b all-ones (0xffffffff)"] = tuple([0, M, 0, 0, 0, 0, 0, 0])
    fams["b alt 0x55555555"] = tuple([0, 0x55555555, 0, 0, 0, 0, 0, 0])
    fams["b two-high b[30],b[31]"] = flip_bit(bit_to_delta(1, 31), 1, 30)
    # rotation-symmetric on b: bits at the Sigma0 rotation offsets {2,13,22}
    fams["b rot-sym Sig0 {2,13,22}"] = tuple([0, (1 << 2) | (1 << 13) | (1 << 22), 0, 0, 0, 0, 0, 0])
    # e rot-sym at Sigma1 offsets {6,11,25} (e feeds Sigma1/Ch)
    fams["e rot-sym Sig1 {6,11,25}"] = tuple([0, 0, 0, 0, (1 << 6) | (1 << 11) | (1 << 25), 0, 0, 0])
    # paired high bits across slow registers (b and c high)
    fams["b[31]+c[31]"] = flip_bit(bit_to_delta(1, 31), 2, 31)
    fams["b[31]+a[31]"] = flip_bit(bit_to_delta(1, 31), 0, 31)
    return fams

# ==================================================================
def run_for_R(R, scan_ksamp, climb_ksamp, fam_ksamp, seed_base):
    print(f"\n{'='*64}\n=== TWIST 8 @ R={R} ===\n{'='*64}")

    # --- baseline single-bit scan ---
    sb = scan_single_bits(R, scan_ksamp, seed=seed_base + 1)
    print(f"\n[single-bit baseline] slowest-diffusing single-bit input diffs:")
    for av, reg, off in sb[:6]:
        print(f"    {NAMES[reg]}[{off:2d}]: av={av:6.1f}")
    print(f"  fastest single-bit: {NAMES[sb[-1][1]]}[{sb[-1][2]}] av={sb[-1][0]:.1f}"
          f"   (spread {sb[-1][0]/sb[0][0]:.2f}x)")
    best_sb_av, best_sb_reg, best_sb_off = sb[0]
    best_sb = bit_to_delta(best_sb_reg, best_sb_off)
    print(f"  >> best single-bit baseline: {NAMES[best_sb_reg]}[{best_sb_off}]  av={best_sb_av:.1f}  (HW=1)")

    # --- (1) greedy hill-climb from best single bit ---
    print(f"\n[search 1: greedy hill-climb] start = best single-bit "
          f"{NAMES[best_sb_reg]}[{best_sb_off}]")
    hc_delta, hc_av, hist = hill_climb(best_sb, R, climb_ksamp, seed=seed_base + 2, verbose=True)
    print(f"  local-min difference: HW={delta_hw(hc_delta)}  av={hc_av:.1f}")
    print(f"    bits: {delta_str(hc_delta)}")
    # also climb from a couple of other low single-bit starts to check robustness
    alt_starts = [bit_to_delta(r, o) for (_, r, o) in sb[1:3]]
    alt_results = []
    for st in alt_starts:
        d, a, _ = hill_climb(st, R, climb_ksamp, seed=seed_base + 2, max_iters=40)
        alt_results.append((a, d))
    alt_results.sort()
    best_climb_av, best_climb_delta = min([(hc_av, hc_delta)] + alt_results)

    # --- (2) structured families ---
    print(f"\n[search 2: structured families]")
    fam = structured_families()
    fam_rows = []
    for nm, d in fam.items():
        av = avalanche(d, R=R, Ksamp=fam_ksamp, seed=seed_base + 3)
        fam_rows.append((av, delta_hw(d), nm, d))
    fam_rows.sort()
    for av, h, nm, d in fam_rows:
        marker = " <== slowest structured" if (av, h, nm, d) == fam_rows[0] else ""
        print(f"    {nm:30s} HW={h:2d}  av={av:6.1f}{marker}")
    best_fam_av, best_fam_hw, best_fam_nm, best_fam_delta = fam_rows[0]

    # --- compare the three on a COMMON fresh seed (fair head-to-head) ---
    cmp_seed = seed_base + 99
    cmp_ksamp = max(fam_ksamp, 4000)
    sb_cmp = avalanche(best_sb, R=R, Ksamp=cmp_ksamp, seed=cmp_seed)
    climb_cmp = avalanche(best_climb_delta, R=R, Ksamp=cmp_ksamp, seed=cmp_seed)
    fam_cmp = avalanche(best_fam_delta, R=R, Ksamp=cmp_ksamp, seed=cmp_seed)

    print(f"\n[head-to-head on common fresh seed, Ksamp={cmp_ksamp}]")
    print(f"    best single-bit  HW={delta_hw(best_sb):2d}  av={sb_cmp:6.1f}  (baseline)")
    print(f"    greedy local-min HW={delta_hw(best_climb_delta):2d}  av={climb_cmp:6.1f}"
          f"  ({climb_cmp/sb_cmp:.3f}x baseline)  bits: {delta_str(best_climb_delta)}")
    print(f"    best structured  HW={delta_hw(best_fam_delta):2d}  av={fam_cmp:6.1f}"
          f"  ({fam_cmp/sb_cmp:.3f}x baseline)  [{best_fam_nm}]")

    # normalized: avalanche PER difference bit (does richer buy slower *per bit*?)
    print(f"\n[normalized: avalanche per input-difference bit]")
    print(f"    single-bit : {sb_cmp/delta_hw(best_sb):6.1f} / bit")
    print(f"    local-min  : {climb_cmp/delta_hw(best_climb_delta):6.1f} / bit")
    print(f"    structured : {fam_cmp/delta_hw(best_fam_delta):6.1f} / bit")

    return {
        "R": R,
        "best_sb": (best_sb, sb_cmp),
        "best_climb": (best_climb_delta, climb_cmp),
        "best_fam": (best_fam_delta, best_fam_nm, fam_cmp),
        "cmp_ksamp": cmp_ksamp,
    }

if __name__ == "__main__":
    results = {}
    # R=4: heavier sampling (cheap). R=6: lighter Ksamp (more rounds).
    results[4] = run_for_R(4, scan_ksamp=1500, climb_ksamp=2000, fam_ksamp=4000, seed_base=400)
    results[6] = run_for_R(6, scan_ksamp=1200, climb_ksamp=1500, fam_ksamp=3000, seed_base=600)

    print(f"\n{'='*64}\n=== VERDICT SUMMARY ===\n{'='*64}")
    for R in (4, 6):
        r = results[R]
        sb_d, sb_av = r["best_sb"]
        cl_d, cl_av = r["best_climb"]
        fm_d, fm_nm, fm_av = r["best_fam"]
        best_av = min(sb_av, cl_av, fm_av)
        if best_av == sb_av:
            who = f"single-bit HW=1"
        elif best_av == cl_av:
            who = f"greedy local-min HW={delta_hw(cl_d)}"
        else:
            who = f"structured [{fm_nm}] HW={delta_hw(fm_d)}"
        print(f"  R={R}: slowest overall = {who}  av={best_av:.1f}"
              f"   (single-bit baseline av={sb_av:.1f}, ratio {best_av/sb_av:.3f})")
