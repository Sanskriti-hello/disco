# backend/mcp_tools/google_workspace.py
"""
Google Workspace MCP - Production Implementation
Connects to Google Calendar, Drive, Gmail, Docs using OAuth2

Setup Instructions:
1. Go to https://console.cloud.google.com/
2. Create a new project or select existing
3. Enable APIs: Calendar API, Drive API, Gmail API, Docs API
4. Create OAuth 2.0 credentials (Desktop app type)
5. Download credentials.json and place in backend/mcp/
6. First run will open browser for authorization
7. Token will be saved in token.json for future use

Required .env:
    GOOGLE_CREDENTIALS_PATH=backend/mcp/credentials.json
    GOOGLE_TOKEN_PATH=backend/mcp/token.json
"""

import os
import pickle
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Scopes define what APIs we can access
SCOPES = [
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/calendar.events',
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/drive.metadata.readonly',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/documents.readonly',
    'https://www.googleapis.com/auth/youtube.readonly'
]


class GoogleWorkspaceError(Exception):
    """Custom exception for Google Workspace errors"""
    pass


class GoogleWorkspaceMCP:
    """
    Production Google Workspace integration with proper OAuth2
    """
    
    def __init__(self, access_token: Optional[str] = None):
        self.credentials_path = os.getenv(
            "GOOGLE_CREDENTIALS_PATH", 
            os.path.join(os.path.dirname(__file__), "credentials.json")
        )
        self.token_path = os.getenv(
            "GOOGLE_TOKEN_PATH",
            os.path.join(os.path.dirname(__file__), "token.json")
        )
        
        self.creds = None
        
        if access_token:
            self._initialize_from_token(access_token)
        else:
            self._authenticate()
    
    def _initialize_from_token(self, token_string: str):
        """Initialize credentials from a raw access token string (e.g. from extension)"""
        self.creds = Credentials(token_string)
        print("✓ Initialized Google Workspace with provided Access Token")
    
    def _authenticate(self):
        """
        Authenticate with Google using OAuth2
        Flow:
        1. Check if token.json exists (saved credentials)
        2. If expired, refresh it
        3. If no token, run OAuth flow (opens browser)
        """
        
        # Load saved credentials
        if os.path.exists(self.token_path):
            with open(self.token_path, 'rb') as token:
                self.creds = pickle.load(token)
        
        # If credentials don't exist or are invalid
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                print("[GoogleWorkspace] Refreshing access token...")
                self.creds.refresh(Request())
            else:
                # No valid credentials - run OAuth flow
                if not os.path.exists(self.credentials_path):
                    raise GoogleWorkspaceError(
                        f"Credentials file not found at {self.credentials_path}\n"
                        "Please download OAuth2 credentials from Google Cloud Console"
                    )
                
                print("[GoogleWorkspace] Starting OAuth flow (will open browser)...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES
                )
                # Let the library pick a random available port (Standard for Desktop apps)
                self.creds = flow.run_local_server(port=8080)
            
            # Save credentials for next run
            with open(self.token_path, 'wb') as token:
                pickle.dump(self.creds, token)
            
            print("PASS: Google Workspace authentication successful")
    
    # ========================================================================
    # CALENDAR API
    # ========================================================================
    
    def get_calendar_events(
        self,
        time_min: Optional[str] = None,
        time_max: Optional[str] = None,
        max_results: int = 10,
        calendar_id: str = 'primary'
    ) -> Dict[str, Any]:
        """
        Get upcoming calendar events
        
        Args:
            time_min: Start time (ISO format). Defaults to now
            time_max: End time (ISO format). Defaults to 7 days from now
            max_results: Max number of events to return
            calendar_id: Calendar ID (default: 'primary')
        
        Returns:
            {
                "events": [...],
                "busy_dates": [...],
                "free_ranges": [...]
            }
        """
        
        try:
            service = build('calendar', 'v3', credentials=self.creds)
            
            # Default time range: now to 7 days
            if not time_min:
                time_min = datetime.now(datetime.UTC).isoformat().replace('+00:00', 'Z')
            if not time_max:
                time_max = (datetime.now(datetime.UTC) + timedelta(days=7)).isoformat().replace('+00:00', 'Z')
            
            # Fetch events
            events_result = service.events().list(
                calendarId=calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Extract busy dates
            busy_dates = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                if start:
                    date_str = start.split('T')[0]
                    if date_str not in busy_dates:
                        busy_dates.append(date_str)
            
            # Format events
            formatted_events = []
            for event in events:
                formatted_events.append({
                    'summary': event.get('summary', 'Untitled Event'),
                    'start': event['start'].get('dateTime', event['start'].get('date')),
                    'end': event['end'].get('dateTime', event['end'].get('date')),
                    'location': event.get('location', ''),
                    'description': event.get('description', ''),
                    'attendees': [a.get('email') for a in event.get('attendees', [])],
                    'htmlLink': event.get('htmlLink', '')
                })
            
            return {
                'events': formatted_events,
                'busy_dates': busy_dates,
                'free_ranges': self._calculate_free_time(events, time_min, time_max)
            }
            
        except HttpError as error:
            raise GoogleWorkspaceError(f"Calendar API error: {error}")
    
    def create_event(
        self,
        summary: str,
        start_time: str,
        end_time: str,
        description: str = "",
        location: str = "",
        attendees: List[str] = None
    ) -> Dict[str, Any]:
        """
        Create a calendar event
        
        Args:
            summary: Event title
            start_time: ISO format datetime
            end_time: ISO format datetime
            description: Event description
            location: Event location
            attendees: List of email addresses
        
        Returns:
            {"status": "created", "link": "...", "event_id": "..."}
        """
        
        try:
            service = build('calendar', 'v3', credentials=self.creds)
            
            event = {
                'summary': summary,
                'location': location,
                'description': description,
                'start': {
                    'dateTime': start_time,
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': end_time,
                    'timeZone': 'UTC',
                },
            }
            
            if attendees:
                event['attendees'] = [{'email': email} for email in attendees]
            
            created_event = service.events().insert(
                calendarId='primary',
                body=event
            ).execute()
            
            return {
                'status': 'created',
                'link': created_event.get('htmlLink'),
                'event_id': created_event.get('id')
            }
            
        except HttpError as error:
            raise GoogleWorkspaceError(f"Failed to create event: {error}")
    
    def _calculate_free_time(
        self,
        events: List[Dict],
        time_min: str,
        time_max: str
    ) -> List[Dict[str, str]]:
        """Calculate free time slots between events"""
        
        if not events:
            return [{
                'start': time_min,
                'end': time_max
            }]
        
        free_slots = []
        prev_end = time_min
        
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            if start > prev_end:
                free_slots.append({
                    'start': prev_end,
                    'end': start
                })
            prev_end = event['end'].get('dateTime', event['end'].get('date'))
        
        # Add final free slot
        if prev_end < time_max:
            free_slots.append({
                'start': prev_end,
                'end': time_max
            })
        
        return free_slots
    
    # ========================================================================
    # GOOGLE DRIVE API
    # ========================================================================
    
    def search_drive(
        self,
        query: str,
        limit: int = 10,
        file_types: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search Google Drive files
        
        Args:
            query: Search query (file name, content, etc.)
            limit: Max results
            file_types: Filter by MIME types (e.g., ['document', 'spreadsheet'])
        
        Returns:
            List of files with metadata
        """
        
        try:
            service = build('drive', 'v3', credentials=self.creds)
            
            # Build query string
            q = f"name contains '{query}'"
            
            if file_types:
                mime_types = {
                    'document': 'application/vnd.google-apps.document',
                    'spreadsheet': 'application/vnd.google-apps.spreadsheet',
                    'presentation': 'application/vnd.google-apps.presentation',
                    'pdf': 'application/pdf'
                }
                type_filters = [f"mimeType='{mime_types.get(t, t)}'" for t in file_types]
                q += " and (" + " or ".join(type_filters) + ")"
            
            # Execute search
            results = service.files().list(
                q=q,
                pageSize=limit,
                fields="files(id, name, mimeType, webViewLink, modifiedTime, owners, iconLink)",
                orderBy="modifiedTime desc"
            ).execute()
            
            files = results.get('files', [])
            
            formatted_files = []
            for file in files:
                formatted_files.append({
                    'id': file['id'],
                    'name': file['name'],
                    'mimeType': file['mimeType'],
                    'webViewLink': file.get('webViewLink', ''),
                    'modifiedTime': file.get('modifiedTime', ''),
                    'owner': file.get('owners', [{}])[0].get('emailAddress', 'Unknown'),
                    'iconLink': file.get('iconLink', '')
                })
            
            return formatted_files
            
        except HttpError as error:
            raise GoogleWorkspaceError(f"Drive API error: {error}")
    
    def get_file_content(self, file_id: str) -> str:
        """
        Get content of a Google Doc
        
        Args:
            file_id: Google Drive file ID
        
        Returns:
            Plain text content
        """
        
        try:
            service = build('docs', 'v1', credentials=self.creds)
            
            document = service.documents().get(documentId=file_id).execute()
            
            # Extract text from document structure
            content = []
            for element in document.get('body', {}).get('content', []):
                if 'paragraph' in element:
                    for text_run in element['paragraph'].get('elements', []):
                        if 'textRun' in text_run:
                            content.append(text_run['textRun'].get('content', ''))
            
            return ''.join(content)
            
        except HttpError as error:
            raise GoogleWorkspaceError(f"Failed to fetch document: {error}")
    
    # ========================================================================
    # GMAIL API
    # ========================================================================
    
    def search_gmail(
        self,
        query: str,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search Gmail messages
        
        Args:
            query: Gmail search query (e.g., "from:user@example.com")
            max_results: Max results
        
        Returns:
            List of email messages
        """
        
        try:
            service = build('gmail', 'v1', credentials=self.creds)
            
            # Search messages
            results = service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            
            formatted_messages = []
            for msg in messages:
                # Get full message details
                msg_data = service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='metadata',
                    metadataHeaders=['From', 'To', 'Subject', 'Date']
                ).execute()
                
                headers = {h['name']: h['value'] for h in msg_data['payload']['headers']}
                
                formatted_messages.append({
                    'id': msg['id'],
                    'from': headers.get('From', ''),
                    'to': headers.get('To', ''),
                    'subject': headers.get('Subject', ''),
                    'date': headers.get('Date', ''),
                    'snippet': msg_data.get('snippet', '')
                })
            
            return formatted_messages
            
        except HttpError as error:
            raise GoogleWorkspaceError(f"Gmail API error: {error}")


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

google_workspace_mcp = None

def get_google_workspace_mcp() -> GoogleWorkspaceMCP:
    """
    Get singleton instance of Google Workspace MCP
    Lazy initialization - only authenticates when first called
    """
    global google_workspace_mcp
    
    if google_workspace_mcp is None:
        google_workspace_mcp = GoogleWorkspaceMCP()
    
    return google_workspace_mcp


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    import json
    from dotenv import load_dotenv
    
    load_dotenv()
    
    try:
        print("🔐 Initializing Google Workspace MCP...")
        mcp = get_google_workspace_mcp()
        
        # Test 1: Calendar
        print("\n📅 Testing Calendar API...")
        events = mcp.get_calendar_events(max_results=5)
        print(f"PASS: Found {len(events['events'])} upcoming events")
        if events['events']:
            print(f"  Next event: {events['events'][0]['summary']}")
        
        # Test 2: Drive
        print("\n📁 Testing Drive API...")
        files = mcp.search_drive("project", limit=5)
        print(f"PASS: Found {len(files)} files")
        for f in files[:3]:
            print(f"  - {f['name']} ({f['mimeType']})")
        
        # Test 3: Gmail
        print("\n📧 Testing Gmail API...")
        emails = mcp.search_gmail("is:unread", max_results=5)
        print(f"PASS: Found {len(emails)} unread emails")
        
        print("\nPASS: All tests passed!")
        
    except GoogleWorkspaceError as e:
        print(f"\n❌ Error: {e}")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")