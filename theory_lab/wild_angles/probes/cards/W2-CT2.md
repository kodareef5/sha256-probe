# W2-CT2 — Controllability-rank collapse pins "round 60"   ·   VERDICT: KILLED

**Card claim:** track rank of the round-by-round reachability matrix `R_t = [B, AB, ..., A^{t-1}B]`; the round `r*` where the target (`δH=0`) can no longer be covered by `Im R_t` is the cascade death, lands near 60/64, and **moves when a rotation constant is swapped** (ROR7→ROR8).

**Probe run:** GF(2) reachability-rank curve. `A` = one XOR-linearized SHA-256 round on the 8N-dim difference state (`kernels/linround.py`, carries dropped — the standard differential linearization the card asks for, Σ0/Σ1/σ rotations + the T1/T2 skeleton, Ch/Maj surrogate on). `B` = the per-round difference lever injected into register `a` (N columns). Tracked `rank(R_t)` for t=1..64 at N=8,10,12; ran the rotation-swap kicker (Σ0 first amount +1) at N=12. Throttled (`OMP_NUM_THREADS=2 taskpolicy -b`).

**Result (numbers):**
- Rank grows **strictly linearly** at +N per round (N=8: 8,16,24,…; N=10: 10,20,…; N=12: 12,24,…), then **monotonically saturates at the full state dimension 8N** (64 / 80 / 96) at **round 8**, and stays flat to round 64.
- Per-round gain `d1` = `[N×8 times, then 0×56]`. Rounds 55..64 gains are all **0** — perfectly flat, no dip.
- Saturation round `r* = 8` for all N (= `r*/64 ≈ 0.125`), **not ~60**.
- Kicker: baseline `r* = 8`, perturbed `r* = 8` → **moved by 0**.

**Kill_criterion:** "Dead if rank monotone-saturates (no collapse) or `r*` is insensitive to large rotation perturbations." — **fired? YES, on BOTH clauses.**

**Verdict reasoning:** KILLED. The linearized reachability rank does not collapse anywhere — it climbs monotonically and saturates the *entire* difference state by round 8 (each round injects N fresh independent levers; the round map is non-singular on the reached subspace, so SHR-induced bit-drops never starve it). There is no rank-deficiency event at round 60, and `r*` is completely insensitive to the rotation swap. The card's whole premise — that "sr=k reachable" is a falling reachability rank that crosses a threshold at ~60 and tracks the rotation constants — is false at the linear level. The real cascade death at round 60 is a property of the **nonlinear carry/T1+T2 structure and the specific output functional `δH=0`** (an intersection-with-an-affine-target effect), not of a contracting linear reachable subspace.

**Cross-check / skeptic note:** This directly corroborates lead finding #3 (control/rigidity dimension shows no sharp 60→61 discontinuity — and W1-PH2 KILLED). One could object that dropping carries removes the very singularity the card invokes; but the card's *own* probe specifies "XOR-linearize / GF(2) row-reduce," and the SHR bit-drops *are* retained in the linear σ/Σ maps — yet they cause zero rank loss because fresh `a`-injection each round dominates. If anything, keeping the real nonlinear/carry tail (as W2-CT1's modular probe did) is where "60" lives, and that is a deterministic-control census phenomenon, not a reachability-rank collapse. The "r* = 8 ≪ 60" gap is so large that no N-extrapolation rescues the round-60 claim.

**Reproduce:** `OMP_NUM_THREADS=2 taskpolicy -b python3 wild_angles/probes/cards/W2-CT2.py`
