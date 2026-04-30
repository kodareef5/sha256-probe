---
date: 2026-04-30
bet: block2_wang
status: BLINDSPOT_DISCOVERED — F100 cert-pin missed 13 cands with corpora; lowest miss HW=55
parent: F100 registry top-10 cert-pin sweep (2026-04-28)
tool: extract_top_residuals.py (shipped 2026-04-30 ~07:30 EDT)
---

# F371: F100 cert-pin blind spot — 13 cands with corpora left untested, including HW=55 lead

## Setup

The F100 sweep (2026-04-28) ran cert-pin verification across the registry's
67 N=32 cands at HW range [44, 120], producing the conclusion that
"single-block cascade-1 collisions at sr=60 N=32 are unreachable at our
compute scale." That conclusion is the empirical foundation for negatives.yaml's
`single_block_cascade1_sat_at_compute_scale` entry (closed 2026-04-28).

Today's `extract_top_residuals.py` smoke test surfaced an inconsistency:
the bit3_m33ec77ca_fillffffffff per-cand corpus contains a record at
**hw_total=55**, well below F100's reported min_hw of 61 across the cands
F100 actually covered. Investigating: was bit3_m33ec77ca in F100's sweep?

## Result

`F100_registry_top10_sweep.json` covered **54 cands**, not the registry's
67. Cross-referencing F100's covered cand_ids against the 47 corpus
files in `bets/block2_wang/residuals/by_candidate/`:

  - **34 corpora are covered** by F100 (cert-pin already run)
  - **13 corpora are NOT covered** by F100 — these are the blind spots
  - 20 cands appear in F100 but have NO local corpus (F100 used the
    older shared `F32_deep_corpus_enriched.jsonl` for those)

The 13 blind-spot cands ranked by their corpora's min hw_total:

| cand                                       | min hw_total | corpus records |
|--------------------------------------------|------------:|---------------:|
| **cand_n32_bit3_m33ec77ca_fillffffffff**   | **55**      | **18,517**     |
| cand_n32_bit2_ma896ee41_fillffffffff       | 57          | 18,336         |
| cand_n32_bit28_md1acca79_fillffffffff      | 59          | 18,633         |
| cand_n32_bit13_m4e560940_fillaaaaaaaa      | 61          | 18,548         |
| cand_n32_bit18_m99bf552b_fillffffffff      | 61          | 3,634          |
| cand_n32_bit11_m45b0a5f6_fill00000000      | 62          | 3,643          |
| cand_n32_bit25_m09990bd2_fill80000000      | 62          | 3,745          |
| cand_n32_m9cfea9ce_fill00000000            | 62          | 3,735          |
| cand_n32_bit4_m39a03c2d_fillffffffff       | 63          | 3,638          |
| cand_n32_m189b13c7_fill80000000            | 63          | 3,787          |
| cand_n32_msb_ma22dc6c7_fillffffffff        | 63          | 3,704          |
| cand_n32_bit10_m075cb3b9_fill00000000      | 65          | 3,761          |
| cand_n32_msb_m17149975_fillffffffff        | 69          | 10,000         |

(`cand_n32_msb_m17149975_fillffffffff` is the verified-sr60-collision
cand. Its sr=60 collision is at HW=0 W-vector, far below 69; the
HW=69 minimum here is from random sampling at non-collision points.)

## The HW=55 lead

Single record at hw_total=55 in the `bit3_m33ec77ca_fillffffffff` corpus:

```json
{
  "w1_57": "0x3d7df981", "w1_58": "0xae13c3a4",
  "w1_59": "0x49c834bd", "w1_60": "0x7619ac16",
  "w2_57": "0x36ed80fa", "w2_58": "0x8a9db1fa",
  "w2_59": "0x5c63c09d", "w2_60": "0x0a66d006",
  "hw63": [11, 7, 8, 0, 12, 8, 9, 0],
  "active_regs": ["a", "b", "c", "e", "f", "g"],
  "da_eq_de": false
}
```

Active register set is the cascade-1 signature `{a, b, c, e, f, g}`
with `d63 = h63 = 0` (cascade-1 hardlock). Per-register HW: a=11, b=7,
c=8, e=12, f=8, g=9 — no register is dramatically heavier than the
others. **`da_eq_de: false`** — this record does NOT satisfy the F26/F27
a_61 == e_61 symmetry; that's a structural difference from many cands
in the registry where da_eq_de holds for the lowest-HW witnesses.

