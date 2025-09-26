"""
AI-Powered Email Orchestration System

This module provides the main orchestration logic for multi-step email operations
using Google's Gemini AI. It handles workflow management, prompt generation,
and task execution coordination.

Author: AI Assistant
Date: September 2025
"""

import os
import re
import json
import gc
import atexit
from typing import List, Dict, Optional
from datetime import datetime

from google import genai
from dotenv import load_dotenv
from main import create_gmail_client
from email_analyzer import analyze_emails_for_intent

load_dotenv()


# ==================== GLOBAL CONFIGURATION ====================

# Load API key and initialize clients
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY environment variable is required")

client = genai.Client(api_key=api_key)
gmail_client = create_gmail_client()


# ==================== UTILITY FUNCTIONS ====================

def get_current_date_and_time():
    """Get current date and time as formatted string."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def convert_given_time_into_days_ago(given_time):
    """Convert given time to days ago from now."""
    return (datetime.now() - given_time).days


def parse_llm_response(response):
    """Parse LLM response to extract JSON object with robust error handling."""
    try:
        # Try to extract JSON from markdown code block
        json_object = re.search(r"```json\n(.*?)\n```", response, re.DOTALL)
        if json_object:
            json_str = json_object.group(1)
            parsed_response = json.loads(json_str)
            return parsed_response
            
        # Fallback: Try to find JSON object directly
        json_match = re.search(r'\{.*?\}', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            parsed_response = json.loads(json_str)
            return parsed_response
            
        print("❌ No valid JSON found in response")
        return None
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error: {e}")
        print(f"🔍 Problematic response snippet: {response[:200]}...")
        
        # Try to fix common JSON issues
        try:
            if json_object:
                json_str = json_object.group(1)
                # Fix common escape issues
                json_str = json_str.replace('\\', '\\\\')  # Escape backslashes
                json_str = json_str.replace('\n', '\\n')   # Escape newlines
                json_str = json_str.replace('\t', '\\t')   # Escape tabs
                parsed_response = json.loads(json_str)
                print("✅ Fixed JSON parsing with escape handling")
                return parsed_response
        except:
            pass
            
        return None
    except Exception as e:
        print(f"❌ Unexpected parsing error: {e}")
        return None


# ==================== ORCHESTRATION PROMPT SYSTEM ====================

def create_prompt(previous_results=None, next_steps=None):
    """
    Create the main orchestration prompt for multi-step email workflows.
    
    Args:
        previous_results: Results from previous step execution
        next_steps: Next steps to be executed
        
    Returns:
        Formatted prompt string for Gemini AI
    """
    base_prompt = """
You are an AI assistant that can solve tasks by calling specific tools in a multi-step workflow.
You must ONLY respond with a single JSON object in the format:

```json
{"function_name": "<tool_name>", "parameters": {<arguments>}, "next_steps": "", "workflow_complete": false}
```

CRITICAL JSON FORMATTING RULES:
- Use double quotes for all strings
- Do NOT include any backslashes, newlines, or special characters in JSON values
- Keep parameter values simple and clean (strings, numbers, booleans only)
- Do NOT include any text outside the JSON object
- Do NOT pass complex objects like email lists as parameters - they are handled automatically
- Only pass simple string/number parameters as documented

---

### Available Tools

1. **Read Emails by Time Period**
   - **Name:** read_emails_by_time_period
   - **Description:** Fetch email threads from a specific time window. Can read emails from recent days/hours or specific months.
   - **Parameters:**
       - days_ago (int, optional): Number of days ago to start searching. For specific months, calculate from current date.
       - hours_ago (int, optional): Number of hours ago to start searching (overrides days_ago).
       - count (int, optional): Maximum number of threads to return (default: 50).
   - **Returns:** List of EmailSummary objects.
   - **Examples:**
     - Recent emails: {"function_name": "read_emails_by_time_period", "parameters": {"days_ago": 7}}
     - Specific month: {"function_name": "read_emails_by_time_period", "parameters": {"days_ago": 30, "count": 100}}

2. **Apply Label to Emails**
   - **Name:** apply_label_to_emails
   - **Description:** Apply a label to one or more email threads.
   - **Parameters:**
       - label_name (str): The name of the label to apply.
       - email_ids (list[str], optional): List of individual email IDs.
       - thread_ids (list[str], optional): List of thread IDs (applies to all emails in the thread).
   - **Returns:** OperationResult object with details.

