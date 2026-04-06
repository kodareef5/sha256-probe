#!/usr/bin/env python3
"""
Differentiable SHA-256 tail surrogate for gradient-based collision search.

Uses continuous relaxation of discrete SHA-256 operations:
  - Bits represented as continuous values in [0,1]
  - AND(a,b) → a*b
  - XOR(a,b) → a+b-2*a*b
  - NOT(a) → 1-a
  - Modular addition → bitwise with differentiable carry chain
  - Rotation → permutation of bit positions (exact, no approximation)

The loss is the L2 norm of the state difference after 7 tail rounds.
Gradient descent finds "warm spots" — continuous relaxations near
valid collisions. These can be discretized and used as SAT hints.

ROUND8_PLAN Experiment L: Differentiable Late-Round Surrogate

Usage:
    python3 differentiable_sha256.py [N] [n_restarts] [n_steps]
"""

import sys, os, time
import torch
import torch.nn.functional as F

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

K32 = [
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5,
    0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3,
    0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc,
    0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7,
    0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13,
    0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3,
    0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5,
    0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208,
    0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
]
IV32 = [0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
        0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19]


def scale_rot(k32, N):
    return max(1, round(k32 * N / 32))


# --- Differentiable bit operations ---

def d_and(a, b):
    """Differentiable AND: a*b"""
    return a * b

def d_xor(a, b):
    """Differentiable XOR: a + b - 2*a*b"""
    return a + b - 2 * a * b

def d_not(a):
    """Differentiable NOT: 1 - a"""
    return 1.0 - a

def d_xor3(a, b, c):
    """Differentiable 3-way XOR"""
    return d_xor(d_xor(a, b), c)

def d_ch(e, f, g):
    """Differentiable Ch(e,f,g) = (e AND f) XOR (NOT(e) AND g)"""
    return d_xor(d_and(e, f), d_and(d_not(e), g))

def d_maj(a, b, c):
    """Differentiable Maj(a,b,c) = (a AND b) XOR (a AND c) XOR (b AND c)"""
    return d_xor3(d_and(a, b), d_and(a, c), d_and(b, c))


def d_ror(x, k, N):
    """
    Differentiable rotation: just permute bit positions.
    x: (..., N) tensor of continuous bit values.
    """
    k = k % N
    return torch.cat([x[..., k:], x[..., :k]], dim=-1)


def d_shr(x, k, N):
    """Differentiable right shift: shift and fill with zeros."""
    if k >= N:
        return torch.zeros_like(x)
    zeros = torch.zeros_like(x[..., :k])
    return torch.cat([x[..., k:], zeros], dim=-1)


def d_add(a, b, N):
    """
    Differentiable modular addition using carry chain.
    a, b: (..., N) tensors of continuous bit values [0,1].
    Returns: (..., N) tensor.

    Full adder per bit: sum = a XOR b XOR carry_in
                        carry_out = (a AND b) OR (carry_in AND (a XOR b))
    """
    carry = torch.zeros_like(a[..., :1])  # carry starts at 0

    result_bits = []
    for i in range(N):
        ai = a[..., i:i+1]
        bi = b[..., i:i+1]
        ab_xor = d_xor(ai, bi)
        s = d_xor(ab_xor, carry)
        # carry = (a AND b) OR (carry AND (a XOR b))
        # OR(x,y) = x + y - x*y
        ab_and = d_and(ai, bi)
        carry_xor = d_and(carry, ab_xor)
        carry = ab_and + carry_xor - d_and(ab_and, carry_xor)
        result_bits.append(s)

    return torch.cat(result_bits, dim=-1)


def d_add3(a, b, c, N):
    """Add three values."""
    return d_add(d_add(a, b, N), c, N)


def d_add5(a, b, c, d, e, N):
    """Add five values (for T1)."""
    return d_add(d_add(d_add(d_add(a, b, N), c, N), d, N), e, N)


def int_to_bits(val, N, device):
    """Convert integer to bit tensor [LSB, ..., MSB]."""
    bits = torch.zeros(N, dtype=torch.float32, device=device)
    for i in range(N):
        bits[i] = float((val >> i) & 1)
    return bits


def bits_to_int(bits):
    """Convert bit tensor back to integer."""
    val = 0
    for i in range(bits.shape[-1]):
        if bits[..., i].item() > 0.5:
            val |= 1 << i
    return val


def bits_hw(bits):
    """Continuous Hamming weight: sum of bit values."""
    return bits.sum(dim=-1)


