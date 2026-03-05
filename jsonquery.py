#!/usr/bin/env python3
"""
JSONQuery v1.0.0 - Smart JSON Query & Filter Tool
==================================================

Query, filter, search, and transform JSON data from files or stdin
using simple path expressions. Zero external dependencies.

Part of the Holy Grail Automation Toolkit - Team Brain
Built by: ATLAS (Cursor IDE - Claude Sonnet)
For: Logan Smith / Metaphy LLC

Usage:
    jsonquery get data.json "$.users[0].name"
    jsonquery filter data.json "$.users" "age>18"
    jsonquery search data.json "admin"
    jsonquery pretty data.json
    cat data.json | jsonquery get - "$.count"

Exit Codes:
    0 = Success / match found
    1 = No match / empty result
    2 = Error (bad JSON, invalid path, file not found)
"""

import argparse
import csv
import io
import json
import os
import re
import sys
import statistics
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# =============================================================
# SECTION 1: Constants & Version
# =============================================================

VERSION = "1.0.0"
TOOL_NAME = "JSONQuery"
AUTHOR = "ATLAS (Team Brain)"
FOR = "Logan Smith / Metaphy LLC"
GITHUB = "https://github.com/DonkRonk17/JSONQuery"

CONFIG_DIR = Path.home() / ".jsonquery"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_CONFIG = {
    "default_format": "pretty",
    "color": True,
    "indent": 2,
    "null_ok": False,
}

# =============================================================
# SECTION 2: Color / ANSI Utilities
# =============================================================

class Colors:
    """ANSI color codes. Auto-disabled when not a TTY or on unsupported terminals."""
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    # Foreground colors
    RED     = "\033[31m"
    GREEN   = "\033[32m"
    YELLOW  = "\033[33m"
    BLUE    = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN    = "\033[36m"
    WHITE   = "\033[37m"
    BRIGHT_RED    = "\033[91m"
    BRIGHT_GREEN  = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE   = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN   = "\033[96m"
    BRIGHT_WHITE  = "\033[97m"


def _color_enabled() -> bool:
    """Check if color output is supported."""
    if not sys.stdout.isatty():
        return False
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("TERM") == "dumb":
        return False
    # Windows: enable ANSI on Win10+
    if os.name == "nt":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
            return True
        except Exception:
            return False
    return True


_COLOR_SUPPORTED = _color_enabled()


def colorize(text: str, *codes: str, enabled: bool = True) -> str:
    """Wrap text in ANSI color codes if color is enabled."""
    if not enabled or not _COLOR_SUPPORTED:
        return text
    return "".join(codes) + text + Colors.RESET


def color_json(obj: Any, indent: int = 2, enabled: bool = True) -> str:
    """Pretty-print JSON with syntax highlighting."""
    raw = json.dumps(obj, indent=indent, ensure_ascii=False)
    if not enabled or not _COLOR_SUPPORTED:
        return raw

    lines = []
    for line in raw.splitlines():
        stripped = line.rstrip()
        # Detect indent level (preserve leading whitespace)
        leading = len(stripped) - len(stripped.lstrip())
        prefix = " " * leading
        content = stripped.lstrip()

        # Key: value pattern
        key_val_match = re.match(r'^("(?:[^"\\]|\\.)*")\s*:\s*(.*)', content)
        if key_val_match:
            key_part = key_val_match.group(1)
            val_part = key_val_match.group(2)
            colored_key = colorize(key_part, Colors.CYAN, enabled=enabled)
            colored_val = _colorize_value(val_part, enabled=enabled)
            lines.append(f"{prefix}{colored_key}: {colored_val}")
        else:
            colored = _colorize_value(content, enabled=enabled)
            lines.append(f"{prefix}{colored}")

    return "\n".join(lines)


def _colorize_value(s: str, enabled: bool = True) -> str:
    """Apply color to a JSON value string."""
    if not enabled:
        return s
    s_stripped = s.rstrip(",").strip()
    if s_stripped in ("true", "false"):
        return colorize(s, Colors.BRIGHT_BLUE, enabled=enabled)
    if s_stripped == "null":
        return colorize(s, Colors.DIM + Colors.RED, enabled=enabled)
    if s_stripped.startswith('"'):
        return colorize(s, Colors.BRIGHT_GREEN, enabled=enabled)
    if re.match(r"^-?\d", s_stripped):
        return colorize(s, Colors.BRIGHT_YELLOW, enabled=enabled)
    if s_stripped in ("{", "}", "[", "]", "{}", "[]"):
        return colorize(s, Colors.WHITE, enabled=enabled)
    return s


# =============================================================
# SECTION 3: Exceptions
# =============================================================

class JSONQueryError(Exception):
    """Base exception for JSONQuery errors."""
    pass


class PathError(JSONQueryError):
    """Invalid or unresolvable path expression."""
    pass


class FilterError(JSONQueryError):
    """Invalid filter condition syntax."""
    pass


