"""
Django management command to rollback the company contact normalization.
This provides instant rollback capability by switching the serializer back to Company fields.

Usage:
    python manage.py rollback_contact_migration --preview  # Preview rollback
    python manage.py rollback_contact_migration            # Execute rollback
"""

import os
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Rollback company contact normalization by switching serializer to use Company fields'

    def add_arguments(self, parser):
        parser.add_argument(
            '--preview',
            action='store_true',
            help='Preview what the rollback would do',
        )

    def handle(self, *args, **options):
        """Main command handler"""
        
        if options['preview']:
            self.preview_rollback()
        else:
            self.execute_rollback()

    def preview_rollback(self):
        """Preview what the rollback would do"""
        self.stdout.write(
            self.style.WARNING('🔮 ROLLBACK PREVIEW')
        )
        self.stdout.write('=' * 50)
        
        self.stdout.write('The rollback will:')
        self.stdout.write('1. 📝 Modify AdminCompanyListSerializer.get_contacts() method')
        self.stdout.write('2. 🔄 Switch from User model back to Company fields')
        self.stdout.write('3. ✅ Restore original API behavior')
        self.stdout.write('4. 💾 Keep all User data intact (no data loss)')
        
        self.stdout.write('\n📊 Current Status:')
        serializer_path = self.get_serializer_path()
        if os.path.exists(serializer_path):
            with open(serializer_path, 'r') as f:
                content = f.read()
                if 'User.objects.filter' in content:
                    self.stdout.write('   🔄 Currently using User model (normalized)')
                else:
                    self.stdout.write('   📁 Currently using Company fields (original)')
        
        self.stdout.write('\n⚠️  Run without --preview to execute rollback')

    def execute_rollback(self):
        """Execute the rollback"""
        self.stdout.write(
            self.style.SUCCESS('🔄 EXECUTING ROLLBACK')
        )
        self.stdout.write('=' * 50)
        
        serializer_path = self.get_serializer_path()
        
        if not os.path.exists(serializer_path):
            self.stdout.write(
                self.style.ERROR(f'❌ Serializer file not found: {serializer_path}')
            )
            return
            
        # Read current content
        with open(serializer_path, 'r') as f:
            content = f.read()
            
        # Check if already rolled back
        if 'User.objects.filter' not in content:
            self.stdout.write(
                self.style.WARNING('⚠️  Already using Company fields - no rollback needed')
            )
            return
            
        # Create backup
        backup_path = f"{serializer_path}.backup"
        with open(backup_path, 'w') as f:
            f.write(content)
        self.stdout.write(f'💾 Backup created: {backup_path}')
        
        # Replace the get_contacts method
        new_content = self.get_rollback_content(content)
        
        with open(serializer_path, 'w') as f:
            f.write(new_content)
            
        self.stdout.write('✅ Serializer updated to use Company fields')
        self.stdout.write('🔄 API now uses original Company model structure')
        self.stdout.write('💾 All User data preserved (no data loss)')
        
        # Validate rollback
        self.validate_rollback()

    def get_serializer_path(self):
        """Get the path to the company serializer file"""
        return os.path.join(
            settings.BASE_DIR,
            'company',
            'serializer.py'
        )

    def get_rollback_content(self, current_content):
        """Generate the rollback content for the serializer"""
        
        # Find the get_contacts method and replace it
        lines = current_content.split('\n')
        new_lines = []
        in_get_contacts = False
        indent_level = 0
        
        for line in lines:
            if 'def get_contacts(self, obj):' in line:
                in_get_contacts = True
                indent_level = len(line) - len(line.lstrip())
                # Add the original get_contacts method
                new_lines.extend(self.get_original_contacts_method(indent_level))
                continue
                
            if in_get_contacts:
                # Skip lines until we find the next method or end of class
                current_indent = len(line) - len(line.lstrip()) if line.strip() else float('inf')
                if line.strip() and current_indent <= indent_level:
                    # We've reached the next method or end of class
                    in_get_contacts = False
                    new_lines.append(line)
                # Skip the current get_contacts method content
                continue
            else:
                new_lines.append(line)
                
        return '\n'.join(new_lines)

    def get_original_contacts_method(self, indent_level):
        """Get the original get_contacts method content"""
        indent = ' ' * indent_level
        
        return [
            f'{indent}def get_contacts(self, obj):',
            f'{indent}    """',
            f'{indent}    Construct contacts array from primary and secondary contact fields',
            f'{indent}    (ROLLBACK: Using original Company model fields)',
            f'{indent}    """',
            f'{indent}    contacts = []',
            f'{indent}    ',
            f'{indent}    # Primary contact',
            f'{indent}    if obj.primary_first_name and obj.primary_last_name and obj.primary_email:',
            f'{indent}        primary_contact = {{',
            f'{indent}            \'name\': f"{{obj.primary_first_name}} {{obj.primary_last_name}}",',
            f'{indent}            \'email\': obj.primary_email,',
            f'{indent}            \'position\': obj.primary_position or ""',
            f'{indent}        }}',
            f'{indent}        contacts.append(primary_contact)',
            f'{indent}    ',
            f'{indent}    # Secondary contact',
            f'{indent}    if obj.secondary_first_name and obj.secondary_last_name and obj.secondary_email:',
            f'{indent}        secondary_contact = {{',
            f'{indent}            \'name\': f"{{obj.secondary_first_name}} {{obj.secondary_last_name}}",',
            f'{indent}            \'email\': obj.secondary_email,',
            f'{indent}            \'position\': obj.secondary_position or ""',
            f'{indent}        }}',
            f'{indent}        contacts.append(secondary_contact)',
            f'{indent}    ',
            f'{indent}    return contacts',
        ]

    def validate_rollback(self):
        """Validate that the rollback was successful"""
        self.stdout.write('\n🔍 VALIDATING ROLLBACK')
        self.stdout.write('=' * 30)
        
        try:
            # Try to import the serializer to check for syntax errors
            from company.serializer import AdminCompanyListSerializer
            
            # Create a test instance (this will fail if there are import issues)
            serializer_class = AdminCompanyListSerializer
            
            self.stdout.write('✅ Serializer imports successfully')
            self.stdout.write('✅ No syntax errors detected')
            self.stdout.write('🎉 Rollback completed successfully!')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Rollback validation failed: {e}')
            )
            self.stdout.write('🔧 Please check the serializer file manually')

    def show_rollback_instructions(self):
        """Show manual rollback instructions"""
        self.stdout.write('\n📋 MANUAL ROLLBACK INSTRUCTIONS')
        self.stdout.write('=' * 50)
        
        self.stdout.write('If automatic rollback fails, manually edit company/serializer.py:')
        self.stdout.write('')
        self.stdout.write('1. Find the get_contacts method in AdminCompanyListSerializer')
        self.stdout.write('2. Replace the User.objects.filter logic with:')
        self.stdout.write('')
        self.stdout.write('   def get_contacts(self, obj):')
        self.stdout.write('       contacts = []')
        self.stdout.write('       if obj.primary_first_name and obj.primary_email:')
        self.stdout.write('           contacts.append({')
        self.stdout.write('               "name": f"{obj.primary_first_name} {obj.primary_last_name}",')
        self.stdout.write('               "email": obj.primary_email,')
        self.stdout.write('               "position": obj.primary_position or ""')
        self.stdout.write('           })')
        self.stdout.write('       # ... similar for secondary contact')
        self.stdout.write('       return contacts')
        self.stdout.write('')
        self.stdout.write('3. Remove the User import if no longer needed')
        self.stdout.write('4. Test the API to ensure it works')
