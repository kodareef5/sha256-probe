# N=30 is massive

N=30 SAT means we're 2 bits away from full SHA-256. The scaling from N=25 to N=30:
- N=25: ~87min
- N=27: 2.9h  
- N=28: 3.1h
- N=30: 8.5h

That's roughly 2x per 2 bits. N=32 extrapolation: ~34h from N=30, or ~19h from the full fit.

With the GPU+SAT pipeline and programmatic SAT, N=32 might actually be reachable
on the 24-core server in a dedicated multi-day run.

N=29 and N=31 are solving. If those come in, we'll have SAT at every N from 8 to 31.
That would make the "sr=60 is fundamentally impossible" claim untenable.

The paper's thermodynamic floor was always about one candidate family. We've now
shown that with enough candidate diversity and compute, sr=60 yields at every
tested word width up to N=30.
