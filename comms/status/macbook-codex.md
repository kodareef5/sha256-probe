---
date: 2026-04-30
machine: macbook-codex
status: active
---

# macbook-codex status

Started from `.codex_session/brief_2026-04-30.md`, then read `CLAUDE.md`,
`CLAIMS.md`, `headline_hunt/TARGETS.md`, registry state, and current inbox
context. Registry validates clean at session start.

Rules of engagement acknowledged:

- Commit as configured `kodareef5`; push is authorized.
- No force-push to master without explicit approval.
- Every solver run must be CNF-audited first and logged through
  `headline_hunt/infra/append_run.py`.
- Claim long-running bet work in `headline_hunt/registry/mechanisms.yaml`
  before launching it.
- Do not reopen closed bets unless reopen criteria are met.
- Do not touch `/tmp/F350` or `/tmp/deep_dig`.
- Do not reimplement `lib/` primitives.
- F-numbered memos for substantive findings, with explicit evidence level.

Ordering decision:

1. Cleanup first: low-risk coordination hygiene before the fleet pulls.
2. Path C next: bounded, no solver, highest EV/CPU-hour among immediately
   executable interventions, and aligned with `block2_wang` priority.
3. Path A after Path C: directly targets the bit2 outlier and F397 priority
   mechanism, but has longer C++/runtime risk and needs registry claiming.
4. Path B last: the F381-F395 chain already mined the learned-clause lead and
   falsified ladder pre-injection as a speedup; remaining value is secondary.

Capacity: using this local Codex session on the Mac workspace. `getconf`
reports 10 online processors; I will keep initial work bounded and avoid
unclaimed long solver jobs.

## 2026-04-30 ~21:10 EDT

Cleanup commit pushed as `b728caf`.

Path C in progress/completed first pass:

- Added annealing/restarts/tabu/candidate controls to `block2_bridge_beam.py`.
- Ran 4-cand annealing sweep, 458s wall, no solver search.
- New residual records: bit3 HW=51, bit2 HW=51, bit24 HW=49, bit28 HW=45.
- Built audited cert-pin CNFs for all 4; audit verdicts `CONFIRMED`.
- Logged 8 cert-pin solver runs; kissat + cadical both UNSAT for all 4.

Next: commit F408 memo/artifacts, then reassess whether to continue Path C
around bit28 or switch to the bit2-specific Path A follow-up left by F407.

## 2026-05-01 ~08:30 EDT

Pulled origin first; origin/master was already at `695b283`.

Read Yale F416-F419 in full before Path B. Decision: old Path B aimed at
F343/dW-row learned clauses is superseded by Yale's zero-touch F417/F418 result,
but Path B itself is still useful if retargeted to F419's fresh learned
neighborhood. Proceeded with F420: cross-candidate F419 replication over
bit2/bit24/bit28 using actual `a/e` registers rounds 57-63 plus
`aux_modular_diff` watches.

F420 result:

- `dW57`/`dW58` remains the wrong surface.
- Actual-register learned neighborhood generalizes: 74-78% of exported learned
  clauses touch watched actual/modular vars across all three candidates.
- `actual_p1_a_57` dominates, but hot bits are candidate-specific.
- F343 decision deltas are not explained by raw learned-touch volume.

Next recommendation from F420: revised Path A, not old Path B. Test priority or
activity pressure on candidate-specific `actual_p1_a_57` hotspot bits.

## 2026-05-01 ~08:45 EDT

Executed revised Path A as F421.

- Extended `cascade_propagator.cc` with `--seed=N`.
- Extended `run_decision_priority_matrix.py` with `--hotspot-matrix`.
- Ran 3 candidates × 3 seeds × 3 arms at 50k conflicts:
  baseline, F343, hotspot-priority max132.
- All 27 final runs audited `CONFIRMED` before solve and logged.

Verdict: actual `a_57` hotspot priority does not dominate F343. It is a
candidate-specific lead: strong for bit24 (-23.16% mean decisions), harmful for
bit2 (+14.79%) and bit28 (+12.69%). F343 remains the better panel-wide nudge.

Next if continuing this branch: bit24-only decomposition of hotspot bits
14/16 vs 21-25 and smaller caps. Stop hotspot-priority for bit2/bit28.

## 2026-05-17 ~09:45 EDT

Re-entered as mac-codex for free-word shaping / MITM task design and a first
prototype pass.

Added task-design packet under `headline_hunt/reports/task_design/`, then built
`headline_hunt/bets/mitm_residue/prototypes/free_word_mitm_reducedn.c`.

First reduced-N result:

- N=8 exact: D60=0 matches 65,954 vs 65,536 random expectation, no tail collisions.
- N=10 exact: D60=0 matches 1,045,126 vs 1,048,576 random expectation, no tail collisions, best tail HW7.
- N=12 sampled: D60=0 matches 65,266 vs 65,536 expectation, no tail collisions in the sample.

