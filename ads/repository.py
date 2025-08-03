from base.utils.responses import RepositoryResponse
from base.services.logging import LoggingService
from django.db.models import Q, Count, Max
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Ad, Location, Address, Subscription
from company.models import Company
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

    def get_admin_ads_filtered(self, search=None, status=None, page=1, page_size=10) -> RepositoryResponse:
        """
        Get ads for admin with filtering and pagination support
        """
        try:
            # Start with all ads, including related objects for optimization
            queryset = Ad.objects.select_related(
                'user', 'category', 'location', 'user__company'
            ).prefetch_related('bids').all().order_by('-created_at')
            
            # Apply search filter across multiple fields
            if search:
                queryset = queryset.filter(
                    Q(title__icontains=search) |
                    Q(description__icontains=search) |
                    Q(category__name__icontains=search) |
                    Q(user__username__icontains=search) |
                    Q(user__company__official_name__icontains=search) |
                    Q(specific_material__icontains=search) |
                    Q(keywords__icontains=search)
                )
            
            # Apply status filter
            if status and status != 'all':
                if status == 'active':
                    queryset = queryset.filter(is_active=True, is_complete=True)
                elif status == 'inactive':
                    queryset = queryset.filter(is_active=False)
                elif status == 'pending':
                    queryset = queryset.filter(is_complete=False)
                elif status == 'draft':
                    queryset = queryset.filter(is_complete=False, is_active=False)
            
            # Apply pagination
            paginator = Paginator(queryset, page_size)
            
            try:
                ads_page = paginator.page(page)
            except:
                # If page number is out of range, return first page
                ads_page = paginator.page(1)
            
            pagination_data = {
                'count': paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': ads_page.number,
                'page_size': page_size,
                'next': ads_page.has_next(),
                'previous': ads_page.has_previous(),
                'results': list(ads_page.object_list)
            }
            
            return RepositoryResponse(
                success=True,
                message="Ads retrieved successfully",
                data=pagination_data,
            )
        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(
                success=False,
                message="Failed to get ads",
                data=None,
            )

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
                only_complete: bool = True, exclude_brokers: Optional[bool] = None,
                only_brokers: Optional[bool] = None) -> RepositoryResponse:
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

            # Broker filtering
            if exclude_brokers:
                query &= ~Q(user__company__sector='broker')
            elif only_brokers:
                query &= Q(user__company__sector='broker')

            ads = Ad.objects.filter(query).select_related(
                'category', 'subcategory', 'location', 'user', 'user__company'
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
            ).order_by('-created_at')

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
            
            # Check if the ad is suspended by admin
            if ad.status == 'suspended' and ad.suspended_by_admin:
                return RepositoryResponse(False, "This ad has been suspended by an administrator and cannot be activated. Please contact support for assistance.", None)

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

    def admin_approve_ad(self, ad_id: int, admin_user: User) -> RepositoryResponse:
        """Admin approval for an ad"""
        try:
            # Verify the user is an admin
            if not admin_user.is_staff and not admin_user.is_superuser:
                return RepositoryResponse(False, "Only administrators can approve ads", None)
            
            # Get the ad regardless of owner
            ad = Ad.objects.filter(id=ad_id).first()
            if not ad:
                return RepositoryResponse(False, "Ad not found", None)
            
            # Update the ad status
            ad.status = 'active'
            ad.suspended_by_admin = False
            ad.save()
        
            return RepositoryResponse(True, "Ad approved by administrator", ad)
        
        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(False, "Failed to approve ad", None)

    def admin_suspend_ad(self, ad_id: int, admin_user: User) -> RepositoryResponse:
        """Admin suspension for an ad"""
        try:
            # Verify the user is an admin
            if not admin_user.is_staff and not admin_user.is_superuser:
                return RepositoryResponse(False, "Only administrators can suspend ads", None)
            
            # Get the ad regardless of owner
            ad = Ad.objects.filter(id=ad_id).first()
            if not ad:
                return RepositoryResponse(False, "Ad not found", None)
            
            # Update the ad status
            ad.status = 'suspended'
            ad.suspended_by_admin = True
            ad.is_active = False  # Also deactivate the ad
            ad.save()
        
            return RepositoryResponse(True, "Ad suspended by administrator", ad)
        
        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(False, "Failed to suspend ad", None)

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

    def get_admin_addresses_filtered(self, search=None, type_filter=None, is_verified=None, page=1, page_size=10) -> RepositoryResponse:
        """
        Get addresses for admin with filtering and pagination support
        """
        try:
            # Start with all addresses, including related objects for optimization
            queryset = Address.objects.select_related('company').all().order_by('-created_at')
            
            # Apply search filter across multiple fields
            if search:
                queryset = queryset.filter(
                    Q(company__official_name__icontains=search) |
                    Q(contact_name__icontains=search) |
                    Q(contact_phone__icontains=search) |
                    Q(city__icontains=search) |
                    Q(country__icontains=search) |
                    Q(address_line1__icontains=search) |
                    Q(address_line2__icontains=search)
                )
            
            # Apply type filter
            if type_filter:
                queryset = queryset.filter(type=type_filter)
            
            # Apply is_verified filter
            if is_verified is not None:
                queryset = queryset.filter(is_verified=is_verified)
            
            # Apply pagination
            paginator = Paginator(queryset, page_size)
            
            try:
                addresses_page = paginator.page(page)
            except:
                # If page number is out of range, return first page
                addresses_page = paginator.page(1)
            
            pagination_data = {
                'count': paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': addresses_page.number,
                'page_size': page_size,
                'next': addresses_page.has_next(),
                'previous': addresses_page.has_previous(),
                'results': list(addresses_page.object_list)
            }
            
            return RepositoryResponse(
                success=True,
                message="Addresses retrieved successfully",
                data=pagination_data,
            )
        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(
                success=False,
                message="Failed to get addresses",
                data=None,
            )

    def get_address_by_id(self, address_id: int) -> RepositoryResponse:
        """Get address by ID for admin"""
        try:
            address = Address.objects.select_related('company').filter(id=address_id).first()
            
            if not address:
                return RepositoryResponse(False, "Address not found", None)

            return RepositoryResponse(True, "Address retrieved successfully", address)

        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(False, "Failed to retrieve address", None)

    def update_address_verification(self, address_id: int, is_verified: bool) -> RepositoryResponse:
        """Update address verification status for admin"""
        try:
            address = Address.objects.filter(id=address_id).first()
            
            if not address:
                return RepositoryResponse(False, "Address not found", None)

            address.is_verified = is_verified
            address.save()

            return RepositoryResponse(True, f"Address verification status updated to {is_verified}", address)

        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(False, "Failed to update address verification", None)

    def get_admin_subscriptions_filtered(self, search=None, plan=None, status=None, page=1, page_size=10) -> RepositoryResponse:
        """
        Get subscriptions for admin with filtering and pagination support
        """
        try:
            # Start with all subscriptions, including related objects for optimization
            queryset = Subscription.objects.select_related('company').all().order_by('-start_date')
            
            # Apply search filter across multiple fields
            if search:
                queryset = queryset.filter(
                    Q(company__official_name__icontains=search) |
                    Q(contact_name__icontains=search) |
                    Q(contact_email__icontains=search) |
                    Q(amount__icontains=search)
                )
            
            # Apply plan filter
            if plan:
                queryset = queryset.filter(plan=plan)
            
            # Apply status filter
            if status:
                queryset = queryset.filter(status=status)
            
            # Apply pagination
            paginator = Paginator(queryset, page_size)
            
            try:
                subscriptions_page = paginator.page(page)
            except:
                # If page number is out of range, return first page
                subscriptions_page = paginator.page(1)
            
            pagination_data = {
                'count': paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': subscriptions_page.number,
                'page_size': page_size,
                'next': subscriptions_page.has_next(),
                'previous': subscriptions_page.has_previous(),
                'results': list(subscriptions_page.object_list)
            }
            
            return RepositoryResponse(
                success=True,
                message="Subscriptions retrieved successfully",
                data=pagination_data,
            )
        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(
                success=False,
                message="Failed to get subscriptions",
                data=None,
            )
            
    def get_admin_subscriptions_filtered(self, search=None, plan=None, status=None, page=1, page_size=10) -> RepositoryResponse:
        """
        Get subscriptions for admin with filtering and pagination support
        """
        try:
            # Start with all subscriptions, including related objects for optimization
            queryset = Subscription.objects.select_related('company').all().order_by('-start_date')
            
            # Apply search filter across multiple fields
            if search:
                queryset = queryset.filter(
                    Q(company__official_name__icontains=search) |
                    Q(contact_name__icontains=search) |
                    Q(contact_email__icontains=search) |
                    Q(amount__icontains=search)
                )
            
            # Apply plan filter
            if plan:
                queryset = queryset.filter(plan=plan)
            
            # Apply status filter
            if status:
                queryset = queryset.filter(status=status)
            
            # Apply pagination
            paginator = Paginator(queryset, page_size)
            
            try:
                subscriptions_page = paginator.page(page)
            except:
                # If page number is out of range, return first page
                subscriptions_page = paginator.page(1)
            
            pagination_data = {
                'count': paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': subscriptions_page.number,
                'page_size': page_size,
                'next': subscriptions_page.has_next(),
                'previous': subscriptions_page.has_previous(),
                'results': list(subscriptions_page.object_list)
            }
            
            return RepositoryResponse(
                success=True,
                message="Subscriptions retrieved successfully",
                data=pagination_data,
            )
        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(
                success=False,
                message="Failed to get subscriptions",
                data=None,
            )

    def get_subscription_by_id(self, subscription_id: int) -> RepositoryResponse:
        """Get subscription by ID for admin"""
        try:
            subscription = Subscription.objects.filter(id=subscription_id).first()
            
            if not subscription:
                return RepositoryResponse(False, "Subscription not found", None)

            return RepositoryResponse(True, "Subscription retrieved successfully", subscription)

        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(False, "Failed to retrieve subscription", None)

    def get_company_subscription(self, company_id: int) -> RepositoryResponse:
        """
        Get the latest active subscription for a company
        """
        try:
            # Get the most recent subscription for the company
            subscription = Subscription.objects.filter(
                company_id=company_id
            ).order_by('-end_date').first()
            
            if not subscription:
                return RepositoryResponse(False, "No subscription found for this company", None)

            return RepositoryResponse(True, "Company subscription retrieved successfully", subscription)

        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(False, "Failed to retrieve company subscription", None)
            
    def create_subscription(self, company_id: int, subscription_data: dict) -> RepositoryResponse:
        """
        Create a new subscription for a company
        """
        try:
            # Get the company
            company = Company.objects.get(id=company_id)
            
            # Create the subscription with the company and provided data
            subscription = Subscription.objects.create(
                company=company,
                **subscription_data
            )
            
            return RepositoryResponse(True, "Subscription created successfully", subscription)

        except Company.DoesNotExist:
            return RepositoryResponse(False, "Company not found", None)
        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(False, "Failed to create subscription", None)
            
    def get_company_addresses(self, company_id: int) -> RepositoryResponse:
        """
        Get all addresses for a company
        """
        try:
            addresses = Address.objects.filter(company_id=company_id).order_by('-is_primary', '-created_at')
            
            if not addresses.exists():
                return RepositoryResponse(False, "No addresses found for this company", [])

            return RepositoryResponse(True, "Company addresses retrieved successfully", list(addresses))

        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(False, "Failed to retrieve company addresses", None)
            
    def create_company_address(self, company_id: int, address_data: dict) -> RepositoryResponse:
        """
        Create a new address for a company
        """
        try:
            # If this is set as primary, unset any existing primary addresses of the same type
            if address_data.get('is_primary', False):
                Address.objects.filter(
                    company_id=company_id,
                    type=address_data.get('type'),
                    is_primary=True
                ).update(is_primary=False)
            
            # Create the new address
            address = Address.objects.create(
                company_id=company_id,
                **address_data
            )
            
            return RepositoryResponse(True, "Address created successfully", address)

        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(False, "Failed to create address", None)
            
    def get_address_by_id_for_company(self, address_id: int, company_id: int) -> RepositoryResponse:
        """
        Get a specific address by ID, ensuring it belongs to the specified company
        """
        try:
            address = Address.objects.filter(id=address_id, company_id=company_id).first()
            
            if not address:
                return RepositoryResponse(False, "Address not found or does not belong to this company", None)

            return RepositoryResponse(True, "Address retrieved successfully", address)

        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(False, "Failed to retrieve address", None)
            
    def update_company_address(self, address_id: int, company_id: int, address_data: dict) -> RepositoryResponse:
        """
        Update an existing address for a company
        """
        try:
            # First get the address to ensure it belongs to the company
            address = Address.objects.filter(id=address_id, company_id=company_id).first()
            
            if not address:
                return RepositoryResponse(False, "Address not found or does not belong to this company", None)
            
            # If this is being set as primary, unset any existing primary addresses of the same type
            if address_data.get('is_primary', False) and not address.is_primary:
                Address.objects.filter(
                    company_id=company_id,
                    type=address_data.get('type', address.type),
                    is_primary=True
                ).update(is_primary=False)
            
            # Update the address fields
            for key, value in address_data.items():
                setattr(address, key, value)
            
            address.save()
            
            return RepositoryResponse(True, "Address updated successfully", address)

        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(False, "Failed to update address", None)
            
    def delete_company_address(self, address_id: int, company_id: int) -> RepositoryResponse:
        """
        Delete an address for a company
        """
        try:
            # First get the address to ensure it belongs to the company
            address = Address.objects.filter(id=address_id, company_id=company_id).first()
            
            if not address:
                return RepositoryResponse(False, "Address not found or does not belong to this company", None)
            
            # Store address details for response
            address_type = address.type
            address_city = address.city
            
            # Delete the address
            address.delete()
            
            return RepositoryResponse(True, f"{address_type} address in {address_city} deleted successfully", None)

        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(False, "Failed to delete address", None)