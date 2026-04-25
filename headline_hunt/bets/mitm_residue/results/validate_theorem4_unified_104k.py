"""
Cross-corpus validation: da_r - de_r ≡ dT2_r (mod 2^32) for r=63
across the 104k-record block2_wang corpus.

The corpus stores iv_63 = (a, b, c, d, e, f, g, h)_63. Shift register gives:
  a_60 = d_63  (since c_61 = b_60 = a_59 ... and d_63 = c_62 = b_61 = a_60)
  a_61 = c_63  (b_62 = a_61; c_63 = b_62)
  a_62 = b_63  (b_63 = a_62)

For dT2_63: need dSigma0(a_62) + dMaj(a_62, a_61, a_60).
"""
import json
import sys

MASK = 0xFFFFFFFF


def rotr(x, n):
    return ((x >> n) | (x << (32 - n))) & MASK


def Sigma0(x):
    return rotr(x, 2) ^ rotr(x, 13) ^ rotr(x, 22)


def Maj(x, y, z):
    return (x & y) ^ (x & z) ^ (y & z)


def main(path):
    total = 0
    matches = 0
    da63_zero = 0
    de63_zero = 0
    dT2_63_zero = 0
    mismatches = []

    with open(path) as f:
        for line in f:
            r = json.loads(line)
            iv1 = [int(x, 16) for x in r["iv1_63"]]
            iv2 = [int(x, 16) for x in r["iv2_63"]]

            a1_63 = iv1[0]; a1_62 = iv1[1]; a1_61 = iv1[2]; a1_60 = iv1[3]
            e1_63 = iv1[4]
            a2_63 = iv2[0]; a2_62 = iv2[1]; a2_61 = iv2[2]; a2_60 = iv2[3]
            e2_63 = iv2[4]

            da_63 = (a1_63 - a2_63) & MASK
            de_63 = (e1_63 - e2_63) & MASK

            dSigma0_a62 = (Sigma0(a1_62) - Sigma0(a2_62)) & MASK
            dMaj_62 = (Maj(a1_62, a1_61, a1_60) - Maj(a2_62, a2_61, a2_60)) & MASK
            dT2_63 = (dSigma0_a62 + dMaj_62) & MASK

            lhs = (da_63 - de_63) & MASK
            rhs = dT2_63

            total += 1
            if lhs == rhs:
                matches += 1
            else:
                if len(mismatches) < 5:
                    mismatches.append({
                        "lhs": hex(lhs), "rhs": hex(rhs),
                        "da63": hex(da_63), "de63": hex(de_63),
                        "dT2_63": hex(dT2_63),
                    })
            if da_63 == 0:
                da63_zero += 1
            if de_63 == 0:
                de63_zero += 1
            if dT2_63 == 0:
                dT2_63_zero += 1

    print(f"records: {total}")
    print(f"da_63 - de_63 ≡ dT2_63 (mod 2^32): {matches}/{total} ({matches/total*100:.4f}%)")
    print(f"da_63 == 0: {da63_zero}")
    print(f"de_63 == 0: {de63_zero}")
    print(f"dT2_63 == 0: {dT2_63_zero}")
    if mismatches:
        print(f"first {len(mismatches)} mismatches:")
        for m in mismatches:
            print(f"  {m}")


if __name__ == "__main__":
    main(sys.argv[1])
