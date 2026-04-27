#!/usr/bin/env python3
"""
validate_trail_bundle.py — schema validator for 2blockcertpin/v1 trail bundles.

Checks a JSON trail bundle against the v1 schema (per
trails/2BLOCK_CERTPIN_SPEC.md). Exit 0 if valid, 1 if invalid, with
human-readable error messages.

Used by:
- yale: validate trail bundle drafts before shipping
- macbook: validate incoming bundles before invoking build_2block_certpin.py
- CI / pre-commit (when wired up)

Usage:
    python3 validate_trail_bundle.py path/to/trail_bundle.json
    python3 validate_trail_bundle.py --quiet bundle.json   # exit code only
"""

import argparse
import json
import re
import sys


SCHEMA_VERSION = "2blockcertpin/v1"

HEX32 = re.compile(r"^0x[0-9a-fA-F]{1,8}$")
HEX_NONNEG = re.compile(r"^0x[0-9a-fA-F]+$")


def err(errors, path, msg):
    errors.append(f"  {path}: {msg}")


def is_hex32(val):
    return isinstance(val, str) and HEX32.match(val) is not None


def validate_block1(b1, errors):
    p = "block1"
    for k in ("m0", "fill", "kernel_bit", "W1_57_60",
              "residual_state_diff"):
        if k not in b1:
            err(errors, p, f"missing required field '{k}'")

    if "m0" in b1 and not is_hex32(b1["m0"]):
        err(errors, p + ".m0", f"expected 32-bit hex, got {b1['m0']!r}")
    if "fill" in b1 and not is_hex32(b1["fill"]):
        err(errors, p + ".fill", f"expected 32-bit hex, got {b1['fill']!r}")
    if "kernel_bit" in b1:
        kb = b1["kernel_bit"]
        if not isinstance(kb, int) or not (0 <= kb <= 31):
            err(errors, p + ".kernel_bit", f"expected int in [0,31], got {kb!r}")
    if "W1_57_60" in b1:
        ws = b1["W1_57_60"]
        if not isinstance(ws, list) or len(ws) != 4:
            err(errors, p + ".W1_57_60", f"expected list of 4 hex strings, got {ws!r}")
        else:
            for i, w in enumerate(ws):
                if not is_hex32(w):
                    err(errors, p + f".W1_57_60[{i}]", f"expected 32-bit hex, got {w!r}")
    if "residual_state_diff" in b1:
        rsd = b1["residual_state_diff"]
        if not isinstance(rsd, dict):
            err(errors, p + ".residual_state_diff", "expected object")
        else:
            for reg in ("a", "b", "c", "d", "e", "f", "g", "h"):
                key = f"d{reg}63"
                if key not in rsd:
                    err(errors, p + ".residual_state_diff", f"missing '{key}'")
                elif not is_hex32(rsd[key]):
                    err(errors, p + f".residual_state_diff.{key}",
                        f"expected 32-bit hex, got {rsd[key]!r}")


VALID_CONSTRAINT_TYPES = {"exact", "exact_diff", "modular_relation", "bit_condition"}


