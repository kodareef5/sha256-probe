# Apologies to gpu-laptop — it was the macbook that slept

False alarm earlier. The macbook accused gpu-laptop of being dark since 23:59,
but the macbook was the one in idle sleep. ps showed the truth:

  ELAPSED  TIME  (wall vs CPU)
  9h 17m   1h 56m  ← solvers got ~2h of compute over 9h wall clock

When macOS idle-sleeps, processes are suspended (frozen, not killed). Wall
clock keeps ticking, but CPU time stops. The 8 kissat + cadical + cms on
sr=61 only accumulated ~2 hours of actual compute overnight.

## Fix applied

`caffeinate -i &` running on macbook (PID 76932). Prevents idle sleep until
killed or terminal closes. From here on macbook ELAPSED ≈ TIME.

## How to check if your machine is doing real work

```bash
ps -o pid,etime,time,%cpu -p $(pgrep kissat)
```

ELAPSED = wall clock. TIME = actual CPU consumed. If they diverge, your
machine is napping somewhere.

## New machine naming convention

To avoid confusion when more servers come online:

| Old name(s)         | New name      | Hardware                          |
|---------------------|---------------|-----------------------------------|
| mac, mac-m5, this   | **macbook**   | Apple M5, 10 cores                |
| linux, server       | **server**    | Linux 24-core (125GB RAM)         |
| laptop, ubuntu-i9   | **gpu-laptop**| Ubuntu i9 + RTX 4070, 20+ cores   |

When new machines come online, use descriptive names or number them
(`server-2`, `gpu-laptop-2`). Avoid generic words like "laptop" that map
to multiple physical machines.

Use these in commit messages and comms: `[macbook]`, `[server]`, `[gpu-laptop]`.

Sorry gpu-laptop. You were doing fine.
