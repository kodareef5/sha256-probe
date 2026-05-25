# 2026-05-25: Schedule-Realizable Repair — the a-zeroing cascade is tail-suboptimal

Runner: macbook (kodareef5)
Tool: `prototypes/sched_repair_probe.c` (new), reuses the `free_word_mitm_reducedn.c` reduced-N model verbatim.
Evidence level: **EVIDENCE** (reduced-N, sampled at N>=10; effect consistent N=8..14; see caveats).
Lead status: **RESOLVED** — repair is realizable at the round-57..60 interface
(prefix word `Wpre2[44]`); the sole obstacle is the upstream `W44<->init2`
coupling = `block2_wang`'s dense schedule inverse. No new tractable path; the two
leads share one bottleneck. gh60-structure + neutral-set follow-ups noted below.

## Question

The free-word route had a standing gap: the **oracle** repair (overwrite
`W60_2 := req_w2_60`, not schedule-realizable) reached tail **HW8**, while
**schedule-realizable low-HW `D60` repairs plateaued at HW10/HW9**
(`20260517_next_fronts_after_n13.md`, Front 5). The flagged next step was to find
a *schedule-realizable repair variable* targeting the good (high-HW) oracle patches.

## Key realization

In the model, message-2's words `w2_57, w2_58, w2_59` are **not free** — the
cascade pins each to `w2_for_zero_a(round, ...)` so the a-register difference is
zeroed every round. `W60_2 = s1(w2_58) + Wpre2[53] + s0(Wpre2[45]) + Wpre2[44]`
is the only tail word fed by a (cascade-pinned) free word, `w2_58`.

The oracle's un-realizable patch is therefore equivalent to a question the search
never asked: **what if message-2's word is chosen to minimize the tail instead of
to zero the a-register?** That alternative is fully schedule-consistent (W60..W63
still follow the real recurrence).

## Method

`sched_repair_probe.c` releases one cascade-pinned word: `w2_KNOB = base + delta`,
then runs rounds honestly (no oracle overwrite) and scores the round-63 tail HW.
Four frontiers per window, all over the **same** sampled prefixes:

- `honest_d0`   — best tail at `delta=0`, `D60=0` (reproduces the existing exact scan)
- `honest_any`  — best tail at `delta=0`, any `D60`
- `oracle`      — best tail with `W60_2 := req` (the un-realizable bound)
- `sched_repair`— best HONEST tail over `delta != 0` (the new schedule-realizable result)

**Validation:** `honest_d0 = HW9` at N=8 reproduces the documented exact-scan
control exactly, so `eval_probe` matches the reference model. `sched_repair`
runs the identical evaluator over additional `w2_KNOB` values.

## Results

Tail HW (lower = closer to collision). `cascade` = `honest_d0`.

| N  | cascade | oracle | sched_repair (knob=W2_58) | coverage |
|---:|--------:|-------:|--------------------------:|----------|
| 8  | 9       | 2      | 6                         | exhaustive (2^16 prefixes, full δ) |
| 10 | 14      | 5      | 8                         | 4096 prefixes, full δ |
| 12 | 24      | 9      | 15                        | 256 prefixes, full δ |
| 14 | 28      | 18     | 20                        | 64 prefixes, δ-ball r=6 |

The schedule-realizable repair beats the cascade plateau by **3–9 bits** and
sits strictly between cascade and oracle at every width, closing **~43–80%** of
the cascade→oracle gap with a single freed word. Absolute values at N>=12 are
coverage-limited (thin prefix sample); the robust quantity is the same-prefix gap.

### Control: which word to free (N=8 exhaustive)

| knob freed | sched_repair tail |
|------------|------------------:|
| W2_57 (earliest) | 3 |
| W2_58 (W60 knob) | 6 |
| W2_59 (latest)   | 5 |
| (cascade, none)  | 9 |
| (oracle bound)   | 2 |

**The control corrected the hypothesis.** It is *not* specifically the W60
interface: freeing *any one* of message-2's words beats the cascade. At N=8 the
earliest word (`w2_57`) helped most, but this ordering does **not** replicate —
at N=10 and N=12 the W60 word `w2_58` wins. So the stable claim is the existence
of the gain, not which word is best:

> The a-register-zeroing cascade is a suboptimal way to spend message-2's word
> freedom. Choosing those words to minimize the final tail (instead of zeroing
> the a-register) is schedule-consistent and recovers a large fraction of the
> oracle gap. Which word is most productive varies with N / sampling.

