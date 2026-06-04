"""
adder_diff.py — shared kernel for the geometry/topology sub-block (W1-GE*).

Extracts the per-adder XOR-differential structure of an N-bit modular-add network
(the tail-round adder cascade is the canonical case), exactly the structure the
repo's `active_adder_lm_bound.c` computes at 32-bit width. Re-used by:
  - W1-GE1 (Cech / contextuality nerve of the adder cover)
  - W1-GE6 (configuration-space braid: per-adder carry crossings -> writhe)

READ-ONLY toward the repo. Builds on shabridge (which re-exports lib.sha256).

Core object: a modular adder  alpha + beta -> gamma  (mod 2^N) carries XOR-diffs.
Lipmaa-Moriai (2001) exact xdp+:
    compatible iff  (alpha ^ beta ^ gamma ^ (beta<<1)) & (eq<<1) == 0  on bits < N
        where eq = ~(alpha^beta) & ~(alpha^gamma)
    cost (= -log2 p) = popcount( ~eq & (2^N-2) )    [bits 1..N-1, LSB free]
This is the *exact* differential, identical to the repo's lm_cost() but width-parametric.
"""
import sys
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb

def maskN(N):
    return (1 << N) - 1

def lm_compatible(alpha, beta, gamma, N):
    """Lipmaa-Moriai XOR-diff compatibility for alpha+beta->gamma mod 2^N."""
    m = maskN(N)
    alpha &= m; beta &= m; gamma &= m
    eq = (~(alpha ^ beta)) & (~(alpha ^ gamma)) & m
    # violation on bits i>=1: (a^b^g)[i] must equal beta[i-1] where eq[i-1]=1
    viol = (alpha ^ beta ^ gamma ^ ((beta << 1) & m)) & ((eq << 1) & m)
    return viol == 0

def lm_cost(alpha, beta, gamma, N):
    """-log2 xdp+; -1 if incompatible. Bit 0 (LSB) is always free."""
    if not lm_compatible(alpha, beta, gamma, N):
        return -1
    m = maskN(N)
    eq = (~(alpha ^ beta)) & (~(alpha ^ gamma)) & m
    free_bits = (~eq) & (m & ~1)          # bits 1..N-1 where eq fails
    return bin(free_bits).count('1')

def add_carry_trace(x, y, N):
    """Return the carry sequence c[0..N] of x+y mod 2^N (c[0]=0)."""
    m = maskN(N)
    x &= m; y &= m
    c = [0] * (N + 1)
    for i in range(N):
        s = ((x >> i) & 1) + ((y >> i) & 1) + c[i]
        c[i + 1] = s >> 1
    return c

def diff_carry_pattern(x, y, dx, dy, N):
    """For the modular adder, the *signed carry difference* per bit: how the
    carry chain of (x+y) differs from ((x^dx)+(y^dy)).  Returns list len N of
    {-1,0,+1}.  This is the 'crossing sign' used by the braid card (W1-GE6)."""
    m = maskN(N)
    c0 = add_carry_trace(x, y, N)
    c1 = add_carry_trace((x ^ dx) & m, (y ^ dy) & m, N)
    return [c1[i + 1] - c0[i + 1] for i in range(N)]

# ---- reduced faithful tail network (small N) -------------------------------
# We model ONE compression round's 7-adder chain at width N, with the genuine
# rotation cross-links (Sigma0,Sigma1) that the skeptic note says are what could
# create loops in the nerve.  Sigma's are rotations on N bits (scaled from 32).

def rotN(x, r, N):
    m = maskN(N)
    r %= N
    return ((x >> r) | (x << (N - r))) & m

def SigmaN(x, rots, N):
    out = 0
    for r in rots:
        out ^= rotN(x, r, N)
    return out

# scaled rotation amounts (32-bit (2,13,22)/(6,11,25) -> mod N, deduped non-trivially)
def sig0_rots(N): return sorted({2 % N, 13 % N, 22 % N})
def sig1_rots(N): return sorted({6 % N, 11 % N, 25 % N})