class InputError(JSONQueryError):
    """Invalid input (bad JSON, file not found, etc.)."""
    pass


# =============================================================
# SECTION 4: JSON Loading
# =============================================================

def load_json(source: str) -> Any:
    """
    Load JSON from a file path or stdin ('-').
    Returns parsed JSON data.
    Raises InputError on failure.
    """
    try:
        if source == "-":
            content = sys.stdin.read()
            try:
                return json.loads(content)
            except json.JSONDecodeError as e:
                raise InputError(f"Invalid JSON from stdin: {e}")
        else:
            path = Path(source)
            if not path.exists():
                raise InputError(f"File not found: '{source}'")
            if not path.is_file():
                raise InputError(f"Not a file: '{source}'")
            try:
                content = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                content = path.read_text(encoding="latin-1")
            try:
                return json.loads(content)
            except json.JSONDecodeError as e:
                raise InputError(
                    f"Invalid JSON in '{source}': {e}\n"
                    f"  Tip: Use 'jsonquery validate {source}' for details"
                )
    except InputError:
        raise
    except OSError as e:
        raise InputError(f"Cannot read '{source}': {e}")


# =============================================================
# SECTION 5: JSONPathEvaluator
# =============================================================

class JSONPathEvaluator:
    """
    Evaluate simplified JSONPath expressions against JSON data.

    Supports:
        $               Root element
        $.key           Object key
        $.a.b.c         Nested keys
        $.arr[0]        Array index
        $.arr[-1]       Last element
        $.arr[*]        All elements (returns list)
        $.arr[0:3]      Slice
        $..key          Recursive descent
        $[0]            Root is array
    """

    def evaluate(self, data: Any, path: str) -> Any:
        """
        Evaluate a path expression against data.
        Returns the matched value(s).
        Raises PathError on invalid path or missing key.
        """
        if not path.startswith("$"):
            raise PathError(f"Path must start with '$': '{path}'")

        path_body = path[1:]  # Remove leading $

        if not path_body or path_body == ".":
            return data

        # Tokenize
        tokens = self._tokenize(path_body)
        return self._walk(data, tokens, path)

    def _tokenize(self, path_body: str) -> List[str]:
        """Convert path string to list of tokens."""
        tokens = []
        remaining = path_body

        while remaining:
            # Recursive descent: ..key
            if remaining.startswith(".."):
                remaining = remaining[2:]
                # Grab next key
                m = re.match(r"^([A-Za-z0-9_\-@#]+)(.*)", remaining)
                if m:
                    tokens.append(f"..{m.group(1)}")
                    remaining = m.group(2)
                else:
                    raise PathError(f"Invalid recursive descent in path: '{remaining}'")

            # Dot notation: .key
            elif remaining.startswith("."):
                remaining = remaining[1:]
                m = re.match(r"^([A-Za-z0-9_\-@#]+)(.*)", remaining)
                if m:
                    tokens.append(m.group(1))
                    remaining = m.group(2)
                elif remaining.startswith("["):
                    pass  # Will be handled as bracket next iteration
                else:
                    # Wildcard .*
                    if remaining.startswith("*"):
                        tokens.append("*")
                        remaining = remaining[1:]
                    else:
                        raise PathError(f"Invalid path segment: '{remaining}'")

            # Bracket notation: [key], [0], [*], [0:3], [-1]
            elif remaining.startswith("["):
                m = re.match(r"^\[([^\]]+)\](.*)", remaining)
                if m:
                    bracket_content = m.group(1).strip()
                    tokens.append(f"[{bracket_content}]")
                    remaining = m.group(2)
                else:
                    raise PathError(f"Unclosed bracket in path: '{remaining}'")

            else:
                raise PathError(f"Unexpected character in path: '{remaining}'")

        return tokens

    def _walk(self, data: Any, tokens: List[str], original_path: str) -> Any:
        """Recursively walk the data tree following tokens."""
        current = data

        for i, token in enumerate(tokens):
            remaining_tokens = tokens[i + 1:]

            # Recursive descent
            if token.startswith(".."):
                key = token[2:]
                results = self._recursive_descent(current, key)
                if not results:
                    return None
                if remaining_tokens:
                    all_results = []
                    for r in results:
                        try:
                            sub = self._walk(r, remaining_tokens, original_path)
                            if isinstance(sub, list):
                                all_results.extend(sub)
                            elif sub is not None:
                                all_results.append(sub)
                        except PathError:
                            pass
                    return all_results if all_results else None
                return results if len(results) > 1 else results[0]

            # Wildcard
            elif token == "*":
                if isinstance(current, dict):
                    values = list(current.values())
                elif isinstance(current, list):
                    values = current
                else:
                    raise PathError(f"Cannot apply wildcard to {type(current).__name__}")
                if remaining_tokens:
                    all_results = []
                    for v in values:
                        try:
                            sub = self._walk(v, remaining_tokens, original_path)
                            if isinstance(sub, list):
                                all_results.extend(sub)
                            elif sub is not None:
                                all_results.append(sub)
                        except PathError:
                            pass
                    return all_results
                return values

            # Bracket notation
            elif token.startswith("["):
                bracket_content = token[1:-1].strip()
                result = self._apply_bracket(current, bracket_content, original_path)
                if result is None:
                    return None
                # Wildcard or slice bracket returns a list - fan out to remaining tokens
                is_fanout = bracket_content in ("*",) or ":" in bracket_content
                if is_fanout and isinstance(result, list) and remaining_tokens:
                    all_results = []
                    for item in result:
                        try:
                            sub = self._walk(item, remaining_tokens, original_path)
                            if isinstance(sub, list):
                                all_results.extend(sub)
                            elif sub is not None:
                                all_results.append(sub)
                        except PathError:
                            pass
                    return all_results if all_results else None
                current = result
                # Continue the loop for remaining tokens

            # Simple key
            else:
                if isinstance(current, dict):
                    if token not in current:
                        return None
                    current = current[token]
                elif isinstance(current, list):
                    # Apply key to each element in list (implicit fan-out)
                    results = []
                    for item in current:
                        if isinstance(item, dict) and token in item:
                            results.append(item[token])
                    if not results:
                        return None
                    if remaining_tokens:
                        # Fan out to remaining tokens
                        all_results = []
                        for v in results:
                            try:
                                sub = self._walk(v, remaining_tokens, original_path)
                                if isinstance(sub, list):
                                    all_results.extend(sub)
                                elif sub is not None:
                                    all_results.append(sub)
                            except PathError:
                                pass
                        return all_results if all_results else (
                            results if len(results) > 1 else results[0]
                        )
                    current = results if len(results) > 1 else results[0]
                else:
                    raise PathError(
                        f"Cannot access key '{token}' on {type(current).__name__}"
                    )

        return current

    def _apply_bracket(self, data: Any, content: str, path: str) -> Any:
        """Apply bracket access: index, slice, wildcard, or string key."""
        # Wildcard [*]
        if content == "*":
            if isinstance(data, (list, dict)):
                return list(data.values()) if isinstance(data, dict) else data
            raise PathError(f"Cannot apply [*] to {type(data).__name__}")

        # Slice [start:end] or [start:end:step]
        if ":" in content:
            parts = content.split(":")
            try:
                start = int(parts[0]) if parts[0].strip() else None
                end = int(parts[1]) if len(parts) > 1 and parts[1].strip() else None
                step = int(parts[2]) if len(parts) > 2 and parts[2].strip() else None
            except ValueError:
                raise PathError(f"Invalid slice syntax: '[{content}]'")
            if not isinstance(data, list):
                raise PathError(f"Cannot slice {type(data).__name__}")
            return data[slice(start, end, step)]

        # String key in quotes ["key"]
        if content.startswith('"') and content.endswith('"'):
            key = content[1:-1]
            if isinstance(data, dict):
                return data.get(key)
            raise PathError(f"Cannot apply string key to {type(data).__name__}")

        # Integer index
        try:
            idx = int(content)
            if isinstance(data, list):
                try:
                    return data[idx]
                except IndexError:
                    return None
            raise PathError(f"Cannot index {type(data).__name__} with integer")
        except ValueError:
            pass

        # Plain key (no quotes)
        if isinstance(data, dict):
            return data.get(content)

        raise PathError(f"Invalid bracket content: '[{content}]'")

    def _recursive_descent(self, data: Any, key: str) -> List[Any]:
        """Find all values matching key at any depth using BFS."""
        results = []
        queue = [data]
        while queue:
            current = queue.pop(0)
            if isinstance(current, dict):
                if key in current:
                    results.append(current[key])
                for v in current.values():
                    if isinstance(v, (dict, list)):
                        queue.append(v)
            elif isinstance(current, list):
                for item in current:
                    if isinstance(item, (dict, list)):
                        queue.append(item)
        return results


