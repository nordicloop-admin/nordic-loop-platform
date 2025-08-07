from rest_framework import serializers
from .models import PricingPlan, BaseFeature, PlanFeature, PricingPageContent


class PlanFeatureSerializer(serializers.ModelSerializer):
    """
    Serializer for plan features with computed display text
    """
    feature_text = serializers.CharField(source='display_text', read_only=True)
    feature_name = serializers.CharField(source='base_feature.name', read_only=True)
    category = serializers.CharField(source='base_feature.category', read_only=True)

    class Meta:
        model = PlanFeature
        fields = [
            'id', 'feature_text', 'feature_name', 'category',
            'is_included', 'feature_value', 'order', 'is_highlighted'
        ]


class PricingPlanSerializer(serializers.ModelSerializer):
    """
    Serializer for pricing plans with their features
    """
    features = PlanFeatureSerializer(source='plan_features', many=True, read_only=True)

    class Meta:
        model = PricingPlan
        fields = [
            'id', 'name', 'plan_type', 'price', 'currency',
            'color', 'is_popular', 'is_active', 'order', 'features'
        ]


class PricingPageContentSerializer(serializers.ModelSerializer):
    """
    Serializer for pricing page content
    """
    class Meta:
        model = PricingPageContent
        fields = ['id', 'title', 'subtitle', 'section_label', 'cta_text', 'cta_url']
