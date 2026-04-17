# SDD Compilation: Exponential Blowup on Raw CNF

**Date**: 2026-04-17
**Evidence level**: VERIFIED (N=4, killed at 10.5GB RAM)

## Test

Used pysdd (SDD library) to compile the N=4 sr=60 CNF (1162 vars, 4828 clauses)
by conjoining clauses one by one with a balanced vtree.

## Result

- 7 minutes runtime, 87% CPU
- **10.5GB RAM and growing** — killed before OOM
- Did NOT complete compilation

## Interpretation

Raw CNF-to-SDD compilation hits the SAME exponential intermediate blowup
as ROBDD Apply (127K intermediate nodes at N=4 vs 183 final). The balanced
vtree doesn't match the problem's structural decomposition.

Both Review 8 respondents predicted this:
- Gemini: "Use d4 (top-down CDCL-based), not Apply-style bottom-up"
- GPT-5.4: "AND/OR search with component caching, not raw SDD"

## Next Steps

1. Build d4v2 (top-down d-DNNF compiler with CDCL)
2. Try SDD with a custom vtree aligned to round/chunk structure
3. Preprocess CNF: XOR elimination, linear backbone removal
4. Try on the DERIVED encoder CNF (96 free vars instead of 192)

The key insight: bottom-up compilation (pysdd, CUDD Apply) always hits
the intermediate blowup. Top-down compilation (d4, c2d) uses CDCL to
navigate the space and may avoid it.
