# overnight_kissat — concurrent kissat dispatcher for Apple Silicon

Tight-C work-queue runner that drives N parallel kissat workers across a
TSV-formatted queue of (CNF, seed, conflicts) jobs. Designed for Apple
Silicon with sustained multi-core load.

## Files

- `dispatcher.c` — main C runner. fork+exec kissat children, atomic queue
  pop via flock, parse status, append to `results.tsv`, refill workers
  on completion. Signal-clean shutdown on SIGINT/SIGTERM.
- `build_queue.py` — produces `work_queue.tsv` from registry + cnfs_n32/
  + prior runs.jsonl. 4 phases:
    - **A**: 6 distinguished cands × 8 fresh seeds × 100M conflicts (broad)
    - **B**: 6 distinguished × 5 seeds × 1B conflicts (deep, hits time cap)
    - **C**: ~61 other cnfs_n32 cands × 1 seed × 100M (registry breadth)
    - **D**: top 2 cands × 3 seeds × 5B conflicts (very deep)
- `log_results.py` — converts `results.tsv` → `runs.jsonl` entries via
  `infra/append_run.py`. Run after dispatcher finishes.
- `run_overnight.sh` — entry point: build queue → audit → dispatcher →
  log → dashboard refresh.

## Compile

```
gcc -O3 -march=native -o dispatcher dispatcher.c
```

## Run

```
# Build queue + smoke audit (light)
python3 build_queue.py --phase all --out work_queue.tsv

# Launch
nohup ./dispatcher work_queue.tsv 6 --time-cap-sec 1800 > overnight.log 2>&1 &

# Or full orchestration via shell wrapper
nohup bash run_overnight.sh > overnight.log 2>&1 &
```

## Watch

- `tail -f overnight.log` — dispatcher LAUNCH/FINISH events.
- `cat results.tsv` — per-run summary (8 columns: ts, run_id, cnf, seed,
  conflicts, status, wall, tag).
- `cat work_queue.tsv | awk '{print $1}' | sort | uniq -c` — queue state.
- `ls logs/ | wc -l` — completed runs count.

## Stop

```
kill <DISPATCH_PID>      # SIGTERM, drains gracefully (5s grace, then SIGKILL)
```

## Interpreting status

- `s SAT` — collision found (HEADLINE!)
- `s UNSAT` — proven no collision (HEADLINE — sr=61 impossibility for cand)
- `s UNKNOWN` — neither, hit conflict or time cap

`results.tsv` normalizes to `SAT`, `UNSAT`, `UNKNOWN`. `log_results.py`
maps `UNKNOWN` → `TIMEOUT` for `runs.jsonl` schema.

## Tuning

- **`--time-cap-sec`**: hard wall cap per kissat invocation. Default 1800s.
  Set lower for fast turnover, higher for deep search.
- **N workers**: pick based on M5/M-series core count. 6 is a good default
  on M5 (10 cores; leave 4 for system/IO).

## Discipline

- Every CNF audited via `infra/audit_cnf.py` before any run (use
  `run_overnight.sh` for full audit pre-dispatch, or spot-audit + trust
  `cnfs_n32/` as previously bulk-CONFIRMED).
- Every run logged via `log_results.py` → `infra/append_run.py`.
- Dashboard refreshed via `infra/summarize_runs.py` post-batch.

## Architecture notes

- Queue uses flock-based atomic line-pop. Robust under N concurrent workers.
- Worker stderr+stdout redirected per-run to `logs/run_NNNNN.log`.
- Dispatcher loops until queue empty AND all workers idle.
- Time cap is enforced via kissat's own `--time=N` flag (kissat-internal).
- No DRAT proof generation by default (overnight is for SAT search, not
  UNSAT proof). Add `--proof=...` flag manually if needed.