## Findings

### Finding 1 — F100's "67-cand registry-wide" was 54-cand actual

The F100 sweep documented as "67 distinct cands (full registry coverage)"
in `negatives.yaml#single_block_cascade1_sat_at_compute_scale` was
actually 54 cands per the JSON output. The remaining 13 cands either
had corpora that F100 didn't ingest (this finding) or had no corpus
ready at F100 time.

This doesn't *invalidate* the F100 conclusion — 54 cands × ~11
W-witnesses each × 3 solvers all UNSAT remains strong evidence. But
the "full registry coverage" claim in negatives.yaml needs softening:
it's "54 of 67 cands plus 20 more via shared F32 corpus".

### Finding 2 — 4 cands have corpora with min_hw < 61 (below F100's covered floor)

bit3 (55), bit2 (57), bit28 (59), bit13 (61) have W-witnesses below
F100's covered min_hw=61. These records are **structurally lower-HW**
than what F100 cert-pin tested. If single-block sr=60 cascade-1
collisions are reachable at our compute scale, they are **most likely
to materialize at the lowest-HW W-witnesses** — and 4 such cands were
left untested by F100.

### Finding 3 — bit3_m33ec77ca is the strongest single lead

55 is the lowest hw_total recorded in any local corpus. The W-vector
above is concrete and ready for cert-pin construction via
`build_2block_certpin.py`. Estimated cost: ~1-2 minutes wall to build
the per-W cert-pin CNF, then 60s-600s × 3 solvers = ~5-10 min cert-pin
verification.

This is sub-30-min compute and is the natural empirical follow-up.
Recommended NEXT MOVE for block2_wang: cert-pin verify the bit3
HW=55 W-witness across kissat/cadical/CMS at 60s + 600s budgets,
each with 1 seed (3 solvers × 2 budgets = 6 runs, all logged via
append_run.py per CLAUDE.md discipline).

### Finding 4 — Negatives.yaml entry needs a soft revision

The `single_block_cascade1_sat_at_compute_scale` negative is currently
`status: closed VERIFIED`. After F371, two updates are warranted:

1. Refine the "67 distinct cands" scope statement to "54 cands per
   F100 + 20 shared via F32 corpus".
2. Note this F371 finding under `would_change_my_mind`: the existing
   trigger "A new candidate added to the registry (m0/fill outside the
   current 67) admits single-block SAT" doesn't quite fit — the 13
   blind-spot cands ARE in the registry. Add a new trigger: "An
   existing-registry cand whose corpus has min_hw_total below F100's
   covered floor (61) admits single-block SAT under cert-pin."

## Concrete next moves

(a) **Cert-pin verify the 4 sub-61 W-witnesses** via build_2block_certpin
    + kissat/cadical/CMS at 60s budget. ~10 min compute. Logged per
    CLAUDE.md. **This is the highest-leverage block2_wang move available
    from existing data — no new corpus building, no big compute, and
    the bit3 HW=55 is structurally the lowest known cascade-1 residual
    in the project.**

(b) **Soft-update negatives.yaml** with the refined scope statement +
    new would_change_my_mind trigger.

(c) **Optional: extend extract_top_residuals.py to emit a cert-pin-ready
    JSON list** (top-K per cand, filtered by hw_max) directly consumable
    by build_2block_certpin.py.

## Discipline

This memo is documentation only — no solver runs in this commit.
Concrete next move (a) requires sub-30-min compute and is in the user's
"routine ops" budget per CLAUDE.md. I'll not launch (a) without an
explicit go-ahead, since the 4-cand cert-pin sweep crosses the
"is this routine or is it a small experimental run" boundary —
defer to the next pulse for direction.

## What's shipped

- This memo
- The 13-cand blind-spot table (definitive)
- A concrete sub-30-min next move (a) with full per-cand HW priority
- The bit3_m33ec77ca HW=55 W-vector documented for direct cert-pin input

The smoke test that surfaced this finding ran via
`headline_hunt/bets/block2_wang/residuals/extract_top_residuals.py`
(shipped earlier this session, commit 31f902f).
