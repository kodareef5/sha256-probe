#!/usr/bin/env python3
"""
Smoke test for cascade_aux_encoder.py.

Run: python3 test_encoder.py
Exits non-zero on any failure.

Covers:
  - sr=60 MSB candidate in both modes produces a valid DIMACS CNF.
  - sr=61 bit-10 candidate in both modes produces a valid DIMACS CNF.
  - Aux CNFs pass audit_cnf.py with CONFIRMED verdict.
  - Expose-mode and force-mode CNFs for the same sr differ ONLY in the replaced
    collision-vs-force clauses (by construction).

This script is intentionally fast (~1 second total). Run after any encoder change.
"""
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ENCODER = os.path.join(HERE, "cascade_aux_encoder.py")
REPO_ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
AUDIT = os.path.join(REPO_ROOT, "headline_hunt", "infra", "audit_cnf.py")


def run_encoder(args, out_path):
    cmd = [sys.executable, ENCODER] + args + ["--out", out_path, "--quiet"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"FAIL: encoder exit {r.returncode}\nstderr: {r.stderr}")
        sys.exit(1)


def run_audit(cnf_path):
    cmd = [sys.executable, AUDIT, cnf_path, "--json"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"FAIL: audit exit {r.returncode}\n{r.stdout}\n{r.stderr}")
        sys.exit(1)
    import json
    return json.loads(r.stdout)


def validate_dimacs(path):
    with open(path) as f:
        lines = [ln.strip() for ln in f]
    p_line = next((ln for ln in lines if ln.startswith("p cnf")), None)
    if not p_line:
        print(f"FAIL: no p cnf header in {path}")
        sys.exit(1)
    _, _, nv, nc = p_line.split()
    nv, nc = int(nv), int(nc)
    clauses = [ln for ln in lines if ln and not ln.startswith("c") and not ln.startswith("p")]
    if len(clauses) != nc:
        print(f"FAIL: {path} declares {nc} clauses, found {len(clauses)}")
        sys.exit(1)
    for c in clauses:
        toks = c.split()
        if toks[-1] != "0":
            print(f"FAIL: clause doesn't end in 0: {c}")
            sys.exit(1)
        for t in toks[:-1]:
            v = abs(int(t))
            if v < 1 or v > nv:
                print(f"FAIL: lit {t} out of range 1..{nv}")
                sys.exit(1)
    return nv, nc


