"""
Quick test to understand the executor - simple examples
"""

import asyncio
from action.executor import run_user_code


class MockTool:
    def __init__(self, name: str):
        self.name = name
        self.description = ""
        self.inputSchema = {"type": "object", "properties": {}}


class MockMultiMCP:
    def __init__(self):
        self.tools = [MockTool("add"), MockTool("multiply")]
        self.tool_map = {t.name: {"tool": t, "config": {}} for t in self.tools}
    
    def get_all_tools(self):
        return self.tools
    
    async def function_wrapper(self, tool_name: str, *args):
        await asyncio.sleep(0.01)
        if tool_name == "add":
            return sum(args) if args else 0
        elif tool_name == "multiply":
            result = 1
            for arg in args:
                result *= arg
            return result
        return f"Result from {tool_name}"


async def main():
    mock_mcp = MockMultiMCP()
    
    print("=" * 60)
    print("QUICK EXECUTOR TEST")
    print("=" * 60)
    
    # Test 1: Basic math
    print("\n1. Basic Math:")
    code1 = "result = 2 + 2"
    result1 = await run_user_code(code1, mock_mcp)
    print(f"   Code: {code1}")
    print(f"   Status: {result1['status']}")
    print(f"   Result: {result1.get('result', 'N/A')}")
    
    # Test 2: Using math module
    print("\n2. Using Math Module:")
    code2 = """
import math
result = math.sqrt(16)
"""
    result2 = await run_user_code(code2, mock_mcp)
    print(f"   Code: import math; result = math.sqrt(16)")
    print(f"   Status: {result2['status']}")
    print(f"   Result: {result2.get('result', 'N/A')}")
    
    # Test 3: MCP tool call
    print("\n3. MCP Tool Call:")
    code3 = "result = add(10, 20)"
    result3 = await run_user_code(code3, mock_mcp)
    print(f"   Code: {code3}")
    print(f"   Status: {result3['status']}")
    print(f"   Result: {result3.get('result', 'N/A')}")
    
    # Test 4: Too many function calls
    print("\n4. Too Many Function Calls (should fail):")
    code4 = "result = add(1,1) + add(2,2) + add(3,3) + add(4,4) + add(5,5) + add(6,6)"
    result4 = await run_user_code(code4, mock_mcp)
    print(f"   Code: 6 function calls")
    print(f"   Status: {result4['status']}")
    print(f"   Error: {result4.get('error', 'N/A')}")
    
    # Test 5: Restricted module
    print("\n5. Restricted Module (should fail):")
    code5 = """
import os
result = os.getcwd()
"""
    result5 = await run_user_code(code5, mock_mcp)
    print(f"   Code: import os; result = os.getcwd()")
    print(f"   Status: {result5['status']}")
    print(f"   Error: {result5.get('error', 'N/A')}")
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

