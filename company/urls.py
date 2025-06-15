from django.urls import path
from company.view import CompanyView, ApproveCompanyView, CompanyAdminViewSet
from rest_framework.routers import DefaultRouter

urlpatterns = [
    path("create/", CompanyView.as_view(), name="create-company"),  
    path("<int:company_id>/", CompanyView.as_view(), name="get-update-delete-company"),  
    path("get/by-vat/<str:vat>/", CompanyView.as_view(), name="get-company-by-vat"), 
    path("", CompanyView.as_view(), name="list-companies"),  

    path("approve/<int:company_id>/", ApproveCompanyView.as_view(), name="approve_deney_companies"),
]

# Admin endpoints
router = DefaultRouter()
router.register(r'admin/companies', CompanyAdminViewSet, basename='admin-companies')

urlpatterns += router.urls
