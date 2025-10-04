#!/usr/bin/env python3
"""
Test client to verify Preview drawing and text capabilities work correctly.
"""

import asyncio
import os
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_preview_capabilities():
    """Test each Preview capability individually"""
    print("🚀 Starting Preview Capabilities Test")
    print("="*50)
    
    try:
        # Create MCP server connection
        print("📡 Connecting to Mac MCP server...")
        server_params = StdioServerParameters(
            command="uv",
            args=["run", "python", "mcp_server_mac.py"]
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # Test 1: Open Preview with PDF
                print("\n📖 Test 1: Opening Preview with empty PDF...")
                result = await session.call_tool("open_preview_with_pdf")
                print(f"✅ Result: {result.content[0].text}")
                
                # Wait for Preview to fully load
                await asyncio.sleep(3)
                
                # Test 2: Draw Rectangle at center coordinates
                print("\n📐 Test 2: Drawing rectangle at center (200,200) to (400,300)...")
                result = await session.call_tool("draw_rectangle", {
                    "x1": 200,
                    "y1": 200,
                    "x2": 400,
                    "y2": 300
                })
                print(f"✅ Result: {result.content[0].text}")
                
                # Wait before adding text
                await asyncio.sleep(2)
                
                # Test 3: Add text inside the rectangle
                print("\n✏️  Test 3: Adding text inside rectangle at (250,240)...")
                result = await session.call_tool("add_text_in_preview", {
                    "text": "Hello Preview!",
                    "x": 250,
                    "y": 240
                })
                print(f"✅ Result: {result.content[0].text}")
                
                # Wait before testing another rectangle
                await asyncio.sleep(2)
                
                # Test 4: Draw another rectangle (smaller, different position)
                print("\n📐 Test 4: Drawing smaller rectangle at (100,100) to (180,150)...")
                result = await session.call_tool("draw_rectangle", {
                    "x1": 100,
                    "y1": 100,
                    "x2": 180,
                    "y2": 150
                })
                print(f"✅ Result: {result.content[0].text}")
                
                # Wait before adding more text
                await asyncio.sleep(2)
                
                # Test 5: Add text in the smaller rectangle
                print("\n✏️  Test 5: Adding text in smaller rectangle at (120,120)...")
                result = await session.call_tool("add_text_in_preview", {
                    "text": "Small Box",
                    "x": 120,
                    "y": 120
                })
                print(f"✅ Result: {result.content[0].text}")
                
                # Wait before saving
                await asyncio.sleep(2)
                
                # Test 6: Save the PDF
                print("\n💾 Test 6: Saving the PDF...")
                result = await session.call_tool("save_pdf")
                print(f"✅ Result: {result.content[0].text}")
                
                print("\n🎉 All tests completed!")
                print("Check the preview_results directory for the saved PDF with:")
                print("  - Large rectangle with 'Hello Preview!' text")
                print("  - Small rectangle with 'Small Box' text")
                
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

async def interactive_drawing_test():
    """Interactive test where user can specify coordinates"""
    print("🎨 Interactive Drawing Test")
    print("="*30)
    
    try:
        server_params = StdioServerParameters(
            command="uv",
            args=["run", "python", "mcp_server_mac.py"]
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # Open Preview
                print("📖 Opening Preview...")
                result = await session.call_tool("open_preview_with_pdf")
                print(f"Result: {result.content[0].text}")
                await asyncio.sleep(3)
                
                while True:
                    print("\n" + "="*40)
                    print("Choose an action:")
                    print("1. Draw rectangle")
                    print("2. Add text")
                    print("3. Save PDF")
                    print("4. Exit")
                    
                    try:
                        choice = input("\nEnter choice (1-4): ").strip()
                        
                        if choice == "1":
                            print("Enter rectangle coordinates:")
                            x1 = int(input("x1 (left): "))
                            y1 = int(input("y1 (top): "))
                            x2 = int(input("x2 (right): "))
                            y2 = int(input("y2 (bottom): "))
                            
                            result = await session.call_tool("draw_rectangle", {
                                "x1": x1, "y1": y1, "x2": x2, "y2": y2
                            })
                            print(f"✅ {result.content[0].text}")
                            
                        elif choice == "2":
                            text = input("Enter text: ")
                            x = int(input("x coordinate: "))
                            y = int(input("y coordinate: "))
                            
                            result = await session.call_tool("add_text_in_preview", {
                                "text": text, "x": x, "y": y
                            })
                            print(f"✅ {result.content[0].text}")
                            
                        elif choice == "3":
                            result = await session.call_tool("save_pdf")
                            print(f"✅ {result.content[0].text}")
                            
                        elif choice == "4":
                            print("👋 Goodbye!")
                            break
                            
                        else:
                            print("Invalid choice!")
                            
                    except ValueError:
                        print("Invalid input! Please enter numbers for coordinates.")
                    except KeyboardInterrupt:
                        print("\n👋 Goodbye!")
                        break
                        
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Main function"""
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        print("Running interactive mode...")
        asyncio.run(interactive_drawing_test())
    else:
        print("Running automated test...")
        asyncio.run(test_preview_capabilities())

if __name__ == "__main__":
    main()