3. **Universal AI-Powered Intent Analysis**
   - **Name:** analyze_emails_for_intent
   - **Description:** Use advanced AI reasoning to analyze email content for ANY specified intent without restrictions. The AI dynamically understands and classifies emails based on your intent description. Examples: "SPAM", "URGENT", "AMAZON ORDERS", "CUSTOMER COMPLAINTS", "WORK MEETINGS", "BIRTHDAY INVITATIONS", etc. This function automatically uses emails from previous steps - DO NOT pass emails as parameters.
   - **Parameters:**
       -emails (list[EmailSummary]): List of EmailSummary strings to analyze.
       - intent (str): ANY intent description you want to analyze for - completely flexible and unrestricted.
   - **Returns:** List of thread_ids that match the specified intent, with automatic labeling applied.

---

### Workflow Rules
- You are working on a multi-step task. Execute one step at a time.
- If previous_results are provided, use them to determine the next action.
- Set "workflow_complete": true when the user's original request is fully satisfied.
- Set "workflow_complete": false when more steps are needed.
- For time-based requests like "emails from February 2025", use read_emails_by_time_period with appropriate days_ago calculation.
- Do NOT explain your reasoning or output natural language.  
- Do NOT invent tool names or parameters outside the defined set.
- If the user asks something unrelated to these tools, return:  
{"function_name": "none", "parameters": {}, "next_steps": "", "workflow_complete": true}

### Important Notes:
- For "month of Feb 2025" requests, this is a future date, so use a reasonable days_ago value like 30-60 days to capture a month's worth of emails
- Always include a reasonable count parameter for email reading (suggest 50-100 for monthly requests)  
- The intent analysis system is COMPLETELY UNIVERSAL - it can understand and analyze for ANY intent the user specifies
- Examples of intents: "SPAM", "URGENT", "AMAZON ORDERS", "CUSTOMER COMPLAINTS", "WORK MEETINGS", "BIRTHDAY INVITATIONS", "CRYPTOCURRENCY NEWS", etc.
- The AI uses sophisticated semantic understanding, contextual analysis, and pattern recognition for ANY intent
- Labels are automatically created and applied based on the intent name (spaces become underscores)
- The system dynamically adapts to new intents without requiring predefined configurations
"""
    
    if previous_results is not None:
        context = f"""

### Previous Step Results:
{str(previous_results)}...

### Next Steps to Execute:
{next_steps}

