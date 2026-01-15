<img width="1536" height="1024" alt="image" src="https://github.com/user-attachments/assets/72671ae4-f15c-4f5d-92d7-695731ca468e" />

# 🔍 JSONQuery - Smart JSON/YAML Query Tool

**Version:** 1.0.0  
**Author:** Logan Smith / Metaphy LLC  
**License:** MIT  
**GitHub:** https://github.com/DonkRonk17/JSONQuery

---

## 📖 Overview

**JSONQuery** is a powerful yet simple command-line tool for querying and manipulating JSON and YAML data. It provides an intuitive query syntax that's easier than `jq` while maintaining **zero external dependencies**.

Perfect for developers who need to extract data from API responses, configuration files, or any JSON/YAML document without installing complex tools or learning cryptic syntax.

---

## ✨ Features

### 🎯 Core Capabilities
- **Path Queries** - Simple dot notation (`users[0].name`)
- **Wildcards** - Query all array items (`items[*].price`)
- **Filtering** - SQL-like filter expressions (`age > 25`)
- **Search** - Regex search across all values
- **Statistics** - Calculate sum, avg, min, max, count
- **Multiple Formats** - Output as JSON, CSV, keys, values, or plain text
- **YAML Support** - Built-in YAML parser (zero dependencies!)
- **Stdin Support** - Pipe data from curl, cat, etc.
- **Zero Dependencies** - Pure Python stdlib
- **Cross-Platform** - Works on Windows, Linux, macOS

### 🎨 User Experience
- **Intuitive Syntax** - Easier than jq, more powerful than grep
- **Pretty Output** - Formatted JSON by default
- **Color Support** - Readable terminal output
- **Fast** - Pure Python, instant startup
- **Portable** - Single file, no installation required

---

## 🚀 Quick Start

### Installation

**Option 1: Direct Download (Recommended)**
```bash
# Download the script
curl -O https://raw.githubusercontent.com/DonkRonk17/JSONQuery/main/jsonquery.py

# Make it executable (Linux/macOS)
chmod +x jsonquery.py

# Run it
python jsonquery.py data.json
```

**Option 2: Clone Repository**
```bash
git clone https://github.com/DonkRonk17/JSONQuery.git
cd JSONQuery
python jsonquery.py data.json
```

**Option 3: Install with setup.py**
```bash
git clone https://github.com/DonkRonk17/JSONQuery.git
cd JSONQuery
pip install -e .

# Now use 'jsonquery' command directly
jsonquery data.json users
```

### System Requirements
- **Python 3.6+** (included with most systems)
- **No external dependencies** - uses only Python standard library

---

## 📚 Usage Guide

### Basic Queries

**Get entire file**
```bash
jsonquery data.json
```

**Get specific key**
```bash
jsonquery data.json users
```

**Get nested key**
```bash
jsonquery data.json data.users
```

**Get array element**
```bash
jsonquery data.json users[0]
```

**Get nested array element**
```bash
jsonquery data.json users[0].name
```

**Get all array elements (wildcard)**
```bash
jsonquery data.json 'users[*].name'
```

### Filtering

**Numeric comparison**
```bash
jsonquery data.json users --filter 'age > 25'
jsonquery data.json items --filter 'price >= 100'
jsonquery data.json products --filter 'quantity < 10'
```

**Exact match**
```bash
jsonquery data.json users --filter 'name == "John"'
jsonquery data.json items --filter 'active == true'
```

**Not equal**
```bash
jsonquery data.json users --filter 'status != "inactive"'
```

**Regex match**
```bash
jsonquery data.json users --filter 'email ~ "@example.com"'
```

### Search

**Search for pattern in all values**
```bash
jsonquery data.json --search 'example'
```

**Case-sensitive search**
```bash
jsonquery data.json --search 'Example' --case-sensitive
```

**Regex search**
```bash
jsonquery data.json --search '\d{3}-\d{4}'
```

### Statistics

**Calculate stats on numeric values**
```bash
jsonquery data.json items[*].price --stats
```

Output:
```json
{
  "count": 10,
  "sum": 450.5,
  "avg": 45.05,
  "min": 10.0,
  "max": 99.99
}
```

### Output Formats

**JSON (default)**
```bash
jsonquery data.json users
```

**CSV (for arrays of objects)**
```bash
jsonquery data.json users --format csv
```

**Keys only**
```bash
jsonquery data.json data --format keys
```

**Values only**
```bash
jsonquery data.json users[0] --format values
```

**Plain text**
```bash
jsonquery data.json users[0].name --format plain
```

**Compact JSON (no pretty print)**
```bash
jsonquery data.json users --no-pretty
```

### YAML Support

**Parse YAML file**
```bash
jsonquery config.yaml database.host --yaml
```

**Auto-detect from extension**
```bash
jsonquery config.yml settings.port
```

### Stdin Input

**From curl**
```bash
curl https://api.github.com/users/octocat | jsonquery - name
```

**From cat**
```bash
cat data.json | jsonquery - users[0].email
```

