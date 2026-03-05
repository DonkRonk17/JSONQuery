# JSONQuery v1.0.0

> **Smart JSON Query & Filter Tool** — Query, filter, search, and transform JSON from files or stdin using simple path expressions. Zero external dependencies. Pure Python stdlib.

[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Dependencies](https://img.shields.io/badge/dependencies-zero-brightgreen.svg)]()
[![Tests](https://img.shields.io/badge/tests-100%2F100-brightgreen.svg)]()
[![Part of](https://img.shields.io/badge/part%20of-Holy%20Grail%20Toolkit-gold.svg)](https://github.com/DonkRonk17)

---

## What Is JSONQuery?

JSONQuery is a command-line tool for working with JSON data. Think of it like `jq` but pure Python — no installation of compiled binaries, no external packages, no surprises. It runs anywhere Python 3.8+ runs.

**Perfect for:**
- Drilling into complex API responses
- Extracting specific fields from JSON configs
- Filtering arrays of objects by conditions
- Searching across all keys and values
- Converting JSON arrays to CSV
- Validating JSON files before deployment
- Piping with RestCLI, SQLiteExplorer, and other Team Brain tools

---

## Quick Start

```bash
# Get a specific value
python jsonquery.py get data.json "$.users[0].name"

# Filter an array
python jsonquery.py filter data.json "$.users" "age>18"

# Search everywhere
python jsonquery.py search data.json "admin"

# Pretty-print with color
python jsonquery.py pretty data.json

# Pipe from stdin
cat api_response.json | python jsonquery.py get - "$.data.count"
```

---

## Installation

**Requirements:** Python 3.8+, zero external packages

```bash
# Method 1: Copy the script (simplest)
cp jsonquery.py /usr/local/bin/jsonquery
chmod +x /usr/local/bin/jsonquery

# Method 2: pip install (local)
pip install -e .

# Method 3: Run directly
python jsonquery.py --help
```

**Windows:**
```powershell
# Copy to a folder on your PATH
Copy-Item jsonquery.py "$env:USERPROFILE\bin\jsonquery.py"

# Run as:
python jsonquery.py get data.json "$.key"
```

---

## Commands

| Command | Description | Example |
|---------|-------------|---------|
| `get` | Get value at a JSON path | `get data.json "$.name"` |
| `filter` | Filter array by condition | `filter data.json "$.items" "age>18"` |
| `search` | Search all keys/values | `search data.json "admin"` |
| `keys` | List all keys at path | `keys data.json "$.config"` |
| `stats` | Statistics on numeric array | `stats data.json "$.prices"` |
| `pretty` | Pretty-print with color | `pretty data.json` |
| `validate` | Validate JSON syntax | `validate data.json` |
| `csv` | Convert array to CSV | `csv data.json "$.users"` |
| `count` | Count elements at path | `count data.json "$.items"` |
| `version` | Show version info | `version` |

---

## Path Syntax

JSONQuery uses a simplified JSONPath-inspired syntax:

| Pattern | Description | Example |
|---------|-------------|---------|
| `$` | Root element | `$` |
| `$.key` | Object key | `$.name` |
| `$.a.b.c` | Nested keys | `$.user.address.city` |
| `$.arr[0]` | Array index (0-based) | `$.items[0]` |
| `$.arr[-1]` | Last element | `$.items[-1]` |
| `$.arr[*]` | All elements | `$.items[*]` |
| `$.arr[0:3]` | Slice | `$.items[0:5]` |
| `$..key` | Recursive search | `$..email` |
| `$[0]` | Root array index | `$[0]` |

**Examples:**
```bash
# Root object
jsonquery get data.json "$"

# Simple key
jsonquery get data.json "$.name"

# Nested access
jsonquery get data.json "$.user.address.city"

# Array index
jsonquery get data.json "$.items[0]"

# Last element
jsonquery get data.json "$.items[-1]"

# All emails in users array
jsonquery get data.json "$.users[*].email"

# Array slice (first 5 items)
jsonquery get data.json "$.items[0:5]"

# Array index then key
jsonquery get data.json "$.users[2].name"

# Recursive descent (any depth)
jsonquery get data.json "$..email"
```

---

## Filter Conditions

The `filter` command filters JSON arrays using condition expressions:

| Operator | Description | Example |
|----------|-------------|---------|
| `key=value` | Exact match | `name=Alice` |
| `key!=value` | Not equal | `status!=deleted` |
| `key>number` | Numeric greater than | `age>18` |
| `key<number` | Numeric less than | `price<100` |
| `key>=number` | Numeric >= | `rating>=4` |
| `key<=number` | Numeric <= | `score<=10` |
| `key~pattern` | Contains (case-insensitive) | `name~ali` |
| `key^pattern` | Starts with | `email^admin` |
| `key$pattern` | Ends with | `email$gmail.com` |
| `key` | Key exists and is truthy | `active` |
| `!key` | Key absent or falsy | `!deleted` |

**Boolean values:** Use `true`/`false` (lowercase) to match JSON booleans:
```bash
jsonquery filter data.json "$.users" "active=true"
jsonquery filter data.json "$.users" "verified=false"
```

**Numeric comparisons:**
```bash
jsonquery filter data.json "$.products" "price>50"
jsonquery filter data.json "$.products" "stock<=0"
jsonquery filter data.json "$.scores" "rating>=4.5"
```

**String matching:**
```bash
# Exact match
jsonquery filter data.json "$.users" "role=admin"

# Contains (case-insensitive)
jsonquery filter data.json "$.users" "name~john"

# Starts with
jsonquery filter data.json "$.files" "name^report"

# Ends with
jsonquery filter data.json "$.files" "name$.pdf"
```

---

## Output Formats

Use `--format` (or `-f`) to control output format:

| Format | Description | Use Case |
|--------|-------------|---------|
| `pretty` | Indented JSON (default) | Human reading |
| `plain` | Compact JSON | Piping to other tools |
| `csv` | Comma-separated values | Spreadsheets |
| `table` | ASCII table | Terminal display |
| `raw` | Raw string value | Shell variables |
| `count` | Count only | Scripting |

**Examples:**
```bash
# Default: pretty JSON with color
jsonquery get data.json "$.users"

# Compact for pipes
jsonquery get data.json "$.users" --format plain

# CSV for spreadsheet
jsonquery csv data.json "$.users" > users.csv

# ASCII table
jsonquery get data.json "$.users" --format table

# Raw string (no quotes)
jsonquery get data.json "$.config.api_key" --format raw --no-color

# Just the count
jsonquery get data.json "$.users" --format count

# Raw flag shortcut
jsonquery get data.json "$.name" --raw
```

---

## Command Reference

### `jsonquery get FILE PATH [OPTIONS]`

Get the value at a JSON path expression.

```
Arguments:
  FILE    JSON file path, or '-' for stdin
  PATH    JSONPath expression

Options:
  --format, -f   Output format (pretty/plain/csv/table/raw/count)
  --raw, -r      Raw output (no quotes for string values)
  --no-color     Disable ANSI colors
  --null-ok      Return null instead of error for missing paths

Exit codes:
  0 = Value found
  1 = Path not found / null result
  2 = Error (bad file, invalid JSON)
```

### `jsonquery filter FILE PATH CONDITION [OPTIONS]`

Filter a JSON array by a condition expression.

```
Arguments:
  FILE        JSON file path, or '-' for stdin
  PATH        Path to the array (e.g. $.users)
  CONDITION   Filter condition (e.g. age>18, name~alice, active=true)

Options:
  --format, -f   Output format
  --no-color     Disable ANSI colors
  --null-ok      Don't error on missing path

Exit codes:
  0 = Matches found
  1 = No matches
  2 = Error
```

### `jsonquery search FILE TERM [OPTIONS]`

Search all keys and values for a term.

```
Arguments:
  FILE    JSON file path, or '-' for stdin
  TERM    Search term (or regex pattern with --regex)

Options:
  --regex         Use TERM as a regex pattern
  --keys-only     Search keys only
  --values-only   Search values only
  --no-color      Disable ANSI colors

Exit codes:
  0 = Matches found
  1 = No matches
  2 = Error
```

### `jsonquery keys FILE [PATH] [OPTIONS]`

List all keys at a JSON path (default: root).

```
Arguments:
  FILE    JSON file path, or '-' for stdin
  PATH    Optional path to object (default: $ root)

Exit codes:
  0 = Keys listed
  2 = Error
```

### `jsonquery stats FILE PATH [OPTIONS]`

Compute statistics on a numeric array.

```
Arguments:
  FILE    JSON file path, or '-' for stdin
  PATH    Path to array

Output includes:
  count, sum, min, max, mean, median,
  std_dev, p25, p75, type_distribution

Exit codes:
  0 = Stats computed
  2 = Error
```

### `jsonquery pretty FILE [OPTIONS]`

Pretty-print JSON with syntax highlighting.

```
Arguments:
  FILE    JSON file path, or '-' for stdin

Options:
  --no-color   Disable syntax highlighting

Exit codes:
  0 = Success
  2 = Error
```

### `jsonquery validate FILE [OPTIONS]`

Validate JSON syntax and report errors.

```
Arguments:
  FILE    JSON file path, or '-' for stdin

Output:
  VALID   'filename.json' is valid JSON
  INVALID 'filename.json' has JSON syntax errors
           Line X, Column Y: error message

Exit codes:
  0 = Valid JSON
  1 = Invalid JSON
  2 = Error (file not found)
```

### `jsonquery csv FILE PATH [OPTIONS]`

Convert a JSON array of objects to CSV.

```
Arguments:
  FILE    JSON file path, or '-' for stdin
  PATH    Path to array of objects

Exit codes:
  0 = Success
  2 = Error
```

### `jsonquery count FILE PATH [OPTIONS]`

Count elements in an array or keys in an object.

```
Arguments:
  FILE    JSON file path, or '-' for stdin
  PATH    Path to array or object

Output:
  Single integer (e.g. "42")

Exit codes:
  0 = Success
  2 = Error
```

---

## Piping and Integration

JSONQuery is designed to work in pipelines with other Team Brain tools:

### RestCLI → JSONQuery (Query live API responses)
```bash
# Get public repos count from GitHub API
python restcli.py get https://api.github.com/users/DonkRonk17 | python jsonquery.py get - "$.public_repos" --raw

# Filter API results
python restcli.py get https://jsonplaceholder.typicode.com/posts | python jsonquery.py filter - "$" "userId=1"
```

### SQLiteExplorer → JSONQuery (Query database results)
```bash
# Export SQLite to JSON, then query
python sqliteexplorer.py query mydb.db "SELECT * FROM users" --format json | python jsonquery.py filter - "$" "age>18"
```

### JSONQuery → DiffPilot (Compare JSON files)
```bash
# Pretty-print both, then diff
python jsonquery.py pretty config_v1.json > /tmp/v1.txt
python jsonquery.py pretty config_v2.json > /tmp/v2.txt
python diffpilot.py file /tmp/v1.txt /tmp/v2.txt
```

### JSONQuery → HashGuard (Detect API response changes)
```bash
# Save API response hash for change detection
python jsonquery.py get api.json "$.data[*].id" --format plain | python hashguard.py file -
```

### LogHunter → JSONQuery (Filter JSON log files)
```bash
# If logs are JSON format
python logHunter.py search app.log.json "ERROR" | python jsonquery.py get - "$.timestamp"
```

### JSONQuery in Shell Scripts
```bash
#!/bin/bash
# Extract config value in script
API_KEY=$(python jsonquery.py get config.json "$.api.key" --raw --no-color)
echo "API Key: $API_KEY"

# Count records and branch
COUNT=$(python jsonquery.py count data.json "$.records" --no-color)
if [ "$COUNT" -gt 100 ]; then
  echo "Large dataset: $COUNT records"
fi
```

---

## Color Support

JSONQuery automatically detects color support:
- **macOS/Linux**: Full color on any terminal
- **Windows 10+**: Full color (ANSI enabled automatically)
- **Windows 8 and below**: No color (graceful fallback)
- **No TTY (piped output)**: No color (automatic detection)
- **`NO_COLOR` env var**: Disables color
- **`--no-color` flag**: Disables color

**Color scheme:**
- Keys: Cyan
- String values: Green
- Numbers: Yellow
- Booleans: Blue
- Null: Dim red
- Search paths: Magenta

---

## Configuration

Create `~/.jsonquery/config.json` to customize defaults:

```json
{
  "default_format": "pretty",
  "color": true,
  "indent": 2,
  "null_ok": false
}
```

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `default_format` | string | `"pretty"` | Default output format |
| `color` | bool | `true` | Enable/disable ANSI colors |
| `indent` | int | `2` | JSON pretty-print indent spaces |
| `null_ok` | bool | `false` | Return null instead of error for missing paths |

Config is created automatically on first run if missing.

---

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success — value found / condition matched |
| `1` | No match — path not found / empty result / invalid JSON |
| `2` | Error — bad file, invalid syntax, wrong argument |

This convention makes JSONQuery easy to use in shell scripts:
```bash
# Check if a key exists
python jsonquery.py get config.json "$.database.host" --null-ok > /dev/null
if [ $? -eq 0 ]; then
  echo "Database host is configured"
fi

# Use with set -e
set -e
python jsonquery.py validate deploy-config.json
echo "Config is valid, proceeding with deploy..."
```

---

## Error Messages

JSONQuery provides clear, actionable error messages:

```
[ERROR] File not found: 'missing_data.json'

[ERROR] Invalid JSON in 'broken.json': Expecting ',' delimiter
  Tip: Use 'jsonquery validate broken.json' for details

[ERROR] Path not found: '$.users.nonexistent'

[ERROR] Filter requires an array, got dict.
  Use a path that points to an array.

[ERROR] Operator '>' requires numeric values, got 'hello' and '18'
```

---

## Advanced Usage

### Combining get and filter
```bash
# Get names of active users over 21
python jsonquery.py filter data.json "$.users" "active=true" --format plain | \
  python jsonquery.py get - "$..[*].name"
```

### Extracting multiple fields
```bash
# Get both name and email for first user
python jsonquery.py get data.json "$.users[0]" --format plain | \
  python -c "import json,sys; u=json.load(sys.stdin); print(u['name'], u['email'])"
```

### Checking API health
```bash
# Validate API response has expected fields
python jsonquery.py validate response.json && \
  python jsonquery.py get response.json "$.status" --raw | grep -q "ok" && \
  echo "API healthy"
```

### Stats on sales data
```bash
python jsonquery.py stats sales.json "$.transactions[*].amount"
# Output:
# {
#   "count": 1523,
#   "sum": 87234.50,
#   "min": 0.99,
#   "max": 4999.00,
#   "mean": 57.28,
#   "median": 29.99,
#   "std_dev": 123.45,
#   "p25": 9.99,
#   "p75": 79.99
# }
```

### Recursive search for all emails
```bash
python jsonquery.py get org_data.json "$..email"
# Finds ALL emails at ANY depth in the JSON
```

---

## Comparison with jq

| Feature | JSONQuery | jq |
|---------|-----------|-----|
| Dependencies | None (Python stdlib) | Compiled C binary |
| Installation | Copy one .py file | Must install binary |
| Path syntax | Simplified JSONPath | Full jq language |
| Filter syntax | `key>value`, `key~term` | Full jq filter expressions |
| Cross-platform | Any Python 3.8+ | Requires OS-specific binary |
| Scripting | Python-importable API | CLI only |
| Learning curve | Minimal | Moderate (unique syntax) |
| Power | High (common cases) | Higher (complex transforms) |

**When to use JSONQuery:** You want quick, readable JSON queries without installing or learning `jq`. Works great for 95% of real-world JSON use cases.

**When to use jq:** You need complex data transformations, custom functions, or recursive path logic beyond what JSONQuery supports.

---

## Python API

JSONQuery can be imported and used as a Python library:

```python
from jsonquery import (
    JSONPathEvaluator,
    JSONFilter,
    JSONSearcher,
    JSONStats,
    JSONFormatter,
    load_json
)

# Load data
data = load_json("data.json")

# Query
evaluator = JSONPathEvaluator()
names = evaluator.evaluate(data, "$.users[*].name")
print(names)  # ['Alice', 'Bob', 'Charlie']

# Filter
filterer = JSONFilter()
adults = filterer.apply(data["users"], "age>18")

# Search
searcher = JSONSearcher()
matches = searcher.search(data, "admin")
for m in matches:
    print(f"{m['path']}: {m['value']}")

# Stats
stats = JSONStats()
result = stats.compute(data["prices"])
print(f"Average: {result['mean']}")

# Format
formatter = JSONFormatter()
csv_output = formatter.format(adults, fmt="csv")
print(csv_output)
```

---

## Integration Examples

### Team Brain: SessionMirror Inspection
```bash
# Inspect a session handoff package
python jsonquery.py keys ~/.session_mirror/sessions/ 2>/dev/null

# Check what agent created a session
python jsonquery.py get session_001.json "$.from_agent" --raw

# List all tasks in a handoff
python jsonquery.py get handoff.json "$.task.description" --raw
```

### Team Brain: EnvGuard Complement
```bash
# Inspect .env.json config structure
python jsonquery.py keys env_config.json
python jsonquery.py get env_config.json "$.database" --format table
```

### Team Brain: MemoryBridge Query
```bash
# If MemoryBridge exports to JSON
python jsonquery.py search memory_export.json "BCH"
python jsonquery.py filter records.json "$" "namespace=team_brain"
```

---

## Testing

```bash
# Run full test suite
python test_jsonquery.py

# Run specific test class
python -m pytest test_jsonquery.py::TestJSONPathEvaluator -v

# Run with coverage
python -m pytest test_jsonquery.py --cov=jsonquery --cov-report=term-missing
```

**Test Results:** 100/100 tests passing (100%)

Test categories:
- `TestJSONPathEvaluator` (24 tests) - Path expression evaluation
- `TestJSONFilter` (15 tests) - Array filtering
- `TestJSONSearcher` (8 tests) - Search functionality
- `TestJSONStats` (7 tests) - Statistics computation
- `TestJSONFormatter` (11 tests) - Output formatting
- `TestLoadJson` (5 tests) - JSON loading
- `TestCLIIntegration` (16 tests) - Full CLI command testing
- `TestEdgeCases` (14 tests) - Edge cases and error handling

---

## Troubleshooting

### "Path not found" for a key that exists
- Check your path syntax. Key names are case-sensitive: `$.Name` ≠ `$.name`
- Verify the key exists: `jsonquery keys data.json "$.parent"`
- Use `--null-ok` to return null instead of error

### Filter not matching booleans
- Use lowercase: `active=true` not `active=True`
- JSON booleans are `true`/`false` (lowercase)

### Unicode display issues on Windows
- Use `--no-color` to disable ANSI codes
- Ensure your terminal supports UTF-8

### No color in output
- Check `NO_COLOR` environment variable isn't set
- Verify terminal supports ANSI (Windows 10+ required)
- Use `-f pretty` explicitly

### CSV output has extra quotes
- This is standard CSV escaping for values containing commas
- Open with a spreadsheet app for proper display

---

## License

MIT License

Copyright (c) 2026 Logan Smith / Metaphy LLC

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.

---

## About

**JSONQuery** is part of the **Holy Grail Automation Toolkit** — 88 professional-grade CLI tools built for developers, AI agents, and automation workflows.

- **GitHub:** https://github.com/DonkRonk17
- **Built by:** ATLAS (Team Brain — Cursor IDE, Claude Sonnet)
- **For:** Logan Smith / Metaphy LLC
- **Date:** March 5, 2026

**Tool #88 of 88** in the Holy Grail Automation Toolkit

---

*"Build something extremely useful, that is easy to use, solves a common problem, and has clear instructions."*

**For the Maximum Benefit of Life. One World. One Family. One Love.** 🔆⚒️🔗
