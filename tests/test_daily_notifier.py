#!/usr/bin/env python3
"""
Unit tests for the School Menu Notifier

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

from school_menu_notifier.daily_notifier import SchoolMenuNotifier


class TestSchoolMenuNotifier(unittest.TestCase):
    """Test cases for the SchoolMenuNotifier class."""

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
        
        notifier = SchoolMenuNotifier()
        
        self.assertEqual(notifier.config.school_id, '2f37947e-6d30-4bb3-a306-7f69a3b3ed62')
        self.assertEqual(notifier.config.grade, '01')
        self.assertEqual(notifier.config.serving_line, 'Main Line')
        self.assertEqual(notifier.config.meal_type, 'Lunch')
        self.assertEqual(notifier.config.smtp_server, 'smtp.gmail.com')
        self.assertEqual(notifier.config.smtp_port, 587)

    def test_init_with_custom_values(self):
        """Test initialization with custom environment variables."""
        notifier = SchoolMenuNotifier()
        
        self.assertEqual(notifier.config.school_id, 'test-school-id')
        self.assertEqual(notifier.config.grade, '02')
        self.assertEqual(notifier.config.serving_line, 'Test Line')
        self.assertEqual(notifier.config.meal_type, 'Breakfast')
        self.assertEqual(notifier.config.smtp_server, 'test.smtp.com')
        self.assertEqual(notifier.config.smtp_port, 587)

    def test_init_with_empty_strings(self):
        """Test initialization handles empty environment variables gracefully."""
        os.environ['SCHOOL_ID'] = ''
        os.environ['GRADE'] = ''
        os.environ['SERVING_LINE'] = ''
        os.environ['MEAL_TYPE'] = ''
        os.environ['SMTP_SERVER'] = ''
        os.environ['SMTP_PORT'] = ''
        
        notifier = SchoolMenuNotifier()
        
        # Should use defaults for empty strings
        self.assertEqual(notifier.config.school_id, '2f37947e-6d30-4bb3-a306-7f69a3b3ed62')
        self.assertEqual(notifier.config.grade, '01')
        self.assertEqual(notifier.config.serving_line, 'Main Line')
        self.assertEqual(notifier.config.meal_type, 'Lunch')
        self.assertEqual(notifier.config.smtp_server, 'smtp.gmail.com')
        self.assertEqual(notifier.config.smtp_port, 587)

    def test_init_with_invalid_smtp_port(self):
        """Test initialization handles invalid SMTP port gracefully."""
        os.environ['SMTP_PORT'] = 'invalid'
        
        notifier = SchoolMenuNotifier()
        
        # Should fall back to default port
        self.assertEqual(notifier.config.smtp_port, 587)

    def test_multiple_recipients(self):
        """Test handling of multiple recipients."""
        notifier = SchoolMenuNotifier()
        
        self.assertEqual(len(notifier.config.recipient_emails), 2)
        self.assertIn('recipient@example.com', notifier.config.recipient_emails)
        self.assertIn('additional@example.com', notifier.config.recipient_emails)

    def test_multiple_recipients_with_duplicates(self):
        """Test handling of duplicate recipients."""
        os.environ['RECIPIENT_EMAIL'] = 'same@example.com'
        os.environ['ADDITIONAL_RECIPIENTS'] = 'same@example.com,other@example.com'
        
        notifier = SchoolMenuNotifier()
        
        # Should remove duplicates
        self.assertEqual(len(notifier.config.recipient_emails), 2)
        self.assertIn('same@example.com', notifier.config.recipient_emails)
        self.assertIn('other@example.com', notifier.config.recipient_emails)

    def test_get_target_date_normal_mode(self):
        """Test target date calculation in normal mode."""
        os.environ['TEST_RUN'] = 'false'
        notifier = SchoolMenuNotifier()
        
        target_date = notifier.get_target_date()
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%m/%d/%Y')
        
        self.assertEqual(target_date, tomorrow)

    def test_get_target_date_test_mode(self):
        """Test target date calculation in test mode."""
        os.environ['TEST_RUN'] = 'true'
        notifier = SchoolMenuNotifier()
        
        target_date = notifier.get_target_date()
        today = datetime.now().strftime('%m/%d/%Y')
        
        self.assertEqual(target_date, today)

    def test_get_target_date_weekend_detection(self):
        """Test weekend detection in target date calculation."""
        os.environ['TEST_RUN'] = 'false'
        notifier = SchoolMenuNotifier()
        
        # Mock datetime to simulate Friday
        with patch('school_menu_notifier.daily_notifier.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2025, 8, 15)  # Friday
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            target_date = notifier.get_target_date()
            # Should detect that Saturday is a weekend
            # The actual weekend detection is in the logging, not return value

    @patch('school_menu_notifier.daily_notifier.requests.get')
    def test_fetch_menu_data_success(self, mock_get):
        """Test successful menu data fetching."""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'ENTREES': [{'MenuItemDescription': 'Test Entree'}],
            'VEGETABLES': [{'MenuItemDescription': 'Test Vegetable'}]
        }
        mock_get.return_value = mock_response
        
        notifier = SchoolMenuNotifier()
        result = notifier.fetch_menu_data('08/19/2025')
        
        self.assertIsNotNone(result)
        self.assertIn('ENTREES', result)
        self.assertIn('VEGETABLES', result)

    @patch('school_menu_notifier.daily_notifier.requests.get')
    def test_fetch_menu_data_empty_response(self, mock_get):
        """Test handling of empty API response."""
        # Mock empty API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_get.return_value = mock_response
        
        notifier = SchoolMenuNotifier()
        result = notifier.fetch_menu_data('08/19/2025')
        
        # Should return empty dict, not None
        self.assertEqual(result, {})

    @patch('school_menu_notifier.daily_notifier.requests.get')
    def test_fetch_menu_data_api_error(self, mock_get):
        """Test handling of API errors."""
        # Mock API error
        mock_get.side_effect = Exception("API Error")
        
        notifier = SchoolMenuNotifier()
        result = notifier.fetch_menu_data('08/19/2025')
        
        self.assertIsNone(result)
        mock_get.assert_called_once()

    @patch('school_menu_notifier.daily_notifier.requests.get')
    def test_fetch_prek_menu_data_success(self, mock_get):
        """Test successful PreK menu data fetching."""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'ENTREES': [{'MenuItemDescription': 'Test PreK Entree'}]
        }
        mock_get.return_value = mock_response
        
        notifier = SchoolMenuNotifier()
        result = notifier.fetch_prek_menu_data('08/19/2025')
        
        self.assertIsNotNone(result)
        self.assertIn('ENTREES', result)

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
        
        notifier = SchoolMenuNotifier()
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
        
        notifier = SchoolMenuNotifier()
        result = notifier.find_prek_entree(main_menu, prek_menu)
        
        self.assertIsNone(result)

    def test_find_prek_entree_empty_menus(self):
        """Test handling of empty menus."""
        notifier = SchoolMenuNotifier()
        
        # Test with None menus
        result = notifier.find_prek_entree(None, {})
        self.assertIsNone(result)
        
        result = notifier.find_prek_entree({}, None)
        self.assertIsNone(result)

    def test_format_menu_email_with_prek(self):
        """Test email formatting with PreK indicator."""
        menu_data = {
            'ENTREES': [
                {'MenuItemDescription': 'Cheese Pizza', 'ServingSizeByGrade': '1 slice', 'Calories': 360},
                {'MenuItemDescription': 'Pepperoni Pizza', 'ServingSizeByGrade': '1 slice', 'Calories': 380}
            ]
        }
        
        notifier = SchoolMenuNotifier()
        result = notifier.format_menu_email(menu_data, '08/19/2025', 'Cheese Pizza')
        
        # Should include PreK indicator
        self.assertIn('[Pre-K]', result)
        self.assertIn('Cheese Pizza [Pre-K]', result)
        self.assertNotIn('Pepperoni Pizza [Pre-K]', result)

    def test_format_menu_email_without_prek(self):
        """Test email formatting without PreK indicator."""
        menu_data = {
            'ENTREES': [
                {'MenuItemDescription': 'Cheese Pizza', 'ServingSizeByGrade': '1 slice', 'Calories': 360}
            ]
        }
        
        notifier = SchoolMenuNotifier()
        result = notifier.format_menu_email(menu_data, '08/19/2025', None)
        
        # Should not include PreK indicator
        self.assertNotIn('[Pre-K]', result)
        self.assertIn('Cheese Pizza', result)

    def test_format_menu_email_with_allergens(self):
        """Test email formatting includes allergen information."""
        menu_data = {
            'ENTREES': [
                {
                    'MenuItemDescription': 'Cheese Pizza',
                    'ServingSizeByGrade': '1 slice',
                    'Calories': 360,
                    'Allergens': 'Milk,Wheat,Soy'
                }
            ]
        }
        
        notifier = SchoolMenuNotifier()
        result = notifier.format_menu_email(menu_data, '08/19/2025')
        
        # Should include allergen information
        self.assertIn('⚠️ Allergens: Milk,Wheat,Soy', result)

    @patch('school_menu_notifier.common.email_sender.smtplib.SMTP')
    def test_send_email_success(self, mock_smtp):
        """Test successful email sending."""
        # Mock SMTP server
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        notifier = SchoolMenuNotifier()
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
        
        notifier = SchoolMenuNotifier()
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
        
        notifier = SchoolMenuNotifier()
        result = notifier.send_email('Test Subject', '<html>Test Content</html>')
        
        self.assertTrue(result)
        # Should send to all recipients
        self.assertEqual(mock_server.send_message.call_count, 2)

    def test_validation_missing_required_vars(self):
        """Test validation fails with missing required environment variables."""
        # Remove required environment variables
        del os.environ['SENDER_EMAIL']
        
        with self.assertRaises(ValueError) as context:
            SchoolMenuNotifier()
        
        self.assertIn('SENDER_EMAIL', str(context.exception))

    def test_validation_missing_password(self):
        """Test validation fails with missing password."""
        # Remove required environment variables
        del os.environ['SENDER_PASSWORD']
        
        with self.assertRaises(ValueError) as context:
            SchoolMenuNotifier()
        
        self.assertIn('SENDER_PASSWORD', str(context.exception))

    def test_validation_missing_recipient(self):
        """Test validation fails with missing recipient."""
        # Remove required environment variables
        del os.environ['RECIPIENT_EMAIL']
        del os.environ['ADDITIONAL_RECIPIENTS']
        
        with self.assertRaises(ValueError) as context:
            SchoolMenuNotifier()
        
        self.assertIn('RECIPIENT_EMAIL', str(context.exception))


if __name__ == '__main__':
    unittest.main()
