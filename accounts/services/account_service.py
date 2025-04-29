from accounts.models import Account
from users.models import CustomUser
from users.repositories.user_repository import UserRepository
from base.services.logging import LoggingService
from typing import List, Optional

logging_service = LoggingService()


class AccountService:
    """
    Service class for account-related operations.
    This class handles business logic related to user accounts.
    """

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def create_account(self, user: CustomUser, subscription_type: str = 'basic') -> Account:
        """
        Create a new account for a user.

        Args:
            user: The user to create an account for
            subscription_type: The subscription type (default: 'basic')

        Returns:
            The created account object

        Raises:
            ValueError: If the user already has an account
        """
        try:
            if hasattr(user, 'account'):
                raise ValueError(f"User {user.email} already has an account")

            # Validate subscription type
            valid_types = [choice[0] for choice in Account.SUBSCRIPTION_CHOICES]
            if subscription_type not in valid_types:
                raise ValueError(f"Invalid subscription type. Must be one of: {', '.join(valid_types)}")

            account = Account(
                user=user,
                subscription_type=subscription_type,
                is_active=True
            )
            account.save()

            return account
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def get_account_by_user(self, user: CustomUser) -> Optional[Account]:
        """
        Get an account by user.

        Args:
            user: The user whose account to get

        Returns:
            The account object if found, None otherwise
        """
        try:
            return Account.objects.get(user=user)
        except Account.DoesNotExist:
            return None
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def get_account_by_id(self, account_id: int) -> Optional[Account]:
        """
        Get an account by ID.

        Args:
            account_id: Account's ID

        Returns:
            The account object if found, None otherwise
        """
        try:
            return Account.objects.get(id=account_id)
        except Account.DoesNotExist:
            return None
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def update_subscription(self, account: Account, subscription_type: str) -> Account:
        """
        Update an account's subscription type.

        Args:
            account: The account to update
            subscription_type: The new subscription type

        Returns:
            The updated account object

        Raises:
            ValueError: If the subscription type is invalid
        """
        try:
            valid_types = [choice[0] for choice in Account.SUBSCRIPTION_CHOICES]
            if subscription_type not in valid_types:
                raise ValueError(f"Invalid subscription type. Must be one of: {', '.join(valid_types)}")

            account.subscription_type = subscription_type
            account.save()

            return account
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def activate_account(self, account: Account) -> Account:
        """
        Activate an account.

        Args:
            account: The account to activate
        """
        try:
            account.is_active = True
            account.save()

            return account
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def deactivate_account(self, account: Account) -> Account:
        """
        Deactivate an account.

        Args:
            account: The account to deactivate
        """
        try:
            account.is_active = False
            account.save()

            return account
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def delete_account(self, account: Account) -> None:
        """
        Delete an account.

        Args:
            account: The account to delete
        """
        try:
            account.delete()
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def get_all_accounts(self) -> List[Account]:
        """
        Get all accounts.
        """
        try:
            return Account.objects.all()
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def get_active_accounts(self) -> List[Account]:
        """
        Get all active accounts.
        """
        try:
            return Account.objects.filter(is_active=True)
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def get_accounts_by_subscription(self, subscription_type: str) -> List[Account]:
        """
        Get accounts by subscription type.

        Args:
            subscription_type: The subscription type to filter by
        """
        try:
            # Validate subscription type
            valid_types = [choice[0] for choice in Account.SUBSCRIPTION_CHOICES]
            if subscription_type not in valid_types:
                raise ValueError(f"Invalid subscription type. Must be one of: {', '.join(valid_types)}")

            return Account.objects.filter(subscription_type=subscription_type)
        except Exception as e:
            logging_service.log_error(e)
            raise e
