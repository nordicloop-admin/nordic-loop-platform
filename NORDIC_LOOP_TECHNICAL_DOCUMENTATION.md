# Nordic Loop Platform - Technical Document├── Services Layer
    ├── Payment Processing (Stripe Connect)
    ├── File Storage (Cloudflare R2/Local Hybrid)
    ├── Email Services (Mailjet)
    └── Background Tasks
## Comprehensive Evidence of Original Development & Ownership

*This documentation serves as evidence of our original development work and technical expertise in building the Nordic Loop marketplace platform from the ground up.*

---

## Executive Summary

**Nordic- **Hybrid Storage System**: Custom Django field with Cloudflare R2 implementationLoop** is a comprehensive B2B marketplace platform for trading surplus materials and waste streams, built with modern, scalable architecture. This documentation demonstrates our deep technical expertise and original development work across:

- **Backend**: Django REST API with complex business logic
- **Frontend**: Next.js React application with modern UI
- **Database**: PostgreSQL with sophisticated data modeling
- **Payment Integration**: Custom Stripe Connect implementation
- **Infrastructure**: Docker, cloud storage, and deployment systems

---

## 1. Technical Architecture Overview

### 1.1 Backend Architecture (Django)
```
Nordic Loop Backend (Django 5.2)
├── core/ - Project Configuration
│   ├── settings.py - Environment & Security Config
│   ├── urls.py - URL Routing
│   ├── wsgi.py - WSGI Application
│   └── asgi.py - ASGI Configuration
├── base/ - Core Services & Utilities
│   ├── fields.py - Custom Django Fields
│   ├── models.py - Base Models
│   ├── utils/ - Helper Functions
│   └── services/
│       ├── hybrid_storage_service.py - R2/Local Storage
│       ├── r2_storage_service.py - Cloudflare R2 Service
│       └── firebase_service.py - Firebase Integration
├── Business Logic Applications
│   ├── ads/ - Material Auction System
│   ├── bids/ - Bidding Engine
│   ├── users/ - User Authentication & Management
│   ├── company/ - B2B Company Management
│   ├── payments/ - Stripe Connect Integration
│   ├── notifications/ - Real-time Messaging System
│   ├── category/ - Material Classification
│   ├── category_subscriptions/ - Category Alerts
│   └── pricing/ - Subscription Management
├── Infrastructure
│   ├── Docker Configuration
│   ├── Requirements Management (pyproject.toml)
│   └── Deployment Scripts
└── Storage & Media
    ├── static/ - Static Files
    ├── media/ - Local File Storage
    └── Cloudflare R2 Integration
```

### 1.2 Frontend Architecture (Next.js)
```
Nordic Loop Frontend (Next.js 15.3.0)
├── src/
│   ├── app/ - App Router Pages
│   │   ├── about/ - About Page
│   │   ├── admin/ - Admin Dashboard
│   │   ├── contact/ - Contact Page
│   │   ├── dashboard/ - User Dashboard
│   │   ├── login/ - Authentication Pages
│   │   ├── market-place/ - Marketplace Interface
│   │   ├── pricing/ - Subscription Plans
│   │   └── layout.tsx - Root Layout
│   ├── components/ - Reusable Components
│   │   ├── ui/ - Base UI Components
│   │   ├── layout/ - Layout Components
│   │   ├── forms/ - Form Components
│   │   └── dashboard/ - Dashboard Components
│   ├── contexts/ - React Context Providers
│   │   └── AuthContext.tsx - Authentication State
│   ├── services/ - API Integration
│   │   └── auth.ts - Authentication Services
│   ├── types/ - TypeScript Definitions
│   ├── hooks/ - Custom React Hooks
│   ├── lib/ - Utility Libraries
│   └── utils/ - Helper Functions
├── public/ - Static Assets
└── Configuration Files
    ├── next.config.js - Next.js Configuration
    ├── tailwind.config.js - TailwindCSS Setup
    └── package.json - Dependencies
```

---

## 2. Core Business Features & Custom Implementations

### 2.1 Advanced Material Auction System

