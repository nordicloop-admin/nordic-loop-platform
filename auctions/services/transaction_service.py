from typing import Dict, Any, Optional, List
from django.utils import timezone
from django.db import transaction
from auctions.models import Transaction, Auction, Bid
from auctions.repositories.transaction_repository import TransactionRepository
from auctions.repositories.auction_repository import AuctionRepository
from auctions.repositories.bid_repository import BidRepository
from base.services.logging import LoggingService
from users.models import CustomUser

logging_service = LoggingService()


class TransactionService:
    """
    Service class for transaction-related operations.
    This class handles business logic related to transactions.
    """

    def __init__(self, transaction_repository: TransactionRepository, auction_repository: AuctionRepository,
                 bid_repository: BidRepository):
        self.repository = transaction_repository
        self.auction_repository = auction_repository
        self.bid_repository = bid_repository

    def create_transaction_from_auction(self, auction: Auction) -> Optional[Transaction]:
        """
        Create a transaction from an auction.

        Args:
            auction: The auction to create a transaction for

        Returns:
            The created transaction object, or None if no transaction was created

        Raises:
            ValueError: If the transaction cannot be created
        """
        try:
            # Check if auction is ended
            if auction.status != 'ended':
                raise ValueError("Cannot create transaction for an auction that is not ended")

            # Check if transaction already exists
            existing_transaction = self.repository.get_transaction_by_auction(auction).data
            if existing_transaction:
                raise ValueError("Transaction already exists for this auction")

            # Get the winning bid
            winning_bid = self.bid_repository.get_winning_bid(auction).data
            if not winning_bid:
                # No winning bid, no transaction
                return None

            # Create the transaction
            with transaction.atomic():
                transaction_data = {
                    'auction': auction,
                    'winning_bid': winning_bid,
                    'seller': auction.seller,
                    'buyer': winning_bid.bidder,
                    'amount': winning_bid.amount,
                    'status': 'pending'
                }

                transaction_obj = self.repository.create_transaction(transaction_data).data

                # Update auction status
                self.auction_repository.update_auction(auction.id, {'status': 'completed'})

            return transaction_obj
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def get_transaction_by_id(self, transaction_id: int) -> Optional[Transaction]:
        """
        Get a transaction by ID.

        Args:
            transaction_id: Transaction's ID

        Returns:
            The transaction object if found, None otherwise
        """
        try:
            transaction = self.repository.get_transaction_by_id(transaction_id).data
            return transaction
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def get_transaction_by_auction(self, auction: Auction) -> Optional[Transaction]:
        """
        Get a transaction by auction.

        Args:
            auction: The auction to get the transaction for

        Returns:
            The transaction object if found, None otherwise
        """
        try:
            transaction = self.repository.get_transaction_by_auction(auction).data
            return transaction
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def get_transactions_by_seller(self, seller: CustomUser) -> List[Transaction]:
        """
        Get all transactions where the user is the seller.

        Args:
            seller: The seller user

        Returns:
            List of transactions
        """
        try:
            transactions = self.repository.get_transactions_by_seller(seller).data
            return transactions
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def get_transactions_by_buyer(self, buyer: CustomUser) -> List[Transaction]:
        """
        Get all transactions where the user is the buyer.

        Args:
            buyer: The buyer user

        Returns:
            List of transactions
        """
        try:
            transactions = self.repository.get_transactions_by_buyer(buyer).data
            return transactions
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def get_transactions_by_status(self, status: str) -> List[Transaction]:
        """
        Get all transactions with a specific status.

        Args:
            status: The status to filter by

        Returns:
            List of transactions
        """
        try:
            transactions = self.repository.get_transactions_by_status(status).data
            return transactions
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def update_transaction(self, transaction_obj: Transaction, **kwargs) -> Transaction:
        """
        Update a transaction.

        Args:
            transaction_obj: The transaction to update
            **kwargs: Fields to update

        Returns:
            The updated transaction object
        """
        try:
            transaction = self.repository.update_transaction(transaction_obj.id, kwargs).data
            return transaction
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def mark_as_paid(self, transaction_obj: Transaction) -> Transaction:
        """
        Mark a transaction as paid.

        Args:
            transaction_obj: The transaction to mark as paid

        Returns:
            The updated transaction object

        Raises:
            ValueError: If the transaction cannot be marked as paid
        """
        try:
            # Check if transaction can be marked as paid
            if transaction_obj.status != 'pending':
                raise ValueError("Only pending transactions can be marked as paid")

            # Mark as paid
            transaction = self.repository.mark_as_paid(transaction_obj.id).data
            return transaction
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def mark_as_completed(self, transaction_obj: Transaction) -> Transaction:
        """
        Mark a transaction as completed.

        Args:
            transaction_obj: The transaction to mark as completed

        Returns:
            The updated transaction object

        Raises:
            ValueError: If the transaction cannot be marked as completed
        """
        try:
            # Check if transaction can be marked as completed
            if transaction_obj.status != 'paid':
                raise ValueError("Only paid transactions can be marked as completed")

            # Mark as completed
            transaction = self.repository.mark_as_completed(transaction_obj.id).data
            return transaction
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def mark_as_cancelled(self, transaction_obj: Transaction) -> Transaction:
        """
        Mark a transaction as cancelled.

        Args:
            transaction_obj: The transaction to mark as cancelled

        Returns:
            The updated transaction object

        Raises:
            ValueError: If the transaction cannot be marked as cancelled
        """
        try:
            # Check if transaction can be marked as cancelled
            if transaction_obj.status in ['completed', 'disputed']:
                raise ValueError("Completed or disputed transactions cannot be cancelled")

            # Mark as cancelled
            with transaction.atomic():
                # Update the transaction
                cancelled_transaction = self.repository.mark_as_cancelled(transaction_obj.id).data

                # Update the auction status back to ended
                self.auction_repository.update_auction(transaction_obj.auction.id, {'status': 'ended'})

            return cancelled_transaction
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def mark_as_disputed(self, transaction_obj: Transaction) -> Transaction:
        """
        Mark a transaction as disputed.

        Args:
            transaction_obj: The transaction to mark as disputed

        Returns:
            The updated transaction object

        Raises:
            ValueError: If the transaction cannot be marked as disputed
        """
        try:
            # Check if transaction can be marked as disputed
            if transaction_obj.status == 'cancelled':
                raise ValueError("Cancelled transactions cannot be disputed")

            # Mark as disputed
            transaction = self.repository.mark_as_disputed(transaction_obj.id).data
            return transaction
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def process_ended_auctions(self) -> List[Transaction]:
        """
        Process all ended auctions and create transactions for them.

        Returns:
            List of created transactions
        """
        try:
            # Get all ended auctions without transactions
            ended_auctions = Auction.objects.filter(status='ended').exclude(transaction__isnull=False)

            created_transactions = []
            for auction in ended_auctions:
                try:
                    transaction_obj = self.create_transaction_from_auction(auction)
                    if transaction_obj:
                        created_transactions.append(transaction_obj)
                except ValueError:
                    # Skip auctions that already have transactions or other errors
                    continue

            return created_transactions
        except Exception as e:
            logging_service.log_error(e)
            raise e
