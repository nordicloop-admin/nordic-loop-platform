#!/usr/bin/env python3

import os
import django
from pathlib import Path
import secrets
import string

# Setup Django
BASE_DIR = Path(__file__).resolve().parent
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import sys
sys.path.append(str(BASE_DIR))

django.setup()

from users.models import User
from django.contrib.auth.hashers import make_password

def generate_secure_password(length=12):
    """Generate a secure random password"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for i in range(length))
    return password

def reset_passwords_for_users_with_missing_images():
    """Reset passwords for users who have ads without images"""
    
    print('🔐 RESETTING PASSWORDS FOR USERS WITH ADS MISSING IMAGES')
    print('=' * 70)
    
    # The 3 users we identified with ads missing images
    target_usernames = ['annapettersson', 'eriklundberg', 'mariaandersson']
    
    reset_credentials = []
    
    for username in target_usernames:
        try:
            user = User.objects.get(username=username)
            
            # Generate a new secure password
            new_password = generate_secure_password(12)
            
            # Set the new password
            user.set_password(new_password)
            user.save()
            
            # Store credentials for display
            reset_credentials.append({
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': user.name or f"{user.first_name} {user.last_name}".strip() or "Not provided",
                'company': user.company.official_name if user.company else "No company",
                'new_password': new_password
            })
            
            print(f'✅ Password reset successful for: {username}')
            
        except User.DoesNotExist:
            print(f'❌ User not found: {username}')
        except Exception as e:
            print(f'❌ Error resetting password for {username}: {e}')
    
    print('\n' + '=' * 70)
    print('🔑 NEW LOGIN CREDENTIALS')
    print('=' * 70)
    
    for cred in reset_credentials:
        print(f'\n👤 USER: {cred["full_name"]}')
        print(f'   Company: {cred["company"]}')
        print(f'   Username: {cred["username"]}')
        print(f'   Email: {cred["email"]}')
        print(f'   New Password: {cred["new_password"]}')
        print(f'   User ID: {cred["user_id"]}')
        print('-' * 50)
    
    print(f'\n📋 SUMMARY:')
    print(f'   Total passwords reset: {len(reset_credentials)}')
    print(f'   Users can now log in with their new passwords')
    print(f'   Recommend they change passwords after first login')
    
    return reset_credentials

def reset_password_for_specific_user(username_or_email):
    """Reset password for a specific user by username or email"""
    
    try:
        # Try to find user by username first, then by email
        try:
            user = User.objects.get(username=username_or_email)
        except User.DoesNotExist:
            user = User.objects.get(email=username_or_email)
        
        # Generate a new secure password
        new_password = generate_secure_password(12)
        
        # Set the new password
        user.set_password(new_password)
        user.save()
        
        print(f'✅ Password reset successful!')
        print(f'   Username: {user.username}')
        print(f'   Email: {user.email}')
        print(f'   New Password: {new_password}')
        
        return {
            'username': user.username,
            'email': user.email,
            'new_password': new_password
        }
        
    except User.DoesNotExist:
        print(f'❌ User not found: {username_or_email}')
        return None
    except Exception as e:
        print(f'❌ Error resetting password: {e}')
        return None

def show_all_user_login_status():
    """Show login status for all users"""
    print('\n\n👥 ALL USERS LOGIN STATUS')
    print('=' * 70)
    
    users = User.objects.all().order_by('id')
    
    for user in users:
        print(f'\n👤 {user.username} (ID: {user.id})')
        print(f'   Email: {user.email}')
        print(f'   Name: {user.name or "Not provided"}')
        print(f'   Company: {user.company.official_name if user.company else "No company"}')
        print(f'   Is Active: {user.is_active}')
        print(f'   Can Place Ads: {user.can_place_ads}')
        print(f'   Last Login: {user.last_login.strftime("%Y-%m-%d %H:%M") if user.last_login else "Never"}')
        print(f'   Password Set: {"Yes" if user.password else "No"}')
        print('-' * 40)

if __name__ == '__main__':
    import sys
    
    try:
        if len(sys.argv) > 1:
            # Reset password for specific user
            username_or_email = sys.argv[1]
            print(f'🔐 RESETTING PASSWORD FOR: {username_or_email}')
            print('=' * 50)
            reset_password_for_specific_user(username_or_email)
        else:
            # Reset passwords for all users with missing image ads
            reset_passwords_for_users_with_missing_images()
            show_all_user_login_status()
            
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc() 