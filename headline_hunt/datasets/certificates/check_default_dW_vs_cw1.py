"""Question: For msb_m17149975 default M, does the schedule-derived dW[57..60]
EQUAL the cw1[57..60] needed for cascade-1?

If YES: the cert's W[57..60] aren't actually free — the default schedule already
gives cascade-1 alignment at those slots. The collision is automatic, no
schedule relaxation needed.

If NO: the cert's W[57..60] are RELAXED from schedule. The cert is a semi-free-
start collision in the schedule-attack model.
"""
import sys
sys.path.insert(0, '/Users/mac/Desktop/sha256_review')
from lib.sha256 import K, IV, MASK, Sigma0, Sigma1, Ch, Maj, sigma0, sigma1

def cw1(s1, s2):
    return ((s1[7]-s2[7]) + (Sigma1(s1[4])-Sigma1(s2[4])) +
            (Ch(s1[4],s1[5],s1[6])-Ch(s2[4],s2[5],s2[6])) +
            (Sigma0(s1[0])+Maj(s1[0],s1[1],s1[2])) -
            (Sigma0(s2[0])+Maj(s2[0],s2[1],s2[2]))) & MASK

def sr_round(s, k, w):
    a,b,c,d,e,f,g,h = s
    T1 = (h+Sigma1(e)+Ch(e,f,g)+k+w) & MASK
    T2 = (Sigma0(a)+Maj(a,b,c)) & MASK
    return [(T1+T2)&MASK,a,b,c,(d+T1)&MASK,e,f,g]

def schedule(M):
    W = list(M) + [0]*48
    for i in range(16, 64):
        W[i] = (sigma1(W[i-2]) + W[i-7] + sigma0(W[i-15]) + W[i-16]) & MASK
    return W

# Default M for msb_m17149975
M1 = [0x17149975] + [0xffffffff]*15
M2 = list(M1)
M2[0] ^= 0x80000000
M2[9] ^= 0x80000000

W1 = schedule(M1)
W2 = schedule(M2)

# State at slot 57 input (before round 57)
s1 = list(IV); s2 = list(IV)
for r in range(57):
    s1 = sr_round(s1, K[r], W1[r])
    s2 = sr_round(s2, K[r], W2[r])

# Does the default schedule's dW[57..60] match cw1[57..60]?
print("=== Default M schedule's dW[57..60] vs cw1[57..60] (cascade-1 needed) ===")
print(f'(default M = [0x17149975, 0xff, 0xff, ..., 0xff])\n')
for k in range(57, 64):
    cw1_needed = cw1(s1, s2)
    schedule_dW = (W2[k] - W1[k]) & MASK
    match = (cw1_needed == schedule_dW)
    print(f'  slot {k}: cw1_needed=0x{cw1_needed:08x}  schedule_dW=0x{schedule_dW:08x}  match={match}')
    # Apply round (using actual schedule W) to advance state
    s1 = sr_round(s1, K[k], W1[k])
    s2 = sr_round(s2, K[k], W2[k])

# Also — would the default schedule give a hash collision?
# (If schedule's dW[k] != cw1[k] at any slot in 57..63, cascade-1 fails there.)
print(f'\n=== Final state under default schedule ===')
print(f'After 64 rounds:')
print(f'  M1: {[hex(x) for x in s1]}')
print(f'  M2: {[hex(x) for x in s2]}')
print(f'  state matches (collision): {s1 == s2}')
