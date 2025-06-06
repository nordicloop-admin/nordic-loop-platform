from base.utils.responses import RepositoryResponse
from base.services.logging import LoggingService
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Ad, Location
from .serializer import (
    AdCreateSerializer, AdStep1Serializer, AdStep2Serializer, AdStep3Serializer,
    AdStep4Serializer, AdStep5Serializer, AdStep6Serializer, AdStep7Serializer,
    AdStep8Serializer, AdCompleteSerializer, AdListSerializer, AdUpdateSerializer
)
from category.models import Category, SubCategory, CategorySpecification
from users.models import User
from typing import Optional, Dict, Any, List

logging_service = LoggingService()


class AdRepository:
    
    def get_step_serializer(self, step: int):
        """Get the appropriate serializer for a step"""
        serializers = {
            1: AdStep1Serializer,
            2: AdStep2Serializer,
            3: AdStep3Serializer,
            4: AdStep4Serializer,
            5: AdStep5Serializer,
            6: AdStep6Serializer,
            7: AdStep7Serializer,
            8: AdStep8Serializer,
        }
        return serializers.get(step)

    def create_new_ad(self, user: User) -> RepositoryResponse:
        """Create a new empty ad for step-by-step completion"""
        try:
            if not user or not user.is_authenticated:
                return RepositoryResponse(False, "Authentication required", None)

            # Check if user can create ads (assuming this method exists on User model)
            # if not user.can_place_ads:
            #     return RepositoryResponse(False, "You are not allowed to place ads", None)

            ad = Ad.objects.create(
                user=user,
                current_step=1,
                is_complete=False,
                is_active=False
            )

            return RepositoryResponse(True, "Ad created successfully", ad)

        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(False, "Failed to create ad", None)

    def create_ad_with_step1(self, data: Dict[str, Any], files: Optional[Dict[str, Any]] = None, user: Optional[User] = None) -> RepositoryResponse:
        """Create a new ad with step 1 (material type) data"""
        try:
            if not user or not user.is_authenticated:
                return RepositoryResponse(False, "Authentication required", None)

            # Create new ad with step 1 data
            ad = Ad.objects.create(
                user=user,
                current_step=2,  # Move to step 2 after completing step 1
                is_complete=False,
                is_active=False
            )

            # Update with step 1 data using the step 1 serializer
            serializer = AdStep1Serializer(ad, data=data, partial=True)
            if serializer.is_valid():
                updated_ad = serializer.save()
                return RepositoryResponse(True, "Ad created with step 1 data", updated_ad)
            else:
                # Delete the ad if validation fails
                ad.delete()
                return RepositoryResponse(False, "Validation failed", serializer.errors)

        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(False, "Failed to create ad with step 1 data", None)

    def get_ad_by_id(self, ad_id: int, user: Optional[User] = None) -> RepositoryResponse:
        """Get ad by ID with optional user ownership check"""
        try:
            query = Q(id=ad_id)
            
            # If user is provided, check ownership for non-complete ads
            if user:
                query = Q(id=ad_id) & (Q(user=user) | Q(is_complete=True, is_active=True))
            
            ad = Ad.objects.filter(query).first()
            
            if not ad:
                return RepositoryResponse(False, "Ad not found", None)

            return RepositoryResponse(True, "Ad retrieved successfully", ad)

        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(False, "Failed to retrieve ad", None)

    def update_ad_step(self, ad_id: int, step: int, data: Dict[str, Any], 
                      files: Optional[Dict[str, Any]] = None, user: Optional[User] = None) -> RepositoryResponse:
        """Update a specific step of the ad"""
        try:
            if not user or not user.is_authenticated:
                return RepositoryResponse(False, "Authentication required", None)

            ad = Ad.objects.filter(id=ad_id, user=user).first()
            if not ad:
                return RepositoryResponse(False, "Ad not found or access denied", None)

            if step < 1 or step > 8:
                return RepositoryResponse(False, "Invalid step", None)

            # Get the appropriate serializer
            serializer_class = self.get_step_serializer(step)
            if not serializer_class:
                return RepositoryResponse(False, f"Serializer for step {step} not found", None)

            # Handle file uploads for step 8
            if files and step == 8:
                data.update(files)

            serializer = serializer_class(ad, data=data, partial=True)
            if serializer.is_valid():
                updated_ad = serializer.save()
                return RepositoryResponse(True, f"Step {step} updated successfully", updated_ad)
            else:
                return RepositoryResponse(False, "Validation failed", serializer.errors)

        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(False, f"Failed to update step {step}", None)

    def delete_ad(self, ad_id: int, user: User) -> RepositoryResponse:
        """Delete an ad (only by owner)"""
        try:
            if not user or not user.is_authenticated:
                return RepositoryResponse(False, "Authentication required", None)

            ad = Ad.objects.filter(id=ad_id, user=user).first()
            if not ad:
                return RepositoryResponse(False, "Ad not found or access denied", None)

            ad.delete()
            return RepositoryResponse(True, "Ad deleted successfully", None)

        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(False, "Failed to delete ad", None)

    def list_ads(self, category_id: Optional[int] = None, subcategory_id: Optional[int] = None,
                origin: Optional[str] = None, contamination: Optional[str] = None,
                location_country: Optional[str] = None, location_city: Optional[str] = None,
                only_complete: bool = True) -> RepositoryResponse:
        """List ads with optional filtering"""
        try:
            query = Q()
            
            if only_complete:
                query &= Q(is_complete=True, is_active=True)
            
            # Apply filters
            if category_id:
                query &= Q(category_id=category_id)
            if subcategory_id:
                query &= Q(subcategory_id=subcategory_id)
            if origin:
                query &= Q(origin=origin)
            if contamination:
                query &= Q(contamination=contamination)
            if location_country:
                query &= Q(location__country__icontains=location_country)
            if location_city:
                query &= Q(location__city__icontains=location_city)

            ads = Ad.objects.filter(query).select_related(
                'category', 'subcategory', 'location', 'user'
            ).order_by('-created_at')

            return RepositoryResponse(True, "Ads retrieved successfully", list(ads))

        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(False, "Failed to retrieve ads", None)

    def list_user_ads(self, user: User, only_complete: bool = False) -> RepositoryResponse:
        """List ads belonging to a specific user"""
        try:
            query = Q(user=user)
            if only_complete:
                query &= Q(is_complete=True)

            ads = Ad.objects.filter(query).select_related(
                'category', 'subcategory', 'location'
            ).order_by('-updated_at')

            return RepositoryResponse(True, "User ads retrieved successfully", list(ads))

        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(False, "Failed to retrieve user ads", None)

    def get_ad_step_data(self, ad_id: int, step: int, user: Optional[User] = None) -> RepositoryResponse:
        """Get specific step data for an ad"""
        try:
            ad_response = self.get_ad_by_id(ad_id, user)
            if not ad_response.success:
                return ad_response

            ad = ad_response.data
            serializer_class = self.get_step_serializer(step)
            if not serializer_class:
                return RepositoryResponse(False, f"Invalid step {step}", None)

            serializer = serializer_class(ad)
            return RepositoryResponse(True, f"Step {step} data retrieved", serializer.data)

        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(False, f"Failed to get step {step} data", None)

    def validate_step_data(self, step: int, data: Dict[str, Any]) -> RepositoryResponse:
        """Validate step data without saving"""
        try:
            serializer_class = self.get_step_serializer(step)
            if not serializer_class:
                return RepositoryResponse(False, f"Invalid step {step}", None)

            serializer = serializer_class(data=data)
            is_valid = serializer.is_valid()
            
            if is_valid:
                return RepositoryResponse(True, f"Step {step} data is valid", True)
            else:
                return RepositoryResponse(False, "Validation failed", serializer.errors)

        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(False, "Validation error", None)

    def get_user_ad_statistics(self, user: User) -> RepositoryResponse:
        """Get statistics about user's ads"""
        try:
            stats = {
                'total_ads': Ad.objects.filter(user=user).count(),
                'complete_ads': Ad.objects.filter(user=user, is_complete=True).count(),
                'active_ads': Ad.objects.filter(user=user, is_active=True).count(),
                'draft_ads': Ad.objects.filter(user=user, is_complete=False).count(),
                'ads_by_step': {}
            }

            # Get ads count by current step
            for step in range(1, 9):
                count = Ad.objects.filter(user=user, current_step=step, is_complete=False).count()
                stats['ads_by_step'][f'step_{step}'] = count

            return RepositoryResponse(True, "Statistics retrieved", stats)

        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(False, "Failed to get statistics", None)

    def activate_ad(self, ad_id: int, user: User) -> RepositoryResponse:
        """Activate an ad for bidding (only if complete)"""
        try:
            ad = Ad.objects.filter(id=ad_id, user=user).first()
            if not ad:
                return RepositoryResponse(False, "Ad not found or access denied", None)

            if not ad.is_complete:
                return RepositoryResponse(False, "Ad must be complete before activation", None)

            ad.is_active = True
            ad.auction_start_date = timezone.now()
            
            # Calculate auction end date based on duration
            if ad.auction_duration:
                ad.auction_end_date = ad.auction_start_date + timedelta(days=ad.auction_duration)
            
            ad.save()

            return RepositoryResponse(True, "Ad activated successfully", ad)

        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(False, "Failed to activate ad", None)

    def deactivate_ad(self, ad_id: int, user: User) -> RepositoryResponse:
        """Deactivate an ad"""
        try:
            ad = Ad.objects.filter(id=ad_id, user=user).first()
            if not ad:
                return RepositoryResponse(False, "Ad not found or access denied", None)

            ad.is_active = False
            ad.save()

            return RepositoryResponse(True, "Ad deactivated successfully", ad)

        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(False, "Failed to deactivate ad", None)

    def get_ads_by_category(self, category_id: int) -> RepositoryResponse:
        """Get all ads in a specific category"""
        try:
            ads = Ad.objects.filter(
                category_id=category_id, 
                is_complete=True, 
                is_active=True
            ).select_related('category', 'subcategory', 'location')

            return RepositoryResponse(True, "Category ads retrieved", list(ads))

        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(False, "Failed to get category ads", None)

    def search_ads(self, search_term: str) -> RepositoryResponse:
        """Search ads by title, description, or keywords"""
        try:
            query = Q(is_complete=True, is_active=True) & (
                Q(title__icontains=search_term) |
                Q(description__icontains=search_term) |
                Q(keywords__icontains=search_term) |
                Q(category__name__icontains=search_term) |
                Q(subcategory__name__icontains=search_term)
            )

            ads = Ad.objects.filter(query).select_related(
                'category', 'subcategory', 'location'
            ).order_by('-created_at')

            return RepositoryResponse(True, "Search completed", list(ads))

        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(False, "Search failed", None)

    def update_complete_ad(self, ad_id: int, data: Dict[str, Any], files: Optional[Dict[str, Any]] = None, user: Optional[User] = None) -> RepositoryResponse:
        """Update complete ad with all provided fields"""
        try:
            if not user or not user.is_authenticated:
                return RepositoryResponse(False, "Authentication required", None)

            ad = Ad.objects.filter(id=ad_id, user=user).first()
            if not ad:
                return RepositoryResponse(False, "Ad not found or access denied", None)

            # Handle file uploads
            if files:
                data.update(files)

            # Use AdUpdateSerializer for validation and update
            serializer = AdUpdateSerializer(ad, data=data, partial=False)  # Complete update
            if serializer.is_valid():
                updated_ad = serializer.save()
                return RepositoryResponse(True, "Ad updated successfully", updated_ad)
            else:
                return RepositoryResponse(False, "Validation failed", serializer.errors)

        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(False, "Failed to update ad", None)

    def partial_update_ad(self, ad_id: int, data: Dict[str, Any], files: Optional[Dict[str, Any]] = None, user: Optional[User] = None) -> RepositoryResponse:
        """Partially update ad with only provided fields"""
        try:
            if not user or not user.is_authenticated:
                return RepositoryResponse(False, "Authentication required", None)

            ad = Ad.objects.filter(id=ad_id, user=user).first()
            if not ad:
                return RepositoryResponse(False, "Ad not found or access denied", None)

            # Handle file uploads
            if files:
                data.update(files)

            # Use AdUpdateSerializer for validation and partial update
            serializer = AdUpdateSerializer(ad, data=data, partial=True)  # Partial update
            if serializer.is_valid():
                updated_ad = serializer.save()
                return RepositoryResponse(True, "Ad partially updated successfully", updated_ad)
            else:
                return RepositoryResponse(False, "Validation failed", serializer.errors)

        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(False, "Failed to partially update ad", None)

    # Legacy methods for backward compatibility
    def create_ad_step1(self, data, user=None) -> RepositoryResponse:
        """Legacy method - use create_new_ad instead"""
        return self.create_new_ad(user)

    def list_ads_by_user(self, user: User) -> RepositoryResponse:
        """Legacy method - use list_user_ads instead"""
        return self.list_user_ads(user)