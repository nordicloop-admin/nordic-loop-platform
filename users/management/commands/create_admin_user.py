from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
from users.models import User
from company.models import Company
from ads.models import Ad, Location
from bids.models import Bid
from category.models import Category, SubCategory


class Command(BaseCommand):
    help = 'Creates a user with admin role, company, ads, and bids'

    def handle(self, *args, **kwargs):
        # Try to find existing company by VAT number
        try:
            company = Company.objects.get(vat_number='SE123456789')
            self.stdout.write(self.style.WARNING(f'Found existing company with VAT number SE123456789: {company.official_name}'))
            
            # Update company details
            company.official_name = "Karera Recycling"
            company.email = 'company@karera.com'
            company.sector = 'recycling'
            company.country = 'Sweden'
            company.website = 'https://karera-recycling.com'
            company.primary_first_name = 'Olivier'
            company.primary_last_name = 'Karera'
            company.primary_email = 'karera@gmail.com'
            company.primary_position = 'CEO'
            company.status = 'approved'
            company.save()
            self.stdout.write(self.style.SUCCESS(f'Updated company: {company.official_name}'))
            created = False
        except Company.DoesNotExist:
            # Create new company
            company = Company.objects.create(
                official_name="Karera Recycling",
                vat_number='SE123456789',
                email='company@karera.com',
                sector='recycling',
                country='Sweden',
                website='https://karera-recycling.com',
                primary_first_name='Olivier',
                primary_last_name='Karera',
                primary_email='karera@gmail.com',
                primary_position='CEO',
                status='approved'
            )
            self.stdout.write(self.style.SUCCESS(f'Created company: {company.official_name}'))
            created = True
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created company: {company.official_name}'))
        else:
            self.stdout.write(self.style.WARNING(f'Company {company.official_name} already exists'))
            
        # Create user
        user, created = User.objects.get_or_create(
            username='karera',
            email='karera@gmail.com',
            defaults={
                'first_name': 'Olivier',
                'last_name': 'Karera',
                'name': 'Olivier Karera',
                'company': company,
                'can_place_ads': True,
                'can_place_bids': True,
                'role': 'Admin',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        
        if created:
            user.set_password('123')
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Created user: {user.username}'))
        else:
            self.stdout.write(self.style.WARNING(f'User {user.username} already exists'))
            # Update user attributes
            user.first_name = 'Olivier'
            user.last_name = 'Karera'
            user.name = 'Olivier Karera'
            user.company = company
            user.can_place_ads = True
            user.can_place_bids = True
            user.role = 'Admin'
            user.is_staff = True
            user.is_superuser = True
            user.set_password('123')
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Updated user: {user.username}'))
            
        # Get or create categories and subcategories
        plastic_category, _ = Category.objects.get_or_create(name="Plastic")
        metal_category, _ = Category.objects.get_or_create(name="Metal")
        
        pet_subcategory, _ = SubCategory.objects.get_or_create(
            name="PET",
            category=plastic_category
        )
        
        aluminum_subcategory, _ = SubCategory.objects.get_or_create(
            name="Aluminum",
            category=metal_category
        )
        
        # Create location
        stockholm_location, _ = Location.objects.get_or_create(
            city="Stockholm",
            country="Sweden",
            postal_code="10055"
        )
        
        # Create ads
        ad1, created = Ad.objects.get_or_create(
            title="Recycled PET Flakes",
            user=user,
            defaults={
                'description': "High-quality recycled PET flakes, clean and ready for processing.",
                'category': plastic_category,
                'subcategory': pet_subcategory,
                'available_quantity': Decimal('1000'),
                'unit_of_measurement': 'kg',
                'starting_bid_price': Decimal('2.50'),
                'currency': 'EUR',
                'packaging': 'big_bag',
                'material_frequency': 'monthly',
                'origin': 'post_consumer',
                'contamination': 'clean',
                'additives': 'no_additives',
                'storage_conditions': 'climate_controlled',
                'location': stockholm_location,
                'delivery_options': ['national_shipping'],
                'auction_duration': 7,
                'auction_end_date': timezone.now() + timedelta(days=7),
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created ad: {ad1.title}'))
        else:
            self.stdout.write(self.style.WARNING(f'Ad {ad1.title} already exists'))
            
        ad2, created = Ad.objects.get_or_create(
            title="Aluminum Scrap",
            user=user,
            defaults={
                'description': "Clean aluminum scrap from industrial sources.",
                'category': metal_category,
                'subcategory': aluminum_subcategory,
                'available_quantity': Decimal('500'),
                'unit_of_measurement': 'kg',
                'starting_bid_price': Decimal('3.75'),
                'currency': 'EUR',
                'packaging': 'container',
                'material_frequency': 'one_time',
                'origin': 'post_industrial',
                'contamination': 'clean',
                'additives': 'no_additives',
                'storage_conditions': 'protected_outdoor',
                'location': stockholm_location,
                'delivery_options': ['pickup_only'],
                'auction_duration': 14,
                'auction_end_date': timezone.now() + timedelta(days=14),
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created ad: {ad2.title}'))
        else:
            self.stdout.write(self.style.WARNING(f'Ad {ad2.title} already exists'))
            
        # Create a second user to place bids
        bidder, _ = User.objects.get_or_create(
            username='bidder',
            email='bidder@example.com',
            defaults={
                'first_name': 'John',
                'last_name': 'Bidder',
                'password': '123',
                'can_place_bids': True,
            }
        )
        bidder.set_password('123')
        bidder.save()
        
        # Create bids on the ads
        bid1, created = Bid.objects.get_or_create(
            user=bidder,
            ad=ad1,
            defaults={
                'bid_price_per_unit': Decimal('2.75'),
                'volume_requested': Decimal('500'),
                'volume_type': 'partial',
                'status': 'active',
                'notes': 'Interested in regular supply if quality is good.'
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created bid on {ad1.title}'))
        else:
            self.stdout.write(self.style.WARNING(f'Bid on {ad1.title} already exists'))
            
        bid2, created = Bid.objects.get_or_create(
            user=bidder,
            ad=ad2,
            defaults={
                'bid_price_per_unit': Decimal('4.00'),
                'volume_requested': Decimal('500'),
                'volume_type': 'full',
                'status': 'active',
                'notes': 'Can pick up immediately.'
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created bid on {ad2.title}'))
        else:
            self.stdout.write(self.style.WARNING(f'Bid on {ad2.title} already exists'))
            
        self.stdout.write(self.style.SUCCESS('Setup completed successfully!'))
        self.stdout.write(self.style.SUCCESS(f'User created: {user.username} (email: {user.email}, password: 123)'))
        self.stdout.write(self.style.SUCCESS(f'Company: {company.official_name}'))
        self.stdout.write(self.style.SUCCESS(f'Ads created: {ad1.title}, {ad2.title}'))
        self.stdout.write(self.style.SUCCESS(f'Bids created on both ads'))
