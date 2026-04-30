---
date: 2026-05-01
bet: cascade_aux_encoding
status: REFINED RULE FOUND — fill > 0x80000000 (unsigned) → ladder; fits 12/12 cands
parent: F385 (proposed "fill_bit[kbit]=1", 10/11 fit)
type: negative_finding + iterative_refinement + new_rule
compute: 0 cadical reanalysis + 1 new cadical run on bit6_m6781a62a (fill=aaaa, kbit=6) to test mid-rule conjecture
---

> **NOTE (2026-05-01 ~12:00 EDT)**: F386's first proposed rule
> "fill_bit[31]=1 AND fill_bit[kbit]=1" was tested on bit6_m6781a62a
> (fill=0xaaaaaaaa, kbit=6, fill_bit[6]=0; rule predicts Class B) and
> FALSIFIED — that cand actually shows ladder=31. The corrected rule
> is **fill_bit[31]=1 AND fill HW > 1** (i.e., `fill > 0x80000000`
> unsigned). Fits all 12 cands tested. Below is the original F386
> writeup; the section "Re-corrected rule (12/12 fit)" at the end is
> the actually-final rule.

# F386: bit6_m024723f3 outlier is GENUINE — fill_bit[kbit]=1 rule is incomplete

## Question

F385 proposed `ladder iff fill_bit[kbit] = 1`. Fit 10/11 cands cleanly.
The lone outlier was bit6_m024723f3 (fill=0x7fffffff, kbit=6;
fill_bit[6]=1 but no 31-step ladder).

Three explanations were possible:
1. Rule incomplete (bit6 is a real counterexample)
2. Classifier missed the ladder (different step parameters)
3. m0-specific structure suppresses ladder

F386 tests #2 by relaxing classifier parameters.

## Method

Re-parsed `/tmp/F385_bit6_7fff_proof.lrat` (bit6_m024723f3 LRAT proof)
and ran ladder-search with relaxed step combinations:

  aux_step ∈ {1, 2}
  dw_step  ∈ {3, 4, 5, 6}
  dw_width ∈ {1, 2, 3}
  polarity ∈ {EVEN, ODD}

Total: 24 (aux_step × dw_step × dw_width × polarity) combinations tested.

## Result

**Zero ladders of length ≥3 under ANY step combination.** The
bit6_m024723f3 proof's XOR triples are genuinely scattered.

Sampled the 24 dW57-touching XOR triples:

```
  (316, 378, 12940)  EVEN
  (344, 406, 12935)  ODD
  (506, 568, 12950)  ODD
  (522, 584, 12858)  ODD
  ...
  (4997, 5122, 12638)  ODD
  (6529, 6654, 12702)  ODD
```

No arithmetic progression. No consistent dw_step. Mixed polarities.
This is qualitatively the **scattered Class B pattern** from F383, not
the regular Class A ladder.

## Findings

### Finding 1 — bit6_m024723f3 is a genuine counterexample

Explanation #2 (classifier artifact) is RULED OUT. The ladder isn't in
the proof at any tested arithmetic-progression parameters. Either the
rule needs more conditions (m0-dependent, fill-bit-31-dependent...) or
bit6_m024723f3's m0=0x024723f3 specifically interacts with
fill=0x7fffffff in a way that suppresses ladder formation.

### Finding 2 — Tentative rule needs additional condition

The "fill_bit[kbit] = 1" rule fits 10/11 cands. The 11th breaks it.
Possible additional conditions:

  (A) fill_bit[kbit] = 1 AND fill_bit[31] = 1
      (fits 10/11, predicts bit6 [fill bit-31=0] correctly as no ladder)

  (B) fill_bit[kbit] = 1 AND m0_bit[kbit] = some value
      (would explain bit6 if m0_bit[6] = 0; m0=0x024723f3 has bit 6 = ?)

  (C) fill ∈ {0xffffffff, 0xaaaaaaaa, 0x55555555}
      (a specific allowed set; fits the 10 fits but predicts 0x7fffffff
       gives no ladder, which matches bit6 but doesn't quantitatively
       explain why)

Let me check (A) directly:

  Class A cands (ladder=31):
    bit31_m17149975: fill_bit[31]=1, fill_bit[31]=1 ✓ (ffffffff)
    bit2_ma896ee41:  fill_bit[2]=1,  fill_bit[31]=1 ✓ (ffffffff)
    bit3_m33ec77ca:  fill_bit[3]=1,  fill_bit[31]=1 ✓ (ffffffff)
    bit28_md1acca79: fill_bit[28]=1, fill_bit[31]=1 ✓ (ffffffff)
    msb_m3f239926:   fill_bit[31]=1, fill_bit[31]=1 ✓ (aaaaaaaa)
    bit13_m4e560940: fill_bit[13]=1, fill_bit[31]=1 ✓ (aaaaaaaa)

  Class B cands (ladder=1):
    bit11_m45b0a5f6: fill=00000000, fill_bit[31]=0 ✓
    bit13_m4d9f691c: fill=55555555, fill_bit[31]=0 ✓
    bit10_m3304caa0: fill=80000000, fill_bit[10]=0 ✓ (rule (A): kbit fails)
    bit17_m427c281d: fill=80000000, fill_bit[17]=0 ✓ (kbit fails)
    bit6_m024723f3:  fill=7fffffff, fill_bit[6]=1 BUT fill_bit[31]=0 ✓ (rule A: bit-31 fails)

