from company.models import Company
from base.services.logging import LoggingService
from typing import Dict, Any, Optional, List
from company.repository.company_repository import CompanyRepository

logging_service = LoggingService()

class  CompanyService:

    def __init__(self, company_repository: CompanyRepository):
         self.repository = company_repository


    def create_company(self, company_data: Dict[str, Any]) -> Company:
        try:
            # Validate required fields
            required_fields = ['vat_number', 'official_name', 'email',
                            'primary_first_name','primary_last_name', 'primary_email']

            for field in required_fields:
                if field not in company_data or not company_data[field]:
                    raise ValueError(f"{field.replace('_', ' ').title()} is required")

            if self.repository.get_company_by_vat(company_data['vat_number']).data:
                raise ValueError(f"Company with VAT number {company_data['vat_number']} already exists")

            if self.repository.get_company_by_email(company_data['email']).data:
                raise ValueError(f"Company with email {company_data['email']} already exists")

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
