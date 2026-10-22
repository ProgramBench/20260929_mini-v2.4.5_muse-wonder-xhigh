#!/usr/bin/env python3
"""Write `_stats/cost.json` at muse-wonder-1.0's published USD/Mtok rates.

Each call's cacheable prefix is the previous call's prompt when the prompt grew (0 for the
first call or when it shrank). That prefix is charged as cached at a 99.15% hit rate; all
other input is charged as uncached.
"""

import json
from pathlib import Path

RUN_DIR = Path(__file__).resolve().parent.parent
TOKENS_PER_MILLION = 1_000_000
INPUT_USD_PER_MILLION = 4.00
CACHED_INPUT_USD_PER_MILLION = 0.20
OUTPUT_USD_PER_MILLION = 20.00
PREFIX_CACHE_HIT_RATE = 60_963_731_212 / 61_488_219_465


def _usage_of(msg: dict) -> dict | None:
    response = (msg.get("extra") or {}).get("response")
    if isinstance(response, dict) and isinstance(response.get("usage"), dict):
        return response["usage"]
    if isinstance(msg.get("usage"), dict):
        return msg["usage"]
    return None


def cost_from_traj(traj: dict) -> tuple[float, int, float, int] | None:
    uncached_input = 0
    cached_input = 0.0
    output = 0
    previous_prompt: int | None = None
    found = False

    for msg in traj.get("messages", []):
        usage = _usage_of(msg)
        if not usage:
            continue
        prompt = usage.get("prompt_tokens", usage.get("input_tokens"))
        completion = usage.get("completion_tokens", usage.get("output_tokens"))
        if prompt is None or completion is None:
            raise ValueError("Incomplete token usage")
        if not isinstance(prompt, int) or not isinstance(completion, int) or min(prompt, completion) < 0:
            raise ValueError("Invalid token counts")
        details = usage.get("prompt_tokens_details") or usage.get("input_tokens_details") or {}
        if details.get("cached_tokens") is not None:
            raise ValueError("Unexpected recorded cache count")

        cacheable = previous_prompt if previous_prompt is not None and prompt >= previous_prompt else 0
        cached = cacheable * PREFIX_CACHE_HIT_RATE

        uncached_input += prompt - cached
        cached_input += cached
        output += completion
        previous_prompt = prompt
        found = True

    if not found:
        return None
    cost = (
        uncached_input * INPUT_USD_PER_MILLION
        + cached_input * CACHED_INPUT_USD_PER_MILLION
        + output * OUTPUT_USD_PER_MILLION
    ) / TOKENS_PER_MILLION
    return cost, uncached_input, cached_input, output


cost = {}
totals = {"uncached_input": 0, "cached_input": 0, "output": 0}
for traj in sorted(RUN_DIR.glob("[!_]*/*.traj.json")):
    value = cost_from_traj(json.loads(traj.read_text()))
    if value is not None:
        amount, uncached_input, cached_input, output = value
        cost[traj.parent.name] = amount
        totals["uncached_input"] += uncached_input
        totals["cached_input"] += cached_input
        totals["output"] += output

scored = json.loads((RUN_DIR / "_stats" / "score.json").read_text())
if set(cost) != set(scored):
    raise ValueError("Cost coverage differs from scored instances")

(RUN_DIR / "_stats").mkdir(exist_ok=True)
(RUN_DIR / "_stats" / "cost.json").write_text(json.dumps(cost, indent=2, sort_keys=True))
print(f"Wrote _stats/cost.json for {len(cost)} instance(s)")
print(
    f"Usage: uncached_input={totals['uncached_input']:,.0f}, "
    f"cached_input={totals['cached_input']:,.0f}, output={totals['output']:,}; "
    f"total_cost=${sum(cost.values()):,.6f}"
)