**Refined rule (A): `ladder iff fill_bit[kbit]=1 AND fill_bit[31]=1`**.
Fits 11/11 cands. **THIS may be the correct rule.**

This brings us back to a fill-bit-31-DEPENDENCE, but combined with the
F385-found fill_bit[kbit] dependence. The original F382 hypothesis
(fill bit-31 alone) was too narrow; the F385 rule (fill_bit[kbit] alone)
was also too narrow; F386 finds **the conjunction is the right rule**.

### Finding 3 — F382 was on the right track after all

F382 claimed fill-bit-31 axis but n=3 confounded with kbit. F385
showed fill-bit-31 alone isn't sufficient (msb_m3f239926 fill=aaaa,
bit-31 of aaaa = 1, ladders). F386 proposes the conjunction works:
fill bit-31 = 1 AND fill bit at kbit position = 1.

This is structurally satisfying: bit-31 is the SHA-256 schedule
recurrence's MSB, where sigma0/sigma1's rotation effects propagate
specially. The kbit position is where the kernel diff lives. **Both
positions need to be SET for the per-slot symmetry to hold across
the ladder.**

### Finding 4 — Recomputed Class A coverage

Per refined rule "fill_bit[31]=1 AND fill_bit[kbit]=1":

Per fill family:
  fill=ffffffff: fill_bit[31]=1, fill_bit[kbit]=1 for all 31 cands → 31 in Class A
  fill=aaaaaaaa: fill_bit[31]=1, fill_bit[kbit]=1 only for ODD kbits → 3 in Class A (of 6)
  fill=55555555: fill_bit[31]=0 → 0 in Class A
  fill=80000000: fill_bit[31]=1, fill_bit[kbit]=1 only for kbit=31 → 1 in Class A (of 11)
  fill=7fffffff: fill_bit[31]=0 → 0 in Class A
  fill=00000000: fill_bit[31]=0 → 0 in Class A

Total Class A under refined rule: 31 + 3 + 0 + 1 + 0 + 0 = **35 cands** (52% of registry).

Slightly larger than F384's 31 (46%) and F382's claim (also fill bit-31).
Smaller than F385's 41 (61%) speculation.

## What's shipped

- This memo
- 0 cadical runs (pure analysis on existing F385 proof)
- Refined rule: `ladder iff fill_bit[31]=1 AND fill_bit[kbit]=1`
  fits 11/11 cands tested so far
- Phase 2D Class A target: 35 of 67 cands (52%) under refined rule

## Compute discipline

- 0 solver runs
- 0 runs.jsonl entries
- audit_required: not applicable

## F381 → F386 chain summary

  F381 (n=1):  discovered Tseitin XOR ladder structure on bit31 proof
  F382 (n=3):  "fill-bit-31 axis"               — falsified by F383 (too narrow)
  F383 (n=6):  "fill=0xffffffff axis"           — provisional
  F384 (n=8):  "fill=0xffffffff specifically"   — narrowed by F385 (too narrow)
  F385 (n=11): "fill_bit[kbit]=1 rule"          — falsified by bit6 outlier (1/11)
  F386 (n=11): "fill_bit[31]=1 AND fill_bit[kbit]=1" — fits 11/11 ← TENTATIVE LOCK

Project's 9th iterative refinement in this chain. Each iteration:
either falsified or narrowed. F386 is the first to fit 11/11 — strongest
candidate for the correct rule.

## Next step (next session)

(a) **Verify the F386 rule** by testing more cands at the rule's edge cases:
    - bit13_m72f21093 (fill=aaaaaaaa, kbit=13 odd → predicted Class A)
    - bit6_m6781a62a (fill=aaaaaaaa, kbit=6 even → predicted Class B
      because aaaa bit-6 = 0)
    - bit15 cands at fill=aaaaaaaa or other (kbit=15 odd → Class A
      under rule)

