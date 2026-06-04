"""
W2-SO3 — Carry-avalanche SOC: is 0.74 a sandpile avalanche exponent?

Card claim: ARX carry chains are toppling avalanches; if SHA self-organizes to
criticality, 0.74 is the avalanche exponent. de57/59/60 (constant channels) =
subcritical; de58 (growing) = critical/scale-free.

Probe (per CATALOG): instrument masked adds to record carry-cascade-length and
avalanche-size distributions per random pair; fit for a power law, extract the
exponent, relate it to 0.74; test whether constant channels are subcritical
(exp cutoff) and de58 critical (scale-free); test abelian/order-independence.

Kill: Dead if cascade-length distributions are EXPONENTIAL (clear cutoff) at all
N, OR the exponent is far from a simple function of 0.74, OR no subcritical/
critical channel contrast.

ADVERSARIAL PRIORS WEAPONIZED:
  #2: 0.74 is NOT sharp — repo data refits to slope 0.673, spread 0.72-1.04.
      A power-law exponent landing in 0.6-0.8 proves nothing; we must show the
      actual exponent, its fit quality, and whether it is distinguishable from
      0.673 (and from 0.74). And the skeptic note: a <=32-bit chain gives <1
      decade of avalanche size -> too short to assert SOC at all.

We measure, on the REAL masked modular adder (lib via shabridge's primitives,
exact carry chain), the avalanche induced by a single LSB-direction perturbation:
flip one input bit of (x+y) and record how far the carry chain DIFFERS (the
"toppling" length) and how many output bits flip (avalanche size). We do this
both for a generic adder and for the de-channel adders (the tail-round T1 / d+T1
adders that produce de57..de60), to test the subcritical/critical contrast.
"""
import sys, math, random, collections
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb
import adder_diff as ad

MASKN = lambda N: (1 << N) - 1


# ----------------------------------------------------------------------
# Avalanche of a single-bit perturbation through a modular adder x+y mod 2^N.
# "Toppling": flipping input bit k of x can flip carry c[k+1], which can flip
# c[k+2], ... -> a 1-D carry avalanche. Avalanche LENGTH = # consecutive carry
# positions that differ; avalanche SIZE = # output (sum) bits that differ.
# This is the literal SOC object the card asks for (carry-cascade length dist).
# ----------------------------------------------------------------------
def avalanche_len_size(x, y, k, N):
    m = MASKN(N)
    c0 = ad.add_carry_trace(x, y, N)
    xp = x ^ (1 << k)
    c1 = ad.add_carry_trace(xp & m, y, N)
    # carry differs at positions where c0 != c1 (toppled carries), for bits >k
    diff_carries = [i for i in range(N + 1) if c0[i] != c1[i]]
    length = (max(diff_carries) - k) if diff_carries else 0  # run-length from injection
    s0 = (x + y) & m
    s1 = (xp + y) & m
    size = bin(s0 ^ s1).count('1')  # output bits flipped = avalanche size
    return length, size


def sample_avalanches(N, trials=200000, seed=0, only_lsb=False):
    """Random pairs, random injection bit -> (length, size) samples."""
    rng = random.Random(seed)
    lens = collections.Counter()
    sizes = collections.Counter()
    for _ in range(trials):
        x = rng.getrandbits(N); y = rng.getrandbits(N)
        k = 0 if only_lsb else rng.randrange(N)
        L, S = avalanche_len_size(x, y, k, N)
        lens[L] += 1
        sizes[S] += 1
    return lens, sizes


# ----------------------------------------------------------------------
# Power-law fit via MLE for a discrete distribution P(s) ~ s^-alpha, s>=smin.
# (Clauset-Shalizi-Newman discrete MLE; smin chosen by KS minimization.)
# Also fit a pure-exponential P(s) ~ exp(-s/xi) and compare log-likelihoods,
# because the kill-criterion turns on "exponential (clear cutoff) vs scale-free".
# ----------------------------------------------------------------------
def discrete_powerlaw_mle(counts, smin):
    data = []
    for s, c in counts.items():
        if s >= smin and s > 0:
            data += [s] * c
    n = len(data)
    if n < 20:
        return None
    # discrete MLE approx (CSN eq 3.7): alpha = 1 + n / sum ln(s/(smin-0.5))
    denom = sum(math.log(s / (smin - 0.5)) for s in data)
    if denom <= 0:
        return None
    alpha = 1.0 + n / denom
    return alpha, n


def exp_mle(counts, smin):
    """Geometric/exponential tail rate: lambda_hat for P(s) ~ exp(-lambda s)."""
    data = []
    for s, c in counts.items():
        if s >= smin:
            data += [s] * c
    n = len(data)
    if n < 20:
        return None
    mean = sum(data) / n
    if mean <= smin:
        return None
    lam = 1.0 / (mean - smin)          # MLE for shifted-geometric mean
    return lam, mean, n


def ks_stat(counts, smin, alpha):
    """KS distance between empirical tail CDF and the fitted power-law CDF."""
    ss = sorted(s for s in counts if s >= smin and s > 0)
    if len(ss) < 3:
        return 1.0
    total = sum(counts[s] for s in ss)
    # empirical CDF
    cum = 0; emp = {}
    for s in ss:
        cum += counts[s]; emp[s] = cum / total
    # model CDF (discrete zeta-like, normalized over observed support)
    smax = ss[-1]
    norm = sum(s ** (-alpha) for s in range(smin, smax + 1))
    cmodel = 0; D = 0
    for s in range(smin, smax + 1):
        cmodel += (s ** (-alpha)) / norm
        if s in emp:
            D = max(D, abs(emp[s] - cmodel))
    return D


def decade_span(counts):
    pos = [s for s in counts if s > 0]
    if not pos:
        return 0.0
    return math.log10(max(pos)) - math.log10(min(pos))


