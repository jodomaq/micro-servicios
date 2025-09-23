import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SMTPEmailSender:
    def __init__(self, smtp_server: str, port: int, username: str, password: str):
        """
        Initialize SMTP Email Sender
        
        Args:
            smtp_server: SMTP server address (e.g., smtp.ionos.mx)
            port: SMTP port (e.g., 465 for SSL/TLS)
            username: Email account username
            password: Email account password
        """
        self.smtp_server = smtp_server
        self.port = port
        self.username = username
        self.password = password
        
    def send_email(self, to_email: str, subject: str, body: str, from_email: Optional[str] = None) -> bool:
        """
        Send a plain text email using SMTP
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body (plain text)
            from_email: Sender email (optional, uses username if not provided)
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            # Create message
            message = MIMEText(body, 'plain')
            message['From'] = from_email or self.username
            message['To'] = to_email
            message['Subject'] = subject
            
            # Create SSL context
            context = ssl.create_default_context()
            
            # Connect to server and send email
            with smtplib.SMTP_SSL(self.smtp_server, self.port, context=context) as server:
                server.login(self.username, self.password)
                server.send_message(message)
                
            logger.info(f"Plain text email sent successfully to {to_email}")
            return True
            
        except Exception as error:
            logger.error(f"Error sending plain text email: {error}")
            raise Exception(f"Error sending email: {error}")
    
    def send_html_email(self, to_email: str, subject: str, html_body: str, 
                       text_body: Optional[str] = None, from_email: Optional[str] = None) -> bool:
        """
        Send an HTML email using SMTP
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_body: Email body in HTML format
            text_body: Email body in plain text format (optional fallback)
            from_email: Sender email (optional, uses username if not provided)
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            # Create message
            message = MIMEMultipart('alternative')
            message['From'] = from_email or self.username
            message['To'] = to_email
            message['Subject'] = subject
            
            # Attach text version if provided
            if text_body:
                text_part = MIMEText(text_body, 'plain')
                message.attach(text_part)
            
            # Attach HTML version
            html_part = MIMEText(html_body, 'html')
            message.attach(html_part)
            
            # Create SSL context
            context = ssl.create_default_context()
            
            # Connect to server and send email
            with smtplib.SMTP_SSL(self.smtp_server, self.port, context=context) as server:
                server.login(self.username, self.password)
                server.send_message(message)
                
            logger.info(f"HTML email sent successfully to {to_email}")
            return True
            
        except Exception as error:
            logger.error(f"Error sending HTML email: {error}")
            raise Exception(f"Error sending HTML email: {error}")