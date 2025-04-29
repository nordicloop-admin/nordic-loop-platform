from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from subscriptions.models import Subscription, SubscriptionPlan, SubscriptionHistory
from subscriptions.repositories.subscription_repository import SubscriptionRepository
from users.models import CustomUser


class SubscriptionRepositoryTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email="test@example.com",
            name="Test User",
            password="testpassword"
        )
        
        self.plan = SubscriptionPlan.objects.create(
            name="Basic Plan",
            plan_type="basic",
            description="Basic subscription plan",
            price=9.99,
            duration_days=30
        )
        
        self.repository = SubscriptionRepository()

    def test_create_subscription(self):
        response = self.repository.create_subscription(
            user=self.user,
            plan_id=self.plan.id
        )

        self.assertTrue(response.success)
        self.assertEqual(Subscription.objects.count(), 1)
        self.assertEqual(response.data.user, self.user)
        self.assertEqual(response.data.plan, self.plan)
        self.assertEqual(response.data.status, "pending")
        
        # Check that history record was created
        self.assertEqual(SubscriptionHistory.objects.count(), 1)
        history = SubscriptionHistory.objects.first()
        self.assertEqual(history.action, "created")
        self.assertEqual(history.to_plan, self.plan)

    def test_create_subscription_invalid_plan(self):
        response = self.repository.create_subscription(
            user=self.user,
            plan_id=999
        )

        self.assertFalse(response.success)
        self.assertEqual(response.message, "Subscription plan not found")
        self.assertEqual(Subscription.objects.count(), 0)

    def test_get_subscription_by_id_success(self):
        # Create a subscription first
        subscription_response = self.repository.create_subscription(
            user=self.user,
            plan_id=self.plan.id
        )
        subscription_id = subscription_response.data.id
        
        # Get the subscription by ID
        response = self.repository.get_subscription_by_id(subscription_id)

        self.assertTrue(response.success)
        self.assertEqual(response.data.id, subscription_id)
        self.assertEqual(response.data.user, self.user)
        self.assertEqual(response.data.plan, self.plan)

    def test_get_subscription_by_id_not_found(self):
        response = self.repository.get_subscription_by_id(999)
        
        self.assertFalse(response.success)
        self.assertEqual(response.message, "Subscription not found")

    def test_get_active_subscription_for_user(self):
        # Create a subscription with active status
        subscription = Subscription.objects.create(
            user=self.user,
            plan=self.plan,
            status="active",
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30)
        )
        
        response = self.repository.get_active_subscription_for_user(self.user)
        
        self.assertTrue(response.success)
        self.assertEqual(response.data.id, subscription.id)
        self.assertEqual(response.message, "Active subscription found")

    def test_get_active_subscription_for_user_none_found(self):
        # Create a subscription with non-active status
        Subscription.objects.create(
            user=self.user,
            plan=self.plan,
            status="expired",
            start_date=timezone.now() - timedelta(days=60),
            end_date=timezone.now() - timedelta(days=30)
        )
        
        response = self.repository.get_active_subscription_for_user(self.user)
        
        self.assertFalse(response.success)
        self.assertEqual(response.message, "No active subscription found for this user")

    def test_get_subscriptions_by_user(self):
        # Create multiple subscriptions for the user
        subscription1 = Subscription.objects.create(
            user=self.user,
            plan=self.plan,
            status="active"
        )
        
        subscription2 = Subscription.objects.create(
            user=self.user,
            plan=self.plan,
            status="expired"
        )
        
        response = self.repository.get_subscriptions_by_user(self.user)
        
        self.assertTrue(response.success)
        self.assertEqual(response.data.count(), 2)
        self.assertIn(subscription1, response.data)
        self.assertIn(subscription2, response.data)

    def test_get_subscriptions_by_plan(self):
        # Create a subscription for the plan
        subscription = Subscription.objects.create(
            user=self.user,
            plan=self.plan,
            status="active"
        )
        
        # Create another plan and subscription
        other_plan = SubscriptionPlan.objects.create(
            name="Premium Plan",
            plan_type="premium",
            description="Premium subscription plan",
            price=19.99,
            duration_days=30
        )
        
        other_subscription = Subscription.objects.create(
            user=self.user,
            plan=other_plan,
            status="active"
        )
        
        response = self.repository.get_subscriptions_by_plan(self.plan.id)
        
        self.assertTrue(response.success)
        self.assertEqual(response.data.count(), 1)
        self.assertIn(subscription, response.data)
        self.assertNotIn(other_subscription, response.data)

    def test_get_subscriptions_by_status(self):
        # Create subscriptions with different statuses
        active_subscription = Subscription.objects.create(
            user=self.user,
            plan=self.plan,
            status="active"
        )
        
        expired_subscription = Subscription.objects.create(
            user=self.user,
            plan=self.plan,
            status="expired"
        )
        
        response = self.repository.get_subscriptions_by_status("active")
        
        self.assertTrue(response.success)
        self.assertEqual(response.data.count(), 1)
        self.assertIn(active_subscription, response.data)
        self.assertNotIn(expired_subscription, response.data)

    def test_update_subscription(self):
        # Create a subscription
        subscription_response = self.repository.create_subscription(
            user=self.user,
            plan_id=self.plan.id
        )
        subscription_id = subscription_response.data.id
        
        # Create a new plan
        new_plan = SubscriptionPlan.objects.create(
            name="Premium Plan",
            plan_type="premium",
            description="Premium subscription plan",
            price=19.99,
            duration_days=30
        )
        
        # Update the subscription
        update_data = {
            "status": "active",
            "auto_renew": True,
            "plan": new_plan.id
        }
        
        response = self.repository.update_subscription(subscription_id, update_data)
        
        self.assertTrue(response.success)
        self.assertEqual(response.data.status, "active")
        self.assertEqual(response.data.auto_renew, True)
        self.assertEqual(response.data.plan, new_plan)
        
        # Check that history record was created for plan change
        self.assertEqual(SubscriptionHistory.objects.count(), 2)  # 1 for create, 1 for change
        history = SubscriptionHistory.objects.filter(action="changed").first()
        self.assertEqual(history.from_plan, self.plan)
        self.assertEqual(history.to_plan, new_plan)

    def test_update_subscription_not_found(self):
        response = self.repository.update_subscription(999, {"status": "active"})
        
        self.assertFalse(response.success)
        self.assertEqual(response.message, "Subscription not found")

    def test_cancel_subscription(self):
        # Create a subscription
        subscription_response = self.repository.create_subscription(
            user=self.user,
            plan_id=self.plan.id,
            data={"status": "active", "auto_renew": True}
        )
        subscription_id = subscription_response.data.id
        
        response = self.repository.cancel_subscription(subscription_id, notes="Customer requested cancellation")
        
        self.assertTrue(response.success)
        self.assertEqual(response.data.status, "cancelled")
        self.assertEqual(response.data.auto_renew, False)
        
        # Check that history record was created
        self.assertEqual(SubscriptionHistory.objects.count(), 2)  # 1 for create, 1 for cancel
        history = SubscriptionHistory.objects.filter(action="cancelled").first()
        self.assertEqual(history.from_plan, self.plan)
        self.assertEqual(history.notes, "Customer requested cancellation")

    def test_renew_subscription(self):
        # Create a subscription
        subscription = Subscription.objects.create(
            user=self.user,
            plan=self.plan,
            status="active",
            start_date=timezone.now() - timedelta(days=30),
            end_date=timezone.now()
        )
        
        response = self.repository.renew_subscription(subscription.id, days=60, notes="Extended renewal")
        
        self.assertTrue(response.success)
        self.assertEqual(response.data.status, "active")
        # Check that end date was extended by 60 days
        self.assertGreater(response.data.end_date, timezone.now() + timedelta(days=59))
        
        # Check that history record was created
        history = SubscriptionHistory.objects.filter(action="renewed").first()
        self.assertEqual(history.to_plan, self.plan)
        self.assertEqual(history.notes, "Extended renewal")

    def test_expire_subscription(self):
        # Create a subscription
        subscription = Subscription.objects.create(
            user=self.user,
            plan=self.plan,
            status="active"
        )
        
        response = self.repository.expire_subscription(subscription.id)
        
        self.assertTrue(response.success)
        self.assertEqual(response.data.status, "expired")
        
        # Check that history record was created
        history = SubscriptionHistory.objects.filter(action="expired").first()
        self.assertEqual(history.from_plan, self.plan)

    def test_get_subscription_history(self):
        # Create a subscription with multiple history events
        subscription_response = self.repository.create_subscription(
            user=self.user,
            plan_id=self.plan.id
        )
        subscription_id = subscription_response.data.id
        
        # Cancel the subscription
        self.repository.cancel_subscription(subscription_id, notes="Test cancellation")
        
        # Get the history
        response = self.repository.get_subscription_history(subscription_id)
        
        self.assertTrue(response.success)
        self.assertEqual(response.data.count(), 2)  # 1 for create, 1 for cancel
        
        # Check that history records are in the correct order (newest first)
        self.assertEqual(response.data[0].action, "cancelled")
        self.assertEqual(response.data[1].action, "created")
