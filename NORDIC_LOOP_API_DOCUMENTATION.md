# Nordic Loop API Documentation & Code Evidence

## Detailed Backend Implementation & Ownership Proof

*This document provides detailed API documentation and specific code implementations that demonstrate our original development work.*

---

## 1. Custom API Endpoints & Business Logic

### 1.1 Material Auction API (`ads/`)

#### Complex Ad Creation Workflow

```python
# ads/views.py - Custom ViewSets with Business Logic
class AdViewSet(viewsets.ModelViewSet):
    """
    Advanced material auction management with multi-s    # Image optimization
    images: {
        domains: [
            'r2.nordicloop.se',
            'api.nordicloop.se',
            'localhost',
        ],
    },dation
    Our custom implementation handles different material types with 
    different validation workflows (8-step for plastics, 4-step for others)
    """
  
    def create(self, request):
        # Custom creation logic with step tracking
      
    def update(self, request, pk=None):
        # Partial update with step completion recalculation
      
    def publish_auction(self, request, pk=None):
        # Custom endpoint for auction publication
        # Validates payment setup before allowing publication
      
    def get_step_status(self, request, pk=None):
        # Returns completion status for multi-step form
```

**Key API Features:**

- `GET /api/ads/` - List materials with advanced filtering
- `POST /api/ads/` - Create new material auction
- `PATCH /api/ads/{id}/step/{step_number}/` - Update specific form step
- `POST /api/ads/{id}/publish/` - Publish auction (validates payment setup)
- `GET /api/ads/{id}/step-status/` - Get form completion status

### 1.2 Bidding System API (`bids/`)

#### Advanced Bidding Engine

```python
# bids/views.py - Custom Bidding Logic
class BidViewSet(viewsets.ModelViewSet):
    """
    Sophisticated bidding system with payment pre-authorization
    """
  
    def create(self, request):
        """
        Custom bid creation with:
        - Broker permission validation
        - Payment method authorization
        - Automatic outbid detection
        """
      
    def authorize_payment(self, request, pk=None):
        """
        Custom endpoint for payment authorization before bid confirmation
        Integrates with Stripe to hold funds
        """
      
    def update_auto_bid_limit(self, request, pk=None):
        """
        Custom auto-bidding functionality
        """
```

**Bidding API Endpoints:**

- `POST /api/bids/` - Place new bid with validation
- `POST /api/bids/{id}/authorize-payment/` - Pre-authorize payment
- `GET /api/bids/my-bids/` - Get user's bid history
- `PATCH /api/bids/{id}/auto-bid/` - Update auto-bid settings

### 1.3 Payment Integration API (`payments/`)

#### Custom Stripe Connect Implementation

```python
# payments/views.py - Advanced Payment Processing
class StripeConnectViewSet(viewsets.ViewSet):
    """
    Custom Stripe Connect integration for marketplace payments
    Implements platform-hold model for secure transactions
    """
  
    def setup_seller_account(self, request):
        """
        Custom seller onboarding with Stripe Connect
        Creates Custom accounts with bank verification
        """
      
    def create_payment_intent(self, request):
        """
        Platform-hold payment creation
        Calculates commission based on subscription tier
        """
      
    def process_payout(self, request):
        """
        Admin endpoint for processing seller payouts
        Handles cross-border restrictions and insufficient funds
        """
```

**Payment API Features:**

- `POST /api/payments/setup-seller/` - Stripe Connect account setup
- `POST /api/payments/create-intent/` - Create payment with commission calculation
- `POST /api/payments/process-payout/{id}/` - Process seller payout
- `GET /api/payments/payout-schedules/` - Admin payout management

### 1.4 Company Management API (`company/`)

#### B2B Company Operations

