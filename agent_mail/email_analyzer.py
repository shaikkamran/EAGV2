"""
Universal AI-Powered Email Intent Analysis Module

This module provides a completely generic email analysis system using Google's Gemini AI.
It can analyze emails for ANY intent without predefined restrictions - the AI dynamically
understands and classifies emails based on the user's intent description.

Author: AI Assistant
Date: September 2025
"""

import os
from typing import List, Dict, Optional
from dataclasses import dataclass

from google import genai
from dotenv import load_dotenv

load_dotenv()


# ==================== DATA CLASSES ====================

@dataclass
class AnalysisResult:
    """Result of email intent analysis."""
    intent: str
    total_emails: int
    classified_emails: int
    thread_ids: List[str]
    success: bool
    error_message: Optional[str] = None


# ==================== UNIVERSAL AI ANALYSIS ENGINE ====================

class UniversalEmailAnalyzer:
    """
    Universal AI engine for analyzing any email intent without restrictions.
    
    This class provides a completely generic interface that can understand
    and classify emails for ANY intent the user specifies.
    """
    
    def __init__(self, gemini_client: genai.Client, gmail_client):
        """Initialize the analyzer with required clients."""
        self.gemini_client = gemini_client
        self.gmail_client = gmail_client
    
    def analyze_emails_for_intent(self, emails: List, intent: str) -> AnalysisResult:
        """
        Analyze emails for ANY specified intent using universal AI reasoning.
        
        Args:
            emails: List of email objects to analyze
            intent: ANY intent description (e.g., "SPAM", "URGENT", "CUSTOMER COMPLAINTS", 
                   "AMAZON ORDERS", "BIRTHDAY INVITATIONS", "WORK MEETINGS", etc.)
            
        Returns:
            AnalysisResult with classification details
        """
        if not emails:
            return AnalysisResult(
                intent=intent,
                total_emails=0,
                classified_emails=0,
                thread_ids=[],
                success=True
            )
        
        print(f"🤖 Analyzing {len(emails)} emails for intent: {intent}")
        
        # Debug: Check the actual emails being passed
        print(f"🔍 Email Analysis Debug:")
        print(f"  - Emails type: {type(emails)}")
        print(f"  - Emails length: {len(emails)}")
        if emails:
            print(f"  - First email type: {type(emails[0])}")
            print(f"  - First email attributes: {dir(emails[0])[:10]}...")  # First 10 attributes
            if hasattr(emails[0], 'subject'):
                print(f"  - Sample subjects: {[e.subject[:50] for e in emails[:3]]}")
            if hasattr(emails[0], 'thread_id'):
                print(f"  - Sample thread IDs: {[e.thread_id for e in emails[:3]]}")
        print()
        
        try:
            # Generate universal AI prompt for ANY intent
            analysis_prompt = self._create_universal_prompt(emails, intent)
            
            # Call Gemini AI
            response = self.gemini_client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[{"parts": [{"text": analysis_prompt}]}]
            )
            
            # Debug: Print the AI response for troubleshooting
            print(f"🔍 AI Response:")
            print(f"{response.text}")
            print()
            
            # Parse response and extract thread IDs
            classified_thread_ids = self._parse_ai_response(response.text, emails)
            
            # Display results
            self._display_analysis_results(intent, classified_thread_ids, emails)
            
            return AnalysisResult(
                intent=intent,
                total_emails=len(emails),
                classified_emails=len(classified_thread_ids),
                thread_ids=classified_thread_ids,
                success=True
            )
            
        except Exception as e:
            print(f"❌ AI analysis failed for intent '{intent}': {e}")
            
            # Fallback to keyword-based analysis
            fallback_thread_ids = self._keyword_fallback(emails, intent)
            
            return AnalysisResult(
                intent=intent,
                total_emails=len(emails),
                classified_emails=len(fallback_thread_ids),
                thread_ids=fallback_thread_ids,
                success=False,
                error_message=str(e)
            )
    
    def _create_universal_prompt(self, emails: List, intent: str) -> str:
        """Create a universal AI prompt that can handle ANY intent."""
        
        # Prepare email data - handle both EmailSummary objects and dictionaries
        email_data = []
        for idx, email in enumerate(emails):
            try:
                # Extract email information safely
                if hasattr(email, 'thread_id'):
                    # EmailSummary object
                    thread_id = email.thread_id
                    subject = email.subject
                    sender = email.sender
                    date = email.date
                    content = email.content_preview[:400] if email.content_preview else ""
                else:
                    # Dictionary or other format
                    thread_id = email.get('thread_id', f'thread_{idx}')
                    subject = email.get('subject', 'No subject')
                    sender = email.get('sender', 'Unknown sender')
                    date = email.get('date', 'Unknown date')
                    content = email.get('content_preview', '')[:400]
                
                email_data.append(f"""
Email {idx + 1}:
- Thread ID: {thread_id}
- Subject: {subject}
- From: {sender}
- Date: {date}
- Content: {content}...
""")
            except Exception as e:
                print(f"⚠️ Error processing email {idx}: {e}")
                # Create a fallback entry
                email_data.append(f"""
Email {idx + 1}:
- Thread ID: email_error_{idx}
- Subject: Error processing email
- From: Unknown
- Date: Unknown
- Content: Could not process email data
""")
        
        # Create universal intent-agnostic prompt
        prompt = f"""
You are an expert email analyst with deep understanding of email patterns, contexts, and user intents.

TASK: Analyze these emails and identify which ones match the specified intent.

INTENT TO IDENTIFY: {intent}

EMAILS TO ANALYZE:
{chr(10).join(email_data)}

UNIVERSAL ANALYSIS FRAMEWORK:
Use your comprehensive understanding to determine if each email relates to "{intent}". Consider:

1. SEMANTIC UNDERSTANDING:
   - Does the email's meaning and purpose align with "{intent}"?
   - What is the core nature and intention of this email?

2. CONTEXTUAL ANALYSIS:
   - Who is the sender and what type of organization/person are they?
   - What is the subject matter and tone of the email?
   - What action or information is being communicated?

3. CONTENT PATTERNS:
   - Are there specific keywords, phrases, or patterns that relate to "{intent}"?
   - Does the email structure or format suggest it belongs to this category?

4. SENDER CONTEXT:
   - Does the sender type (domain, organization) align with "{intent}"?
   - Is this from a source that would typically send "{intent}" related emails?

5. PURPOSE ALIGNMENT:
   - What is the primary purpose of this email?
   - Does this purpose match what "{intent}" emails typically aim to achieve?

ANALYSIS GUIDELINES:
- Think deeply about what "{intent}" means in the context of email communication
- Consider both explicit and implicit indicators
- Be precise - only classify emails that truly belong to this intent
- Use your knowledge of email patterns, business communications, and user behaviors
- When uncertain, err on the side of NOT classifying to avoid false positives

REQUIRED OUTPUT FORMAT:
Return ONLY the thread IDs of emails that clearly match "{intent}", one per line:
thread_abc123
thread_def456

If NO emails match the intent, return:
NO_MATCHES_FOUND

Do not include explanations, reasoning, or additional text - just the thread IDs or "NO_MATCHES_FOUND".
"""
        return prompt
    
    def _parse_ai_response(self, ai_response: str, emails: List) -> List[str]:
        """Parse AI response to extract valid thread IDs."""
        classified_thread_ids = []
        
        # Check for no matches
        if "NO_MATCHES_FOUND" in ai_response.upper():
            return []
        
        # Extract thread IDs
        lines = ai_response.strip().split('\n')
        # Get valid thread IDs from emails (handle both object and dict formats)
        valid_thread_ids = set()
        for email in emails:
            if hasattr(email, 'thread_id'):
                valid_thread_ids.add(email.thread_id)
            elif isinstance(email, dict) and 'thread_id' in email:
                valid_thread_ids.add(email['thread_id'])
        
        for line in lines:
            line = line.strip()
            # Check if line looks like a thread ID (either with 'thread_' prefix or raw thread ID)
            if (line.startswith('thread_') or (line and len(line) > 10 and line.replace('_', '').replace('-', '').isalnum())) and line in valid_thread_ids:
                classified_thread_ids.append(line)
                print(f"    ✅ Found valid thread ID: {line}")
        
        return classified_thread_ids
    
    def _display_analysis_results(self, intent: str, classified_thread_ids: List[str], emails: List):
        """Display analysis results in a user-friendly format."""
        if classified_thread_ids:
            print(f"✅ AI classified {len(classified_thread_ids)} emails as '{intent}':")
            for thread_id in classified_thread_ids:
                # Find matching email (handle both object and dict formats)
                email = None
                for e in emails:
                    if hasattr(e, 'thread_id') and e.thread_id == thread_id:
                        email = e
                        break
                    elif isinstance(e, dict) and e.get('thread_id') == thread_id:
                        email = e
                        break
                
                if email:
                    if hasattr(email, 'subject'):
                        subject = email.subject[:50]
                        sender = email.sender
                    else:
                        subject = email.get('subject', 'No subject')[:50]
                        sender = email.get('sender', 'Unknown')
                    print(f"   📧 {intent}: {subject}... (from: {sender})")
        else:
            print(f"📭 No emails classified as '{intent}'")
    
    def _keyword_fallback(self, emails: List, intent: str) -> List[str]:
        """
        Fallback keyword-based classification when AI fails.
        Uses the intent words themselves as keywords.
        """
        print(f"🔄 Using keyword fallback for intent: {intent}")
        
        # Extract keywords from the intent itself
        intent_words = intent.lower().replace('_', ' ').split()
        keywords = [word for word in intent_words if len(word) > 2]  # Filter short words
        
        if not keywords:
            return []
        
        print(f"🔍 Fallback keywords: {keywords}")
        
        classified_thread_ids = []
        
        for email in emails:
            # Handle both EmailSummary objects and dictionaries
            if hasattr(email, 'subject'):
                content = (email.subject + " " + email.sender + " " + (email.content_preview or "")).lower()
                thread_id = email.thread_id
                subject = email.subject
            else:
                content = (email.get('subject', '') + " " + email.get('sender', '') + " " + email.get('content_preview', '')).lower()
                thread_id = email.get('thread_id', f'unknown_{id(email)}')
                subject = email.get('subject', 'No subject')
            
            # Count keyword matches
            matches = sum(1 for keyword in keywords if keyword in content)
            
            # Conservative threshold for fallback (at least half the keywords)
            threshold = max(1, len(keywords) // 2)
            if matches >= threshold:
                classified_thread_ids.append(thread_id)
                print(f"📌 Keyword match for '{intent}': {subject} (matches: {matches})")
        
        return classified_thread_ids


# ==================== CONVENIENCE FUNCTIONS ====================

def create_analyzer(gmail_client, gemini_api_key: Optional[str] = None) -> UniversalEmailAnalyzer:
    """
    Create and return a configured UniversalEmailAnalyzer instance.
    
    Args:
        gmail_client: Configured Gmail client instance
        gemini_api_key: Google AI API key (optional, will use environment variable)
        
    Returns:
        Configured UniversalEmailAnalyzer instance
    """
    api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is required")
    
    gemini_client = genai.Client(api_key=api_key)
    return UniversalEmailAnalyzer(gemini_client, gmail_client)


def analyze_emails_for_intent(emails: List, intent: str, gmail_client, gemini_api_key: Optional[str] = None) -> List[str]:
    """
    Universal function for analyzing emails for ANY intent.
    
    Args:
        emails: List of email objects
        intent: ANY intent description (completely flexible)
        gmail_client: Configured Gmail client instance
        gemini_api_key: Google AI API key (optional)
        
    Returns:
        List of thread IDs that match the intent
        
    Examples:
        analyze_emails_for_intent(emails, "SPAM", gmail_client)
        analyze_emails_for_intent(emails, "URGENT CUSTOMER COMPLAINTS", gmail_client)
        analyze_emails_for_intent(emails, "AMAZON ORDERS", gmail_client)
        analyze_emails_for_intent(emails, "BIRTHDAY INVITATIONS", gmail_client)
        analyze_emails_for_intent(emails, "WORK MEETINGS", gmail_client)
        analyze_emails_for_intent(emails, "NEWSLETTER SUBSCRIPTIONS", gmail_client)
    """
    # Clean up intent for label naming
    clean_intent = intent.upper().strip()
    label_name = clean_intent.replace(" ", "_").replace("-", "_")
    
    print(f"🎯 Analyzing for intent: '{intent}' (will label as: '{label_name}')")
    
    # Initialize analyzer
    analyzer = create_analyzer(gmail_client, gemini_api_key)
    
    # Perform analysis
    result = analyzer.analyze_emails_for_intent(emails, intent)
    
    # Auto-apply labels if emails were classified
    if result.thread_ids:
        print(f"🏷️ Auto-applying '{label_name}' labels to {len(result.thread_ids)} emails...")
        try:
            label_result = gmail_client.apply_label_to_emails(label_name, thread_ids=result.thread_ids)
            print(f"📊 Labeling Result: {label_result.summary}")
        except Exception as e:
            print(f"⚠️ Labeling failed: {e}")
    
    return result.thread_ids


# ==================== TESTING UTILITIES ====================

def test_universal_analysis(gmail_client, test_intents: Optional[List[str]] = None):
    """
    Test function to demonstrate the universal intent analysis capabilities.
    
    Args:
        gmail_client: Configured Gmail client instance
        test_intents: List of ANY intents to test
    """
    print("🧪 Testing Universal Intent Analysis System")
    print("=" * 60)
    
    # Use provided intents or diverse examples
    intents_to_test = test_intents or [
        "SPAM",
        "URGENT CUSTOMER SUPPORT", 
        "AMAZON DELIVERIES",
        "WORK MEETINGS",
        "PROMOTIONAL OFFERS",
        "FINANCIAL STATEMENTS",
        "SOCIAL MEDIA NOTIFICATIONS"
    ]
    
    for intent in intents_to_test:
        print(f"\n🔍 Testing intent: '{intent}'...")
        
        try:
            # Get recent emails for testing
            recent_emails = gmail_client.read_emails_by_time_period(days_ago=3, count=5)
            
            if recent_emails:
                # Analyze for current intent
                result_thread_ids = analyze_emails_for_intent(recent_emails, intent, gmail_client)
                
                print(f"📊 Results for '{intent}':")
                print(f"   📧 Total emails analyzed: {len(recent_emails)}")
                print(f"   🎯 Emails matching intent: {len(result_thread_ids)}")
                print()
            else:
                print(f"📭 No recent emails found for testing '{intent}'")
                
        except Exception as e:
            print(f"❌ Error testing '{intent}': {e}")
    
    print("✅ Universal intent analysis testing completed!")


# ==================== EXAMPLE INTENTS ====================

def get_example_intents() -> List[str]:
    """
    Get a list of example intents to demonstrate the system's flexibility.
    These are just examples - the system can handle ANY intent.
    """
    return [
        # Common intents
        "SPAM", "URGENT", "WORK", "PERSONAL",
        
        # Specific business intents  
        "CUSTOMER COMPLAINTS", "SALES INQUIRIES", "SUPPORT TICKETS",
        "MEETING INVITATIONS", "PROJECT UPDATES", "INVOICE REMINDERS",
        
        # E-commerce intents
        "AMAZON ORDERS", "SHOPPING CONFIRMATIONS", "DELIVERY NOTIFICATIONS",
        "REFUND REQUESTS", "PRODUCT RECOMMENDATIONS",
        
        # Financial intents
        "BANK STATEMENTS", "CREDIT CARD BILLS", "PAYMENT CONFIRMATIONS",
        "SUBSCRIPTION RENEWALS", "TAX DOCUMENTS",
        
        # Social intents  
        "BIRTHDAY INVITATIONS", "EVENT ANNOUNCEMENTS", "NEWSLETTER SUBSCRIPTIONS",
        "SOCIAL MEDIA NOTIFICATIONS", "FORUM REPLIES",
        
        # Travel intents
        "FLIGHT CONFIRMATIONS", "HOTEL BOOKINGS", "TRAVEL UPDATES",
        "VISA DOCUMENTS", "ITINERARY CHANGES",
        
        # And literally ANY other intent the user can think of!
        "CAT VIDEOS", "COOKING RECIPES", "CRYPTOCURRENCY NEWS",
        "REAL ESTATE LISTINGS", "JOB APPLICATIONS", "DATING MATCHES"
    ]


if __name__ == "__main__":
    print("🌟 Universal Email Intent Analyzer")
    print("This system can analyze emails for ANY intent you specify!")
    print("\nExample intents:")
    for intent in get_example_intents()[:10]:
        print(f"   • {intent}")
    print("   • ... and literally ANY other intent you can think of!")