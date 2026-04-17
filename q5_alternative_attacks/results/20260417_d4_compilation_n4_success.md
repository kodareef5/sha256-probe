# d4 Top-Down Compilation: N=4 SUCCESS (49 models in 39s)

**Date**: 2026-04-17 ~16:00 UTC
**Evidence level**: VERIFIED

## Result

d4v2 (top-down d-DNNF compiler with CDCL) successfully compiled the
N=4 sr=60 CNF (1162 vars, 4828 clauses) and counted exactly **49 models**
in **39 seconds**.

- 559 recursive calls
- 279 decisions
- 0 cache hits (small instance, no sharing)

## Comparison

| Method | N=4 result | Time | Memory |
|--------|-----------|------|--------|
| d4 (top-down CDCL) | **49 models ✓** | **39s** | OK |
| pysdd (bottom-up SDD) | KILLED | 7min+ | **10.5GB** |
| ROBDD Apply | 127K intermediates | Fast | High |
| Brute force | 49 ✓ | <1s | Trivial |

## Significance

d4's top-down approach with clause learning and component caching
**bypasses the intermediate blowup** that kills all bottom-up methods.
This confirms both Review 8 recommendations (Gemini: "use d4", GPT-5.4:
"AND/OR search with component caching").

## Next Test

Running d4 on N=8 (2544 vars, 10656 clauses, expected 260 models).
If it completes, knowledge compilation IS the path around the rotation frontier.
