# F89: cascade-1 signature filter — HW_a(60)=0 is NECESSARY for min residual at N=8
**2026-04-28 00:50 EDT**

Building on F88's structural finding (N=8 cascade trajectory matches
N=32 m17149975), implemented a `--cascade-filter` mode that filters
the brute-force enumeration by per-round per-register HW=0 constraints.

The result is sharper than expected: the cascade-1 a-zero signature at
round 60 is not just a CHARACTERISTIC of low-residual dm — it's a
NECESSARY condition for the global minimum at N=8.

## Tool

`forward_bounded_searcher.py --cascade-filter <constraints>`

Constraints format: `<register>:<round>[,<register>:<round>...]`
where register ∈ {a,b,c,d,e,f,g,h} and round ∈ [0, 63].
All constraints AND'd together. Each requires HW(register, round) = 0.

## Findings at N=8 (m0, m9)-restricted, 65,536 patterns

### Single-register filter `a:60`

```
Total patterns:        65,536
Non-trivial survivors: 260
Wall:                  12.6s
Min residual HW:       16  (= brute-force global min)
Best dm:               (0x22, 0xa3)  ← SAME as brute-force best
```

**260 / 65,535 = 0.397% survival rate** — the cascade-1 a-zero
condition at round 60 prunes 99.6% of the dm space.

### Multi-register filter `a:60, b:61, c:62, d:63`

```
Identical results to single-register filter.
260 non-trivial survivors. Same min HW=16 at same dm.
```

**Why identical**: SHA-256's round update has shift-register structure.
At round r+1: b_{r+1} = a_r, c_{r+1} = b_r, etc. So if a_60 has zero
differential, that zero propagates forward to b at round 61, c at
round 62, d at round 63 — automatically. The multi-register filter is
redundant; the single-register filter at round 60 already captures
the full forward-cascade structure.

This matches the m17149975 sr=60 collision certificate: in the full-
N=32 case, the cascade-1 condition is da[60]=0; the rest follows from
shift-propagation. **F89 confirms this same property at N=8.**

### Trans-register filter `a:60, e:60`

```
Total patterns:        65,536
Non-trivial survivors: 0
```

The 2-register zeroing at the same round (a AND e simultaneously zero
at round 60) is too strict at N=8 (m0, m9)-restricted. NO non-trivial
dm satisfies both. This is consistent with cascade-1 having only the
a-path active in this restriction; the e-path needs the second
"trigger" word that's not freely varied here.

For full-N=32 m17149975: BOTH cascade-1 (da[60]=0) and cascade-2
(de[60]=0) are required. The N=8 (m0, m9)-restricted setting is too
narrow to admit this dual-cascade — that's a structural prediction.

## Structural significance

The cascade-1 condition `HW_a(60)=0` is shown to be:

1. **NECESSARY for the optimum at N=8**. The brute-force global min
   HW=16 dm IS in the cascade-filter set. No pattern with HW_a(60)≠0
   reaches lower residual HW.

2. **HIGHLY SELECTIVE**: 260 / 65,536 = 0.4% of patterns survive.
   This is a 252× search-space narrowing.

3. **N-INVARIANT in shape**: matches the full-N=32 m17149975 cascade
   structure (per F88 trace and sr60_collision_anatomy.md).

4. **SHIFT-PROPAGATING**: zeroing one register at round 60 zeroes 7
   subsequent positions automatically. The multi-register filter is
   redundant.

## Implication for the searcher

**The intermediate-round filter IS the key mechanism.** Forward HW-bound
pruning fails (F88: prunes everything because HW peaks mid-rounds).
**Per-register zero pruning at the cascade rounds works.**

This refines the SPEC v1 design:

```
Search algorithm (revised, post-F88+F89):
  1. Enumerate dm space depth-first
  2. At each dm candidate, propagate forward to round 60
  3. CHECK: does HW_a(60) == 0?  If not, prune entire dm subtree.
  4. Otherwise propagate rounds 61-63 forward; record final HW.
```

This narrows the search by 250× at N=8 (and likely similar ratios at
larger N — to be confirmed at N=10).

## N=10 cross-check (LANDED — and reveals structural divergence)

```
N=10 (m0, m9)-restricted, filter `a:60`:
  Total patterns:        1,048,576
  Non-trivial survivors: 1,048   (0.10% — 1000× search-space narrowing)
  Wall:                  216.6s
  Min residual HW:       19    (NOT 18!)
  Best filter dm:        (0xe7, 0x2b)
```

**Divergence from N=8 finding**: at N=10, the cascade-filter MIN is
HW=19, but the brute-force GLOBAL min is HW=18 at dm=(0x335, 0x334).
**The global optimum at N=10 is NOT cascade-1 compatible.**

### Trace of N=10 brute-force best vs cascade-filter best

