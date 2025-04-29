from typing import Dict, Any, Optional, List
from subscriptions.repositories.subscription_repository import SubscriptionRepository
from base.services.logging import LoggingService

logging_service = LoggingService()


class SubscriptionService:
    """
    Service class for subscription-related operations.
    This class handles business logic related to subscriptions.
    """

    def __init__(self, subscription_repository: SubscriptionRepository):
        self.repository = subscription_repository

    def create_subscription(self, data: Dict[str, Any]):
        """
        Create a new subscription.

        Args:
            data: Dictionary containing subscription data

        Returns:
            The created subscription object
        """
        try:
            # Create the subscription
            subscription = self.repository.create_subscription(data).data
            return subscription
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def get_subscription_by_id(self, subscription_id: int) -> Optional[object]:
        """
        Get a subscription by ID.

        Args:
            subscription_id: Subscription's ID

        Returns:
            The subscription object if found, None otherwise
        """
        try:
            subscription = self.repository.get_subscription_by_id(subscription_id).data
            return subscription
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def get_all_subscriptions(self) -> List[object]:
        """
        Get all subscriptions.

        Returns:
            List of all subscriptions
        """
        try:
            subscriptions = self.repository.get_all_subscriptions().data
            return subscriptions
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def update_subscription(self, subscription_id: int, data: Dict[str, Any]):
        """
        Update a subscription.

        Args:
            subscription_id: The ID of the subscription to update
            data: Dictionary containing fields to update

        Returns:
            The updated subscription object
        """
        try:
            # Update the subscription
            subscription = self.repository.update_subscription(subscription_id, data).data
            return subscription
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def delete_subscription(self, subscription_id: int) -> None:
        """
        Delete a subscription.

        Args:
            subscription_id: The ID of the subscription to delete
        """
        try:
            # Delete the subscription
            self.repository.delete_subscription(subscription_id)
        except Exception as e:
            logging_service.log_error(e)
            raise e