from django.urls import path
from .view import CompanyView, ApproveCompanyView, AdminCompanyListView, AdminCompanyDetailView, CompanyFiltersView

urlpatterns = [
    path("", CompanyView.as_view(), name="company-list-create"),
    path("create/", CompanyView.as_view(), name="company-create"),  # Explicit create endpoint
    path("filters/", CompanyFiltersView.as_view(), name="company-filters"),  # Filter options endpoint
    path("<int:company_id>/", CompanyView.as_view(), name="company-detail"),
    path("vat/<str:vat>/", CompanyView.as_view(), name="company-by-vat"),
    path("<int:company_id>/approve/", ApproveCompanyView.as_view(), name="approve-company"),

    # Admin endpoints
    path("admin/companies/", AdminCompanyListView.as_view(), name="admin-company-list"),
    path("admin/companies/<int:company_id>/", AdminCompanyDetailView.as_view(), name="admin-company-detail"),
]