knob=57 vs knob=58 (same prefixes):

| N  | cascade | knob=W2_57 | knob=W2_58 | oracle |
|---:|--------:|-----------:|-----------:|-------:|
| 8  | 9       | **3**      | 6          | 2      |
| 10 | 14      | 11         | **8**      | 5      |
| 12 | 24      | 17         | **15**     | 9      |

(bold = best knob at that width)

## Caveats (do not over-read)

1. **Relaxation, not full SHA.** This is the same free-word relaxation as the
   existing tool: `W57..W59` are treated as free, not enforced schedule-consistent
   with `W0..W15`. "Schedule-realizable" here means W60..W63 follow the recurrence
   from the (free) words — it does not re-derive the prefix.
2. **Structure vs tail.** The a-zeroing cascade is what concentrates the hardness
   into the ~24-bit MITM residue. Breaking it for a lower tail may trade that
   exploitable structure for a generic near-collision. Lower tail HW here is
   **not yet** demonstrated attack progress — it quantifies that the cascade
   leaves a real, schedule-consistent degree of freedom unused.
3. **Sampled coverage** at N>=10: frontier values are upper bounds; the robust
   claim is the *gap* (sched_repair < cascade on identical prefixes).

## Update (same day): freeing all three message-2 words does NOT help — gain saturates at one word

Tested lead (1) directly with two extra search modes in the same probe:
- `delta_mode=3` — random joint `(d57,d58,d59)` draws (8192/triple).
- `delta_mode=4` — coordinate descent: exhaustively optimize one word, fix, repeat.

On an identical N=8 4096-prefix sample (`honest_d0=9`, oracle `=3`):

| method | sched_repair tail |
|--------|------------------:|
| single word d58 (mode 1) | 8 |
| single word d57 (mode 1) | 8 |
| coordinate descent, 3 sweeps (mode 4) | 8 (identical witness to d58) |
| random joint, 8192 draws (mode 3) | 7–8 (sparser, never beats single word) |

**Coordinate descent returns the exact same HW8 witness as single-word d58** —
optimizing `d59`/`d57` after `d58` yields no further drop. So the gain **saturates
with one freed word**; the remaining cascade→oracle gap (HW8→3 here, HW6→2 on the
full N=8 space) is *not* a message-2 word-freedom deficit.

**Reframing of the gap.** All three words drive the round-60 interface through the
same bottleneck `W60_2 = s1(w2_58) + const`. The oracle wins only because it sets
`W60_2` to a value that need not lie in the schedule-reachable set
`{ s1(x) + const }`. So the residual gap is the **non-surjectivity / reachability
of `W60_2` under the schedule recurrence**, not a lack of free words.

EVIDENCE level: the saturation result is a clean same-sample comparison (N=8);
worth confirming at N=10/12 and characterizing the `W60_2` reachable set vs the
`req` the e-wave demands.

## Update 2: reachability split (mode 5) — the gap lives on un-satisfiable interfaces

`delta_mode=5` classifies each free triple as **D60=0 reachable** iff some `w2_58`
(full δ sweep) zeroes `d60`, then splits the oracle frontier by reachability.

N=8, 2048-prefix sample (524288 triples):

```
D60=0 reachable          = 63.4% of triples
min oracle tail | reachable   = 6   unreachable = 3
min honest(D60=0) | reachable = 9
```

Two findings, both **opposite** to the naive guess:

1. **The oracle's deepest wins are on UNREACHABLE triples** (HW3 there vs HW6 on
   reachable). The oracle's real power is fixing the round-60 e-interface for free
   exactly where the schedule *cannot* satisfy it (`d60` can't be zeroed by any
   `w2_58`). So the residual cascade→oracle gap is concentrated on
   schedule-unsatisfiable interfaces — not something a schedule DOF can reach.
2. **Even on reachable triples, oracle (6) beats honest-D60=0 (9).** Achieving
   `d60=0` honestly requires `w2_58 = base+δ`, which perturbs the round-58 state;
   the oracle keeps the clean a-zeroed round-58 state *and* fixes `W60_2`. The
   oracle decouples (round-58 shaping) from (W60_2); the schedule couples them
   through the single word `w2_58`. That coupling is the cost.

