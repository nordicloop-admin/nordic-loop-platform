from typing import Dict, Any, Optional, List
from django.utils import timezone
from auctions.models import Transaction, Auction, Bid
from users.models import CustomUser


class TransactionRepository:
    """
    Repository class for transaction-related database operations.
    """
    
    @staticmethod
    def create_transaction(transaction_data: Dict[str, Any]) -> Transaction:
        """
        Create a new transaction.
        
        Args:
            transaction_data: Dictionary containing transaction data
            
        Returns:
            The created transaction object
        """
        transaction = Transaction(**transaction_data)
        transaction.save()
        return transaction
    
    @staticmethod
    def get_transaction_by_id(transaction_id: int) -> Optional[Transaction]:
        """
        Get a transaction by ID.
        
        Args:
            transaction_id: Transaction's ID
            
        Returns:
            The transaction object if found, None otherwise
        """
        try:
            return Transaction.objects.get(id=transaction_id)
        except Transaction.DoesNotExist:
            return None
    
    @staticmethod
    def get_transaction_by_auction(auction: Auction) -> Optional[Transaction]:
        """
        Get a transaction by auction.
        
        Args:
            auction: The auction to get the transaction for
            
        Returns:
            The transaction object if found, None otherwise
        """
        try:
            return Transaction.objects.get(auction=auction)
        except Transaction.DoesNotExist:
            return None
    
    @staticmethod
    def get_transactions_by_seller(seller: CustomUser) -> List[Transaction]:
        """
        Get all transactions where the user is the seller.
        
        Args:
            seller: The seller user
            
        Returns:
            List of transactions
        """
        return Transaction.objects.filter(seller=seller).order_by('-created_at')
    
    @staticmethod
    def get_transactions_by_buyer(buyer: CustomUser) -> List[Transaction]:
        """
        Get all transactions where the user is the buyer.
        
        Args:
            buyer: The buyer user
            
        Returns:
            List of transactions
        """
        return Transaction.objects.filter(buyer=buyer).order_by('-created_at')
    
    @staticmethod
    def get_transactions_by_status(status: str) -> List[Transaction]:
        """
        Get all transactions with a specific status.
        
        Args:
            status: The status to filter by
            
        Returns:
            List of transactions
        """
        return Transaction.objects.filter(status=status).order_by('-created_at')
    
    @staticmethod
    def update_transaction(transaction: Transaction, **kwargs) -> Transaction:
        """
        Update a transaction.
        
        Args:
            transaction: The transaction to update
            **kwargs: Fields to update
            
        Returns:
            The updated transaction object
        """
        for key, value in kwargs.items():
            setattr(transaction, key, value)
        
        transaction.save()
        return transaction
    
    @staticmethod
    def mark_as_paid(transaction: Transaction) -> Transaction:
        """
        Mark a transaction as paid.
        
        Args:
            transaction: The transaction to mark as paid
            
        Returns:
            The updated transaction object
        """
        transaction.status = 'paid'
        transaction.payment_date = timezone.now()
        transaction.save()
        return transaction
    
    @staticmethod
    def mark_as_completed(transaction: Transaction) -> Transaction:
        """
        Mark a transaction as completed.
        
        Args:
            transaction: The transaction to mark as completed
            
        Returns:
            The updated transaction object
        """
        transaction.status = 'completed'
        transaction.completion_date = timezone.now()
        transaction.save()
        return transaction
    
    @staticmethod
    def mark_as_cancelled(transaction: Transaction) -> Transaction:
        transaction.status = 'cancelled'
        transaction.save()
        return transaction
    
    @staticmethod
    def mark_as_disputed(transaction: Transaction) -> Transaction:
        """
        Mark a transaction as disputed.
        
        Args:
            transaction: The transaction to mark as disputed
            
        Returns:
            The updated transaction object
        """
        transaction.status = 'disputed'
        transaction.save()
        return transaction
