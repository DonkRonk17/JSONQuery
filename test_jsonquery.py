"""
Test Suite for JSONQuery v1.0.0
================================

Comprehensive tests following the Bug Hunt Protocol:
BUILD -> TEST -> BREAK -> OPTIMIZE -> REPEAT

Tests:
- Unit Tests: JSONPathEvaluator, JSONFilter, JSONSearcher, JSONStats, JSONFormatter
- Integration Tests: Full CLI command execution
- Edge Case Tests: Malformed input, missing paths, bad JSON, etc.

Built by: ATLAS (Team Brain)
For: Logan Smith / Metaphy LLC
"""

import csv
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# Add parent dir to path for import
sys.path.insert(0, str(Path(__file__).parent))

from jsonquery import (
    JSONPathEvaluator,
    JSONFilter,
    JSONSearcher,
    JSONStats,
    JSONFormatter,
    FilterError,
    InputError,
    PathError,
    JSONQueryError,
    load_json,
    main,
    color_json,
    cmd_get,
    cmd_filter,
    cmd_search,
    cmd_keys,
    cmd_stats,
    cmd_pretty,
    cmd_validate,
    cmd_csv,
    cmd_count,
)

# =============================================================
# Test Fixtures
# =============================================================

SAMPLE_DATA = {
    "users": [
        {"id": 1, "name": "Alice", "age": 25, "email": "alice@example.com", "active": True},
        {"id": 2, "name": "Bob", "age": 17, "email": "bob@example.com", "active": False},
        {"id": 3, "name": "Charlie", "age": 30, "email": "charlie@admin.com", "active": True},
        {"id": 4, "name": "Diana", "age": 22, "email": "diana@example.com", "active": True},
    ],
    "meta": {
        "total": 4,
        "page": 1,
        "version": "2.0",
        "nested": {"deep": {"value": 42}},
    },
    "tags": ["python", "json", "cli", "tool"],
    "empty_list": [],
    "count": 100,
    "enabled": True,
    "ratio": 0.75,
    "nothing": None,
}

NESTED_DATA = {
    "company": {
        "name": "Metaphy LLC",
        "departments": [
            {
                "name": "Engineering",
                "employees": [
                    {"name": "Alice", "role": "Lead"},
                    {"name": "Bob", "role": "Dev"},
                ]
            },
            {
                "name": "Research",
                "employees": [
                    {"name": "Charlie", "role": "Scientist"},
                ]
            }
        ]
    }
}


def make_temp_json(data: dict) -> str:
    """Create a temp JSON file and return its path."""
    fd, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(data, f)
    return path


# =============================================================
# Unit Tests: JSONPathEvaluator
# =============================================================

