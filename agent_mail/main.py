"""
Gmail Client Application

A comprehensive Gmail API client for reading, organizing, and managing emails.
Provides functionality for email retrieval, thread management, and automated labeling.

Author: Your Name
Date: September 2025
"""

import os.path
import base64
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Union, Any
from dataclasses import dataclass

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


@dataclass
class EmailSummary:
    """Data class for email summary information."""
    subject: str
    sender: str
    date: str
    thread_id: str
    message_id: str
    message_count: int
    content_preview: str


@dataclass
class OperationResult:
    """Data class for operation results."""
    success: bool
    message: str
    processed_items: List[str]
    errors: List[str]
    
    @property
    def summary(self) -> str:
        """Get a summary of the operation results."""
        success_count = len(self.processed_items)
        error_count = len(self.errors)
        return f"✅ {success_count} successful, ❌ {error_count} errors"


class GmailAuthenticator:
    """Handles Gmail API authentication and credential management."""
    
    def __init__(self, scopes: List[str], credentials_file: str = "credentials.json", 
                 token_file: str = "token.json"):
        """
        Initialize the authenticator.
        
        Args:
            scopes: List of Gmail API scopes required
            credentials_file: Path to the OAuth2 credentials file
            token_file: Path to store/retrieve access tokens
        """
        self.scopes = scopes
        self.credentials_file = credentials_file
        self.token_file = token_file
        self._credentials = None
    
    def authenticate(self) -> Credentials:
        """
        Authenticate with Gmail API and return credentials.
        
        Returns:
            Authenticated credentials object
            
        Raises:
            FileNotFoundError: If credentials file is missing
            Exception: If authentication fails
        """
        creds = None
        
        # Load existing token
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, self.scopes)
        
        # If there are no valid credentials available, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print("🔄 Refreshing expired credentials...")
                creds.refresh(Request())
            else:
                print("🔐 Starting OAuth2 authentication flow...")
                if not os.path.exists(self.credentials_file):
                    raise FileNotFoundError(f"Credentials file not found: {self.credentials_file}")
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.scopes
                )
                creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open(self.token_file, "w") as token:

                token.write(creds.to_json())
            print("✅ Authentication successful!")
        
        self._credentials = creds
        return creds
    
    @property
    def credentials(self) -> Credentials:
        """Get current credentials, authenticating if necessary."""
        if not self._credentials:
            return self.authenticate()
        return self._credentials


class EmailContentExtractor:
    """Utility class for extracting content from Gmail message payloads."""
    
    @staticmethod
    def extract_message_body(payload: Dict[str, Any]) -> str:
        """
        Extract readable text content from a Gmail message payload.
        
        Args:
            payload: Gmail message payload dictionary
            
        Returns:
            Extracted text content, preferring plain text over HTML
        """
        body = ""
        
        try:
            if 'parts' in payload:
                # Multi-part message
                for part in payload['parts']:
                    if part['mimeType'] == 'text/plain' and part['body'].get('data'):
                        data = part['body']['data']
                        body = base64.urlsafe_b64decode(data).decode('utf-8')
                        break
                    elif part['mimeType'] == 'text/html' and not body and part['body'].get('data'):
                        data = part['body']['data']
                        body = base64.urlsafe_b64decode(data).decode('utf-8')
            elif payload['body'].get('data'):
                # Simple message
                body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
                
        except Exception as e:
            print(f"⚠️ Warning: Could not extract message body: {e}")
            body = "[Content could not be extracted]"
        
        return body
    
    @staticmethod
    def extract_headers(payload: Dict[str, Any]) -> Dict[str, str]:
        """
        Extract common email headers from message payload.
        
        Args:
            payload: Gmail message payload dictionary
            
        Returns:
            Dictionary with extracted header values
        """
        headers = payload.get('headers', [])
        
        extracted = {
            'subject': 'No Subject',
            'from': 'Unknown Sender',
            'to': 'Unknown Recipient',
            'date': 'Unknown Date'
        }
        
        for header in headers:
            name = header['name'].lower()
            if name in ['subject', 'from', 'to', 'date']:
                extracted[name] = header['value']
        
        return extracted


