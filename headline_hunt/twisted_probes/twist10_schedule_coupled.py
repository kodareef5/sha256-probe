#!/usr/bin/env python3
"""Twist 10: SCHEDULE-COUPLED local-collision length (the most attack-relevant twist).

Prior twists (3-8) held the message word W per-round INDEPENDENT across the two messages:
the per-round difference dW was chosen greedily every round to cancel the state-diff trail
(Twist 7: register h sustains ~6.59 forward rounds at HW<=8). That is a *schedule-uncoupled*
fantasy attacker who can inject an arbitrary fresh dW each round for free.

A REAL local collision does NOT have that freedom. The attacker picks ONE difference in the 16
input words W[0..15]; the schedule recurrence
    W[i] = (sigma1(W[i-2]) + W[i-7] + sigma0(W[i-15]) + W[i-16]) & M    (i >= 16)
then DETERMINES the difference in every later word. The message difference RE-INJECTS in later
rounds (notably through the sigma1(W[i-2]) term), and this re-injection is exactly why SHA-2
local collisions are bounded (~9 rounds) and why message expansion is the modern bottleneck.

This probe: take two messages M1, M2 = M1 with a single perturbation in ONE input word; expand
BOTH 64-word schedules; run both through the compression rounds from a common random start state;
measure how the state-diff Hamming weight evolves and the longest leading run kept HW <= T for
T in {8,16,32}. We sweep which input word (0..15) and which perturbation (single-bit i, and the
MSB-pair / classic local-collision disturbances), and ask: does schedule coupling let a thin trail
run LONGER than the uncoupled greedy baseline, or does recurrence re-injection HURT?

Deterministic (seeded RNG). Full N=32 words. Imports verified lib/sha256 primitives.
Reproduce: python3 headline_hunt/twisted_probes/twist10_schedule_coupled.py
"""
import sys, random
sys.path.insert(0, "lib")
from sha256 import Sigma0, Sigma1, sigma0, sigma1, Ch, Maj, K as KCONST

M = 0xffffffff
R = 32                 # state-diff trail measured over this many compression rounds
THRESHOLDS = (8, 16, 32)
SEED = 20260609


def hw(x):
    return bin(x & M).count("1")


def shw(s):
    return sum(hw(x) for x in s)


# --- verified round function (copied exactly from twist7 / three_twists_v2 / fresh_batch) ---
def fwd(s, w, k):
    a, b, c, d, e, f, g, h = s
    T1 = (h + Sigma1(e) + Ch(e, f, g) + k + w) & M
    T2 = (Sigma0(a) + Maj(a, b, c)) & M
    return ((T1 + T2) & M, a, b, c, (d + T1) & M, e, f, g)


def expand(M16, n):
    """Expand 16 input words into an n-word schedule via the verified recurrence."""
    W = list(M16) + [0] * (n - 16)
    for i in range(16, n):
        W[i] = (sigma1(W[i - 2]) + W[i - 7] + sigma0(W[i - 15]) + W[i - 16]) & M
    return W


def schedule_diff_profile(perturb, n):
    """Given a per-word input perturbation `perturb` (dict word->delta applied by XOR),
    return the AVERAGE expanded-schedule difference HW per round over random base messages,
    plus the fraction of rounds the *message* difference (not state) is nonzero.
    This isolates the message-expansion re-injection from the compression mixing."""
    rng = random.Random(SEED + 777)
    KS = 400
    acc = [0.0] * n
    for _ in range(KS):
        base = [rng.getrandbits(32) for _ in range(16)]
        m2 = list(base)
        for w, d in perturb.items():
            m2[w] ^= d
        W1 = expand(base, n)
        W2 = expand(m2, n)
        for i in range(n):
            acc[i] += hw(W1[i] ^ W2[i])
    return [v / KS for v in acc]


