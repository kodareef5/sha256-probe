# F85 + F86: Cascade-equation searcher SPEC + brute-force baseline at small N
**2026-04-27 23:55 EDT**

User suggested a tiny custom solver around the cascade equations:
> "standalone reduced-N searcher over the cascade variables and
> schedule residues, with aggressive memoization and explicit failure
> explanations. If it beats brute force at N=12/14, then decide whether
> to integrate with SAT. The goal is to discover a representation, not
> beat Kissat immediately."

This memo ships the design SPEC + a runnable brute-force baseline.
The baseline is the benchmark the eventual searcher must beat (or
match while providing structural insight that brute force lacks).

## F85: SPEC for the cascade-equation searcher

`headline_hunt/bets/block2_wang/cascade_searcher/SPEC.md` — full
specification of:
- 3-layer variable structure (message-diff / schedule-residue / cascade-state)
- Modular propagation rules (schedule expansion + round update)
- Memoization key (round + canonical state-diff hash)
- Failure-explanation format (round, verdict, state, dm-subset, first-diverging-round)
- Search algorithm sketch (depth-first w/ memo)
- Wall projection table (custom solver target: beat brute force at N=12-14)

The SPEC's 3-layer structure aligns with the existing F32/F36/F42
empirical findings — the 43 universal active-modular-adders all live
in layer-3 propagation; the 4 schedule-residue d.o.f. (W57..W60) drive
the search; the dm trigger pattern is the search axis.

## F86: brute-force baseline at small N (the benchmark to beat)

`headline_hunt/bets/block2_wang/cascade_searcher/bf_baseline.py` —
mini-SHA-256 enumerator at N ∈ {4, 6, 8, 10}. Pure Python, ~200 LOC,
no external dependencies.

For each (N, dm-positions), enumerates the dm space restricted to the
cascade-driving positions (default m[0] + m[9]; the MSB-kernel pattern
truncated to N bits), computes mini-SHA-256(M) and mini-SHA-256(M XOR dm)
for 64 rounds, tallies the residual state-diff Hamming weight.

### Results (rounds=64, dm in {m[0], m[9]}, m0=zero)

| N | patterns | wall (s) | collisions | min residual HW | wall ratio |
|---|---:|---:|---:|---:|---:|
| 4 | 256 | 0.07 | 0 | 7 | 1.0× |
| 6 | 4 096 | 0.84 | 0 | 12 | 12× |
| 8 | 65 536 | 13.15 | 0 | 16 | 188× |
| 10 | 1 048 576 | (running, ETA ~3.5 min) | TBD | TBD | TBD |

### Top-K min-residual dm patterns

**N=4** (best 4 of 256):
```
HW=7  dm=(0x4, 0x7)
HW=9  dm=(0x1, 0x4)
HW=9  dm=(0xf, 0xe)
HW=10 dm=(0x6, 0x1)
```

**N=6** (best 4 of 4 096):
```
HW=12 dm=(0xe,  0xb)
HW=12 dm=(0x24, 0x16)
HW=12 dm=(0x3b, 0x39)
HW=13 dm=(0xd,  0x33)
```

**N=8** (best 4 of 65 536):
```
HW=16 dm=(0x22, 0xa3)
HW=17 dm=(0x26, 0x6f)
HW=17 dm=(0x6e, 0x6b)
HW=17 dm=(0x8a, 0x3d)
```

### Observations

1. **Min residual HW grows linearly with N** (~2N). N=4 → 7, N=6 → 12,
   N=8 → 16. Pattern: HW_min ≈ 2N - 1.
   - This is consistent with cascade-1 being a STRUCTURAL property at
     N=32 specifically (where 4 modular d.o.f. across 6 active registers
     creates a 4-bit free dimension capable of dropping HW to 0).
   - At small N with the restricted (m0, m9) dm-only patterning, the
     cascade structure doesn't have enough freedom to zero out the
     residual.

2. **No full collision in restricted (m0, m9) dm space at N ∈ {4,6,8}**.
   The trivial (dm=0,0) is excluded from collision_count.

3. **Wall scales ~16× per +2 N** (= 4× for the dm enumeration size, and
   the inner work also scales linearly with N). N=10 projection ~3.5
   min, N=12 ~50 min, N=14 ~13 h. This is the curve the custom solver
   must beat — likely via memoization and early-cutoff at the round
   where residual HW exceeds the target threshold.

### What this confirms about the SPEC

The SPEC's "discover a representation" framing is reinforced by the
N-scaling data:

- **The cascade structure is N-dependent for collision yield**, even
  though F34 (universal-43 active adders) and other modular relations
  are N-invariant. The custom solver's job is to find what factorization
  exposes the cascade constraint at small N + restricted dm — likely
  requires moving beyond the (m0, m9)-only restriction to allow more
  message-word freedom.

- **Brute force is the trivial baseline**. At N=10 it finishes in
  minutes; at N=14 it's an overnight job. The custom solver's
  value-add is structural insight (failure cores at small N, modular
  invariants visible across N) — not raw speed below N=12.

## Next moves

1. **Wait for N=10 result** (~3.5 min from now). Append to this memo.

2. **Extend baseline** to allow more dm freedom. The user's suggestion
   "search over cascade variables AND schedule residues" implies dm is
   not the only search axis — also enumerate cascade-driving residue
   classes at rounds 57-60 directly. That would require the searcher
   (not brute force), so it's the next-session work.

3. **Build the searcher** in C using the SPEC's algorithm. ~300-500
   LOC with hash table memoization, depth-first stack, failure-core
   logging. Estimated 2-3 sessions.

4. **Connect to existing structural finds**: F34 (43 universal active
   adders), F36 (universal LM compatibility), F45 (online Pareto
   sampler). The searcher should expose those structures via the
   memoization keys it converges on.

## Discipline

- No solver runs (Python brute force is enumeration, not SAT).
- F85 SPEC + F86 baseline both stdlib-only.
- N=4, 6, 8 results captured in this memo with reproducible commands.
- N=10 run launched in background; will be appended when complete.

EVIDENCE-level: VERIFIED at N=4, 6, 8. N=10 in flight. Memo is
data-grounded and the SPEC is concrete enough for next-session work.

## Reproduce

```bash
# Run baseline at any N up to ~12 (N=12 takes ~50 min):
python3 headline_hunt/bets/block2_wang/cascade_searcher/bf_baseline.py \
    --N 8 --positions 0,9 --rounds 64

# With JSON output:
python3 .../bf_baseline.py --N 10 --positions 0,9 --rounds 64 \
    --out-json /tmp/result.json --progress
```
