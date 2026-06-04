#!/usr/bin/env python3
"""
lever_feasibility.py — clean-lever matching analyzer for gap placement.

Supersedes the abandoned root script 04_alternative_gaps.py, whose analyzer
only modeled the t-2 (sigma1) enforcement rule (`if i-2 in free`) and never
implemented the linear t-7 / t-16 levers it explicitly proposed in its own
docstring. That buggy, solver-free analyzer wrongly declared non-contiguous
gaps "wasteful" and the idea was dropped.

The SHA-256 schedule recurrence has FOUR feedback terms:

    W[t] = sigma1(W[t-2]) + W[t-7] + sigma0(W[t-15]) + W[t-16]
            \__ t-2 ___/   \_t-7_/   \___ t-15 ___/   \_t-16_/
              sigma1        LINEAR        sigma0        LINEAR

"Gap placement" relaxes some schedule words to free SAT variables; the held
boundary words are then *controlled* by whichever free word sits in their
dependency set. The paper and every repo encoder only ever use the t-2 (sigma1)
lever, which CHAINS the boundary words W[61],W[62],W[63] onto too few free
words (one knob, several targets -> over-determined). The t-7 / t-16 terms enter
as the IDENTITY, so a free word placed there is a *dedicated, decoupled* knob
for exactly one boundary word.

NOTE on the GF(2) rank finding (see results/20260530_sigma_ranks.md): at N=32
sigma0 and sigma1 are BOTH full-rank (invertible). So the advantage of a linear
lever at N=32 is NOT "reaching values outside sigma1's image" (there is no image
restriction at N=32) — it is DECOUPLING: giving each boundary word its own
independent free knob instead of chaining several boundary words to one free
word through the sigma1 cascade.

This analyzer:
  * computes sr via the single clean formula sr = 16 + #{computed positions};
  * for a target boundary set (default {61,62,63}), finds a maximum bipartite
    matching of targets to DISTINCT free words drawn from each target's direct
    dependency set — a System of Distinct Representatives (SDR). A perfect
    matching == the boundary words are independently leverable (decoupled);
  * reports the lever kind per target (linear vs sigma) and the residual
    collision-freedom (free words not consumed as levers);
  * enumerates and ranks configs reaching sr in {60,61,62}.

It is pure combinatorics (no solver, no SHA evaluation) — it tells us which
(free_set, lever_assignment) configs are STRUCTURALLY worth encoding, not
whether they are SAT.
"""

import argparse
import itertools

# Offset -> (name, lever kind). Linear terms enter as identity (full rank).
FEEDBACK = [
    (2,  "sigma1_tm2",  "sigma"),
    (7,  "linear_tm7",  "linear"),
    (15, "sigma0_tm15", "sigma"),
    (16, "linear_tm16", "linear"),
]

LAST = 63          # final round index
FIRST_EXPANSION = 16   # first schedule-expansion position


def deps(t):
    """Direct schedule dependencies of W[t]: list of (pos, name, kind)."""
    return [(t - off, name, kind) for (off, name, kind) in FEEDBACK if t - off >= 0]


def schedule_compliance(free_positions):
    """sr = 16 + (# expansion positions 16..63 that are COMPUTED, i.e. not free).

    Free (relaxed) positions do not satisfy their schedule equation; every
    other position 16..63 is computed from the recurrence and so its equation
    holds by construction. Positions 0..15 are message words (always count).
    """
    free = set(free_positions)
    computed = [t for t in range(FIRST_EXPANSION, LAST + 1) if t not in free]
    return 16 + len(computed)


def _match(targets, free_positions):
    """Maximum bipartite matching: each target -> a distinct free word in its
    direct dependency set. Returns dict target -> (free_pos, name, kind) for the
    matched targets (Hungarian-style augmenting-path on a tiny graph).

    Prefers linear levers: dependency candidates are ordered linear-first so the
    greedy/augmenting search picks decoupled (t-7, t-16) knobs when available.
    """
    free = set(free_positions)
    # candidate lever words per target, linear levers first
    cand = {}
    for t in targets:
        opts = [(p, name, kind) for (p, name, kind) in deps(t) if p in free]
        opts.sort(key=lambda x: 0 if x[2] == "linear" else 1)
        cand[t] = opts

    assign = {}          # free_pos -> target
    chosen = {}          # target -> (free_pos, name, kind)

    def try_assign(t, seen):
        for (p, name, kind) in cand[t]:
            if p in seen:
                continue
            seen.add(p)
            if p not in assign or try_assign(assign[p], seen):
                assign[p] = t
                chosen[t] = (p, name, kind)
                return True
        return False

    for t in sorted(targets, reverse=True):   # solve highest round first
        try_assign(t, set())
    return chosen


