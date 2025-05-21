from users.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from company.models import Company
from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate, login
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import UserSerializer


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
            user = User.objects.filter(email=email, role="staff").first()

        if not user:
            return Response({"error": "Unauthorized login. Not a company contact or admin."}, status=status.HTTP_403_FORBIDDEN)

        if not user.check_password(password):
            return Response({"error": "Invalid credentials."}, status=status.HTTP_400_BAD_REQUEST)

        refresh = RefreshToken.for_user(user)

        return Response({
            "message": "Login successful.",
            "username": user.username,
            "email": user.email,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }, status=status.HTTP_200_OK)


class ListUsersView(APIView):
    def get(self, request):
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response({"users": serializer.data})
