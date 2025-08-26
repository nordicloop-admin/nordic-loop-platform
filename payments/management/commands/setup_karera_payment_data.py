from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
import random
from datetime import datetime, timedelta

from users.models import User
from bids.models import Bid
from ads.models import Ad, Subscription
from payments.models import StripeAccount, PaymentIntent, Transaction, PayoutSchedule


class Command(BaseCommand):
    help = 'Set up payment data for karera@gmail.com user for testing'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Setting up payment data for karera@gmail.com...'))
        
        try:
            # Get the karera user
            karera_user = User.objects.get(email='karera@gmail.com')
            self.stdout.write(f'Found user: {karera_user.email}')
            
            # Create Stripe account for karera (as a seller)
            self.create_stripe_account_for_karera(karera_user)
            
            # Create some sample ads and bids for testing
            self.create_sample_data_for_testing(karera_user)
            
            # Create payment data
            self.create_payment_transactions(karera_user)
            
            # Create payout schedules
            self.create_payout_schedules_for_karera(karera_user)
            
            self.stdout.write(self.style.SUCCESS('Payment data setup completed for karera@gmail.com!'))
            
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('User karera@gmail.com not found!'))
            return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))

    def create_stripe_account_for_karera(self, user):
        """Create Stripe account for karera user"""
        stripe_account, created = StripeAccount.objects.get_or_create(
            user=user,
            defaults={
                'stripe_account_id': f'acct_test_karera_{random.randint(1000, 9999)}',
                'account_status': 'active',
                'bank_account_last4': '1234',
                'bank_name': 'Swedbank',
                'bank_country': 'SE',
                'charges_enabled': True,
                'payouts_enabled': True,
            }
        )
        
        if created:
            self.stdout.write('  ✓ Created Stripe account for karera@gmail.com')
        else:
            self.stdout.write('  ✓ Stripe account already exists for karera@gmail.com')

    def create_sample_data_for_testing(self, karera_user):
        """Create sample ads and bids for testing"""
        
        # Create some other test users if they don't exist
        test_buyers = []
        for i in range(3):
            buyer_email = f'buyer{i+1}@test.com'
            buyer, created = User.objects.get_or_create(
                email=buyer_email,
                defaults={
                    'username': f'buyer{i+1}',
                    'first_name': f'Buyer{i+1}',
                    'last_name': 'Test',
                    'company': karera_user.company,  # Use same company
                    'can_place_bids': True,
                }
            )
            test_buyers.append(buyer)
            if created:
                self.stdout.write(f'  ✓ Created test buyer: {buyer_email}')

        # Create sample ads for karera (as seller)
        sample_ads_data = [
            {
                'title': 'High-Quality Steel Scrap',
                'description': 'Clean steel scrap from construction project',
                'material_type': 'Steel',
                'quantity': 500,
                'unit': 'kg',
                'location': 'Stockholm, Sweden',
                'starting_price': Decimal('15.00'),
            },
            {
                'title': 'Aluminum Sheets - Industrial Grade',
                'description': 'Unused aluminum sheets from manufacturing',
                'material_type': 'Aluminum',
                'quantity': 200,
                'unit': 'kg',
                'location': 'Gothenburg, Sweden',
                'starting_price': Decimal('25.00'),
            },
            {
                'title': 'Copper Wire Collection',
                'description': 'Various copper wires from electrical work',
                'material_type': 'Copper',
                'quantity': 50,
                'unit': 'kg',
                'location': 'Malmö, Sweden',
                'starting_price': Decimal('45.00'),
            }
        ]

        created_ads = []
        for ad_data in sample_ads_data:
            ad, created = Ad.objects.get_or_create(
                title=ad_data['title'],
                user=karera_user,
                defaults={
                    'description': ad_data['description'],
                    'material_type': ad_data['material_type'],
                    'quantity': ad_data['quantity'],
                    'unit': ad_data['unit'],
                    'location': ad_data['location'],
                    'starting_price': ad_data['starting_price'],
                    'status': 'active',
                    'auction_end_date': timezone.now() - timedelta(days=random.randint(1, 10)),
                }
            )
            created_ads.append(ad)
            if created:
                self.stdout.write(f'  ✓ Created ad: {ad.title}')

        # Create winning bids for these ads
        for i, ad in enumerate(created_ads):
            buyer = test_buyers[i % len(test_buyers)]
            
            # Create a winning bid
            bid, created = Bid.objects.get_or_create(
                ad=ad,
                user=buyer,
                defaults={
                    'bid_price_per_unit': ad.starting_price + Decimal(str(random.randint(5, 20))),
                    'volume_requested': random.randint(50, min(200, ad.quantity)),
                    'status': 'won',
                    'created_at': timezone.now() - timedelta(days=random.randint(1, 5)),
                }
            )
            
            if created:
                self.stdout.write(f'  ✓ Created winning bid for {ad.title} by {buyer.email}')

    def create_payment_transactions(self, karera_user):
        """Create payment transactions for karera's winning bids"""
        
        # Get winning bids where karera is the seller
        winning_bids = Bid.objects.filter(
            ad__user=karera_user,
            status='won'
        )

        for bid in winning_bids:
            # Skip if payment intent already exists
            if hasattr(bid, 'payment_intent'):
                continue

            buyer = bid.user
            seller = karera_user

            # Calculate amounts
            total_amount = bid.bid_price_per_unit * bid.volume_requested
            commission_rate = self.get_commission_rate(buyer)
            commission_amount = (total_amount * commission_rate / 100).quantize(Decimal('0.01'))
            seller_amount = total_amount - commission_amount

            # Create payment intent
            payment_intent = PaymentIntent.objects.create(
                stripe_payment_intent_id=f'pi_test_karera_{bid.id}_{random.randint(100000, 999999)}',
                bid=bid,
                buyer=buyer,
                seller=seller,
                total_amount=total_amount,
                commission_amount=commission_amount,
                seller_amount=seller_amount,
                commission_rate=commission_rate,
                status='succeeded',
                currency='SEK',
                confirmed_at=timezone.now() - timedelta(days=random.randint(1, 15))
            )

            # Create commission transaction
            Transaction.objects.create(
                payment_intent=payment_intent,
                transaction_type='commission',
                amount=commission_amount,
                currency='SEK',
                status='completed',
                from_user=buyer,
                to_user=None,  # Platform commission
                description=f'Commission from payment {payment_intent.stripe_payment_intent_id}',
                processed_at=payment_intent.confirmed_at
            )

            # Create seller transaction (pending payout)
            Transaction.objects.create(
                payment_intent=payment_intent,
                transaction_type='payout',
                amount=seller_amount,
                currency='SEK',
                status='pending',
                from_user=None,  # Platform
                to_user=seller,
                description=f'Seller payout from payment {payment_intent.stripe_payment_intent_id}'
            )

            self.stdout.write(f'  ✓ Created payment for bid {bid.id}: {total_amount} SEK (commission: {commission_amount} SEK)')

    def get_commission_rate(self, user):
        """Get commission rate based on user's subscription"""
        try:
            subscription = Subscription.objects.filter(
                company=user.company,
                status='active'
            ).first()
            
            if subscription:
                plan_rates = {
                    'free': Decimal('9.00'),
                    'standard': Decimal('7.00'),
                    'premium': Decimal('0.00'),
                }
                return plan_rates.get(subscription.plan, Decimal('9.00'))
            else:
                return Decimal('9.00')  # Default to free plan
        except:
            return Decimal('9.00')

    def create_payout_schedules_for_karera(self, karera_user):
        """Create payout schedules for karera"""
        
        # Get pending transactions for karera
        pending_transactions = Transaction.objects.filter(
            to_user=karera_user,
            transaction_type='payout',
            status='pending'
        )

        if not pending_transactions.exists():
            self.stdout.write('  ! No pending transactions found for karera')
            return

        total_pending = sum(t.amount for t in pending_transactions)
        
        # Get admin user (or create one)
        admin_user = User.objects.filter(is_staff=True).first()
        if not admin_user:
            admin_user = karera_user  # Use karera as admin for testing

        # Create a completed payout (past)
        completed_amount = total_pending * Decimal('0.4')  # 40% of total
        completed_schedule = PayoutSchedule.objects.create(
            seller=karera_user,
            total_amount=completed_amount,
            currency='SEK',
            status='completed',
            scheduled_date=timezone.now().date() - timedelta(days=7),
            processed_date=timezone.now().date() - timedelta(days=3),
            stripe_payout_id=f'po_test_karera_{random.randint(100000, 999999)}',
            created_by=admin_user,
            processed_by=admin_user,
            notes='Test payout for karera - completed'
        )
        self.stdout.write(f'  ✓ Created completed payout: {completed_amount} SEK')

        # Create a scheduled payout (future)
        scheduled_amount = total_pending * Decimal('0.4')  # Another 40%
        scheduled_schedule = PayoutSchedule.objects.create(
            seller=karera_user,
            total_amount=scheduled_amount,
            currency='SEK',
            status='scheduled',
            scheduled_date=timezone.now().date() + timedelta(days=5),
            created_by=admin_user,
            notes='Test payout for karera - scheduled'
        )
        
        # Link some transactions to this schedule
        transactions_to_link = list(pending_transactions[:2])
        scheduled_schedule.transactions.set(transactions_to_link)
        self.stdout.write(f'  ✓ Created scheduled payout: {scheduled_amount} SEK')

        # Create an overdue payout
        overdue_amount = total_pending * Decimal('0.2')  # Remaining 20%
        overdue_schedule = PayoutSchedule.objects.create(
            seller=karera_user,
            total_amount=overdue_amount,
            currency='SEK',
            status='scheduled',
            scheduled_date=timezone.now().date() - timedelta(days=2),
            created_by=admin_user,
            notes='Test payout for karera - overdue (for testing)'
        )
        self.stdout.write(f'  ✓ Created overdue payout: {overdue_amount} SEK')

        self.stdout.write(f'  ✓ Total pending amount for karera: {total_pending} SEK')
