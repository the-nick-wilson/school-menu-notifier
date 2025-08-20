#!/usr/bin/env python3
"""
Local testing script for the School Menu Notifier

This script allows you to test the menu notifier locally by loading
configuration from a .env file.
"""

import os
import sys
from dotenv import load_dotenv

# Add the src directory to the path so we can import the modules
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

from school_menu_notifier.daily_notifier import SchoolMenuNotifier

def load_env_file():
    """Load environment variables from .env file if it exists."""
    env_file = '.env'
    if os.path.exists(env_file):
        print(f"Loading configuration from {env_file}")
        load_dotenv(env_file)
        return True
    else:
        print(f"No {env_file} file found. Using system environment variables.")
        return False

def test_configuration():
    """Test the configuration and show what will be used."""
    print("=== Configuration Test ===")
    
    # Check required variables
    required_vars = [
        'SENDER_EMAIL',
        'SENDER_PASSWORD', 
        'RECIPIENT_EMAIL'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if 'PASSWORD' in var:
                print(f"✓ {var}: {'*' * len(value)}")
            else:
                print(f"✓ {var}: {value}")
        else:
            print(f"✗ {var}: NOT SET")
            missing_vars.append(var)
    
    # Check optional variables
    optional_vars = [
        'SCHOOL_ID',
        'GRADE',
        'SERVING_LINE',
        'MEAL_TYPE',
        'SMTP_SERVER',
        'SMTP_PORT'
    ]
    
    print("\n=== Optional Configuration ===")
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            print(f"✓ {var}: {value}")
        else:
            print(f"- {var}: Using default value")
    
    if missing_vars:
        print(f"\n❌ Missing required variables: {', '.join(missing_vars)}")
        print("Please set these in your .env file or as environment variables.")
        return False
    
    print("\n✅ Configuration looks good!")
    return True

def main():
    """Main testing function."""
    print("School Menu Notifier - Local Test")
    print("=" * 40)
    
    # Load environment variables
    load_env_file()
    
    # Test configuration
    if not test_configuration():
        print("\nExiting due to configuration issues.")
        return
    
    # Ask user if they want to proceed
    response = input("\nDo you want to test the menu notifier now? (y/N): ")
    if response.lower() != 'y':
        print("Exiting. You can run the test again later.")
        return
    
    try:
        print("\n🚀 Starting menu notifier test...")
        notifier = SchoolMenuNotifier()
        success = notifier.run()
        
        if success:
            print("\n✅ Test completed successfully!")
            print("Check your email for the menu notification.")
        else:
            print("\n❌ Test failed. Check the logs above for details.")
            
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        print("Please check your configuration and try again.")

if __name__ == "__main__":
    # Check if python-dotenv is available
    try:
        from dotenv import load_dotenv
    except ImportError:
        print("python-dotenv not found. Installing...")
        import subprocess
        subprocess.run(["pip", "install", "python-dotenv"])
        from dotenv import load_dotenv
    
    main() 