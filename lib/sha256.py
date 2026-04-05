"""
SHA-256 native primitives, constants, and precomputation.

This is the shared foundation — all tools in this repo should import
from here instead of reimplementing SHA-256 functions.
"""

MASK = 0xFFFFFFFF


# --- Primitives ---

def ROR(x, n):
    return ((x >> n) | (x << (32 - n))) & MASK

def SHR(x, n):
    return x >> n

def Ch(e, f, g):
    return ((e & f) ^ ((~e & MASK) & g))

def Maj(a, b, c):
    return (a & b) ^ (a & c) ^ (b & c)

def Sigma0(a):
    return ROR(a, 2) ^ ROR(a, 13) ^ ROR(a, 22)

def Sigma1(e):
    return ROR(e, 6) ^ ROR(e, 11) ^ ROR(e, 25)

def sigma0(x):
    return ROR(x, 7) ^ ROR(x, 18) ^ SHR(x, 3)

def sigma1(x):
    return ROR(x, 17) ^ ROR(x, 19) ^ SHR(x, 10)

def hw(x):
    """Hamming weight (popcount) of a 32-bit value."""
    return bin(x & MASK).count('1')

def add(*args):
    """Modular 32-bit addition of any number of arguments."""
    s = 0
    for a in args:
        s = (s + a) & MASK
    return s


# --- Constants ---

K = [
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

IV = [
    0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
    0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19,
]


# --- Precomputation ---

def precompute_state(M):
    """
    Run 57 rounds of SHA-256 compression on message M (16 words).
    Returns (state_after_round_56, W[0..56]).

    state is [a, b, c, d, e, f, g, h] as a tuple.
    W is a list of 57 schedule words.
    """
    W = list(M) + [0] * 41
    for i in range(16, 57):
        W[i] = add(sigma1(W[i-2]), W[i-7], sigma0(W[i-15]), W[i-16])

    a, b, c, d, e, f, g, h = IV
    for i in range(57):
        T1 = add(h, Sigma1(e), Ch(e, f, g), K[i], W[i])
        T2 = add(Sigma0(a), Maj(a, b, c))
        h, g, f, e, d, c, b, a = g, f, e, add(d, T1), c, b, a, add(T1, T2)

    return (a, b, c, d, e, f, g, h), W


def full_compression(M, free_words_57_61):
    """
    Run all 64 rounds with free schedule words W[57..61].
    W[62] and W[63] are computed from the schedule rule.
    Returns (final_state, full_W[0..63]).
    """
    W = list(M) + [0] * 48
    for i in range(16, 57):
        W[i] = add(sigma1(W[i-2]), W[i-7], sigma0(W[i-15]), W[i-16])
    for i, v in enumerate(free_words_57_61):
        W[57 + i] = v
    W[62] = add(sigma1(W[60]), W[55], sigma0(W[47]), W[46])
    W[63] = add(sigma1(W[61]), W[56], sigma0(W[48]), W[47])

    a, b, c, d, e, f, g, h = IV
    for i in range(64):
        T1 = add(h, Sigma1(e), Ch(e, f, g), K[i], W[i])
        T2 = add(Sigma0(a), Maj(a, b, c))
        h, g, f, e, d, c, b, a = g, f, e, add(d, T1), c, b, a, add(T1, T2)

    return (a, b, c, d, e, f, g, h), W


def build_schedule_tail(W_pre, free_words_4):
    """
    Build W[57..63] given precomputed W[0..56] and 4 free words (W[57..60]).
    Returns list of 7 schedule words [W[57], ..., W[63]].
    """
    W = list(W_pre) + list(free_words_4)
    # W[61] = sigma1(W[59]) + W[54] + sigma0(W[46]) + W[45]
    W.append(add(sigma1(W[59]), W[54], sigma0(W[46]), W[45]))
    # W[62] = sigma1(W[60]) + W[55] + sigma0(W[47]) + W[46]
    W.append(add(sigma1(W[60]), W[55], sigma0(W[47]), W[46]))
    # W[63] = sigma1(W[61]) + W[56] + sigma0(W[48]) + W[47]
    W.append(add(sigma1(W[61]), W[56], sigma0(W[48]), W[47]))
    return W[57:]


def run_tail_rounds(state, schedule_words, start_round=57):
    """
    Run compression rounds from start_round using given schedule words.
    Returns list of states: [state_before, state_after_r57, ..., state_after_last].
    """
    a, b, c, d, e, f, g, h = state
    trace = [(a, b, c, d, e, f, g, h)]
    for i, Wi in enumerate(schedule_words):
        T1 = add(h, Sigma1(e), Ch(e, f, g), K[start_round + i], Wi)
        T2 = add(Sigma0(a), Maj(a, b, c))
        h, g, f, e, d, c, b, a = g, f, e, add(d, T1), c, b, a, add(T1, T2)
        trace.append((a, b, c, d, e, f, g, h))
    return trace
