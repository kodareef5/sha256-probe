#!/usr/bin/env python3
"""Build a 2blockcertpin/v1 trail bundle from a block-1 free-word record.

Connects the residual-minimization frontier (e.g. bit13 HW35) to the block-2
absorber tools (sweep/beam_w2_exactdiff), which only had naive HW55-63 bundles.
Computes the round-63 residual via block2_bridge_beam.run_full and emits a bundle
mirroring the naive_blocktwo fixtures. Reuse, no SHA reimplementation.

Usage: build_bundle_from_record.py <cand_short> <w57>,<w58>,<w59>,<w60> <out.json>
  e.g. build_bundle_from_record.py bit13_m916a56aa 0x5228ed8d,0x61a1a29c,0x6a7a8409,0xc7d515db out.json
"""
import json
import sys
import os

ENCODERS = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(ENCODERS, "../../../.."))
sys.path.insert(0, REPO)
sys.path.insert(0, ENCODERS)
from block2_bridge_beam import CANDS, setup_cand, run_full  # noqa: E402

REG = ["a", "b", "c", "d", "e", "f", "g", "h"]


def main():
    short = sys.argv[1]
    w = [int(x, 16) & 0xffffffff for x in sys.argv[2].split(",")]
    out = sys.argv[3]
    cand = next((c for c in CANDS if c[0] == short), None)
    assert cand, f"unknown candidate {short}"
    _, m0, fill, kbit = cand
    s = setup_cand(m0, fill, kbit)
    assert s, f"{short} not cascade-eligible"
    s1i, s2i, W1p, W2p = s
    r = run_full(s1i, s2i, W1p, W2p, *w)
    assert r is not None, "record violates cascade-1/2 invariants"
    diff = r["diff63"]
    hw = sum(bin(d).count("1") for d in diff)
    w2 = r["w_ms_2"]
    print(f"{short}: residual HW={hw}  diff63={[hex(d) for d in diff]}")

    bundle = {
        "schema_version": "2blockcertpin/v1",
        "cand_id": f"cand_n32_{short}_fill{fill:08x}",
        "witness_id": f"{short}_HW{hw}_from_record_macbook_claude",
        "block1": {
            "m0": f"0x{m0:08x}", "fill": f"0x{fill:08x}", "kernel_bit": kbit,
            "W1_57_60": [f"0x{x:08x}" for x in w],
            "W2_57_60": [f"0x{x:08x}" for x in w2],
            "expected_status": "near_residual_unsat",
            "residual_state_diff": {f"d{REG[i]}63": f"0x{diff[i]:08x}" for i in range(8)},
            "residual_hw": hw,
            "residual_lm_cost": None,
            "comment": (f"{short} HW={hw} from the residual-min frontier record "
                        "(macbook-claude 2026-05-25). Built to test whether the optimized "
                        "residual absorbs in block-2 better than the naive HW55-63 bundles."),
        },
        "block2": {
            "absorption_pattern": "naive_no_constraints_test",
            "modified_message_words": [],
            "W2_constraints": [],
            "chain_state_input": {"comment": f"Block-1 produces HW={hw} working-state residual, d=h=0 cascade-1 forced."},
            "target_diff_at_round_N": dict(
                {"round": 63}, **{f"diff_{REG[i]}": "0x00000000" for i in range(8)},
                comment="All-zero collision target; naive block-2, no W2 constraints."),
            "expected_status": "forward_broken_test",
            "expected_modular_paths": [],
            "predicted_lm_cost_block2": None,
        },
        "metadata": {
            "designer": "macbook-claude (residual<->absorber integration test)",
            "design_date": "2026-05-25",
            "design_method": "block1_residual_min_frontier_record",
            "confidence": "test_whether_optimized_residual_helps_block2",
            "compat_with_block1_witness": True,
            "smaller_N_validation": None,
            "purpose": ("Integration test: does the HW35 residual-min record absorb in block-2 "
                        "better than naive HW55-63 bundles? Compare sweep/beam_w2_exactdiff."),
        },
    }
    with open(out, "w") as f:
        json.dump(bundle, f, indent=2)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
