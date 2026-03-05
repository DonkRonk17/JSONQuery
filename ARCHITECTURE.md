# ARCHITECTURE - JSONQuery v1.0.0

**Project:** JSONQuery
**Builder:** ATLAS (Team Brain)
**Date:** March 5, 2026
**Protocol:** BUILD_PROTOCOL_V1.md Phase 3

---

## Design Philosophy

**Delta Change Detection Philosophy Applied:**
- Start with the SIMPLEST approach: Python's built-in `json` module
- Custom path evaluator using simple string parsing (no complex AST)
- Filter conditions parsed with `re` (stdlib regex)
- Output: plain text, colored ANSI, CSV - all via stdlib
- Single file, zero external dependencies

---

## Core Architecture: Single-File Design

```
jsonquery.py (single file, ~900-1100 LOC)
├── class JSONPathEvaluator     # Core: parse and evaluate path expressions
├── class JSONFilter            # Array filtering with condition expressions
├── class JSONSearcher          # Recursive key/value search
├── class JSONStats             # Statistics on numeric arrays
├── class JSONFormatter         # Output formatting (pretty, csv, table, plain)
├── class ColorWriter           # ANSI color output (Windows 10+ compatible)
└── main()                      # CLI argument parsing and command dispatch
```

---

## Component Design

### 1. JSONPathEvaluator

**Purpose:** Parse and evaluate path expressions against JSON data

**Path Syntax Supported:**
```
$               # Root element
$.key           # Object key access
$.nested.key    # Nested key access (dot notation)
$.array[0]      # Array index (0-based)
$.array[-1]     # Negative index (last element)
$.array[*]      # All array elements (returns list)
$.array[0:3]    # Slice notation
$..key          # Recursive descent (search any depth)
$[0]            # Root is array, access by index
```

**Implementation Strategy:**
1. Tokenize path: split on `.` and `[]` markers
2. Walk the JSON tree token by token
3. Handle wildcards `[*]` by returning lists
4. Handle recursive `..` by BFS/DFS traversal
5. Return `None` with clear error on invalid path

**Inputs:** `data: dict/list`, `path: str`
**Outputs:** `Any` (value at path) or raises `JSONQueryError`

---

### 2. JSONFilter

**Purpose:** Filter JSON arrays by condition expressions

**Filter Syntax:**
```
key=value        # Exact string/number match
key!=value       # Not equal
key>number       # Numeric greater than
key<number       # Numeric less than
key>=number      # Numeric >=
key<=number      # Numeric <=
key~pattern      # Contains string (case-insensitive)
key^pattern      # Starts with (case-insensitive)
key$pattern      # Ends with (case-insensitive)
key              # Key exists (truthy check)
!key             # Key absent or falsy
```

**Implementation Strategy:**
1. Parse condition with regex: `^(!?)(\w+)(=|!=|>=|<=|>|<|~|\^|\$)?(.*)$`
2. Apply condition to each item in array
3. Return filtered list
4. Graceful skip if item doesn't have the key

**Inputs:** `data: list`, `condition: str`
**Outputs:** `list` (filtered items)

---

### 3. JSONSearcher

**Purpose:** Recursively search all keys and values for a pattern

**Search Modes:**
- String match (default, case-insensitive)
- Regex match (--regex flag)
- Keys only (--keys-only flag)
- Values only (--values-only flag)

**Implementation Strategy:**
1. BFS traversal of entire JSON tree
2. Track path to each match (e.g., `$.users[2].email`)
3. Return list of `{path: str, key: str, value: any}` match objects

**Inputs:** `data: dict/list`, `term: str`, `flags: SearchFlags`
**Outputs:** `list[dict]` with path, key, value for each match

---

### 4. JSONStats

**Purpose:** Compute statistics on numeric arrays

**Statistics Computed:**
- Count, Sum, Min, Max, Mean (average)
- Median, Mode (most common)
- Standard deviation
- Percentiles (25th, 75th)
- Type distribution (int/float/str/null counts)

**Inputs:** `data: list`, `numeric_only: bool`
**Outputs:** `dict` with all statistics

---

### 5. JSONFormatter

**Purpose:** Format output in various modes

**Format Modes:**
- `pretty`: Pretty-printed JSON (default, with optional color)
- `plain`: Compact single-line JSON
- `csv`: Comma-separated values (array of objects)
- `table`: ASCII table (array of objects)
- `raw`: Raw string value (no quotes for strings)
- `count`: Just the count (for arrays)

**Inputs:** `data: Any`, `format: str`, `color: bool`
**Outputs:** `str`

---

### 6. ColorWriter

**Purpose:** ANSI color output compatible with Windows 10+

**Color Scheme:**
- Keys: Cyan
- String values: Green
- Number values: Yellow
- Boolean values: Blue
- Null values: Red/dim
- Brackets/braces: White
- Paths in search results: Magenta

**Implementation:**
- Use Python's `colorama`? NO - stdlib only
- Detect terminal capability with `os.environ.get('TERM')` and `sys.stdout.isatty()`
- Auto-disable on Windows if not Win10+ (check `os.name == 'nt'` and `sys.version_info`)
- Simple ANSI escape code constants

---

## CLI Command Dispatch

