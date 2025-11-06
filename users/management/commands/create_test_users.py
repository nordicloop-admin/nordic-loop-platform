from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import random

from users.models import User
from company.models import Company
from category.models import Category, SubCategory, CategorySpecification
from ads.models import Ad, Location


class Command(BaseCommand):
    help = 'Create test users with companies and auctions'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating test users with companies and auctions...'))
        
        # Create basic categories first if they don't exist
        self.create_categories()
        
        # Create the two users with their companies and auctions
        self.create_user_with_data(
            email='kareraol1@gmail.com',
            password='Krol@2027',
            name='Oliver Karera',
            company_name='NordicLoop Technologies AB',
            is_admin=True
        )
        
        self.create_user_with_data(
            email='olivierkarera@gmail.com', 
            password='Krol@2027',
            name='Olivier Karera',
            company_name='Green Materials Sweden AB',
            is_admin=False
        )
        
        self.stdout.write(self.style.SUCCESS('Successfully created test users, companies, and auctions!'))

    def create_categories(self):
        """Create basic categories and subcategories for auctions"""
        self.stdout.write('Creating categories and subcategories...')
        
        categories_data = [
            ('Plastics', ['HDPE', 'LDPE', 'PET', 'PP', 'PVC', 'PS', 'ABS']),
            ('Metals', ['Aluminum', 'Steel', 'Copper', 'Brass', 'Iron']),
            ('Paper', ['Cardboard', 'Office Paper', 'Newsprint', 'Magazines']),
            ('Glass', ['Clear Glass', 'Colored Glass', 'Bottle Glass']),
            ('Textiles', ['Cotton', 'Polyester', 'Wool', 'Mixed Fabrics'])
        ]
        
        for category_name, subcategories in categories_data:
            category, created = Category.objects.get_or_create(name=category_name)
            if created:
                self.stdout.write(f'  Created category: {category_name}')
            
            for sub_name in subcategories:
                subcategory, created = SubCategory.objects.get_or_create(
                    category=category, 
                    name=sub_name
                )
                if created:
                    self.stdout.write(f'    Created subcategory: {sub_name}')

        # Create some specifications for Plastics (since they have more complex requirements)
        plastic_category = Category.objects.get(name='Plastics')
        
        specifications_data = [
            {'color': 'Natural/Clear', 'material_grade': 'virgin_grade', 'material_form': 'pellets_granules'},
            {'color': 'White', 'material_grade': 'industrial_grade', 'material_form': 'flakes'},
            {'color': 'Mixed Colors', 'material_grade': 'recycled_grade', 'material_form': 'regrind'},
            {'color': 'Black', 'material_grade': 'automotive_grade', 'material_form': 'pellets_granules'},
            {'color': 'Blue', 'material_grade': 'food_grade', 'material_form': 'sheets'},
        ]
        
        for spec_data in specifications_data:
            spec, created = CategorySpecification.objects.get_or_create(
                Category=plastic_category,
                **spec_data
            )
            if created:
                self.stdout.write(f'    Created specification: {spec}')

    def create_user_with_data(self, email, password, name, company_name, is_admin):
        """Create a user with company and 10 auctions"""
        self.stdout.write(f'\nCreating user: {email}')
        
        # Create company first
        company = self.create_company(company_name)
        
        # Create user
        user = User.objects.create(
            username=email.split('@')[0],  # Use email prefix as username
            email=email,
            password=make_password(password),
            name=name,
            first_name=name.split()[0],
            last_name=' '.join(name.split()[1:]) if len(name.split()) > 1 else '',
            company=company,
            is_staff=is_admin,
            is_superuser=is_admin,
            is_primary_contact=True,
            contact_type='primary',
            position='CEO' if is_admin else 'Sales Manager',
            can_place_ads=True,
            can_place_bids=True,
            role='Admin' if is_admin else 'Staff'
        )
        
        self.stdout.write(f'  Created user: {user.email} (Admin: {is_admin})')
        
        # Create 10 auctions for this user
        self.create_auctions(user)

    def create_company(self, company_name):
        """Create a company with approved status"""
        # Generate a unique VAT number
        vat_number = f'SE{random.randint(100000000, 999999999)}'
        
        company = Company.objects.create(
            official_name=company_name,
            vat_number=vat_number,
            email=f'info@{company_name.lower().replace(" ", "").replace("ab", "")}.se',
            sector=random.choice(['manufacturing  & Production', 'recycling', 'packaging']),
            country='Sweden',
            website=f'https://{company_name.lower().replace(" ", "").replace("ab", "")}.se',
            status='approved',  # Make sure company is approved
            payment_ready=True,  # Allow payments
            stripe_onboarding_complete=True,
            stripe_capabilities_complete=True,
            stripe_account_id=f'acct_test_{random.randint(1000000, 9999999)}',  # Mock Stripe account
            last_payment_check=timezone.now()
        )
        
        self.stdout.write(f'  Created company: {company.official_name} (Status: {company.status})')
        return company

    def create_auctions(self, user):
        """Create 10 active auctions for the user"""
        self.stdout.write(f'  Creating 10 auctions for {user.email}...')
        
        locations = self.create_sample_locations()
        
        # Set auction dates in October 2025 as requested
        base_date = datetime(2025, 10, 13)
        
        auction_templates = [
            {
                'title': 'High Quality HDPE Bottles Regrind',
                'description': 'Clean HDPE regrind from milk bottles, excellent for manufacturing new containers.',
                'category_name': 'Plastics',
                'subcategory_name': 'HDPE',
                'quantity': random.randint(5, 50),
                'starting_price': random.randint(800, 1200),
            },
            {
                'title': 'Industrial Grade PET Flakes', 
                'description': 'Post-consumer PET flakes from beverage bottles, ready for recycling.',
                'category_name': 'Plastics',
                'subcategory_name': 'PET',
                'quantity': random.randint(10, 80),
                'starting_price': random.randint(600, 1000),
            },
            {
                'title': 'Clean Aluminum Scrap',
                'description': 'Mixed aluminum scrap from automotive and construction industry.',
                'category_name': 'Metals',
                'subcategory_name': 'Aluminum', 
                'quantity': random.randint(20, 100),
                'starting_price': random.randint(1500, 2500),
            },
            {
                'title': 'Premium PP Pellets',
                'description': 'Virgin grade polypropylene pellets suitable for food packaging.',
                'category_name': 'Plastics',
                'subcategory_name': 'PP',
                'quantity': random.randint(15, 60),
                'starting_price': random.randint(900, 1400),
            },
            {
                'title': 'Office Paper Waste Bundle',
                'description': 'Clean office paper waste, perfect for recycling into new paper products.',
                'category_name': 'Paper',
                'subcategory_name': 'Office Paper',
                'quantity': random.randint(30, 150),
                'starting_price': random.randint(200, 400),
            },
            {
                'title': 'Steel Scrap Collection',
                'description': 'Industrial steel scrap from manufacturing processes.',
                'category_name': 'Metals',
                'subcategory_name': 'Steel',
                'quantity': random.randint(50, 200),
                'starting_price': random.randint(300, 600),
            },
            {
                'title': 'Clear Glass Bottles',
                'description': 'Mixed clear glass bottles from beverage industry.',
                'category_name': 'Glass', 
                'subcategory_name': 'Clear Glass',
                'quantity': random.randint(25, 120),
                'starting_price': random.randint(150, 300),
            },
            {
                'title': 'LDPE Film Rolls',
                'description': 'Clean LDPE film from packaging operations.',
                'category_name': 'Plastics',
                'subcategory_name': 'LDPE',
                'quantity': random.randint(10, 40),
                'starting_price': random.randint(700, 1100),
            },
            {
                'title': 'Copper Wire Scrap',
                'description': 'High purity copper wire from electrical installations.',
                'category_name': 'Metals',
                'subcategory_name': 'Copper',
                'quantity': random.randint(5, 30),
                'starting_price': random.randint(5000, 8000),
            },
            {
                'title': 'Mixed Cardboard Bales',
                'description': 'Compressed cardboard bales from retail packaging.',
                'category_name': 'Paper',
                'subcategory_name': 'Cardboard', 
                'quantity': random.randint(40, 180),
                'starting_price': random.randint(100, 250),
            }
        ]
        
        for i, template in enumerate(auction_templates):
            # Get category and subcategory
            try:
                category = Category.objects.get(name=template['category_name'])
                subcategory = SubCategory.objects.get(category=category, name=template['subcategory_name'])
            except (Category.DoesNotExist, SubCategory.DoesNotExist):
                continue
            
            # Create auction start date (varying dates in October 2025)
            auction_start = timezone.make_aware(base_date + timedelta(days=random.randint(-5, 5)))
            auction_end = auction_start + timedelta(days=7)  # 7-day auctions
            
            # Get random location
            location = random.choice(locations)
            
            # Create a unique specification for plastic materials (since it's OneToOneField)
            specification = None
            if template['category_name'] == 'Plastics':
                try:
                    # Create a unique specification for each ad
                    specification = CategorySpecification.objects.create(
                        Category=category,
                        color=random.choice(['Natural/Clear', 'White', 'Black', 'Blue', 'Mixed Colors']),
                        material_grade=random.choice(['virgin_grade', 'industrial_grade', 'recycled_grade']),
                        material_form=random.choice(['pellets_granules', 'flakes', 'regrind']),
                        additional_specifications=f"Specification for {template['title']}"
                    )
                except Exception:
                    # If creation fails, leave specification as None
                    pass
            
            ad = Ad.objects.create(
                user=user,
                category=category,
                subcategory=subcategory,
                specific_material=f"{subcategory.name} - {template['title']}",
                packaging=random.choice(['baled', 'loose', 'big_bag', 'container']),
                material_frequency=random.choice(['one_time', 'monthly', 'weekly']),
                specification=specification,
                additional_specifications="High quality material suitable for industrial use",
                origin=random.choice(['post_industrial', 'post_consumer', 'mix']),
                contamination=random.choice(['clean', 'slightly_contaminated']),
                additives=random.choice(['no_additives', 'uv_stabilizer', 'antioxidant']),
                storage_conditions=random.choice(['climate_controlled', 'protected_outdoor']),
                processing_methods=[random.choice(['injection_moulding', 'extrusion', 'blow_moulding'])],
                location=location,
                delivery_options=['local_delivery', 'national_shipping'],
                available_quantity=Decimal(str(template['quantity'])),
                unit_of_measurement='tons',
                minimum_order_quantity=Decimal('1'),
                starting_bid_price=Decimal(str(template['starting_price'])),
                currency='EUR',
                auction_duration=7,
                title=template['title'],
                description=template['description'],
                keywords=f"{subcategory.name}, recycling, materials, {category.name.lower()}",
                status='active',
                auction_start_date=auction_start,
                auction_end_date=auction_end,
                is_complete=True,
                allow_broker_bids=True,
                current_step=8,
                # Set all step completion flags to True
                step_1_complete=True,
                step_2_complete=True,
                step_3_complete=True,
                step_4_complete=True,
                step_5_complete=True,
                step_6_complete=True,
                step_7_complete=True,
                step_8_complete=True,
            )
            
            self.stdout.write(f'    Created auction {i+1}: {ad.title}')

    def create_sample_locations(self):
        """Create sample locations in Sweden"""
        locations_data = [
            {'city': 'Stockholm', 'state_province': 'Stockholm County', 'postal_code': '111 29'},
            {'city': 'Gothenburg', 'state_province': 'Västra Götaland', 'postal_code': '411 03'},
            {'city': 'Malmö', 'state_province': 'Skåne County', 'postal_code': '211 20'},
            {'city': 'Uppsala', 'state_province': 'Uppsala County', 'postal_code': '751 05'},
            {'city': 'Västerås', 'state_province': 'Västmanland County', 'postal_code': '721 30'},
        ]
        
        locations = []
        for loc_data in locations_data:
            location, _ = Location.objects.get_or_create(
                country='Sweden',
                city=loc_data['city'],
                defaults={
                    'state_province': loc_data['state_province'],
                    'postal_code': loc_data['postal_code'],
                    'address_line': f'{loc_data["city"]} Industrial Area',
                }
            )
            locations.append(location)
            
        return locations