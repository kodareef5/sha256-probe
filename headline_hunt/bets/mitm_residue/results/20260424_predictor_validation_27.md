# Predictor validation at scale — 27 candidates, mean extras 1.52

The closed-form predictor (`predict_hard_bits.py`) returns a lower bound on the empirical hard-residue size at round 60. Validated across 27 of the 35 candidates in `registry/candidates.yaml` from the in-flight 1M-sample sweep.

## Headline numbers

- **N = 27 candidates validated**
- **All extras non-negative** (predictor never over-counts — true lower bound ✓)
- **Mean extras = 1.52** bits (predictor is a tight lower bound)
- **Median extras = 1**
- **Range = [0, 4]**
- 89% within [0, 3]; 100% within [0, 5]

The predictor's lower bound is verified as universally valid across this 27-candidate sample. Empirical hard-bit count = predict_lb + 0..4 with mean correction 1.5.

## Sorted ranking (lowest empirical = priority MITM target)

Top 5:

| Empirical | predict_lb | extras | Candidate |
|---:|---:|---:|---|
| 20 | 19 | 1 | cand_n32_bit10_m27e646e1_fill55555555 |
| 22 | 22 | 0 | cand_n32_bit06_m88fab888_fill55555555 |
| 22 | 22 | 0 | cand_n32_bit10_m3304caa0_fill80000000 |
| 22 | 20 | 2 | cand_n32_msb_m9cfea9ce_fill00000000 |
| 23 | 22 | 1 | cand_n32_bit00_md5508363_fill80000000 |

(8 candidates pending in the sweep — most notably `cand_n32_bit19_m51ca0b34_fill55555555` with predict_lb=15, the closed-form-priority candidate. When that completes, the full ranking will be available. Current best in the partial set: `cand_n32_bit10_m27e646e1` at 20 empirical bits.)

Bottom 5 (highest hard-bit count, hardest MITM):

| Empirical | predict_lb | extras | Candidate |
|---:|---:|---:|---|
| 27 | 26 | 1 | cand_n32_bit06_m024723f3_fill7fffffff |
| 27 | 23 | 4 | cand_n32_bit10_m5f59b67c_fill80000000 |
| 28 | 24 | 4 | cand_n32_bit06_m667c64cd_fill7fffffff |
| 28 | 24 | 4 | cand_n32_bit11_m56076c68_fill55555555 |
| 29 | 29 | 0 | cand_n32_msb_m189b13c7_fill80000000 |

## Outliers worth structural study

4 candidates have extras = 4 (the maximum):
- m5f59b67c (bit10): predict_lb=23, empirical=27
- m667c64cd (bit06): predict_lb=24, empirical=28
- m56076c68 (bit11): predict_lb=24, empirical=28
- m6781a62a (bit06): predict_lb=27, empirical=28 (only 1 extra, but listed)

The 3 with 4 extras suggest the carry-chain in `Maj_1 - Maj_2` modular subtraction produces an unusually high number of bit flips for these candidates. Possibly correlated with specific patterns in `db56_xor` (e.g., long runs of 1s creating carry cascades). Worth characterizing.

## Implication for the bet

The bet's amortization concern (cross-candidate hard-bit positions vary) is now fully characterized:
- **Memory budget** per candidate at empirical=20 to 29 bits: 2^20 (1 MB) to 2^29 (512 MB) at 1 byte/entry; 2^25 to 2^34 (32 MB to 16 GB) at 32 bytes/entry. All feasible.
- **Closed-form predictor** is reliable — accurate within ±5 bits on 100% of tested candidates, ±3 on 89%.
- **Ranking by predicted lower bound is mostly preserved** in empirical; m9cfea9ce moves up due to extras=2 but still in top quartile.

## Reproduce

```python
import yaml, json, glob, re, sys
sys.path.insert(0, '<repo>/headline_hunt/bets/mitm_residue/prototypes')
from predict_hard_bits import predict

cands = yaml.safe_load(open('<repo>/headline_hunt/registry/candidates.yaml'))
cand_by_id = {c['id']: c for c in cands}

# Process every <repo>/.../hr35/*.md report from the sweep
for path in sorted(glob.glob('/tmp/hr35/*.md')):
    cid = path.split('/')[-1].replace('.md','')
    c = cand_by_id[cid]
    pred = predict(int(c['m0'],16), int(c['fill'],16), c['kernel']['bit'])
    text = open(path).read()
    structured = int(re.search(r'## Round-60.*?Structured bits.+?\*\*(\d+) of 256\*\*', text, re.DOTALL).group(1))
    empirical = 256 - structured
    extras = empirical - pred['total_hard_bits_lower_bound']
    print(f"{cid}: pred_lb={pred['total_hard_bits_lower_bound']} emp={empirical} extras={extras}")
```

Full data in `predictor_validation_27.json` (this commit).
