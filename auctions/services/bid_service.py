from typing import Dict, Any, Optional, List
from django.utils import timezone
from django.db import transaction
from auctions.models import Bid, Auction
from auctions.repositories.bid_repository import BidRepository
from auctions.repositories.auction_repository import AuctionRepository
from base.services.logging import LoggingService
from users.models import CustomUser

logging_service = LoggingService()


class BidService:
    """
    Service class for bid-related operations.
    This class handles business logic related to bids.
    """

    def __init__(self, bid_repository: BidRepository, auction_repository: AuctionRepository):
        self.repository = bid_repository
        self.auction_repository = auction_repository

    def place_bid(self, bidder: CustomUser, auction: Auction, amount: float) -> Bid:
        """
        Place a bid on an auction.

        Args:
            bidder: The user placing the bid
            auction: The auction to bid on
            amount: The bid amount

        Returns:
            The created bid object

        Raises:
            ValueError: If the bid cannot be placed
        """
        try:
            # Check if auction is active
            if not auction.is_active():
                raise ValueError("Cannot bid on an inactive auction")

            # Check if bidder is the seller
            if bidder == auction.seller:
                raise ValueError("Cannot bid on your own auction")

            # Check if bid amount is valid
            highest_bid = self.repository.get_highest_bid(auction).data
            if highest_bid:
                if amount <= highest_bid.amount:
                    raise ValueError(
                        f"Bid amount must be higher than the current highest bid ({highest_bid.amount})")
            elif amount < auction.starting_price:
                raise ValueError(f"Bid amount must be at least the starting price ({auction.starting_price})")

            # Create the bid
            with transaction.atomic():
                bid_data = {
                    'auction': auction,
                    'bidder': bidder,
                    'amount': amount,
                    'is_winning': False
                }

                bid = self.repository.create_bid(bid_data).data

                # Update auction's current price
                self.auction_repository.update_auction(auction.id, {'current_price': amount})

            return bid
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def get_bid_by_id(self, bid_id: int) -> Optional[Bid]:
        """
        Get a bid by ID.

        Args:
            bid_id: Bid's ID

        Returns:
            The bid object if found, None otherwise
        """
        try:
            bid = self.repository.get_bid_by_id(bid_id).data
            return bid
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def get_bids_by_auction(self, auction: Auction) -> List[Bid]:
        """
        Get all bids for an auction.

        Args:
            auction: The auction to get bids for

        Returns:
            List of bids
        """
        try:
            bids = self.repository.get_bids_by_auction(auction).data
            return bids
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def get_bids_by_bidder(self, bidder: CustomUser) -> List[Bid]:
        """
        Get all bids by a bidder.

        Args:
            bidder: The bidder user

        Returns:
            List of bids
        """
        try:
            bids = self.repository.get_bids_by_bidder(bidder).data
            return bids
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def get_highest_bid(self, auction: Auction) -> Optional[Bid]:
        """
        Get the highest bid for an auction.

        Args:
            auction: The auction to get the highest bid for

        Returns:
            The highest bid if found, None otherwise
        """
        try:
            bid = self.repository.get_highest_bid(auction).data
            return bid
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def get_winning_bid(self, auction: Auction) -> Optional[Bid]:
        """
        Get the winning bid for an auction.

        Args:
            auction: The auction to get the winning bid for

        Returns:
            The winning bid if found, None otherwise
        """
        try:
            bid = self.repository.get_winning_bid(auction).data
            return bid
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def set_winning_bid(self, bid: Bid) -> Bid:
        """
        Set a bid as the winning bid.

        Args:
            bid: The bid to set as winning

        Returns:
            The updated bid object

        Raises:
            ValueError: If the bid cannot be set as winning
        """
        try:
            # Check if auction is ended
            if bid.auction.status != 'ended':
                raise ValueError("Cannot set winning bid for an auction that is not ended")

            # Check if bid is the highest
            highest_bid = self.repository.get_highest_bid(bid.auction).data
            if highest_bid and bid.id != highest_bid.id:
                raise ValueError("Only the highest bid can be set as winning")

            # Set the bid as winning
            bid = self.repository.set_winning_bid(bid).data
            return bid
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def get_bid_count(self, auction: Auction) -> int:
        """
        Get the number of bids for an auction.

        Args:
            auction: The auction to get the bid count for

        Returns:
            The number of bids
        """
        try:
            count = self.repository.get_bid_count(auction)
            return count
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def get_unique_bidder_count(self, auction: Auction) -> int:
        """
        Get the number of unique bidders for an auction.

        Args:
            auction: The auction to get the unique bidder count for

        Returns:
            The number of unique bidders
        """
        try:
            count = self.repository.get_unique_bidder_count(auction)
            return count
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def has_user_bid_on_auction(self, auction: Auction, user: CustomUser) -> bool:
        """
        Check if a user has bid on an auction.

        Args:
            auction: The auction to check
            user: The user to check

        Returns:
            True if the user has bid on the auction, False otherwise
        """
        try:
            has_bid = self.repository.has_user_bid_on_auction(auction, user)
            return has_bid
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def determine_auction_winner(self, auction: Auction) -> Optional[Bid]:
        """
        Determine the winner of an auction.

        Args:
            auction: The auction to determine the winner for

        Returns:
            The winning bid if found, None otherwise

        Raises:
            ValueError: If the auction is not ended
        """
        try:
            # Check if auction is ended
            if auction.status != 'ended':
                raise ValueError("Cannot determine winner for an auction that is not ended")

            # Get the highest bid
            highest_bid = self.repository.get_highest_bid(auction).data

            # Check if there are any bids
            if not highest_bid:
                return None

            # Check if the highest bid meets the reserve price
            if auction.reserve_price and highest_bid.amount < auction.reserve_price:
                return None

            # Set the bid as winning
            winning_bid = self.repository.set_winning_bid(highest_bid).data
            return winning_bid
        except Exception as e:
            logging_service.log_error(e)
            raise e
