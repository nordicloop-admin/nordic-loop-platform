# Stripe Connect Integration Setup Guide

## Required Environment Variables

Add these to your Django settings or `.env` file:

```python
# Stripe Configuration
STRIPE_PUBLISHABLE_KEY = "pk_test_..." # Your Stripe publishable key
STRIPE_SECRET_KEY = "sk_test_..."      # Your Stripe secret key  
STRIPE_WEBHOOK_SECRET = "whsec_..."    # Webhook endpoint secret

# For production, use live keys:
# STRIPE_PUBLISHABLE_KEY = "pk_live_..."
# STRIPE_SECRET_KEY = "sk_live_..."
```

## Stripe Dashboard Setup

### 1. Create Stripe Account
- Go to https://dashboard.stripe.com
- Create account or sign in
- Complete business verification

### 2. Enable Connect
- Go to Connect settings in Stripe Dashboard
- Enable Express accounts
- Configure branding and business details

### 3. Get API Keys
- Go to Developers → API keys
- Copy publishable and secret keys
- Use test keys for development

### 4. Set Up Webhooks
- Go to Developers → Webhooks
- Create endpoint: `https://yourdomain.com/api/companies/payments/webhook/`
- Select events: `account.updated`
- Copy webhook secret

### 5. Configure Connect Settings
- Go to Connect → Settings
- Set up your platform settings:
  - Platform name: "Nordic Loop Marketplace"
  - Support email: your support email
  - Platform website: your website URL

## Testing the Integration

Run the test script to verify everything works:

```bash
python test_stripe_integration.py
```

Expected output:
```
=== Stripe Connect Integration Test Suite ===

Creating test company...
✓ Created user: stripetest1234567890
✓ Created company: Stripe Test Company 1234567890

--- Testing Stripe Account Creation ---
✓ Account created successfully: acct_1234567890
  Message: Account created successfully
  Company stripe_account_id: acct_1234567890

--- Testing Account Status Check ---
✓ Account exists: acct_1234567890
  Charges enabled: False
  Details submitted: False
  Payouts enabled: False
  Country: SE
  Requirements: 15+ items
  Capability card_payments: inactive
  Capability transfers: inactive
  Company payment_ready: False
  Company stripe_capabilities_complete: False
  Company stripe_onboarding_complete: False

--- Testing Onboarding Link Creation ---
✓ Onboarding link created successfully
  URL: https://connect.stripe.com/setup/...
  Message: Onboarding link created

🎉 ALL CORE TESTS PASSED!
```

## API Endpoints

The following endpoints are available:

### Create Stripe Account
```
POST /api/companies/payments/create-account/
Authorization: Bearer <token>
```

### Get Account Status
```
GET /api/companies/payments/account-status/
Authorization: Bearer <token>
```

### Create Onboarding Link
```
POST /api/companies/payments/create-onboarding-link/
Authorization: Bearer <token>
```

### Create Dashboard Link
```
POST /api/companies/payments/dashboard-link/
Authorization: Bearer <token>
```

## Frontend Integration

Use the provided React components:

1. **PaymentAccountSetup.tsx** - Main setup component
2. **PaymentSetupComplete.tsx** - Completion page

### Usage Example:
```tsx
import PaymentAccountSetup from '@/components/payment/PaymentAccountSetup';

// In your dashboard page
<PaymentAccountSetup />
```

## User Flow

1. **User tries to activate auction** → Gets blocked with payment setup message
2. **User clicks "Setup Payments"** → Creates Stripe Express account
3. **User redirects to Stripe** → Completes onboarding (bank details, verification)
4. **User returns to platform** → Account status automatically updated via webhooks
5. **User can now publish auctions** → Payment validation passes

## Security Notes

- All sensitive operations happen on backend
- Stripe handles PCI compliance
- Webhooks verify account status automatically
- Users never see sensitive payment data
- Onboarding happens on Stripe's secure platform

## Troubleshooting

### Common Issues:

1. **"Invalid API key"**
   - Check STRIPE_SECRET_KEY in settings
   - Ensure using correct test/live key

2. **"Webhook signature verification failed"**
   - Check STRIPE_WEBHOOK_SECRET matches dashboard
   - Ensure webhook endpoint is accessible

3. **"Account creation failed"**
   - Check Stripe Connect is enabled in dashboard
   - Verify business information is complete

4. **"Onboarding link expired"**
   - Links expire after 24 hours
   - Generate new link via API

### Debug Mode:

Set Django logging to DEBUG to see detailed Stripe API interactions:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'company.stripe_service': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```