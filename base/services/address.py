from typing import Dict, Any
from base.models import Address
from base.utils.responses import APIResponse
from base.services.logging import LoggingService
from rest_framework import status

logging_service = LoggingService()


class AddressService:
    """
    Service for managing addresses.
    """
    
    def get_or_create_address(self, data: Dict[str, Any]) -> APIResponse:
        """
        Get an existing address or create a new one.
        
        Args:
            data: Address data
            
        Returns:
            APIResponse with success status, message, data, and code
        """
        try:
            # Check if address already exists
            existing_address = Address.objects.filter(
                country=data.get('country'),
                province=data.get('province'),
                district=data.get('district'),
                city=data.get('city'),
                street_number=data.get('street_number'),
                code=data.get('code')
            ).first()
            
            if existing_address:
                return APIResponse(
                    success=True,
                    message="Address found",
                    data=existing_address,
                    code=status.HTTP_200_OK
                )
            
            # Create new address
            address = Address.objects.create(**data)
            
            return APIResponse(
                success=True,
                message="Address created successfully",
                data=address,
                code=status.HTTP_201_CREATED
            )
        except Exception as e:
            logging_service.log_error(e)
            return APIResponse(
                success=False,
                message="Failed to get or create address",
                code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def add_address(self, data: Dict[str, Any], obj: Any) -> APIResponse:
        """
        Add an address to an object.
        
        Args:
            data: Address data
            obj: The object to add the address to
            
        Returns:
            APIResponse with success status, message, data, and code
        """
        try:
            # Check if object already has an address
            if hasattr(obj, 'address') and obj.address:
                # Update existing address
                address = obj.address
                for key, value in data.items():
                    setattr(address, key, value)
                address.save()
                
                return APIResponse(
                    success=True,
                    message="Address updated successfully",
                    data=address,
                    code=status.HTTP_200_OK
                )
            
            # Create new address
            address_response = self.get_or_create_address(data)
            
            if not address_response.success:
                return address_response
            
            # Add address to object
            obj.address = address_response.data
            obj.save()
            
            return APIResponse(
                success=True,
                message="Address added successfully",
                data=address_response.data,
                code=status.HTTP_200_OK
            )
        except Exception as e:
            logging_service.log_error(e)
            return APIResponse(
                success=False,
                message="Failed to add address",
                code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