class DifferentiableSHA256Tail:
    """
    Differentiable 7-round SHA-256 tail (rounds 57-63).
    All operations are continuous relaxations of discrete SHA-256.
    """

    def __init__(self, N, state1, state2, W1_pre, W2_pre, device):
        self.N = N
        self.device = device

        MASK = (1 << N) - 1
        rS0 = [scale_rot(2,N), scale_rot(13,N), scale_rot(22,N)]
        rS1 = [scale_rot(6,N), scale_rot(11,N), scale_rot(25,N)]
        rs1 = [scale_rot(17,N), scale_rot(19,N)]
        ss1 = scale_rot(10,N)

        self.rS0 = rS0; self.rS1 = rS1; self.rs1 = rs1; self.ss1 = ss1

        # Precompute constant bit-vectors
        self.K = [int_to_bits(K32[57+i] & MASK, N, device) for i in range(7)]
        self.s1 = [int_to_bits(state1[i], N, device) for i in range(8)]
        self.s2 = [int_to_bits(state2[i], N, device) for i in range(8)]

        # Schedule constants (precomputed from first 57 rounds)
        sha_mod = __import__('50_precision_homotopy').MiniSHA256(N)
        self.w1c = {k: int_to_bits(W1_pre[k], N, device) for k in [45,46,47,48,54,55,56]}
        self.w2c = {k: int_to_bits(W2_pre[k], N, device) for k in [45,46,47,48,54,55,56]}
        self.w1c['s46'] = int_to_bits(sha_mod.sigma0(W1_pre[46]), N, device)
        self.w2c['s46'] = int_to_bits(sha_mod.sigma0(W2_pre[46]), N, device)
        self.w1c['s47'] = int_to_bits(sha_mod.sigma0(W1_pre[47]), N, device)
        self.w2c['s47'] = int_to_bits(sha_mod.sigma0(W2_pre[47]), N, device)
        self.w1c['s48'] = int_to_bits(sha_mod.sigma0(W1_pre[48]), N, device)
        self.w2c['s48'] = int_to_bits(sha_mod.sigma0(W2_pre[48]), N, device)

    def sigma1(self, x):
        N = self.N
        return d_xor3(d_ror(x, self.rs1[0], N), d_ror(x, self.rs1[1], N),
                       d_shr(x, self.ss1, N))

    def Sigma0(self, a):
        N = self.N
        return d_xor3(d_ror(a, self.rS0[0], N), d_ror(a, self.rS0[1], N),
                       d_ror(a, self.rS0[2], N))

    def Sigma1(self, e):
        N = self.N
        return d_xor3(d_ror(e, self.rS1[0], N), d_ror(e, self.rS1[1], N),
                       d_ror(e, self.rS1[2], N))

    def one_round(self, state, Ki, Wi):
        """One SHA-256 compression round with continuous bits."""
        N = self.N
        a, b, c, d, e, f, g, h = state
        ch = d_ch(e, f, g)
        T1 = d_add5(h, self.Sigma1(e), ch, Ki, Wi, N)
        maj = d_maj(a, b, c)
        T2 = d_add(self.Sigma0(a), maj, N)
        a_new = d_add(T1, T2, N)
        e_new = d_add(d, T1, N)
        return [a_new, a, b, c, e_new, e, f, g]

    def forward(self, w1_free, w2_free):
        """
        Run 7 tail rounds with continuous free words.
        w1_free, w2_free: each (batch, 4, N) tensors of bit values in [0,1]
        Returns: loss (batch,) = sum of squared state difference bits
        """
        N = self.N
        batch = w1_free.shape[0]

        # Expand state to batch
        s1 = [self.s1[i].expand(batch, N) for i in range(8)]
        s2 = [self.s2[i].expand(batch, N) for i in range(8)]

        # Expand schedule constants
        def exp(v): return v.expand(batch, N)

        # Schedule: W[61..63]
        w1_59 = w1_free[:, 2]
        w2_59 = w2_free[:, 2]
        w1_60 = w1_free[:, 3]
        w2_60 = w2_free[:, 3]

        w1_61 = d_add(d_add(self.sigma1(w1_59), exp(self.w1c[54]), N),
                       d_add(exp(self.w1c['s46']), exp(self.w1c[45]), N), N)
        w2_61 = d_add(d_add(self.sigma1(w2_59), exp(self.w2c[54]), N),
                       d_add(exp(self.w2c['s46']), exp(self.w2c[45]), N), N)
        w1_62 = d_add(d_add(self.sigma1(w1_60), exp(self.w1c[55]), N),
                       d_add(exp(self.w1c['s47']), exp(self.w1c[46]), N), N)
        w2_62 = d_add(d_add(self.sigma1(w2_60), exp(self.w2c[55]), N),
                       d_add(exp(self.w2c['s47']), exp(self.w2c[46]), N), N)
        w1_63 = d_add(d_add(self.sigma1(w1_61), exp(self.w1c[56]), N),
                       d_add(exp(self.w1c['s48']), exp(self.w1c[47]), N), N)
        w2_63 = d_add(d_add(self.sigma1(w2_61), exp(self.w2c[56]), N),
                       d_add(exp(self.w2c['s48']), exp(self.w2c[47]), N), N)

        W1_tail = [w1_free[:, 0], w1_free[:, 1], w1_59, w1_60, w1_61, w1_62, w1_63]
        W2_tail = [w2_free[:, 0], w2_free[:, 1], w2_59, w2_60, w2_61, w2_62, w2_63]

        Ki = [self.K[i].expand(batch, N) for i in range(7)]

        for i in range(7):
            s1 = self.one_round(s1, Ki[i], W1_tail[i])
        for i in range(7):
            s2 = self.one_round(s2, Ki[i], W2_tail[i])

        # Loss: sum of squared XOR differences across all registers
        loss = torch.zeros(batch, device=self.device)
        for i in range(8):
            diff = d_xor(s1[i], s2[i])  # XOR in continuous domain
            loss = loss + (diff ** 2).sum(dim=-1)

        return loss

    def discrete_hw(self, w1_free, w2_free):
        """Evaluate with hard thresholding to get actual discrete HW."""
        w1_hard = (w1_free > 0.5).float()
        w2_hard = (w2_free > 0.5).float()
        with torch.no_grad():
            loss = self.forward(w1_hard, w2_hard)
        return loss


