import os
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
import asyncio
from google import genai
from concurrent.futures import TimeoutError
from functools import partial
from utils import get_tools_description, parse_llm_response
from pydantic import BaseModel

# Load environment variables from .env file
load_dotenv()

# Access your API key and initialize Gemini client correctly
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

max_iterations = 10  # Increased to allow for drawing operations
last_response = None
iteration = 0
response_history = {}

# Pydantic model for response
class Response(BaseModel):
    reasoning: str
    function_name: str
    parameters: dict
    next_steps: str
    workflow_complete: bool
    

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
    global last_response, response_history
    iteration = 0
    response_history = {}




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
                
                tools_description = get_tools_description(tools)
                
                print("Creating system prompt...")
                # import pdb; pdb.set_trace()  # Commented out debug line

                # load system prompt from agent_prompt.yaml
                with open('agent_prompt.yaml', 'r') as file:
                    system_prompt = file.read()
                
                
                system_prompt = system_prompt.format(tools_description=tools_description)
                
                query = """Find the ASCII values of characters in BHARAT and then return sum of exponentials of those values. wherein you draw a rectangle and place the result inside it Mark this as first result in the Rectangle and do the same for another word INDIA and put it in the same rectangle just beneath it, for each result also put the actual word as well as the result inside the rectangle"""
                print("Starting iteration loop...")

                # Use global iteration variables
                global iteration, response_history
                
                while iteration < max_iterations:
                    print(f"\n--- Iteration {iteration + 1} ---")
                    if not response_history:
                        current_query = f"New Task: {query}"

                    else:
                        # create a new query by appending the response history to the query
                        current_query = ""

                        for key, value in response_history.items():
                            current_query = current_query + f"\n\nResponse History {key}: {value}"

                        current_query = current_query + "\n\nWhat should I do next?"


                    # Get model's response with timeout
                    print("Preparing to generate LLM response...")
                    prompt = f"{system_prompt}\n\nQuery: {current_query}"
                    print(prompt)
                    try:
                        response = await generate_with_timeout(client, prompt)

                        response_object = parse_llm_response(response.text)

                        if "plan" in response_object:
                            plan = response_object["plan"]
                            response_history[iteration] = {"plan": plan}
                            iteration += 1
                            continue
                        elif response_object['function_name'] != "none":
                            func_name = response_object['function_name']
                            params = response_object['parameters']
                            result = await session.call_tool(func_name, arguments=params)
                            response_history[iteration] = {"function_name": func_name, "parameters": params, "result": result}
                            iteration += 1
                            continue
                        else:
                            print(f"Response Object: {response_object}")
                            break
                        
                    except Exception as e:
                        print(f"Failed to get LLM response: {e}")
                        break
                    
    except Exception as e:
        print(f"Error in main execution: {e}")
        import traceback
        traceback.print_exc()
    finally:
        reset_state()  # Reset at the end of main

if __name__ == "__main__":
    asyncio.run(main())
    
    
