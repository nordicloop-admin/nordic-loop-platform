import json
import os
from django.core.management.base import BaseCommand
from django.db import transaction
from category.models import Category, SubCategory


class Command(BaseCommand):
    help = 'Populate categories and subcategories from JSON file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='data/categories.json',
            help='Path to categories JSON file (default: data/categories.json)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing categories before importing'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        clear_existing = options['clear']

        # Check if file exists
        if not os.path.exists(file_path):
            self.stdout.write(
                self.style.ERROR(f'File not found: {file_path}')
            )
            return

        # Load JSON data
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            self.stdout.write(
                self.style.ERROR(f'Invalid JSON file: {e}')
            )
            return
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error reading file: {e}')
            )
            return

        # Clear existing data if requested
        if clear_existing:
            self.stdout.write('Clearing existing categories and subcategories...')
            SubCategory.objects.all().delete()
            Category.objects.all().delete()
            self.stdout.write(
                self.style.SUCCESS('Existing data cleared.')
            )

        # Import categories and subcategories
        categories_data = data.get('categories', [])
        created_categories = 0
        created_subcategories = 0

        with transaction.atomic():
            for category_data in categories_data:
                category_name = category_data.get('name', '')
                if not category_name:
                    self.stdout.write(
                        self.style.WARNING(f'Skipping category with missing name: {category_data}')
                    )
                    continue

                # Create or get category
                category, created = Category.objects.get_or_create(
                    name=category_name
                )
                
                if created:
                    created_categories += 1
                    self.stdout.write(f'Created category: {category_name}')
                else:
                    self.stdout.write(f'Category already exists: {category_name}')

                # Create subcategories
                subcategories_data = category_data.get('subcategories', [])
                for subcategory_data in subcategories_data:
                    subcategory_name = subcategory_data.get('name', '')
                    if not subcategory_name:
                        self.stdout.write(
                            self.style.WARNING(f'Skipping subcategory with missing name: {subcategory_data}')
                        )
                        continue

                    # Create or get subcategory
                    subcategory, created = SubCategory.objects.get_or_create(
                        category=category,
                        name=subcategory_name
                    )
                    
                    if created:
                        created_subcategories += 1
                        self.stdout.write(f'  Created subcategory: {subcategory_name}')
                    else:
                        self.stdout.write(f'  Subcategory already exists: {subcategory_name}')

        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f'\nImport completed successfully!\n'
                f'Categories created: {created_categories}\n'
                f'Subcategories created: {created_subcategories}\n'
                f'Total categories in database: {Category.objects.count()}\n'
                f'Total subcategories in database: {SubCategory.objects.count()}'
            )
        ) 