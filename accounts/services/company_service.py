from accounts.repositories.company_repository import CompanyRepository
from accounts.models import Company
from users.models import CustomUser
from typing import List, Optional
from django.contrib.auth.hashers import make_password


class CompanyService:
    """
    Service class for company-related operations.
    This class handles business logic related to companies.
    """

    @staticmethod
    def register_company(
        vat_number: str,
        official_name: str,
        business_address: str,
        phone_number: str,
        email: str,
        password: str,
        website: str = None
    ) -> Company:
        """
        Register a new company.

        Args:
            vat_number: Company's VAT number
            official_name: Company's official name
            business_address: Company's business address
            phone_number: Company's phone number
            email: Company's email address (will be used for login)
            password: Password for the company account
            website: Company's website (optional)

        Returns:
            The created company object

        Raises:
            ValueError: If required fields are missing or if a company with the same VAT number already exists
        """
        # Validate required fields
        if not vat_number:
            raise ValueError("VAT number is required")
        if not official_name:
            raise ValueError("Official name is required")
        if not business_address:
            raise ValueError("Business address is required")
        if not phone_number:
            raise ValueError("Phone number is required")
        if not email:
            raise ValueError("Email is required")
        if not password:
            raise ValueError("Password is required")

        # Check if company with this VAT number already exists
        existing_company = CompanyRepository.get_company_by_vat(vat_number)
        if existing_company:
            raise ValueError(f"Company with VAT number {vat_number} already exists")

        # Hash the password using Django's password hashing
        hashed_password = make_password(password)

        # Create the company
        company = Company(
            vat_number=vat_number,
            official_name=official_name,
            business_address=business_address,
            phone_number=phone_number,
            email=email,
            password=hashed_password,
            website=website,
            status='pending'
        )
        company.save()

        return company

    @staticmethod
    def get_company_by_vat(vat_number: str) -> Optional[Company]:
        """
        Get a company by VAT number.

        Args:
            vat_number: Company's VAT number

        Returns:
            The company object if found, None otherwise
        """
        return CompanyRepository.get_company_by_vat(vat_number)

    @staticmethod
    def get_company_by_id(company_id: int) -> Optional[Company]:
        """
        Get a company by ID.

        Args:
            company_id: Company's ID

        Returns:
            The company object if found, None otherwise
        """
        return CompanyRepository.get_company_by_id(company_id)

    @staticmethod
    def search_companies(query: str) -> List[Company]:
        """
        Search for companies by name, VAT number, or email.

        Args:
            query: Search query

        Returns:
            List of matching companies
        """
        return CompanyRepository.search_companies(query)

    @staticmethod
    def update_company(company: Company, **kwargs) -> Company:
        """
        Update a company's information.

        Args:
            company: The company to update
            **kwargs: Fields to update

        Returns:
            The updated company object
        """
        return CompanyRepository.update_company(company, **kwargs)

    @staticmethod
    def delete_company(company: Company) -> None:
        """
        Delete a company.

        Args:
            company: The company to delete
        """
        CompanyRepository.delete_company(company)

    @staticmethod
    def approve_company(company_id: int, admin_user=None) -> Company:
        """
        Approve a company and create a user account.

        Args:
            company_id: ID of the company to approve
            admin_user: The admin user who approved the company (optional)

        Returns:
            The approved company object

        Raises:
            ValueError: If the company doesn't exist or is already rejected
        """
        return CustomUser.objects.approve_company(company_id, admin_user=admin_user)

    @staticmethod
    def reject_company(company_id: int) -> Company:
        """
        Reject a company.

        Args:
            company_id: ID of the company to reject

        Returns:
            The rejected company object

        Raises:
            ValueError: If the company doesn't exist
        """
        return CustomUser.objects.reject_company(company_id)

    @staticmethod
    def get_pending_companies() -> List[Company]:
        """
        Get all companies with pending status.

        Returns:
            List of pending companies
        """
        return Company.objects.filter(status='pending')

    @staticmethod
    def get_approved_companies() -> List[Company]:
        """
        Get all companies with approved status.

        Returns:
            List of approved companies
        """
        return Company.objects.filter(status='approved')

    @staticmethod
    def get_rejected_companies() -> List[Company]:
        """
        Get all companies with rejected status.

        Returns:
            List of rejected companies
        """
        return Company.objects.filter(status='rejected')
