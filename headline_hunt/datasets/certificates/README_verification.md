# sr=60 certificate verification

## Three verifier scripts in this folder

### `verify_sr60_default_message.py`
Tests: does running standard SHA-256 on `M = [0x17149975, 0xff, 0xff, ..., 0xff]`
(default message) produce the cert's W[57..60]?

**Result: NO.** The default schedule's W[57..60] differs from the cert's
W[57..60]. The default M is NOT the message that produces this collision.

### `verify_sr60_with_relaxed_W.py`
Tests: with W[0..56] from default M's schedule, W[57..60] OVERRIDDEN by cert
values, and W[61..63] extended by schedule recursion from the cert W[57..60]:
  - run all 64 rounds for both M1 and M2
  - check if final hashes match

**Result: YES.** Final hash matches cert hash
`ba6287f0dcaf9857d89ad44a6cced1e2adf8a242524236fbc0c656cd50a7e23b`. State
at slot 64 fully matches between M1 and M2 (8/8 components).

### `check_default_dW_vs_cw1.py`
Tests: at the slot-57-input state from default M, does the schedule's
dW[57..63] match the cw1[57..63] required for cascade-1 collision?

**Result: NO at every slot 57-63.** Cascade-1 in the standard schedule
fails at slot 57 already.

## What this means

The cert is a "schedule_compliance: 60 of 64" semi-free-start collision:
- 60 of 64 schedule equations are enforced (W[0..56] and W[61..63])
- 4 are RELAXED (W[57..60])
- Within this relaxation, M1 and M2 hash to the same value — **a real
  256-bit hash collision IN THIS MODEL**

This is NOT a full SHA-256 collision in the strict sense. It's a
**round-reduced semi-free-start collision** at sr=60 — extending Viragh
2026's sr=59 by one round if Viragh used the same relaxation model.

## To upgrade to a "real" SHA-256 collision

Find an M[0..15] (with kernel diff at positions 0 and 9) such that the
standard SHA-256 schedule produces W[57..60] satisfying cascade-1 + cascade-2
simultaneously. That's a 4×32 = 128-bit constraint on dW[57..60] derived
from 14×32 = 448 free message bits. Expected solutions: 2^320 in count, but
the constraints are nonlinear via sigma0/sigma1 modular arithmetic.

Kissat at TRUE sr=61 (cnfs_n32/sr61_n32_*_enf0.cnf) tests an extended
version of this: 5 cascade-1 alignments. 1800+ CPU-hours of search across
the project, 0 SAT found. Project's working hypothesis: sr=61 may be
structurally UNSAT (writeups/sr61_impossibility_argument.md, 47.9% XOR
conflict rate).

## Reproducibility

Run any of the three Python scripts with the project's lib/ on path:
```
PYTHONPATH=. python3 headline_hunt/datasets/certificates/verify_sr60_with_relaxed_W.py
```
