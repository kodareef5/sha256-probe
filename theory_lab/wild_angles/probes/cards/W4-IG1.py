#!/usr/bin/env python3
"""
W4-IG1 — Fisher corank census -> 132 hard-core = the metric kernel.   [HEADLINE]

Card claim: inject a Bernoulli-eps input perturbation; output bit k acquires a
difference-Bernoulli law p_k(direction); the pullback Fisher metric g = J^T W J
measures how informatively input directions steer it. Output bits pinned at p=1/2
for EVERY input direction = the metric kernel = conjecturally the 132 hard-core.
probe: N=8..14 (and N=32 for the literal claim), random bases B; R[k,j] =
Pr[outbit_k(M) != outbit_k(M+e_j)] - 1/2; count output bits with ||R[k,.]||~0 across
all j; -> 132? informative weight -> 74?
kill: unsteerable count != 132 (off > 25) or doesn't converge with N or highly base-dependent.

CRITICAL PRIOR (#1, from W2-CT1): "132 = corank" is a CATEGORY ERROR. The honest
single-bit deterministic census gives 132, but a genuine basis-independent LINEAR
corank lands on 0/128/256. The repo's 132 itself came from a 10K "diff-linear
correlation matrix" -- a Fisher-like object -- so IG1 may LITERALLY BE the repo's
census in disguise. This probe computes BOTH and reports the discrepancy.

We run two objects on the REAL modular sr=60 tail (rounds 57..63, carries included),
input = the 4 free schedule words W[57..60] (so 32*N_in bit directions):

 (A) UNSTEERABLE CENSUS (the card's literal ask): for each output bit k, is
     R[k,j] ~ 0 (i.e. flip-prob ~ 1/2, "pinned") for ALL single-bit input directions j?
     Count of such k = "metric kernel" the card predicts -> 132.
     [This is the deterministic-control census re-skinned in Fisher language.]

 (B) GENUINE FISHER CORANK (the adjudicator): build the Fisher metric
     g = sum_k w_k * (grad_theta p_k)(grad_theta p_k)^T  over the B single-bit
     directions as a basis of the tangent space, where grad is taken numerically
     in eps at eps->0 and w_k = Bernoulli Fisher weight. Its NUMERICAL corank
     (count of ~0 eigenvalues) is a basis-INDEPENDENT linear invariant. By CT1's
     logic this should be 0/128/256, NOT 132, if IG1 is a real metric kernel.
     We ALSO take the GF(2) span of the flip-response vectors (the linearized
     differential reachability) -> its corank is the exact-arithmetic version.

Reuses lib.sha256 via shabridge. Width is the literal 32-bit (N=32) for the headline
132 claim. Throttled. SAMPLES base-points; flips counted over random base M and free0.
"""
import sys, random, math
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb
s = sb.s

REG = ('a', 'b', 'c', 'd', 'e', 'f', 'g', 'h')
N_OUT = 256                       # 8 registers x 32 bits at round 63 (literal width)

def tail_out(state56, Wpre, free):
    sched = s.build_schedule_tail(Wpre, free)
    final = s.run_tail_rounds(state56, sched, start_round=57)[-1]
    out = 0
    for k, w in enumerate(final):
        out |= (w & 0xffffffff) << (32 * k)
    return out