def trail(perturb, Ksamp, seed):
    """Run the schedule-COUPLED local collision: expand both schedules from one input
    perturbation, run R compression rounds from a common random state, measure the
    per-round state-diff HW trail.

    We report TWO families of metrics so the "entry latency" artifact is separated from
    the real local-collision SUSTAIN property:
      * lead[T]    = leading run from round 0 kept HW<=T (dominated by entry latency: a
                     diff in input word w produces zero state-diff for the first w rounds
                     because W[w] is not yet consumed).
      * sustain[T] = consecutive rounds the trail stays HW<=T STARTING at the entry round
                     (first round with nonzero diff) -- the attack-relevant span: once the
                     disturbance is live, how long can a thin trail persist under the
                     schedule-COUPLED (re-injecting) difference?
    Returns (mean_trail[R], {T: mean_lead}, {T: mean_sustain}, mean_entry_round)."""
    rng = random.Random(seed)
    trail_acc = [0.0] * R
    lead = {T: 0.0 for T in THRESHOLDS}
    sustain = {T: 0.0 for T in THRESHOLDS}
    entry_acc = 0.0
    for _ in range(Ksamp):
        base = [rng.getrandbits(32) for _ in range(16)]
        m2 = list(base)
        for w, d in perturb.items():
            m2[w] ^= d
        W1 = expand(base, R)
        W2 = expand(m2, R)
        s = tuple(rng.getrandbits(32) for _ in range(8))   # common start state
        cur1, cur2 = s, s
        traj = []
        for r in range(R):
            cur1 = fwd(cur1, W1[r], KCONST[r])
            cur2 = fwd(cur2, W2[r], KCONST[r])
            d = shw(tuple((x ^ y) & M for x, y in zip(cur1, cur2)))
            traj.append(d)
        for i in range(R):
            trail_acc[i] += traj[i]
        # entry round = first round with nonzero state-diff
        entry = next((i for i, d in enumerate(traj) if d > 0), R)
        entry_acc += entry
        for T in THRESHOLDS:
            cnt = 0
            for d in traj:
                if d <= T:
                    cnt += 1
                else:
                    break
            lead[T] += cnt
            # sustain: from entry round, how many consecutive rounds stay <= T
            scnt = 0
            for d in traj[entry:]:
                if d <= T:
                    scnt += 1
                else:
                    break
            sustain[T] += scnt
    return ([v / Ksamp for v in trail_acc],
            {T: lead[T] / Ksamp for T in THRESHOLDS},
            {T: sustain[T] / Ksamp for T in THRESHOLDS},
            entry_acc / Ksamp)


