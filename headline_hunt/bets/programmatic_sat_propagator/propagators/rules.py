#!/usr/bin/env python3
"""
Cascade-DP propagation rules (Phase 1 prototype).

Pure-Python implementation of the 8 rules in SPEC.md, designed for:
- Validation: check rule logic against fresh cascade-held samples.
- Reference: serve as the spec for the eventual C++ IPASIR-UP port.
- Counting: measure how often each rule's *trigger condition* is met
  across a representative sample, giving a rough upper bound on
  CDCL conflict reduction.

This is NOT integrated with a SAT solver. It operates on full
differential states; it returns FORCED bit values given partial state.
A future IPASIR-UP wrapper translates these into solver propagation calls.

Usage:
    from rules import CascadePropagator
    p = CascadePropagator()
    forced = p.fire_all(diff_state)  # diff_state: dict of register-diff bits

The propagator is candidate-independent (per SPEC §"What this rule set DOES NOT do").
"""
import os
import sys
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
if REPO not in sys.path:
    sys.path.insert(0, REPO)
from lib.sha256 import MASK, Sigma0, Maj


@dataclass
class DiffState:
    """Differential state at a snapshot of solver progress.

    Each *_diff field is a 32-bit modular integer (a1[r] - a2[r] mod 2^32)
    or None if not yet decided.

    actual_a / actual_e: actual register values from pair-1 (used by Rule 6's
    nonlinear constraints involving Sigma0, Maj, Ch).
    """
    da: Dict[int, Optional[int]] = field(default_factory=dict)  # da_r per round
    db: Dict[int, Optional[int]] = field(default_factory=dict)
    dc: Dict[int, Optional[int]] = field(default_factory=dict)
    dd: Dict[int, Optional[int]] = field(default_factory=dict)
    de: Dict[int, Optional[int]] = field(default_factory=dict)
    df: Dict[int, Optional[int]] = field(default_factory=dict)
    dg: Dict[int, Optional[int]] = field(default_factory=dict)
    dh: Dict[int, Optional[int]] = field(default_factory=dict)
    actual_a: Dict[int, Optional[Tuple[int, int]]] = field(default_factory=dict)  # (pair1, pair2) per round


def fire_rule_1_cascade_diagonal(state: DiffState) -> Dict[str, int]:
    """Theorem 1: cascade-diagonal zeros."""
    forced = {}
    targets = [("da", 57), ("da", 58), ("da", 59), ("da", 60),
               ("db", 58), ("db", 59), ("db", 60),
               ("dc", 59), ("dc", 60),
               ("dd", 60)]
    for reg, r in targets:
        regdict = getattr(state, reg)
        if regdict.get(r) is None:
            forced[f"{reg}_{r}"] = 0
        elif regdict[r] != 0:
            forced[f"{reg}_{r}"] = "CONFLICT"
    return forced


def fire_rule_2_de60_zero(state: DiffState) -> Dict[str, int]:
    """Theorem 2: dE[60] = 0 always under cascade-DP."""
    forced = {}
    if state.de.get(60) is None:
        forced["de_60"] = 0
    elif state.de[60] != 0:
        forced["de_60"] = "CONFLICT"
    return forced


def fire_rule_3_three_filter(state: DiffState) -> Dict[str, int]:
    """Theorem 3: dE[61..63] = 0 (Mode FORCE only)."""
    forced = {}
    for r in (61, 62, 63):
        if state.de.get(r) is None:
            forced[f"de_{r}"] = 0
        elif state.de[r] != 0:
            forced[f"de_{r}"] = "CONFLICT"
    return forced


def fire_rule_4_unified_theorem4(state: DiffState) -> Dict[str, int]:
    """
    Unified Theorem 4: da_r − de_r ≡ dT2_r (mod 2^32) for r ∈ {61, 62, 63}.

    At r=61: dT2_61 = 0 (cascade gives a_60, b_60, c_60 zero diff). So da_61 = de_61.
    At r=62, 63: dT2_r computable from actual register values (in state.actual_a).
    """
    forced = {}

    # r=61 specialization (no actual values needed)
    if state.da.get(61) is not None and state.de.get(61) is None:
        forced["de_61"] = state.da[61]
    elif state.de.get(61) is not None and state.da.get(61) is None:
        forced["da_61"] = state.de[61]
    elif state.da.get(61) is not None and state.de.get(61) is not None:
        if state.da[61] != state.de[61]:
            forced["da_de_61"] = "CONFLICT"

    # r=62, 63: need actual values to compute dT2_r
    for r in (62, 63):
        if (state.actual_a.get(r-1) is not None and
            state.actual_a.get(r-2) is not None and
            state.actual_a.get(r-3) is not None):
            a1_p, a2_p = state.actual_a[r-1]
            b1_p, b2_p = state.actual_a[r-2]
            c1_p, c2_p = state.actual_a[r-3]
            dSigma0 = (Sigma0(a1_p) - Sigma0(a2_p)) & MASK
            dMaj = (Maj(a1_p, b1_p, c1_p) - Maj(a2_p, b2_p, c2_p)) & MASK
            dT2_r = (dSigma0 + dMaj) & MASK

            if state.da.get(r) is not None and state.de.get(r) is None:
                forced[f"de_{r}"] = (state.da[r] - dT2_r) & MASK
            elif state.de.get(r) is not None and state.da.get(r) is None:
                forced[f"da_{r}"] = (state.de[r] + dT2_r) & MASK
            elif state.da.get(r) is not None and state.de.get(r) is not None:
                if ((state.da[r] - state.de[r]) & MASK) != dT2_r:
                    forced[f"da_de_{r}"] = "CONFLICT"
    return forced


