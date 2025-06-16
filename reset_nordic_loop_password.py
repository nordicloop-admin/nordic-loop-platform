#!/usr/bin/env python3

import os
import django
from pathlib import Path

# Setup Django
BASE_DIR = Path(__file__).resolve().parent
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import sys
sys.path.append(str(BASE_DIR))

django.setup()

from users.models import User

def reset_nordic_loop_ceo_password():
    """Reset Nordic Loop CEO password to specific value"""
    
    print("🔐 Resetting Nordic Loop CEO Password...")
    print("=" * 50)
    
    # New password
    new_password = "NordicFounder@2025"
    email = "rahimianshaya@gmail.com"
    
    try:
        # Find the user
        user = User.objects.get(email=email)
        
        print(f"👤 Found user: {user.username}")
        print(f"   Email: {user.email}")
        print(f"   Full Name: {user.first_name} {user.last_name}")
        print(f"   Company: {user.company.official_name if user.company else 'No company'}")
        
        # Reset the password
        user.set_password(new_password)
        user.save()
        
        print(f"\n✅ Password reset successful!")
        print(f"   New Password: {new_password}")
        
        print("\n" + "=" * 50)
        print("🎉 Password Reset Complete!")
        print("\n📋 UPDATED LOGIN CREDENTIALS:")
        print(f"   Username: {user.username}")
        print(f"   Email: {user.email}")
        print(f"   Password: {new_password}")
        
        # Update credentials file
        credentials_content = f"""
Nordic Loop CEO Login Credentials (UPDATED)
==========================================
Username: {user.username}
Email: {user.email}
Password: {new_password}
Role: CEO & Founder
Company: {user.company.official_name if user.company else 'No company'}
Website: {user.company.website if user.company else 'N/A'}
Last Updated: {user.date_joined.strftime('%Y-%m-%d %H:%M:%S') if hasattr(user, 'date_joined') else 'N/A'}
"""
        
        with open('nordic_loop_credentials.txt', 'w') as f:
            f.write(credentials_content)
        print(f"\n💾 Updated credentials saved to: nordic_loop_credentials.txt")
        
        return True
        
    except User.DoesNotExist:
        print(f"❌ User not found with email: {email}")
        print("   Please make sure the user exists first.")
        return False
        
    except Exception as e:
        print(f"❌ Error resetting password: {e}")
        return False

if __name__ == "__main__":
    success = reset_nordic_loop_ceo_password()
    
    if success:
        print("\n✅ Password reset completed successfully!")
    else:
        print("\n❌ Password reset failed!") 