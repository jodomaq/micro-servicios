import pickle
import os
import base64
from typing import Optional
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Gmail API scope for sending emails
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

class GmailOAuth:
    def __init__(self, credentials_path: str = 'credentials.json', token_path: str = 'token.pickle'):
        """
        Initialize Gmail OAuth handler
        
        Args:
            credentials_path: Path to the OAuth 2.0 credentials file from Google Cloud Console
            token_path: Path to store the authentication token
        """
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Gmail API using OAuth 2.0"""
        creds = None
        
        # Load existing token if available
        if os.path.exists(self.token_path):
            try:
                with open(self.token_path, 'rb') as token:
                    creds = pickle.load(token)
                logger.info("Loaded existing authentication token")
            except Exception as e:
                logger.warning(f"Could not load token: {e}")
        
        # If there are no valid credentials available, request authorization
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    logger.info("Refreshed authentication token")
                except Exception as e:
                    logger.error(f"Could not refresh token: {e}")
                    creds = None
            
            if not creds:
                if not os.path.exists(self.credentials_path):
                    raise FileNotFoundError(
                        f"Credentials file not found at {self.credentials_path}. "
                        "Please download it from Google Cloud Console."
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)
                logger.info("Completed OAuth 2.0 flow")
            
            # Save the credentials for the next run
            try:
                with open(self.token_path, 'wb') as token:
                    pickle.dump(creds, token)
                logger.info("Saved authentication token")
            except Exception as e:
                logger.warning(f"Could not save token: {e}")
        
        # Build the Gmail service
        try:
            self.service = build('gmail', 'v1', credentials=creds)
            logger.info("Gmail service initialized successfully")
        except Exception as e:
            logger.error(f"Could not build Gmail service: {e}")
            raise
    
    def send_email(self, to_email: str, subject: str, body: str, from_email: Optional[str] = None) -> dict:
        """
        Send an email using Gmail API
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body (plain text)
            from_email: Sender email (optional, uses authenticated user's email if not provided)
            
        Returns:
            dict: Gmail API response
        """
        try:
            # Create message
            message = MIMEMultipart()
            message['to'] = to_email
            if from_email:
                message['from'] = from_email
            message['subject'] = subject
            
            # Attach body
            message.attach(MIMEText(body, 'plain'))
            
            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            # Send email
            send_result = self.service.users().messages().send(
                userId="me", 
                body={'raw': raw_message}
            ).execute()
            
            logger.info(f"Email sent successfully. Message ID: {send_result.get('id')}")
            return send_result
            
        except HttpError as error:
            logger.error(f"Gmail API error: {error}")
            raise Exception(f"Gmail API error: {error}")
        except Exception as error:
            logger.error(f"Error sending email: {error}")
            raise Exception(f"Error sending email: {error}")
    
    def send_html_email(self, to_email: str, subject: str, html_body: str, 
                       text_body: Optional[str] = None, from_email: Optional[str] = None) -> dict:
        """
        Send an HTML email using Gmail API
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_body: Email body in HTML format
            text_body: Email body in plain text format (optional fallback)
            from_email: Sender email (optional, uses authenticated user's email if not provided)
            
        Returns:
            dict: Gmail API response
        """
        try:
            # Create message
            message = MIMEMultipart('alternative')
            message['to'] = to_email
            if from_email:
                message['from'] = from_email
            message['subject'] = subject
            
            # Attach text version if provided
            if text_body:
                text_part = MIMEText(text_body, 'plain')
                message.attach(text_part)
            
            # Attach HTML version
            html_part = MIMEText(html_body, 'html')
            message.attach(html_part)
            
            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            # Send email
            send_result = self.service.users().messages().send(
                userId="me", 
                body={'raw': raw_message}
            ).execute()
            
            logger.info(f"HTML email sent successfully. Message ID: {send_result.get('id')}")
            return send_result
            
        except HttpError as error:
            logger.error(f"Gmail API error: {error}")
            raise Exception(f"Gmail API error: {error}")
        except Exception as error:
            logger.error(f"Error sending HTML email: {error}")
            raise Exception(f"Error sending HTML email: {error}")
    
    def get_user_profile(self) -> dict:
        """
        Get the authenticated user's Gmail profile
        
        Returns:
            dict: User profile information
        """
        try:
            profile = self.service.users().getProfile(userId="me").execute()
            logger.info(f"Retrieved profile for: {profile.get('emailAddress')}")
            return profile
        except HttpError as error:
            logger.error(f"Error getting user profile: {error}")
            raise Exception(f"Error getting user profile: {error}")