**From echo**
```bash
echo '{"name": "John", "age": 30}' | jsonquery - age
```

---

## 🎯 Real-World Examples

### Example 1: GitHub API

```bash
# Get user's name
curl -s https://api.github.com/users/octocat | jsonquery - name

# Get follower count
curl -s https://api.github.com/users/octocat | jsonquery - followers

# Get all repository names
curl -s https://api.github.com/users/octocat/repos | jsonquery - '[*].name'
```

### Example 2: Package.json

```bash
# Get project name
jsonquery package.json name

# Get all dependencies
jsonquery package.json dependencies --format keys

# Get scripts
jsonquery package.json scripts --format json
```

### Example 3: Configuration Files

```bash
# Get database host
jsonquery config.json database.host

# Get all API endpoints
jsonquery config.json 'api.endpoints[*].url'

# Find all configs with debug enabled
jsonquery config.json --filter 'debug == true'
```

### Example 4: Data Analysis

```bash
# Get all products over $50
jsonquery products.json items --filter 'price > 50'

# Calculate average price
jsonquery products.json 'items[*].price' --stats

# Export to CSV
jsonquery users.json users --format csv > users.csv
```

### Example 5: Docker Compose

```bash
# Get all service names
jsonquery docker-compose.yml services --format keys --yaml

# Get specific service ports
jsonquery docker-compose.yml services.web.ports --yaml

# Find services with restart policy
jsonquery docker-compose.yml --search 'restart: always' --yaml
```

### Example 6: API Testing Workflow

```bash
# Make API call and extract data
curl -s https://api.example.com/data | \
  jsonquery - 'results[*]' --filter 'active == true' --format csv

# Chain with other tools
curl -s https://api.example.com/users | \
  jsonquery - 'users[*].email' --format values | \
  sort | uniq

# Get stats from API
curl -s https://api.example.com/metrics | \
  jsonquery - 'data[*].value' --stats
```

---

## 📖 Query Syntax Guide

### Path Notation

| Syntax | Description | Example |
|--------|-------------|---------|
| `key` | Access dictionary key | `name` |
| `key1.key2` | Nested keys | `user.profile.name` |
| `[0]` | Array index | `users[0]` |
| `key[0]` | Key then index | `users[0].name` |
| `[*]` | All array elements | `items[*].price` |
| `key[*].subkey` | Wildcard with path | `users[*].email` |

### Filter Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `==` | Equal to | `age == 25` |
| `!=` | Not equal to | `status != "active"` |
| `>` | Greater than | `price > 100` |
| `<` | Less than | `quantity < 10` |
| `>=` | Greater or equal | `score >= 80` |
| `<=` | Less or equal | `age <= 30` |
| `~` | Regex match | `email ~ "@gmail.com"` |

### Value Types

| Type | Example | Notes |
|------|---------|-------|
| String | `"text"` or `'text'` | Quotes optional for single words |
| Number | `123` or `45.67` | Integer or float |
| Boolean | `true` or `false` | Case-insensitive |
| Null | `null` or `none` | Case-insensitive |

---

## 🆚 Comparison

| Feature | JSONQuery | jq | grep | Python script |
|---------|-----------|----|----- |---------------|
| **Zero Dependencies** | ✅ | ❌ | ✅ | ⚠️ |
| **Simple Syntax** | ✅ | ⚠️ | ⚠️ | ❌ |
| **JSON Support** | ✅ | ✅ | ❌ | ✅ |
| **YAML Support** | ✅ | ❌ | ❌ | ⚠️ |
| **Filtering** | ✅ | ✅ | ❌ | ✅ |
| **Statistics** | ✅ | ✅ | ❌ | ✅ |
| **CSV Output** | ✅ | ✅ | ❌ | ✅ |
| **Learning Curve** | Low | High | Low | High |
| **File Size** | <50KB | ~1MB | Built-in | Varies |

**JSONQuery = jq power + grep simplicity - dependencies**

---

## 🔧 Advanced Usage

### Combining Queries

```bash
# Query then filter
jsonquery data.json users --filter 'age > 25' --format csv

# Query then search
jsonquery data.json users[*] --search '@example.com'

# Query then stats
jsonquery data.json 'sales[*].amount' --stats
```

### Piping with Other Tools

```bash
# Count results
jsonquery data.json users --format values | wc -l

# Sort results
jsonquery data.json 'users[*].name' --format values | sort

# Unique values
jsonquery data.json 'items[*].category' --format values | sort | uniq

# Combine with grep
jsonquery data.json users --format csv | grep '@gmail.com'
```

### Shell Scripting

```bash
#!/bin/bash

# Extract API token
TOKEN=$(jsonquery config.json api.token --format plain)

# Get all user IDs
IDS=$(jsonquery users.json 'users[*].id' --format values)

# Process each ID
for id in $IDS; do
  curl -H "Authorization: Bearer $TOKEN" \
    https://api.example.com/users/$id
done
```

### Data Transformation

