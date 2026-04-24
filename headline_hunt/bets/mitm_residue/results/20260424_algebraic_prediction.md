# Algebraic prediction of hard-residue positions in dh60 — VERIFIED

**Status**: Headline finding for `mitm_residue`. The cross-candidate amortization problem (open question from `20260424_cross_candidate_hard_bit_positions.md`) has a clean closed-form answer.

## Theorem (empirical, 6/6 candidates)

For a cascade-eligible candidate (m0, fill, kernel_bit) producing precomputed states (s1, s2) at round 56, the **uniform bits in dh60** at round 60 (= the empirical hard-residue bits in the h-register) are exactly:

```
{ i ∈ [1, 31]  :  (Δe57 mod 2^i) / 2^i  ∈  [0.45, 0.55] }
```

where:
```
Δe57 = (d1_56 − d2_56) + (h1_56 − h2_56)
       + (Sigma1(e1_56) − Sigma1(e2_56))
       + (Ch(e1_56,f1_56,g1_56) − Ch(e2_56,f2_56,g2_56))
       − cw57    (mod 2^32)

cw57 = (dh + dSigma1(e) + dCh + dT2)    (mod 2^32)
```

Computable in O(1) from the precomputed candidate state. No sampling required.

## Why this works

dh60 = de57 (3 shift-register hops at rounds 57→58→59→60).

de57 (modular) = const + cw57-derived offset = a fixed Δe57 per candidate.

For random R = e1_57 (uniform mod 2^32 since w1_57 is random and e1_57 = const + w1_57):
- e2_57 = R - Δe57 (mod 2^32)
- e1_57 XOR e2_57 = R XOR (R - Δe57)
- Bit i of (R XOR (R - Δ)) = Δ[i] XOR carry_in[i]
- P(carry_in[i] = 1) = (Δ mod 2^i) / 2^i

So |freq − 0.5| ≤ 0.05 exactly when (Δ mod 2^i) / 2^i ∈ [0.45, 0.55], assuming the threshold uses the carry probability rather than the XOR-frequency directly.

(For bits where Δ[i] = 1, the XOR-frequency is 1 − carry_prob; the threshold check is symmetric.)

## Verification

| Candidate | Δe57 | Predicted | Empirical (30k) | Empirical (1M) |
|---|---|---|---|---|
| MSB | 0xefef3e30 | [5, 10, 15, 21, 29] | [5, 10, 15, 21, 29] | (matches) |
| bit10_3304caa0 | 0xab634898 | [2, 7, 12, 19] | [2, 7, 12, 19] | (matches) |
| bit06_6781a62a | 0xd7decf19 | [1, 9, 25, 30] | [1, 9, 25, 30] | (matches) |
| bit17_8c752c40 | 0x75ec3127 | [6, 15, 21] | [6, 15, 21] | (matches) |
| bit19_51ca0b34 | 0xe12e3f7a | [2, 8, 15, 30] | [2, 8, 15, 21, 30] *(noise; 1M shows bit 21 freq=0.5543, just outside threshold)* | [2, 8, 15, 30] |
| bit13_916a56aa | 0xa7e0ad69 | [1, 11, 21, 26] | [1, 11, 21, 26] | (matches) |

The bit19 "mismatch" at 30k samples was empirical noise: predicted carry-prob at bit 21 is 0.4452 (just outside the 0.45 threshold), and the 1M-sample empirical XOR-frequency is 0.5543 (just outside 0.55). At 30k samples this lands inside the threshold by chance. Increasing sample size or tightening the empirical threshold to match the analytical [0.45, 0.55] resolves the discrepancy. **The algebraic prediction is correct.**

## Implications for `mitm_residue`

The bet's main amortization concern was: hard-bit positions vary per candidate, so a forward-table built for one candidate doesn't apply to another. Cross-candidate sweep (`20260424_cross_candidate_hard_bit_positions.md`) showed Jaccard 0.08-0.47 across 6 candidates, no shared bits.

The algebraic prediction RESOLVES this by giving a per-candidate signature in O(1) time:

1. **Pre-screen candidates**: compute Δe57 per candidate, predict hard-bit count, sort. Pick candidates with the SMALLEST predicted residue (best Wang-attack target).

2. **Build per-candidate forward tables analytically**: the table key set is computable; the table population is then per-candidate empirical (or predicted via further extension of this analysis to f60, g60).

3. **Avoid sampling per candidate**: `hard_residue_analyzer.py` is no longer needed for new candidates — replace with a fast prediction call.

The bet's economic outlook tightens significantly. Full pre-screen of all 35 candidates in `candidates.yaml` is now ≤1 second of CPU.

## Extensions (open follow-ups, none yet completed)

- **f60 prediction**: f60 = de59 = dT1_59. Same form but Δe59 depends on cw57, cw58, cw59 in chain. Should be derivable.
- **g60 prediction**: g60 = de58. Similarly chained.
- **Joint hard-bit count** = |predicted-uniform(f) ∪ predicted-uniform(g) ∪ predicted-uniform(h)|. This is the per-candidate forward-table key width.
- **Pre-screen all 35 candidates** in `candidates.yaml`, identify the candidate with smallest joint hard-bit count, pin it as the priority MITM target.

f60 and g60 are next-action items — both <1 day to derive given the dh60 derivation as template.

## Reproduce

```python
import sys; sys.path.insert(0, '/path/to/sha256_review')
from lib.sha256 import precompute_state, K, MASK, Sigma0, Sigma1, Ch, Maj

m0, fill, kbit = 0x17149975, 0xffffffff, 31
M1=[m0]+[fill]*15; M2=list(M1); M2[0]^=1<<kbit; M2[9]^=1<<kbit
s1,_=precompute_state(M1); s2,_=precompute_state(M2)

dh = (s1[7]-s2[7]) & MASK
dSig1 = (Sigma1(s1[4])-Sigma1(s2[4])) & MASK
dCh = (Ch(s1[4],s1[5],s1[6])-Ch(s2[4],s2[5],s2[6])) & MASK
T2_1 = (Sigma0(s1[0])+Maj(s1[0],s1[1],s1[2])) & MASK
T2_2 = (Sigma0(s2[0])+Maj(s2[0],s2[1],s2[2])) & MASK
cw57 = (dh + dSig1 + dCh + (T2_1-T2_2)) & MASK

dd56 = (s1[3]-s2[3]) & MASK
de57_mod = (dd56 + dh + dSig1 + dCh - cw57) & MASK

predicted = [i for i in range(1,32)
             if 0.45 <= ((de57_mod & ((1<<i)-1)) / (1<<i)) <= 0.55]
print(predicted)  # → [5, 10, 15, 21, 29]
```
