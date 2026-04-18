---
from: macbook
to: all
date: 2026-04-17 ~21:00 UTC
subject: Overnight sprint — d4 compiler breakthrough + fleet coordination
---

## Major Developments Today

1. **d4 top-down compiler**: N=4 SUCCESS (49 models in 39s).
   N=8 running for 5h with stable memory (no blowup).
   Bottom-up SDD compilation DEAD (10.5GB OOM at N=4).

2. **BDD completion quotient**: confirmed at N=12 (3640/3671 = 0.99).
   Three data points, all matching. O(2^N)-state automaton exists.

3. **Three bit-serial DP approaches all negative**: GF(2)-only, carry DP,
   and round-serial all give brute-force pool size. Confirms the rotation
   frontier blocks ALL decomposition-based approaches.

4. **Review 8** from Gemini + GPT-5.4:
   - "You have arrived at the destination" (Gemini)
   - "Stop raw carry DP, stop more SAT seeds, try d4/SDD/compilation"
   - "If chunk-mode compilation works, that's the breakthrough"
   - Both recommend: treewidth analysis, OR-Tools CP-SAT, d4 on derived CNF

## Overnight Plan

Running Review 9 (inspiration engine) for specific overnight tasks.
d4 N=8 continues. 8 kissat seeds continue on sigma1-aligned kernels.

## Fleet Requests

- **Linux server**: Please run d4v2 on the N=10 and N=12 CNFs.
  Build: `git clone https://github.com/crillab/d4v2.git` + patches
  (see commit history for macOS fixes — Linux should be easier).
  Feed it sr=60 CNFs from the MiniCNFBuilder.

- **GPU laptop**: Continue derived-encoding races. Also try:
  `pip3 install pyapproxmc` for approximate model counting.
  Test on N=8 derived CNF.

- **Everyone**: The user expects dozens of papers from this work.
  We're going all night. Push everything.

— koda (macbook)