Conclusion: W60-defect matching is the right interface to instrument, but D60
alone is not the construction key. Next useful key is D60 + r61 residual bucket
+ tail carry chamber signature.

## 2026-05-17 ~10:35 EDT

Extended the free-word MITM prototype with enhanced key profiling:

- `(g60,h60)` bucket profile,
- exact r61 active-mask buckets,
- tail carry-signature buckets,
- coarse `gh60+r61_hw` buckets.

Ran N=8 exact, N=10 exact, N=11 exact, and N=12 samples. Result: `gh60`
compresses strongly, but exact r61 masks are nearly injective and tail carry
signatures are fully injective. Coarse `gh60+r61_hw` keeps multiplicity but
its fattest buckets are mediocre. The next useful direction is supervised
coarse-key design: selected late-register bits or learned tail-score features,
not occupancy-max buckets.

Added one-bit r61 supervised feature stats. Result is negative: active/inactive
mean-tail shifts are only hundredths of a bit at N=10/N=12. Single r61 bits are
too weak. Next should be pair/triple projected features or a streaming top-k
bucket miner keyed by `gh60 + feature projection`.

Added late-register pair-state stats over r61 regs 6/7. Also weak: pair states
move the mean slightly more than single bits, but still do not rank the global
low-tail witnesses. Simple manual feature selectors are now poor candidates;
next best implementation is direct top-k bucket mining by low-tail rate.

## 2026-05-17 ~11:20 EDT

Built the streaming top-k projected-bucket miner into
`headline_hunt/bets/mitm_residue/prototypes/free_word_mitm_reducedn.c`.

Runs covered N=8 exact, N=10 exact, and an N=12 262,144-prefix sample. The
miner can recover buckets containing the best reduced-N tail witnesses, but the
low-tail event is usually isolated inside a bucket rather than enriched across
the bucket. This demotes plain bucket selection as a construction rule.

Next useful build: persist best witnesses from top best-tail buckets and launch
a second-stage local refinement around those witnesses. Treat projected buckets
as an address system for neighborhoods, not as a closing constraint by
themselves.

## 2026-05-17 ~12:35 EDT

Built second-stage local refinement into the free-word MITM prototype. The scan
retains top `D60=0` witnesses, then the refinement stage tests one-bit and
two-bit neighborhoods plus an annealed D60-HW walk through nearby nonzero-D60
states.

Controls:

- N=8 exact, 100k refinement tests: best tail stayed HW9.
- N=10 exact, 1M refinement tests: best tail stayed HW7.
- N=12 262,144-prefix sample, 50M refinement tests: 18,768 local `D60=0`
  returns and 24 new retained seeds, but best tail stayed HW15.

Conclusion: raw local mutation around best bucket witnesses is cheap and valid,
but not a closing mechanism. Next refinement should preserve or directly solve
the `D60=0` interface, e.g. mutate a `(W57,W58)` neighborhood and enumerate or
solve `W59` values that land on `D60=0`, then score tail.

## 2026-05-17 ~14:05 EDT

Implemented the `D60=0`-surface version of refinement: retained low-tail seeds
now drive full `W59` fiber enumeration over neighboring `(W57,W58)` prefixes.
Also added `sample_start` so disjoint N=12 prefix samples can run in parallel.

Controls stayed clean:

- N=8 exact: 389 prefix fibers, best stayed HW9.
- N=10 exact: 975 prefix fibers, best stayed HW7.

Ran nine N=12 262,144-prefix windows total. Best reduced-N lead is now
sample_start `524288` with tail HW11:

```text
W1[57..59] = e43,203,594
W2[57..59] = 878,faf,d04
r61 HW     = 14
```

Focused 500M-test prefix refinement on that HW11 window enumerated 122,005 full
prefix fibers and found 126,199 `D60=0` returns, but did not improve below HW11.

Conclusion: broad disjoint prefix sampling is currently higher EV than local
refinement. Next build should be a lean scan-only/witness-registry mode for
parallel N=12/N=13 sample sweeps, retaining compact low-tail witnesses without
the full profiling tables.

## 2026-05-17 ~15:20 EDT

Implemented scan-only witness-registry mode in
`headline_hunt/bets/mitm_residue/prototypes/free_word_mitm_reducedn.c`.

Changes:

- `mode=scan` disables the heavy profiling tables and keeps compact low-tail
  witnesses.
- N=13 is now unlocked by a deterministic random-fallback `da56=0` seed:
  `M0=0x974`, `kernel=dM0=dM9=0x1000`.
- Scan mode can be used with refinement, so retained witnesses feed the same
  prefix-fiber second stage.

