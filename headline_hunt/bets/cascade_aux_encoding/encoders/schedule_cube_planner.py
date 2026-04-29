#!/usr/bin/env python3
"""
schedule_cube_planner.py - Generate cascade_aux schedule-bit cubes.

This is a lightweight cube-and-conquer helper for the cascade_aux CNFs.
It uses the encoder's documented allocation convention:

  var 1 is TRUE
  W1 free words start at var 2
  W2 free words follow W1

For sr=60 the free rounds are W[57..60], so W1_57[0] is var 2 and
W2_57[0] is var 130. For sr=61 there are three free rounds W[57..59].

The planner can create unit cubes on W1/W2 bits or joint dW cubes, where
dW[round][bit] is represented as W2[round][bit] XOR W1[round][bit].
It always writes a JSONL manifest and can optionally emit augmented CNFs
with the cube clauses appended and the DIMACS header clause count fixed.
"""

from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path
from typing import Iterable


def parse_bits(spec: str) -> list[int]:
    bits: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            lo_s, hi_s = part.split("-", 1)
            lo, hi = int(lo_s), int(hi_s)
            if hi < lo:
                raise ValueError(f"descending bit range: {part}")
            bits.update(range(lo, hi + 1))
        else:
            bits.add(int(part))
    out = sorted(bits)
    bad = [b for b in out if b < 0 or b > 31]
    if bad:
        raise ValueError(f"bit positions outside 0..31: {bad}")
    return out


def parse_combos(spec: str) -> list[tuple[int, ...]]:
    combos: list[tuple[int, ...]] = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        combo = tuple(int(x) for x in part.replace(":", "+").split("+") if x)
        if not combo:
            continue
        bad = [b for b in combo if b < 0 or b > 31]
        if bad:
            raise ValueError(f"combo bits outside 0..31: {bad}")
        if len(set(combo)) != len(combo):
            raise ValueError(f"combo repeats a bit: {part}")
        combos.append(combo)
    if not combos:
        raise ValueError("no combos parsed")
    depths = {len(c) for c in combos}
    if len(depths) != 1:
        raise ValueError(f"all combos must have the same depth, got {sorted(depths)}")
    return combos


def infer_sr_from_name(path: Path) -> int | None:
    for sr in (59, 60, 61):
        if f"sr{sr}" in path.name:
            return sr
    return None


def n_free_words(sr: int) -> int:
    if sr not in (59, 60, 61):
        raise ValueError("sr must be one of 59, 60, 61")
    return 64 - sr


def schedule_var(sr: int, word: str, round_: int, bit: int) -> int:
    """Return the SAT var for W1/W2 free schedule bit."""
    n_free = n_free_words(sr)
    first_round = 57
    last_round = first_round + n_free - 1
    if round_ < first_round or round_ > last_round:
        raise ValueError(
            f"round {round_} outside free schedule window "
            f"{first_round}..{last_round} for sr={sr}"
        )
    if bit < 0 or bit > 31:
        raise ValueError("bit must be 0..31")
    round_offset = round_ - first_round
    if word == "w1":
        base = 2
    elif word == "w2":
        base = 2 + n_free * 32
    else:
        raise ValueError("word must be w1 or w2")
    return base + round_offset * 32 + bit


def unit_clause_for_value(var: int, value: int) -> list[int]:
    if value not in (0, 1):
        raise ValueError("cube values must be 0 or 1")
    return [var if value else -var]


def xor_clauses_for_value(left_var: int, right_var: int, value: int) -> list[list[int]]:
    """Clauses for right_var XOR left_var == value."""
    if value == 0:
        return [[left_var, -right_var], [-left_var, right_var]]
    if value == 1:
        return [[left_var, right_var], [-left_var, -right_var]]
    raise ValueError("cube values must be 0 or 1")


def parse_dimacs_header(path: Path) -> tuple[int, int]:
    with path.open() as f:
        for line in f:
            if line.startswith("p cnf "):
                fields = line.split()
                if len(fields) != 4:
                    raise ValueError(f"bad DIMACS header in {path}: {line.rstrip()}")
                return int(fields[2]), int(fields[3])
    raise ValueError(f"missing DIMACS header in {path}")


def write_augmented_cnf(src: Path, dst: Path, added_clauses: list[list[int]], cube_id: str) -> None:
    max_var, n_clauses = parse_dimacs_header(src)
    dst.parent.mkdir(parents=True, exist_ok=True)
    with src.open() as inp, dst.open("w") as out:
        header_written = False
        for line in inp:
            if line.startswith("p cnf "):
                out.write(f"p cnf {max_var} {n_clauses + len(added_clauses)}\n")
                header_written = True
            else:
                out.write(line)
        if not header_written:
            raise ValueError(f"missing DIMACS header in {src}")
        out.write(f"c schedule_cube_planner cube_id={cube_id}\n")
        for clause in added_clauses:
            out.write(" ".join(str(lit) for lit in clause))
            out.write(" 0\n")


