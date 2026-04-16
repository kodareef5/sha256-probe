# N=12 Candidate Census (all kernel bits × 6 fills)

Candidates per (kernel_bit, fill) combo:

| Bit | fff | 000 | 7ff | 800 | 055 | 0aa | Total |
|-----|-----|-----|-----|-----|-----|-----|-------|
| 0   | 0   | 0   | 1   | 2   | 1   | 1   | 5     |
| **1** | 0 | 0 | 0 | 1 | 1 | **2** | **4** (8826 winner) |
| 2   | 0   | 0   | 0   | 0   | 1   | 0   | 1     |
| 3   | 1   | 0   | 2   | 1   | 2   | 0   | 6     |
| 4   | 2   | 0   | 1   | 0   | 3   | **3** | **9** (most fill=0aa!) |
| 5   | 2   | 3   | 0   | 0   | 1   | 1   | 7     |
| 6   | 1   | 0   | 3   | 1   | 0   | 0   | 5     |
| **7** | 1 | 1 | 1 | 2 | 1 | **3** | **9** |
| 8   | 0   | 1   | 2   | 2   | 1   | 0   | 6     |
| 9   | 0   | 2   | 1   | 0   | 0   | 0   | 3     |
| 10  | 3   | 1   | 0   | 1   | 0   | 1   | 6     |
| 11  | 1   | 2   | 0   | 2   | 0   | 0   | 5     |

## Unexplored Promising Configurations

Bits 4 and 7 have the MOST fill=0x0aa candidates (3 each). If fill=0x0aa
is universally powerful, bit 4 and bit 7 could potentially BEAT bit 1.

## GPU Time Estimate
Full kernel sweep at N=12: 12 bits × ~5 candidates × 13h = ~780h = ~32 days
Just fill=0x0aa candidates: ~13 candidates × 13h = ~170h = 1 week

Too long for current session. Priority: test bit 4 and bit 7 fill=0x0aa
when GPU frees up (after current MSB sweep completes in ~65h).
