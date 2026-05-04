#!/usr/bin/env python3
"""F839 — schedule dependency analysis for cascade-1 5-slot alignment.

Builds the SYMBOLIC dependency graph of W[k] on M[i] for k ∈ {57..61}.
For each W[k] we track which M[i] (and which of the 32 bits of each)
have nonzero influence under the schedule expansion.

The schedule is:
    W[k] = M[k]                       for k < 16
    W[k] = sigma1(W[k-2]) + W[k-7]    for k >= 16
         + sigma0(W[k-15]) + W[k-16]

sigma0(x) = ROR(x,7) ^ ROR(x,18) ^ SHR(x,3)
sigma1(x) = ROR(x,17) ^ ROR(x,19) ^ SHR(x,10)

We track:
  1. M[i] support of each W[k]: which message words feed W[k] at all.
  2. M[i]:bit support: which (M[i], bit b) ∈ {0..31} feeds each bit of W[k].
  3. For the cascade-1 alignment problem at sr=61 (slots 57..61, with
     kernel M[0]=m0 fixed and M[9] kernel-fixed), how decomposable is
     the system of 5 constraints?
"""
from collections import defaultdict


def shr_bit(b, k):
    """Bit position b after SHR by k: contributes to position b - k iff b - k ≥ 0."""
    out = b - k
    return out if out >= 0 else None


def ror_bit(b, k):
    """Bit b after ROR by k contributes to position (b - k) mod 32."""
    return (b - k) % 32


# ───── symbolic GF(2) algebra ─────
#
# We track each bit as a SET of (M_word_idx, bit_pos) pairs — XOR of those
# message bits + an unknown nonlinear part. Modular addition is approximated
# linearly here (i.e., we ignore carry — gives an UPPER BOUND on which M-bits
# influence W[k]). This is fine for "structural support" — if a bit doesn't
# appear in the linear part, it doesn't appear in the carry part either,
# because carry only mixes things that are already there.


def xor_sets(*sets):
    """GF(2) XOR over sets: symmetric difference across all sets."""
    out = set()
    for s in sets:
        out ^= s
    return out


def sigma0_linear(W_bit):
    """W_bit: dict mapping bit-position-of-W → set((Mi, bp))).
    sigma0(W) = ROR(W,7) ^ ROR(W,18) ^ SHR(W,3).
    Returns dict for sigma0(W)."""
    out = {}
    for b in range(32):
        contribs = []
        # ROR(W,7)[b] = W[(b+7) % 32]
        contribs.append(W_bit.get((b + 7) % 32, set()))
        # ROR(W,18)[b] = W[(b+18) % 32]
        contribs.append(W_bit.get((b + 18) % 32, set()))
        # SHR(W,3)[b] = W[b+3] if b+3 < 32 else 0
        if b + 3 < 32:
            contribs.append(W_bit.get(b + 3, set()))
        out[b] = xor_sets(*contribs)
    return out


def sigma1_linear(W_bit):
    """sigma1(W) = ROR(W,17) ^ ROR(W,19) ^ SHR(W,10)."""
    out = {}
    for b in range(32):
        contribs = []
        contribs.append(W_bit.get((b + 17) % 32, set()))
        contribs.append(W_bit.get((b + 19) % 32, set()))
        if b + 10 < 32:
            contribs.append(W_bit.get(b + 10, set()))
        out[b] = xor_sets(*contribs)
    return out


def add_linear(A, B):
    """Linear approximation of modular addition: A XOR B (lower bound).

    The true support is A ∪ B (because carry propagates from any active bit
    to higher positions). We use UNION as the upper bound for support."""
    out = {}
    for b in range(32):
        out[b] = A.get(b, set()) | B.get(b, set())
    return out


