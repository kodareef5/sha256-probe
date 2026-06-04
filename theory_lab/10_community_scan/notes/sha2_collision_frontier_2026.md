# Note — The SHA-2 collision frontier, 2024–2026

**Citations (see `../papers.bib`):**
- Li, Liu, Wang. *New Records in Collision Attacks on SHA-2.* EUROCRYPT 2024
  (LNCS 14651); IACR ePrint [2024/349](https://eprint.iacr.org/2024/349).
- Li, Liu, Wang, Dong, Sun. *The First Practical Collision for 31-Step SHA-256.*
  ASIACRYPT 2024 (LNCS 15494; best-paper award).
- Zhang, Li, Gao, Wang. *Collision Attacks on SHA-256 up to 37 Steps with Improved
  Trail Search.* IACR ePrint [2026/232](https://eprint.iacr.org/2026/232).
- Alamgir, Nejati, Bright. *SHA-256 Collision Attack with Programmatic SAT.*
  [arXiv:2406.20072](https://arxiv.org/abs/2406.20072) (2024).
- Zhou, Sun, Zhang et al. *Quantum collision attacks on reduced SHA-256.* Quantum
  Information Processing 25(2), 2026; [DOI 10.1007/s11128-025-05024-w](https://doi.org/10.1007/s11128-025-05024-w).
- Classical lineage: Mendel–Nad–Schläffer (EUROCRYPT 2013), De Cannière–Rechberger
  (ASIACRYPT 2006), Mouha et al. (SAC 2010), Lipmaa–Moriai (FSE 2001).

## State of the frontier

- **Full SHA-256 is unbroken** (collision and preimage). All results are reduced-round.
- **31 steps** — first *practical* full collision (ASIACRYPT 2024). **39 steps** —
  semi-free-start (SFS) collision (EUROCRYPT 2024), beating the 38-step SFS record held
  since 2013. **~37 steps** — practical frontier via automated local-collision search
  (ePrint 2026/232). These broke ~decade-old records.
- **Dominant toolchain:** MILP-relaxed signed-differential-characteristic search →
  SAT/SMT realization → message modification. The MILP front-end is what got past the
  heuristic plateau that had stalled longer trails.
- **SAT+CAS variant:** a CDCL solver driven by a computer-algebra system through
  IPASIR-UP (CaDiCaL) to catch inconsistencies early — 38-step modified-IV collision
  vs. 28 steps for pure SAT.
- **Quantum sub-line (new):** convert the 39-step SFS collision into a two-block full
  collision quantumly; reported `t = 2^124/√S`. Still reduced-round, riding the
  classical characteristic.

## The two reduction axes (why this lab's project is a different cut)

| Axis | Knob | Compliance held fixed | Best public / project |
|---|---|---|---|
| **Round-count** (mainstream) | rounds `R < 64` | full message schedule | 31 practical / 37 / 39 SFS |
| **Schedule-compliance `sr`** (Viragh 2026 + this project) | enforce `sr` of 48 expansion eqs | all 64 rounds | sr=59 (Viragh) → **sr=60** (project); sr=61 open |

The axes parameterize *different* reduced-SHA-256 families and are not directly
comparable. But the sr axis is what isolates the message-schedule/carry obstruction as
the resisting object — which is precisely what the lab's adjacent-field angles target.

## Relevance to lab

Grounds the **community-context** layer for the whole catalog: it fixes the honest
baseline (full SHA-256 unbroken; mainstream effort = trail-search on the round-count
axis) so novelty of any lab angle is judged against what is *actually* being worked.
Concretely: it tells us the mainstream is **not** attacking the schedule/carry structure
as a standalone object, which is the opening every fresh angle in this lab tries to use.
Caveat: nothing here changes SHA-256's unbroken status; the project's sr=60 is a
semi-free-start certificate on a relaxed-schedule variant, not a full-SHA-256 collision.
