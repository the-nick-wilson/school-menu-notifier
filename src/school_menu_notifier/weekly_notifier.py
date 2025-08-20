"""
Weekly School Menu Notifier

Fetches the upcoming week's lunch menus and sends a weekly overview email.
"""

import os
import logging
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from .common.config import Config
from .common.email_sender import EmailSender

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WeeklySchoolMenuNotifier:
    """Handles fetching and emailing weekly school menu notifications."""

    def __init__(self):
        """Initialize the weekly menu notifier with configuration."""
        logger.info("Starting Weekly School Menu Notifier...")
        
        # Load configuration
        self.config = Config()
        
        # Initialize email sender
        self.email_sender = EmailSender(
            smtp_server=self.config.smtp_server,
            smtp_port=self.config.smtp_port,
            sender_email=self.config.sender_email,
            sender_password=self.config.sender_password
        )
        
        logger.info("Configuration loaded successfully")

    def get_week_dates(self) -> List[Tuple[datetime, str]]:
        """Get the dates for the upcoming week based on test_run setting."""
        today = datetime.now()
        
        if self.config.test_run:
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
                    # If it's already Friday or later, show next Monday
                    # Find next Monday (Monday is weekday 0)
                    days_until_monday = (7 - current_weekday) % 7
                    if days_until_monday == 0:  # Already Monday
                        days_until_monday = 7
                    start_date = today + timedelta(days=days_until_monday)
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
        """Fetch main menu data from the SchoolCafe API."""
        params = {
            'SchoolId': self.config.school_id,
            'ServingDate': serving_date,
            'ServingLine': self.config.serving_line,
            'MealType': self.config.meal_type,
            'Grade': self.config.grade,
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
            response = requests.get(self.config.api_base_url, params=params, headers=headers)
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
        except Exception as e:
            logger.error(f"Unexpected error fetching menu data: {e}")
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
            'SchoolId': self.config.school_id,
            'ServingDate': serving_date,
            'ServingLine': 'Prek Lunch',
            'MealType': self.config.meal_type,
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
            response = requests.get(self.config.api_base_url, params=params, headers=headers)
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
        except Exception as e:
            logger.error(f"Unexpected error fetching PreK menu data: {e}")
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
        # Determine header text based on test run
        if self.config.test_run:
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
        if self.config.test_run:
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
                            email_content += f'<div class="entree-name">{entree_name} [Pre-K]</div>\n'
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
        """Send the weekly menu email."""
        return self.email_sender.send_email(
            subject=subject,
            html_content=html_content,
            recipients=self.config.recipient_emails,
            test_run=self.config.test_run
        )

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
            if self.config.test_run:
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
    """Main entry point for the weekly notifier."""
    try:
        notifier = WeeklySchoolMenuNotifier()
        success = notifier.run()
        
        if success:
            logger.info("Weekly menu notification completed successfully")
        else:
            logger.error("Weekly menu notification failed")
            exit(1)
            
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        exit(1)


if __name__ == "__main__":
    main()
