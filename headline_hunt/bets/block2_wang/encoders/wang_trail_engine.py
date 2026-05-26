#!/usr/bin/env python3
"""Wang-style differential trail engine for SHA-256 block-2 absorption.

Bet block2_wang kill_criteria #1: produce a differential trail satisfying local
conditions through >18 schedule-compliant rounds with message modification, beating
the naive-block-2 ~18-round SAT frontier. The exact_diff-pin search
(sweep/beam_w2_exactdiff) is too weak (FORWARD_BROKEN; see 20260525 results). This is
the real engine: generalized-condition (de Canniere-Rechberger) characteristic
propagation + guess-and-determine, built incrementally.

BUILD PLAN (each increment validated + committed):
  [1] generalized-condition algebra + forward propagation through the round's
      linear (sigma/Sigma = XOR-of-rotations) and boolean (Ch, Maj) functions.  <-- THIS FILE, now
  [2] carry-aware modular-addition condition propagation (the crux).
  [3] one-round forward+backward propagation; multi-round characteristic consistency.
  [4] guess-and-determine search over free message bits (message modification).
  [5] control validation (reproduce a known SHA-256 local-collision trail).
  [6] run on >=5 residual clusters; report best-trail-round count (kill-criterion gate).

INCREMENT 1 (this commit): the condition algebra and forward bitwise/linear
propagation, with self-tests. Modular addition is a documented stub for [2].

Generalized conditions on a bit PAIR (x, x*), encoded as a 4-bit mask over the
allowed values v = (x<<1)|x*  (v in 0..3):  bit v set  <=>  (x,x*) allowed.
"""

# value index v = (x<<1)|x*   ->   00:0  01:1  10:2  11:3
COND = {
    "?": 0b1111,  # no constraint
    "-": 0b1001,  # x == x*        (00 or 11)
    "x": 0b0110,  # x != x*        (01 or 10)
    "0": 0b0001,  # x = x* = 0
    "n": 0b0010,  # x=0, x*=1
    "u": 0b0100,  # x=1, x*=0
    "1": 0b1000,  # x = x* = 1
    "#": 0b0000,  # contradiction (empty)
}
MASK_TO_SYM = {m: s for s, m in COND.items()}


def sym(mask):
    return MASK_TO_SYM.get(mask, f"[{mask:04b}]")


def bits(mask):
    """Allowed pair-values v=(x<<1)|x* for a condition mask."""
    return [v for v in range(4) if (mask >> v) & 1]


def fwd_unop(ma, op):
    """Forward-propagate a 1-input bitwise op (e.g. NOT) over a condition mask."""
    out = 0
    for va in range(4):
        if (ma >> va) & 1:
            a, as_ = va >> 1, va & 1
            out |= 1 << ((op(a) << 1) | op(as_))
    return out


def fwd_binop(ma, mb, op):
    """Forward-propagate a 2-input bitwise op (XOR, AND, OR) over condition masks.
    Treats the two inputs as independent (exact for distinct variables)."""
    out = 0
    for va in range(4):
        if not (ma >> va) & 1:
            continue
        a, as_ = va >> 1, va & 1
        for vb in range(4):
            if not (mb >> vb) & 1:
                continue
            b, bs = vb >> 1, vb & 1
            out |= 1 << ((op(a, b) << 1) | op(as_, bs))
    return out


def fwd_terop(ma, mb, mc, op):
    """Forward-propagate a 3-input bitwise op (Ch, Maj) exactly over masks."""
    out = 0
    for va in range(4):
        if not (ma >> va) & 1:
            continue
        a, as_ = va >> 1, va & 1
        for vb in range(4):
            if not (mb >> vb) & 1:
                continue
            b, bs = vb >> 1, vb & 1
            for vc in range(4):
                if not (mc >> vc) & 1:
                    continue
                c, cs = vc >> 1, vc & 1
                out |= 1 << ((op(a, b, c) << 1) | op(as_, bs, cs))
    return out


_XOR = lambda a, b: a ^ b
_AND = lambda a, b: a & b
_NOT = lambda a: a ^ 1
_CH = lambda e, f, g: (e & f) ^ ((e ^ 1) & g)
_MAJ = lambda a, b, c: (a & b) ^ (a & c) ^ (b & c)


def xor(ma, mb):
    return fwd_binop(ma, mb, _XOR)


def ch(me, mf, mg):
    return fwd_terop(me, mf, mg, _CH)


def maj(ma, mb, mc):
    return fwd_terop(ma, mb, mc, _MAJ)


# ---- word-level (32 bitconditions, index 0 = LSB) ----
N = 32


