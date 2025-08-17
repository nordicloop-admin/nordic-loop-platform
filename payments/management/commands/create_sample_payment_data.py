from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
import random
from datetime import datetime, timedelta

from users.models import User
from bids.models import Bid
from ads.models import Subscription
from payments.models import StripeAccount, PaymentIntent, Transaction, PayoutSchedule


class Command(BaseCommand):
    help = 'Create realistic sample payment data based on existing bids'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-email',
            type=str,
            default='karera@gmail.com',
            help='Email of the user to preserve (default: karera@gmail.com)'
        )

    def handle(self, *args, **options):
        preserve_user_email = options['user_email']
        
        self.stdout.write(self.style.SUCCESS('Creating sample payment data...'))
        
        # Get existing bids with 'won' status
        winning_bids = Bid.objects.filter(status='won')
        
        if not winning_bids.exists():
            # Create some sample winning bids first
            self.create_sample_winning_bids()
            winning_bids = Bid.objects.filter(status='won')
        
        # Create Stripe accounts for sellers
        self.create_stripe_accounts(preserve_user_email)
        
        # Create payment intents and transactions for winning bids
        self.create_payment_data(winning_bids)
        
        # Create payout schedules
        self.create_payout_schedules()
        
        self.stdout.write(self.style.SUCCESS('Sample payment data created successfully!'))

    def create_sample_winning_bids(self):
        """Create some sample winning bids if none exist"""
        self.stdout.write('Creating sample winning bids...')
        
        # Get some existing bids and mark them as won
        existing_bids = Bid.objects.filter(status='active')[:5]
        
        for bid in existing_bids:
            bid.status = 'won'
            bid.save()
            self.stdout.write(f'  - Marked bid {bid.id} as won')

    def create_stripe_accounts(self, preserve_user_email):
        """Create Stripe accounts for sellers"""
        self.stdout.write('Creating Stripe accounts for sellers...')
        
        # Get all users who have ads (potential sellers)
        sellers = User.objects.filter(ads__isnull=False).distinct()
        
        for seller in sellers:
            if seller.email == preserve_user_email:
                continue  # Skip the preserved user
                
            stripe_account, created = StripeAccount.objects.get_or_create(
                user=seller,
                defaults={
                    'stripe_account_id': f'acct_test_{seller.id}_{random.randint(1000, 9999)}',
                    'account_status': random.choice(['active', 'pending', 'restricted']),
                    'bank_account_last4': str(random.randint(1000, 9999)),
                    'bank_name': random.choice(['Swedbank', 'SEB', 'Nordea', 'Handelsbanken']),
                    'bank_country': 'SE',
                    'charges_enabled': True,
                    'payouts_enabled': random.choice([True, False]),
                }
            )
            
            if created:
                self.stdout.write(f'  - Created Stripe account for {seller.email}')

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

    def create_payment_data(self, winning_bids):
        """Create payment intents and transactions for winning bids"""
        self.stdout.write('Creating payment data for winning bids...')
        
        for bid in winning_bids:
            # Skip if payment intent already exists
            if hasattr(bid, 'payment_intent'):
                continue
                
            buyer = bid.user
            seller = bid.ad.user
            
            # Skip if seller doesn't have Stripe account
            if not hasattr(seller, 'stripe_account'):
                continue
            
            # Calculate amounts
            total_amount = bid.bid_price_per_unit * bid.volume_requested
            commission_rate = self.get_commission_rate(buyer)
            commission_amount = (total_amount * commission_rate / 100).quantize(Decimal('0.01'))
            seller_amount = total_amount - commission_amount
            
            # Create payment intent
            payment_intent = PaymentIntent.objects.create(
                stripe_payment_intent_id=f'pi_test_{bid.id}_{random.randint(100000, 999999)}',
                bid=bid,
                buyer=buyer,
                seller=seller,
                total_amount=total_amount,
                commission_amount=commission_amount,
                seller_amount=seller_amount,
                commission_rate=commission_rate,
                status='succeeded',
                currency='SEK',
                confirmed_at=timezone.now() - timedelta(days=random.randint(1, 30))
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
            
            self.stdout.write(f'  - Created payment data for bid {bid.id} ({total_amount} SEK)')

    def create_payout_schedules(self):
        """Create payout schedules for sellers with pending transactions"""
        self.stdout.write('Creating payout schedules...')
        
        # Get sellers with pending payout transactions
        pending_transactions = Transaction.objects.filter(
            transaction_type='payout',
            status='pending'
        ).select_related('to_user')
        
        # Group by seller
        seller_payouts = {}
        for transaction in pending_transactions:
            seller = transaction.to_user
            if seller.id not in seller_payouts:
                seller_payouts[seller.id] = {
                    'seller': seller,
                    'transactions': [],
                    'total_amount': Decimal('0.00')
                }
            
            seller_payouts[seller.id]['transactions'].append(transaction)
            seller_payouts[seller.id]['total_amount'] += transaction.amount
        
        # Create payout schedules
        admin_user = User.objects.filter(is_staff=True).first()
        
        for seller_data in seller_payouts.values():
            # Create some completed payouts (past)
            if random.choice([True, False]):
                completed_schedule = PayoutSchedule.objects.create(
                    seller=seller_data['seller'],
                    total_amount=seller_data['total_amount'] * Decimal('0.6'),  # 60% of total
                    currency='SEK',
                    status='completed',
                    scheduled_date=timezone.now().date() - timedelta(days=random.randint(7, 30)),
                    processed_date=timezone.now().date() - timedelta(days=random.randint(1, 7)),
                    stripe_payout_id=f'po_test_{random.randint(100000, 999999)}',
                    created_by=admin_user,
                    processed_by=admin_user,
                    notes='Monthly payout batch'
                )
                self.stdout.write(f'  - Created completed payout schedule for {seller_data["seller"].email}')
            
            # Create scheduled payout (future)
            if random.choice([True, False, True]):  # 66% chance
                scheduled_schedule = PayoutSchedule.objects.create(
                    seller=seller_data['seller'],
                    total_amount=seller_data['total_amount'] * Decimal('0.4'),  # Remaining 40%
                    currency='SEK',
                    status='scheduled',
                    scheduled_date=timezone.now().date() + timedelta(days=random.randint(1, 14)),
                    created_by=admin_user,
                    notes='Upcoming payout batch'
                )
                
                # Link some transactions to this schedule
                transactions_to_link = seller_data['transactions'][:2]  # Link first 2 transactions
                scheduled_schedule.transactions.set(transactions_to_link)
                
                self.stdout.write(f'  - Created scheduled payout for {seller_data["seller"].email}')
            
            # Create some overdue payouts
            if random.choice([True, False, False]):  # 33% chance
                overdue_schedule = PayoutSchedule.objects.create(
                    seller=seller_data['seller'],
                    total_amount=seller_data['total_amount'] * Decimal('0.2'),
                    currency='SEK',
                    status='scheduled',
                    scheduled_date=timezone.now().date() - timedelta(days=random.randint(1, 5)),
                    created_by=admin_user,
                    notes='Overdue payout - needs attention'
                )
                self.stdout.write(f'  - Created overdue payout for {seller_data["seller"].email}')

        self.stdout.write(self.style.SUCCESS('Payment data creation completed!'))