(Note: best honest tail over *all* δ — not just `d60=0` — does reach ~HW6 at N=8,
via `d60!=0` paths; it's the `d60=0`-constrained honest that plateaus at 9.)

## Net read

Freeing message-2 words is a real but **bounded** lever: one word recovers a large
slice of the gap (HW9→6 at N=8); more words add nothing; the rest of the gap is
structural — the oracle wins by (a) satisfying un-satisfiable interfaces and
(b) decoupling round-58 shaping from W60_2. Closing it would need a genuinely new
DOF (e.g. perturbing the *prefix* words W44/W45/W53 that feed W60 without touching
round-58), whose schedule-realizability is the open question.

## Update 3 (DECISIVE): the prefix-word Wpre2[44] lever reproduces the oracle exactly

`delta_mode=6` sweeps a perturbation of `Wpre2[44]` — the one prefix word that
feeds **only** `W60_2` (linearly) and **not** rounds 57..59. N=8, 4096 prefixes:

```
honest_d0    tail 9
oracle       tail 3  (d60_hw=5)  W1=0x30,0x73,0x82
sched_repair tail 3  (d60_hw=0)  W1=0x30,0x73,0x82   <- mode 6, SAME witness
```

**Mode 6 reproduces the oracle tail (HW3) exactly — but honestly, with d60=0.**
Perturbing `Wpre2[44]` shifts `W60_2` to `req` with a single modular add and zero
round-58 cost, so it realizes the oracle within the schedule recurrence.

### What this resolves

The "schedule-realizable repair" gap is **not** in the round 57..60 free-word
interface at all — that interface fully admits the oracle, via `Wpre2[44]`. The
entire remaining obstacle is **upstream**: in full SHA-256, `Wpre2[44]` and
`init2` (the round-57 state) are both functions of message-2's `W0..W15`, so you
cannot move `W44` by the needed δ without moving `init2` and breaking the cascade.

That is exactly a **constrained message-modification problem** — i.e. the
`block2_wang` Wang-style problem. So this lead converges with `block2_wang`: the
mitm_residue tail-repair reduces to "perturb message-2's schedule to shift `W44`
by a target δ while holding the round-57 state fixed."

EVIDENCE level: decisive within the reduced-N relaxation (N=8 exact; confirm at
N=10/12/14). The relaxation->full-SHA gap (the `W44 <-> init2` coupling) is the
real open problem and is now cleanly isolated.

## Where this leaves the bet

1. Cascade a-zeroing is tail-suboptimal; one freed interface word recovers a big
   slice (HW9->6), but the gain saturates (joint/coord-descent add nothing).
2. The *full* oracle gap is realizable in the relaxation by one prefix word
   (`Wpre2[44]`), so the round-57..60 interface is not the bottleneck.
3. The real bottleneck is the upstream `W44 <-> init2` schedule coupling — a
   constrained message-modification problem shared with `block2_wang`.

## Update 4: the W44<->init2 coupling is tight (mode 7) + mode-6==oracle confirmed N=10/12

**Mode-6 >= oracle across widths** (prefix-44 lever reaches the oracle tail
honestly): N=8 HW3=oracle, N=10 HW5=oracle, N=12 HW9=oracle, N=14 **HW16 < oracle
HW18**. At N=14 the lever *beats* the oracle: sweeping `Wpre2[44]` explores ALL
`W60_2` values, while the "oracle" only tried `req` (the round-60 e-zeroing
value). So the prefix-44 lever is the true interface bound and the naive oracle
was a lower bound on it — the round-57..60 interface admits optimal `W60_2`
selection schedule-consistently.

**Coupling (mode 7)**, N=12, state = 96 bits, 16.7M random message perturbations
(<=6 bit flips of W0..W15):

```
min round-57 state move with ANY W44 change = 23 / 96 bits (~24%)
Pareto (dW44_hw : min d-state_hw):  1:29  2:27  3:25  4:25  5:23  6:24 ...
```

The cheapest way to move `W44` (via the message) still disturbs ~a quarter of the
round-57 state. So `W44` is **tightly coupled** to `init2`: there is no cheap lever
to shift `W44` while holding the round-57 state, under naive small perturbations.
(It is below full avalanche ~50%, hinting at *some* structure, but far above the
~0 disturbance the cascade needs.) This quantifies the upstream obstacle as
genuinely hard — i.e. the Wang-style neutral-set / message-modification problem.

Caveat: this is naive <=6-bit random search (a difficulty *lower bound* on cheap
levers). Structured neutral sets are exactly what `block2_wang` tools
(`m2_delta_neutral_combo.py`, `search_schedule_space.py`, `preimage_lift.py`)
search for — the proper next attack lives there. (Minor: mode-7 `samples` is
clamped to `prefix_space`; fine at the counts used.)

**Scaling — the coupling is width-stable.** Same metric at larger widths:

| N  | state bits | min state move for any W44 change | ratio |
|---:|-----------:|----------------------------------:|------:|
| 12 | 96         | 23                                | 24%   |
| 16 | 128        | 33                                | 26%   |
| 20 | 160        | 44                                | 27.5% |
| 24 | 192        | 57                                | 30%   |

The cost to move `W44` holds at ~a quarter-to-third of the round-57 state across
all tested widths (300M samples, <=8-bit perturbations). The slight upward drift
is partly a sampling artifact (fixed sample count covers less of the perturbation
space at larger N). Robust conclusion: the upstream obstacle does **not** weaken
with scale — no cheap W44 lever exists at any width.

## Net read (final for this session's probe)

The "schedule-realizable repair" question is answered: the repair IS realizable —
the round-57..60 free-word interface fully admits the oracle via the single prefix
word `Wpre2[44]` (confirmed N=8/10/12). The only obstacle is the upstream
`W44 <-> init2` coupling, now measured to be tight (>=23/96 state bits to move W44
at N=12). That obstacle is the `block2_wang` constrained-message problem, so the
two leads converge: **progress on mitm_residue tail-repair now routes through
block2_wang's neutral-set machinery.**

## Update 5 (synthesis): the coupling IS block2_wang's "dense schedule inverse"

Reading `block2_wang/encoders/preimage_lift.py`: it already found that lifting a
low-HW `dW` target back to `dM` via the schedule recurrence gives **high-HW dM
(~113 bits mean)** because "the schedule recurrence's GF(2) inverse is dense."
`search_schedule_space.py` then *abandoned* the linear lift for an atlas-loss
mutation search precisely for this reason.

That is the **same structural fact** as the `W44 <-> init2` coupling measured
here (mode 7) from the other direction: you cannot cheaply move a late schedule
word (W44) via the message because the inverse map is dense. Two independent
leads, one obstacle.

**Honest conclusion for the bet:** the mitm_residue tail-repair does NOT open a
new tractable path. It is *realizable* at the round-57..60 interface (via
`Wpre2[44]`), but realizing it in full SHA reduces exactly to the dense
schedule-inverse / neutral-set problem that `block2_wang` is already grinding on
(and which it has shown is not linearly tractable). The value delivered: the
"oracle gap" mystery is fully explained and localized, and the two leads are now
known to share one bottleneck rather than being independent shots.

## Update 6 (gh60 follow-up RESOLVED): the repair is orthogonal to the residue

`delta_mode=8` compares gh60 of cascade vs prefix-44-lever near-collisions. The
decisive observation: the lever produces exactly **prefix-count** distinct gh60
values (16 prefixes→16, 64→64, 128→128). Reason from the round function: after
round 60, `g60 = e58` and `h60 = e57` (the g,h registers are shifted in *before*
W60 acts), so **gh60 is independent of W60_2** — hence of the prefix-44 lever and
the oracle — and `gh60 = f(w57, w58)` only (independent of `w59` too).

Consequence: the round-60 repair touches only `a60/e60`; it **cannot** disturb
the gh60 residue key. So the tail-repair and the gh60-keyed MITM residue are
**separable** — the repair preserves the residue structure by construction.
Tail-optimization (via W60_2) and residue-MITM (keyed on gh60 = f(w57,w58)) act on
orthogonal parts of the round-60 state. (Mode-8 distinct/witness ratios are
confounded by unequal witness populations — cascade has only the rare D60=0
triples; the round-structure argument above is the decisive one.)

## Final status

The schedule-realizable-repair investigation is **complete**:
1. Cascade a-zeroing is tail-suboptimal; one freed word recovers a big slice; the
   gain saturates (joint/coord-descent add nothing).
2. The full oracle is realizable at the interface via the prefix word `Wpre2[44]`
   (== oracle N=8/10/12, *beats* the e-zeroing oracle N=14).
3. The sole obstacle is the upstream `W44<->init2` coupling — tight, width-stable
   (~25-30% of state, N=12..24), == `block2_wang`'s dense schedule inverse.
4. The repair is **orthogonal to the gh60 residue** (gh60 = f(w57,w58)); it
   preserves the MITM residue by construction.

Net for the bet: no new *tractable* path (the upstream coupling is the same hard
problem block2_wang faces), but the oracle-gap mystery is fully explained, the
tail-repair and residue are shown separable, and the two leads are unified on one
bottleneck. Further work routes through `block2_wang`'s neutral-set machinery.
