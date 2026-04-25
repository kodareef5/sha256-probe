#!/usr/bin/env python3
"""
forward_table_reader.py — Read priority candidate forward MITM table.

The table at `datasets/bdds/priority_forward_table.bin` maps 17-bit
signatures (sig in [0, 131071]) to a witness (W1[57], W1[58], W1[59])
triple that produces that signature on the priority candidate.

Format:
  bytes 0..3:   magic 'PFT1'
  bytes 4..7:   uint32 signature bit count (17)
  bytes 8..11:  uint32 max signatures (131072)
  bytes 12..15: uint32 actual coverage
  bytes 16..31: reserved
  bytes 32+:    131072 × (3 × uint32) records, indexed by signature

Sentinel (0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF) means no witness recorded.

Usage:
  python3 forward_table_reader.py --info
  python3 forward_table_reader.py --lookup 12345
  python3 forward_table_reader.py --sample 3
"""
import argparse
import os
import struct
import sys

DEFAULT_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "..", "datasets", "bdds", "priority_forward_table.bin")


def read_header(f):
    magic = f.read(4)
    if magic != b'PFT1':
        raise RuntimeError(f"bad magic: {magic!r}")
    bit_count, max_sigs, coverage = struct.unpack('<III', f.read(12))
    f.read(16)
    return bit_count, max_sigs, coverage


def read_witness(f, sig, max_sigs):
    if sig < 0 or sig >= max_sigs:
        raise ValueError(f"sig {sig} out of range [0, {max_sigs})")
    f.seek(32 + sig * 12)
    w = struct.unpack('<III', f.read(12))
    if w == (0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF):
        return None
    return w


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", default=DEFAULT_PATH)
    ap.add_argument("--info", action="store_true")
    ap.add_argument("--lookup", type=int, default=None)
    ap.add_argument("--sample", type=int, default=None)
    args = ap.parse_args()

    if not os.path.exists(args.path):
        print(f"ERROR: table not found at {args.path}", file=sys.stderr)
        sys.exit(2)

    with open(args.path, 'rb') as f:
        bit_count, max_sigs, coverage = read_header(f)
        if args.info:
            size = os.path.getsize(args.path)
            print(f"Forward MITM table: {args.path}")
            print(f"  Magic OK: PFT1")
            print(f"  Signature bit count: {bit_count}")
            print(f"  Max signatures (2^bits): {max_sigs}")
            print(f"  Recorded coverage: {coverage}/{max_sigs} ({100*coverage/max_sigs:.1f}%)")
            print(f"  File size: {size:,} bytes ({size/(1024*1024):.2f} MB)")
            empty = 0
            for sig in range(max_sigs):
                f.seek(32 + sig * 12)
                if struct.unpack('<III', f.read(12)) == (0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF):
                    empty += 1
            print(f"  Empty (sentinel): {empty}")
        if args.lookup is not None:
            w = read_witness(f, args.lookup, max_sigs)
            if w is None:
                print(f"sig={args.lookup}: no witness recorded")
            else:
                print(f"sig={args.lookup}: W1[57]=0x{w[0]:08x} W1[58]=0x{w[1]:08x} W1[59]=0x{w[2]:08x}")
        if args.sample:
            import random
            for _ in range(args.sample):
                sig = random.randrange(max_sigs)
                w = read_witness(f, sig, max_sigs)
                if w is not None:
                    print(f"sig={sig:>5d}: W1[57]=0x{w[0]:08x} W1[58]=0x{w[1]:08x} W1[59]=0x{w[2]:08x}")


if __name__ == "__main__":
    main()
