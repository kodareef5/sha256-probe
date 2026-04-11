# CASCADE CHAIN DETERMINES ALL W2 WORDS

At N=4, for each W1[57]:
- W2[57] = W1[57] + C_57 (universal constant)
- W2[58] = W1[58] + C_58(W1[57]) (depends on W1[57] only)
- W2[59] = W1[59] + C_59(W1[57], W1[58]) (depends on W1[57] and W1[58])

The entire second message is DETERMINED by the first message
plus cascade constants. Search is over W1 only: 2^(4N) not 2^(8N).

At N=4: 2^16 = 65536 candidates (vs 2^32 = 4.3B brute force)
Speedup: 65536x

This is the CONSTRUCTIVE cascade chain: the cascade mechanism not only
zeros register differences, but also computes the message word offsets.
