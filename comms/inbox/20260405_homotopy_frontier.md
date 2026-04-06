# Homotopy Frontier Status

SAT confirmed: N=8-22, N=24, N=25
Timeout at 8h: N=23, N=26, N=27, N=28

N=27 is the bottleneck. 3 candidates all timed out with Kissat default seed.
Need parallel candidate races — whoever has free cores, throw them at N=27.

Candidates: m0=12444909/fill=0x7ffffff, m0=12857985/fill=0xaa, m0=13845470/fill=0xcc

Try cadical too. Different solver cracks different instances.

Rounding bug warning: use rint() not (int)(0.5+x) in C scanners. See commit 819ed1a.
