from base.utils.responses import RepositoryResponse
from base.services.logging import LoggingService
from django.db.models import Q
from django.utils import timezone
from datetime import datetime
from .models import Ad
from .serializer import AdSerializer
from category.models import Category, SubCategory
from users.models import User

logging_service = LoggingService()

class AdRepository:
    def create_ad(self, data, files=None, user=None) -> RepositoryResponse:
        try:
            if not user or not user.is_authenticated or not user.can_place_ads:
                return RepositoryResponse(
                    success=False,
                    message="You are not allowed to place ads",
                    data=None
                )

            category_name = data.pop("category")
            subcategory_name = data.pop("subcategory")
            end_date = data.pop("end_date")
            end_time = data.pop("end_time")
            selling_type = data.get("selling_type")

            if selling_type not in ["whole", "partition", "both"]:
                return RepositoryResponse(success=False, message="Invalid selling type", data=None)

            if selling_type in ["whole", "both"] and not data.get("base_price"):
                return RepositoryResponse(success=False, message="Base price is required", data=None)

            if selling_type in ["partition", "both"]:
                if not data.get("price_per_partition") or not data.get("volume"):
                    return RepositoryResponse(success=False, message="Partition price and volume are required", data=None)

            country_of_origin = data.get("country_of_origin")
            if country_of_origin and country_of_origin.lower() != "sweden":
                return RepositoryResponse(
                    success=False,
                    message="We are currently not operating in that location",
                    data=None
                )

            category = Category.objects.filter(name__iexact=category_name).first()
            if not category:
                return RepositoryResponse(success=False, message="Category not found", data=None)

            subcategory = SubCategory.objects.filter(
                name__iexact=subcategory_name, category=category
            ).first()
            if not subcategory:
                return RepositoryResponse(
                    success=False,
                    message="Subcategory not found or doesn't belong to the category",
                    data=None
                )

            item_image = files.get("item_image") if files else None

            ad = Ad.objects.create(
                item_name=data.get("item_name"),
                category=category,
                subcategory=subcategory,
                description=data.get("description"),
                base_price=data.get("base_price"),
                price_per_partition=data.get("price_per_partition"),
                volume=data.get("volume"),
                unit=data.get("unit"),
                country_of_origin=data.get("country_of_origin"),
                end_date=end_date,
                end_time=end_time,
                item_image=item_image,
                user=user,
                selling_type=selling_type
            )

            return RepositoryResponse(
                success=True,
                message="Ad created successfully",
                data=AdSerializer(ad).data
            )

        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(False, "Failed to create an ad", None)
        
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
            serialized_ads = AdSerializer(ads, many=True).data
            return RepositoryResponse(True, "Ads retrieved successfully", serialized_ads)
        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(False, "Failed to retrieve ads", None)