def analyze(free_positions, targets=(61, 62, 63)):
    """Full structural report for one config."""
    free = sorted(free_positions)
    sr = schedule_compliance(free)
    targets = tuple(sorted(targets))
    matching = _match(targets, free)
    matched = [t for t in targets if t in matching]
    all_matched = len(matched) == len(targets)
    lever_words = {info[0] for info in matching.values()}
    residual = [p for p in free if p not in lever_words]
    n_linear = sum(1 for info in matching.values() if info[2] == "linear")
    tail_start = min(free) if free else LAST
    return {
        "free": free,
        "sr": sr,
        "tail_start": tail_start,
        "tail_rounds": LAST - tail_start + 1,
        "targets": targets,
        "matching": matching,
        "all_targets_independent": all_matched,
        "n_linear_levers": n_linear,
        "residual_freedom_words": residual,
        "residual_bits": len(residual) * 32,
    }


def _fmt(report):
    m = report["matching"]
    levers = ", ".join(
        f"{t}<-W[{m[t][0]}]({m[t][1]})" if t in m else f"{t}<-NONE"
        for t in report["targets"]
    )
    flag = "INDEP-CONTROLLABLE" if report["all_targets_independent"] else "COUPLED/INFEASIBLE"
    return (f"free={report['free']}  sr={report['sr']}  "
            f"tail={report['tail_rounds']}r  linear_levers={report['n_linear_levers']}  "
            f"residual={report['residual_freedom_words']} ({report['residual_bits']}b)\n"
            f"      levers: {levers}   [{flag}]")


def enumerate_configs(sr_levels=(60, 61, 62), pos_lo=44, pos_hi=63,
                      targets=(61, 62, 63)):
    """Enumerate free-position sets reaching each sr level and rank them.

    sr = 64 - len(free), so sr=60 -> 4 free, sr=61 -> 3 free, sr=62 -> 2 free.
    Free positions drawn from [pos_lo, pos_hi]; targets must NOT be free (we want
    to HOLD the boundary). Ranked by: independently-controllable, #linear levers,
    residual freedom, shorter tail.
    """
    results = {}
    for sr in sr_levels:
        n_free = 64 - sr
        configs = []
        for combo in itertools.combinations(range(pos_lo, pos_hi + 1), n_free):
            if any(t in combo for t in targets):
                continue  # boundary targets must be held, not free
            rep = analyze(combo, targets)
            configs.append(rep)
        configs.sort(key=lambda r: (
            not r["all_targets_independent"],
            -r["n_linear_levers"],
            -r["residual_bits"],
            r["tail_rounds"],
        ))
        results[sr] = configs
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=6, help="top configs to show per sr")
    ap.add_argument("--targets", default="61,62,63")
    args = ap.parse_args()
    targets = tuple(int(x) for x in args.targets.split(","))

    print("=" * 78)
    print("CLEAN-LEVER MATCHING ANALYSIS  (target boundary set = %s)" % (targets,))
    print("=" * 78)

    # --- The two head-to-head reference configs ---
    print("\n--- Headline LINEAR-LEVER config (the new idea) ---")
    head = analyze({54, 55, 56, 57}, targets)
    print(_fmt(head))
    assert head["sr"] == 60, f"headline config sr={head['sr']}, expected 60"
    assert head["all_targets_independent"], "headline config should be indep-controllable"
    assert head["n_linear_levers"] == 3, "headline config should use 3 linear levers"
    print("      -> CONFIRMED sr=60 (held = {16..53} U {58..63} = 44 eqs), NOT sr=58.")

    print("\n--- Paper/repo SIGMA1-CASCADE sr=60 (the wall) ---")
    wall = analyze({57, 58, 59, 60}, targets)
    print(_fmt(wall))
    assert wall["sr"] == 60
    assert not wall["all_targets_independent"], \
        "sigma1 cascade sr=60 should FAIL to independently lever all of {61,62,63}"
    miss = [t for t in targets if t not in wall["matching"]]
    print(f"      -> W{miss} has NO free lever: sigma1 cascade canNOT hold+control "
          f"all boundary words at sr=60. This is the wall.")

    # --- Enumerated ranking ---
    ranked = enumerate_configs(sr_levels=(60, 61, 62), targets=targets)
    for sr, configs in ranked.items():
        n_free = 64 - sr
        indep = [c for c in configs if c["all_targets_independent"]]
        print(f"\n{'='*78}\nsr={sr}  ({n_free} free words)  — "
              f"{len(indep)}/{len(configs)} configs independently controllable")
        print("-" * 78)
        for rep in configs[: args.top]:
            print(_fmt(rep))


if __name__ == "__main__":
    main()
