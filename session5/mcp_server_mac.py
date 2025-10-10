# basic import 
from mcp.server.fastmcp import FastMCP, Image
from mcp.server.fastmcp.prompts import base
from mcp.types import TextContent
from mcp import types
from PIL import Image as PILImage
import math
import sys
import subprocess
import time
import shutil
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch

# instantiate an MCP server client
mcp = FastMCP("Calculator")

# Global variables
current_pdf_path = None
pdf_elements = []  # Store elements to draw on PDF

# DEFINE TOOLS

#addition tool
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    print("CALLED: add(a: int, b: int) -> int:")
    return int(a + b)

@mcp.tool()
def add_list(l: list) -> int:
    """Add all numbers in a list"""
    print("CALLED: add(l: list) -> int:")
    return sum(l)

# subtraction tool
@mcp.tool()
def subtract(a: int, b: int) -> int:
    """Subtract two numbers"""
    print("CALLED: subtract(a: int, b: int) -> int:")
    return int(a - b)

# multiplication tool
@mcp.tool()
def multiply(a: int, b: int) -> int:
    """Multiply two numbers"""
    print("CALLED: multiply(a: int, b: int) -> int:")
    return int(a * b)

#  division tool
@mcp.tool() 
def divide(a: int, b: int) -> float:
    """Divide two numbers"""
    print("CALLED: divide(a: int, b: int) -> float:")
    return float(a / b)

# power tool
@mcp.tool()
def power(a: int, b: int) -> int:
    """Power of two numbers"""
    print("CALLED: power(a: int, b: int) -> int:")
    return int(a ** b)

# square root tool
@mcp.tool()
def sqrt(a: int) -> float:
    """Square root of a number"""
    print("CALLED: sqrt(a: int) -> float:")
    return float(a ** 0.5)

# cube root tool
@mcp.tool()
def cbrt(a: int) -> float:
    """Cube root of a number"""
    print("CALLED: cbrt(a: int) -> float:")
    return float(a ** (1/3))

# factorial tool
@mcp.tool()
def factorial(a: int) -> int:
    """factorial of a number"""
    print("CALLED: factorial(a: int) -> int:")
    return int(math.factorial(a))

# log tool
@mcp.tool()
def log(a: int) -> float:
    """log of a number"""
    print("CALLED: log(a: int) -> float:")
    return float(math.log(a))

# remainder tool
@mcp.tool()
def remainder(a: int, b: int) -> int:
    """remainder of two numbers divison"""
    print("CALLED: remainder(a: int, b: int) -> int:")
    return int(a % b)

# sin tool
@mcp.tool()
def sin(a: int) -> float:
    """sin of a number"""
    print("CALLED: sin(a: int) -> float:")
    return float(math.sin(a))

# cos tool
@mcp.tool()
def cos(a: int) -> float:
    """cos of a number"""
    print("CALLED: cos(a: int) -> float:")
    return float(math.cos(a))

# tan tool
@mcp.tool()
def tan(a: int) -> float:
    """tan of a number"""
    print("CALLED: tan(a: int) -> float:")
    return float(math.tan(a))

# mine tool
@mcp.tool()
def mine(a: int, b: int) -> int:
    """special mining tool"""
    print("CALLED: mine(a: int, b: int) -> int:")
    return int(a - b - b)

@mcp.tool()
def create_thumbnail(image_path: str) -> Image:
    """Create a thumbnail from an image"""
    print("CALLED: create_thumbnail(image_path: str) -> Image:")
    img = PILImage.open(image_path)
    img.thumbnail((100, 100))
    return Image(data=img.tobytes(), format="png")

@mcp.tool()
def strings_to_chars_to_int(string: str) -> list[int]:
    """Return the ASCII values of the characters in a word"""
    print("CALLED: strings_to_chars_to_int(string: str) -> list[int]:")
    return [int(ord(char)) for char in string]

@mcp.tool()
def int_list_to_exponential_sum(int_list: list) -> str:
    """Return sum of exponentials of numbers in a list (formatted to 2 decimal places)"""
    print("CALLED: int_list_to_exponential_sum(int_list: list) -> str:")
    result = sum(math.exp(i) for i in int_list)
    # Format large numbers in scientific notation with 2 decimal places
    return f"{result:.2e}"

@mcp.tool()
def fibonacci_numbers(n: int) -> list:
    """Return the first n Fibonacci Numbers"""
    print("CALLED: fibonacci_numbers(n: int) -> list:")
    if n <= 0:
        return []
    fib_sequence = [0, 1]
    for _ in range(2, n):
        fib_sequence.append(fib_sequence[-1] + fib_sequence[-2])
    return fib_sequence[:n]

