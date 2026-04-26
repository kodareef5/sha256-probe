# HW4 floor checkpoint — 11 1B-trial walks summary
**2026-04-26 13:15 EDT**

After 11 1B-trial M5 surface61greedywalk runs (~11B trials, ~2.6 hours
wall on M5 with `-mcpu=apple-m4` + 10 OMP threads) the joint yale +
macbook campaign appears to have reached a **structural floor at D61=HW4
under random-flip greedy walks**. This memo summarizes the evidence
and the current open paths.

## The frontier

| objective | best | point |
|---|---:|---|
| round-61 defect | **HW4** | idx=0 `0x6ced4182,0x9af03606`; idx=8 `0x63f723cf,0x10990224` and `0x4197e38f,0x20b94223` |
| checked tail (full state @ slot 64) | **HW59** | idx=8 `0xe537c1c7,0x598feb25` (yale 3335040) |

**6-bit total D61 improvement** from yale's initial HW10. **17-bit total
tail improvement** from yale's initial HW76.

## HW4 is reachable on 2 cands × 3 distinct basins

| cand | sparse off58 | W58, W59 | defect61 |
|---|---:|---:|---:|
| idx 0 (msb_cert m17149975) | `0x00000021` | `0x6ced4182, 0x9af03606` | `0x80110200` |
| idx 8 (bit3_m33ec77ca) | `0x00010002` | `0x63f723cf, 0x10990224` | `0x41200001` |
| idx 8 (bit3_m33ec77ca) | `0x00010002` | `0x4197e38f, 0x20b94223` | (HW4 alt basin) |

Different cands, different sparse off58 chambers, different W coords,
different defect61 bit patterns — all HW4. **Structural reproduction.**

## HW4 basins are deep traps under greedy-flip

| HW4 base | trial budget | % HW4 hits | HW3-or-lower hits |
|---|---:|---:|---:|
| idx=0 (run15) | 1B | 99.30% | 0 |
| idx=8 (run17) | 1B | 99.94% | 0 |

Once the walker enters an HW4 basin, ~all exact-D60 hits are HW4.
Greedy-flip + Newton repair cannot escape downward at radius=32 / 80
passes / 1B trials.

## Histogram regime by starting basin

The walker geometry is starting-basin-dependent:

| starting basin | dominant exact-D60 D61 | sub-frontier reachable? |
|---|---:|---|
| HW8 (idx=3) | HW8 (40.5M / 1B) | ↓ HW6 (1.7M) |
| HW8 (idx=0) | HW8 (37.9M) | ↓ HW5 (2.1M) |
| HW8 (idx=8 cascaded) | HW8 (45 hits, gap) | ↓ HW7-HW5 (12.4M total) |
| HW7 (idx=8) | HW7 (42.4M) | ↓ HW5 (5.9M) |
| HW5 (idx=0) | HW5 (46.3M) | ↓ HW4 (660k) |
| HW5 (idx=8) | HW5 (46.3M) | locally trapped |
| HW4 (idx=0, idx=8) | HW4 (99%+) | NONE in 1B |
| HW59-tail (idx=8) | HW14 (29.3M) | ↓ HW4 (1.46M) |

Pattern: each starting basin can reach 1-2 D61 levels lower with
diminishing-but-not-zero rate, until HW4. From HW4, sub-D61 is
unreachable in 1B trials.

## What this evidence does NOT prove

- HW3 / HW2 / HW1 / HW0 don't exist on the exact D60=0 surface.
- Yale's structural cap-2 terrace (D60=HW7/D61=HW2 non-exact) cannot
  be repaired onto exact D60=0 by some carry-aware operator.
- Some other (m0, fill, bit) candidate doesn't have a structurally
  lower floor.

## What this evidence DOES suggest

- Greedy-flip + Newton-style repair is unlikely to reach D61<4 even at
  10B-100B trials. The 99%+ HW4 trap rate across two cands × three
  distinct basins makes random walks an exponentially-poor escape
  operator.
- HW4 is reachable from **wide-spectrum tail bases** (yale's HW59 tail
  point reaches HW4 at 1.46M / 1B = 0.146%) more easily than from HW5
  bases (660k / 1B = 0.066%). So *transition* states between basins are
  more permissive than basin centers — but not enough to cross HW4.

## Open paths forward (in order of expected info)

1. **Yale's carry-aware proposal operator** — can it close the
   D60-HW7/D61-HW2 cap-2 terrace onto exact D60=0? If yes, D61=HW2 is
   real. This is the highest-leverage move; macbook can't accelerate
   it directly, but should NOT spend more 1B walks on the same
   greedy-flip operator while yale develops it.

2. **Cross-cand survey at HW8 base** — extend the 3-cand sweep
   (idx=0, idx=3, idx=8) to all 18 yale-tested cands at 1B trials each.
   ~1.5 hours wall on M5. Tests whether ANY cand has a lower floor than
   HW4 under the same operator.

3. **Different perturbation operators** — pair-bit flips that preserve
   carry-mask invariants, byte-rotation moves, tangent-kernel-aligned
   moves from yale's rank-31 kernel decomposition. Implementation
   requires modifying yale's tool.

4. **Wider radius / longer passes** — try max_flips=64, max_passes=200
   on the HW4 trap. Tests whether HW3 is just a longer-tail event.
   Cheap (~30 min for 4 cands × 1B), useful negative-result.

5. **Tail<59** — separate from D61 descent, the tail HW59 frontier may
   admit further descent. Yale found it via pooled frontier walk;
   could try different policies.

## Recommendation

Pause raw 1B greedy-flip campaign on the same starting bases.
Either (a) sweep cands 4-17 at HW8 base × 1B trials each (~1.5h M5,
non-committed unless cross-cand floor moves), or (b) wait for yale's
carry-aware repair work and provide M5 brute-force support for
specific carry-preserving proposals when they're ready.

## Run inventory (campaign so far)

| run | command | result | committed? |
|---|---|---|---|
| 7 | idx=8 HW7 base | **HW5 / HW68** | cddef23 |
| 8 | idx=8 HW5 base | tail HW67 | ffc01c3 |
| 9 | idx=8 HW67 tail | **tail HW60** | c28c1bb |
| 10 | idx=8 HW60 tail | null | no |
| 11 | yale cap-4 terrace | null | no |
| 12 | idx=3 HW8 base | HW6 / HW67 | rolled into b69d5c4 |
| 13 | idx=0 HW8 base | HW5 / HW64 | rolled into b69d5c4 |
| 14 | idx=0 HW5 base | **HW4 / HW70** | 37b721a |
| 15 | idx=0 HW4 base | null (HW4 trap) | no |
| 16 | yale's HW59 tail base | **idx=8 HW4 reproduces** | c14c587 |
| 17 | idx=8 HW4 base | null (HW4 trap) | this memo |

11 walks, ~11B trials, ~2.6h wall. 6 commits (5 frontier + 1 summary).

Status: HW4 looks like the structural greedy-flip floor. Next move
is operator change or cross-cand survey, not more of the same.