# =============================================================
# SECTION 6: JSONFilter
# =============================================================

class JSONFilter:
    """
    Filter JSON arrays using condition expressions.

    Conditions:
        key=value       Exact match (string or number)
        key!=value      Not equal
        key>number      Numeric >
        key<number      Numeric <
        key>=number     Numeric >=
        key<=number     Numeric <=
        key~pattern     Contains (case-insensitive)
        key^pattern     Starts with
        key$pattern     Ends with
        key             Key exists and is truthy
        !key            Key absent or falsy
    """

    CONDITION_RE = re.compile(
        r"^(!?)([A-Za-z_][A-Za-z0-9_.\-]*)"
        r"(!=|>=|<=|>|<|=|~|\^|\$)?"
        r"(.*)$"
    )

    def apply(self, data: Any, condition: str) -> List[Any]:
        """Apply a filter condition to a list. Returns filtered list."""
        if not isinstance(data, list):
            raise FilterError(
                f"Filter requires an array, got {type(data).__name__}. "
                "Use a path that points to an array."
            )
        m = self.CONDITION_RE.match(condition.strip())
        if not m:
            raise FilterError(f"Invalid filter condition: '{condition}' (key must start with a letter or underscore)")

        negate = m.group(1) == "!"
        key = m.group(2)
        op = m.group(3)
        value = m.group(4)

        results = []
        for item in data:
            try:
                match = self._test(item, negate, key, op, value)
                if match:
                    results.append(item)
            except (TypeError, ValueError, KeyError):
                pass
        return results

    def _get_nested(self, item: Any, key: str) -> Any:
        """Get value from item, supporting dot-notation keys."""
        parts = key.split(".")
        current = item
        for part in parts:
            if isinstance(current, dict):
                if part not in current:
                    return None
                current = current[part]
            else:
                return None
        return current

    def _test(self, item: Any, negate: bool, key: str, op: Optional[str], value: str) -> bool:
        """Test a single item against the condition."""
        item_value = self._get_nested(item, key)

        # No operator: check existence/truthiness
        if op is None:
            result = item_value is not None and item_value is not False and item_value != ""
            return not result if negate else result

        str_val = str(item_value) if item_value is not None else ""

        if op == "=":
            # Boolean coercion: true/false strings match Python booleans
            if isinstance(item_value, bool):
                if value.lower() in ("true", "1", "yes"):
                    result = item_value is True
                elif value.lower() in ("false", "0", "no"):
                    result = item_value is False
                else:
                    result = False
            else:
                # Try numeric comparison first
                try:
                    result = float(item_value) == float(value)  # type: ignore[arg-type]
                except (TypeError, ValueError):
                    result = str_val == value
            return not result if negate else result

        if op == "!=":
            if isinstance(item_value, bool):
                if value.lower() in ("true", "1", "yes"):
                    result = item_value is not True
                elif value.lower() in ("false", "0", "no"):
                    result = item_value is not False
                else:
                    result = True
            else:
                try:
                    result = float(item_value) != float(value)  # type: ignore[arg-type]
                except (TypeError, ValueError):
                    result = str_val != value
            return not result if negate else result

        if op in (">", "<", ">=", "<="):
            # If value is None (key not present on item), skip gracefully
            if item_value is None:
                return False
            try:
                a = float(item_value)  # type: ignore[arg-type]
                b = float(value)
                if op == ">":
                    result = a > b
                elif op == "<":
                    result = a < b
                elif op == ">=":
                    result = a >= b
                else:
                    result = a <= b
            except (TypeError, ValueError):
                raise FilterError(
                    f"Operator '{op}' requires numeric values, "
                    f"got '{item_value}' and '{value}'"
                )
            return not result if negate else result

        if op == "~":
            result = value.lower() in str_val.lower()
            return not result if negate else result

        if op == "^":
            result = str_val.lower().startswith(value.lower())
            return not result if negate else result

        if op == "$":
            result = str_val.lower().endswith(value.lower())
            return not result if negate else result

        raise FilterError(f"Unknown operator: '{op}'")


