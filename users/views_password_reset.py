from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings
from mailjet_rest import Client
import os
import json
from .models import PasswordResetOTP

User = get_user_model()

# OTP and token generation is now handled by the PasswordResetOTP model

# Mailjet configuration
MAILJET_API_KEY = os.environ.get('MAILJET_API_KEY', '')
MAILJET_SECRET_KEY = os.environ.get('MAILJET_SECRET_KEY', '')
MAILJET_SENDER_EMAIL = os.environ.get('MAILJET_SENDER_EMAIL', settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@nordicloop.com')
MAILJET_SENDER_NAME = os.environ.get('MAILJET_SENDER_NAME', 'Nordic Loop')

class RequestPasswordResetView(APIView):
    """
    Endpoint for requesting a password reset
    POST /api/users/request-password-reset/
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        try:
            email = request.data.get('email')
            
            if not email:
                return Response({
                    'error': 'Email is required',
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if user exists
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                # For security reasons, don't reveal that the user doesn't exist
                return Response({
                    'message': 'If your email is registered, you will receive a password reset OTP',
                    'success': True
                }, status=status.HTTP_200_OK)
            
            # Generate OTP using our model
            otp_obj = PasswordResetOTP.generate_otp(email)
            
            # Send email with OTP using Mailjet
            try:
                self.send_otp_email(email, otp_obj.otp)
                return Response({
                    'message': 'Password reset OTP has been sent to your email',
                    'success': True
                }, status=status.HTTP_200_OK)
            except Exception as e:
                # Log the error but don't expose details to the client
                print(f"Error sending email via Mailjet: {str(e)}")
                return Response({
                    'message': 'Failed to send OTP email. Please try again later.',
                    'success': False
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            return Response({
                'error': 'Failed to process password reset request',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    def send_otp_email(self, email, otp):
        """Send OTP email using Mailjet"""
        if not MAILJET_API_KEY or not MAILJET_SECRET_KEY:
            raise Exception("Mailjet API credentials not configured")
            
        mailjet = Client(auth=(MAILJET_API_KEY, MAILJET_SECRET_KEY), version='v3.1')
        
        data = {
            'Messages': [
                {
                    "From": {
                        "Email": MAILJET_SENDER_EMAIL,
                        "Name": MAILJET_SENDER_NAME
                    },
                    "To": [
                        {
                            "Email": email,
                            "Name": email.split('@')[0]  # Use part before @ as name
                        }
                    ],
                    "Subject": "Nordic Loop - Password Reset OTP",
                    "TextPart": f"Your OTP for password reset is: {otp}\n\nThis OTP will expire in 30 minutes.",
                    "HTMLPart": f"<h3>Password Reset OTP</h3><p>Your OTP for password reset is: <strong>{otp}</strong></p><p>This OTP will expire in 30 minutes.</p>"
                }
            ]
        }
        
        result = mailjet.send.create(data=data)
        
        # Check if the email was sent successfully
        if result.status_code != 200:
            raise Exception(f"Failed to send email: {result.reason}")
            
        return result


class VerifyOtpView(APIView):
    """
    Endpoint for verifying OTP and generating reset token
    POST /api/users/verify-otp/
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        try:
            email = request.data.get('email')
            otp = request.data.get('otp')
            
            if not email or not otp:
                return Response({
                    'error': 'Email and OTP are required',
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Verify OTP using our model
            otp_obj = PasswordResetOTP.verify_otp(email, otp)
            
            if not otp_obj:
                return Response({
                    'error': 'Invalid or expired OTP',
                    'success': False
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Generate reset token
            token = otp_obj.generate_token()
            
            return Response({
                'message': 'OTP verified successfully',
                'success': True,
                'token': token
            }, status=status.HTTP_200_OK)
                
        except Exception as e:
            return Response({
                'error': 'Failed to verify OTP',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ResetPasswordView(APIView):
    """
    Endpoint for resetting password using token
    POST /api/users/reset-password/
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        try:
            email = request.data.get('email')
            token = request.data.get('token')
            new_password = request.data.get('new_password')
            confirm_password = request.data.get('confirm_password')
            
            if not email or not token or not new_password or not confirm_password:
                return Response({
                    'error': 'Email, token, new password, and confirm password are required',
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if passwords match
            if new_password != confirm_password:
                return Response({
                    'error': 'Passwords do not match',
                    'success': False
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Find the OTP object with this token
            try:
                otp_obj = PasswordResetOTP.objects.get(
                    email=email,
                    reset_token=token,
                    is_used=False,
                    expires_at__gt=timezone.now()
                )
            except PasswordResetOTP.DoesNotExist:
                return Response({
                    'error': 'Invalid or expired token',
                    'success': False
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get user and reset password
            try:
                user = User.objects.get(email=email)
                user.set_password(new_password)
                user.save()
                
                # Mark OTP as used
                otp_obj.mark_as_used()
                
                return Response({
                    'message': 'Password has been reset successfully',
                    'success': True
                }, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                return Response({
                    'error': 'User not found',
                    'success': False
                }, status=status.HTTP_404_NOT_FOUND)
                
        except Exception as e:
            return Response({
                'error': 'Failed to reset password',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
