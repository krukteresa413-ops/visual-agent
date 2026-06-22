"""Shared LLM utilities — JSON parsing from LLM responses."""
import json
import re


def parse_json(raw: str) -> dict:
    """Extract JSON from LLM response (may have markdown fences or stray text).

    Tries in order:
    1. Direct JSON parse
    2. Extract from ```json fences
    3. Extract first { ... } block
    """
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    match = re.search(r"```(?:json)?\s*(.*?)\s*```", raw, re.DOTALL)
    if match:
        return json.loads(match.group(1))

    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        return json.loads(match.group(0))

    raise ValueError(f"Could not parse JSON from LLM response: {raw[:200]}")
