from accounts.models import Account
from users.models import CustomUser
from typing import List, Dict, Any, Optional


class AccountService:
    """
    Service class for account-related operations.
    This class handles business logic related to user accounts.
    """
    
    @staticmethod
    def create_account(user: CustomUser, subscription_type: str = 'basic') -> Account:
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
        if hasattr(user, 'account'):
            raise ValueError(f"User {user.email} already has an account")
            
        account = Account(
            user=user,
            subscription_type=subscription_type,
            is_active=True
        )
        account.save()
        
        return account
    
    @staticmethod
    def get_account_by_user(user: CustomUser) -> Optional[Account]:
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
    
    @staticmethod
    def get_account_by_id(account_id: int) -> Optional[Account]:
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
    
    @staticmethod
    def update_subscription(account: Account, subscription_type: str) -> Account:
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
        valid_types = [choice[0] for choice in Account.SUBSCRIPTION_CHOICES]
        if subscription_type not in valid_types:
            raise ValueError(f"Invalid subscription type. Must be one of: {', '.join(valid_types)}")
            
        account.subscription_type = subscription_type
        account.save()
        
        return account
    
    @staticmethod
    def activate_account(account: Account) -> Account:
        """
        Activate an account.
        
        Args:
            account: The account to activate
            
        Returns:
            The activated account object
        """
        account.is_active = True
        account.save()
        
        return account
    
    @staticmethod
    def deactivate_account(account: Account) -> Account:
        """
        Deactivate an account.
        
        Args:
            account: The account to deactivate
            
        Returns:
            The deactivated account object
        """
        account.is_active = False
        account.save()
        
        return account
    
    @staticmethod
    def delete_account(account: Account) -> None:
        """
        Delete an account.
        
        Args:
            account: The account to delete
        """
        account.delete()
    
    @staticmethod
    def get_all_accounts() -> List[Account]:
        """
        Get all accounts.
        
        Returns:
            List of all accounts
        """
        return Account.objects.all()
    
    @staticmethod
    def get_active_accounts() -> List[Account]:
        """
        Get all active accounts.
        
        Returns:
            List of active accounts
        """
        return Account.objects.filter(is_active=True)
    
    @staticmethod
    def get_accounts_by_subscription(subscription_type: str) -> List[Account]:
        """
        Get accounts by subscription type.
        
        Args:
            subscription_type: The subscription type to filter by
            
        Returns:
            List of accounts with the specified subscription type
        """
        return Account.objects.filter(subscription_type=subscription_type)
