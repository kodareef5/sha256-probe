"""
W2-SO4 — Reaction-diffusion Turing instability: are the 132 hard-core bits the
unstable (growth-factor>1) modes of the linearized difference map?

Card claim: linearize the difference map around da=0; rotations=diffusion,
carries=reaction. A Turing instability makes specific wavelengths grow; the 132
hard-core bits = the unstable Fourier band, forcing the HW floor. Probe predicts
which positions are hard-core and ties them to rotation constants.

Probe (per CATALOG): build the per-round linearized difference-propagation
Jacobian around da=0 (masked primitives), compose over rounds, compute the
eigen/singular spectrum; identify growth-factor>1 modes; does their support match
the 132 hard-core positions? near-circulant => dispersion-vs-wavelength plot with
an unstable band of width ~132.

Kill: Dead if there are no growth-factor>1 modes (da=0 fully stable => hard core
is nonlinear), OR unstable-mode support doesn't align with the measured hard-core
bits.

ADVERSARIAL PRIOR WEAPONIZED:
  #1: "132 = corank" is a CATEGORY ERROR (confirmed 4x: CT1/CT5/NT2/RG2). 132 is
      the repo's single-bit deterministic-control CENSUS (carry nonlinearity),
      NOT a basis-independent linear corank (real corank 0/128). For SO4, a real
      linear instability/eigenmode count should be 0/128/256, not 132. If you
      "get 132" you're re-running the census. NEVER confirm a near-132 without a
      real, stable, basis-independent corank/mode-count with {a,b,e,f}+4dc support.

STRATEGY: Two complementary linearizations, both around da=0, BOTH compute the
genuine spectral object (growth factors), NOT a single-bit census:
  (A) Real-valued empirical Jacobian of the FULL nonlinear difference map (carries
      INCLUDED) around da=0, via finite differences on the 8N-bit XOR-difference
      state, averaged over conditioning states. Compose over the 7 tail rounds.
      Singular values sigma_i are the genuine linear growth factors. Count
      sigma>1 modes; read their support on the 8N output bits; compare to the
      132 hard-core support {a,b,e,f}@63 + 4 dc.
  (B) GF(2) XOR-linearized round (linround, carries DROPPED = the strict
      "linearize around da=0" surrogate). Compose over 7 rounds. Its rank/corank
      is the basis-independent linear (un)reachability dimension -> the #1 test:
      does it land on 0/128/256 or (falsely) on 132?
"""
import sys, math, random
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb
import linround as lr
import numpy as np

s = sb.s
MASKN = lambda N: (1 << N) - 1
OFF = dict(a=0, b=1, c=2, d=3, e=4, f=5, g=6, h=7)


# ----------------------------------------------------------------------
# A real N-bit SHA tail round on the FULL 8-word state (carries included),
# scaled rotations matching the repo enumerators (rint(k*N/32), floor 1).
# ----------------------------------------------------------------------
def _scale(k32, N):
    r = int(round(k32 * N / 32.0)); return r if r >= 1 else 1

def _rots(N):
    return (tuple(_scale(k, N) for k in (2, 13, 22)),
            tuple(_scale(k, N) for k in (6, 11, 25)))

def make_round(N):
    m = MASKN(N); (S0r, S1r) = _rots(N)
    def ror(x, k): k %= N; return ((x >> k) | (x << (N - k))) & m
    def S0(a): return ror(a, S0r[0]) ^ ror(a, S0r[1]) ^ ror(a, S0r[2])
    def S1(e): return ror(e, S1r[0]) ^ ror(e, S1r[1]) ^ ror(e, S1r[2])
    def Ch(e, f, g): return ((e & f) ^ ((~e & m) & g)) & m
    def Maj(a, b, c): return ((a & b) ^ (a & c) ^ (b & c)) & m
    def rnd(state, k, w):
        a, b, c, d, e, f, g, h = state
        T1 = (h + S1(e) + Ch(e, f, g) + (k & m) + w) & m
        T2 = (S0(a) + Maj(a, b, c)) & m
        return ((T1 + T2) & m, a, b, c, (d + T1) & m, e, f, g)
    return rnd


def pack_state(st, N):
    """8-word state -> 8N XOR-difference bit positions (block X bit j @ off*N+j)."""
    v = []
    for X in 'abcdefgh':
        x = st[OFF[X]]
        for j in range(N):
            v.append((x >> j) & 1)
    return v


