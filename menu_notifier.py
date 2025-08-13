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
        self.school_id = os.getenv('SCHOOL_ID', '2f37947e-6d30-4bb3-a306-7f69a3b3ed62')
        self.grade = os.getenv('GRADE', '01')
        self.serving_line = os.getenv('SERVING_LINE', 'Main Line')
        self.meal_type = os.getenv('MEAL_TYPE', 'Lunch')
        
        # Email configuration
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.sender_email = os.getenv('SENDER_EMAIL')
        self.sender_password = os.getenv('SENDER_PASSWORD')
        self.recipient_email = os.getenv('RECIPIENT_EMAIL')
        
        # API configuration
        self.api_base_url = 'https://webapis.schoolcafe.com/api/CalendarView/GetDailyMenuitemsByGrade'
        
        if not all([self.sender_email, self.sender_password, self.recipient_email]):
            raise ValueError("Email configuration incomplete. Please set SENDER_EMAIL, SENDER_PASSWORD, and RECIPIENT_EMAIL environment variables.")

    def get_tomorrow_date(self) -> str:
        """Get tomorrow's date in MM/DD/YYYY format."""
        tomorrow = datetime.now() + timedelta(days=1)
        return tomorrow.strftime('%m/%d/%Y')

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
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching menu data: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response: {e}")
            return None

    def format_menu_email(self, menu_data: Dict, serving_date: str) -> str:
        """Format the menu data into a readable email."""
        # Convert date format for display
        try:
            date_obj = datetime.strptime(serving_date, '%m/%d/%Y')
            display_date = date_obj.strftime('%A, %B %d, %Y')
        except ValueError:
            display_date = serving_date
        
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
        .footer {{ margin-top: 30px; text-align: center; color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🍽️ Tomorrow's School Lunch Menu</h1>
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
                        email_content += f'<div class="item-name">{item["MenuItemDescription"]}</div>\n'
                        
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
        <p>This email was automatically generated by your School Menu Notifier.</p>
        <p>Data provided by SchoolCafe</p>
    </div>
</body>
</html>
"""
        
        return email_content

    def send_email(self, subject: str, html_content: str) -> bool:
        """Send the formatted email."""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.sender_email
            msg['To'] = self.recipient_email
            
            # Attach HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {self.recipient_email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False

    def run(self) -> bool:
        """Main execution method."""
        try:
            # Get tomorrow's date
            tomorrow_date = self.get_tomorrow_date()
            logger.info(f"Processing menu for tomorrow: {tomorrow_date}")
            
            # Fetch menu data
            menu_data = self.fetch_menu_data(tomorrow_date)
            if not menu_data:
                logger.error("Failed to fetch menu data")
                return False
            
            # Check if we have any menu items
            total_items = sum(len(items) if isinstance(items, list) else 0 
                            for items in menu_data.values())
            
            if total_items == 0:
                logger.warning("No menu items found for tomorrow")
                # Still send an email to notify about no menu
                subject = f"School Menu - {tomorrow_date} (No Menu Available)"
                content = f"""
                <html>
                <body>
                    <h2>No School Menu Available</h2>
                    <p>No lunch menu items were found for {tomorrow_date}.</p>
                    <p>This could mean:</p>
                    <ul>
                        <li>It's a school holiday</li>
                        <li>Menu hasn't been posted yet</li>
                        <li>There's a technical issue</li>
                    </ul>
                </body>
                </html>
                """
            else:
                # Format and send menu email
                subject = f"Tomorrow's School Lunch Menu - {tomorrow_date}"
                content = self.format_menu_email(menu_data, tomorrow_date)
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
        notifier = SchoolMenuNotifier()
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