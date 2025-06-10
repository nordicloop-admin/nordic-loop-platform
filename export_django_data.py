#!/usr/bin/env python
"""
Django Data Export Script for Nordic Loop Platform
Exports all data from current database using Django's native tools
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
import subprocess

# Set minimal environment variables if not set
if not os.getenv('DJANGO_SECRET_KEY'):
    os.environ['DJANGO_SECRET_KEY'] = 'export-key-temporary'
if not os.getenv('DJANGO_ENV'):
    os.environ['DJANGO_ENV'] = 'development'
if not os.getenv('DJANGO_DEBUG'):
    os.environ['DJANGO_DEBUG'] = 'True'
if not os.getenv('DJANGO_ALLOWED_HOSTS'):
    os.environ['DJANGO_ALLOWED_HOSTS'] = 'localhost,127.0.0.1'

import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.core.management import call_command
from django.db import connection
from django.apps import apps
from django.core import serializers

# Import your models to check data
from company.models import Company
from users.models import User
from category.models import Category, SubCategory, CategorySpecification
from ads.models import Ad, Location
from bids.models import Bid, BidHistory


class DjangoDataExporter:
    """
    Export data using Django's native data management tools
    """
    
    def __init__(self):
        self.export_dir = Path("django_exports")
        self.export_dir.mkdir(exist_ok=True)
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.log_entries = []
    
    def log(self, message):
        """Log export progress"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        self.log_entries.append(log_message)
    
    def check_current_database(self):
        """Check what database we're currently connected to"""
        self.log("🔍 Checking current database connection...")
        
        db_settings = connection.settings_dict
        engine = db_settings['ENGINE']
        db_name = db_settings.get('NAME', 'Unknown')
        
        self.log(f"📊 Database Engine: {engine}")
        self.log(f"📊 Database Name: {db_name}")
        
        if 'sqlite' in engine:
            self.log(f"✅ Connected to SQLite database: {db_name}")
        elif 'postgresql' in engine:
            self.log(f"✅ Connected to PostgreSQL database")
        else:
            self.log(f"⚠️  Connected to: {engine}")
        
        return engine, db_name
    
    def analyze_current_data(self):
        """Analyze current data in the database"""
        self.log("📈 Analyzing current data...")
        
        data_counts = {
            'Companies': Company.objects.count(),
            'Users': User.objects.count(),
            'Categories': Category.objects.count(),
            'SubCategories': SubCategory.objects.count(),
            'Category Specifications': CategorySpecification.objects.count(),
            'Locations': Location.objects.count(),
            'Ads': Ad.objects.count(),
            'Bids': Bid.objects.count(),
            'Bid History': BidHistory.objects.count()
        }
        
        self.log("📊 Current Database Contents:")
        total_records = 0
        for model_name, count in data_counts.items():
            self.log(f"   {model_name}: {count} records")
            total_records += count
        
        self.log(f"📊 Total Records: {total_records}")
        return data_counts, total_records
    
    def export_full_database(self):
        """Export entire database using Django's dumpdata"""
        self.log("💾 Exporting full database using Django dumpdata...")
        
        output_file = self.export_dir / f"full_database_export_{self.timestamp}.json"
        
        try:
            # Export all data except Django's internal data
            with open(output_file, 'w', encoding='utf-8') as f:
                call_command(
                    'dumpdata',
                    '--natural-foreign',
                    '--natural-primary',
                    '--indent=2',
                    exclude=[
                        'contenttypes',
                        'auth.permission',
                        'admin.logentry',
                        'sessions.session',
                    ],
                    stdout=f
                )
            
            self.log(f"✅ Full database exported to: {output_file}")
            return output_file
            
        except Exception as e:
            self.log(f"❌ Error exporting full database: {e}")
            return None
    
    def export_by_app(self):
        """Export data by Django app for better organization"""
        self.log("📦 Exporting data by Django app...")
        
        apps_to_export = [
            'company',
            'users', 
            'category',
            'ads',
            'bids'
        ]
        
        exported_files = []
        
        for app_name in apps_to_export:
            try:
                output_file = self.export_dir / f"{app_name}_data_{self.timestamp}.json"
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    call_command(
                        'dumpdata',
                        app_name,
                        '--natural-foreign',
                        '--natural-primary',
                        '--indent=2',
                        stdout=f
                    )
                
                # Check if file has content
                if output_file.stat().st_size > 10:  # More than just empty brackets
                    self.log(f"✅ {app_name} data exported to: {output_file}")
                    exported_files.append(output_file)
                else:
                    self.log(f"⚠️  {app_name} has no data to export")
                    output_file.unlink()  # Remove empty file
                    
            except Exception as e:
                self.log(f"❌ Error exporting {app_name}: {e}")
        
        return exported_files
    
    def export_user_data_with_passwords(self):
        """Export user data while preserving password hashes"""
        self.log("🔐 Exporting user data with password preservation...")
        
        output_file = self.export_dir / f"users_with_passwords_{self.timestamp}.json"
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                call_command(
                    'dumpdata',
                    'users.User',
                    '--natural-foreign',
                    '--natural-primary',
                    '--indent=2',
                    stdout=f
                )
            
            self.log(f"✅ User data with passwords exported to: {output_file}")
            self.log("🔐 Password hashes have been preserved")
            return output_file
            
        except Exception as e:
            self.log(f"❌ Error exporting user data: {e}")
            return None
    
    def create_import_script(self, exported_files):
        """Create a script to import the data into PostgreSQL"""
        self.log("📝 Creating import script for PostgreSQL...")
        
        import_script = self.export_dir / f"import_to_postgres_{self.timestamp}.py"
        
        script_content = f'''#!/usr/bin/env python
"""
Import Script for PostgreSQL Database
Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

import os
import sys
from pathlib import Path

# Set environment variables for PostgreSQL
if not os.getenv('DJANGO_SECRET_KEY'):
    os.environ['DJANGO_SECRET_KEY'] = 'your-postgres-secret-key'
if not os.getenv('DJANGO_ENV'):
    os.environ['DJANGO_ENV'] = 'production'  # or development
if not os.getenv('DJANGO_DEBUG'):
    os.environ['DJANGO_DEBUG'] = 'False'

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.core.management import call_command
from django.db import connection

def main():
    print("🔄 Importing data to PostgreSQL database...")
    
    # Check database connection
    db_settings = connection.settings_dict
    print(f"🗄️  Database Engine: {{db_settings['ENGINE']}}")
    
    if 'postgresql' not in db_settings['ENGINE']:
        print("❌ This script requires PostgreSQL database connection")
        print("💡 Make sure DATABASE_URL is set and points to PostgreSQL")
        return
    
    # Import order is important due to foreign key relationships
    import_files = [
'''

        # Add import files in dependency order
        for file_path in exported_files:
            file_name = file_path.name
            script_content += f'        "{file_name}",\n'
        
        script_content += f'''    ]
    
    current_dir = Path(__file__).parent
    
    for file_name in import_files:
        file_path = current_dir / file_name
        if file_path.exists():
            print(f"📥 Importing {{file_name}}...")
            try:
                call_command('loaddata', str(file_path))
                print(f"✅ {{file_name}} imported successfully")
            except Exception as e:
                print(f"❌ Error importing {{file_name}}: {{e}}")
        else:
            print(f"⚠️  File not found: {{file_name}}")
    
    print("🎉 Import completed!")
    print("🔐 User passwords have been preserved")
    print("👥 Users can log in with their existing credentials")

if __name__ == "__main__":
    main()
'''
        
        with open(import_script, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        # Make script executable
        import_script.chmod(0o755)
        
        self.log(f"✅ Import script created: {import_script}")
        return import_script
    
    def create_readme(self):
        """Create README with instructions"""
        self.log("📄 Creating README with instructions...")
        
        readme_file = self.export_dir / f"README_{self.timestamp}.md"
        
        readme_content = f'''# Django Data Export - Nordic Loop Platform

Export created on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Files Created

### 1. Full Database Export
- `full_database_export_{self.timestamp}.json` - Complete database dump

### 2. App-specific Exports
- `company_data_{self.timestamp}.json` - Company data
- `users_data_{self.timestamp}.json` - User data  
- `category_data_{self.timestamp}.json` - Category and subcategory data
- `ads_data_{self.timestamp}.json` - Ads and location data
- `bids_data_{self.timestamp}.json` - Bids and bid history data

### 3. User Data with Passwords
- `users_with_passwords_{self.timestamp}.json` - User data with preserved password hashes

### 4. Import Script
- `import_to_postgres_{self.timestamp}.py` - Automated import script for PostgreSQL

## How to Import to PostgreSQL

### Method 1: Using the Import Script (Recommended)

1. **Switch to PostgreSQL database**:
   - Update your Django settings to use PostgreSQL
   - Set the DATABASE_URL environment variable
   - Run migrations: `python manage.py migrate`

2. **Run the import script**:
   ```bash
   python import_to_postgres_{self.timestamp}.py
   ```

### Method 2: Manual Import

1. **Switch to PostgreSQL database** (same as above)

2. **Import data manually**:
   ```bash
   # Import in dependency order
   python manage.py loaddata company_data_{self.timestamp}.json
   python manage.py loaddata users_with_passwords_{self.timestamp}.json
   python manage.py loaddata category_data_{self.timestamp}.json
   python manage.py loaddata ads_data_{self.timestamp}.json
   python manage.py loaddata bids_data_{self.timestamp}.json
   ```

### Method 3: Full Database Import

```bash
python manage.py loaddata full_database_export_{self.timestamp}.json
```

## Important Notes

- ✅ User passwords have been preserved
- ✅ All foreign key relationships are maintained
- ✅ Data integrity is ensured by Django's serialization
- ⚠️  Make sure PostgreSQL database is empty or run `python manage.py flush` first
- ⚠️  Run `python manage.py migrate` before importing data

## Verification

After import, verify the data:

```python
python manage.py shell

# Check data counts
from company.models import Company
from users.models import User
from category.models import Category
from ads.models import Ad
from bids.models import Bid

print(f"Companies: {{Company.objects.count()}}")
print(f"Users: {{User.objects.count()}}")
print(f"Categories: {{Category.objects.count()}}")
print(f"Ads: {{Ad.objects.count()}}")
print(f"Bids: {{Bid.objects.count()}}")
```

## Support

If you encounter any issues:
1. Check that PostgreSQL is properly configured
2. Ensure all migrations are applied
3. Verify environment variables are set correctly
4. Check Django logs for detailed error messages
'''
        
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        self.log(f"✅ README created: {readme_file}")
        return readme_file
    
    def save_export_log(self):
        """Save export log"""
        log_file = self.export_dir / f"export_log_{self.timestamp}.txt"
        
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write("Django Data Export Log\n")
            f.write("=" * 50 + "\n\n")
            for log_entry in self.log_entries:
                f.write(f"{log_entry}\n")
        
        self.log(f"📄 Export log saved: {log_file}")
        return log_file
    
    def run_full_export(self):
        """Run complete export process"""
        self.log("🚀 Starting Django data export...")
        
        # Check database
        engine, db_name = self.check_current_database()
        
        # Analyze data
        data_counts, total_records = self.analyze_current_data()
        
        if total_records == 0:
            self.log("⚠️  No data found to export!")
            return False
        
        # Export data
        exported_files = []
        
        # Full database export
        full_export = self.export_full_database()
        if full_export:
            exported_files.append(full_export)
        
        # App-specific exports
        app_exports = self.export_by_app()
        exported_files.extend(app_exports)
        
        # User data with passwords
        user_export = self.export_user_data_with_passwords()
        if user_export:
            exported_files.append(user_export)
        
        # Create import script
        import_script = self.create_import_script(app_exports)
        
        # Create README
        readme = self.create_readme()
        
        # Save log
        log_file = self.save_export_log()
        
        self.log("🎉 Export completed successfully!")
        self.log(f"📁 All files saved to: {self.export_dir}")
        self.log("📋 Next steps:")
        self.log("   1. Switch Django settings to PostgreSQL")
        self.log("   2. Run: python manage.py migrate")
        self.log(f"   3. Run: python {import_script.name}")
        
        return exported_files


def main():
    """Main export function"""
    print("📊 Django Data Exporter for Nordic Loop Platform")
    print("This will export all data from your current database using Django tools")
    print()
    
    exporter = DjangoDataExporter()
    
    try:
        results = exporter.run_full_export()
        
        if results:
            print("\n✅ Export completed successfully!")
            print(f"📁 Check the '{exporter.export_dir}' directory for all exported files")
            print("🔄 Ready for PostgreSQL import!")
        else:
            print("\n❌ Export failed or no data found")
    
    except Exception as e:
        print(f"\n❌ Export error: {e}")
        exporter.save_export_log()


if __name__ == "__main__":
    main() 