class GmailClient:
    """
    Comprehensive Gmail API client for reading and managing emails.
    
    This class provides a high-level interface for common Gmail operations
    including reading emails, managing threads, and applying labels.
    """
    
    # Default Gmail API scopes
    DEFAULT_SCOPES = [
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.modify"
    ]
    
    def __init__(self, scopes: Optional[List[str]] = None):
        """
        Initialize the Gmail client.
        
        Args:
            scopes: List of Gmail API scopes. Uses default if None.
        """
        self.scopes = scopes or self.DEFAULT_SCOPES
        self.authenticator = GmailAuthenticator(self.scopes)
        self.content_extractor = EmailContentExtractor()
        self._service = None
    
    @property
    def service(self):
        """Get Gmail API service, creating it if necessary."""
        if not self._service:
            credentials = self.authenticator.authenticate()
            self._service = build("gmail", "v1", credentials=credentials)
        return self._service
    
    # ==================== EMAIL READING METHODS ====================
    
    def read_latest_emails(self, count: int = 10) -> List[EmailSummary]:
        """
        Read the latest email threads.
        
        Args:
            count: Maximum number of threads to retrieve
            
        Returns:
            List of EmailSummary objects for latest threads
        """
        print(f"📧 Reading latest {count} email threads...")
        
        try:
            # Get thread list
            results = self.service.users().threads().list(
                userId="me", 
                maxResults=count
            ).execute()
            threads = results.get("threads", [])
            
            if not threads:
                print("📭 No emails found.")
                return []
            
            return self._process_threads(threads, f"LATEST {count}")
            
        except HttpError as error:
            print(f"❌ Error reading emails: {error}")
            return []
    
    def read_emails_by_time_period(self, days_ago: int = 1, hours_ago: Optional[int] = None, 
                                 count: int = 50) -> List[EmailSummary]:
        """
        Read email threads from a specific time period.
        
        Args:
            days_ago: Number of days ago to search from
            hours_ago: Number of hours ago to search from (overrides days_ago)
            count: Maximum number of threads to return
            
        Returns:
            List of EmailSummary objects for the time period
        """
        # Calculate time parameters
        if hours_ago is not None:
            days_ago = hours_ago / 24.0
            time_description = f"last {hours_ago} hours"
        else:
            time_description = f"last {days_ago} days"
        
        print(f"📧 Searching for emails from the {time_description}...")
        
        try:
            # Create Gmail date query
            target_date = datetime.now() - timedelta(days=days_ago)
            after_date = target_date.strftime("%Y/%m/%d")
            query = f"after:{after_date}"
            
            print(f"🔍 Query: {query}")
            
            # Get threads with date filter
            results = self.service.users().threads().list(
                userId="me", 
                maxResults=count,
                q=query
            ).execute()
            threads = results.get("threads", [])
            
            if not threads:
                print(f"📭 No emails found from the {time_description}.")
                return []
            
            print(f"✅ Found {len(threads)} conversation(s) from the {time_description}")
            return self._process_threads(threads, time_description.upper())
            
        except HttpError as error:
            print(f"❌ Error reading emails: {error}")
            return []
    
    def _process_threads(self, threads: List[Dict], context: str) -> List[EmailSummary]:
        """
        Process thread data into EmailSummary objects and display them.
        
        Args:
            threads: List of thread dictionaries from Gmail API
            context: Context string for display (e.g., "LATEST 10")
            
        Returns:
            List of processed EmailSummary objects
        """
        email_summaries = []
        
        for i, thread in enumerate(threads):
            try:
                # Get full thread details
                thread_data = self.service.users().threads().get(
                    userId="me", 
                    id=thread['id']
                ).execute()
                
                messages_in_thread = thread_data['messages']
                latest_message = messages_in_thread[-1]
                
                # Extract headers and content
                headers = self.content_extractor.extract_headers(latest_message['payload'])
                content = self.content_extractor.extract_message_body(latest_message['payload'])
                
                # Create summary object
                summary = EmailSummary(
                    subject=headers['subject'],
                    sender=headers['from'],
                    date=headers['date'],
                    thread_id=thread['id'],
                    message_id=latest_message['id'],
                    message_count=len(messages_in_thread),
                    content_preview=content[:500] + "..." if len(content) > 500 else content
                )
                
                email_summaries.append(summary)
                
                # Display the email
                self._display_email_summary(summary, i + 1, context)
                
            except HttpError as error:
                print(f"❌ Error processing thread {thread.get('id', 'unknown')}: {error}")
        
        return email_summaries
    
    def _display_email_summary(self, summary: EmailSummary, index: int, context: str):
        """Display a formatted email summary."""
        print(f"\n=== CONVERSATION {index} ({context}) ===")
        print(f"Subject: {summary.subject}")
        print(f"From: {summary.sender}")
        print(f"Date: {summary.date}")
        print(f"Messages in thread: {summary.message_count}")
        print("Latest message content:")
        print(summary.content_preview)
        
        if summary.message_count > 1:
            print(f"\n[This is part of a conversation with {summary.message_count} messages]")
        
        print("=" * 50)
    
    # ==================== EMAIL MANAGEMENT METHODS ====================
    
    def get_or_create_label(self, label_name: str) -> Optional[str]:
        """
        Get a label by name, or create it if it doesn't exist.
        
        Args:
            label_name: Name of the label to get or create
            
        Returns:
            Label ID if successful, None if failed
        """
        try:
            # Search for existing label
            results = self.service.users().labels().list(userId="me").execute()
            labels = results.get("labels", [])
            
            for label in labels:
                if label["name"].lower() == label_name.lower():
                    print(f"✅ Found existing label: {label_name}")
                    return label["id"]
            
            # Create new label
            label_object = {
                "name": label_name,
                "labelListVisibility": "labelShow",
                "messageListVisibility": "show"
            }
            
            created_label = self.service.users().labels().create(
                userId="me", 
                body=label_object
            ).execute()
            
            print(f"🏷️ Created new label: {label_name}")
            return created_label["id"]
            
        except HttpError as error:
            print(f"❌ Error with label '{label_name}': {error}")
            return None
    
    def apply_label_to_emails(self, label_name: str, email_ids: Optional[List[str]] = None, 
                            thread_ids: Optional[List[str]] = None) -> OperationResult:
        """
        Apply a label to specified emails or threads.
        
        Args:
            label_name: Name of the label to apply
            email_ids: List of individual email IDs to label
            thread_ids: List of thread IDs to label (all emails in thread)
            
        Returns:
            OperationResult with details of the operation
        """
        if not email_ids and not thread_ids:
            return OperationResult(
                success=False,
                message="No email or thread IDs provided",
                processed_items=[],
                errors=["No targets specified"]
            )
        
        # Get or create the label
        label_id = self.get_or_create_label(label_name)
        if not label_id:
            return OperationResult(
                success=False,
                message=f"Could not create or find label: {label_name}",
                processed_items=[],
                errors=[f"Label creation failed: {label_name}"]
            )
        
        processed_items = []
        errors = []
        
        try:
            # Apply label to individual emails
            if email_ids:
                for email_id in email_ids:
                    try:
                        self.service.users().messages().modify(
                            userId="me",
                            id=email_id,
                            body={"addLabelIds": [label_id]}
                        ).execute()
                        processed_items.append(email_id)
                        print(f"✅ Applied '{label_name}' to email {email_id}")
                    except HttpError as error:
                        error_msg = f"Failed to label email {email_id}: {error}"
                        errors.append(error_msg)
                        print(f"❌ {error_msg}")
            
            # Apply label to entire threads
            if thread_ids:
                for thread_id in thread_ids:
                    try:
                        self.service.users().threads().modify(
                            userId="me",
                            id=thread_id,
                            body={"addLabelIds": [label_id]}
                        ).execute()
                        processed_items.append(f"thread_{thread_id}")
                        print(f"✅ Applied '{label_name}' to thread {thread_id}")
                    except HttpError as error:
                        error_msg = f"Failed to label thread {thread_id}: {error}"
                        errors.append(error_msg)
                        print(f"❌ {error_msg}")
            
            result = OperationResult(
                success=len(processed_items) > 0,
                message=f"Applied label '{label_name}' to {len(processed_items)} items",
                processed_items=processed_items,
                errors=errors
            )
            
            print(f"\n📊 {result.summary}")
            return result
            
        except HttpError as error:
            return OperationResult(
                success=False,
                message=f"Operation failed: {error}",
                processed_items=processed_items,
                errors=errors + [str(error)]
            )
    
    def list_labels(self) -> List[Dict[str, Any]]:
        """
        List all available labels in the Gmail account.
        
        Returns:
            List of label dictionaries
        """
        try:
            results = self.service.users().labels().list(userId="me").execute()
            labels = results.get("labels", [])
            
            print("📋 Available Gmail Labels:")
            print("=" * 40)
            
            system_labels = [label for label in labels if label.get("type") == "system"]
            user_labels = [label for label in labels if label.get("type") != "system"]
            
            if system_labels:
                print("\n🔧 System Labels:")
                for label in system_labels:
                    print(f"  • {label['name']} (ID: {label['id']})")
            
            if user_labels:
                print("\n🏷️ Custom Labels:")
                for label in user_labels:
                    print(f"  • {label['name']} (ID: {label['id']})")
            else:
                print("\n🏷️ Custom Labels: None created yet")
            
            print(f"\nTotal: {len(system_labels)} system labels, {len(user_labels)} custom labels")
            return labels
            
        except HttpError as error:
            print(f"❌ Error retrieving labels: {error}")
            return []
    
    # ==================== CONVENIENCE METHODS ====================
    
    def label_email_threads(self, thread_ids: List[str], label_name: str) -> OperationResult:
        """
        Generic email labeler function - Apply a label to specified email threads.
        
        This is the main function for labeling emails by thread IDs. It provides
        a simple interface for bulk labeling operations.
        
        Args:
            thread_ids: List of Gmail thread IDs to label
            label_name: Name of the label to apply (will be created if doesn't exist)
            
        Returns:
            OperationResult with detailed success/error information
            
        Example:
            # Label specific threads as urgent
            thread_ids = ['thread_123', 'thread_456', 'thread_789']
            result = client.label_email_threads(thread_ids, "URGENT")
            print(f"Labeled {len(result.processed_items)} threads")
        """
        if not thread_ids:
            return OperationResult(
                success=False,
                message="No thread IDs provided",
                processed_items=[],
                errors=["Empty thread_ids list"]
            )
        
        print(f"🏷️ Applying label '{label_name}' to {len(thread_ids)} email thread(s)...")
        
        # Use the existing apply_label_to_emails method with thread_ids
        return self.apply_label_to_emails(label_name, thread_ids=thread_ids)
    
    def mark_latest_as_important(self, count: int = 5, label_name: str = "Important") -> OperationResult:
        """Mark the latest emails with specified label."""
        print(f"🏷️ Marking the latest {count} emails as '{label_name}'...")
        
        emails = self.read_latest_emails(count=count)
        if not emails:
            return OperationResult(False, "No emails found", [], ["No emails to mark"])
        
        thread_ids = [email.thread_id for email in emails]
        return self.label_email_threads(thread_ids, label_name)
    
    def mark_time_period_as_important(self, days_ago: int = 1, hours_ago: Optional[int] = None, 
                                    label_name: str = "Important") -> OperationResult:
        """Mark emails from a time period with specified label."""
        time_desc = f"last {hours_ago} hours" if hours_ago else f"last {days_ago} days"
        print(f"🏷️ Marking emails from the {time_desc} as '{label_name}'...")
        
        emails = self.read_emails_by_time_period(days_ago=days_ago, hours_ago=hours_ago)
        if not emails:
            return OperationResult(False, f"No emails found from {time_desc}", [], [])
        
        thread_ids = [email.thread_id for email in emails]
        return self.label_email_threads(thread_ids, label_name)
    
    # Quick access methods for common time periods
    def read_today(self) -> List[EmailSummary]:
        """Read emails from today (last 24 hours)."""
        return self.read_emails_by_time_period(hours_ago=24)
    
    def read_this_week(self) -> List[EmailSummary]:
        """Read emails from the last 7 days."""
        return self.read_emails_by_time_period(days_ago=7)
    
    def read_this_month(self) -> List[EmailSummary]:
        """Read emails from the last 30 days."""
        return self.read_emails_by_time_period(days_ago=30)


