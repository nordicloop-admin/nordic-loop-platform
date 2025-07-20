#!/usr/bin/env python
"""
Test script for the password reset flow.
This script tests the three endpoints:
1. Request password reset (send OTP)
2. Verify OTP
3. Reset password
"""

import os
import sys
import django
import requests
import json
import time

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'base.settings')
django.setup()

from django.contrib.auth import get_user_model
from users.models import PasswordResetOTP

User = get_user_model()

# Configuration
BASE_URL = 'http://localhost:8000/api'  # Change this to your actual API base URL
TEST_EMAIL = 'test@example.com'  # Change this to an existing user email
NEW_PASSWORD = 'newpassword123'

def print_separator():
    print('-' * 50)

def test_request_password_reset():
    """Test the request password reset endpoint"""
    print("Testing Request Password Reset Endpoint...")
    
    url = f"{BASE_URL}/users/request-password-reset/"
    data = {
        'email': TEST_EMAIL
    }
    
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Check if OTP was created in the database
    otp_obj = PasswordResetOTP.objects.filter(email=TEST_EMAIL).order_by('-created_at').first()
    if otp_obj:
        print(f"OTP created in database: {otp_obj.otp}")
        return otp_obj.otp
    else:
        print("No OTP found in database")
        return None

def test_verify_otp(otp):
    """Test the verify OTP endpoint"""
    print_separator()
    print("Testing Verify OTP Endpoint...")
    
    url = f"{BASE_URL}/users/verify-otp/"
    data = {
        'email': TEST_EMAIL,
        'otp': otp
    }
    
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        return response.json().get('token')
    return None

def test_reset_password(token):
    """Test the reset password endpoint"""
    print_separator()
    print("Testing Reset Password Endpoint...")
    
    url = f"{BASE_URL}/users/reset-password/"
    data = {
        'email': TEST_EMAIL,
        'token': token,
        'new_password': NEW_PASSWORD,
        'confirm_password': NEW_PASSWORD
    }
    
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Verify if password was actually changed
    if response.status_code == 200:
        user = User.objects.get(email=TEST_EMAIL)
        if user.check_password(NEW_PASSWORD):
            print("Password was successfully changed!")
        else:
            print("Password change failed!")

def main():
    """Run the complete password reset flow test"""
    print("Starting Password Reset Flow Test")
    print_separator()
    
    # Step 1: Request password reset
    otp = test_request_password_reset()
    if not otp:
        print("Failed to get OTP. Exiting test.")
        return
    
    # Step 2: Verify OTP
    token = test_verify_otp(otp)
    if not token:
        print("Failed to verify OTP. Exiting test.")
        return
    
    # Step 3: Reset password
    test_reset_password(token)
    
    print_separator()
    print("Password Reset Flow Test Completed")

if __name__ == "__main__":
    main()