```
jsonquery <command> [FILE] [PATH] [OPTIONS]

Commands:
  get       FILE PATH [--format FORMAT] [--raw]
  filter    FILE PATH CONDITION [--format FORMAT]
  search    FILE TERM [--regex] [--keys-only] [--values-only]
  keys      FILE [PATH]
  stats     FILE PATH
  pretty    FILE [--no-color]
  validate  FILE
  csv       FILE PATH
  count     FILE PATH
  version   (no args)

FILE: path to JSON file, or '-' for stdin

Global Options:
  --format FORMAT    Output format: pretty/plain/csv/table/raw (default: pretty)
  --no-color         Disable ANSI colors
  --compact          Compact output (no indentation)
  --null-ok          Don't error on missing paths (return null)
  --help, -h         Show help
```

---

## Data Flow

```
User Input (CLI args)
        ↓
main() - argparse dispatch
        ↓
load_json(file_or_stdin)  →  JSONDecodeError → error + exit 2
        ↓
Command Router:
  get     → JSONPathEvaluator.evaluate(data, path)
  filter  → JSONPathEvaluator.evaluate(data, path) → JSONFilter.apply(result, condition)
  search  → JSONSearcher.search(data, term)
  keys    → JSONPathEvaluator.evaluate(data, path) → extract_keys(result)
  stats   → JSONPathEvaluator.evaluate(data, path) → JSONStats.compute(result)
  pretty  → JSONFormatter.format(data, 'pretty')
  validate → json.loads() → report valid/invalid
  csv     → JSONPathEvaluator.evaluate(data, path) → JSONFormatter.format(result, 'csv')
  count   → JSONPathEvaluator.evaluate(data, path) → len(result)
        ↓
JSONFormatter.format(result, format_mode, color)
        ↓
stdout output
        ↓
Exit codes: 0=success/match, 1=no match/empty, 2=error
```

---

## Error Handling Strategy

```python
class JSONQueryError(Exception):
    """Base exception for JSONQuery errors."""
    pass

class PathError(JSONQueryError):
    """Invalid or unresolvable path."""
    pass

class FilterError(JSONQueryError):
    """Invalid filter condition syntax."""
    pass

class InputError(JSONQueryError):
    """Invalid input (bad JSON, file not found, etc.)."""
    pass
```

**Error Display Format:**
```
[ERROR] Invalid JSON syntax in 'data.json'
  Line 5, Column 12: Expecting ',' delimiter
  Tip: Use 'jsonquery validate data.json' for details
```

---

## Configuration Strategy

Config file at `~/.jsonquery/config.json`:
```json
{
  "default_format": "pretty",
  "color": true,
  "indent": 2,
  "null_ok": false,
  "history_enabled": false,
  "history_max": 100
}
```

Config created on first run if missing. Uses `pathlib.Path.home()` for cross-platform path.

---

## Integration Design: Team Brain Pipes

**RestCLI → JSONQuery:**
```bash
restcli get https://api.github.com/users/DonkRonk17 | jsonquery get - "$.public_repos"
```

**SQLiteExplorer → JSONQuery:**
```bash
sqliteexplorer query mydb.db "SELECT * FROM users" --format json | jsonquery filter - "$" "age>18"
```

**JSONQuery → DiffPilot:**
```bash
jsonquery pretty v1.json > v1_pretty.json && jsonquery pretty v2.json > v2_pretty.json
diffpilot file v1_pretty.json v2_pretty.json
```

**JSONQuery → HashGuard (change detection):**
```bash
jsonquery get api_response.json "$.data[*].id" | hashguard file -
```

---

## Single-File Architecture Rationale

Consistent with 15+ Team Brain tools (DiffPilot, HashGuard, SessionMirror, etc.):
- One file = easy install (`cp jsonquery.py ~/.local/bin/`)
- Zero import errors from missing packages
- Readable, auditable
- Easy to embed in other scripts

---

## Code Organization (within single file)

```python
# ============================================================
# JSONQuery v1.0.0 - Smart JSON Query & Filter Tool
# ============================================================
# Standard library imports only

# Section 1: Constants & Configuration (~30 lines)
# Section 2: Color/ANSI utilities (~60 lines)
# Section 3: JSON Loading (~40 lines)
# Section 4: JSONPathEvaluator class (~200 lines)
# Section 5: JSONFilter class (~100 lines)
# Section 6: JSONSearcher class (~80 lines)
# Section 7: JSONStats class (~80 lines)
# Section 8: JSONFormatter class (~150 lines)
# Section 9: CLI argument parser (~80 lines)
# Section 10: Command handlers (~150 lines)
# Section 11: main() entrypoint (~30 lines)

# Total estimated: ~1000 LOC
```

---

## Quality Requirements Met

- Single file, ~1000 LOC
- Zero external dependencies
- Full test suite in separate test file
- Cross-platform (Windows + Linux)
- Consistent with Team Brain tool patterns
- Follows DiffPilot's exit code conventions (0/1/2)
- ANSI color auto-detection

---

**Architecture Complete: 99%+**
**Proceed to Phase 4: Implementation**

---

**Architecture By:** ATLAS (Team Brain)
**For:** Logan Smith / Metaphy LLC
"Quality is not an act, it is a habit!" ⚛️⚔️
