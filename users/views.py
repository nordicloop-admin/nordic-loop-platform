from users.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from company.models import Company
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from django.contrib.auth import authenticate, login
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import UserSerializer, AdminUserListSerializer, AdminUserDetailSerializer, UserProfileSerializer
from users.repository.user_repository import UserRepository
from users.services.user_service import UserService

# Initialize repository and service
repository = UserRepository()
service = UserService(repository)


class ContactSignupView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response({"error": "Email and password are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            company = Company.objects.get(primary_email=email)
        except Company.DoesNotExist:
            return Response({"error": "No company found with this email."}, status=status.HTTP_404_NOT_FOUND)

        if User.objects.filter(email=email).exists():
            return Response({"error": "User already registered with this email."}, status=status.HTTP_400_BAD_REQUEST)

        full_name = f"{company.primary_first_name or ''} {company.primary_last_name or ''}".strip()

        user = User.objects.create_user(
            username=full_name,
            email=email,
            name=full_name,
            password=password,
            company=company
        )

        return Response({
            "message": "User created successfully.",
            "username": user.username,
            "company": str(user.company)
        }, status=status.HTTP_201_CREATED)


class ContactLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response({"error": "Email and password are required."}, status=status.HTTP_400_BAD_REQUEST)

        user = None
        company = Company.objects.filter(primary_email=email).first()

        if company:
            user = User.objects.filter(email=email, company=company).first()
        else:
            user = User.objects.filter(email=email, role="Admin").first()

        if not user:
            return Response({"error": "Unauthorized login. Not a company contact or admin."}, status=status.HTTP_403_FORBIDDEN)

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

            # Get filtered users
            pagination_data = service.get_admin_users_filtered(
                search=search,
                company=company,
                is_active=is_active,
                page=page,
                page_size=page_size
            )

            # Serialize the results
            serializer = AdminUserListSerializer(pagination_data['results'], many=True)
            
            # Format response according to specification
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
        except Exception as e:
            return Response(
                {"error": "Failed to retrieve users"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


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
