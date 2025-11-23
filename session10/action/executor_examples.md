# Executor Examples and Documentation

This document explains how the executor works with practical examples.

## How the Executor Works

The executor is a **sandboxed Python code runner** that:

1. **Parses** user code into an Abstract Syntax Tree (AST)
2. **Transforms** the AST to:
   - Strip keyword arguments (convert to positional)
   - Auto-await MCP tool calls
   - Wrap everything in an async function
3. **Executes** the transformed code in a restricted environment
4. **Returns** results or errors

## Key Features

### ✅ What Works

#### 1. Basic Python Operations
```python
result = 2 + 2
result = [1, 2, 3]
result = {"key": "value"}
```

#### 2. Allowed Modules
The executor allows these modules:
- `math`, `json`, `datetime`, `time`, `calendar`
- `collections`, `itertools`, `functools`
- `re`, `string`, `textwrap`
- `pathlib`, `tempfile`
- `csv`, `sqlite3`
- And more (see `ALLOWED_MODULES` in executor.py)

```python
import math
result = math.sqrt(16)

import json
result = json.dumps({"a": 1})
```

#### 3. MCP Tools (Auto-Awaited)
MCP tools are automatically wrapped with `await`:

```python
# This code:
result = add(10, 20)

# Is transformed to:
result = await add(10, 20)
```

#### 4. Auto-Return Detection
If you assign to `result` but don't return, it's automatically returned:

```python
# This code:
result = 42

# Becomes:
result = 42
return result
```

### ❌ What Doesn't Work

#### 1. Function Call Limit
Maximum **5 function calls** per code block:

```python
# ❌ This will fail:
result = func1() + func2() + func3() + func4() + func5() + func6()
# Error: "Too many functions (6 > 5)"
```

#### 2. Keyword Arguments Are Stripped
Keyword arguments are converted to positional:

```python
# This code:
func(key="value", num=42)

# Becomes:
func("value", 42)  # Order matters!
```

#### 3. Restricted Modules
Many modules are not allowed:

```python
# ❌ These won't work:
import os
import sys
import subprocess
import requests
```

#### 4. Restricted Builtins
Only these builtins are available:
- `range`, `len`, `int`, `float`, `str`, `list`, `dict`, `print`, `sum`, `__import__`

```python
# ❌ These won't work:
open()   # File operations not allowed
eval()   # Code execution not allowed
exec()   # Code execution not allowed
```

#### 5. Everything Runs Async
Your code is wrapped in an async function, but you can't use `await` explicitly:

```python
# ❌ This won't work:
await some_function()

# ✅ But MCP tools are auto-awaited:
result = mcp_tool()  # Automatically awaited
```

## Code Transformation Examples

### Example 1: Simple Calculation

**Input:**
```python
result = 2 + 2
```

**Transformed (conceptually):**
```python
async def __main():
    result = 2 + 2
    return result
```

### Example 2: With MCP Tool

**Input:**
```python
result = add(10, 20)
```

**Transformed (conceptually):**
```python
async def __main():
    result = await add(10, 20)
    return result
```

### Example 3: Keyword Arguments

**Input:**
```python
result = add(x=10, y=20)
```

**Transformed (conceptually):**
```python
async def __main():
    result = await add(10, 20)  # Keywords stripped, order matters!
    return result
```

## Running Tests

### Run All Examples
```bash
python action/test_executor.py
```

### Interactive Mode
```bash
python action/test_executor.py --interactive
```

## Understanding the Output

The executor returns a dictionary:

```python
{
    "status": "success" | "error",
    "result": "string representation of result",  # if success
    "error": "error message",  # if error
    "execution_time": "2025-01-08 12:34:56",
    "total_time": "0.123"  # seconds
}
```

## Common Patterns

### Pattern 1: Simple Calculation
```python
result = 10 * 5
```

### Pattern 2: Using Modules
```python
import math
result = math.sqrt(144)
```

### Pattern 3: Multiple Steps
```python
a = 10
b = 20
result = a + b
```

### Pattern 4: MCP Tool Calls
```python
value1 = add(5, 3)
value2 = multiply(4, 2)
result = value1 + value2
```

### Pattern 5: List Operations
```python
numbers = [1, 2, 3, 4, 5]
result = sum(numbers)
```

## Limitations Summary

| Feature | Status | Notes |
|---------|--------|-------|
| Basic Python | ✅ | Works |
| Allowed Modules | ✅ | See `ALLOWED_MODULES` |
| MCP Tools | ✅ | Auto-awaited |
| Function Calls | ⚠️ | Max 5 calls |
| Keyword Args | ⚠️ | Stripped to positional |
| Restricted Modules | ❌ | os, sys, etc. blocked |
| Restricted Builtins | ❌ | open, eval, etc. blocked |
| File I/O | ❌ | Not allowed |
| Network | ❌ | Not allowed |
| System Calls | ❌ | Not allowed |

## Tips

1. **Keep it simple**: The executor is designed for simple calculations and tool calls
2. **Use positional args**: Don't rely on keyword arguments
3. **Watch function count**: Stay under 5 function calls
4. **Use allowed modules**: Check `ALLOWED_MODULES` before importing
5. **Assign to `result`**: The executor will auto-return it