# ----------------------------------------------------------------------
# (A) Real-valued empirical Jacobian of the composed 7-round tail difference
#     map around da=0 (carries included). Element J[i,k] = P(output diff-bit i
#     flips when input diff-bit k is flipped), averaged over conditioning states
#     and message words (cascade-pinned: paths share W, msgdiff=0). The genuine
#     LINEAR-RESPONSE operator; its singular values are the growth factors.
# ----------------------------------------------------------------------
def empirical_tail_jacobian(N, rounds=7, samples=4000, seed=0):
    rnd = make_round(N); m = MASKN(N)
    rng = random.Random(seed)
    n = 8 * N
    # We measure response of the COMPOSED tail map: inject a 1-bit difference into
    # the round-57 input state of path 2, run `rounds` rounds for both paths
    # sharing the per-round W, read the output XOR-difference (8N bits).
    Ks = [s.K[57 + r] & m for r in range(rounds)]

    def run_pair(d_in_bits, st0, ws):
        # path1 from st0; path2 from st0 XOR d_in (applied to the 8N packing)
        st1 = list(st0)
        st2 = list(st0)
        # apply input difference bits to st2
        for X in 'abcdefgh':
            base = OFF[X] * N
            xor = 0
            for j in range(N):
                if d_in_bits[base + j]:
                    xor ^= (1 << j)
            st2[OFF[X]] ^= xor
        for r in range(rounds):
            st1 = list(rnd(st1, Ks[r], ws[r]))
            st2 = list(rnd(st2, Ks[r], ws[r]))
        d_out = [(pack_state(st1, N)[i] ^ pack_state(st2, N)[i]) for i in range(n)]
        return d_out

    J = np.zeros((n, n), dtype=float)
    # baseline: da=0 (no input diff) -> output diff is 0 (collision fixed point)
    for k in range(n):
        flips = np.zeros(n)
        for _ in range(samples // n + 2):
            st0 = [rng.getrandbits(N) for _ in range(8)]
            ws = [rng.getrandbits(N) for _ in range(rounds)]
            d_in = [0] * n; d_in[k] = 1
            d_out = run_pair(d_in, st0, ws)
            flips += np.array(d_out, dtype=float)
        J[:, k] = flips / (samples // n + 2)
    return J


def spectrum_report(J):
    sv = np.linalg.svd(J, compute_uv=False)
    n = J.shape[0]
    n_gt1 = int(np.sum(sv > 1.0 + 1e-9))
    # an eigen view too (J not symmetric; use abs eigenvalues)
    ev = np.abs(np.linalg.eigvals(J))
    n_ev_gt1 = int(np.sum(ev > 1.0 + 1e-9))
    return dict(sv=sv, n_sv_gt1=n_gt1, n_ev_gt1=n_ev_gt1,
                sv_max=float(sv[0]), ev_max=float(ev.max()), n=n)


# ----------------------------------------------------------------------
# (B) GF(2) XOR-linearized composed tail (linround): carries DROPPED.
#     The basis-independent linear (un)reachability dimension. #1 test: 0/128/256?
# ----------------------------------------------------------------------
def gf2_tail_rank(N, rounds=7):
    rows = lr.round_matrix(N, include_ch_maj=False)
    nn = 8 * N
    M = lr.identity_rows(nn)
    for _ in range(rounds):
        M = lr.matmul(rows, M, nn)
    rank = lr.rank_gf2([r for r in M], nn)
    return rank, nn - rank, nn


# ----------------------------------------------------------------------
# Hard-core support (the repo's 132): a,b,e,f @ output fully (128) + 4 dc.
# Compute the OVERLAP of the unstable-mode energy with the {a,b,e,f} block.
# ----------------------------------------------------------------------
def hardcore_block_mask(N):
    """8N-vector: 1 on a,b,e,f bit positions (the 128 part of the 132)."""
    mask = np.zeros(8 * N)
    for X in ('a', 'b', 'e', 'f'):
        base = OFF[X] * N
        mask[base:base + N] = 1.0
    return mask


def unstable_support_overlap(J, N):
    """Where does the leading (largest-sigma) right/left singular energy live?
    Compare the output-side (left) singular vectors' energy on {a,b,e,f} vs
    {c,d,g,h}. If Turing's unstable band = the hard core, the growing modes must
    concentrate on a,b,e,f."""
    U, sv, Vt = np.linalg.svd(J)
    hc = hardcore_block_mask(N)            # output bits a,b,e,f
    # energy of each left singular vector on the hard-core block
    k_top = min(8, J.shape[0])
    rows = []
    for i in range(k_top):
        u = U[:, i] ** 2
        rows.append((sv[i], float((u * hc).sum())))   # fraction on a,b,e,f
    frac_hc = (hc.sum()) / (8 * N)         # = 0.5 (128/256-ish)
    return rows, frac_hc


def run(Ns=(8, 10), rounds=7):
    print("=" * 72)
    print("W2-SO4  Turing instability  —  are the 132 hard-core bits unstable modes?")
    print("=" * 72)
    print("  hard core = a,b,e,f@63 fully (128) + 4 dc = 132 ; expected if a real")
    print("  linear mode-count: 0 / 128 / 256 (prior #1). 'getting 132' = the census.\n")

    for N in Ns:
        # (B) GF(2) basis-independent dimension
        rank, corank, nn = gf2_tail_rank(N, rounds)
        print(f"  N={N:2d} | (B) GF(2) XOR-linearized {rounds}-round tail (carries dropped):")
        print(f"         rank={rank} / {nn}   corank={corank}   "
              f"-> {'0/128/256-type' if corank in (0, N*1, N*2, N*4) else 'OTHER'}")

        # (A) real-valued empirical Jacobian growth spectrum
        J = empirical_tail_jacobian(N, rounds=rounds, samples=3000, seed=2)
        sp = spectrum_report(J)
        print(f"       (A) real linear-response Jacobian of the {rounds}-round tail "
              f"(carries INCLUDED), around da=0:")
        print(f"         sigma_max={sp['sv_max']:.3f}  #(sigma>1)={sp['n_sv_gt1']}/{sp['n']}"
              f"   |lambda|_max={sp['ev_max']:.3f}  #(|lambda|>1)={sp['n_ev_gt1']}")
        rows, frac = unstable_support_overlap(J, N)
        print(f"         leading singular-vec energy fraction on hard-core block "
              f"{{a,b,e,f}} (chance={frac:.2f}):")
        for (sv_i, f) in rows[:4]:
            print(f"           sigma={sv_i:.3f}  hc-energy-frac={f:.3f}")
        print()


if __name__ == '__main__':
    run(Ns=(8, 10), rounds=7)
    print("=" * 72)
    print("  VERDICT ARITHMETIC")
    print("=" * 72)
    print("  Two questions decide it:")
    print("   1) Are there growth-factor>1 modes around da=0? (else: hard core is")
    print("      NONLINEAR, da=0 linearly stable -> kill clause 1.)")
    print("   2) If a basis-independent linear count, is it 132 (=> re-ran the")
    print("      census, prior #1) or 0/128/256 (=> a real linear object)?")
