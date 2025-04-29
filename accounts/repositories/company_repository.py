from django.db.models import Q
from accounts.models import Company
from base.utils.responses import RepositoryResponse
from base.services.logging import LoggingService

logging_service = LoggingService()


class CompanyRepository:
    """
    A class to manage CRUD operations for Company
    """

    def create_company(self, user, data) -> RepositoryResponse:
        """
        Creates a new company for the user
        """
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
        """
        Get a company by ID
        """
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
        """
        Get a company by VAT number
        """
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
        """
        Get a company by email
        """
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
        """
        Search for companies by name, VAT number, or email
        """
        try:
            companies = Company.objects.filter(
                Q(official_name__icontains=query) |
                Q(vat_number__icontains=query) |
                Q(email__icontains=query) |
                Q(contact_email__icontains=query)
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
        """
        Get companies by status
        """
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
        """
        Update a company with the provided data
        """
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
        """
        Delete a company
        """
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