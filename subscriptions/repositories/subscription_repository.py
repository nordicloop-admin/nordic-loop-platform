from django.db.models import Q
from subscriptions.models import Subscription, SubscriptionPlan, SubscriptionFeature, SubscriptionHistory
from users.models import CustomUser
from base.utils.responses import RepositoryResponse
from base.services.logging import LoggingService

logging_service = LoggingService()


class SubscriptionRepository:
    """
    A class to manage CRUD operations for Subscription
    """

    def create_subscription(self, user, plan_id, data=None) -> RepositoryResponse:
        """
        Creates a new subscription for the user

        Args:
            user: The user to create a subscription for
            plan_id: The ID of the subscription plan
            data: Additional data for the subscription

        Returns:
            RepositoryResponse with success status, message, and data
        """
        if data is None:
            data = {}

        try:
            plan = SubscriptionPlan.objects.get(id=plan_id)

            subscription = Subscription.objects.create(
                user=user,
                plan=plan,
                **data
            )

            # Create history record
            SubscriptionHistory.objects.create(
                subscription=subscription,
                action='created',
                to_plan=plan
            )

            return RepositoryResponse(
                success=True,
                message="Subscription created successfully",
                data=subscription,
            )
        except SubscriptionPlan.DoesNotExist:
            return RepositoryResponse(
                success=False,
                message="Subscription plan not found",
                data=None,
            )
        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(
                success=False,
                message="Failed to create subscription",
                data=None,
            )

    def get_subscription_by_id(self, id) -> RepositoryResponse:
        """
        Get a subscription by ID

        Args:
            id: Subscription's ID

        Returns:
            RepositoryResponse with success status, message, and data
        """
        try:
            subscription = Subscription.objects.select_related('user', 'plan').get(id=id)
            return RepositoryResponse(
                success=True,
                message="Subscription found",
                data=subscription,
            )
        except Subscription.DoesNotExist:
            return RepositoryResponse(
                success=False,
                message="Subscription not found",
                data=None,
            )
        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(
                success=False,
                message="Failed to get subscription",
                data=None,
            )

    def get_active_subscription_for_user(self, user) -> RepositoryResponse:
        """
        Get the active subscription for a user

        Args:
            user: The user to get the subscription for

        Returns:
            RepositoryResponse with success status, message, and data
        """
        try:
            subscription = Subscription.objects.select_related('user', 'plan').filter(
                user=user,
                status='active'
            ).order_by('-start_date').first()

            if subscription:
                return RepositoryResponse(
                    success=True,
                    message="Active subscription found",
                    data=subscription,
                )
            else:
                return RepositoryResponse(
                    success=False,
                    message="No active subscription found for this user",
                    data=None,
                )
        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(
                success=False,
                message="Failed to get active subscription",
                data=None,
            )

    def get_subscriptions_by_user(self, user) -> RepositoryResponse:
        """
        Get all subscriptions for a user

        Args:
            user: The user to get subscriptions for

        Returns:
            RepositoryResponse with success status, message, and data
        """
        try:
            subscriptions = Subscription.objects.select_related('user', 'plan').filter(
                user=user
            ).order_by('-start_date')

            return RepositoryResponse(
                success=True,
                message="Subscriptions retrieved successfully",
                data=subscriptions,
            )
        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(
                success=False,
                message="Failed to get subscriptions",
                data=None,
            )

    def get_subscriptions_by_plan(self, plan_id) -> RepositoryResponse:
        """
        Get all subscriptions for a plan

        Args:
            plan_id: The ID of the plan to get subscriptions for

        Returns:
            RepositoryResponse with success status, message, and data
        """
        try:
            plan = SubscriptionPlan.objects.get(id=plan_id)
            subscriptions = Subscription.objects.select_related('user', 'plan').filter(plan=plan)

            return RepositoryResponse(
                success=True,
                message=f"Subscriptions for plan '{plan.name}' retrieved successfully",
                data=subscriptions,
            )
        except SubscriptionPlan.DoesNotExist:
            return RepositoryResponse(
                success=False,
                message="Subscription plan not found",
                data=None,
            )
        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(
                success=False,
                message="Failed to get subscriptions by plan",
                data=None,
            )

    def get_subscriptions_by_status(self, status) -> RepositoryResponse:
        """
        Get all subscriptions with a specific status

        Args:
            status: The status to filter by

        Returns:
            RepositoryResponse with success status, message, and data
        """
        try:
            subscriptions = Subscription.objects.select_related('user', 'plan').filter(status=status)

            return RepositoryResponse(
                success=True,
                message=f"Subscriptions with status '{status}' retrieved successfully",
                data=subscriptions,
            )
        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(
                success=False,
                message="Failed to get subscriptions by status",
                data=None,
            )

    def update_subscription(self, id, data) -> RepositoryResponse:
        """
        Update a subscription

        Args:
            id: The ID of the subscription to update
            data: Fields to update

        Returns:
            RepositoryResponse with success status, message, and data
        """
        try:
            subscription = Subscription.objects.select_related('user', 'plan').get(id=id)

            # Check if plan is being changed
            old_plan = subscription.plan
            new_plan_id = data.get('plan', None)
            new_plan = None

            if new_plan_id:
                try:
                    new_plan = SubscriptionPlan.objects.get(id=new_plan_id)
                    data['plan'] = new_plan
                except SubscriptionPlan.DoesNotExist:
                    return RepositoryResponse(
                        success=False,
                        message="Subscription plan not found",
                        data=None,
                    )

            # Update fields
            for key, value in data.items():
                setattr(subscription, key, value)

            subscription.save()

            # Create history record if plan changed
            if new_plan and new_plan != old_plan:
                SubscriptionHistory.objects.create(
                    subscription=subscription,
                    action='changed',
                    from_plan=old_plan,
                    to_plan=new_plan
                )

            return RepositoryResponse(
                success=True,
                message="Subscription updated successfully",
                data=subscription,
            )
        except Subscription.DoesNotExist:
            return RepositoryResponse(
                success=False,
                message="Subscription not found",
                data=None,
            )
        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(
                success=False,
                message="Failed to update subscription",
                data=None,
            )

    def cancel_subscription(self, id, notes=None) -> RepositoryResponse:
        """
        Cancel a subscription

        Args:
            id: The ID of the subscription to cancel
            notes: Optional notes about the cancellation

        Returns:
            RepositoryResponse with success status, message, and data
        """
        try:
            subscription = Subscription.objects.select_related('user', 'plan').get(id=id)

            subscription.status = 'cancelled'
            subscription.auto_renew = False
            subscription.save()

            # Create history record
            SubscriptionHistory.objects.create(
                subscription=subscription,
                action='cancelled',
                from_plan=subscription.plan,
                notes=notes
            )

            return RepositoryResponse(
                success=True,
                message="Subscription cancelled successfully",
                data=subscription,
            )
        except Subscription.DoesNotExist:
            return RepositoryResponse(
                success=False,
                message="Subscription not found",
                data=None,
            )
        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(
                success=False,
                message="Failed to cancel subscription",
                data=None,
            )

    def renew_subscription(self, id, days=None, notes=None) -> RepositoryResponse:
        """
        Renew a subscription

        Args:
            id: The ID of the subscription to renew
            days: Number of days to renew for (default: plan's duration)
            notes: Optional notes about the renewal

        Returns:
            RepositoryResponse with success status, message, and data
        """
        try:
            subscription = Subscription.objects.select_related('user', 'plan').get(id=id)

            subscription.renew(days=days)

            # Create history record
            SubscriptionHistory.objects.create(
                subscription=subscription,
                action='renewed',
                to_plan=subscription.plan,
                notes=notes
            )

            return RepositoryResponse(
                success=True,
                message="Subscription renewed successfully",
                data=subscription,
            )
        except Subscription.DoesNotExist:
            return RepositoryResponse(
                success=False,
                message="Subscription not found",
                data=None,
            )
        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(
                success=False,
                message="Failed to renew subscription",
                data=None,
            )

    def expire_subscription(self, id) -> RepositoryResponse:
        """
        Mark a subscription as expired

        Args:
            id: The ID of the subscription to expire

        Returns:
            RepositoryResponse with success status, message, and data
        """
        try:
            subscription = Subscription.objects.select_related('user', 'plan').get(id=id)

            subscription.status = 'expired'
            subscription.save()

            # Create history record
            SubscriptionHistory.objects.create(
                subscription=subscription,
                action='expired',
                from_plan=subscription.plan
            )

            return RepositoryResponse(
                success=True,
                message="Subscription marked as expired",
                data=subscription,
            )
        except Subscription.DoesNotExist:
            return RepositoryResponse(
                success=False,
                message="Subscription not found",
                data=None,
            )
        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(
                success=False,
                message="Failed to expire subscription",
                data=None,
            )

    def get_subscription_history(self, id) -> RepositoryResponse:
        """
        Get the history for a subscription

        Args:
            id: The ID of the subscription to get history for

        Returns:
            RepositoryResponse with success status, message, and data
        """
        try:
            subscription = Subscription.objects.get(id=id)
            history = SubscriptionHistory.objects.filter(subscription=subscription).order_by('-timestamp')

            return RepositoryResponse(
                success=True,
                message="Subscription history retrieved successfully",
                data=history,
            )
        except Subscription.DoesNotExist:
            return RepositoryResponse(
                success=False,
                message="Subscription not found",
                data=None,
            )
        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(
                success=False,
                message="Failed to get subscription history",
                data=None,
            )
