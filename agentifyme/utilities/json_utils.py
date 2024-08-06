import json
import re
from typing import Any, Dict


def extract_json(text: str) -> Dict[str, Any] | None:
    """
    Extracts the first JSON object from the given text, handling Markdown-style code blocks,
    single-quoted JSON, and escaped quotes.

    Args:
        text (str): The input text containing JSON data.

    Returns:
        dict: The parsed JSON object, or None if no JSON object is found.
    """
    # Remove Markdown code block delimiters if present
    text = re.sub(r"```(?:json)?\n?(.*?)\n?```", r"\1", text, flags=re.DOTALL)

    # Regular expression to match JSON objects (now including single quotes)
    json_pattern = re.compile(r"\{(?:[^{}]|(?:\{(?:[^{}]|(?:\{[^{}]*\}))*\}))*\}")
    json_match = json_pattern.search(text)
    if json_match:
        try:
            json_str = json_match.group()
            # If the string is already valid JSON, parse it directly
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                # If it's not valid JSON, apply our transformations
                # Replace single quotes with double quotes, but not within string values or escaped
                json_str = re.sub(
                    r"(?<![\\])(')((?:\\.|[^\\'])*?)(?<![\\])(')", r'"\2"', json_str
                )
                # Replace any remaining unescaped single quotes
                json_str = re.sub(r"(?<![\\])'", '"', json_str)
                # Replace 'true', 'false', and 'null' with their JSON equivalents
                json_str = re.sub(r"\btrue\b", "true", json_str)
                json_str = re.sub(r"\bfalse\b", "false", json_str)
                json_str = re.sub(r"\bnull\b", "null", json_str)
                # Parse the JSON object
                return json.loads(json_str)
        except json.JSONDecodeError:
            # If parsing fails, return None
            return None
    return None
