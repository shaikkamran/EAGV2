import os
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
import asyncio
from google import genai
from concurrent.futures import TimeoutError
from functools import partial

# Load environment variables from .env file
load_dotenv()

# Access your API key and initialize Gemini client correctly
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

max_iterations = 10  # Increased to allow for drawing operations
last_response = None
iteration = 0
iteration_response = []
final_answer_given = False  # Track if we've reached the mathematical solution

async def generate_with_timeout(client, prompt, timeout=10):
    """Generate content with a timeout"""
    print("Starting LLM generation...")
    try:
        # Convert the synchronous generate_content call to run in a thread
        loop = asyncio.get_event_loop()
        response = await asyncio.wait_for(
            loop.run_in_executor(
                None, 
                lambda: client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt
                )
            ),
            timeout=timeout
        )
        print("LLM generation completed")
        return response
    except TimeoutError:
        print("LLM generation timed out!")
        raise
    except Exception as e:
        print(f"Error in LLM generation: {e}")
        raise

def reset_state():
    """Reset all global variables to their initial state"""
    global last_response, iteration, iteration_response, final_answer_given
    last_response = None
    iteration = 0
    iteration_response = []
    final_answer_given = False

async def main():
    reset_state()  # Reset at the start of main
    print("Starting main execution...")
    try:
        # Create a single MCP server connection
        print("Establishing connection to MCP server...")
        server_params = StdioServerParameters(
            command="uv",
            args=["run", "python", "mcp_server_mac.py"]
        )

        async with stdio_client(server_params) as (read, write):
            print("Connection established, creating session...")
            async with ClientSession(read, write) as session:
                print("Session created, initializing...")
                await session.initialize()
                
                # Get available tools
                print("Requesting tool list...")
                tools_result = await session.list_tools()
                tools = tools_result.tools
                print(f"Successfully retrieved {len(tools)} tools")
                

                # Create system prompt with available tools
                print("Creating system prompt...")
                print(f"Number of tools: {len(tools)}")
                
                try:
                    # First, let's inspect what a tool object looks like
                    # if tools:
                    #     print(f"First tool properties: {dir(tools[0])}")
                    #     print(f"First tool example: {tools[0]}")
                    
                    tools_description = []
                    for i, tool in enumerate(tools):
                        try:
                            # Get tool properties
                            params = tool.inputSchema
                            desc = getattr(tool, 'description', 'No description available')
                            name = getattr(tool, 'name', f'tool_{i}')
                            
                            # Format the input schema in a more readable way
                            if 'properties' in params:
                                param_details = []
                                for param_name, param_info in params['properties'].items():
                                    param_type = param_info.get('type', 'unknown')
                                    param_details.append(f"{param_name}: {param_type}")
                                params_str = ', '.join(param_details)
                            else:
                                params_str = 'no parameters'

                            tool_desc = f"{i+1}. {name}({params_str}) - {desc}"
                            tools_description.append(tool_desc)
                            print(f"Added description for tool: {tool_desc}")
                        except Exception as e:
                            print(f"Error processing tool {i}: {e}")
                            tools_description.append(f"{i+1}. Error processing tool")
                    
                    tools_description = "\n".join(tools_description)
                    print("Successfully created tools description")
                except Exception as e:
                    print(f"Error creating tools description: {e}")
                    tools_description = "Error loading tools"
                
                print("Created system prompt...")
                # import pdb; pdb.set_trace()  # Commented out debug line
                
                system_prompt = f"""You are an intelligent autonomous agent specialized in solving mathematical problems and creating visual representations. You have access to various mathematical tools and PDF drawing capabilities.

Available tools:
{tools_description}

WORKFLOW:
1. MATHEMATICAL PHASE: Solve the given problem using available mathematical tools
2. VISUALIZATION PHASE: Once you have the final answer, create a visual representation

RESPONSE FORMATS:
- For mathematical calculations: FUNCTION_CALL: function_name|param1|param2|...
- For final mathematical result: FINAL_ANSWER: [result]
- For drawing operations: FUNCTION_CALL: function_name|param1|param2|...

AUTONOMOUS DRAWING INSTRUCTIONS:
After providing FINAL_ANSWER, you MUST autonomously proceed to:

1. OPEN PDF CANVAS: Call open_preview_with_pdf to create a drawing canvas

2. DRAW RECTANGLE: Call draw_rectangle with intelligent coordinates:
   - Use reasonable margins (at least 30 pixels from edges)
   - Make rectangle large enough for text (typical: x1=50, y1=120, x2=400, y2=200)
   - Adjust size based on answer length:
     * Short answers (<20 chars): x1=80, y1=150, x2=350, y2=220
     * Medium answers (20-50 chars): x1=50, y1=120, x2=400, y2=200  
     * Long answers (>50 chars): x1=30, y1=100, x2=450, y2=180

3. ADD TEXT: Call add_text_in_preview with your final answer:
   - Position text centrally within the rectangle
   - Text X = rectangle x1 + 20-30 pixels for left padding
   - Text Y = rectangle y1 + 40-50 pixels for vertical centering

4. SAVE RESULT: Call save_pdf to finalize the document

5. Once the Saving is complete, you must respond in a different format which will indicate the Agent to complete the Session and break out of the loop

COORDINATE SYSTEM:
- PDF canvas: 612x792 pixels (letter size)
- Rectangle: (x1,y1) = top-left, (x2,y2) = bottom-right  
- Text: (x,y) where y is measured from top
- Keep all coordinates within bounds: x < 550, y < 750

IMPORTANT RULES:
- Complete ALL mathematical calculations before starting visualization
- Do not repeat function calls with identical parameters
- Each response should be exactly ONE line with the specified format
- Continue making function calls until the complete visualization is done

Examples:
- FUNCTION_CALL: strings_to_chars_to_int|INDIA
- FINAL_ANSWER: [1.23e+195]
- FUNCTION_CALL: open_preview_with_pdf
- FUNCTION_CALL: draw_rectangle|50|120|400|200
- FUNCTION_CALL: add_text_in_preview|FINAL_ANSWER: [1.23e+195]|70|160
- FUNCTION_CALL: save_pdf

DO NOT include explanations. Respond with exactly one line using the specified formats."""

                query = """Find the ASCII values of characters in BHARAT and then return sum of exponentials of those values. """
                print("Starting iteration loop...")
                
                # Use global iteration variables
                global iteration, last_response, final_answer_given
                
                while iteration < max_iterations:
                    print(f"\n--- Iteration {iteration + 1} ---")
                    if last_response is None:
                        current_query = query
                    else:
                        current_query = current_query + "\n\n" + " ".join(iteration_response)
                        current_query = current_query + "  What should I do next?"

                    # Get model's response with timeout
                    print("Preparing to generate LLM response...")
                    prompt = f"{system_prompt}\n\nQuery: {current_query}"
                    try:
                        response = await generate_with_timeout(client, prompt)
                        response_text = response.text.strip()
                        print(f"LLM Response: {response_text}")
                        
                        # Find the FUNCTION_CALL line in the response
                        for line in response_text.split('\n'):
                            line = line.strip()
                            if line.startswith("FUNCTION_CALL:"):
                                response_text = line
                                break
                        
                    except Exception as e:
                        print(f"Failed to get LLM response: {e}")
                        break


                    if response_text.startswith("FUNCTION_CALL:"):
                        _, function_info = response_text.split(":", 1)
                        parts = [p.strip() for p in function_info.split("|")]
                        func_name, params = parts[0], parts[1:]
                        
                        print(f"\nDEBUG: Raw function info: {function_info}")
                        print(f"DEBUG: Split parts: {parts}")
                        print(f"DEBUG: Function name: {func_name}")
                        print(f"DEBUG: Raw parameters: {params}")
                        
                        try:
                            # Find the matching tool to get its input schema
                            tool = next((t for t in tools if t.name == func_name), None)
                            if not tool:
                                print(f"DEBUG: Available tools: {[t.name for t in tools]}")
                                raise ValueError(f"Unknown tool: {func_name}")

                            print(f"DEBUG: Found tool: {tool.name}")
                            print(f"DEBUG: Tool schema: {tool.inputSchema}")

                            # Prepare arguments according to the tool's input schema
                            arguments = {}
                            schema_properties = tool.inputSchema.get('properties', {})
                            print(f"DEBUG: Schema properties: {schema_properties}")

                            for param_name, param_info in schema_properties.items():
                                if not params:  # Check if we have enough parameters
                                    raise ValueError(f"Not enough parameters provided for {func_name}")
                                    
                                value = params.pop(0)  # Get and remove the first parameter
                                param_type = param_info.get('type', 'string')
                                
                                print(f"DEBUG: Converting parameter {param_name} with value {value} to type {param_type}")
                                
                                # Convert the value to the correct type based on the schema
                                if param_type == 'integer':
                                    arguments[param_name] = int(value)
                                elif param_type == 'number':
                                    arguments[param_name] = float(value)
                                elif param_type == 'array':
                                    # Handle array input
                                    if isinstance(value, str):
                                        value = value.strip('[]').split(',')
                                    arguments[param_name] = [int(x.strip()) for x in value]
                                else:
                                    arguments[param_name] = str(value)

                            print(f"DEBUG: Final arguments: {arguments}")
                            print(f"DEBUG: Calling tool {func_name}")
                            
                            result = await session.call_tool(func_name, arguments=arguments)
                            print(f"DEBUG: Raw result: {result}")
                            
                            # Get the full result content
                            if hasattr(result, 'content'):
                                print(f"DEBUG: Result has content attribute")
                                # Handle multiple content items
                                if isinstance(result.content, list):
                                    iteration_result = [
                                        item.text if hasattr(item, 'text') else str(item)
                                        for item in result.content
                                    ]
                                else:
                                    iteration_result = str(result.content)
                            else:
                                print(f"DEBUG: Result has no content attribute")
                                iteration_result = str(result)
                                
                            print(f"DEBUG: Final iteration result: {iteration_result}")
                            
                            # Format the response based on result type
                            if isinstance(iteration_result, list):
                                result_str = f"[{', '.join(iteration_result)}]"
                            else:
                                result_str = str(iteration_result)
                            
                            iteration_response.append(
                                f"In the {iteration + 1} iteration you called {func_name} with {arguments} parameters, "
                                f"and the function returned {result_str}."
                            )
                            last_response = iteration_result
                            
                            # Check if visualization is complete (save_pdf was called)
                            if func_name == "save_pdf" and final_answer_given:
                                print("\n=== Autonomous Agent Complete - Visualization Finished ===")
                                break

                        except Exception as e:
                            print(f"DEBUG: Error details: {str(e)}")
                            print(f"DEBUG: Error type: {type(e)}")
                            import traceback
                            traceback.print_exc()
                            iteration_response.append(f"Error in iteration {iteration + 1}: {str(e)}")
                            break

                    elif response_text.startswith("FINAL_ANSWER:"):
                        print("\n=== Mathematical Phase Complete - Agent will now proceed to visualization ===")
                        # Store the final answer and continue the loop for visualization
                        iteration_response.append(f"Mathematical solution complete: {response_text}")
                        final_answer_given = True
                        # Don't break - let the agent continue to make drawing function calls
                    
                    else:
                        print(f"Unexpected response format: {response_text}")
                        break

                    iteration += 1

    except Exception as e:
        print(f"Error in main execution: {e}")
        import traceback
        traceback.print_exc()
    finally:
        reset_state()  # Reset at the end of main

if __name__ == "__main__":
    asyncio.run(main())
    
    
