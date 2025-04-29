from typing import Dict, Any, Optional, List
from django.utils import timezone
from django.db import transaction
from auctions.models import Auction, AuctionImage, Category
from auctions.repositories.auction_repository import AuctionRepository
from auctions.repositories.category_repository import CategoryRepository
from base.services.logging import LoggingService
from users.models import CustomUser

logging_service = LoggingService()


class AuctionService:
    """
    Service class for auction-related operations.
    This class handles business logic related to auctions.
    """

    def __init__(self, auction_repository: AuctionRepository, category_repository: CategoryRepository):
        self.repository = auction_repository
        self.category_repository = category_repository

    def create_auction(self, seller: CustomUser, auction_data: Dict[str, Any]) -> Auction:
        """
        Create a new auction.

        Args:
            seller: The user creating the auction
            auction_data: Dictionary containing auction data

        Returns:
            The created auction object

        Raises:
            ValueError: If required fields are missing or invalid
        """
        try:
            # Validate required fields
            required_fields = ['title', 'description', 'category', 'quantity', 'unit',
                              'location', 'starting_price', 'end_date']

            for field in required_fields:
                if field not in auction_data or not auction_data[field]:
                    raise ValueError(f"{field.replace('_', ' ').title()} is required")

            # Validate category
            category_id = auction_data.get('category')
            if isinstance(category_id, int):
                category = self.category_repository.get_category_by_id(category_id).data
                if not category:
                    raise ValueError(f"Category with ID {category_id} does not exist")
                if not category.is_active:
                    raise ValueError(f"Category '{category.name}' is not active")
                auction_data['category'] = category

            # Validate dates
            end_date = auction_data.get('end_date')
            if end_date and end_date <= timezone.now():
                raise ValueError("End date must be in the future")

            # Set seller and initial values
            auction_data['seller'] = seller
            auction_data['current_price'] = auction_data.get('starting_price')

            # Create the auction
            auction = self.repository.create_auction(auction_data).data
            return auction
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def get_auction_by_id(self, auction_id: int) -> Optional[Auction]:
        """
        Get an auction by ID.

        Args:
            auction_id: Auction's ID

        Returns:
            The auction object if found, None otherwise
        """
        try:
            auction = self.repository.get_auction_by_id(auction_id).data
            return auction
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def get_auctions_by_seller(self, seller: CustomUser) -> List[Auction]:
        """
        Get all auctions by a seller.

        Args:
            seller: The seller user

        Returns:
            List of auctions
        """
        try:
            auctions = self.repository.get_auctions_by_seller(seller).data
            return auctions
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def get_auctions_by_category(self, category: Category) -> List[Auction]:
        """
        Get all auctions in a category.

        Args:
            category: The category

        Returns:
            List of auctions
        """
        try:
            auctions = self.repository.get_auctions_by_category(category).data
            return auctions
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def get_active_auctions(self) -> List[Auction]:
        """
        Get all active auctions.

        Returns:
            List of active auctions
        """
        try:
            auctions = self.repository.get_active_auctions().data
            return auctions
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def get_featured_auctions(self) -> List[Auction]:
        """
        Get all featured auctions.

        Returns:
            List of featured auctions
        """
        try:
            auctions = self.repository.get_featured_auctions().data
            return auctions
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def search_auctions(self, query: str) -> List[Auction]:
        """
        Search for auctions.

        Args:
            query: Search query

        Returns:
            List of matching auctions
        """
        try:
            auctions = self.repository.search_auctions(query).data
            return auctions
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def update_auction(self, auction: Auction, **kwargs) -> Auction:
        """
        Update an auction.

        Args:
            auction: The auction to update
            **kwargs: Fields to update

        Returns:
            The updated auction object

        Raises:
            ValueError: If the auction cannot be updated
        """
        try:
            # Check if auction can be updated
            if auction.status not in ['draft', 'pending']:
                raise ValueError("Only draft or pending auctions can be updated")

            # Validate category if provided
            category_id = kwargs.get('category')
            if isinstance(category_id, int):
                category = self.category_repository.get_category_by_id(category_id).data
                if not category:
                    raise ValueError(f"Category with ID {category_id} does not exist")
                if not category.is_active:
                    raise ValueError(f"Category '{category.name}' is not active")
                kwargs['category'] = category

            # Validate end date if provided
            end_date = kwargs.get('end_date')
            if end_date and end_date <= timezone.now():
                raise ValueError("End date must be in the future")

            # Update the auction
            auction = self.repository.update_auction(auction.id, kwargs).data
            return auction
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def delete_auction(self, auction: Auction) -> None:
        """
        Delete an auction.

        Args:
            auction: The auction to delete

        Raises:
            ValueError: If the auction cannot be deleted
        """
        try:
            # Check if auction can be deleted
            if auction.status not in ['draft', 'pending', 'cancelled']:
                raise ValueError("Only draft, pending, or cancelled auctions can be deleted")

            # Delete the auction
            self.repository.delete_auction(auction.id)
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def publish_auction(self, auction: Auction) -> Auction:
        """
        Publish an auction (change status from draft to pending).

        Args:
            auction: The auction to publish

        Returns:
            The updated auction object

        Raises:
            ValueError: If the auction cannot be published
        """
        try:
            # Check if auction can be published
            if auction.status != 'draft':
                raise ValueError("Only draft auctions can be published")

            # Check if auction has all required fields
            if not all([
                auction.title,
                auction.description,
                auction.category,
                auction.quantity,
                auction.unit,
                auction.location,
                auction.starting_price,
                auction.end_date
            ]):
                raise ValueError("Auction is missing required fields")

            # Check if end date is in the future
            if auction.end_date <= timezone.now():
                raise ValueError("End date must be in the future")

            # Update the auction status
            auction = self.repository.update_auction(auction.id, {'status': 'pending'}).data
            return auction
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def approve_auction(self, auction: Auction) -> Auction:
        """
        Approve an auction (change status from pending to active).

        Args:
            auction: The auction to approve

        Returns:
            The updated auction object

        Raises:
            ValueError: If the auction cannot be approved
        """
        try:
            # Check if auction can be approved
            if auction.status != 'pending':
                raise ValueError("Only pending auctions can be approved")

            # Update the auction status
            auction = self.repository.update_auction(auction.id, {'status': 'active'}).data
            return auction
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def reject_auction(self, auction: Auction) -> Auction:
        """
        Reject an auction (change status from pending to draft).

        Args:
            auction: The auction to reject

        Returns:
            The updated auction object

        Raises:
            ValueError: If the auction cannot be rejected
        """
        try:
            # Check if auction can be rejected
            if auction.status != 'pending':
                raise ValueError("Only pending auctions can be rejected")

            # Update the auction status
            auction =  self.repository.update_auction(auction.id, {'status': 'draft'}).data
            return auction
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def cancel_auction(self, auction: Auction) -> Auction:
        """
        Cancel an auction.

        Args:
            auction: The auction to cancel

        Returns:
            The updated auction object

        Raises:
            ValueError: If the auction cannot be cancelled
        """
        try:
            # Check if auction can be cancelled
            if auction.status not in ['active', 'pending']:
                raise ValueError("Only active or pending auctions can be cancelled")

            # Update the auction status
            auction = self.repository.update_auction(auction.id, {'status': 'cancelled'}).data
            return auction
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def end_auction(self, auction: Auction) -> Auction:
        """
        End an auction.

        Args:
            auction: The auction to end

        Returns:
            The updated auction object

        Raises:
            ValueError: If the auction cannot be ended
        """
        try:
            # Check if auction can be ended
            if auction.status != 'active':
                raise ValueError("Only active auctions can be ended")

            # Update the auction status
            auction = self.repository.update_auction(auction.id, {'status': 'ended'}).data
            return auction
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def complete_auction(self, auction: Auction) -> Auction:
        """
        Complete an auction.

        Args:
            auction: The auction to complete

        Returns:
            The updated auction object

        Raises:
            ValueError: If the auction cannot be completed
        """
        try:
            # Check if auction can be completed
            if auction.status != 'ended':
                raise ValueError("Only ended auctions can be completed")

            # Update the auction status
            auction = self.repository.update_auction(auction.id, {'status': 'completed'}).data
            return auction
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def add_image_to_auction(self, auction: Auction, image_data: Dict[str, Any]) -> AuctionImage:
        """
        Add an image to an auction.

        Args:
            auction: The auction to add the image to
            image_data: Dictionary containing image data

        Returns:
            The created image object

        Raises:
            ValueError: If the image cannot be added
        """
        try:
            # Check if auction can have images added
            if auction.status not in ['draft', 'pending']:
                raise ValueError("Only draft or pending auctions can have images added")

            # Add the image
            image = self.repository.add_image_to_auction(auction.id, image_data).data
            return image
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def get_auction_images(self, auction: Auction) -> List[AuctionImage]:
        """
        Get all images for an auction.

        Args:
            auction: The auction to get images for

        Returns:
            List of images
        """
        try:
            images = self.repository.get_auction_images(auction.id).data
            return images
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def get_primary_image(self, auction: Auction) -> Optional[AuctionImage]:
        """
        Get the primary image for an auction.

        Args:
            auction: The auction to get the primary image for

        Returns:
            The primary image if found, None otherwise
        """
        try:
            image = self.repository.get_primary_image(auction.id).data
            return image
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def check_ended_auctions(self) -> List[Auction]:
        """
        Check for auctions that have ended but still have 'active' status.

        Returns:
            List of auctions that were updated to 'ended' status
        """
        try:
            now = timezone.now()
            ended_auctions = []

            # Get all active auctions that have ended
            active_auctions = self.repository.get_active_auctions().data
            if active_auctions:
                for auction in active_auctions:
                    if auction.end_date <= now:
                        # Update the auction status
                        self.repository.update_auction(auction.id, {'status': 'ended'})
                        ended_auctions.append(auction)

            return ended_auctions
        except Exception as e:
            logging_service.log_error(e)
            raise e
