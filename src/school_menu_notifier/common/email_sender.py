"""
Email sending functionality for the School Menu Notifier.
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List

logger = logging.getLogger(__name__)


class EmailSender:
    """Handles email sending functionality."""
    
    def __init__(self, smtp_server: str, smtp_port: int, sender_email: str, sender_password: str):
        """Initialize email sender with SMTP configuration."""
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.sender_password = sender_password
    
    def send_email(self, subject: str, html_content: str, recipients: List[str], test_run: bool = False) -> bool:
        """
        Send an HTML email to the specified recipients.
        
        Args:
            subject: Email subject line
            html_content: HTML content of the email
            recipients: List of recipient email addresses
            test_run: If True, only send to the first recipient
            
        Returns:
            True if all emails were sent successfully, False otherwise
        """
        if not recipients:
            logger.error("No recipients specified")
            return False
        
        # Filter recipients based on test mode
        if test_run:
            filtered_recipients = [recipients[0]] if recipients else []
            logger.info("TEST_RUN mode - sending only to primary recipient")
        else:
            filtered_recipients = recipients
            logger.info("Normal mode - sending to all recipients")
        
        try:
            logger.info(f"Connecting to SMTP server: {self.smtp_server}:{self.smtp_port}")
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                logger.info("SMTP connection established, starting TLS...")
                server.starttls()
                logger.info("TLS started, attempting login...")
                server.login(self.sender_email, self.sender_password)
                logger.info("Login successful, sending messages...")
                
                success_count = 0
                for recipient_email in filtered_recipients:
                    try:
                        # Create message
                        msg = MIMEMultipart('alternative')
                        msg['From'] = self.sender_email
                        msg['To'] = recipient_email
                        msg['Subject'] = subject
                        
                        # Add HTML content
                        html_part = MIMEText(html_content, 'html')
                        msg.attach(html_part)
                        
                        # Send message
                        server.send_message(msg)
                        logger.info(f"Email sent successfully to {recipient_email}")
                        success_count += 1
                        
                    except Exception as e:
                        logger.error(f"Failed to send email to {recipient_email}: {e}")
                
                if success_count == len(filtered_recipients):
                    logger.info(f"All emails sent successfully to {success_count} recipient(s)")
                    return True
                elif success_count > 0:
                    logger.warning(f"Partially successful: {success_count}/{len(filtered_recipients)} emails sent")
                    return True
                else:
                    logger.error("Failed to send emails to any recipients")
                    return False
                    
        except Exception as e:
            logger.error(f"SMTP connection error: {e}")
            return False
