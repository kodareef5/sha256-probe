#!/usr/bin/env python3
"""
Re-rank the block2_wang residual corpus using the cascade-DP structural picture.

The 6 active registers at r=63 satisfy:
  R63.1:  dc_63 = dg_63 (modular)        — pinning dc bits ⇒ dg matches automatically
  R63.3:  de_63 = da_63 − dT2_63 (mod)   — de is determined by da and a-values

Naive HW ranking treats all 6 registers equally. Structural ranking accounts for:
  - dc/dg coupling (1 bit set in dc → 2 bits set total, but 1 d.o.f. choice)
  - da/de coupling (de inherits HW from da−dT2_63, not a free d.o.f.)

We compute two metrics:
  HW_naive   = HW(da) + HW(db) + HW(dc) + HW(de) + HW(df) + HW(dg)
  HW_struct  = HW(da) + HW(db) + 2*HW(dc) + HW(da-dT2_63) + HW(df)
             = HW_naive when de = da-dT2_63 holds (always, by R63.3) and dg=dc (always, by R63.1)
             [identical to HW_naive in practice; structural relations don't change the SUM, just the d.o.f. count]

The interesting question: what's the structural FLOOR on HW_naive given the 4 d.o.f.?
And: are records near the floor reachable via cheap perturbations?
"""
import json
import sys


def hw(x):
    return bin(x & 0xFFFFFFFF).count("1")


def main(in_path, out_path, top_k=50):
    records = []
    with open(in_path) as f:
        for line in f:
            r = json.loads(line)
            iv1 = [int(x, 16) for x in r["iv1_63"]]
            iv2 = [int(x, 16) for x in r["iv2_63"]]
            MASK = 0xFFFFFFFF
            da = (iv1[0] - iv2[0]) & MASK
            db = (iv1[1] - iv2[1]) & MASK
            dc = (iv1[2] - iv2[2]) & MASK
            de = (iv1[4] - iv2[4]) & MASK
            df = (iv1[5] - iv2[5]) & MASK
            dg = (iv1[6] - iv2[6]) & MASK
            hw_naive = hw(da) + hw(db) + hw(dc) + hw(de) + hw(df) + hw(dg)
            # Structural FREE-d.o.f. HW: count just the 4 free moduli
            hw_free4 = hw(da) + hw(db) + hw(dc) + hw(df)
            r["hw_naive"] = hw_naive
            r["hw_free4"] = hw_free4
            r["da"] = da
            r["db"] = db
            r["dc"] = dc
            r["de"] = de
            r["df"] = df
            r["dg"] = dg
            records.append(r)

    print(f"records: {len(records)}")
    print()

    # Sort by hw_free4 (the 4 free d.o.f. HW)
    records.sort(key=lambda r: r["hw_free4"])
    print(f"Top-{top_k} by hw_free4 (4 d.o.f. Hamming weight):")
    print(f"{'rank':>4}  {'hw_free4':>9}  {'hw_naive':>9}  hw breakdown (da,db,dc,de,df,dg)")
    for i, r in enumerate(records[:top_k]):
        breakdown = (hw(r["da"]), hw(r["db"]), hw(r["dc"]),
                     hw(r["de"]), hw(r["df"]), hw(r["dg"]))
        print(f"{i+1:>4}  {r['hw_free4']:>9}  {r['hw_naive']:>9}  {breakdown}")

    print()
    print("Statistics:")
    hw_naive_list = [r["hw_naive"] for r in records]
    hw_free4_list = [r["hw_free4"] for r in records]
    print(f"  hw_naive   min={min(hw_naive_list)}  median={sorted(hw_naive_list)[len(hw_naive_list)//2]}  max={max(hw_naive_list)}")
    print(f"  hw_free4   min={min(hw_free4_list)}  median={sorted(hw_free4_list)[len(hw_free4_list)//2]}  max={max(hw_free4_list)}")

    # Save top-50 by hw_free4
    with open(out_path, "w") as f:
        for r in records[:top_k]:
            keys = ["candidate", "w1_57", "w1_58", "w1_59", "w1_60",
                    "w2_57", "w2_58", "w2_59", "w2_60",
                    "iv1_63", "iv2_63", "diff63", "hw63", "hw_total",
                    "active_regs", "da_eq_de", "hw_naive", "hw_free4"]
            out = {k: r[k] for k in keys if k in r}
            f.write(json.dumps(out) + "\n")
    print(f"\nWrote top-{top_k} by hw_free4 to {out_path}")


if __name__ == "__main__":
    in_path = sys.argv[1] if len(sys.argv) > 1 else "corpus_msb_200k_hw96.jsonl"
    out_path = sys.argv[2] if len(sys.argv) > 2 else "top50_lowest_hw_free4.jsonl"
    main(in_path, out_path)
