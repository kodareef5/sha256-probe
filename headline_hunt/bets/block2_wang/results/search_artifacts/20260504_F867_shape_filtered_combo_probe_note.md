# F867 Shape-Filtered Combo Probe Note

F865/F866 apply the new M2 shape filters from F864 to the best target-density
transfer branch from today:

```text
source: bit18 HW86
target: bit14 HW85 lane
atlas: F851
baseline combo: F852
```

Baseline F852, unfiltered:

- sampled combos: 1,000,000
- evaluated: 999,970
- HW<=86: 0
- target-L1-improving: 283
- best HW: 90
- best target: L1 12 at HW95

F865, strict shape filter:

- filter: `min_m2_removed=2`, `max_m2_net_added=4`
- sampled combos: 1,000,000
- evaluated: 0
- skipped by M2 shape: 999,983

F866, F788-like looser raw-detour shape:

- filter: `min_m2_removed=2`, `max_m2_net_added=8`
- sampled combos: 1,000,000
- evaluated: 3,964
- skipped by M2 shape: 996,009
- HW<=86: 0
- target-L1-improving: 1
- best HW and best target: HW99, L1 18, add9/remove2/net+7

## Interpretation

The apparent target-density in F852 mostly lives in over-additive combo space.
When we require even two removals and bounded net growth, the branch nearly
vanishes and the surviving candidates are much worse.

This supports the upstream-selector rule: target-density alone is not enough.
For sparse-source shelves, shape-aware selection must be built into the sample
itself, or the selector mostly rediscovers additive construction moves.
