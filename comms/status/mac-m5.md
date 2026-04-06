# mac-m5 Status

**Last updated:** 2026-04-05 21:00 EDT
**Cores:** 10 (M5) | **RAM:** 16GB | **Solvers:** kissat, cadical, cms

## Currently Running (7/10 cores)

| Task | N | Candidate | Elapsed | Timeout |
|------|---|-----------|---------|---------|
| N=23 cand2 | 23 | 0x622f3b, fill=0x400000 | 2.5h | 8h |
| N=26 cand2 | 26 | 0x5cc42c, fill=0x2000000 | 1h | 8h |
| N=27 race | 27 | 0xbde4ed, fill=0x7ffffff | 1.5h | 8h |
| N=27 seed42 | 27 | 0xc43281, fill=0xaa | 1.5h | 8h |
| N=27 seed42 | 27 | 0xd343de, fill=0xcc | 1.5h | 8h |
| N=28 seed42 | 28 | 0x14542a, fill=0x33 | 1.5h | 8h |
| (cadical) | 27 | 0xbde4ed (same as race) | 1.5h | 8h |

## Completed This Session

| N | Result | Time | Candidate |
|---|--------|------|-----------|
| 8-22 | SAT | 4s-2546s | various |
| 24 | SAT | 4206s | 0x221e85, fill=0x0 |
| 25 | SAT | ~5200s | 0xa0e50f, fill=0xaa |
| 23 cand1 | TIMEOUT | >4h | 0x25c53e, fill=0x400000 |
| 26 cand1 | TIMEOUT | >4h | 0x254c4a, fill=0x3ffffff |
| 24 cand2 | TIMEOUT | >4h | 0x241e51, fill=0x0 |
| 27 (3 cands) | TIMEOUT | >8h | kissat default seed |
| 28 (1 cand) | TIMEOUT | >8h | kissat default seed |

## Available Capacity

3 free cores. Can launch more work.

## Needs From Other Machines

- **linux-24core**: Run N=27 with ALL candidates in parallel (24 cores = 24 candidates). Single-candidate runs time out at 8h.
- **ubuntu-i9**: Try N=23/26/27 with CaDiCaL — different solver may crack what Kissat can't.
- **any**: If you find SAT at N=27+, share the candidate immediately.