**Our Original Implementation:**
```python
# ads/models.py - Complex Ad Model with Business Logic
class Ad(models.Model):
    # 8-step auction creation process for plastics
    # 4-step simplified process for other materials
    
    # Dynamic step completion tracking
    step_1_complete = models.BooleanField(default=False)
    step_2_complete = models.BooleanField(default=False)
    # ... up to step_8_complete
    
    def update_step_completion_flags(self):
        """Custom business logic for step validation"""
        is_plastic = self.category.name.lower() in ['plastic', 'plastics']
        
        if is_plastic:
            # Full 8-step process for plastic materials
            self.is_complete = all([
                self.step_1_complete, self.step_2_complete, 
                # ... all 8 steps
            ])
        else:
            # Simplified 4-step process for other materials
            self.is_complete = all([
                self.step_1_complete, self.step_6_complete,
                self.step_7_complete, self.step_8_complete
            ])
```

**Key Features Demonstrating Ownership:**
1. **Dynamic Form Workflow**: Different material types follow different creation paths
2. **Custom Validation Logic**: Business rules for minimum quantities, broker permissions
3. **Auction Timing System**: Automatic start/end date calculation
4. **Status Management**: Draft → Active → Completed workflow

### 2.2 Sophisticated Bidding Engine

**Our Bidding System Architecture:**
```python
# bids/models.py - Advanced Bidding Logic
class Bid(models.Model):
    # Integer-only pricing to avoid decimal issues
    bid_price_per_unit = models.IntegerField(
        validators=[MinValueValidator(1)]
    )
    volume_requested = models.IntegerField(
        validators=[MinValueValidator(1)]
    )
    
    # Payment authorization integration
    stripe_payment_method_id = models.CharField(max_length=255)
    authorization_status = models.CharField(max_length=30)
    authorization_expires_at = models.DateTimeField()
    
    def clean(self):
        """Custom validation against ad requirements"""
        # Check broker bid permissions
        if (self.user.company.sector == 'broker' and 
            not self.ad.allow_broker_bids):
            raise ValidationError("Broker bids not allowed")
```

**Unique Features:**
- **Payment Pre-authorization**: Bids require payment method authorization
- **Broker Permission System**: Sellers can restrict broker participation
- **Automatic Outbidding**: System tracks winning/losing bid status
- **Volume-based Bidding**: Partial or full quantity bidding

### 2.3 Advanced Payment Processing System

**Custom Stripe Connect Implementation:**
```python
# payments/services.py - Platform-Hold Payment Model
class StripeConnectService:
    def create_payment_intent(self, payment_intent_obj: PaymentIntent):
        """Platform-hold model: Platform collects, then transfers to seller"""
        
        # Platform collects payment directly
        intent = stripe.PaymentIntent.create(
            amount=total_amount_cents,
            currency=payment_intent_obj.currency.lower(),
            metadata={
                'payment_flow': 'platform_hold_and_transfer',
                'commission_rate': str(payment_intent_obj.commission_rate),
                'seller_account_id': seller_company.stripe_account_id,
            }
        )
        
    def process_payout(self, payout_schedule: PayoutSchedule):
        """Transfer funds from platform to seller"""
        transfer = stripe.Transfer.create(
            amount=payout_amount_cents,
            currency=payout_schedule.currency.lower(),
            destination=seller_company.stripe_account_id,
        )
```

**Advanced Payment Features:**
- **Platform-Hold Model**: Secure fund holding before seller payout
- **Commission Calculation**: Subscription-based commission rates
- **Cross-border Handling**: Automatic detection and manual processing
- **Insufficient Funds Handling**: Admin alerts and manual intervention

### 2.4 Hybrid File Storage System

**Custom Cloudflare R2/Local Storage Implementation:**
```python
# base/fields.py - Custom Django Field
class FirebaseImageField(models.URLField):
    """Custom field with Cloudflare R2/Local hybrid storage"""
    
    def pre_save(self, model_instance, add):
        file = getattr(model_instance, self.attname)
        
        if isinstance(file, (InMemoryUploadedFile, TemporaryUploadedFile)):
            # Upload using hybrid storage (R2 first, local fallback)
            success, message, image_url = hybrid_storage_service.upload_image(
                file, folder=self.folder, user_id=user_id
            )
```

