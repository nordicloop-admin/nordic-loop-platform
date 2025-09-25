#!/usr/bin/env python3
"""
Direct test of the dashboard stats view logic
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from base.views import UserDashboardStatsView
from django.test import RequestFactory
from rest_framework.test import force_authenticate

def test_dashboard_view_directly():
    """Test the dashboard view directly without HTTP client"""
    print("🧪 Testing Dashboard View Logic Directly...")
    
    User = get_user_model()
    user = User.objects.first()
    
    if not user:
        print("❌ No users found in database")
        return
    
    print(f"📋 Testing with user: {user.username}")
    
    try:
        # Create a fake request
        factory = RequestFactory()
        request = factory.get('/api/base/dashboard/stats/')
        force_authenticate(request, user=user)
        request.user = user
        
        # Test the view
        view = UserDashboardStatsView()
        response = view.get(request)
        
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Dashboard stats view working successfully!")
            data = response.data
            print(f"📈 Response contains: {list(data.keys())}")
            
            # Check for expected keys
            expected_keys = ['user_id', 'username', 'active_bids', 'winning_bids', 'total_bids', 'active_ads']
            for key in expected_keys:
                if key in data:
                    print(f"  ✓ {key}: {data[key]}")
                else:
                    print(f"  ⚠ Missing key: {key}")
            
        else:
            print(f"❌ Error status code: {response.status_code}")
            if hasattr(response, 'data'):
                print(f"   Error data: {response.data}")
            
    except Exception as e:
        print(f"❌ Exception occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_dashboard_view_directly()