# =============================================================
# SECTION 7: JSONSearcher
# =============================================================

class JSONSearcher:
    """
    Recursively search all keys and values in JSON data.
    Returns list of matches with path, key, value.
    """

    def search(
        self,
        data: Any,
        term: str,
        keys_only: bool = False,
        values_only: bool = False,
        use_regex: bool = False,
    ) -> List[Dict[str, Any]]:
        """Search data for term. Returns list of match dicts."""
        results: List[Dict[str, Any]] = []
        if use_regex:
            try:
                pattern = re.compile(term, re.IGNORECASE)
                matcher = lambda s: bool(pattern.search(str(s)))
            except re.error as e:
                raise FilterError(f"Invalid regex: '{term}': {e}")
        else:
            term_lower = term.lower()
            matcher = lambda s: term_lower in str(s).lower()

        self._search_recursive(data, "$", term, matcher, keys_only, values_only, results)
        return results

    def _search_recursive(
        self,
        obj: Any,
        path: str,
        term: str,
        matcher,
        keys_only: bool,
        values_only: bool,
        results: List[Dict],
    ) -> None:
        """Recursively traverse and collect matches."""
        if isinstance(obj, dict):
            for key, value in obj.items():
                current_path = f"{path}.{key}"
                key_match = (not values_only) and matcher(key)
                val_match = (not keys_only) and (
                    not isinstance(value, (dict, list)) and matcher(value)
                )
                if key_match or val_match:
                    results.append({
                        "path": current_path,
                        "key": key,
                        "value": value,
                        "match_on": "key" if key_match and not val_match
                                    else "value" if val_match and not key_match
                                    else "both",
                    })
                if isinstance(value, (dict, list)):
                    self._search_recursive(
                        value, current_path, term, matcher,
                        keys_only, values_only, results
                    )

        elif isinstance(obj, list):
            for idx, item in enumerate(obj):
                current_path = f"{path}[{idx}]"
                if not keys_only and not isinstance(item, (dict, list)) and matcher(item):
                    results.append({
                        "path": current_path,
                        "key": f"[{idx}]",
                        "value": item,
                        "match_on": "value",
                    })
                if isinstance(item, (dict, list)):
                    self._search_recursive(
                        item, current_path, term, matcher,
                        keys_only, values_only, results
                    )