class TestJSONPathEvaluator(unittest.TestCase):
    """Unit tests for the JSONPathEvaluator class."""

    def setUp(self):
        self.ev = JSONPathEvaluator()
        self.data = SAMPLE_DATA

    def test_root_returns_full_data(self):
        """Test: '$' returns the entire root object."""
        result = self.ev.evaluate(self.data, "$")
        self.assertEqual(result, self.data)

    def test_simple_key_access(self):
        """Test: '$.count' returns simple integer value."""
        result = self.ev.evaluate(self.data, "$.count")
        self.assertEqual(result, 100)

    def test_nested_key_access(self):
        """Test: '$.meta.total' returns nested value."""
        result = self.ev.evaluate(self.data, "$.meta.total")
        self.assertEqual(result, 4)

    def test_deep_nested_key(self):
        """Test: '$.meta.nested.deep.value' returns deeply nested value."""
        result = self.ev.evaluate(self.data, "$.meta.nested.deep.value")
        self.assertEqual(result, 42)

    def test_array_index_zero(self):
        """Test: '$.users[0]' returns first array element."""
        result = self.ev.evaluate(self.data, "$.users[0]")
        self.assertIsInstance(result, dict)
        self.assertEqual(result["name"], "Alice")

    def test_array_index_nonzero(self):
        """Test: '$.users[2]' returns third array element."""
        result = self.ev.evaluate(self.data, "$.users[2]")
        self.assertEqual(result["name"], "Charlie")

    def test_array_negative_index(self):
        """Test: '$.users[-1]' returns last element."""
        result = self.ev.evaluate(self.data, "$.users[-1]")
        self.assertEqual(result["name"], "Diana")

    def test_array_index_then_key(self):
        """Test: '$.users[0].name' returns field from indexed item."""
        result = self.ev.evaluate(self.data, "$.users[0].name")
        self.assertEqual(result, "Alice")

    def test_array_wildcard(self):
        """Test: '$.users[*].email' returns all emails as list."""
        result = self.ev.evaluate(self.data, "$.users[*].email")
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 4)
        self.assertIn("alice@example.com", result)

    def test_array_wildcard_name(self):
        """Test: '$.users[*].name' returns all names."""
        result = self.ev.evaluate(self.data, "$.users[*].name")
        self.assertEqual(result, ["Alice", "Bob", "Charlie", "Diana"])

    def test_array_slice(self):
        """Test: '$.users[1:3]' returns slice of array."""
        result = self.ev.evaluate(self.data, "$.users[1:3]")
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["name"], "Bob")

    def test_tags_array_index(self):
        """Test: '$.tags[0]' on string array."""
        result = self.ev.evaluate(self.data, "$.tags[0]")
        self.assertEqual(result, "python")

    def test_recursive_descent(self):
        """Test: '$..email' finds all emails at any depth."""
        result = self.ev.evaluate(self.data, "$..email")
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 4)

    def test_recursive_descent_nested(self):
        """Test: '$..name' finds names in nested structures."""
        result = self.ev.evaluate(NESTED_DATA, "$..name")
        self.assertIsInstance(result, list)
        # Should find: "Metaphy LLC", "Engineering", "Research", "Alice", "Bob", "Charlie"
        self.assertGreaterEqual(len(result), 3)

    def test_missing_key_returns_none(self):
        """Test: Missing key returns None (no exception)."""
        result = self.ev.evaluate(self.data, "$.nonexistent")
        self.assertIsNone(result)

    def test_missing_nested_key_returns_none(self):
        """Test: '$.meta.nonexistent' returns None."""
        result = self.ev.evaluate(self.data, "$.meta.nonexistent")
        self.assertIsNone(result)

    def test_out_of_bounds_index_returns_none(self):
        """Test: '$.users[99]' returns None (out of bounds)."""
        result = self.ev.evaluate(self.data, "$.users[99]")
        self.assertIsNone(result)

    def test_path_must_start_with_dollar(self):
        """Test: Path without $ raises PathError."""
        with self.assertRaises(PathError):
            self.ev.evaluate(self.data, "users[0]")

    def test_null_value(self):
        """Test: '$.nothing' returns None (null JSON value)."""
        result = self.ev.evaluate(self.data, "$.nothing")
        self.assertIsNone(result)

    def test_boolean_value(self):
        """Test: '$.enabled' returns Python True."""
        result = self.ev.evaluate(self.data, "$.enabled")
        self.assertTrue(result)

    def test_float_value(self):
        """Test: '$.ratio' returns float."""
        result = self.ev.evaluate(self.data, "$.ratio")
        self.assertAlmostEqual(result, 0.75)

    def test_empty_list(self):
        """Test: '$.empty_list' returns empty list."""
        result = self.ev.evaluate(self.data, "$.empty_list")
        self.assertEqual(result, [])

    def test_root_array_index(self):
        """Test: '$[0]' when root is array."""
        arr_data = [{"a": 1}, {"a": 2}]
        result = self.ev.evaluate(arr_data, "$[0]")
        self.assertEqual(result, {"a": 1})

    def test_users_id_all(self):
        """Test: '$.users[*].id' returns all IDs."""
        result = self.ev.evaluate(self.data, "$.users[*].id")
        self.assertEqual(result, [1, 2, 3, 4])


