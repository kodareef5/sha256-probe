# W7-CG5 — Octal-game encoding: read the wall off the nim-sequence period   ·   VERDICT: KILLED

**Card claim:** Encode carry resolution as an octal/subtraction game on the de58 heap; octal games are eventually periodic (Guy–Smith), so the wall = where de58's *size* lands on a Grundy-0 slot of the (periodic) nim-sequence — a number-theoretic prediction.

**Probe run:** Faithful mini-SHA(N) cascade. Tested the DEFINING property of an octal/subtraction game — move legality from a heap depends only on heap SIZE — by (a) grouping all states-entering-round-58 by their de58 value and comparing their reachable next-de58 move-sets, and (b) mapping the de58-setting prefix word u → de58 to check for a size-indexed transition sequence. N=8, N=10. Throttled: yes.

**Result (numbers):**
- Every state's reachable next-de58 move-set under the round-58 free word has size **1** (a singleton): the round-58 "move" does NOT change de58 (0/256 and 0/1024 states reach more than one value). de58 is fixed by the *earlier* round (w57's analog), not by a move on the heap.
- de58 is produced ONCE, via a **many-to-one** map u→de58: uniform fibers of size **32** at N=8 (256/8) and **64** at N=10 (1024/16); the map is non-monotone (e.g. de58(u=0..15)=[194,194,196,196,178,178,180,180,…]). |de58 image| = 8, 16 = 2^hw(db56).

**Kill_criterion:** "the SHA carry rule corresponds to NO well-defined octal game (move legality depends on more than heap size)." — **fired? yes.**

**Verdict reasoning:** There is no octal game to encode. (1) **No moves on the heap:** the natural "play on the de58 heap" word (round-58 input) leaves de58 a singleton — there are no size-transforming moves. (2) **No size-indexed sequence:** de58 is generated at a single round (the value is set once by the prefix word), so there is no progression of heap sizes 0,1,2,… for a Grundy sequence to be defined over — the Guy–Smith eventual-periodicity theorem has no input. (3) **What structure exists is addend-bit-, not size-, governed:** de58 = the many-to-one image of a group-free carry map (prior finding #5), exactly the "legality depends on the actual bits, not the size" failure the card was flagged for. The wall is the schedule identity g1=0∧h=0 (CG3/CG4), not a Grundy-0 slot of any nim-sequence. KILLED as a forced-fit / category error (finding #6 confirmed); no new number or period emerges, so the CONFIRM bar is not met.

**Cross-check / skeptic note:** The mini-SHA again reproduces |de58|=2^hw(db56) (8, 16), so the engine is sound. The earlier coarse test reported "legality depends only on size = True", but inspection showed that is *vacuous* — every move-set is a forced singleton, i.e. there are no moves to be size-dependent. A defender could try to *define* an octal code on the abstract size 2^hw, but with a single size per N and no transition rule, eventual periodicity is content-free. No prediction survives.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W7-CG5.py`
