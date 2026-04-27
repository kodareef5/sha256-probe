#!/usr/bin/env python3
"""
parse_F28_archive.py — Convert F28_registry_1B/ block2_lowhw_set.c
human-readable logs into structured JSONL corpus entries.

Input log format (one per cand):
    === block2 lowhw set: m0=0x... fill=0x... bit=N max_hw=K ===
    samples: 1000000000  elapsed: ...
    min HW seen: ...
    HW=NN: M total, D distinct vectors
      [0] W = 0xW57 0xW58 0xW59 0xW60
          d = 0xd0 0xd1 0xd2 0xd3 0xd4 0xd5 0xd6 0xd7
      [1] W = ...
          d = ...
      ...

Output: deep_corpus.jsonl with one record per (cand, hw, distinct_idx)
of the form:
  {"candidate_id": "cand_n32_...", "m0": "0x...", "fill": "0x...",
   "kernel_bit": N, "samples": 1000000000, "hw_total": NN, "hw_idx": I,
   "diff63": [...], "w_57": ..., "w_58": ..., "w_59": ..., "w_60": ...}

Usage: python3 parse_F28_archive.py <archive_dir> <out_jsonl>
"""
import json
import os
import re
import sys


HW_LINE = re.compile(r"^HW=(\d+):\s+(\d+)\s+total,\s+(\d+)\s+distinct")
W_LINE = re.compile(r"^\s*\[(\d+)\]\s+W\s*=\s*0x([0-9a-fA-F]+)\s+0x([0-9a-fA-F]+)\s+0x([0-9a-fA-F]+)\s+0x([0-9a-fA-F]+)")
D_LINE = re.compile(r"^\s+d\s*=\s*((?:0x[0-9a-fA-F]+\s+){8})")
HEADER = re.compile(r"^=== block2 lowhw set: m0=0x([0-9a-fA-F]+) fill=0x([0-9a-fA-F]+) bit=(\d+) max_hw=(\d+) ===")
SAMPLES_LINE = re.compile(r"^samples:\s+(\d+)\s+elapsed:\s+([0-9.]+)s")


def parse_log(path):
    """Yield records from one F28 cand log."""
    cand_id = os.path.basename(path).replace(".log", "")
    with open(path) as f:
        lines = f.readlines()

    m0 = fill = kernel_bit = max_hw = samples = None
    for line in lines[:10]:
        h = HEADER.match(line.strip())
        if h:
            m0 = "0x" + h.group(1).lower()
            fill = "0x" + h.group(2).lower()
            kernel_bit = int(h.group(3))
            max_hw = int(h.group(4))
        s = SAMPLES_LINE.match(line.strip())
        if s:
            samples = int(s.group(1))

    if m0 is None:
        return

    cur_hw = None
    cur_total = cur_distinct = 0
    cur_w = None
    cur_idx = None
    i = 0
    while i < len(lines):
        line = lines[i]
        h = HW_LINE.match(line.strip())
        if h:
            cur_hw = int(h.group(1))
            cur_total = int(h.group(2))
            cur_distinct = int(h.group(3))
            i += 1
            continue
        wm = W_LINE.match(line)
        if wm and cur_hw is not None:
            cur_idx = int(wm.group(1))
            cur_w = (
                "0x" + wm.group(2).lower(),
                "0x" + wm.group(3).lower(),
                "0x" + wm.group(4).lower(),
                "0x" + wm.group(5).lower(),
            )
            i += 1
            if i < len(lines):
                dm = D_LINE.match(lines[i])
                if dm:
                    parts = dm.group(1).split()
                    diff = [p.lower() for p in parts]
                    yield {
                        "candidate_id": cand_id,
                        "m0": m0, "fill": fill, "kernel_bit": kernel_bit,
                        "samples": samples,
                        "hw_total": cur_hw, "hw_idx": cur_idx,
                        "hw_total_count": cur_total,
                        "hw_distinct_count": cur_distinct,
                        "w_57": cur_w[0], "w_58": cur_w[1],
                        "w_59": cur_w[2], "w_60": cur_w[3],
                        "diff63": diff,
                        "a63": diff[0], "b63": diff[1], "c63": diff[2],
                        "d63": diff[3], "e63": diff[4], "f63": diff[5],
                        "g63": diff[6], "h63": diff[7],
                        "a61": diff[2], "e61": diff[6],
                        "a61_eq_e61": diff[2] == diff[6],
                    }
                    i += 1
                    continue
        i += 1


def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <archive_dir> <out_jsonl>", file=sys.stderr)
        sys.exit(1)
    archive = sys.argv[1]
    out = sys.argv[2]
    n_logs = 0
    n_records = 0
    cand_min_hw = {}
    cand_a61_e61 = {}
    with open(out, "w") as fout:
        for fn in sorted(os.listdir(archive)):
            if not fn.endswith(".log"):
                continue
            n_logs += 1
            min_hw = 999
            for rec in parse_log(os.path.join(archive, fn)):
                fout.write(json.dumps(rec) + "\n")
                n_records += 1
                if rec["hw_total"] < min_hw:
                    min_hw = rec["hw_total"]
                    cand_id = rec["candidate_id"]
            if min_hw < 999:
                cand_min_hw[cand_id] = min_hw
                # a_61 == e_61 at MIN HW for this cand
                pass

    print(f"Parsed {n_logs} cand logs, wrote {n_records} records to {out}",
          file=sys.stderr)
    print(f"Min HW summary (top 5 cands by lowest):", file=sys.stderr)
    sorted_cands = sorted(cand_min_hw.items(), key=lambda x: x[1])
    for cid, hw in sorted_cands[:5]:
        print(f"  {cid}: HW={hw}", file=sys.stderr)


if __name__ == "__main__":
    main()