# =============================================================
# Unit Tests: JSONFilter
# =============================================================

class TestJSONFilter(unittest.TestCase):
    """Unit tests for the JSONFilter class."""

    def setUp(self):
        self.f = JSONFilter()
        self.users = SAMPLE_DATA["users"]

    def test_filter_numeric_gt(self):
        """Test: age>18 returns adults only."""
        result = self.f.apply(self.users, "age>18")
        self.assertEqual(len(result), 3)
        names = [u["name"] for u in result]
        self.assertNotIn("Bob", names)

    def test_filter_numeric_lt(self):
        """Test: age<20 returns minors only."""
        result = self.f.apply(self.users, "age<20")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "Bob")

    def test_filter_numeric_gte(self):
        """Test: age>=25 returns users 25 and older."""
        result = self.f.apply(self.users, "age>=25")
        names = [u["name"] for u in result]
        self.assertIn("Alice", names)
        self.assertIn("Charlie", names)
        self.assertNotIn("Bob", names)
        self.assertNotIn("Diana", names)

    def test_filter_numeric_lte(self):
        """Test: age<=22 returns users 22 and younger."""
        result = self.f.apply(self.users, "age<=22")
        names = [u["name"] for u in result]
        self.assertIn("Bob", names)
        self.assertIn("Diana", names)

    def test_filter_exact_string(self):
        """Test: name=Alice returns only Alice."""
        result = self.f.apply(self.users, "name=Alice")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "Alice")

    def test_filter_not_equal_string(self):
        """Test: name!=Alice excludes Alice."""
        result = self.f.apply(self.users, "name!=Alice")
        names = [u["name"] for u in result]
        self.assertNotIn("Alice", names)
        self.assertEqual(len(result), 3)

    def test_filter_contains(self):
        """Test: name~ali case-insensitive contains."""
        result = self.f.apply(self.users, "name~ali")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "Alice")

    def test_filter_starts_with(self):
        """Test: name^cha starts-with."""
        result = self.f.apply(self.users, "name^cha")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "Charlie")

    def test_filter_ends_with(self):
        """Test: email$example.com ends-with."""
        result = self.f.apply(self.users, "email$example.com")
        self.assertEqual(len(result), 3)

    def test_filter_boolean_true(self):
        """Test: active=true returns only active users."""
        result = self.f.apply(self.users, "active=true")
        self.assertEqual(len(result), 3)
        for u in result:
            self.assertTrue(u["active"])

    def test_filter_boolean_false(self):
        """Test: active=false returns only inactive users."""
        result = self.f.apply(self.users, "active=false")
        self.assertEqual(len(result), 1)
        self.assertFalse(result[0]["active"])

    def test_filter_key_exists(self):
        """Test: key existence check (no operator)."""
        result = self.f.apply(self.users, "email")
        self.assertEqual(len(result), 4)

    def test_filter_empty_result(self):
        """Test: Filter with no matches returns empty list."""
        result = self.f.apply(self.users, "age>100")
        self.assertEqual(result, [])

    def test_filter_not_a_list_raises(self):
        """Test: Filter on non-list raises FilterError."""
        with self.assertRaises(FilterError):
            self.f.apply({"name": "Alice"}, "name=Alice")

    def test_filter_invalid_condition_raises(self):
        """Test: Completely invalid condition raises FilterError."""
        with self.assertRaises(FilterError):
            self.f.apply(self.users, "123invalid!!!")

    def test_filter_numeric_string_exact(self):
        """Test: id=1 matches numeric field."""
        result = self.f.apply(self.users, "id=1")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "Alice")


# =============================================================
# Unit Tests: JSONSearcher
# =============================================================

