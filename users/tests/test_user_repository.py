from django.test import TestCase
from users.models import CustomUser
from users.repositories.user_repository import UserRepository


class UserRepositoryTest(TestCase):
    def setUp(self):
        self.repository = UserRepository()
        self.user_data = {
            "email": "test@example.com",
            "name": "Test User",
            "password": "testpassword"
        }

    def test_create_user(self):
        response = self.repository.create_user(
            email=self.user_data["email"],
            name=self.user_data["name"],
            password=self.user_data["password"]
        )

        self.assertTrue(response.success)
        self.assertEqual(CustomUser.objects.count(), 1)
        self.assertEqual(response.data.email, "test@example.com")
        self.assertEqual(response.data.name, "Test User")
        self.assertTrue(response.data.check_password("testpassword"))

    def test_get_user_by_id_success(self):
        user_response = self.repository.create_user(
            email=self.user_data["email"],
            name=self.user_data["name"],
            password=self.user_data["password"]
        )
        user_id = user_response.data.id
        
        response = self.repository.get_user_by_id(user_id)

        self.assertTrue(response.success)
        self.assertEqual(response.data.id, user_id)
        self.assertEqual(response.data.email, "test@example.com")

    def test_get_user_by_id_not_found(self):
        response = self.repository.get_user_by_id(999)
        self.assertFalse(response.success)
        self.assertEqual(response.message, "User not found")

    def test_get_user_by_email_success(self):
        self.repository.create_user(
            email=self.user_data["email"],
            name=self.user_data["name"],
            password=self.user_data["password"]
        )
        
        response = self.repository.get_user_by_email("test@example.com")

        self.assertTrue(response.success)
        self.assertEqual(response.data.email, "test@example.com")
        self.assertEqual(response.data.name, "Test User")

    def test_get_user_by_email_not_found(self):
        response = self.repository.get_user_by_email("nonexistent@example.com")
        self.assertFalse(response.success)
        self.assertEqual(response.message, "User not found")

    def test_search_users(self):
        # Create first user
        self.repository.create_user(
            email=self.user_data["email"],
            name=self.user_data["name"],
            password=self.user_data["password"]
        )
        
        # Create second user
        self.repository.create_user(
            email="another@example.com",
            name="Another User",
            password="password123"
        )
        
        # Search by email
        response = self.repository.search_users("test@example")
        self.assertTrue(response.success)
        self.assertEqual(response.data.count(), 1)
        self.assertEqual(response.data[0].email, "test@example.com")
        
        # Search by name
        response = self.repository.search_users("Another")
        self.assertTrue(response.success)
        self.assertEqual(response.data.count(), 1)
        self.assertEqual(response.data[0].name, "Another User")
        
        # Search with partial match
        response = self.repository.search_users("User")
        self.assertTrue(response.success)
        self.assertEqual(response.data.count(), 2)
        
        # Search with no results
        response = self.repository.search_users("nonexistent")
        self.assertTrue(response.success)
        self.assertEqual(response.data.count(), 0)

    def test_update_user(self):
        user_response = self.repository.create_user(
            email=self.user_data["email"],
            name=self.user_data["name"],
            password=self.user_data["password"]
        )
        user_id = user_response.data.id
        
        update_data = {
            "name": "Updated Name",
            "email": "updated@example.com"
        }
        
        response = self.repository.update_user(user_id, update_data)
        
        self.assertTrue(response.success)
        self.assertEqual(response.data.name, "Updated Name")
        self.assertEqual(response.data.email, "updated@example.com")
        
        # Test password update
        update_data = {
            "password": "newpassword123"
        }
        
        response = self.repository.update_user(user_id, update_data)
        
        self.assertTrue(response.success)
        self.assertTrue(response.data.check_password("newpassword123"))

    def test_update_user_not_found(self):
        update_data = {
            "name": "Updated Name"
        }
        
        response = self.repository.update_user(999, update_data)
        
        self.assertFalse(response.success)
        self.assertEqual(response.message, "User not found")

    def test_delete_user(self):
        user_response = self.repository.create_user(
            email=self.user_data["email"],
            name=self.user_data["name"],
            password=self.user_data["password"]
        )
        user_id = user_response.data.id
        
        response = self.repository.delete_user(user_id)
        
        self.assertTrue(response.success)
        self.assertEqual(response.message, "User deleted successfully")
        self.assertEqual(CustomUser.objects.count(), 0)

    def test_delete_user_not_found(self):
        response = self.repository.delete_user(999)
        
        self.assertFalse(response.success)
        self.assertEqual(response.message, "User not found")
