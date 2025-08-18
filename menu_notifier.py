#!/usr/bin/env python3
"""
School Menu Notifier

This script fetches the next day's lunch menu from SchoolCafe API and sends
a formatted email with the menu items.
"""

import os
import json
import smtplib
import requests
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SchoolMenuNotifier:
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

    def get_target_date(self) -> str:
        """Get the target date based on test_run setting."""
        test_run = os.getenv('TEST_RUN', 'false').lower() == 'true'
        
        if test_run:
            # For test runs, use today's date
            target_date = datetime.now()
            logger.info("TEST_RUN is true - using today's date")
        else:
            # For normal runs, use tomorrow's date
            target_date = datetime.now() + timedelta(days=1)
            logger.info("Using tomorrow's date (normal operation)")
        
        # Check if target date is a weekend
        target_weekday = target_date.weekday()
        if target_weekday >= 5:  # Saturday (5) or Sunday (6)
            logger.info(f"Target date {target_date.strftime('%A %m/%d')} is a weekend - expecting no menu")
        
        return target_date.strftime('%m/%d/%Y')

    def fetch_menu_data(self, serving_date: str) -> Optional[Dict]:
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
            logger.info(f"Successfully fetched menu data with {len(data)} categories")
            
            # Check if we got an empty response (common for weekends/holidays)
            if not data or len(data) == 0:
                logger.info(f"Empty response received for {serving_date} - likely weekend or holiday")
                return {}  # Return empty dict instead of None
            
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching menu data: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response: {e}")
            return None

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

    def format_menu_email(self, menu_data: Dict, serving_date: str, prek_entree: Optional[str] = None) -> str:
        """Format the menu data into a readable email."""
        # Convert date format for display
        try:
            date_obj = datetime.strptime(serving_date, '%m/%d/%Y')
            display_date = date_obj.strftime('%A, %B %d, %Y')
        except ValueError:
            display_date = serving_date
        
        # Determine if this is a test run
        test_run = os.getenv('TEST_RUN', 'false').lower() == 'true'
        header_text = "Today's School Lunch Menu" if test_run else "Tomorrow's School Lunch Menu"
        
        email_content = f"""
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; border-radius: 5px; }}
        .category {{ margin: 20px 0; }}
        .category-title {{ font-size: 18px; font-weight: bold; color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 5px; margin-bottom: 10px; }}
        .menu-item {{ margin: 10px 0; padding: 10px; background-color: #f9f9f9; border-left: 4px solid #4CAF50; }}
        .item-name {{ font-weight: bold; color: #333; }}
        .item-details {{ color: #666; font-size: 14px; margin-top: 5px; }}
        .allergens {{ color: #d32f2f; font-size: 12px; margin-top: 5px; }}
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
        🧪 <strong>TEST RUN</strong> - This is a test email using today's menu
    </div>
"""
        
        email_content += f"""
    <div class="header">
        <h1>🍽️ {header_text}</h1>
        <h2>{display_date}</h2>
    </div>
"""
        
        # Process each category
        for category, items in menu_data.items():
            if items and isinstance(items, list):
                email_content += f'<div class="category">\n'
                email_content += f'<div class="category-title">{category.title()}</div>\n'
                
                for item in items:
                    if isinstance(item, dict) and 'MenuItemDescription' in item:
                        email_content += '<div class="menu-item">\n'
                        
                        # Item name with PreK indicator if applicable
                        item_name = item["MenuItemDescription"]
                        if prek_entree and item_name == prek_entree:
                            email_content += f'<div class="item-name">{item_name} [Pre-K]</div>\n'
                        else:
                            email_content += f'<div class="item-name">{item_name}</div>\n'
                        
                        # Add serving size if available
                        if item.get('ServingSizeByGrade'):
                            email_content += f'<div class="item-details">Serving: {item["ServingSizeByGrade"]}</div>\n'
                        
                        # Add calories if available
                        if item.get('Calories'):
                            email_content += f'<div class="item-details">Calories: {item["Calories"]}</div>\n'
                        
                        # Add allergens if available
                        if item.get('Allergens'):
                            email_content += f'<div class="allergens">⚠️ Allergens: {item["Allergens"]}</div>\n'
                        
                        email_content += '</div>\n'
                
                email_content += '</div>\n'
        
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
            # Get target date (today for test runs, tomorrow for normal runs)
            target_date = self.get_target_date()
            test_run = os.getenv('TEST_RUN', 'false').lower() == 'true'
            
            if test_run:
                logger.info(f"Processing menu for today (TEST_RUN): {target_date}")
            else:
                logger.info(f"Processing menu for tomorrow: {target_date}")
            
            # Fetch main menu data
            menu_data = self.fetch_menu_data(target_date)
            if menu_data is None:
                logger.error("Failed to fetch menu data (API error)")
                return False
            
            # Fetch PreK menu data to find matching entree
            prek_menu_data = self.fetch_prek_menu_data(target_date)
            prek_entree = None
            if prek_menu_data is not None:
                prek_entree = self.find_prek_entree(menu_data, prek_menu_data)
                if prek_entree:
                    logger.info(f"PreK entree identified: {prek_entree}")
                else:
                    logger.info("No matching PreK entree found")
            else:
                logger.warning("Could not fetch PreK menu data - continuing without PreK indicator")
            
            # Check if we have any menu items
            total_items = sum(len(items) if isinstance(items, list) else 0 
                            for items in menu_data.values())
            
            if total_items == 0:
                logger.info(f"No menu items found for {target_date} - likely weekend or holiday")
                # Still send an email to notify about no menu
                date_description = "today" if test_run else "tomorrow"
                subject = f"School Menu - {target_date} (No Menu Available)"
                content = f"""
                <html>
                <body>
                    <h2>No School Menu Available</h2>
                    <p>No lunch menu items were found for {target_date} ({date_description}).</p>
                    <p>This could mean:</p>
                    <ul>
                        <li>It's a weekend (no school)</li>
                        <li>It's a school holiday</li>
                        <li>Menu hasn't been posted yet</li>
                        <li>There's a technical issue</li>
                    </ul>
                    <p><em>This is normal for weekends and holidays.</em></p>
                </body>
                </html>
                """
            else:
                # Format and send menu email
                date_description = "Today's" if test_run else "Tomorrow's"
                subject = f"{date_description} School Lunch Menu - {target_date}"
                content = self.format_menu_email(menu_data, target_date, prek_entree)
                logger.info(f"Formatted menu with {total_items} items")
            
            # Send email
            success = self.send_email(subject, content)
            return success
            
        except Exception as e:
            logger.error(f"Unexpected error in main execution: {e}")
            return False


def main():
    """Main entry point."""
    try:
        logger.info("Starting School Menu Notifier...")
        
        # Test configuration loading first
        try:
            notifier = SchoolMenuNotifier()
            logger.info("Configuration loaded successfully")
        except Exception as config_error:
            logger.error(f"Configuration error: {config_error}")
            exit(1)
        
        # Run the notifier
        success = notifier.run()
        
        if success:
            logger.info("Menu notification completed successfully")
            exit(0)
        else:
            logger.error("Menu notification failed")
            exit(1)
            
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        exit(1)


if __name__ == "__main__":
    main() 