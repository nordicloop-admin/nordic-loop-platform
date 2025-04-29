from typing import Dict, Any, Optional, List
from django.db.models import Q
from auctions.models import Auction, AuctionImage, Category
from users.models import CustomUser


class AuctionRepository:
    """
    Repository class for auction-related database operations.
    """
    
    @staticmethod
    def create_auction(auction_data: Dict[str, Any]) -> Auction:
        """
        Create a new auction.
        
        Args:
            auction_data: Dictionary containing auction data
            
        Returns:
            The created auction object
        """
        auction = Auction(**auction_data)
        auction.save()
        return auction
    
    @staticmethod
    def get_auction_by_id(auction_id: int) -> Optional[Auction]:
        """
        Get an auction by ID.
        
        Args:
            auction_id: Auction's ID
            
        Returns:
            The auction object if found, None otherwise
        """
        try:
            return Auction.objects.get(id=auction_id)
        except Auction.DoesNotExist:
            return None
    
    @staticmethod
    def get_auctions_by_seller(seller: CustomUser) -> List[Auction]:
        """
        Get all auctions by a seller.
        
        Args:
            seller: The seller user
            
        Returns:
            List of auctions
        """
        return Auction.objects.filter(seller=seller).order_by('-created_at')
    
    @staticmethod
    def get_auctions_by_category(category: Category) -> List[Auction]:
        """
        Get all auctions in a category.
        
        Args:
            category: The category
            
        Returns:
            List of auctions
        """
        return Auction.objects.filter(category=category, status='active').order_by('-created_at')
    
    @staticmethod
    def get_active_auctions() -> List[Auction]:
        """
        Get all active auctions.
        
        Returns:
            List of active auctions
        """
        return Auction.objects.filter(status='active').order_by('-created_at')
    
    @staticmethod
    def get_featured_auctions() -> List[Auction]:
        """
        Get all featured auctions.
        
        Returns:
            List of featured auctions
        """
        return Auction.objects.filter(status='active', is_featured=True).order_by('-created_at')
    
    @staticmethod
    def search_auctions(query: str) -> List[Auction]:
        """
        Search for auctions.
        
        Args:
            query: Search query
            
        Returns:
            List of matching auctions
        """
        return Auction.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(location__icontains=query),
            status='active'
        ).order_by('-created_at')
    
    @staticmethod
    def update_auction(auction: Auction, **kwargs) -> Auction:
        """
        Update an auction.
        
        Args:
            auction: The auction to update
            **kwargs: Fields to update
            
        Returns:
            The updated auction object
        """
        for key, value in kwargs.items():
            setattr(auction, key, value)
        
        auction.save()
        return auction
    
    @staticmethod
    def delete_auction(auction: Auction) -> None:
        """
        Delete an auction.
        
        Args:
            auction: The auction to delete
        """
        auction.delete()
    
    @staticmethod
    def add_image_to_auction(auction: Auction, image_data: Dict[str, Any]) -> AuctionImage:
        """
        Add an image to an auction.
        
        Args:
            auction: The auction to add the image to
            image_data: Dictionary containing image data
            
        Returns:
            The created image object
        """
        image_data['auction'] = auction
        image = AuctionImage(**image_data)
        image.save()
        
        # If this is the first image or is_primary is True, make it the primary image
        if image.is_primary or auction.images.count() == 1:
            # Set all other images to not primary
            if image.is_primary:
                auction.images.exclude(id=image.id).update(is_primary=False)
            else:
                image.is_primary = True
                image.save()
        
        return image
    
    @staticmethod
    def get_auction_images(auction: Auction) -> List[AuctionImage]:
        """
        Get all images for an auction.
        
        Args:
            auction: The auction to get images for
            
        Returns:
            List of images
        """
        return auction.images.all().order_by('-is_primary', 'created_at')
    
    @staticmethod
    def get_primary_image(auction: Auction) -> Optional[AuctionImage]:
        """
        Get the primary image for an auction.
        
        Args:
            auction: The auction to get the primary image for
            
        Returns:
            The primary image if found, None otherwise
        """
        try:
            return auction.images.filter(is_primary=True).first()
        except AuctionImage.DoesNotExist:
            return None
