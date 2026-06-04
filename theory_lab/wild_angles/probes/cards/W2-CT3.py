#!/usr/bin/env python3
"""
W2-CT3 — Schedule as an IIR filter -> poles predict the N=10 interference?

Card claim: the schedule recurrence
    W[i] = sigma1(W[i-2]) + W[i-7] + sigma0(W[i-15]) + W[i-16]
is a linear IIR filter in the round index i. In the bit-rotation DFT basis it block-
diagonalizes into N scalar sub-filters with poles z(omega). Resonances (|z|~1, low damping)
= rounds where differences don't decay = long trails; a dominant pole whose natural period is
commensurate with the word width N selects the constructive-interference N (claimed N=10).

PROBE (per card): numpy `roots` of the degree-16 characteristic polynomials per DFT frequency
(ROR caricature first, then SHR correction); check that the empirical masked-schedule
difference-echo envelope tracks the dominant pole modulus.

KILL: dead if the echo envelope doesn't track the dominant pole modulus at small N.

Method:
  (A) Per rotation-DFT frequency k (omega = exp(2pi i k / N)), the rotation operators ROR(r)
      act as multiplication by omega^{-r} (ROTR by r sends bit b -> b-r; on the additive
      character chi_k(x)=omega^{k x}, ROTR is mult by omega^{-r}... we just use the standard
      DFT eigenvalue w^{r} up to sign of convention; |z| is convention-independent).
      sigma1 ~ w^{17}+w^{19} (+ SHR10 correction), sigma0 ~ w^{7}+w^{18} (+ SHR3 correction).
      Characteristic polynomial of the order-16 recurrence:
        z^16 = s1(w) z^14 + z^9 + s0(w) z^1 + z^0
      i.e.  z^16 - s1 z^14 - z^9 - s0 z - 1 = 0.   Roots -> poles. Dominant pole = max |z|.
  (B) SHR correction: SHR drops bits and is NOT diagonal in the rotation-DFT. We approximate
      the SHR contribution by its average gain on frequency k (a real attenuation factor), to
      see if it moves the dominant modulus much.
  (C) Empirical echo envelope: inject a single-bit difference into W[16] of an otherwise random
      message, run the REAL schedule forward, and measure HW(dW[i]) the difference echo as a
      function of i. The "envelope" decay/growth rate is compared to the dominant-pole modulus.
      Do this for several N (8,10,11,12,16) and see whether N=10 is singled out by either the
      poles (a commensurate natural period) OR the empirical echo (a peak in persistence).

Throttled. numpy used only for polynomial roots. N small.
"""
import sys, random, cmath, math
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb
s = sb.s
import numpy as np

# ---- scaled rotation amounts for small-sigma at width N (mirror lib.sha256 small sigmas) ----
def small_sigma_rots(N):
    # full: sigma0 = ROR7 ^ ROR18 ^ SHR3 ; sigma1 = ROR17 ^ ROR19 ^ SHR10  (32-bit)
    f = lambda x: max(1, min(N - 1, round(x * N / 32)))
    g = lambda x: max(0, min(N - 1, round(x * N / 32)))   # shifts may be 0..N-1
    return dict(s0=(f(7), f(18), g(3)), s1=(f(17), f(19), g(10)))

def char_poly_roots(N, k, with_shr=True):
    """Roots of the schedule characteristic polynomial at rotation-DFT frequency k (0..N-1).
    Recurrence order 16; taps at lags 2 (sigma1), 7, 15 (sigma0), 16."""
    r = small_sigma_rots(N)
    w = cmath.exp(2j * math.pi * k / N)
    # rotation parts (unit modulus); SHR part: in DFT it's not unit-modulus. Caricature: drop
    # SHR (with_shr=False) or add a real average-gain term (with_shr=True, gain ~ (N-c)/N).
    s1 = w**r['s1'][0] + w**r['s1'][1]
    s0 = w**r['s0'][0] + w**r['s0'][1]
    if with_shr:
        s1 += (N - r['s1'][2]) / N      # SHR10 average surviving-bit gain (real attenuation)
        s0 += (N - r['s0'][2]) / N      # SHR3
    # poly in z (descending powers z^16 .. z^0):
    # z^16 - s1 z^14 - 1*z^9 - s0 z^1 - 1 = 0   (lag2 -> z^14, lag7 -> z^9, lag15 -> z^1, lag16 -> z^0)
    coeffs = [0j] * 17
    coeffs[0] = 1                 # z^16
    coeffs[2] = -s1               # z^14  (lag 2)
    coeffs[7] = -1                # z^9   (lag 7)
    coeffs[15] = -s0              # z^1   (lag 15)
    coeffs[16] = -1               # z^0   (lag 16)
    roots = np.roots(coeffs)
    return roots

def dominant_pole(N, with_shr=True):
    """Max over frequencies k of (max |root|). Also return the per-frequency dominant moduli."""
    per_k = []
    for k in range(N):
        roots = char_poly_roots(N, k, with_shr=with_shr)
        per_k.append(max(abs(z) for z in roots))
    return max(per_k), per_k

