#!/usr/bin/env python3
"""
certpin_verify.py — one-line cert-pin verification utility.

Takes a (cand, W-witness) tuple, builds the cert-pin CNF, runs kissat,
and reports SAT (= verified collision) or UNSAT (= near-residual) with
wall time.

Used by the fleet to verify online-sampler findings end-to-end:
  yale's online sampler discovers (cand, W-witness)
  → certpin_verify.py runs in <5s
  → confirms whether it's a near-residual or full collision

Usage:
    python3 certpin_verify.py --m0 0xd1acca79 --fill 0xffffffff \\
        --kernel-bit 28 --w57 0xce9b8db6 --w58 0xb26e4c72 \\
        --w59 0xc904fbc4 --w60 0x73b182dd

Or batch mode:
    python3 certpin_verify.py --batch /path/to/witnesses.jsonl

JSONL format for batch:
    {"cand_id": "...", "m0": "0x...", "fill": "0x...", "kernel_bit": N,
     "w57": "0x...", "w58": "0x...", "w59": "0x...", "w60": "0x..."}
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
import time


HERE = os.path.dirname(os.path.abspath(__file__))
ENCODER = os.path.join(HERE, "cascade_aux_encoder.py")
PIN_BUILDER = os.path.join(HERE, "build_certpin.py")


def verify_one(m0, fill, kernel_bit, w57, w58, w59, w60, conflicts=10_000_000, seed=1, quiet=True):
    """Run cert-pin verification on a single (cand, W-witness) tuple.

    Returns dict with: status (SAT/UNSAT/UNKNOWN/ERROR), wall_sec, message.
    """
    with tempfile.TemporaryDirectory() as tmp:
        base_cnf = os.path.join(tmp, "base.cnf")
        varmap = os.path.join(tmp, "base.cnf.varmap.json")
        pinned_cnf = os.path.join(tmp, "pinned.cnf")

        # 1. Build base CNF + varmap
        try:
            subprocess.run([
                "python3", ENCODER,
                "--sr", "60", "--m0", m0, "--fill", fill,
                "--kernel-bit", str(kernel_bit),
                "--mode", "expose", "--quiet",
                "--out", base_cnf, "--varmap", "auto",
            ], check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            return {"status": "ERROR", "wall_sec": 0,
                    "message": f"encoder failed: {e.stderr.decode()[:200]}"}

        # 2. Build pinned CNF
        try:
            subprocess.run([
                "python3", PIN_BUILDER,
                "--base", base_cnf, "--varmap", varmap,
                "--w57", w57, "--w58", w58, "--w59", w59, "--w60", w60,
                "--out", pinned_cnf,
            ], check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            return {"status": "ERROR", "wall_sec": 0,
                    "message": f"pin builder failed: {e.stderr.decode()[:200]}"}

        # 3. Run kissat
        t0 = time.time()
        try:
            r = subprocess.run([
                "kissat", f"--conflicts={conflicts}", f"--seed={seed}", "-q",
                pinned_cnf,
            ], capture_output=True, timeout=600)
        except subprocess.TimeoutExpired:
            return {"status": "TIMEOUT", "wall_sec": time.time() - t0,
                    "message": "kissat timeout 600s"}
        wall = time.time() - t0

        out = r.stdout.decode()
        # Parse status line
        status = "UNKNOWN"
        for line in out.split("\n"):
            if line.startswith("s SATISFIABLE"):
                status = "SAT"
                break
            if line.startswith("s UNSATISFIABLE"):
                status = "UNSAT"
                break

        msg = "verified collision" if status == "SAT" else \
              "near-residual" if status == "UNSAT" else \
              f"unknown (kissat hit conflict cap or err)"

        return {"status": status, "wall_sec": round(wall, 3), "message": msg}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--m0")
    ap.add_argument("--fill")
    ap.add_argument("--kernel-bit", type=int)
    ap.add_argument("--w57")
    ap.add_argument("--w58")
    ap.add_argument("--w59")
    ap.add_argument("--w60")
    ap.add_argument("--cand-id", default="")
    ap.add_argument("--batch", help="JSONL file with multiple witnesses (each "
                                     "record needs cand_id, m0, fill, kernel_bit, w57..w60)")
    ap.add_argument("--conflicts", type=int, default=10_000_000)
    ap.add_argument("--seed", type=int, default=1)
    args = ap.parse_args()

    if args.batch:
        if not os.path.exists(args.batch):
            print(f"ERROR: batch file not found: {args.batch}", file=sys.stderr)
            sys.exit(1)
        n_sat = n_unsat = n_err = 0
        with open(args.batch) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                rec = json.loads(line)
                result = verify_one(
                    rec["m0"], rec["fill"], rec["kernel_bit"],
                    rec["w57"], rec["w58"], rec["w59"], rec["w60"],
                    conflicts=args.conflicts, seed=args.seed,
                )
                cid = rec.get("cand_id", "?")
                print(f"{cid:<50}  {result['status']:<8}  {result['wall_sec']:>8.3f}s  "
                      f"{result.get('hw', '?')}  {result['message']}")
                if result["status"] == "SAT": n_sat += 1
                elif result["status"] == "UNSAT": n_unsat += 1
                else: n_err += 1
        print(f"\nSummary: {n_sat} SAT (collisions!), {n_unsat} UNSAT (near-residuals), "
              f"{n_err} other")
        if n_sat > 0:
            print("⚠ HEADLINE-CLASS DISCOVERY: 1+ SAT result indicates a verified "
                  "collision certificate.")
        sys.exit(0)

    # Single-witness mode
    if not all([args.m0, args.fill, args.kernel_bit is not None,
                args.w57, args.w58, args.w59, args.w60]):
        print("ERROR: Single mode requires --m0 --fill --kernel-bit --w57 --w58 --w59 --w60",
              file=sys.stderr)
        ap.print_help()
        sys.exit(2)

    result = verify_one(
        args.m0, args.fill, args.kernel_bit,
        args.w57, args.w58, args.w59, args.w60,
        conflicts=args.conflicts, seed=args.seed,
    )

    cand = args.cand_id or f"m0={args.m0} fill={args.fill} bit={args.kernel_bit}"
    print(f"\n=== cert-pin verification ===")
    print(f"Cand:    {cand}")
    print(f"W-witness: W57={args.w57} W58={args.w58} W59={args.w59} W60={args.w60}")
    print(f"Status:  {result['status']}")
    print(f"Wall:    {result['wall_sec']}s")
    print(f"Verdict: {result['message']}")

    if result["status"] == "SAT":
        print("\n🎉 HEADLINE-CLASS DISCOVERY: verified collision certificate!")
        print("   This is a sr=60 cascade-1 SAT solution at the given W-witness.")
    elif result["status"] == "UNSAT":
        print("\nConfirmed near-residual. Wang-style block-2 absorption needed for "
              "full collision.")

    sys.exit(0 if result["status"] in ("SAT", "UNSAT") else 1)


if __name__ == "__main__":
    main()
