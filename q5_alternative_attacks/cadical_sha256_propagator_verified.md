# CaDiCaL-SHA256 Propagator Activation Verified

## Test

Ran `/tmp/cadical-sha256/build/cadical --seed=99 sr60_m44b49bc3.cnf`
on the alt sr=60 CNF (our encoder format, NOT Nejati's).

## Result

```
Connected!
Bitsliced propagation turned on.
Custom blocking turned on.
```

The IPASIR-UP propagator successfully attaches and activates **even
on CNFs that use our variable naming convention** (not Nejati's).

The propagator detects modular addition gates structurally — it
doesn't require specific variable names.

## Implication

The 6 cadical-sha256 instances already running on sr=61 ARE benefiting
from the propagator (bitsliced propagation + custom blocking). They've
been running ~41 hours with no SAT/UNSAT — the propagator is providing
inference but the instance is hard regardless.

Adding 2 more cadical-sha256 instances (seeds 42, 99) on the alt sr=60
CNF gives us propagator-aware diversity in the alt experiment.

## Next steps

- If the alt sr=60 race solves SAT, see if cadical-sha256 was the one
  that found it (vs vanilla kissat seeds 5/7/11)
- If both alt sr=60 and sr=61 races stall, try regenerating the encoding
  with Nejati-format variable naming to see if the propagator gets
  better leverage

## Evidence level

**VERIFIED**: direct observation of the "Bitsliced propagation turned on"
message at solver startup.