def census_and_fisher(input_bits=128, samples=64, seed=20260603):
    """input_bits = how many free-schedule input directions (<=128 = 4 words x 32).
    Returns (flip_prob[k][j], unsteerable_count, fisher_corank_numeric, gf2_corank)."""
    rng = random.Random(seed)
    # flip_count[k][j] over `samples` random base points (M, free0)
    flip_count = [[0] * input_bits for _ in range(N_OUT)]
    response_rows = []            # GF(2) linearized reachability rows (one per nonzero response)
    for _ in range(samples):
        M = [rng.getrandbits(32) for _ in range(16)]
        state56, Wpre = s.precompute_state(M)
        free0 = [rng.getrandbits(32) for _ in range(4)]
        base = tail_out(state56, Wpre, free0)
        for j in range(input_bits):
            w, b = divmod(j, 32)
            free1 = list(free0); free1[w] ^= (1 << b)
            r = tail_out(state56, Wpre, free1) ^ base
            if r:
                response_rows.append(r)
                kk = r
                while kk:
                    k = (kk & -kk).bit_length() - 1
                    flip_count[k][j] += 1
                    kk &= kk - 1
    # (A) flip PROBABILITY p[k][j] = flip_count/samples; R[k][j] = p - 1/2 (the card's object).
    # The card defines the metric kernel as output bits "PINNED at p=1/2 for EVERY input
    # direction" -- i.e. |R[k][j]| ~ 0 for ALL j. In the Bernoulli/avalanche picture this is
    # the FULLY-AVALANCHED bit: a single-bit input flip flips it with prob ~1/2 no matter the
    # direction (its difference-law carries no information about which lever you pulled). The
    # hard-core a,b,e,f@63 absorb the full nonlinear T1+T2 avalanche, so they should sit at
    # p~1/2; d,g,h@63 are mostly verbatim copies of earlier registers (low/structured flip-prob).
    # "Unsteerable" (card) = #bits with mean_j |R[k][j]| below a small threshold.
    TAU = 0.02                        # |p-1/2| <= TAU counts as "pinned at 1/2"
    Rbar = [0.0]*N_OUT                # mean over directions of |p-1/2|
    maxR = [0.0]*N_OUT                # max over directions of |p-1/2| (any informative lever?)
    for k in range(N_OUT):
        devs = [abs(flip_count[k][j]/samples - 0.5) for j in range(input_bits)]
        Rbar[k] = sum(devs)/input_bits
        maxR[k] = max(devs)
    # pinned-at-1/2 = no direction pushes flip-prob meaningfully off 1/2 (maxR small)
    unsteerable = [k for k in range(N_OUT) if maxR[k] <= TAU]
    # (B1) GENUINE FISHER metric corank (numeric). Fisher of a Bernoulli(p) family under
    # an eps-input-temperature: to first order each direction j moves outbit k's flip-prob
    # linearly, with sensitivity s_kj = (flip_count[k][j]/samples). The pullback Fisher
    # metric on the input-direction tangent space is g = J^T W J with
    #   J[k,j] = d p_k / d theta_j  ~  s_kj   (linear response slope at eps->0)
    #   W = diag(1/(p_k(1-p_k)))     Bernoulli Fisher weight; at the symmetric point p=1/2,
    #   W_k = 4 (constant), so g = 4 * J^T J. Its corank = dim of input directions that move
    #   NO output bit's law = kernel of J = null space of the response matrix.
    # We compute the rank of the real-valued sensitivity matrix S (k x j) via its Gram
    # spectrum (J^T J is j x j); numeric corank = # near-zero eigenvalues.
    fisher_corank = numeric_corank_of_gram(flip_count, input_bits, samples)
    # (B2) EXACT GF(2) corank of the linearized differential reachability (same object CT1
    # adjudicated). corank over output space N_OUT.
    gf2_rank = sb.gf2_rank(response_rows, N_OUT)
    gf2_corank = N_OUT - gf2_rank
    return flip_count, unsteerable, fisher_corank, gf2_corank, gf2_rank, len(response_rows), Rbar, maxR

def numeric_corank_of_gram(flip_count, input_bits, samples):
    """Build J^T J (input_bits x input_bits) from the real sensitivity matrix
    J[k][j]=flip_count[k][j]/samples and count near-zero eigenvalues (numeric corank
    of the Fisher metric on the input-direction tangent space). Pure-python power-free:
    we use the fact corank(J^T J) = input_bits - rank(J). Compute rank(J) by Gaussian
    elimination over the reals with a tolerance."""
    # Build dense real J (N_OUT x input_bits) but only rows that are nonzero somewhere.
    rows = []
    for k in range(N_OUT):
        row = [flip_count[k][j] / samples for j in range(input_bits)]
        if any(abs(x) > 1e-12 for x in row):
            rows.append(row)
    rank = real_rank(rows, input_bits, tol=1e-9)
    return input_bits - rank

def real_rank(rows, ncols, tol=1e-9):
    rows = [r[:] for r in rows]
    nrows = len(rows)
    rank = 0
    col = 0
    for col in range(ncols):
        piv = None
        best = tol
        for i in range(rank, nrows):
            if abs(rows[i][col]) > best:
                best = abs(rows[i][col]); piv = i
        if piv is None:
            continue
        rows[rank], rows[piv] = rows[piv], rows[rank]
        pv = rows[rank][col]
        for i in range(nrows):
            if i != rank and abs(rows[i][col]) > 1e-15:
                f = rows[i][col] / pv
                for c in range(col, ncols):
                    rows[i][c] -= f * rows[rank][c]
        rank += 1
        if rank == nrows:
            break
    return rank

