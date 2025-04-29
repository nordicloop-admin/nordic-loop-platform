from django.test import TestCase
from accounts.services.company_service import CompanyService
from accounts.models import Company
from users.models import CustomUser


class CompanyServiceTests(TestCase):
    def setUp(self):
        # Create an instance of CompanyService
        self.company_service = CompanyService()
    def test_register_company(self):
        company_data = {
            'vat_number': '12345678',
            'official_name': 'Test Company',
            'email': 'company@test.com',
            'contact_name': 'Test Contact',
            'contact_email': 'contact@test.com',
            'contact_position': 'Manager',
            'sector': 'manufacturing',
            'password': 'testpass123',
            'website': 'https://example.com'
        }

        company = self.company_service.register_company(company_data)

        self.assertIsInstance(company, Company)
        self.assertEqual(company.vat_number, '12345678')
        self.assertEqual(company.official_name, 'Test Company')
        self.assertEqual(company.status, 'pending')

    def test_register_company_duplicate_vat(self):
        # Create first company
        company1_data = {
            'vat_number': '12345678',
            'official_name': 'Test Company 1',
            'email': 'company1@test.com',
            'contact_name': 'Test Contact 1',
            'contact_email': 'contact1@test.com',
            'contact_position': 'Manager',
            'sector': 'manufacturing',
            'password': 'testpass123',
            'website': 'https://example.com'
        }

        self.company_service.register_company(company1_data)

        # Try to create second company with same VAT number
        company2_data = {
            'vat_number': '12345678',  # Same VAT number
            'official_name': 'Test Company 2',
            'email': 'company2@test.com',
            'contact_name': 'Test Contact 2',
            'contact_email': 'contact2@test.com',
            'contact_position': 'Director',
            'sector': 'retail',
            'password': 'testpass456',
            'website': 'https://example2.com'
        }

        with self.assertRaises(ValueError):
            self.company_service.register_company(company2_data)

    def test_get_company_by_vat(self):
        company_data = {
            'vat_number': '12345678',
            'official_name': 'Test Company',
            'email': 'company@test.com',
            'contact_name': 'Test Contact',
            'contact_email': 'contact@test.com',
            'contact_position': 'Manager',
            'sector': 'manufacturing',
            'password': 'testpass123',
            'website': 'https://example.com'
        }

        created_company = self.company_service.register_company(company_data)

        found_company = self.company_service.get_company_by_vat('12345678')
        self.assertEqual(created_company, found_company)

    def test_get_company_by_id(self):
        company_data = {
            'vat_number': '12345678',
            'official_name': 'Test Company',
            'email': 'company@test.com',
            'contact_name': 'Test Contact',
            'contact_email': 'contact@test.com',
            'contact_position': 'Manager',
            'sector': 'manufacturing',
            'password': 'testpass123',
            'website': 'https://example.com'
        }

        created_company = self.company_service.register_company(company_data)

        found_company = self.company_service.get_company_by_id(created_company.id)
        self.assertEqual(created_company, found_company)

    def test_search_companies(self):
        # Create first company
        company1_data = {
            'vat_number': '12345678',
            'official_name': 'Alpha Company',
            'email': 'alpha@test.com',
            'contact_name': 'Alpha Contact',
            'contact_email': 'alpha.contact@test.com',
            'contact_position': 'Manager',
            'sector': 'manufacturing',
            'password': 'testpass123',
            'website': 'https://alpha-example.com'
        }

        company1 = self.company_service.register_company(company1_data)

        # Create second company
        company2_data = {
            'vat_number': '87654321',
            'official_name': 'Beta Company',
            'email': 'beta@test.com',
            'contact_name': 'Beta Contact',
            'contact_email': 'beta.contact@test.com',
            'contact_position': 'Director',
            'sector': 'retail',
            'password': 'testpass456',
            'website': 'https://beta-example.com'
        }

        company2 = self.company_service.register_company(company2_data)

        # Search by name
        results = self.company_service.search_companies("Alpha")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], company1)

        # Search by VAT number
        results = self.company_service.search_companies("87654321")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], company2)

    def test_update_company(self):
        company_data = {
            'vat_number': '12345678',
            'official_name': 'Test Company',
            'email': 'company@test.com',
            'contact_name': 'Test Contact',
            'contact_email': 'contact@test.com',
            'contact_position': 'Manager',
            'sector': 'manufacturing',
            'password': 'testpass123',
            'website': 'https://example.com'
        }

        company = self.company_service.register_company(company_data)

        updated_company = self.company_service.update_company(
            company,
            official_name="Updated Company",
            website="https://updated-example.com"
        )

        self.assertEqual(updated_company.official_name, "Updated Company")
        self.assertEqual(updated_company.website, "https://updated-example.com")

    def test_approve_company(self):
        company_data = {
            'vat_number': '12345678',
            'official_name': 'Test Company',
            'email': 'company@test.com',
            'contact_name': 'Test Contact',
            'contact_email': 'contact@test.com',
            'contact_position': 'Manager',
            'sector': 'manufacturing',
            'password': 'testpass123',
            'website': 'https://example.com'
        }

        company = self.company_service.register_company(company_data)

        # Approve the company
        approved_company = self.company_service.approve_company(company.id)

        # Check company status
        self.assertEqual(approved_company.status, "approved")

        # Check that a user was created
        user = CustomUser.objects.filter(email="company@test.com").first()
        self.assertIsNotNone(user)
        self.assertTrue(user.is_active)

        # Check that the password was cleared from the company record
        self.assertIsNone(approved_company.password)

    def test_reject_company(self):
        company_data = {
            'vat_number': '12345678',
            'official_name': 'Test Company',
            'email': 'company@test.com',
            'contact_name': 'Test Contact',
            'contact_email': 'contact@test.com',
            'contact_position': 'Manager',
            'company_sector': 'manufacturing',
            'password': 'testpass123',
            'website': 'https://example.com'
        }

        company = self.company_service.register_company(company_data)

        # Reject the company
        rejected_company = self.company_service.reject_company(company.id)

        # Check company status
        self.assertEqual(rejected_company.status, "rejected")

    def test_get_pending_companies(self):
        # Create pending company
        pending_company_data = {
            'vat_number': '12345678',
            'official_name': 'Pending Company',
            'email': 'pending@test.com',
            'contact_name': 'Pending Contact',
            'contact_email': 'pending.contact@test.com',
            'contact_position': 'Manager',
            'company_sector': 'manufacturing',
            'password': 'testpass123',
            'website': 'https://pending-example.com'
        }

        pending_company = self.company_service.register_company(pending_company_data)

        # Create and approve another company
        approved_company_data = {
            'vat_number': '87654321',
            'official_name': 'Approved Company',
            'email': 'approved@test.com',
            'contact_name': 'Approved Contact',
            'contact_email': 'approved.contact@test.com',
            'contact_position': 'Director',
            'company_sector': 'retail',
            'password': 'testpass456',
            'website': 'https://approved-example.com'
        }

        approved_company = self.company_service.register_company(approved_company_data)
        self.company_service.approve_company(approved_company.id)

        # Get pending companies
        pending_companies = self.company_service.get_pending_companies()

        self.assertEqual(len(pending_companies), 1)
        self.assertEqual(pending_companies[0], pending_company)

    def test_delete_company(self):
        company_data = {
            'vat_number': '12345678',
            'official_name': 'Test Company',
            'email': 'company@test.com',
            'contact_name': 'Test Contact',
            'contact_email': 'contact@test.com',
            'contact_position': 'Manager',
            'company_sector': 'manufacturing',
            'password': 'testpass123',
            'website': 'https://example.com'
        }

        company = self.company_service.register_company(company_data)

        # Verify company exists
        self.assertTrue(Company.objects.filter(id=company.id).exists())

        # Delete company
        self.company_service.delete_company(company)

        # Verify company no longer exists
        self.assertFalse(Company.objects.filter(id=company.id).exists())