class TestJSONSearcher(unittest.TestCase):
    """Unit tests for JSONSearcher class."""

    def setUp(self):
        self.s = JSONSearcher()
        self.data = SAMPLE_DATA

    def test_search_finds_value(self):
        """Test: Search finds a string value."""
        results = self.s.search(self.data, "admin")
        self.assertGreater(len(results), 0)
        paths = [r["path"] for r in results]
        self.assertTrue(any("email" in p for p in paths))

    def test_search_finds_key(self):
        """Test: Search can find matching keys."""
        results = self.s.search(self.data, "email", keys_only=True)
        self.assertGreater(len(results), 0)
        for r in results:
            self.assertEqual(r["match_on"], "key")

    def test_search_values_only(self):
        """Test: values_only flag restricts to value matches."""
        results = self.s.search(self.data, "Alice", values_only=True)
        self.assertGreater(len(results), 0)
        for r in results:
            self.assertIn(r["match_on"], ("value", "both"))

    def test_search_case_insensitive(self):
        """Test: Search is case-insensitive by default."""
        results_lower = self.s.search(self.data, "alice")
        results_upper = self.s.search(self.data, "ALICE")
        self.assertEqual(len(results_lower), len(results_upper))

    def test_search_no_match(self):
        """Test: No match returns empty list."""
        results = self.s.search(self.data, "xyzzy_nonexistent_12345")
        self.assertEqual(results, [])

    def test_search_regex(self):
        """Test: Regex search mode."""
        results = self.s.search(self.data, r"alice|bob", use_regex=True)
        self.assertGreater(len(results), 0)

    def test_search_invalid_regex_raises(self):
        """Test: Invalid regex raises FilterError."""
        with self.assertRaises(FilterError):
            self.s.search(self.data, "[invalid(regex", use_regex=True)

    def test_search_returns_path(self):
        """Test: Each result includes a 'path' field."""
        results = self.s.search(self.data, "python")
        self.assertGreater(len(results), 0)
        for r in results:
            self.assertIn("path", r)
            self.assertTrue(r["path"].startswith("$"))


# =============================================================
# Unit Tests: JSONStats
# =============================================================

class TestJSONStats(unittest.TestCase):
    """Unit tests for JSONStats class."""

    def setUp(self):
        self.stats = JSONStats()

    def test_stats_basic_numeric_array(self):
        """Test: Stats on plain numeric array."""
        result = self.stats.compute([1, 2, 3, 4, 5])
        self.assertEqual(result["count"], 5)
        self.assertEqual(result["sum"], 15.0)
        self.assertEqual(result["min"], 1.0)
        self.assertEqual(result["max"], 5.0)
        self.assertAlmostEqual(result["mean"], 3.0)

    def test_stats_median(self):
        """Test: Median calculation."""
        result = self.stats.compute([1, 3, 5])
        self.assertEqual(result["median"], 3)

    def test_stats_object_array(self):
        """Test: Stats on array of objects (extracts all numbers)."""
        data = [{"age": 25}, {"age": 17}, {"age": 30}]
        result = self.stats.compute(data)
        self.assertEqual(result["count"], 3)
        self.assertIn("numeric_count", result)

    def test_stats_empty_array(self):
        """Test: Stats on empty array."""
        result = self.stats.compute([])
        self.assertEqual(result["count"], 0)

    def test_stats_non_numeric_array(self):
        """Test: Stats on string array notes no numbers."""
        result = self.stats.compute(["a", "b", "c"])
        self.assertEqual(result["numeric_count"], 0)
        self.assertIn("note", result)

    def test_stats_requires_list(self):
        """Test: Stats on non-list raises error."""
        with self.assertRaises(JSONQueryError):
            self.stats.compute({"key": "value"})

    def test_stats_type_distribution(self):
        """Test: Type distribution counts types correctly."""
        data = [1, "hello", True, None, {"key": "val"}]
        result = self.stats.compute(data)
        dist = result["type_distribution"]
        self.assertIn("integer", dist)
        self.assertIn("string", dist)
        self.assertIn("boolean", dist)
        self.assertIn("null", dist)
        self.assertIn("object", dist)


# =============================================================
# Unit Tests: JSONFormatter
# =============================================================

