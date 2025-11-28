"""
LLM utilities for generating responses using Google Gemini API.

This module provides functions to:
- Generate LLM responses using system and user prompts
- Handle API key management
- Configure model selection
"""

import os
from typing import Optional
from dotenv import load_dotenv
from google import genai

# Load environment variables
load_dotenv()


def generate_llm_response(
    system_prompt: str,
    formatted_user_prompt: str,
    api_key: Optional[str] = None,
    model: str = "gemini-2.0-flash",
) -> str:
    """
    Generate a response from the LLM using the system prompt and formatted user prompt.

    Uses Google Gemini API with structured role-based messages for proper separation
    of system and user content.

    Args:
        system_prompt: System prompt string (instructions for the model)
        formatted_user_prompt: Formatted user prompt string (actual query/input)
        api_key: Gemini API key. If None, uses GEMINI_API_KEY environment variable
        model: Model name to use (default: gemini-2.0-flash)

    Returns:
        Response text from the LLM (stripped of leading/trailing whitespace)

    Raises:
        ValueError: If API key is not provided and not found in environment
        Exception: If API call fails (network error, API error, etc.)

    Example:
        >>> response = generate_llm_response(
        ...     system_prompt="You are a helpful assistant.",
        ...     formatted_user_prompt="What is 2+2?"
        ... )
        >>> print(response)
    """
    # Get API key from parameter or environment
    if api_key is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY not found in environment or explicitly provided."
            )

    # Initialize Gemini client
    client = genai.Client(api_key=api_key)

    # Combine system and user prompts
    contents = f"{system_prompt}\n\n{formatted_user_prompt}"

    # Generate response
    response = client.models.generate_content(model=model, contents=contents)

    return response.text.strip()