```python
# company/views.py - Business Account Management
class CompanyViewSet(viewsets.ModelViewSet):
    """
    Advanced B2B company management with multi-user support
    """
  
    def verify_company(self, request, pk=None):
        """
        Admin endpoint for company verification
        Updates approval status and sends notifications
        """
      
    def add_user(self, request, pk=None):
        """
        Add new user to company with role assignment
        """
      
    def setup_payment_account(self, request, pk=None):
        """
        Integration with Stripe Connect for payment setup
        """
```

---

## 2. Database Models & Relationships

### 2.1 Advanced Model Relationships

```python
# Our sophisticated data model design

# Company-centric B2B architecture
Company (1) ←→ (M) User
    ├── official_name, vat_number (unique validation)
    ├── sector (industry classification)
    ├── status (pending/approved/rejected workflow)
    └── stripe_account_id (payment integration)

# Multi-user company structure
User extends AbstractUser:
    ├── company (ForeignKey to Company)
    ├── role (Admin/Staff/Viewer)
    ├── can_place_ads, can_place_bids (permissions)
    ├── is_primary_contact (company contact designation)
    └── contact_type (primary/secondary/regular)

# Complex auction system
Ad (Material Auction):
    ├── Multi-step completion tracking (step_1_complete → step_8_complete)
    ├── Dynamic validation based on material type
    ├── Auction timing (start_date, end_date, duration)
    ├── Pricing (starting_bid, reserve_price, currency)
    ├── Location & Logistics (delivery_options as JSONField)
    └── Business rules (allow_broker_bids, minimum_order_quantity)

# Advanced bidding relationships
Bid:
    ├── user (bidder) → company validation
    ├── ad (material) → business rule validation
    ├── bid_price_per_unit (integer to avoid decimal issues)
    ├── volume_requested (partial/full quantity)
    ├── Payment authorization fields:
    │   ├── stripe_payment_method_id
    │   ├── authorization_status
    │   └── authorization_expires_at
    └── Transfer tracking (stripe_transfer_id, transfer_status)
```

### 2.2 Custom Model Fields & Validation

```python
# base/fields.py - Custom Django Field Implementation
class FirebaseImageField(models.URLField):
    """
    Our custom field that seamlessly handles:
    - Firebase Cloud Storage (production)
    - Local file storage (development)
    - Automatic fallback between storage types
    - URL generation and validation
    """
  
    def pre_save(self, model_instance, add):
        # Custom upload logic with hybrid storage
      
    def validate(self, value, model_instance):
        # File type and size validation
      
    def contribute_to_class(self, cls, name, **kwargs):
        # Adds helper methods to model instances
```

### 2.3 Business Logic in Models

```python
# ads/models.py - Complex Business Validation
class Ad(models.Model):
    def clean(self):
        """Custom validation for auction publication"""
        if self.status == 'active' and self.is_complete:
            # Validate payment setup before allowing publication
            validate_auction_publication(self.user)
  
    def save(self, *args, **kwargs):
        """Override save with business logic"""
        # Update step completion flags
        self.update_step_completion_flags()
      
        # Auto-set auction timing on activation
        if self.status == 'active' and self.is_complete:
            if not self.auction_start_date:
                self.auction_start_date = timezone.now()
          
            duration_days = self.effective_auction_duration or 7
            self.auction_end_date = self.auction_start_date + timedelta(days=duration_days)
  
    def get_step_completion_status(self):
        """Dynamic step requirements based on material type"""
        is_plastic = self.category.name.lower() in ['plastic', 'plastics']
      
        if is_plastic:
            return {1: self.step_1_complete, ..., 8: self.step_8_complete}
        else:
            return {1: self.step_1_complete, 6: self.step_6_complete, 
                   7: self.step_7_complete, 8: self.step_8_complete}
```

---

## 3. Advanced Service Layer Implementation

### 3.1 Payment Processing Service

