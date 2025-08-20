"""
Configuration management for the School Menu Notifier.
"""

import os
import logging
from typing import List

logger = logging.getLogger(__name__)


class Config:
    """Handles configuration loading and validation for the School Menu Notifier."""
    
    def __init__(self):
        """Initialize configuration from environment variables."""
        self.load_config()
        self.validate_config()
        self.log_config()
    
    def load_config(self):
        """Load configuration from environment variables with defaults."""
        # School configuration
        self.school_id = os.getenv('SCHOOL_ID', '').strip()
        if not self.school_id:
            self.school_id = '2f37947e-6d30-4bb3-a306-7f69a3b3ed62'
        
        self.grade = os.getenv('GRADE', '').strip()
        if not self.grade:
            self.grade = '01'
        
        self.serving_line = os.getenv('SERVING_LINE', '').strip()
        if not self.serving_line:
            self.serving_line = 'Main Line'
        
        self.meal_type = os.getenv('MEAL_TYPE', '').strip()
        if not self.meal_type:
            self.meal_type = 'Lunch'
        
        # Email configuration
        self.sender_email = os.getenv('SENDER_EMAIL', '').strip()
        self.sender_password = os.getenv('SENDER_PASSWORD', '').strip()
        
        # SMTP configuration
        self.smtp_server = os.getenv('SMTP_SERVER', '').strip()
        if not self.smtp_server:
            self.smtp_server = 'smtp.gmail.com'
        
        smtp_port_str = os.getenv('SMTP_PORT', '').strip()
        if smtp_port_str:
            try:
                self.smtp_port = int(smtp_port_str)
            except (ValueError, TypeError):
                logger.warning(f"Invalid SMTP_PORT '{smtp_port_str}', using default 587")
                self.smtp_port = 587
        else:
            logger.info("SMTP_PORT not set, using default 587")
            self.smtp_port = 587
        
        # Recipients
        recipient_email = os.getenv('RECIPIENT_EMAIL', '').strip()
        additional_recipients = os.getenv('ADDITIONAL_RECIPIENTS', '').strip()
        
        self.recipient_emails = []
        if recipient_email:
            self.recipient_emails.append(recipient_email)
        if additional_recipients:
            # Split by comma and clean up whitespace
            additional_list = [email.strip() for email in additional_recipients.split(',') if email.strip()]
            self.recipient_emails.extend(additional_list)
        
        # Remove duplicates while preserving order
        seen = set()
        self.recipient_emails = [email for email in self.recipient_emails if not (email in seen or seen.add(email))]
        
        # Test mode
        self.test_run = os.getenv('TEST_RUN', 'false').lower() == 'true'
        
        # API configuration
        self.api_base_url = 'https://webapis.schoolcafe.com/api/CalendarView/GetDailyMenuitemsByGrade'
    
    def validate_config(self):
        """Validate required configuration."""
        missing_vars = []
        
        if not self.sender_email:
            missing_vars.append('SENDER_EMAIL')
        if not self.sender_password:
            missing_vars.append('SENDER_PASSWORD')
        if not self.recipient_emails:
            missing_vars.append('RECIPIENT_EMAIL (or ADDITIONAL_RECIPIENTS)')
        
        if missing_vars:
            raise ValueError(f"Email configuration incomplete. Missing required environment variables: {', '.join(missing_vars)}")
    
    def log_config(self):
        """Log configuration (without sensitive data)."""
        logger.info("Environment variables:")
        logger.info(f"  SCHOOL_ID: {self.school_id or 'NOT_SET'}")
        logger.info(f"  GRADE: {self.grade or 'NOT_SET'}")
        logger.info(f"  SERVING_LINE: {self.serving_line or 'NOT_SET'}")
        logger.info(f"  MEAL_TYPE: {self.meal_type or 'NOT_SET'}")
        logger.info(f"  SMTP_SERVER: {self.smtp_server or 'NOT_SET'}")
        logger.info(f"  SMTP_PORT: {self.smtp_port or 'NOT_SET'}")
        logger.info(f"  SENDER_EMAIL: {'***' if self.sender_email else 'NOT_SET'}")
        logger.info(f"  RECIPIENT_EMAIL: {'***' if self.recipient_emails else 'NOT_SET'}")
        if self.test_run:
            logger.info(f"  TEST_RUN: {self.test_run}")
        
        logger.info(f"Configuration loaded - School: {self.school_id}, Grade: {self.grade}, SMTP: {self.smtp_server}:{self.smtp_port}, TEST_RUN: {self.test_run}")
        logger.info(f"Recipients: {len(self.recipient_emails)} email(s) configured")
