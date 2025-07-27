#!/usr/bin/env python3
"""
Test category subscription endpoints functionality
"""

import os
import django
import requests
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

from category.models import Category, SubCategory
from category_subscriptions.models import CategorySubscription
from users.models import User

User = get_user_model()


def test_category_subscription_endpoints():
    """Test category subscription endpoints functionality"""
    print("🧪 Testing Category Subscription Endpoints")
    print("=" * 60)
    
    # Get the existing admin user
    try:
        test_user = User.objects.get(email="karera@gmail.com")
        print(f"✅ Found test user: {test_user.username}")
        print(f"   - Is Staff: {test_user.is_staff}")
        print(f"   - Is Superuser: {test_user.is_superuser}")
    except User.DoesNotExist:
        print("❌ Test user not found")
        return
    
    # Generate JWT token
    refresh = RefreshToken.for_user(test_user)
    access_token = str(refresh.access_token)
    
    # Set up headers
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    base_url = 'http://localhost:8000'
    
    # Get or create test categories
    category, created = Category.objects.get_or_create(name="Test Plastics")
    if created:
        print(f"✅ Created test category: {category.name}")
    else:
        print(f"✅ Using existing category: {category.name}")
    
    subcategory, created = SubCategory.objects.get_or_create(
        name="Test PP", 
        category=category
    )
    if created:
        print(f"✅ Created test subcategory: {subcategory.name}")
    else:
        print(f"✅ Using existing subcategory: {subcategory.name}")
    
    print(f"\n📋 Test data:")
    print(f"   - Category ID: {category.id}")
    print(f"   - Category Name: {category.name}")
    print(f"   - Subcategory ID: {subcategory.id}")
    print(f"   - Subcategory Name: {subcategory.name}")
    
    # Clean up any existing subscriptions for this user
    CategorySubscription.objects.filter(user=test_user, category=category).delete()
    print("🧹 Cleaned up existing subscriptions")
    
    # Test 1: List existing subscriptions (GET)
    print(f"\n🔧 TEST 1: List Category Subscriptions (GET)")
    print("-" * 40)
    
    list_url = f'{base_url}/api/category-subscriptions/'
    print(f"GET {list_url}")
    
    try:
        response = requests.get(list_url, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SUCCESS: Subscriptions list retrieved")
            response_data = response.json()
            print(f"Current subscriptions count: {len(response_data)}")
            
        else:
            print(f"❌ FAILED: Status {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {error_data}")
            except:
                print(f"Raw response: {response.text}")
                
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test 2: Subscribe to Category (POST)
    print(f"\n🔧 TEST 2: Subscribe to Category (POST)")
    print("-" * 40)
    
    subscribe_category_url = f'{base_url}/api/category-subscriptions/subscribe_category/'
    print(f"POST {subscribe_category_url}")
    
    category_data = {
        'category_id': category.id
    }
    print(f"Data: {category_data}")
    
    try:
        response = requests.post(subscribe_category_url, headers=headers, json=category_data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 201:
            print("✅ SUCCESS: Category subscription created")
            response_data = response.json()
            print(f"Subscription ID: {response_data.get('id', 'Unknown')}")
            print(f"Material Type: {response_data.get('material_type', 'Unknown')}")
            
        else:
            print(f"❌ FAILED: Status {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {error_data}")
            except:
                print(f"Raw response: {response.text}")
                
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test 3: Subscribe to Subcategory (POST)
    print(f"\n🔧 TEST 3: Subscribe to Subcategory (POST)")
    print("-" * 40)
    
    subscribe_subcategory_url = f'{base_url}/api/category-subscriptions/subscribe_subcategory/'
    print(f"POST {subscribe_subcategory_url}")
    
    subcategory_data = {
        'subcategory_id': subcategory.id
    }
    print(f"Data: {subcategory_data}")
    
    try:
        response = requests.post(subscribe_subcategory_url, headers=headers, json=subcategory_data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 201:
            print("✅ SUCCESS: Subcategory subscription created")
            response_data = response.json()
            print(f"Subscription ID: {response_data.get('id', 'Unknown')}")
            print(f"Material Type: {response_data.get('material_type', 'Unknown')}")
            print(f"Subcategory: {response_data.get('subcategory_name', 'Unknown')}")
            
        else:
            print(f"❌ FAILED: Status {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {error_data}")
            except:
                print(f"Raw response: {response.text}")
                
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test 4: Create subscription using standard POST (ModelViewSet create)
    print(f"\n🔧 TEST 4: Create Subscription via Standard POST")
    print("-" * 40)
    
    create_url = f'{base_url}/api/category-subscriptions/'
    print(f"POST {create_url}")
    
    # Create another category for this test
    category2, _ = Category.objects.get_or_create(name="Test Metals")
    
    create_data = {
        'category': category2.id
    }
    print(f"Data: {create_data}")
    
    try:
        response = requests.post(create_url, headers=headers, json=create_data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 201:
            print("✅ SUCCESS: Subscription created via standard POST")
            response_data = response.json()
            print(f"Subscription ID: {response_data.get('id', 'Unknown')}")
            print(f"Material Type: {response_data.get('material_type', 'Unknown')}")
            
        else:
            print(f"❌ FAILED: Status {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {error_data}")
            except:
                print(f"Raw response: {response.text}")
                
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test 5: Check subscription status
    print(f"\n🔧 TEST 5: Check Subscription Status")
    print("-" * 40)
    
    check_url = f'{base_url}/api/category-subscriptions/check_subscription/'
    print(f"GET {check_url}?category_id={category.id}")
    
    try:
        response = requests.get(f"{check_url}?category_id={category.id}", headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SUCCESS: Subscription status checked")
            response_data = response.json()
            print(f"Is Subscribed: {response_data.get('is_subscribed', 'Unknown')}")
            
        else:
            print(f"❌ FAILED: Status {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {error_data}")
            except:
                print(f"Raw response: {response.text}")
                
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test 6: Test without authentication
    print(f"\n🔧 TEST 6: Test without Authentication")
    print("-" * 40)
    
    try:
        response = requests.get(list_url)  # No headers
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 401:
            print("✅ SUCCESS: Correctly returns 401 for unauthenticated request")
        else:
            print(f"❓ Status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test 7: Test duplicate subscription
    print(f"\n🔧 TEST 7: Test Duplicate Subscription")
    print("-" * 40)
    
    try:
        response = requests.post(subscribe_category_url, headers=headers, json=category_data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 400:
            print("✅ SUCCESS: Correctly prevents duplicate subscription")
            response_data = response.json()
            print(f"Error: {response_data.get('error', 'No error message')}")
        else:
            print(f"❓ Status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test 8: Unsubscribe
    print(f"\n🔧 TEST 8: Unsubscribe")
    print("-" * 40)
    
    # Get a subscription to unsubscribe from
    subscription = CategorySubscription.objects.filter(user=test_user, category=category).first()
    if subscription:
        unsubscribe_url = f'{base_url}/api/category-subscriptions/unsubscribe/'
        unsubscribe_data = {
            'subscription_id': subscription.id
        }
        print(f"POST {unsubscribe_url}")
        print(f"Data: {unsubscribe_data}")
        
        try:
            response = requests.post(unsubscribe_url, headers=headers, json=unsubscribe_data)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 204:
                print("✅ SUCCESS: Unsubscribed successfully")
            else:
                print(f"❌ FAILED: Status {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"Error: {error_data}")
                except:
                    print(f"Raw response: {response.text}")
                    
        except Exception as e:
            print(f"❌ Exception: {e}")
    else:
        print("❌ No subscription found to unsubscribe from")
    
    # Clean up
    print(f"\n🧹 Cleaning up test data...")
    CategorySubscription.objects.filter(user=test_user, category__in=[category, category2]).delete()
    print("✅ Test subscriptions cleaned up")
    
    print(f"\n🎯 TESTING COMPLETE")
    print("-" * 40)
    print("✅ Category subscription list tested")
    print("✅ Category subscription creation tested")
    print("✅ Subcategory subscription creation tested")
    print("✅ Standard POST creation tested")
    print("✅ Subscription status check tested")
    print("✅ Authentication tested")
    print("✅ Duplicate prevention tested")
    print("✅ Unsubscribe tested")


if __name__ == "__main__":
    test_category_subscription_endpoints()
