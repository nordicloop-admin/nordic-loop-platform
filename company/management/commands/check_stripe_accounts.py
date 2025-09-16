"""
Management command to check Stripe accounts stored in the database
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from company.models import Company
from users.models import User

class Command(BaseCommand):
    help = 'Check Stripe accounts stored in the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--detailed',
            action='store_true',
            help='Show detailed information about each account',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('=== Stripe Account Database Check ===\n')
        )

        # Get all companies with Stripe accounts
        companies_with_stripe = Company.objects.filter(
            stripe_account_id__isnull=False
        ).order_by('registration_date')

        if not companies_with_stripe.exists():
            self.stdout.write(
                self.style.WARNING('No companies with Stripe accounts found in database.')
            )
            return

        self.stdout.write(f'Found {companies_with_stripe.count()} companies with Stripe accounts:\n')

        for i, company in enumerate(companies_with_stripe, 1):
            # Basic info
            self.stdout.write(f'{i}. Company: {company.official_name}')
            self.stdout.write(f'   Stripe Account ID: {company.stripe_account_id}')
            self.stdout.write(f'   Status: {company.status}')
            self.stdout.write(f'   Payment Ready: {company.payment_ready}')
            
            if options['detailed']:
                # Detailed info
                self.stdout.write(f'   VAT Number: {company.vat_number}')
                self.stdout.write(f'   Email: {company.email}')
                self.stdout.write(f'   Country: {company.country}')
                self.stdout.write(f'   Sector: {company.sector}')
                self.stdout.write(f'   Registration Date: {company.registration_date}')
                self.stdout.write(f'   Stripe Onboarding Complete: {company.stripe_onboarding_complete}')
                self.stdout.write(f'   Stripe Capabilities Complete: {company.stripe_capabilities_complete}')
                self.stdout.write(f'   Last Payment Check: {company.last_payment_check or "Never"}')
                
                # Get associated users
                users = User.objects.filter(company=company)
                if users.exists():
                    self.stdout.write(f'   Associated Users: {", ".join([u.email for u in users])}')
                else:
                    self.stdout.write('   Associated Users: None')
            
            self.stdout.write('')  # Empty line

        # Summary statistics
        self.stdout.write(self.style.SUCCESS('=== Summary Statistics ==='))
        total_companies = Company.objects.count()
        companies_payment_ready = companies_with_stripe.filter(payment_ready=True).count()
        companies_onboarding_complete = companies_with_stripe.filter(stripe_onboarding_complete=True).count()
        
        self.stdout.write(f'Total Companies: {total_companies}')
        self.stdout.write(f'Companies with Stripe Accounts: {companies_with_stripe.count()}')
        self.stdout.write(f'Companies Payment Ready: {companies_payment_ready}')
        self.stdout.write(f'Companies Onboarding Complete: {companies_onboarding_complete}')
        
        if companies_with_stripe.count() > 0:
            percentage = (companies_payment_ready / companies_with_stripe.count()) * 100
            self.stdout.write(f'Payment Ready Percentage: {percentage:.1f}%')

        self.stdout.write(
            self.style.SUCCESS(f'\nCommand completed at {timezone.now()}')
        )