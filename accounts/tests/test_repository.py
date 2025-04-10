from django.test import TestCase
from accounts.repositories.company_repository import CompanyRepository
from accounts.models import Company
from users.models import CustomUser
from django.db import IntegrityError

class CompanyRepositoryTests(TestCase):
    def setUp(self):
        self.repository = CompanyRepository()
        
    def create_test_user(self, email="test@example.com", name="Test User"):
        return CustomUser.objects.create_user(
            email=email,
            name=name,
            password="testpass123"
        )

    def test_create_company(self):
        test_user = self.create_test_user()
        company = self.repository.create_company(
            vat_number="12345678",
            official_name="Test Company",
            business_address="123 Test St",
            phone_number="+1234567890",
            user=test_user,
            email="company@test.com"
        )
        self.assertIsInstance(company, Company)
        self.assertEqual(company.vat_number, "12345678")
        self.assertEqual(company.official_name, "Test Company")
        
    def test_get_company_by_vat(self):
        test_user = self.create_test_user(email="test2@example.com")
        created_company = self.repository.create_company(
            vat_number="12345678",
            official_name="Test Company",
            business_address="123 Test St",
            phone_number="+1234567890",
            user=test_user,
            email="company@test.com"
        )
        
        found_company = self.repository.get_company_by_vat("12345678")
        self.assertEqual(created_company, found_company)
        
    def test_search_companies(self):
        # Create first company with first user
        user1 = self.create_test_user(email="user1@example.com", name="User One")
        company1 = self.repository.create_company(
            vat_number="12345678",
            official_name="Alpha Company",
            business_address="123 Test St",
            phone_number="+1234567890",
            user=user1,
            email="alpha@test.com"
        )
        
        # Create second company with second user
        user2 = self.create_test_user(email="user2@example.com", name="User Two")
        company2 = self.repository.create_company(
            vat_number="87654321",
            official_name="Beta Company",
            business_address="456 Test Ave",
            phone_number="+0987654321",
            user=user2,
            email="beta@test.com"
        )
        
        results = self.repository.search_companies("Alpha")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], company1)
        
    def test_update_company(self):
        test_user = self.create_test_user(email="test3@example.com")
        company = self.repository.create_company(
            vat_number="12345678",
            official_name="Test Company",
            business_address="123 Test St",
            phone_number="+1234567890",
            user=test_user,
            email="company@test.com"
        )
        
        updated_company = self.repository.update_company(
            company,
            official_name="Updated Company",
            business_address="456 New St"
        )
        
        self.assertEqual(updated_company.official_name, "Updated Company")
        self.assertEqual(updated_company.business_address, "456 New St")

    def test_delete_company(self):
        test_user = self.create_test_user(email="test4@example.com")
        company = self.repository.create_company(
            vat_number="12345678",
            official_name="Test Company",
            business_address="123 Test St",
            phone_number="+1234567890",
            user=test_user,
            email="company@test.com"
        )
        
        # Verify company exists
        self.assertTrue(Company.objects.filter(id=company.id).exists())
        
        # Delete company
        self.repository.delete_company(company)
        
        # Verify company no longer exists
        self.assertFalse(Company.objects.filter(id=company.id).exists())

    def test_duplicate_vat_number(self):
        # Create first company
        user1 = self.create_test_user(email="user5@example.com")
        self.repository.create_company(
            vat_number="12345678",
            official_name="Test Company 1",
            business_address="123 Test St",
            phone_number="+1234567890",
            user=user1,
            email="company1@test.com"
        )
        
        # Try to create second company with same VAT number
        user2 = self.create_test_user(email="user6@example.com")
        with self.assertRaises(IntegrityError):
            self.repository.create_company(
                vat_number="12345678",  # Same VAT number
                official_name="Test Company 2",
                business_address="456 Test Ave",
                phone_number="+0987654321",
                user=user2,
                email="company2@test.com"
            )
