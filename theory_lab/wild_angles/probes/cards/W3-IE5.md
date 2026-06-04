# W3-IE5 — Three-distance theorem → the bumpy collision-vs-N features   ·   VERDICT: KILLED

**Card claim:** {7,18,3},{17,19,10} mod N give ≤3 distinct gaps (Steinhaus); the multiset's CF-transition points predict the discrete jumps in collision multiplicity (the "N=10 spike", the |de58| jumps).

**Probe run:** Pure arithmetic N=4..40. Built the exact three-distance gap multiset for each σ rotation amount mod N (verified ≤3 distinct gaps), defined the card's "transition" signal (change in #distinct gaps and/or CF/rational resonance amount-mod-N), and tested alignment vs the real collision/|de58| extrema; emitted an out-of-sample next-jump and measured the rule's specificity. Throttled (`taskpolicy -b`, OMP=2).

**Result (numbers):**
- Steinhaus ≤3-distinct-gaps: holds for every amount, every N (sanity OK).
- Real features (local extrema): collision SPIKE @N=9 (14263), TROUGH @N=10 (1467); de58 SPIKE @N=12 — feature-N's {5,6,9,10,12}.
- Three-distance transition fires at **11/11 N** in-sample (every N), "hitting" all 5 features — but expected hits by chance = **5.0**, actual = **5** → exactly chance, zero discrimination.
- It flags N=9 (spike) and N=10 (trough) identically — cannot tell them apart.
- Out-of-sample: pre-registered next jump = N=15, but the rule flags **26/26 = 100%** of N in 15..40 (specificity 0%).

**Kill_criterion:** "no alignment with the empirical jumps" — **fired? YES** (alignment is indistinguishable from chance; the rule flags everything)

**Verdict reasoning:** The three-distance "transition signal" fires at *every* N (100% flag density in- and out-of-sample), so its apparent 5/5 feature coincidence is exactly what chance gives (5.0 expected) — it carries zero predictive information. It cannot distinguish the N=9 spike from the N=10 trough (both flagged like all N), and the card even **misidentifies** its headline feature: the data make N=10 a *trough*, not the "spike" the card claims to predict. This is precisely the failure mode the card's own skeptic flagged ("3 constants + free combination can fit any bumpy curve; only an out-of-sample prediction counts") — and the out-of-sample rule is unfalsifiable (flags 100% of N). It **post-hoc fits; it does not predict** (prior finding #4 confirmed).

**Cross-check / skeptic note:** Steinhaus three-distance is real and verified, so the kill is not about the theorem but about its *predictive content here* — none. A charitable reader might pick a stricter transition definition (only #distinct-gaps changes, dropping CF-resonance) to lower flag density, but any rule built from 6 free rotation constants with free combination over a 9-point bumpy curve is overdetermined; the only honest bar is out-of-sample specificity, which is 0%. The genuine collision-vs-N bumpiness is real but is driven by the kernel/cascade combinatorics (N=9→14263, N=10→1467), not by an arithmetic rotation-gap resonance.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W3-IE5.py`
