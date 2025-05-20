from django.db.models import Q
from base.utils.responses import RepositoryResponse
from base.services.logging import LoggingService
from company.models import Company

logging_service = LoggingService()


class CompanyRepository:
    def create_company(self, data) -> RepositoryResponse:

        try:
            company = Company.objects.create(**data)
            return RepositoryResponse(
                success=True,
                message="Company created successfully",
                data=company,
            )
        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(
                success=False,
                message="Failed to create company",
                data=None,
            )

    def get_company_by_id(self, id) -> RepositoryResponse:
   
        try:
            company = Company.objects.get(id=id)
            return RepositoryResponse(
                success=True,
                message="Company found",
                data=company,
            )
        except Company.DoesNotExist:
            return RepositoryResponse(
                success=False,
                message="Company not found",
                data=None,
            )
        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(
                success=False,
                message="Failed to get company",
                data=None,
            )

    def get_company_by_vat(self, vat_number) -> RepositoryResponse:
        try:
            company = Company.objects.get(vat_number=vat_number)
            return RepositoryResponse(
                success=True,
                message="Company found",
                data=company,
            )
        except Company.DoesNotExist:
            return RepositoryResponse(
                success=False,
                message="Company not found",
                data=None,
            )
        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(
                success=False,
                message="Failed to get company",
                data=None,
            )

    def get_company_by_email(self, email) -> RepositoryResponse:
        try:
            company = Company.objects.get(email=email)
            return RepositoryResponse(
                success=True,
                message="Company found",
                data=company,
            )
        except Company.DoesNotExist:
            return RepositoryResponse(
                success=False,
                message="Company not found",
                data=None,
            )
        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(
                success=False,
                message="Failed to get company",
                data=None,
            )

    def search_companies(self, query) -> RepositoryResponse:
        try:
            companies = Company.objects.filter(
                Q(official_name__icontains=query) |
                Q(vat_number__icontains=query) |
                Q(email__icontains=query) |
                Q(primary_email__icontains=query)
            )
            return RepositoryResponse(
                success=True,
                message="Companies found",
                data=companies,
            )
        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(
                success=False,
                message="Failed to search companies",
                data=None,
            )

    def get_companies_by_status(self, status) -> RepositoryResponse:
        try:
            companies = Company.objects.filter(status=status)
            return RepositoryResponse(
                success=True,
                message=f"Companies with status '{status}' found",
                data=companies,
            )
        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(
                success=False,
                message="Failed to get companies by status",
                data=None,
            )

    def update_company(self, id, data) -> RepositoryResponse:
        try:
            company = Company.objects.get(id=id)
            for key, value in data.items():
                setattr(company, key, value)
            company.save()
            return RepositoryResponse(
                success=True,
                message="Company updated successfully",
                data=company,
            )
        except Company.DoesNotExist:
            return RepositoryResponse(
                success=False,
                message="Company not found",
                data=None,
            )
        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(
                success=False,
                message="Failed to update company",
                data=None,
            )

    def delete_company(self, id) -> RepositoryResponse:
        try:
            company = Company.objects.get(id=id)
            company.delete()
            return RepositoryResponse(
                success=True,
                message="Company deleted successfully",
                data=None,
            )
        except Company.DoesNotExist:
            return RepositoryResponse(
                success=False,
                message="Company not found",
                data=None,
            )
        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(
                success=False,
                message="Failed to delete company",
                data=None,
            )
        
    
    def list_companies(self) -> RepositoryResponse:
        try:
            companies = Company.objects.all()
            return RepositoryResponse(
                success=True,
                message="Companies found",
                data=companies,
            )
        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(
                success=False,
                message="Failed to get companies",
                data=None,
            )
