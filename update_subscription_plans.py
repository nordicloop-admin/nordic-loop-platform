#!/usr/bin/env python3
"""
Script to update the pricing database with the new subscription plans
Based on the subscription plans from the UI:
- Free Plan: 0.00 SEK
- Standard Plan: 799.00 SEK / Month
- Premium Plan: 999.00 SEK / Month (Most Popular)
"""
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from pricing.models import PricingPlan, BaseFeature, PlanFeature, PricingPageContent


def update_subscription_plans():
    """Update the database with the new subscription plans"""
    
    print("Updating pricing page content...")
    # Update pricing page content
    content, created = PricingPageContent.objects.get_or_create(
        defaults={
            'title': 'Flexible Business Plans for Sustainable Growth',
            'subtitle': 'Flexible plans for every business; whether you\'re just starting or looking to scale sustainability.',
            'section_label': 'Pricing',
            'cta_text': 'Get Started',
            'cta_url': '/coming-soon'
        }
    )
    print(f"Pricing page content {'created' if created else 'updated'}")
    
    print("\nUpdating base features...")
    
    # Define base features (reusable across plans)
    base_features_data = [
        {
            'name': 'marketplace_listings',
            'category': 'marketplace',
            'base_description': '{value} marketplace listings',
            'order': 1
        },
        {
            'name': 'monthly_auctions',
            'category': 'auctions',
            'base_description': '{value} monthly auctions',
            'order': 2
        },
        {
            'name': 'reporting',
            'category': 'reporting',
            'base_description': '{value} reporting',
            'order': 3
        },
        {
            'name': 'discussion_forums',
            'category': 'community',
            'base_description': 'Participation in discussion forums for industry insights',
            'order': 4
        },
        {
            'name': 'commission_fee',
            'category': 'commission',
            'base_description': '{value} commission fee on trades',
            'order': 5
        },
        {
            'name': 'account_verification',
            'category': 'verification',
            'base_description': 'Verified account status and company ratings',
            'order': 6
        },
        {
            'name': 'customer_support',
            'category': 'support',
            'base_description': '{value} customer support with faster response times',
            'order': 7
        },
        {
            'name': 'sample_requests',
            'category': 'access',
            'base_description': '{value} sample request functionality',
            'order': 8
        },
        {
            'name': 'contact_access',
            'category': 'access',
            'base_description': 'Access to contact information',
            'order': 9
        },
        {
            'name': 'priority_listing',
            'category': 'access',
            'base_description': 'Priority listing and access',
            'order': 10
        }
    ]
    
    # Create or update base features
    base_features = {}
    for feature_data in base_features_data:
        feature, created = BaseFeature.objects.get_or_create(
            name=feature_data['name'],
            defaults=feature_data
        )
        base_features[feature_data['name']] = feature
        if created:
            print(f"  Created base feature: {feature.name}")
    
    print("\nUpdating pricing plans...")
    
    # Updated pricing plans with new prices
    plans_data = [
        {
            'name': 'Free Plan',
            'plan_type': 'free',
            'price': 0.00,
            'order': 1,
            'is_popular': False
        },
        {
            'name': 'Standard Plan',
            'plan_type': 'standard',
            'price': 799.00,  # Updated price
            'order': 2,
            'is_popular': False
        },
        {
            'name': 'Premium Plan',
            'plan_type': 'premium',
            'price': 999.00,  # Updated price
            'order': 3,
            'is_popular': True  # Most Popular
        }
    ]
    
    plans = {}
    for plan_data in plans_data:
        # Update existing plan or create new one
        plan, created = PricingPlan.objects.update_or_create(
            plan_type=plan_data['plan_type'],
            defaults={
                'name': plan_data['name'],
                'price': plan_data['price'],
                'currency': 'SEK',
                'color': '#FF8A00',  # Updated to match the orange theme
                'is_popular': plan_data['is_popular'],
                'is_active': True,
                'order': plan_data['order']
            }
        )
        plans[plan_data['plan_type']] = plan
        print(f"  {'Created' if created else 'Updated'} plan: {plan.name} - {plan.price} SEK/month")
    
    print("\nConfiguring plan features...")
    
    # Define plan-specific feature configurations based on the UI
    plan_features_config = {
        'free': [
            {'feature': 'marketplace_listings', 'value': 'Limited', 'order': 1},
            {'feature': 'monthly_auctions', 'value': 'Limited', 'order': 2},
            {'feature': 'reporting', 'value': 'Basic', 'order': 3},
            {'feature': 'discussion_forums', 'value': None, 'order': 4},
            {'feature': 'commission_fee', 'value': '7%', 'order': 5},
        ],
        'standard': [
            {'feature': 'marketplace_listings', 'value': 'Unlimited', 'order': 1},
            {'feature': 'monthly_auctions', 'value': 'Unlimited', 'order': 2},
            {'feature': 'reporting', 'value': 'Advanced', 'order': 3},
            {'feature': 'discussion_forums', 'value': None, 'order': 4},
            {'feature': 'commission_fee', 'value': '5%', 'order': 5},
            {'feature': 'account_verification', 'value': None, 'order': 6},
            {'feature': 'customer_support', 'value': 'Premium', 'order': 7},
        ],
        'premium': [
            {'feature': 'commission_fee', 'value': '2%', 'order': 1, 'highlighted': True},
            {'feature': 'sample_requests', 'value': 'Advanced', 'order': 2, 'highlighted': True},
            {'feature': 'contact_access', 'value': None, 'order': 3, 'highlighted': True},
            {'feature': 'priority_listing', 'value': None, 'order': 4, 'highlighted': True},
            {'feature': 'marketplace_listings', 'value': 'Unlimited', 'order': 5},
            {'feature': 'monthly_auctions', 'value': 'Unlimited', 'order': 6},
            {'feature': 'reporting', 'value': 'Advanced', 'order': 7},
            {'feature': 'discussion_forums', 'value': None, 'order': 8},
            {'feature': 'account_verification', 'value': None, 'order': 9},
            {'feature': 'customer_support', 'value': 'Premium', 'order': 10},
        ]
    }
    
    # Clear existing plan features and create new ones
    for plan_type, features_config in plan_features_config.items():
        plan = plans[plan_type]
        print(f"  Updating features for {plan.name}:")
        
        # Remove existing features for this plan
        PlanFeature.objects.filter(plan=plan).delete()
        
        for config in features_config:
            feature_name = config['feature']
            base_feature = base_features[feature_name]
            
            plan_feature = PlanFeature.objects.create(
                plan=plan,
                base_feature=base_feature,
                is_included=True,
                feature_value=config['value'],
                order=config['order'],
                is_highlighted=config.get('highlighted', False)
            )
            
            print(f"    + {base_feature.name}: {config['value'] or 'included'}")
    
    print(f"\nSubscription plans update completed!")
    print(f"Total plans: {PricingPlan.objects.count()}")
    print(f"Total base features: {BaseFeature.objects.count()}")
    print(f"Total plan features: {PlanFeature.objects.count()}")
    
    # Display final pricing summary
    print(f"\nFinal Pricing Summary:")
    for plan in PricingPlan.objects.filter(is_active=True).order_by('order'):
        popular_text = " (Most Popular)" if plan.is_popular else ""
        print(f"  - {plan.name}: {plan.price} {plan.currency}/Month{popular_text}")


if __name__ == '__main__':
    update_subscription_plans()
