"""
Explanation of Python's compile() function and how it's used in the executor.

The compile() function converts Python source code (or AST) into a code object
that can be executed by exec() or eval().
"""

import ast

# ───────────────────────────────────────────────────────────────
# UNDERSTANDING COMPILE()
# ───────────────────────────────────────────────────────────────

print("=" * 70)
print("UNDERSTANDING compile() FUNCTION")
print("=" * 70)

# ───────────────────────────────────────────────────────────────
# Example 1: compile() from source string
# ───────────────────────────────────────────────────────────────

print("\n1. Compiling from source string:")
print("-" * 70)

source_code = """
def add(a, b):
    return a + b

result = add(10, 20)
"""

# Compile the source code into a code object
code_obj = compile(source_code, filename="<example>", mode="exec")
print(f"Type of compiled object: {type(code_obj)}")
print(f"Code object: {code_obj}")

# Now we can execute it
namespace = {}
exec(code_obj, namespace)
print(f"Result after execution: {namespace.get('result')}")

# ───────────────────────────────────────────────────────────────
# Example 2: compile() from AST (like in executor)
# ───────────────────────────────────────────────────────────────

print("\n\n2. Compiling from AST (like executor does):")
print("-" * 70)

# Step 1: Parse source into AST
source = "result = 2 + 2"
tree = ast.parse(source)
print(f"AST tree type: {type(tree)}")
print(f"AST tree: {ast.dump(tree, indent=2)}")

# Step 2: Compile AST into code object
code_obj_from_ast = compile(tree, filename="<user_code>", mode="exec")
print(f"\nCompiled code object: {code_obj_from_ast}")

# Step 3: Execute the code object
namespace2 = {}
exec(code_obj_from_ast, namespace2)
print(f"Result: {namespace2.get('result')}")

# ───────────────────────────────────────────────────────────────
# Example 3: What happens in the executor
# ───────────────────────────────────────────────────────────────

print("\n\n3. What happens in the executor:")
print("-" * 70)

# User provides code
user_code = """
import math
result = math.sqrt(16)
"""

print(f"User code:\n{user_code}")

# Step 1: Parse to AST
tree = ast.parse(user_code)
print(f"\n✓ Parsed to AST")

# Step 2: Transform AST (simplified - executor does more)
# In executor: KeywordStripper, AwaitTransformer, etc.

# Step 3: Wrap in async function (like executor does)
async_func = ast.AsyncFunctionDef(
    name="__main",
    args=ast.arguments(posonlyargs=[], args=[], kwonlyargs=[], kw_defaults=[], defaults=[]),
    body=tree.body,
    decorator_list=[]
)
wrapper = ast.Module(body=[async_func], type_ignores=[])
ast.fix_missing_locations(wrapper)

print(f"✓ Wrapped in async function '__main'")

# Step 4: COMPILE - Convert AST to executable code object
compiled = compile(wrapper, filename="<user_code>", mode="exec")
print(f"✓ Compiled to code object: {type(compiled)}")

# Step 5: Execute (executor does this with sandbox globals)
print(f"✓ Ready to execute with exec()")

# ───────────────────────────────────────────────────────────────
# COMPILE() PARAMETERS EXPLAINED
# ───────────────────────────────────────────────────────────────

print("\n\n" + "=" * 70)
print("compile() PARAMETERS")
print("=" * 70)

print("""
compile(source, filename, mode, flags=0, dont_inherit=False, optimize=-1)

1. source: 
   - Can be a string (source code) OR an AST object
   - In executor: AST object (wrapper)

2. filename:
   - Name used in error messages and tracebacks
   - In executor: "<user_code>" (shows up in errors)

3. mode:
   - 'exec': For statements, modules, classes (returns None)
   - 'eval': For single expressions (returns value)
   - 'single': For interactive statements (like REPL)
   - In executor: 'exec' (because we're executing a block of code)

4. flags (optional):
   - Compiler flags (like ast.PyCF_ONLY_AST)
   
5. dont_inherit (optional):
   - Whether to inherit compiler flags
   
6. optimize (optional):
   - Optimization level (-1, 0, 1, 2)
""")

# ───────────────────────────────────────────────────────────────
# WHY COMPILE() IS NEEDED
# ───────────────────────────────────────────────────────────────

print("\n\n" + "=" * 70)
print("WHY compile() IS NEEDED IN THE EXECUTOR")
print("=" * 70)

print("""
The executor workflow:

1. User Code (string)
   ↓
2. ast.parse() → AST (Abstract Syntax Tree)
   ↓
3. AST Transformations (KeywordStripper, AwaitTransformer)
   ↓
4. Wrap in async function
   ↓
5. compile() → Code Object (bytecode)
   ↓
6. exec() → Execute the code object

Why compile()?
- AST is just a tree structure (data)
- Code object is executable bytecode (instructions)
- exec() needs a code object, not an AST
- compile() bridges the gap: AST → Code Object

Benefits:
- Can transform/modify code before execution
- Can control execution environment (globals/locals)
- Can catch syntax errors early
- Can optimize code before execution
""")

# ───────────────────────────────────────────────────────────────
# COMPARISON: Direct exec vs compile + exec
# ───────────────────────────────────────────────────────────────

print("\n\n" + "=" * 70)
print("COMPARISON: Direct exec() vs compile() + exec()")
print("=" * 70)

code_string = """

def add_numbers(a,b):

    result = a + b
    # print(result)
    return result

def print_pascal(row):

    for i in range(row):
        print(" " * (row - i - 1), end="")
        print("*" * (2 * i + 1), end="")
        print()

print_pascal(5)


result = add_numbers(100,200)
"""

print("\nMethod 1: Direct exec()")
print("-" * 70)
namespace1 = {}
exec(code_string, namespace1)
print(f"Result: {namespace1['result']}")
print("✓ Works, but can't transform code before execution")

print("\nMethod 2: compile() then exec()")
print("-" * 70)
code_obj = compile(code_string, "<test>", "exec")
namespace2 = {}
exec(code_obj, namespace2)
print(f"Result: {namespace2['result']}")
print("✓ Same result, but allows transformation between compile and exec")

print("\nMethod 3: AST transformation (like executor)")
print("-" * 70)
tree = ast.parse(code_string)
# Transform AST here (e.g., change 10 to 20)
for node in ast.walk(tree):
    if isinstance(node, ast.Constant) and node.value == 10:
        node.value = 20  # Transform: 10 → 20

compiled = compile(tree, "<test>", "exec")
namespace3 = {}
exec(compiled, namespace3)
print(f"Result: {namespace3['result']} (was transformed from 10*5 to 20*5)")
print("✓ This is why executor uses compile() - to transform code!")

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print("""
compile() converts Python source code or AST into executable bytecode.

In the executor:
- compile(wrapper, "<user_code>", "exec")
- wrapper = AST Module containing transformed code
- Returns a code object ready for exec()
- Allows code transformation before execution
- Enables sandboxed execution with custom globals
""")

