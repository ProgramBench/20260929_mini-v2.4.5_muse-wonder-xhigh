# Muse Wonder (xhigh) — ProgramBench submission

- **Model:** Muse Wonder, reasoning effort **xhigh**, max 65,536 output tokens per call
- **Scaffold:** mini-SWE-agent v2.4.5 (single-agent), open source; step limit 1,000, no cost
  limit, 6 h wall-time limit
- **Protocol:** no-internet + `task_cleanroom_v6` images. The agent sees only the compiled binary
  (source removed, `.git` reset), reimplements it from scratch by interacting with it, and never
  has network access (`--network none` at the container level).
- **Score:** 0.865 (mean per-instance test pass-rate over the fixed 200, missing = 0; the
  leaderboard recomputes authoritatively from `_stats/score.json`). Only tests listed in the
  benchmark's `tests.json` are scored.
- **Inference dates:** 2026-09-29 to 2026-09-30

## Task accounting

199 tasks are evaluated and included here; the other one produced no gradeable submission and
scores 0.

## Extra stats

Cost, model-call, and output-token statistics are generated from the published trajectories by
the scripts under `_scripts/`.

Cost uses muse-wonder-1.0's rates of $4.00 per million uncached input tokens, $0.20 per
million cached input tokens, and $20.00 per million output tokens. `_scripts/calculate_cost.py`
treats each call's previous prompt as its cacheable prefix and charges it as cached at a
99.15% hit rate.

## Redactions

Plaintext reasoning (`reasoning_content`) is removed from every trajectory; the opaque
`reasoning_id`s are kept. Credential fields in the harness config are replaced with
`[REDACTED]`. Model and tool turns are otherwise unmodified.

Each test is run up to 3× (pytest-rerunfailures); only the final attempt is scored (flakiness defense).
