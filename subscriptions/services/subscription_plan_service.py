from typing import Dict, Any, Optional, List
from subscriptions.repositories.subscription_plan_repository import SubscriptionPlanRepository
from base.services.logging import LoggingService

logging_service = LoggingService()


class SubscriptionPlanService:
    """
    Service class for subscription plan-related operations.
    This class handles business logic related to subscription plans.
    """

    def __init__(self, subscription_plan_repository: SubscriptionPlanRepository):
        self.repository = subscription_plan_repository

    def create_subscription_plan(self, data: Dict[str, Any]):
        """
        Create a new subscription plan.

        Args:
            data: Dictionary containing subscription plan data

        Returns:
            The created subscription plan object
        """
        try:
            # Create the subscription plan
            subscription_plan = self.repository.create_subscription_plan(data).data
            return subscription_plan
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def get_subscription_plan_by_id(self, subscription_plan_id: int) -> Optional[object]:
        """
        Get a subscription plan by ID.

        Args:
            subscription_plan_id: Subscription plan's ID

        Returns:
            The subscription plan object if found, None otherwise
        """
        try:
            subscription_plan = self.repository.get_subscription_plan_by_id(subscription_plan_id).data
            return subscription_plan
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def get_all_subscription_plans(self) -> List[object]:
        """
        Get all subscription plans.

        Returns:
            List of all subscription plans
        """
        try:
            subscription_plans = self.repository.get_all_subscription_plans().data
            return subscription_plans
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def update_subscription_plan(self, subscription_plan_id: int, data: Dict[str, Any]):
        """
        Update a subscription plan.

        Args:
            subscription_plan_id: The ID of the subscription plan to update
            data: Dictionary containing fields to update

        Returns:
            The updated subscription plan object
        """
        try:
            # Update the subscription plan
            subscription_plan = self.repository.update_subscription_plan(subscription_plan_id, data).data
            return subscription_plan
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def delete_subscription_plan(self, subscription_plan_id: int) -> None:
        """
        Delete a subscription plan.

        Args:
            subscription_plan_id: The ID of the subscription plan to delete
        """
        try:
            # Delete the subscription plan
            self.repository.delete_subscription_plan(subscription_plan_id)
        except Exception as e:
            logging_service.log_error(e)
            raise e