def word_const_diff(dxor):
    """Word condition with no value constraint but a fixed XOR difference dxor:
    bit i is 'x' where dxor bit set, else '-'. (The classic input-difference start.)"""
    return [COND["x"] if (dxor >> i) & 1 else COND["-"] for i in range(N)]


def rotr_word(cond, r):
    return [cond[(i + r) % N] for i in range(N)]


def shr_word(cond, s):
    return [cond[i + s] if i + s < N else COND["0"] for i in range(N)]


def xor_word(ca, cb):
    return [xor(ca[i], cb[i]) for i in range(N)]


def bigsigma0(c):  # ROTR2 ^ ROTR13 ^ ROTR22
    return xor_word(xor_word(rotr_word(c, 2), rotr_word(c, 13)), rotr_word(c, 22))


def bigsigma1(c):  # ROTR6 ^ ROTR11 ^ ROTR25
    return xor_word(xor_word(rotr_word(c, 6), rotr_word(c, 11)), rotr_word(c, 25))


def smallsigma0(c):  # ROTR7 ^ ROTR18 ^ SHR3
    return xor_word(xor_word(rotr_word(c, 7), rotr_word(c, 18)), shr_word(c, 3))


def smallsigma1(c):  # ROTR17 ^ ROTR19 ^ SHR10
    return xor_word(xor_word(rotr_word(c, 17), rotr_word(c, 19)), shr_word(c, 10))


def word_active_bits(cond):
    return sum(1 for c in cond if c == COND["x"])


# ---- increment 2: carry-aware modular addition ----
#
# (A + B) mod 2^N is NOT bitwise XOR of conditions: bit i produces a carry-out
# (c,c*) that becomes bit i+1's carry-in, coupling the whole word LSB->MSB. We
# propagate a per-bit transducer whose STATE is the carry condition mask (over the
# carry pair (c,c*)). For each bit we enumerate the feasible (a,a*,b,b*,cin,cin*),
# emit the sum-bit pair s=(a^b^cin, a*^b*^cin*) and the carry-out pair
# co=(maj(a,b,cin), maj(a*,b*,cin*)). The result is a SOUND forward over-approximation:
# the per-bit sum mask and the propagated carry mask together contain every concrete
# behaviour. (Tracking the joint (sum,carry) correlation -- a tighter result -- is for
# the backward/search increments; mask-level soundness is what forward needs.)

_MAJ3 = lambda a, b, c: (a & b) | (a & c) | (b & c)


def add_words(ca, cb, carry_in=None):
    """Carry-aware modular add of two condition-words (index 0 = LSB).
    Returns (sum_word, final_carry_mask). carry_in defaults to '0' (no carry, no diff)."""
    c = COND["0"] if carry_in is None else carry_in
    out = [0] * N
    for i in range(N):
        s_mask = 0
        cout_mask = 0
        for va in bits(ca[i]):
            a, as_ = va >> 1, va & 1
            for vb in bits(cb[i]):
                b, bs = vb >> 1, vb & 1
                for vc in bits(c):
                    ci, cis = vc >> 1, vc & 1
                    s = a ^ b ^ ci
                    ss = as_ ^ bs ^ cis
                    co = _MAJ3(a, b, ci)
                    cos = _MAJ3(as_, bs, cis)
                    s_mask |= 1 << ((s << 1) | ss)
                    cout_mask |= 1 << ((co << 1) | cos)
        out[i] = s_mask
        c = cout_mask
    return out, c


def add_words_multi(words, carry_in=None):
    """Chain modular addition over a list of condition-words (associative)."""
    acc = words[0]
    carry = carry_in
    for w in words[1:]:
        acc, carry = add_words(acc, w, carry)
        carry = None  # only the very first add may take an external carry
    return acc, carry


def word_from_concrete(x, xstar):
    """Exact condition-word for a known concrete pair (x, x*), each N-bit ints."""
    out = [0] * N
    for i in range(N):
        xi = (x >> i) & 1
        xs = (xstar >> i) & 1
        out[i] = 1 << ((xi << 1) | xs)
    return out


def word_contains(cond, x, xstar):
    """True if the concrete pair (x, x*) is admitted by condition-word cond at every bit."""
    for i in range(N):
        v = (((x >> i) & 1) << 1) | ((xstar >> i) & 1)
        if not (cond[i] >> v) & 1:
            return False
    return True