**Storage Strategy:**
- **Cloudflare R2 Primary**: High-performance cloud storage for production
- **Local Fallback**: Automatic fallback for development/testing
- **URL Abstraction**: Seamless switching between storage backends

---

## 3. Database Design & Data Models

### 3.1 Sophisticated Data Relationships

**Company-Centric Architecture:**
```python
# Our normalized company structure
Company (1) → (M) User  # Multiple users per company
Company (1) → (1) StripeAccount  # Payment setup
Company (1) → (M) Subscription  # Billing history
Company (1) → (M) Address  # Multiple address types

# Material auction relationships
Ad (1) → (M) Bid  # Multiple bids per auction
Bid (1) → (1) PaymentIntent  # Payment tracking
PaymentIntent (1) → (M) Transaction  # Payment breakdown
```

**Advanced Features:**
- **Multi-user Companies**: Proper B2B user management
- **Payment Integration**: Stripe Connect account linking
- **Subscription Tiers**: Free/Standard/Premium with different commission rates
- **Address Management**: Business/Shipping/Billing addresses

### 3.2 Material Classification System

**Complex Category Structure:**
```python
Category → SubCategory → CategorySpecification
# Example: Plastics → HDPE → Specific grades and properties

# Dynamic specification system
class CategorySpecification(models.Model):
    specifications = models.JSONField(default=dict)
    # Stores material-specific properties like:
    # {"melt_flow_index": "2.5", "density": "0.95 g/cm³"}
```

---

## 4. Custom Business Logic Implementation

### 4.1 Multi-step Form Validation

**Dynamic Form Workflow:**
```python
# Different material types follow different validation paths
def get_step_completion_status(self):
    is_plastic = self.category.name.lower() in ['plastic', 'plastics']
    
    if is_plastic:
        # 8-step process for plastics
        return {1: step_1_complete, 2: step_2_complete, ..., 8: step_8_complete}
    else:
        # 4-step process for other materials
        return {1: step_1_complete, 6: step_6_complete, 7: step_7_complete, 8: step_8_complete}
```

### 4.2 Commission Rate Engine

**Subscription-Based Pricing:**
```python
class CommissionCalculatorService:
    COMMISSION_RATES = {
        'free': Decimal('9.00'),      # 9% for free users
        'standard': Decimal('7.00'),  # 7% for standard subscription
        'premium': Decimal('0.00'),   # 0% for premium subscription
    }
    
    def get_commission_rate(self, user: User) -> Decimal:
        subscription = Subscription.objects.filter(
            company=user.company, status='active'
        ).first()
        return self.COMMISSION_RATES.get(subscription.plan, self.COMMISSION_RATES['free'])
```

### 4.3 Notification System

**Real-time Business Notifications:**
```python
# Automated notifications for business events
- Bid received/outbid notifications
- Payment authorization alerts
- Payout processing confirmations
- Admin alerts for payment issues
- Auction completion notifications
```

---

## 5. Frontend Development Evidence

### 5.1 Modern React Architecture

**Authentication System:**
```tsx
// contexts/AuthContext.tsx - Custom authentication
export function AuthProvider({ children }: { children: React.ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    
    // JWT token management
    // Periodic token validation
    // User state synchronization
}
```

**Dashboard Implementation:**
- Multi-step auction creation forms
- Real-time bidding interface
- Payment method management
- Company profile management
- Notification center

### 5.2 Component Architecture

**Reusable UI Components:**
```typescript
// Modern component structure
├── components/
│   ├── ui/           # Base UI components (buttons, forms)
│   ├── layout/       # Layout components
│   ├── forms/        # Complex form components
│   ├── dashboard/    # Dashboard-specific components
│   └── marketplace/  # Marketplace UI components
```

---

## 6. Infrastructure & DevOps

### 6.1 Development Environment

**Docker Configuration:**
```yaml
# docker-compose.yaml
services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DJANGO_ENV=development
      - DATABASE_URL=postgresql://...
    
  frontend:
    build: ./front_end
    ports:
      - "3000:3000"
```

### 6.2 Production Deployment

**Cloud Infrastructure:**
- **Backend**: Contabo VPS servers
- **Frontend**: Vercel deployment
- **Database**: PostgreSQL cloud instance
- **Storage**: Cloudflare R2 Cloud Storage
- **CDN**: Cloudflare CDN integration

