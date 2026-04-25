#!/usr/bin/env python3
"""
varmap_loader.py — Load a cascade_aux_encoder varmap sidecar and provide
forward and reverse lookup between SAT variable IDs and (register, round, bit)
coordinates.

Schema (from cascade_aux_encoder.py write_varmap_sidecar):

  {
    "version": 1,
    "summary": {sr, m0, fill, kernel_bit, mode, total_vars, ...},
    "aux_reg": {
      "<reg>_<round>": [32 ints],   # e.g. "a_61" -> [v0, v1, ..., v31]
    },
    "aux_W": {
      "<round>": [32 ints]          # e.g. "57" -> [...]
    }
  }

  Literal convention:
    - positive int = SAT variable ID
    - negative int = negated literal (signed convention)
    - 1  = constant TRUE
    - -1 = constant FALSE

  For propagator integration, we typically want POSITIVE-VAR semantics:
  if the literal is negative, the SAT variable's TRUE value corresponds
  to the differential bit being FALSE (and vice versa).

Usage:

    from varmap_loader import VarMap
    vm = VarMap.load("aux_force_sr60_n32_bit31.cnf.varmap.json")

    # Forward: get the literal for a specific differential bit
    lit = vm.diff_lit("a", 61, 0)  # dA[61][0] -> e.g. +5318
    # If lit > 1: SAT var lit, positive polarity
    # If lit < -1: SAT var |lit|, negated polarity
    # If lit == 1: bit is constant TRUE (always 1)
    # If lit == -1: bit is constant FALSE (always 0)

    # Reverse: SAT var ID -> ((reg, round, bit), polarity)
    info = vm.lookup_var(5318)   # returns ('a', 61, 0, +1) or None
"""
import json
from collections import namedtuple


VarBit = namedtuple("VarBit", ["reg", "round", "bit", "polarity"])


class VarMap:
    """Bidirectional map between SAT vars and differential bits."""

    def __init__(self, summary, aux_reg, aux_W):
        self.summary = summary
        self.aux_reg = aux_reg     # (reg, round) -> [32 lits]
        self.aux_W = aux_W         # round -> [32 lits]
        self._reverse = {}         # |var_id| -> [(reg, round, bit, polarity)]
        self._build_reverse()

    @classmethod
    def load(cls, path):
        with open(path) as f:
            data = json.load(f)
        if data.get("version") != 1:
            raise ValueError(f"Unknown varmap version: {data.get('version')}")
        aux_reg = {}
        for k, v in data["aux_reg"].items():
            reg, r = k.rsplit("_", 1)
            aux_reg[(reg, int(r))] = v
        aux_W = {int(r): v for r, v in data["aux_W"].items()}
        return cls(data["summary"], aux_reg, aux_W)

    def _build_reverse(self):
        for (reg, r), lits in self.aux_reg.items():
            for bit, lit in enumerate(lits):
                if abs(lit) <= 1:
                    continue
                var = abs(lit)
                pol = +1 if lit > 0 else -1
                self._reverse.setdefault(var, []).append(
                    VarBit(reg, r, bit, pol)
                )
        for r, lits in self.aux_W.items():
            for bit, lit in enumerate(lits):
                if abs(lit) <= 1:
                    continue
                var = abs(lit)
                pol = +1 if lit > 0 else -1
                self._reverse.setdefault(var, []).append(
                    VarBit("W", r, bit, pol)
                )

    def diff_lit(self, reg, round_, bit):
        """Return the literal for dX[round][bit] where X = reg in 'abcdefgh'.

        +1 = constant TRUE, -1 = constant FALSE, otherwise SAT-var literal.
        """
        return self.aux_reg[(reg, round_)][bit]

    def w_lit(self, round_, bit):
        """Return the literal for dW[round][bit]."""
        return self.aux_W[round_][bit]

    def lookup_var(self, var_id):
        """SAT var ID -> list of (reg, round, bit, polarity).
        A var may be aliased to multiple bits if XOR canonicalization shared it.
        Returns empty list for non-aux SAT vars (W bits, register bits, etc.
        from the underlying SHA-256 encoding).
        """
        return list(self._reverse.get(abs(var_id), []))

    def is_constant(self, reg, round_, bit):
        """True if dX[round][bit] is constant-folded by the encoder."""
        lit = self.diff_lit(reg, round_, bit)
        return abs(lit) == 1

    def is_const_true(self, reg, round_, bit):
        return self.diff_lit(reg, round_, bit) == 1

    def is_const_false(self, reg, round_, bit):
        return self.diff_lit(reg, round_, bit) == -1

    def list_diff_vars(self, reg, round_):
        """Return list of (bit, var_id, polarity) for non-constant bits."""
        out = []
        for bit, lit in enumerate(self.aux_reg[(reg, round_)]):
            if abs(lit) > 1:
                out.append((bit, abs(lit), +1 if lit > 0 else -1))
        return out


def selftest():
    """Verify load + roundtrip on a small generated varmap."""
    import os, sys, tempfile
    HERE = os.path.dirname(os.path.abspath(__file__))
    encoder = os.path.join(HERE, "..", "..", "cascade_aux_encoding", "encoders", "cascade_aux_encoder.py")
    if not os.path.exists(encoder):
        print(f"SKIP: encoder not found at {encoder}")
        return 0

    tmp = tempfile.mkdtemp()
    cnf = os.path.join(tmp, "aux_force_sr60_n32_test.cnf")
    varmap = cnf + ".varmap.json"
    rc = os.system(
        f"python3 {encoder} --sr 60 --m0 0x17149975 --fill 0xffffffff "
        f"--kernel-bit 31 --mode force --out {cnf} --varmap + --quiet"
    )
    if rc != 0:
        print("FAIL: encoder run failed")
        return 1

    vm = VarMap.load(varmap)
    print(f"loaded varmap: {len(vm.aux_reg)} (reg,round) entries, "
          f"{len(vm.aux_W)} W-rounds, {len(vm._reverse)} unique SAT vars")
    print(f"  summary.mode = {vm.summary['mode']}")
    print(f"  summary.total_vars = {vm.summary['total_vars']}")

    # Roundtrip: pick a non-constant bit, verify forward + reverse agree.
    for r in (61, 62, 63):
        for reg in "abefg":
            for bit in range(32):
                lit = vm.diff_lit(reg, r, bit)
                if abs(lit) > 1:
                    var = abs(lit)
                    info = vm.lookup_var(var)
                    found = any(v.reg == reg and v.round == r and v.bit == bit
                                for v in info)
                    if not found:
                        print(f"FAIL: roundtrip {reg}_{r}_{bit} (var {var}) -> {info}")
                        return 1

    # Cascade-zero sanity at sr=60 force mode: dA[57] should be const-FALSE
    # WAIT — actually in force mode the dA[57]=0 is enforced via UNIT clauses
    # on the SAT var, not by the var literal becoming -1. The aux_reg literal
    # remains a SAT var; the force-clauses make it always-false at solve time.
    # So is_const_false will return False here. That's correct semantics.
    a57_lit = vm.diff_lit("a", 57, 0)
    print(f"  dA[57][0] literal = {a57_lit} (force-mode unit clauses force it)")

    # Find a constant-folded bit (these come from encoder's constant propagation)
    n_const = sum(1 for (reg, r), lits in vm.aux_reg.items()
                  for lit in lits if abs(lit) == 1)
    print(f"  {n_const} bits constant-folded by encoder")

    print("selftest: PASS")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(selftest())
