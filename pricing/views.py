from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import PricingPlan, PricingPageContent
from .serializers import PricingPlanSerializer, PricingPageContentSerializer


class PricingPlanListView(generics.ListAPIView):
    """
    API view to retrieve all active pricing plans with their features
    """
    serializer_class = PricingPlanSerializer
    
    def get_queryset(self):
        return PricingPlan.objects.filter(is_active=True).prefetch_related(
            'plan_features__base_feature'
        )


class PricingPageContentView(generics.RetrieveAPIView):
    """
    API view to retrieve pricing page content
    """
    serializer_class = PricingPageContentSerializer
    
    def get_object(self):
        # Get the first (and should be only) pricing page content
        content, created = PricingPageContent.objects.get_or_create(
            defaults={
                'title': 'Flexible Business Plans for Sustainable Growth',
                'subtitle': 'Flexible plans for every business; whether you\'re just starting or looking to scale sustainability.',
                'section_label': 'Pricing',
                'cta_text': 'Get Started',
                'cta_url': '/coming-soon'
            }
        )
        return content


@api_view(['GET'])
def pricing_data(request):
    """
    Combined API endpoint that returns both pricing plans and page content
    """
    try:
        # Get pricing plans
        plans = PricingPlan.objects.filter(is_active=True).prefetch_related(
            'plan_features__base_feature'
        )
        plans_serializer = PricingPlanSerializer(plans, many=True)
        
        # Get page content
        content, created = PricingPageContent.objects.get_or_create(
            defaults={
                'title': 'Flexible Business Plans for Sustainable Growth',
                'subtitle': 'Flexible plans for every business; whether you\'re just starting or looking to scale sustainability.',
                'section_label': 'Pricing',
                'cta_text': 'Get Started',
                'cta_url': '/coming-soon'
            }
        )
        content_serializer = PricingPageContentSerializer(content)
        
        return Response({
            'success': True,
            'data': {
                'page_content': content_serializer.data,
                'pricing_plans': plans_serializer.data
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
