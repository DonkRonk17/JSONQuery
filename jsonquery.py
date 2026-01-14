#!/usr/bin/env python3
"""
JSONQuery v1.0.0 - Smart JSON/YAML Query Tool
A powerful yet simple CLI tool for querying JSON and YAML with zero dependencies.

Author: Logan Smith / Metaphy LLC
License: MIT
GitHub: https://github.com/DonkRonk17/JSONQuery
"""

import sys
import io
import json
import re
import argparse
from pathlib import Path
from typing import Any, List, Dict, Union, Optional

# Ensure UTF-8 encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

__version__ = "1.0.0"


class Colors:
    """ANSI color codes for terminal output"""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    GRAY = '\033[90m'


class YAMLParser:
    """Simple YAML parser - supports basic YAML syntax"""
    
    @staticmethod
    def parse(text: str) -> Any:
        """Parse YAML text to Python objects"""
        lines = text.strip().split('\n')
        return YAMLParser._parse_lines(lines, 0)[0]
    
    @staticmethod
    def _parse_lines(lines: List[str], start_indent: int) -> tuple:
        """Parse lines starting from given indentation level"""
        result = {}
        current_list = []
        current_key = None
        i = 0
        in_list = False
        
        while i < len(lines):
            line = lines[i]
            
            # Skip empty lines and comments
            if not line.strip() or line.strip().startswith('#'):
                i += 1
                continue
            
            # Calculate indentation
            indent = len(line) - len(line.lstrip())
            
            # If indentation decreased, we're done with this level
            if indent < start_indent:
                break
            
            # If indentation increased, parse nested structure
            if indent > start_indent:
                if current_key:
                    # Nested dict or list
                    nested_result, lines_consumed = YAMLParser._parse_lines(lines[i:], indent)
                    result[current_key] = nested_result
                    i += lines_consumed
                    current_key = None
                    continue
                else:
                    i += 1
                    continue
            
            stripped = line.strip()
            
            # List item
            if stripped.startswith('- '):
                in_list = True
                value = stripped[2:].strip()
                
                # List item with key-value
                if ': ' in value:
                    key, val = value.split(': ', 1)
                    current_list.append({key: YAMLParser._parse_value(val)})
                else:
                    current_list.append(YAMLParser._parse_value(value))
                i += 1
                continue
            
            # Key-value pair
            if ': ' in stripped:
                key, value = stripped.split(': ', 1)
                key = key.strip()
                value = value.strip()
                
                if value:
                    result[key] = YAMLParser._parse_value(value)
                else:
                    # Value on next line(s)
                    current_key = key
                
                i += 1
                continue
            
            i += 1
        
        if in_list:
            return current_list, i
        
        return result if result else None, i
    
    @staticmethod
    def _parse_value(value: str) -> Any:
        """Parse YAML value to Python type"""
        value = value.strip()
        
        # Boolean
        if value.lower() in ('true', 'yes', 'on'):
            return True
        if value.lower() in ('false', 'no', 'off'):
            return False
        
        # Null
        if value.lower() in ('null', 'none', '~'):
            return None
        
        # Number
        try:
            if '.' in value:
                return float(value)
            return int(value)
        except ValueError:
            pass
        
        # String (remove quotes if present)
        if (value.startswith('"') and value.endswith('"')) or \
           (value.startswith("'") and value.endswith("'")):
            return value[1:-1]
        
        return value


def parse_query_path(path: str) -> List[Union[str, int]]:
    """
    Parse query path into components.
    Examples:
        'users' -> ['users']
        'users[0]' -> ['users', 0]
        'data.users[0].name' -> ['data', 'users', 0, 'name']
        'items[*]' -> ['items', '*']
    """
    components = []
    current = ''
    
    i = 0
    while i < len(path):
        char = path[i]
        
        if char == '.':
            if current:
                components.append(current)
                current = ''
        elif char == '[':
            if current:
                components.append(current)
                current = ''
            # Find matching ]
            j = i + 1
            while j < len(path) and path[j] != ']':
                j += 1
            index_str = path[i+1:j]
            if index_str == '*':
                components.append('*')
            else:
                try:
                    components.append(int(index_str))
                except ValueError:
                    components.append(index_str)
            i = j
        else:
            current += char
        
        i += 1
    
    if current:
        components.append(current)
    
    return components


def query_data(data: Any, path: List[Union[str, int]]) -> Any:
    """
    Query data using parsed path.
    Supports wildcards (*) for array iteration.
    """
    if not path:
        return data
    
    component = path[0]
    remaining = path[1:]
    
    # Wildcard - iterate over all items
    if component == '*':
        if isinstance(data, list):
            results = []
            for item in data:
                result = query_data(item, remaining)
                if result is not None:
                    results.append(result)
            return results if results else None
        else:
            return None
    
    # Dictionary access
    if isinstance(data, dict):
        if component in data:
            return query_data(data[component], remaining)
        else:
            return None
    
    # List access by index
    if isinstance(data, list):
        if isinstance(component, int):
            try:
                return query_data(data[component], remaining)
            except IndexError:
                return None
        else:
            # Try to access key in dict items
            results = []
            for item in data:
                if isinstance(item, dict) and component in item:
                    result = query_data(item[component], remaining)
                    if result is not None:
                        results.append(result)
            return results if results else None
    
    return None