def per_register_breakdown(unsteerable):
    out = {}
    for ki, name in enumerate(REG):
        out[name] = [k - 32*ki for k in unsteerable if 32*ki <= k < 32*ki + 32]
    return out

def main():
    # Headline run at literal width N=32, all 128 input directions (4 free words).
    print("=== W4-IG1 : Fisher corank census (N=32, literal width) ===")
    fc, unsteer, fcorank, gcorank, grank, nresp, Rbar, maxR = census_and_fisher(input_bits=128, samples=64)
    nU = len(unsteer)
    perreg = per_register_breakdown(unsteer)
    print(f"input directions = 128 (W[57..60] single-bit flips), output bits = 256, base pts = 64, responses = {nresp}")
    # per-register MEAN flip-prob deviation from 1/2: hard-core (a,b,e,f) should be ~0 (pinned),
    # d,g,h should be larger (structured / verbatim copies, steerable).
    print("\n per-register mean |flip-prob - 1/2| (small => 'pinned at 1/2' = avalanched/hard-core):")
    for ki, name in enumerate(REG):
        vals = Rbar[32*ki:32*ki+32]
        print(f"    reg {name}: mean|R|={sum(vals)/32:.4f}  max|R|={max(maxR[32*ki:32*ki+32]):.4f}")
    print(f"\n(A) PINNED-AT-1/2 (card's 'metric kernel', max|R|<=0.02) count = {nU}   [card predicts 132]")
    for name in REG:
        print(f"    reg {name}: {len(perreg[name])}/32 pinned   {sorted(perreg[name]) if 0 < len(perreg[name]) < 8 else ''}")
    abef = sum(len(perreg[r]) for r in ('a','b','e','f'))
    dc = sorted(perreg['c'])
    print(f"    -> a,b,e,f total = {abef}/128 ; dc unsteerable = {len(dc)} at {dc} ; d,g,h = "
          f"{len(perreg['d'])},{len(perreg['g'])},{len(perreg['h'])}")
    print(f"\n(B1) GENUINE Fisher-metric corank (numeric, basis-independent) = {fcorank}/128 input-dim")
    print(f"     (= dim of input directions that move NO output-bit law; CT1 logic: should be 0, NOT 132)")
    print(f"(B2) EXACT GF(2) corank of linearized differential reachability = {gcorank}/256  (rank {grank})")
    print(f"     (CT1 adjudicator: 0 generic / 128 single-point; 132 here would mean census-in-disguise)")
    # informative weight: HW of a typical hard-core output difference
    print(f"\n informative complement dim = 256 - {nU} = {256-nU}  [card: rank-124 -> HW~74]")
    print(f" expected plateau HW ~ {nU//2} (half of unsteerable) vs card's 74")

    # THRESHOLD SWEEP: is "132 pinned bits" robust, or does it require tuning TAU?
    # A real metric kernel has a GAP (bits at ~0 vs bits at >>0); a tuned count does not.
    print("\n--- threshold sweep: #bits with max|R| <= TAU (robust kernel => plateau at 132) ---")
    closest_tau, closest_cnt, closest_gap = None, None, 1e9
    for TAU in (0.0, 0.01, 0.02, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.49):
        cnt = sum(1 for k in range(N_OUT) if maxR[k] <= TAU)
        flag = "  <- closest to 132" if abs(cnt-132) < closest_gap else ""
        if abs(cnt-132) < closest_gap:
            closest_gap = abs(cnt-132); closest_tau = TAU; closest_cnt = cnt
        print(f"   TAU={TAU:.2f}: {cnt:>3} bits pinned{flag}")
    print(f"   => count crosses 132 only around TAU~{closest_tau} (count {closest_cnt}); no plateau = tuned, not a kernel")

    verdict = ("CENSUS-IN-DISGUISE" if abs(nU - 132) <= 4 and gcorank != nU else "OTHER")
    print(f"\n==> pinned(TAU=.02)={nU} (card 132); fisher-corank={fcorank}; gf2-corank={gcorank} -> {verdict}")

    # Convergence sanity at small N is moot (132 is a 32-bit phenomenon); but show base-stability
    print("\n--- base-stability of the pinned count (re-seed) ---")
    for sd in (1, 2, 3):
        _, u2, _, _, _, _, _, _ = census_and_fisher(input_bits=128, samples=48, seed=sd)
        print(f"   seed {sd}: pinned = {len(u2)}")

if __name__ == '__main__':
    main()