```python
# payments/services.py - Custom Stripe Integration
class StripeConnectService:
    """
    Our sophisticated payment service implementing platform-hold model
    """
  
    def create_connect_account(self, user: User, bank_account_data: Dict):
        """
        Creates Stripe Custom accounts with:
        - Business profile setup
        - Bank account verification
        - Capability requests (card_payments, transfers)
        - TOS acceptance automation
        """
      
        account = stripe.Account.create(
            type='custom',
            capabilities={
                'card_payments': {'requested': True},
                'transfers': {'requested': True},
            },
            business_profile={'mcc': '5999'},  # Marketplace classification
            tos_acceptance={'date': int(timezone.now().timestamp())},
        )
  
    def create_payment_intent(self, payment_intent_obj: PaymentIntent):
        """
        Platform-hold payment model:
        1. Customer pays platform directly
        2. Platform holds funds
        3. Platform transfers to seller after completion
        """
      
        intent = stripe.PaymentIntent.create(
            amount=total_amount_cents,
            metadata={
                'payment_flow': 'platform_hold_and_transfer',
                'commission_rate': str(payment_intent_obj.commission_rate),
                'seller_account_id': seller_company.stripe_account_id,
            }
        )
  
    def process_payout(self, payout_schedule: PayoutSchedule):
        """
        Advanced payout processing with error handling:
        - Cross-border restriction detection
        - Insufficient funds handling
        - Admin notification system
        """
      
        try:
            transfer = stripe.Transfer.create(
                amount=payout_amount_cents,
                destination=seller_company.stripe_account_id,
            )
        except stripe.error.StripeError as e:
            # Handle various Stripe error scenarios
            if 'insufficient available funds' in str(e).lower():
                # Critical admin notification
                self._send_admin_insufficient_funds_notification(payout_schedule, str(e))
            elif 'cross-border' in str(e):
                # Mark for manual processing
                payout_schedule.status = 'failed'
                payout_schedule.metadata = {'requires_manual_processing': True}
```

### 3.2 Commission Calculator Service

```python
# payments/services.py - Business Logic Service
class CommissionCalculatorService:
    """
    Subscription-based commission calculation
    """
  
    COMMISSION_RATES = {
        'free': Decimal('9.00'),      # 9% commission
        'standard': Decimal('7.00'),  # 7% commission  
        'premium': Decimal('0.00'),   # 0% commission
    }
  
    def get_commission_rate(self, user: User) -> Decimal:
        """
        Dynamic commission based on company subscription
        """
        subscription = Subscription.objects.filter(
            company=user.company,
            status='active'
        ).first()
      
        return self.COMMISSION_RATES.get(
            subscription.plan if subscription else 'free',
            self.COMMISSION_RATES['free']
        )
```

### 3.3 Hybrid Storage Service

```python
# base/services/hybrid_storage_service.py - Custom Storage
class HybridImageStorageService:
    """
    Our custom storage solution with Cloudflare R2/Local fallback
    """
  
    def upload_image(self, image_file, folder="material_images", user_id=None, force_local=False):
        """
        Hybrid upload strategy:
        1. Try Cloudflare R2 first (if enabled)
        2. Fallback to local storage if R2 fails
        3. Return appropriate URL for each storage type
        """
      
        if not force_local:
            r2_enabled = getattr(settings, 'USE_R2', False)
          
            # Attempt R2 upload
            if r2_enabled:
                try:
                    r2_success, r2_message, r2_url = r2_storage_service.upload_image(
                        image_file, folder, user_id
                    )
                    if r2_success:
                        return True, "Image uploaded to R2 successfully", r2_url
                except Exception as e:
                    logger.warning(f"R2 upload failed: {e}")
      
        # Fallback to local storage
        local_url = self._upload_to_local(image_file, folder, user_id)
        return True, "Image uploaded to local storage successfully", local_url
  
    def get_storage_type(self, image_url):
        """Detect storage backend from URL"""
        if self._is_r2_url(image_url):
            return 'r2'
        elif self._is_local_url(image_url):
            return 'local'
        return 'unknown'
```

---

