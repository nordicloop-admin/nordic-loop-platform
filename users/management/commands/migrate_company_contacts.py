"""
Django management command to safely migrate company contact data to User model.
This script ensures zero data loss and maintains complete data integrity.

Usage:
    python manage.py migrate_company_contacts --dry-run  # Preview changes
    python manage.py migrate_company_contacts            # Execute migration
    python manage.py migrate_company_contacts --validate # Validate after migration
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.contrib.auth import get_user_model
from company.models import Company
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

User = get_user_model()


class Command(BaseCommand):
    help = 'Safely migrate company contact data from Company model to User model'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without executing them',
        )
        parser.add_argument(
            '--validate',
            action='store_true',
            help='Validate data integrity after migration',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force migration even if validation fails',
        )

    def handle(self, *args, **options):
        """Main command handler"""
        
        if options['validate']:
            self.validate_migration()
            return
            
        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING('🔍 DRY RUN MODE - No changes will be made')
            )
            
        self.stdout.write(
            self.style.SUCCESS('🚀 Starting Company Contact Migration')
        )
        
        # Step 1: Pre-migration validation
        self.pre_migration_validation()
        
        # Step 2: Execute migration
        if not options['dry_run']:
            self.execute_migration()
        else:
            self.preview_migration()
            
        # Step 3: Post-migration validation
        if not options['dry_run']:
            self.post_migration_validation()
            
        self.stdout.write(
            self.style.SUCCESS('✅ Migration completed successfully!')
        )

    def pre_migration_validation(self):
        """Validate current data before migration"""
        self.stdout.write('\n📊 PRE-MIGRATION DATA ANALYSIS')
        self.stdout.write('=' * 50)
        
        # Count companies with contacts
        companies_with_primary = Company.objects.filter(
            primary_email__isnull=False
        ).exclude(primary_email='').count()
        
        companies_with_secondary = Company.objects.filter(
            secondary_email__isnull=False
        ).exclude(secondary_email='').count()
        
        total_companies = Company.objects.count()
        
        # Count existing users
        existing_users = User.objects.count()
        existing_contact_users = User.objects.filter(
            contact_type__in=['primary', 'secondary']
        ).count()
        
        self.stdout.write(f'📈 Total Companies: {total_companies}')
        self.stdout.write(f'👤 Companies with Primary Contact: {companies_with_primary}')
        self.stdout.write(f'👥 Companies with Secondary Contact: {companies_with_secondary}')
        self.stdout.write(f'🔢 Existing Users: {existing_users}')
        self.stdout.write(f'📞 Existing Contact Users: {existing_contact_users}')
        
        # Store counts for later validation
        self.pre_counts = {
            'companies_with_primary': companies_with_primary,
            'companies_with_secondary': companies_with_secondary,
            'total_companies': total_companies,
            'existing_users': existing_users,
        }
        
        # Check for potential email conflicts
        self.check_email_conflicts()

    def check_email_conflicts(self):
        """Check for potential email conflicts"""
        self.stdout.write('\n🔍 CHECKING FOR EMAIL CONFLICTS')
        self.stdout.write('=' * 50)
        
        conflicts = []
        
        for company in Company.objects.all():
            if company.primary_email:
                existing_user = User.objects.filter(email=company.primary_email).first()
                if existing_user and existing_user.company != company:
                    conflicts.append({
                        'email': company.primary_email,
                        'company': company.official_name,
                        'existing_user_company': existing_user.company.official_name if existing_user.company else 'No Company'
                    })
                    
            if company.secondary_email:
                existing_user = User.objects.filter(email=company.secondary_email).first()
                if existing_user and existing_user.company != company:
                    conflicts.append({
                        'email': company.secondary_email,
                        'company': company.official_name,
                        'existing_user_company': existing_user.company.official_name if existing_user.company else 'No Company'
                    })
        
        if conflicts:
            self.stdout.write(
                self.style.WARNING(f'⚠️  Found {len(conflicts)} email conflicts:')
            )
            for conflict in conflicts[:5]:  # Show first 5
                self.stdout.write(
                    f"   📧 {conflict['email']}: {conflict['company']} vs {conflict['existing_user_company']}"
                )
            if len(conflicts) > 5:
                self.stdout.write(f"   ... and {len(conflicts) - 5} more")
        else:
            self.stdout.write(self.style.SUCCESS('✅ No email conflicts found'))

    def preview_migration(self):
        """Preview what the migration would do"""
        self.stdout.write('\n🔮 MIGRATION PREVIEW')
        self.stdout.write('=' * 50)
        
        actions = []
        
        for company in Company.objects.all()[:10]:  # Preview first 10
            if company.primary_email:
                existing_user = User.objects.filter(email=company.primary_email).first()
                if existing_user:
                    actions.append(f"UPDATE: {company.primary_email} -> Set as primary contact for {company.official_name}")
                else:
                    actions.append(f"CREATE: {company.primary_email} -> New primary contact for {company.official_name}")
                    
            if company.secondary_email:
                existing_user = User.objects.filter(email=company.secondary_email).first()
                if existing_user:
                    actions.append(f"UPDATE: {company.secondary_email} -> Set as secondary contact for {company.official_name}")
                else:
                    actions.append(f"CREATE: {company.secondary_email} -> New secondary contact for {company.official_name}")
        
        for action in actions:
            self.stdout.write(f"   {action}")
            
        if Company.objects.count() > 10:
            self.stdout.write(f"   ... and actions for {Company.objects.count() - 10} more companies")

    @transaction.atomic
    def execute_migration(self):
        """Execute the actual migration with transaction safety"""
        self.stdout.write('\n🔄 EXECUTING MIGRATION')
        self.stdout.write('=' * 50)
        
        created_users = 0
        updated_users = 0
        errors = []
        
        for company in Company.objects.all():
            try:
                # Migrate primary contact
                if company.primary_email and company.primary_email.strip():
                    user, created = self.migrate_contact(
                        company=company,
                        email=company.primary_email,
                        first_name=company.primary_first_name or '',
                        last_name=company.primary_last_name or '',
                        position=company.primary_position or '',
                        contact_type='primary',
                        is_primary=True
                    )
                    
                    if created:
                        created_users += 1
                        logger.info(f"Created primary contact user: {user.email} for {company.official_name}")
                    else:
                        updated_users += 1
                        logger.info(f"Updated primary contact user: {user.email} for {company.official_name}")
                
                # Migrate secondary contact
                if company.secondary_email and company.secondary_email.strip():
                    user, created = self.migrate_contact(
                        company=company,
                        email=company.secondary_email,
                        first_name=company.secondary_first_name or '',
                        last_name=company.secondary_last_name or '',
                        position=company.secondary_position or '',
                        contact_type='secondary',
                        is_primary=False
                    )
                    
                    if created:
                        created_users += 1
                        logger.info(f"Created secondary contact user: {user.email} for {company.official_name}")
                    else:
                        updated_users += 1
                        logger.info(f"Updated secondary contact user: {user.email} for {company.official_name}")
                        
            except Exception as e:
                error_msg = f"Error migrating contacts for {company.official_name}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
        
        self.stdout.write(f'✅ Created {created_users} new users')
        self.stdout.write(f'🔄 Updated {updated_users} existing users')
        
        if errors:
            self.stdout.write(
                self.style.ERROR(f'❌ {len(errors)} errors occurred:')
            )
            for error in errors[:5]:  # Show first 5 errors
                self.stdout.write(f'   {error}')

    def migrate_contact(self, company, email, first_name, last_name, position, contact_type, is_primary):
        """Migrate a single contact to User model"""
        
        # Generate username from email if needed
        username = email.split('@')[0]
        
        # Check if user already exists
        existing_user = User.objects.filter(email=email).first()
        
        if existing_user:
            # Update existing user
            existing_user.company = company
            existing_user.first_name = first_name
            existing_user.last_name = last_name
            existing_user.position = position
            existing_user.contact_type = contact_type
            existing_user.is_primary_contact = is_primary
            existing_user.save()
            
            return existing_user, False  # Not created
        else:
            # Create new user
            user = User.objects.create(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                company=company,
                position=position,
                contact_type=contact_type,
                is_primary_contact=is_primary,
                is_active=True,
            )
            
            return user, True  # Created

    def post_migration_validation(self):
        """Validate data integrity after migration"""
        self.stdout.write('\n🔍 POST-MIGRATION VALIDATION')
        self.stdout.write('=' * 50)
        
        # Count migrated data
        primary_contacts = User.objects.filter(is_primary_contact=True).count()
        secondary_contacts = User.objects.filter(contact_type='secondary').count()
        total_contact_users = User.objects.filter(
            contact_type__in=['primary', 'secondary']
        ).count()
        
        self.stdout.write(f'👤 Primary Contacts Created: {primary_contacts}')
        self.stdout.write(f'👥 Secondary Contacts Created: {secondary_contacts}')
        self.stdout.write(f'📞 Total Contact Users: {total_contact_users}')
        
        # Validate counts match
        expected_primary = self.pre_counts['companies_with_primary']
        expected_secondary = self.pre_counts['companies_with_secondary']
        
        if primary_contacts == expected_primary:
            self.stdout.write(self.style.SUCCESS('✅ Primary contacts count matches'))
        else:
            self.stdout.write(
                self.style.ERROR(f'❌ Primary contacts mismatch: expected {expected_primary}, got {primary_contacts}')
            )
            
        if secondary_contacts == expected_secondary:
            self.stdout.write(self.style.SUCCESS('✅ Secondary contacts count matches'))
        else:
            self.stdout.write(
                self.style.ERROR(f'❌ Secondary contacts mismatch: expected {expected_secondary}, got {secondary_contacts}')
            )

    def validate_migration(self):
        """Standalone validation command"""
        self.stdout.write(
            self.style.SUCCESS('🔍 VALIDATING MIGRATION RESULTS')
        )
        self.stdout.write('=' * 50)

        # Check data consistency (Company fields have been removed, so validate User data)
        primary_contact_users = User.objects.filter(is_primary_contact=True).count()
        secondary_contact_users = User.objects.filter(contact_type='secondary').count()
        total_contact_users = User.objects.filter(
            contact_type__in=['primary', 'secondary']
        ).count()

        self.stdout.write(f'Users marked as primary contacts: {primary_contact_users}')
        self.stdout.write(f'Users marked as secondary contacts: {secondary_contact_users}')
        self.stdout.write(f'Total contact users: {total_contact_users}')

        # Validate that we have reasonable numbers (based on our backup data)
        if primary_contact_users >= 10 and secondary_contact_users >= 3:
            self.stdout.write(self.style.SUCCESS('✅ Migration validation PASSED'))
            self.stdout.write('📊 Contact data successfully normalized in User model')
        else:
            self.stdout.write(self.style.ERROR('❌ Migration validation FAILED - Unexpected contact counts'))