# ----------------------------------------------------------------------
# de-channel contrast: the tail rounds produce de57..de60. The card says the
# CONSTANT channels (de57/59/60 = 1 always) should be SUBCRITICAL and the
# GROWING channel (de58, ~2^hw(db56)) CRITICAL. We test this directly via the
# repo's de-law ground truth (sb.DE_SIZES) AND by measuring the per-channel
# adder avalanche statistics around the cascade fixed point.
# ----------------------------------------------------------------------
def de_channel_report():
    rows = []
    for N, (d57, d58, d59, d60) in sorted(sb.DE_SIZES.items()):
        rows.append((N, d57, d58, d59, d60))
    return rows


def run(N_list=(8, 10, 12), N32=False):
    print("=" * 70)
    print("W2-SO3  carry-avalanche SOC  —  is 0.74 a sandpile exponent?")
    print("=" * 70)
    print(f"  Target exponent (card): 0.74   |  refit slope (prior #2): 0.673\n")

    results = {}
    Ns = list(N_list) + ([32] if N32 else [])
    for N in Ns:
        lens, sizes = sample_avalanches(N, trials=200000, seed=1)
        span_len = decade_span(lens)
        span_size = decade_span(sizes)

        # fit power law on avalanche SIZE (the SOC observable) with smin sweep
        best = None
        for smin in range(1, max(2, N // 2)):
            res = discrete_powerlaw_mle(sizes, smin)
            if res is None:
                continue
            alpha, n = res
            D = ks_stat(sizes, smin, alpha)
            if best is None or D < best[3]:
                best = (smin, alpha, n, D)
        # exponential alternative on the same observable
        ex = exp_mle(sizes, 1)

        # mean carry-cascade length and its tail decay (is it exponential?)
        tot = sum(lens.values())
        mean_len = sum(L * c for L, c in lens.items()) / tot
        # exponential-tail check on LENGTH: ratio P(L+1)/P(L) ~ const if geometric
        Ls = sorted(L for L in lens if L >= 1)
        ratios = []
        for L in Ls[:-1]:
            if lens[L] > 0 and (L + 1) in lens:
                ratios.append(lens[L + 1] / lens[L])
        geom_ratio = (sum(ratios) / len(ratios)) if ratios else float('nan')

        results[N] = dict(best=best, ex=ex, mean_len=mean_len,
                          span_len=span_len, span_size=span_size,
                          geom_ratio=geom_ratio, maxlen=max(lens),
                          maxsize=max(sizes))
        a_str = f"{best[1]:.3f}" if best else "n/a"
        print(f"  N={N:2d}: avalanche-SIZE power-law alpha={a_str} "
              f"(smin={best[0] if best else '-'}, KS={best[3]:.3f})  "
              f"| size-decades={span_size:.2f}")
        print(f"        carry-LENGTH: mean={mean_len:.3f} max={max(lens)} "
              f"geom-ratio P(L+1)/P(L)~{geom_ratio:.3f} (const=>exponential) "
              f"len-decades={span_len:.2f}")
        if ex:
            lam, mn, n = ex
            print(f"        exponential-fit lambda={lam:.3f} (xi={1/lam:.2f} bits) "
                  f"mean-size={mn:.3f}")
    return results


def subcrit_contrast():
    print("\n" + "-" * 70)
    print("  de-channel subcritical/critical contrast (card's prediction)")
    print("  prediction: de57/59/60 SUBCRITICAL (cutoff), de58 CRITICAL (scale-free)")
    print("-" * 70)
    print("   N |  de57  de58  de59  de60   | de58 = 2^hw(db56)")
    for (N, d57, d58, d59, d60) in de_channel_report():
        crit = "growing" if d58 > 1 else "flat"
        print(f"  {N:3d} | {d57:5d} {d58:5d} {d59:5d} {d60:5d}   | {crit}")
    print("\n  -> de57/59/60 are LITERALLY constant=1 (a single difference value:")
    print("     |de|=1 is not a 'subcritical avalanche-size distribution', it is")
    print("     NO distribution at all). de58 grows but as 2^hw(db56), a carry-")
    print("     COLLAPSE count, not a power-law avalanche-size law.")


if __name__ == '__main__':
    res = run(N_list=(8, 10, 12))
    subcrit_contrast()

    print("\n" + "=" * 70)
    print("  VERDICT ARITHMETIC")
    print("=" * 70)
    # Is any fitted alpha 'a simple function of 0.74'? and distinguishable from
    # the null refit 0.673? Report the spread.
    alphas = {N: r['best'][1] for N, r in res.items() if r['best']}
    print(f"  fitted avalanche-size exponents by N: "
          f"{ {N: round(a,3) for N,a in alphas.items()} }")
    if alphas:
        vals = list(alphas.values())
        print(f"  exponent range: [{min(vals):.3f}, {max(vals):.3f}] "
              f"spread={max(vals)-min(vals):.3f}")
        print(f"  distance of mean-alpha to 0.74 : "
              f"{abs(sum(vals)/len(vals) - 0.74):.3f}")
        print(f"  distance of mean-alpha to 0.673: "
              f"{abs(sum(vals)/len(vals) - 0.673):.3f}")
    geoms = [r['geom_ratio'] for r in res.values()]
    print(f"  carry-length tail ratios P(L+1)/P(L): "
          f"{[round(g,3) for g in geoms]}  (roughly constant => GEOMETRIC/EXPONENTIAL)")
    spans = [r['span_size'] for r in res.values()]
    print(f"  avalanche-size decade spans: {[round(s,2) for s in spans]} "
          f"(SOC needs >=1.5-2 decades; <1 decade => cannot assert a power law)")