# =============================================================
# SECTION 8: JSONStats
# =============================================================

class JSONStats:
    """Compute statistics on numeric arrays."""

    def compute(self, data: Any) -> Dict[str, Any]:
        """
        Compute stats on data.
        Works on arrays of numbers, or arrays of objects (extracts all numeric fields).
        """
        if not isinstance(data, list):
            raise JSONQueryError(
                f"Stats requires an array, got {type(data).__name__}"
            )

        nums = self._extract_numbers(data)
        type_counts = self._count_types(data)

        result: Dict[str, Any] = {
            "count": len(data),
            "type_distribution": type_counts,
        }

        if nums:
            result["numeric_count"] = len(nums)
            result["sum"] = sum(nums)
            result["min"] = min(nums)
            result["max"] = max(nums)
            result["mean"] = round(sum(nums) / len(nums), 6)
            if len(nums) >= 2:
                result["std_dev"] = round(statistics.stdev(nums), 6)
                result["median"] = statistics.median(nums)
                result["p25"] = self._percentile(nums, 25)
                result["p75"] = self._percentile(nums, 75)
            else:
                result["median"] = nums[0]
        else:
            result["numeric_count"] = 0
            result["note"] = "No numeric values found in array"

        return result

    def _extract_numbers(self, data: List) -> List[float]:
        """Extract all numeric values from a list."""
        nums = []
        for item in data:
            if isinstance(item, (int, float)) and not isinstance(item, bool):
                nums.append(float(item))
            elif isinstance(item, dict):
                for v in item.values():
                    if isinstance(v, (int, float)) and not isinstance(v, bool):
                        nums.append(float(v))
        return nums

    def _count_types(self, data: List) -> Dict[str, int]:
        """Count types of items in list."""
        counts: Dict[str, int] = {}
        for item in data:
            if item is None:
                t = "null"
            elif isinstance(item, bool):
                t = "boolean"
            elif isinstance(item, int):
                t = "integer"
            elif isinstance(item, float):
                t = "float"
            elif isinstance(item, str):
                t = "string"
            elif isinstance(item, dict):
                t = "object"
            elif isinstance(item, list):
                t = "array"
            else:
                t = "unknown"
            counts[t] = counts.get(t, 0) + 1
        return counts

    def _percentile(self, nums: List[float], pct: float) -> float:
        """Simple percentile calculation."""
        sorted_nums = sorted(nums)
        n = len(sorted_nums)
        idx = (pct / 100) * (n - 1)
        lo = int(idx)
        hi = lo + 1
        if hi >= n:
            return round(sorted_nums[-1], 6)
        frac = idx - lo
        return round(sorted_nums[lo] + frac * (sorted_nums[hi] - sorted_nums[lo]), 6)


# =============================================================
# SECTION 9: JSONFormatter
# =============================================================

class JSONFormatter:
    """Format JSON output in various modes."""

    def format(
        self,
        data: Any,
        fmt: str = "pretty",
        color: bool = True,
        indent: int = 2,
        raw: bool = False,
    ) -> str:
        """
        Format data for output.

        fmt options:
            pretty  - Indented JSON (default)
            plain   - Compact single-line JSON
            csv     - CSV (for arrays of objects)
            table   - ASCII table (for arrays of objects)
            raw     - Raw value (no quotes for strings)
            count   - Just the count
        """
        if raw and isinstance(data, str):
            return data
        if raw and not isinstance(data, (dict, list)):
            return str(data)

        if fmt == "pretty":
            return color_json(data, indent=indent, enabled=color)
        elif fmt == "plain":
            return json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        elif fmt == "csv":
            return self._to_csv(data)
        elif fmt == "table":
            return self._to_table(data)
        elif fmt == "count":
            if isinstance(data, list):
                return str(len(data))
            elif isinstance(data, dict):
                return str(len(data))
            else:
                return "1"
        elif fmt == "raw":
            if isinstance(data, str):
                return data
            return json.dumps(data, ensure_ascii=False)
        else:
            return color_json(data, indent=indent, enabled=color)

    def _to_csv(self, data: Any) -> str:
        """Convert array of objects to CSV."""
        if not isinstance(data, list):
            raise JSONQueryError(
                f"CSV format requires an array, got {type(data).__name__}"
            )
        if not data:
            return ""

        # Get all unique keys from all objects
        headers: List[str] = []
        seen: set = set()
        for item in data:
            if isinstance(item, dict):
                for k in item.keys():
                    if k not in seen:
                        headers.append(k)
                        seen.add(k)

        if not headers:
            # Array of scalars
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["value"])
            for item in data:
                writer.writerow([item])
            return output.getvalue().rstrip()

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        for item in data:
            if isinstance(item, dict):
                writer.writerow({k: item.get(k, "") for k in headers})
            else:
                writer.writerow({headers[0]: item})
        return output.getvalue().rstrip()

    def _to_table(self, data: Any) -> str:
        """Convert array of objects to ASCII table."""
        if not isinstance(data, list):
            raise JSONQueryError(
                f"Table format requires an array, got {type(data).__name__}"
            )
        if not data:
            return "(empty)"

        # Get headers
        headers: List[str] = []
        seen: set = set()
        for item in data:
            if isinstance(item, dict):
                for k in item.keys():
                    if k not in seen:
                        headers.append(k)
                        seen.add(k)

        if not headers:
            return "\n".join(str(i) for i in data)

        # Build rows
        rows: List[List[str]] = []
        for item in data:
            if isinstance(item, dict):
                rows.append([str(item.get(h, "")) for h in headers])
            else:
                rows.append([str(item)] + [""] * (len(headers) - 1))

        # Calculate column widths
        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                if i < len(col_widths):
                    col_widths[i] = max(col_widths[i], len(cell))

        # Build table
        sep = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"
        header_row = "|" + "|".join(
            f" {h:<{col_widths[i]}} " for i, h in enumerate(headers)
        ) + "|"
        lines = [sep, header_row, sep]
        for row in rows:
            padded = [f" {row[i] if i < len(row) else '':<{col_widths[i]}} "
                      for i in range(len(headers))]
            lines.append("|" + "|".join(padded) + "|")
        lines.append(sep)
        return "\n".join(lines)


