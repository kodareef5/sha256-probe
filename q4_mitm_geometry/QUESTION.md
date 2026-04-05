# Q4: Can We Solve the Hard Residue Directly?

## The Question
The MITM analysis shows 232 of 256 anchor bits can be matched by forward/backward
simulation. Can we focus all compute on the remaining 24 hard bits (g60, h60)
and bypass the SAT solver entirely?

## What We Know
- Forward cone (r56→r60): 5 free words determine all 8 state registers at r60
- Backward cone (r63→r60): W[61..63] (schedule-determined) fix 3 state updates
- Intersection: 232/256 bits are "almost free" — the hard residue is in g60 and h60
- Scripts 71, 74, 75 exist as probes but are not operational MITM tools

## Open Questions
1. What is the exact information-theoretic cost of matching the 24 hard bits?
2. Can we build explicit forward/backward hash tables keyed on the hard residue?
3. How much memory does a table-based MITM require? Is it practical?
4. Does the hard residue shift location for different candidates?

## Strategy (strongest recommendation from external review)
Stop solving the whole tail uniformly. Solve the HARD RESIDUE:
1. Build forward partial state tables keyed only on bottleneck bits
2. Build backward partial state tables keyed only on bottleneck bits
3. Hash on compressed anchor signatures
4. Treat the easy 232 bits as "almost free" and spend all compute on the hard 24

Test at reduced word widths first to validate the approach.

## Key Tools (to build)
- Forward table builder: enumerate W[57..60] → extract (g60, h60)
- Backward table builder: enumerate schedule tails → extract (g60, h60) requirements
- Compressed meet: hash-based join on the hard residue
- Scripts 71, 74, 75 from archive/ as starting points

## See Also
- Issue #4 on GitHub
- ChatGPT review recommends this as THE highest-upside direction
