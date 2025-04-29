from django.test import TestCase
from accounts.models import Company
from accounts.repositories.company_repository import CompanyRepository
from users.models import CustomUser


class CompanyRepositoryTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email="test@example.com",
            name="Test User",
            password="testpassword"
        )
        self.repository = CompanyRepository()
        self.company_data = {
            "vat_number": "BE0123456789",
            "official_name": "Test Company",
            "email": "company@example.com",
            "sector": "manufacturing",
            "website": "https://example.com",
            "contact_name": "Contact Person",
            "contact_position": "Manager",
            "contact_email": "contact@example.com",
            "password": "securepassword"
        }

    def test_create_company(self):
        response = self.repository.create_company(
            user=self.user, data=self.company_data
        )

        self.assertTrue(response.success)
        self.assertEqual(Company.objects.count(), 1)
        self.assertEqual(response.data.official_name, "Test Company")
        self.assertEqual(response.data.vat_number, "BE0123456789")

    def test_get_company_by_id_success(self):
        company_response = self.repository.create_company(
            user=self.user, data=self.company_data
        )
        company_id = company_response.data.id
        
        response = self.repository.get_company_by_id(company_id)

        self.assertTrue(response.success)
        self.assertEqual(response.data.id, company_id)
        self.assertEqual(response.data.official_name, "Test Company")

    def test_get_company_by_id_not_found(self):
        response = self.repository.get_company_by_id(999)
        self.assertFalse(response.success)
        self.assertEqual(response.message, "Company not found")

    def test_get_company_by_vat_success(self):
        self.repository.create_company(
            user=self.user, data=self.company_data
        )
        
        response = self.repository.get_company_by_vat("BE0123456789")

        self.assertTrue(response.success)
        self.assertEqual(response.data.vat_number, "BE0123456789")
        self.assertEqual(response.data.official_name, "Test Company")

    def test_get_company_by_vat_not_found(self):
        response = self.repository.get_company_by_vat("NONEXISTENT")
        self.assertFalse(response.success)
        self.assertEqual(response.message, "Company not found")

    def test_get_company_by_email_success(self):
        self.repository.create_company(
            user=self.user, data=self.company_data
        )
        
        response = self.repository.get_company_by_email("company@example.com")

        self.assertTrue(response.success)
        self.assertEqual(response.data.email, "company@example.com")
        self.assertEqual(response.data.official_name, "Test Company")

    def test_get_company_by_email_not_found(self):
        response = self.repository.get_company_by_email("nonexistent@example.com")
        self.assertFalse(response.success)
        self.assertEqual(response.message, "Company not found")

    def test_search_companies(self):
        self.repository.create_company(
            user=self.user, data=self.company_data
        )
        
        # Search by name
        response = self.repository.search_companies("Test Company")
        self.assertTrue(response.success)
        self.assertEqual(response.data.count(), 1)
        
        # Search by VAT
        response = self.repository.search_companies("BE0123456789")
        self.assertTrue(response.success)
        self.assertEqual(response.data.count(), 1)
        
        # Search by email
        response = self.repository.search_companies("company@example.com")
        self.assertTrue(response.success)
        self.assertEqual(response.data.count(), 1)
        
        # Search with no results
        response = self.repository.search_companies("nonexistent")
        self.assertTrue(response.success)
        self.assertEqual(response.data.count(), 0)

    def test_get_companies_by_status(self):
        # Create a company with default status (pending)
        self.repository.create_company(
            user=self.user, data=self.company_data
        )
        
        # Create another company with approved status
        approved_data = self.company_data.copy()
        approved_data["vat_number"] = "BE9876543210"
        approved_data["email"] = "approved@example.com"
        approved_data["contact_email"] = "approved-contact@example.com"
        approved_data["status"] = "approved"
        self.repository.create_company(
            user=self.user, data=approved_data
        )
        
        # Get pending companies
        response = self.repository.get_companies_by_status("pending")
        self.assertTrue(response.success)
        self.assertEqual(response.data.count(), 1)
        self.assertEqual(response.data[0].status, "pending")
        
        # Get approved companies
        response = self.repository.get_companies_by_status("approved")
        self.assertTrue(response.success)
        self.assertEqual(response.data.count(), 1)
        self.assertEqual(response.data[0].status, "approved")
        
        # Get companies with non-existent status
        response = self.repository.get_companies_by_status("nonexistent")
        self.assertTrue(response.success)
        self.assertEqual(response.data.count(), 0)

    def test_update_company(self):
        company_response = self.repository.create_company(
            user=self.user, data=self.company_data
        )
        company_id = company_response.data.id
        
        update_data = {
            "official_name": "Updated Company Name",
            "website": "https://updated-example.com"
        }
        
        response = self.repository.update_company(company_id, update_data)
        
        self.assertTrue(response.success)
        self.assertEqual(response.data.official_name, "Updated Company Name")
        self.assertEqual(response.data.website, "https://updated-example.com")
        # Ensure other fields remain unchanged
        self.assertEqual(response.data.vat_number, "BE0123456789")

    def test_update_company_not_found(self):
        update_data = {
            "official_name": "Updated Company Name"
        }
        
        response = self.repository.update_company(999, update_data)
        
        self.assertFalse(response.success)
        self.assertEqual(response.message, "Company not found")

    def test_delete_company(self):
        company_response = self.repository.create_company(
            user=self.user, data=self.company_data
        )
        company_id = company_response.data.id
        
        response = self.repository.delete_company(company_id)
        
        self.assertTrue(response.success)
        self.assertEqual(response.message, "Company deleted successfully")
        self.assertEqual(Company.objects.count(), 0)

    def test_delete_company_not_found(self):
        response = self.repository.delete_company(999)
        
        self.assertFalse(response.success)
        self.assertEqual(response.message, "Company not found")