@mcp.tool()
async def open_preview_with_pdf() -> dict:
    """Create a new PDF for drawing and open it in Preview"""
    global current_pdf_path, pdf_elements
    try:
        # Create a unique filename for this session
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        current_pdf_path = f"/Users/kamran/Documents/EAGV2/EAGV2/session4/preview_results/drawing_{unique_id}.pdf"
        
        # Reset elements list
        pdf_elements = []
        
        # Create initial empty PDF
        c = canvas.Canvas(current_pdf_path, pagesize=letter)
        width, height = letter
        c.setTitle("MCP Drawing Canvas")
        c.showPage()
        c.save()
        
        # Open the PDF with Preview
        subprocess.run(["open", "-a", "Preview", current_pdf_path], check=True)
        time.sleep(1)  # Brief wait for Preview to open
        
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"PDF created and opened in Preview: {current_pdf_path}"
                )
            ]
        }
    except Exception as e:
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Error creating PDF: {str(e)}"
                )
            ]
        }

@mcp.tool()
async def draw_rectangle(x1: int, y1: int, x2: int, y2: int) -> dict:
    """Draw a rectangle directly on the PDF from (x1,y1) to (x2,y2)"""
    global current_pdf_path, pdf_elements
    try:
        if not current_pdf_path:
            return {
                "content": [
                    TextContent(
                        type="text",
                        text="No PDF is open. Please call open_preview_with_pdf first."
                    )
                ]
            }
        
        # Add rectangle to elements list
        pdf_elements.append({
            "type": "rectangle",
            "x1": x1, "y1": y1, "x2": x2, "y2": y2
        })
        
        # Regenerate the PDF with all elements
        await _regenerate_pdf()
        
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Rectangle drawn from ({x1},{y1}) to ({x2},{y2}) and PDF updated automatically"
                )
            ]
        }
    except Exception as e:
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Error drawing rectangle: {str(e)}"
                )
            ]
        }

@mcp.tool()
async def add_text_in_preview(text: str, x: int = 300, y: int = 300) -> dict:
    """Add text directly to the PDF at specified coordinates"""
    global current_pdf_path, pdf_elements
    try:
        if not current_pdf_path:
            return {
                "content": [
                    TextContent(
                        type="text",
                        text="No PDF is open. Please call open_preview_with_pdf first."
                    )
                ]
            }
        
        # Add text to elements list
        pdf_elements.append({
            "type": "text",
            "text": text,
            "x": x, "y": y
        })
        
        # Regenerate the PDF with all elements
        await _regenerate_pdf()
        
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Text '{text}' added at position ({x},{y}) and PDF updated automatically"
                )
            ]
        }
    except Exception as e:
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Error adding text: {str(e)}"
                )
            ]
        }

async def _regenerate_pdf():
    """Helper function to regenerate the PDF with all elements"""
    global current_pdf_path, pdf_elements
    
    if not current_pdf_path:
        return
    
    # Create new PDF with all elements
    c = canvas.Canvas(current_pdf_path, pagesize=letter)
    width, height = letter
    c.setTitle("MCP Drawing Canvas")
    
    # Draw all elements
    for element in pdf_elements:
        if element["type"] == "rectangle":
            # Convert coordinates (PDF coordinate system has origin at bottom-left)
            x1, y1, x2, y2 = element["x1"], element["y1"], element["x2"], element["y2"]
            # Flip Y coordinates for PDF
            pdf_y1 = height - y1
            pdf_y2 = height - y2
            
            # Draw rectangle
            c.setStrokeColor(colors.black)
            c.setLineWidth(2)
            c.rect(x1, min(pdf_y1, pdf_y2), abs(x2-x1), abs(pdf_y1-pdf_y2), stroke=1, fill=0)
            
        elif element["type"] == "text":
            # Convert coordinates
            x, y = element["x"], element["y"]
            pdf_y = height - y
            
            # Draw text
            c.setFont("Helvetica", 12)
            c.setFillColor(colors.black)
            c.drawString(x, pdf_y, element["text"])
    
    c.showPage()
    c.save()

@mcp.tool()
async def save_pdf() -> dict:
    """Save the current PDF (already saved automatically)"""
    global current_pdf_path
    try:
        if not current_pdf_path:
            return {
                "content": [
                    TextContent(
                        type="text",
                        text="No PDF is currently open."
                    )
                ]
            }
        
        # PDF is already saved automatically, just confirm
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"PDF is automatically saved: {current_pdf_path}"
                )
            ]
        }
    except Exception as e:
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Error with PDF: {str(e)}"
                )
            ]
        }

# DEFINE RESOURCES

# Add a dynamic greeting resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    print("CALLED: get_greeting(name: str) -> str:")
    return f"Hello, {name}!"


# DEFINE AVAILABLE PROMPTS
@mcp.prompt()
def review_code(code: str) -> str:
    return f"Please review this code:\n\n{code}"
    print("CALLED: review_code(code: str) -> str:")


@mcp.prompt()
def debug_error(error: str) -> list[base.Message]:
    return [
        base.UserMessage("I'm seeing this error:"),
        base.UserMessage(error),
        base.AssistantMessage("I'll help debug that. What have you tried so far?"),
    ]

if __name__ == "__main__":
    # Check if running with mcp dev command
    print("STARTING THE MAC MCP SERVER")
    if len(sys.argv) > 1 and sys.argv[1] == "dev":
        mcp.run()  # Run without transport for dev server
    else:
        mcp.run(transport="stdio")  # Run with stdio for direct execution
