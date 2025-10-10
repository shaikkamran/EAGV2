import re
import json
import asyncio
from concurrent.futures import TimeoutError

def parse_llm_response(response):
    try:
        # Try to extract JSON from markdown code block
        json_object = re.search(r"```json\n(.*?)\n```", response, re.DOTALL)
        if json_object:
            json_str = json_object.group(1)
            parsed_response = json.loads(json_str)
            return parsed_response
    except Exception as e:
        print(f"Error parsing LLM response: {e}")
        return None

def get_tools_description(tools):
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
        return tools_description
    except Exception as e:
        print(f"Error creating tools description: {e}")
        tools_description = "Error loading tools"
        return tools_description


async def generate_with_timeout(client, prompt, timeout=20):
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