def run_gradient_search(N, n_restarts=256, n_steps=2000, lr=0.01,
                        anneal=True, device=None):
    """Run gradient-based collision search."""
    if device is None:
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    # Find a candidate
    spec = __import__('50_precision_homotopy')
    sha = spec.MiniSHA256(N)
    MASK = sha.MASK; MSB = sha.MSB

    # Find first candidate
    for m0 in range(min(MASK, (1 << 20))):
        M1 = [m0] + [MASK]*15
        M2 = list(M1); M2[0] = m0 ^ MSB; M2[9] = MASK ^ MSB
        s1, W1 = sha.compress(M1)
        s2, W2 = sha.compress(M2)
        if s1[0] == s2[0]:
            break
    else:
        print(f"No candidate at N={N}")
        return

    print(f"Differentiable SHA-256 Tail Search")
    print(f"N={N}, candidate M[0]=0x{m0:x}, fill=0x{MASK:x}")
    print(f"Restarts={n_restarts}, steps={n_steps}, lr={lr}")
    print(f"Device: {device}")

    tail = DifferentiableSHA256Tail(N, s1, s2, W1, W2, device)

    # Initialize free words as learnable parameters
    # Shape: (n_restarts, 4, N) — 4 free words, each N bits
    w1_logits = torch.randn(n_restarts, 4, N, device=device) * 0.1
    w2_logits = torch.randn(n_restarts, 4, N, device=device) * 0.1
    w1_logits.requires_grad_(True)
    w2_logits.requires_grad_(True)

    optimizer = torch.optim.Adam([w1_logits, w2_logits], lr=lr)

    best_discrete_hw = 8 * N
    best_continuous_loss = float('inf')
    t0 = time.time()

    for step in range(n_steps):
        # Temperature for sigmoid annealing
        if anneal:
            temp = max(0.1, 5.0 * (1.0 - step / n_steps))
        else:
            temp = 1.0

        # Soft bits via sigmoid
        w1_soft = torch.sigmoid(w1_logits / temp)
        w2_soft = torch.sigmoid(w2_logits / temp)

        # Forward pass
        loss = tail.forward(w1_soft, w2_soft)

        # Backprop on mean loss
        total_loss = loss.mean()
        optimizer.zero_grad()
        total_loss.backward()
        optimizer.step()

        # Track best
        min_loss = loss.min().item()
        if min_loss < best_continuous_loss:
            best_continuous_loss = min_loss

        # Periodic discrete evaluation
        if step % 200 == 0 or step == n_steps - 1:
            with torch.no_grad():
                disc_hw = tail.discrete_hw(
                    torch.sigmoid(w1_logits / temp),
                    torch.sigmoid(w2_logits / temp))
                min_disc = disc_hw.min().item()
                if min_disc < best_discrete_hw:
                    best_discrete_hw = min_disc
                    idx = disc_hw.argmin().item()
                    elapsed = time.time() - t0
                    print(f"  step {step:5d}: cont_loss={min_loss:.2f}, "
                          f"disc_hw={min_disc:.0f} (BEST), temp={temp:.2f}, "
                          f"mean_loss={total_loss.item():.2f} ({elapsed:.1f}s)")
                elif step % 500 == 0:
                    elapsed = time.time() - t0
                    print(f"  step {step:5d}: cont_loss={min_loss:.2f}, "
                          f"disc_hw={min_disc:.0f}, temp={temp:.2f}, "
                          f"mean_loss={total_loss.item():.2f} ({elapsed:.1f}s)")

    elapsed = time.time() - t0

    print(f"\n{'='*60}")
    print(f"RESULT N={N}: best_disc_hw={best_discrete_hw:.0f}, "
          f"best_cont_loss={best_continuous_loss:.2f}, time={elapsed:.1f}s")
    print(f"{'='*60}")

    # Compare with random baseline
    print(f"\nRandom baseline (same number of evaluations):")
    with torch.no_grad():
        random_w1 = torch.rand(n_restarts, 4, N, device=device)
        random_w2 = torch.rand(n_restarts, 4, N, device=device)
        random_hw = tail.discrete_hw(random_w1, random_w2)
        print(f"  Random min_hw: {random_hw.min().item():.0f}")
        print(f"  Random mean_hw: {random_hw.mean().item():.1f}")

    return best_discrete_hw, best_continuous_loss


if __name__ == "__main__":
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    restarts = int(sys.argv[2]) if len(sys.argv) > 2 else 512
    steps = int(sys.argv[3]) if len(sys.argv) > 3 else 3000

    run_gradient_search(N, restarts, steps)
