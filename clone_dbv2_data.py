#!/usr/bin/env python
"""
Database Cloning Script for Nordic Loop Platform
Clones all data from dbv2.sqlite3 with multiple export options
"""

import os
import sys
import sqlite3
import json
import csv
import argparse
from pathlib import Path
from datetime import datetime
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.core import serializers
from django.apps import apps
from django.db import connections, transaction
from django.core.management import call_command


class DatabaseCloner:
    """
    A comprehensive database cloning utility that supports multiple export formats
    """
    
    def __init__(self, source_db_path="dbv2.sqlite3", target_db_path="db.sqlite3"):
        self.source_db_path = Path(source_db_path)
        self.target_db_path = Path(target_db_path)
        self.output_dir = Path("cloned_data")
        self.output_dir.mkdir(exist_ok=True)
        
        if not self.source_db_path.exists():
            raise FileNotFoundError(f"Source database {source_db_path} not found")
    
    def get_db_connection(self, db_path):
        """Get SQLite database connection"""
        return sqlite3.connect(db_path)
    
    def get_table_info(self, conn):
        """Get information about all tables in the database"""
        cursor = conn.cursor()
        
        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        
        table_info = {}
        for table in tables:
            if table == 'sqlite_sequence':
                continue
                
            # Get column information
            cursor.execute(f"PRAGMA table_info({table});")
            columns = cursor.fetchall()
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table};")
            row_count = cursor.fetchone()[0]
            
            table_info[table] = {
                'columns': columns,
                'row_count': row_count
            }
        
        return table_info
    
    def analyze_source_database(self):
        """Analyze the source database structure and content"""
        print(f"🔍 Analyzing source database: {self.source_db_path}")
        
        with self.get_db_connection(self.source_db_path) as conn:
            table_info = self.get_table_info(conn)
            
            print(f"\n📊 Database Analysis:")
            print(f"{'Table Name':<30} {'Columns':<10} {'Rows':<10}")
            print("-" * 50)
            
            total_rows = 0
            for table_name, info in table_info.items():
                col_count = len(info['columns'])
                row_count = info['row_count']
                total_rows += row_count
                print(f"{table_name:<30} {col_count:<10} {row_count:<10}")
            
            print("-" * 50)
            print(f"{'Total Tables:':<30} {len(table_info):<10} {total_rows:<10}")
            
            return table_info
    
    def export_to_sql_dump(self):
        """Export database to SQL dump file"""
        print(f"\n💾 Creating SQL dump...")
        
        output_file = self.output_dir / f"dbv2_dump_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        
        with self.get_db_connection(self.source_db_path) as conn:
            with open(output_file, 'w', encoding='utf-8') as f:
                # Write header
                f.write(f"-- SQL Dump from {self.source_db_path}\n")
                f.write(f"-- Generated on {datetime.now()}\n\n")
                
                # Dump schema and data
                for line in conn.iterdump():
                    f.write(f"{line}\n")
        
        print(f"✅ SQL dump saved to: {output_file}")
        return output_file
    
    def export_to_csv(self):
        """Export each table to separate CSV files"""
        print(f"\n📄 Exporting tables to CSV...")
        
        csv_dir = self.output_dir / "csv_export"
        csv_dir.mkdir(exist_ok=True)
        
        exported_files = []
        
        with self.get_db_connection(self.source_db_path) as conn:
            cursor = conn.cursor()
            table_info = self.get_table_info(conn)
            
            for table_name, info in table_info.items():
                if info['row_count'] == 0:
                    continue
                
                output_file = csv_dir / f"{table_name}.csv"
                
                # Get all data
                cursor.execute(f"SELECT * FROM {table_name};")
                rows = cursor.fetchall()
                
                # Get column names
                column_names = [col[1] for col in info['columns']]
                
                # Write CSV
                with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(column_names)
                    writer.writerows(rows)
                
                exported_files.append(output_file)
                print(f"  ✅ {table_name}: {len(rows)} rows -> {output_file}")
        
        return exported_files
    
    def export_to_json(self):
        """Export database to JSON format"""
        print(f"\n🔄 Exporting to JSON...")
        
        output_file = self.output_dir / f"dbv2_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        all_data = {}
        
        with self.get_db_connection(self.source_db_path) as conn:
            cursor = conn.cursor()
            table_info = self.get_table_info(conn)
            
            for table_name, info in table_info.items():
                if info['row_count'] == 0:
                    continue
                
                # Get all data
                cursor.execute(f"SELECT * FROM {table_name};")
                rows = cursor.fetchall()
                
                # Get column names
                column_names = [col[1] for col in info['columns']]
                
                # Convert to dictionaries
                table_data = []
                for row in rows:
                    row_dict = dict(zip(column_names, row))
                    table_data.append(row_dict)
                
                all_data[table_name] = table_data
                print(f"  ✅ {table_name}: {len(table_data)} records")
        
        # Save JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, indent=2, default=str)
        
        print(f"✅ JSON export saved to: {output_file}")
        return output_file
    
    def clone_to_target_database(self):
        """Clone data directly to target database"""
        print(f"\n🔄 Cloning data to target database: {self.target_db_path}")
        
        if not self.target_db_path.exists():
            print(f"⚠️  Target database {self.target_db_path} does not exist.")
            create = input("Create new target database? (y/N): ").lower().strip()
            if create != 'y':
                print("❌ Operation cancelled")
                return False
        
        # Backup target database if it exists
        if self.target_db_path.exists():
            backup_path = self.target_db_path.with_suffix(f'.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.sqlite3')
            import shutil
            shutil.copy2(self.target_db_path, backup_path)
            print(f"📋 Target database backed up to: {backup_path}")
        
        try:
            with self.get_db_connection(self.source_db_path) as source_conn:
                with self.get_db_connection(self.target_db_path) as target_conn:
                    
                    source_cursor = source_conn.cursor()
                    target_cursor = target_conn.cursor()
                    
                    # Get table info from source
                    table_info = self.get_table_info(source_conn)
                    
                    for table_name, info in table_info.items():
                        if info['row_count'] == 0:
                            continue
                        
                        print(f"  🔄 Cloning table: {table_name}")
                        
                        # Get table schema
                        source_cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}';")
                        create_sql = source_cursor.fetchone()
                        
                        if create_sql:
                            # Drop table if exists and recreate
                            target_cursor.execute(f"DROP TABLE IF EXISTS {table_name};")
                            target_cursor.execute(create_sql[0])
                        
                        # Copy data
                        source_cursor.execute(f"SELECT * FROM {table_name};")
                        rows = source_cursor.fetchall()
                        
                        if rows:
                            placeholders = ','.join(['?' for _ in range(len(info['columns']))])
                            target_cursor.executemany(f"INSERT INTO {table_name} VALUES ({placeholders});", rows)
                        
                        print(f"    ✅ {len(rows)} rows copied")
                    
                    target_conn.commit()
            
            print("✅ Database cloning completed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Error cloning database: {e}")
            return False
    
    def create_django_fixtures(self):
        """Create Django fixtures from the data (if tables match Django models)"""
        print(f"\n🏗️  Attempting to create Django fixtures...")
        
        try:
            # This would require mapping SQLite tables to Django models
            # For now, we'll create a basic structure
            
            fixture_file = self.output_dir / f"dbv2_fixtures_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with self.get_db_connection(self.source_db_path) as conn:
                cursor = conn.cursor()
                table_info = self.get_table_info(conn)
                
                fixtures = []
                
                # Map common Django tables
                django_table_mappings = {
                    'auth_user': 'auth.user',
                    'django_content_type': 'contenttypes.contenttype',
                    'company_company': 'company.company',
                    'users_user': 'users.user',
                    'category_category': 'category.category',
                    'category_subcategory': 'category.subcategory',
                    'ads_ad': 'ads.ad',
                    'ads_location': 'ads.location',
                    'bids_bid': 'bids.bid',
                }
                
                for table_name, info in table_info.items():
                    if table_name in django_table_mappings and info['row_count'] > 0:
                        model_name = django_table_mappings[table_name]
                        
                        cursor.execute(f"SELECT * FROM {table_name};")
                        rows = cursor.fetchall()
                        column_names = [col[1] for col in info['columns']]
                        
                        for row in rows:
                            fields = dict(zip(column_names, row))
                            # Remove pk field as it's handled separately
                            pk = fields.pop('id', None)
                            
                            fixture = {
                                'model': model_name,
                                'pk': pk,
                                'fields': fields
                            }
                            fixtures.append(fixture)
                        
                        print(f"  ✅ {table_name} -> {model_name}: {len(rows)} records")
                
                if fixtures:
                    with open(fixture_file, 'w', encoding='utf-8') as f:
                        json.dump(fixtures, f, indent=2, default=str)
                    
                    print(f"✅ Django fixtures saved to: {fixture_file}")
                    print(f"   Load with: python manage.py loaddata {fixture_file}")
                    return fixture_file
                else:
                    print("⚠️  No Django model mappings found")
                    return None
                    
        except Exception as e:
            print(f"❌ Error creating Django fixtures: {e}")
            return None
    
    def full_clone_operation(self, export_formats=None):
        """Perform a complete cloning operation with specified formats"""
        if export_formats is None:
            export_formats = ['sql', 'json', 'csv', 'fixtures']
        
        print("🚀 Starting database cloning operation...")
        print(f"Source: {self.source_db_path}")
        print(f"Output directory: {self.output_dir}")
        
        # Analyze database
        table_info = self.analyze_source_database()
        
        results = {}
        
        # Export in requested formats
        if 'sql' in export_formats:
            results['sql_dump'] = self.export_to_sql_dump()
        
        if 'json' in export_formats:
            results['json_export'] = self.export_to_json()
        
        if 'csv' in export_formats:
            results['csv_files'] = self.export_to_csv()
        
        if 'fixtures' in export_formats:
            results['django_fixtures'] = self.create_django_fixtures()
        
        if 'clone' in export_formats:
            results['database_clone'] = self.clone_to_target_database()
        
        print(f"\n🎉 Cloning operation completed!")
        print(f"📁 All files saved to: {self.output_dir}")
        
        return results


def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(description='Clone data from dbv2.sqlite3')
    parser.add_argument('--source', '-s', default='dbv2.sqlite3', 
                       help='Source database path (default: dbv2.sqlite3)')
    parser.add_argument('--target', '-t', default='db.sqlite3', 
                       help='Target database path (default: db.sqlite3)')
    parser.add_argument('--formats', '-f', nargs='+', 
                       choices=['sql', 'json', 'csv', 'fixtures', 'clone'],
                       default=['sql', 'json', 'csv', 'fixtures'],
                       help='Export formats (default: all except clone)')
    parser.add_argument('--analyze-only', '-a', action='store_true',
                       help='Only analyze database structure, no exports')
    
    args = parser.parse_args()
    
    try:
        cloner = DatabaseCloner(args.source, args.target)
        
        if args.analyze_only:
            cloner.analyze_source_database()
        else:
            cloner.full_clone_operation(args.formats)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 