from django.test import TestCase
from accounts.services.company_service import CompanyService
from accounts.models import Company
from users.models import CustomUser


class CompanyServiceTests(TestCase):
    def test_register_company(self):
        company = CompanyService.register_company(
            vat_number="12345678",
            official_name="Test Company",
            business_address="123 Test St",
            phone_number="+1234567890",
            email="company@test.com",
            password="testpass123",
            website="https://example.com"
        )
        
        self.assertIsInstance(company, Company)
        self.assertEqual(company.vat_number, "12345678")
        self.assertEqual(company.official_name, "Test Company")
        self.assertEqual(company.status, "pending")
        
    def test_register_company_duplicate_vat(self):
        # Create first company
        CompanyService.register_company(
            vat_number="12345678",
            official_name="Test Company 1",
            business_address="123 Test St",
            phone_number="+1234567890",
            email="company1@test.com",
            password="testpass123"
        )
        
        # Try to create second company with same VAT number
        with self.assertRaises(ValueError):
            CompanyService.register_company(
                vat_number="12345678",  # Same VAT number
                official_name="Test Company 2",
                business_address="456 Test Ave",
                phone_number="+0987654321",
                email="company2@test.com",
                password="testpass456"
            )
            
    def test_get_company_by_vat(self):
        created_company = CompanyService.register_company(
            vat_number="12345678",
            official_name="Test Company",
            business_address="123 Test St",
            phone_number="+1234567890",
            email="company@test.com",
            password="testpass123"
        )
        
        found_company = CompanyService.get_company_by_vat("12345678")
        self.assertEqual(created_company, found_company)
        
    def test_get_company_by_id(self):
        created_company = CompanyService.register_company(
            vat_number="12345678",
            official_name="Test Company",
            business_address="123 Test St",
            phone_number="+1234567890",
            email="company@test.com",
            password="testpass123"
        )
        
        found_company = CompanyService.get_company_by_id(created_company.id)
        self.assertEqual(created_company, found_company)
        
    def test_search_companies(self):
        # Create first company
        company1 = CompanyService.register_company(
            vat_number="12345678",
            official_name="Alpha Company",
            business_address="123 Test St",
            phone_number="+1234567890",
            email="alpha@test.com",
            password="testpass123"
        )
        
        # Create second company
        company2 = CompanyService.register_company(
            vat_number="87654321",
            official_name="Beta Company",
            business_address="456 Test Ave",
            phone_number="+0987654321",
            email="beta@test.com",
            password="testpass456"
        )
        
        # Search by name
        results = CompanyService.search_companies("Alpha")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], company1)
        
        # Search by VAT number
        results = CompanyService.search_companies("87654321")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], company2)
        
    def test_update_company(self):
        company = CompanyService.register_company(
            vat_number="12345678",
            official_name="Test Company",
            business_address="123 Test St",
            phone_number="+1234567890",
            email="company@test.com",
            password="testpass123"
        )
        
        updated_company = CompanyService.update_company(
            company,
            official_name="Updated Company",
            business_address="456 New St"
        )
        
        self.assertEqual(updated_company.official_name, "Updated Company")
        self.assertEqual(updated_company.business_address, "456 New St")
        
    def test_approve_company(self):
        company = CompanyService.register_company(
            vat_number="12345678",
            official_name="Test Company",
            business_address="123 Test St",
            phone_number="+1234567890",
            email="company@test.com",
            password="testpass123"
        )
        
        # Approve the company
        approved_company = CompanyService.approve_company(company.id)
        
        # Check company status
        self.assertEqual(approved_company.status, "approved")
        
        # Check that a user was created
        user = CustomUser.objects.filter(email="company@test.com").first()
        self.assertIsNotNone(user)
        self.assertTrue(user.is_active)
        
        # Check that the password was cleared from the company record
        self.assertIsNone(approved_company.password)
        
    def test_reject_company(self):
        company = CompanyService.register_company(
            vat_number="12345678",
            official_name="Test Company",
            business_address="123 Test St",
            phone_number="+1234567890",
            email="company@test.com",
            password="testpass123"
        )
        
        # Reject the company
        rejected_company = CompanyService.reject_company(company.id)
        
        # Check company status
        self.assertEqual(rejected_company.status, "rejected")
        
    def test_get_pending_companies(self):
        # Create pending company
        pending_company = CompanyService.register_company(
            vat_number="12345678",
            official_name="Pending Company",
            business_address="123 Test St",
            phone_number="+1234567890",
            email="pending@test.com",
            password="testpass123"
        )
        
        # Create and approve another company
        approved_company = CompanyService.register_company(
            vat_number="87654321",
            official_name="Approved Company",
            business_address="456 Test Ave",
            phone_number="+0987654321",
            email="approved@test.com",
            password="testpass456"
        )
        CompanyService.approve_company(approved_company.id)
        
        # Get pending companies
        pending_companies = CompanyService.get_pending_companies()
        
        self.assertEqual(len(pending_companies), 1)
        self.assertEqual(pending_companies[0], pending_company)
        
    def test_delete_company(self):
        company = CompanyService.register_company(
            vat_number="12345678",
            official_name="Test Company",
            business_address="123 Test St",
            phone_number="+1234567890",
            email="company@test.com",
            password="testpass123"
        )
        
        # Verify company exists
        self.assertTrue(Company.objects.filter(id=company.id).exists())
        
        # Delete company
        CompanyService.delete_company(company)
        
        # Verify company no longer exists
        self.assertFalse(Company.objects.filter(id=company.id).exists())
