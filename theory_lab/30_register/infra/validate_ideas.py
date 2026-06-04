#!/usr/bin/env python3
"""Validate 30_register/ideas.yaml against the SCHEMA.md taxonomy.

Fails (exit 1) if any entry is missing a required axis, uses an out-of-vocab
value, has a duplicate id, or — the cardinal sin — lacks a non-empty
kill_criterion. Run before every commit.
"""
import os
import sys

try:
    import yaml
except ImportError:
    sys.exit("FATAL: PyYAML not installed. `pip3 install pyyaml` (or use the repo's env).")

HERE = os.path.dirname(os.path.abspath(__file__))
IDEAS = os.path.join(HERE, "..", "ideas.yaml")

LENS = {
    "algebraic-geometry", "commutative-algebra", "boolean-function",
    "automata-transducer", "coding-theory", "lattice", "number-theory-padic",
    "prob-combinatorics", "graph-spectral", "tensor-network",
    "knowledge-compilation", "proof-complexity", "communication-complexity",
    "statistical-physics", "differential-crypto", "information-theory",
    "dynamical-systems", "other",
}
LOCUS = {
    "message-schedule", "round-function", "carries", "differential-trail",
    "state-cross-section", "feed-forward", "whole-function",
}
MECHANISM = {
    "solve", "reduce", "lower-bound", "reframe", "bridge-scales",
    "structural-invariant", "count",
}
NOVELTY = {
    "repo-established", "repo-killed", "flagged-unpursued",
    "adjacent-untested", "genuinely-new",
}
PROBE_COST = {"trivial", "cheap", "moderate", "heavy"}
STATUS = {
    "captured", "triaged", "deep-dive", "probe-designed", "probed",
    "promoted", "archived",
}
REQUIRED = [
    "id", "title", "one_liner", "lens", "locus", "mechanism", "reframes",
    "novelty", "plausibility", "probe_cost", "kill_criterion", "status",
]


def main():
    with open(IDEAS) as f:
        ideas = yaml.safe_load(f)
    if not isinstance(ideas, list):
        sys.exit("FATAL: ideas.yaml must be a top-level list of entries.")

    errors = []
    seen = set()
    for i, e in enumerate(ideas):
        tag = e.get("id", f"<entry #{i}>") if isinstance(e, dict) else f"<entry #{i}>"
        if not isinstance(e, dict):
            errors.append(f"{tag}: not a mapping")
            continue
        for k in REQUIRED:
            if k not in e or e[k] in (None, "", []):
                errors.append(f"{tag}: missing/empty required field '{k}'")
        if e.get("id") in seen:
            errors.append(f"{tag}: duplicate id")
        seen.add(e.get("id"))
        if e.get("lens") not in LENS:
            errors.append(f"{tag}: lens '{e.get('lens')}' not in vocab")
        for loc in (e.get("locus") or []):
            if loc not in LOCUS:
                errors.append(f"{tag}: locus '{loc}' not in vocab")
        if e.get("mechanism") not in MECHANISM:
            errors.append(f"{tag}: mechanism '{e.get('mechanism')}' not in vocab")
        if e.get("novelty") not in NOVELTY:
            errors.append(f"{tag}: novelty '{e.get('novelty')}' not in vocab")
        if e.get("probe_cost") not in PROBE_COST:
            errors.append(f"{tag}: probe_cost '{e.get('probe_cost')}' not in vocab")
        if e.get("status") not in STATUS:
            errors.append(f"{tag}: status '{e.get('status')}' not in vocab")
        p = e.get("plausibility")
        if not (isinstance(p, int) and 1 <= p <= 5):
            errors.append(f"{tag}: plausibility must be int 1..5, got {p!r}")
        kc = e.get("kill_criterion")
        if not (isinstance(kc, str) and len(kc.strip()) > 10):
            errors.append(f"{tag}: kill_criterion missing or too short (the entry fee)")
        rf = e.get("reframes")
        if not (isinstance(rf, dict) and "competes_with" in rf and "delta" in rf):
            errors.append(f"{tag}: reframes must be {{competes_with: [...], delta: ...}}")

    if errors:
        print(f"INVALID — {len(errors)} error(s):")
        for er in errors:
            print("  -", er)
        sys.exit(1)
    print(f"OK — {len(ideas)} entries, all axes valid, every kill_criterion present.")


if __name__ == "__main__":
    main()