# =============================================================
# SECTION 10: Configuration
# =============================================================

def load_config() -> Dict[str, Any]:
    """Load user config or return defaults."""
    config = DEFAULT_CONFIG.copy()
    if CONFIG_FILE.exists():
        try:
            user_config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            config.update(user_config)
        except (json.JSONDecodeError, OSError):
            pass
    return config


# =============================================================
# SECTION 11: Command Handlers
# =============================================================

evaluator = JSONPathEvaluator()
filterer = JSONFilter()
searcher = JSONSearcher()
stats_calc = JSONStats()
formatter = JSONFormatter()


def cmd_get(args, config: Dict) -> int:
    """Get value at a JSON path."""
    try:
        data = load_json(args.file)
        result = evaluator.evaluate(data, args.path)

        if result is None:
            if not args.null_ok and not config.get("null_ok"):
                print_error(f"Path not found: '{args.path}'")
                return 1
            result = None

        color = not args.no_color and config.get("color", True)
        fmt = args.format or config.get("default_format", "pretty")
        output = formatter.format(result, fmt=fmt, color=color, raw=args.raw)
        print(output)
        return 0 if result is not None else 1

    except (JSONQueryError, PathError, InputError) as e:
        print_error(str(e))
        return 2


def cmd_filter(args, config: Dict) -> int:
    """Filter a JSON array by condition."""
    try:
        data = load_json(args.file)
        array = evaluator.evaluate(data, args.path)

        if array is None:
            print_error(f"Path not found: '{args.path}'")
            return 2

        filtered = filterer.apply(array, args.condition)

        if not filtered:
            print("[]")
            return 1

        color = not args.no_color and config.get("color", True)
        fmt = args.format or config.get("default_format", "pretty")
        output = formatter.format(filtered, fmt=fmt, color=color)
        print(output)
        return 0

    except (JSONQueryError, PathError, FilterError, InputError) as e:
        print_error(str(e))
        return 2


def cmd_search(args, config: Dict) -> int:
    """Search all keys/values for a term."""
    try:
        data = load_json(args.file)
        matches = searcher.search(
            data,
            args.term,
            keys_only=args.keys_only,
            values_only=args.values_only,
            use_regex=args.regex,
        )

        if not matches:
            print(f"No matches found for '{args.term}'")
            return 1

        color = not args.no_color and config.get("color", True)
        print(f"Found {len(matches)} match(es) for '{args.term}':\n")
        for m in matches:
            path_str = colorize(m["path"], Colors.BRIGHT_MAGENTA, enabled=color)
            match_on = colorize(f"({m['match_on']})", Colors.DIM + Colors.WHITE, enabled=color)
            val = m["value"]
            if isinstance(val, (dict, list)):
                val_str = json.dumps(val, ensure_ascii=False)[:80] + "..."
            else:
                val_str = str(val)
            val_colored = colorize(repr(val_str) if isinstance(val, str) else val_str,
                                   Colors.BRIGHT_GREEN, enabled=color)
            print(f"  {path_str} {match_on}")
            print(f"    {val_colored}\n")
        return 0

    except (JSONQueryError, FilterError, InputError) as e:
        print_error(str(e))
        return 2