## 4. Cloudflare R2 Storage Implementation

### 4.1 R2 Configuration

```python
# core/settings.py - Cloudflare R2 Configuration  
USE_R2 = env.bool('USE_R2', default=False)
CLOUDFLARE_ACCOUNT_ID = env('CLOUDFLARE_ACCOUNT_ID', default='')
CLOUDFLARE_R2_BUCKET = env('CLOUDFLARE_R2_BUCKET', default='')
CLOUDFLARE_R2_ACCESS_KEY_ID = env('CLOUDFLARE_R2_ACCESS_KEY_ID', default='')
CLOUDFLARE_R2_SECRET_ACCESS_KEY = env('CLOUDFLARE_R2_SECRET_ACCESS_KEY', default='')
R2_PUBLIC_BASE_URL = env('R2_PUBLIC_BASE_URL', default='')
DUAL_WRITE_R2 = env.bool('DUAL_WRITE_R2', default=False)
```

### 4.2 R2 Storage Service Implementation

```python
# base/services/r2_storage_service.py - Custom Cloudflare R2 Service
class R2StorageService:
    """Cloudflare R2 storage service with S3-compatible API"""
  
    def __init__(self):
        self._client = None
        self._bucket = getattr(settings, 'CLOUDFLARE_R2_BUCKET', None)
        self._public_base = getattr(settings, 'R2_PUBLIC_BASE_URL', '').rstrip('/')
        self._endpoint_url = f"https://{getattr(settings, 'CLOUDFLARE_ACCOUNT_ID', '')}.r2.cloudflarestorage.com"
  
    def upload_image(self, image_file, folder="material_images", user_id=None):
        """Upload image to Cloudflare R2 using S3-compatible API"""
        try:
            filename = self._generate_filename(getattr(image_file, 'name', 'image.jpg'), user_id)
            key = f"{folder}/user_{user_id}/{filename}" if user_id else f"{folder}/{filename}"
          
            # S3-compatible upload to Cloudflare R2
            self.client.put_object(Bucket=self._bucket, Key=key, Body=image_file.read())
          
            public_url = self._build_public_url(key)
            return True, "Image uploaded successfully", public_url
        except Exception as e:
            return False, f"Upload failed: {e}", None
          
    def _build_public_url(self, key: str) -> str:
        """Build public URL for R2 object"""
        if self._public_base:
            return f"{self._public_base}/{key}"
        return f"{self._endpoint_url}/{self._bucket}/{key}"
```

## 5. Frontend Implementation Details

### 4.1 Authentication Context

```typescript
// contexts/AuthContext.tsx - Custom Authentication
export function AuthProvider({ children }: { children: React.ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [isLoading, setIsLoading] = useState(true);
  
    // JWT token management
    const checkAuthStatus = useCallback(() => {
        const currentAuthStatus = isAuthenticated();
        const currentUser = getUser();
      
        if (currentAuthStatus !== authStatus) {
            setAuthStatus(currentAuthStatus);
        }
      
        if (JSON.stringify(currentUser) !== JSON.stringify(user)) {
            setUser(currentUser);
        }
    }, [authStatus, user]);
  
    // Periodic token validation (every 30 seconds)
    useEffect(() => {
        const tokenCheckInterval = setInterval(() => {
            checkAuthStatus();
        }, 30000);
      
        return () => clearInterval(tokenCheckInterval);
    }, [checkAuthStatus]);
}
```

### 4.2 API Service Layer

```typescript
// services/auth.ts - API Integration
interface LoginResponse {
    data?: {
        id: number;
        email: string;
        username: string;
	firsname: string;
        company_id?: number;
        role?: string;
    };
    tokens?: {
        access: string;
        refresh: string;
    };
}

export const login = async (credentials: LoginCredentials): Promise<LoginResponse> => {
    const response = await fetch(`${API_BASE_URL}/users/login/`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(credentials),
    });
  
    if (response.ok) {
        const data = await response.json();
  
        // Store JWT tokens securely
        if (data.tokens) {
            localStorage.setItem('access_token', data.tokens.access);
            localStorage.setItem('refresh_token', data.tokens.refresh);
        }
  
        return { data, tokens: data.tokens };
    }
  
    throw new Error('Login failed');
};
```

