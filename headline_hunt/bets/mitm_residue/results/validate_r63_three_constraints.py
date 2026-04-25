"""
Cross-corpus validation of modular constraints among the 6 active registers
at r=63 in the cascade-DP residual.

Theorem 4 (unified) + shift-register propagation imply:

  C1:  dc_63 ≡ dg_63 (mod 2^32)
       Reason: c_63 = a_61, g_63 = e_61, and at r=61 we have da_61 = de_61
       (Theorem 4 specialized; dT2_61 = 0 since a_60, b_60, c_60 cascade-zero).

  C3:  da_63 − de_63 ≡ dT2_63 (mod 2^32)
       Reason: unified Theorem 4 at r=63 with dd_62 = 0 (cascade still holds for d).

Checked here. The third natural relation `db_63 − df_63 ≡ dT2_62` requires
the value a_59 to compute dT2_62 correctly (Maj depends on actual values,
not just differences), and the corpus only stores iv_63 which gives a_60..a_63.
We omit it here; the cascade-aware fresh-sample harness already verified it
1000/1000 separately.
"""
import json, sys

MASK = 0xFFFFFFFF


def rotr(x, n):
    return ((x >> n) | (x << (32 - n))) & MASK


def Sigma0(x):
    return rotr(x, 2) ^ rotr(x, 13) ^ rotr(x, 22)


def Maj(x, y, z):
    return (x & y) ^ (x & z) ^ (y & z)


def main(path):
    n = 0
    c1 = c3 = 0

    with open(path) as f:
        for line in f:
            r = json.loads(line)
            iv1 = [int(x, 16) for x in r["iv1_63"]]
            iv2 = [int(x, 16) for x in r["iv2_63"]]

            dc_63 = (iv1[2] - iv2[2]) & MASK
            dg_63 = (iv1[6] - iv2[6]) & MASK
            da_63 = (iv1[0] - iv2[0]) & MASK
            de_63 = (iv1[4] - iv2[4]) & MASK

            a1_60 = iv1[3]; a2_60 = iv2[3]
            a1_61 = iv1[2]; a2_61 = iv2[2]
            a1_62 = iv1[1]; a2_62 = iv2[1]

            dSigma0_a62 = (Sigma0(a1_62) - Sigma0(a2_62)) & MASK
            dMaj_62 = (Maj(a1_62, a1_61, a1_60) - Maj(a2_62, a2_61, a2_60)) & MASK
            dT2_63 = (dSigma0_a62 + dMaj_62) & MASK

            n += 1
            if dc_63 == dg_63: c1 += 1
            if ((da_63 - de_63) & MASK) == dT2_63: c3 += 1

    def pct(x): return f"{x/n*100:.4f}%"
    print(f"records: {n}")
    print(f"C1: dc_63 ≡ dg_63                    : {c1}/{n} ({pct(c1)})")
    print(f"C3: da_63 − de_63 ≡ dT2_63 (unified) : {c3}/{n} ({pct(c3)})")


if __name__ == "__main__":
    main(sys.argv[1])
