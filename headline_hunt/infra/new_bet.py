#!/usr/bin/env python3
"""
new_bet.py — Scaffold a new bet directory.

Usage: python3 new_bet.py <bet_id>

Creates:
  bets/<bet_id>/{BET.yaml, README.md, kill_criteria.md, results/}

Adds a stub entry to registry/mechanisms.yaml (if not already present).

Edit the resulting files before committing — these are scaffolds, not finished bets.
"""
import argparse
import datetime
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
HUNT_ROOT = os.path.dirname(HERE)
BETS_DIR = os.path.join(HUNT_ROOT, "bets")
MECHANISMS_PATH = os.path.join(HUNT_ROOT, "registry", "mechanisms.yaml")


BET_YAML_TEMPLATE = """\
mechanism_id: {mechanism_id}
priority: null
status: open
owner: unassigned
machines_assigned: []
compute_budget_cpu_hours: null
current_progress: |
  TODO: describe what's built and what's next.
last_heartbeat: "{today}T00:00:00Z"
heartbeat_interval_days: 7
"""

README_TEMPLATE = """\
# bet: {bet_id}

## The bet

TODO: one paragraph — what is the testable claim?

## Hypothesis

TODO: structural argument for why this might work.

## Headline if it works

TODO: what could be said publicly if this succeeds.

## What's built / TODO

- [ ] TODO

## How to join

1. Set `{mechanism_id}.owner` in `../../registry/mechanisms.yaml`.
2. Update `BET.yaml` `owner` and `machines_assigned`.
3. Read `kill_criteria.md` first.

## Related

- TODO: adjacencies and dependencies.
"""

KILL_TEMPLATE = """\
# Kill criteria — {bet_id}

## #1 — TODO

**Trigger**: TODO

**Required evidence**: TODO

## Reopen triggers

- TODO
"""

MECHANISM_STUB = """\

- id: {mechanism_id}
  name: "TODO: human-readable name"
  headline_if_success: "TODO"
  hypothesis: "TODO"
  structural_basis:
    - "TODO"
  status: open
  priority: null
  expected_info_per_cpu_hour: unknown
  dependencies:
    - "TODO"
  next_action: "TODO"
  kill_criteria:
    - "TODO"
  reopen_criteria:
    - "TODO"
  evidence: []
  owner: unassigned
  last_updated: "{today}"
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bet_id", help="Short ID for the bet directory and mechanism")
    args = ap.parse_args()

    bet_id = args.bet_id
    if not bet_id.replace("_", "").isalnum():
        print("ERROR: bet_id must be alphanumeric + underscores", file=sys.stderr)
        sys.exit(2)

    bet_dir = os.path.join(BETS_DIR, bet_id)
    if os.path.exists(bet_dir):
        print(f"ERROR: {bet_dir} already exists", file=sys.stderr)
        sys.exit(2)

    today = datetime.date.today().isoformat()
    mechanism_id = bet_id  # same id by convention

    os.makedirs(os.path.join(bet_dir, "results"))

    with open(os.path.join(bet_dir, "BET.yaml"), "w") as f:
        f.write(BET_YAML_TEMPLATE.format(mechanism_id=mechanism_id, today=today))
    with open(os.path.join(bet_dir, "README.md"), "w") as f:
        f.write(README_TEMPLATE.format(bet_id=bet_id, mechanism_id=mechanism_id))
    with open(os.path.join(bet_dir, "kill_criteria.md"), "w") as f:
        f.write(KILL_TEMPLATE.format(bet_id=bet_id))

    # Append stub mechanism if not present
    if os.path.exists(MECHANISMS_PATH):
        with open(MECHANISMS_PATH) as f:
            content = f.read()
        if f"id: {mechanism_id}" not in content:
            with open(MECHANISMS_PATH, "a") as f:
                f.write(MECHANISM_STUB.format(mechanism_id=mechanism_id, today=today))
            print(f"Appended mechanism stub to {MECHANISMS_PATH}")

    print(f"Created {bet_dir}")
    print("Edit BET.yaml, README.md, kill_criteria.md, and the mechanism entry before committing.")


if __name__ == "__main__":
    main()