---

## 6. Configuration & Environment Management

### 5.1 Django Settings Architecture

```python
# core/settings.py - Production-Ready Configuration
class EnvironmentConfig:
    """
    Our sophisticated environment management
    """
  
    # Multi-environment support
    ENV = env('DJANGO_ENV')  # development/staging/production
    PRODUCTION = ENV == 'production'
    DEBUG = env.bool('DJANGO_DEBUG', default=not PRODUCTION)
  
    # Database configuration with fallback
    if DEBUG:
        DATABASES = {
            'default': dj_database_url.config(
                default=DATABASE_URL,
                conn_max_age=600,
                conn_health_checks=True,
            )
        }
  
    # Security configuration
    if not DEBUG and PRODUCTION:
        SECURE_SSL_REDIRECT = True
        SESSION_COOKIE_SECURE = True
        CSRF_COOKIE_SECURE = True
  
    # CORS configuration for cross-origin requests
    CORS_ALLOWED_ORIGINS = [
        "http://localhost:3000",
        "https://testingnordicloop.vercel.app", 
        "https://nordicloop.se",
        "https://nordicloop.se",
    ]
```

### 5.2 Frontend Configuration

```typescript
// next.config.js - Advanced Next.js Configuration
const nextConfig = {
    experimental: {
        turbo: {
            // Turbopack for faster development builds
        }
    },
  
    // Image optimization
    images: {
        domains: [
            'images.nordicloop.se',
            'api.nordicloop.se',
   
        ],
    },
  
    // Environment variables
    env: {
        NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
        NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY: process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY,
    },
};
```

---

## 7. Deployment & Infrastructure

### 6.1 Docker Configuration

```dockerfile
# Dockerfile - Multi-stage Production Build
FROM python:3.12-slim as base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync

# Application setup
COPY . .
EXPOSE 8000

# Production command
CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000"]
```

```yaml
# docker-compose.yaml - Development Environment
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DJANGO_ENV=development
      - DATABASE_URL=postgresql://postgres:password@db:5432/nordicloop
    depends_on:
      - db
    
  frontend:
    build:
      context: ./front_end
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
  
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: nordicloop
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
```

### 6.2 Production Deployment

**Backend (Contabo VPS):**

```bash
# Production deployment on Contabo VPS
# Nginx + Gunicorn setup
server {
    listen 443 ssl;
    server_name api.nordicloop.se;
  
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
  
    # SSL configuration
    ssl_certificate /path/to/ssl/cert;
    ssl_certificate_key /path/to/ssl/key;
}

# Gunicorn service
gunicorn core.wsgi:application --bind 127.0.0.1:8000 --workers 4
```

**Frontend (Vercel):**

```json
{
  "builds": [
    {
      "src": "package.json",
      "use": "@vercel/next"
    }
  ],
  "env": {
    "NEXT_PUBLIC_API_URL": "https://api.nordicloop.se"
  }
}
```

---

## 8. Testing & Quality Assurance

### 7.1 Model Testing

```python
# ads/tests.py - Comprehensive Model Testing
class AdModelTest(TestCase):
    def test_step_completion_plastic_material(self):
        """Test 8-step completion for plastic materials"""
        ad = Ad.objects.create(category=self.plastic_category)
      
        # Initially incomplete
        self.assertFalse(ad.is_complete)
      
        # Complete all 8 steps for plastic
        ad.step_1_complete = True
        # ... complete all steps
        ad.step_8_complete = True
        ad.update_step_completion_flags()
      
        self.assertTrue(ad.is_complete)
  
    def test_step_completion_non_plastic_material(self):
        """Test 4-step completion for non-plastic materials"""
        ad = Ad.objects.create(category=self.metal_category)
      
        # Complete required steps (1, 6, 7, 8)
        ad.step_1_complete = True
        ad.step_6_complete = True
        ad.step_7_complete = True
        ad.step_8_complete = True
        ad.update_step_completion_flags()
      
        self.assertTrue(ad.is_complete)
```