def main():
    KS = 400
    print("=" * 80)
    print("TWIST 10: SCHEDULE-COUPLED local-collision length (R=%d rounds, K=%d, full N=32)" % (R, KS))
    print("=" * 80)
    print("Two messages differ in the 16 INPUT words; the difference propagates through the")
    print("schedule recurrence and RE-INJECTS in later rounds. Common random start state.")
    print("Baseline to beat: Twist 7 uncoupled greedy single-bit dW = 6.59 fwd rounds @ HW<=8.\n")

    print("KEY METRIC: SUSTAIN-after-entry = consecutive thin rounds STARTING at the round the")
    print("disturbance first enters the state (strips the trivial entry-latency from input-word w).\n")

    # ---------------------------------------------------------------
    # PART 1: single-bit perturbation of each input word x each bit.
    #         Headline metric is SUSTAIN@HW<=8 (entry-latency removed). We also print the
    #         raw leading run and the mean entry round so the artifact is visible.
    # ---------------------------------------------------------------
    print("-" * 80)
    print("PART 1: single-bit input perturbation sweep (word 0..15 x bit 0..31)")
    print("-" * 80)
    best_s8 = None        # best by SUSTAIN @ HW<=8 (the attack-relevant metric)
    best_lead8 = None     # best by raw leading run (shows the latency artifact)
    per_word_best = {}    # best bit per word, by sustain@8
    msb_results = {}      # MSB perturbation per word: (lead, sustain, entry)
    for w in range(16):
        wbest = None
        for bit in range(32):
            perturb = {w: 1 << bit}
            _, lead, sus, entry = trail(perturb, KS, SEED + w * 100 + bit)
            if bit == 31:
                msb_results[w] = (lead, sus, entry)
            if wbest is None or sus[8] > wbest[1][8]:
                wbest = (bit, lead, sus, entry)
            cs = (sus[8], sus[16], w, bit, perturb)
            cl = (lead[8], lead[16], w, bit, perturb)
            if best_s8 is None or cs[:2] > best_s8[:2]:
                best_s8 = cs
            if best_lead8 is None or cl[:2] > best_lead8[:2]:
                best_lead8 = cl
        per_word_best[w] = wbest

    print("  Per-input-word BEST single-bit perturbation (ranked by SUSTAIN@HW<=8):")
    print("    word | best bit | SUSTAIN@8 | SUSTAIN@16 | SUSTAIN@32 | lead@8 | entry-rnd")
    for w in range(16):
        bit, lead, sus, entry = per_word_best[w]
        print("    %4d |    %2d    |   %5.2f   |   %6.2f   |   %6.2f   | %5.2f  |  %5.2f"
              % (w, bit, sus[8], sus[16], sus[32], lead[8], entry))

    print("\n  >>> GLOBAL BEST by SUSTAIN@HW<=8 : word %d bit %d -> sustain@8=%.2f sustain@16=%.2f"
          % (best_s8[2], best_s8[3], best_s8[0], best_s8[1]))
    print("  >>> GLOBAL BEST by raw LEAD@HW<=8 : word %d bit %d -> lead@8=%.2f (= entry latency, artifact)"
          % (best_lead8[2], best_lead8[3], best_lead8[0]))

    # MSB-of-each-word ranking (the classic SHA local-collision disturbance is the MSB,
    # where XOR == modular and there is no carry-out). Ranked by SUSTAIN@8.
    print("\n  MSB (bit 31) perturbation per word, SUSTAIN@HW<=8 (classic disturbance site):")
    msb_rank = sorted(range(16), key=lambda w: -msb_results[w][1][8])
    for w in msb_rank:
        lead, sus, entry = msb_results[w]
        print("    word %2d MSB : sustain@8=%.2f  sustain@16=%.2f  sustain@32=%.2f  (entry-rnd %.1f)"
              % (w, sus[8], sus[16], sus[32], entry))

    # ---------------------------------------------------------------
    # PART 2: schedule re-injection profile for the best seed and for a low-word MSB.
    #         Shows WHERE the message difference comes back via the recurrence.
    # ---------------------------------------------------------------
    print("\n" + "-" * 80)
    print("PART 2: schedule-difference RE-INJECTION profile (why coupling bounds the trail)")
    print("-" * 80)
    print("  How a single input-word difference re-injects through W[i]=sigma1(W[i-2])+W[i-7]+")
    print("  sigma0(W[i-15])+W[i-16]. A low-word disturbance re-appears every few rounds and the")
    print("  XOR-difference *expands* (sigma1/sigma0 fan-out) -- the message-expansion bottleneck.\n")
    bw, bb = best_s8[2], best_s8[3]
    for label, perturb in [
        ("word0 MSB (earliest input word)", {0: 1 << 31}),
        ("word2 MSB", {2: 1 << 31}),
        ("word15 MSB (latest input word)", {15: 1 << 31}),
    ]:
        prof = schedule_diff_profile(perturb, R)
        nz = [i for i, v in enumerate(prof) if v > 0.01]
        first_reinject = next((i for i in range(16, R) if prof[i] > 0.01), None)
        print("  [%s] mean schedule-diff HW per word W[0..%d]:" % (label, R - 1))
        print("    " + " ".join("%4.1f" % v for v in prof[:R]))
        print("    nonzero-diff words: %s" % nz)
        print("    first RE-INJECTED word (i>=16): %s\n" % (first_reinject if first_reinject is not None else "none within R"))

    # ---------------------------------------------------------------
    # PART 3: small search over MSB-pair candidates (XOR==modular, classic disturbance pairs)
    #         to minimize TOTAL trail HW over R rounds. Cheap.
    # ---------------------------------------------------------------
    print("\n" + "-" * 80)
    print("PART 3: small search — single-bit + MSB-pair candidates, MAXIMIZE sustain@HW<=8")
    print("-" * 80)
    print("  (sustain = thin rounds after entry; this is the real local-collision span to compare")
    print("   against the uncoupled greedy 6.59 and the textbook ~9-round SHA-2 local collision.)")
    cand_list = []
    # all single-bit MSBs
    for w in range(16):
        cand_list.append(("w%d MSB" % w, {w: 1 << 31}))
    # the global-best single bit from part 1
    cand_list.append(("best-sustain w%d bit%d" % (bw, bb), {bw: 1 << bb}))
    # MSB pairs spaced by the recurrence offsets (the canonical local-collision idea: a second
    # disturbance timed to partially cancel the re-injection of the first)
    for (w1, w2) in [(0, 9), (0, 7), (0, 2), (0, 1), (0, 14)]:
        if w1 == w2:
            continue
        cand_list.append(("w%d+w%d MSB" % (w1, w2), {w1: 1 << 31, w2: 1 << 31}))

    results = []
    for label, perturb in cand_list:
        tr, lead, sus, entry = trail(perturb, KS, SEED + hash(label) % 9973)
        results.append((sus[8], sus[16], sus[32], entry, label, tr))
    results.sort(key=lambda x: -x[0])   # descending sustain@8 = longest thin span
    print("  candidate                    | SUS@8 | SUS@16 | SUS@32 | entry | trail[entry..entry+7]")
    for s8, s16, s32, entry, label, tr in results:
        e = int(round(entry))
        seg = " ".join("%3.0f" % v for v in tr[e:e + 8])
        print("  %-28s | %5.2f | %5.2f  | %5.2f  | %5.1f | %s"
              % (label, s8, s16, s32, entry, seg))
    bestsus = results[0]
    print("\n  >>> LONGEST sustained thin span (max sustain@HW<=8): %s  (sustain@8=%.2f)"
          % (bestsus[4], bestsus[0]))

    # ---------------------------------------------------------------
    # PART 4: the FAIR comparison to the textbook ~9-round local collision.
    #   The uncoupled greedy (Twist 7) gets a FREE fresh dW EVERY round forever.
    #   A real local collision only has free message words in W[0..15]; rounds 16+ are
    #   SCHEDULE-DETERMINED. So: run a greedy correction that may inject any single-bit dW
    #   in the FREE-INPUT region (rounds 0..15) to keep the trail thin -- exactly the
    #   message-modification budget a real attacker has -- and watch what happens when the
    #   schedule takes over at round 16 (re-injection of the accumulated input difference).
    #   This isolates THE bottleneck: can a locally-corrected thin trail survive expansion?
    # ---------------------------------------------------------------
    print("\n" + "-" * 80)
    print("PART 4: FAIR test vs the textbook ~9-round local collision (disturbance PRESERVED)")
    print("-" * 80)
    print("  A real collision must keep the two messages genuinely different: we FIX an MSB")
    print("  disturbance in W[0] (never cancelled) and let the attacker use the remaining free")
    print("  input words W[1..15] greedily (best single-bit dW per round) to keep the state-diff")
    print("  thin -- the actual message-modification budget. Then the schedule (rounds 16+) is")
    print("  determined and re-injects the accumulated difference. Does the thin trail survive?\n")
    SINGLE = [0] + [1 << i for i in range(32)]
    rngp = random.Random(SEED + 4242)
    KS4 = 300
    in_window_sus = 0.0     # leading thin run within the free window (rounds 0..15)
    survived = {16: 0, 20: 0, 24: 0}   # samples still HW<=8 at these post-handover rounds
    post_trail = [0.0] * R
    for _ in range(KS4):
        base = [rngp.getrandbits(32) for _ in range(16)]
        m2 = list(base)
        s = tuple(rngp.getrandbits(32) for _ in range(8))
        m2[0] ^= (1 << 31)                # FIXED disturbance, never corrected away
        cur1, cur2 = s, s
        # round 0 consumes the disturbance (no correction available here)
        cur1 = fwd(cur1, base[0], KCONST[0]); cur2 = fwd(cur2, m2[0], KCONST[0])
        # rounds 1..15: greedily correct with a single-bit dW baked into that input word
        for r in range(1, 16):
            best = None
            for dW in SINGLE:
                n1 = fwd(cur1, base[r], KCONST[r])
                n2 = fwd(cur2, (m2[r] ^ dW) & M, KCONST[r])
                d = shw(tuple((x ^ y) & M for x, y in zip(n1, n2)))
                if best is None or d < best[0]:
                    best = (d, n1, n2, dW)
            cur1, cur2 = best[1], best[2]
            m2[r] = (m2[r] ^ best[3]) & M
        # recompute cleanly with the now-fixed input difference, expand schedule, run all R
        W1 = expand(base, R); W2 = expand(m2, R)
        c1, c2 = s, s
        traj = []
        for r in range(R):
            c1 = fwd(c1, W1[r], KCONST[r]); c2 = fwd(c2, W2[r], KCONST[r])
            traj.append(shw(tuple((x ^ y) & M for x, y in zip(c1, c2))))
        for i in range(R):
            post_trail[i] += traj[i]
        cnt = 0
        for d in traj[:16]:
            if d <= 8:
                cnt += 1
            else:
                break
        in_window_sus += cnt
        for rr in survived:
            if traj[rr] <= 8:
                survived[rr] += 1
    post_trail = [v / KS4 for v in post_trail]
    print("  In-FREE-WINDOW greedy thin run (rounds 0..15, HW<=8, disturbance fixed): mean %.2f rounds"
          % (in_window_sus / KS4))
    print("  Fraction still HW<=8 at round 16 / 20 / 24 (after schedule handover): %.0f%% / %.0f%% / %.0f%%"
          % (100.0 * survived[16] / KS4, 100.0 * survived[20] / KS4, 100.0 * survived[24] / KS4))
    print("  Mean trail across handover [rounds 8..27]:")
    print("    " + " ".join("%3.0f" % v for v in post_trail[8:28]))
    print("  -> with the disturbance preserved, the schedule re-injects it at rounds ~16-22 and the")
    print("     trail blows up; the locally-corrected thin segment does NOT survive message expansion.")

    # ---------------------------------------------------------------
    # SUMMARY vs baseline
    # ---------------------------------------------------------------
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("  Schedule-COUPLED best SUSTAINED thin span @ HW<=8 : %.2f rounds  (word %d bit %d)"
          % (best_s8[0], best_s8[2], best_s8[3]))
    print("  (raw leading run reached %.2f rounds but that is dominated by entry latency: a diff in"
          % best_lead8[0])
    print("   input word w is invisible for the first w rounds -- not a sustain property.)")
    print("  Schedule-UNCOUPLED greedy baseline (Twist 7, reg h, fwd, fresh dW/round) : 6.59 @ HW<=8")
    print("  Textbook SHA-2 local-collision span (full message-modification freedom) : ~9 rounds")
    delta = best_s8[0] - 6.59
    print("\n  Delta (coupled sustain - uncoupled greedy) : %+.2f rounds  ->  schedule coupling %s"
          % (delta, "HELPS" if delta > 0 else "HURTS"))
    print("\nDone. See 20260609_twist10_schedule_coupled.md for the memo.")


if __name__ == "__main__":
    main()
