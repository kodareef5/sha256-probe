"""
W2-SO2 — Quasispecies error threshold: the plateau as an information-maintenance
limit (Eigen error catastrophe).

Card claim: fitness f(m)=exp(-beta*HW), per-bit mutation mu. Below mu_c the
population localizes as a cloud around low-HW masters (can climb); above mu_c
mutation overwhelms selection and it delocalizes (HW->N/2). The HW~74 plateau =
the system pinned AT its error threshold. Gives mu_c(N) and the optimal solver
schedule (sit just below mu_c).

Probe (per CATALOG): (a) simulate a Moran/Wright-Fisher message population,
fitness exp(-beta*HW), sweep mu, find the sharp HW-jump transition; does localized
HW saturate near the plateau? (b) build the coarse-grained HW-shell quasispecies
matrix from collision-list neighbor stats, diagonalize, read mu_c from where the
dominant eigenvector delocalizes.

Kill: Dead if mu-sweep shows a SMOOTH crossover (no sharp threshold), OR the
localized phase concentrates at HW~0 (collisions easy to localize), OR the
dominant eigenvector is delocalized for ALL mu>0.

ADVERSARIAL FRAME: like SO1, the HW~74 plateau is the repo's measured floor and
is fully explained by "132 hard-core bits ~ random draws". SO2 must ADD a
mechanism (a genuine Eigen error THRESHOLD at finite mu_c, with the LOCALIZED
phase sitting at the plateau and NOT at HW=0). The skeptic: SHA's HW-vs-message
may be rugged/multi-peak -> glassy freezing, not a clean error catastrophe; and
the fitness landscape is the SO1 Binomial bowl, whose single 'master' (HW=0
collisions) is a measure-zero needle, so 'localization around a master' may never
happen at any mu>0.

We reuse SO1's exact cascade output_diff_hw machinery (same M0, same N).
"""
import sys, math, random, collections
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/cards')
import shabridge as sb
import numpy as np
import importlib
SO1 = importlib.import_module('W2-SO1')

MASKN = lambda N: (1 << N) - 1


# ----------------------------------------------------------------------
# (a) Wright-Fisher message population on the 4N-bit tail genotype.
#     Fitness f = exp(-beta*HW(output_diff(tail))). Each generation: select
#     parents proportional to fitness, mutate each bit with prob mu. Sweep mu,
#     record the stationary mean population HW.
# ----------------------------------------------------------------------
def wright_fisher(N, kit, ctx, beta, mu, pop=300, gens=120, seed=0, burn=60):
    rng = np.random.default_rng(seed)
    st1, st2, W1, W2 = ctx
    G = 4 * N
    # genotype = 4N-bit int; store as python ints, fitness via output HW
    def hw_of(geno):
        w57 = geno & MASKN(N)
        w58 = (geno >> N) & MASKN(N)
        w59 = (geno >> 2*N) & MASKN(N)
        w60 = (geno >> 3*N) & MASKN(N)
        _, hw = SO1.output_diff_hw(N, kit, st1, st2, W1, W2, w57, w58, w59, w60)
        return hw
    # init random population
    popg = [int(rng.integers(0, 1 << G)) for _ in range(pop)]
    hwcache = {}
    def gethw(g):
        v = hwcache.get(g)
        if v is None:
            v = hw_of(g); hwcache[g] = v
        return v
    mean_trace = []
    for gen in range(gens):
        hws = np.array([gethw(g) for g in popg], dtype=float)
        fit = np.exp(-beta * hws)
        fit /= fit.sum()
        # select parents
        idx = rng.choice(pop, size=pop, p=fit)
        children = []
        for i in idx:
            g = popg[i]
            # mutate each of G bits w.p. mu : draw # flips ~ Binomial(G, mu)
            nflip = rng.binomial(G, mu)
            if nflip:
                bits = rng.choice(G, size=nflip, replace=False)
                for b in bits:
                    g ^= (1 << int(b))
            children.append(g)
        popg = children
        if gen >= burn:
            mean_trace.append(float(np.mean([gethw(g) for g in popg])))
    return float(np.mean(mean_trace)), float(np.std(mean_trace))


