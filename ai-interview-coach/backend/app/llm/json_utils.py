from __future__ import annotations

import json
import re
from collections.abc import Awaitable, Callable
from typing import Any


def extract_json_object(text: str) -> str | None:
    if not text:
        return None

    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL | re.IGNORECASE)
    if fenced:
        return fenced.group(1)

    start = text.find("{")
    if start == -1:
        return None

    depth = 0
    in_string = False
    escape = False
    for idx in range(start, len(text)):
        char = text[idx]
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : idx + 1]
    return None


async def parse_json_or_repair(
    text: str,
    repair_fn: Callable[[str], Awaitable[str]] | None = None,
) -> dict[str, Any]:
    candidate = extract_json_object(text) or text
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        if repair_fn is None:
            raise

    repaired = await repair_fn(text)
    repaired_candidate = extract_json_object(repaired) or repaired
    return json.loads(repaired_candidate)
