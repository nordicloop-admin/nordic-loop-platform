"""
Email service for handling Mailjet email communications
"""
import os
from django.conf import settings
from mailjet_rest import Client
from typing import Dict, Any, Optional


class MailjetEmailService:
    """Service class for handling Mailjet email operations"""
    
    def __init__(self):
        self.api_key = os.environ.get('MAILJET_API_KEY', '')
        self.secret_key = os.environ.get('MAILJET_SECRET_KEY', '')
        self.sender_email = os.environ.get(
            'MAILJET_SENDER_EMAIL', 
            getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@nordicloop.com')
        )
        self.sender_name = os.environ.get('MAILJET_SENDER_NAME', 'Nordic Loop')
        
        # Initialize client only if credentials are available
        self.client = None
        if self.api_key and self.secret_key:
            self.client = Client(auth=(self.api_key, self.secret_key), version='v3.1')
    
    def _check_credentials(self):
        """Check if Mailjet credentials are configured"""
        if not self.api_key or not self.secret_key:
            raise Exception("Mailjet API credentials not configured. Please set MAILJET_API_KEY and MAILJET_SECRET_KEY environment variables.")
        if not self.client:
            self.client = Client(auth=(self.api_key, self.secret_key), version='v3.1')
    
    def send_password_reset_otp(self, email: str, otp: str, recipient_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Send password reset OTP email
        
        Args:
            email: Recipient email address
            otp: 6-digit OTP code
            recipient_name: Optional recipient name
            
        Returns:
            Dict containing email send result
        """
        self._check_credentials()
        
        if not recipient_name:
            recipient_name = email.split('@')[0]
            
        # Enhanced HTML template for password reset OTP
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Password Reset - Nordic Loop</title>
            <style>
                body {{
                    margin: 0;
                    padding: 0;
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    background-color: #f5f5f5;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background-color: #ffffff;
                    border-radius: 10px;
                    overflow: hidden;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                }}
                .header {{
                    background: linear-gradient(135deg, #FF8A00 0%, #e67e00 100%);
                    color: white;
                    padding: 30px 20px;
                    text-align: center;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 28px;
                    font-weight: 300;
                }}
                .content {{
                    padding: 40px 20px;
                }}
                .otp-container {{
                    background-color: #f8f9fa;
                    border: 2px dashed #FF8A00;
                    border-radius: 10px;
                    padding: 25px;
                    text-align: center;
                    margin: 30px 0;
                }}
                .otp-code {{
                    font-size: 36px;
                    font-weight: bold;
                    color: #FF8A00;
                    letter-spacing: 8px;
                    margin: 0;
                    font-family: 'Courier New', monospace;
                }}
                .warning-box {{
                    background-color: #fff3cd;
                    border: 1px solid #ffeaa7;
                    border-radius: 5px;
                    padding: 15px;
                    margin: 20px 0;
                }}
                .warning-text {{
                    color: #856404;
                    margin: 0;
                    font-size: 14px;
                }}
                .footer {{
                    background-color: #f8f9fa;
                    padding: 20px;
                    text-align: center;
                    border-top: 1px solid #e9ecef;
                }}
                .footer p {{
                    margin: 0;
                    color: #6c757d;
                    font-size: 14px;
                }}
                .btn {{
                    display: inline-block;
                    padding: 12px 30px;
                    background-color: #FF8A00;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    font-weight: bold;
                    margin: 20px 0;
                }}
                @media (max-width: 600px) {{
                    .container {{
                        margin: 10px;
                        border-radius: 5px;
                    }}
                    .content {{
                        padding: 20px 15px;
                    }}
                    .otp-code {{
                        font-size: 28px;
                        letter-spacing: 4px;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Password Reset</h1>
                </div>
                <div class="content">
                    <h2>Hello {recipient_name},</h2>
                    <p>We received a request to reset your password for your Nordic Loop account. Use the verification code below to proceed:</p>
                    
                    <div class="otp-container">
                        <p style="margin: 0 0 10px 0; font-size: 16px; color: #666;">Your verification code is:</p>
                        <p class="otp-code">{otp}</p>
                    </div>
                    
                    <div class="warning-box">
                        <p class="warning-text">
                            <strong>Important:</strong> This code will expire in 30 minutes. If you didn't request this password reset, please ignore this email or contact our support team.
                        </p>
                    </div>
                    
                    <p>For your security:</p>
                    <ul>
                        <li>Never share this code with anyone</li>
                        <li>Nordic Loop will never ask for your password via email</li>
                        <li>If you have concerns, contact our support team</li>
                    </ul>
                    
                    <p>Best regards,<br>The Nordic Loop Team</p>
                </div>
                <div class="footer">
                    <p>© 2024 Nordic Loop. All rights reserved.</p>
                    <p>If you need help, contact us at support@nordicloop.com</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text version for email clients that don't support HTML
        text_content = f"""
        Nordic Loop - Password Reset
        
        Hello {recipient_name},
        
        We received a request to reset your password for your Nordic Loop account.
        
        Your verification code is: {otp}
        
        This code will expire in 30 minutes.
        
        For your security:
        - Never share this code with anyone
        - Nordic Loop will never ask for your password via email
        - If you didn't request this, please ignore this email
        
        If you need help, contact us at support@nordicloop.com
        
        Best regards,
        The Nordic Loop Team
        
        © 2024 Nordic Loop. All rights reserved.
        """
        
        data = {
            'Messages': [
                {
                    "From": {
                        "Email": self.sender_email,
                        "Name": self.sender_name
                    },
                    "To": [
                        {
                            "Email": email,
                            "Name": recipient_name
                        }
                    ],
                    "Subject": "🔐 Nordic Loop - Password Reset Verification Code",
                    "TextPart": text_content,
                    "HTMLPart": html_content
                }
            ]
        }
        
        result = self.client.send.create(data=data)
        
        if result.status_code != 200:
            raise Exception(f"Failed to send email: {result.status_code} - {result.reason}")
            
        return {
            'success': True,
            'message_id': result.json().get('Messages', [{}])[0].get('MessageID'),
            'status': result.status_code
        }
    
    def send_password_reset_success(self, email: str, recipient_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Send password reset success notification email
        
        Args:
            email: Recipient email address
            recipient_name: Optional recipient name
            
        Returns:
            Dict containing email send result
        """
        self._check_credentials()
        
        if not recipient_name:
            recipient_name = email.split('@')[0]
            
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Password Reset Successful - Nordic Loop</title>
            <style>
                body {{
                    margin: 0;
                    padding: 0;
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    background-color: #f5f5f5;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background-color: #ffffff;
                    border-radius: 10px;
                    overflow: hidden;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                }}
                .header {{
                    background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
                    color: white;
                    padding: 30px 20px;
                    text-align: center;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 28px;
                    font-weight: 300;
                }}
                .content {{
                    padding: 40px 20px;
                }}
                .success-icon {{
                    text-align: center;
                    font-size: 48px;
                    color: #28a745;
                    margin: 20px 0;
                }}
                .footer {{
                    background-color: #f8f9fa;
                    padding: 20px;
                    text-align: center;
                    border-top: 1px solid #e9ecef;
                }}
                .footer p {{
                    margin: 0;
                    color: #6c757d;
                    font-size: 14px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Password Reset Successful</h1>
                </div>
                <div class="content">
                    <div class="success-icon"></div>
                    <h2>Hello {recipient_name},</h2>
                    <p>Your password has been successfully reset for your Nordic Loop account.</p>
                    <p>You can now log in with your new password. If this wasn't you, please contact our support team immediately.</p>
                    <p>For your security, we recommend:</p>
                    <ul>
                        <li>Using a strong, unique password</li>
                        <li>Enabling two-factor authentication if available</li>
                        <li>Keeping your login credentials secure</li>
                    </ul>
                    <p>Best regards,<br>The Nordic Loop Team</p>
                </div>
                <div class="footer">
                    <p>© 2024 Nordic Loop. All rights reserved.</p>
                    <p>If you need help, contact us at support@nordicloop.com</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Nordic Loop - Password Reset Successful
        
        Hello {recipient_name},
        
        Your password has been successfully reset for your Nordic Loop account.
        
        You can now log in with your new password. If this wasn't you, please contact our support team immediately.
        
        For your security, we recommend:
        - Using a strong, unique password
        - Enabling two-factor authentication if available
        - Keeping your login credentials secure
        
        Best regards,
        The Nordic Loop Team
        
        © 2024 Nordic Loop. All rights reserved.
        """
        
        data = {
            'Messages': [
                {
                    "From": {
                        "Email": self.sender_email,
                        "Name": self.sender_name
                    },
                    "To": [
                        {
                            "Email": email,
                            "Name": recipient_name
                        }
                    ],
                    "Subject": "Nordic Loop - Password Reset Successful",
                    "TextPart": text_content,
                    "HTMLPart": html_content
                }
            ]
        }
        
        result = self.client.send.create(data=data)
        
        if result.status_code != 200:
            raise Exception(f"Failed to send email: {result.status_code} - {result.reason}")
            
        return {
            'success': True,
            'message_id': result.json().get('Messages', [{}])[0].get('MessageID'),
            'status': result.status_code
        }


# Singleton instance
email_service = MailjetEmailService()