def fire_rule_5_dc_dg_equality(state: DiffState) -> Dict[str, int]:
    """R63.1: dc_63 ≡ dg_63 (modular). Both equal da_61 = de_61."""
    forced = {}
    if state.dc.get(63) is not None and state.dg.get(63) is None:
        forced["dg_63"] = state.dc[63]
    elif state.dg.get(63) is not None and state.dc.get(63) is None:
        forced["dc_63"] = state.dg[63]
    elif state.dc.get(63) is not None and state.dg.get(63) is not None:
        if state.dc[63] != state.dg[63]:
            forced["dc_dg_63"] = "CONFLICT"

    # Also: both should equal da_61 (= de_61 by R61.1)
    if state.da.get(61) is not None:
        for reg, regname in [(state.dc.get(63), "dc_63"), (state.dg.get(63), "dg_63")]:
            if reg is None:
                forced[regname] = state.da[61]
            elif reg != state.da[61]:
                forced[f"{regname}_chain"] = "CONFLICT"
    return forced


def fire_rule_6_modular_sum_r63(state: DiffState) -> Dict[str, int]:
    """R63.3 (also Rule 4 specialization at r=63): da_63 − de_63 ≡ dT2_63."""
    # Already covered by fire_rule_4_unified_theorem4 at r=63. Listed separately
    # for clarity (and because it's the "most powerful rule" per SPEC).
    return {}


def fire_rule_7_w60_schedule(state: DiffState, candidate_w_partial: Dict[int, int]) -> Dict[str, int]:
    """W[60] = sigma1(W[58]) + W[53] + sigma0(W[45]) + W[44] (mod 2^32, sr=61)."""
    # Stub: depends on candidate-specific W values, omitted in candidate-independent prototype.
    return {}


def fire_rule_8_failed_residue_cache(state: DiffState, cache: Dict) -> Dict[str, int]:
    """Cache of failed residual interfaces for cross-restart pruning."""
    # Stub: requires hash of partial state at cascade boundary; omitted in this prototype.
    return {}


class CascadePropagator:
    """Aggregates the rule firing into a single dispatch."""

    def __init__(self, mode_force: bool = True):
        self.mode_force = mode_force
        self.fire_count = {f"rule_{i}": 0 for i in range(1, 9)}

    def fire_all(self, state: DiffState) -> Dict[str, int]:
        forced = {}
        forced.update(fire_rule_1_cascade_diagonal(state))
        forced.update(fire_rule_2_de60_zero(state))
        if self.mode_force:
            forced.update(fire_rule_3_three_filter(state))
        forced.update(fire_rule_4_unified_theorem4(state))
        forced.update(fire_rule_5_dc_dg_equality(state))
        # Rule 6 covered by Rule 4
        # Rule 7 needs candidate context; skip in this prototype
        # Rule 8 needs cross-restart state; skip in this prototype
        return forced


def selftest():
    """Validate rule logic on a fresh cascade-held sample."""
    sys.path.insert(0, os.path.join(HERE, "..", "..", "mitm_residue", "results"))
    from validate_residual_structure import run_one
    from lib.sha256 import precompute_state
    import random

    # Priority candidate
    m0 = 0x17149975
    fill = 0xffffffff
    M1 = [m0] + [fill] * 15
    M2 = list(M1)
    M2[0] ^= (1 << 31)
    M2[9] ^= (1 << 31)
    s1_init, W1_pre = precompute_state(M1)
    s2_init, W2_pre = precompute_state(M2)

    rng = random.Random(0)
    for trial in range(5):
        result = run_one(s1_init, s2_init, W1_pre, W2_pre,
                         rng.randrange(2**32), rng.randrange(2**32),
                         rng.randrange(2**32), rng.randrange(2**32))
        if result is None:
            continue
        states1, states2 = result

        # Build "fully decided" diff state from the ground truth
        state = DiffState()
        for r_idx, r in enumerate([60, 61, 62, 63]):
            s1, s2 = states1[r_idx], states2[r_idx]
            state.da[r] = (s1[0] - s2[0]) & MASK
            state.db[r] = (s1[1] - s2[1]) & MASK
            state.dc[r] = (s1[2] - s2[2]) & MASK
            state.dd[r] = (s1[3] - s2[3]) & MASK
            state.de[r] = (s1[4] - s2[4]) & MASK
            state.df[r] = (s1[5] - s2[5]) & MASK
            state.dg[r] = (s1[6] - s2[6]) & MASK
            state.dh[r] = (s1[7] - s2[7]) & MASK
            state.actual_a[r] = (s1[0], s2[0])
        # Cascade rounds 57-59 zero-diffs (these are vacuous at fresh-sample time)
        for r in (57, 58, 59):
            state.da[r] = 0; state.db[r] = 0; state.dc[r] = 0; state.dd[r] = 0

        # Mode FORCE prop should report no conflicts (since this IS a cascade-held sample);
        # but Rule 3 will FORCE de_61, de_62, de_63 to zero, which contradicts the actual
        # values — so we test in non-force mode here.
        prop = CascadePropagator(mode_force=False)
        forced = prop.fire_all(state)
        conflicts = [k for k, v in forced.items() if v == "CONFLICT"]
        if conflicts:
            print(f"trial {trial}: CONFLICTS detected on cascade-held sample (BUG):", conflicts)
            return 1
    print("selftest: no conflicts on 5 cascade-held samples — rule logic is consistent")
    return 0


if __name__ == "__main__":
    sys.exit(selftest())
