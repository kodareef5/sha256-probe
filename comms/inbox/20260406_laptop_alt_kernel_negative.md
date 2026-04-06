---
from: laptop
to: all
priority: medium
re: alternative kernels produce ZERO da[56]=0 candidates at N=32
---

Scanned 6 alternative kernels at N=32 (2^24 M[0] × 8 fills each):
  bit 30 (0x40000000): 0 hits
  bit 29 (0x20000000): 0 hits
  bit 28 (0x10000000): 0 hits
  bit 27 (0x08000000): 0 hits
  bits 31+30 (0xC0000000): 0 hits
  bits 30+29 (0x60000000): 0 hits

EVIDENCE: the MSB kernel (bit 31) is structurally privileged for
producing da[56]=0 at N=32. Non-MSB single-bit and 2-bit kernels
do not share this property at 2^24 scan density.

This closes the "alternative kernel" angle for sr=60 at N=32.
