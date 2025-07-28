from company.models import Company
from base.services.logging import LoggingService
from typing import Dict, Any, Optional, List
from company.repository.company_repository import CompanyRepository
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()
logging_service = LoggingService()

class  CompanyService:

    def __init__(self, company_repository: CompanyRepository):
         self.repository = company_repository


    @transaction.atomic
    def create_company(self, company_data: Dict[str, Any]) -> Company:
        try:
            # Separate company data from contact data
            contact_data = self._extract_contact_data(company_data)
            clean_company_data = self._extract_company_data(company_data)

            # Validate required company fields
            required_company_fields = ['vat_number', 'official_name', 'email']
            for field in required_company_fields:
                if field not in clean_company_data or not clean_company_data[field]:
                    raise ValueError(f"{field.replace('_', ' ').title()} is required")

            # Validate required contact fields
            if contact_data['primary']:
                primary = contact_data['primary']
                required_contact_fields = ['first_name', 'last_name', 'email']
                for field in required_contact_fields:
                    if field not in primary or not primary[field]:
                        raise ValueError(f"Primary contact {field.replace('_', ' ')} is required")

            # Check for duplicates
            if self.repository.get_company_by_vat(clean_company_data['vat_number']).data:
                raise ValueError(f"Company with VAT number {clean_company_data['vat_number']} already exists")

            if self.repository.get_company_by_email(clean_company_data['email']).data:
                raise ValueError(f"Company with email {clean_company_data['email']} already exists")

            # Set default status
            clean_company_data.setdefault('status', 'pending')

            # Create the company
            company = self.repository.create_company(clean_company_data).data

            # Create contact users
            self._create_contact_users(company, contact_data)

            return company
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def _extract_company_data(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract only company-related fields from the input data"""
        company_fields = [
            'official_name', 'vat_number', 'email', 'country', 'sector', 'website', 'status'
        ]
        return {key: value for key, value in company_data.items() if key in company_fields}

    def _extract_contact_data(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract contact-related fields from the input data"""
        contact_data = {'primary': None, 'secondary': None}

        # Extract primary contact
        if any(key.startswith('primary_') for key in company_data.keys()):
            contact_data['primary'] = {
                'first_name': company_data.get('primary_first_name', ''),
                'last_name': company_data.get('primary_last_name', ''),
                'email': company_data.get('primary_email', ''),
                'position': company_data.get('primary_position', ''),
            }

        # Extract secondary contact
        if any(key.startswith('secondary_') for key in company_data.keys()):
            secondary_data = {
                'first_name': company_data.get('secondary_first_name', ''),
                'last_name': company_data.get('secondary_last_name', ''),
                'email': company_data.get('secondary_email', ''),
                'position': company_data.get('secondary_position', ''),
            }
            # Only include secondary if it has meaningful data
            if any(secondary_data.values()):
                contact_data['secondary'] = secondary_data

        return contact_data

    def _create_contact_users(self, company: Company, contact_data: Dict[str, Any]) -> None:
        """Create User records for company contacts"""

        # Create primary contact user
        if contact_data['primary']:
            primary = contact_data['primary']
            if primary['email']:  # Only create if email exists
                # Check if user already exists with this email
                existing_user = User.objects.filter(email=primary['email']).first()
                if existing_user:
                    # Update existing user to be primary contact for this company
                    existing_user.company = company
                    existing_user.first_name = primary['first_name']
                    existing_user.last_name = primary['last_name']
                    existing_user.position = primary['position']
                    existing_user.contact_type = 'primary'
                    existing_user.is_primary_contact = True
                    existing_user.save()
                else:
                    # Create new user with unique username
                    username = self._generate_unique_username(primary['email'])
                    User.objects.create(
                        username=username,
                        email=primary['email'],
                        first_name=primary['first_name'],
                        last_name=primary['last_name'],
                        company=company,
                        position=primary['position'],
                        contact_type='primary',
                        is_primary_contact=True,
                        is_active=True,
                    )

        # Create secondary contact user
        if contact_data['secondary']:
            secondary = contact_data['secondary']
            if secondary['email']:  # Only create if email exists
                # Check if user already exists with this email
                existing_user = User.objects.filter(email=secondary['email']).first()
                if existing_user:
                    # Update existing user to be secondary contact for this company
                    existing_user.company = company
                    existing_user.first_name = secondary['first_name']
                    existing_user.last_name = secondary['last_name']
                    existing_user.position = secondary['position']
                    existing_user.contact_type = 'secondary'
                    existing_user.is_primary_contact = False
                    existing_user.save()
                else:
                    # Create new user with unique username
                    username = self._generate_unique_username(secondary['email'])
                    User.objects.create(
                        username=username,
                        email=secondary['email'],
                        first_name=secondary['first_name'],
                        last_name=secondary['last_name'],
                        company=company,
                        position=secondary['position'],
                        contact_type='secondary',
                        is_primary_contact=False,
                        is_active=True,
                    )

    def _generate_unique_username(self, email: str) -> str:
        """Generate a unique username from email"""
        base_username = email.split('@')[0]
        username = base_username
        counter = 1

        while User.objects.filter(username=username).exists():
            username = f"{base_username}_{counter}"
            counter += 1

        return username



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
    

    def delete_company(self, company: Company) -> None:
        """Delete a company"""
        try:
            self.repository.delete_company(company.id)
        except Exception as e:
            logging_service.log_error(e)
            raise e 
        

    def update_company(self, company_id: int, data: Dict[str, Any]) -> Company:
        """Update a company"""
        try:
            company = self.repository.update_company(company_id, data).data
            return company
        except Exception as e:
            logging_service.log_error(e)
            raise e
    
    def list_companies(self) -> List[Company]:
        """List all companies"""
        try:
            companies = self.repository.list_companies().data
            return companies
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def get_admin_companies_filtered(self, search=None, status=None, page=1, page_size=10) -> Dict[str, Any]:
        """
        Get filtered companies for admin with pagination
        """
        try:
            result = self.repository.get_admin_companies_filtered(search, status, page, page_size)
            if result.success:
                return result.data
            else:
                raise Exception(result.message)
        except Exception as e:
            logging_service.log_error(e)
            raise e
