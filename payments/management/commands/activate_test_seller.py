"""
Management command to activate test seller account for payment testing
This bypasses the normal verification process for testing purposes only
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from users.models import User
from payments.models import StripeAccount
from notifications.models import Notification
import stripe
from django.conf import settings

class Command(BaseCommand):
    help = 'Activate test seller account for payment testing (bypasses verification)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            default='karera@gmail.com',
            help='Email of the seller to activate (default: karera@gmail.com)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force activation even if account is already active'
        )

    def handle(self, *args, **options):
        email = options['email']
        force = options['force']
        
        self.stdout.write(self.style.SUCCESS(f'🚀 Activating test seller account: {email}'))
        
        try:
            # Get the user
            user = User.objects.get(email=email)
            self.stdout.write(f'✅ Found user: {user.email}')
            
            # Get or create Stripe account
            stripe_account, created = StripeAccount.objects.get_or_create(
                user=user,
                defaults={
                    'stripe_account_id': f'acct_test_{user.id}_{int(timezone.now().timestamp())}',
                    'account_status': 'active',
                    'bank_account_last4': '0003',
                    'bank_name': 'Svenska Handelsbanken',
                    'bank_country': 'SE',
                    'charges_enabled': True,
                    'payouts_enabled': True,
                }
            )
            
            if created:
                self.stdout.write('✅ Created new Stripe account')
            else:
                self.stdout.write('✅ Found existing Stripe account')
                
            # Check current status
            self.stdout.write(f'📊 Current Status:')
            self.stdout.write(f'   Account Status: {stripe_account.account_status}')
            self.stdout.write(f'   Charges Enabled: {stripe_account.charges_enabled}')
            self.stdout.write(f'   Payouts Enabled: {stripe_account.payouts_enabled}')
            self.stdout.write(f'   Stripe Account ID: {stripe_account.stripe_account_id}')
            
            # Activate if needed
            if stripe_account.account_status != 'active' or not stripe_account.charges_enabled or not stripe_account.payouts_enabled or force:
                self.stdout.write('🔧 Activating account capabilities...')
                
                # Update account to active status with all capabilities
                stripe_account.account_status = 'active'
                stripe_account.charges_enabled = True
                stripe_account.payouts_enabled = True
                stripe_account.updated_at = timezone.now()
                stripe_account.save()
                
                self.stdout.write('✅ Account activated successfully!')
                
                # Create notification for user
                try:
                    Notification.objects.create(
                        user=user,
                        title="Payment Account Activated (Test)",
                        message="Your test payment account has been activated and you can now receive payments from sales. This is a test activation for development purposes.",
                        type='account',
                        priority='normal',
                        metadata={
                            'stripe_account_id': stripe_account.stripe_account_id,
                            'account_status': 'active',
                            'test_activation': True
                        }
                    )
                    self.stdout.write('✅ Created activation notification')
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'⚠️  Could not create notification: {str(e)}'))
                
            else:
                self.stdout.write('✅ Account is already active with all capabilities')
            
            # Verify final status
            stripe_account.refresh_from_db()
            self.stdout.write(f'\n📊 Final Status:')
            self.stdout.write(f'   Account Status: {stripe_account.account_status}')
            self.stdout.write(f'   Charges Enabled: {stripe_account.charges_enabled}')
            self.stdout.write(f'   Payouts Enabled: {stripe_account.payouts_enabled}')
            
            # Test payment capability
            self.test_payment_capability(stripe_account)
            
            self.stdout.write(self.style.SUCCESS(f'\n🎉 Test seller account activation completed!'))
            self.stdout.write(f'📧 Account: {email}')
            self.stdout.write(f'🔑 Password: CMU@2025')
            self.stdout.write(f'💳 Stripe Account: {stripe_account.stripe_account_id}')
            self.stdout.write(f'✅ Ready for payment testing!')
            
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'❌ User {email} not found!'))
            self.stdout.write('Available users:')
            for user in User.objects.all()[:10]:
                self.stdout.write(f'   - {user.email}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {str(e)}'))
            import traceback
            self.stdout.write(traceback.format_exc())

    def test_payment_capability(self, stripe_account):
        """Test if the account can receive payments"""
        self.stdout.write('\n🧪 Testing payment capability...')
        
        # Check if account has required capabilities
        required_capabilities = ['charges_enabled', 'payouts_enabled']
        missing_capabilities = []
        
        if not stripe_account.charges_enabled:
            missing_capabilities.append('charges_enabled')
        if not stripe_account.payouts_enabled:
            missing_capabilities.append('payouts_enabled')
            
        if missing_capabilities:
            self.stdout.write(self.style.WARNING(f'⚠️  Missing capabilities: {", ".join(missing_capabilities)}'))
            return False
        
        # Check account status
        if stripe_account.account_status != 'active':
            self.stdout.write(self.style.WARNING(f'⚠️  Account status is not active: {stripe_account.account_status}'))
            return False
            
        self.stdout.write('✅ Payment capability test passed!')
        self.stdout.write('   ✓ Charges enabled')
        self.stdout.write('   ✓ Payouts enabled') 
        self.stdout.write('   ✓ Account status active')
        
        return True
