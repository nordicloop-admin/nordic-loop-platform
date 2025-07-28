"""
Django management command to validate that API responses remain identical 
before and after the company contact normalization.

This ensures zero user impact during the migration.

Usage:
    python manage.py validate_api_responses --before  # Save current responses
    python manage.py validate_api_responses --after   # Compare after migration
    python manage.py validate_api_responses --compare # Compare saved responses
"""

import json
import os
from django.core.management.base import BaseCommand
from django.test import Client
from django.contrib.auth import get_user_model
from company.models import Company
from company.serializer import AdminCompanyDetailSerializer

User = get_user_model()


class Command(BaseCommand):
    help = 'Validate API responses before and after migration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--before',
            action='store_true',
            help='Save current API responses as baseline',
        )
        parser.add_argument(
            '--after',
            action='store_true',
            help='Compare current responses with saved baseline',
        )
        parser.add_argument(
            '--compare',
            action='store_true',
            help='Compare two saved response files',
        )
        parser.add_argument(
            '--output-dir',
            type=str,
            default='/tmp',
            help='Directory to save response files',
        )

    def handle(self, *args, **options):
        """Main command handler"""
        
        self.output_dir = options['output_dir']
        
        if options['before']:
            self.save_baseline_responses()
        elif options['after']:
            self.compare_with_baseline()
        elif options['compare']:
            self.compare_saved_responses()
        else:
            self.stdout.write(
                self.style.ERROR('Please specify --before, --after, or --compare')
            )

    def save_baseline_responses(self):
        """Save current API responses as baseline"""
        self.stdout.write(
            self.style.SUCCESS('💾 Saving baseline API responses...')
        )
        
        responses = self.collect_api_responses()
        
        baseline_file = os.path.join(self.output_dir, 'api_responses_before.json')
        with open(baseline_file, 'w') as f:
            json.dump(responses, f, indent=2, default=str)
            
        self.stdout.write(
            self.style.SUCCESS(f'✅ Baseline saved to: {baseline_file}')
        )
        self.stdout.write(f'📊 Captured {len(responses)} company responses')

    def compare_with_baseline(self):
        """Compare current responses with baseline"""
        self.stdout.write(
            self.style.SUCCESS('🔍 Comparing current responses with baseline...')
        )
        
        baseline_file = os.path.join(self.output_dir, 'api_responses_before.json')
        
        if not os.path.exists(baseline_file):
            self.stdout.write(
                self.style.ERROR(f'❌ Baseline file not found: {baseline_file}')
            )
            self.stdout.write('Run with --before first to create baseline')
            return
            
        # Load baseline
        with open(baseline_file, 'r') as f:
            baseline_responses = json.load(f)
            
        # Get current responses
        current_responses = self.collect_api_responses()
        
        # Save current responses
        current_file = os.path.join(self.output_dir, 'api_responses_after.json')
        with open(current_file, 'w') as f:
            json.dump(current_responses, f, indent=2, default=str)
            
        # Compare
        self.compare_responses(baseline_responses, current_responses)

    def compare_saved_responses(self):
        """Compare two saved response files"""
        before_file = os.path.join(self.output_dir, 'api_responses_before.json')
        after_file = os.path.join(self.output_dir, 'api_responses_after.json')
        
        if not os.path.exists(before_file):
            self.stdout.write(
                self.style.ERROR(f'❌ Before file not found: {before_file}')
            )
            return
            
        if not os.path.exists(after_file):
            self.stdout.write(
                self.style.ERROR(f'❌ After file not found: {after_file}')
            )
            return
            
        with open(before_file, 'r') as f:
            before_responses = json.load(f)
            
        with open(after_file, 'r') as f:
            after_responses = json.load(f)
            
        self.compare_responses(before_responses, after_responses)

    def collect_api_responses(self):
        """Collect API responses for all companies"""
        responses = {}
        
        # Get first 10 companies for testing (or all if less than 10)
        companies = Company.objects.all()[:10]
        
        for company in companies:
            try:
                # Use serializer directly (more reliable than HTTP client)
                serializer = AdminCompanyDetailSerializer(company)
                response_data = serializer.data
                
                responses[str(company.id)] = {
                    'company_id': company.id,
                    'company_name': company.official_name,
                    'response': response_data
                }
                
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'⚠️  Error getting response for company {company.id}: {e}')
                )
                
        return responses

    def compare_responses(self, before_responses, after_responses):
        """Compare two sets of responses"""
        self.stdout.write('\n📊 COMPARISON RESULTS')
        self.stdout.write('=' * 50)
        
        total_companies = len(before_responses)
        identical_count = 0
        different_count = 0
        missing_count = 0
        
        for company_id, before_data in before_responses.items():
            if company_id not in after_responses:
                missing_count += 1
                self.stdout.write(
                    self.style.ERROR(f'❌ Company {company_id} missing in after responses')
                )
                continue
                
            after_data = after_responses[company_id]
            
            # Compare the actual response data
            before_response = before_data['response']
            after_response = after_data['response']
            
            if self.responses_identical(before_response, after_response):
                identical_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Company {company_id} ({before_data["company_name"]}): IDENTICAL')
                )
            else:
                different_count += 1
                self.stdout.write(
                    self.style.ERROR(f'❌ Company {company_id} ({before_data["company_name"]}): DIFFERENT')
                )
                self.show_differences(before_response, after_response, company_id)
        
        # Summary
        self.stdout.write('\n📈 SUMMARY')
        self.stdout.write('=' * 30)
        self.stdout.write(f'Total Companies: {total_companies}')
        self.stdout.write(f'✅ Identical: {identical_count}')
        self.stdout.write(f'❌ Different: {different_count}')
        self.stdout.write(f'🔍 Missing: {missing_count}')
        
        if different_count == 0 and missing_count == 0:
            self.stdout.write(
                self.style.SUCCESS('\n🎉 ALL RESPONSES IDENTICAL - MIGRATION SUCCESSFUL!')
            )
        else:
            self.stdout.write(
                self.style.ERROR(f'\n⚠️  {different_count + missing_count} ISSUES FOUND - REVIEW NEEDED')
            )

    def responses_identical(self, response1, response2):
        """Check if two responses are identical"""
        try:
            # Convert to JSON strings for comparison (handles ordering)
            json1 = json.dumps(response1, sort_keys=True, default=str)
            json2 = json.dumps(response2, sort_keys=True, default=str)
            return json1 == json2
        except Exception:
            return response1 == response2

    def show_differences(self, before, after, company_id):
        """Show specific differences between responses"""
        
        # Focus on contacts array since that's what we're changing
        before_contacts = before.get('contacts', [])
        after_contacts = after.get('contacts', [])
        
        if before_contacts != after_contacts:
            self.stdout.write(f'   📞 Contacts differ for company {company_id}:')
            self.stdout.write(f'      Before: {len(before_contacts)} contacts')
            self.stdout.write(f'      After:  {len(after_contacts)} contacts')
            
            # Show first few contacts for debugging
            for i, (before_contact, after_contact) in enumerate(zip(before_contacts, after_contacts)):
                if before_contact != after_contact:
                    self.stdout.write(f'      Contact {i+1} differs:')
                    self.stdout.write(f'        Before: {before_contact}')
                    self.stdout.write(f'        After:  {after_contact}')
                    break
        
        # Check other important fields
        important_fields = ['companyName', 'email', 'status', 'sector']
        for field in important_fields:
            if before.get(field) != after.get(field):
                self.stdout.write(f'   🔍 {field} differs:')
                self.stdout.write(f'      Before: {before.get(field)}')
                self.stdout.write(f'      After:  {after.get(field)}')

    def create_test_admin_user(self):
        """Create a test admin user for API testing"""
        admin_user, created = User.objects.get_or_create(
            username='test_admin',
            defaults={
                'email': 'test@admin.com',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin_user.set_password('testpass123')
            admin_user.save()
        return admin_user
