from django.db.models import Q
from accounts.models import Company
from users.models import CustomUser

class CompanyRepository:
    @staticmethod
    def create_company(
        vat_number: str,
        official_name: str,
        business_address: str,
        phone_number: str,
        user: CustomUser,
        **extra_fields
    ) -> Company:
        company = Company(
            vat_number=vat_number,
            official_name=official_name,
            business_address=business_address,
            phone_number=phone_number,
            user=user,
            **extra_fields
        )
        company.save()
        return company
    
    @staticmethod
    def get_company_by_vat(vat_number: str) -> Company:
        return Company.objects.filter(vat_number=vat_number).first()
    
    @staticmethod
    def get_company_by_id(company_id: int) -> Company:
        return Company.objects.filter(id=company_id).first()
    
    @staticmethod
    def search_companies(query: str):
        return Company.objects.filter(
            Q(official_name__icontains=query) |
            Q(vat_number__icontains=query) |
            Q(email__icontains=query)
        )
    
    @staticmethod
    def update_company(company: Company, **kwargs) -> Company:
        for key, value in kwargs.items():
            setattr(company, key, value)
        company.save()
        return company
    
    @staticmethod
    def delete_company(company: Company):
        company.delete()