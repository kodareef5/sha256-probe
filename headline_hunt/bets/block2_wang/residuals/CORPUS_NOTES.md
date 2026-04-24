# Block-1 residual corpus — notes

## First-pass data (2026-04-24, MSB candidate, 200k random samples)

`corpus_msb_200k_hw96.jsonl` — 104,700 records (residuals with total HW ≤ 96 at round 63).

Distribution highlights:
- **Min total HW: 62** (top result; active in {a,b,c,e,f,g}, never d or h)
- HW distribution: 62..125 across all 200k samples; concentrated near 96 (50% of max possible 192)
- d63 and h63 are **always zero** (cascade structure: d63 from cascade-1, h63 from cascade-2)
- Active register pattern is structurally `[a,b,c,_,e,f,g,_]` for every residual — a cascade signature

## Reality check vs writeups/multiblock_feasibility.md

The multiblock writeup characterized residual structure at **N=4**: 49 collisions + 283 near-collisions with HW≤4. At N=32, random sampling produces a much harder distribution — minimum HW=62 in 200k samples. To find HW≤16 residuals (the threshold for Wang differential attacks), we'd need either:
- Astronomical random samples (extrapolating, ~2^40 attempts)
- Hill-climbing search (existing tool: `q4_mitm_geometry/cascade_hillclimb.py`)
- Algebraic construction (e.g., via the cascade-aux encoding to constrain residual HW)

## Existing hill-climb tools (recommended)

The block2_wang residual corpus build should NOT use uniform random sampling at N=32. Instead, use:

- **`q4_mitm_geometry/cascade_hillclimb.py`** — hill-climbs (W[57..60]) to minimize round-63 residual HW. Likely produces HW≤24 residuals in feasible time.
- **`q4_mitm_geometry/cascade_forward_scan.py`** — broader scan; may complement hill-climb.
- **`q5_alternative_attacks/analyze_near_collisions.py`** — analytical tool for studying the residual structure once a corpus exists.

## Concrete next-action

Before launching a million-sample random run, audit `cascade_hillclimb.py`:
- Does it run on the MSB candidate without modification?
- What HW threshold does it reach in 1 hour?
- Does it produce JSONL-compatible output that this corpus can ingest?

Once the hill-climb is working, the corpus build pivots from "random sample + filter" to "hill-climb + dedupe + cluster". That's the right architecture for the block-2 trail-search engine.

## Schema (current build_corpus.py output)

Each JSONL line:
```json
{
  "candidate": {"m0": "0x...", "fill": "0x...", "kernel_bit": int},
  "w1_57": "0x...", "w1_58": "0x...", "w1_59": "0x...", "w1_60": "0x...",
  "w2_57..w2_60": "0x...",
  "iv1_63": ["0x..." × 8],   # state at round 63 for message 1
  "iv2_63": ["0x..." × 8],
  "diff63": ["0x..." × 8],
  "hw63": [int × 8],
  "hw_total": int,
  "active_regs": ["a", "b", ...],
  "da_eq_de": bool
}
```

A residual is reproducible from `(candidate, w1_57..w1_60)` alone — the rest is for analysis convenience.
