"""
Test file to demonstrate how the executor works.
Shows examples of what works and what doesn't.
"""

import asyncio
from action.executor import run_user_code


# ───────────────────────────────────────────────────────────────
# MOCK MCP CLASS FOR TESTING
# ───────────────────────────────────────────────────────────────
class MockTool:
    """Mock tool object that mimics MCP tool structure"""
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.inputSchema = {
            "type": "object",
            "properties": {
                "x": {"type": "number"},
                "y": {"type": "string"}
            }
        }


class MockMultiMCP:
    """Mock MultiMCP for testing without real MCP servers"""
    def __init__(self):
        self.tool_map = {}
        # Create some mock tools
        self.tools = [
            MockTool("add", "Adds two numbers"),
            MockTool("multiply", "Multiplies two numbers"),
            MockTool("greet", "Greets someone"),
        ]
        for tool in self.tools:
            self.tool_map[tool.name] = {"tool": tool, "config": {}}
    
    def get_all_tools(self):
        return self.tools
    
    async def function_wrapper(self, tool_name: str, *args):
        """Mock function wrapper that simulates tool execution"""
        await asyncio.sleep(0.01)  # Simulate async delay
        
        if tool_name == "add":
            return sum(args) if args else 0
        elif tool_name == "multiply":
            result = 1
            for arg in args:
                result *= arg
            return result
        elif tool_name == "greet":
            return f"Hello, {args[0] if args else 'World'}!"
        else:
            return f"Mock result from {tool_name} with args: {args}"


# ───────────────────────────────────────────────────────────────
# TEST EXAMPLES
# ───────────────────────────────────────────────────────────────

async def test_example(description: str, code: str, expected_status: str = "success"):
    """Run a test example and print results"""
    print(f"\n{'='*70}")
    print(f"TEST: {description}")
    print(f"{'='*70}")
    print(f"Code:\n{code}")
    print(f"\nExpected Status: {expected_status}")
    print("-" * 70)
    
    mock_mcp = MockMultiMCP()
    result = await run_user_code(code, mock_mcp)
    
    print(f"Status: {result['status']}")
    if result['status'] == 'success':
        print(f"Result: {result.get('result', 'None')}")
    else:
        print(f"Error: {result.get('error', 'Unknown error')}")
    print(f"Execution Time: {result.get('total_time', 'N/A')}s")
    
    return result


