"""
Custom JWT tokens with additional user claims
"""
from rest_framework_simplejwt.tokens import RefreshToken
from typing import Dict, Any


class CustomRefreshToken(RefreshToken):
    """
    Custom refresh token that includes additional user information in the payload
    """
    
    @classmethod
    def for_user(cls, user):
        """
        Create a refresh token for the given user with custom claims
        """
        token = super().for_user(user)
        
        # Add custom claims to the token payload
        token['email'] = user.email
        token['username'] = user.username
        token['first_name'] = user.first_name or ''
        token['last_name'] = user.last_name or ''
        token['role'] = user.role or ''
        token['contact_type'] = user.contact_type or ''
        
        # Add company information if user has a company
        if hasattr(user, 'company') and user.company:
            token['company_id'] = user.company.id
            token['company_name'] = user.company.official_name
        else:
            token['company_id'] = None
            token['company_name'] = None
            
        # Add user permissions/capabilities
        token['can_place_ads'] = getattr(user, 'can_place_ads', False)
        token['can_place_bids'] = getattr(user, 'can_place_bids', False)
        
        return token


class CustomAccessToken(CustomRefreshToken.access_token_class):
    """
    Custom access token that inherits the custom claims from refresh token
    """
    pass


# Update the access token class for the custom refresh token
CustomRefreshToken.access_token_class = CustomAccessToken