#!/usr/bin/env python3
"""
Unit tests for the Weekly School Menu Notifier

These tests ensure that future changes don't break existing functionality.
"""

import unittest
from unittest.mock import patch, MagicMock, Mock
import os
import sys
from datetime import datetime, timedelta
import json

# Add the src directory to the path so we can import the modules
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

from school_menu_notifier.weekly_notifier import WeeklySchoolMenuNotifier


class TestWeeklySchoolMenuNotifier(unittest.TestCase):
    """Test cases for the WeeklySchoolMenuNotifier class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Set up environment variables for testing
        os.environ['SENDER_EMAIL'] = 'test@example.com'
        os.environ['SENDER_PASSWORD'] = 'test_password'
        os.environ['RECIPIENT_EMAIL'] = 'recipient@example.com'
        os.environ['ADDITIONAL_RECIPIENTS'] = 'additional@example.com'
        os.environ['SCHOOL_ID'] = 'test-school-id'
        os.environ['GRADE'] = '02'
        os.environ['SERVING_LINE'] = 'Test Line'
        os.environ['MEAL_TYPE'] = 'Breakfast'
        os.environ['SMTP_SERVER'] = 'test.smtp.com'
        os.environ['SMTP_PORT'] = '587'
        os.environ['TEST_RUN'] = 'false'

    def tearDown(self):
        """Clean up after each test method."""
        # Clear environment variables
        for key in ['SENDER_EMAIL', 'SENDER_PASSWORD', 'RECIPIENT_EMAIL', 
                   'ADDITIONAL_RECIPIENTS', 'SCHOOL_ID', 'GRADE', 'SERVING_LINE', 
                   'MEAL_TYPE', 'SMTP_SERVER', 'SMTP_PORT', 'TEST_RUN']:
            if key in os.environ:
                del os.environ[key]

    def test_init_with_defaults(self):
        """Test initialization with default values."""
        # Clear some environment variables to test defaults
        del os.environ['SCHOOL_ID']
        del os.environ['GRADE']
        del os.environ['SERVING_LINE']
        del os.environ['MEAL_TYPE']
        del os.environ['SMTP_SERVER']
        del os.environ['SMTP_PORT']
        
        notifier = WeeklySchoolMenuNotifier()
        
        self.assertEqual(notifier.config.school_id, '2f37947e-6d30-4bb3-a306-7f69a3b3ed62')
        self.assertEqual(notifier.config.grade, '01')
        self.assertEqual(notifier.config.serving_line, 'Main Line')
        self.assertEqual(notifier.config.meal_type, 'Lunch')
        self.assertEqual(notifier.config.smtp_server, 'smtp.gmail.com')
        self.assertEqual(notifier.config.smtp_port, 587)

    def test_init_with_custom_values(self):
        """Test initialization with custom environment variables."""
        notifier = WeeklySchoolMenuNotifier()
        
        self.assertEqual(notifier.config.school_id, 'test-school-id')
        self.assertEqual(notifier.config.grade, '02')
        self.assertEqual(notifier.config.serving_line, 'Test Line')
        self.assertEqual(notifier.config.meal_type, 'Breakfast')
        self.assertEqual(notifier.config.smtp_server, 'test.smtp.com')
        self.assertEqual(notifier.config.smtp_port, 587)

    def test_get_week_dates_normal_mode(self):
        """Test week date generation in normal mode."""
        os.environ['TEST_RUN'] = 'false'
        notifier = WeeklySchoolMenuNotifier()
        
        # Mock datetime to get predictable results
        with patch('school_menu_notifier.weekly_notifier.datetime') as mock_datetime:
            # Mock Sunday
            mock_datetime.now.return_value = datetime(2025, 8, 17)  # Sunday
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            week_dates = notifier.get_week_dates()
            
            # Should generate 5 weekdays starting Monday
            self.assertEqual(len(week_dates), 5)
            self.assertEqual(week_dates[0][0].strftime('%A'), 'Monday')
            self.assertEqual(week_dates[4][0].strftime('%A'), 'Friday')

    def test_get_week_dates_test_mode_monday(self):
        """Test week date generation in test mode starting Monday."""
        os.environ['TEST_RUN'] = 'true'
        notifier = WeeklySchoolMenuNotifier()
        
        # Mock datetime to get predictable results
        with patch('school_menu_notifier.weekly_notifier.datetime') as mock_datetime:
            # Mock Monday
            mock_datetime.now.return_value = datetime(2025, 8, 18)  # Monday
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            week_dates = notifier.get_week_dates()
            
            # Should show Tuesday through Friday (4 days)
            self.assertEqual(len(week_dates), 4)
            self.assertEqual(week_dates[0][0].strftime('%A'), 'Tuesday')
            self.assertEqual(week_dates[3][0].strftime('%A'), 'Friday')

    def test_get_week_dates_test_mode_wednesday(self):
        """Test week date generation in test mode starting Wednesday."""
        os.environ['TEST_RUN'] = 'true'
        notifier = WeeklySchoolMenuNotifier()
        
        # Mock datetime to get predictable results
        with patch('school_menu_notifier.weekly_notifier.datetime') as mock_datetime:
            # Mock Wednesday
            mock_datetime.now.return_value = datetime(2025, 8, 20)  # Wednesday
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            week_dates = notifier.get_week_dates()
            
            # Should show Thursday and Friday (2 days)
            self.assertEqual(len(week_dates), 2)
            self.assertEqual(week_dates[0][0].strftime('%A'), 'Thursday')
            self.assertEqual(week_dates[1][0].strftime('%A'), 'Friday')

    def test_get_week_dates_test_mode_friday(self):
        """Test week date generation in test mode starting Friday."""
        os.environ['TEST_RUN'] = 'true'
        notifier = WeeklySchoolMenuNotifier()
        
        # Mock datetime to get predictable results
        with patch('school_menu_notifier.weekly_notifier.datetime') as mock_datetime:
            # Mock Friday
            mock_datetime.now.return_value = datetime(2025, 8, 22)  # Friday
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            week_dates = notifier.get_week_dates()
            
            # Should show Monday (next school day)
            self.assertEqual(len(week_dates), 1)
            self.assertEqual(week_dates[0][0].strftime('%A'), 'Monday')

    def test_get_week_dates_test_mode_sunday(self):
        """Test week date generation in test mode starting Sunday."""
        os.environ['TEST_RUN'] = 'true'
        notifier = WeeklySchoolMenuNotifier()
        
        # Mock datetime to get predictable results
        with patch('school_menu_notifier.weekly_notifier.datetime') as mock_datetime:
            # Mock Sunday
            mock_datetime.now.return_value = datetime(2025, 8, 17)  # Sunday
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            week_dates = notifier.get_week_dates()
            
            # Should show entire upcoming week (Monday through Friday)
            self.assertEqual(len(week_dates), 5)
            self.assertEqual(week_dates[0][0].strftime('%A'), 'Monday')
            self.assertEqual(week_dates[4][0].strftime('%A'), 'Friday')

    @patch('school_menu_notifier.weekly_notifier.requests.get')
    def test_fetch_main_menu_data_success(self, mock_get):
        """Test successful main menu data fetching."""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'ENTREES': [{'MenuItemDescription': 'Test Entree'}],
            'VEGETABLES': [{'MenuItemDescription': 'Test Vegetable'}]
        }
        mock_get.return_value = mock_response
        
        notifier = WeeklySchoolMenuNotifier()
        result = notifier.fetch_main_menu_data('08/19/2025')
        
        self.assertIsNotNone(result)
        self.assertIn('ENTREES', result)
        self.assertIn('VEGETABLES', result)

    @patch('school_menu_notifier.weekly_notifier.requests.get')
    def test_fetch_prek_menu_data_success(self, mock_get):
        """Test successful PreK menu data fetching."""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'ENTREES': [{'MenuItemDescription': 'Test PreK Entree'}]
        }
        mock_get.return_value = mock_response
        
        notifier = WeeklySchoolMenuNotifier()
        result = notifier.fetch_prek_menu_data('08/19/2025')
        
        self.assertIsNotNone(result)
        self.assertIn('ENTREES', result)

    def test_extract_entrees(self):
        """Test extraction of entrees from menu data."""
        menu_data = {
            'ENTREES': [
                {'MenuItemDescription': 'Cheese Pizza'},
                {'MenuItemDescription': 'Pepperoni Pizza'}
            ],
            'VEGETABLES': [
                {'MenuItemDescription': 'Broccoli'}  # Should be ignored
            ]
        }
        
        notifier = WeeklySchoolMenuNotifier()
        entrees = notifier.extract_entrees(menu_data)
        
        self.assertEqual(len(entrees), 2)
        self.assertEqual(entrees[0]['MenuItemDescription'], 'Cheese Pizza')
        self.assertEqual(entrees[1]['MenuItemDescription'], 'Pepperoni Pizza')

    def test_extract_entrees_empty(self):
        """Test extraction of entrees from empty menu data."""
        menu_data = {}
        
        notifier = WeeklySchoolMenuNotifier()
        entrees = notifier.extract_entrees(menu_data)
        
        self.assertEqual(len(entrees), 0)

    def test_find_prek_entree_matching(self):
        """Test finding matching PreK entrees."""
        main_menu = {
            'ENTREES': [
                {'MenuItemDescription': 'Cheese Pizza'},
                {'MenuItemDescription': 'Pepperoni Pizza'},
                {'MenuItemDescription': 'Chicken Nuggets'}
            ]
        }
        
        prek_menu = {
            'ENTREES': [
                {'MenuItemDescription': 'Cheese Pizza'},
                {'MenuItemDescription': 'Fish Sticks'}
            ]
        }
        
        notifier = WeeklySchoolMenuNotifier()
        result = notifier.find_prek_entree(main_menu, prek_menu)
        
        self.assertEqual(result, 'Cheese Pizza')

    def test_find_prek_entree_no_matching(self):
        """Test handling when no PreK entrees match."""
        main_menu = {
            'ENTREES': [
                {'MenuItemDescription': 'Cheese Pizza'},
                {'MenuItemDescription': 'Pepperoni Pizza'}
            ]
        }
        
        prek_menu = {
            'ENTREES': [
                {'MenuItemDescription': 'Fish Sticks'},
                {'MenuItemDescription': 'Chicken Tenders'}
            ]
        }
        
        notifier = WeeklySchoolMenuNotifier()
        result = notifier.find_prek_entree(main_menu, prek_menu)
        
        self.assertIsNone(result)

    def test_format_weekly_email_with_prek(self):
        """Test weekly email formatting with PreK indicators."""
        # Create test data
        week_menus = [
            (datetime(2025, 8, 18), '08/18/2025', {
                'ENTREES': [
                    {'MenuItemDescription': 'Cheese Pizza', 'ServingSizeByGrade': '1 slice', 'Calories': 360},
                    {'MenuItemDescription': 'Pepperoni Pizza', 'ServingSizeByGrade': '1 slice', 'Calories': 380}
                ]
            }),
            (datetime(2025, 8, 19), '08/19/2025', {
                'ENTREES': [
                    {'MenuItemDescription': 'Chicken Nuggets', 'ServingSizeByGrade': '6 pieces', 'Calories': 300}
                ]
            })
        ]
        
        prek_entrees = {
            '08/18/2025': 'Cheese Pizza',
            '08/19/2025': 'Chicken Nuggets'
        }
        
        notifier = WeeklySchoolMenuNotifier()
        result = notifier.format_weekly_email(week_menus, prek_entrees)
        
        # Should include PreK indicators
        self.assertIn('[Pre-K]', result)
        self.assertIn('Cheese Pizza [Pre-K]', result)
        self.assertIn('Chicken Nuggets [Pre-K]', result)
        self.assertNotIn('Pepperoni Pizza [Pre-K]', result)

    def test_format_weekly_email_without_prek(self):
        """Test weekly email formatting without PreK indicators."""
        # Create test data
        week_menus = [
            (datetime(2025, 8, 18), '08/18/2025', {
                'ENTREES': [
                    {'MenuItemDescription': 'Cheese Pizza', 'ServingSizeByGrade': '1 slice', 'Calories': 360}
                ]
            })
        ]
        
        prek_entrees = {}
        
        notifier = WeeklySchoolMenuNotifier()
        result = notifier.format_weekly_email(week_menus, prek_entrees)
        
        # Should not include PreK indicators
        self.assertNotIn('[Pre-K]', result)
        self.assertIn('Cheese Pizza', result)

    def test_format_weekly_email_test_mode(self):
        """Test weekly email formatting in test mode."""
        os.environ['TEST_RUN'] = 'true'
        
        week_menus = [
            (datetime(2025, 8, 18), '08/18/2025', {
                'ENTREES': [
                    {'MenuItemDescription': 'Cheese Pizza', 'ServingSizeByGrade': '1 slice', 'Calories': 360}
                ]
            })
        ]
        
        prek_entrees = {}
        
        notifier = WeeklySchoolMenuNotifier()
        result = notifier.format_weekly_email(week_menus, prek_entrees)
        
        # Should show test mode header
        self.assertIn("This Week's School Lunch Menu", result)
        self.assertIn("Rest of Current Week", result)

    def test_format_weekly_email_normal_mode(self):
        """Test weekly email formatting in normal mode."""
        os.environ['TEST_RUN'] = 'false'
        
        week_menus = [
            (datetime(2025, 8, 18), '08/18/2025', {
                'ENTREES': [
                    {'MenuItemDescription': 'Cheese Pizza', 'ServingSizeByGrade': '1 slice', 'Calories': 360}
                ]
            })
        ]
        
        prek_entrees = {}
        
        notifier = WeeklySchoolMenuNotifier()
        result = notifier.format_weekly_email(week_menus, prek_entrees)
        
        # Should show normal mode header
        self.assertIn("Next Week's School Lunch Menu", result)
        self.assertIn("Upcoming Week", result)

    @patch('school_menu_notifier.common.email_sender.smtplib.SMTP')
    def test_send_email_success(self, mock_smtp):
        """Test successful email sending."""
        # Mock SMTP server
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        notifier = WeeklySchoolMenuNotifier()
        result = notifier.send_email('Test Subject', '<html>Test Content</html>')
        
        self.assertTrue(result)
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once()
        mock_server.send_message.assert_called()

    @patch('school_menu_notifier.common.email_sender.smtplib.SMTP')
    def test_send_email_test_mode_primary_only(self, mock_smtp):
        """Test email sending in test mode only sends to primary recipient."""
        os.environ['TEST_RUN'] = 'true'
        
        # Mock SMTP server
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        notifier = WeeklySchoolMenuNotifier()
        result = notifier.send_email('Test Subject', '<html>Test Content</html>')
        
        self.assertTrue(result)
        # Should only send to primary recipient (first in list)
        self.assertEqual(mock_server.send_message.call_count, 1)

    @patch('school_menu_notifier.common.email_sender.smtplib.SMTP')
    def test_send_email_normal_mode_all_recipients(self, mock_smtp):
        """Test email sending in normal mode sends to all recipients."""
        os.environ['TEST_RUN'] = 'false'
        
        # Mock SMTP server
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        notifier = WeeklySchoolMenuNotifier()
        result = notifier.send_email('Test Subject', '<html>Test Content</html>')
        
        self.assertTrue(result)
        # Should send to all recipients
        self.assertEqual(mock_server.send_message.call_count, 2)

    @patch('school_menu_notifier.weekly_notifier.requests.get')
    def test_run_success(self, mock_get):
        """Test successful run method execution."""
        # Mock successful API responses
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'ENTREES': [{'MenuItemDescription': 'Test Entree'}]
        }
        mock_get.return_value = mock_response
        
        # Mock SMTP
        with patch('school_menu_notifier.common.email_sender.smtplib.SMTP') as mock_smtp:
            mock_server = Mock()
            mock_smtp.return_value.__enter__.return_value = mock_server
            
            notifier = WeeklySchoolMenuNotifier()
            result = notifier.run()
            
            self.assertTrue(result)

    def test_validation_missing_required_vars(self):
        """Test validation fails with missing required environment variables."""
        # Remove required environment variables
        del os.environ['SENDER_EMAIL']
        
        with self.assertRaises(ValueError) as context:
            WeeklySchoolMenuNotifier()
        
        self.assertIn('SENDER_EMAIL', str(context.exception))

    def test_validation_missing_password(self):
        """Test validation fails with missing password."""
        # Remove required environment variables
        del os.environ['SENDER_PASSWORD']
        
        with self.assertRaises(ValueError) as context:
            WeeklySchoolMenuNotifier()
        
        self.assertIn('SENDER_PASSWORD', str(context.exception))

    def test_validation_missing_recipient(self):
        """Test validation fails with missing recipient."""
        # Remove required environment variables
        del os.environ['RECIPIENT_EMAIL']
        del os.environ['ADDITIONAL_RECIPIENTS']
        
        with self.assertRaises(ValueError) as context:
            WeeklySchoolMenuNotifier()
        
        self.assertIn('RECIPIENT_EMAIL', str(context.exception))


if __name__ == '__main__':
    unittest.main()
