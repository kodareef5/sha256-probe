# 2026-05-25: Schedule-Realizable Repair — the a-zeroing cascade is tail-suboptimal

Runner: macbook (kodareef5)
Tool: `prototypes/sched_repair_probe.c` (new), reuses the `free_word_mitm_reducedn.c` reduced-N model verbatim.
Evidence level: **EVIDENCE** (reduced-N, sampled at N>=10; effect consistent N=8..14; see caveats).

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

## Next

- Free all three message-2 words jointly (6-free-word search) — does it reach the oracle?
- Measure whether freed-word near-collisions retain MITM `gh60` residue structure.
- If structure survives: this is a real new DOF for the bet. If not: it bounds
  what the cascade costs and argues for a different residue definition.