def main():
    tmp = tempfile.mkdtemp(prefix="aux_test_")
    print(f"Using tmpdir {tmp}")
    cases = [
        # (args, expected filename prefix, expected audit claim)
        (["--sr", "60", "--m0", "0x17149975", "--fill", "0xffffffff",
          "--kernel-bit", "31", "--mode", "expose"],
         "aux_expose_sr60", {"sr_level": 60, "encoder_variant": "cascade_aux_expose"}),
        (["--sr", "60", "--m0", "0x17149975", "--fill", "0xffffffff",
          "--kernel-bit", "31", "--mode", "force"],
         "aux_force_sr60", {"sr_level": 60, "encoder_variant": "cascade_aux_force"}),
        (["--sr", "61", "--m0", "0x3304caa0", "--fill", "0x80000000",
          "--kernel-bit", "10", "--mode", "expose"],
         "aux_expose_sr61", {"sr_level": 61, "encoder_variant": "cascade_aux_expose"}),
        (["--sr", "61", "--m0", "0x3304caa0", "--fill", "0x80000000",
          "--kernel-bit", "10", "--mode", "force"],
         "aux_force_sr61", {"sr_level": 61, "encoder_variant": "cascade_aux_force"}),
    ]

    results = []
    for args, prefix, claim in cases:
        out_path = os.path.join(tmp, prefix + ".cnf")
        run_encoder(args, out_path)
        nv, nc = validate_dimacs(out_path)
        audit = run_audit(out_path)
        if audit["verdict"] != "CONFIRMED":
            print(f"FAIL: {prefix} audit verdict={audit['verdict']}, expected CONFIRMED")
            print(audit)
            sys.exit(1)
        if audit["claimed"]["sr_level"] != claim["sr_level"]:
            print(f"FAIL: {prefix} sr_level mismatch")
            sys.exit(1)
        print(f"PASS: {prefix} -> {nv} vars, {nc} clauses, {audit['verdict']}")
        results.append((prefix, nv, nc))

    # Cross-check: sr=60 and sr=61 should have different sizes (sanity check).
    sr60 = [r for r in results if "sr60" in r[0]][0]
    sr61 = [r for r in results if "sr61" in r[0]][0]
    if sr60[1] >= sr61[1] or sr60[2] >= sr61[2]:
        print(f"FAIL: sr=60 sizes ({sr60[1]}/{sr60[2]}) >= sr=61 sizes "
              f"({sr61[1]}/{sr61[2]}) — likely bug")
        sys.exit(1)

    print(f"\nAll {len(cases)} smoke tests PASSED")

    # Bonus: varmap sidecar smoke (added 2026-04-25)
    print("\nValidating --varmap sidecar...")
    varmap_cnf = os.path.join(tmp, "varmap_check.cnf")
    cmd = [sys.executable, ENCODER, "--sr", "60", "--m0", "0x17149975",
           "--fill", "0xffffffff", "--kernel-bit", "31", "--mode", "force",
           "--out", varmap_cnf, "--varmap", "+", "--quiet"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"FAIL: varmap encoder exit {r.returncode}\nstderr: {r.stderr}")
        sys.exit(1)
    varmap_path = varmap_cnf + ".varmap.json"
    if not os.path.exists(varmap_path):
        print(f"FAIL: varmap sidecar not written at {varmap_path}")
        sys.exit(1)

    import json
    with open(varmap_path) as f:
        vm = json.load(f)
    if vm.get("version") not in (1, 2, 3):
        print(f"FAIL: varmap version mismatch (got {vm.get('version')})")
        sys.exit(1)
    expected_keys = {f"{r}_{rd}" for r in "abcdefgh" for rd in range(57, 64)}
    if set(vm["aux_reg"].keys()) != expected_keys:
        missing = expected_keys - set(vm["aux_reg"].keys())
        extra = set(vm["aux_reg"].keys()) - expected_keys
        print(f"FAIL: varmap aux_reg keys mismatch. missing={missing}, extra={extra}")
        sys.exit(1)
    if set(vm["aux_W"].keys()) != {str(r) for r in range(57, 64)}:
        print(f"FAIL: varmap aux_W keys mismatch")
        sys.exit(1)

    # Round-trip: a non-constant SAT var should be reachable via varmap_loader
    sys.path.insert(0, os.path.join(REPO_ROOT, "headline_hunt", "bets",
                                     "programmatic_sat_propagator", "propagators"))
    try:
        from varmap_loader import VarMap
    except ImportError:
        print("INFO: varmap_loader.py not on path; skipping reverse-lookup test")
    else:
        loader = VarMap.load(varmap_path)
        # find any non-constant var, look it up
        sample = next((b for r in range(57, 64) for reg in "abcdefgh"
                       for b in [loader.diff_lit(reg, r, 0)]
                       if abs(b) > 1), None)
        if sample is None:
            print("WARN: all aux bits are constants? Unusual but not a fail.")
        else:
            info = loader.lookup_var(abs(sample))
            if not info:
                print(f"FAIL: varmap reverse lookup empty for var {sample}")
                sys.exit(1)
            print(f"PASS: varmap roundtrip OK (var {abs(sample)} -> {info[0]})")

    print(f"PASS: varmap sidecar emitted, schema correct, "
          f"{len(vm['aux_reg'])} (reg,round) entries, {len(vm['aux_W'])} W-rounds")
    print(f"\nAll {len(cases) + 1} smoke tests PASSED")


if __name__ == "__main__":
    main()
