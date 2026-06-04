# Neutral-bit decouple probe — VERDICT: BLOCKED (rank 0)

**Question (lead follow-up, make-or-break):** can the sr=60→61 barrier's `2^-2N` be
discounted by finding **message "neutral bits"** — perturbations that move g1's absolute
target `sched1[60]` (via the precompute words `W1p[44],W1p[45],W1p[53]`) WITHOUT disturbing
the cascade (`da56=0`) or the inter-message compatibility gap `h`? If a rank-`r` subspace of
such perturbations exists, g1 gains `r` free bits and sr=61 drops `2^-2N → 2^-(2N-r)`.

**Headline number:** rank of free g1-control via differential-preserving message bits =
**0/N** at both N=8 and N=10. **Neutral bits do NOT exist. The decouple is BLOCKED.**
sr=61 stays `2^-2N`.

---

## Engine + ground-truth validation (done first, adversarially)

Reused the **already-validated** small-N cascade engine `cards/_w5co_engine.py`:
- selftest reproduces **49 collisions @ N=4** (this run, all with de61=de62=0) ✓
- cross-checked against the repo's C enumerator `gap_analysis.c` compiled lab-side
  (`/tmp/gap_n8`): **260 sr=60 collisions @ N=8**, M0=0x67, fill=0xff, and the verified
  `2^-2N` independence structure (P(g1=0)=P(h=0)=2^-N, ratio 0.923 @ N=8) ✓
- the probe's own `evaluate()` reproduces the C enumerator's **(g1, h) bit-for-bit** on 4
  distinct real collision tuples:
  - N=8  (131,70,82,92): g1=28, h=249 — py==C ✓  ·  (131,140,71,87): g1=207, h=89 — py==C ✓
  - N=10 (309,594,54,698): g1=277, h=609 — py==C ✓ · (310,477,913,139): g1=981, h=452 — py==C ✓

So the machinery measuring sched1[60], h, da56 and the full collision is faithful to the
repo's own enumerator before any perturbation is applied.

---

## What was computed

Anchored on a verified sr=60 collision (the cross-checked tuples above), for each **message
perturbation** δ (single-bit and low-weight multi-bit flips of the message words M[0..15]) in
three modes — `common` (δ added to BOTH M1 and M2, preserving the XOR-difference to first
order, exactly the structural-insight candidate), `m1` (M1 only), `m2` (M2 only) — measured:
- **(a) Δsched1[60]** — does g1's absolute target move?
- **(b) is the differential preserved?** — `da56==0` (cascade-eligible) AND `h` **EXACTLY**
  unchanged (full-width equality, NOT the weak de61=0 filter) AND the full 8-register
  collision at r63 survives (the strongest filter).
- **Headline = GF(2) rank of {Δsched1[60]}** restricted to the subspace that preserves
  (da56=0 AND h-exact AND full collision).

## Results

**Single-bit + weight≤2 ball, all 3 modes, N=8 and N=10:**

| quantity | N=8 | N=10 |
|---|---|---|
| rank{Δsched1[60]} **unconstrained** (ignore differential) | **8/8** | **10/10** |
| rank{Δsched1[60]} over **NEUTRAL** subspace (da56=0 ∧ h-exact ∧ collide) | **0/8** | **0/10** |
| perturbations keeping da56=0 (weight≤2 ball, common mode) | 26 / 8256 | 19 / 12880 |
| …of those, keeping **h exact** | **0** | **0** |
| …of those, keeping the full collision | **0** | **0** |

The contrast is the whole story: sched1[60] **is fully reachable** by message bits (rank N
unconstrained) — but **never while preserving the differential** (rank 0 constrained).
Single-bit common-mode δ moves sched1[60] in 128/128 cases yet keeps da56=0 in **0** of them;
m1/m2 single bits keep da56=0 in only 1–2 cases and **none** keep h.

## Adversarial deep-dive: is rank 0 just because `da56=0` is rare?

The most honest objection to a rank-0 result: maybe `da56=0` (cascade eligibility) is so
restrictive that too few perturbations survive it to fairly judge h-decoupling. So I forced
the search into a larger weight≤3 ball (cap 60000 tries/mode) and looked ONLY at the da56=0
survivors, asking: among perturbations that DO keep the cascade eligible, is sched1[60]-movement
EVER decoupled from h-movement, AND does any such perturbation keep the FULL collision?

**N=8 (weight≤3, ~60k tries/mode):**

| mode | da56=0 survivors | move sched1 | also move h (coupling) | sched1 moves & h FIXED | …& FULL collision (STRICT NEUTRAL) |
|---|---|---|---|---|---|
| common | 255 | 254 | **252/254 = 99%** | 2 | **0** |
| m1 | 216 | 215 | **215/215 = 100%** | 0 | **0** |
| m2 | 237 | **0** | — | 0 | **0** |

