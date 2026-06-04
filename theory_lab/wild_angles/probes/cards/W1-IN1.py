"""
W1-IN1 — Feed-forward coincidence operator → quotient out the bijection.

Card reframe: quotient out the invertible permutation P; define Phi(M)=P(IV,M) ⊟ IV
per lane. A collision ⇔ Phi(M)=Phi(M'). "The only non-injective op is the final 8×32
modular add" → collision-finding = two inputs landing in the same coset of the
add-kernel. Study the fibers of that one adder.

PROBE (as stated): N=4,6,8; fix 14 message words, vary 2; compute Phi; over COLLIDING
pairs measure the per-lane PRE-ADD MODULAR-DIFFERENCE distribution — predict
concentration at LOW 2-ADIC VALUATION (low carry depth).
KILL: dead if the pre-add differences are uniform (KL < 0.02 bits) — the quotient
buys nothing.

WHAT "PRE-ADD" MEANS HERE (faithful operationalization):
SHA's Davies–Meyer output is  H[lane] = state64[lane] ⊞ IV[lane]. The card isolates
that final adder. We run the genuine N-bit compression (transfer_operator._make_round,
scaled rotations) for R rounds with 2 free message words (14 frozen), giving the
pre-feed-forward register vector  s(M) = (a,b,c,d,e,f,g,h)_after_R. The feed-forward
adds IV (a per-lane bijection of a constant), so two messages collide in the OUTPUT iff
they collide in s(M) lane-by-lane.

A *coincidence* of the adder is then any pair (M,M') with s(M)=s(M'). The "pre-add
modular difference" the card wants is the per-lane modular gap  d_lane = s(M)[lane] ⊟
s(M')[lane] (mod 2^N), examined over the pairs the adder MERGES. Because a true full
collision forces every d_lane = 0 (uninteresting), the live object is the
*reduced-round* coincidence: take the output to be only the last K_OUT lanes
(equivalently: shave the final K_OUT rounds so those lanes haven't yet been frozen).
The pairs that coincide in the *kept* lanes generically DIFFER in the shaved lanes;
THOSE residual per-lane modular differences are the adder-coset structure. We histogram
their 2-adic valuation v2(d_lane) and compare to the uniform v2 law (the card's null:
P(v2=k) = 2^{-(k+1)}, i.e. "uniform random N-bit difference" — a random nonzero
N-bit value has v2=k w.p. 2^{-(k+1)} for k<N).

If the quotient "buys" something, the merged pairs should pile up at LOW valuation
(adjacent in 2-adic metric = low carry depth). If the residual differences look like
uniform random N-bit values (KL<0.02 from the 2^{-(k+1)} law), the quotient buys
nothing → KILLED.

Throttled per the playbook (this is itself the throttled python process).
"""
import sys, math, itertools, collections
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb
import transfer_operator as to
import numpy as np

MASKN = lambda N: (1 << N) - 1


def v2(x, N):
    """2-adic valuation of x mod 2^N; v2(0)=N (defined as 'maximal depth')."""
    if x == 0:
        return N
    k = 0
    while not (x >> k) & 1:
        k += 1
    return k


def compress_reduced(N, M16, R, k_base=0):
    """Genuine N-bit reduced compression: R rounds from IV, 16 message words M16
    (schedule rule for i>=16). Returns the pre-feed-forward 8-lane state tuple."""
    m = MASKN(N)
    rnd = to._make_round(N)
    rp = to._rot_params(N)

    def ror(x, kk):
        kk %= N
        return ((x >> kk) | (x << (N - kk))) & m
    s0r, s1r = rp['s0'], rp['s1']
    sig0 = lambda x: ror(x, s0r[0]) ^ ror(x, s0r[1]) ^ ((x >> s0r[2]) & m)
    sig1 = lambda x: ror(x, s1r[0]) ^ ror(x, s1r[1]) ^ ((x >> s1r[2]) & m)

    W = list(M16) + [0] * (R - 16 if R > 16 else 0)
    for i in range(16, R):
        W.append(0)
    for i in range(16, R):
        W[i] = (sig1(W[i-2]) + W[i-7] + sig0(W[i-15]) + W[i-16]) & m
    st = tuple(int(v) & m for v in sb.IV[:8])
    for i in range(R):
        st = rnd(st, sb.s.K[i] & m, W[i] & m)
    return st