(b) **Algebraically derive** why fill_bit[31]=1 AND fill_bit[kbit]=1
    matters in the cascade-aux Tseitin output. SHA-256 schedule
    recurrence at round 16 = sigma1(W[14]) + W[9] + sigma0(W[1]) +
    W[0]. With M[1..15] all = fill, sigma0(fill) and sigma1(fill)
    depend on fill bit pattern. Some symmetric values produce
    high-symmetry W[16+] patterns. The bit-31 condition presumably
    relates to the SHR3/SHR10 components of sigma0/sigma1 (which
    treat bit-31 specially).

(c) **Build the deployable propagator pre-injection spec**: per cand,
    apply the F386 rule to decide ladder injection or not. The shape
    of the ladder is universal (31 EVEN-XOR triples + 8 size-2
    equivalences); only the var-base offsets vary per cand. Sub-30-min
    coding work.

The F386 finding is **the strongest candidate yet for the correct
algebraic rule** governing the ladder's appearance. With (a)
confirming, the rule is locked. With (c) shipping, Phase 2D's
ladder-injection becomes a deterministic per-cand operation.

---

## Re-corrected rule (12/12 fit)

After F386 was first written, I tested the proposed rule on
bit6_m6781a62a (fill=0xaaaaaaaa, kbit=6, fill_bit[6]=0). The rule
predicted Class B; empirical was Class A (ladder=31). RULE FALSIFIED.

Re-derived rule on the now n=12 fingerprint:

```
cand                fill          b31  fill&7fffffff   class    rule (b31=1 AND HW>1)
bit31_m17149975     0xffffffff      1   0x7fffffff       A       ✓
bit2_ma896ee41      0xffffffff      1   0x7fffffff       A       ✓
bit3_m33ec77ca      0xffffffff      1   0x7fffffff       A       ✓
bit28_md1acca79     0xffffffff      1   0x7fffffff       A       ✓
msb_m3f239926       0xaaaaaaaa      1   0x2aaaaaaa       A       ✓
bit13_m4e560940     0xaaaaaaaa      1   0x2aaaaaaa       A       ✓
bit6_m6781a62a      0xaaaaaaaa      1   0x2aaaaaaa       A       ✓
bit6_m024723f3      0x7fffffff      0   0x7fffffff       B       ✓
bit11_m45b0a5f6     0x00000000      0   0x00000000       B       ✓
bit13_m4d9f691c     0x55555555      0   0x55555555       B       ✓
bit10_m3304caa0     0x80000000      1   0x00000000       B       ✓
bit17_m427c281d     0x80000000      1   0x00000000       B       ✓
```

**Refined rule fits 12/12: `ladder iff fill_bit[31]=1 AND (fill & 0x7fffffff) != 0`.**

Equivalently:
  - `fill > 0x80000000` (unsigned interpretation)
  - `fill_bit[31] = 1 AND fill_HW > 1`
  - `fill ∉ {00..0x7fffffff} ∪ {0x80000000}`

The rule doesn't depend on kbit at all (F385 was wrong on that). The
rule is purely a property of FILL: must have bit-31 set AND must have
some other bit set.

### Class A coverage under refined 12/12 rule

  fill=0xffffffff (HW=32, b31=1): Class A → 31 cands
  fill=0xaaaaaaaa (HW=16, b31=1): Class A → 6 cands
  fill=0x55555555 (HW=16, b31=0): Class B → 0 in A
  fill=0x80000000 (HW=1,  b31=1, but ONLY bit 31): Class B → 0 in A
  fill=0x7fffffff (HW=31, b31=0): Class B → 0 in A
  fill=0x00000000 (HW=0,  b31=0): Class B → 0 in A

  **Total Class A under refined rule: 37 of 67 cands (55%).**

### Mechanism conjecture (refined)

The cascade-1 round function involves Sigma1(state_e) which uses
ROTR17/ROTR19/SHR10. SHR10 sends bits 10-31 of input down to bits 0-21
of output; bit 31 of input goes to bit 21 of output (etc.). When
fill has bit-31 set AND has many lower bits set, sigma1(M-derived
values) produces RICH bit patterns at most output positions, giving
CDCL many Tseitin XOR equivalences to learn (the ladder).

When fill = 0x80000000 (only bit 31), sigma1(M-derived) is too sparse
— most output bits are 0, leaving few Tseitin XORs. When fill bit-31
is 0, ROTR17/ROTR19 don't bring any "high" bits into the rich part of
the output.

This is qualitative — full algebraic derivation is open. But the rule
fits 12/12 and is empirically sharp.

### F386 final summary

  Original F386: "fill_bit[31]=1 AND fill_bit[kbit]=1" (10/11)
                 — falsified by bit6_m6781a62a within ~10 minutes
  Corrected F386: **"fill_bit[31]=1 AND fill HW > 1"** (12/12)
                 — current best rule

Project's **9th iterative narrowing**. Each one within hours of being
proposed. The rule has stabilized at 12/12 — the strongest candidate
algebraic specification for the ladder.