def main():
    # initial schedule W[0..15] = M[0..15]
    # represent each W[k] as dict bit→ set of (M_word, M_bit)
    W = {}
    for k in range(16):
        W[k] = {b: {(k, b)} for b in range(32)}

    # extend schedule with linear-support tracking
    for k in range(16, 64):
        s1 = sigma1_linear(W[k - 2])
        w_seven = W[k - 7]
        s0 = sigma0_linear(W[k - 15])
        w_sixteen = W[k - 16]
        # additive support: union of all
        out = add_linear(add_linear(add_linear(s1, w_seven), s0), w_sixteen)
        W[k] = out

    # ── analysis 1: per-slot M-word support ──
    print("=== Per-slot M-word support (W[k] depends on which M[i]) ===")
    print(f"{'slot':>4} | {'n_Mi':>5} | M-words involved")
    print("-" * 60)
    word_support = {}  # k → set of M_word indices
    for k in range(57, 64):
        words = set()
        for b in range(32):
            for mi, _ in W[k].get(b, set()):
                words.add(mi)
        word_support[k] = words
        print(f"{k:>4} | {len(words):>5} | {sorted(words)}")

    # ── analysis 2: pairwise overlap ──
    print(f"\n=== Pairwise M-word overlap (cascade-1 slots 57..61) ===")
    slots_alignment = [57, 58, 59, 60, 61]
    print(f"{'':>5} " + " ".join(f"{s:>5}" for s in slots_alignment))
    for j in slots_alignment:
        row = [f"{j:>5}"]
        for i in slots_alignment:
            inter = word_support[i] & word_support[j]
            row.append(f"{len(inter):>5}")
        print(" ".join(row))

    # ── analysis 3: M-words EXCLUSIVE to each slot ──
    print(f"\n=== M-words EXCLUSIVE to each cascade-1 slot ===")
    print("(if W[k] depends on M[i] but no OTHER cascade-1 slot does, M[i] solves slot k alone)")
    for k in slots_alignment:
        others = set()
        for j in slots_alignment:
            if j != k:
                others |= word_support[j]
        excl = word_support[k] - others
        print(f"  slot {k}: |excl|={len(excl)} {sorted(excl)}")

    # ── analysis 4: sequential conditioning ──
    print(f"\n=== Sequential conditioning analysis ===")
    print("(if we solve slot k first, then slot k+1's free M-words = those NOT yet fixed by k..k-1)")
    fixed = set()
    for k in slots_alignment:
        new_fixed = word_support[k] - fixed
        new_free = fixed - word_support[k]  # not used in this slot, can be anything
        print(f"  slot {k}: depends on {len(word_support[k])} M-words; "
              f"NEW fixed by this slot: {len(new_fixed)} {sorted(new_fixed)}")
        fixed |= word_support[k]
    print(f"  TOTAL M-words fixed after all 5 slots: {len(fixed)} {sorted(fixed)}")

    # ── analysis 5: bit-level support per slot ──
    print(f"\n=== Per-slot M-bit support ===")
    for k in slots_alignment:
        all_bits = set()
        for b in range(32):
            all_bits |= W[k].get(b, set())
        print(f"  slot {k}: {len(all_bits)} M-bits influence dW[{k}] (out of 14*32=448 free)")

    # ── kernel-aware version: M[0] fixed (kernel m0), M[9] fixed (kernel) ──
    print(f"\n=== Kernel-aware (M[0] and M[9] fixed by kernel) ===")
    free_words = set(range(16)) - {0, 9}
    print(f"Free message words: {sorted(free_words)} ({len(free_words)} words)")
    for k in slots_alignment:
        free_in_slot = word_support[k] & free_words
        print(f"  slot {k}: depends on {len(free_in_slot)} FREE M-words {sorted(free_in_slot)}")

    print(f"\n=== Sequential conditioning (kernel-aware) ===")
    fixed = set()
    for k in slots_alignment:
        free_in_slot = word_support[k] & free_words
        new_fixed = free_in_slot - fixed
        print(f"  slot {k}: free M-words involved={len(free_in_slot)}; "
              f"NEW free fixed: {len(new_fixed)} {sorted(new_fixed)}")
        fixed |= free_in_slot
    print(f"  Free M-words touched after 5 slots: {len(fixed)} {sorted(fixed)}")
    print(f"  Free M-words UNTOUCHED: {sorted(free_words - fixed)}")

    # ── analysis 6: PER-OUTPUT-BIT support ──
    print(f"\n=== Per-output-bit M-bit support (slot 57..61) ===")
    print(f"{'slot':>4} | {'min':>5} {'avg':>6} {'max':>5} | distribution of |support| across 32 output bits")
    for k in slots_alignment:
        sizes = [len(W[k].get(b, set())) for b in range(32)]
        sizes.sort()
        avg = sum(sizes) / 32
        # show histogram bins
        buckets = defaultdict(int)
        for s in sizes:
            buckets[s] += 1
        hist = " ".join(f"{cnt}x{sz}" for sz, cnt in sorted(buckets.items()))
        print(f"{k:>4} | {min(sizes):>5} {avg:>6.1f} {max(sizes):>5} | {hist}")

    # ── analysis 7: pairwise BIT-level overlap ──
    # If per-bit support is X bits and the average overlap between
    # (W[57] bit b1, W[58] bit b2) is small, pairs of slots' bits could
    # share constraints sparsely.
    print(f"\n=== Bit-level support overlap: average |support(W[57] bit b) ∩ support(W[58] bit b)| ===")
    pairs = [(57, 58), (57, 59), (57, 61), (58, 60), (60, 61)]
    for k1, k2 in pairs:
        overlaps = []
        for b in range(32):
            o = W[k1].get(b, set()) & W[k2].get(b, set())
            overlaps.append(len(o))
        avg = sum(overlaps) / 32
        print(f"  W[{k1}].b ∩ W[{k2}].b: avg overlap = {avg:.1f} M-bits (per output bit)")

    # ── analysis 8: density of the 5-equation system in 448 free bits ──
    # If the constraint matrix (rows = 5*32 cascade-1 conditions, cols = 14*32
    # free M-bits) is sparse, the Jacobian of dW=cw1 in free M is sparse and
    # algebraic methods could exploit it.
    print(f"\n=== Linear-support density of 5x32 cascade-1 system ===")
    free_bits_set = set()
    for w in free_words:
        for b in range(32):
            free_bits_set.add((w, b))
    total_constraints = 5 * 32
    sparsity_per_row = []
    for k in slots_alignment:
        for b in range(32):
            supp = W[k].get(b, set()) & free_bits_set
            sparsity_per_row.append(len(supp))
    print(f"  total rows: {total_constraints}, total cols: {14*32} = 448")
    print(f"  per-row support: min={min(sparsity_per_row)} avg={sum(sparsity_per_row)/len(sparsity_per_row):.1f} max={max(sparsity_per_row)}")
    print(f"  matrix density: {sum(sparsity_per_row) / (total_constraints * 448):.3f}")


if __name__ == "__main__":
    main()