class TestJSONFormatter(unittest.TestCase):
    """Unit tests for JSONFormatter class."""

    def setUp(self):
        self.fmt = JSONFormatter()

    def test_pretty_format_dict(self):
        """Test: Pretty format produces indented JSON."""
        result = self.fmt.format({"key": "value"}, fmt="pretty", color=False)
        self.assertIn('"key"', result)
        self.assertIn('"value"', result)

    def test_plain_format(self):
        """Test: Plain format is compact single-line."""
        result = self.fmt.format({"a": 1, "b": 2}, fmt="plain", color=False)
        self.assertNotIn("\n", result)
        self.assertIn('"a":1', result)

    def test_csv_format_list_of_dicts(self):
        """Test: CSV format converts list of objects."""
        data = [{"name": "Alice", "age": 25}, {"name": "Bob", "age": 17}]
        result = self.fmt.format(data, fmt="csv", color=False)
        self.assertIn("name,age", result)
        self.assertIn("Alice,25", result)
        self.assertIn("Bob,17", result)

    def test_csv_format_scalar_array(self):
        """Test: CSV format handles array of scalars."""
        result = self.fmt.format(["a", "b", "c"], fmt="csv", color=False)
        self.assertIn("value", result)
        self.assertIn("a", result)

    def test_table_format(self):
        """Test: Table format produces ASCII table."""
        data = [{"name": "Alice", "age": 25}]
        result = self.fmt.format(data, fmt="table", color=False)
        self.assertIn("+", result)
        self.assertIn("name", result)
        self.assertIn("Alice", result)

    def test_count_format_list(self):
        """Test: Count format returns list length."""
        result = self.fmt.format([1, 2, 3], fmt="count", color=False)
        self.assertEqual(result, "3")

    def test_count_format_dict(self):
        """Test: Count format returns dict key count."""
        result = self.fmt.format({"a": 1, "b": 2}, fmt="count", color=False)
        self.assertEqual(result, "2")

    def test_raw_format_string(self):
        """Test: Raw format returns string without quotes."""
        result = self.fmt.format("hello world", fmt="raw", color=False)
        self.assertEqual(result, "hello world")

    def test_raw_flag_string(self):
        """Test: raw=True flag returns unquoted string."""
        result = self.fmt.format("test value", raw=True, color=False)
        self.assertEqual(result, "test value")

    def test_csv_non_list_raises(self):
        """Test: CSV on non-list raises error."""
        with self.assertRaises(JSONQueryError):
            self.fmt._to_csv({"key": "value"})

    def test_table_empty_returns_empty_str(self):
        """Test: Table on empty list returns '(empty)'."""
        result = self.fmt._to_table([])
        self.assertEqual(result, "(empty)")


# =============================================================
# Unit Tests: load_json
# =============================================================

class TestLoadJson(unittest.TestCase):
    """Tests for JSON loading function."""

    def test_load_valid_file(self):
        """Test: Load valid JSON file."""
        path = make_temp_json({"key": "value"})
        try:
            result = load_json(path)
            self.assertEqual(result["key"], "value")
        finally:
            os.unlink(path)

    def test_load_nonexistent_file(self):
        """Test: Missing file raises InputError."""
        with self.assertRaises(InputError):
            load_json("/nonexistent/path/data.json")

    def test_load_invalid_json(self):
        """Test: Invalid JSON raises InputError."""
        fd, path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "w") as f:
            f.write("{invalid json!!!")
        try:
            with self.assertRaises(InputError):
                load_json(path)
        finally:
            os.unlink(path)

    def test_load_stdin(self):
        """Test: Load from stdin using '-'."""
        test_input = json.dumps({"from": "stdin"})
        with patch("sys.stdin", io.StringIO(test_input)):
            result = load_json("-")
        self.assertEqual(result["from"], "stdin")

    def test_load_empty_json(self):
        """Test: Empty JSON object loads successfully."""
        path = make_temp_json({})
        try:
            result = load_json(path)
            self.assertEqual(result, {})
        finally:
            os.unlink(path)


