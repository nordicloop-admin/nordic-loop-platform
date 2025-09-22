#!/usr/bin/env python3
"""
Test the subscription API endpoint directly
"""
import os
import sys
import django
import requests
import json

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.test.client import Client
from django.urls import reverse

User = get_user_model()

def test_api_endpoint():
    """Test the subscription API endpoint using Django's test client"""
    
    # Get the user
    try:
        user = User.objects.get(email='kareraol1@gmail.com')
        print(f"Found user: {user.email}")
    except User.DoesNotExist:
        print("User not found!")
        return
    
    # Create a test client and login
    client = Client()
    client.force_login(user)
    
    # Test the API endpoint
    url = '/api/payments/subscriptions/change-plan/'
    data = {'plan_type': 'standard'}
    
    print(f"Testing URL: {url}")
    print(f"Data: {data}")
    
    response = client.post(
        url,
        data=json.dumps(data),
        content_type='application/json'
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response Content: {response.content.decode()}")
    
    if response.status_code != 200:
        print(f"Headers: {dict(response.headers)}")


if __name__ == "__main__":
    test_api_endpoint()