def cmd_keys(args, config: Dict) -> int:
    """List all keys at a path."""
    try:
        data = load_json(args.file)
        if args.path:
            target = evaluator.evaluate(data, args.path)
        else:
            target = data

        if target is None:
            print_error(f"Path not found: '{args.path}'")
            return 2

        if isinstance(target, dict):
            keys = list(target.keys())
        elif isinstance(target, list):
            # Get all unique keys from objects in list
            seen = set()
            keys = []
            for item in target:
                if isinstance(item, dict):
                    for k in item.keys():
                        if k not in seen:
                            keys.append(k)
                            seen.add(k)
        else:
            print_error(f"Cannot list keys of {type(target).__name__}")
            return 2

        color = not args.no_color and config.get("color", True)
        for key in keys:
            print(colorize(key, Colors.CYAN, enabled=color))
        print(colorize(f"\n{len(keys)} key(s)", Colors.DIM + Colors.WHITE, enabled=color))
        return 0

    except (JSONQueryError, PathError, InputError) as e:
        print_error(str(e))
        return 2


def cmd_stats(args, config: Dict) -> int:
    """Compute statistics on a numeric array."""
    try:
        data = load_json(args.file)
        target = evaluator.evaluate(data, args.path)

        if target is None:
            print_error(f"Path not found: '{args.path}'")
            return 2

        result = stats_calc.compute(target)
        color = not args.no_color and config.get("color", True)
        output = formatter.format(result, fmt="pretty", color=color)
        print(output)
        return 0

    except (JSONQueryError, PathError, InputError) as e:
        print_error(str(e))
        return 2


def cmd_pretty(args, config: Dict) -> int:
    """Pretty-print JSON with optional color."""
    try:
        data = load_json(args.file)
        color = not args.no_color and config.get("color", True)
        indent = config.get("indent", 2)
        output = color_json(data, indent=indent, enabled=color)
        print(output)
        return 0

    except (JSONQueryError, InputError) as e:
        print_error(str(e))
        return 2


def cmd_validate(args, config: Dict) -> int:
    """Validate JSON syntax."""
    source = args.file
    try:
        if source == "-":
            content = sys.stdin.read()
            source_label = "stdin"
        else:
            path = Path(source)
            if not path.exists():
                print_error(f"File not found: '{source}'")
                return 2
            content = path.read_text(encoding="utf-8")
            source_label = str(path)

        json.loads(content)
        color = not args.no_color and config.get("color", True)
        msg = colorize(f"VALID", Colors.BRIGHT_GREEN, enabled=color)
        print(f"{msg}  '{source_label}' is valid JSON")
        size = len(content)
        print(f"  Size: {size:,} bytes")
        return 0

    except json.JSONDecodeError as e:
        color = not args.no_color and config.get("color", True)
        msg = colorize("INVALID", Colors.BRIGHT_RED, enabled=color)
        print(f"{msg}  '{source}' has JSON syntax errors")
        print(f"  Line {e.lineno}, Column {e.colno}: {e.msg}")
        # Show the problematic line
        lines = content.splitlines() if 'content' in dir() else []
        if lines and e.lineno <= len(lines):
            bad_line = lines[e.lineno - 1]
            print(f"  >>> {bad_line}")
            if e.colno > 1:
                print(f"  {'':>4}{'':>{e.colno - 1}}^")
        return 1

    except OSError as e:
        print_error(str(e))
        return 2


def cmd_csv(args, config: Dict) -> int:
    """Convert a JSON array to CSV."""
    try:
        data = load_json(args.file)
        target = evaluator.evaluate(data, args.path)

        if target is None:
            print_error(f"Path not found: '{args.path}'")
            return 2

        output = formatter._to_csv(target)
        print(output)
        return 0

    except (JSONQueryError, PathError, InputError) as e:
        print_error(str(e))
        return 2


def cmd_count(args, config: Dict) -> int:
    """Count elements at a JSON path."""
    try:
        data = load_json(args.file)
        target = evaluator.evaluate(data, args.path)

        if target is None:
            print_error(f"Path not found: '{args.path}'")
            return 2

        if isinstance(target, (list, dict)):
            count = len(target)
        else:
            count = 1

        print(count)
        return 0

    except (JSONQueryError, PathError, InputError) as e:
        print_error(str(e))
        return 2


def cmd_version(args, config: Dict) -> int:
    """Show version information."""
    color = config.get("color", True) and _COLOR_SUPPORTED
    title = colorize(f"{TOOL_NAME} v{VERSION}", Colors.BRIGHT_CYAN + Colors.BOLD, enabled=color)
    print(f"""
{title}
{"=" * 40}
Smart JSON Query & Filter Tool
Part of the Holy Grail Automation Toolkit

Built by:  {AUTHOR}
For:       {FOR}
GitHub:    {GITHUB}

Zero external dependencies. Pure Python stdlib.
""")
    return 0


# =============================================================
# SECTION 12: Error Output
# =============================================================

def print_error(msg: str) -> None:
    """Print error message to stderr."""
    color = _COLOR_SUPPORTED
    prefix = colorize("[ERROR]", Colors.BRIGHT_RED, enabled=color)
    print(f"{prefix} {msg}", file=sys.stderr)


