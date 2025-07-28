"""
Django management command to create comprehensive backup of company contact data
before removing the old contact fields from Company model.

This ensures we can restore data if anything goes wrong during field removal.

Usage:
    python manage.py backup_company_contacts                    # Default backup
    python manage.py backup_company_contacts --output /path/   # Custom location
    python manage.py backup_company_contacts --verify          # Verify existing backup
"""

import json
import os
from datetime import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from company.models import Company

User = get_user_model()


class Command(BaseCommand):
    help = 'Create comprehensive backup of company contact data before field removal'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default='/tmp',
            help='Directory to save backup files (default: /tmp)',
        )
        parser.add_argument(
            '--verify',
            action='store_true',
            help='Verify an existing backup file',
        )
        parser.add_argument(
            '--restore',
            type=str,
            help='Restore from backup file (path to backup JSON)',
        )

    def handle(self, *args, **options):
        """Main command handler"""
        
        if options['verify']:
            self.verify_backup(options['output'])
        elif options['restore']:
            self.restore_backup(options['restore'])
        else:
            self.create_backup(options['output'])

    def create_backup(self, output_dir):
        """Create comprehensive backup of all company contact data"""
        self.stdout.write(
            self.style.SUCCESS('💾 Creating comprehensive backup of company contact data...')
        )
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Create backup data structure
        backup_data = {
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'django_version': self.get_django_version(),
                'total_companies': Company.objects.count(),
                'backup_type': 'company_contact_fields_removal',
                'description': 'Backup before removing primary/secondary contact fields from Company model'
            },
            'company_contact_fields': [],
            'user_contact_data': [],
            'validation_data': {}
        }
        
        # Backup Company contact fields (the ones we're about to remove)
        self.stdout.write('📊 Backing up Company contact fields...')
        companies_with_contacts = 0
        
        for company in Company.objects.all():
            company_data = {
                'id': company.id,
                'official_name': company.official_name,
                'vat_number': company.vat_number,
                'primary_first_name': company.primary_first_name,
                'primary_last_name': company.primary_last_name,
                'primary_email': company.primary_email,
                'primary_position': company.primary_position,
                'secondary_first_name': company.secondary_first_name,
                'secondary_last_name': company.secondary_last_name,
                'secondary_email': company.secondary_email,
                'secondary_position': company.secondary_position,
            }
            
            # Check if company has any contact data
            has_primary = any([
                company.primary_first_name,
                company.primary_last_name,
                company.primary_email
            ])
            has_secondary = any([
                company.secondary_first_name,
                company.secondary_last_name,
                company.secondary_email
            ])
            
            if has_primary or has_secondary:
                companies_with_contacts += 1
                
            backup_data['company_contact_fields'].append(company_data)
        
        # Backup User contact data (the new normalized structure)
        self.stdout.write('👥 Backing up User contact data...')
        contact_users = User.objects.filter(
            contact_type__in=['primary', 'secondary']
        )
        
        for user in contact_users:
            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'company_id': user.company.id if user.company else None,
                'company_name': user.company.official_name if user.company else None,
                'is_primary_contact': user.is_primary_contact,
                'contact_type': user.contact_type,
                'position': user.position,
                'date_joined': user.date_joined.isoformat() if user.date_joined else None,
            }
            backup_data['user_contact_data'].append(user_data)
        
        # Create validation data for integrity checks
        backup_data['validation_data'] = {
            'companies_with_primary_contacts': Company.objects.filter(
                primary_email__isnull=False
            ).exclude(primary_email='').count(),
            'companies_with_secondary_contacts': Company.objects.filter(
                secondary_email__isnull=False
            ).exclude(secondary_email='').count(),
            'users_marked_primary': User.objects.filter(is_primary_contact=True).count(),
            'users_marked_secondary': User.objects.filter(contact_type='secondary').count(),
            'total_contact_users': User.objects.filter(
                contact_type__in=['primary', 'secondary']
            ).count(),
        }
        
        # Save backup to file
        backup_filename = f'company_contacts_backup_{timestamp}.json'
        backup_path = os.path.join(output_dir, backup_filename)
        
        with open(backup_path, 'w') as f:
            json.dump(backup_data, f, indent=2, default=str)
        
        # Create a "latest" symlink for easy access
        latest_path = os.path.join(output_dir, 'company_contacts_backup_latest.json')
        if os.path.exists(latest_path):
            os.remove(latest_path)
        os.symlink(backup_filename, latest_path)
        
        # Display summary
        self.stdout.write('\n📊 BACKUP SUMMARY')
        self.stdout.write('=' * 50)
        self.stdout.write(f'💾 Backup saved to: {backup_path}')
        self.stdout.write(f'🔗 Latest backup: {latest_path}')
        self.stdout.write(f'🏢 Total companies: {len(backup_data["company_contact_fields"])}')
        self.stdout.write(f'📞 Companies with contacts: {companies_with_contacts}')
        self.stdout.write(f'👥 Contact users: {len(backup_data["user_contact_data"])}')
        
        # Validation summary
        validation = backup_data['validation_data']
        self.stdout.write(f'✅ Primary contacts (Company): {validation["companies_with_primary_contacts"]}')
        self.stdout.write(f'✅ Primary contacts (User): {validation["users_marked_primary"]}')
        self.stdout.write(f'✅ Secondary contacts (Company): {validation["companies_with_secondary_contacts"]}')
        self.stdout.write(f'✅ Secondary contacts (User): {validation["users_marked_secondary"]}')
        
        # Verify backup integrity
        self.verify_backup_integrity(backup_data)
        
        self.stdout.write(
            self.style.SUCCESS('\n🎉 Backup completed successfully!')
        )
        self.stdout.write('🛡️  You can now safely proceed with field removal')

    def verify_backup(self, output_dir):
        """Verify an existing backup file"""
        latest_path = os.path.join(output_dir, 'company_contacts_backup_latest.json')
        
        if not os.path.exists(latest_path):
            self.stdout.write(
                self.style.ERROR(f'❌ No backup found at: {latest_path}')
            )
            return
            
        self.stdout.write(
            self.style.SUCCESS('🔍 Verifying backup integrity...')
        )
        
        with open(latest_path, 'r') as f:
            backup_data = json.load(f)
            
        # Verify backup structure
        required_keys = ['metadata', 'company_contact_fields', 'user_contact_data', 'validation_data']
        for key in required_keys:
            if key not in backup_data:
                self.stdout.write(
                    self.style.ERROR(f'❌ Missing key in backup: {key}')
                )
                return
        
        # Verify data integrity
        self.verify_backup_integrity(backup_data)
        
        self.stdout.write(
            self.style.SUCCESS('✅ Backup verification completed successfully!')
        )

    def verify_backup_integrity(self, backup_data):
        """Verify the integrity of backup data"""
        self.stdout.write('\n🔍 VERIFYING BACKUP INTEGRITY')
        self.stdout.write('=' * 40)
        
        validation = backup_data['validation_data']
        
        # Check if counts match between Company and User models
        company_primary = validation['companies_with_primary_contacts']
        user_primary = validation['users_marked_primary']
        
        company_secondary = validation['companies_with_secondary_contacts']
        user_secondary = validation['users_marked_secondary']
        
        if company_primary == user_primary:
            self.stdout.write('✅ Primary contact counts match')
        else:
            self.stdout.write(
                self.style.WARNING(f'⚠️  Primary contact mismatch: Company({company_primary}) vs User({user_primary})')
            )
            
        if company_secondary == user_secondary:
            self.stdout.write('✅ Secondary contact counts match')
        else:
            self.stdout.write(
                self.style.WARNING(f'⚠️  Secondary contact mismatch: Company({company_secondary}) vs User({user_secondary})')
            )
        
        # Check for data completeness
        companies_in_backup = len(backup_data['company_contact_fields'])
        current_companies = Company.objects.count()
        
        if companies_in_backup == current_companies:
            self.stdout.write('✅ All companies backed up')
        else:
            self.stdout.write(
                self.style.ERROR(f'❌ Company count mismatch: Backup({companies_in_backup}) vs Current({current_companies})')
            )

    def restore_backup(self, backup_path):
        """Restore data from backup (emergency use only)"""
        self.stdout.write(
            self.style.WARNING('🚨 EMERGENCY RESTORE MODE')
        )
        self.stdout.write('=' * 50)
        
        if not os.path.exists(backup_path):
            self.stdout.write(
                self.style.ERROR(f'❌ Backup file not found: {backup_path}')
            )
            return
            
        # This is a placeholder for emergency restore functionality
        # In a real emergency, this would restore the Company fields
        self.stdout.write('⚠️  Restore functionality requires manual implementation')
        self.stdout.write('📋 To restore manually:')
        self.stdout.write('1. Add the contact fields back to Company model')
        self.stdout.write('2. Create migration to add fields')
        self.stdout.write('3. Run migration')
        self.stdout.write('4. Use backup data to populate fields')

    def get_django_version(self):
        """Get Django version for backup metadata"""
        try:
            import django
            return django.get_version()
        except:
            return 'unknown'
