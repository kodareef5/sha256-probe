"""W7-RA4 decisive null model: the card's baseline (uniform random subset) is the
WRONG null. de58's reachable set S is a small ADDITIVELY-STRUCTURED band (carry
collapse). The honest question: are S's APs in EXCESS of what *any* equally
additively-structured set of the same shape gives? If the AP excess is fully
explained by S's coset/affine shape, the vdW angle is a RENAME of finding #5
(de58 = 2^hw(db56) carry-collapse image), not a new density-forcing.

Null model = sets generated as { base + (XOR-combination of the SAME free-bit
weights that S occupies) }, i.e. structurally identical 'free-bit' sets but with
random which-combinations included at the same size. Compare 3-AP counts.

Also: does the dominant common-difference d EQUAL a free-bit weight (=> it's just
the group-translation by a free bit, the carry shadow), and is it STABLE across N?
"""
import sys, random, statistics as st
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/cards')
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import importlib.util, os
spec = importlib.util.spec_from_file_location("ra4mod", os.path.join(os.path.dirname(__file__), "W7-RA4.py"))
ra4 = importlib.util.module_from_spec(spec); spec.loader.exec_module(ra4)


def free_bit_weights(S, N):
    AND = (1 << N) - 1; OR = 0
    for x in S:
        AND &= x; OR |= x
    return [1 << j for j in range(N) if ((OR >> j) & 1) and not ((AND >> j) & 1)], AND & OR_const(N), (AND)
def OR_const(N): return (1 << N) - 1


def structured_null(S, N, trials=400, seed=7):
    """Random sets of the same size living in the SAME affine span (fixed bits
    fixed to S's common value, free bits varying)."""
    mod = 1 << N
    AND = (1 << N) - 1; OR = 0
    for x in S:
        AND &= x; OR |= x
    fixed_val = AND  # bits constant across S keep their value
    free = [1 << j for j in range(N) if ((OR >> j) & 1) and not ((AND >> j) & 1)]
    # full affine span the free bits can reach:
    span = []
    for mask in range(1 << len(free)):
        v = fixed_val
        for k, w in enumerate(free):
            if (mask >> k) & 1:
                v |= w
        span.append(v)
    span = list(set(span))
    rng = random.Random(seed)
    size = len(S)
    if size > len(span):
        size = len(span)
    aps = []
    for _ in range(trials):
        R = set(rng.sample(span, size))
        aps.append(ra4.count_3aps(R, mod))
    aps.sort()
    return dict(span=len(span), mean=st.mean(aps), p95=aps[int(0.95*(len(aps)-1))],
                mx=max(aps), free_weights=free)


for N in (8, 10, 11):
    mod = 1 << N
    S, M = ra4.de58_set(N)
    real = ra4.count_3aps(S, mod)
    cd = ra4.common_diff_hist(S, mod)
    null = structured_null(S, N)
    top = cd.most_common(3)
    dom_d = top[0][0] if top else None
    dom_is_freebit = dom_d in null['free_weights'] if dom_d is not None else False
    print(f"\nN={N}  |S|={len(S)}  affine-span={null['span']} (free bit weights {[hex(w) for w in null['free_weights']]})")
    print(f"  real 3-APs                 = {real}")
    print(f"  structured(same-span) null : mean={null['mean']:.1f} p95={null['p95']:.1f} max={null['mx']}")
    print(f"  EXCESS over STRUCTURED null p95? {real > null['p95']}")
    print(f"  dominant common-diff       = {hex(dom_d) if dom_d else None}  "
          f"(== a free-bit group-translation weight? {dom_is_freebit})")
print("\nIf real ~= structured-null (no excess over the SAME affine span), the APs are"
      "\npure carry-collapse additive shadow = restatement of |de58|=2^hw(db56), not vdW.")