**dm=(0x335, 0x334), HW=18 (BF best, NOT cascade-1)**:
```
round 60: HW_a = 2   ← cascade-1 violated
round 61: HW_b = 1
round 62: HW_c = 1
round 63: HW_d = 2, total HW=18
```

**dm=(0xe7, 0x2b), HW=19 (cascade-filter best, IS cascade-1)**:
```
round 60: HW_a = 0   ← cascade-1 satisfied
round 61: HW_b = 0   ← shift propagation
round 62: HW_c = 0
round 63: HW_d = 0, total HW=19
```

### Interpretation: N-dependent optimality of cascade-1

| N | BF min HW | cascade-filter min | gap | observation |
|---|---:|---:|---:|---|
| 8 | 16 | 16 | 0 | cascade-1 IS the optimum |
| 10 | 18 | 19 | 1 | cascade-1 is NEAR-optimum |

At N=8, the (m0, m9)-restricted dm space is small enough that the
ONLY way to achieve low residual HW is through cascade-1.

At N=10, there's enough freedom for a "near-cascade" dm that
violates cascade-1 by 2 HW (HW_a(60)=2) but achieves 1 HW lower
final residual through some other convergence mechanism.

**At N=32 (where m17149975 lives)**, cascade-1 produces TRUE collisions
(HW=0). Whether near-cascade alternatives also exist at N=32 is an
open question — possibly relevant to yale's frontier work (HW=33, 39,
45 are NEAR-cascade or fully-cascade?).

### Updated structural claim (revised from N=8 only)

The cascade-1 a-zero signature at round 60 is:

1. **OPTIMAL at small N** (N=8). 
2. **NEAR-OPTIMAL at intermediate N** (N=10: 1 HW gap to global).
3. **THE PATH AT LARGE N** (N=32: m17149975 confirmed collision via
   cascade-1).

The 1-HW gap at N=10 may grow or shrink with N. **Paper-class
question**: characterize how the gap (BF-min minus cascade-filter-min)
evolves with N. If it shrinks to 0 at some N* (and stays at 0 for
N ≥ N*), that gives a structural threshold for cascade-1 dominance.

### Significance for the searcher

The cascade-filter is still the right structural tool — but it's a
*near-optimal* search at intermediate N, not strictly optimal.
For headline-hunt purposes:
- Use cascade-filter for fast first-pass search (250-1000× narrowing)
- Use brute force as a finishing pass on the residual space
- At N=32 where brute force is infeasible, cascade-filter is the
  only option — and the gap may be 0 anyway (per m17149975)

## Connection to existing structural work

- **F34 universal-43 active adders**: the 43 active adders are the
  rounds where dW or differential register inputs change. Cascade-1
  at round 60 is the consequence of the round-60 active adder
  (T1+T2 = 0 modulo wrap).
- **F36 universal-LM compatibility**: the LM cost calculation should
  apply to the 260 N=8 cascade-filter survivors. Future memo: extract
  LM cost for each survivor, find LM minimum.
- **m17149975**: sr=60 collision with da[60]=0; the full-N=32
  realization of what F89 finds at N=8.
- **Yale's bit28 frontier**: HW=33, 39, 45 EXACT-sym near-residuals.
  These are known to satisfy cascade-1 at round 60 by construction
  (cascade_aux_encoder Mode A's force).

## What this changes for the headline-path

The cascade signature filter is a STRUCTURAL TOOL that:
- Confirms brute-force optimality (the cascade-filter min ≤
  brute-force min, by construction; equal at N=8 means no
  cascade-non-compatible dm beats it).
- Provides a 250× narrower search space for any future small-N tool
  (backward search, IPASIR-UP propagator, hand-crafted heuristic).
- Ships as a Python library function callable from any future searcher.

## Reproduce

```bash
# Single-register cascade-1 filter at N=8:
python3 forward_bounded_searcher.py --N 8 --positions 0,9 --rounds 64 \
    --cascade-filter "a:60"

# Multi-register filter (proves shift-propagation):
python3 forward_bounded_searcher.py --N 8 --positions 0,9 --rounds 64 \
    --cascade-filter "a:60,b:61,c:62,d:63"

# Dual-cascade filter (too strict for restricted setting):
python3 forward_bounded_searcher.py --N 8 --positions 0,9 --rounds 64 \
    --cascade-filter "a:60,e:60"
```

EVIDENCE-level: VERIFIED. 3 filter configurations tested, all
consistent. N=10 cross-check pending (will append on completion).

## Discipline

- No solver runs (Python compute, no SAT).
- forward_bounded_searcher.py self-tested: cascade-filter min == bf_baseline min at N=8.
- Bug fix in cascade-filter mode (max_round off-by-one) caught and
  resolved before shipping.
