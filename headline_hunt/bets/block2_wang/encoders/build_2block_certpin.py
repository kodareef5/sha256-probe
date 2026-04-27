#!/usr/bin/env python3
"""
build_2block_certpin.py — verify a 2blockcertpin/v1 trail bundle.

Loads a trail bundle JSON (per
headline_hunt/bets/block2_wang/trails/2BLOCK_CERTPIN_SPEC.md),
validates it against the v1 schema, then attempts to build the
corresponding 2-block CNF and run a SAT solver on it.

Current state (2026-04-27, F84):
  TRIVIAL CASE (block2.W2_constraints empty + block1.residual = zero):
    Delegates to the existing single-block cert-pin pipeline
    (certpin_verify.py). Returns SAT for known single-block collisions.
  NON-TRIVIAL CASE (any non-empty W2_constraints or non-zero residual):
    Errors out with NotImplementedError. Encoder extension is the next
    macbook task — see SPEC's "Encoder gap to close" section.

This staged delivery means:
  - The end-to-end pipeline (bundle → validator → CNF → solver → verdict)
    is provably wired up TODAY for the m17149975 trivial round-trip case.
  - Yale can ship draft trail bundles and immediately get either a SAT
    verdict (trivial) or a precise NotImplementedError pointing to the
    missing encoder feature (non-trivial).
  - When the encoder extension lands, only the non-trivial branch needs
    to be filled in; the rest of the plumbing is already validated.

Usage:
    python3 build_2block_certpin.py <trail_bundle.json>
    python3 build_2block_certpin.py --solver all <trail_bundle.json>
"""
import argparse
import json
import os
import subprocess
import sys


HERE = os.path.dirname(os.path.abspath(__file__))
TRAILS_DIR = os.path.join(HERE, "..", "trails")
VALIDATOR = os.path.join(TRAILS_DIR, "validate_trail_bundle.py")
CASCADE_AUX_DIR = os.path.join(HERE, "..", "..", "cascade_aux_encoding", "encoders")
CERTPIN_VERIFY = os.path.join(CASCADE_AUX_DIR, "certpin_verify.py")


def is_zero_hex(s):
    return isinstance(s, str) and int(s, 16) == 0


def is_trivial_residual(rsd):
    return all(is_zero_hex(rsd.get(f"d{r}63", "1")) for r in "abcdefgh")


def is_trivial_target(td):
    return all(is_zero_hex(td.get(f"diff_{r}", "1")) for r in "abcdefgh")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("bundle", help="Path to 2blockcertpin/v1 trail bundle JSON")
    ap.add_argument("--solver", default="kissat",
                    choices=["kissat", "cadical", "cms", "all"])
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--conflicts", type=int, default=10_000_000)
    args = ap.parse_args()

    # Step 1: schema validation
    r = subprocess.run(
        ["python3", VALIDATOR, args.bundle],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        print(f"BUNDLE INVALID — refusing to proceed.\n", file=sys.stderr)
        print(r.stdout, file=sys.stderr)
        print(r.stderr, file=sys.stderr)
        sys.exit(2)

    # Step 2: load and dispatch
    with open(args.bundle) as f:
        bundle = json.load(f)
    b1 = bundle["block1"]
    b2 = bundle["block2"]

    cand_id = bundle.get("cand_id", "?")
    witness_id = bundle.get("witness_id", "?")

    trivial_residual = is_trivial_residual(b1["residual_state_diff"])
    trivial_target = is_trivial_target(b2["target_diff_at_round_N"])
    no_w2_constraints = len(b2.get("W2_constraints", [])) == 0

    print(f"\n=== 2-block cert-pin verification ===")
    print(f"Bundle:     {args.bundle}")
    print(f"Cand:       {cand_id}")
    print(f"Witness:    {witness_id}")
    print(f"Block-1 residual: {'ZERO' if trivial_residual else 'NON-ZERO'}")
    print(f"Block-2 target:   {'ZERO' if trivial_target else 'NON-ZERO'}")
    print(f"Block-2 W2 constraints: {len(b2.get('W2_constraints', []))}")

    is_trivial = trivial_residual and trivial_target and no_w2_constraints

    if not is_trivial:
        print(f"\nNON-TRIVIAL bundle. Encoder extension required.", file=sys.stderr)
        print(f"  trivial_residual = {trivial_residual}", file=sys.stderr)
        print(f"  trivial_target   = {trivial_target}", file=sys.stderr)
        print(f"  no_w2_constraints = {no_w2_constraints}", file=sys.stderr)
        print(f"\nSee SPEC: headline_hunt/bets/block2_wang/trails/"
              f"2BLOCK_CERTPIN_SPEC.md", file=sys.stderr)
        print(f"Section: 'Encoder gap to close (macbook's TODO)'.",
              file=sys.stderr)
        print(f"\nThis branch will be implemented after cascade_aux_encoder.py "
              f"is extended to emit 2-block CNFs with chaining-state wiring.",
              file=sys.stderr)
        sys.exit(3)

    # TRIVIAL CASE: delegate to single-block cert-pin
    print(f"\nTRIVIAL CASE detected. Delegating to single-block cert-pin")
    print(f"(block-2 with zero input diff + zero target + no W2 "
          f"constraints is trivially SAT for any block-2 message;")
    print(f"  reduces to verifying block-1 alone is SAT).\n")

    w57, w58, w59, w60 = b1["W1_57_60"]
    cmd = [
        "python3", CERTPIN_VERIFY,
        "--cand-id", witness_id,
        "--m0", b1["m0"],
        "--fill", b1["fill"],
        "--kernel-bit", str(b1["kernel_bit"]),
        "--w57", w57, "--w58", w58, "--w59", w59, "--w60", w60,
        "--solver", args.solver,
        "--seed", str(args.seed),
        "--conflicts", str(args.conflicts),
    ]
    print("Invoking: " + " ".join(cmd[:3]) + " ... [truncated]")
    print()

    r2 = subprocess.run(cmd)
    sys.exit(r2.returncode)


if __name__ == "__main__":
    main()