Ran 20 disjoint N=13 windows of 65,536 prefixes each, covering 1,310,720 of
67,108,864 N=13 prefixes. Best N=13 tail lead improved to HW12:

```text
sample_start = 1048576
W1[57..59]   = 0092,0dbf,0ae1
W2[57..59]   = 1a0e,05d3,1eb2
r61 HW       = 22
```

Best r61 lead in the N=13 sweep is HW9, seen in multiple windows.

Focused 500M-test prefix-surface refinement on the HW12 window found 63,497
`D60=0` returns and no improvement below HW12. This reinforces the current
working rule: broad disjoint scan is the main engine; local prefix-fiber
refinement is validation, not a basin descent.

## 2026-05-17 ~16:20 EDT

Continued the N=13 scan sweep through 59 unique windows, covering 3,866,624 of
67,108,864 prefixes, plus one targeted duplicate rerun of the best r61 window.

Tail frontier is unchanged:

```text
N=13 best tail HW = 12
sample_start      = 1048576
W1[57..59]        = 0092,0dbf,0ae1
W2[57..59]        = 1a0e,05d3,1eb2
```

r61 frontier improved:

```text
N=13 best r61 HW = 8
sample_start     = 2031616
tail HW          = 28
W1[57..59]       = 0486,020a,1fcf
W2[57..59]       = 1e02,169e,0967
```

Added a separate r61-first scan registry. The targeted rerun showed the r61-HW8
witness would be dropped by the tail-first registry, so future scan output now
retains both tail frontier candidates and low-r61 candidates.

## 2026-05-17 ~16:50 EDT

Ran a mixed batch after the r61-registry commit:

- four more N=13 windows, no improvement beyond tail HW12 or r61 HW8,
- four N=14 pilot windows, same 536,870,912 triples per worker.

This brings N=13 coverage to 63 unique windows, or 4,128,768 of 67,108,864
prefixes.

N=14 is operational with the same random-fallback seed path:

```text
M0            = 0x3d36
kernel        = dM0=dM9=0x2000
scan rate     = about 23M triples/sec/worker
best tail HW  = 20 at sample_start 32768
best r61 HW   = 13 at sample_start 98304
```

Current interpretation: keep N=13 broad scan as the best near-term tail hunt,
but N=14 is now cheap enough for staged pilots and scaling checks.

## 2026-05-17 ~17:45 EDT

Continued N=13 broad scan and added a grep-friendly `SUMMARY` line to
`free_word_mitm_reducedn.c`.

Coverage is now 94 unique N=13 windows:

```text
prefixes covered = 6,160,384 / 67,108,864 = 9.18%
triples covered  = 50,465,865,728
```

New N=13 tail frontier:

```text
tail HW      = 9
sample_start = 5570560
r61 HW       = 17
W1[57..59]   = 04cb,0eaa,196e
W2[57..59]   = 1e47,13bf,029e
```

Focused 500M-test prefix-surface refinement on the HW9 window validated the
witness and found 64,120 `D60=0` returns, but did not improve below HW9.

The r61 frontier remains HW8 at `sample_start=2031616`; a later HW8 r61 match
also appeared at `sample_start=5177344`, but with tail HW21. Current working
rule is unchanged: broad disjoint scan is the productive engine, local
prefix-fiber refinement is a validator, and the next research value is in
nonlocal recombination over retained witnesses.

## 2026-05-17 ~19:00 EDT

Built logged batch tooling for the all-day N=13 sweep:

- `run_scan_batch.py` launches parallel scan windows and writes per-window logs.
- `summarize_scan_batch.py` reports JSONL coverage/frontiers.
- Batch summaries are in
  `headline_hunt/bets/mitm_residue/results/runs/20260517_n13_scan_batch/summaries.jsonl`.

Checkpoint through window 949:

```text
unique N=13 windows = 950
prefixes covered    = 62,259,200 / 67,108,864 = 92.77%
triples covered     = 510,027,366,400
tail frontier       = HW7 at sample_start 24641536
r61 frontier        = HW7 in seven logged windows
```

The tail frontier moved from HW9 to HW7:

```text
W1[57..59] = 0f36,07db,082b
W2[57..59] = 08b2,1b15,1ef6
r61 HW     = 9
```

Focused 500M-test prefix-surface refinement validated the HW7 witness and
found 64,306 `D60=0` returns, but did not improve below HW7. The separate r61
frontier also improved from HW8 to HW7 and repeated in seven logged windows;
those r61-only witnesses still have mediocre tails, so the split-registry
model remains right. No tail improvement appeared after crossing 61% of the
N=13 prefix surface. The added `630..949` windows only reached HW12, at
`sample_start=53477376` and `sample_start=55377920`. The latest r61-HW7 repeat
is `sample_start=54853632`, with tail HW16.
