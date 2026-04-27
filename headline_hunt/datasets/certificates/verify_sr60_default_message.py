"""Verify the sr=60 collision certificate end-to-end:
  M = [0x17149975, 0xffffffff, ..., 0xffffffff] for M1.
  M2 = M1 with M2[0] ^= 0x80000000, M2[9] ^= 0x80000000.
  W1[57..60] should match cert: 0x9ccfa55e, 0xd9d64416, 0x9e3ffb08, 0xb6befe82
  W2[57..60] should match cert: 0x72e6c8cd, 0x4b96ca51, 0x587ffaa6, 0xea3ce26b
  Final hash should match: ba6287f0dcaf9857d89ad44a6cced1e2adf8a242524236fbc0c656cd50a7e23b
  Both M1 and M2 should produce IDENTICAL state at slot 61 (rounds 0-60 collide).
"""
import sys, hashlib, struct
sys.path.insert(0, '/Users/mac/Desktop/sha256_review')
from lib.sha256 import K, IV, MASK, Sigma0, Sigma1, Ch, Maj, sigma0, sigma1, precompute_state

def sha_round(s, k, w):
    a,b,c,d,e,f,g,h = s
    T1 = (h + Sigma1(e) + Ch(e,f,g) + k + w) & MASK
    T2 = (Sigma0(a) + Maj(a,b,c)) & MASK
    return [(T1+T2)&MASK, a, b, c, (d+T1)&MASK, e, f, g]

def schedule(M):
    W = list(M) + [0]*48
    for i in range(16, 64):
        W[i] = (sigma1(W[i-2]) + W[i-7] + sigma0(W[i-15]) + W[i-16]) & MASK
    return W

# === Cert values ===
M1 = [0x17149975] + [0xffffffff]*15
M2 = list(M1)
M2[0] ^= 0x80000000
M2[9] ^= 0x80000000

W1_cert = {57: 0x9ccfa55e, 58: 0xd9d64416, 59: 0x9e3ffb08, 60: 0xb6befe82}
W2_cert = {57: 0x72e6c8cd, 58: 0x4b96ca51, 59: 0x587ffaa6, 60: 0xea3ce26b}

print('=== sr=60 CERTIFICATE VERIFICATION ===')
print(f'M1[0]    = 0x{M1[0]:08x}')
print(f'M2[0]    = 0x{M2[0]:08x}  (M1[0] ^ 0x80000000)')
print(f'M1[9]    = 0x{M1[9]:08x}')
print(f'M2[9]    = 0x{M2[9]:08x}  (M1[9] ^ 0x80000000)')
print()

# Check W1[57..60] from default schedule
W1 = schedule(M1)
W2 = schedule(M2)

print('Schedule check:')
all_match = True
for k in [57, 58, 59, 60]:
    cert_w1 = W1_cert[k]
    cert_w2 = W2_cert[k]
    actual_w1 = W1[k]
    actual_w2 = W2[k]
    match_1 = (cert_w1 == actual_w1)
    match_2 = (cert_w2 == actual_w2)
    if not (match_1 and match_2): all_match = False
    print(f'  W1[{k}]: cert=0x{cert_w1:08x}  schedule=0x{actual_w1:08x}  match={match_1}')
    print(f'  W2[{k}]: cert=0x{cert_w2:08x}  schedule=0x{actual_w2:08x}  match={match_2}')

print()
print(f'Schedule matches cert? {all_match}')
print()

# Run SHA-256 forward through round 60 for both, check for collision at slot 61
def run_through(W, k_target):
    state = list(IV)
    for r in range(k_target):
        state = sha_round(state, K[r], W[r])
    return state

state1_at_61 = run_through(W1, 61)  # state after rounds 0..60
state2_at_61 = run_through(W2, 61)

print('State at slot 61 (after rounds 0..60):')
print('  M1:', [f'0x{x:08x}' for x in state1_at_61])
print('  M2:', [f'0x{x:08x}' for x in state2_at_61])

state_match_at_61 = (state1_at_61 == state2_at_61)
print(f'sr=60 (rounds 0..60 collide): state[slot 61] M1==M2? {state_match_at_61}')

# Compare differences component by component
diffs = [(state1_at_61[i] ^ state2_at_61[i]) for i in range(8)]
print(f'XOR diffs: {[hex(d) for d in diffs]}')
print(f'Components matching (diff=0): {sum(1 for d in diffs if d == 0)}/8')

# Run all 64 rounds for full hash
state1_64 = run_through(W1, 64)
state2_64 = run_through(W2, 64)

# Final hash = IV + state mod 2^32 (Davies-Meyer)
final1 = [(IV[i] + state1_64[i]) & MASK for i in range(8)]
final2 = [(IV[i] + state2_64[i]) & MASK for i in range(8)]
hash1 = b''.join(struct.pack('>I', x) for x in final1).hex()
hash2 = b''.join(struct.pack('>I', x) for x in final2).hex()

print(f'\nFinal hash (compression output, IV + state[64]):')
print(f'  M1: {hash1}')
print(f'  M2: {hash2}')
print(f'Cert hash: ba6287f0dcaf9857d89ad44a6cced1e2adf8a242524236fbc0c656cd50a7e23b')
print(f'M1 hash matches cert? {hash1 == "ba6287f0dcaf9857d89ad44a6cced1e2adf8a242524236fbc0c656cd50a7e23b"}')
print(f'M1 == M2 hash? {hash1 == hash2}  (FALSE expected since rounds 61-63 not collided)')
