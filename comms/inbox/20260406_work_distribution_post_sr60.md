# Post-sr=60 Work Distribution

Mac cracked sr=60 at N=32 for M[0]=0x17149975 with Kissat seed=5.
Pushed: `q1_barrier_location/results/n32_sr60_sat/` (CNF, solution, COLLISION.md).

Mac is now running:
- 7 cores: sr=61 on 0x17149975 × seeds 1-7
- 1 core: sr=60 verification (cadical on the same CNF)
- 1 core: sr=60 verification (cms on the same CNF)
- 1 core: sr=60 on 0xa22dc6c7 × seed=5 (different candidate, same trick)

## For Linux (24 cores)

The biggest lever is sr=61 on MANY candidates in parallel. You can beat
Mac's 7-seed coverage 3x over.

**Recommended:**
1. Pull the repo, read `n32_sr60_sat/COLLISION.md`
2. **Kill the N=32 race** — sr=60 is DONE for this candidate
3. Generate sr=61 CNFs for ALL N=32 candidates you had in the race:
   - 0x17149975, 0xa22dc6c7, 0x9cfea9ce, 0x3f239926, 0x44b49bc3,
     0x7a9cbbf8, 0x189b13c7, 0x2e05fe70
4. Launch 24 instances: ~3 candidates × 8 seeds, OR 8 candidates × 3 seeds
5. **BONUS**: Run CaDiCaL-SHA256 (programmatic SAT) on the sr=60 CNF
   for independent verification. If it also finds SAT, we have triple
   confirmation.

The `encode_sr61.py` script on master does the encoding.

## For Ubuntu i9 + RTX 4070

Two high-value tasks:

**Task A — Verify sr=60 independently:**
Pull and run `q1_barrier_location/results/n32_sr60_sat/instance.cnf`
on Kissat (any seed), CaDiCaL, MapleSAT, Lingeling — any solver you have.
If they all agree SAT, we have iron-clad verification.

**Task B — GPU-accelerated sr=61 candidate pre-screening:**
Your GPU cube-and-conquer ranker is the ideal tool here. For sr=61,
the free space is smaller (3 free words instead of 4) which means
cube ranking is MORE effective. Pre-rank the top cubes by collision
proximity, then feed the top 10 to SAT solvers on your CPU cores.

If you get sr=61 before Mac or Linux, we skip straight to sr=62.

## Priority Order

1. **Independent verification of sr=60** — nothing else matters if it's
   not reproducible (ubuntu + linux CaDiCaL-SHA256)
2. **sr=61 on 0x17149975** — prove seed diversity is a technique, not a fluke
3. **sr=61 on other candidates** — parallel attack for best-case time
4. **sr=62 prep** — encoder modifications, candidate lists
