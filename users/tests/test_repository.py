from django.test import TestCase
from users.repositories.user_repository import UserRepository
from users.models import CustomUser

class UserRepositoryTests(TestCase):
    def setUp(self):
        self.repository = UserRepository()
        
    def test_create_user(self):
        user = self.repository.create_user(
            email="test@example.com",
            name="Test User",
            password="testpass123"
        )
        self.assertIsInstance(user, CustomUser)
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.name, "Test User")
        
    def test_get_user_by_email(self):
        created_user = self.repository.create_user(
            email="test@example.com",
            name="Test User",
            password="testpass123"
        )
        
        found_user = self.repository.get_user_by_email("test@example.com")
        self.assertEqual(created_user, found_user)

    
    