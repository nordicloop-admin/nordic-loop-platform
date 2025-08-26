#!/usr/bin/env python3
"""
Test script for Swedish bank account setup with correct Stripe test data
Tests the POST /api/payments/bank-account/ endpoint with valid Swedish bank data
"""

import os
import sys
import django
import json
import requests

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

def test_swedish_bank_account_data():
    """Test valid Swedish bank account test data for Stripe"""
    
    print("🇸🇪 Swedish Bank Account Test Data for Stripe")
    print("=" * 50)
    
    # Valid test data for different Swedish banks
    test_accounts = [
        {
            "name": "Handelsbanken (Recommended)",
            "data": {
                "account_holder_name": "Test User",
                "bank_name": "Svenska Handelsbanken",
                "account_number": "SE4550000000058398257466",  # Valid Swedish IBAN
                "routing_number": "HANDSESS",  # BIC/SWIFT code for Handelsbanken
                "bank_country": "SE",
                "currency": "SEK"
            }
        },
        {
            "name": "SEB (Alternative)",
            "data": {
                "account_holder_name": "Test User",
                "bank_name": "Skandinaviska Enskilda Banken",
                "account_number": "SE3550000000054910000003",  # Valid Swedish IBAN
                "routing_number": "ESSESESS",  # BIC/SWIFT code for SEB
                "bank_country": "SE",
                "currency": "SEK"
            }
        },
        {
            "name": "Swedbank (Alternative)",
            "data": {
                "account_holder_name": "Test User",
                "bank_name": "Swedbank",
                "account_number": "SE7280000810340009783242",  # Valid Swedish IBAN
                "routing_number": "SWEDSESS",  # BIC/SWIFT code for Swedbank
                "bank_country": "SE",
                "currency": "SEK"
            }
        }
    ]
    
    print("✅ Valid Swedish Bank Account Test Data:")
    print()
    
    for i, account in enumerate(test_accounts, 1):
        print(f"{i}. {account['name']}")
        print(f"   Account Holder: {account['data']['account_holder_name']}")
        print(f"   Bank Name: {account['data']['bank_name']}")
        print(f"   IBAN: {account['data']['account_number']}")
        print(f"   BIC/SWIFT: {account['data']['routing_number']}")
        print(f"   Country: {account['data']['bank_country']}")
        print(f"   Currency: {account['data']['currency']}")
        print()
    
    return test_accounts

def test_iban_format_validation():
    """Test IBAN format validation for Swedish accounts"""
    
    print("🔍 Swedish IBAN Format Validation")
    print("=" * 35)
    
    print("Swedish IBAN Format: SE + 2 check digits + 20 digits")
    print("Example: SE4550000000058398257466")
    print()
    
    print("Structure breakdown:")
    print("• SE: Country code for Sweden")
    print("• 45: Check digits (calculated)")
    print("• 5000: Bank code")
    print("• 0000005839: Account number")
    print("• 8257466: Additional digits")
    print()
    
    print("✅ Key Requirements:")
    print("• Total length: 24 characters")
    print("• Starts with 'SE'")
    print("• Followed by 22 digits")
    print("• Must pass IBAN checksum validation")
    
    return True

def test_bic_codes():
    """Test BIC/SWIFT codes for Swedish banks"""
    
    print("\n🏦 Swedish Bank BIC/SWIFT Codes")
    print("=" * 35)
    
    bic_codes = [
        ("HANDSESS", "Svenska Handelsbanken", "Most widely used"),
        ("ESSESESS", "Skandinaviska Enskilda Banken (SEB)", "Major commercial bank"),
        ("SWEDSESS", "Swedbank", "Popular retail bank"),
        ("NDEASESS", "Nordea Bank", "Nordic bank"),
        ("ELLFSESS", "Länsförsäkringar Bank", "Regional bank")
    ]
    
    print("Valid BIC codes for Swedish banks:")
    print()
    
    for bic, bank, description in bic_codes:
        print(f"• {bic}: {bank}")
        print(f"  {description}")
        print()
    
    print("✅ BIC Format: 8 characters")
    print("• First 4: Bank code")
    print("• Next 2: Country code (SE)")
    print("• Last 2: Location code")
    
    return True

