"""
W5-CO4 — Final coalgebra: collision count as fiber sizes; power-of-2 quantization.

Card claim: the behavior map to the final coalgebra has fibers = collisions;
image size = 2^(domain - 0.74N). Sharp test: are fiber sizes QUANTIZED to powers
of 2 (a bisimulation-class regularity a random oracle lacks)?
Probe: N=8,10 fiber-size histogram of the behavior map; mean ~= 2^0.74N, and is it
power-of-2-quantized vs a Poisson null?
Kill: indistinguishable from the random-oracle Poisson.

Per prior finding #5: the power-of-2 fact is real but shallow; CONFIRM only if the
coalgebra DERIVES a specific count (0.74 slope or |de58|), not "fibers are powers of 2".

----------------------------------------------------------------------------
What is the behavior map here?
In the cascade tail model, path-1 ranges over (w57,w58,w59,w60); path-2 is the
da=0 cascade partner. The honest "final coalgebra behavior" of a single message
under the round-as-coalgebra is its FINAL OUTPUT (the 8 registers after round 63),
which is exactly its observable terminal behavior. We take the behavior map
   B : (w57,w58,w59,w60)  ->  final 8-register state (path-1 hash).
Fibers of B = inputs that hash equal. Collisions (the colliding-pair count the
repo measures, 260 at N=8) live INSIDE this: a colliding pair (M, M') has M from
path-1 and M' = its cascade partner; but the *self-collision* structure of B
(distinct path-1 inputs landing on the same output) is the genuine "fibers" object.

We measure BOTH:
  (A) fiber-size histogram of the path-1 behavior map B (whole-function fibers);
  (B) the cascade collision count (260@N8) as the cross-path fiber.

Then we test power-of-2 quantization of (A) against a Poisson null with the same
mean, and ask whether mean fiber size = 2^0.74N (the card's derived count).
"""
import sys, math
from collections import Counter
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/cards')
import _w5co_engine as E


def behavior_fibers(N):
    """Histogram of fiber sizes of B: (w57..w60) -> final state (path-1 output)."""
    M = E.make_model(N)
    setup = E.find_M0(M)
    R = M['MASK'] + 1
    out_counts = Counter()
    domain = 0
    for w57 in range(R):
        for w58 in range(R):
            for w59 in range(R):
                for w60 in range(R):
                    r = E.run_tail(M, setup, w57, w58, w59, w60)
                    out_counts[r['s63'][0]] += 1   # path-1 final state
                    domain += 1
    fiber_hist = Counter(out_counts.values())  # size -> #fibers of that size
    image = len(out_counts)
    return domain, image, fiber_hist, M, setup


def poisson_pmf(k, lam):
    return math.exp(-lam) * lam**k / math.factorial(k)


def main():
    print("=== W5-CO4: final-coalgebra fiber sizes & power-of-2 quantization ===\n")
    for N in (4,):
        domain, image, fiber_hist, M, setup = behavior_fibers(N)
        # mean fiber size over NONEMPTY fibers (= domain/image)
        mean_fiber = domain / image
        pred_074 = 2 ** (0.74 * N)
        print(f"--- N={N}  (M0=0x{setup['M0']:x}) ---")
        print(f"domain (4N free bits) = {domain} = 2^{4*N}")
        print(f"image size            = {image}")
        print(f"mean nonempty fiber   = {mean_fiber:.4f}   "
              f"(card predicts 2^0.74N = {pred_074:.3f})")
        print(f"empirical slope log2(domain/image)/N = "
              f"{math.log2(domain/image)/N:.4f}  (card: 0.74)")
        # fiber-size histogram
        print("fiber-size histogram (size : #fibers):")
        for sz in sorted(fiber_hist):
            print(f"   {sz:3d} : {fiber_hist[sz]}")
        # power-of-2 quantization test: fraction of MASS in power-of-2-sized fibers
        pows = {1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024}
        mass_pow = sum(sz * cnt for sz, cnt in fiber_hist.items() if sz in pows)
        mass_tot = sum(sz * cnt for sz, cnt in fiber_hist.items())
        print(f"mass in power-of-2-sized fibers: {mass_pow}/{mass_tot} "
              f"= {mass_pow/mass_tot:.3f}")
        # number of DISTINCT fiber sizes, and are they all powers of 2?
        sizes = sorted(fiber_hist)
        all_pow2 = all((s & (s-1)) == 0 for s in sizes)
        print(f"distinct fiber sizes = {sizes}  all powers of 2? {all_pow2}")

        # Poisson null: if outputs were a random oracle on the SAME image-sized
        # codomain with 'domain' balls, fiber sizes ~ Poisson(lam=domain/codomain).
        # The fair null fixes the codomain to the FULL state space 2^(8N) (a true
        # random oracle), not the realized image. Compute expected #collision-pairs.
        codomain_full = 2 ** (8 * N)
        lam_full = domain / codomain_full
        # expected colliding PAIRS under random oracle = C(domain,2)/codomain
        exp_pairs_ro = (domain * (domain - 1) / 2) / codomain_full
        # observed self-collision pairs of B:
        obs_pairs = sum(sz * (sz - 1) // 2 for sz, cnt in fiber_hist.items() for _ in range(cnt))
        # (recompute cleanly)
        obs_pairs = sum(cnt * (sz * (sz - 1) // 2) for sz, cnt in fiber_hist.items())
        print(f"\nRandom-oracle null (codomain=2^{8*N}): lam={lam_full:.3e}")
        print(f"  expected self-collision pairs ~= {exp_pairs_ro:.3f}")
        print(f"  observed self-collision pairs   = {obs_pairs}")
        if exp_pairs_ro > 0:
            print(f"  ratio observed/expected         = {obs_pairs/exp_pairs_ro:.2f}")

        # The cascade cross-path collision count (the repo's '260@N8' object):
        colls, _, _ = E.enumerate_tail(N, want='collide')
        print(f"\ncascade cross-path full collisions (the repo object) = {len(colls)}  "
              f"(N4=49, N8=260)")
        # does THIS number = 2^0.74N or 2^N?  N=4: 2^0.74*4=10.6, 2^4=16
        print(f"  vs 2^0.74N={pred_074:.2f}, vs 2^N={2**N}, vs 2^1.x?: "
              f"log2(count)/N = {math.log2(len(colls))/N:.3f}")


if __name__ == '__main__':
    main()
