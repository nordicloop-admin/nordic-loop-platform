from django.contrib.auth.hashers import make_password
from django.utils import timezone
from accounts.repositories.company_repository import CompanyRepository
from accounts.models import Company, Account
from users.models import CustomUser
from users.repositories.user_repository import UserRepository
from base.services.logging import LoggingService
from typing import Dict, Any, Optional, List

logging_service = LoggingService()


class CompanyService:
    def __init__(self, company_repository: CompanyRepository, user_repository: UserRepository):
        self.repository = company_repository
        self.user_repository = user_repository

    def register_company(self, company_data: Dict[str, Any]) -> Company:
        """Register a new company with validation and password hashing"""
        try:
            # Validate required fields
            required_fields = ['vat_number', 'official_name', 'email',
                              'contact_name', 'contact_email', 'password']

            for field in required_fields:
                if field not in company_data or not company_data[field]:
                    raise ValueError(f"{field.replace('_', ' ').title()} is required")

            # Check for existing company with same VAT number or email
            if self.repository.get_company_by_vat(company_data['vat_number']).data:
                raise ValueError(f"Company with VAT number {company_data['vat_number']} already exists")

            if self.repository.get_company_by_email(company_data['email']).data:
                raise ValueError(f"Company with email {company_data['email']} already exists")

            # Hash the password
            raw_password = company_data.pop('password')
            company_data['password'] = make_password(raw_password)

            # Set default status
            company_data.setdefault('status', 'pending')

            # Create the company
            company = self.repository.create_company(company_data).data
            return company
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def get_company_by_id(self, company_id: int) -> Optional[Company]:
        """Get a company by ID"""
        try:
            company = self.repository.get_company_by_id(company_id).data
            return company
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def get_company_by_vat(self, vat_number: str) -> Optional[Company]:
        """Get a company by VAT number"""
        try:
            company = self.repository.get_company_by_vat(vat_number).data
            return company
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def get_company_by_email(self, email: str) -> Optional[Company]:
        """Get a company by email"""
        try:
            company = self.repository.get_company_by_email(email).data
            return company
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def search_companies(self, query: str) -> List[Company]:
        """Search for companies"""
        try:
            companies = self.repository.search_companies(query).data
            return companies
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def update_company(self, company: Company, **kwargs) -> Company:
        """Update a company"""
        try:
            # Special handling for password
            if 'password' in kwargs:
                kwargs['password'] = make_password(kwargs['password'])

            company = self.repository.update_company(company.id, kwargs).data
            return company
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def delete_company(self, company: Company) -> None:
        """Delete a company"""
        try:
            self.repository.delete_company(company.id)
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def approve_company(self, company_id: int, admin_user=None) -> Company:
        """Approve a company and create a user account"""
        try:
            company = self.repository.get_company_by_id(company_id).data

            if not company:
                raise ValueError(f"Company with ID {company_id} does not exist")

            if company.status == 'approved':
                return company

            if company.status == 'rejected':
                raise ValueError("Cannot approve a rejected company")

            # Update company status
            company.status = 'approved'
            company.approval_date = timezone.now()
            company.last_status_change = timezone.now()

            # Find or create user with the company's email
            user_response = self.user_repository.get_user_by_email(company.email)
            user = user_response.data if user_response.success else None

            if not user and company.email and company.password:
                # Create a new user with the registration credentials
                user = CustomUser(
                    email=company.email,
                    name=company.contact_name,
                    username=company.email,
                    is_active=True
                )

                # Set the password directly from the hashed password
                user.password = company.password
                user.save()

                # Create an account for the user
                account = Account(user=user)
                account.save()

                # Clear the password from the company record for security
                company.password = None
            elif user:
                # Activate existing user
                user.is_active = True
                user.save()

                # Create an account if it doesn't exist
                if not hasattr(user, 'account'):
                    account = Account(user=user)
                    account.save()

            # Save the company
            company = self.repository.update_company(company.id, company.__dict__).data
            return company
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def reject_company(self, company_id: int, rejection_reason: str = None) -> Company:
        """Reject a company"""
        try:
            company = self.repository.get_company_by_id(company_id).data

            if not company:
                raise ValueError(f"Company with ID {company_id} does not exist")

            if company.status == 'rejected':
                return company

            # Update company status
            company.status = 'rejected'
            company.last_status_change = timezone.now()

            if rejection_reason:
                company.rejection_reason = rejection_reason

            # Find and deactivate associated user
            user_response = self.user_repository.get_user_by_email(company.email)
            user = user_response.data if user_response.success else None
            if user:
                user.is_active = False
                user.save()

            # Save the company
            company = self.repository.update_company(company.id, company.__dict__).data
            return company
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def get_pending_companies(self) -> List[Company]:
        """Get all pending companies"""
        try:
            companies = self.repository.get_companies_by_status('pending').data
            return companies
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def get_approved_companies(self) -> List[Company]:
        """Get all approved companies"""
        try:
            companies = self.repository.get_companies_by_status('approved').data
            return companies
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def get_rejected_companies(self) -> List[Company]:
        """Get all rejected companies"""
        try:
            companies = self.repository.get_companies_by_status('rejected').data
            return companies
        except Exception as e:
            logging_service.log_error(e)
            raise e