# =============================================================
# SECTION 13: CLI Argument Parser
# =============================================================

def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        prog="jsonquery",
        description=(
            "JSONQuery - Smart JSON Query & Filter Tool\n"
            "Query, filter, search, and transform JSON from files or stdin.\n\n"
            "Examples:\n"
            "  jsonquery get data.json '$.users[0].name'\n"
            "  jsonquery filter data.json '$.users' 'age>18'\n"
            "  jsonquery search data.json 'admin'\n"
            "  cat data.json | jsonquery get - '$.count'\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--version", action="version",
        version=f"%(prog)s {VERSION}"
    )

    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")
    subparsers.required = True

    # Common args shared across commands
    def add_common(p):
        p.add_argument("--no-color", action="store_true", help="Disable ANSI colors")
        p.add_argument("--null-ok", action="store_true",
                       help="Return null instead of error on missing path")

    def add_format(p):
        p.add_argument(
            "--format", "-f",
            choices=["pretty", "plain", "csv", "table", "raw", "count"],
            default=None,
            help="Output format (default: pretty)"
        )

    # get
    p_get = subparsers.add_parser("get", help="Get value at a JSON path")
    p_get.add_argument("file", metavar="FILE", help="JSON file or '-' for stdin")
    p_get.add_argument("path", metavar="PATH", help="JSONPath expression (e.g. $.users[0].name)")
    p_get.add_argument("--raw", "-r", action="store_true",
                       help="Raw output (no quotes for strings)")
    add_format(p_get)
    add_common(p_get)

    # filter
    p_filter = subparsers.add_parser("filter", help="Filter array by condition")
    p_filter.add_argument("file", metavar="FILE", help="JSON file or '-' for stdin")
    p_filter.add_argument("path", metavar="PATH", help="Path to array")
    p_filter.add_argument("condition", metavar="CONDITION",
                          help="Filter condition (e.g. age>18, name~john, active=true)")
    add_format(p_filter)
    add_common(p_filter)

    # search
    p_search = subparsers.add_parser("search", help="Search all keys/values")
    p_search.add_argument("file", metavar="FILE", help="JSON file or '-' for stdin")
    p_search.add_argument("term", metavar="TERM", help="Search term")
    p_search.add_argument("--regex", action="store_true", help="Use term as regex pattern")
    p_search.add_argument("--keys-only", action="store_true", help="Search keys only")
    p_search.add_argument("--values-only", action="store_true", help="Search values only")
    add_common(p_search)

    # keys
    p_keys = subparsers.add_parser("keys", help="List all keys at a path")
    p_keys.add_argument("file", metavar="FILE", help="JSON file or '-' for stdin")
    p_keys.add_argument("path", metavar="PATH", nargs="?", default="$",
                        help="Path to object (default: $ root)")
    add_common(p_keys)

    # stats
    p_stats = subparsers.add_parser("stats", help="Statistics on a numeric array")
    p_stats.add_argument("file", metavar="FILE", help="JSON file or '-' for stdin")
    p_stats.add_argument("path", metavar="PATH", help="Path to array")
    add_common(p_stats)

    # pretty
    p_pretty = subparsers.add_parser("pretty", help="Pretty-print JSON with color")
    p_pretty.add_argument("file", metavar="FILE", help="JSON file or '-' for stdin")
    add_common(p_pretty)

    # validate
    p_validate = subparsers.add_parser("validate", help="Validate JSON syntax")
    p_validate.add_argument("file", metavar="FILE", help="JSON file or '-' for stdin")
    add_common(p_validate)

    # csv
    p_csv = subparsers.add_parser("csv", help="Convert array to CSV")
    p_csv.add_argument("file", metavar="FILE", help="JSON file or '-' for stdin")
    p_csv.add_argument("path", metavar="PATH", help="Path to array of objects")
    add_common(p_csv)

    # count
    p_count = subparsers.add_parser("count", help="Count elements at path")
    p_count.add_argument("file", metavar="FILE", help="JSON file or '-' for stdin")
    p_count.add_argument("path", metavar="PATH", help="Path to array or object")
    add_common(p_count)

    # version
    subparsers.add_parser("version", help="Show version information")

    return parser


# =============================================================
# SECTION 14: Main Entry Point
# =============================================================

COMMAND_MAP = {
    "get": cmd_get,
    "filter": cmd_filter,
    "search": cmd_search,
    "keys": cmd_keys,
    "stats": cmd_stats,
    "pretty": cmd_pretty,
    "validate": cmd_validate,
    "csv": cmd_csv,
    "count": cmd_count,
    "version": cmd_version,
}


def main() -> int:
    """Main entry point."""
    parser = build_parser()
    args = parser.parse_args()
    config = load_config()

    handler = COMMAND_MAP.get(args.command)
    if handler is None:
        print_error(f"Unknown command: '{args.command}'")
        return 2

    return handler(args, config)


if __name__ == "__main__":
    sys.exit(main())
