from base.utils.responses import RepositoryResponse
from base.services.logging import LoggingService
from django.db.models import Q
from django.utils import timezone
from datetime import datetime
from .models import Ad
from .serializer import AdStep1Serializer, AdStep2Serializer, AdStep3Serializer,AdStep4Serializer,AdStep5Serializer, AdStep6Serializer
from category.models import Category, SubCategory
from users.models import User


logging_service = LoggingService()

class AdRepository:
    def create_ad_step1(self, data, user=None) -> RepositoryResponse:
        try:
            if not user or not user.is_authenticated or not user.can_place_ads:
                return RepositoryResponse(False, "You are not allowed to place ads", None)

            category_id = data.get("category_id")
            subcategory_id = data.get("subcategory_id")

            category = Category.objects.filter(id=category_id).first()
            subcategory = SubCategory.objects.filter(id=subcategory_id, category=category).first()

            if not category:
                return RepositoryResponse(False, "Category not found", None)
            if not subcategory:
                return RepositoryResponse(False, "Subcategory not found or doesn't belong to the category", None)

            ad = Ad.objects.create(
                item_name=data.get("item_name"),
                category=category,
                subcategory=subcategory,
                sector=data.get("sector"),
                material_frequency=data.get("material_frequency"),
                user=user
            )

            return RepositoryResponse(True, "Step 1 completed", AdStep1Serializer(ad).data)

        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(False, "Failed at step 1", None)

    def update_ad_step(self, ad_id, data, step=2) -> RepositoryResponse:
        try:
            ad = Ad.objects.filter(id=ad_id).first()
            if not ad:
                return RepositoryResponse(False, "Ad not found", None)

            step_serializers = {
                2: AdStep2Serializer,
                3: AdStep3Serializer,
                4: AdStep4Serializer,
                5: AdStep5Serializer,
                6: AdStep6Serializer
            }

            serializer_class = step_serializers.get(step)
            if not serializer_class:
                return RepositoryResponse(False, f"Step {step} is not supported", None)

            serializer = serializer_class(ad, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return RepositoryResponse(True, f"Step {step} updated", serializer.data)
            return RepositoryResponse(False, "Invalid data", serializer.errors)

        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(False, f"Failed at step {step}", None)

    def delete_ad(self, ad_id, user=None) -> RepositoryResponse:
        try:
            if not user or not user.is_authenticated:
                return RepositoryResponse(False, "Authentication required", None)

            ad = Ad.objects.filter(id=ad_id).first()
            if not ad:
                return RepositoryResponse(False, "Ad not found", None)

            if ad.user != user:
                return RepositoryResponse(False, "You are not allowed to delete this ad", None)

            ad.delete()
            return RepositoryResponse(True, "Ad deleted successfully", None)

        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(False, "Failed to delete the ad", None)

    def list_ads(self) -> RepositoryResponse:
        try:
            ads = Ad.objects.all().order_by("-end_date", "-end_time")
            serialized_ads = AdStep1Serializer(ads, many=True).data
            return RepositoryResponse(True, "Ads retrieved successfully", serialized_ads)
        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(False, "Failed to retrieve ads", None)

    def list_ads_by_user(self, user: User) -> RepositoryResponse:
        try:
            ads = Ad.objects.filter(user=user).order_by("-end_date", "-end_time")
            return RepositoryResponse(True, "User ads retrieved", ads)
        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(False, "Failed to retrieve user ads", None)