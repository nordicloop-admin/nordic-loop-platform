from base.utils.responses import RepositoryResponse
from base.services.logging import LoggingService
from django.db.models import Q
from django.utils import timezone
from datetime import datetime
from .models import Ad
from .serializer import AdSerializer
from category.models import Category, SubCategory

logging_service = LoggingService()

class AdRepository:
    def create_ad(self, data, files=None) -> RepositoryResponse:
        try:

            category_name = data.pop("category")
            subcategory_name = data.pop("subcategory")
            end_date = data.pop("end_date")
            end_time = data.pop("end_time")

            country_of_origin = data.get("country_of_origin")
            if country_of_origin and country_of_origin.lower() != "sweden":
                return RepositoryResponse(success=False, message="We are currently not operating in that location", data=None)

            category = Category.objects.filter(name__iexact=category_name).first()
            if not category:
                return RepositoryResponse(success=False, message="Category not found", data=None)

            subcategory = SubCategory.objects.filter(
                name__iexact=subcategory_name, category=category
            ).first()
            if not subcategory:
                return RepositoryResponse(
                    success=False, message="Subcategory not found or doesn't belong to the category", data=None
                )

            item_image = files.get("item_image") if files else None

            ad = Ad.objects.create(
                item_name=data.get("item_name"),
                category=category,
                subcategory=subcategory,
                description=data.get("description"),
                base_price=data.get("base_price"),
                volume=data.get("volume"),
                unit=data.get("unit"),
                country_of_origin=data.get("country_of_origin"),
                end_date=end_date,  
                end_time=end_time,  
                item_image=item_image,
            )

            return RepositoryResponse(success= True, message="Ad created successfully", data=AdSerializer(ad).data)

        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(False, "Failed to create an ad", None)

    def update_ad(self, ad_id, data, files=None) -> RepositoryResponse:
        try:
            ad = Ad.objects.filter(id=ad_id).first()
            if not ad:
                return RepositoryResponse(False, "Ad not found", None)

            if "category" in data:
                category = Category.objects.filter(name__iexact=data.pop("category")).first()
                if not category:
                    return RepositoryResponse(False, "Category not found", None)
                ad.category = category

            if "subcategory" in data:
                subcategory = SubCategory.objects.filter(name__iexact=data.pop("subcategory"), category=ad.category).first()
                if not subcategory:
                    return RepositoryResponse(False, "Subcategory not found or doesn't belong to the category", None)
                ad.subcategory = subcategory

            if "end_date" in data:
                try:
                    ad.end_date = datetime.strptime(data.pop('end_date'), "%Y-%m-%d").date()
                except ValueError:
                    return RepositoryResponse(False, "Invalid end date format", None)

            if "end_time" in data:
                try:
                    ad.end_time = datetime.strptime(data.pop('end_time'), "%H:%M:%S").time()
                except ValueError:
                    return RepositoryResponse(False, "Invalid end time format", None)

            if files and files.get("item_image"):
                ad.item_image = files.get("item_image")


            for key, value in data.items():
                setattr(ad, key, value)

            ad.save()

            return RepositoryResponse(True, "Ad updated successfully", AdSerializer(ad).data)

        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(False, "Failed to update the ad", None)

    def delete_ad(self, ad_id) -> RepositoryResponse:
        try:
            ad = Ad.objects.filter(id=ad_id).first()
            if not ad:
                return RepositoryResponse(False, "Ad not found", None)

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
