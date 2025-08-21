#!/usr/bin/env python
"""
Webhook Secret Configuration Helper

This script helps configure the Stripe webhook secret for development and production.
For development, it can generate a test webhook secret that bypasses signature verification.
For production, it guides you through setting up the real webhook secret.
"""

import os
import sys
import secrets
import string

def generate_test_webhook_secret():
    """Generate a test webhook secret for development"""
    # Generate a random string that looks like a Stripe webhook secret
    random_part = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
    return f"whsec_test_{random_part}"

def update_env_file(webhook_secret):
    """Update the .env file with the new webhook secret"""
    env_file_path = '.env'
    
    if not os.path.exists(env_file_path):
        print(f"❌ .env file not found at {env_file_path}")
        return False
    
    # Read current .env file
    with open(env_file_path, 'r') as f:
        lines = f.readlines()
    
    # Update the webhook secret line
    updated = False
    for i, line in enumerate(lines):
        if line.startswith('STRIPE_WEBHOOK_SECRET='):
            lines[i] = f'STRIPE_WEBHOOK_SECRET={webhook_secret}\n'
            updated = True
            break
    
    if not updated:
        # Add the webhook secret if it doesn't exist
        lines.append(f'STRIPE_WEBHOOK_SECRET={webhook_secret}\n')
    
    # Write back to .env file
    with open(env_file_path, 'w') as f:
        f.writelines(lines)
    
    print(f"✅ Updated .env file with webhook secret")
    return True

def create_development_webhook_bypass():
    """Create a development webhook configuration that bypasses signature verification"""
    print("🧪 Setting up development webhook configuration...")
    
    # For development, we'll modify the webhook handler to accept a test secret
    webhook_file_path = 'payments/webhooks.py'
    
    if not os.path.exists(webhook_file_path):
        print(f"❌ Webhook file not found at {webhook_file_path}")
        return False
    
    # Read the webhook file
    with open(webhook_file_path, 'r') as f:
        content = f.read()
    
    # Check if development bypass is already in place
    if 'DEVELOPMENT_WEBHOOK_BYPASS' in content:
        print("✅ Development webhook bypass already configured")
        return True
    
    # Add development bypass
    bypass_code = '''
# Development webhook bypass
DEVELOPMENT_WEBHOOK_BYPASS = getattr(settings, 'DJANGO_DEBUG', False) and endpoint_secret.startswith('whsec_test_')

if DEVELOPMENT_WEBHOOK_BYPASS:
    # For development with test webhook secret, skip signature verification
    try:
        event = json.loads(payload.decode('utf-8'))
        # Add a mock event structure if needed
        if 'type' not in event:
            event = {
                'type': 'payment_intent.succeeded',
                'data': {'object': event}
            }
    except json.JSONDecodeError:
        logger.error("Invalid JSON payload in development webhook")
        return HttpResponseBadRequest("Invalid JSON payload")
else:
    # Production webhook signature verification
'''
    
    # Replace the signature verification section
    old_verification = '''    try:
        # Verify webhook signature
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError:
        logger.error("Invalid payload in Stripe webhook")
        return HttpResponseBadRequest("Invalid payload")
    except stripe.error.SignatureVerificationError:
        logger.error("Invalid signature in Stripe webhook")
        return HttpResponseBadRequest("Invalid signature")'''
    
    new_verification = bypass_code + '''        try:
            # Verify webhook signature
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        except ValueError:
            logger.error("Invalid payload in Stripe webhook")
            return HttpResponseBadRequest("Invalid payload")
        except stripe.error.SignatureVerificationError:
            logger.error("Invalid signature in Stripe webhook")
            return HttpResponseBadRequest("Invalid signature")'''
    
    if old_verification in content:
        content = content.replace(old_verification, new_verification)
        
        # Write back to webhook file
        with open(webhook_file_path, 'w') as f:
            f.write(content)
        
        print("✅ Added development webhook bypass to webhook handler")
        return True
    else:
        print("⚠️  Could not find signature verification section to modify")
        print("   Manual modification may be required")
        return False

def main():
    """Main configuration function"""
    print("🔧 Stripe Webhook Secret Configuration")
    print("=" * 40)
    
    print("\nChoose configuration mode:")
    print("1. Development (generate test secret with bypass)")
    print("2. Production (guide for real webhook secret)")
    print("3. Exit")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice == '1':
        print("\n🧪 Configuring for development...")
        
        # Generate test webhook secret
        test_secret = generate_test_webhook_secret()
        print(f"Generated test webhook secret: {test_secret}")
        
        # Update .env file
        if update_env_file(test_secret):
            print("✅ Development webhook secret configured")
            print("\n📋 Next steps:")
            print("1. Restart your Django development server")
            print("2. Test payment flow")
            print("3. Check that payments complete automatically")
            print("\n⚠️  This configuration is for development only!")
            print("   Use real webhook secret for production")
        
    elif choice == '2':
        print("\n🏭 Production webhook configuration guide...")
        print("\n📋 Steps to configure production webhook:")
        print("1. Go to Stripe Dashboard (https://dashboard.stripe.com)")
        print("2. Navigate to Developers > Webhooks")
        print("3. Click 'Add endpoint' or edit existing endpoint")
        print("4. Set endpoint URL to: https://yourdomain.com/api/payments/webhooks/stripe/")
        print("5. Select these events:")
        print("   - payment_intent.succeeded")
        print("   - payment_intent.payment_failed")
        print("   - account.updated")
        print("   - payout.paid")
        print("   - payout.failed")
        print("6. Click 'Add endpoint'")
        print("7. Copy the 'Signing secret' (starts with whsec_)")
        
        webhook_secret = input("\nPaste your webhook signing secret here: ").strip()
        
        if webhook_secret.startswith('whsec_') and len(webhook_secret) > 20:
            if update_env_file(webhook_secret):
                print("✅ Production webhook secret configured")
                print("\n📋 Next steps:")
                print("1. Deploy your application")
                print("2. Test webhook delivery in Stripe Dashboard")
                print("3. Monitor webhook logs")
        else:
            print("❌ Invalid webhook secret format")
            print("   Webhook secrets should start with 'whsec_'")
    
    elif choice == '3':
        print("👋 Exiting...")
        return
    
    else:
        print("❌ Invalid choice")
        return

if __name__ == "__main__":
    main()
