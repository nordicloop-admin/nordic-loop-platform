from typing import Dict, Any, Optional, List
from django.db.models import Max
from auctions.models import Bid, Auction
from users.models import CustomUser


class BidRepository:
    """
    Repository class for bid-related database operations.
    """
    
    @staticmethod
    def create_bid(bid_data: Dict[str, Any]) -> Bid:
        """
        Create a new bid.
        
        Args:
            bid_data: Dictionary containing bid data
            
        Returns:
            The created bid object
        """
        bid = Bid(**bid_data)
        bid.save()
        return bid
    
    @staticmethod
    def get_bid_by_id(bid_id: int) -> Optional[Bid]:
        """
        Get a bid by ID.
        
        Args:
            bid_id: Bid's ID
            
        Returns:
            The bid object if found, None otherwise
        """
        try:
            return Bid.objects.get(id=bid_id)
        except Bid.DoesNotExist:
            return None
    
    @staticmethod
    def get_bids_by_auction(auction: Auction) -> List[Bid]:
        """
        Get all bids for an auction.
        
        Args:
            auction: The auction to get bids for
            
        Returns:
            List of bids
        """
        return auction.bids.all().order_by('-amount')
    
    @staticmethod
    def get_bids_by_bidder(bidder: CustomUser) -> List[Bid]:
        """
        Get all bids by a bidder.
        
        Args:
            bidder: The bidder user
            
        Returns:
            List of bids
        """
        return Bid.objects.filter(bidder=bidder).order_by('-created_at')
    
    @staticmethod
    def get_highest_bid(auction: Auction) -> Optional[Bid]:
        """
        Get the highest bid for an auction.
        
        Args:
            auction: The auction to get the highest bid for
            
        Returns:
            The highest bid if found, None otherwise
        """
        return auction.bids.order_by('-amount').first()
    
    @staticmethod
    def get_winning_bid(auction: Auction) -> Optional[Bid]:
        """
        Get the winning bid for an auction.
        
        Args:
            auction: The auction to get the winning bid for
            
        Returns:
            The winning bid if found, None otherwise
        """
        return auction.bids.filter(is_winning=True).first()
    
    @staticmethod
    def set_winning_bid(bid: Bid) -> Bid:
        """
        Set a bid as the winning bid.
        
        Args:
            bid: The bid to set as winning
            
        Returns:
            The updated bid object
        """
        # Set all other bids for this auction to not winning
        bid.auction.bids.exclude(id=bid.id).update(is_winning=False)
        
        # Set this bid as winning
        bid.is_winning = True
        bid.save()
        
        return bid
    
    @staticmethod
    def get_bid_count(auction: Auction) -> int:
        """
        Get the number of bids for an auction.
        
        Args:
            auction: The auction to get the bid count for
            
        Returns:
            The number of bids
        """
        return auction.bids.count()
    
    @staticmethod
    def get_unique_bidder_count(auction: Auction) -> int:
        """
        Get the number of unique bidders for an auction.
        
        Args:
            auction: The auction to get the unique bidder count for
            
        Returns:
            The number of unique bidders
        """
        return auction.bids.values('bidder').distinct().count()
    
    @staticmethod
    def has_user_bid_on_auction(auction: Auction, user: CustomUser) -> bool:
        """
        Check if a user has bid on an auction.
        
        Args:
            auction: The auction to check
            user: The user to check
            
        Returns:
            True if the user has bid on the auction, False otherwise
        """
        return auction.bids.filter(bidder=user).exists()
