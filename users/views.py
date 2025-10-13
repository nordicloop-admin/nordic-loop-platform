from users.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from company.models import Company
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from django.contrib.auth import authenticate, login
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import UserSerializer, AdminUserListSerializer, AdminUserDetailSerializer, UserProfileSerializer, PasswordChangeSerializer, UserCompanyNameSerializer
from users.repository.user_repository import UserRepository
from users.services.user_service import UserService
from django.db.models import Q

# Initialize repository and service
repository = UserRepository()
service = UserService(repository)


class ContactSignupView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        from users.models import PasswordResetOTP
        from users.services.email_service import email_service

        email = request.data.get("email")
        if not email:
            return Response({"error": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            contact_user = User.objects.get(email=email, contact_type__in=['primary', 'secondary'])
        except User.DoesNotExist:
            return Response({"error": "No company contact found with this email."}, status=status.HTTP_404_NOT_FOUND)

        if contact_user.has_usable_password() and contact_user.password:
            return Response({"error": "Account already activated. Please log in."}, status=status.HTTP_400_BAD_REQUEST)

        otp_obj = PasswordResetOTP.generate_otp(email, purpose='account_activation')
        try:
            recipient_name = contact_user.first_name or contact_user.username or email.split('@')[0]
            email_service.send_account_activation_otp(email, otp_obj.otp, recipient_name)
        except Exception as e:
            print(f"Error sending activation OTP: {e}")
            return Response({"error": "Failed to send activation code"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            "message": "Activation code sent. Verify OTP to proceed to password creation.",
            "step": "otp_sent",
            "email": email
        }, status=status.HTTP_200_OK)


class ContactLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response({"error": "Email and password are required."}, status=status.HTTP_400_BAD_REQUEST)

        # Try to find user by email - could be contact user or admin
        user = User.objects.filter(email=email).first()

        if not user:
            return Response({"error": "No user found with this email."}, status=status.HTTP_404_NOT_FOUND)

        # Check if user is either a company contact or admin
        if not (user.contact_type in ['primary', 'secondary'] or user.role == "Admin"):
            return Response({
                "error": "Unauthorized login. Not a company contact or admin."
            }, status=status.HTTP_403_FORBIDDEN)

        if not user.check_password(password):
            return Response({"error": "Invalid credentials."}, status=status.HTTP_400_BAD_REQUEST)

        refresh = RefreshToken.for_user(user)

        return Response({
            "message": "Login successful.",
            "username": user.username,
            "email": user.email,
            "firstname": user.first_name,
            "lastname": user.last_name,
            "role": user.role,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }, status=status.HTTP_200_OK)


class ListUsersView(APIView):
    def get(self, request):
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response({"users": serializer.data})


class AdminUserListView(APIView):
    """
    Admin endpoint for listing users with filtering and pagination
    GET /api/users/admin/users/
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        try:
            # Get query parameters
            search = request.query_params.get('search', None)
            company = request.query_params.get('company', None)
            is_active = request.query_params.get('is_active', None)
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 10))

            # Convert is_active string to boolean if provided
            if is_active is not None:
                is_active = is_active.lower() in ['true', '1', 'yes', 'active']

            # Get filtered users via service
            pagination_data = service.get_admin_users_filtered(
                search=search,
                company=company,
                is_active=is_active,
                page=page,
                page_size=page_size
            )

            serializer = AdminUserListSerializer(pagination_data['results'], many=True)
            response_data = {
                "count": pagination_data['count'],
                "next": pagination_data['next'],
                "previous": pagination_data['previous'],
                "results": serializer.data,
                "page_size": pagination_data['page_size'],
                "total_pages": pagination_data['total_pages'],
                "current_page": pagination_data['current_page']
            }
            return Response(response_data, status=status.HTTP_200_OK)
        except ValueError as ve:
            return Response({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({"error": "Failed to retrieve users"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminUserDetailView(APIView):
    """
    Admin endpoint for retrieving a specific user
    GET /api/users/admin/users/{id}/
    """
    permission_classes = [IsAdminUser]

    def get(self, request, user_id):
        try:
            # Get user by ID
            user = service.get_user_by_id(user_id)
            
            if not user:
                return Response({
                    'error': 'User not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            serializer = AdminUserDetailSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
                
        except Exception as e:
            return Response({
                'error': 'Failed to retrieve user',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserProfileView(APIView):
    """
    Endpoint for retrieving and updating the logged-in user's profile
    GET /api/users/profile/
    PATCH /api/users/profile/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            # Get the current logged-in user
            user = request.user
            
            serializer = UserProfileSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
                
        except Exception as e:
            return Response({
                'error': 'Failed to retrieve user profile',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def patch(self, request):
        try:
            # Get the current logged-in user
            user = request.user
            
            # Update the user with the provided data
            serializer = UserProfileSerializer(user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'message': 'Profile updated successfully',
                    'user': serializer.data
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': 'Invalid data provided',
                    'details': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                'error': 'Failed to update user profile',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PasswordChangeView(APIView):
    """
    Endpoint for changing the password of the logged-in user
    POST /api/users/change-password/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            # Create serializer with request context
            serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
            
            if serializer.is_valid():
                # Get the current user
                user = request.user
                
                # Set the new password
                user.set_password(serializer.validated_data['new_password'])
                user.save()
                
                return Response({
                    'message': 'Password updated successfully'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': 'Invalid data provided',
                    'details': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                'error': 'Failed to update password',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserCompanySearchView(APIView):
    """
    Endpoint for retrieving user names and their companies with search functionality
    GET /api/users/search/
    """
    permission_classes = [AllowAny]  # Allow anyone to search users and companies
    
    def get(self, request):
        try:
            # Get search query parameter
            search_query = request.query_params.get('query', None)
            
            # Initialize queryset
            queryset = User.objects.select_related('company').all()
            
            if search_query:
                # If search query exists, filter by user name or company name
                queryset = queryset.filter(
                    Q(name__icontains=search_query) | 
                    Q(company__official_name__icontains=search_query)
                )
            else:
                # If no query provided, return recent 10 users
                queryset = queryset.order_by('-date_joined')[:10]
            
            # Serialize the data
            serializer = UserCompanyNameSerializer(queryset, many=True)
            
            return Response({
                'results': serializer.data,
                'count': len(serializer.data)
            }, status=status.HTTP_200_OK)
                
        except Exception as e:
            return Response({
                'error': 'Failed to retrieve users and companies',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