def mu_sweep(N, kit, ctx, beta, mus, pop=250, gens=100, seed=0):
    out = []
    for mu in mus:
        mh, sh = wright_fisher(N, kit, ctx, beta, mu, pop=pop, gens=gens,
                               seed=seed, burn=gens//2)
        out.append((mu, mh, sh))
    return out


# ----------------------------------------------------------------------
# (b) Coarse-grained HW-shell quasispecies (Eigen) matrix. States = HW shells
#     h=0..Hmax. Replication-mutation operator W[h',h] = f(h) * Q[h'<-h], with
#     f(h)=exp(-beta h) (selection) and Q the per-bit-mutation kernel between
#     shells, estimated from the SO1 neighbor census (down/up/neutral fractions
#     give the local HW random-walk; lift to a mutation kernel over G bits at
#     rate mu). Diagonalize; the dominant eigenvector is the quasispecies
#     distribution over HW. LOCALIZED = peaked at low HW; DELOCALIZED = peaked
#     at the entropic mode (~plateau). Find mu_c where the peak jumps.
# ----------------------------------------------------------------------
def build_shell_kernel(N, kit, ctx, Hmax, samples=4000, seed=3):
    """Estimate, per HW shell h, the fractions p_down(h), p_up(h), p_neu(h) of a
    single random bit-flip (the SO1 neighbor census), and the mean step. Returns
    arrays for building the mutation kernel."""
    rng = random.Random(seed)
    st1, st2, W1, W2 = ctx
    G = 4 * N
    cnt = collections.defaultdict(lambda: np.zeros(3))  # [neutral,down,up]
    nsamp = collections.defaultdict(int)
    for _ in range(samples):
        t = [rng.getrandbits(N) for _ in range(4)]
        _, h0 = SO1.output_diff_hw(N, kit, st1, st2, W1, W2, *t)
        if h0 > Hmax: continue
        nsamp[h0] += 1
        # sample a few random bit flips (not all G, for speed)
        for _k in range(8):
            bit = rng.randrange(G); wi = bit // N; bj = bit % N
            t2 = list(t); t2[wi] ^= (1 << bj)
            _, h1 = SO1.output_diff_hw(N, kit, st1, st2, W1, W2, *t2)
            if h1 == h0: cnt[h0][0] += 1
            elif h1 < h0: cnt[h0][1] += 1
            else: cnt[h0][2] += 1
    pdown = np.zeros(Hmax+1); pup = np.zeros(Hmax+1); pneu = np.zeros(Hmax+1)
    for h in range(Hmax+1):
        tot = cnt[h].sum()
        if tot > 0:
            pneu[h], pdown[h], pup[h] = cnt[h] / tot
        else:
            pneu[h], pdown[h], pup[h] = 1.0, 0.0, 0.0
    return pdown, pup, pneu


def eigen_quasispecies(Hmax, beta, mu, G, pdown, pup, pneu):
    """Build replication-mutation matrix over HW shells and return dominant
    eigenvector + its localization (mean HW under it, and IPR)."""
    n = Hmax + 1
    # per-generation expected #mutations m = mu*G. Mutation moves HW by a random
    # walk whose single-step down/up probs are pdown/pup at the current shell.
    # Coarse kernel: from shell h, after one mutated bit -> h-1 w.p pdown[h],
    # h+1 w.p pup[h], h w.p pneu[h]. Apply ~m steps -> tridiagonal^m. We use the
    # single-step tridiagonal scaled by mu*G as the linearized mutation kernel.
    Q = np.zeros((n, n))
    for h in range(n):
        stay = max(0.0, 1.0 - mu * G * (pdown[h] + pup[h]))
        Q[h, h] += stay + mu * G * pneu[h]
        if h - 1 >= 0: Q[h-1, h] += mu * G * pdown[h]
        if h + 1 < n:  Q[h+1, h] += mu * G * pup[h]
    # normalize columns (stochastic mutation)
    Q = Q / np.maximum(Q.sum(axis=0, keepdims=True), 1e-12)
    f = np.exp(-beta * np.arange(n))
    Wm = Q * f[np.newaxis, :]               # W[h',h] = Q[h'<-h]*f(h)
    ev, evec = np.linalg.eig(Wm)
    k = int(np.argmax(ev.real))
    v = np.abs(evec[:, k].real); v = v / v.sum()
    meanhw = float((np.arange(n) * v).sum())
    ipr = float((v**2).sum())               # 1/IPR = participation; low IPR=delocalized
    return meanhw, ipr, v


def run(N=10):
    print("=" * 74)
    print("W2-SO2  quasispecies error threshold  —  plateau as info-maintenance limit?")
    print("=" * 74)
    kit = SO1.make_kit(N)
    got = SO1.find_M0(N, kit)
    if got is None:
        print(f"  no cascade-eligible M0 at N={N}"); return
    M0, M1, M2, st1, st2, W1, W2 = got
    ctx = (st1, st2, W1, W2)
    G = 4 * N
    # the random-tail mean HW (= the plateau analog & the delocalized target)
    hws0 = SO1.sample_hw(N, kit, ctx, trials=8000, seed=9)
    plateau = float(np.mean(hws0))
    print(f"  N={N}  M0=0x{M0:x}  G={G} tail-bits  random-tail mean HW (plateau analog)"
          f"={plateau:.2f}\n")

    # ---- (a) Wright-Fisher mu-sweep at moderate selection beta ----
    beta = 1.0
    mus = [0.005, 0.01, 0.02, 0.04, 0.08, 0.12, 0.2, 0.35, 0.5]
    print(f"  (a) Wright-Fisher population (pop=250, gens=100, beta={beta}); sweep mu:")
    print(f"      mu      stationary-meanHW   (delocalized target={plateau:.1f}; "
          f"localized-master would be HW->0)")
    sweep = mu_sweep(N, kit, ctx, beta, mus, pop=250, gens=100, seed=0)
    prev = None; max_jump = 0; jump_mu = None
    for (mu, mh, sh) in sweep:
        print(f"      {mu:5.3f}   {mh:6.2f} +/- {sh:4.2f}")
        if prev is not None:
            d = mh - prev[1]
            if d > max_jump: max_jump = d; jump_mu = mu
        prev = (mu, mh)
    lo = sweep[0][1]; hi = sweep[-1][1]
    print(f"      span: meanHW {lo:.2f} (mu={mus[0]}) -> {hi:.2f} (mu={mus[-1]})")
    print(f"      largest single-step jump = {max_jump:.2f} at mu~{jump_mu} "
          f"(SHARP threshold would be a near-discontinuous jump; SMOOTH ramp => kill)")

    # ---- (b) Eigen HW-shell quasispecies matrix ----
    Hmax = int(plateau + 6*np.std(hws0))
    pdown, pup, pneu = build_shell_kernel(N, kit, ctx, Hmax, samples=3000, seed=3)
    print(f"\n  (b) Eigen HW-shell quasispecies (beta={beta}); dominant-eigenvector"
          f" localization vs mu:")
    print(f"      mu      <HW>_dom   IPR     (LOCALIZED=low<HW>&high IPR; "
          f"DELOCALIZED~plateau&low IPR)")
    loc_rows = []
    for mu in [0.0001, 0.001, 0.005, 0.02, 0.05, 0.1, 0.3]:
        mhw, ipr, v = eigen_quasispecies(Hmax, beta, mu, G, pdown, pup, pneu)
        loc_rows.append((mu, mhw, ipr))
        print(f"      {mu:6.4f}  {mhw:6.2f}    {ipr:.4f}")
    # where does <HW>_dom cross to the plateau?
    print(f"\n  -> kill if: (a) the mu-sweep is a SMOOTH ramp (no sharp jump), OR")
    print(f"     the localized phase sits at HW~0 (collisions easy), OR (b) the")
    print(f"     dominant eigenvector is delocalized (<HW> near plateau) for ALL mu>0.")
    return dict(plateau=plateau, sweep=sweep, max_jump=max_jump, loc=loc_rows)


if __name__ == '__main__':
    run(N=10)
