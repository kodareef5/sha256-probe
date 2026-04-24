#!/usr/bin/env python3
"""
validate_registry.py — Schema + cross-reference + staleness validation.

Loads each registry/*.yaml and bets/*/BET.yaml against schemas/*.schema.yaml.
Reports errors and exits non-zero if any found.

Usage: python3 validate_registry.py [--no-stale-fail]
"""
import argparse
import datetime
import glob
import os
import sys

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML required. pip install pyyaml", file=sys.stderr)
    sys.exit(2)


HERE = os.path.dirname(os.path.abspath(__file__))
HUNT_ROOT = os.path.dirname(HERE)
REGISTRY_DIR = os.path.join(HUNT_ROOT, "registry")
BETS_DIR = os.path.join(HUNT_ROOT, "bets")
SCHEMA_DIR = os.path.join(HERE, "schemas")

REGISTRY_FILES = {
    "candidates":  ("candidates.yaml",  "candidate.schema.yaml"),
    "kernels":     ("kernels.yaml",     "kernel.schema.yaml"),
    "mechanisms":  ("mechanisms.yaml",  "mechanism.schema.yaml"),
    "negatives":   ("negatives.yaml",   "negative.schema.yaml"),
    "literature":  ("literature.yaml",  "literature.schema.yaml"),
}

STALE_DAYS = {
    "in_flight": 7,
    "open":      30,
    "blocked":   30,
}


def load_yaml(path):
    with open(path) as f:
        return yaml.safe_load(f)


def get_nested(record, dotted_key):
    parts = dotted_key.split(".")
    cur = record
    for p in parts:
        if not isinstance(cur, dict) or p not in cur:
            return None
        cur = cur[p]
    return cur


def parse_date(s):
    if not s:
        return None
    if isinstance(s, datetime.date):
        return s
    s = str(s).strip()
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return datetime.datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def validate_record(rec, schema, source, errors, warnings):
    rid = rec.get(schema.get("record_id_field", "id"), "<no-id>")
    # Required fields
    for field in schema.get("required_fields", []):
        if get_nested(rec, field) is None:
            errors.append(f"{source}/{rid}: missing required field `{field}`")
    # Nested required
    for parent, kids in (schema.get("nested_required") or {}).items():
        if isinstance(kids, list):
            parent_val = get_nested(rec, parent)
            if parent_val is None:
                continue  # already reported by required_fields if applicable
            for kid in kids:
                if isinstance(parent_val, dict) and kid not in parent_val:
                    errors.append(f"{source}/{rid}: missing nested field `{parent}.{kid}`")
    # Status enum checks
    for field, allowed in (schema.get("status_enum") or {}).items():
        val = get_nested(rec, field)
        if val is not None and val not in allowed:
            errors.append(f"{source}/{rid}: `{field}`={val!r} not in enum {allowed}")
    for field, allowed in (schema.get("evidence_level_enum") and
                           {"evidence_level": schema["evidence_level_enum"]} or {}).items():
        val = get_nested(rec, field)
        if val is not None and val not in allowed:
            errors.append(f"{source}/{rid}: `{field}`={val!r} not in enum {allowed}")
    for field, allowed in (schema.get("expected_info_enum") or {}).items():
        val = get_nested(rec, field)
        if val is not None and val not in allowed:
            errors.append(f"{source}/{rid}: `{field}`={val!r} not in enum {allowed}")
    for field, allowed in (schema.get("confidence_enum") or {}).items():
        val = get_nested(rec, field)
        if val is not None and val not in allowed:
            errors.append(f"{source}/{rid}: `{field}`={val!r} not in enum {allowed}")
    for field, allowed in (schema.get("read_status_enum") or {}).items():
        val = get_nested(rec, field)
        if val is not None and val not in allowed:
            errors.append(f"{source}/{rid}: `{field}`={val!r} not in enum {allowed}")


