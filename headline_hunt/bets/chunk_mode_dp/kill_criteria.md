# Kill criteria — chunk_mode_dp

## #1 — N=8 prototype cannot recover 260 with compact state

**Trigger**: N=8 prototype either:
- fails to enumerate the known 260 collisions (correctness failure), OR
- enumerates them but with a state count comparable to brute force (no compression).

**Required evidence**: `prototypes/n8_state_growth.md` showing state count vs.
N for N=4, 6, 8.

## Reopen triggers

- New quotient theory (e.g., from a BDD construction proof) suggests a workable
  mode set.
- A breakthrough on `programmatic_sat_cascade_propagator` reveals the right
  propagation/state structure that DP can also use.
