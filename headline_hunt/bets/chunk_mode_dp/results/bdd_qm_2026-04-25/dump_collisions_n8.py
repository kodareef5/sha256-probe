#!/usr/bin/env python3
"""Brute-force enumerate all N=8 collisions for the chunk_mode_dp candidate
(M[0]=0x67, fill=0xff, MSB kernel). Writes one collision per line as
"W57 W58 W59 W60" hex bytes — the format bdd_qm reads.

Used to feed q5/bdd_qm tool (BDD completion-quotient + marginal-probability
analysis on the 260-collision corpus).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/../../../../..')
spec = __import__('50_precision_homotopy')
sha = spec.MiniSHA256(8)
MASK = sha.MASK

result = sha.find_m0()
m0, s1, s2, W1_pre, W2_pre = result
assert m0 is not None, "no candidate"

K = sha.K
sigma1 = sha.sigma1
sigma0 = sha.sigma0
Sigma1 = sha.Sigma1
Sigma0 = sha.Sigma0
ch = sha.ch
maj = sha.maj


def round_step(s, k, w):
    a, b, c, d, e, f, g, h = s
    T1 = (h + Sigma1(e) + ch(e, f, g) + k + w) & MASK
    T2 = (Sigma0(a) + maj(a, b, c)) & MASK
    return ((T1 + T2) & MASK, a, b, c, (d + T1) & MASK, e, f, g)


# Cascade-1 offset (W2[57] - W1[57] required for da_57 = 0)
dh = (s1[7] - s2[7]) & MASK
dSig1 = (Sigma1(s1[4]) - Sigma1(s2[4])) & MASK
dCh = (ch(s1[4], s1[5], s1[6]) - ch(s2[4], s2[5], s2[6])) & MASK
T2_1 = (Sigma0(s1[0]) + maj(s1[0], s1[1], s1[2])) & MASK
T2_2 = (Sigma0(s2[0]) + maj(s2[0], s2[1], s2[2])) & MASK
dT2_56 = (T2_1 - T2_2) & MASK
C_w57 = (dh + dSig1 + dCh + dT2_56) & MASK


count = 0
total = 0
for w57_1 in range(256):
    w57_2 = (w57_1 + C_w57) & MASK
    s1_57 = round_step(s1, K[57], w57_1)
    s2_57 = round_step(s2, K[57], w57_2)
    if (s1_57[0] - s2_57[0]) & MASK != 0:
        continue
    for w58_1 in range(256):
        # cascade extends — required offset depends on r=57 state
        dh = (s1_57[7] - s2_57[7]) & MASK
        dSig1 = (Sigma1(s1_57[4]) - Sigma1(s2_57[4])) & MASK
        dCh = (ch(s1_57[4], s1_57[5], s1_57[6]) - ch(s2_57[4], s2_57[5], s2_57[6])) & MASK
        T2_1 = (Sigma0(s1_57[0]) + maj(s1_57[0], s1_57[1], s1_57[2])) & MASK
        T2_2 = (Sigma0(s2_57[0]) + maj(s2_57[0], s2_57[1], s2_57[2])) & MASK
        dT2 = (T2_1 - T2_2) & MASK
        C_w58 = (dh + dSig1 + dCh + dT2) & MASK
        w58_2 = (w58_1 + C_w58) & MASK
        s1_58 = round_step(s1_57, K[58], w58_1)
        s2_58 = round_step(s2_57, K[58], w58_2)
        if (s1_58[0] - s2_58[0]) & MASK != 0:
            continue
        for w59_1 in range(256):
            dh = (s1_58[7] - s2_58[7]) & MASK
            dSig1 = (Sigma1(s1_58[4]) - Sigma1(s2_58[4])) & MASK
            dCh = (ch(s1_58[4], s1_58[5], s1_58[6]) - ch(s2_58[4], s2_58[5], s2_58[6])) & MASK
            T2_1 = (Sigma0(s1_58[0]) + maj(s1_58[0], s1_58[1], s1_58[2])) & MASK
            T2_2 = (Sigma0(s2_58[0]) + maj(s2_58[0], s2_58[1], s2_58[2])) & MASK
            dT2 = (T2_1 - T2_2) & MASK
            C_w59 = (dh + dSig1 + dCh + dT2) & MASK
            w59_2 = (w59_1 + C_w59) & MASK
            s1_59 = round_step(s1_58, K[59], w59_1)
            s2_59 = round_step(s2_58, K[59], w59_2)
            if any((s1_59[i] - s2_59[i]) & MASK != 0 for i in (0, 1, 2)):
                continue
            # cascade-2 at r=60: offset zeros de60
            dh = (s1_59[7] - s2_59[7]) & MASK
            dSig1 = (Sigma1(s1_59[4]) - Sigma1(s2_59[4])) & MASK
            dCh = (ch(s1_59[4], s1_59[5], s1_59[6]) - ch(s2_59[4], s2_59[5], s2_59[6])) & MASK
            C_w60 = (dh + dSig1 + dCh) & MASK
            for w60_1 in range(256):
                w60_2 = (w60_1 + C_w60) & MASK
                s1_60 = round_step(s1_59, K[60], w60_1)
                s2_60 = round_step(s2_59, K[60], w60_2)
                if (s1_60[4] - s2_60[4]) & MASK != 0:
                    continue
                # Build W[61..63]
                W1 = list(W1_pre[:57]) + [w57_1, w58_1, w59_1, w60_1]
                W2 = list(W2_pre[:57]) + [w57_2, w58_2, w59_2, w60_2]
                for r in range(61, 64):
                    W1.append((sigma1(W1[r-2]) + W1[r-7] + sigma0(W1[r-15]) + W1[r-16]) & MASK)
                    W2.append((sigma1(W2[r-2]) + W2[r-7] + sigma0(W2[r-15]) + W2[r-16]) & MASK)
                s1_x, s2_x = s1_60, s2_60
                for r in range(61, 64):
                    s1_x = round_step(s1_x, K[r], W1[r])
                    s2_x = round_step(s2_x, K[r], W2[r])
                total += 1
                if all((s1_x[i] - s2_x[i]) & MASK == 0 for i in range(8)):
                    print(f"{w57_1:02x} {w58_1:02x} {w59_1:02x} {w60_1:02x}")
                    count += 1

print(f"# {count} collisions across {total} cascade-extending tuples", file=sys.stderr)