def cube_records(
    sr: int,
    target: str,
    round_: int,
    bits: list[int],
    depth: int,
    combos: list[tuple[int, ...]] | None = None,
) -> Iterable[dict]:
    if combos is None:
        if depth < 1:
            raise ValueError("depth must be >= 1")
        if depth > len(bits):
            raise ValueError("depth cannot exceed number of selected bits")
        selected_combos: Iterable[tuple[int, ...]] = itertools.combinations(bits, depth)
    else:
        selected_combos = combos
        depth = len(combos[0])

    for combo in selected_combos:
        for values in itertools.product((0, 1), repeat=depth):
            clauses: list[list[int]] = []
            assignments: list[dict] = []
            id_parts: list[str] = []
            for bit, value in zip(combo, values):
                if target in ("w1", "w2"):
                    var = schedule_var(sr, target, round_, bit)
                    clause = unit_clause_for_value(var, value)
                    clauses.append(clause)
                    assignments.append({
                        "target": target,
                        "round": round_,
                        "bit": bit,
                        "value": value,
                        "literal": clause[0],
                    })
                    id_parts.append(f"{target}r{round_}b{bit:02d}v{value}")
                elif target == "dw":
                    w1 = schedule_var(sr, "w1", round_, bit)
                    w2 = schedule_var(sr, "w2", round_, bit)
                    bit_clauses = xor_clauses_for_value(w1, w2, value)
                    clauses.extend(bit_clauses)
                    assignments.append({
                        "target": "dw",
                        "round": round_,
                        "bit": bit,
                        "value": value,
                        "w1_var": w1,
                        "w2_var": w2,
                        "clauses": bit_clauses,
                    })
                    id_parts.append(f"dwr{round_}b{bit:02d}v{value}")
                else:
                    raise ValueError("target must be w1, w2, or dw")
            yield {
                "cube_id": "__".join(id_parts),
                "target": target,
                "sr": sr,
                "round": round_,
                "depth": depth,
                "assignments": assignments,
                "clauses": clauses,
                "added_clause_count": len(clauses),
            }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cnf", required=True, type=Path, help="base DIMACS CNF")
    ap.add_argument("--sr", type=int, help="sr level; inferred from CNF name if omitted")
    ap.add_argument("--target", choices=("w1", "w2", "dw"), default="dw",
                    help="cube target: W1 bits, W2 bits, or joint dW XOR bits")
    ap.add_argument("--round", type=int, default=60,
                    help="free schedule round to cube, usually 57..60 for sr=60")
    ap.add_argument("--bits", default="0-31", help="bit list/ranges, e.g. 0-7,16,31")
    ap.add_argument("--depth", type=int, default=1,
                    help="number of bit positions fixed per cube")
    ap.add_argument("--combos",
                    help="explicit bit combos, e.g. 22:26,25:28; overrides --bits")
    ap.add_argument("--limit", type=int, default=0,
                    help="maximum manifest records to write; 0 means all")
    ap.add_argument("--out-jsonl", required=True, type=Path, help="cube manifest JSONL")
    ap.add_argument("--emit-cnf-dir", type=Path,
                    help="optional directory for augmented cube CNFs")
    ap.add_argument("--emit-limit", type=int, default=0,
                    help="maximum augmented CNFs to write; 0 means every manifest record")
    args = ap.parse_args()

    sr = args.sr if args.sr is not None else infer_sr_from_name(args.cnf)
    if sr is None:
        raise SystemExit("could not infer sr from CNF name; pass --sr")
    combos = parse_combos(args.combos) if args.combos else None
    bits = parse_bits(args.bits)
    max_var, n_clauses = parse_dimacs_header(args.cnf)

    args.out_jsonl.parent.mkdir(parents=True, exist_ok=True)
    n_records = 0
    n_emitted = 0
    with args.out_jsonl.open("w") as out:
        for rec in cube_records(sr, args.target, args.round, bits, args.depth, combos):
            if args.limit and n_records >= args.limit:
                break
            rec["base_cnf"] = str(args.cnf)
            rec["base_vars"] = max_var
            rec["base_clauses"] = n_clauses
            rec["augmented_clauses"] = n_clauses + rec["added_clause_count"]
            rec["cnf_path"] = None

            should_emit = args.emit_cnf_dir is not None
            if args.emit_limit and n_emitted >= args.emit_limit:
                should_emit = False
            if should_emit:
                dst = args.emit_cnf_dir / f"{args.cnf.stem}__{rec['cube_id']}.cnf"
                write_augmented_cnf(args.cnf, dst, rec["clauses"], rec["cube_id"])
                rec["cnf_path"] = str(dst)
                n_emitted += 1

            out.write(json.dumps(rec, sort_keys=True))
            out.write("\n")
            n_records += 1

    print(
        f"wrote {n_records} cube records to {args.out_jsonl} "
        f"({n_emitted} augmented CNFs emitted)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
