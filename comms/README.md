# Inter-Machine Communication

Git-based message passing between Claude instances on different machines.
Check on every `git pull`. Act on messages addressed to you.

## How It Works

1. **Check inbox** at session start and after every pull
2. **Read messages** addressed to you (or `all`)
3. **Act** on requests, update your status
4. **Move processed messages** to `comms/read/` (or just leave them — inbox is append-only)
5. **Send messages** by creating files in `comms/inbox/`
6. **Update your status** in `comms/status/<machine>.md`

## Message Format

Filename: `YYYYMMDD_HHMMSS_<from>_to_<to>_<subject>.md`

```markdown
---
from: mac-m5
to: linux-24core     # or "all" or "ubuntu-i9"
priority: normal     # normal | urgent | fyi
re: q1/homotopy      # which workstream
---

Your message here. Be specific about what you need.
```

## Conventions

- **Check inbox on every pull.** This is how agents discover work.
- `to: all` = broadcast to every machine
- `priority: urgent` = act on this before starting new work
- Include machine name in commit messages: `[mac] ...`, `[linux] ...`, `[ubuntu] ...`
- Keep messages short and actionable
- Update your status board after significant events

## Machine Registry

| Name | Hardware | Cores | RAM | Strengths |
|------|----------|-------|-----|-----------|
| mac-m5 | Apple M5 | 10 | 16GB | Homotopy frontier, fast iteration |
| linux-24core | Linux server | 24 | 125GB | Heavy parallel, overnight batches |
| ubuntu-i9 | i9 + RTX 4070 | ? | ? | GPU potential, high single-thread |

## Status Boards

Each machine maintains `comms/status/<name>.md` with:
- What's currently running
- What's queued
- Recent findings
- Available capacity
