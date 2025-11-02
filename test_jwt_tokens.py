"""
Test script to verify JWT token contains custom user data
Run this after implementing the custom tokens
"""
import os
import sys
import django
from pathlib import Path

# Add the project root to Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Setup Django
os.environ.setdefault('DJANGO_SECRET_KEY', 'test-key-for-development')
os.environ.setdefault('DJANGO_DEBUG', 'True')

# Configure Django settings
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        SECRET_KEY='test-key-for-development',
        DEBUG=True,
        INSTALLED_APPS=[
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'rest_framework',
            'rest_framework_simplejwt',
            'users',
        ],
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },
        AUTH_USER_MODEL='users.User',
        USE_TZ=True,
        SIMPLE_JWT={
            "ACCESS_TOKEN_LIFETIME": django.utils.timezone.timedelta(days=1),
            "REFRESH_TOKEN_LIFETIME": django.utils.timezone.timedelta(days=90),
        }
    )

django.setup()

# Now import Django models
from users.models import User
from users.tokens import CustomRefreshToken
import json
import base64

def test_custom_jwt_token():
    """Test that custom JWT tokens contain expected user data"""
    
    # Create a test user
    user = User(
        id=123,
        email='test@example.com',
        username='testuser',
        first_name='John',
        last_name='Doe',
        role='Admin',
        contact_type='primary',
    )
    
    # Generate custom token
    refresh_token = CustomRefreshToken.for_user(user)
    access_token = refresh_token.access_token
    
    print("🔧 Testing Custom JWT Token Implementation")
    print("=" * 50)
    
    # Decode token payload manually (for testing only)
    token_parts = str(access_token).split('.')
    if len(token_parts) >= 2:
        # Decode the payload
        payload_encoded = token_parts[1]
        # Add padding if necessary
        payload_encoded += '=' * (4 - len(payload_encoded) % 4)
        
        try:
            payload_decoded = base64.b64decode(payload_encoded)
            payload_json = json.loads(payload_decoded)
            
            print("📋 JWT Payload Contents:")
            print("-" * 30)
            for key, value in payload_json.items():
                print(f"  {key}: {value}")
            
            print("\n✅ Expected Fields Check:")
            print("-" * 30)
            expected_fields = [
                'user_id', 'email', 'username', 'first_name', 
                'last_name', 'role', 'contact_type'
            ]
            
            for field in expected_fields:
                if field in payload_json:
                    print(f"  ✓ {field}: {payload_json[field]}")
                else:
                    print(f"  ❌ {field}: MISSING")
                    
            # Check company fields (should be null for test user)
            company_fields = ['company_id', 'company_name']
            print(f"\n🏢 Company Fields:")
            print("-" * 30)
            for field in company_fields:
                if field in payload_json:
                    print(f"  ✓ {field}: {payload_json[field]}")
                else:
                    print(f"  ❌ {field}: MISSING")
            
            print(f"\n🎫 Token Details:")
            print("-" * 30)
            print(f"  Token Type: {payload_json.get('token_type', 'N/A')}")
            print(f"  Expires: {payload_json.get('exp', 'N/A')}")
            print(f"  Issued At: {payload_json.get('iat', 'N/A')}")
            
        except Exception as e:
            print(f"❌ Error decoding token: {e}")
    
    print(f"\n🔑 Tokens Generated:")
    print("-" * 30)
    print(f"Access Token Length: {len(str(access_token))} chars")
    print(f"Refresh Token Length: {len(str(refresh_token))} chars")
    print(f"Access Token: {str(access_token)[:50]}...")
    
    return access_token, refresh_token

if __name__ == "__main__":
    test_custom_jwt_token()