from django.test import TestCase
from users.services.user_service import UserService
from users.models import CustomUser


class UserServiceTests(TestCase):
    def test_register_user(self):
        user = UserService.register_user(
            email="test@example.com",
            name="Test User",
            password="testpass123"
        )
        self.assertIsInstance(user, CustomUser)
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.name, "Test User")
        self.assertTrue(user.check_password("testpass123"))
        
    def test_register_user_duplicate_email(self):
        # Create first user
        UserService.register_user(
            email="test@example.com",
            name="Test User",
            password="testpass123"
        )
        
        # Try to create second user with same email
        with self.assertRaises(ValueError):
            UserService.register_user(
                email="test@example.com",
                name="Another User",
                password="testpass456"
            )
            
    def test_get_user_by_email(self):
        created_user = UserService.register_user(
            email="test@example.com",
            name="Test User",
            password="testpass123"
        )
        
        found_user = UserService.get_user_by_email("test@example.com")
        self.assertEqual(created_user, found_user)
        
    def test_get_user_by_id(self):
        created_user = UserService.register_user(
            email="test@example.com",
            name="Test User",
            password="testpass123"
        )
        
        found_user = UserService.get_user_by_id(created_user.id)
        self.assertEqual(created_user, found_user)
        
    def test_search_users(self):
        # Create first user
        user1 = UserService.register_user(
            email="john@example.com",
            name="John Doe",
            password="testpass123"
        )
        
        # Create second user
        user2 = UserService.register_user(
            email="jane@example.com",
            name="Jane Smith",
            password="testpass456"
        )
        
        # Search by name
        results = UserService.search_users("John")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], user1)
        
        # Search by email
        results = UserService.search_users("jane")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], user2)
        
    def test_update_user(self):
        user = UserService.register_user(
            email="test@example.com",
            name="Test User",
            password="testpass123"
        )
        
        updated_user = UserService.update_user(
            user,
            name="Updated Name"
        )
        
        self.assertEqual(updated_user.name, "Updated Name")
        
    def test_change_password(self):
        user = UserService.register_user(
            email="test@example.com",
            name="Test User",
            password="testpass123"
        )
        
        # Change password
        result = UserService.change_password(
            user,
            old_password="testpass123",
            new_password="newpass456"
        )
        
        self.assertTrue(result)
        self.assertTrue(user.check_password("newpass456"))
        
    def test_change_password_incorrect_old_password(self):
        user = UserService.register_user(
            email="test@example.com",
            name="Test User",
            password="testpass123"
        )
        
        # Try to change password with incorrect old password
        with self.assertRaises(ValueError):
            UserService.change_password(
                user,
                old_password="wrongpass",
                new_password="newpass456"
            )
            
    def test_delete_user(self):
        user = UserService.register_user(
            email="test@example.com",
            name="Test User",
            password="testpass123"
        )
        
        # Verify user exists
        self.assertTrue(CustomUser.objects.filter(id=user.id).exists())
        
        # Delete user
        UserService.delete_user(user)
        
        # Verify user no longer exists
        self.assertFalse(CustomUser.objects.filter(id=user.id).exists())