def _selftest():
    # XOR identities
    assert xor(COND["-"], COND["-"]) == COND["-"], sym(xor(COND["-"], COND["-"]))
    assert xor(COND["x"], COND["-"]) == COND["x"]
    assert xor(COND["x"], COND["x"]) == COND["-"]          # diff ^ diff cancels (value unknown)
    assert xor(COND["0"], COND["1"]) == COND["1"]
    assert xor(COND["u"], COND["u"]) == COND["0"]          # (1,0)^(1,0)=(0,0); fixed values cancel
    assert xor(COND["u"], COND["n"]) == COND["1"]          # (1,0)^(0,1)=(1,1)
    # NOT
    assert fwd_unop(COND["0"], _NOT) == COND["1"]
    assert fwd_unop(COND["x"], _NOT) == COND["x"]          # NOT preserves difference
    assert fwd_unop(COND["u"], _NOT) == COND["n"]
    # Ch: Ch(e,f,g)=(e&f)^(~e&g). If e='-' (no diff) and f=g='-', output '-'.
    assert ch(COND["-"], COND["-"], COND["-"]) == COND["-"]
    # If e fixed 0, Ch = g, so a diff in g passes, diff in f absorbed.
    assert ch(COND["0"], COND["x"], COND["-"]) == COND["-"]   # e=0 selects g; f-diff absorbed
    assert ch(COND["0"], COND["-"], COND["x"]) == COND["x"]   # e=0 selects g; g-diff passes
    assert ch(COND["1"], COND["x"], COND["-"]) == COND["x"]   # e=1 selects f; f-diff passes
    # Maj all-equal no-diff stays no-diff
    assert maj(COND["-"], COND["-"], COND["-"]) == COND["-"]
    # Maj('-','-','x'): the two no-diff inputs are independent (may disagree in VALUE),
    # so when they split, the 'x' input decides the majority -> diff passes; result '?'.
    assert maj(COND["-"], COND["-"], COND["x"]) == COND["?"]
    # Sigma0 of a single-bit difference (active bit 0) -> active at -2,-13,-22 (mod 32)
    c = word_const_diff(1 << 0)
    s = bigsigma0(c)
    active = {i for i in range(N) if s[i] == COND["x"]}
    assert active == {(0 - 2) % N, (0 - 13) % N, (0 - 22) % N}, active
    print("wang_trail_engine increment-1 self-tests: PASS")
    print(f"  conditions: {' '.join(sym(COND[s2]) for s2 in ['?','-','x','0','1','u','n'])}")
    print(f"  Sigma0(diff@bit0) active bits: {sorted(active)}")


def _selftest_add():
    import random

    MASK = (1 << N) - 1
    # (a) two no-diff words ('-') add to a no-diff word; carry-out has no diff either.
    nd = [COND["-"]] * N
    s, cfin = add_words(nd, nd)
    assert all(b == COND["-"] for b in s), [sym(b) for b in s]
    assert cfin == COND["-"], sym(cfin)
    # (b) known modular behaviour: 1 + (2^N - 1) wraps to 0 (concrete, no diff).
    s, _ = add_words(word_from_concrete(1, 1), word_from_concrete(MASK, MASK))
    assert word_active_bits(s) == 0 and word_contains(s, 0, 0), [sym(b) for b in s]
    # (c) a single MSB-only difference adds with no carry into nothing above it:
    #     dA = 2^(N-1), B = 0  ->  sum difference exactly the MSB ('x' at bit N-1).
    ca = word_const_diff(1 << (N - 1))
    s, _ = add_words(ca, nd)
    assert s[N - 1] == COND["x"], sym(s[N - 1])
    # (d) SOUNDNESS cross-check vs concrete arithmetic: for random A,B and XOR-diffs
    #     dA,dB, the engine's sum-word must CONTAIN the true (S,S*) pair at every bit.
    rng = random.Random(20260526)
    for _ in range(4000):
        A = rng.getrandbits(N)
        B = rng.getrandbits(N)
        dA = rng.getrandbits(N)
        dB = rng.getrandbits(N)
        As, Bs = A ^ dA, B ^ dB
        S = (A + B) & MASK
        Ss = (As + Bs) & MASK
        s, _ = add_words(word_from_concrete(A, As), word_from_concrete(B, Bs))
        assert word_contains(s, S, Ss), (hex(A), hex(B), hex(dA), hex(dB))
    # (e) multi-operand chain matches a 5-way concrete add (mimics T1 = h+S1+Ch+K+W).
    for _ in range(2000):
        vals = [rng.getrandbits(N) for _ in range(5)]
        dvs = [rng.getrandbits(N) for _ in range(5)]
        valss = [v ^ d for v, d in zip(vals, dvs)]
        S = sum(vals) & MASK
        Ss = sum(valss) & MASK
        ws = [word_from_concrete(v, vs) for v, vs in zip(vals, valss)]
        s, _ = add_words_multi(ws)
        assert word_contains(s, S, Ss)
    print("wang_trail_engine increment-2 (modular add) self-tests: PASS")
    print("  6000 concrete cross-checks (2-op + 5-op) all contained by the engine output")


if __name__ == "__main__":
    _selftest()
    _selftest_add()