def filter_data(data: Any, filter_expr: str) -> Any:
    """
    Filter data based on expression.
    Examples:
        'name == "John"' - match name exactly
        'age > 25' - age greater than 25
        'active == true' - boolean match
        'email ~ "@example.com"' - regex match
    """
    if not filter_expr:
        return data
    
    # Parse filter expression
    operators = ['==', '!=', '>=', '<=', '>', '<', '~']
    operator = None
    key = None
    value = None
    
    for op in operators:
        if op in filter_expr:
            parts = filter_expr.split(op, 1)
            key = parts[0].strip()
            value = parts[1].strip()
            operator = op
            break
    
    if not operator:
        return data
    
    # Parse value
    parsed_value = parse_filter_value(value)
    
    # Apply filter
    if isinstance(data, list):
        filtered = []
        for item in data:
            if isinstance(item, dict) and key in item:
                item_value = item[key]
                if check_condition(item_value, operator, parsed_value):
                    filtered.append(item)
        return filtered
    elif isinstance(data, dict) and key in data:
        if check_condition(data[key], operator, parsed_value):
            return data
    
    return None


def parse_filter_value(value: str) -> Any:
    """Parse filter value to appropriate type"""
    value = value.strip()
    
    # Remove quotes
    if (value.startswith('"') and value.endswith('"')) or \
       (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    
    # Boolean
    if value.lower() == 'true':
        return True
    if value.lower() == 'false':
        return False
    
    # Null
    if value.lower() in ('null', 'none'):
        return None
    
    # Number
    try:
        if '.' in value:
            return float(value)
        return int(value)
    except ValueError:
        pass
    
    return value


def check_condition(item_value: Any, operator: str, filter_value: Any) -> bool:
    """Check if condition is met"""
    try:
        if operator == '==':
            return item_value == filter_value
        elif operator == '!=':
            return item_value != filter_value
        elif operator == '>':
            return item_value > filter_value
        elif operator == '<':
            return item_value < filter_value
        elif operator == '>=':
            return item_value >= filter_value
        elif operator == '<=':
            return item_value <= filter_value
        elif operator == '~':
            # Regex match
            if isinstance(item_value, str) and isinstance(filter_value, str):
                return re.search(filter_value, item_value) is not None
    except (TypeError, AttributeError):
        return False
    
    return False


def search_data(data: Any, pattern: str, case_sensitive: bool = False) -> List[tuple]:
    """
    Search for pattern in all string values.
    Returns list of (path, value) tuples.
    """
    results = []
    flags = 0 if case_sensitive else re.IGNORECASE
    
    def search_recursive(obj: Any, path: str = ''):
        if isinstance(obj, dict):
            for key, value in obj.items():
                new_path = f"{path}.{key}" if path else key
                search_recursive(value, new_path)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                new_path = f"{path}[{i}]"
                search_recursive(item, new_path)
        elif isinstance(obj, str):
            if re.search(pattern, obj, flags):
                results.append((path, obj))
    
    search_recursive(data)
    return results


def calculate_stats(data: Any) -> Dict[str, Any]:
    """Calculate statistics on numeric data"""
    numbers = []
    
    def collect_numbers(obj: Any):
        if isinstance(obj, (int, float)):
            numbers.append(obj)
        elif isinstance(obj, dict):
            for value in obj.values():
                collect_numbers(value)
        elif isinstance(obj, list):
            for item in obj:
                collect_numbers(item)
    
    collect_numbers(data)
    
    if not numbers:
        return {'error': 'No numeric values found'}
    
    return {
        'count': len(numbers),
        'sum': sum(numbers),
        'avg': sum(numbers) / len(numbers),
        'min': min(numbers),
        'max': max(numbers)
    }


def format_output(data: Any, format: str, pretty: bool = True) -> str:
    """Format data for output"""
    if data is None:
        return 'null'
    
    if format == 'json':
        indent = 2 if pretty else None
        return json.dumps(data, indent=indent, ensure_ascii=False)
    
    elif format == 'csv':
        # Simple CSV output for list of dicts
        if isinstance(data, list) and data and isinstance(data[0], dict):
            lines = []
            # Header
            headers = list(data[0].keys())
            lines.append(','.join(str(h) for h in headers))
            # Rows
            for item in data:
                row = [str(item.get(h, '')) for h in headers]
                lines.append(','.join(row))
            return '\n'.join(lines)
        else:
            return json.dumps(data)
    
    elif format == 'keys':
        # Show only keys
        if isinstance(data, dict):
            return '\n'.join(data.keys())
        elif isinstance(data, list) and data and isinstance(data[0], dict):
            return '\n'.join(data[0].keys())
        else:
            return 'Not a dictionary'
    
    elif format == 'values':
        # Show only values
        if isinstance(data, dict):
            return '\n'.join(str(v) for v in data.values())
        elif isinstance(data, list):
            return '\n'.join(str(v) for v in data)
        else:
            return str(data)
    
    elif format == 'plain':
        # Plain text output
        if isinstance(data, (list, dict)):
            return json.dumps(data, indent=2, ensure_ascii=False)
        else:
            return str(data)
    
    return str(data)


def print_banner():
    """Print JSONQuery banner"""
    banner = f"""
{Colors.CYAN}╔═══════════════════════════════════════════════════╗
║  {Colors.BOLD}JSONQuery v{__version__}{Colors.RESET}{Colors.CYAN} - Smart JSON/YAML Query  ║
║  Zero dependencies • Simple • Powerful            ║
╚═══════════════════════════════════════════════════╝{Colors.RESET}
"""
    print(banner)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='JSONQuery - Smart JSON/YAML Query Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Query path
  jsonquery data.json users[0].name
  jsonquery data.json 'items[*].price'
  
  # Filter
  jsonquery data.json users --filter 'age > 25'
  jsonquery data.json items --filter 'active == true'
  
  # Search
  jsonquery data.json --search '@example.com'
  
  # Statistics
  jsonquery data.json items[*].price --stats
  
  # Output formats
  jsonquery data.json users --format csv
  jsonquery data.json data --format keys
  
  # From stdin
  cat data.json | jsonquery - users[0]
  curl https://api.example.com/data | jsonquery -
        """
    )
    
    parser.add_argument('file', help='JSON/YAML file or - for stdin')
    parser.add_argument('query', nargs='?', default='', help='Query path (e.g., users[0].name)')
    parser.add_argument('-f', '--filter', help='Filter expression (e.g., age > 25)')
    parser.add_argument('-s', '--search', help='Search pattern (regex)')
    parser.add_argument('--case-sensitive', action='store_true', help='Case-sensitive search')
    parser.add_argument('--stats', action='store_true', help='Calculate statistics on numeric values')
    parser.add_argument('--format', choices=['json', 'csv', 'keys', 'values', 'plain'], 
                       default='json', help='Output format (default: json)')
    parser.add_argument('--no-pretty', action='store_true', help='Disable pretty printing')
    parser.add_argument('--yaml', action='store_true', help='Parse as YAML')
    parser.add_argument('-v', '--version', action='version', version=f'JSONQuery v{__version__}')
    
    args = parser.parse_args()
    
    # Read input
    try:
        if args.file == '-':
            content = sys.stdin.read()
        else:
            with open(args.file, 'r', encoding='utf-8') as f:
                content = f.read()
    except FileNotFoundError:
        print(f"{Colors.RED}✗ File not found: {args.file}{Colors.RESET}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"{Colors.RED}✗ Error reading file: {e}{Colors.RESET}", file=sys.stderr)
        return 1
    
    # Parse data
    try:
        if args.yaml or (args.file != '-' and args.file.endswith(('.yaml', '.yml'))):
            data = YAMLParser.parse(content)
        else:
            data = json.loads(content)
    except json.JSONDecodeError as e:
        print(f"{Colors.RED}✗ Invalid JSON: {e}{Colors.RESET}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"{Colors.RED}✗ Error parsing data: {e}{Colors.RESET}", file=sys.stderr)
        return 1
    
    # Apply query
    if args.query:
        try:
            path = parse_query_path(args.query)
            data = query_data(data, path)
            
            if data is None:
                print(f"{Colors.YELLOW}No results found{Colors.RESET}", file=sys.stderr)
                return 0
        except Exception as e:
            print(f"{Colors.RED}✗ Query error: {e}{Colors.RESET}", file=sys.stderr)
            return 1
    
    # Apply filter
    if args.filter:
        try:
            data = filter_data(data, args.filter)
            
            if not data:
                print(f"{Colors.YELLOW}No results match filter{Colors.RESET}", file=sys.stderr)
                return 0
        except Exception as e:
            print(f"{Colors.RED}✗ Filter error: {e}{Colors.RESET}", file=sys.stderr)
            return 1
    
    # Search
    if args.search:
        try:
            results = search_data(data, args.search, args.case_sensitive)
            
            if not results:
                print(f"{Colors.YELLOW}No matches found{Colors.RESET}", file=sys.stderr)
                return 0
            
            # Format search results
            for path, value in results:
                print(f"{Colors.CYAN}{path}{Colors.RESET}: {value}")
            return 0
        except Exception as e:
            print(f"{Colors.RED}✗ Search error: {e}{Colors.RESET}", file=sys.stderr)
            return 1
    
    # Statistics
    if args.stats:
        stats = calculate_stats(data)
        print(format_output(stats, 'json', not args.no_pretty))
        return 0
    
    # Output
    try:
        output = format_output(data, args.format, not args.no_pretty)
        print(output)
    except Exception as e:
        print(f"{Colors.RED}✗ Output error: {e}{Colors.RESET}", file=sys.stderr)
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