# =============================================================
# Integration Tests: Full CLI commands
# =============================================================

class TestCLIIntegration(unittest.TestCase):
    """Integration tests running full CLI command handlers."""

    def setUp(self):
        """Create temp JSON file for testing."""
        self.temp_path = make_temp_json(SAMPLE_DATA)
        self.config = {"default_format": "pretty", "color": False, "indent": 2, "null_ok": False}

    def tearDown(self):
        """Clean up temp file."""
        if os.path.exists(self.temp_path):
            os.unlink(self.temp_path)

    def make_args(self, **kwargs):
        """Create a simple namespace object for args."""
        import argparse
        args = argparse.Namespace()
        args.no_color = True
        args.null_ok = False
        args.format = None
        args.raw = False
        args.regex = False
        args.keys_only = False
        args.values_only = False
        for k, v in kwargs.items():
            setattr(args, k, v)
        return args

    def test_cmd_get_simple_key(self):
        """Integration: cmd_get returns correct value."""
        args = self.make_args(file=self.temp_path, path="$.count")
        output = io.StringIO()
        with patch("sys.stdout", output):
            exit_code = cmd_get(args, self.config)
        self.assertEqual(exit_code, 0)
        self.assertIn("100", output.getvalue())

    def test_cmd_get_array_index_and_key(self):
        """Integration: cmd_get resolves array[idx].key path."""
        args = self.make_args(file=self.temp_path, path="$.users[0].name")
        output = io.StringIO()
        with patch("sys.stdout", output):
            exit_code = cmd_get(args, self.config)
        self.assertEqual(exit_code, 0)
        self.assertIn("Alice", output.getvalue())

    def test_cmd_get_wildcard(self):
        """Integration: cmd_get with wildcard returns all values."""
        args = self.make_args(file=self.temp_path, path="$.users[*].name")
        output = io.StringIO()
        with patch("sys.stdout", output):
            exit_code = cmd_get(args, self.config)
        self.assertEqual(exit_code, 0)
        result_text = output.getvalue()
        self.assertIn("Alice", result_text)
        self.assertIn("Bob", result_text)

    def test_cmd_get_missing_path_returns_1(self):
        """Integration: cmd_get on missing path returns exit code 1."""
        args = self.make_args(file=self.temp_path, path="$.nonexistent_key_xyz")
        with patch("sys.stderr", io.StringIO()):
            exit_code = cmd_get(args, self.config)
        self.assertEqual(exit_code, 1)

    def test_cmd_get_bad_file_returns_2(self):
        """Integration: cmd_get on missing file returns exit code 2."""
        args = self.make_args(file="/nonexistent/file.json", path="$.key")
        with patch("sys.stderr", io.StringIO()):
            exit_code = cmd_get(args, self.config)
        self.assertEqual(exit_code, 2)

    def test_cmd_filter_age_gt(self):
        """Integration: cmd_filter by age>18 works correctly."""
        args = self.make_args(file=self.temp_path, path="$.users", condition="age>18")
        output = io.StringIO()
        with patch("sys.stdout", output):
            exit_code = cmd_filter(args, self.config)
        self.assertEqual(exit_code, 0)
        result = json.loads(output.getvalue())
        self.assertEqual(len(result), 3)

    def test_cmd_filter_no_match_returns_1(self):
        """Integration: cmd_filter with no matches returns exit code 1."""
        args = self.make_args(file=self.temp_path, path="$.users", condition="age>200")
        output = io.StringIO()
        with patch("sys.stdout", output):
            exit_code = cmd_filter(args, self.config)
        self.assertEqual(exit_code, 1)

    def test_cmd_search_finds_term(self):
        """Integration: cmd_search finds matching values."""
        args = self.make_args(file=self.temp_path, term="admin")
        output = io.StringIO()
        with patch("sys.stdout", output):
            exit_code = cmd_search(args, self.config)
        self.assertEqual(exit_code, 0)
        self.assertIn("admin", output.getvalue())

    def test_cmd_search_no_match_returns_1(self):
        """Integration: cmd_search with no match returns exit code 1."""
        args = self.make_args(file=self.temp_path, term="xyzzy_no_match_ever")
        output = io.StringIO()
        with patch("sys.stdout", output):
            exit_code = cmd_search(args, self.config)
        self.assertEqual(exit_code, 1)

    def test_cmd_keys_root(self):
        """Integration: cmd_keys lists root keys."""
        args = self.make_args(file=self.temp_path, path="$")
        output = io.StringIO()
        with patch("sys.stdout", output):
            exit_code = cmd_keys(args, self.config)
        self.assertEqual(exit_code, 0)
        result_text = output.getvalue()
        self.assertIn("users", result_text)
        self.assertIn("meta", result_text)

    def test_cmd_stats_numeric_array(self):
        """Integration: cmd_stats on array computes stats."""
        args = self.make_args(file=self.temp_path, path="$.users")
        output = io.StringIO()
        with patch("sys.stdout", output):
            exit_code = cmd_stats(args, self.config)
        self.assertEqual(exit_code, 0)
        result_text = output.getvalue()
        self.assertIn("count", result_text)

    def test_cmd_validate_valid_file(self):
        """Integration: cmd_validate passes for valid JSON."""
        args = self.make_args(file=self.temp_path)
        output = io.StringIO()
        with patch("sys.stdout", output):
            exit_code = cmd_validate(args, self.config)
        self.assertEqual(exit_code, 0)
        self.assertIn("VALID", output.getvalue())

    def test_cmd_validate_invalid_json(self):
        """Integration: cmd_validate fails for invalid JSON."""
        fd, bad_path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "w") as f:
            f.write("{bad json!!!")
        try:
            args = self.make_args(file=bad_path)
            output = io.StringIO()
            err = io.StringIO()
            with patch("sys.stdout", output), patch("sys.stderr", err):
                exit_code = cmd_validate(args, self.config)
            self.assertEqual(exit_code, 1)
            self.assertIn("INVALID", output.getvalue())
        finally:
            os.unlink(bad_path)

    def test_cmd_csv_array(self):
        """Integration: cmd_csv converts array to CSV."""
        args = self.make_args(file=self.temp_path, path="$.users")
        output = io.StringIO()
        with patch("sys.stdout", output):
            exit_code = cmd_csv(args, self.config)
        self.assertEqual(exit_code, 0)
        result = output.getvalue()
        self.assertIn("name", result)
        self.assertIn("Alice", result)

    def test_cmd_count_array(self):
        """Integration: cmd_count returns correct count."""
        args = self.make_args(file=self.temp_path, path="$.users")
        output = io.StringIO()
        with patch("sys.stdout", output):
            exit_code = cmd_count(args, self.config)
        self.assertEqual(exit_code, 0)
        self.assertEqual(output.getvalue().strip(), "4")

    def test_cmd_count_tags(self):
        """Integration: cmd_count on string array."""
        args = self.make_args(file=self.temp_path, path="$.tags")
        output = io.StringIO()
        with patch("sys.stdout", output):
            exit_code = cmd_count(args, self.config)
        self.assertEqual(exit_code, 0)
        self.assertEqual(output.getvalue().strip(), "4")


