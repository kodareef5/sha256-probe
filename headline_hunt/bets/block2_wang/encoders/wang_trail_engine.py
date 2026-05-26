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


# NOTE [increment 2]: modular addition needs carry-aware propagation. A '+' of two
# difference words is NOT bitwise XOR — carries couple bit i to i+1 with their own
# conditions. Implement as a per-bit transducer over (carry-in condition) next.


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


if __name__ == "__main__":
    _selftest()
