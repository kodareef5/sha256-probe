---
F-number: F835
date: 2026-05-04
author: macbook-claude
type: meta / literature scan
evidence_level: SURVEY (external sources only — no claims about our results)
---

# F835 — External research inspiration scan (May 2026)

User asked to "pull up, way up — find a new angle to attack from" while Yale
keeps running the block-2 absorber pair-beam pipeline (currently plateaued
at HW=82 absorber floor across a 13-cand portfolio).

This memo summarises a casual web scan of recent (2024–2026) SHA-256 and
adjacent-hash cryptanalysis literature, then proposes three candidate angles
that are *orthogonal* to the current pair-beam loop and not obviously
duplicating Yale's path.

## What's new in the literature (2024–2026)

| Reference | Venue / year | Why it matters |
|---|---|---|
| Eurocrypt 2026, eprint 2026/232 — "Collision Attacks on SHA-256 up to 37 Steps with Improved Trail Search" | Eurocrypt 2026 | First push past the decade-long 31-step record. Key novelty: an *automated tool to identify high-quality local collisions in the message expansion*. Replaces the bespoke Mendel-style hand-curated kbits. |
| Bright et al., arXiv 2406.20072 — "SHA-256 Collision Attack with Programmatic SAT" | 2024 | Introduces IPASIR-UP-based callback propagators for SHA-2 trail search: bitsliced + wordwise propagation, two-bit-condition contradiction detection, blocking clauses on inconsistencies, CAS+SAT integration. They explicitly note their SAT+CAS techniques may generalise to alternate encodings (Li et al.'s 39-step SFS). |
| Li et al., Eurocrypt 2024 | 2024 | 39-step semi-free-start SFS collision via SAT/SMT-driven *sparsity-controlled* characteristic search. |
| Zhou et al., Quantum Information Processing 2026 | 2026 | Quantum collision attacks on reduced SHA-256 (Grover variant). Not actionable on classical HW but useful to track. |
| eprint 2026/775 — "Differential and Linear Cryptanalysis of Modular Addition" | 2026 | New DDT/LAT machinery for ARX. Carry-bit probability → 1/2 with position. Directly relevant to anything `bridge_score`-shaped. |
| Survey: 6 Years of Neural Differential Cryptanalysis (eprint 2024/1300) | 2024 | 66-paper taxonomy. Almost no application to SHA-256 (mostly SPECK / SHA-3 / lightweight). Open lane. |
| Viragh's own admission ("We broke 92% of SHA-256", 2026-03-27) | self-flagged | "Wang-style message modifications were not utilized. Statistical properties for search-space pruning remain largely unexplored." Their own gap list. They also report 64% solve on the *full* SR=64 with kissat. |
| OffSeq "first verified second-preimage W-schedule" (Dec 2025) | — | Marketing/red-flagged. No mathematical content. Skip. |

## Three candidate angles to pull up to

### Angle A — Programmatic-SAT (IPASIR-UP) for absorber search
**The idea.** Stop driving the M2-pair search from a Python beam loop with stock
solvers as black-box cert-pin verifiers. Instead, embed the bridge_score-cube
predicate and the M2-mask combinatorial structure directly as **callback
propagators** inside kissat (or cadical) using IPASIR-UP, the way Bright et
al. 2024 did for their 31-step record.

**Why this is "pulling up".** It is a *paradigm change in the search engine*,
not another point in our current parameter-space sweep. The paper is the
operationalised version of the same loop we hand-rolled this week. Concretely:
- Two-bit conditions over `(M1[i], M2[i], M2_pair[i])` — extract on the fly,
  detect contradictions, inject blocking clauses.
- Wordwise propagation across W-schedule rounds 16–63 — exploit the carry
  cascade structure we already understand from the bit-serial DP work
  (project memory: carry-DP plateau).
- Use the CAS+SAT integration to detect unsat'd cubes early.

**Cost.** Real but bounded. kissat 4.0.4 ships with IPASIR-UP. We have to
write the propagator (C, ~500 lines), wire it to a small Python orchestrator,
and benchmark. If the Bright et al. propagator is open-source, scope drops
to porting. **Estimate: 1–2 days to a working prototype.**

**Why now.** Our current pair-beam plateau is consistent with running out of
locally-fruitful M2-mask space at fixed search depth. A solver with
contradiction-blocking propagators reaches deeper for the same wallclock.

### Angle B — Automated local-collision discovery in W-schedule
**The idea.** Eurocrypt 2026 shows the 31→37 jump came from *finding new
local collisions in message expansion*, automated. Today our `CANDS` list in
`block2_bridge_beam.py` is hand-curated: bit2_ma896ee41, bit24_m9908b6a8,
etc. — these were chosen based on cascade-1 diagnostics, not by a search
that scores a candidate's *future* extendability.

**Concretely.** Build a small enumerator that, given a W-cube basis (W57–W60
right now), scores each (M1 kbit, M2 mask) tuple by:
1. Hamming-ball reachability in the W-schedule under a depth-3 expansion;
2. cascade-1 invariant {a,b,c,e,f,g} purity at the IV2 boundary;
3. Empirical absorber-floor predictor trained on our F520–F834 jsonl
   telemetry.

This automates what we've been doing by hand and surfaces kbits we wouldn't
have picked.

**Cost.** Smaller than (A). ~1 day. Composes with (A) — a better seed list
plus a smarter solver.

### Angle C — Neural seed-scoring on accumulated jsonl telemetry
**The idea.** We have a *huge* corpus of seed/result jsonl files under
`headline_hunt/bets/block2_wang/results/search_artifacts/` from F428 through
F834 — every M2-pair-beam run, every absorber outcome, every cert-pin
verdict. Each line is a labelled training example: `(features, final_HW)`.

Train a small classifier (MLP or gradient-boosted trees, no fancy
transformer needed) to predict "will this (M1, M2) seed reach HW≤85 within
N iterations". Use it as a **prefilter** before cert-pin verification —
which is currently the bottleneck.

Even a 5–10× reduction in the candidate set fed to cert-pin would compound
across the whole portfolio scan.

**Why this is novel here.** The neural-distinguisher literature (post-Gohr)
has barely touched SHA-256 — the survey of 66 papers found mostly SPECK,
PRESENT, SHA3. Lane is open. We have data nobody else has (~weeks of run
telemetry on one specific kernel family). That asymmetry is rare.

**Cost.** Smallest of the three. ~half a day to build the dataset + train
a baseline. Genuinely "casual research" priced.

## What I'd do tomorrow if you said "pick one"

**(C) first**, because:
- Cheapest cost, fastest signal — if the classifier doesn't beat random
  baseline at filtering, we learn that quickly and move on.
- Doesn't conflict with Yale's current path; Yale keeps shipping HW results,
  we mine them.
- Compounds with (A) and (B) later — a learned scorer plugs into either as
  a heuristic.

**(A) is the bigger swing.** If we want a real pull-up that takes the next
record (block-2 absorber HW<82 *with cert-pin*) it's the engine swap, not
another beam-search variant. But it's a 2-day commitment and it overlaps
some with what Yale's pair-beam tooling already does in Python. Worth
discussing before starting.

**(B) is the right complement to (A) if we go that route**, but it's not
worth doing alone — without a stronger search engine downstream, a better
seed list just changes the same plateau's location.

## Out-of-scope (logged for later, not pursued)

- **Quantum collision attacks** (Zhou et al. 2026): no fault-tolerant qubits.
- **Higher-order / 2nd-order differentials** (Mendel ASIACRYPT 2011 lineage):
  potentially interesting on its own but a from-scratch encoding effort.
  Defer until after (A) shows whether engine upgrades alone close the gap.
- **Wang-style multi-block message modification** (Viragh's #1 self-flagged
  gap): conceptually purest "new angle", but the least operationalised in
  open literature. Park as a research thread, not a code thread.
- **"OffSeq W-schedule second-preimage"**: marketing, no math, ignore.

## References (URLs)

- eprint 2026/232 — Collision Attacks on SHA-256 up to 37 Steps with Improved Trail Search
- arXiv 2406.20072 — SHA-256 Collision Attack with Programmatic SAT (Bright et al.)
- eprint 2026/775 — Differential and Linear Cryptanalysis of Modular Addition
- Springer s11128-025-05024-w — Quantum collision attacks on reduced SHA-256 (Zhou et al.)
- eprint 2024/1300 — Survey: 6 Years of Neural Differential Cryptanalysis
- stateofutopia.com/papers/2/we-broke-92-percent-of-sha-256.html — Viragh 2026