---

## 7. Security Implementation

### 7.1 Authentication & Authorization

**JWT-based Security:**
```python
# JWT token configuration
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=90),
}

# Permission system
- User-level permissions (can_place_ads, can_place_bids)
- Company-level verification (approved/pending/rejected)
- Role-based access (Admin/Staff/Viewer)
```

### 7.2 Payment Security

**Secure Payment Processing:**
- Stripe Connect for seller onboarding
- Payment authorization before bid confirmation
- Platform-hold model for secure transactions
- Commission calculation and automatic splits

---

## 8. Evidence of Original Development

### 8.1 Custom Code Patterns

**Unique Implementation Signatures:**

1. **Multi-path Form Logic**: Different material types follow different validation workflows
2. **Hybrid Storage System**: Custom Django field with Firebase/Local fallback
3. **Platform-Hold Payment Model**: Custom Stripe integration for marketplace transactions
4. **Dynamic Commission Calculation**: Subscription-based rate calculation
5. **Advanced Bidding Engine**: Integer-only pricing with payment pre-authorization

### 8.2 Business Logic Complexity

**Domain-Specific Features:**
- Material contamination levels and additives tracking
- Processing method validation for different material types
- Broker permission system for seller control
- Multi-currency support with regional considerations
- Cross-border payment restrictions handling

### 8.3 Technical Innovation

**Custom Solutions:**
```python
# Custom model field for hybrid storage
class FirebaseImageField(models.URLField):
    # Seamless switching between Cloudflare R2 and local storage
    
# Dynamic step completion tracking
def update_step_completion_flags(self):
    # Complex business rules for form validation
    
# Platform-hold payment processing
def process_payout(self, payout_schedule):
    # Custom transfer logic with error handling
```

---

## 9. Technology Stack Expertise

### 9.1 Backend Technologies
- **Django 5.2**: Latest framework features
- **Django REST Framework**: API development
- **PostgreSQL**: Advanced database features
- **Stripe Connect**: Complex payment processing
- **Cloudflare R2**: Cloud storage integration
- **JWT Authentication**: Secure token management

### 9.2 Frontend Technologies
- **Next.js 15.3.0**: Latest React framework
- **TypeScript**: Type-safe development
- **TailwindCSS**: Modern styling
- **Framer Motion**: Advanced animations
- **Context API**: State management
- **Stripe.js**: Payment integration

### 9.3 DevOps & Infrastructure
- **Docker**: Containerization
- **PostgreSQL**: Production database
- **Contabo VPS**: Backend hosting
- **Vercel**: Frontend deployment
- **Firebase**: Cloud storage
- **Mailjet**: Email services

---

## 10. Conclusion: Proof of Ownership

This documentation demonstrates our comprehensive technical expertise and original development work on the Nordic Loop platform. Key evidence includes:

### Original Custom Development:
1. **Complex Business Logic**: Multi-step material auction workflows
2. **Advanced Payment Integration**: Platform-hold model with Stripe Connect
3. **Hybrid Storage System**: Custom Django field implementation
4. **Sophisticated Data Models**: B2B-focused relationship design
5. **Modern Frontend Architecture**: Next.js with TypeScript integration

### Technical Depth:
- **Full-Stack Expertise**: Django backend + Next.js frontend
- **Payment Processing**: Custom Stripe Connect implementation
- **Database Design**: Complex normalized relationships
- **Security Implementation**: JWT authentication + role-based permissions
- **Cloud Integration**: Cloudflare R2 storage + Contabo VPS deployment

### Business Domain Expertise:
- **Marketplace Dynamics**: Bidding systems, commission calculation
- **B2B Requirements**: Company management, multi-user support
- **Material Trading**: Industry-specific workflows and validation
- **Payment Security**: Platform-hold model for secure transactions

This platform represents months of dedicated development work, showcasing our ability to build sophisticated, production-ready applications from scratch. The code complexity, custom implementations, and business logic integration clearly demonstrate original development work rather than template-based solutions.

---

*Documentation prepared to demonstrate technical ownership and development capabilities for investor review.*

**Nordic Loop Development Team**  
*Built with expertise, designed for scale*