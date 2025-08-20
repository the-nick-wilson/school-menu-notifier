#!/usr/bin/env python3
"""
Simple API test script for SchoolCafe

This script tests the connection to the SchoolCafe API without sending emails.
"""

import requests
from datetime import datetime, timedelta

def test_api_connection():
    """Test the SchoolCafe API connection."""
    
    # Configuration (you can modify these values)
    school_id = '2f37947e-6d30-4bb3-a306-7f69a3b3ed62'
    grade = '01'
    serving_line = 'Main Line'
    meal_type = 'Lunch'
    
    # Get tomorrow's date
    tomorrow = datetime.now() + timedelta(days=1)
    serving_date = tomorrow.strftime('%m/%d/%Y')
    
    # API endpoint
    api_url = 'https://webapis.schoolcafe.com/api/CalendarView/GetDailyMenuitemsByGrade'
    
    # Parameters
    params = {
        'SchoolId': school_id,
        'ServingDate': serving_date,
        'ServingLine': serving_line,
        'MealType': meal_type,
        'Grade': grade,
        'PersonId': 'null'
    }
    
    # Headers
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'en-US,en;q=0.9,es;q=0.8',
        'origin': 'https://www.schoolcafe.com',
        'referer': 'https://www.schoolcafe.com/'
    }
    
    print("SchoolCafe API Test")
    print("=" * 30)
    print(f"Testing connection for: {serving_date}")
    print(f"School ID: {school_id}")
    print(f"Grade: {grade}")
    print(f"Meal: {meal_type}")
    print(f"Serving Line: {serving_line}")
    print()
    
    try:
        print("🔄 Making API request...")
        response = requests.get(api_url, params=params, headers=headers, timeout=30)
        
        print(f"📡 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ API request successful!")
            
            try:
                data = response.json()
                print(f"📊 Response contains {len(data)} categories")
                
                # Show menu items by category
                total_items = 0
                for category, items in data.items():
                    if items and isinstance(items, list):
                        print(f"\n🍽️ {category.title()}:")
                        for item in items[:3]:  # Show first 3 items
                            if isinstance(item, dict) and 'MenuItemDescription' in item:
                                name = item['MenuItemDescription']
                                serving = item.get('ServingSizeByGrade', 'N/A')
                                calories = item.get('Calories', 'N/A')
                                allergens = item.get('Allergens', 'None')
                                print(f"  • {name} ({serving}, {calories} cal)")
                                if allergens and allergens != 'None':
                                    print(f"    ⚠️ Allergens: {allergens}")
                        total_items += len(items)
                
                print(f"\n📈 Total menu items: {total_items}")
                
                if total_items == 0:
                    print("⚠️ No menu items found. This might be normal for weekends/holidays.")
                
            except Exception as e:
                print(f"❌ Error parsing JSON response: {e}")
                print(f"Raw response: {response.text[:500]}...")
                
        else:
            print(f"❌ API request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out. The API might be slow or unavailable.")
    except requests.exceptions.ConnectionError:
        print("🔌 Connection error. Check your internet connection.")
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
    except Exception as e:
        print(f"💥 Unexpected error: {e}")

if __name__ == "__main__":
    test_api_connection() 