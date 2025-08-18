#!/usr/bin/env python3
"""
Weekly School Menu Notifier

This script fetches the upcoming week's lunch menus from SchoolCafe API and sends
a formatted weekly overview email.
"""

import os
import json
import smtplib
import requests
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WeeklySchoolMenuNotifier:
    def __init__(self):
        """Initialize the notifier with configuration from environment variables."""
        # Log all environment variables for debugging (without sensitive data)
        logger.info("Environment variables:")
        logger.info(f"  SCHOOL_ID: {os.getenv('SCHOOL_ID', 'NOT_SET')}")
        logger.info(f"  GRADE: {os.getenv('GRADE', 'NOT_SET')}")
        logger.info(f"  SERVING_LINE: {os.getenv('SERVING_LINE', 'NOT_SET')}")
        logger.info(f"  MEAL_TYPE: {os.getenv('MEAL_TYPE', 'NOT_SET')}")
        logger.info(f"  SMTP_SERVER: {os.getenv('SMTP_SERVER', 'NOT_SET')}")
        logger.info(f"  SMTP_PORT: {os.getenv('SMTP_PORT', 'NOT_SET')}")
        logger.info(f"  SENDER_EMAIL: {os.getenv('SENDER_EMAIL', 'NOT_SET')}")
        logger.info(f"  RECIPIENT_EMAIL: {os.getenv('RECIPIENT_EMAIL', 'NOT_SET')}")
        logger.info(f"  TEST_RUN: {os.getenv('TEST_RUN', 'NOT_SET')}")
        
        # Handle school configuration with fallbacks for empty strings
        school_id_env = os.getenv('SCHOOL_ID', '')
        self.school_id = school_id_env if school_id_env else '2f37947e-6d30-4bb3-a306-7f69a3b3ed62'
        
        grade_env = os.getenv('GRADE', '')
        self.grade = grade_env if grade_env else '01'
        
        serving_line_env = os.getenv('SERVING_LINE', '')
        self.serving_line = serving_line_env if serving_line_env else 'Main Line'
        
        meal_type_env = os.getenv('MEAL_TYPE', '')
        self.meal_type = meal_type_env if meal_type_env else 'Lunch'
        
        # Email configuration with fallbacks for empty strings
        smtp_server_env = os.getenv('SMTP_SERVER', '')
        self.smtp_server = smtp_server_env if smtp_server_env else 'smtp.gmail.com'
        
        # Handle SMTP_PORT with better error handling
        smtp_port_str = os.getenv('SMTP_PORT', '')
        if smtp_port_str:
            try:
                self.smtp_port = int(smtp_port_str)
            except (ValueError, TypeError):
                logger.warning(f"Invalid SMTP_PORT '{smtp_port_str}', using default 587")
                self.smtp_port = 587
        else:
            logger.info("SMTP_PORT not set, using default 587")
            self.smtp_port = 587
        
        self.sender_email = os.getenv('SENDER_EMAIL')
        self.sender_password = os.getenv('SENDER_PASSWORD')
        
        # Handle multiple recipients
        recipient_email = os.getenv('RECIPIENT_EMAIL', '')
        additional_recipients = os.getenv('ADDITIONAL_RECIPIENTS', '')
        
        # Combine recipients into a list
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
        
        # API configuration
        self.api_base_url = 'https://webapis.schoolcafe.com/api/CalendarView/GetDailyMenuitemsByGrade'
        
        # Validate required email configuration
        missing_vars = []
        if not self.sender_email:
            missing_vars.append('SENDER_EMAIL')
        if not self.sender_password:
            missing_vars.append('SENDER_PASSWORD')
        if not self.recipient_emails:
            missing_vars.append('RECIPIENT_EMAIL (or ADDITIONAL_RECIPIENTS)')
        
        if missing_vars:
            raise ValueError(f"Email configuration incomplete. Missing required environment variables: {', '.join(missing_vars)}")
        
        # Log configuration (without sensitive data)
        test_run = os.getenv('TEST_RUN', 'false').lower() == 'true'
        logger.info(f"Configuration loaded - School: {self.school_id}, Grade: {self.grade}, SMTP: {self.smtp_server}:{self.smtp_port}, TEST_RUN: {test_run}")
        logger.info(f"Recipients: {len(self.recipient_emails)} email(s) configured")

    def get_week_dates(self) -> List[Tuple[datetime, str]]:
        """Get the dates for the upcoming week based on test_run setting."""
        test_run = os.getenv('TEST_RUN', 'false').lower() == 'true'
        today = datetime.now()
        
        if test_run:
            # For test runs, show the rest of the current week
            logger.info("TEST_RUN is true - showing rest of current week")
            current_weekday = today.weekday()  # Monday=0, Sunday=6
            
            if current_weekday == 6:  # Sunday
                # If it's Sunday, show the entire upcoming week
                start_date = today + timedelta(days=1)  # Monday
                end_date = start_date + timedelta(days=4)  # Friday
                logger.info("Sunday detected - showing entire upcoming week")
            else:
                # Show from tomorrow to Friday of current week
                start_date = today + timedelta(days=1)
                # Calculate days until Friday (Friday is weekday 4)
                days_until_friday = 4 - current_weekday
                if days_until_friday > 0:
                    end_date = today + timedelta(days=days_until_friday)
                else:
                    # If it's already Friday or later, just show tomorrow
                    end_date = start_date
                logger.info(f"Showing rest of week from {start_date.strftime('%A')} to {end_date.strftime('%A')}")
        else:
            # For normal Sunday runs, show the upcoming week
            start_date = today + timedelta(days=1)  # Monday
            end_date = start_date + timedelta(days=4)  # Friday
            logger.info("Normal operation - showing upcoming week starting Monday")
        
        # Generate dates from start to end (inclusive)
        week_dates = []
        current_date = start_date
        while current_date <= end_date:
            if current_date.weekday() < 5:  # Only weekdays
                week_dates.append((current_date, current_date.strftime('%m/%d/%Y')))
            current_date += timedelta(days=1)
        
        logger.info(f"Generated {len(week_dates)} weekdays: {[date.strftime('%A %m/%d') for date, _ in week_dates]}")
        return week_dates

    def fetch_main_menu_data(self, serving_date: str) -> Optional[Dict]:
        """Fetch menu data from the SchoolCafe API."""
        params = {
            'SchoolId': self.school_id,
            'ServingDate': serving_date,
            'ServingLine': self.serving_line,
            'MealType': self.meal_type,
            'Grade': self.grade,
            'PersonId': 'null'
        }
        
        headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en-US,en;q=0.9,es;q=0.8',
            'origin': 'https://www.schoolcafe.com',
            'referer': 'https://www.schoolcafe.com/'
        }
        
        try:
            logger.info(f"Fetching menu data for {serving_date}")
            response = requests.get(self.api_base_url, params=params, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Successfully fetched main menu data with {len(data)} categories")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching menu data: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response: {e}")
            return None

    def extract_entrees(self, menu_data: Dict) -> List[Dict]:
        """Extract just the entrees from menu data."""
        entrees = []
        if 'ENTREES' in menu_data and isinstance(menu_data['ENTREES'], list):
            for entree in menu_data['ENTREES']:
                if isinstance(entree, dict) and 'MenuItemDescription' in entree:
                    entrees.append(entree)
        return entrees

    def fetch_prek_menu_data(self, serving_date: str) -> Optional[Dict]:
        """Fetch PreK menu data from the SchoolCafe API."""
        params = {
            'SchoolId': self.school_id,
            'ServingDate': serving_date,
            'ServingLine': 'Prek Lunch',
            'MealType': self.meal_type,
            'Grade': 'PK',
            'PersonId': 'null'
        }
        
        headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en-US,en;q=0.9,es;q=0.8',
            'origin': 'https://www.schoolcafe.com',
            'referer': 'https://www.schoolcafe.com/'
        }
        
        try:
            logger.info(f"Fetching PreK menu data for {serving_date}")
            response = requests.get(self.api_base_url, params=params, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Successfully fetched PreK menu data with {len(data)} categories")
            
            # Check if we got an empty response (common for weekends/holidays)
            if not data or len(data) == 0:
                logger.info(f"Empty PreK response received for {serving_date} - likely weekend or holiday")
                return {}  # Return empty dict instead of None
            
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching PreK menu data: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing PreK JSON response: {e}")
            return None

    def find_prek_entree(self, main_menu_data: Dict, prek_menu_data: Dict) -> Optional[str]:
        """Find which main line entree is also served to preschoolers."""
        if not main_menu_data or not prek_menu_data:
            return None
        
        # Extract entrees from both menus
        main_entrees = []
        if 'ENTREES' in main_menu_data and isinstance(main_menu_data['ENTREES'], list):
            main_entrees = [item.get('MenuItemDescription', '') for item in main_menu_data['ENTREES'] if isinstance(item, dict)]
        
        prek_entrees = []
        if 'ENTREES' in prek_menu_data and isinstance(prek_menu_data['ENTREES'], list):
            prek_entrees = [item.get('MenuItemDescription', '') for item in prek_menu_data['ENTREES'] if isinstance(item, dict)]
        
        # Find matching entrees
        matching_entrees = []
        for main_entree in main_entrees:
            if main_entree in prek_entrees:
                matching_entrees.append(main_entree)
        
        if matching_entrees:
            logger.info(f"Found {len(matching_entrees)} matching entrees for PreK: {matching_entrees}")
            return matching_entrees[0]  # Return the first match
        
        logger.info("No matching entrees found between main line and PreK")
        return None

    def format_weekly_email(self, week_menus: List[Tuple[datetime, str, Optional[Dict]]], prek_entrees: Dict[str, str]) -> str:
        """Format the weekly menu data into a readable email."""
        test_run = os.getenv('TEST_RUN', 'false').lower() == 'true'
        
        # Determine header text based on test run
        if test_run:
            header_text = "This Week's School Lunch Menu"
            subtitle = "Rest of Current Week"
        else:
            header_text = "Next Week's School Lunch Menu"
            subtitle = "Upcoming Week"
        
        email_content = f"""
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; border-radius: 5px; }}
        .subtitle {{ color: #E8F5E8; font-size: 16px; margin-top: 10px; }}
        .day-section {{ margin: 25px 0; border: 2px solid #4CAF50; border-radius: 8px; overflow: hidden; }}
        .day-header {{ background-color: #4CAF50; color: white; padding: 15px; font-size: 18px; font-weight: bold; }}
        .day-content {{ padding: 20px; }}
        .no-menu {{ color: #666; font-style: italic; text-align: center; padding: 20px; }}
        .entree-item {{ margin: 15px 0; padding: 15px; background-color: #f9f9f9; border-left: 4px solid #4CAF50; }}
        .entree-name {{ font-weight: bold; color: #333; font-size: 16px; }}
        .entree-details {{ color: #666; font-size: 14px; margin-top: 8px; }}
        .allergens {{ color: #d32f2f; font-size: 12px; margin-top: 8px; font-weight: bold; }}
        .prek-note {{ color: #666; font-size: 12px; font-style: italic; margin-top: 20px; text-align: center; }}
        .footer {{ margin-top: 30px; text-align: center; color: #666; font-size: 12px; }}
        .test-banner {{ background-color: #FF9800; color: white; padding: 10px; text-align: center; margin-bottom: 20px; border-radius: 5px; }}
    </style>
</head>
<body>
"""
        
        # Add test run banner if applicable
        if test_run:
            email_content += f"""
    <div class="test-banner">
        🧪 <strong>TEST RUN</strong> - This is a test email showing the rest of the current week
    </div>
"""
        
        email_content += f"""
    <div class="header">
        <h1>🍽️ {header_text}</h1>
        <div class="subtitle">{subtitle}</div>
    </div>
"""
        
        # Process each day
        for date_obj, date_str, menu_data in week_menus:
            day_name = date_obj.strftime('%A')
            display_date = date_obj.strftime('%B %d, %Y')
            
            email_content += f'<div class="day-section">\n'
            email_content += f'<div class="day-header">{day_name} - {display_date}</div>\n'
            email_content += '<div class="day-content">\n'
            
            if menu_data:
                entrees = self.extract_entrees(menu_data)
                if entrees:
                    for entree in entrees:
                        email_content += '<div class="entree-item">\n'
                        
                        # Entree name with PreK indicator if applicable
                        entree_name = entree["MenuItemDescription"]
                        date_key = date_obj.strftime('%m/%d/%Y')
                        if date_key in prek_entrees and entree_name == prek_entrees[date_key]:
                            email_content += f'<div class="entree-name">{entree_name} *</div>\n'
                        else:
                            email_content += f'<div class="entree-name">{entree_name}</div>\n'
                        
                        # Add serving size if available
                        if entree.get('ServingSizeByGrade'):
                            email_content += f'<div class="entree-details">Serving: {entree["ServingSizeByGrade"]}</div>\n'
                        
                        # Add calories if available
                        if entree.get('Calories'):
                            email_content += f'<div class="entree-details">Calories: {entree["Calories"]}</div>\n'
                        
                        # Add allergens if available
                        if entree.get('Allergens'):
                            email_content += f'<div class="entree-details">⚠️ Allergens: {entree["Allergens"]}</div>\n'
                        
                        email_content += '</div>\n'
                else:
                    email_content += '<div class="no-menu">No entrees found for this day</div>\n'
            else:
                email_content += '<div class="no-menu">No menu data available for this day</div>\n'
            
            email_content += '</div>\n</div>\n'
        
        # Add PreK note if applicable
        if prek_entrees:
            email_content += """
    <div class="prek-note">
        * Pre-K item
    </div>
"""
        
        email_content += """
    <div class="footer">
        <p>This email was automatically generated by the school-menu-notifier tool built by Nick Wilson.</p>
        <p>Data provided by SchoolCafe</p>
    </div>
</body>
</html>
"""
        
        return email_content

    def send_email(self, subject: str, html_content: str) -> bool:
        """Send the formatted email to all recipients."""
        try:
            # Validate SMTP configuration
            if not self.smtp_server:
                logger.error("SMTP_SERVER is not configured")
                return False
            
            logger.info(f"Connecting to SMTP server: {self.smtp_server}:{self.smtp_port}")
            
            # Send email to each recipient
            success_count = 0
            total_recipients = len(self.recipient_emails)
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                logger.info("SMTP connection established, starting TLS...")
                server.starttls()
                logger.info("TLS started, attempting login...")
                server.login(self.sender_email, self.sender_password)
                logger.info("Login successful, sending messages...")
                
                for recipient_email in self.recipient_emails:
                    try:
                        # Create message for this recipient
                        msg = MIMEMultipart('alternative')
                        msg['Subject'] = subject
                        msg['From'] = self.sender_email
                        msg['To'] = recipient_email
                        
                        # Attach HTML content
                        html_part = MIMEText(html_content, 'html')
                        msg.attach(html_part)
                        
                        # Send to this recipient
                        server.send_message(msg)
                        logger.info(f"Email sent successfully to {recipient_email}")
                        success_count += 1
                        
                    except Exception as e:
                        logger.error(f"Failed to send email to {recipient_email}: {e}")
                        # Continue with other recipients
            
            if success_count == total_recipients:
                logger.info(f"All emails sent successfully to {total_recipients} recipient(s)")
                return True
            elif success_count > 0:
                logger.warning(f"Partial success: {success_count}/{total_recipients} emails sent")
                return True  # Still consider it a success if some emails were sent
            else:
                logger.error("Failed to send emails to any recipients")
                return False
            
        except Exception as e:
            logger.error(f"Error in email sending process: {e}")
            return False

    def run(self) -> bool:
        """Main execution method."""
        try:
            logger.info("Starting Weekly School Menu Notifier...")
            
            # Get week dates
            week_dates = self.get_week_dates()
            if not week_dates:
                logger.error("No week dates generated")
                return False
            
            # Fetch menu data for each day
            week_menus = []
            total_entrees = 0
            prek_entrees = {}  # Dictionary to store PreK entree for each date
            
            for date_obj, date_str in week_dates:
                logger.info(f"Processing {date_obj.strftime('%A %m/%d')}")
                menu_data = self.fetch_main_menu_data(date_str)
                
                # Fetch PreK data to find matching entree
                prek_menu_data = self.fetch_prek_menu_data(date_str)
                if prek_menu_data is not None:
                    prek_entree = self.find_prek_entree(menu_data, prek_menu_data)
                    if prek_entree:
                        prek_entrees[date_str] = prek_entree
                        logger.info(f"PreK entree for {date_obj.strftime('%A')}: {prek_entree}")
                    else:
                        logger.info(f"No matching PreK entree found for {date_obj.strftime('%A')}")
                else:
                    logger.warning(f"Could not fetch PreK menu data for {date_obj.strftime('%A')}")
                
                if menu_data:
                    entrees = self.extract_entrees(menu_data)
                    total_entrees += len(entrees)
                    logger.info(f"Found {len(entrees)} entrees for {date_obj.strftime('%A')}")
                else:
                    logger.warning(f"No menu data found for {date_obj.strftime('%A')}")
                
                week_menus.append((date_obj, date_str, menu_data))
            
            # Format and send email
            test_run = os.getenv('TEST_RUN', 'false').lower() == 'true'
            if test_run:
                subject = f"Weekly School Lunch Menu - Rest of Current Week"
            else:
                subject = f"Weekly School Lunch Menu - Next Week"
            
            content = self.format_weekly_email(week_menus, prek_entrees)
            logger.info(f"Formatted weekly menu with {total_entrees} total entrees across {len(week_dates)} days")
            
            # Send email
            success = self.send_email(subject, content)
            return success
            
        except Exception as e:
            logger.error(f"Unexpected error in main execution: {e}")
            return False


def main():
    """Main entry point."""
    try:
        logger.info("Starting Weekly School Menu Notifier...")
        
        # Test configuration loading first
        try:
            notifier = WeeklySchoolMenuNotifier()
            logger.info("Configuration loaded successfully")
        except Exception as config_error:
            logger.error(f"Configuration error: {config_error}")
            exit(1)
        
        # Run the notifier
        success = notifier.run()
        
        if success:
            logger.info("Weekly menu notification completed successfully")
            exit(0)
        else:
            logger.error("Weekly menu notification failed")
            exit(1)
            
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        exit(1)


if __name__ == "__main__":
    main() 