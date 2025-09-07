#!/usr/bin/env python
"""
Test script to verify the HTTP API endpoint for company registration
"""
import requests
import json
import time

def test_api_endpoint():
    """Test the /api/company/create/ endpoint directly"""
    
    # Use a timestamp to ensure unique values
    timestamp = str(int(time.time()))
    
    # Sample payload that was causing the error
    test_payload = {
        "official_name": "API Test Company",
        "vat_number": f"API{timestamp}",
        "email": f"apitest{timestamp}@testcompany.com",
        "website": "testcompany.com",
        "country": "Sweden",
        "sector": "manufacturing",
        "primary_first_name": "Olivier",
        "primary_last_name": "Karera",
        "primary_email": f"apikarera{timestamp}@testcompany.com",
        "primary_position": "Developer",
        "status": "pending",
        "secondary_first_name": "olivier2",
        "secondary_last_name": "karera2",
        "secondary_email": f"apikarera1{timestamp}@testcompany.com",
        "secondary_position": "CEO"
    }
    
    # Assuming the server is running on localhost:8000
    url = "http://localhost:8000/api/company/create/"
    
    try:
        print("Testing API endpoint...")
        print(f"URL: {url}")
        print(f"Payload: {json.dumps(test_payload, indent=2)}")
        
        response = requests.post(
            url,
            json=test_payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 201:
            print("✅ SUCCESS: API endpoint works correctly!")
            response_data = response.json()
            print(f"Company ID: {response_data.get('id')}")
            print(f"Company Name: {response_data.get('official_name')}")
            return True
        else:
            print(f"❌ ERROR: Unexpected status code {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Could not connect to the server. Make sure the Django server is running.")
        print("You can start it with: python manage.py runserver")
        return False
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False


if __name__ == "__main__":
    test_api_endpoint()
