from django.urls import path
from company.view import CompanyView

urlpatterns = [
    path("companies/create/", CompanyView.as_view(), name="create-company"),  
    path("companies/<int:company_id>/", CompanyView.as_view(), name="get-update-delete-company"),  
    path("companies/by-vat/<str:vat>/", CompanyView.as_view(), name="get-company-by-vat"), 
    path("companies/", CompanyView.as_view(), name="list-companies"),  
]
