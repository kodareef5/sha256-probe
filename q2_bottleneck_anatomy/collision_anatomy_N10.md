# Collision Anatomy: N=10 SAT Solution

## Extracted Free Words

| Word | Msg1 | Msg2 | dW (XOR) | HW |
|------|------|------|----------|-----|
| W[57] | 0x1f0 | 0x296 | 0x366 | 6 |
| W[58] | 0x01c | 0x2be | 0x2a2 | 4 |
| W[59] | 0x057 | 0x00d | 0x05a | 4 |
| W[60] | 0x164 | 0x1a7 | 0x0c3 | 4 |

## Schedule Differences (determined by free words)

| Word | dW (XOR) | HW |
|------|----------|-----|
| dW[61] | 0x0ef | 7 |
| dW[62] | 0x22f | 6 |
| dW[63] | 0x020 | **1** |

## Key Observations

1. **da57≠0**: The solver did NOT use the da57=0 strategy. dW[57] has hw=6.
   Our algebraic constraint (da57=0) is ONE valid strategy, but the solver
   found a DIFFERENT one with lower overall dW budget.

2. **dW[63] has hw=1**: The collision closes at the LAST round with
   almost-zero schedule difference. This means rounds 57-62 do the heavy
   lifting (accumulating and canceling state differences), and round 63
   provides the final nudge with minimal schedule interference.

3. **Low dW[58..60]** (all hw=4): The free words are chosen for minimal
   XOR difference across the pair. This minimizes branching in the
   schedule-determined rounds.

4. **dW budget**: total dW across free words = 6+4+4+4 = 18 bits.
   Schedule total = 7+6+1 = 14 bits. Grand total = 32 active bits
   across all 7 schedule words.

## Implication

The SAT solver's strategy is NOT da57=0. It prefers BALANCED low-HW
differences across ALL words rather than zeroing one register.

For N=32: the optimal strategy may be to constrain TOTAL dW budget
(sum of HW across all free words) rather than zeroing specific dW values.
This is a different optimization target than our GPU sweeps have used.

## Evidence Level

EVIDENCE: single N=10 solution analyzed. Would need multiple solutions
(different seeds, different candidates) to confirm pattern is universal.
