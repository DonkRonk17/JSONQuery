# JSONQuery Examples

> 15+ working examples with expected output
> Part of the Holy Grail Automation Toolkit

---

## Setup

All examples use this sample `data.json`:

```json
{
  "users": [
    {"id": 1, "name": "Alice", "age": 25, "email": "alice@example.com", "active": true},
    {"id": 2, "name": "Bob", "age": 17, "email": "bob@example.com", "active": false},
    {"id": 3, "name": "Charlie", "age": 30, "email": "charlie@admin.com", "active": true},
    {"id": 4, "name": "Diana", "age": 22, "email": "diana@example.com", "active": true}
  ],
  "meta": {
    "total": 4,
    "page": 1,
    "version": "2.0"
  },
  "tags": ["python", "json", "cli", "tool"],
  "count": 100
}
```

---

## Example 1: Get a Simple Value

```bash
python jsonquery.py get data.json "$.count" --no-color
```

**Expected output:**
```
100
```

---

## Example 2: Get a Nested Value

```bash
python jsonquery.py get data.json "$.meta.version" --no-color --raw
```

**Expected output:**
```
2.0
```

---

## Example 3: Get Array Item by Index

```bash
python jsonquery.py get data.json "$.users[0].name" --no-color --raw
```

**Expected output:**
```
Alice
```

---

## Example 4: Get Array Item with Negative Index (Last)

```bash
python jsonquery.py get data.json "$.users[-1].email" --no-color --raw
```

**Expected output:**
```
diana@example.com
```

---

## Example 5: Get All Values via Wildcard

```bash
python jsonquery.py get data.json "$.users[*].name" --no-color
```

**Expected output:**
```json
[
  "Alice",
  "Bob",
  "Charlie",
  "Diana"
]
```

---

## Example 6: Filter Array by Numeric Condition

```bash
python jsonquery.py filter data.json "$.users" "age>18" --no-color --format table
```

**Expected output:**
```
+----+---------+-----+-------------------+--------+
| id | name    | age | email             | active |
+----+---------+-----+-------------------+--------+
| 1  | Alice   | 25  | alice@example.com | True   |
| 3  | Charlie | 30  | charlie@admin.com | True   |
| 4  | Diana   | 22  | diana@example.com | True   |
+----+---------+-----+-------------------+--------+
```

---

## Example 7: Filter Array by Boolean

```bash
python jsonquery.py filter data.json "$.users" "active=true" --no-color --format count
```

**Expected output:**
```
3
```

---

## Example 8: Filter by String Contains

```bash
python jsonquery.py filter data.json "$.users" "email~admin" --no-color --format plain
```

**Expected output:**
```json
[{"id":3,"name":"Charlie","age":30,"email":"charlie@admin.com","active":true}]
```

---

## Example 9: Search All Keys and Values

```bash
python jsonquery.py search data.json "admin" --no-color
```

**Expected output:**
```
Found 1 match(es) for 'admin':

  $.users[2].email (value)
    'charlie@admin.com'
```

---

## Example 10: Recursive Descent (Find at Any Depth)

```bash
python jsonquery.py get data.json "$..email" --no-color
```

**Expected output:**
```json
[
  "alice@example.com",
  "bob@example.com",
  "charlie@admin.com",
  "diana@example.com"
]
```

---

## Example 11: List All Keys

```bash
python jsonquery.py keys data.json "$.meta" --no-color
```

**Expected output:**
```
total
page
version

3 key(s)
```

---

## Example 12: Statistics on Array

```bash
python jsonquery.py stats data.json "$.users[*].age" --no-color
```

**Expected output:**
```json
{
  "count": 4,
  "type_distribution": {
    "integer": 4
  },
  "numeric_count": 4,
  "sum": 94.0,
  "min": 17.0,
  "max": 30.0,
  "mean": 23.5,
  "std_dev": 5.447047,
  "median": 23.5,
  "p25": 20.75,
  "p75": 26.25
}
```

---

## Example 13: Convert to CSV

```bash
python jsonquery.py csv data.json "$.users"
```

**Expected output:**
```csv
id,name,age,email,active
1,Alice,25,alice@example.com,True
2,Bob,17,bob@example.com,False
3,Charlie,30,charlie@admin.com,True
4,Diana,22,diana@example.com,True
```

