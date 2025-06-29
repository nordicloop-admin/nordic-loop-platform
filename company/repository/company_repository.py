from django.db.models import Q
from django.core.paginator import Paginator
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

    def get_admin_companies_filtered(self, search=None, status=None, page=1, page_size=10) -> RepositoryResponse:
        """
        Get companies for admin with filtering and pagination support
        """
        try:
            queryset = Company.objects.all().order_by('-registration_date')
            
            # Apply search filter
            if search:
                queryset = queryset.filter(
                    Q(official_name__icontains=search) |
                    Q(vat_number__icontains=search) |
                    Q(email__icontains=search) |
                    Q(country__icontains=search) |
                    Q(primary_first_name__icontains=search) |
                    Q(primary_last_name__icontains=search) |
                    Q(primary_email__icontains=search)
                )
            
            # Apply status filter
            if status and status != 'all':
                if status in ['pending', 'approved', 'rejected']:
                    queryset = queryset.filter(status=status)
            
            # Apply pagination
            paginator = Paginator(queryset, page_size)
            
            try:
                companies_page = paginator.page(page)
            except:
                # If page number is out of range, return first page
                companies_page = paginator.page(1)
            
            pagination_data = {
                'count': paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': companies_page.number,
                'page_size': page_size,
                'next': companies_page.has_next(),
                'previous': companies_page.has_previous(),
                'results': list(companies_page.object_list)
            }
            
            return RepositoryResponse(
                success=True,
                message="Companies retrieved successfully",
                data=pagination_data,
            )
        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(
                success=False,
                message="Failed to get companies",
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