def empirical_echo(N, trials=200, length=48):
    """Inject single-bit diff in W[16]; run REAL width-N schedule; measure HW(dW[i]) vs i.
    Returns per-position mean HW and a fitted exponential rate (log-HW slope) over i=16..length.
    Width-N schedule: reimplement sigma at width N using shabridge ROR/SHR? We must NOT reimpl
    sha primitives, but a width-N *toy* schedule is a research surrogate (the card asks for it).
    We build sigma at width N from sb.ROR/sb.SHR semantics generalized to N bits explicitly."""
    r = small_sigma_rots(N)
    msk = (1 << N) - 1
    def rorN(x, c): return ((x >> c) | (x << (N - c))) & msk
    def shrN(x, c): return x >> c
    def sig0(x): return rorN(x, r['s0'][0]) ^ rorN(x, r['s0'][1]) ^ shrN(x, r['s0'][2])
    def sig1(x): return rorN(x, r['s1'][0]) ^ rorN(x, r['s1'][1]) ^ shrN(x, r['s1'][2])
    def sched(M16):
        W = list(M16) + [0] * (length - 16)
        for i in range(16, length):
            W[i] = (sig1(W[i-2]) + W[i-7] + sig0(W[i-15]) + W[i-16]) & msk
        return W
    rng = random.Random(20260603 + N)
    hw_sum = [0.0] * length
    for _ in range(trials):
        M = [rng.getrandbits(N) for _ in range(16)]
        bit = rng.randrange(N)
        M2 = list(M); M2[15] ^= (1 << bit)     # diff in W[15] (last input word, lag-1 into i=16)
        W1, W2 = sched(M), sched(M2)
        for i in range(length):
            hw_sum[i] += bin((W1[i] ^ W2[i]) & msk).count('1')
    hw_mean = [h / trials for h in hw_sum]
    # fit log(HW) slope over the active tail i=16..length-1 (avoid log 0)
    xs, ys = [], []
    for i in range(16, length):
        if hw_mean[i] > 1e-9:
            xs.append(i); ys.append(math.log(hw_mean[i]))
    if len(xs) >= 2:
        n = len(xs); sx = sum(xs); sy = sum(ys); sxx = sum(x*x for x in xs); sxy = sum(x*y for x,y in zip(xs,ys))
        slope = (n*sxy - sx*sy) / (n*sxx - sx*sx)
    else:
        slope = float('nan')
    echo_rate = math.exp(slope) if slope == slope else float('nan')  # per-round multiplicative envelope rate
    plateau = sum(hw_mean[length-8:length]) / 8
    return hw_mean, echo_rate, plateau

def main():
    print("=" * 72)
    print("W2-CT3: schedule IIR poles vs empirical difference-echo envelope")
    print("=" * 72)
    Ns = [8, 10, 11, 12, 16]
    print(f"\n{'N':>3} | {'dom|z| (ROR-caric)':>18} | {'dom|z| (+SHR)':>14} | "
          f"{'echo rate/round':>15} | {'echo plateau HW':>15}")
    rows = []
    for N in Ns:
        dz_caric, _ = dominant_pole(N, with_shr=False)
        dz_shr, perk = dominant_pole(N, with_shr=True)
        hw_mean, echo_rate, plateau = empirical_echo(N)
        rows.append((N, dz_caric, dz_shr, echo_rate, plateau))
        print(f"{N:>3} | {dz_caric:>18.4f} | {dz_shr:>14.4f} | {echo_rate:>15.4f} | {plateau:>15.3f}")

    print("\nPer-frequency dominant moduli at N=10 (the alleged special N):")
    _, perk10 = dominant_pole(10, with_shr=True)
    for k, m in enumerate(perk10):
        print(f"   freq k={k}: dom|z| = {m:.4f}")

    print("\nDoes the pole modulus TRACK the empirical echo rate? (card kill test)")
    print(f"{'N':>3} | {'dom|z|(+SHR)':>12} | {'echo rate':>10} | {'ratio echo/pole':>15}")
    for N, dzc, dzs, er, pl in rows:
        ratio = er / dzs if dzs else float('nan')
        print(f"{N:>3} | {dzs:>12.4f} | {er:>10.4f} | {ratio:>15.4f}")

    print("\nIs N=10 singled out?  (a) by poles: is dom|z| at N=10 a local max / commensurate?")
    print("                       (b) by echo:  is echo persistence (rate, plateau) peaked at N=10?")
    dz_by_N = {N: dzs for N, _, dzs, _, _ in rows}
    er_by_N = {N: er for N, _, _, er, _ in rows}
    pl_by_N = {N: pl for N, _, _, _, pl in rows}
    print(f"   dom|z| by N : {dz_by_N}")
    print(f"   echo rate by N: {er_by_N}")
    print(f"   echo plateau by N: {pl_by_N}")
    print(f"   argmax dom|z| over N = {max(dz_by_N, key=dz_by_N.get)}; "
          f"argmax echo-rate = {max(er_by_N, key=er_by_N.get)}; "
          f"argmax plateau = {max(pl_by_N, key=pl_by_N.get)}")

    print("\n" + "=" * 72)
    print("KILL: dead if the echo envelope does not track the dominant pole modulus at small N.")
    print("=" * 72)

if __name__ == '__main__':
    main()