---

## Example 14: Validate JSON File

```bash
python jsonquery.py validate data.json --no-color
```

**Expected output:**
```
VALID  'data.json' is valid JSON
  Size: 489 bytes
```

**For an invalid file:**
```bash
echo "{bad json" > bad.json
python jsonquery.py validate bad.json --no-color
```

**Expected output:**
```
INVALID  'bad.json' has JSON syntax errors
  Line 1, Column 10: Expecting property name enclosed in double quotes
  >>> {bad json
```

---

## Example 15: Count Elements

```bash
python jsonquery.py count data.json "$.users"
```

**Expected output:**
```
4
```

```bash
python jsonquery.py count data.json "$.tags"
```

**Expected output:**
```
4
```

---

## Example 16: Array Slice

```bash
python jsonquery.py get data.json "$.users[1:3]" --no-color --format table
```

**Expected output:**
```
+----+---------+-----+-------------------+--------+
| id | name    | age | email             | active |
+----+---------+-----+-------------------+--------+
| 2  | Bob     | 17  | bob@example.com   | False  |
| 3  | Charlie | 30  | charlie@admin.com | True   |
+----+---------+-----+-------------------+--------+
```

---

## Example 17: Pipe from Stdin

```bash
# Linux/macOS
cat data.json | python jsonquery.py get - "$.meta.total" --raw

# Windows PowerShell
Get-Content data.json | python jsonquery.py get - "$.meta.total" --raw
```

**Expected output:**
```
4
```

---

## Example 18: Search with Regex

```bash
python jsonquery.py search data.json "alice|charlie" --regex --no-color
```

**Expected output:**
```
Found 4 match(es) for 'alice|charlie':

  $.users[0].name (value)
    'Alice'

  $.users[0].email (value)
    'alice@example.com'

  $.users[2].name (value)
    'Charlie'

  $.users[2].email (value)
    'charlie@admin.com'
```

---

## Example 19: Keys-Only Search

```bash
python jsonquery.py search data.json "meta" --keys-only --no-color
```

**Expected output:**
```
Found 1 match(es) for 'meta':

  $.meta (key)
    {page, total, version}
```

---

## Example 20: Filter by Ends-With

```bash
python jsonquery.py filter data.json "$.users" "email$example.com" --no-color --format table
```

**Expected output:**
```
+----+-------+-----+-------------------+--------+
| id | name  | age | email             | active |
+----+-------+-----+-------------------+--------+
| 1  | Alice | 25  | alice@example.com | True   |
| 2  | Bob   | 17  | bob@example.com   | False  |
| 4  | Diana | 22  | diana@example.com | True   |
+----+-------+-----+-------------------+--------+
```

---

## Example 21: Python API Usage

```python
from jsonquery import JSONPathEvaluator, JSONFilter, load_json

# Load data
data = load_json("data.json")

# Get value at path
evaluator = JSONPathEvaluator()
names = evaluator.evaluate(data, "$.users[*].name")
print(names)
# ['Alice', 'Bob', 'Charlie', 'Diana']

# Filter array
filterer = JSONFilter()
adults = filterer.apply(data["users"], "age>=18")
print([u["name"] for u in adults])
# ['Alice', 'Charlie', 'Diana']

# Count
active_count = len(filterer.apply(data["users"], "active=true"))
print(f"{active_count} active users")
# 3 active users
```

---

## Example 22: Shell Script Integration

```bash
#!/bin/bash
# extract_emails.sh - Extract active user emails to a file

echo "Extracting active user emails..."

# Get active users, extract emails, save to CSV
python jsonquery.py filter data.json "$.users" "active=true" --format plain \
  | python jsonquery.py get - "$[*].email" --no-color \
  > active_emails.json

# Count
COUNT=$(python jsonquery.py count active_emails.json "$" --no-color)
echo "Found $COUNT active users"

# Validate the output
python jsonquery.py validate active_emails.json --no-color
```

---

*Examples built by ATLAS (Team Brain)*
*For Logan Smith / Metaphy LLC*
*"Quality is not an act, it is a habit!" ⚛️⚔️*
