# Mailjet Setup Guide for Nordic Loop Password Reset

## Overview

The Nordic Loop platform now uses Mailjet for sending password reset emails with professional templates. This guide will help you configure Mailjet integration.

## Prerequisites

1. **Mailjet Account**: Sign up at [https://www.mailjet.com/](https://www.mailjet.com/)
2. **API Credentials**: Get your API key and secret from Mailjet dashboard
3. **Sender Email**: Verify your sender domain/email in Mailjet

## Step 1: Get Mailjet Credentials

1. Go to [Mailjet Dashboard](https://app.mailjet.com/)
2. Navigate to **Account Settings** > **REST API** > **API Key Management**
3. Copy your **API Key** and **Secret Key**

## Step 2: Environment Configuration

Add these environment variables to your `.env` file:

```bash
# Mailjet Email Configuration
MAILJET_API_KEY=your-mailjet-api-key-here
MAILJET_SECRET_KEY=your-mailjet-secret-key-here
MAILJET_SENDER_EMAIL=noreply@yourdomain.com
MAILJET_SENDER_NAME=Nordic Loop
```

### Environment Variables Explained

- `MAILJET_API_KEY`: Your Mailjet API public key
- `MAILJET_SECRET_KEY`: Your Mailjet API private key  
- `MAILJET_SENDER_EMAIL`: Verified sender email address
- `MAILJET_SENDER_NAME`: Display name for emails (default: "Nordic Loop")

## Step 3: Install Dependencies

The required dependency has been added to `requirements.txt`:

```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install mailjet-rest==1.3.4
```

## Step 4: Verify Domain (Production)

For production use:

1. Go to **Sender Domains** in Mailjet dashboard
2. Add your domain (e.g., `nordicloop.com`)
3. Follow the DNS verification steps
4. Wait for verification (usually takes a few minutes)

## Step 5: Test the Integration

### Using Django Shell

```python
python manage.py shell

# Test email service
from users.services.email_service import email_service

# Test OTP email
result = email_service.send_password_reset_otp(
    email="test@example.com",
    otp="123456",
    recipient_name="Test User"
)
print(result)

# Test success email
result = email_service.send_password_reset_success(
    email="test@example.com", 
    recipient_name="Test User"
)
print(result)
```

### Using the API

```bash
# Request password reset
curl -X POST http://localhost:8000/api/users/request-password-reset/ \
  -H "Content-Type: application/json" \
  -d '{"email": "your-email@example.com"}'
```

## Email Templates

The integration includes two professional email templates:

### 1. Password Reset OTP Email
- **Subject**: "🔐 Nordic Loop - Password Reset Verification Code"
- **Features**: 
  - Professional Nordic Loop branding
  - Large, easy-to-read OTP code
  - Security warnings
  - Mobile-responsive design
  - 30-minute expiry notice

### 2. Password Reset Success Email
- **Subject**: "✅ Nordic Loop - Password Reset Successful"
- **Features**:
  - Success confirmation
  - Security recommendations
  - Support contact information

## Template Customization

To customize email templates, edit the files in:
- `users/services/email_service.py`

Key areas to customize:
- Colors and branding
- Logo (add your logo URL)
- Footer information
- Support contact details

## Troubleshooting

### Common Issues

1. **"Mailjet API credentials not configured"**
   - Check your environment variables are set correctly
   - Restart your Django server after adding env vars

2. **"Failed to send email: 401"**
   - Verify your API credentials are correct
   - Check if your Mailjet account is active

3. **"Failed to send email: 400"**
   - Verify your sender email is authenticated
   - Check the recipient email format

4. **Emails not being received**
   - Check spam/junk folders
   - Verify sender domain is authenticated
   - Test with a different email provider

### Development vs Production

**Development (Mailjet Sandbox)**:
- Use sandbox mode for testing
- Limited to 200 emails/day
- No domain verification required

**Production**:
- Verify your sending domain
- Configure SPF, DKIM records
- Monitor delivery statistics

## Mailjet Dashboard Features

Monitor your email performance:
- **Statistics**: Open rates, click rates, bounces
- **Real-time Events**: Track email delivery status
- **Blocked Emails**: View bounced/blocked emails
- **Templates**: Create reusable email templates (optional)

## Advanced Configuration

### Using Mailjet Templates (Optional)

Instead of HTML in code, you can create templates in Mailjet dashboard:

1. Go to **Templates** > **Transactional Templates**
2. Create templates for OTP and success emails
3. Update the email service to use template IDs:

```python
# In email_service.py, replace HTMLPart with:
"TemplateID": your_template_id,
"TemplateLanguage": True,
"Variables": {
    "otp": otp,
    "recipient_name": recipient_name
}
```

### Rate Limiting

Mailjet free tier limits:
- 6,000 emails/month
- 200 emails/day

For higher volumes, consider upgrading your Mailjet plan.

## Security Best Practices

1. **Never expose API credentials** in code or logs
2. **Use environment variables** for all sensitive data
3. **Verify sender domains** for production
4. **Monitor email delivery** for suspicious activity
5. **Implement rate limiting** to prevent abuse

## Support

- **Mailjet Documentation**: [https://dev.mailjet.com/](https://dev.mailjet.com/)
- **Mailjet Support**: Available through dashboard
- **Nordic Loop Support**: Contact your development team

---

## Summary

After setup, users will receive:
1. **Professional OTP emails** when requesting password reset
2. **Success confirmation emails** after password reset
3. **Mobile-responsive templates** that work across all email clients
4. **Security warnings** and best practice guidance

The integration is now ready for production use with proper Mailjet configuration!

