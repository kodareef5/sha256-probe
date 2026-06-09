#!/usr/bin/env python3
"""Twist 7: map the CONTROLLABILITY SPECTRUM of SHA-256 (the attack-relevant dual of diffusion).

Prior twists found that passive diffusion-softness is NOT the attack-relevant quantity; what
matters is CONTROL LEVERAGE — how well a chosen low-weight MESSAGE difference dW can cancel the
state-difference trail round after round. Twist 3 found this leverage is ~2x stronger FORWARD
(W enters T1, driving both new registers a',e') than BACKWARD (W only enters h's recovery), and
that register h is the leverage point in both regimes.

Here we generalize: seed a 1-bit difference in each register R_seed (8) in each direction (2),
run a greedy local-collision that injects the best low-weight dW each round to MINIMIZE the
resulting state-diff Hamming weight, and count how many LEADING rounds stay <= a threshold T.
This produces an 8x2 controllability spectrum, which we cross-reference against the Twist 4
diffusion spectrum (b slowest fwd, e fastest fwd) to hunt for the holy grail: a register that is
BOTH slow-diffusing AND highly controllable.

Deterministic (seeded RNG). Full N=32 words. Imports verified lib/sha256 primitives.
Reproduce: python3 headline_hunt/twisted_probes/twist7_controllability.py
"""
import sys, random
sys.path.insert(0, "lib")
from sha256 import Sigma0, Sigma1, sigma0, sigma1, Ch, Maj, K as KCONST

M = 0xffffffff
NAMES = "a b c d e f g h".split()
THRESHOLDS = (4, 8, 16)


def hw(x):
    return bin(x & M).count("1")


def shw(s):
    return sum(hw(x) for x in s)


# --- verified round functions (copied exactly from twist3_exploit.py / three_twists_v2.py) ---
def fwd(s, w, k):
    a, b, c, d, e, f, g, h = s
    T1 = (h + Sigma1(e) + Ch(e, f, g) + k + w) & M
    T2 = (Sigma0(a) + Maj(a, b, c)) & M
    return ((T1 + T2) & M, a, b, c, (d + T1) & M, e, f, g)


def inv(s, w, k):
    a2, b2, c2, d2, e2, f2, g2, h2 = s
    a = b2; b = c2; c = d2; e = f2; f = g2; g = h2
    T2 = (Sigma0(a) + Maj(a, b, c)) & M
    T1 = (a2 - T2) & M
    d = (e2 - T1) & M
    h = (T1 - Sigma1(e) - Ch(e, f, g) - k - w) & M
    return (a, b, c, d, e, f, g, h)


# --- candidate message-difference sets ---
SINGLE = [0] + [1 << i for i in range(32)]  # {0} + all 32 single-bit flips


def make_twobit(rng, n_extra):
    """{0} + all single-bit + a deterministic sample of n_extra 2-bit flips."""
    cands = list(SINGLE)
    seen = set()
    while len(cands) - 33 < n_extra:
        i = rng.randrange(32); j = rng.randrange(32)
        if i == j:
            continue
        v = (1 << i) | (1 << j)
        if v in seen:
            continue
        seen.add(v); cands.append(v)
    return cands


def greedy_trail(direction, seed_reg, R, Ksamp, seed, cands):
    """Mean leading-rounds-kept-<=T for a 1-bit diff seeded in seed_reg, greedily controlled
    by injecting the best dW from `cands` each round. Returns {T: mean_rounds}."""
    rnd = random.Random(seed)
    sustained = {T: 0.0 for T in THRESHOLDS}
    for _ in range(Ksamp):
        s1 = tuple(rnd.getrandbits(32) for _ in range(8))
        s2 = list(s1)
        s2[seed_reg] ^= 1 << rnd.randrange(32)
        s2 = tuple(s2)
        ks = [rnd.getrandbits(32) for _ in range(R)]
        ws = [rnd.getrandbits(32) for _ in range(R)]
        cur1, cur2 = s1, s2
        traj = []
        for r in range(R):
            w1 = ws[r]
            # kernel convention matches Twist 3: fwd uses K[r]; bwd inverts a fwd run using
            # kernels K[0..R-1], so the r-th inverse step consumes K[R-1-r].
            k = ks[r] if direction == "fwd" else KCONST[(R - 1 - r) % 64]
            step = fwd if direction == "fwd" else inv
            best = None
            for dW in cands:
                n1 = step(cur1, w1, k)
                n2 = step(cur2, (w1 ^ dW) & M, k)
                d = tuple((x ^ y) & M for x, y in zip(n1, n2))
                hwt = shw(d)
                if best is None or hwt < best[0]:
                    best = (hwt, n1, n2)
            cur1, cur2 = best[1], best[2]
            traj.append(best[0])
        for T in THRESHOLDS:
            cnt = 0
            for hwt in traj:
                if hwt <= T:
                    cnt += 1
                else:
                    break
            sustained[T] += cnt
    return {T: sustained[T] / Ksamp for T in THRESHOLDS}


# === diffusion spectrum (re-derive Twist 4, both directions) so cross-ref is self-contained ===
def diffusion_by_register(direction, R, Ksamp, seed):
    """Mean avalanche HW at round R for a 1-bit diff seeded in each register (no control)."""
    rnd = random.Random(seed)
    acc = [0.0] * 8
    for _ in range(Ksamp):
        for reg in range(8):
            s1 = tuple(rnd.getrandbits(32) for _ in range(8))
            s2 = list(s1)
            s2[reg] ^= 1 << rnd.randrange(32)
            s2 = tuple(s2)
            ws = [rnd.getrandbits(32) for _ in range(R)]
            ks = [rnd.getrandbits(32) for _ in range(R)]
            a, b = s1, s2
            for r in range(R):
                k = ks[r] if direction == "fwd" else KCONST[(R - 1 - r) % 64]
                step = fwd if direction == "fwd" else inv
                a = step(a, ws[r], k); b = step(b, ws[r], k)
            acc[reg] += sum(hw(x ^ y) for x, y in zip(a, b))
    return [v / Ksamp for v in acc]


