from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from base.utils.responses import APIResponse


class BaseAPIView(APIView):
    """
    Base API view that handles standard response formatting.
    """
    
    def get_response(self, api_response):
        """
        Convert an APIResponse to a DRF Response.
        
        Args:
            api_response: An APIResponse object
            
        Returns:
            A DRF Response object
        """
        return Response(
            api_response.to_dict(),
            status=api_response.code
        )
    
    def success_response(self, data=None, message="", code=status.HTTP_200_OK):
        """
        Create a success response.
        
        Args:
            data: The data to include in the response
            message: A message describing the result
            code: The HTTP status code
            
        Returns:
            A DRF Response object
        """
        api_response = APIResponse(
            success=True,
            message=message,
            data=data,
            code=code
        )
        return self.get_response(api_response)
    
    def error_response(self, message="An error occurred", code=status.HTTP_400_BAD_REQUEST, errors=None):
        """
        Create an error response.
        
        Args:
            message: A message describing the error
            code: The HTTP status code
            errors: A dictionary of field-specific errors
            
        Returns:
            A DRF Response object
        """
        api_response = APIResponse(
            success=False,
            message=message,
            code=code,
            errors=errors
        )
        return self.get_response(api_response)