# ==================== CONVENIENCE FUNCTIONS ====================

def create_gmail_client() -> GmailClient:
    """Create and return a configured Gmail client."""
    return GmailClient()


def label_email_threads(thread_ids: List[str], label_name: str) -> OperationResult:
    """
    Standalone generic email labeler function.
    
    This is a convenient wrapper around the GmailClient.label_email_threads method
    for quick one-off labeling operations without creating a client instance.
    
    Args:
        thread_ids: List of Gmail thread IDs to label
        label_name: Name of the label to apply
        
    Returns:
        OperationResult with operation details
        
    Example:
        # Quick labeling without creating client
        thread_ids = ['thread_123', 'thread_456']
        result = label_email_threads(thread_ids, "URGENT")
        print(result.summary)
    """
    client = create_gmail_client()
    return client.label_email_threads(thread_ids, label_name)


# Legacy function names for backward compatibility
def read_emails(count: int = 10) -> List[EmailSummary]:
    """Legacy function - read latest emails."""
    client = create_gmail_client()
    return client.read_latest_emails(count)


def read_emails_today() -> List[EmailSummary]:
    """Legacy function - read today's emails."""
    client = create_gmail_client()
    return client.read_today()


def main():
    """
    Main function demonstrating Gmail client usage.
    
    This function shows examples of how to use the GmailClient
    for various email operations.
    """
    print("🚀 Gmail Client Demo")
    print("=" * 50)
    
    try:
        # Create Gmail client
        client = create_gmail_client()
        
        # Read today's emails
        # print("\n📧 Reading today's emails...")
        today_emails = client.read_today()
        
        # print("Total Number of ")
        if today_emails:
            print(f"\n✅ Found {len(today_emails)} emails from today")
            
            # Example: Use generic labeler to mark first email as important
            if len(today_emails) > 0:
                print(f"\n🏷️ Using generic labeler to mark first email as IMPORTANT...")
                
                # Method 1: Using the client instance method
                result = client.label_email_threads(
                    thread_ids=[today_emails[0].thread_id],
                    label_name="SPAM"
                )
                print(f"Result: {result.message}")
                
                # Method 2: Using the standalone function (commented out to avoid duplicate labeling)
                # result2 = label_email_threads([today_emails[0].thread_id], "URGENT")
                # print(f"Standalone function result: {result2.summary}")
        
        # # List available labels
        print(f"\n📋 Listing available labels...")
        client.list_labels()
        
        print(f"\n✅ Demo completed successfully!")
        
    except Exception as error:
        print(f"❌ Demo failed: {error}")


if __name__ == "__main__":
    main()