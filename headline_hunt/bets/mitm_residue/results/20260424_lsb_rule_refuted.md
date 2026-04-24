# Hard-bit prediction: LSB rule REFUTED

Hypothesis tested: "h60 uniform bits = bits >= lsb(cw57)" — the simplest predictor, based on the intuition that XOR-difference of (w + cw) varies for bits at or above where carries can propagate.

| Candidate | cw57 | lsb(cw57) | h60 uniform empirical | Jaccard(predict, empirical) |
|---|---|---:|---|---:|
| MSB | 0xd617236f | 0 | [5, 10, 15, 21, 29] | 0.16 |
| bit10_3304caa0 | 0x67d1a444 | 2 | (3 bits) | 0.10 |
| bit06_6781a62a | 0xfbafac35 | 0 | (4 bits) | 0.12 |
| bit17_8c752c40 | 0x8c959ec4 | 2 | (3 bits) | 0.10 |
| bit19_51ca0b34 | 0xbb196829 | 0 | (4 bits) | 0.12 |
| bit13_916a56aa | 0xcacc4464 | 2 | (4 bits) | 0.10 |

LSB rule predicts roughly all 32 bits uniform (since lsb(cw57) is 0-2 for these candidates), but only 3-5 are empirically uniform in h60. Jaccard 0.10-0.16 → bad fit.

The empirical h60_uniform set for MSB — `[5, 10, 15, 21, 29]` — has irregular spacing that suggests bit positions aren't determined by simple linear functions of cw57. The Sigma1 rotations (6, 11, 25) and SHR amounts in the SHA-256 small sigmas may be contributing more than the cw57 LSB.

**Implication**: simple algebraic prediction won't work. Either (a) need a richer model that incorporates Sigma1/Ch carry-propagation specifically, or (b) per-candidate empirical measurement is the only way.

The 200k-sample run takes ~10s/candidate via `hard_residue_analyzer.py`, so empirical measurement is cheap; the algebraic-prediction win was in fast pre-screening, not avoiding measurement entirely. Refuting LSB rule trims the search space for a future researcher.

Open: try a richer model — specifically, the bits that propagate through Sigma1's three rotations should be candidates for the structured (non-uniform) class. Could be a 2-day investigation, not 30min.
