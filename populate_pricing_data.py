#!/usr/bin/env python3
"""
Script to populate the pricing database with current pricing data
"""
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from pricing.models import PricingPlan, PricingFeature, PricingPageContent


def populate_pricing_data():
    """Populate the database with current pricing data"""
    
    print("Creating pricing page content...")
    # Create or update pricing page content
    content, created = PricingPageContent.objects.get_or_create(
        defaults={
            'title': 'Flexible Business Plans for Sustainable Growth',
            'subtitle': 'Flexible plans for every business; whether you\'re just starting or looking to scale sustainability.',
            'section_label': 'Pricing',
            'cta_text': 'Get Started',
            'cta_url': '/coming-soon'
        }
    )
    print(f"Pricing page content {'created' if created else 'already exists'}")
    
    print("\nCreating pricing plans...")
    
    # Free Plan
    free_plan, created = PricingPlan.objects.get_or_create(
        plan_type='free',
        defaults={
            'name': 'Free Plan',
            'price': 0,
            'currency': 'SEK',
            'color': '#008066',
            'is_popular': False,
            'is_active': True,
            'order': 1
        }
    )
    print(f"Free plan {'created' if created else 'already exists'}")
    
    # Free plan features
    free_features = [
        'Limited marketplace listings',
        'Limited monthly auctions',
        'Basic reporting',
        'Participation in discussion forums for industry insights',
        '9% commission fee on trades'
    ]
    
    for i, feature_text in enumerate(free_features):
        feature, created = PricingFeature.objects.get_or_create(
            plan=free_plan,
            feature_text=feature_text,
            defaults={
                'is_included': True,
                'order': i + 1
            }
        )
    
    # Standard Plan
    standard_plan, created = PricingPlan.objects.get_or_create(
        plan_type='standard',
        defaults={
            'name': 'Standard Plan',
            'price': 599,
            'currency': 'SEK',
            'color': '#008066',
            'is_popular': False,
            'is_active': True,
            'order': 2
        }
    )
    print(f"Standard plan {'created' if created else 'already exists'}")
    
    # Standard plan features
    standard_features = [
        'Unlimited marketplace listings',
        'Unlimited monthly auctions',
        'Advanced reporting',
        'Participation in discussion forums for industry insights',
        '7% commission fee on trades',
        'Verified account status and company ratings',
        'Premium customer support with faster response times'
    ]
    
    for i, feature_text in enumerate(standard_features):
        feature, created = PricingFeature.objects.get_or_create(
            plan=standard_plan,
            feature_text=feature_text,
            defaults={
                'is_included': True,
                'order': i + 1
            }
        )
    
    # Premium Plan
    premium_plan, created = PricingPlan.objects.get_or_create(
        plan_type='premium',
        defaults={
            'name': 'Premium Plan',
            'price': 799,
            'currency': 'SEK',
            'color': '#008066',
            'is_popular': True,  # Mark as popular
            'is_active': True,
            'order': 3
        }
    )
    print(f"Premium plan {'created' if created else 'already exists'}")
    
    # Premium plan features
    premium_features = [
        'No commission fees on trades',
        'Advanced sample request functionality',
        'Access to contact information',
        'Priority listing and access',
        'Unlimited marketplace listings',
        'Unlimited monthly auctions',
        'Advanced reporting',
        'Participation in discussion forums for industry insights',
        'Verified account status and company ratings',
        'Premium customer support with faster response times'
    ]
    
    for i, feature_text in enumerate(premium_features):
        feature, created = PricingFeature.objects.get_or_create(
            plan=premium_plan,
            feature_text=feature_text,
            defaults={
                'is_included': True,
                'order': i + 1
            }
        )
    
    print(f"\nPricing data population completed!")
    print(f"Total plans: {PricingPlan.objects.count()}")
    print(f"Total features: {PricingFeature.objects.count()}")


if __name__ == '__main__':
    populate_pricing_data()