async def run_all_tests():
    """Run all test examples"""
    
    print("\n" + "="*70)
    print("EXECUTOR TEST SUITE")
    print("="*70)
    print("\nThis demonstrates how the executor handles different Python code patterns.")
    
    # ───────────────────────────────────────────────────────────────
    # ✅ WORKING EXAMPLES
    # ───────────────────────────────────────────────────────────────
    
    print("\n\n" + "="*70)
    print("✅ WORKING EXAMPLES")
    print("="*70)
    
    # Example 1: Basic arithmetic
    await test_example(
        "Basic arithmetic operations",
        """
result = 2 + 2
result = result * 3
"""
    )
    
    # Example 2: Using allowed modules
    await test_example(
        "Using math module (allowed)",
        """
import math
result = math.sqrt(16) + math.pi
"""
    )
    
    # Example 3: Lists and dictionaries
    await test_example(
        "Working with lists and dicts",
        """
numbers = [1, 2, 3, 4, 5]
result = sum(numbers)
data = {"key": "value", "num": 42}
result = f"{result} and {data['num']}"
"""
    )
    
    # Example 4: Using MCP tools (automatically awaited)
    await test_example(
        "Calling MCP tools (auto-awaited)",
        """
result = add(10, 20)
"""
    )
    
    # Example 5: Multiple MCP tool calls
    await test_example(
        "Multiple MCP tool calls",
        """
a = add(5, 3)
b = multiply(4, 2)
result = a + b
"""
    )
    
    # Example 6: Using json module
    await test_example(
        "Using json module",
        """
import json
data = {"name": "test", "value": 123}
result = json.dumps(data)
"""
    )
    
    # Example 7: String operations
    await test_example(
        "String operations",
        """
text = "Hello World"
result = text.upper().replace("WORLD", "Python")
"""
    )
    
    # Example 8: List comprehensions
    await test_example(
        "List comprehensions",
        """
numbers = [1, 2, 3, 4, 5]
squared = [x * x for x in numbers]
result = sum(squared)
"""
    )
    
    # Example 9: Explicit return statement
    await test_example(
        "Explicit return statement",
        """
def calculate():
    return 10 * 2

result = calculate()
"""
    )
    
    # Example 10: Using datetime
    await test_example(
        "Using datetime module",
        """
from datetime import datetime
now = datetime.now()
result = now.strftime("%Y-%m-%d")
"""
    )
    
    # ───────────────────────────────────────────────────────────────
    # ❌ FAILING EXAMPLES
    # ───────────────────────────────────────────────────────────────
    
    print("\n\n" + "="*70)
    print("❌ FAILING EXAMPLES (Expected to fail)")
    print("="*70)
    
    # Example 1: Too many function calls
    await test_example(
        "Too many function calls (>5 limit)",
        """
result = add(1, 1) + add(2, 2) + add(3, 3) + add(4, 4) + add(5, 5) + add(6, 6)
""",
        expected_status="error"
    )
    
    # Example 2: Keyword arguments (will be stripped, may cause issues)
    await test_example(
        "Keyword arguments (stripped to positional)",
        """
# Note: Keyword args are converted to positional, order matters!
result = add(x=10, y=20)  # This becomes add(10, 20)
""",
        expected_status="success"  # May still work if args match positionally
    )
    
    # Example 3: Restricted module
    await test_example(
        "Trying to import restricted module (os)",
        """
import os
result = os.getcwd()
""",
        expected_status="error"
    )
    
    # Example 4: Restricted builtin
    await test_example(
        "Trying to use restricted builtin (open)",
        """
result = open("test.txt", "r")
""",
        expected_status="error"
    )
    
    # Example 5: Using eval (not in allowed builtins)
    await test_example(
        "Trying to use eval (not allowed)",
        """
result = eval("2 + 2")
""",
        expected_status="error"
    )
    
    # Example 6: Syntax error
    await test_example(
        "Syntax error in code",
        """
result = 2 + 
""",
        expected_status="error"
    )
    
    # ───────────────────────────────────────────────────────────────
    # 🔍 EDGE CASES
    # ───────────────────────────────────────────────────────────────
    
    print("\n\n" + "="*70)
    print("🔍 EDGE CASES")
    print("="*70)
    
    # Example 1: Empty code
    await test_example(
        "Empty code",
        """
# Just a comment
result = None
"""
    )
    
    # Example 2: Code with only assignment, no return
    await test_example(
        "Assignment to 'result' (auto-return added)",
        """
result = "This will be automatically returned"
"""
    )
    
    # Example 3: Code with return statement
    await test_example(
        "Explicit return (no auto-return needed)",
        """
x = 10
return x * 2
"""
    )
    
    # Example 4: Nested function calls
    await test_example(
        "Nested function calls",
        """
result = add(multiply(2, 3), multiply(4, 5))
"""
    )
    
    # Example 5: Using parallel helper (if available)
    await test_example(
        "Using parallel execution helper",
        """
# Note: parallel() is available if multi_mcp is provided
result = "parallel() function available"
"""
    )


async def interactive_test():
    """Interactive mode to test custom code"""
    print("\n" + "="*70)
    print("INTERACTIVE TEST MODE")
    print("="*70)
    print("Enter Python code to test (type 'exit' to quit)")
    print("Note: Code will be executed in the sandboxed environment")
    print("-" * 70)
    
    mock_mcp = MockMultiMCP()
    
    while True:
        print("\n" + "-" * 70)
        code_lines = []
        print("Enter code (empty line to execute):")
        while True:
            line = input(">>> " if not code_lines else "... ")
            if not line and code_lines:
                break
            if line.lower() == 'exit':
                return
            code_lines.append(line)
        
        code = "\n".join(code_lines)
        if not code.strip():
            continue
        
        print("\nExecuting...")
        result = await run_user_code(code, mock_mcp)
        
        print(f"\nStatus: {result['status']}")
        if result['status'] == 'success':
            print(f"Result: {result.get('result', 'None')}")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
        print(f"Execution Time: {result.get('total_time', 'N/A')}s")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        asyncio.run(interactive_test())
    else:
        asyncio.run(run_all_tests())
        
    print("\n" + "="*70)
    print("TEST SUITE COMPLETE")
    print("="*70)
    print("\nRun with --interactive flag for interactive testing:")
    print("  python action/test_executor.py --interactive")