def main():
    R = 12
    K_CTRL = 600     # samples per controllability cell
    K_DIFF = 1500    # samples per diffusion cell
    SEED = 20260609

    # ---- 1. CONTROLLABILITY SPECTRUM (single-bit dW): 8 registers x 2 directions ----
    print("=" * 78)
    print("TWIST 7: CONTROLLABILITY SPECTRUM  (greedy single-bit-dW local collision, R=%d, K=%d)" % (R, K_CTRL))
    print("=" * 78)
    print("Mean leading rounds the controlled trail stays HW <= T (higher = more controllable):\n")

    ctrl = {"fwd": {}, "bwd": {}}
    for direction in ("fwd", "bwd"):
        for reg in range(8):
            # distinct deterministic seed per cell
            cell_seed = SEED + (0 if direction == "fwd" else 1000) + reg
            ctrl[direction][reg] = greedy_trail(direction, reg, R, K_CTRL, cell_seed, SINGLE)

    for direction in ("fwd", "bwd"):
        print(f"  [{direction.upper()}]  seed-reg | T<=4   T<=8   T<=16")
        for reg in range(8):
            r = ctrl[direction][reg]
            print(f"           {NAMES[reg]:>6}  | {r[4]:5.2f}  {r[8]:5.2f}  {r[16]:5.2f}")
        # standouts on the T<=8 column
        best = max(range(8), key=lambda x: ctrl[direction][x][8])
        worst = min(range(8), key=lambda x: ctrl[direction][x][8])
        print(f"    -> most controllable {direction}: {NAMES[best]} ({ctrl[direction][best][8]:.2f} rounds @T<=8); "
              f"least: {NAMES[worst]} ({ctrl[direction][worst][8]:.2f})\n")

    # ---- 2. CROSS-REFERENCE vs DIFFUSION SPECTRUM ----
    print("=" * 78)
    print("CROSS-REF: diffusion vs controllability per register (hunting the holy grail)")
    print("=" * 78)
    diff = {
        "fwd": diffusion_by_register("fwd", 4, K_DIFF, SEED + 7),
        "bwd": diffusion_by_register("bwd", 4, K_DIFF, SEED + 8),
    }
    for direction in ("fwd", "bwd"):
        print(f"\n  [{direction.upper()}]  reg | diffuse HW@R4 | control rounds@T<=8 | slow-diff? high-ctrl?")
        d = diff[direction]
        c = {reg: ctrl[direction][reg][8] for reg in range(8)}
        dmed = sorted(d)[len(d) // 2]
        cmed = sorted(c.values())[4]
        for reg in range(8):
            slow = d[reg] <= dmed       # at-or-below-median diffusion = slow
            high = c[reg] >= cmed       # at-or-above-median control = highly controllable
            tag = ""
            if slow and high:
                tag = "  <== SLOW-DIFF & HIGH-CTRL (holy grail candidate)"
            elif slow:
                tag = "  (slow-diff only)"
            elif high:
                tag = "  (high-ctrl only)"
            print(f"        {NAMES[reg]:>3} | {d[reg]:11.1f}  | {c[reg]:17.2f}  |{tag}")
        # Pearson correlation between diffusion and controllability across registers
        import statistics
        xs = [d[reg] for reg in range(8)]
        ys = [c[reg] for reg in range(8)]
        mx = statistics.mean(xs); my = statistics.mean(ys)
        cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
        sx = (sum((x - mx) ** 2 for x in xs)) ** 0.5
        sy = (sum((y - my) ** 2 for y in ys)) ** 0.5
        corr = cov / (sx * sy) if sx and sy else float("nan")
        print(f"    Pearson corr(diffusion, controllability) over 8 registers: {corr:+.2f}")

    # ---- 3. RICHER CONTROL: does 2-bit dW materially extend the trail? ----
    print("\n" + "=" * 78)
    print("RICHER CONTROL: single-bit dW vs single+2-bit dW (forward, on best register)")
    print("=" * 78)
    rng2 = random.Random(SEED + 99)
    cands2 = make_twobit(rng2, 200)  # +200 sampled 2-bit flips on top of {0}+single
    print(f"  candidate set sizes: single={len(SINGLE)}, single+2bit={len(cands2)}")
    # test on register h (the leverage point) and the forward-best register, both directions
    test_regs = sorted({7, max(range(8), key=lambda x: ctrl["fwd"][x][8]),
                        max(range(8), key=lambda x: ctrl["bwd"][x][8])})
    print(f"\n  {'dir':>4} {'reg':>4} | {'1bit T<=8':>10} {'2bit T<=8':>10}  delta | {'1bit T<=16':>11} {'2bit T<=16':>11}  delta")
    for direction in ("fwd", "bwd"):
        for reg in test_regs:
            cell_seed = SEED + (0 if direction == "fwd" else 1000) + reg  # SAME seed as part 1 -> paired
            one = ctrl[direction][reg]
            two = greedy_trail(direction, reg, R, K_CTRL, cell_seed, cands2)
            d8 = two[8] - one[8]; d16 = two[16] - one[16]
            print(f"  {direction:>4} {NAMES[reg]:>4} | {one[8]:10.2f} {two[8]:10.2f}  {d8:+5.2f} | "
                  f"{one[16]:11.2f} {two[16]:11.2f}  {d16:+5.2f}")

    print("\nDone. See 20260609_twist7_controllability.md for the memo.")


if __name__ == "__main__":
    main()
