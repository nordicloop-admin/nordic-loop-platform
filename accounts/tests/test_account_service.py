from django.test import TestCase
from accounts.services.account_service import AccountService
from accounts.models import Account
from users.models import CustomUser


class AccountServiceTests(TestCase):
    def setUp(self):
        # Create a test user
        self.user = CustomUser.objects.create_user(
            email="test@example.com",
            name="Test User",
            password="testpass123"
        )

        # Create an instance of AccountService
        self.account_service = AccountService()

    def test_create_account(self):
        account = self.account_service.create_account(self.user)

        self.assertIsInstance(account, Account)
        self.assertEqual(account.user, self.user)
        self.assertEqual(account.subscription_type, "basic")
        self.assertTrue(account.is_active)

    def test_create_account_with_subscription_type(self):
        account = self.account_service.create_account(self.user, subscription_type="premium")

        self.assertEqual(account.subscription_type, "premium")

    def test_create_account_duplicate(self):
        # Create first account
        self.account_service.create_account(self.user)

        # Try to create second account for the same user
        with self.assertRaises(ValueError):
            self.account_service.create_account(self.user)

    def test_get_account_by_user(self):
        created_account = self.account_service.create_account(self.user)

        found_account = self.account_service.get_account_by_user(self.user)
        self.assertEqual(created_account, found_account)

    def test_get_account_by_id(self):
        created_account = self.account_service.create_account(self.user)

        found_account = self.account_service.get_account_by_id(created_account.id)
        self.assertEqual(created_account, found_account)

    def test_update_subscription(self):
        account = self.account_service.create_account(self.user)

        updated_account = self.account_service.update_subscription(account, "premium")

        self.assertEqual(updated_account.subscription_type, "premium")

    def test_update_subscription_invalid_type(self):
        account = self.account_service.create_account(self.user)

        with self.assertRaises(ValueError):
            self.account_service.update_subscription(account, "invalid_type")

    def test_activate_account(self):
        account = self.account_service.create_account(self.user)

        # Deactivate the account first
        account.is_active = False
        account.save()

        # Activate the account
        activated_account = self.account_service.activate_account(account)

        self.assertTrue(activated_account.is_active)

    def test_deactivate_account(self):
        account = self.account_service.create_account(self.user)

        # Deactivate the account
        deactivated_account = self.account_service.deactivate_account(account)

        self.assertFalse(deactivated_account.is_active)

    def test_delete_account(self):
        account = self.account_service.create_account(self.user)

        # Verify account exists
        self.assertTrue(Account.objects.filter(id=account.id).exists())

        # Delete account
        self.account_service.delete_account(account)

        # Verify account no longer exists
        self.assertFalse(Account.objects.filter(id=account.id).exists())

    def test_get_accounts_by_subscription(self):
        # Create users with different subscription types
        user1 = CustomUser.objects.create_user(
            email="user1@example.com",
            name="User One",
            password="testpass123"
        )
        user2 = CustomUser.objects.create_user(
            email="user2@example.com",
            name="User Two",
            password="testpass123"
        )

        # Create accounts with different subscription types
        basic_account = self.account_service.create_account(self.user, subscription_type="basic")
        premium_account = self.account_service.create_account(user1, subscription_type="premium")
        enterprise_account = self.account_service.create_account(user2, subscription_type="enterprise")

        # Get accounts by subscription type
        basic_accounts = self.account_service.get_accounts_by_subscription("basic")
        premium_accounts = self.account_service.get_accounts_by_subscription("premium")
        enterprise_accounts = self.account_service.get_accounts_by_subscription("enterprise")

        self.assertEqual(len(basic_accounts), 1)
        self.assertEqual(basic_accounts[0], basic_account)

        self.assertEqual(len(premium_accounts), 1)
        self.assertEqual(premium_accounts[0], premium_account)

        self.assertEqual(len(enterprise_accounts), 1)
        self.assertEqual(enterprise_accounts[0], enterprise_account)
