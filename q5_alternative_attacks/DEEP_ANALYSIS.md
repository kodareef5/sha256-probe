# Deep Analysis: Why sr=60 is Hard and How to Break It

## The Branching Model

The signed-difference expansion model (Li et al.) reveals that modular
addition creates BRANCHING POINTS where the solver must choose between
two valid carry-propagation paths. The number of branching points is
proportional to the number of ACTIVE BITS (non-zero signed diffs).

For each addition with A active input bits:
- ~44% of input combinations create 2-way branches
- Each active bit contributes ~0.44 expected branching points
- Total branching: ~0.44 × A per addition

## Why da57=0 is the Only Strategy

**de57=0 is UNSAT in 0.2s** because:
- Zeroing de57 forces dW57 such that da57 has hw=8-21
- This da57 error propagates as db58, dc59 (shift register)
- The Maj function at round 58 gets TWO non-zero inputs (b58, c58)
- Combined with de57=0 (which forces non-zero a57), the constraint
  geometry collapses: Kissat proves impossibility instantly

**da57=0 is hard (timeout)** because:
- Zeroing da57 creates the ZERO WAVE: a57=0 → b58=0 → c59=0 → d60=0
- This wave eliminates branching in the Maj/Sigma0 path for 3 rounds
- The error flows through de57 only, which feeds Ch(e,f,g)
- The solver must navigate the e-register error through 6 more rounds

## The Fundamental Bottleneck: de57 Error

When da57=0, the de57 error determines difficulty:
- de57_err = HW of the e-register error after fixing dW57 for da57=0
- This error propagates as: df58, dg59, dh60 (shift register)
- AND feeds into Ch(e57,f57,g57) → non-linear interaction

Published candidate (0x17149975): de57_err = 21
Best candidate (0x44b49bc3):     de57_err = 11

10 fewer active bits = ~4.4 fewer branching points PER ADDITION.
Over 10 additions in 6 rounds = ~44 fewer branching points total.
That's 2^44 less search space — potentially the difference between
TIMEOUT and SAT.

## The Carry Expansion Branching Table

From Li et al.'s expansion model (13 valid transitions):

| Input | Carry_in | Output | Carry_out | Branch? |
|-------|----------|--------|-----------|---------|
| 0 | 0 | 0 | 0 | No |
| 0 | n | n | 0 | |
| 0 | n | u | n | ** YES ** |
| 0 | u | u | 0 | |
| 0 | u | n | u | ** YES ** |
| n | 0 | n | 0 | |
| n | 0 | u | n | ** YES ** |
| n | n | 0 | n | No |
| n | u | 0 | 0 | No |
| u | 0 | u | 0 | |
| u | 0 | n | u | ** YES ** |
| u | n | 0 | 0 | No |
| u | u | 0 | u | No |

Branching occurs when a non-zero diff meets a zero (or vice versa).
When TWO non-zero diffs meet, they CANCEL (no branching).
When a diff meets a carry of the SAME SIGN, they also combine without branching.

**Implication for trail design:** A trail where active bits are CLUSTERED
(adjacent positions all active) produces LESS branching than one where
active bits are SCATTERED. This is because adjacent active bits interact
via carry chains that reduce to the deterministic cases (n+n→0,n or u+u→0,u).

## What Would Break sr=60

1. **Lower de57_err**: Candidate 0x44b49bc3 has de57_err=11, reducing
   the branching by ~2^44 compared to the published candidate.
   Combined with the partition solver (fixing bits of W[58]), this
   could make the problem tractable.

2. **Clustered active bits**: If de57 has its 11 active bits CLUSTERED
   in a few consecutive positions rather than scattered across all 32,
   the carry interactions would be largely deterministic.

3. **Programmatic SAT**: Bitsliced propagation (Alamgir et al.) can
   detect and prune invalid carry patterns during search, avoiding
   the full 2^branching exploration.

4. **Multi-block attack**: A second compression block gets 256+512 bits
   of freedom. Even with de57_err=21, a second block could correct
   the residual.

## Why Wang Modification Changes Everything

Standard SHA-256 collision attacks use Wang-style message modification:
- **Basic modification**: directly set W[i] to force conditions (probability 1)
- **Advanced modification**: modify earlier W[i] to fix later-round conditions
  without disturbing already-satisfied ones

For sr=60 with W[57..60] free:
- W[57..60] can be SET DIRECTLY to satisfy conditions in rounds 57-60
- This is BASIC modification ��� probability 1, no search needed
- The only "search" is for W values that simultaneously satisfy the
  schedule constraints for W[61..63] AND the collision condition

**This is not a SAT problem — it's a message modification problem.**
The SAT solver is brute-forcing something that message modification
can solve deterministically for many bit positions.

The da57=0 constraint is already a form of basic modification (fixing
dW[57] to zero the a-register). Extending this:
- Fix dW[57] for da57=0 (1 condition, 1 free word consumed)
- Fix dW[58] to minimize da58 or de58 error (1 condition, 1 word)
- Use W[59], W[60] for the remaining conditions
- Only the bits that CAN'T be deterministically set need SAT solving

**Estimated improvement**: If basic modification can deterministically
satisfy 60-80% of the collision conditions, the residual SAT problem
has ~50-100 effective bits of search instead of ~256. That's the
difference between TIMEOUT and SAT in seconds.

## A-Path Cascade Cannot Use All Free Words (2026-04-06)

Using all 4 free words for a-path zeroing (da57=da58=da59=da60=0):
- Produces 4 zero registers (a,b,c,d) after round 60
- BUT rounds 61-63 have NO free words (schedule-determined W[61..63])
- These 3 rounds must zero the remaining 4 non-zero e-registers
- The e-path accumulates error from de57 (~11-16 bits) through 6 rounds
- 3 fixed rounds CANNOT zero 4 non-zero registers

IMPLICATION: The solver must BALANCE a-path and e-path control.
The da57=0 constraint commits 1 of 4 free words to the a-path.
The remaining 3 must jointly optimize BOTH paths — this is a 96-bit
joint optimization problem (3 words × 32 bits) with holistic
interactions through 6 rounds of SHA-256 compression.

## Experimental Summary (2026-04-05/06)

| Experiment | CPU-hours | Result |
|---|---|---|
| da57=0 × 6 candidates × 7200s | 12 | ALL TIMEOUT |
| da57+da58=0 × 1800s | 0.5 | TIMEOUT |
| 4-bit partition (16 × 1800s) | 8 | ALL TIMEOUT |
| 5-bit partition (32 × 3600s) | 32 | ALL TIMEOUT |
| 8-bit partition (256 × 3600s) | 256 (running) | 42/256 TIMEOUT so far |
| de57=0 × 6 candidates | instant | ALL UNSAT <0.5s |
| Alt gap W[58..61] × 3 | instant | ALL UNSAT <1s |
| Thermometer (256 partitions) | 0.1 | All identical |
| **Total** | **~310** | **0 SAT, 0 UNSAT (non-trivial)** |

## Next Steps

- Complete overnight 8-bit partition (214 remaining, ~8h)
- Run 10-bit timeout diagnostic (1024 parts × 60s) when cores free
- Implement eager carry propagation in CaDiCaL IPASIR-UP
- Extend signed-diff model to multiple rounds
- Explore whether the JOINT optimization can be decomposed differently
