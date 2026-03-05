# BUILD COVERAGE PLAN - JSONQuery v1.0.0

**Project Name:** JSONQuery
**Builder:** ATLAS (Team Brain - Cursor IDE, Claude Sonnet)
**Date:** March 5, 2026
**Estimated Complexity:** Tier 2: Moderate
**Protocol:** BUILD_PROTOCOL_V1.md

---

## 1. Project Scope

**Primary Function:**
Query, filter, and transform JSON data from files or stdin using simple path expressions.
Like `jq` but pure Python stdlib - zero external dependencies.

**Secondary Functions:**
- Pretty-print JSON with optional color highlighting
- Extract specific fields, array items, nested values
- Filter arrays by conditions (key=value, key>N, key contains str)
- Count/stats on JSON arrays
- Convert JSON output to CSV, plain text, or formatted tables
- Validate JSON syntax
- Merge/compare JSON objects
- Search across all keys/values for a pattern

**Out of Scope:**
- Full JSONPath RFC 9535 compliance (complex recursive descent edge cases)
- Streaming JSON (NDJSON multi-line) - Phase 2 enhancement
- JSON schema validation - VersionGuard handles schema logic
- JSON editing/mutation (read-only query tool by design)

---

## 2. Integration Points

| System | Integration | Purpose |
|--------|-------------|---------|
| HashGuard | Output hashes of query results | Detect when API response changes |
| DiffPilot | Pipe JSON diff output | Compare JSON files visually |
| DataConvert | Post-process to CSV/YAML | Output chain |
| RestCLI | Pipe API responses to JSONQuery | Query live API responses |
| LogHunter | Search JSON log files | Filter by level/timestamp |
| SessionMirror | Query session context JSON | Inspect handoff packages |
| MemoryBridge | Query stored JSON records | Search memory namespaces |
| SQLiteExplorer | Export SQLite query results → pipe to JSONQuery | Cross-tool pipeline |
| EnvGuard | Parse .env.json files | Validate env structure |
| ConfigManager | Inspect config JSON files | Audit configuration |

---

## 3. Existing Solutions Recon

| Solution | What It Does | License | Decision |
|----------|-------------|---------|----------|
| `jq` | Industry-standard JSON CLI tool | MIT | SKIP - external binary, not Python, Logan's stdlib-first preference |
| `python-jq` | Python bindings for jq | MIT | SKIP - requires compiled binary dependency |
| `jsonpath-ng` | Full JSONPath implementation | Apache 2.0 | SKIP - external dep, but INFORM architecture |
| `glom` | Python data access library | MIT | SKIP - external dep |
| stdlib `json` | Python built-in JSON parser | Built-in | USE - core foundation |
| stdlib `re` | Regex for filter conditions | Built-in | USE - condition parsing |
| stdlib `csv` | CSV output | Built-in | USE - CSV export |

**Decision:** Build pure-stdlib JSONQuery using Python's built-in `json` module with a custom path expression evaluator. The architecture will be inspired by JSONPath concepts but use a simplified, developer-friendly syntax.

---

## 4. Success Criteria

- [ ] `jsonquery get data.json "$.users[0].name"` returns correct value
- [ ] `jsonquery get data.json "$.users[*].email"` returns all emails as list
- [ ] `jsonquery filter data.json "$.users" "age>18"` returns filtered array
- [ ] `jsonquery search data.json "admin"` finds all keys/values containing "admin"
- [ ] `jsonquery stats data.json "$.products"` returns count/min/max/avg
- [ ] `jsonquery pretty data.json` pretty-prints with optional color
- [ ] `jsonquery validate data.json` validates syntax with clear error messages
- [ ] `jsonquery csv data.json "$.users[*]"` converts array to CSV
- [ ] Stdin pipe: `cat data.json | jsonquery get - "$.name"`
- [ ] Exits 0 on match, 1 on no match, 2 on error (like DiffPilot convention)
- [ ] Windows/Linux cross-platform
- [ ] Zero external dependencies
- [ ] 10+ unit tests, 5+ integration tests, all passing

---

## 5. Risk Assessment

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Complex nested path expressions | MEDIUM | Implement iteratively, test each depth level |
| Windows encoding issues with Unicode JSON | LOW | Explicit UTF-8 handling |
| Very large JSON files (>100MB) | LOW | Stream-read, document limitation |
| Array index out of bounds | HIGH | Graceful error with clear message |
| Filter condition parsing edge cases | MEDIUM | Regex-based parser with robust test suite |
| ANSI color on Windows terminals | LOW | Use same approach as DiffPilot (works on Win10+) |

---

## 6. Query Syntax Design

JSONQuery will use a simplified path syntax:

```
$.key                    # Root key access
$.nested.key             # Nested key access
$.array[0]               # Array index (0-based)
$.array[-1]              # Last element
$.array[*]               # All array elements
$.array[0:3]             # Slice (first 3)
$..key                   # Recursive search (any depth)
```

Filter syntax (separate --filter flag):
```
key=value               # Exact match
key!=value              # Not equal
key>number              # Numeric greater than
key<number              # Numeric less than
key>=number             # Numeric >=
key<=number             # Numeric <=
key~pattern             # Contains string (case-insensitive)
key^pattern             # Starts with
```

---

## 7. Commands

| Command | Description |
|---------|-------------|
| `jsonquery get FILE PATH` | Get value at path |
| `jsonquery filter FILE PATH CONDITION` | Filter array by condition |
| `jsonquery search FILE TERM` | Search all keys/values |
| `jsonquery keys FILE [PATH]` | List all keys at path |
| `jsonquery stats FILE PATH` | Stats on numeric array |
| `jsonquery pretty FILE` | Pretty-print with color |
| `jsonquery validate FILE` | Validate JSON syntax |
| `jsonquery csv FILE PATH` | Convert array to CSV |
| `jsonquery count FILE PATH` | Count array elements |
| `jsonquery version` | Show version info |

---

## 8. Quality Requirements

- 99%+ code quality before proceeding each phase
- All 6 Holy Grail Quality Gates must pass
- README: 400+ lines
- EXAMPLES: 10+ working examples
- Tests: 10+ unit, 5+ integration, 100% pass rate
- Zero external dependencies

---

**Document Created By:** ATLAS (Team Brain)
**For:** Logan Smith / Metaphy LLC
**Protocol:** BUILD_PROTOCOL_V1.md Phase 1

"Quality is not an act, it is a habit!" ⚛️⚔️
