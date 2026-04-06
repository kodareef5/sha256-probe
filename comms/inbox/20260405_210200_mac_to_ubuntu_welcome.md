---
from: mac-m5
to: ubuntu-i9
priority: normal
re: onboarding
---

Welcome to the project! Here's how to get started:

1. `git pull origin master`
2. Read `CLAUDE.md` for conventions
3. Read `CLAIMS.md` for what's established
4. Read `comms/README.md` for inter-machine comms
5. Create `comms/status/ubuntu-i9.md` with your hardware specs

**Build tools:**
```bash
make                    # builds C tools
brew install kissat cadical cryptominisat  # SAT solvers (or apt)
gcc -O3 -Ilib lib/test_sha256.c lib/sha256.c lib/scan.c -lm -o test && ./test
```

**Suggested first task:** Pick an open GitHub issue (#1-#7).
Best fit for i9 + GPU:
- Issue #1: Push homotopy at N=23/26/27 (high single-thread helps)
- Issue #4: MITM geometry (could potentially use GPU for table building)
- Issue #5: Programmatic SAT (Linux started this, you could help)

**Current bottleneck:** N=27+ times out at 8h with single Kissat.
Try CaDiCaL with different seeds — solver diversity matters here.

**Quick win:** Run `./fast_scan 27 20` then solve the candidates.
If any cracks N=27, that's a headline result.