Based on the previous results and next steps, determine what action to take next to complete the user's request.
"""
        base_prompt += context
    
    return base_prompt


# ==================== WORKFLOW EXECUTION ENGINE ====================

def execute_llm_response(parsed_response, email_data_store):
    """
    Execute the function specified in the LLM response.
    
    Args:
        parsed_response: Parsed JSON response from LLM
        email_data_store: Dictionary to store data between workflow steps
        
    Returns:
        Result of the executed function
    """
    function_name = parsed_response.get("function_name")
    parameters = parsed_response.get("parameters", {})
    
    if function_name == "read_emails_by_time_period":
        result = gmail_client.read_emails_by_time_period(**parameters)
        # Store emails in data store for later use
        email_data_store['emails'] = result
        
        # Debug: Confirm storage
        print(f"🔍 Email Storage Debug:")
        print(f"  - Storing {len(result) if result else 0} emails in data store")
        if result:
            print(f"  - Sample stored email subjects: {[e.subject[:50] for e in result[:3]]}")
        print()
        
        return result
    
    elif function_name == "apply_label_to_emails":
        return gmail_client.apply_label_to_emails(**parameters)
    
    elif function_name == "analyze_emails_for_intent":
        # Use the stored emails for intent analysis
        emails = email_data_store.get('emails', [])
        intent = parameters.get("intent", "SPAM")
        
        # Debug: Check what emails we have
        print(f"🔍 Email Data Store Debug:")
        print(f"  - Data store keys: {list(email_data_store.keys())}")
        print(f"  - Number of emails retrieved: {len(emails)}")
        if emails:
            print(f"  - Sample email subjects: {[e.subject[:50] for e in emails[:3]]}")
        else:
            print(f"  - ❌ No emails found in data store!")
        print()
        
        result = analyze_emails_for_intent(emails, intent, gmail_client, api_key)
        # Store classified thread IDs for later use
        email_data_store[f'{intent.lower()}_thread_ids'] = result
        return result
    
    elif function_name == "none":
        return None
    
    else:
        print(f"❌ Unknown function: {function_name}")
        return None


# ==================== MAIN ORCHESTRATION WORKFLOW ====================

def run_email_workflow(user_message: str, max_attempts: int = 5):
    """
    Run the main email orchestration workflow.
    
    Args:
        user_message: User's request to process
        max_attempts: Maximum number of workflow steps to attempt
        
    Returns:
        Dictionary with workflow results and status
    """
    print(f"🚀 Starting email workflow for: {user_message}")
    print("=" * 80)
    
    workflow_complete = False
    previous_results = None
    next_steps = None
    step_number = 1
    email_data_store = {}  # Store email data between steps
    workflow_results = []
    
    try:
        for attempt in range(max_attempts):
            if workflow_complete:
                print("✅ Workflow completed successfully!")
                break
                
            print(f"\n📋 STEP {step_number}: Planning next action...")
            
            # Create dynamic prompt based on current state
            current_prompt = create_prompt(previous_results, next_steps)
            current_prompt = f"You took the current date and time as {get_current_date_and_time()}\n" + current_prompt
            
            # Format according to Gemini API structure
            if step_number == 1:
                prompt_text = f"{current_prompt}\n\nUser request: {user_message}"
            else:
                prompt_text = f"{current_prompt}\n\nOriginal user request: {user_message}\nContinue with the next step to complete this request."
            
            contents = [{"parts": [{"text": prompt_text}]}]
            
            print(f"🤖 Sending request to Gemini AI...")
            
            # Call Gemini API
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=contents,
            )
            
            # Parse LLM response
            parsed_response = parse_llm_response(response.text)
            print(f"📥 Parsed Response: {parsed_response}")
            
            if not parsed_response:
                print("❌ Failed to parse LLM response")
                break
            
            # Execute the function
            function_name = parsed_response.get('function_name', 'unknown')
            print(f"⚡ Executing: {function_name}")
            execution_result = execute_llm_response(parsed_response, email_data_store)
            
            # Store step results
            step_result = {
                "step": step_number,
                "function": function_name,
                "parameters": parsed_response.get("parameters", {}),
                "result": execution_result,
                "success": execution_result is not None
            }
            workflow_results.append(step_result)
            
            # Update state for next iteration
            previous_results = execution_result
            next_steps = parsed_response.get("next_steps", "")
            workflow_complete = parsed_response.get("workflow_complete", False)
            step_number += 1
            
            print(f"📊 Step {step_number-1} Results: {type(execution_result)} with {len(execution_result) if hasattr(execution_result, '__len__') else 'N/A'} items")
            
            if workflow_complete:
                print("✅ Workflow marked as complete by LLM")
                break
                
            print(f"➡️ Next steps: {next_steps}")
            print("-" * 60)
        
        return {
            "success": workflow_complete,
            "steps_executed": len(workflow_results),
            "results": workflow_results,
            "email_data": email_data_store,
            "message": "Workflow completed successfully" if workflow_complete else "Workflow incomplete"
        }
        
    except Exception as e:
        print(f"❌ Workflow failed: {e}")
        return {
            "success": False,
            "steps_executed": len(workflow_results),
            "results": workflow_results,
            "email_data": email_data_store,
            "error": str(e),
            "message": f"Workflow failed: {e}"
        }


# ==================== RESOURCE CLEANUP ====================

def cleanup_resources():
    """Clean up resources properly."""
    global client, gmail_client
    try:
        client = None
        gmail_client = None
        gc.collect()
    except:
        pass

# Register cleanup function
atexit.register(cleanup_resources)


# ==================== MAIN EXECUTION ====================

if __name__ == "__main__":
    # Example workflow execution
    user_message = "Read the top 10 emails from 3 days and analyze them for ECOMMERCE AMAZON intent, then automatically label them"
    
    try:
        result = run_email_workflow(user_message)
        
        print("\n" + "=" * 80)
        print("📊 WORKFLOW SUMMARY")
        print("=" * 80)
        print(f"✅ Success: {result['success']}")
        print(f"📋 Steps Executed: {result['steps_executed']}")
        print(f"💬 Message: {result['message']}")
        
        if result.get('email_data'):
            print(f"📧 Email Data Available: {list(result['email_data'].keys())}")
        
    finally:
        # Clean up resources
        cleanup_resources()