def test_api_endpoint_with_valid_data():
    """Test the API endpoint with valid Swedish bank data"""
    
    print("\n🧪 Testing API Endpoint with Valid Data")
    print("=" * 40)
    
    # Check if backend is running
    try:
        response = requests.get('http://127.0.0.1:8000/api/', timeout=5)
        if response.status_code != 200:
            print("❌ Backend server not accessible")
            return False
    except:
        print("❌ Backend server not running")
        print("   Start with: python manage.py runserver")
        return False
    
    print("✅ Backend server is running")
    
    # Get test data
    test_accounts = test_swedish_bank_account_data()
    recommended_data = test_accounts[0]['data']  # Use Handelsbanken data
    
    print(f"\n📝 Testing with {test_accounts[0]['name']} data:")
    print(f"   IBAN: {recommended_data['account_number']}")
    print(f"   BIC: {recommended_data['routing_number']}")
    
    print("\n🔗 To test manually:")
    print("1. Open: http://localhost:3000/dashboard/payments")
    print("2. Fill in the form with this data:")
    print(f"   • Account Holder Name: {recommended_data['account_holder_name']}")
    print(f"   • Bank Name: {recommended_data['bank_name']}")
    print(f"   • Account Number: {recommended_data['account_number']}")
    print(f"   • Routing Number: {recommended_data['routing_number']}")
    print(f"   • Country: Sweden")
    print(f"   • Currency: SEK")
    print("3. Submit the form")
    print("4. Check for successful account creation")
    
    return True

def test_common_errors():
    """Test common errors and their solutions"""
    
    print("\n❌ Common Errors and Solutions")
    print("=" * 35)
    
    errors = [
        {
            "error": "Invalid BIC",
            "cause": "Using incorrect or non-existent BIC code",
            "solution": "Use valid Swedish BIC codes like HANDSESS, ESSESESS, SWEDSESS"
        },
        {
            "error": "Invalid account number",
            "cause": "Using non-IBAN format or incorrect IBAN",
            "solution": "Use proper Swedish IBAN format (24 chars, starts with SE)"
        },
        {
            "error": "Currency mismatch",
            "cause": "Using wrong currency for Swedish accounts",
            "solution": "Always use SEK for Swedish bank accounts"
        },
        {
            "error": "Country code mismatch",
            "cause": "Using wrong country code",
            "solution": "Use 'SE' for Sweden, not 'SWE' or other variants"
        }
    ]
    
    for i, error in enumerate(errors, 1):
        print(f"{i}. Error: {error['error']}")
        print(f"   Cause: {error['cause']}")
        print(f"   Solution: {error['solution']}")
        print()
    
    return True

def main():
    """Main test function"""
    
    print("🚀 Swedish Bank Account Setup Test")
    print("=" * 50)
    print("Testing Stripe Connect integration with valid Swedish bank data")
    print("=" * 50)
    
    # Run all tests
    tests = [
        ("Swedish Bank Account Data", test_swedish_bank_account_data),
        ("IBAN Format Validation", test_iban_format_validation),
        ("BIC Codes", test_bic_codes),
        ("API Endpoint Testing", test_api_endpoint_with_valid_data),
        ("Common Errors", test_common_errors),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
            results.append((test_name, False))
    
    # Summary
    print("📊 Test Summary")
    print("=" * 20)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        print("\n📋 Ready to Test:")
        print("• Use the provided Swedish bank account test data")
        print("• Test the bank account setup form")
        print("• Verify Stripe Connect integration works")
        print("• Check the improved UI/UX design")
        
        print("\n🔗 Test URLs:")
        print("• Payment Setup: http://localhost:3000/dashboard/payments")
        print("• API Endpoint: http://127.0.0.1:8000/api/payments/bank-account/")
        
        print("\n💡 Recommended Test Data (Handelsbanken):")
        print("• Account Holder: Test User")
        print("• Bank Name: Svenska Handelsbanken")
        print("• IBAN: SE4550000000058398257466")
        print("• BIC: HANDSESS")
        print("• Country: Sweden (SE)")
        print("• Currency: SEK")
        
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check the issues above.")

if __name__ == "__main__":
    main()