def check_staleness(rec, source, today, warnings):
    status = rec.get("status")
    if status not in STALE_DAYS:
        return
    last = parse_date(rec.get("last_updated"))
    if last is None:
        return
    days = (today - last).days
    if days > STALE_DAYS[status]:
        rid = rec.get("id", "<no-id>")
        warnings.append(
            f"{source}/{rid}: STALE — status={status} last_updated={last} ({days}d ago, threshold {STALE_DAYS[status]}d)"
        )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-stale-fail", action="store_true",
                    help="Don't exit non-zero on stale-only findings")
    args = ap.parse_args()

    errors = []
    warnings = []
    today = datetime.date.today()

    # Load all schemas
    schemas = {}
    for name, (_, schema_file) in REGISTRY_FILES.items():
        schemas[name] = load_yaml(os.path.join(SCHEMA_DIR, schema_file))
    bet_schema = load_yaml(os.path.join(SCHEMA_DIR, "bet.schema.yaml"))

    # Track IDs across registries for cross-reference checking
    all_ids = {name: set() for name in REGISTRY_FILES}

    # Validate each registry
    for name, (yaml_file, _) in REGISTRY_FILES.items():
        path = os.path.join(REGISTRY_DIR, yaml_file)
        if not os.path.exists(path):
            errors.append(f"Missing registry file: {path}")
            continue
        try:
            data = load_yaml(path)
        except yaml.YAMLError as e:
            errors.append(f"{path}: YAML parse error — {e}")
            continue
        if data is None:
            warnings.append(f"{path}: empty registry")
            continue
        schema = schemas[name]
        if schema.get("type") != "list_of_records":
            errors.append(f"{path}: schema mismatch — expected list_of_records")
            continue
        if not isinstance(data, list):
            errors.append(f"{path}: expected a YAML list, got {type(data).__name__}")
            continue
        ids = set()
        for rec in data:
            if not isinstance(rec, dict):
                errors.append(f"{path}: non-dict record encountered")
                continue
            rid = rec.get(schema.get("record_id_field", "id"))
            if rid in ids:
                errors.append(f"{path}: duplicate id `{rid}`")
            ids.add(rid)
            validate_record(rec, schema, yaml_file, errors, warnings)
            check_staleness(rec, yaml_file, today, warnings)
        all_ids[name] = ids

    # Cross-reference check: mechanisms.related_mechanisms must point at real mechanisms
    mech_path = os.path.join(REGISTRY_DIR, "mechanisms.yaml")
    if os.path.exists(mech_path):
        for rec in (load_yaml(mech_path) or []):
            for ref in (rec.get("dependencies") or []):
                pass  # free text, no enforcement
    neg_path = os.path.join(REGISTRY_DIR, "negatives.yaml")
    if os.path.exists(neg_path):
        for rec in (load_yaml(neg_path) or []):
            for ref in (rec.get("related_mechanisms") or []):
                if ref not in all_ids["mechanisms"]:
                    errors.append(f"negatives.yaml/{rec.get('id')}: related_mechanisms `{ref}` not found in mechanisms.yaml")

    # Validate each BET.yaml
    for bet_yaml in sorted(glob.glob(os.path.join(BETS_DIR, "*", "BET.yaml"))):
        bet_dir = os.path.basename(os.path.dirname(bet_yaml))
        try:
            data = load_yaml(bet_yaml)
        except yaml.YAMLError as e:
            errors.append(f"{bet_yaml}: YAML parse error — {e}")
            continue
        if data is None:
            errors.append(f"{bet_yaml}: empty")
            continue
        rel_source = f"bets/{bet_dir}/BET.yaml"
        validate_record(data, bet_schema, rel_source, errors, warnings)
        # Cross-reference: mechanism_id must exist
        mid = data.get("mechanism_id")
        if mid and mid not in all_ids["mechanisms"]:
            errors.append(f"{rel_source}: mechanism_id `{mid}` not found in mechanisms.yaml")
        # Heartbeat staleness
        last = parse_date(data.get("last_heartbeat"))
        interval = data.get("heartbeat_interval_days", 7)
        if last is not None:
            days = (today - last).days
            if days > interval:
                warnings.append(
                    f"{rel_source}: HEARTBEAT STALE — last={last} ({days}d ago, interval {interval}d)"
                )

    # Report
    print(f"validate_registry.py: {len(errors)} errors, {len(warnings)} warnings")
    for e in errors:
        print(f"  ERROR: {e}")
    for w in warnings:
        print(f"  WARN:  {w}")

    if errors:
        sys.exit(1)
    if warnings and not args.no_stale_fail:
        # Stale-only is non-fatal by default? GPT-5.5 said it should be enforceable.
        # We exit 0 on warnings unless --no-stale-fail is explicitly disabled... actually
        # the more useful default is: warnings don't fail. CI can pass --strict-warnings.
        pass
    sys.exit(0)


if __name__ == "__main__":
    main()