```bash
# JSON to CSV pipeline
jsonquery data.json users --format csv > users.csv

# Extract specific fields
jsonquery data.json 'users[*]' | \
  jsonquery - '[*].email' --format values > emails.txt

# Filter and export
jsonquery data.json items --filter 'active == true' --format csv | \
  csvtool col 1,2,3 -
```

---

## 📂 Data Examples

### Example JSON File (users.json)

```json
{
  "users": [
    {
      "id": 1,
      "name": "John Doe",
      "email": "john@example.com",
      "age": 30,
      "active": true
    },
    {
      "id": 2,
      "name": "Jane Smith",
      "email": "jane@example.com",
      "age": 25,
      "active": false
    }
  ],
  "metadata": {
    "total": 2,
    "page": 1
  }
}
```

**Queries:**
```bash
# Get all user names
jsonquery users.json 'users[*].name'

# Get active users
jsonquery users.json users --filter 'active == true'

# Get metadata total
jsonquery users.json metadata.total

# Calculate average age
jsonquery users.json 'users[*].age' --stats
```

### Example YAML File (config.yml)

```yaml
database:
  host: localhost
  port: 5432
  name: myapp

services:
  - name: web
    port: 8080
    replicas: 3
  - name: api
    port: 9000
    replicas: 2
```

**Queries:**
```bash
# Get database host
jsonquery config.yml database.host

# Get all service names
jsonquery config.yml 'services[*].name'

# Get services with more than 2 replicas
jsonquery config.yml services --filter 'replicas > 2'
```

---

## 🐛 Troubleshooting

### Issue: "Invalid JSON" Error

```bash
# Validate JSON first
python -m json.tool data.json

# Check for trailing commas, single quotes
# JSON requires double quotes and no trailing commas
```

### Issue: Query Returns Nothing

```bash
# Check if path exists
jsonquery data.json  # View entire structure first

# Use verbose errors (check spelling, case)
# Remember: JSON is case-sensitive
```

### Issue: YAML Not Parsing

```bash
# Explicitly specify YAML
jsonquery config.yaml --yaml

# Or rename file to .yml/.yaml for auto-detection
```

### Issue: Wildcard Not Working

```bash
# Quote wildcards in shell
jsonquery data.json 'items[*].name'  # Good
jsonquery data.json items[*].name    # Bad (shell expands *)
```

---

## 🎓 Tips & Best Practices

### 1. Start Simple, Then Add Complexity
```bash
# Good progression
jsonquery data.json users                    # Step 1: Get array
jsonquery data.json users[0]                 # Step 2: Get item
jsonquery data.json users[0].name            # Step 3: Get value
jsonquery data.json users --filter 'age > 25' # Step 4: Add filter
```

### 2. Use Format Options for Integration
```bash
# Good: CSV for spreadsheets
jsonquery data.json users --format csv > users.csv

# Good: Values for shell scripting
for email in $(jsonquery data.json 'users[*].email' --format values); do
  echo "Sending to $email"
done
```

### 3. Combine with Other Tools
```bash
# Good: Use with curl
curl -s https://api.example.com/data | jsonquery - result

# Good: Use with jq for advanced features
jsonquery data.json users | jq 'map(.name)'
```

### 4. Quote Complex Queries
```bash
# Good
jsonquery data.json 'users[*].profile.settings'

# Bad (shell misinterprets)
jsonquery data.json users[*].profile.settings
```

---

## 📊 Project Statistics

- **Lines of Code:** ~650
- **Dependencies:** 0 (pure Python stdlib)
- **File Size:** ~25 KB
- **Python Version:** 3.6+
- **Platforms:** Windows, Linux, macOS
- **Query Types:** 7 (path, filter, search, stats, keys, values, wildcard)
- **Output Formats:** 5 (JSON, CSV, keys, values, plain)

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 📄 License

MIT License - see LICENSE file for details

---

## 🔗 Links

- **GitHub Repository:** https://github.com/DonkRonk17/JSONQuery
- **Report Issues:** https://github.com/DonkRonk17/JSONQuery/issues
- **Author:** Logan Smith / Metaphy LLC

---
<img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/7d596c28-9bbb-437d-829e-a558504fa263" />



## 🌟 Why JSONQuery?

**JSONQuery was built to solve a simple problem:** developers need to query JSON/YAML data quickly without installing complex tools or learning arcane syntax.

### Perfect For:
- 🔍 **API Response Analysis** - Extract data from REST APIs
- ⚙️ **Configuration Management** - Query config files
- 📊 **Data Exploration** - Understand JSON structure
- 🤖 **Shell Scripting** - Integrate into automation
- 🧪 **Testing** - Validate API responses
- 📝 **Documentation** - Extract examples from data

### Not For:
- ❌ Complex transformations (use jq)
- ❌ Large-scale data processing (use pandas)
- ❌ Binary formats (use specialized tools)

---

**Built with ❤️ by the Holy Grail Automation System**

**Zero dependencies. Maximum utility. Pure Python.**