def validate_block2(b2, errors):
    p = "block2"
    for k in ("W2_constraints", "target_diff_at_round_N"):
        if k not in b2:
            err(errors, p, f"missing required field '{k}'")

    if "W2_constraints" in b2:
        cs = b2["W2_constraints"]
        if not isinstance(cs, list):
            err(errors, p + ".W2_constraints", "expected list")
        else:
            for i, c in enumerate(cs):
                cp = p + f".W2_constraints[{i}]"
                if not isinstance(c, dict):
                    err(errors, cp, "expected object")
                    continue
                if "type" not in c:
                    err(errors, cp, "missing 'type'")
                elif c["type"] not in VALID_CONSTRAINT_TYPES:
                    err(errors, cp + ".type",
                        f"expected one of {sorted(VALID_CONSTRAINT_TYPES)}, got {c['type']!r}")
                if "round" not in c:
                    err(errors, cp, "missing 'round'")
                elif not isinstance(c["round"], int) or not (0 <= c["round"] <= 63):
                    err(errors, cp + ".round",
                        f"expected int in [0,63], got {c.get('round')!r}")
                t = c.get("type")
                if t == "exact" and not is_hex32(c.get("value", "")):
                    err(errors, cp + ".value", "exact constraint requires 32-bit hex 'value'")
                if t == "exact_diff" and not is_hex32(c.get("diff", "")):
                    err(errors, cp + ".diff", "exact_diff constraint requires 32-bit hex 'diff'")
                if t == "modular_relation" and not isinstance(c.get("constraint"), str):
                    err(errors, cp + ".constraint",
                        "modular_relation requires string 'constraint'")
                if t == "bit_condition" and "condition" not in c:
                    err(errors, cp + ".condition", "bit_condition requires 'condition' field")

    if "target_diff_at_round_N" in b2:
        td = b2["target_diff_at_round_N"]
        if not isinstance(td, dict):
            err(errors, p + ".target_diff_at_round_N", "expected object")
        else:
            if "round" not in td:
                err(errors, p + ".target_diff_at_round_N", "missing 'round'")
            elif not isinstance(td["round"], int) or not (0 <= td["round"] <= 63):
                err(errors, p + ".target_diff_at_round_N.round",
                    f"expected int in [0,63], got {td.get('round')!r}")
            for reg in ("a", "b", "c", "d", "e", "f", "g", "h"):
                key = f"diff_{reg}"
                if key not in td:
                    err(errors, p + ".target_diff_at_round_N",
                        f"missing '{key}' (collision target needs all 8 register diffs)")
                elif not is_hex32(td[key]):
                    err(errors, p + f".target_diff_at_round_N.{key}",
                        f"expected 32-bit hex, got {td[key]!r}")


def validate_bundle(bundle):
    """Returns list of error strings; empty list = valid."""
    errors = []

    if not isinstance(bundle, dict):
        return ["root: expected JSON object"]

    sv = bundle.get("schema_version")
    if sv != SCHEMA_VERSION:
        errors.append(f"  root.schema_version: expected {SCHEMA_VERSION!r}, got {sv!r}")

    for k in ("cand_id", "witness_id", "block1", "block2"):
        if k not in bundle:
            errors.append(f"  root: missing required field '{k}'")

    if "block1" in bundle and isinstance(bundle["block1"], dict):
        validate_block1(bundle["block1"], errors)
    if "block2" in bundle and isinstance(bundle["block2"], dict):
        validate_block2(bundle["block2"], errors)

    return errors


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("bundle", help="Path to trail bundle JSON")
    ap.add_argument("--quiet", action="store_true",
                    help="Suppress output; exit code only")
    args = ap.parse_args()

    try:
        with open(args.bundle) as f:
            bundle = json.load(f)
    except FileNotFoundError:
        if not args.quiet:
            print(f"ERROR: file not found: {args.bundle}", file=sys.stderr)
        sys.exit(2)
    except json.JSONDecodeError as e:
        if not args.quiet:
            print(f"ERROR: invalid JSON in {args.bundle}: {e}", file=sys.stderr)
        sys.exit(2)

    errors = validate_bundle(bundle)

    if errors:
        if not args.quiet:
            print(f"INVALID: {args.bundle}", file=sys.stderr)
            print(f"  {len(errors)} error(s):", file=sys.stderr)
            for e in errors:
                print(e, file=sys.stderr)
        sys.exit(1)

    if not args.quiet:
        cand = bundle.get("cand_id", "?")
        wit = bundle.get("witness_id", "?")
        n_constraints = len(bundle.get("block2", {}).get("W2_constraints", []))
        print(f"VALID: {args.bundle}")
        print(f"  schema:     {bundle.get('schema_version')}")
        print(f"  cand:       {cand}")
        print(f"  witness:    {wit}")
        print(f"  block-2 W2 constraints: {n_constraints}")
    sys.exit(0)


if __name__ == "__main__":
    main()
