"""
Prompt utilities for reading and formatting YAML templates.

This module provides functions to:
- Read YAML prompt templates
- Format templates with variable substitution
- Generate final prompts from templates
"""

import yaml
from pathlib import Path
from typing import Dict, Optional
import json


def read_yaml_template(yaml_path: str = "prompts/perception_prompt.yaml") -> Dict[str, str]:
    """
    Read the YAML template file and extract system_prompt and user_prompt.

    Args:
        yaml_path: Path to the YAML template file

    Returns:
        Dictionary with 'system_prompt' and 'user_prompt' keys

    Raises:
        FileNotFoundError: If the YAML file doesn't exist
        yaml.YAMLError: If the YAML file is invalid
    """
    yaml_file = Path(yaml_path)
    if not yaml_file.exists():
        raise FileNotFoundError(f"YAML template not found at {yaml_path}")

    with open(yaml_file, "r", encoding="utf-8") as f:
        template = yaml.safe_load(f)

    if template is None:
        raise ValueError(f"YAML file {yaml_path} is empty or invalid")

    return {
        "system_prompt": template.get("system_prompt", ""),
        "user_prompt": template.get("user_prompt", ""),
    }


def format_template(template: str, context: Dict[str, str]) -> str:
    """
    Format a template string that uses {{variable}} syntax with provided context.

    Args:
        template: Template string with {{variable}} placeholders
        context: Dictionary with variable names as keys and values to substitute

    Returns:
        Formatted string with placeholders replaced

    Example:
        >>> format_template("Hello {{name}}!", {"name": "World"})
        'Hello World!'
    """
    if not template:
        return template

    formatted = template
    for key, value in context.items():
        placeholder = f"{{{{{key}}}}}"
        formatted = formatted.replace(placeholder, str(value))
    return formatted


def get_final_prompt(
    template: Dict[str, str],
    context: Optional[Dict[str, str]] = None,
    verbose: bool = False,
) -> Dict[str, str]:
    """
    Read the YAML template and generate formatted prompts.

    Args:
        yaml_path: Path to the YAML template file
        context: Dictionary with values to substitute into the template.
                 If None, raises ValueError.
        verbose: If True, prints the prompts to stdout. Default: False

    Returns:
        Dictionary with 'system_prompt' and 'formatted_user_prompt' keys

    Raises:
        ValueError: If context is None
        FileNotFoundError: If the YAML file doesn't exist
    """
    if context is None:
        raise ValueError("context parameter is required")

    # Format the user prompt with context
    formatted_user_prompt = format_template(template["user_prompt"], context)

    # Optionally print prompts
    if verbose:
        print("=" * 80)
        print("SYSTEM PROMPT:")
        print("=" * 80)
        print(template["system_prompt"])
        print("\n")
        print("=" * 80)
        print("FORMATTED USER PROMPT:")
        print("=" * 80)
        print(formatted_user_prompt)

    return {
        "system_prompt": template["system_prompt"],
        "formatted_user_prompt": formatted_user_prompt,
    }

def parse_response(response: str) -> dict:
    """
    Parse the response from the LLM into a dictionary.
    
    Args:
        response: LLM response string that may contain JSON in a code block
        
    Returns:
        Dictionary parsed from the JSON block
        
    Raises:
        ValueError: If the response doesn't contain a valid JSON code block
        json.JSONDecodeError: If the JSON block is invalid JSON
    """
    try:
        # Extract JSON block from markdown code block
        if "```json" not in response:
            raise ValueError("Response does not contain a ```json code block")
        
        parts = response.split("```json")
        if len(parts) < 2:
            raise ValueError("Could not find JSON code block start marker")
        
        json_part = parts[1]
        if "```" not in json_part:
            raise ValueError("Could not find JSON code block end marker")
        
        json_block = json_part.split("```")[0].strip()
        
        if not json_block:
            raise ValueError("JSON code block is empty")
        
        output = json.loads(json_block)
        return output
        
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"Failed to parse JSON from response: {str(e)}",
            e.doc,
            e.pos
        ) from e
    except (IndexError, ValueError) as e:
        raise ValueError(f"Error parsing response: {str(e)}") from e