def run(Ns=(4, 6, 8), R=20, n_free=2, k_keep_list=(1, 2), fill=None, seed=7,
        max_pairs_per_fiber=4000):
    """Enumerate all 2^(n_free*N) messages (others frozen), group by a SMALL set of
    KEPT output lanes (the coincidence condition), and over each fiber's pairs collect
    the residual per-lane modular differences in ALL OTHER lanes; histogram v2; KL vs
    the uniform-random 2-adic law.

    NOTE on the framing: for Davies–Meyer the feed-forward adds a COMMON IV, so per-lane
    modular differences are IDENTICAL before and after the add ((x+IV)-(y+IV)=x-y). So
    "pre-add" == "post-add" modular difference; we measure it on state_R. We make the
    coincidence condition small (1-2 kept lanes) so fibers are large and pairs exist."""
    LANE = dict(a=0, b=1, c=2, d=3, e=4, f=5, g=6, h=7)
    print(f"# W1-IN1  feed-forward coincidence adder fibers.  R={R} rounds, "
          f"{n_free} free msg words, rest frozen.")
    results = []
    for N in Ns:
        m = MASKN(N)
        # frozen fill for the 14 non-free words
        rng = np.random.default_rng(seed + N)
        base = [int(rng.integers(0, 1 << N)) for _ in range(16)]
        free_positions = [0, 1]   # vary M[0], M[1]; freeze the other 14
        # enumerate all messages
        states = {}
        msgs = []
        for combo in itertools.product(range(1 << N), repeat=n_free):
            M = list(base)
            for p, val in zip(free_positions, combo):
                M[p] = val
            st = compress_reduced(N, M, R)
            states[combo] = st
            msgs.append(combo)

        for k_keep in k_keep_list:
            # KEEP only the first k_keep lanes (the coincidence/fiber condition).
            # "residual" = ALL OTHER lanes, where merged pairs generically differ.
            kept = tuple(range(0, k_keep))
            residual = tuple(range(k_keep, 8))
            # group messages by the kept-lane signature
            groups = collections.defaultdict(list)
            for combo in msgs:
                st = states[combo]
                sig = tuple(st[i] for i in kept)
                groups[sig].append(combo)

            # over every colliding (merged) pair, residual modular diffs
            v2_counts = collections.Counter()
            diff_vals = collections.Counter()   # the raw modular diffs (for a 2nd null)
            npairs = 0
            for sig, members in groups.items():
                if len(members) < 2:
                    continue
                # cap pair budget per fiber for speed (sample first/random members)
                mem = members if len(members) <= 200 else members[:200]
                for i in range(len(mem)):
                    for j in range(i + 1, len(mem)):
                        a_st = states[mem[i]]
                        b_st = states[mem[j]]
                        for lane in residual:
                            d = (a_st[lane] - b_st[lane]) & m
                            if d == 0:
                                continue   # this lane happened to also match
                            v2_counts[v2(d, N)] += 1
                            diff_vals[d] += 1
                            npairs += 1
                        if npairs > max_pairs_per_fiber * len(groups):
                            break
            if npairs == 0:
                print(f"  N={N} k_keep={k_keep}: no merged pairs with residual diffs.")
                continue

            # observed v2 distribution
            tot = sum(v2_counts.values())
            obs = np.array([v2_counts.get(k, 0) / tot for k in range(N + 1)])
            # NULL A: uniform random nonzero N-bit value: P(v2=k)=2^{-(k+1)} for k<N,
            #         and v2=N (value 0) excluded since we dropped d==0. Renormalize over k<N.
            null = np.array([2.0 ** (-(k + 1)) for k in range(N)] + [0.0])
            null = null / null.sum()
            # KL(obs || null) in bits, with smoothing on zero obs bins
            eps = 1e-12
            kl = float(np.sum(np.where(obs > 0, obs * np.log2((obs + eps) / (null + eps)), 0.0)))
            # mean valuation (low => "low carry depth" as card predicts)
            mean_v2 = float(np.sum([k * obs[k] for k in range(N + 1)]))
            null_mean = float(np.sum([k * null[k] for k in range(N)]))
            print(f"  N={N:2d} k_keep={k_keep}: merged-pair lane-diffs={npairs:6d}  "
                  f"KL(obs||uniform)={kl:.4f} bits  mean v2={mean_v2:.3f} "
                  f"(uniform={null_mean:.3f})")
            # show the histograms
            obs_str = " ".join(f"{obs[k]:.3f}" for k in range(N))
            nul_str = " ".join(f"{null[k]:.3f}" for k in range(N))
            print(f"          obs  P(v2=k) k=0..{N-1}: {obs_str}")
            print(f"          unif P(v2=k):           {nul_str}")
            results.append((N, k_keep, kl, mean_v2, null_mean, npairs))

    print()
    if results:
        maxkl = max(r[2] for r in results)
        print(f"MAX KL across all (N,k_out) = {maxkl:.4f} bits   "
              f"(kill threshold 0.02 bits)")
        verdict = "SURVIVES (KL>0.02 somewhere)" if maxkl > 0.02 else "KILLED (uniform, KL<0.02)"
        print(f"VERDICT-INPUT: {verdict}")
        # is the concentration toward LOW valuation (card's prediction)?
        low = [r for r in results if r[3] < r[4] - 0.05]
        print(f"  cases concentrated at LOW v2 (card prediction) : {len(low)}/{len(results)}")
    return results


if __name__ == '__main__':
    run()
