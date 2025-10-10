import os
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
import asyncio
from google import genai
from concurrent.futures import TimeoutError
from functools import partial
from utils import get_tools_description, parse_llm_response, generate_with_timeout
from pydantic import BaseModel

# Load environment variables from .env file
load_dotenv()

# Access your API key and initialize Gemini client correctly
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

max_iterations = 20  # Increased to allow for drawing operations
iteration = 0
response_history = {}

# Pydantic model for response
class Response(BaseModel):
    reasoning: str
    function_name: str
    parameters: dict
    next_steps: str
    workflow_complete: bool
    


def reset_state():
    """Reset all global variables to their initial state"""
    global iteration,response_history
    iteration = 0
    response_history = {}


async def main():
    reset_state()  # Reset at the start of main
    print("\033[92m🚀 Starting main execution...\033[0m")
    try:
        # Create a single MCP server connection
        print("\033[94m🔗 Establishing connection to MCP server...\033[0m")
        server_params = StdioServerParameters(
            command="uv",
            args=["run", "python", "mcp_server_mac.py"]
        )

        async with stdio_client(server_params) as (read, write):
            print("\033[92m✅ Connection established, creating session...\033[0m")
            async with ClientSession(read, write) as session:
                print("\033[96m🔧 Session created, initializing...\033[0m")
                await session.initialize()
                
                # Get available tools
                print("\033[93m🛠️  Requesting tool list...\033[0m")
                tools_result = await session.list_tools()
                tools = tools_result.tools
                print(f"\033[92m✅ Successfully retrieved \033[1m{len(tools)}\033[0m\033[92m tools\033[0m")
                

                # Create system prompt with available tools
                print("\033[94m📝 Creating system prompt...\033[0m")
                print(f"\033[96m📊 Number of tools: \033[1m{len(tools)}\033[0m")
                
                tools_description = get_tools_description(tools)
                
                print("\033[94m📋 System prompt created successfully\033[0m")
                # import pdb; pdb.set_trace()  # Commented out debug line

                # load system prompt from agent_prompt.yaml
                with open('agent_prompt.yaml', 'r') as file:
                    system_prompt = file.read()
                
                
                system_prompt = system_prompt.format(tools_description=tools_description)
                
                query = """Find the ASCII values of characters in BHARAT and then return sum of exponentials of those values. wherein you draw a rectangle and place the result inside it Mark this as first result in the Rectangle and do the same for another word INDIA and put it in the same rectangle just beneath it, for each result also put the actual word as well as the result inside the rectangle"""
                print("\033[95m🔄 Starting iteration loop...\033[0m")

                # Use global iteration variables
                global iteration, response_history
                
                while iteration < max_iterations:
                    print(f"\n\033[1m\033[36m{'='*50}\033[0m")
                    print(f"\033[1m\033[35m🔄 Iteration {iteration + 1}/{max_iterations}\033[0m")
                    print(f"\033[1m\033[36m{'='*50}\033[0m")
                    if not response_history:
                        current_query = f"New Task: {query}"

                    else:
                        # create a new query by appending the response history to the query
                        current_query = ""

                        for key, value in response_history.items():
                            current_query = current_query + f"\n\nResponse History {key}: {value}"

                        current_query = current_query + "\n\nWhat should I do next?"


                    # Get model's response with timeout
                    print("\033[93m🤖 Preparing to generate LLM response...\033[0m")
                    prompt = f"{system_prompt}\n\nQuery: {current_query}"
                    
                    # Print the prompt only for the first iteration
                    if iteration == 0:
                        print("\033[94m📄 Full prompt:\033[0m")
                        print(prompt)
                    else:
                        print("\033[96m📚 Response History:\033[0m", current_query)
                    try:
                        response = await generate_with_timeout(client, prompt)

                        response_object = parse_llm_response(response.text)
                        print(f"\033[92m📦 Response Object: \033[1m{response_object}\033[0m")

                        if "plan" in response_object:
                            plan = response_object["plan"]
                            response_history[iteration] = {"plan": plan}
                            print(f"\033[94m📋 Plan received: \033[1m{plan}\033[0m")
                            iteration += 1
                            continue
                        elif response_object['function_name'] != "none":
                            func_name = response_object['function_name']
                            params = response_object['parameters']
                            print(f"\033[93m🔧 Calling function: \033[1m{func_name}\033[0m with params: \033[1m{params}\033[0m")
                            result = await session.call_tool(func_name, arguments=params)
                            response_history[iteration] = {"function_name": func_name, "parameters": params, "result": result}
                            print(f"\033[92m✅ Function result: \033[1m{result}\033[0m")
                            iteration += 1
                            continue
                        else:
                            # print(f"Response Object: {response_object}")
                            print("\033[95m🏁 Workflow completed!\033[0m")
                            break
                        
                    except Exception as e:
                        print(f"\033[91m❌ Failed to get LLM response: \033[1m{e}\033[0m")
                        break
                    
    except Exception as e:
        print(f"\033[91m💥 Error in main execution: \033[1m{e}\033[0m")
        import traceback
        traceback.print_exc()
    finally:
        print("\033[96m🧹 Cleaning up and resetting state...\033[0m")
        reset_state()  # Reset at the end of main

if __name__ == "__main__":
    asyncio.run(main())
    
    
