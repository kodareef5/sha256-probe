# Cross-candidate per-register HW distribution comparison
**2026-04-25 evening** — block2_wang residuals/by_candidate/

## Method

Same forward-run residual corpus generation across 3 candidates, all
MSB-kernel (bit-31), 200k samples, HW≤80 threshold. Compare per-register
mean Hamming weight at r=63 register XOR diffs.

## Result

| Corpus              | records | <a> | <b> | <c> | <e> | <f> | <g> | min totHW | da=de XOR |
|---------------------|--------:|----:|----:|----:|----:|----:|----:|----------:|----------:|
| MSB cert (m17149975)| 104,700 |15.19|15.17|14.87|15.17|15.16|14.88|        62 | 0/104,700 |
| **SURPRISE** (m9cfea9ce) | 3,735 |13.45|13.42|12.00|13.47|13.45|11.94|        62 | 0/3,735 |
| **BOTTOM** (m189b13c7)   | 3,787 |13.49|13.46|11.90|13.49|13.37|11.97|        63 | 0/3,787 |

## Structural finding

**SURPRISE and BOTTOM have ~2 bits lower per-register mean HW than the cert.**
- Per-register: ~13.0 (SURPRISE/BOTTOM) vs ~15.0 (cert)
- Total active-register HW (6 registers): ~78 vs ~90 — 12 bits lower mean

This is NOT visible from de58 image-size analysis alone. de58 measures W57 →
de58(r=58) variation; this measures the FULL r=63 residual structure under
random sampling.

**Implication for block2_wang**: SURPRISE and BOTTOM produce structurally
TIGHTER residuals on average than the cert. They're better starting corpora
for Wang-style trail search even though their min-HW floor is the same (62-63).

## c-register and g-register effect

Across all 3 candidates: **c and g have ~1 bit lower mean HW than a, b, e, f**:
- a, b, e, f: 13.4-15.2 mean
- c, g: 11.9-14.9 mean

This is consistent with R63.1 (`dc_63 ≡ dg_63 mod 2^32`) — c and g share modular
structure, which constrains their bit pattern in a way that other registers
don't share.

## Theorem 4 in XOR form: NEVER holds at r=63

`da_63 == de_63` (XOR-equality) is 0% across 104,700 + 3,735 + 3,787 = 112,222
records. Confirms the structural finding from earlier today: Theorem 4's
natural domain is r=61 modularly. At r=63, da and de differ. The MODULAR
relation `da_63 - de_63 ≡ dT2_63 (mod 2^N)` (R63.3) holds but XOR equality
doesn't.

## What this changes for the bet

- **Re-rank corpora by per-register mean HW**: SURPRISE/BOTTOM are
  structurally TIGHTER than cert. Should the block2_wang corpus seed
  preferences shift toward SURPRISE/BOTTOM for trail-search experiments?
- **Per-register R63.1 evidence**: the c-vs-g HW correlation gives a
  concrete observable for trail-search filtering (any candidate residual
  must satisfy `dc_63 ≡ dg_63` modularly, regardless of HW).
- **No XOR-Theorem-4 shortcut at r=63**: confirms the mitm_residue closure.
  Future Wang-trail design must use the modular form, not the simpler
  XOR form.

## Files

- `corpus_m9cfea9ce_fill00000000.jsonl` (3735 records)
- `corpus_m189b13c7_fill80000000.jsonl` (3787 records)
- `HW_DISTRIBUTION_COMPARISON.md` (this file)
- Compare to: `../CLUSTER_ANALYSIS.md` (cert-only earlier analysis)
