from users.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from company.models import Company
from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate, login
  # Import the custom user model

class ContactSignupView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        contact_email = request.data.get("email")
        password = request.data.get("password")

        if not contact_email or not password:
            return Response({"error": "Email and password are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            company = Company.objects.get(contact_email=contact_email)
        except Company.DoesNotExist:
            return Response({"error": "No company found with this contact email."}, status=status.HTTP_404_NOT_FOUND)

        if User.objects.filter(email=contact_email).exists():  
            return Response({"error": "User already registered with this email."}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(  
            username=company.contact_name,
            email=contact_email,
            name=company.contact_name or '',
            password=password 
        )

        return Response({
            "message": "User created successfully.",
            "username": user.username,
        }, status=status.HTTP_201_CREATED)


class ContactLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        contact_email = request.data.get("email")
        password = request.data.get("password")

        if not contact_email or not password:
            return Response({"error": "Email and password are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            company = Company.objects.get(contact_email=contact_email)
        except Company.DoesNotExist:
            return Response({"error": "No company found with this contact email."}, status=status.HTTP_404_NOT_FOUND)

        user = User.objects.filter(email=contact_email).first()

        if not user:
            return Response({"error": "No user found with this email."}, status=status.HTTP_404_NOT_FOUND)

        if not user.check_password(password):
            return Response({"error": "Invalid credentials."}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "message": "Login successful.",
            "username": company.contact_name,  
            "email": user.email,
        }, status=status.HTTP_200_OK)

class ListUsersView(APIView):
    def get(self, request):
        users = User.objects.all()
    
        user_data = []
        for user in users:
            user_data.append({
                "username": user.username,
                "email": user.email,
                "date_joined": user.date_joined,
            })
        return Response({"users": user_data}, status=status.HTTP_200_OK)
