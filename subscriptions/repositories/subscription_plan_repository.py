from typing import Dict, Any, Optional, List
from django.db.models import Q
from subscriptions.models import SubscriptionPlan, SubscriptionFeature


class SubscriptionPlanRepository:
    """
    Repository class for subscription plan-related database operations.
    """
    
    @staticmethod
    def create_plan(plan_data: Dict[str, Any]) -> SubscriptionPlan:
        """
        Create a new subscription plan.
        
        Args:
            plan_data: Dictionary containing plan data
            
        Returns:
            The created plan object
        """
        plan = SubscriptionPlan(**plan_data)
        plan.save()
        return plan
    
    @staticmethod
    def get_plan_by_id(plan_id: int) -> Optional[SubscriptionPlan]:
        """
        Get a plan by ID.
        
        Args:
            plan_id: Plan's ID
            
        Returns:
            The plan object if found, None otherwise
        """
        try:
            return SubscriptionPlan.objects.get(id=plan_id)
        except SubscriptionPlan.DoesNotExist:
            return None
    
    @staticmethod
    def get_plan_by_type(plan_type: str) -> Optional[SubscriptionPlan]:
        """
        Get a plan by type.
        
        Args:
            plan_type: Plan type (basic, premium, enterprise)
            
        Returns:
            The plan object if found, None otherwise
        """
        try:
            return SubscriptionPlan.objects.filter(
                plan_type=plan_type,
                is_active=True
            ).first()
        except SubscriptionPlan.DoesNotExist:
            return None
    
    @staticmethod
    def get_all_plans() -> List[SubscriptionPlan]:
        """
        Get all subscription plans.
        
        Returns:
            List of all plans
        """
        return SubscriptionPlan.objects.all()
    
    @staticmethod
    def get_active_plans() -> List[SubscriptionPlan]:
        """
        Get all active subscription plans.
        
        Returns:
            List of active plans
        """
        return SubscriptionPlan.objects.filter(is_active=True)
    
    @staticmethod
    def update_plan(plan: SubscriptionPlan, **kwargs) -> SubscriptionPlan:
        """
        Update a subscription plan.
        
        Args:
            plan: The plan to update
            **kwargs: Fields to update
            
        Returns:
            The updated plan object
        """
        for key, value in kwargs.items():
            setattr(plan, key, value)
        
        plan.save()
        return plan
    
    @staticmethod
    def delete_plan(plan: SubscriptionPlan) -> None:
        """
        Delete a subscription plan.
        
        Args:
            plan: The plan to delete
        """
        plan.delete()
    
    @staticmethod
    def deactivate_plan(plan: SubscriptionPlan) -> SubscriptionPlan:
        """
        Deactivate a subscription plan.
        
        Args:
            plan: The plan to deactivate
            
        Returns:
            The deactivated plan object
        """
        plan.is_active = False
        plan.save()
        return plan
    
    @staticmethod
    def activate_plan(plan: SubscriptionPlan) -> SubscriptionPlan:
        """
        Activate a subscription plan.
        
        Args:
            plan: The plan to activate
            
        Returns:
            The activated plan object
        """
        plan.is_active = True
        plan.save()
        return plan
    
    @staticmethod
    def add_feature_to_plan(plan: SubscriptionPlan, feature: SubscriptionFeature) -> None:
        """
        Add a feature to a plan.
        
        Args:
            plan: The plan to add the feature to
            feature: The feature to add
        """
        plan.features.add(feature)
    
    @staticmethod
    def remove_feature_from_plan(plan: SubscriptionPlan, feature: SubscriptionFeature) -> None:
        """
        Remove a feature from a plan.
        
        Args:
            plan: The plan to remove the feature from
            feature: The feature to remove
        """
        plan.features.remove(feature)
    
    @staticmethod
    def get_plan_features(plan: SubscriptionPlan) -> List[SubscriptionFeature]:
        """
        Get all features for a plan.
        
        Args:
            plan: The plan to get features for
            
        Returns:
            List of features
        """
        return plan.features.all()
