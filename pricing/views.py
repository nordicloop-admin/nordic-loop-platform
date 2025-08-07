from rest_framework import generics, status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import api_view, action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .models import PricingPlan, BaseFeature, PlanFeature, PricingPageContent
from .serializers import (
    PricingPlanSerializer, PricingPageContentSerializer,
    BaseFeatureSerializer, AdminPricingPlanSerializer, AdminPlanFeatureSerializer
)


class PricingPlanListView(generics.ListAPIView):
    """
    API view to retrieve all active pricing plans with their features
    """
    serializer_class = PricingPlanSerializer

    def get_queryset(self):
        return PricingPlan.objects.filter(is_active=True).prefetch_related(
            'plan_features__base_feature'
        )


class BaseFeatureListView(generics.ListAPIView):
    """
    API view to retrieve all base features (public endpoint)
    """
    serializer_class = BaseFeatureSerializer
    queryset = BaseFeature.objects.filter(is_active=True)


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


# Admin-only viewsets
class AdminBaseFeatureViewSet(viewsets.ModelViewSet):
    """
    Admin viewset for managing base features
    """
    queryset = BaseFeature.objects.all()
    serializer_class = BaseFeatureSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    ordering = ['category', 'order']


class AdminPricingPlanViewSet(viewsets.ModelViewSet):
    """
    Admin viewset for managing pricing plans
    """
    queryset = PricingPlan.objects.all()
    serializer_class = AdminPricingPlanSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    ordering = ['order', 'price']

    @action(detail=True, methods=['post'], url_path='features')
    def configure_features(self, request, pk=None):
        """
        Configure features for a specific pricing plan
        """
        try:
            plan = self.get_object()
            features_data = request.data.get('features', [])

            # Clear existing plan features
            PlanFeature.objects.filter(plan=plan).delete()

            # Create new plan features based on configuration
            for feature_config in features_data:
                if not feature_config.get('isIncluded', False):
                    continue

                base_feature_id = feature_config.get('baseFeatureId')
                try:
                    base_feature = BaseFeature.objects.get(id=base_feature_id)
                except BaseFeature.DoesNotExist:
                    continue

                # Generate feature text
                feature_text = base_feature.base_description
                feature_value = feature_config.get('featureValue', '')

                if feature_value and '{value}' in feature_text:
                    feature_text = feature_text.replace('{value}', feature_value)

                # Create plan feature
                PlanFeature.objects.create(
                    plan=plan,
                    base_feature=base_feature,
                    feature_text=feature_text,
                    feature_name=base_feature.name,
                    category=base_feature.category,
                    is_included=True,
                    feature_value=feature_value,
                    order=feature_config.get('order', base_feature.order),
                    is_highlighted=feature_config.get('isHighlighted', False)
                )

            return Response({
                'success': True,
                'message': f'Features configured successfully for {plan.name}',
                'features_count': PlanFeature.objects.filter(plan=plan).count()
            })

        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class AdminPlanFeatureViewSet(viewsets.ModelViewSet):
    """
    Admin viewset for managing plan features
    """
    queryset = PlanFeature.objects.all()
    serializer_class = AdminPlanFeatureSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    ordering = ['plan__order', 'order']


class AdminPricingPageContentView(generics.RetrieveUpdateAPIView):
    """
    Admin view for managing pricing page content
    """
    serializer_class = PricingPageContentSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get_object(self):
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


@api_view(['POST'])
def configure_plan_features(request, plan_id):
    """
    Endpoint to configure features for a specific pricing plan
    Requires authentication
    """
    # Check if user is authenticated
    if not request.user.is_authenticated:
        return Response({
            'success': False,
            'error': 'Authentication credentials were not provided.'
        }, status=status.HTTP_401_UNAUTHORIZED)
    try:
        plan = PricingPlan.objects.get(id=plan_id)
        features_data = request.data.get('features', [])

        # Clear existing plan features
        PlanFeature.objects.filter(plan=plan).delete()

        # Create new plan features based on configuration
        for feature_config in features_data:
            if not feature_config.get('isIncluded', False):
                continue

            base_feature_id = feature_config.get('baseFeatureId')
            try:
                base_feature = BaseFeature.objects.get(id=base_feature_id)
            except BaseFeature.DoesNotExist:
                continue

            # Get feature configuration
            feature_value = feature_config.get('featureValue', '')
            custom_description = feature_config.get('customDescription', '')

            # Create plan feature with correct field names
            PlanFeature.objects.create(
                plan=plan,
                base_feature=base_feature,
                is_included=True,
                custom_description=custom_description if custom_description else None,
                feature_value=feature_value if feature_value else None,
                order=feature_config.get('order', base_feature.order),
                is_highlighted=feature_config.get('isHighlighted', False)
            )

        return Response({
            'success': True,
            'message': f'Features configured successfully for {plan.name}',
            'features_count': PlanFeature.objects.filter(plan=plan).count()
        })

    except PricingPlan.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Plan not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
