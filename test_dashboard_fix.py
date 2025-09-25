#!/usr/bin/env python3
"""
Test script to verify dashboard stats API fix
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client
import json

def test_dashboard_stats():
    """Test the dashboard stats API endpoint"""
    print("🧪 Testing Dashboard Stats API...")
    
    User = get_user_model()
    client = Client()
    
    # Try to get a user to test with
    user = User.objects.first()
    if not user:
        print("❌ No users found in database")
        return
    
    print(f"📋 Testing with user: {user.username}")
    client.force_login(user)
    
    try:
        response = client.get('/api/base/dashboard/stats/')
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Dashboard stats API working successfully!")
            data = response.json()
            print(f"📈 Response contains: {list(data.keys())}")
            
            # Check for expected keys
            expected_keys = ['user_id', 'username', 'active_bids', 'winning_bids', 'total_bids', 'active_ads']
            for key in expected_keys:
                if key in data:
                    print(f"  ✓ {key}: {data[key]}")
                else:
                    print(f"  ⚠ Missing key: {key}")
            
        elif response.status_code == 500:
            print("❌ Internal Server Error - the 'is_active' issue may still exist")
            try:
                error_data = response.json()
                if 'error' in error_data:
                    print(f"   Error: {error_data['error']}")
            except:
                print("   Unable to parse error response")
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Exception occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_dashboard_stats()