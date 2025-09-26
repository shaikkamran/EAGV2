
from email import message
from google import genai
import os
from dotenv import load_dotenv
from datetime import datetime
from main import create_gmail_client
import re,json
import gc
import atexit

load_dotenv()
# read the api key from the environment variable
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)
gmail_client = create_gmail_client()

# Function to clean up resources properly
def cleanup_resources():
    global client, gmail_client
    try:
        client = None
        gmail_client = None
        gc.collect()  # Force garbage collection
    except:
        pass

# Register cleanup function to run on exit
atexit.register(cleanup_resources)


# write a function to get the current date and time
def get_current_date_and_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def convert_given_time_into_days_ago(given_time):
    return (datetime.now() - given_time).days

# Help me Write a prompt that reads emails given time period by user by using the functionality from the main.py file that is the Gmail Client

def create_prompt(previous_results=None, next_steps=None):
    base_prompt = """
You are an AI assistant that can solve tasks by calling specific tools in a multi-step workflow.
You must ONLY respond with a single JSON object in the format:

```json
{"function_name": "<tool_name>", "parameters": {<arguments>}, "next_steps": "", "workflow_complete": false}
```

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

3. **Analyze Email Content for SPAM**
   - **Name:** analyze_emails_for_spam
   - **Description:** Analyze email content to determine if emails should be labeled as SPAM. Uses previously retrieved emails automatically.
   - **Parameters:**
       - spam_keywords (list, optional): List of keywords that indicate SPAM.
   - **Returns:** List of thread_ids that should be labeled as SPAM.

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
- When analyzing for SPAM, look for suspicious patterns, promotional content, unknown senders, etc.
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


# Create properly formatted contents for Gemini API
user_message = "Read the top 10 emails from the month of Feb 2025 and label them as SPAM if the content of the email is related to the topic of SPAM"

max_attempts = 5
workflow_complete = False
previous_results = None
next_steps = None
step_number = 1
email_data_store = {}  # Store email data between steps

def parse_llm_response(response):

    # Get the json object that is present within the ```json``` blocks
    json_object = re.search(r"```json\n(.*?)\n```", response, re.DOTALL)
    if json_object:
        parsed_response = json.loads(json_object.group(1))
    else:
        parsed_response = None

    return parsed_response

# SPAM analysis function
def analyze_emails_for_spam(emails, spam_keywords=None):
    """Analyze emails for SPAM content and return thread_ids that should be labeled as SPAM."""
    if spam_keywords is None:
        spam_keywords = [
            'win', 'winner', 'prize', 'congratulations', 'free', 'click here', 
            'urgent', 'limited time', 'act now', 'offer', 'deal', 'discount',
            'lottery', 'million', 'inheritance', 'prince', 'nigeria',
            'viagra', 'casino', 'poker', 'loan', 'credit', 'debt',
            'weight loss', 'diet pill', 'supplements', 'enhancement'
        ]
    
    spam_thread_ids = []
    
    for email in emails:
        content_to_check = (email.subject + " " + email.sender + " " + email.content_preview).lower()
        
        # Check for SPAM indicators
        spam_score = 0
        
        # Check for SPAM keywords
        for keyword in spam_keywords:
            if keyword.lower() in content_to_check:
                spam_score += 1
        
        # Check for suspicious patterns
        if 'urgent' in content_to_check or 'act now' in content_to_check:
            spam_score += 2
        
        if any(char in email.sender for char in ['noreply', 'no-reply']):
            spam_score += 1
            
        # Check for promotional content patterns
        if 'deal' in content_to_check and ('save' in content_to_check or '%' in content_to_check):
            spam_score += 2
            
        # Suspicious subject patterns
        if any(word in email.subject.lower() for word in ['re:', 'fwd:', 'urgent', 'important']):
            if not any(word in email.subject.lower() for word in ['payment', 'account', 'security']):
                spam_score += 1
        
        # If spam score is high enough, mark as SPAM
        if spam_score >= 2:
            spam_thread_ids.append(email.thread_id)
            print(f"🚨 SPAM detected: {email.subject} (Score: {spam_score})")
    
    print(f"📊 Analyzed {len(emails)} emails, found {len(spam_thread_ids)} potential SPAM emails")
    return spam_thread_ids

# Now write code which is given in the parsed response using the gmail_client
def execute_llm_response(parsed_response, email_data_store):
    if parsed_response["function_name"] == "read_emails_by_time_period":
        result = gmail_client.read_emails_by_time_period(**parsed_response["parameters"])
        # Store emails in data store for later use
        email_data_store['emails'] = result
        return result
    
    elif parsed_response["function_name"] == "apply_label_to_emails":
        return gmail_client.apply_label_to_emails(**parsed_response["parameters"])
    
    elif parsed_response["function_name"] == "analyze_emails_for_spam":
        # Use the stored emails instead of trying to parse from string
        emails = email_data_store.get('emails', [])
        spam_keywords = parsed_response["parameters"].get("spam_keywords", None)
        result = analyze_emails_for_spam(emails, spam_keywords)
        # Store spam thread IDs for later labeling
        email_data_store['spam_thread_ids'] = result
        return result
    
    elif parsed_response["function_name"] == "none":
        return None
    
    else:
        return None


try:
    print(f"🚀 Starting multi-step workflow for: {user_message}")
    print("="*80)
    
    for attempt in range(max_attempts):
        if workflow_complete:
            print("✅ Workflow completed successfully!")
            break
            
        print(f"\n📋 STEP {step_number}: Planning next action...")
        
        # Create dynamic prompt based on current state
        current_prompt = create_prompt(previous_results, next_steps)
        current_prompt = f"You took the current date and time as {get_current_date_and_time()}\n" + current_prompt
        
        # Format according to new Gemini API structure
        if step_number == 1:
            # First step - just the user message
            prompt_text = f"{current_prompt}\n\nUser request: {user_message}"
        else:
            # Subsequent steps - include previous context
            prompt_text = f"{current_prompt}\n\nOriginal user request: {user_message}\nContinue with the next step to complete this request."
        
        contents = [
            {
                "parts": [
                    {"text": prompt_text}
                ]
            }
        ]

        print(f"🤖 Sending request to Gemini API... {prompt_text}\n\n======")

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=contents,
        )
        
        parsed_response = parse_llm_response(response.text)
        print(f"📥 Parsed Response: {parsed_response}")
        
        if not parsed_response:
            print("❌ Failed to parse LLM response")
            break
        
        # Execute the function
        print(f"⚡ Executing: {parsed_response['function_name']}")
        execution_result = execute_llm_response(parsed_response, email_data_store)
        
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
        print("-"*60)

finally:
    # Prevent cleanup errors by removing client reference
    try:
        client = None
        gc.collect()
    except:
        pass  # Ignore any errors during cleanup

