# Kernel Sweep at N=4: MSB is NOT Optimal — Bit-1 gives 3x more collisions!

## Result

| Kernel bit | Fill | m0 | Collisions |
|-----------|------|-----|-----------|
| **1** | **0x0** | **0x3** | **146** |
| 1 | 0xa | 0xc | 69 |
| 3 (MSB) | 0xf | 0x0 | 49 |
| 0 (LSB) | 0x0 | 0x1 | 44 |
| 0 (LSB) | 0xf | 0x3 | 27 |
| 3 (MSB) | 0x0 | 0x1 | 22 |
| 2 | 0xf | 0x7 | 17 |
| 3 (MSB) | 0xa | 0xe | 11 |
| 1 | 0xf | 0x5 | 1 |

## Key finding

**Bit-1 kernel with fill=0x0 produces 146 collisions — 2.98x more than
the MSB kernel's 49.** The MSB kernel is NOT optimal at N=4.

## Implications

1. The MSB kernel was chosen by convention (Viragh's original paper),
   not by optimization. Other kernels may be dramatically better.

2. At N=32, the bit-1 kernel (dM=0x00000002) or another non-MSB kernel
   might have MANY more collisions than the MSB's predicted 2^{33.5}.

3. The SCALING LAW depends on the kernel — different kernels will give
   different collision counts at each N.

4. **For sr=61:** a different kernel might push the boundary! The sigma1
   conflict rate depends on the kernel structure.

## Evidence level: VERIFIED (exhaustive cascade DP at N=4)