# =============================================================
# Edge Case Tests
# =============================================================

class TestEdgeCases(unittest.TestCase):
    """Edge case and stress tests."""

    def setUp(self):
        self.ev = JSONPathEvaluator()
        self.f = JSONFilter()

    def test_path_on_empty_dict(self):
        """Edge: Path on empty dict returns None."""
        result = self.ev.evaluate({}, "$.key")
        self.assertIsNone(result)

    def test_path_on_empty_list(self):
        """Edge: Index on empty list returns None."""
        result = self.ev.evaluate([], "$[0]")
        self.assertIsNone(result)

    def test_deeply_nested_path(self):
        """Edge: 5-level deep nested access."""
        data = {"a": {"b": {"c": {"d": {"e": "deep_value"}}}}}
        result = self.ev.evaluate(data, "$.a.b.c.d.e")
        self.assertEqual(result, "deep_value")

    def test_array_of_arrays(self):
        """Edge: Nested array access."""
        data = {"matrix": [[1, 2], [3, 4]]}
        result = self.ev.evaluate(data, "$.matrix[0]")
        self.assertEqual(result, [1, 2])

    def test_json_with_unicode(self):
        """Edge: JSON with Unicode characters."""
        data = {"name": "日本語テスト", "emoji": "🎉"}
        result = self.ev.evaluate(data, "$.name")
        self.assertEqual(result, "日本語テスト")

    def test_filter_on_empty_array(self):
        """Edge: Filter on empty array returns empty list."""
        result = self.f.apply([], "age>18")
        self.assertEqual(result, [])

    def test_filter_items_without_key_skipped(self):
        """Edge: Filter skips items missing the filter key."""
        data = [{"name": "Alice", "age": 25}, {"name": "Bob"}]
        result = self.f.apply(data, "age>18")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "Alice")

    def test_get_numeric_zero(self):
        """Edge: Path returning 0 is not treated as missing."""
        data = {"count": 0}
        result = self.ev.evaluate(data, "$.count")
        self.assertEqual(result, 0)

    def test_get_false_value(self):
        """Edge: Path returning False is not treated as missing."""
        data = {"enabled": False}
        result = self.ev.evaluate(data, "$.enabled")
        self.assertIs(result, False)

    def test_large_array_slice(self):
        """Edge: Slice larger than array length is graceful."""
        data = {"items": [1, 2, 3]}
        result = self.ev.evaluate(data, "$.items[0:100]")
        self.assertEqual(result, [1, 2, 3])

    def test_pretty_format_null_value(self):
        """Edge: Pretty format handles None/null."""
        from jsonquery import JSONFormatter
        fmt = JSONFormatter()
        result = fmt.format(None, fmt="pretty", color=False)
        self.assertIn("null", result)

    def test_load_json_array_at_root(self):
        """Edge: JSON array at root loads correctly."""
        path = make_temp_json([1, 2, 3])
        try:
            result = load_json(path)
            self.assertEqual(result, [1, 2, 3])
        finally:
            os.unlink(path)

    def test_csv_missing_fields_filled_empty(self):
        """Edge: CSV with inconsistent keys fills missing fields with empty string."""
        from jsonquery import JSONFormatter
        fmt = JSONFormatter()
        data = [{"a": 1, "b": 2}, {"a": 3}]  # Second has no "b"
        result = fmt._to_csv(data)
        lines = result.splitlines()
        self.assertEqual(lines[0], "a,b")
        self.assertIn("1,2", lines[1])
        self.assertIn("3,", lines[2])  # b is empty


# =============================================================
# Test Runner
# =============================================================

if __name__ == "__main__":
    # Discover and run all tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    test_classes = [
        TestJSONPathEvaluator,
        TestJSONFilter,
        TestJSONSearcher,
        TestJSONStats,
        TestJSONFormatter,
        TestLoadJson,
        TestCLIIntegration,
        TestEdgeCases,
    ]

    for tc in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(tc))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    total = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    passed = total - failures - errors

    print(f"\n{'='*60}")
    print(f"JSONQuery Test Results")
    print(f"{'='*60}")
    print(f"  Total Tests:  {total}")
    print(f"  Passed:       {passed}")
    print(f"  Failed:       {failures}")
    print(f"  Errors:       {errors}")
    print(f"  Pass Rate:    {(passed/total*100):.1f}%" if total > 0 else "N/A")
    print(f"{'='*60}")

    if failures == 0 and errors == 0:
        print("  ALL TESTS PASSED! Quality Gate 1: TEST - PASS")
    else:
        print("  SOME TESTS FAILED - Fix before proceeding!")
        sys.exit(1)
