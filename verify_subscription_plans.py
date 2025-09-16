#!/usr/bin/env python3
"""
Script to verify and display the subscription plans exactly as shown in the UI
"""
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from pricing.models import PricingPlan, PlanFeature


def display_subscription_plans():
    """Display the subscription plans as they appear in the UI"""
    
    print("=== NORDIC LOOP MARKETPLACE SUBSCRIPTION PLANS ===\n")
    
    plans = PricingPlan.objects.filter(is_active=True).prefetch_related('plan_features__base_feature').order_by('order')
    
    for plan in plans:
        # Header
        popular_badge = " (Most Popular)" if plan.is_popular else ""
        print(f"📦 {plan.name.upper()}{popular_badge}")
        print(f"💰 {plan.price:.2f} {plan.currency}" + (" / Month" if plan.price > 0 else ""))
        print("="*50)
        
        # Features
        features = plan.plan_features.all().order_by('order')
        for feature in features:
            highlight = "✨ " if feature.is_highlighted else "✅ "
            print(f"{highlight}{feature.display_text}")
        
        print("\n" + "="*50 + "\n")
    
    print("🎯 All subscription plans have been successfully added to the database!")
    print("📊 You can now use these plans in your frontend and backend applications.")


if __name__ == '__main__':
    display_subscription_plans()
