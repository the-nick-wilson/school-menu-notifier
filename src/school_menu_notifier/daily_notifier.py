"""
Daily School Menu Notifier

Fetches tomorrow's lunch menu and sends it via email.
"""

import os
import logging
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, Optional

from .common.config import Config
from .common.email_sender import EmailSender

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SchoolMenuNotifier:
    """Handles fetching and emailing daily school menu notifications."""

    def __init__(self):
        """Initialize the menu notifier with configuration."""
        logger.info("Starting School Menu Notifier...")
        
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

    def get_target_date(self) -> str:
        """Get the target date for menu fetching based on test mode."""
        if self.config.test_run:
            target_date = datetime.now()
            logger.info("TEST_RUN is true - using today's date")
        else:
            target_date = datetime.now() + timedelta(days=1)
            logger.info("Using tomorrow's date (normal operation)")
        
        # Check if target date is a weekend
        if target_date.weekday() >= 5:  # Saturday = 5, Sunday = 6
            logger.info(f"Target date {target_date.strftime('%A %m/%d')} is a weekend - expecting no menu")
        
        return target_date.strftime('%m/%d/%Y')

    def fetch_menu_data(self, serving_date: str) -> Optional[Dict]:
        """Fetch menu data from the SchoolCafe API."""
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
        except Exception as e:
            logger.error(f"Unexpected error fetching menu data: {e}")
            return None

    def fetch_prek_menu_data(self, serving_date: str) -> Optional[Dict]:
        """Fetch PreK menu data from the SchoolCafe API."""
        params = {
            'SchoolId': self.config.school_id,
            'ServingDate': serving_date,
            'ServingLine': 'Main Line',  # PreK data is now served from Main Line
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

    def format_menu_email(self, menu_data: Dict, serving_date: str, prek_entree: Optional[str] = None) -> str:
        """Format the menu data into a readable email."""
        # Convert date format for display
        try:
            date_obj = datetime.strptime(serving_date, '%m/%d/%Y')
            formatted_date = date_obj.strftime('%A, %B %d, %Y')
        except ValueError:
            formatted_date = serving_date
        
        # Determine if this is a test run
        test_run = self.config.test_run
        
        # Set subject and header based on test mode
        if test_run:
            subject = f"🧪 TEST: Today's School Lunch Menu - {formatted_date}"
            header_text = "Today's School Lunch Menu"
            subtitle = "Test Run"
        else:
            subject = f"🍽️ Tomorrow's School Lunch Menu - {formatted_date}"
            header_text = "Tomorrow's School Lunch Menu"
            subtitle = formatted_date
        
        # Start building the email content
        email_content = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{subject}</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f9f9f9;
                }}
                .container {{
                    background-color: white;
                    border-radius: 10px;
                    padding: 30px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                }}
                .header {{
                    text-align: center;
                    border-bottom: 3px solid #4CAF50;
                    padding-bottom: 20px;
                    margin-bottom: 30px;
                }}
                .header h1 {{
                    color: #2E7D32;
                    margin: 0;
                    font-size: 24px;
                }}
                .header p {{
                    color: #666;
                    margin: 5px 0 0 0;
                    font-size: 16px;
                }}
                .category {{
                    margin: 25px 0;
                    border-left: 4px solid #4CAF50;
                    padding-left: 15px;
                }}
                .category h2 {{
                    color: #2E7D32;
                    margin: 0 0 10px 0;
                    font-size: 18px;
                }}
                .menu-item {{
                    background-color: #f8f9fa;
                    border-radius: 8px;
                    padding: 15px;
                    margin: 10px 0;
                    border-left: 3px solid #81C784;
                }}
                .item-name {{
                    font-weight: bold;
                    color: #1B5E20;
                    font-size: 16px;
                    margin-bottom: 5px;
                }}
                .item-details {{
                    font-size: 14px;
                    color: #555;
                    margin: 3px 0;
                }}
                .allergens {{
                    background-color: #FFF3E0;
                    border: 1px solid #FFB74D;
                    border-radius: 4px;
                    padding: 5px 8px;
                    margin-top: 8px;
                    font-size: 12px;
                    color: #E65100;
                }}
                .no-menu {{
                    text-align: center;
                    padding: 30px;
                    background-color: #f8f9fa;
                    border-radius: 8px;
                    margin: 20px 0;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                    font-size: 12px;
                    color: #666;
                }}
                .test-banner {{
                    background-color: #FFF3E0;
                    border: 2px solid #FF9800;
                    border-radius: 8px;
                    padding: 15px;
                    margin-bottom: 20px;
                    text-align: center;
                    color: #E65100;
                    font-weight: bold;
                }}
                @media (max-width: 600px) {{
                    body {{ padding: 10px; }}
                    .container {{ padding: 20px; }}
                    .header h1 {{ font-size: 20px; }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
        '''
        
        # Add test banner if in test mode
        if test_run:
            email_content += '''
                <div class="test-banner">
                    🧪 This is a test email - Menu shown is for today, not tomorrow
                </div>
            '''
        
        email_content += f'''
                <div class="header">
                    <h1>🍽️ {header_text}</h1>
                    <p>{subtitle}</p>
                </div>
        '''
        
        # Check if we have menu data
        if not menu_data:
            email_content += '''
                <div class="no-menu">
                    <h2>😴 No Menu Available</h2>
                    <p>There's no menu available for this date. This could be because:</p>
                    <ul style="text-align: left; display: inline-block;">
                        <li>It's a weekend (no school)</li>
                        <li>It's a holiday</li>
                        <li>The menu hasn't been published yet</li>
                        <li>There was an issue fetching the menu data</li>
                    </ul>
                </div>
            '''
        else:
            # Process each category
            category_order = ['ENTREES', 'VEGETABLES', 'FRUITS', 'MILK']
            total_items = 0
            
            for category in category_order:
                if category in menu_data and menu_data[category]:
                    items = menu_data[category]
                    if isinstance(items, list) and items:
                        email_content += f'<div class="category"><h2>{category.title()}</h2>'
                        
                        for item in items:
                            if isinstance(item, dict) and 'MenuItemDescription' in item:
                                total_items += 1
                                
                                # Item name with PreK indicator if applicable
                                item_name = item["MenuItemDescription"]
                                if prek_entree and item_name == prek_entree:
                                    email_content += f'<div class="menu-item"><div class="item-name">{item_name} [Pre-K]</div>'
                                else:
                                    email_content += f'<div class="menu-item"><div class="item-name">{item_name}</div>'
                                
                                # Add serving size and calories if available
                                if item.get("ServingSizeByGrade"):
                                    email_content += f'<div class="item-details">📏 Serving Size: {item["ServingSizeByGrade"]}</div>'
                                
                                if item.get("Calories"):
                                    email_content += f'<div class="item-details">🔥 Calories: {item["Calories"]}</div>'
                                
                                # Add allergens if present
                                if item.get("Allergens"):
                                    allergens = item["Allergens"].strip()
                                    if allergens:
                                        email_content += f'<div class="allergens">⚠️ Allergens: {allergens}</div>'
                                
                                email_content += '</div>'
                        
                        email_content += '</div>'
            
            logger.info(f"Formatted menu with {total_items} items")
        
        # Add footer
        email_content += '''
                <div class="footer">
                    <p>Data provided by SchoolCafe</p>
                    <p>This email was automatically generated by the school-menu-notifier tool built by Nick Wilson.</p>
                </div>
            </div>
        </body>
        </html>
        '''
        
        return email_content

    def send_email(self, subject: str, html_content: str) -> bool:
        """Send the menu email."""
        return self.email_sender.send_email(
            subject=subject,
            html_content=html_content,
            recipients=self.config.recipient_emails,
            test_run=self.config.test_run
        )

    def run(self) -> bool:
        """Run the menu notifier process."""
        try:
            # Get target date
            target_date = self.get_target_date()
            
            logger.info(f"Processing menu for {'today' if self.config.test_run else 'tomorrow'}: {target_date}")
            
            # Fetch menu data
            menu_data = self.fetch_menu_data(target_date)
            
            if menu_data is None:
                logger.error("Failed to fetch menu data")
                return False
            
            # Fetch PreK menu data and find matching entree
            prek_menu_data = self.fetch_prek_menu_data(target_date)
            prek_entree = None
            if prek_menu_data:
                prek_entree = self.find_prek_entree(menu_data, prek_menu_data)
                if prek_entree:
                    logger.info(f"PreK entree identified: {prek_entree}")
            
            # Format email content
            email_content = self.format_menu_email(menu_data, target_date, prek_entree)
            
            # Determine subject
            try:
                date_obj = datetime.strptime(target_date, '%m/%d/%Y')
                formatted_date = date_obj.strftime('%A, %B %d, %Y')
            except ValueError:
                formatted_date = target_date
            
            if self.config.test_run:
                subject = f"🧪 TEST: Today's School Lunch Menu - {formatted_date}"
            else:
                subject = f"🍽️ Tomorrow's School Lunch Menu - {formatted_date}"
            
            # Send email
            if self.send_email(subject, email_content):
                logger.info("Menu notification completed successfully")
                return True
            else:
                logger.error("Failed to send menu notification")
                return False
                
        except Exception as e:
            logger.error(f"Error in menu notification process: {e}")
            return False


def main():
    """Main entry point for the daily notifier."""
    try:
        notifier = SchoolMenuNotifier()
        success = notifier.run()
        
        if success:
            logger.info("Daily menu notification completed successfully")
        else:
            logger.error("Daily menu notification failed")
            exit(1)
            
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        exit(1)


if __name__ == "__main__":
    main()
