# GPU Kernel Sweep — N=8

Date: 2026-04-12 22:12 UTC
Device: NVIDIA GeForce RTX 4070 Laptop GPU

| Bit | M[0] | Fill | Collisions | log2 | Time |
|-----|------|------|-----------|------|------|
| 0 | 0x3d | 0x7f | 180 | 7.49 | 98s |
| 1 | 0x72 | 0xff | 299 | 8.22 | 102s |
| 2 | 0x7a | 0x0 | 307 | 8.26 | 102s |
| 3 | 0xfc | 0xff | 133 | 7.06 | 155s |
| 4 | 0x32 | 0xff | 10 | 3.32 | 142s |
| 5 | 0xa9 | 0xff | 324 | 8.34 | 103s |
| 6 | 0x12 | 0xff | 1644 | 10.68 | 103s |
| 7 | 0x67 | 0xff | 260 | 8.02 | 101s |

Best: bit 6 (1644 collisions)