### 7.2 API Testing

```python
# bids/tests.py - API Integration Testing
class BidAPITest(APITestCase):
    def test_create_bid_with_payment_authorization(self):
        """Test bid creation with payment pre-authorization"""
      
        url = reverse('bid-list')
        data = {
            'ad': self.ad.id,
            'bid_price_per_unit': 150,
            'volume_requested': 100,
            'stripe_payment_method_id': 'pm_test_123'
        }
      
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 201)
      
        # Verify authorization was created
        bid = Bid.objects.get(id=response.data['id'])
        self.assertEqual(bid.authorization_status, 'authorized')
```

---

## 9. Performance Optimization

### 8.1 Database Optimization

```python
# Optimized queries with select_related and prefetch_related
class AdViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return Ad.objects.select_related(
            'user', 'user__company', 'category', 'subcategory', 'location'
        ).prefetch_related(
            'bids__user', 'bids__user__company'
        )
```

### 8.2 Caching Strategy

```python
# Cache frequently accessed data
from django.core.cache import cache

def get_commission_rate(self, user: User) -> Decimal:
    cache_key = f"commission_rate_{user.company_id}"
    rate = cache.get(cache_key)
  
    if rate is None:
        # Calculate and cache for 1 hour
        rate = self._calculate_commission_rate(user)
        cache.set(cache_key, rate, 3600)
  
    return rate
```

---

## 10. Security Implementation

### 9.1 Input Validation

```python
# Custom serializers with business validation
class BidSerializer(serializers.ModelSerializer):
    def validate(self, data):
        """Custom validation for bid creation"""
      
        # Validate bid amount
        if data['bid_price_per_unit'] < int(float(data['ad'].starting_bid_price)):
            raise serializers.ValidationError("Bid too low")
      
        # Validate broker restrictions
        if (self.context['request'].user.company.sector == 'broker' and 
            not data['ad'].allow_broker_bids):
            raise serializers.ValidationError("Broker bids not allowed")
      
        return data
```

### 9.2 Permission System

```python
# Custom permission classes
class CanPlaceAdsPermission(BasePermission):
    """Permission for users who can create material ads"""
  
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and 
            request.user.can_place_ads and
            request.user.company and
            request.user.company.status == 'approved'
        )

class CanPlaceBidsPermission(BasePermission):
    """Permission for users who can place bids"""
  
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.can_place_bids and
            request.user.company and
            request.user.company.status == 'approved'
        )
```

---

## 11. Monitoring & Logging

### 10.1 Structured Logging

```python
# Custom logging configuration
LOGGING = {
    'version': 1,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'nordic_loop.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'payments.services': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Usage in services
logger = logging.getLogger('payments.services')
logger.info(f"Payment intent created: {intent.id}")
logger.error(f"Stripe error: {str(e)}")
```

---

## Conclusion

This detailed documentation demonstrates our comprehensive backend implementation with:

1. **Custom API Development**: Advanced viewsets with business logic
2. **Sophisticated Data Models**: Complex relationships and validation
3. **Advanced Services**: Payment processing, file storage, commission calculation
4. **Production-Ready Code**: Error handling, logging, security
5. **Modern Architecture**: Docker, cloud deployment, performance optimization

The code complexity, custom implementations, and integration depth clearly show original development work rather than template-based solutions. Our platform represents months of dedicated full-stack development with deep domain expertise in marketplace dynamics and B2B requirements.

---

*Nordic Loop Technical Team - Building sophisticated marketplace solutions*