**N=10 (weight≤3, ~60k tries/mode):**

| mode | da56=0 survivors | move sched1 | also move h (coupling) | sched1 moves & h FIXED | …& FULL collision (STRICT NEUTRAL) |
|---|---|---|---|---|---|
| common | 75 | 75 | **75/75 = 100%** | 0 | **0** |
| m1 | 64 | 64 | **64/64 = 100%** | 0 | **0** |
| m2 | 48 | **0** | — | 0 | **0** |

→ **N=10 STRICT neutral rank = 0/10** (and even the weak da56=0∧Δh=0 rank = 0/10 — at N=10 not
a single da56=0 perturbation decouples sched1 from h, not even the collision-breaking kind).

**Two observations sharpen the verdict (both N):**
1. **m2 moves sched1[60] in 0 cases** (0/237 @N=8, 0/48 @N=10) — confirming sched1[60] is a
   *message-1 absolute* quantity (perturbing only M2 cannot touch it), exactly as the
   structural premise stated.
2. The coupling is **99–100%**: nearly every da56=0 perturbation that moves sched1 also moves
   h. At N=8 the only 2 exceptions (common mode) that keep h fixed **break the full collision**
   (+collision = 0); at N=10 there are zero exceptions at all. So the **strict** neutral rank
   (sched1 moves ∧ h-exact ∧ FULL collision) is **0** at both widths.

This rules out the "da56 is just rare" objection: with dozens-to-hundreds of da56=0 survivors
examined per mode, the absolute↔differential coupling is essentially total, and **no**
perturbation clears the full neutral bar.


---

## Why (mechanism, and why it was the expected outcome)

`sched1[60] = σ1(w58) + W1p[53] + σ0(W1p[45]) + W1p[44]`. Its message-dependence enters only
through the **precompute schedule words** `W1p[44], W1p[45], W1p[53]`. But in SHA's message
schedule those words are built by the recurrence `W[k]=σ1(W[k-2])+W[k-7]+σ0(W[k-15])+W[k-16]`
from essentially **all** of M[0..15], and the **same** message words also determine the
precompute state `st1[0]` (the da56 condition) and the cascade states feeding `h`. There is no
message word that touches `W1p[44,45,53]` without also touching da56 / the cascade / h.

The structural insight predicted the escape hatch — a **common-mode** δ keeps the
XOR-difference fixed *to first order*, so it "should" move the absolute sched1[60] while
leaving the differential h untouched. The probe shows that hope dies on the **carry / Ch / Maj
nonlinearity** (the sweep's central finding, "the hardness IS the carry nonlinearity"):
da56 = st1[0]−st2[0] is itself a *differential* quantity computed through 57 nonlinear rounds,
and common-mode δ shifts it via the carry coupling in essentially every case (da56=0 survives
in 0/128 single-bit common-mode perturbations). The absolute↔differential coupling the insight
flagged as the risk is **total** at the measured widths: neutral bits = the perturbations where
it vanishes, and there are **none**.

---

## Verdict (one paragraph, honest caveats)

**The decouple is BLOCKED.** Across N=8 and N=10, the GF(2) rank of free g1-control obtainable
from differential-preserving message perturbations is **0** — there are no message neutral
bits that slide sched1[60] while holding the cascade (da56=0) and h fixed, so g1 gains **zero**
free bits and sr=60→61 remains the full `2^-2N` (two independent conditions g1=0 ∧ h=0). This
is the *consistent-with-the-sweep* outcome: it is the message-space analogue of OC2's
tail-word result ("w60 moves g1 but cannot move h"), now closing the **other** lever — the
absolute message target sched1[60] cannot be moved free of the differential because the same
nonlinear precompute couples them. **Honest caveats:** (1) this is verified at small widths
N=8, 10 within the MSB-kernel cascade-DP construction (the one the boundary proof and all sr=60
collisions live in) — it is a sharp *no-neutral-freedom* result for that construction, not an
impossibility proof for some unknown single-block mechanism; (2) the perturbation search is
exhaustive only up to low Hamming weight (single-bit, weight≤2 ball, and a weight≤3 adversarial
deep-dive) plus the unconstrained-vs-constrained rank contrast — a high-weight neutral
direction that is invisible to weight≤3 and to the rank span cannot be fully excluded, though
the total absolute↔differential coupling among **all** da56=0 survivors (deep-dive) makes one
very unlikely; (3) the rank metric is a first-order/affine-span object on the exact carry
cascade, the honest local linearization these probes use. Within those bounds: **neutral bits
do not exist; the sr=61 decouple does not work.**

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/neutral_bit_probe.py`
(prints the cross-engine (g1,h) validation, the rank table, and the coupling deep-dive).
