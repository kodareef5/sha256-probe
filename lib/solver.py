"""
SAT solver wrappers with consistent interface.

All solvers return (status, stdout) where status is one of:
  "SAT", "UNSAT", "TIMEOUT", "UNKNOWN", "MISSING"
"""

import subprocess
import os


def run_kissat(cnf_file, timeout=600, proof_file=None, seed=None):
    cmd = ["kissat", "-q"]
    if seed is not None:
        cmd.append(f"--seed={seed}")
    if proof_file:
        cmd.extend([cnf_file, proof_file])
    else:
        cmd.append(cnf_file)
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if r.returncode == 10:
            return "SAT", r.stdout
        elif r.returncode == 20:
            return "UNSAT", r.stdout
        return "UNKNOWN", r.stdout
    except subprocess.TimeoutExpired:
        return "TIMEOUT", None
    except FileNotFoundError:
        return "MISSING", None


def run_cadical(cnf_file, timeout=600, seed=None):
    cmd = ["cadical", "-q"]
    if seed is not None:
        cmd.append(f"--seed={seed}")
    cmd.append(cnf_file)
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if r.returncode == 10:
            return "SAT", r.stdout
        elif r.returncode == 20:
            return "UNSAT", r.stdout
        return "UNKNOWN", r.stdout
    except subprocess.TimeoutExpired:
        return "TIMEOUT", None
    except FileNotFoundError:
        return "MISSING", None


def run_cryptominisat(cnf_file, timeout=600, seed=None):
    cmd = ["cryptominisat5"]
    if seed is not None:
        cmd.append(f"--random={seed}")
    cmd.append(cnf_file)
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if r.returncode == 10:
            return "SAT", r.stdout
        elif r.returncode == 20:
            return "UNSAT", r.stdout
        return "UNKNOWN", r.stdout
    except subprocess.TimeoutExpired:
        return "TIMEOUT", None
    except FileNotFoundError:
        return "MISSING", None


def verify_drat(cnf_file, proof_file, timeout=300):
    """Verify a DRAT proof. Returns 'OK', 'FAIL', 'TIMEOUT', or 'MISSING'."""
    # Look for drat-trim in several locations
    candidates = [
        os.path.join(os.path.dirname(__file__), '..', 'infra', 'drat-trim', 'drat-trim'),
        os.path.join(os.path.dirname(__file__), '..', 'sha256_scripts', 'tools', 'drat-trim', 'drat-trim'),
    ]
    drat_bin = None
    for c in candidates:
        if os.path.exists(c):
            drat_bin = c
            break

    if drat_bin is None:
        return "MISSING"

    try:
        r = subprocess.run(
            [drat_bin, cnf_file, proof_file],
            capture_output=True, text=True, timeout=timeout)
        return "OK" if "VERIFIED" in r.stdout else "FAIL"
    except subprocess.TimeoutExpired:
        return "TIMEOUT"


def cross_validate(cnf_file, timeout=600, seed=None):
    """Run all available solvers and return dict of results."""
    results = {}
    results['kissat'] = run_kissat(cnf_file, timeout, seed=seed)[0]
    results['cadical'] = run_cadical(cnf_file, timeout, seed=seed)[0]
    results['cms'] = run_cryptominisat(cnf_file, timeout, seed=seed)[0]
    return results
