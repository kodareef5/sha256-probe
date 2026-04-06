# Mac joining N=32 race

10 cores now running N=32:
- 0x17149975 (fill=0xffffffff) × 5 seeds (1-5)
- 0xa22dc6c7 (fill=0xffffffff) × 5 seeds (1-5)

These are the same candidates Linux has but with Kissat seeds 1-5
(Linux is running default seed + CaDiCaL). Seed diversity gives
independent search trajectories at zero cost.

Couldn't build CaDiCaL-SHA256 on macOS (build errors in sha256/operations.cpp).
Linux has it working — that's the higher-impact solver to try.

Between all 3 machines: ~54 solver instances on N=32.
If any one cracks it, we have an sr=60 collision at full SHA-256 width.
